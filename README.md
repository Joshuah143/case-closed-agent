# Case Closed — Himmens Detective Agent

Deterministic, evidence-complete solver for Railtown's Case Closed agentic hackathon.

The agent is designed around the actual scoring function rather than open-ended tool calling:

- parses the canonical timeline for culprit and means;
- maps a case across disposable, non-committing reconnaissance sessions;
- exhausts guarded-testimony combinations without spending a scored commit;
- compiles a shortest verified final path;
- refuses to commit if the live clue set or action count differs from the audit;
- submits one concise evidentiary gloss for every collected clue plus a sub-140-word narrative.

## Result

As of June 27, 2026, team **Himmens is first on the public H001–H002 leaderboard** with a total score of **1.414015**. All five scored seeds were accepted.

| Seed | Clues | Actions used | Actions left |
|---|---:|---:|---:|
| H001 | 14 | 15 | 45 |
| H002 | 18 | 20 | 40 |
| H003 | 20 | 24 | 41 |
| H004 | 16 | 22 | 43 |
| H005 | 15 | 21 | 49 |

## Setup

Python and dependencies are managed exclusively with `uv`.

```bash
uv sync
export DETECTIVE_TOKEN='your-team-token'
```

Never commit the team token. `.env` and run artifacts are ignored.

## Commands

Run the generic solver on a practice seed without committing:

```bash
uv run case-closed S001
```

Run multi-session reconnaissance. This never commits:

```bash
uv run python -m case_closed.recon S002 --sessions 3
```

Dry-run an audited scored plan. The command verifies every clue and budget invariant but does not submit:

```bash
uv run python -m case_closed.submissions H001
```

A scored commit requires two explicit flags:

```bash
uv run python -m case_closed.submissions H001 --commit --confirm-scored
```

The live server enforces one commit per team on each hidden seed. Team Himmens has already
submitted all five seeds, so further commit attempts are rejected and the existing results stand.
Use dry-run mode to reproduce the audited clue and budget invariants without attempting a commit.

## Architecture

- `case_closed/reasoning.py` — deterministic culprit/means inference and generic semantic artifacts.
- `case_closed/solver.py` — graph exploration, evidence memory, routing, and guarded-testimony logic.
- `case_closed/recon.py` — throttled multi-session pair exhaustion with retry handling.
- `case_closed/submissions.py` — audited final paths, exact clue invariants, and scorer-aligned notes.
- `case_closed/calibrate.py` — controlled S001 scorer experiments using unlimited practice commits.

The important design choice is separating reconnaissance from scoring. Scored seeds allow unlimited sessions but only a small commit allowance. Reconnaissance therefore discovers the map and guarded clue graph first; the final run executes only the evidence-complete critical path.

## Verification

```bash
uv run ruff check .
uv run pytest -q
```

Tests cover timeline parsing, decoy/staging means selection, note coverage, verbosity caps, and exact action-budget arithmetic.
