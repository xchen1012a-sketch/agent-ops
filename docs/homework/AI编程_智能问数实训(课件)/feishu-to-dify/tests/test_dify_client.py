"""Unit tests for Dify SSE parsing helpers."""

from app.models.schemas import DifyStreamEvent
from app.services.dify_client import (
    extract_error_message,
    extract_final_output,
    extract_text_chunk,
    is_human_input_event,
    parse_workflow_finished,
)
from app.services.feishu_message import format_dify_error_for_user


def test_extract_text_chunk() -> None:
    event = DifyStreamEvent(event="text_chunk", data={"text": "Hello"})
    assert extract_text_chunk(event) == "Hello"


def test_extract_final_output_prefers_text_key() -> None:
    event = DifyStreamEvent(
        event="workflow_finished",
        data={"status": "succeeded", "outputs": {"text": "Done"}},
    )
    assert extract_final_output(event) == "Done"


def test_extract_error_message() -> None:
    event = DifyStreamEvent(event="error", data={"message": "boom"})
    assert extract_error_message(event) == "boom"


def test_human_input_event() -> None:
    event = DifyStreamEvent(event="human_input_required", data={})
    assert is_human_input_event(event) is True


def test_parse_workflow_finished_failed_does_not_raise() -> None:
    event = DifyStreamEvent(
        event="workflow_finished",
        data={"status": "failed", "error": "Failed to parse structured output"},
    )
    result = parse_workflow_finished(event)
    assert result is not None
    assert result.success is False
    assert "structured output" in (result.error or "")


def test_format_dify_error_structured_output() -> None:
    msg = format_dify_error_for_user("Failed to parse structured output: ...")
    assert "结构化输出" in msg
