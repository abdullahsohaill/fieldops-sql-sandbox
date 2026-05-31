# FieldOps SQL Sandbox

FieldOps SQL Sandbox is a precision-agriculture analytics service for safely
answering natural-language questions over operational field data.

The project explores an asynchronous multi-agent architecture where LLM-native
tool calls are normalized into an internal tool protocol and routed to isolated
MCP servers. SQL generation is treated as untrusted output and must pass through
a deterministic read-only sandbox before execution.

## Goals

- Keep model-provider details out of the tool execution layer.
- Run SQL tools behind an MCP process boundary.
- Validate generated SQL deterministically before execution.
- Keep the local demo reproducible without requiring production data.

## Planned Architecture

```text
User question
  -> async orchestrator
  -> planner/schema/sql/summarizer agents
  -> provider-specific tool schema adapter
  -> internal tool call
  -> MCP router
  -> isolated SQL sandbox server
  -> read-only SQLite execution
```
