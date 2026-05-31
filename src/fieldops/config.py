from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    db_path: Path = PROJECT_ROOT / "data" / "fieldops.db"
    trace_path: Path = PROJECT_ROOT / "traces" / "runs.jsonl"
    gemini_api_key: str | None = None
    nass_api_key: str | None = None
    model: str = "gemini-2.5-flash"
    mcp_timeout_seconds: float = 8.0
    llm_timeout_seconds: float = 45.0
    max_tool_loops: int = 4


def get_settings() -> Settings:
    return Settings(
        db_path=Path(os.getenv("FIELDOPS_DB_PATH", PROJECT_ROOT / "data" / "fieldops.db")),
        trace_path=Path(os.getenv("FIELDOPS_TRACE_PATH", PROJECT_ROOT / "traces" / "runs.jsonl")),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        nass_api_key=os.getenv("NASS_API_KEY"),
        model=os.getenv("FIELDOPS_MODEL", "gemini-2.5-flash"),
    )

