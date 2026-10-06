"""Total apartment power consumption (served from the dSS cache)."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import DssEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([DssConsumption(entry.runtime_data)])


class DssConsumption(DssEntity, SensorEntity):
    _attr_translation_key = "consumption"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, None, "consumption")

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.consumption
