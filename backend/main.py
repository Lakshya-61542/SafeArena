"""Entry point for local development and the production WSGI factory."""
from __future__ import annotations

import os
import sys

from backend.app import create_app
from backend.config import BASE_DIR, LOOPBACK_HOSTS, Config, load_dotenv


def validate_bind(config: Config, environ=os.environ) -> None:
    if config.public_demo:
        # Config.from_env has already required credentials and a strict host allow-list.
        if config.bind_host != "0.0.0.0":
            raise SystemExit("Public demo mode must bind to 0.0.0.0")
        return
    if config.bind_host not in LOOPBACK_HOSTS and config.mode != "docker" and environ.get("SAFEARENA_ALLOW_REMOTE_BIND") != "1":
        raise SystemExit(
            f"Refusing to bind to {config.bind_host!r}: SafeArena is localhost-only by default. "
            "Set SAFEARENA_ALLOW_REMOTE_BIND=1 only if you understand the exposure (the local API has no authentication)."
        )


def build_app():
    """Gunicorn factory used by the Render public demo."""
    load_dotenv(BASE_DIR / ".env")
    config = Config.from_env()
    validate_bind(config)
    return create_app(config)


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
