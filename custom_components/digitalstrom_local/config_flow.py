"""Setup: enter the server, request an app token, approve it in the dSS Configurator."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import DssApi, DssError
from .const import APP_NAME, CONF_APP_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class DigitalstromLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._port: int = 8080
        self._token: str | None = None

    def _api(self) -> DssApi:
        return DssApi(async_create_clientsession(self.hass, verify_ssl=False), self._host, self._port, self._token)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._host = user_input[CONF_HOST].strip()
            self._port = int(user_input[CONF_PORT])
            await self.async_set_unique_id(self._host)
            self._abort_if_unique_id_configured()
            try:
                self._token = await self._api().request_app_token(APP_NAME)
                _LOGGER.info("App token requested: ...%s", self._token[-8:])
            except DssError as err:
                _LOGGER.warning("Could not request app token: %s", err)
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_approve()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default="dss.local"): str,
                    vol.Required(CONF_PORT, default=8080): int,
                }
            ),
            errors=errors,
        )

    async def async_step_approve(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self._api().login()
            except DssError as err:
                _LOGGER.warning("Login with app token ...%s failed: %s", (self._token or "")[-8:], err)
                errors["base"] = "not_approved"
            else:
                return self.async_create_entry(
                    title=f"digitalSTROM ({self._host})",
                    data={CONF_HOST: self._host, CONF_PORT: self._port, CONF_APP_TOKEN: self._token},
                )
        return self.async_show_form(
            step_id="approve",
            data_schema=vol.Schema({}),
            description_placeholders={"app": f"{APP_NAME} (…{(self._token or '')[-8:]})", "url": f"https://{self._host}:{self._port}"},
            errors=errors,
        )
