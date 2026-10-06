"""digitalSTROM Local: local, event-driven integration for the digitalSTROM server (dSS)."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import DssApi, DssError
from .const import CONF_APP_TOKEN, PLATFORMS
from .coordinator import DssCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_create_clientsession(hass, verify_ssl=False)
    api = DssApi(session, entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_APP_TOKEN])
    coordinator = DssCoordinator(hass, api, entry.entry_id)
    try:
        await coordinator.async_setup()
    except DssError as err:
        raise ConfigEntryNotReady(f"digitalSTROM server not reachable: {err}") from err
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.start(entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        await entry.runtime_data.async_stop()
    return ok
