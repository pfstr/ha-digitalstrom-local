# Floor plan dashboard

A floor plan where rooms glow when their light is on and every lamp, speaker and sensor sits where it really is. It uses only the built-in `picture-elements` card.

## 1. Prepare the image

- Export or scan your floor plan as PNG, crop it to the apartment, about 800 px wide is enough.
- Copy it to `config/www/floorplan/plan.png`. Home Assistant serves it as `/local/floorplan/plan.png`.
- Copy [`assets/glow.svg`](assets/glow.svg) and [`assets/empty.svg`](assets/empty.svg) to the same folder. `glow.svg` is a soft yellow rectangle that stretches to any room size, `empty.svg` is fully transparent.

## 2. Measure the rooms

For each room note the centre and size **in percent of the image**: left, top, width, height. An image editor or a quick script on the pixel coordinates does the job.

## 3. The card

```yaml
type: picture-elements
image: /local/floorplan/plan.png?v=1
elements:
  # Room glow: shows glow.svg while the light is on; tap toggles, hold opens details
  - type: image
    entity: light.office_light
    image: /local/floorplan/empty.svg?v=1
    state_image:
      "on": /local/floorplan/glow.svg?v=1
      "off": /local/floorplan/empty.svg?v=1
    tap_action:
      action: toggle
    hold_action:
      action: more-info
    style:
      left: 46%
      top: 48%
      width: 21%
      height: 40%
  # Icons for lamps, speakers and sensors
  - type: state-icon
    entity: light.desk_lamp
    tap_action:
      action: toggle
    style:
      left: 39%
      top: 32%
      "--mdc-icon-size": 22px
      background: rgba(255,255,255,0.75)
      border-radius: 50%
      padding: 3px
  - type: state-icon
    entity: binary_sensor.office_motion
    style:
      left: 53%
      top: 32%
  # A state label, e.g. power consumption
  - type: state-label
    entity: sensor.apartment_power_consumption
    style:
      left: 15%
      top: 8%
```

## Hints

- `left`/`top` are the **centre** of the element.
- Bump `?v=1` to `?v=2` after changing an image, otherwise the browser keeps the old one.
- In a sections view give the card the full width: `grid_options: {columns: full}`.
- With the [Sonos start](../blueprints/script/digitalstrom_local/sonos_start.yaml) script a tap on a speaker icon can start music in that room:

```yaml
  - type: state-icon
    entity: media_player.office
    tap_action:
      action: perform-action
      perform_action: script.sonos_start
      data:
        speakers: [media_player.office]
    hold_action:
      action: more-info
```
