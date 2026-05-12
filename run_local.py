from __future__ import annotations

import atexit
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from http.client import HTTPException
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


BACKEND_URL = "http://127.0.0.1:8000/api/health"
FRONTEND_URL = "http://127.0.0.1:5500/"
ROOT = Path(__file__).resolve().parent


@dataclass
class ManagedProcess:
    name: str
    command: list[str]
    cwd: Path
    ready_url: str | None = None
    process: subprocess.Popen[str] | None = None
    reader: threading.Thread | None = None


def stream_process_output(managed: ManagedProcess) -> None:
    assert managed.process is not None
    assert managed.process.stdout is not None
    for line in managed.process.stdout:
        print(f"[{managed.name}] {line.rstrip()}", flush=True)


def start_process(managed: ManagedProcess) -> None:
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    process = subprocess.Popen(
        managed.command,
        cwd=str(managed.cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        bufsize=1,
        creationflags=creationflags,
    )
    managed.process = process
    managed.reader = threading.Thread(target=stream_process_output, args=(managed,), daemon=True)
    managed.reader.start()


def wait_for_url(managed: ManagedProcess, url: str, timeout_seconds: float, label: str) -> None:
    deadline = time.time() + timeout_seconds
    last_error = "service did not respond"
    while time.time() < deadline:
        process = managed.process
        if process is not None:
            exit_code = process.poll()
            if exit_code is not None:
                raise RuntimeError(f"{label} process exited before becoming ready (code {exit_code}).")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if 200 <= response.status < 500:
                    print(f"[runner] {label} is ready at {url}", flush=True)
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionError, ConnectionResetError, HTTPException, OSError) as error:
            last_error = str(error)
            time.sleep(0.5)
    raise RuntimeError(f"{label} failed to start at {url}: {last_error}")


def stop_process(managed: ManagedProcess, grace_seconds: float = 8.0) -> None:
    process = managed.process
    if process is None or process.poll() is not None:
        return

    print(f"[runner] Stopping {managed.name}...", flush=True)
    try:
        if sys.platform == "win32":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.send_signal(signal.SIGINT)
    except Exception:
        process.terminate()

    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        print(f"[runner] {managed.name} did not stop in time; terminating forcefully.", flush=True)
        process.kill()
        process.wait(timeout=5)


def stop_all(processes: list[ManagedProcess]) -> None:
    for managed in reversed(processes):
        stop_process(managed)


def main() -> int:
    browser_opened = False
    processes = [
        ManagedProcess(
            name="backend",
            command=[sys.executable, "-u", "run_backend.py"],
            cwd=ROOT,
            ready_url=BACKEND_URL,
        ),
        ManagedProcess(
            name="frontend",
            command=[sys.executable, "-u", "run_frontend.py"],
            cwd=ROOT,
            ready_url=FRONTEND_URL,
        ),
    ]

    atexit.register(stop_all, processes)

    try:
        backend = processes[0]
        frontend = processes[1]

        start_process(backend)
        wait_for_url(backend, BACKEND_URL, timeout_seconds=30, label="Backend")

        start_process(frontend)
        wait_for_url(frontend, FRONTEND_URL, timeout_seconds=20, label="Frontend")

        if not browser_opened:
            webbrowser.open(FRONTEND_URL, new=2)
            browser_opened = True

        print("[runner] CairoGrid local stack is ready.", flush=True)
        print("[runner] Backend:  http://127.0.0.1:8000", flush=True)
        print("[runner] Frontend: http://127.0.0.1:5500", flush=True)
        print("[runner] Browser opened at http://127.0.0.1:5500", flush=True)
        print("[runner] Press Ctrl+C once to stop both services cleanly.", flush=True)

        while True:
            for managed in processes:
                assert managed.process is not None
                exit_code = managed.process.poll()
                if exit_code is not None:
                    raise RuntimeError(f"{managed.name} exited unexpectedly with code {exit_code}.")
            time.sleep(0.75)

    except KeyboardInterrupt:
        print("[runner] Shutdown requested.", flush=True)
        return 0
    finally:
        stop_all(processes)


if __name__ == "__main__":
    raise SystemExit(main())
