"""Shared base entity for Broil King Smoker."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BroilKingCoordinator


def f_to_c(raw_f):
    """Firmware values are always Fahrenheit; convert to Celsius."""
    if raw_f is None:
        return None
    return round((raw_f - 32) * 5.0 / 9.0, 1)


def c_to_f(temp_c) -> int:
    return round(temp_c * 9.0 / 5.0 + 32)


class BroilKingEntity(CoordinatorEntity[BroilKingCoordinator]):
    """Base entity that ties everything to one device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BroilKingCoordinator, key: str):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name="Broil King Smoker",
            manufacturer="Broil King",
            model="iQue Pellet",
        )

    @property
    def _data(self) -> dict:
        return self.coordinator.data or {}
