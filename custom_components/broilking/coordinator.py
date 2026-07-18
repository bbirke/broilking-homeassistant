"""DataUpdateCoordinator for the Broil King smoker."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

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
        # Local mirror of the cook timer: what we last sent to the grill, and
        # when it is due to run out. The firmware accepts a timer command but
        # never echoes the timer back, so this is the only record we have. Both
        # are None while no timer is set.
        self.timer_minutes: float | None = None
        self.timer_ends_at: datetime | None = None

    def set_timer_state(
        self, minutes: float | None, ends_at: datetime | None
    ) -> None:
        """Record the cook timer locally and push it to the timer entities."""
        self.timer_minutes = minutes
        self.timer_ends_at = ends_at
        self.async_update_listeners()

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
