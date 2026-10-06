"""Common base: one HA device per zone, updates via the dispatcher."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, SIGNAL_UPDATE
from .coordinator import DssCoordinator


class DssEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: DssCoordinator, zone_id: int | None, key: str) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.entry_id}_{key}"
        if zone_id is not None and zone_id in coordinator.data.zones:
            name = coordinator.data.zones[zone_id]
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{coordinator.entry_id}_zone_{zone_id}")},
                name=name,
                suggested_area=name,
                manufacturer="digitalSTROM",
                model="Zone",
            )
        else:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{coordinator.entry_id}_apartment")},
                name="Apartment",
                manufacturer="digitalSTROM",
                model="dSS",
            )

    @property
    def available(self) -> bool:
        return self.coordinator.available

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{SIGNAL_UPDATE}_{self.coordinator.entry_id}", self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
