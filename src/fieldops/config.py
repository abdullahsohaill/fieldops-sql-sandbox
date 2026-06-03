from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class Settings:
    db_path: Path = PROJECT_ROOT / "data" / "fieldops.db"
    trace_path: Path = PROJECT_ROOT / "traces" / "runs.jsonl"
    gemini_api_key: str | None = None
    nass_api_key: str | None = None
    model: str = "gemini-3.1-flash-lite"
    mcp_timeout_seconds: float = 8.0
    llm_timeout_seconds: float = 45.0
    max_tool_loops: int = 4


def load_env_file(env_file: Path = ENV_FILE) -> None:
    if not env_file.exists():
        return

    for raw_line in env_file.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_settings() -> Settings:
    load_env_file()
    return Settings(
        db_path=Path(os.getenv("FIELDOPS_DB_PATH", PROJECT_ROOT / "data" / "fieldops.db")),
        trace_path=Path(os.getenv("FIELDOPS_TRACE_PATH", PROJECT_ROOT / "traces" / "runs.jsonl")),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        nass_api_key=os.getenv("NASS_API_KEY"),
        model=os.getenv("FIELDOPS_MODEL", "gemini-3.1-flash-lite"),
    )
