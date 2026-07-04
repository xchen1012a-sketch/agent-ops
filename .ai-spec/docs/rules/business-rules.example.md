# Business rules

> Optional template. Use this only when project behavior depends on domain rules that are easy to forget, dispute, or drift from code.
> Do not write guesses here. Every rule needs a source.

## Scope

- Project/module:
- Last reviewed:
- Maintainer:

## Rule Table

| ID | Rule | Source | Status | Confidence | Conflict note |
|---|---|---|---|---|---|
| BR-001 | Example: a user cannot submit an order after payment is closed. | contract / user confirmation / code path | confirmed | high |  |

Status values:

- `proposed`: observed or inferred, waiting for human confirmation.
- `confirmed`: confirmed by user, contract, test, or authoritative code path.
- `deprecated`: known old rule, kept only for migration/history.

Confidence values:

- `high`: confirmed by source of truth or passing tests.
- `medium`: supported by code/docs but not explicitly confirmed.
- `low`: discovered during review; do not implement against it without confirmation.

## Vocabulary

| Term | Meaning | Allowed names/paths | Notes |
|---|---|---|---|
| Example term |  |  |  |

## Conflict Log

| Date | Conflict | Sources | Decision | Follow-up |
|---|---|---|---|---|
|  |  |  |  |  |

## Update Rules

- AI may add `proposed` rows only when the source is explicit and cited.
- AI must not promote a rule to `confirmed` without user, contract, test, or authoritative code evidence.
- If code and this file disagree, report the conflict before changing code.
- Keep this file short. Move long explanations to contracts, ADRs, or phase docs and link them here.
