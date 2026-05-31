# Demo Walkthrough

## Local Run

```bash
uv sync --extra dev
uv run fieldops build-db --mode offline
uv run fieldops db-summary
uv run fieldops demo
```

Expected outcome:

- the database is created locally
- row counts for all FieldOps tables are shown
- the demo prints a short answer about high weed pressure

## Live Gemini Run

```bash
export GEMINI_API_KEY=...
uv run fieldops ask "Which fields had the highest weed pressure?"
```

Expected outcome:

- Gemini is used as the model provider
- metadata is fetched through the metadata MCP server
- SQL is validated and executed through the SQL sandbox MCP server
- the final answer is summarized back to the user

## Good Reviewer Questions

- Which part is provider-specific and which is provider-agnostic?
- Where is SQL safety actually enforced?
- Why are metadata and SQL separated into different MCP servers?
- What would change if we moved from SQLite to Postgres?
- What would need to change to support another model provider?

## Handy Inspection Commands

```bash
uv run pytest
uv run ruff check .
gh pr list --state all
gh issue list --state all
```

