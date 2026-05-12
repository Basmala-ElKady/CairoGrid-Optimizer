from __future__ import annotations

import http.server
import mimetypes
import os
from pathlib import Path
from urllib.parse import unquote, urlparse


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5500
FRONTEND_DIR = Path(__file__).resolve().parent / "Frontend"


class FrontendRequestHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def do_HEAD(self) -> None:
        self._serve(send_body=False)

    def do_GET(self) -> None:
        self._serve(send_body=True)

    def log_message(self, format: str, *args) -> None:
        return

    def _serve(self, send_body: bool) -> None:
        parsed = urlparse(self.path)
        relative_path = unquote(parsed.path or "/").lstrip("/")
        if not relative_path:
            relative_path = "index.html"

        candidate = (FRONTEND_DIR / relative_path).resolve()
        frontend_root = FRONTEND_DIR.resolve()
        if frontend_root not in candidate.parents and candidate != frontend_root:
            self.send_error(403, "Forbidden")
            return

        if candidate.is_dir():
            candidate = candidate / "index.html"

        if not candidate.exists() or not candidate.is_file():
            self.send_error(404, "File not found")
            return

        content_type, _ = mimetypes.guess_type(str(candidate))
        body = candidate.read_bytes()

        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        if send_body:
            self.wfile.write(body)


def main() -> int:
    host = os.getenv("CAIROGRID_FRONTEND_HOST", DEFAULT_HOST)
    port = int(os.getenv("CAIROGRID_FRONTEND_PORT", str(DEFAULT_PORT)))

    server = http.server.ThreadingHTTPServer((host, port), FrontendRequestHandler)

    print(
        f"[frontend] Serving static frontend from {FRONTEND_DIR} at http://{host}:{port}",
        flush=True,
    )

    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("[frontend] Shutdown requested, stopping static server...", flush=True)
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
