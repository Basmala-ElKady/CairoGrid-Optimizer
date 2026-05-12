import asyncio

from Backend.api import launcher


def test_create_backend_event_loop_uses_selector_on_windows(monkeypatch):
    monkeypatch.setattr(launcher.sys, "platform", "win32")

    loop = launcher.create_backend_event_loop()
    try:
        assert isinstance(loop, asyncio.SelectorEventLoop)
    finally:
        loop.close()


def test_backend_loop_factory_path_points_to_local_factory():
    assert launcher.BACKEND_LOOP_FACTORY == "Backend.api.launcher:create_backend_event_loop"
