from __future__ import annotations

import os
from pathlib import Path


def default_storage_root() -> Path:
    configured = os.environ.get("LABTOOLS_STORAGE_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".labtools").resolve()
