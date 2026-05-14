#!/usr/bin/env python3
"""Container healthcheck for Celery worker."""

from __future__ import annotations

import os
import subprocess
import sys

import redis


def has_worker_process() -> bool:
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue

        try:
            with open(f"/proc/{pid}/cmdline", "rb") as proc_cmd:
                parts = [part.decode("utf-8", errors="ignore") for part in proc_cmd.read().split(b"\x00") if part]
        except OSError:
            continue

        cmdline = " ".join(parts)
        if "celery" in cmdline and "worker_app.celery_app" in cmdline and " worker" in f" {cmdline}":
            return True

    return False


def has_redis_connectivity() -> bool:
    client = redis.Redis(host="redis", port=6379, db=0, socket_connect_timeout=3, socket_timeout=3)
    return bool(client.ping())


def celery_inspect_ok() -> bool:
    result = subprocess.run(
        ["celery", "-A", "worker_app.celery_app", "inspect", "ping", "-d", f"celery@{os.getenv('HOSTNAME', '')}"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    return result.returncode == 0 and "pong" in result.stdout


def main() -> int:
    if not has_worker_process():
        print("No celery worker process found", file=sys.stderr)
        return 1

    if not has_redis_connectivity():
        print("Redis broker is unreachable", file=sys.stderr)
        return 1

    if not celery_inspect_ok():
        print("Celery inspect ping failed", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
