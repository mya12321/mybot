"""Shared isolation for WebSocket tests that persist runtime state."""

import asyncio
from pathlib import Path

import pytest
import websockets
from websockets.exceptions import ConnectionClosed, InvalidMessage


@pytest.fixture(autouse=True)
def isolate_websocket_runtime_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep transcripts and other runtime files out of the active user data directory."""
    monkeypatch.setattr("nanobot.config.paths.get_data_dir", lambda: tmp_path)


# A just-booted test server may bind its socket before its accept loop is
# running, so the first handshake can be dropped before any status line is
# received (raises InvalidMessage/ConnectionClosed). Honest HTTP rejections
# (e.g. 401/403 via InvalidStatus) are NOT affected, so auth tests still see
# them. This wrapper mirrors websockets.connect's dual awaitable + async-CM
# shape, so one patch covers every call site in this package.
_CONNECT_RETRY_TIMEOUT = 2.0
_ORIGINAL_CONNECT = websockets.connect


class _ConnectWithRetry:
    def __init__(self, uri: str, **kwargs: object) -> None:
        self._uri = uri
        self._kwargs = kwargs
        self._ws = None

    async def _connect(self) -> object:
        deadline = asyncio.get_running_loop().time() + _CONNECT_RETRY_TIMEOUT
        while True:
            try:
                return await _ORIGINAL_CONNECT(self._uri, **self._kwargs)
            except (OSError, ConnectionClosed, InvalidMessage):
                if asyncio.get_running_loop().time() >= deadline:
                    raise
                await asyncio.sleep(0.01)

    def __await__(self):
        return self._connect().__await__()

    async def __aenter__(self):
        self._ws = await self._connect()
        return self._ws

    async def __aexit__(self, *exc: object) -> bool:
        await self._ws.close()
        return False


def _connect_with_retry(uri: str, **kwargs: object) -> _ConnectWithRetry:
    return _ConnectWithRetry(uri, **kwargs)


@pytest.fixture(autouse=True)
def retry_websocket_handshake_during_server_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retry handshakes that race the test server's accept loop."""
    monkeypatch.setattr(websockets, "connect", _connect_with_retry)

