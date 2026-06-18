# ActionCue

A Streamlit prototype demonstrating the uncertainty-to-action binding framework.

## Build specification

The complete build target is in `SPEC.md` at the repo root. Read it before
any change. Reference sections by anchor (e.g., "§6", "§12") rather than
restating them.

## Stable from Week 1 — do not modify without asking

These files are the verified Week 1 contract. The 11 tests in §10 pass
against them. Read them as needed; do not change them in this phase.

- `models.py`
- `rules.py`
- `engine.py`
- `cases/healthcare.py`, `cases/cross_domain.py`, `cases/__init__.py`
- `tests/test_engine.py`

If you believe a Week 1 file needs changing to enable Week 2 work, stop
and explain — do not edit.

## Active phase

**Week 2: all four per-panel renderers, two compositors, figure export.**

In scope this phase:
- `viz/__init__.py`
- `viz/cascade.py` — `render_cascade(case, cue, *, reveal, width, height,
  css, interactive) -> str` per §6
- `viz/cascade_styles.css` — scoped CSS per §6
- `viz/cascade_interact.js` — vanilla JS interaction layer per §6
- `viz/case_input.py` — `render_case_input(case)` and `render_interval_bar(case)`
  per §6 ("The other per-panel renderers")
- `viz/signals.py` — `render_signals(case)` per §6
- `viz/cue_output.py` — `render_cue_output(cue)` per §6
- `viz/composite.py` — `render_four_panel(case, cue)` and
  `render_three_way(case, cue)` per §6 ("The two compositors")
- `export_figures.py` — produces Figures 1, 2, 3 plus the three §4.4
  generativity figures, per the v2 export block in §6
- `figures/` — populated by running export_figures.py

Out of scope until I open the next phase: `app.py`, anything in `ui/`,
any Streamlit code. These are Week 3. If you find yourself reaching for
`st.*` or `components.html`, stop.

Verification gate:
1. `pytest tests/` still clean (no Week 1 regression).
2. `python export_figures.py` runs without error and produces six SVGs in
   `figures/`: `figure_1_four_panel.svg`, `figure_2_three_way.svg`,
   `figure_3_panel_3_detailed.svg`, and the three
   `figure_4_generativity_{a,cr,dr}.svg` files.
3. Each SVG opens in a browser and matches the §6 / §9 visual design.

## Checkpoint structure for this phase

Week 2 is load-bearing for the contribution (per §1) and now also for
the paper figures (every figure in §4 of the paper comes from this code).
Build it in five checkpoints, not one. Wait for me to confirm before
moving from one to the next.

**2a — cascade SVG structure.** Implement `render_cascade` returning the
bare SVG (no CSS, no JS yet) per the §6 SVG structure block. Verify by
calling it with a known Case/Cue, saving the string to a file, and
opening in a browser: bands, resolution arrow, output box, and force
scale are present and positioned, even if unstyled.

**2b — cascade scoped CSS and force scale.** Add `viz/cascade_styles.css`
and wire it into `render_cascade` under `css=True`. Implement the
force-scale rendering (vertical scale on the right, active-level tick,
safety-modifier arrow). The SVG now matches the §6 / §9 visual design:
force tints, winner highlight, class accent colors.

**2c — cascade JS interaction layer.** Add `viz/cascade_interact.js` per
§6 and wire it under `interactive=True`. Verify by opening the scratch
HTML and confirming hover tooltips and click-to-expand work for every
band; resolution-arrow and force-scale hover affordances also fire.

**2d — the other three per-panel renderers.** Implement, one at a time,
verifying each before moving to the next:
  - `viz/case_input.py` — `render_case_input` and `render_interval_bar`
  - `viz/signals.py` — `render_signals`, with stable `signal-row-{name}`
    ids so the cascade's back-reference layer can target them
  - `viz/cue_output.py` — `render_cue_output`, including the safety-
    modifier banner when `cue.safety_modified`

All four panel renderers share the calling convention
`(*, width, height, css, interactive)` (per §6, "The other per-panel
renderers"). Match it exactly.

**2e — compositors and figure export.** Implement `render_four_panel`
and `render_three_way` in `viz/composite.py`. The compositors call the
per-panel renderers with `css=False` (CSS lives only on the outer SVG)
and wrap each sub-SVG in `<g transform="translate(...)">` while
preserving its inner viewBox. Then implement `export_figures.py` per
the v2 §6 block to produce all six figures. Verify by running the
export and inspecting all six SVGs against the locked design.

## How to work with me

I am writing this code alongside you to learn. The default mode is:

1. **Explain before implementing.** When I ask about a piece of the
   spec, walk through the encoding choice, the data flow, and any
   SVG/CSS/JS idioms involved before producing code. Default to
   plan-mode reasoning even when plan mode is off.

2. **Scaffold in pieces, with explanation.** Week 2 has more
   transcription from the spec than Week 1 did (CSS and JS are given
   near-verbatim; the cascade SVG structure is also given). When I
   ask you to scaffold a file, produce it in chunks with brief
   explanation of what each chunk does — do not dump the whole file
   silently.

3. **Review, don't rewrite.** When I share code I wrote and ask for
   review, point out what's wrong, missing, or non-idiomatic. Describe
   what to change and where — not the corrected version. If I get
   stuck, I'll ask for the fix.

4. **Debug by pointing, not by patching.** When a figure looks wrong
   or the JS misbehaves, identify the line and the cause but let me
   fix it.

5. **Briefly explain SVG, CSS, and JS idioms when they come up.**
   `viewBox`, SVG groups and z-order, `data-*` attributes as CSS hooks,
   scoped CSS via the `.cascade` prefix, vanilla event listeners,
   `document.currentScript` scoping, sub-SVG translation in compositors
   — assume I'm comfortable with the languages but may not know a
   specific idiom. One or two sentences, not a tutorial.

6. **Ask before creating or modifying files**, except when I've said
   "scaffold this file" or "implement this function." Reading files is
   always fine.

You are the explainer and reviewer, I am the implementer. I will hand
control over explicitly when I want you to write something.

## Conventions

- Python 3.11+, type hints throughout.
- All renderers in `viz/` return strings and do not touch Streamlit
  (per §12). All Streamlit wiring is Week 3.
- All four per-panel renderers share the calling convention
  `(*, width, height, css, interactive)` so the compositors can call
  them uniformly (per §6, "The other per-panel renderers").
- Compositors call sub-renderers with `css=False`; CSS lives only on
  the outer SVG to avoid duplicated style blocks.
- Rule logic, `signal_for`, and `compose_cue` are pure (per §12);
  Week 2 must not break that purity by importing engine state or
  adding side effects to anything in Week 1 modules.
- JS is vanilla — no framework, no bundler, no CDN imports.
- SVG is inline, no external assets, no chart libraries.
- The cascade must be scoped: CSS prefixed with `.cascade`, JS scoped
  to `document.currentScript.parentNode` (per §6), so multiple cascades
  on one page do not interfere.
- Paper figures come from `export_figures.py`, not screenshots (§12).
  Every figure the paper shows is produced by code the live demo also
  runs.
- Force-level vocabulary: `advisory`, `strong`, `mandatory`, `blocking`
  (v2 — do not use older force terms if you find them in your training).
- File layout matches §2 of SPEC.md exactly.

## Verification

- Run `pytest tests/ -v` after any change that touches imports from
  Week 1 modules. Report the result.
- After each checkpoint (2a, 2b, 2c, 2d, 2e), I will open the SVG
  output in a browser and review against §6 / §9. Wait for confirmation
  before proceeding to the next checkpoint.
- When 2e is done, `python export_figures.py` must produce all six
  SVGs without error and they must visually match the locked design.