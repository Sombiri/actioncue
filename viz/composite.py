"""Compositors — assemble per-panel SVGs into paper figures.

Two public functions:

    render_four_panel(case, cue) -> str  (now a three-panel composite —
                                          name kept for SPEC §6 alignment
                                          and import stability)
    render_three_way(case, cue)  -> str

Layout (now a three-panel composite per the 2f redesign that collapsed
Panel 4 back into the cascade):

    +-----------------+-----------------+
    |  Panel 1        |  Panel 2        |   y=0
    |  case input     |  signals        |
    +-----------------+-----------------+
    |                                   |
    |  Panel 3 — cascade (now carries   |   y=top_row_h
    |  the cue: action + force pill +   |
    |  via + force strip + safety       |
    |  banner)                          |
    +-----------------------------------+

The compositor calls each sub-renderer with `css=False` and embeds the
returned SVG inside a `<g transform="translate(...)">`. Each sub-SVG's
inner viewBox is preserved.

CSS lives once on the outer SVG (concatenated from the three remaining
panel stylesheets), avoiding duplicate `<style>` blocks.
"""

from pathlib import Path

from models import Case, Cue
from viz.case_input import render_case_input, render_interval_bar
from viz.signals import render_signals
from viz.cascade import render_cascade


# --- Composite layout (viewBox units) ---
# Top row: case input + signals side by side, each at their standalone-default
# width (360). Bottom row: cascade at its standalone-default width (720).
# All three panels are 720 wide; the composite is edge-to-edge, no margins.
_COMPOSITE_WIDTH = 720
_COMPOSITE_HEIGHT = 760

_TOP_ROW_Y = 0
_TOP_ROW_H = 240
_PANEL_1_X = 0
_PANEL_1_W = 360
_PANEL_2_X = 360
_PANEL_2_W = 360

_CASCADE_ROW_Y = 240
_CASCADE_ROW_H = 520
_CASCADE_X = 0
_CASCADE_W = 720


# --- Three-way comparison layout (viewBox units) ---
_THREE_WAY_WIDTH = 1080
_THREE_WAY_HEIGHT = 560   # bumped from 520 to fit the cascade's 500-tall default

_COL_CONF_X = 0
_COL_CONF_W = 240
_COL_BAR_X = 240
_COL_BAR_W = 280
_COL_CASCADE_X = 520
_COL_CASCADE_W = 560

_COL_HEADER_Y = 28
_COL_BODY_TOP_Y = 60


def _load_combined_css() -> str:
    """Read the three remaining panel stylesheets and emit a single <style> block.

    Each panel's CSS is scoped to its panel class (.case-input, .signals,
    .cascade) so concatenation is safe — no selector collisions.
    """
    css_dir = Path(__file__).parent
    files = [
        "case_input_styles.css",
        "signals_styles.css",
        "cascade_styles.css",
    ]
    combined = "\n\n".join((css_dir / f).read_text() for f in files)
    return f'<style>{combined}</style>'


def _wrap(sub_svg: str, x: int, y: int) -> str:
    """Wrap a sub-SVG in a translate group at the given origin.
    The sub-SVG's viewBox is preserved inside its own <svg>; the wrapper
    just shifts where it sits in the composite's coordinate space.
    """
    return f'  <g transform="translate({x}, {y})">\n{sub_svg}\n  </g>'


def render_four_panel(
    case: Case,
    cue: Cue,
    *,
    width: int = _COMPOSITE_WIDTH,
    height: int = _COMPOSITE_HEIGHT,
    css: bool = True,
    interactive: bool = False,
) -> str:
    """Figure 1: composite of case input + signals (top row) over the cascade
    (bottom row, full-width).

    Per the 2f redesign, the cascade carries the cue display itself —
    output box (action + force pill + via), horizontal force strip below
    the bands, and the safety banner when applicable. The composite no
    longer has a separate cue panel.

    Function name kept for SPEC §6 / import stability; the layout is now
    three panels, not four.
    """
    p1 = render_case_input(
        case,
        width=_PANEL_1_W, height=_TOP_ROW_H,
        css=False, interactive=interactive,
    )
    p2 = render_signals(
        case,
        width=_PANEL_2_W, height=_TOP_ROW_H,
        css=False, interactive=interactive,
    )
    cascade = render_cascade(
        case, cue,
        reveal="none",
        width=_CASCADE_W, height=_CASCADE_ROW_H,
        css=False, interactive=interactive,
    )

    style = _load_combined_css() if css else ""
    p1_wrapped = _wrap(p1, _PANEL_1_X, _TOP_ROW_Y)
    p2_wrapped = _wrap(p2, _PANEL_2_X, _TOP_ROW_Y)
    cascade_wrapped = _wrap(cascade, _CASCADE_X, _CASCADE_ROW_Y)

    return f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" class="four-panel" xmlns="http://www.w3.org/2000/svg">
  {style}
{p1_wrapped}
{p2_wrapped}
{cascade_wrapped}
</svg>'''


# ---------------------------------------------------------------------------
# Three-way comparison (Figure 2)
# ---------------------------------------------------------------------------

def _render_confidence_only_card(case: Case, col_width: int, col_height: int) -> str:
    """The leftmost column of the three-way: a single point estimate against
    the threshold. Synthesized inline here (no separate viz/ module per
    SPEC §6) because it's small and only used in one place.
    """
    score = f"{case.risk_score:.2f}"
    threshold = f"{case.decision_threshold:.2f}"
    center_x = col_width // 2
    body_top = _COL_BODY_TOP_Y
    body_h = col_height - body_top
    score_y = body_top + body_h // 2 - 10
    caption_y = score_y + 36

    return f'''  <g class="conf-only-card" font-family="-apple-system, 'Segoe UI', Roboto, sans-serif">
    <text x="{center_x}" y="{body_top + 24}" text-anchor="middle" font-size="11" fill="#555555" letter-spacing="0.04em">AI RISK SCORE</text>
    <text x="{center_x}" y="{score_y + 30}" text-anchor="middle" font-size="48" font-weight="700" fill="#1F3D5C">{score}</text>
    <text x="{center_x}" y="{caption_y + 30}" text-anchor="middle" font-size="12" fill="#888888">Decision threshold: {threshold}</text>
  </g>'''


def _render_column_header(label: str, col_x: int, col_width: int) -> str:
    center_x = col_x + col_width // 2
    return (
        f'  <text x="{center_x}" y="{_COL_HEADER_Y}" text-anchor="middle" '
        f'font-family="-apple-system, \'Segoe UI\', Roboto, sans-serif" '
        f'font-size="12" font-weight="700" fill="#1F3D5C" '
        f'letter-spacing="0.06em">{label}</text>'
    )


def render_three_way(
    case: Case,
    cue: Cue,
    *,
    width: int = _THREE_WAY_WIDTH,
    height: int = _THREE_WAY_HEIGHT,
    css: bool = True,
    interactive: bool = False,
) -> str:
    """Figure 2: three side-by-side displays of the same case.

        +---------------+---------------+--------------------+
        | Confidence    |  Uncertainty  |     ActionCue      |
        | only          |  display      |     (cascade)      |
        +---------------+---------------+--------------------+

    Right column uses the standalone cascade — the full picture of what
    ActionCue reveals (bands + resolution + cue output + force strip +
    safety banner when applicable).
    """
    conf_card = _render_confidence_only_card(case, _COL_CONF_W, height)
    conf_wrapped = _wrap(
        f'<svg viewBox="0 0 {_COL_CONF_W} {height}" width="{_COL_CONF_W}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n{conf_card}\n</svg>',
        _COL_CONF_X, 0,
    )

    bar_inner = render_interval_bar(case, width=_COL_BAR_W, height=80)
    bar_y_in_col = (height - 80) // 2 + 20
    score_y_in_col = bar_y_in_col - 18
    score_text = (
        f'<text x="{_COL_BAR_W // 2}" y="{score_y_in_col}" text-anchor="middle" '
        f'font-family="-apple-system, \'Segoe UI\', Roboto, sans-serif" '
        f'font-size="20" font-weight="700" fill="#1F3D5C">{case.risk_score:.2f}</text>'
    )
    bar_col_svg = (
        f'<svg viewBox="0 0 {_COL_BAR_W} {height}" width="{_COL_BAR_W}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">\n'
        f'  {score_text}\n'
        f'  <g transform="translate(0, {bar_y_in_col})">\n{bar_inner}\n  </g>\n'
        f'</svg>'
    )
    bar_wrapped = _wrap(bar_col_svg, _COL_BAR_X, 0)

    cascade_h = height - _COL_BODY_TOP_Y - 20
    cascade_svg = render_cascade(
        case, cue,
        reveal="none",
        width=_COL_CASCADE_W, height=cascade_h,
        css=False, interactive=interactive,
    )
    cascade_wrapped = _wrap(cascade_svg, _COL_CASCADE_X, _COL_BODY_TOP_Y)

    h_conf = _render_column_header("CONFIDENCE-ONLY", _COL_CONF_X, _COL_CONF_W)
    h_bar = _render_column_header("UNCERTAINTY DISPLAY", _COL_BAR_X, _COL_BAR_W)
    h_cascade = _render_column_header("ACTIONCUE", _COL_CASCADE_X, _COL_CASCADE_W)

    style = _load_combined_css() if css else ""

    return f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" class="three-way" xmlns="http://www.w3.org/2000/svg">
  {style}
{h_conf}
{h_bar}
{h_cascade}
{conf_wrapped}
{bar_wrapped}
{cascade_wrapped}
</svg>'''
