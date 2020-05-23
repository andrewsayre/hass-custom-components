"""A media player representation of Denon and Maranz comaptible AVRs."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.const import CONF_HOST, CONF_HOSTS, CONF_NAME

from . import DOMAIN
from .avrclient import AvrClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the media player platform."""
    client = hass.data[DOMAIN][CONF_HOSTS][discovery_info[CONF_HOST]]
    name = discovery_info[CONF_NAME]
    async_add_entities([DenonAvrMediaPlayer(client, name)], True)


class DenonAvrMediaPlayer(MediaPlayerEntity):
    """Represents the main AVR media player entity."""

    def __init__(self, client: AvrClient, name: str):
        """Init the media player."""
        self._client = client
        self._name = name

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return device specific state attributes."""
        return {
            "all_zone_stereo_enabled": self._client.all_zone_stereo_enabled,
            "all_zone_stereo_zones": self._client.all_zone_stereo_zones,
        }
