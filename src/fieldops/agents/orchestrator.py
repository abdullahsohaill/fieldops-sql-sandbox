from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from fieldops.agents.catalog import orchestration_tool_catalog
from fieldops.agents.provider import ModelProvider
from fieldops.mcp_client.router import AsyncMcpRouter
from fieldops.tools.protocol import InternalToolCall, InternalToolResult, ToolCatalog


@dataclass(frozen=True)
class OrchestratorResult:
    request_id: str
    question: str
    plan: str
    schema_context: dict[str, Any]
    tool_call: InternalToolCall
    tool_result: InternalToolResult
    answer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "question": self.question,
            "plan": self.plan,
            "schema_context": self.schema_context,
            "tool_call": asdict(self.tool_call),
            "tool_result": asdict(self.tool_result),
            "answer": self.answer,
        }


class FieldOpsOrchestrator:
    def __init__(
        self,
        provider: ModelProvider,
        router: AsyncMcpRouter,
        catalog: ToolCatalog | None = None,
        max_tool_loops: int = 4,
    ) -> None:
        self.provider = provider
        self.router = router
        self.catalog = catalog or orchestration_tool_catalog()
        self.max_tool_loops = max_tool_loops

    async def answer(self, question: str) -> OrchestratorResult:
        request_id = str(uuid.uuid4())
        plan = await self._planner_agent(question)
        schema_context = await self._schema_agent(request_id)
        tool_call = await self._sql_agent(question, plan, schema_context)
        tool_result = await self.router.dispatch(tool_call)
        answer = await self._summarizer_agent(question, plan, schema_context, tool_call, tool_result)
        return OrchestratorResult(
            request_id=request_id,
            question=question,
            plan=plan,
            schema_context=schema_context,
            tool_call=tool_call,
            tool_result=tool_result,
            answer=answer,
        )

    async def _planner_agent(self, question: str) -> str:
        response = await self.provider.generate(
            "\n".join(
                [
                    "You are the FieldOps planner agent.",
                    "Decide the analysis intent and relevant database concepts.",
                    f"Question: {question}",
                ]
            )
        )
        return response.text.strip()

    async def _schema_agent(self, request_id: str) -> dict[str, Any]:
        summary_call = InternalToolCall(
            call_id=f"{request_id}:schema-summary",
            provider="gemini",
            name="get_database_summary",
            arguments={},
            server_name="metadata",
        )
        summary = await self.router.dispatch(summary_call)
        return {
            "summary": summary.result if summary.ok else summary.error,
        }

    async def _sql_agent(
        self,
        question: str,
        plan: str,
        schema_context: dict[str, Any],
    ) -> InternalToolCall:
        response = await self.provider.generate(
            "\n".join(
                [
                    "You are the SQL agent.",
                    "Return a tool call for execute_read_only_sql using only read-only SELECT SQL.",
                    f"Question: {question}",
                    f"Plan: {plan}",
                    f"Schema context: {json.dumps(schema_context, sort_keys=True)}",
                ]
            ),
            tools=self.catalog,
        )
        if response.tool_call is None:
            raise RuntimeError("SQL agent did not return a tool call.")
        return response.tool_call

    async def _summarizer_agent(
        self,
        question: str,
        plan: str,
        schema_context: dict[str, Any],
        tool_call: InternalToolCall,
        tool_result: InternalToolResult,
    ) -> str:
        response = await self.provider.generate(
            "\n".join(
                [
                    "You are the FieldOps summarizer agent.",
                    "Answer the user concisely using the SQL result. Mention if the sandbox rejected the SQL.",
                    f"Question: {question}",
                    f"Plan: {plan}",
                    f"Schema context: {json.dumps(schema_context, sort_keys=True)}",
                    f"Tool call: {json.dumps(asdict(tool_call), sort_keys=True)}",
                    f"Tool result: {json.dumps(asdict(tool_result), sort_keys=True)}",
                ]
            ),
            tool_result=tool_result,
        )
        return response.text.strip()

