from pathlib import Path

from models import Case, Cue


_CLASS_ORDER = ["validity", "completion", "sensitivity", "interpretation"]
_FORCE_ORDER = ["advisory", "strong", "mandatory", "blocking"]

# Layout in viewBox units.
_BAND_X = 40
_BAND_WIDTH = 320
_BAND_HEIGHT = 80
_BAND_GAP = 10
_BAND_Y0 = 20
_ACCENT_WIDTH = 6

_OUTPUT_X = 420
_OUTPUT_Y = 150
_OUTPUT_WIDTH = 130
_OUTPUT_HEIGHT = 80

_SCALE_X = 580
_SCALE_Y0 = 20
_SCALE_STEP = 90


def _band_y(index: int) -> int:
    return _BAND_Y0 + index * (_BAND_HEIGHT + _BAND_GAP)


def _bool_attr(value: bool) -> str:
    return "true" if value else "false"


def _render_band(rule_class: str, fired: bool, is_winner: bool, y: int) -> str:
    label = rule_class.capitalize()
    label_y = y + 30
    status_cx = _BAND_X + _BAND_WIDTH - 20
    status_cy = y + _BAND_HEIGHT // 2
    return f'''    <g class="band" data-class="{rule_class}" data-fired="{_bool_attr(fired)}" data-winner="{_bool_attr(is_winner)}">
      <rect class="band-bg" x="{_BAND_X}" y="{y}" width="{_BAND_WIDTH}" height="{_BAND_HEIGHT}" />
      <rect class="band-accent" x="{_BAND_X}" y="{y}" width="{_ACCENT_WIDTH}" height="{_BAND_HEIGHT}" />
      <text class="band-label" x="{_BAND_X + _ACCENT_WIDTH + 8}" y="{label_y}">{label}</text>
      <g class="status">
        <circle cx="{status_cx}" cy="{status_cy}" r="6" />
      </g>
      <g class="on-demand" aria-hidden="true"></g>
    </g>'''


def _render_output(action: str, force: str) -> str:
    text_x = _OUTPUT_X + _OUTPUT_WIDTH // 2
    action_y = _OUTPUT_Y + 35
    force_y = _OUTPUT_Y + 60
    return f'''  <g class="output" data-force="{force}">
    <rect class="output-bg" x="{_OUTPUT_X}" y="{_OUTPUT_Y}" width="{_OUTPUT_WIDTH}" height="{_OUTPUT_HEIGHT}" fill="#FAFAFA" stroke="#333333" stroke-width="1" />
    <text class="output-action" x="{text_x}" y="{action_y}" text-anchor="middle" font-weight="bold">{action}</text>
    <text class="output-force" x="{text_x}" y="{force_y}" text-anchor="middle">{force.upper()}</text>
  </g>'''


def _render_force_scale(active_force: str) -> str:
    ticks = []
    for i, level in enumerate(_FORCE_ORDER):
        tick_y = _SCALE_Y0 + i * _SCALE_STEP
        is_active = level == active_force
        ticks.append(
            f'      <g class="tick" data-level="{level}" data-active="{_bool_attr(is_active)}">'
            f'<line x1="{_SCALE_X}" y1="{tick_y}" x2="{_SCALE_X + 10}" y2="{tick_y}" '
            f'stroke="#333333" stroke-width="{2 if is_active else 1}" />'
            f'<text x="{_SCALE_X + 14}" y="{tick_y + 4}" font-size="11">{level}</text>'
            f'</g>'
        )
    ticks_svg = "\n".join(ticks)
    return f'''  <g class="force-scale">
{ticks_svg}
  </g>'''


def _render_style() -> str:
    css = Path(__file__).with_name("cascade_styles.css").read_text()
    return f'<style>{css}</style>'


def _render_defs() -> str:
    return '''  <defs>
    <marker id="cascade-arrowhead" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="8" markerHeight="8" orient="auto-start-reverse" markerUnits="userSpaceOnUse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
    </marker>
  </defs>'''


def _render_safety_arrow(cue: Cue) -> str:
    if not cue.safety_modified or cue.primary_firing is None:
        return ""
    base_force = cue.primary_firing.base_force
    modified_force = cue.primary_force
    try:
        i_from = _FORCE_ORDER.index(base_force)
        i_to = _FORCE_ORDER.index(modified_force)
    except ValueError:
        return ""
    y_from = _SCALE_Y0 + i_from * _SCALE_STEP
    y_to = _SCALE_Y0 + i_to * _SCALE_STEP
    x = _SCALE_X - 8
    return (
        f'  <g class="safety-modifier" color="#D55E00">\n'
        f'    <path class="safety-arrow" d="M {x} {y_from} L {x} {y_to}" '
        f'marker-end="url(#cascade-arrowhead)" />\n'
        f'  </g>'
    )


def _render_resolution(winner_index: int) -> str:
    start_x = _BAND_X + _BAND_WIDTH
    start_y = _band_y(winner_index) + _BAND_HEIGHT // 2
    end_x = _OUTPUT_X
    end_y = _OUTPUT_Y + _OUTPUT_HEIGHT // 2
    mid_x = (start_x + end_x) // 2
    return f'''  <g class="resolution">
    <path class="resolution-arrow" d="M {start_x} {start_y} L {mid_x} {start_y} L {mid_x} {end_y} L {end_x} {end_y}" marker-end="url(#cascade-arrowhead)" />
  </g>'''


def render_cascade(
    case: Case,
    cue: Cue,
    *,
    reveal: str = "none",
    width: int = 640,
    height: int = 400,
    css: bool = True,
    interactive: bool = True,
) -> str:
    """
    Return a complete SVG fragment that renders the composition trace for `case` and `cue`.

    - reveal="none" -> compact variant (Figures 1 and 2).
    - reveal="all"  -> detailed variant with on-demand layer expanded (Figure 3).
    - css / interactive are placeholders in 2a; wired in 2b / 2c.
    """
    winner_class = (
        cue.primary_firing.rule.rule_class if cue.primary_firing else None
    )
    fired_classes = {f.rule.rule_class for f in cue.supporting}
    if cue.primary_firing:
        fired_classes.add(winner_class)

    bands = "\n".join(
        _render_band(
            rule_class=cls,
            fired=cls in fired_classes,
            is_winner=cls == winner_class,
            y=_band_y(i),
        )
        for i, cls in enumerate(_CLASS_ORDER)
    )

    if winner_class is not None:
        resolution = _render_resolution(_CLASS_ORDER.index(winner_class))
    else:
        resolution = '  <g class="resolution"></g>'

    output = _render_output(cue.primary_action, cue.primary_force)
    scale = _render_force_scale(cue.primary_force)
    safety = _render_safety_arrow(cue)
    style = _render_style() if css else ""
    defs = _render_defs()

    return f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" class="cascade" data-reveal="{reveal}" xmlns="http://www.w3.org/2000/svg">
{defs}
  {style}
  <g class="back-references"></g>
  <g class="cascade-bands">
{bands}
  </g>
{resolution}
{output}
{scale}
{safety}
</svg>'''
