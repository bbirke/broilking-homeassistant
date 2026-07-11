"""Async client for the Broil King smoker's local JSON-RPC-over-WebSocket API.

The firmware (Mongoose OS) answers on ws://<host>/rpc with no authentication on
the LAN. Custom methods return their result inside response.error.message as a
double-encoded JSON string, and error.code == 0 means success. Control commands
go through SendGenericCommand using the exact byte strings the official iQue app
builds (BleCommandMaker.buildGenericCommandSequence); the firmware appends the
UART checksum itself. Raw temperatures are always Fahrenheit.
"""
from __future__ import annotations

import json
import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)


class BroilKingError(Exception):
    """Raised when the smoker cannot be reached or returns an error."""


class BroilKingClient:
    """Stateless-per-call RPC client (one short WebSocket per request)."""

    # Action codes, verbatim from the iQue app's BleCommandMaker.
    ACT_POWER_OFF = 0
    ACT_GRILL_TEMP = 1   # value = degrees Fahrenheit (16-bit)
    ACT_PROBE1 = 2       # value = probe 1 target, Fahrenheit
    ACT_PROBE2 = 3       # value = probe 2 target, Fahrenheit
    ACT_TEMP_UNIT = 4
    ACT_COOKING_MODE = 5  # 0 Off / 1 Smoke / 2 Cook / 3 High
    ACT_TIMER = 6        # value = hours, value2 = minutes
    ACT_BRIGHTNESS = 7

    def __init__(self, host: str, session: aiohttp.ClientSession, password: str = ""):
        self._host = host
        self._session = session
        self._password = password or ""
        self._id = 0

    # ---- low level -----------------------------------------------------
    async def _rpc(self, method: str, args: dict | None = None):
        self._id += 1
        rid = self._id
        frame: dict = {"method": method, "id": rid}
        if args is not None:
            frame["args"] = args
        url = f"ws://{self._host}/rpc"
        try:
            async with self._session.ws_connect(url, timeout=10) as ws:
                await ws.send_str(json.dumps(frame))
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        resp = json.loads(msg.data)
                        if resp.get("id") != rid:
                            continue
                        err = resp.get("error")
                        if err is None:
                            return True, resp.get("result")
                        raw = err.get("message", "")
                        try:
                            payload = json.loads(raw)
                        except (ValueError, TypeError):
                            payload = raw
                        return err.get("code", -1) == 0, payload
                    if msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break
        except (aiohttp.ClientError, OSError, TimeoutError) as exc:
            raise BroilKingError(f"RPC {method} failed: {exc}") from exc
        raise BroilKingError(f"no reply to {method}")

    # ---- reads ---------------------------------------------------------
    async def async_get_info(self) -> dict:
        """Sys.GetInfo over plain HTTP (used to identify the device)."""
        url = f"http://{self._host}/rpc/Sys.GetInfo"
        try:
            async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                return await r.json(content_type=None)
        except (aiohttp.ClientError, OSError, TimeoutError) as exc:
            raise BroilKingError(f"Sys.GetInfo failed: {exc}") from exc

    async def async_get_temperatures(self) -> dict:
        args = {"reply": "full"}
        if self._password:
            args["pass"] = self._password
        ok, payload = await self._rpc("GetCurrentTemperatures", args)
        if ok and isinstance(payload, dict):
            return payload.get("GetCurrentTemperatures", {})
        return {}

    # ---- control -------------------------------------------------------
    @staticmethod
    def _generic_command_string(action: int, value: int = 0, value2: int = 0) -> str:
        lo = value % 256
        hi = (value - lo) // 256
        p = lambda n: "%03d" % (n & 0xFF)
        table = {
            0: "225 225 000 009 000 048 002 " + p(value),
            1: "225 225 000 010 000 048 005 " + p(hi) + " " + p(lo),
            2: "225 225 000 010 000 048 006 " + p(hi) + " " + p(lo),
            3: "225 225 000 010 000 048 009 " + p(hi) + " " + p(lo),
            4: "225 225 000 009 000 048 003 " + p(value),
            5: "225 225 000 009 000 048 007 " + p(value),
            6: "225 225 000 010 000 048 010 " + p(value) + " " + p(value2),
            7: "225 225 000 009 000 048 011 " + p(value),
        }
        if action not in table:
            raise ValueError(f"bad action {action!r}")
        return table[action]

    async def _send_generic(self, action: int, value: int = 0, value2: int = 0):
        args = {
            "command": self._generic_command_string(action, value, value2),
            "pass": self._password,
        }
        return await self._rpc("SendGenericCommand", args)

    async def async_set_grill_target_f(self, temp_f: int):
        return await self._send_generic(self.ACT_GRILL_TEMP, int(temp_f))

    async def async_set_mode(self, mode_id: int):
        return await self._send_generic(self.ACT_COOKING_MODE, int(mode_id) & 0xFF)

    async def async_set_probe_target_f(self, probe: int, temp_f: int):
        act = self.ACT_PROBE1 if probe == 1 else self.ACT_PROBE2
        return await self._send_generic(act, int(temp_f))

    async def async_set_timer(self, hours: int, minutes: int):
        return await self._send_generic(self.ACT_TIMER, int(hours), int(minutes))
