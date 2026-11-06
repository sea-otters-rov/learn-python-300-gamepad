"""Serve the repo's pages on localhost, and tell open pages when a file is saved.

    .venv\\Scripts\\python.exe tools\\serve.py          # http://127.0.0.1:8770/

A page listens with `new EventSource("/changes")`; each saved file arrives as
one message holding its path from the repo root, e.g. "games/rov_sim.html".
The page decides what to do: re-run a Python file in place, or reload itself.

Two problems with plain `python -m http.server` that this exists to fix:

1. It sends no cache rules, so Chrome guesses, and a plain reload can keep a
   stale module (CLAUDE.md, "Browsers cache the sim's modules"). Everything
   here is sent with Cache-Control: no-store.
2. Nothing tells the page a file changed. Watching is polling: one stat per
   file every POLL_SECONDS, over WATCHED folders only -- .venv alone is
   thousands of files.

3. Chrome tries "localhost" as IPv6 (::1) first. A server on 127.0.0.1 alone
   made every request wait for the fallback: measured 310 ms per file against
   4 ms. So this listens on both loopback addresses.

Loopback only. It serves the whole repo, which is fine for a page nobody else
can reach and not fine for anything more.
"""

import http.server
import os
import socket
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8770
WATCHED = ("games", "spikes")
WATCHED_ENDINGS = (".html", ".js", ".py", ".css")
POLL_SECONDS = 0.25
# A comment line every so often, so a page whose server died notices and
# EventSource reconnects by itself when it comes back.
KEEPALIVE_SECONDS = 15

changes = threading.Condition()
change_count = 0
changed_paths = []  # every change since start; each listener remembers its place


def snapshot():
    """Modified time of every watched file, keyed by its path from ROOT."""
    times = {}
    for folder in WATCHED:
        for here, _dirs, files in os.walk(os.path.join(ROOT, folder)):
            for name in files:
                if not name.endswith(WATCHED_ENDINGS):
                    continue
                path = os.path.join(here, name)
                key = os.path.relpath(path, ROOT).replace(os.sep, "/")
                try:
                    times[key] = os.stat(path).st_mtime_ns
                except OSError:
                    pass  # deleted between walk and stat
    return times


def watch():
    global change_count
    before = snapshot()
    while True:
        time.sleep(POLL_SECONDS)
        after = snapshot()
        saved = [key for key, mtime in after.items() if before.get(key) != mtime]
        before = after
        if not saved:
            continue
        with changes:
            changed_paths.extend(saved)
            change_count += len(saved)
            changes.notify_all()
        for key in saved:
            print(f"[serve] saved {key}")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path == "/changes":
            self.stream_changes()
        else:
            super().do_GET()

    def stream_changes(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        with changes:
            seen = change_count
        try:
            while True:
                with changes:
                    changes.wait_for(
                        lambda: change_count > seen, timeout=KEEPALIVE_SECONDS
                    )
                    fresh = changed_paths[seen:change_count]
                    seen = change_count
                if fresh:
                    for key in fresh:
                        self.wfile.write(f"data: {key}\n\n".encode())
                else:
                    self.wfile.write(b": keepalive\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # the page closed or reloaded

    def log_message(self, format, *args):
        pass  # one line per request drowns out the "saved" lines


class IPv6Server(http.server.ThreadingHTTPServer):
    address_family = socket.AF_INET6


def main():
    threading.Thread(target=watch, daemon=True).start()
    ipv4 = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    ipv6 = IPv6Server(("::1", PORT), Handler)
    for server in (ipv4, ipv6):
        server.daemon_threads = True
    threading.Thread(target=ipv6.serve_forever, daemon=True).start()
    print(f"[serve] http://localhost:{PORT}/  watching {', '.join(WATCHED)}")
    try:
        ipv4.serve_forever()
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
