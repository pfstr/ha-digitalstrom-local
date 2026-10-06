"""Absent (leave) and present (arrive) as buttons."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SCENE_ABSENT, SCENE_PRESENT
from .entity import DssEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities([DssApartmentButton(c, SCENE_ABSENT, "absent"), DssApartmentButton(c, SCENE_PRESENT, "present")])


class DssApartmentButton(DssEntity, ButtonEntity):
    def __init__(self, coordinator, scene: int, key: str) -> None:
        super().__init__(coordinator, None, f"button_{key}")
        self._scene = scene
        self._attr_translation_key = key

    async def async_press(self) -> None:
        await self.coordinator.apartment_scene(self._scene)
