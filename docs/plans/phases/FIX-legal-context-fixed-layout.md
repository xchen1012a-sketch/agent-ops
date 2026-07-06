# FIX Legal Context Fixed Layout

## Status

Completed on 2026-07-06.

## Problem

- Legal SSE generation has no real multi-turn context because the stream prompt only sends the latest question to the LLM adapter.
- Long conversations make the whole page keep growing instead of keeping the composer fixed and scrolling inside the conversation area.

## Evidence

- `question_answer_service.py` loads prior messages into `context_messages` before appending the new user question.
- `legal_questions.py` currently builds `LlmCompletionRequest(rendered_prompt=question)`, so the stream adapter never receives that history.
- `LegalSessionPage.vue` uses document-flow message rendering plus sticky composer; messages increase page height.

## Impact

- Follow-up questions like "刚才那个情况下一步怎么办" lose context in real model generation.
- Long chat sessions become hard to use because the viewport stretches and the input area is no longer a stable chat surface.

## Non-goals

- Do not redesign the whole legal assistant UI.
- Do not change authentication, API keys, model provider settings, or database schema.
- Do not alter recruitment or data-query agents.

## Fix Plan

1. Backend context propagation
   - Add prior `context_messages` to `LegalQuestionAnswerResult`.
   - Render a bounded stream prompt that includes recent user/assistant context and the current question.
   - Add unit coverage proving the stream adapter receives historical context.

2. Frontend fixed chat layout
   - Make the legal chat page occupy a fixed viewport-height area inside the app shell.
   - Move overflow to the conversation region.
   - Keep the composer in the page grid instead of relying on document-level sticky behavior.
   - Auto-scroll the conversation region when streaming or loading messages.

## Verification

- `pytest tests/unit/test_legal_questions_api.py tests/unit/test_deepseek_stream_adapter.py tests/unit/test_sse_forwarder.py -q -p no:cacheprovider --basetemp .\.pytest-basetemp-legal-context-layout --tb=short` -> `11 passed`.
- `ruff check src\legal_consulting_agent\api\v1\endpoints\legal_questions.py src\legal_consulting_agent\application\services\question_answer_service.py tests\unit\test_legal_questions_api.py` -> passed.
- `mypy src\legal_consulting_agent\api\v1\endpoints\legal_questions.py src\legal_consulting_agent\application\services\question_answer_service.py tests\unit\test_legal_questions_api.py` -> passed.
- `agent-suite-web` `npm.cmd run lint` -> passed.
- `agent-suite-web` `npm.cmd run typecheck` -> passed.
- Restarted legal runtime on `127.0.0.1:8101`; `/v1/health/live` -> `200`.
- Gateway SSE smoke on `127.0.0.1:7777`: create session, ask first question, ask follow-up; both emitted thinking and answer deltas, second emitted `message.completed`, no `run.failed`.

## Stop Conditions

- If context requires schema/database migration, stop and report.
- If fixed layout needs app-shell-wide restructuring, keep the change local and report the limitation.

## Rollback

- Remove `context_messages` from `LegalQuestionAnswerResult` and return stream prompt rendering to the latest question only.
- Revert the legal chat page layout CSS and scroll ref changes.
