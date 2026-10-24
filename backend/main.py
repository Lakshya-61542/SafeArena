"""Entry point. ``python run_local.py`` (or ``python -m backend.main``) starts the gateway.

Binds to 127.0.0.1 by default. Inside Docker the container must listen on 0.0.0.0, and
docker-compose.yml publishes that port to the host's 127.0.0.1 only.
"""
from __future__ import annotations

import os
import sys

from backend.app import create_app
from backend.config import BASE_DIR, LOOPBACK_HOSTS, Config, load_dotenv


def validate_bind(config: Config, environ=os.environ) -> None:
    if config.bind_host not in LOOPBACK_HOSTS and config.mode != "docker" and environ.get("SAFEARENA_ALLOW_REMOTE_BIND") != "1":
        raise SystemExit(
            f"Refusing to bind to {config.bind_host!r}: SafeArena is localhost-only by default. "
            "Set SAFEARENA_ALLOW_REMOTE_BIND=1 only if you understand the exposure (the API has no authentication)."
        )


def build_app():
    load_dotenv(BASE_DIR / ".env")
    return create_app(Config.from_env())


def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    try:
        config = Config.from_env()
    except ValueError as exc:  # bad configuration: clear message, no traceback
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    validate_bind(config)
    app = create_app(config)
    print(f"SafeArena {config.mode} mode -> http://{config.bind_host}:{config.bind_port}  (Ctrl+C to stop)", flush=True)
    app.run(host=config.bind_host, port=config.bind_port, threaded=True, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
