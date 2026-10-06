"""Presence, wind, motion and joker outputs (e.g. ventilation)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import DssEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        DssPresence(c),
        DssApartmentState(c, "wind", "wind", BinarySensorDeviceClass.SAFETY),
    ]
    # Motion detectors: states named dev.<dsuid>.<index>
    for name in c.data.states:
        if name.startswith("dev."):
            dsuid = name.split(".")[1]
            dev = c.data.devices.get(dsuid)
            zone = dev.zone_id if dev else None
            entities.append(DssDeviceState(c, name, zone))
    for dsuid in c.data.joker_on:
        entities.append(DssJokerOutput(c, dsuid))
    async_add_entities(entities)


class DssPresence(DssEntity, BinarySensorEntity):
    _attr_translation_key = "presence"
    _attr_device_class = BinarySensorDeviceClass.PRESENCE

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, None, "presence")

    @property
    def is_on(self) -> bool | None:
        state = self.coordinator.data.states.get("presence")
        return None if state is None else state == "present"

    @property
    def extra_state_attributes(self) -> dict:
        return {"last_event": self.coordinator.data.last_event}


class DssApartmentState(DssEntity, BinarySensorEntity):
    def __init__(self, coordinator, state: str, key: str, device_class) -> None:
        super().__init__(coordinator, None, f"state_{state}")
        self._state = state
        self._attr_translation_key = key
        self._attr_device_class = device_class

    @property
    def is_on(self) -> bool | None:
        state = self.coordinator.data.states.get(self._state)
        return None if state is None else state in ("active", "1")


class DssDeviceState(DssEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.MOTION
    _attr_translation_key = "motion"

    def __init__(self, coordinator, state: str, zone_id: int | None) -> None:
        super().__init__(coordinator, zone_id, f"state_{state}")
        self._state = state

    @property
    def is_on(self) -> bool | None:
        state = self.coordinator.data.states.get(self._state)
        return None if state is None else state in ("active", "1")


class DssJokerOutput(DssEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.OPENING

    def __init__(self, coordinator, dsuid: str) -> None:
        dev = coordinator.data.devices[dsuid]
        super().__init__(coordinator, dev.zone_id, f"joker_{dsuid}")
        self._dsuid = dsuid
        self._attr_name = dev.name

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.joker_on.get(self._dsuid)
