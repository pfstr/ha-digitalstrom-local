"""Hub: keeps the apartment state, listens to dSS events and distributes updates."""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .api import DssApi, DssError
from .const import (
    BUS_POLL_SECONDS,
    EVENT_NAME,
    GROUP_JOKER,
    GROUP_LIGHT,
    GROUP_SHADE,
    HIDDEN_SCENES,
    SCENE_ABSENT,
    SCENE_PRESENT,
    SIGNAL_UPDATE,
    STATE_POLL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

SUBSCRIPTION_ID = 8472
EVENTS = ("callScene", "stateChange")


@dataclass
class Device:
    dsuid: str
    dsid: str
    name: str
    zone_id: int
    groups: list[int]
    hw: str
    output_mode: int
    channel: str | None


@dataclass
class NamedScene:
    zone_id: int
    zone_name: str
    group: int
    scene: int
    name: str


@dataclass
class Apartment:
    zones: dict[int, str] = field(default_factory=dict)
    devices: dict[str, Device] = field(default_factory=dict)
    scenes: list[NamedScene] = field(default_factory=list)
    states: dict[str, str] = field(default_factory=dict)  # name -> "active"/"inactive"/"present"/...
    shade_pos: dict[str, int] = field(default_factory=dict)  # dsuid -> 0..100 (100 = open)
    joker_on: dict[str, bool] = field(default_factory=dict)  # dsuid -> output on
    consumption: int | None = None
    light_override: dict[int, int] = field(default_factory=dict)  # zone -> last brightness set (0..255)
    last_event: str | None = None


class DssCoordinator:
    def __init__(self, hass: HomeAssistant, api: DssApi, entry_id: str) -> None:
        self.hass = hass
        self.api = api
        self.entry_id = entry_id
        self.data = Apartment()
        self.available = False
        self._tasks: list[asyncio.Task] = []
        self._last_bus_poll = 0.0

    # ---------- start / stop ----------

    async def async_setup(self) -> None:
        await self.api.login()
        await self._load_structure()
        await self._load_scenes()
        await self._poll_states()
        await self._poll_bus()
        self.available = True

    def start(self, entry) -> None:
        self._tasks.append(entry.async_create_background_task(self.hass, self._event_loop(), "digitalstrom_local_events"))
        self._tasks.append(entry.async_create_background_task(self.hass, self._poll_loop(), "digitalstrom_local_poll"))

    async def async_stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        for name in EVENTS:
            try:
                await self.api.call("event/unsubscribe", {"name": name, "subscriptionID": SUBSCRIPTION_ID}, timeout=5)
            except DssError:
                pass

    # ---------- loading ----------

    async def _load_structure(self) -> None:
        structure = await self.api.call("apartment/getStructure")
        zones = {}
        for z in structure["apartment"]["zones"]:
            zid = int(z["id"])
            if zid not in (0, 65534) and z.get("name"):
                zones[zid] = z["name"]
        devices = {}
        for d in await self.api.call("apartment/getDevices"):
            channels = d.get("outputChannels") or []
            devices[d["dSUID"]] = Device(
                dsuid=d["dSUID"],
                dsid=d["id"],
                name=d.get("name") or d["DisplayID"],
                zone_id=int(d["zoneID"]),
                groups=[int(g) for g in d.get("groups", [])],
                hw=d.get("hwInfo", ""),
                output_mode=int(d.get("outputMode", 0)),
                channel=channels[0]["channelType"] if channels else None,
            )
        self.data.zones = zones
        self.data.devices = devices

    async def _load_scenes(self) -> None:
        res = await self.api.call(
            "property/query",
            {"query": "/apartment/zones/*(ZoneID)/groups/*(group)/scenes/*(scene,name)"},
        )
        scenes = []
        for z in res.get("zones", []):
            zid = int(z.get("ZoneID", 0))
            if zid not in self.data.zones:
                continue
            for g in z.get("groups", []):
                for s in g.get("scenes", []):
                    num = int(s.get("scene", -1))
                    name = (s.get("name") or "").strip()
                    if name and num not in HIDDEN_SCENES:
                        scenes.append(NamedScene(zid, self.data.zones[zid], int(g.get("group", 0)), num, name))
        self.data.scenes = scenes

    # ---------- polling ----------

    async def _poll_states(self) -> None:
        res = await self.api.call("property/query", {"query": "/usr/states/*(name,state,value)"})
        states = {}
        for s in res.get("states", []):
            states[s["name"]] = str(s.get("state") or s.get("value"))
        self.data.states = states
        cons = await self.api.call("apartment/getConsumption")
        value = int(cons.get("consumption", 0))
        # The dSS reports 0 W briefly after a restart; a whole apartment never draws exactly 0 W
        if value > 0 or self.data.consumption is None:
            self.data.consumption = value

    async def _poll_bus(self) -> None:
        """Read output values directly from the terminal blocks. Keep this rare: every read loads the dS485 bus."""
        self._last_bus_poll = time.monotonic()
        for dev in self.data.devices.values():
            try:
                if GROUP_SHADE in dev.groups and dev.channel and "shade" in dev.channel:
                    val = (await self.api.call("device/getOutputValue", {"dsid": dev.dsid, "offset": 2}))["value"]
                    self.data.shade_pos[dev.dsuid] = round(int(val) * 100 / 65535)
                elif dev.groups == [GROUP_JOKER] and dev.channel == "powerLevel":
                    val = (await self.api.call("device/getOutputValue", {"dsid": dev.dsid, "offset": 0}))["value"]
                    self.data.joker_on[dev.dsuid] = int(val) > 0
            except DssError as err:
                _LOGGER.debug("Cannot read output of %s: %s", dev.name, err)

    async def refresh_device_later(self, dsuid: str, delay: float = 70) -> None:
        await asyncio.sleep(delay)
        dev = self.data.devices[dsuid]
        try:
            val = (await self.api.call("device/getOutputValue", {"dsid": dev.dsid, "offset": 2}))["value"]
            self.data.shade_pos[dsuid] = round(int(val) * 100 / 65535)
            self._notify()
        except DssError as err:
            _LOGGER.debug("Cannot read position of %s: %s", dev.name, err)

    async def _poll_loop(self) -> None:
        while True:
            await asyncio.sleep(STATE_POLL_SECONDS)
            try:
                await self._poll_states()
                if time.monotonic() - self._last_bus_poll > BUS_POLL_SECONDS:
                    await self._poll_bus()
                self.available = True
            except DssError as err:
                _LOGGER.warning("dSS not reachable: %s", err)
                self.available = False
            self._notify()

    # ---------- events ----------

    async def _subscribe(self) -> None:
        for name in EVENTS:
            await self.api.call("event/subscribe", {"name": name, "subscriptionID": SUBSCRIPTION_ID})

    async def _event_loop(self) -> None:
        backoff = 5
        while True:
            try:
                await self._subscribe()
                backoff = 5
                while True:
                    res = await self.api.call(
                        "event/get", {"subscriptionID": SUBSCRIPTION_ID, "timeout": 30000}, timeout=45
                    )
                    for ev in (res or {}).get("events", []):
                        self._handle_event(ev)
            except asyncio.CancelledError:
                raise
            except Exception as err:  # connection lost: log in again and re-subscribe
                _LOGGER.warning("Event connection lost (%s), retrying in %ss", err, backoff)
                self.available = False
                self._notify()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 300)
                try:
                    await self.api.login()
                    self.available = True
                except DssError:
                    pass

    def _handle_event(self, ev: dict[str, Any]) -> None:
        name = ev.get("name")
        props = ev.get("properties") or {}
        if name == "stateChange":
            state_name = props.get("statename")
            if state_name and state_name.startswith("zone.") and state_name.endswith(".light"):
                try:
                    self.data.light_override.pop(int(state_name.split(".")[1]), None)
                except ValueError:
                    pass
            if state_name:
                self.data.states[state_name] = str(props.get("state") or props.get("value"))
        elif name == "callScene":
            try:
                zone, group, scene = int(props.get("zoneID", -1)), int(props.get("groupID", -1)), int(props.get("sceneID", -1))
            except ValueError:
                return
            if group in (0, GROUP_LIGHT):
                if zone == 0:
                    self.data.light_override.clear()
                else:
                    self.data.light_override.pop(zone, None)
            if zone == 0 and group == 0 and scene in (SCENE_ABSENT, SCENE_PRESENT):
                kind = "absent" if scene == SCENE_ABSENT else "present"
                self.data.last_event = kind
                self.hass.bus.async_fire(EVENT_NAME, {"type": kind, "origin": props.get("originDSUID")})
            elif zone in self.data.zones:
                self.hass.bus.async_fire(
                    EVENT_NAME,
                    {
                        "type": "zone_scene",
                        "zone": zone,
                        "zone_name": self.data.zones[zone],
                        "group": group,
                        "scene": scene,
                        "origin": props.get("originDSUID"),
                    },
                )
            if group in (0, GROUP_SHADE):
                for dev in self.data.devices.values():
                    if dev.dsuid in self.data.shade_pos and (zone in (0, dev.zone_id)):
                        self.hass.async_create_background_task(
                            self.refresh_device_later(dev.dsuid), f"digitalstrom_local_refresh_{dev.dsuid}"
                        )
        self._notify()

    def _notify(self) -> None:
        async_dispatcher_send(self.hass, f"{SIGNAL_UPDATE}_{self.entry_id}")

    # ---------- commands ----------

    async def zone_scene(self, zone: int, group: int, scene: int) -> None:
        await self.api.call("zone/callScene", {"id": zone, "groupID": group, "sceneNumber": scene})

    async def apartment_scene(self, scene: int) -> None:
        await self.api.call("apartment/callScene", {"sceneNumber": scene})

    async def device_scene(self, dsuid: str, scene: int) -> None:
        await self.api.call("device/callScene", {"dsid": self.data.devices[dsuid].dsid, "sceneNumber": scene})

    async def zone_brightness(self, zone: int, value: int) -> None:
        """Set brightness 0..255 for all lights of a zone."""
        for dev in self.data.devices.values():
            if dev.zone_id == zone and GROUP_LIGHT in dev.groups and dev.channel:
                await self.api.call("device/setValue", {"dsid": dev.dsid, "value": value})
        self.data.light_override[zone] = value
        self._notify()

    async def shade_position(self, dsuid: str, percent: int) -> None:
        value = round(percent * 65535 / 100)
        await self.api.call("device/setOutputValue", {"dsid": self.data.devices[dsuid].dsid, "offset": 2, "value": value})

    # ---------- helpers ----------

    def zone_light_on(self, zone: int) -> bool | None:
        if zone in self.data.light_override:
            return self.data.light_override[zone] > 0
        state = self.data.states.get(f"zone.{zone}.light")
        if state is None:
            return None
        return state in ("active", "1")

    def light_zones(self) -> list[int]:
        return sorted(
            {
                d.zone_id
                for d in self.data.devices.values()
                if GROUP_LIGHT in d.groups and d.channel and d.zone_id in self.data.zones
            }
        )
