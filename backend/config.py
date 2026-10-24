"""Runtime configuration, read from environment variables (and an optional .env file).

Secrets (GEMINI_API_KEY) are only ever read here, on the server. They are never
sent to the browser, never written to the audit log and never put in an error message.
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
        mode = env.get("SAFEARENA_MODE", "local").strip().lower() or "local"
        if mode not in VALID_MODES:
            raise ValueError(f"SAFEARENA_MODE must be one of {VALID_MODES}, got {mode!r}")
        provider = env.get("LLM_PROVIDER", "mock").strip().lower() or "mock"
        if provider not in VALID_PROVIDERS:
            raise ValueError(f"LLM_PROVIDER must be one of {VALID_PROVIDERS}, got {provider!r}")
        model = env.get("GEMINI_MODEL", "").strip() or cls.gemini_model
        if not _MODEL_RE.match(model):
            raise ValueError("GEMINI_MODEL contains invalid characters")
        extra_hosts = tuple(h.strip().lower() for h in env.get("SAFEARENA_ALLOWED_HOSTS", "").split(",") if h.strip())
        data_dir = Path(env.get("SAFEARENA_DATA_DIR", "").strip() or (BASE_DIR / "data"))
        return cls(
            mode=mode,
            data_dir=data_dir,
            bind_host=env.get("BIND_HOST", "127.0.0.1").strip() or "127.0.0.1",
            bind_port=_int(env, "BIND_PORT", 8000, 1, 65535),
            red_service_url=env.get("RED_SERVICE_URL", cls.red_service_url).rstrip("/"),
            blue_service_url=env.get("BLUE_SERVICE_URL", cls.blue_service_url).rstrip("/"),
            llm_service_url=env.get("LLM_SERVICE_URL", cls.llm_service_url).rstrip("/"),
            llm_provider=provider,
            gemini_api_key=env.get("GEMINI_API_KEY", "").strip(),
            gemini_model=model,
            gemini_timeout=float(_int(env, "GEMINI_TIMEOUT_SECONDS", 15, 1, 120)),
            allowed_hosts=cls.allowed_hosts + extra_hosts,
            max_payload_chars=_int(env, "MAX_PAYLOAD_CHARS", 4000, 1, 20000),
            rate_limit_per_minute=_int(env, "RATE_LIMIT_PER_MINUTE", 120, 1, 100000),
        )
