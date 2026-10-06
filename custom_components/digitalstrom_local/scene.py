"""Scenes named in the dSS Configurator, exposed as HA scenes."""
from __future__ import annotations

from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import DssEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities(DssScene(c, s) for s in c.data.scenes)


class DssScene(DssEntity, Scene):
    def __init__(self, coordinator, scene) -> None:
        super().__init__(coordinator, scene.zone_id, f"scene_{scene.zone_id}_{scene.group}_{scene.scene}")
        self._scene = scene
        self._attr_name = scene.name

    async def async_activate(self, **kwargs: Any) -> None:
        await self.coordinator.zone_scene(self._scene.zone_id, self._scene.group, self._scene.scene)
