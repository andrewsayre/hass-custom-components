"""Define the DenonavrEx component."""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_HOSTS, CONF_NAME, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .avrclient import AvrClient

DOMAIN = "denonavrex"

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
        host = entry_config[CONF_HOST]
        client = AvrClient(host, entry_config[CONF_PORT], async_get_clientsession(hass))
        await client.update()

        hass.data[DOMAIN][CONF_HOSTS][host] = client

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
