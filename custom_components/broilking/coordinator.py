"""DataUpdateCoordinator for the Broil King smoker."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import BroilKingClient, BroilKingError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

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
        return data or {}
