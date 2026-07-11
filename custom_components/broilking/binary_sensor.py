"""Binary sensors for the Broil King smoker (running, low fuel)."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import BroilKingEntity


@dataclass(frozen=True, kw_only=True)
class BKBinaryDescription(BinarySensorEntityDescription):
    value: Callable[[dict], bool]


BINARY_SENSORS: tuple[BKBinaryDescription, ...] = (
    BKBinaryDescription(
        key="running", name="Running",
        device_class=BinarySensorDeviceClass.POWER,
        value=lambda d: bool(d.get("moduleIsOn")),
    ),
    BKBinaryDescription(
        key="low_fuel", name="Low Fuel",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:gas-station",
        value=lambda d: bool(d.get("lowFuel")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(BroilKingBinarySensor(coordinator, d) for d in BINARY_SENSORS)


class BroilKingBinarySensor(BroilKingEntity, BinarySensorEntity):
    def __init__(self, coordinator, description: BKBinaryDescription):
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        return self.entity_description.value(self._data)
