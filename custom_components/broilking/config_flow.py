"""Config flow for the Broil King Smoker integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BroilKingClient, BroilKingError
from .const import DOMAIN


class BroilKingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Broil King Smoker."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = BroilKingClient(
                user_input[CONF_HOST], session, user_input.get(CONF_PASSWORD, "")
            )
            try:
                info = await client.async_get_info()
            except BroilKingError:
                errors["base"] = "cannot_connect"
            else:
                if info.get("app") != "Broil_King":
                    errors["base"] = "not_broilking"
                else:
                    device_id = info.get("id", user_input[CONF_HOST])
                    await self.async_set_unique_id(device_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title="Broil King Smoker", data=user_input
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PASSWORD, default=""): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
