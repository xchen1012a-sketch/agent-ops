# KNOW-200 Recruitment Conversation Workflow

## Status

Completed on 2026-07-06.

## Goal

Simplify the recruitment assistant into a Claude-style conversation workflow. Users provide a JD and resume text in the conversation, and the system returns structured extraction, match score, evidence, risk points, interview questions, and report evidence.

## Source Boundary

- Current `docs/homework/` includes Dify workflow courseware and node cases under `AI编程_智能问数实训(课件)/05_Dify工作流智能体开发/dify案例实战/`, including a resume information extraction case.
- This phase maps those Dify node concepts to the project-local recruitment workflow and versioned rules.
- This phase does not claim a real Dify app, real Feishu account, real DeepSeek call, external candidate database, OCR resume parser, or production RAG knowledge base.
- The MVP uses project-local versioned recruitment rules and existing workflow/API surfaces as Dify-equivalent evidence.

## Scope Completed

- Added a versioned MVP rule package under `agents/recruitment-assistant-agent/src/recruitment_assistant_agent/rules/`.
- Moved recruitment MVP boundaries into `recruitment_mvp_v1.json`: workflow nodes, resume/JD extraction fields, skill keyword matching, fairness protected attributes, and completion effect.
- Wired the workflow fairness node to the versioned protected-attribute rule source.
- Added derived `analysis` data to recruitment task detail responses without storing raw resume/JD text in the analysis record.
- Added deterministic MVP analysis output: candidate summary, job title, score tier, matched keywords, missing keywords, risk points, interview questions, fairness note, and workflow node list.
- Updated recruitment reports to include rule version, Dify-equivalent workflow evidence, match summary, risk points, interview questions, fairness boundary, and source boundary.
- Updated frontend recruitment detail view and types to display the structured match summary inside the conversation-style task page.

## Not Done

- No candidate database.
- No OCR resume parsing.
- No complex recruitment audit back office.
- No RAG knowledge base as a required MVP dependency.
- No claim that real Dify/DeepSeek/Feishu/MySQL services were connected for this phase.

## Acceptance Evidence

### Functional Evidence

- Users can create a recruitment task from JD/resume text through the existing conversation-style recruitment flow.
- Task detail API now exposes structured `analysis`.
- Report API now includes rule version, workflow evidence, match score, fairness boundary, and source limitation.
- Sensitive/protected attributes are sourced from versioned rules and ignored for scoring.

### Verification Commands

Run from `C:\Users\ahua\Desktop\agent\agents\recruitment-assistant-agent`:

```powershell
.\.venv\Scripts\python.exe -m ruff check src\recruitment_assistant_agent\rules src\recruitment_assistant_agent\workflows\recruitment_nodes.py src\recruitment_assistant_agent\application\services\recruit_task_api_service.py src\recruitment_assistant_agent\api\v1\schemas\recruitment_tasks.py src\recruitment_assistant_agent\api\v1\endpoints\recruitment_tasks.py tests\unit\test_recruitment_mvp_rules.py tests\integration\test_recruitment_tasks_api.py tests\integration\test_recruitment_reports_api.py tests\integration\test_recruitment_acceptance_api.py
```

Result: passed, `All checks passed!`.

```powershell
.\.venv\Scripts\python.exe -m mypy src\recruitment_assistant_agent\rules src\recruitment_assistant_agent\workflows\recruitment_nodes.py src\recruitment_assistant_agent\application\services\recruit_task_api_service.py src\recruitment_assistant_agent\api\v1\schemas\recruitment_tasks.py src\recruitment_assistant_agent\api\v1\endpoints\recruitment_tasks.py tests\unit\test_recruitment_mvp_rules.py tests\integration\test_recruitment_tasks_api.py tests\integration\test_recruitment_reports_api.py tests\integration\test_recruitment_acceptance_api.py
```

Result: passed, `Success: no issues found in 10 source files`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_recruitment_mvp_rules.py tests\unit\test_recruitment_workflow.py tests\unit\test_workflow_runner_service.py tests\integration\test_recruitment_tasks_api.py tests\integration\test_recruitment_reports_api.py tests\integration\test_recruitment_acceptance_api.py -q -p no:cacheprovider --basetemp .\.pytest-basetemp-know200-verify --tb=short
```

Result: passed, `35 passed in 0.96s`.

Run from `C:\Users\ahua\Desktop\agent\agent-suite-web`:

```powershell
npm.cmd run typecheck
```

Result: passed, `vue-tsc --noEmit`.

## Remaining Evidence For KNOW-400

- Browser screenshots for the final report/demo package are deferred to `KNOW-400`.
- Final homework report wording must keep the source boundary explicit: Dify-equivalent local workflow evidence, not a real Dify deployment.

## Rollback

- Remove the recruitment MVP rule package.
- Remove `analysis` from recruitment task responses and frontend detail display.
- Restore recruitment reports to the previous task/status-only markdown.
