"""Compositors — assemble per-panel SVGs into paper figures.

Two public functions (only the four-panel is implemented in 2e-2; the
three-way comes in 2e-3):

    render_four_panel(case, cue) -> str
    render_three_way(case, cue)  -> str   (not yet implemented)

Layout (four-panel, 2x2 Z-scan per SPEC §6 with Panel 3/4 redundancy
resolved by stripping Panel 3's output box and force scale):

    +-----------------+-----------------+
    |  Panel 1        |  Panel 2        |   y=0, ~360 tall
    |  case input     |  signals        |
    +-----------------+-----------------+
    |                 |                 |
    |  Panel 3        |  Panel 4        |   y=360, ~520 tall
    |  cascade        |  cue output     |
    |  (no box,       |                 |
    |  no scale)      |                 |
    +-----------------+-----------------+

The compositor calls each sub-renderer with `css=False` and embeds the
returned SVG inside a `<g transform="translate(...)">`. Each sub-SVG's
inner viewBox is preserved, so its internal layout is unchanged — only
its position in the outer coordinate system shifts.

CSS lives once on the outer SVG (concatenated from the four panel
stylesheets), avoiding duplicate `<style>` blocks when multiple panels
are embedded.
"""

from pathlib import Path

from models import Case, Cue
from viz.case_input import render_case_input, render_interval_bar
from viz.signals import render_signals
from viz.cascade import render_cascade
from viz.cue_output import render_cue_output


# --- Four-panel layout (viewBox units) ---
_FOUR_PANEL_WIDTH = 960
_FOUR_PANEL_HEIGHT = 660

# Top row — sized to match per-panel content height (Panel 1: ~240, Panel 2: ~220)
_TOP_ROW_Y = 0
_TOP_ROW_H = 240
_PANEL_1_X = 0
_PANEL_1_W = 480
_PANEL_2_X = 480
_PANEL_2_W = 480

# Bottom row — cascade gets the dominant share; Panel 4 sized to its actual
# content needs (action word + pill + via). Closer panel widths to content
# lengths closes the horizontal gap between the arrow tip and Panel 4's content.
_BOTTOM_ROW_Y = 240
_BOTTOM_ROW_H = 420
_PANEL_3_X = 0
_PANEL_3_W = 680
_PANEL_4_X = 680
_PANEL_4_W = 280


# --- Three-way comparison layout (viewBox units) ---
# Three side-by-side displays of the same case at three levels of decision-process
# transparency. Per SPEC §6 caveat, columns are NOT equal-width: the cascade
# column is wider because it encodes more. The data-level displays have less to
# show; padding them to equal width would mislead the reader about their
# information density.
_THREE_WAY_WIDTH = 1080
_THREE_WAY_HEIGHT = 520

_COL_CONF_X = 0
_COL_CONF_W = 240

_COL_BAR_X = 240
_COL_BAR_W = 280

_COL_CASCADE_X = 520
_COL_CASCADE_W = 560

# Common column header
_COL_HEADER_Y = 28
_COL_BODY_TOP_Y = 60


def _load_combined_css() -> str:
    """Read all four panel stylesheets and emit a single <style> block.

    Each panel's CSS is already scoped to its panel class (.case-input,
    .signals, .cascade, .cue-output) so concatenation is safe — no
    selector collisions between panels.
    """
    css_dir = Path(__file__).parent
    files = [
        "case_input_styles.css",
        "signals_styles.css",
        "cascade_styles.css",
        "cue_output_styles.css",
    ]
    combined = "\n\n".join((css_dir / f).read_text() for f in files)
    return f'<style>{combined}</style>'


def _wrap(sub_svg: str, x: int, y: int) -> str:
    """Wrap a sub-SVG in a translate group at the given origin.

    The sub-SVG's viewBox is preserved inside its own <svg> element;
    the wrapper just shifts where it sits in the composite's coordinate
    space.
    """
    return f'  <g transform="translate({x}, {y})">\n{sub_svg}\n  </g>'


def render_four_panel(
    case: Case,
    cue: Cue,
    *,
    width: int = _FOUR_PANEL_WIDTH,
    height: int = _FOUR_PANEL_HEIGHT,
    css: bool = True,
    interactive: bool = False,
) -> str:
    """Figure 1: 2x2 Z-scan grid of the four panels.

    Per the 2d-3/2e design review, Panel 3's cascade is rendered in
    composite mode (no output box, no force scale, no safety arrow) so
    Panel 4's force pill + safety banner carry the canonical action +
    force display. The cascade's resolution arrow extends rightward,
    visually flowing into Panel 4.
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
    p3 = render_cascade(
        case, cue,
        reveal="none",
        width=_PANEL_3_W, height=_BOTTOM_ROW_H,
        css=False, interactive=interactive,
        include_output_box=False,
        include_force_scale=False,
    )
    p4 = render_cue_output(
        cue,
        width=_PANEL_4_W, height=_BOTTOM_ROW_H,
        css=False, interactive=interactive,
    )

    style = _load_combined_css() if css else ""
    p1_wrapped = _wrap(p1, _PANEL_1_X, _TOP_ROW_Y)
    p2_wrapped = _wrap(p2, _PANEL_2_X, _TOP_ROW_Y)
    p3_wrapped = _wrap(p3, _PANEL_3_X, _BOTTOM_ROW_Y)
    p4_wrapped = _wrap(p4, _PANEL_4_X, _BOTTOM_ROW_Y)

    return f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" class="four-panel" xmlns="http://www.w3.org/2000/svg">
  {style}
{p1_wrapped}
{p2_wrapped}
{p3_wrapped}
{p4_wrapped}
</svg>'''


# ---------------------------------------------------------------------------
# Three-way comparison (Figure 2)
# ---------------------------------------------------------------------------

def _render_confidence_only_card(case: Case, col_width: int, col_height: int) -> str:
    """The leftmost column of the three-way: a single point estimate against
    the threshold. Synthesized inline here (no separate viz/ module per
    SPEC §6) because it's small and only used in one place.

    Encodes what a confidence-only display reveals: the risk score as a
    number, the threshold as a caption. No interval, no signals, no
    composition trace.
    """
    score = f"{case.risk_score:.2f}"
    threshold = f"{case.decision_threshold:.2f}"
    center_x = col_width // 2
    # Center the score+caption vertically in the column body.
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
    """Header row for each three-way column, sitting at the same y across
    all three columns so the row reads as a coordinated set of foils."""
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
    """Figure 2: three side-by-side displays of the same case at three
    levels of decision-process transparency.

        +---------------+---------------+--------------------+
        | Confidence    |  Uncertainty  |     ActionCue      |
        | only          |  display      |     (cascade)      |
        +---------------+---------------+--------------------+

    Per SPEC §6, the cascade column is wider than the other two — the
    data-level displays have less to encode, and padding them to equal
    width would either mislead the reader about their density or
    compress the cascade.

    Right column uses the standalone cascade (output box + force scale
    intact) — this is the *foil's terminal state*, the full picture of
    what ActionCue reveals. Unlike Figure 1 (the four-panel composite,
    where Panel 4 carries the cue canonically), Figure 2's cascade is
    its own self-contained display.
    """
    # Column 1: confidence-only card
    conf_card = _render_confidence_only_card(case, _COL_CONF_W, height)
    conf_wrapped = _wrap(
        f'<svg viewBox="0 0 {_COL_CONF_W} {height}" width="{_COL_CONF_W}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n{conf_card}\n</svg>',
        _COL_CONF_X, 0,
    )

    # Column 2: interval bar (vertically centered with a small score label above it)
    bar_inner = render_interval_bar(case, width=_COL_BAR_W, height=80)
    bar_y_in_col = (height - 80) // 2 + 20  # center the bar vertically
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

    # Column 3: standalone cascade (output box + force scale included — this is
    # the full ActionCue foil, not the composite-mode cascade).
    cascade_h = height - _COL_BODY_TOP_Y - 20
    cascade_svg = render_cascade(
        case, cue,
        reveal="none",
        width=_COL_CASCADE_W, height=cascade_h,
        css=False, interactive=interactive,
        include_output_box=True,
        include_force_scale=True,
    )
    cascade_wrapped = _wrap(cascade_svg, _COL_CASCADE_X, _COL_BODY_TOP_Y)

    # Column headers
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
