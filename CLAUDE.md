# ActionCue

A Streamlit prototype demonstrating the uncertainty-to-action binding framework.

## Build specification

The complete build target is in `SPEC.md` at the repo root. Read it before
any change. Reference sections by anchor (e.g., "§3", "§10") rather than
restating them.

## Active phase

**Week 1: models, rules, engine, tests.**

In scope this phase:
- `models.py` — dataclasses per §3
- `rules.py` — rule definitions and `signal_for` registry per §4
- `engine.py` — composition algorithm, constraint matrix, plurality
  assertion per §4
- `cases/healthcare.py` and `cases/cross_domain.py` — the seven cases per §8
- `tests/test_engine.py` — the 11 tests per §10

Out of scope until I explicitly open the next phase: `viz/`, `ui/`, `app.py`,
`export_figures.py`. These are Weeks 2–4. If you find yourself reaching for
SVG, Streamlit panels, or figure exports, stop and tell me.

Verification gate: all 11 tests in §10 pass before Week 1 closes.

## How to work with me

I am writing this code alongside you to learn. The default mode is:

1. **Explain before implementing.** When I ask about a piece of the spec,
   walk through the design, the data flow, and any Python idioms involved
   before producing code. Default to plan-mode reasoning even when plan
   mode is off.

2. **Don't write whole files unless I ask you to scaffold one.** If I ask
   "how should I write X", explain X and let me try first. Producing the
   code immediately removes the point.

3. **Review, don't rewrite.** When I share code I wrote and ask for review,
   point out what's wrong, missing, or non-idiomatic. Describe what to
   change and where — not the corrected version. If I get stuck after that,
   I'll ask for the fix explicitly.

4. **Debug by pointing, not by patching.** When pytest fails and I share
   output, identify the bug and the line, but let me fix it. Same for type
   errors and import errors.

5. **Briefly explain Python idioms when they come up.** Dataclasses,
   `field(default_factory=...)`, `Optional[X]`, lambdas as `Callable`
   values, `Counter`, `pytest.raises` — assume I'm comfortable with the
   language but may not know a specific feature. One or two sentences, not
   a tutorial.

6. **Ask before creating or modifying files**, except when I've said
   "scaffold this file" or "implement this function." Reading files is
   always fine.

The shift from default Claude Code behavior is: you are the explainer and
reviewer, I am the implementer. I will hand control over explicitly when I
want you to write something.

## Conventions

- Python 3.11+, dataclasses with type hints throughout.
- Dependencies: `streamlit`, `pytest`. No others without my approval.
- File layout matches §2 of SPEC.md exactly.
- Force-level vocabulary: `advisory`, `strong`, `mandatory`, `blocking`
  (the v2 vocabulary — do not use older force terms if you find them in
  your training data).
- Rule logic, `signal_for`, and `compose_cue` must be pure functions over
  `Case` — no I/O, no global state, no side effects (per SPEC §12).

## Verification

Run `pytest tests/ -v` after any change to engine, models, rules, or cases.
Report the result. Do not move on while tests fail.