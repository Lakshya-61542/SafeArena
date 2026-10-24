"""Runtime configuration, read from environment variables (and an optional .env file).

Secrets are held only in server-side configuration and excluded from repr output.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, MutableMapping

BASE_DIR = Path(__file__).resolve().parent.parent
VALID_MODES = ("local", "docker")
VALID_PROVIDERS = ("mock", "gemini")
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")
_MODEL_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_HOST_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)"
    r"(?:\.(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?))*$"
)


def load_dotenv(path: Path, environ: MutableMapping[str, str] | None = None) -> None:
    """Minimal .env loader: KEY=VALUE per line, '#' comments, existing env vars win."""
    environ = os.environ if environ is None else environ
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and key not in environ:
            environ[key] = value


def _int(environ: Mapping[str, str], name: str, default: int, lo: int, hi: int) -> int:
    raw = environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from None
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be between {lo} and {hi}")
    return value


@dataclass(frozen=True)
class Config:
    mode: str = "local"
    data_dir: Path = BASE_DIR / "data"
    bind_host: str = "127.0.0.1"
    bind_port: int = 8000
    red_service_url: str = "http://red-service:8101"
    blue_service_url: str = "http://blue-service:8102"
    llm_service_url: str = "http://llm-service:8103"
    llm_provider: str = "mock"
    gemini_api_key: str = field(default="", repr=False)
    public_demo: bool = False
    public_docker_demo: bool = False
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout: float = 15.0
    allowed_hosts: tuple = ("localhost", "127.0.0.1", "::1")
    max_payload_chars: int = 4000
    rate_limit_per_minute: int = 120
    static_dir: Path = BASE_DIR / "static"

    @property
    def audit_path(self) -> Path:
        return self.data_dir / "audit_log.jsonl"

    @property
    def events_path(self) -> Path:
        return self.data_dir / "events.db"

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Config":
        env = os.environ if environ is None else environ
        public_raw = env.get("SAFEARENA_PUBLIC_DEMO", "0").strip()
        public_docker_raw = env.get("SAFEARENA_PUBLIC_DOCKER_DEMO", "0").strip()
        if public_raw not in ("0", "1"):
            raise ValueError("SAFEARENA_PUBLIC_DEMO must be 0 or 1")
        if public_docker_raw not in ("0", "1"):
            raise ValueError("SAFEARENA_PUBLIC_DOCKER_DEMO must be 0 or 1")
        public_demo = public_raw == "1"
        public_docker_demo = public_docker_raw == "1"
        if public_demo and public_docker_demo:
            raise ValueError("SAFEARENA_PUBLIC_DEMO and SAFEARENA_PUBLIC_DOCKER_DEMO cannot both be enabled")

        public_mode = public_demo or public_docker_demo
        mode_raw = env.get("SAFEARENA_MODE", "local").strip().lower() or "local"
        if mode_raw not in VALID_MODES:
            raise ValueError(f"SAFEARENA_MODE must be one of {VALID_MODES}, got {mode_raw!r}")
        mode = "local" if public_demo else ("docker" if public_docker_demo else mode_raw)

        provider_raw = env.get("LLM_PROVIDER", "mock").strip().lower() or "mock"
        if not public_mode and provider_raw not in VALID_PROVIDERS:
            raise ValueError(f"LLM_PROVIDER must be one of {VALID_PROVIDERS}, got {provider_raw!r}")
        provider = "mock" if public_mode else provider_raw

        model = cls.gemini_model if public_mode else (env.get("GEMINI_MODEL", "").strip() or cls.gemini_model)
        if not _MODEL_RE.match(model):
            raise ValueError("GEMINI_MODEL contains invalid characters")

        hosts_raw = env.get("SAFEARENA_ALLOWED_HOSTS", "").strip()
        if public_demo and not hosts_raw:
            # Render supplies this exact hostname for each web service.
            hosts_raw = env.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
        extra_hosts = tuple(h.strip().lower() for h in hosts_raw.split(",") if h.strip())
        if public_mode:
            if not extra_hosts:
                if public_demo:
                    raise ValueError(
                        "Set SAFEARENA_ALLOWED_HOSTS to the exact public hostname, "
                        "or deploy on Render where RENDER_EXTERNAL_HOSTNAME is supplied"
                    )
                raise ValueError("Set SAFEARENA_ALLOWED_HOSTS to the exact public Docker demo hostname")
            if any(host == "*" or not _HOST_RE.fullmatch(host) for host in extra_hosts):
                raise ValueError("Public demo hosts must be exact hostnames without schemes, ports, paths, or wildcards")

        bind_host = env.get("BIND_HOST", "0.0.0.0" if public_mode else "127.0.0.1").strip()
        bind_host = bind_host or ("0.0.0.0" if public_mode else "127.0.0.1")
        if public_mode and bind_host != "0.0.0.0":
            raise ValueError("BIND_HOST must be 0.0.0.0 in public demo mode")
        platform_port = _int(env, "PORT", 8000, 1, 65535)
        bind_port = _int(env, "BIND_PORT", platform_port, 1, 65535)

        data_default = Path("/tmp/safearena-data") if public_demo else (BASE_DIR / "data")
        data_dir = Path(env.get("SAFEARENA_DATA_DIR", "").strip() or data_default)
        gemini_key = "" if public_mode else env.get("GEMINI_API_KEY", "").strip()
        timeout = 15 if public_mode else _int(env, "GEMINI_TIMEOUT_SECONDS", 15, 1, 120)
        allowed_hosts = extra_hosts if public_demo else cls.allowed_hosts + extra_hosts

        return cls(
            mode=mode,
            data_dir=data_dir,
            bind_host=bind_host,
            bind_port=bind_port,
            red_service_url=env.get("RED_SERVICE_URL", cls.red_service_url).rstrip("/"),
            blue_service_url=env.get("BLUE_SERVICE_URL", cls.blue_service_url).rstrip("/"),
            llm_service_url=env.get("LLM_SERVICE_URL", cls.llm_service_url).rstrip("/"),
            llm_provider=provider,
            gemini_api_key=gemini_key,
            public_demo=public_demo,
            public_docker_demo=public_docker_demo,
            gemini_model=model,
            gemini_timeout=float(timeout),
            allowed_hosts=allowed_hosts,
            max_payload_chars=_int(env, "MAX_PAYLOAD_CHARS", 4000, 1, 20000),
            rate_limit_per_minute=_int(env, "RATE_LIMIT_PER_MINUTE", 60 if public_mode else 120, 1, 100000),
        )
