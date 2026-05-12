from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_LOG_LEVEL = "info"
BACKEND_LOOP_FACTORY = "Backend.api.launcher:create_backend_event_loop"


@dataclass(frozen=True)
class BackendServerSettings:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    log_level: str = DEFAULT_LOG_LEVEL


def configure_asyncio_runtime() -> str:
    """
    Apply a stable asyncio policy for the current platform.

    On Windows, Uvicorn can intermittently hit WinError 10014 when using the
    default Proactor-based loop. The selector policy avoids that socket accept
    failure while remaining fully compatible with FastAPI/Uvicorn.
    """

    if sys.platform != "win32":
        return "default"

    selector_policy_cls = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
    if selector_policy_cls is None:
        return "default"

    current_policy = asyncio.get_event_loop_policy()
    if isinstance(current_policy, selector_policy_cls):
        return "windows-selector"

    asyncio.set_event_loop_policy(selector_policy_cls())
    return "windows-selector"


def get_asyncio_policy_name() -> str:
    return type(asyncio.get_event_loop_policy()).__name__


def create_backend_event_loop() -> asyncio.AbstractEventLoop:
    """
    Return the event loop implementation used by the local backend server.

    Uvicorn 0.46+ explicitly picks a Proactor loop on Windows for its default
    asyncio runner, which can reintroduce WinError 10014 during socket accept.
    Providing our own loop factory keeps backend startup stable across Uvicorn
    upgrades instead of depending on its internal platform defaults.
    """

    if sys.platform == "win32":
        return asyncio.SelectorEventLoop()
    return asyncio.new_event_loop()


def load_backend_server_settings() -> BackendServerSettings:
    return BackendServerSettings(
        host=os.getenv("CAIROGRID_API_HOST", DEFAULT_HOST),
        port=int(os.getenv("CAIROGRID_API_PORT", str(DEFAULT_PORT))),
        log_level=os.getenv("CAIROGRID_API_LOG_LEVEL", DEFAULT_LOG_LEVEL).lower(),
    )


def run_backend_server(settings: BackendServerSettings | None = None) -> None:
    configure_asyncio_runtime()
    active_settings = settings or load_backend_server_settings()

    import uvicorn
    from Backend.api.server import app as backend_app

    config = uvicorn.Config(
        backend_app,
        host=active_settings.host,
        port=active_settings.port,
        reload=False,
        loop=BACKEND_LOOP_FACTORY,
        log_level=active_settings.log_level,
        access_log=True,
        lifespan="on",
        server_header=False,
        proxy_headers=False,
    )
    server = uvicorn.Server(config)
    server.run()
