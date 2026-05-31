# Interview Notes

## Defensible MVP Choices

- SQLite instead of external infra
- stdio MCP servers instead of distributed services
- read-only SQL only
- deterministic validation before execution
- Gemini as the live provider, fake provider in tests

## Why The Design Is Reasonable

- It is small enough to run locally.
- It still demonstrates all key layers from the prompt:
  multi-agent flow, native tool mapping, isolated MCP servers, and sandboxed SQL.
- It leaves clear extension points without pretending to be production-complete.

## Likely Extension Questions

### Add another provider

Answer:
Add another adapter that maps provider-native tool schemas into the same
internal tool protocol. The router and MCP servers do not need to change.

### Add remote MCP servers

Answer:
Swap the client transport and server registry details. The tool protocol,
validator, and orchestrator logic can stay the same.

### Allow writes

Answer:
That is a different risk profile. It would require a stricter approval model,
transaction scoping, audited permissions, and a different safety architecture
than the current read-only sandbox.

### Scale up beyond SQLite

Answer:
Move database-specific logic into the SQL sandbox server. The orchestration and
tool adapter layers should remain stable.

