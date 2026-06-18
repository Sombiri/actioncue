import html
from pathlib import Path
from typing import Optional

from models import Case, Cue, RuleFiring
from viz._common import bool_attr, wrap_text, render_style


_CLASS_ORDER = ["validity", "completion", "sensitivity", "interpretation"]
_FORCE_ORDER = ["advisory", "strong", "mandatory", "blocking"]
_FORCE_TOOLTIPS = {
    "advisory":  "Advisory — low-emphasis info",
    "strong":    "Strong — recommended attention",
    "mandatory": "Mandatory — response required",
    "blocking":  "Blocking — action prevented",
}


# Layout in viewBox units.
_BAND_X = 40
_BAND_WIDTH = 320
_BAND_HEIGHT = 80
_BAND_GAP = 10
_BAND_Y0 = 20
_ACCENT_WIDTH = 6

_OUTPUT_X = 420
_OUTPUT_Y = 140
_OUTPUT_WIDTH = 140
_OUTPUT_HEIGHT = 100

_SCALE_X = 620
_SCALE_Y0 = 20
_SCALE_STEP = 90


def _band_y(index: int) -> int:
    return _BAND_Y0 + index * (_BAND_HEIGHT + _BAND_GAP)


def _render_band(rule_class: str, fired: bool, is_winner: bool, y: int, firing: Optional[RuleFiring] = None) -> str:
    label = rule_class.capitalize()
    label_y = y + 30
    status_cx = _BAND_X + _BAND_WIDTH - 20
    status_cy = y + _BAND_HEIGHT // 2
    text_x = _BAND_X + _ACCENT_WIDTH + 8
    if firing is not None:
        rationale = html.escape(firing.rendered_rationale, quote=True)
        signal_label = html.escape(firing.triggering_signal.label, quote=True) if firing.triggering_signal else ""
        data_attrs = f' data-rationale="{rationale}" data-signal-label="{signal_label}"'
        rationale_lines = wrap_text(rationale, max_chars=46)
        rationale_tspans = "".join(
            f'<tspan x="{text_x}" dy="{0 if i == 0 else 11}">{line}</tspan>'
            for i, line in enumerate(rationale_lines)
        )
        # Always-visible rationale sits just below the band label. Visible in
        # both reveal="none" (Figure 1) and reveal="all" (Figure 3) — it's the
        # primary content of a fired band, not on-demand.
        band_rationale = (
            f'<text class="band-rationale" x="{text_x}" y="{y + 48}">{rationale_tspans}</text>'
        )
        # On-demand layer carries only what's reader-useful and not already
        # shown: the triggering-signal label. Rationale is in band_rationale
        # above. Rule id (e.g. "completion_missing_critical") is a debugging
        # identifier, not reader content, so we drop it from the visible
        # on-demand layer — it stays in data-rationale on the band group for
        # the interactive layer's tooltip if needed.
        # Position: just below band-rationale, computed from the actual
        # number of wrapped rationale lines so it never overflows the band.
        signal_y = y + 48 + 11 * max(1, len(rationale_lines)) + 6
        on_demand_content = (
            f'<text class="on-demand-signal" x="{text_x}" y="{signal_y}">from signal: {signal_label}</text>'
        )
    else:
        data_attrs = ""
        band_rationale = ""
        on_demand_content = ""
    return f'''    <g class="band" data-class="{rule_class}" data-fired="{bool_attr(fired)}" data-winner="{bool_attr(is_winner)}"{data_attrs}>
      <rect class="band-bg" x="{_BAND_X}" y="{y}" width="{_BAND_WIDTH}" height="{_BAND_HEIGHT}" />
      <rect class="band-accent" x="{_BAND_X}" y="{y}" width="{_ACCENT_WIDTH}" height="{_BAND_HEIGHT}" />
      <text class="band-label" x="{text_x}" y="{label_y}">{label}</text>
      {band_rationale}
      <g class="status">
        <circle cx="{status_cx}" cy="{status_cy}" r="6" />
      </g>
      <g class="on-demand" aria-hidden="true">
        {on_demand_content}
      </g>
    </g>'''


def _render_output(action: str, force: str, rule_class: Optional[str] = None) -> str:
    """Render the cascade's canonical cue display (now absorbing what was
    Panel 4 in earlier iterations): action word + force-tint pill + optional
    "via {rule_class}" caption.

    The action is the typographic hero; the pill is the visual hero (force
    tint at full strength); the "via" caption anchors the cue to the band
    that produced it.
    """
    text_x = _OUTPUT_X + _OUTPUT_WIDTH // 2

    # Action word at the top of the output box.
    action_y = _OUTPUT_Y + 28

    # Force pill below the action.
    pill_w = _OUTPUT_WIDTH - 24            # 12-unit inset on each side
    pill_x = _OUTPUT_X + 12
    pill_top_y = _OUTPUT_Y + 42
    pill_h = 24
    pill_text_y = pill_top_y + 16

    # "via {rule_class}" caption at the bottom (only when a rule won).
    via_y = pill_top_y + pill_h + 18

    force_attr = html.escape(force, quote=True)
    action_word = html.escape(action.upper())
    force_word = html.escape(force.upper())

    if rule_class is not None:
        via = (
            f'    <text class="cue-via" x="{text_x}" y="{via_y}" text-anchor="middle">'
            f'via {html.escape(rule_class)}</text>'
        )
    else:
        via = ""

    return f'''  <g class="output" data-force="{force_attr}">
    <text class="cue-action" x="{text_x}" y="{action_y}" text-anchor="middle">{action_word}</text>
    <rect class="force-pill" data-force="{force_attr}" x="{pill_x}" y="{pill_top_y}" width="{pill_w}" height="{pill_h}" rx="12" />
    <text class="force-word" data-force="{force_attr}" x="{text_x}" y="{pill_text_y}" text-anchor="middle">{force_word}</text>
{via}
  </g>'''


def _render_force_scale(active_force: str) -> str:
    ticks = []
    for i, level in enumerate(_FORCE_ORDER):
        tick_y = _SCALE_Y0 + i * _SCALE_STEP
        is_active = level == active_force
        tip = _FORCE_TOOLTIPS[level] + (" (current)" if is_active else "")
        ticks.append(
            f'<g class="tick" data-level="{level}" data-active="{bool_attr(is_active)}" data-tip="{tip}">'
            f'<line x1="{_SCALE_X}" y1="{tick_y}" x2="{_SCALE_X + 10}" y2="{tick_y}" '
            f'stroke="#333333" stroke-width="{2 if is_active else 1}" />'
            f'<text x="{_SCALE_X + 14}" y="{tick_y + 4}" font-size="11">{level}</text>'
            f'</g>'
        )
    ticks_svg = "\n".join(ticks)
    return f'''  <g class="force-scale">
{ticks_svg}
  </g>'''


def _render_script() -> str:
    js = Path(__file__).with_name("cascade_interact.js").read_text()
    return f'<script>{js}</script>'


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
    tip = f"Force raised from {base_force} to {modified_force} due to {cue.safety_reason}"
    tip = html.escape(tip, quote=True)
    return (
        f'  <g class="safety-modifier" color="#D55E00" data-tip="{tip}">\n'
        f'    <path class="safety-arrow" d="M {x} {y_from} L {x} {y_to}" '
        f'marker-end="url(#cascade-arrowhead)" />\n'
        f'  </g>'
    )


def _render_resolution(winner_index: int, interactive: bool = True, include_output_box: bool = True, include_force_scale: bool = True) -> str:
    start_x = _BAND_X + _BAND_WIDTH
    start_y = _band_y(winner_index) + _BAND_HEIGHT // 2
    if include_output_box:
        end_x = _OUTPUT_X
        # Land on the force pill's vertical center (pill is the visual hero
        # of the output box and reads as the "endpoint" of the resolution).
        end_y = _OUTPUT_Y + 42 + 12  # pill_top_y + pill_h/2
    else:
        # No output box: straight horizontal arrow at the winner-band mid-y.
        # When the force scale is also gone, the arrow can extend further
        # right (no scale column to clear), making the handoff to Panel 4
        # in the composite feel confident rather than stubby.
        end_y = start_y
        if include_force_scale:
            # Scale still present: keep the arrow short so it doesn't run
            # into the scale ticks.
            end_x = _OUTPUT_X - 30
        else:
            # No scale either: extend ~140 units past the bands' right edge,
            # close to where the cascade's effective right boundary sits in
            # the composite (Panel 4 picks up immediately to the right).
            end_x = start_x + 140
    mid_x = (start_x + end_x) // 2
    return f'''  <g class="resolution">
    <path class="resolution-arrow" data-tip="highest-precedence fired class wins" d="M {start_x} {start_y} L {mid_x} {start_y} L {mid_x} {end_y} L {end_x} {end_y}" marker-end="url(#cascade-arrowhead)" />
  </g>'''


def render_cascade(
    case: Case,
    cue: Cue,
    *,
    reveal: str = "none",
    width: int = 720,
    height: int = 400,
    css: bool = True,
    interactive: bool = True,
    include_output_box: bool = True,
    include_force_scale: bool = True,
) -> str:
    """
    Return a complete SVG fragment that renders the composition trace for `case` and `cue`.

    - reveal="none" -> compact variant (Figures 1 and 2).
    - reveal="all"  -> detailed variant with on-demand layer expanded (Figure 3).
    - css / interactive are placeholders in 2a; wired in 2b / 2c.
    - include_output_box: when False, suppresses the output rectangle and
      truncates the resolution arrow so it ends mid-air pointing right.
      Used by the four-panel compositor so Panel 4 carries the canonical
      action+force display (resolves Panel 3/4 redundancy). Default True
      preserves standalone behavior (Figure 3, the live demo).
    - include_force_scale: when False, suppresses the vertical force scale
      and the safety-modifier arrow (the safety arrow loses its anchor
      without the scale). Used by the four-panel compositor; Panel 4's
      force pill + safety banner cover this data canonically. Default True
      preserves standalone behavior.
    """
    winner_class = (
        cue.primary_firing.rule.rule_class if cue.primary_firing else None
    )
    fired_classes = {f.rule.rule_class for f in cue.supporting}
    if cue.primary_firing:
        fired_classes.add(winner_class)

    firings_by_class: dict[str, RuleFiring] = {}
    if cue.primary_firing:
        firings_by_class[cue.primary_firing.rule.rule_class] = cue.primary_firing
    for f in cue.supporting:
        firings_by_class[f.rule.rule_class] = f

    bands = "\n".join(
        _render_band(
            rule_class=cls,
            fired=cls in fired_classes,
            is_winner=cls == winner_class,
            y=_band_y(i),
            firing=firings_by_class.get(cls),
        )
        for i, cls in enumerate(_CLASS_ORDER)
    )

    if winner_class is not None:
        resolution = _render_resolution(
            _CLASS_ORDER.index(winner_class),
            interactive=interactive,
            include_output_box=include_output_box,
            include_force_scale=include_force_scale,
        )
    else:
        resolution = '  <g class="resolution"></g>'

    primary_class = cue.primary_firing.rule.rule_class if cue.primary_firing else None
    output = _render_output(cue.primary_action, cue.primary_force, primary_class) if include_output_box else ""
    scale = _render_force_scale(cue.primary_force) if include_force_scale else ""
    safety = _render_safety_arrow(cue) if include_force_scale else ""
    style = render_style("cascade_styles.css") if css else ""
    script = _render_script() if interactive else ""
    defs = _render_defs()

    svg_body = f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" class="cascade" data-reveal="{reveal}" xmlns="http://www.w3.org/2000/svg">
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

    if interactive:
        return f'<div class="cascade-wrapper">\n{svg_body}\n{script}\n</div>'
    return svg_body
