"""Define the DenonavrEx component."""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

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
    for entry_config in config[DOMAIN]:
        hass.async_create_task(
            hass.helpers.discovery.async_load_platform(
                "switch", DOMAIN, entry_config, config
            )
        )
    return True
