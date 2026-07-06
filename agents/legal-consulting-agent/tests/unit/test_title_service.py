"""Unit tests for LLM-backed session title generation."""

from __future__ import annotations

import pytest

from legal_consulting_agent.application.services.title_service import LegalTitleService
from legal_consulting_agent.domain.ports.llm_adapter import (
    LlmCompletionRequest,
    LlmCompletionResponse,
)
from legal_consulting_agent.infrastructure.llm.fake_llm_adapter import FakeLlmAdapter


class _RaisingAdapter:
    async def complete(self, request: LlmCompletionRequest) -> LlmCompletionResponse:
        raise RuntimeError("upstream unavailable")


@pytest.mark.asyncio
async def test_generate_title_uses_llm_output_when_available() -> None:
    adapter = FakeLlmAdapter(fixtures={("legal_session_title", "v1"): "《劳动合同调岗纠纷》\n多余内容"})
    service = LegalTitleService(llm_adapter=adapter)

    title = await service.generate_title(first_question="公司要把我调去外地，我能拒绝吗？")

    # First line only, quotes/《》 stripped.
    assert title == "劳动合同调岗纠纷"


@pytest.mark.asyncio
async def test_generate_title_falls_back_to_question_on_empty_output() -> None:
    adapter = FakeLlmAdapter()  # no fixture -> complete returns ""
    service = LegalTitleService(llm_adapter=adapter)

    title = await service.generate_title(first_question="租房押金不退怎么维权？")

    assert title == "租房押金不退怎么维权"


@pytest.mark.asyncio
async def test_generate_title_falls_back_when_adapter_raises() -> None:
    service = LegalTitleService(llm_adapter=_RaisingAdapter())

    title = await service.generate_title(first_question="")

    # Empty question with a failing adapter -> default title, never an exception.
    assert title == "法律咨询"
