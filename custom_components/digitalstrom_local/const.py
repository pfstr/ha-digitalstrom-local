"""Constants for the digitalSTROM Local integration."""

DOMAIN = "digitalstrom_local"
PLATFORMS = ["light", "cover", "binary_sensor", "sensor", "button", "scene"]

CONF_APP_TOKEN = "app_token"
APP_NAME = "Home Assistant"

SIGNAL_UPDATE = f"{DOMAIN}_update"
EVENT_NAME = f"{DOMAIN}_event"

GROUP_LIGHT = 1
GROUP_SHADE = 2
GROUP_JOKER = 8

SCENE_OFF = 0
SCENE_ON = 5
SCENE_SHADE_DOWN = 13
SCENE_SHADE_UP = 14
SCENE_SHADE_STOP = 15
SCENE_PRESENT = 71
SCENE_ABSENT = 72

# Standard scenes that should not show up as separate HA scenes
HIDDEN_SCENES = {0, 5, 13, 14, 15}

STATE_POLL_SECONDS = 60
BUS_POLL_SECONDS = 900  # direct output reads load the dS485 bus, keep them rare
