# Architecture Notes

## Core Flow

The system is organized around one idea: model providers should not know how
tools are implemented, and tools should not trust LLM output.

Flow:

1. A user asks a natural-language FieldOps question.
2. The orchestrator runs a planner agent to frame the task.
3. A schema agent retrieves database context through the metadata MCP server.
4. A SQL agent produces a normalized tool call targeting
   `execute_read_only_sql`.
5. The async MCP router resolves the target server and dispatches the call over
   stdio.
6. The SQL sandbox MCP server validates and executes the query under read-only
   controls.
7. The summarizer agent turns the structured result into a human answer.

## Why The Internal Tool Protocol Exists

The assignment explicitly calls for mapping native tool-calling schemas to MCP
servers. The internal protocol is the seam that makes that work.

Internal types:

- `InternalToolSpec`
- `InternalToolCall`
- `InternalToolResult`

These give the orchestrator and router one stable format, while adapters handle
Gemini and OpenAI-style differences at the edges.

## Why Separate MCP Servers

Two MCP servers are used on purpose:

- Metadata MCP server
- SQL sandbox MCP server

This separation improves:

- blast-radius control
- permission scoping
- reasoning clarity
- easier future migration to remote/containerized servers

The metadata server never executes SQL. The SQL sandbox server never exposes
arbitrary schema mutation capabilities.

## Why SQLite For The MVP

SQLite is intentionally conservative here:

- easy for a reviewer to run locally
- no external infrastructure requirement
- works well for a reproducible demo dataset
- still enough to prove async routing, MCP isolation, and SQL sandboxing

The architecture keeps the database behind the MCP server boundary, so swapping
SQLite for Postgres later is a server-level change rather than an orchestration
rewrite.

## Main Extension Paths

- Add richer schema-driven prompt construction in the SQL agent.
- Add Anthropic-style tool adapter support.
- Promote MCP servers from local stdio processes to remote/containerized
  services.
- Add structured tracing and persisted run logs.
- Add human review or approval gates for high-risk operations if write support is
  ever introduced.

