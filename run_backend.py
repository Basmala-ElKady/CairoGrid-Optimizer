from __future__ import annotations

import asyncio
import sys


def _configure_windows_selector_policy_early() -> None:
    if sys.platform != "win32":
        return
    selector_policy_cls = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
    if selector_policy_cls is None:
        return
    asyncio.set_event_loop_policy(selector_policy_cls())


_configure_windows_selector_policy_early()

from Backend.api.launcher import (
    configure_asyncio_runtime,
    get_asyncio_policy_name,
    load_backend_server_settings,
    run_backend_server,
)


def main() -> int:
    runtime_policy = configure_asyncio_runtime()
    settings = load_backend_server_settings()
    policy_name = get_asyncio_policy_name()

    print(
        f"[backend] Starting CairoGrid API on http://{settings.host}:{settings.port} "
        f"(asyncio-policy={runtime_policy}, policy-class={policy_name}, log-level={settings.log_level})",
        flush=True,
    )
    run_backend_server(settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
