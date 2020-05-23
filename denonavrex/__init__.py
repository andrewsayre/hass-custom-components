"""Define the DenonavrEx component."""
import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_HOSTS, CONF_NAME, CONF_PORT
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .avrclient import AvrClient

DOMAIN = "denonavrex"
SIGNAL_UPDATED = "denonavrex_host_updated"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Required(CONF_NAME): cv.string,
                        vol.Required(CONF_HOST): cv.string,
                        vol.Optional(CONF_PORT, default=8080): cv.port,
                    }
                )
            ],
        )
    },
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistantType, config: ConfigType):
    """Setup the denonavrEx platform."""
    hass.data.setdefault(DOMAIN, {CONF_HOSTS: {}})

    for entry_config in config[DOMAIN]:
        manager = AvrManager(
            hass,
            entry_config[CONF_HOST],
            entry_config[CONF_PORT],
            entry_config[CONF_NAME],
        )
        await manager.update()
        hass.data[DOMAIN][CONF_HOSTS][manager.host] = manager

        hass.helpers.event.async_track_time_interval(
            manager.update, DEFAULT_SCAN_INTERVAL
        )

        hass.async_create_task(
            hass.helpers.discovery.async_load_platform(
                "media_player", DOMAIN, entry_config, config
            )
        )
        hass.async_create_task(
            hass.helpers.discovery.async_load_platform(
                "switch", DOMAIN, entry_config, config
            )
        )
    return True


class AvrManager:
    """Define the Avr manager class."""

    def __init__(self, hass: HomeAssistantType, host: str, port: int, name: str):
        self._hass = hass
        self._client = AvrClient(
            host, port, hass.helpers.aiohttp_client.async_get_clientsession()
        )

    @property
    def client(self):
        """Get the AvrClient."""
        return self._client

    @property
    def host(self):
        """Get the host."""
        return self._client.host

    async def update(self, utcnow=None):
        """Update the Avr data and signal platforms."""
        await self._client.update()
        self._hass.helpers.dispatcher.async_dispatcher_send(
            SIGNAL_UPDATED, self._client.host
        )
