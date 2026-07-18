"""Sensor entities for the Broil King smoker (probes, targets, cook time)."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, MODES
from .entity import BroilKingEntity, f_to_c


@dataclass(frozen=True, kw_only=True)
class BKSensorDescription(SensorEntityDescription):
    value: Callable[[dict], object]


def _probe(raw):
    # 0 == probe unplugged -> report unknown instead of a bogus temperature
    return None if raw in (0, None) else f_to_c(raw)


SENSORS: tuple[BKSensorDescription, ...] = (
    BKSensorDescription(
        key="probe_1", name="Meat Probe 1",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda d: _probe(d.get("probe_1_Temp")),
    ),
    BKSensorDescription(
        key="probe_2", name="Meat Probe 2",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda d: _probe(d.get("probe_2_Temp")),
    ),
    BKSensorDescription(
        key="probe_1_target", name="Probe 1 Target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        value=lambda d: f_to_c(d.get("probe_1_Set_Temp")),
    ),
    BKSensorDescription(
        key="probe_2_target", name="Probe 2 Target",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        value=lambda d: f_to_c(d.get("probe_2_Set_Temp")),
    ),
    BKSensorDescription(
        key="cook_time", name="Cook Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer",
        value=lambda d: round((d.get("elapsedTime") or 0) / 60.0, 1),
    ),
    BKSensorDescription(
        key="mode", name="Preset Mode",
        icon="mdi:grill",
        value=lambda d: MODES.get(d.get("currentMode")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            *(BroilKingSensor(coordinator, d) for d in SENSORS),
            BroilKingTimerEnds(coordinator),
            BroilKingTimerRemaining(coordinator),
        ]
    )


class BroilKingSensor(BroilKingEntity, SensorEntity):
    def __init__(self, coordinator, description: BKSensorDescription):
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        return self.entity_description.value(self._data)


# The cook timer lives on the coordinator rather than in the polled payload (the
# firmware never reports it back), so these two get their own classes instead of
# a BKSensorDescription over the state dict.
class BroilKingTimerEnds(BroilKingEntity, SensorEntity):
    """When the cook timer set from HA runs out."""

    _attr_name = "Cook Timer Ends"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator):
        super().__init__(coordinator, "timer_ends_at")

    @property
    def native_value(self):
        return self.coordinator.timer_ends_at


class BroilKingTimerRemaining(BroilKingEntity, SensorEntity):
    """Minutes left on the cook timer, recomputed on every poll."""

    _attr_name = "Cook Timer Remaining"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator):
        super().__init__(coordinator, "timer_remaining")

    @property
    def native_value(self):
        ends_at = self.coordinator.timer_ends_at
        if ends_at is None:
            return None
        left = (ends_at - dt_util.utcnow()).total_seconds() / 60.0
        return max(0.0, round(left, 1))
