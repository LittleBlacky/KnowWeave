"""LLM-powered knowledge extraction from document chunks.

Extracts structured Knowledge Unit candidates from raw chunk text using an
LLM provider. Handles batch processing, prompt engineering, and LLM-based
deduplication against existing Knowledge Units.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.models.files import Chunk
from app.models.knowledge import KnowledgeUnit
from app.providers.base import LLMProvider, LLMProviderError

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExtractionCandidate:
    """A single knowledge point extracted by the LLM from a batch of chunks."""

    title: str
    unit_type: str  # concept | rule | process | definition | fact
    content: str
    summary: str
    source_chunk_index: int  # 0-based index into the batch


@dataclass(frozen=True)
class ExtractionResult:
    """Result of one extraction batch."""

    candidates: list[ExtractionCandidate]
    model_name: str
    usage: dict[str, int]
    raw_response: str = field(default="", repr=False)


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_EXTRACTION_SYSTEM_PROMPT = """\
你是知识提取专家。从以下文档片段中提取独立的知识点。

## 要求
1. 知识点必须能脱离原文独立理解，具有独立的认知价值
2. 类型（unit_type）从以下选择：
   - concept: 概念、术语定义
   - rule: 规则、约束、要求、审批条件
   - process: 流程、步骤、操作方法
   - definition: 正式定义、名词解释
   - fact: 事实陈述、数据、具体信息
3. title 不超过 30 字，是一个名词短语或简短陈述
4. content 用自己的话重新组织原文信息，确保完整准确，150-500 字
5. summary 是一句话摘要，不超过 100 字
6. **重要**：如果片段只是过渡性文字、目录、标题、空话，不要强行提取，对应的 source_chunk_index 就不要出现在结果中
7. source_chunk_index 标注知识点来自第几个片段（从 0 开始）

## 输出格式
严格返回 JSON 数组，不要有其他文字，不要用 markdown 代码块包裹：
[
  {
    "title": "系统访问审批规则",
    "unit_type": "rule",
    "content": "所有系统访问请求必须先获得直属主管审批...",
    "summary": "系统访问需要主管审批后才能开通账号",
    "source_chunk_index": 0
  }
]
"""

_DUPLICATE_CHECK_PROMPT = """\
判断以下"新知识点"是否与"已有知识点"存在实质性重复。

已有知识点列表：
{existing_kus}

待判断的新知识点：
- 标题：{title}
- 摘要：{summary}

判断标准：如果新知识点的核心含义、关键事实或结论与已有知识点中的一个或多个高度重叠（即使表述不同），则认为重复。
只返回一个单词：true（重复）或 false（不重复）。"""

# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class ExtractionError(Exception):
    """Raised when LLM extraction fails (provider errors, malformed responses)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ExtractionProvider:
    """Uses an LLM provider to extract structured knowledge from chunks."""

    # Valid unit types that the LLM may return
    VALID_UNIT_TYPES = frozenset({"concept", "rule", "process", "definition", "fact"})

    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm = llm_provider

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def extract(
        self,
        *,
        chunks: list[Chunk],
        existing_kus: list[KnowledgeUnit],
    ) -> ExtractionResult:
        """Extract knowledge candidates from a batch of chunks.

        Args:
            chunks: A batch of chunks (recommend 5-8 per batch).
            existing_kus: Already-persisted KUs for dedup context in the prompt.

        Returns:
            ExtractionResult with parsed candidates, model info, and token usage.
        """
        if not chunks:
            return ExtractionResult(candidates=[], model_name="", usage={})

        chunks_text = self._format_chunks(chunks)
        existing_summary = self._format_existing_kus(existing_kus)
        user_prompt = self._build_user_prompt(chunks_text, existing_summary)

        try:
            llm_result = await self._llm.generate(
                messages=[
                    {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                options={"temperature": 0.3, "max_tokens": 4096},
            )
        except LLMProviderError as exc:
            raise ExtractionError(f"LLM extraction call failed: {exc}") from exc

        candidates = self._parse_response(llm_result.content, batch_size=len(chunks))
        return ExtractionResult(
            candidates=candidates,
            model_name=llm_result.model_name,
            usage=llm_result.usage,
            raw_response=llm_result.content,
        )

    async def check_duplicate(
        self,
        *,
        candidate: ExtractionCandidate,
        existing_kus: list[KnowledgeUnit],
    ) -> bool:
        """Use the LLM to judge whether *candidate* duplicates any existing KU.

        Returns True if the candidate is a duplicate and should be skipped.
        """
        if not existing_kus:
            return False

        # Build a compact representation of existing KUs for the prompt.
        lines: list[str] = []
        for ku in existing_kus[:20]:  # cap at 20 to bound prompt size
            summary = (ku.summary or "").strip()
            lines.append(f"- {ku.title}: {summary}")
        existing_text = "\n".join(lines) if lines else "(无已有知识点)"

        prompt = _DUPLICATE_CHECK_PROMPT.format(
            existing_kus=existing_text,
            title=candidate.title,
            summary=candidate.summary,
        )

        try:
            llm_result = await self._llm.generate(
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0, "max_tokens": 10},
            )
        except LLMProviderError:
            # If duplicate check fails, accept the candidate (fail-open).
            return False

        return llm_result.content.strip().lower() == "true"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_chunks(chunks: list[Chunk]) -> str:
        parts: list[str] = []
        for idx, chunk in enumerate(chunks):
            text = (chunk.edited_content or chunk.raw_content).strip()
            ctype = chunk.chunk_type or "text"
            parts.append(f"[片段 {idx}] (类型: {ctype})\n{text}\n")
        return "\n".join(parts)

    @staticmethod
    def _format_existing_kus(kus: list[KnowledgeUnit]) -> str:
        if not kus:
            return "(暂无已有知识点——这是该文件的第一批提取)"
        lines = ["以下是该文件已有的知识点，请避免提取重复内容："]
        for ku in kus[:30]:
            lines.append(f"- [{ku.unit_type}] {ku.title}")
        return "\n".join(lines)

    @staticmethod
    def _build_user_prompt(chunks_text: str, existing_summary: str) -> str:
        return f"""## 已有知识点（避免提取重复内容）
{existing_summary}

## 文档片段
{chunks_text}

请提取其中的独立知识点，严格按 JSON 数组格式返回。"""

    @staticmethod
    def _parse_response(raw: str, *, batch_size: int) -> list[ExtractionCandidate]:
        """Parse the LLM JSON response into ExtractionCandidate objects.

        Handles common LLM output quirks: markdown code fences, trailing commas,
        and stray text before/after the JSON array.
        """
        text = raw.strip()
        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        # Extract the first JSON array
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            raise ExtractionError(
                f"LLM response did not contain a JSON array. Raw: {raw[:300]}"
            )

        try:
            raw_items: list[dict[str, Any]] = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ExtractionError(
                f"Failed to parse LLM JSON response: {exc}. Raw snippet: {raw[:500]}"
            ) from exc

        candidates: list[ExtractionCandidate] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            unit_type = str(item.get("unit_type", "concept")).strip().lower()
            if unit_type not in ExtractionProvider.VALID_UNIT_TYPES:
                unit_type = "concept"
            content = str(item.get("content", "")).strip()
            summary = str(item.get("summary", "")).strip()
            source_idx = item.get("source_chunk_index", 0)
            if isinstance(source_idx, int) and 0 <= source_idx < batch_size:
                candidates.append(
                    ExtractionCandidate(
                        title=title,
                        unit_type=unit_type,
                        content=content,
                        summary=summary or title,
                        source_chunk_index=source_idx,
                    )
                )
        return candidates
