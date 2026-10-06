"""One light per zone, switched via zone scenes (like the wall buttons)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import GROUP_LIGHT, SCENE_OFF, SCENE_ON
from .entity import DssEntity

# dS output modes that only switch on/off (e.g. fluorescent tubes on switched terminal blocks)
SWITCHED_OUTPUT_MODES = {16, 35, 39, 40, 41, 42, 43, 44}


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities(DssZoneLight(c, z) for z in c.light_zones())


class DssZoneLight(DssEntity, LightEntity):
    _attr_translation_key = "zone_light"

    def __init__(self, coordinator, zone_id: int) -> None:
        super().__init__(coordinator, zone_id, f"light_{zone_id}")
        self._zone = zone_id
        dimmbar = any(
            d.output_mode not in SWITCHED_OUTPUT_MODES
            for d in coordinator.data.devices.values()
            if d.zone_id == zone_id and GROUP_LIGHT in d.groups and d.channel
        )
        mode = ColorMode.BRIGHTNESS if dimmbar else ColorMode.ONOFF
        self._attr_color_mode = mode
        self._attr_supported_color_modes = {mode}

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.zone_light_on(self._zone)

    @property
    def brightness(self) -> int | None:
        if self._attr_color_mode == ColorMode.ONOFF or not self.is_on:
            return None
        # After zone scenes the dSS does not know the brightness, only after setting it directly
        return self.coordinator.data.light_override.get(self._zone, 255)

    async def async_turn_on(self, **kwargs: Any) -> None:
        if ATTR_BRIGHTNESS in kwargs and self._attr_color_mode == ColorMode.BRIGHTNESS:
            await self.coordinator.zone_brightness(self._zone, int(kwargs[ATTR_BRIGHTNESS]))
        else:
            await self.coordinator.zone_scene(self._zone, GROUP_LIGHT, SCENE_ON)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.zone_scene(self._zone, GROUP_LIGHT, SCENE_OFF)
