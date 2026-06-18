"""Reference web server for the EEG visualization backend.

Uses only the Python standard library (no Flask/FastAPI required) so it
runs anywhere. It exposes the EEGBackend as JSON endpoints and serves the
browser front-end in web/index.html — demonstrating that the same backend
that powers the PyQt GUI can drive a web GUI.

Run under the pyllm environment:

    python web_server.py            # serves on http://127.0.0.1:8000
    python web_server.py 8080       # custom port

Endpoints:
    GET /api/options                         -> subjects, metrics, bands, defaults
    GET /api/layout                          -> head geometry + electrode positions
    GET /api/connectivity?subject=&metric=&band=
    GET /api/compare?a=&b=&metric=&band=     -> two-patient side-by-side payload
    GET /api/coherence_line?pre=&post=&band=&control=
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from config import load_config
from backend import EEGBackend

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

# One shared backend instance (loads the workbooks once at startup).
BACKEND = EEGBackend(load_config())


class Handler(BaseHTTPRequestHandler):

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except OSError:
            self.send_error(404, "Not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        def arg(name, default=None):
            values = query.get(name)
            return values[0] if values else default

        try:
            if path == "/" or path == "/index.html":
                self._send_file(os.path.join(WEB_DIR, "index.html"), "text/html")

            elif path == "/api/options":
                self._send_json(BACKEND.options())

            elif path == "/api/layout":
                self._send_json(BACKEND.head_layout())

            elif path == "/api/connectivity":
                self._send_json(BACKEND.connectivity(
                    arg("subject"), arg("metric"), arg("band")
                ))

            elif path == "/api/compare":
                self._send_json(BACKEND.compare(
                    arg("a"), arg("b"), arg("metric"), arg("band")
                ))

            elif path == "/api/coherence_line":
                self._send_json(BACKEND.coherence_line_plot(
                    arg("pre"), arg("post"), arg("band"), arg("control")
                ))

            else:
                self.send_error(404, "Not found")

        except Exception as exc:  # surface backend errors as JSON
            self._send_json({"error": str(exc)}, status=500)

    def log_message(self, fmt, *args):
        # Quieter logging: one concise line per request.
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    port = int(os.environ.get("PORT", 8000))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
