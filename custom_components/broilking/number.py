"""Number entities for the Broil King smoker (cook timer)."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MAX_TIMER_MINUTES, TIMER_STEP_MINUTES
from .entity import BroilKingEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BroilKingCookTimer(coordinator)])


class BroilKingCookTimer(BroilKingEntity, NumberEntity):
    """The grill's cook timer, in minutes.

    Two-way: writing sends the timer to the control board (action 6, hours +
    minutes) and the grill echoes it back in alarm_Hour_Set / alarm_Minute_Set,
    so a timer set on the grill's own panel shows up here too.
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

    @property
    def native_value(self) -> float | None:
        return (self._data.get("alarm_Hour_Set") or 0) * 60 + (
            self._data.get("alarm_Minute_Set") or 0
        )

    async def async_set_native_value(self, value: float) -> None:
        # 0 clears the timer on the grill (it takes 0 h 0 min happily).
        hours, minutes = divmod(int(value), 60)
        await self.coordinator.client.async_set_timer(hours, minutes)
        await self.coordinator.async_request_refresh()
