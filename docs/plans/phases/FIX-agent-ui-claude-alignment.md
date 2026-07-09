# FIX Agent UI Claude Alignment

## Status

Completed on 2026-07-06.

## Problem

The legal agent page is now the Claude-style baseline, but the data-query and recruitment detail pages are not fully aligned:

- Data detail uses a similar chat structure but still allows document-level growth, sticky composer behavior, and an always-spinner assistant avatar.
- Recruitment detail still reads like a task/card workspace rather than a quiet conversation thread.
- Data landing still showed recent records in the main content area instead of relying on the sidebar, unlike the legal landing baseline.
- Recruitment landing used a bordered/shadowed helper bubble that felt more like a card than a quiet Claude-style assistant reply.

## Evidence

- `DataSessionPage.vue` uses `min-height: calc(100vh - 180px)` and sticky composer, not the fixed internal-scroll layout used by `LegalSessionPage.vue`.
- `DataSessionPage.vue` assistant avatar always uses a conic spinner even for non-pending assistant messages.
- `RecruitTaskDetailPage.vue` uses card bubbles, header border, and document-flow messages without an internal conversation scroll region.

## Scope

- Align `DataSessionPage.vue` with the legal session page layout and visual behavior.
- Align `DataSessionListPage.vue` with the legal landing page by keeping recent records out of the main content area.
- Align `RecruitNewTaskPage.vue` helper reply styling with the legal Claude-style message treatment.
- Align `RecruitTaskDetailPage.vue` toward a Claude-style conversation thread while preserving existing actions and task workflow.
- Do not change backend APIs, routes, auth, data models, or business logic.
- Do not redesign report/list/admin pages in this fix.

## Plan

1. Data session page
   - Add fixed viewport-height layout.
   - Move overflow to conversation area with subtle Claude-style scrollbar.
   - Auto-scroll to latest streaming answer.
   - Make assistant avatar static except while pending/streaming.

2. Recruitment task detail page
   - Add fixed viewport-height thread layout.
   - Use internal scroll with subtle scrollbar.
   - Reduce assistant card styling and align avatars/user bubble treatment to legal.
   - Keep task actions, review actions, score and evidence visible.

3. Verification
   - Run `agent-suite-web` lint/typecheck.
   - Browser-check legal/data/recruitment dimensions where reachable.

## Result

- `DataSessionListPage.vue`: main page now only shows the chat landing and suggestions; recent conversations remain in the sidebar.
- `DataSessionPage.vue`: fixed viewport-height chat layout, internal conversation scrolling, auto-scroll, subtle scrollbar, and pending-only spinner avatar.
- `RecruitNewTaskPage.vue`: helper reply now uses transparent assistant message styling and AI avatar treatment instead of a bordered card.
- `RecruitTaskDetailPage.vue`: fixed-height conversation thread, internal scroll, quiet assistant messages, right-side user bubble, and subtle scrollbar.

## Verification

- `npm.cmd run lint` passed in `agent-suite-web`.
- `npm.cmd run typecheck` passed in `agent-suite-web`.
- Browser verified:
  - `/data/sessions` has no main-content recent list and uses `chat-composer--data`.
  - `/data/sessions/:id` uses fixed page height with internal `overflow-y: auto`.
  - `/recruitment/tasks/new` uses `chat-composer--recruit`; helper bubble is transparent with no border/shadow and AI avatar styling.
  - Recruitment task detail had no existing task in the current local browser data, so final detail validation was code/type/lint based.

## Stop Conditions

- If an alignment requires changing routing or backend contracts, stop and report.
- If a detail page lacks existing data in the browser, validate by static checks and explain the browser limitation.

## Rollback

- Revert the CSS/layout and scroll-state changes in `DataSessionPage.vue` and `RecruitTaskDetailPage.vue`.
