"""Number entities for the Broil King smoker (cook timer)."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    EVENT_TIMER_SET,
    MAX_TIMER_MINUTES,
    TIMER_STEP_MINUTES,
)
from .entity import BroilKingEntity

ATTR_ENDS_AT = "ends_at"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BroilKingCookTimer(coordinator)])


class BroilKingCookTimer(BroilKingEntity, NumberEntity, RestoreEntity):
    """Cook timer duration in minutes.

    Writing a value sends the timer to the grill (action 6, hours + minutes) and
    starts HA's own countdown. Since the firmware never reports the timer back,
    the value shown is what we last sent; it is restored across restarts from
    this entity's state and its `ends_at` attribute.
    """

    _attr_name = "Cook Timer"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_min_value = 0
    _attr_native_max_value = MAX_TIMER_MINUTES
    _attr_native_step = TIMER_STEP_MINUTES
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:timer-cog-outline"

    def __init__(self, coordinator):
        super().__init__(coordinator, "cook_timer")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.timer_minutes is not None:
            return
        last = await self.async_get_last_state()
        if last is None:
            return
        try:
            minutes = float(last.state)
        except (TypeError, ValueError):
            return
        ends_at = dt_util.parse_datetime(last.attributes.get(ATTR_ENDS_AT) or "")
        self.coordinator.set_timer_state(minutes, ends_at)

    @property
    def native_value(self) -> float | None:
        return self.coordinator.timer_minutes

    @property
    def extra_state_attributes(self) -> dict:
        ends_at = self.coordinator.timer_ends_at
        return {ATTR_ENDS_AT: ends_at.isoformat() if ends_at else None}

    async def async_set_native_value(self, value: float) -> None:
        # 0 clears the timer on the grill (it takes 0 h 0 min happily).
        minutes = int(value)
        hours, mins = divmod(minutes, 60)
        await self.coordinator.client.async_set_timer(hours, mins)

        ends_at = dt_util.utcnow() + timedelta(minutes=minutes) if minutes else None
        self.coordinator.set_timer_state(float(minutes), ends_at)
        self.hass.bus.async_fire(
            EVENT_TIMER_SET,
            {
                "device_id": self.coordinator.device_id,
                "entity_id": self.entity_id,
                "minutes": minutes,
                ATTR_ENDS_AT: ends_at.isoformat() if ends_at else None,
            },
        )
