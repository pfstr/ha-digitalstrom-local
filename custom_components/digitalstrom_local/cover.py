"""Blinds (grey terminal blocks) with position."""
from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SCENE_SHADE_DOWN, SCENE_SHADE_STOP, SCENE_SHADE_UP
from .entity import DssEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities(DssShade(c, dsuid) for dsuid in c.data.shade_pos)


class DssShade(DssEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, coordinator, dsuid: str) -> None:
        dev = coordinator.data.devices[dsuid]
        super().__init__(coordinator, dev.zone_id, f"shade_{dsuid}")
        self._dsuid = dsuid
        self._attr_name = dev.name

    @property
    def current_cover_position(self) -> int | None:
        return self.coordinator.data.shade_pos.get(self._dsuid)

    @property
    def is_closed(self) -> bool | None:
        pos = self.current_cover_position
        return None if pos is None else pos == 0

    def _refresh(self) -> None:
        self.hass.async_create_background_task(
            self.coordinator.refresh_device_later(self._dsuid), f"dss_refresh_{self._dsuid}"
        )

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.coordinator.device_scene(self._dsuid, SCENE_SHADE_UP)
        self._refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.coordinator.device_scene(self._dsuid, SCENE_SHADE_DOWN)
        self._refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self.coordinator.device_scene(self._dsuid, SCENE_SHADE_STOP)
        self.hass.async_create_background_task(
            self.coordinator.refresh_device_later(self._dsuid, delay=3), f"dss_refresh_{self._dsuid}"
        )

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        await self.coordinator.shade_position(self._dsuid, int(kwargs[ATTR_POSITION]))
        self._refresh()
