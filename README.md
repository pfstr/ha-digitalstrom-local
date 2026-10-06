# digitalSTROM Local for Home Assistant

A small, local and event-driven Home Assistant integration for the **digitalSTROM server (dSS)**, plus a set of blueprints: motion lights that leave manual light alone, a shower mode, "tap four times to start music" and automatic leave/arrive by phone presence.

[Deutsche Kurzfassung](README.de.md)

## Why another digitalSTROM integration?

- **No password stored.** Setup requests an app token from the dSS. You approve it once in the dSS Configurator. Home Assistant never sees your dSS password.
- **Event-driven.** One long-poll connection to the dSS event API. Wall buttons, scenes and the "Leave"/"Arrive" activities show up in Home Assistant immediately.
- **Gentle on the dS485 bus.** State comes from the dSS cache and from events. Direct output reads (blind positions, joker outputs) happen only every 15 minutes and after a command.
- **Events for your automations.** Every zone scene and every Leave/Arrive is fired as a Home Assistant event, so "double tap" or "four taps" on an ordinary light button can trigger anything.
- **Local only.** No cloud, no account, no telemetry.

## Features

| Platform | What you get |
| --- | --- |
| `light` | One light per zone (room). On/off via the same zone scenes as the wall buttons. Brightness for dimmed outputs; switched outputs (e.g. fluorescent tubes) are on/off only. |
| `cover` | Blinds with open, close, stop and position. |
| `scene` | All scenes you named in the dSS Configurator (e.g. "TV", "Dinner"). |
| `button` | **Leave** (absent, scene 72) and **Arrive** (present, scene 71). |
| `binary_sensor` | Apartment presence, wind alarm, motion detectors and joker outputs (e.g. ventilation flaps). |
| `sensor` | Total power consumption of the apartment. |

Each zone becomes a Home Assistant device with a suggested area of the same name.

### Events

The integration fires `digitalstrom_local_event`:

```yaml
# Leave / Arrive (apartment scene 72 / 71)
type: absent        # or: present
origin: <dSUID of the button>

# Any scene called in a zone (wall button, app, Configurator)
type: zone_scene
zone: 4
zone_name: Office
group: 1            # 1 = light, 2 = blinds, 8 = joker
scene: 19           # 0 = off, 5 = on, 17/18/19 = double/triple/four taps
origin: <dSUID of the button>
```

## Requirements

- digitalSTROM server dSS20 or newer, firmware 1.19.x. Tested with dSS v1.54.0 (1.19.13) and dSM12 meters.
- Home Assistant 2024.10 or newer.
- The dSS reachable on your network (HTTPS, port 8080). The self-signed certificate of the dSS is accepted.

## Installation

### HACS (custom repository)

1. HACS > three dots > **Custom repositories** > add `https://github.com/pfstr/ha-digitalstrom-local`, type **Integration**.
2. Install **digitalSTROM Local** and restart Home Assistant.

### Manual

Copy `custom_components/digitalstrom_local` into your `config/custom_components` folder and restart Home Assistant.

## Setup

1. **Settings > Devices & services > Add integration > digitalSTROM Local.**
2. Enter the address of your dSS (default `dss.local`, port `8080`) and submit. The dSS creates an app token named **Home Assistant**; the dialog shows its last eight characters.
3. Open the dSS Configurator (`https://dss.local:8080`), go to **System > Access Authorization**, tick the token with the matching ending and click **Apply**.
4. Back in Home Assistant, submit the dialog.

You can revoke the token in the Configurator at any time.

## Blueprints

| Blueprint | What it does | Import |
| --- | --- | --- |
| [Motion light](blueprints/automation/digitalstrom_local/motion_light.yaml) | On with motion, off after a delay. Leaves manually switched light alone, survives restarts, optional darkness threshold, time window, night brightness and a "keep on" helper. Works with any light and motion sensor. | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fpfstr%2Fha-digitalstrom-local%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fdigitalstrom_local%2Fmotion_light.yaml) |
| [Shower mode](blueprints/automation/digitalstrom_local/shower_mode.yaml) | Double tap on the bathroom button keeps the light on while you shower. The first motion after a grace period ends it, a maximum duration ends it anyway. | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fpfstr%2Fha-digitalstrom-local%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fdigitalstrom_local%2Fshower_mode.yaml) |
| [Multi-tap action](blueprints/automation/digitalstrom_local/multi_tap_action.yaml) | Four taps (or two/three) on any light button run your actions, e.g. start music in that room. Optionally switches the room light off again. | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fpfstr%2Fha-digitalstrom-local%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fdigitalstrom_local%2Fmulti_tap_action.yaml) |
| [Leave / arrive by presence](blueprints/automation/digitalstrom_local/presence_leave_arrive.yaml) | Triggers Leave when everybody is gone and nobody pressed the button; Arrive plus a welcome light when someone comes home. | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fpfstr%2Fha-digitalstrom-local%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fdigitalstrom_local%2Fpresence_leave_arrive.yaml) |
| [Sonos start](blueprints/script/digitalstrom_local/sonos_start.yaml) (script) | Joins a group that is already playing, otherwise resumes or plays a fallback station, always at the same start volume. | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fpfstr%2Fha-digitalstrom-local%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fdigitalstrom_local%2Fsonos_start.yaml) |

### Tips

- **Four taps without flicker at the end:** in the Configurator set scene 19 (Preset 4) of every light to *do not change output*. digitalSTROM still steps through Preset 1 to 3 while you tap; the multi-tap blueprint switches the light off afterwards.
- **Pause music and switch off other lights on Leave:** a plain automation on `digitalstrom_local_event` with `type: absent` that calls `media_player.media_pause` and `light.turn_off` for lights of other integrations (e.g. `{{ integration_entities('hue') | select('match', 'light\.') | list }}`). digitalSTROM switches its own lights off by itself.
- **Floor plan dashboard:** see [docs/floor-plan-dashboard.md](docs/floor-plan-dashboard.md).

## Limitations

- After a zone scene the dSS does not report brightness, so the light shows full brightness until you set a value from Home Assistant.
- Blind positions are read from the bus about a minute after a move and every 15 minutes, not continuously.
- Only zone lights, blinds, joker outputs, motion states and apartment scenes are covered. No heating, no per-device lights, no sensors of individual terminal blocks.
- Tested with a single dSS installation. Feedback and pull requests are welcome.

## Disclaimer

Not affiliated with or endorsed by digitalSTROM AG. digitalSTROM is a trademark of its owner.

## License

[MIT](LICENSE)
