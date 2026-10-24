"""DataUpdateCoordinator for the Broil King smoker."""
from __future__ import annotations

import logging
import time
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import BroilKingClient, BroilKingError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, INFO_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class BroilKingCoordinator(DataUpdateCoordinator[dict]):
    """Polls GetCurrentTemperatures and shares the raw state dict."""

    def __init__(self, hass: HomeAssistant, client: BroilKingClient, device_id: str):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.device_id = device_id
        # Whether the last poll reached the grill. An unplugged / powered-off
        # smoker is the normal resting state (e.g. all winter), so entities key
        # their availability off this instead of it being treated as an error.
        self.reachable = False
        # Last Sys.GetInfo reply, for the diagnostic sensors and device info.
        self.info: dict = {}
        self._info_fetched_at = 0.0

    async def _async_update_data(self) -> dict:
        try:
            data = await self.client.async_get_temperatures()
        except BroilKingError as exc:
            # Being unreachable is expected when the grill is off/unplugged - do
            # not raise. Raising would spam the log and, on startup, block the
            # whole integration from loading (ConfigEntryNotReady). Report it as
            # offline instead; entities become "unavailable" until it is back.
            _LOGGER.debug("smoker unreachable, treating as offline: %s", exc)
            self.reachable = False
            return {}
        self.reachable = True
        await self._async_update_info()
        return data or {}

    async def _async_update_info(self) -> None:
        # Sys.GetInfo (firmware, uptime, free RAM) changes slowly, so it is not
        # fetched on every temperature poll. A failure here only leaves the
        # diagnostic sensors stale; it never marks the grill offline.
        now = time.monotonic()
        if self.info and now - self._info_fetched_at < INFO_SCAN_INTERVAL:
            return
        try:
            self.info = await self.client.async_get_info()
        except BroilKingError as exc:
            _LOGGER.debug("Sys.GetInfo failed: %s", exc)
            return
        self._info_fetched_at = now
