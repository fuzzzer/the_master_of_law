#!/usr/bin/env python3
"""Serve a built Flutter web app locally, with SPA fallback.

Used to put `build/web` behind `tailscale serve` for testing on a phone
without deploying. Firebase Hosting applies the rewrite in firebase.json in
production; this reproduces it locally so the two behave the same.

    python3 scripts/serve_web_local.py ../build/web 8080

Lives in the repo rather than a temp directory because a scratch copy gets
cleared out from under a long-running test session, and the first symptom is
the site 502-ing with no obvious cause.
"""
import functools
import http.server
import mimetypes
import os
import socketserver
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "build/web")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8080

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/wasm", ".wasm")


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # index.html and the service worker must never be cached: a stale copy
        # pins the browser to an old build after every rebuild, which looks
        # exactly like "my change did not take effect".
        if self.path.rstrip("/") in ("", "/index.html") or "service_worker" in self.path:
            self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def send_head(self):
        # Flutter's router owns paths like /cases and /auth, which exist only
        # in the client. Serving index.html for anything that is not a real
        # file lets a hard refresh or a shared link resolve. Files still win,
        # so assets are never shadowed by the fallback.
        rel = self.path.split("?")[0].split("#")[0].lstrip("/")
        if rel and not os.path.exists(os.path.join(ROOT, rel)):
            self.path = "/index.html"
        return super().send_head()

    def log_message(self, fmt, *args):
        sys.stderr.write("web %s\n" % (fmt % args))


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if not os.path.isdir(ROOT):
    sys.exit(f"no build at {ROOT} — run: flutter build web --release")

with Server(("127.0.0.1", PORT), functools.partial(Handler, directory=ROOT)) as httpd:
    print(f"serving {ROOT} on 127.0.0.1:{PORT}", flush=True)
    httpd.serve_forever()
