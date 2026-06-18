# ActionCue

A Streamlit prototype demonstrating uncertainty-to-action binding for AI-supported decisions.

## What it demonstrates

The same AI risk score produces structurally different oversight cues depending on which pre-specified uncertainty rules fire and how those rules compose under a precedence-based policy with a safety modifier. ActionCue's central claim is that **the *composition reasoning* — the step from rule firings to the selected primary cue — should be made visible**, not just the inputs and the output. Visibility of the composition reasoning is what distinguishes process-transparency visualization from data-level uncertainty disclosure.

The prototype is not a clinical model. It uses synthetic cases with hard-coded risk scores and pre-computed uncertainty signals so the contribution stays where it belongs: the rule engine, the cue composition, and the visualization of the composition trace — not predictive accuracy.

## The four moving parts

- **Uncertainty signals.** Pre-computed per case: missing critical data, out-of-scope, threshold-crossing, explanation instability, and the decision-context flags (high harm, low reversibility).
- **Rule classes.** Four ordered classes — `validity` → `completion` → `sensitivity` → `interpretation` — each binding one signal to a base action and base force.
- **Precedence + safety modifier.** The highest-precedence fired class wins. The safety modifier raises the force one level when decision-context flags are set (e.g. `strong` → `mandatory` under high harm).
- **The annotated precedence cascade.** A single inline SVG that renders the four bands in precedence order, the resolution arrow from the winner to the cue display, the cue itself (action word + force-tint pill + "via {rule_class}" caption), a horizontal force strip (advisory · strong · mandatory · blocking), and a safety banner when applicable.

Force levels in this codebase: `advisory`, `strong`, `mandatory`, `blocking`.

## Repo structure

```
actioncue/
├── models.py                  # Dataclasses: Case, Rule, UncertaintySignal, RuleFiring, Cue
├── rules.py                   # Rule definitions and signal_for resolver
├── engine.py                  # Rule firing, composition, constraint validation, safety modifier
├── cases/
│   ├── healthcare.py          # CASE_A–CASE_E (clinical decisions)
│   └── cross_domain.py        # CASE_CR (credit), CASE_DR (disaster forecasting)
├── viz/
│   ├── _common.py             # bool_attr, wrap_text, render_style helpers
│   ├── case_input.py          # render_case_input + render_interval_bar
│   ├── case_input_styles.css
│   ├── signals.py             # render_signals (Panel 2)
│   ├── signals_styles.css
│   ├── cascade.py             # render_cascade (Panel 3 — includes the cue display inline)
│   ├── cascade_styles.css
│   ├── cascade_interact.js    # Vanilla JS hover/click affordances
│   └── composite.py           # render_four_panel + render_three_way
├── tests/
│   └── test_engine.py         # 11 tests covering case outcomes + engine invariants
├── figures/                   # Six SVGs + six PDFs + index.html (generated)
├── export_figures.py          # Offline figure generator (no Streamlit)
├── requirements.txt
├── SPEC.md                    # Full build specification
└── CLAUDE.md                  # Active phase + collaboration notes
```

## Quickstart

```bash
# Install dependencies (Python 3.11+).
pip install -r requirements.txt

# Run the engine tests.
pytest tests/

# Regenerate the six paper figures and the all-in-one index.
python export_figures.py
```

After running `export_figures.py`, open `figures/index.html` in a browser to view all figures inline.

The Streamlit live demo (`app.py` and the `ui/` package) is Week 3 scope and not yet present. The engine and the figure pipeline are independent of Streamlit, so everything above runs without it.

## Pre-built cases

| Case | Domain | Behavior |
|------|--------|----------|
| `CASE_A` | healthcare | Stable vitals, complete record, profile in scope. No rules fire → **proceed / advisory**. |
| `CASE_B` | healthcare | Risk near threshold, no missing data. Sensitivity fires → **inspect / strong**. |
| `CASE_C` | healthcare | Risk near threshold, oxygen saturation missing. Completion wins precedence over sensitivity → **complete / mandatory**. |
| `CASE_D` | healthcare | Case outside validated scope. Validity fires → **escalate / mandatory**. |
| `CASE_E` | healthcare | Out of scope, high harm, low reversibility. Safety modifier lifts force → **abstain / blocking**. |
| `CASE_CR` | credit risk | Out of scope + missing recent income verification. Validity dominates completion → **escalate / mandatory**. |
| `CASE_DR` | disaster | Sensitivity fires with explanation instability under high-harm / low-reversibility context. Safety lifts `strong` → **inspect / mandatory**. |

Case C is the recommended starting case for the three-way comparison: confidence-only display says "act"; uncertainty-only display says "borderline"; ActionCue exposes the missing input as the primary issue.

## Figures

Running `python export_figures.py` writes six SVG + PDF pairs and one `index.html` viewer into `figures/`:

| File | What it shows |
|------|---------------|
| `figure_1_four_panel.svg` | Three-panel composite for CASE_C (case input + signals on top, cascade-with-cue full-width below). |
| `figure_2_three_way.svg` | CASE_C across three displays: confidence-only point estimate, interval bar, ActionCue cascade. |
| `figure_3_panel_3_detailed.svg` | Standalone cascade with `reveal="all"` so the per-band rationale and triggering-signal label are visible. |
| `figure_4_generativity_a.svg` | CASE_A composite — no rules fire, proceed / advisory. |
| `figure_4_generativity_cr.svg` | CASE_CR composite — credit decision, validity wins. |
| `figure_4_generativity_dr.svg` | CASE_DR composite — disaster forecasting, safety modifier lifts force. |

Every figure the paper shows is produced by code the live demo also runs (single source of truth).
