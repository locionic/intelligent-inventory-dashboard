# Agent Instructions — Intelligent Inventory Dashboard

Read `spec.md` before writing any code. It contains the data model and API
contract. Do not invent requirements that aren't in it — if something is
ambiguous, ask me or state the assumption you're making and why.

## Working mode: small chunks, not the whole app at once

Build in this order. Stop after each chunk and wait for review before
continuing to the next:

1. Models (Dealership, Vehicle, AgingAction) — nothing else yet.
2. Aging-stock query logic — the highest-risk piece, see rules below.
3. Serializers + read-only views (list, detail, aging list).
4. Write endpoint (log an action) — the only write path in this API.
5. Tests (if not already written per-chunk).
6. README + OpenAPI contract.

Do not jump ahead to a later chunk while an earlier one is unreviewed.

## Test-first for business logic

For anything involving a threshold, boundary, or status rule (e.g. "aging =
>90 days", "can't log actions on sold vehicles"):

1. Write the test(s) first, including edge cases (the boundary value itself,
   one below, one above, zero, and any excluded status).
2. Show me the test before implementing the logic.
3. Implement.
4. Run the tests yourself and paste the actual output — do not claim
   "this should work" or "tests pass" without running them.
5. If a test fails, show the failure, explain the root cause, then fix.

## Default to narrow, not broad

Prefer read-only endpoints over full CRUD unless the spec explicitly
requires writes. If you're about to generate something broader or more
permissive than the spec asks for (e.g. `ModelViewSet` giving full
CRUD when only reads + one write are needed), stop and flag it to me
instead of implementing it silently.

## Efficiency check

Before finalizing any query, check: does this filter/aggregate at the
database level, or does it load rows into Python and process them there?
Flag anything that would load a full table into memory.

## Logging

After each chunk, append an entry to `AI_LOG.md`:
- Prompt/goal for the chunk
- What was generated
- Any test written first and its result against the initial implementation
- Any bug found + root cause + fix
- Any decision you flagged as broad/risky and how it was resolved

This log is the source for the README's AI Collaboration Narrative — keep
entries factual and specific, not summarized.

## Never

- Never mark a task done without running the tests and showing output.
- Never silently expand scope beyond spec.md.
- Never skip writing a boundary test for a numeric/date threshold rule.

