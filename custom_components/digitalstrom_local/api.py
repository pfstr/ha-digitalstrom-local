"""Minimal client for the JSON API of the digitalSTROM server."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class DssError(Exception):
    """Error returned by the dSS."""


class DssAuthError(DssError):
    """Login failed or session expired."""


class DssApi:
    def __init__(self, session: aiohttp.ClientSession, host: str, port: int, app_token: str | None = None) -> None:
        self._session = session
        self._base = f"https://{host}:{port}/json"
        self.app_token = app_token
        self._token: str | None = None
        self._login_lock = asyncio.Lock()

    async def _raw(self, path: str, params: dict[str, Any] | None = None, timeout: float = 30) -> Any:
        try:
            async with self._session.get(
                f"{self._base}/{path}",
                params={k: str(v) for k, v in (params or {}).items()},
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                data = await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise DssError(f"{path}: {err}") from err
        if not data.get("ok"):
            msg = str(data.get("message", ""))
            if any(s in msg.lower() for s in ("not logged in", "authentication", "session", "token")):
                raise DssAuthError(msg)
            raise DssError(f"{path}: {msg}")
        return data.get("result")

    async def request_app_token(self, name: str) -> str:
        result = await self._raw("system/requestApplicationToken", {"applicationName": name})
        return result["applicationToken"]

    async def login(self) -> None:
        async with self._login_lock:
            result = await self._raw("system/loginApplication", {"loginToken": self.app_token})
            self._token = result["token"]

    async def call(self, path: str, params: dict[str, Any] | None = None, timeout: float = 30) -> Any:
        if self._token is None:
            await self.login()
        try:
            return await self._raw(path, {**(params or {}), "token": self._token}, timeout)
        except DssAuthError:
            _LOGGER.debug("Session expired, logging in again")
            await self.login()
            return await self._raw(path, {**(params or {}), "token": self._token}, timeout)
