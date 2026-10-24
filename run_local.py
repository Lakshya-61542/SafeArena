"""Start SafeArena in local mode on http://127.0.0.1:8000 (no Docker needed)."""
import os

os.environ.setdefault("SAFEARENA_MODE", "local")

from backend.main import main  # noqa: E402

if __name__ == "__main__":
    main()
