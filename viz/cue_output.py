"""Panel 4 — cue output renderer.

One public function:
    render_cue_output(cue) — full Panel 4 SVG.

Layout (Alternative A — single dominant card):
    - Section label "ACTION CUE" at the top.
    - Centered card occupying most of the panel:
        - Action word (large, bold) — typographic hero
        - Force pill (rounded rect, force-tint background) — visual hero
        - "via {rule_class}" small muted line at the card's bottom
    - Safety banner outside and below the card, only when
      cue.safety_modified is true: vermillion accent strip +
      caption "Force raised from {base_force} to {primary_force}:
      {safety_reason}". Visual rhyme with Panel 2's detected-rail
      vermillion accent.

Design refinements applied:
    1. Card border uses the force tint at a subtle stroke weight;
       the pill carries the same tint at full strength inside.
       Avoids two-tints-stacking. CSS keys both off data-force.
    2. Safety banner reuses Panel 2's vermillion accent-strip
       vocabulary so vermillion across all four panels always
       means "needs attention".

The safety-banner region is always reserved at the panel bottom
so the card geometry doesn't shift between cases — cases with a
banner look the same shape as cases without.
"""

import html

from models import Cue
from viz._common import render_style


# --- Outer panel layout (viewBox units) ---
_PANEL_PAD_X = 16
_SECTION_LABEL_Y = 20

# --- Content geometry ---
# Panel 4 has no inner card border (the cell boundary in the composite is
# the only framing needed). Action + pill + "via" are stacked and centered
# vertically in the panel. Safety banner reserves a strip at the bottom
# regardless of whether it fires, so the cue stack's geometry is stable
# across cases.

# Vertical anchors for the cue stack (computed against panel height in
# render_cue_output so the stack centers itself in the available space
# above the safety-banner region).
_CUE_STACK_HEIGHT = 100       # action (~32) + gap + pill (28) + gap + via (~14)
_ACTION_TO_PILL_GAP = 14
_PILL_TO_VIA_GAP = 16

# Force pill
_PILL_HEIGHT = 32
_PILL_PAD_X = 40              # horizontal inset inside the panel
_PILL_BORDER_RADIUS = 16      # pill = half-height
_PILL_TEXT_DY = 21            # text baseline relative to pill top

# --- Safety banner (bottom strip) ---
_BANNER_HEIGHT = 32
_BANNER_RESERVED_H = 48       # vertical space reserved at the bottom of the panel
_BANNER_ACCENT_W = 3
_BANNER_TEXT_X = _PANEL_PAD_X + 12
_BANNER_TEXT_DY = 12          # title baseline relative to banner top
_BANNER_DETAIL_DY = 26        # detail baseline relative to banner top


# --- Force tint table (CVD-safe, locked in 2b / §9) ---
# Used by CSS via data-force="..." selectors; the dict here is documentation
# only — the actual color rules live in cue_output_styles.css. Keeping the
# table in the renderer would duplicate it.
_FORCE_LEVELS = ["advisory", "strong", "mandatory", "blocking"]


# ---------------------------------------------------------------------------
# Card components
# ---------------------------------------------------------------------------

def _render_force_pill(force: str, panel_width: int, pill_top_y: int) -> str:
    """The force pill: rounded rect with force-tint fill, force word centered.

    Fill and text color are set by CSS keyed off data-force.
    """
    pill_x = _PANEL_PAD_X + _PILL_PAD_X
    pill_w = panel_width - 2 * _PANEL_PAD_X - 2 * _PILL_PAD_X
    center_x = pill_x + pill_w // 2
    text_y = pill_top_y + _PILL_TEXT_DY
    force_word = html.escape(force.upper())
    force_attr = html.escape(force, quote=True)
    return f'''    <rect class="force-pill" data-force="{force_attr}"
          x="{pill_x}" y="{pill_top_y}" width="{pill_w}" height="{_PILL_HEIGHT}"
          rx="{_PILL_BORDER_RADIUS}" />
    <text class="force-word" data-force="{force_attr}"
          x="{center_x}" y="{text_y}" text-anchor="middle">{force_word}</text>'''


def _render_cue_stack(cue: Cue, panel_width: int, panel_height: int) -> str:
    """The cue: action, force pill, 'via {rule_class}' caption.

    No inner card border — the panel itself is the container. The stack
    is vertically centered in the available space above the safety-banner
    reserved region, so the cue commands the panel.
    """
    center_x = panel_width // 2

    # Available vertical space sits between the section label (~30 units
    # from the top) and the reserved safety-banner strip at the bottom.
    available_top = _SECTION_LABEL_Y + 16
    available_bot = panel_height - _BANNER_RESERVED_H
    available_h = available_bot - available_top

    # Center the stack in the available region.
    stack_top = available_top + (available_h - _CUE_STACK_HEIGHT) // 2

    action_y = stack_top + 30                 # baseline
    pill_top_y = action_y + _ACTION_TO_PILL_GAP
    via_y = pill_top_y + _PILL_HEIGHT + _PILL_TO_VIA_GAP

    action = html.escape(cue.primary_action.upper())
    force_attr = html.escape(cue.primary_force, quote=True)

    if cue.primary_firing is not None:
        rule_class = html.escape(cue.primary_firing.rule.rule_class)
        via = f'    <text class="cue-via" x="{center_x}" y="{via_y}" text-anchor="middle">via {rule_class}</text>'
    else:
        via = ""

    pill = _render_force_pill(cue.primary_force, panel_width, pill_top_y)

    return f'''  <g class="cue-stack" data-force="{force_attr}">
    <text class="cue-action" x="{center_x}" y="{action_y}" text-anchor="middle">{action}</text>
{pill}
{via}
  </g>'''


# ---------------------------------------------------------------------------
# Safety banner (absent when not fired)
# ---------------------------------------------------------------------------

def _render_safety_banner(cue: Cue, panel_width: int, panel_height: int) -> str:
    """Vermillion accent strip + caption, only when cue.safety_modified.

    Banner sits in the reserved strip at the bottom of the panel. Returns
    "" when no safety lift fired, so the DOM is clean.
    """
    if not cue.safety_modified or cue.primary_firing is None:
        return ""

    base_force = html.escape(cue.primary_firing.base_force)
    primary_force = html.escape(cue.primary_force)
    reason = html.escape(cue.safety_reason or "")

    title = f"Force raised from {base_force} to {primary_force}"
    detail = f"Reason: {reason}" if reason else ""

    banner_w = panel_width - 2 * _PANEL_PAD_X
    banner_top_y = panel_height - _BANNER_RESERVED_H + 8

    title_y = banner_top_y + _BANNER_TEXT_DY
    detail_y = banner_top_y + _BANNER_DETAIL_DY

    detail_block = (
        f'    <text class="safety-detail" x="{_BANNER_TEXT_X}" y="{detail_y}">{detail}</text>'
        if detail else ""
    )

    return f'''  <g class="safety-banner">
    <rect class="safety-bg" x="{_PANEL_PAD_X}" y="{banner_top_y}"
          width="{banner_w}" height="{_BANNER_HEIGHT}" rx="4" />
    <rect class="safety-accent" x="{_PANEL_PAD_X}" y="{banner_top_y}"
          width="{_BANNER_ACCENT_W}" height="{_BANNER_HEIGHT}" />
    <text class="safety-title" x="{_BANNER_TEXT_X}" y="{title_y}">{title}</text>
{detail_block}
  </g>'''


# ---------------------------------------------------------------------------
# Public renderer
# ---------------------------------------------------------------------------

def render_cue_output(cue: Cue, *, width: int = 360, height: int = 220,
                      css: bool = True, interactive: bool = False) -> str:
    """Panel 4 SVG: section label, action card, optional safety banner.

    `interactive` is accepted for compositor signature compatibility and
    ignored — Panel 4 has no JS affordances in 2d-3.
    """
    style = render_style("cue_output_styles.css") if css else ""
    section_label = (
        f'  <text class="section-label" x="{_PANEL_PAD_X}" y="{_SECTION_LABEL_Y}">ACTION CUE</text>'
    )
    stack = _render_cue_stack(cue, width, height)
    banner = _render_safety_banner(cue, width, height)

    return f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" class="cue-output" xmlns="http://www.w3.org/2000/svg">
  {style}
{section_label}
{stack}
{banner}
</svg>'''
