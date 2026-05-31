from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import sqlglot
from sqlglot import exp


DEFAULT_MAX_ROWS = 100

BLOCKED_KEYWORDS = {
    "alter",
    "attach",
    "create",
    "delete",
    "detach",
    "drop",
    "insert",
    "pragma",
    "reindex",
    "replace",
    "update",
    "vacuum",
}

UNSAFE_EXPRESSIONS = (
    exp.Alter,
    exp.Command,
    exp.Create,
    exp.Delete,
    exp.Drop,
    exp.Insert,
    exp.Update,
)


@dataclass(frozen=True)
class SqlValidationResult:
    original_query: str
    safe_query: str
    referenced_tables: tuple[str, ...]
    max_rows: int
    limit_added: bool


class SqlValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def validate_read_only_sql(
    query: str,
    allowed_tables: Iterable[str],
    max_rows: int = DEFAULT_MAX_ROWS,
) -> SqlValidationResult:
    normalized_query = query.strip()
    if not normalized_query:
        raise SqlValidationError("empty_query", "SQL query cannot be empty.")
    if max_rows < 1:
        raise SqlValidationError("invalid_limit", "max_rows must be at least 1.")

    _reject_obvious_blocked_keywords(normalized_query)
    expressions = _parse_single_statement(normalized_query)
    expression = expressions[0]

    if not isinstance(expression, exp.Select):
        raise SqlValidationError("not_select", "Only SELECT statements are allowed.")
    if any(expression.find_all(*UNSAFE_EXPRESSIONS)):
        raise SqlValidationError("unsafe_expression", "Query contains a non-read-only SQL operation.")

    referenced_tables = _referenced_tables(expression)
    unknown_tables = referenced_tables - set(allowed_tables)
    if unknown_tables:
        unknown = ", ".join(sorted(unknown_tables))
        raise SqlValidationError("unknown_table", f"Query references unknown table(s): {unknown}.")

    safe_query, limit_added = _with_row_limit(expression, max_rows)
    return SqlValidationResult(
        original_query=normalized_query,
        safe_query=safe_query,
        referenced_tables=tuple(sorted(referenced_tables)),
        max_rows=max_rows,
        limit_added=limit_added,
    )


def _parse_single_statement(query: str) -> list[exp.Expression]:
    try:
        expressions = [parsed for parsed in sqlglot.parse(query, read="sqlite") if parsed is not None]
    except sqlglot.errors.ParseError as exc:
        raise SqlValidationError("parse_error", "SQL query could not be parsed.") from exc

    if len(expressions) != 1:
        raise SqlValidationError("multiple_statements", "Only one SQL statement is allowed.")
    return expressions


def _reject_obvious_blocked_keywords(query: str) -> None:
    tokens = {token.text.lower() for token in sqlglot.tokens.Tokenizer(dialect="sqlite").tokenize(query)}
    blocked = tokens & BLOCKED_KEYWORDS
    if blocked:
        blocked_list = ", ".join(sorted(blocked))
        raise SqlValidationError("blocked_keyword", f"Blocked SQL keyword(s): {blocked_list}.")


def _referenced_tables(expression: exp.Expression) -> set[str]:
    cte_names = {
        cte.alias_or_name
        for cte in expression.find_all(exp.CTE)
        if cte.alias_or_name
    }
    table_names = {
        table.name
        for table in expression.find_all(exp.Table)
        if table.name and table.name not in cte_names
    }
    return table_names


def _with_row_limit(expression: exp.Expression, max_rows: int) -> tuple[str, bool]:
    limited = expression.copy()
    limit_expression = limited.args.get("limit")
    if limit_expression is not None:
        current_limit = _limit_value(limit_expression)
        if current_limit is not None and current_limit <= max_rows:
            return limited.sql(dialect="sqlite"), False

    limited.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))
    return limited.sql(dialect="sqlite"), limit_expression is None


def _limit_value(limit_expression: exp.Expression) -> int | None:
    value_expression = limit_expression.args.get("expression")
    if isinstance(value_expression, exp.Literal) and value_expression.is_number:
        return int(value_expression.this)
    return None

