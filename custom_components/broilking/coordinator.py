"""DataUpdateCoordinator for the Broil King smoker."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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

    async def _async_update_data(self) -> dict:
        try:
            data = await self.client.async_get_temperatures()
        except BroilKingError as exc:
            raise UpdateFailed(str(exc)) from exc
        if not data:
            raise UpdateFailed("empty response from smoker")
        return data
