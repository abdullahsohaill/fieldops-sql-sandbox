from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


JsonSchema = dict[str, Any]
ToolProvider = Literal["gemini", "openai"]


@dataclass(frozen=True)
class InternalToolSpec:
    name: str
    description: str
    input_schema: JsonSchema
    server_name: str
    timeout_seconds: float = 8.0
    read_only: bool = True


@dataclass(frozen=True)
class InternalToolCall:
    call_id: str
    provider: ToolProvider
    name: str
    arguments: dict[str, Any]
    server_name: str


@dataclass(frozen=True)
class InternalToolResult:
    call_id: str
    ok: bool
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    duration_ms: float | None = None

    @classmethod
    def success(
        cls,
        call_id: str,
        result: dict[str, Any],
        duration_ms: float | None = None,
    ) -> InternalToolResult:
        return cls(call_id=call_id, ok=True, result=result, duration_ms=duration_ms)

    @classmethod
    def failure(
        cls,
        call_id: str,
        code: str,
        message: str,
        duration_ms: float | None = None,
    ) -> InternalToolResult:
        return cls(
            call_id=call_id,
            ok=False,
            error={"code": code, "message": message},
            duration_ms=duration_ms,
        )

    def payload(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True)
class ToolCatalog:
    tools: tuple[InternalToolSpec, ...] = field(default_factory=tuple)

    def by_name(self) -> dict[str, InternalToolSpec]:
        return {tool.name: tool for tool in self.tools}

    def resolve(self, name: str) -> InternalToolSpec:
        try:
            return self.by_name()[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def subset(self, *tool_names: str) -> ToolCatalog:
        selected = tuple(self.resolve(name) for name in tool_names)
        return ToolCatalog(selected)
