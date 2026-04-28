"""
Waits until the database port is accepting TCP connections.

Usage:
    python wait_for_db.py [max_seconds]

Reads DATABASE_URL or DATABASE_URI from the environment to determine host:port.
Exits 0 when the port is open, exits 1 on timeout.
"""
import os
import socket
import sys
import time
from urllib.parse import urlparse


def main() -> None:
    max_wait = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    interval = 2

    url = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_URI", "")
    if not url:
        print("No DATABASE_URL configured — skipping DB wait.")
        sys.exit(0)

    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 3306

    waited = 0
    while waited < max_wait:
        try:
            with socket.create_connection((host, port), timeout=3):
                pass
            print(f"Database {host}:{port} is ready (waited {waited}s).")
            sys.exit(0)
        except OSError as exc:
            print(
                f"  Waiting for {host}:{port} ... ({waited}s / {max_wait}s): {exc}",
                file=sys.stderr,
            )
            time.sleep(interval)
            waited += interval

    print(
        f"\nERROR: Database {host}:{port} not available after {max_wait}s. Aborting.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
