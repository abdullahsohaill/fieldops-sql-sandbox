# Threat Model

## Security Goal

Treat generated SQL, tool calls, and tool results as untrusted inputs unless
they are checked by deterministic code.

## Main Risks

### Unsafe SQL generation

Risk:
The model emits `DROP`, `UPDATE`, multiple statements, or other dangerous SQL.

Mitigation:

- Parse SQL with `sqlglot`
- Allow only read-only `SELECT`
- Reject blocked keywords and unsafe expressions
- Reject multiple statements
- Reject unknown tables
- Enforce row limits

### Prompt injection through the user question

Risk:
The user tries to coerce the model into bypassing the sandbox.

Mitigation:

- LLM output is never the enforcement boundary
- SQL must still pass deterministic validation
- MCP server tools expose only limited capabilities

### Tool misuse through arbitrary filesystem/DB targeting

Risk:
The tool caller points the MCP server at a different database file.

Mitigation:

- `db_path` was intentionally removed from MCP tool schemas
- MCP servers resolve the configured database path internally

### Long-running or expensive SQL

Risk:
An otherwise read-only query hangs or becomes too expensive.

Mitigation:

- max row limits
- SQLite progress handler timeout
- structured timeout error path

### Over-trusting a provider-specific tool schema

Risk:
Orchestration becomes tied to one model vendor or one wire format.

Mitigation:

- provider-neutral internal tool protocol
- Gemini and OpenAI-style adapters tested independently

## Residual Risks

- SQLite is local, so host-level compromise is out of scope for this MVP.
- The Gemini live path currently uses lightweight prompt contracts rather than a
  more robust structured planning framework.
- The current demo does not persist full trace/audit records yet.

## Deliberate Non-Goals

- Write-capable SQL workflows
- Multi-tenant authn/authz
- Production deployment hardening
- Remote untrusted tool hosting

