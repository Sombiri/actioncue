(function () {
  const root = document.currentScript.parentNode.querySelector('.cascade');
  if (!root) return;

  const tooltip = document.createElement('div');
  tooltip.className = 'cascade-tooltip';
  tooltip.style.cssText = 'position:absolute; pointer-events:none; padding:6px 10px; '
    + 'background:#212121; color:#fff; border-radius:4px; font:12px sans-serif; '
    + 'opacity:0; transition:opacity 80ms; z-index:1000;';
  document.currentScript.parentNode.appendChild(tooltip);

  function showTip(el, text, ev) {
    tooltip.textContent = text;
    tooltip.style.left = (ev.pageX + 12) + 'px';
    tooltip.style.top  = (ev.pageY + 12) + 'px';
    tooltip.style.opacity = '1';
  }
  function hideTip() { tooltip.style.opacity = '0'; }

  // Bands: hover tooltip + click-to-expand
  root.querySelectorAll('.band').forEach(band => {
    const cls = band.dataset.class;
    const fired = band.dataset.fired === 'true';
    const rationale = band.dataset.rationale || '';
    const signalLabel = band.dataset.signalLabel || '';

    band.addEventListener('mouseenter', ev => {
      const text = fired
        ? cls + ' — fired (' + signalLabel + '): ' + rationale
        : cls + ' — did not fire';
      showTip(band, text, ev);
    });
    band.addEventListener('mousemove', ev => {
      tooltip.style.left = (ev.pageX + 12) + 'px';
      tooltip.style.top  = (ev.pageY + 12) + 'px';
    });
    band.addEventListener('mouseleave', hideTip);

    if (fired) {
      band.style.cursor = 'pointer';
      band.addEventListener('click', () => {
        const expanded = band.dataset.expanded === 'true';
        band.dataset.expanded = expanded ? 'false' : 'true';
      });
    }
  });

  // Resolution arrow: hover tooltip
  const arrow = root.querySelector('.resolution-arrow');
  if (arrow) {
    arrow.addEventListener('mouseenter', ev => {
      showTip(arrow, arrow.dataset.tip || '', ev);
    });
    arrow.addEventListener('mouseleave', hideTip);
  }

  // Force-scale ticks: hover tooltip
  root.querySelectorAll('.force-scale .tick').forEach(tick => {
    tick.addEventListener('mouseenter', ev => {
      showTip(tick, tick.dataset.tip || '', ev);
    });
    tick.addEventListener('mouseleave', hideTip);
  });

  // Safety modifier arrow: hover tooltip
  const safetyArrow = root.querySelector('.safety-modifier');
  if (safetyArrow) {
    safetyArrow.addEventListener('mouseenter', ev => {
      showTip(safetyArrow, safetyArrow.dataset.tip || '', ev);
    });
    safetyArrow.addEventListener('mouseleave', hideTip);
  }
})();
