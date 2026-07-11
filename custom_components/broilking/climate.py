"""Climate entity for the Broil King smoker grill."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MAX_TEMP_C, MIN_TEMP_C, MODE_IDS, MODES, TEMP_STEP_C
from .entity import BroilKingEntity, c_to_f, f_to_c


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BroilKingGrill(coordinator)])


class BroilKingGrill(BroilKingEntity, ClimateEntity):
    """The grill chamber as an HA climate device."""

    _attr_name = None  # use the device name
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_preset_modes = ["Smoke", "Cook", "High"]
    _attr_min_temp = MIN_TEMP_C
    _attr_max_temp = MAX_TEMP_C
    _attr_target_temperature_step = TEMP_STEP_C
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, coordinator):
        super().__init__(coordinator, "grill")

    @property
    def current_temperature(self):
        return f_to_c(self._data.get("grillTemp"))

    @property
    def target_temperature(self):
        return f_to_c(self._data.get("grillSetTemp"))

    @property
    def hvac_mode(self):
        return HVACMode.HEAT if self._data.get("moduleIsOn") else HVACMode.OFF

    @property
    def hvac_action(self):
        return HVACAction.HEATING if self._data.get("moduleIsOn") else HVACAction.OFF

    @property
    def preset_mode(self):
        return MODES.get(self._data.get("currentMode"))

    async def async_set_temperature(self, **kwargs) -> None:
        temp_c = kwargs.get(ATTR_TEMPERATURE)
        if temp_c is None:
            return
        await self.coordinator.client.async_set_grill_target_f(c_to_f(temp_c))
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        mode_id = MODE_IDS.get(preset_mode)
        if mode_id is not None:
            await self.coordinator.client.async_set_mode(mode_id)
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        # OFF -> Null mode (stops active cooking). HEAT -> Cook as a sane default.
        await self.coordinator.client.async_set_mode(
            MODE_IDS["Off"] if hvac_mode == HVACMode.OFF else MODE_IDS["Cook"]
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)
