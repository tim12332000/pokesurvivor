/* ============ layout-ui.js — colocar los botones (móvil) ============
 * Ajustes > Controles > Colocar los botones: se ven los ataques (con el
 * objeto), la pausa y, si es fijo, el joystick, y se arrastran a donde se
 * quiera. Se guarda el centro de cada cosa en proporción a la pantalla
 * (G.Settings 'pad' / 'padPortrait'); lo que no se mueve se queda en su sitio de siempre.
 * El HUD (hud.js) y el joystick (touch.js) leen esas posiciones.
 * Las medidas copian las del HUD: si cambian allí, cambiarlas aquí.
 */
G.LayoutUI = (() => {
  const N = 4;
  let el = null, pos = null, moved = null, mode = 'float';

  /** Dónde está cada cosa ahora mismo (centro en px), con lo guardado o lo de siempre. */
  function current(k, w, h) {
    if (k === 'stick') { const b = G.Touch.stickBase(w, h); return [b.x, b.y]; }
    const rect = G.Touch.controlLayout(w, h, N)[k];
    return [rect.x + rect.w / 2, rect.y + rect.h / 2];
  }

  /** Match the same control bounds used by the canvas HUD. */
  function fit(k, x, y, w, h) {
    const layout = G.Touch.controlLayout(w, h, N);
    const sa = G.Touch.safeArea();
    if (k === 'bar') {
      const b = layout.bar;
      return [G.U.clamp(x, sa.left + 6 + b.w / 2, Math.max(sa.left + 6 + b.w / 2, w - sa.right - b.w / 2 - 6)), G.U.clamp(y, sa.top + 24 + b.h / 2, Math.max(sa.top + 24 + b.h / 2, h - sa.bottom - b.h / 2 - 18))];
    }
    if (k === 'pause') {
      const r = layout.pause.w / 2;
      return [G.U.clamp(x, sa.left + r + 4, w - sa.right - r - 4), G.U.clamp(y, sa.top + r + 10, h - sa.bottom - r - 4)];
    }
    const r = G.Touch.R();
    return [G.U.clamp(x, r + 4, w - r - 4), G.U.clamp(y, r + 4, h - r - 4)];
  }

  function build() {
    el = document.createElement('section');
    el.id = 'scr-layout';
    el.className = 'scr hidden';
    const slots = Array.from({ length: N }, (_, i) => `<div class="lay-slot${i === 0 ? ' on' : ''}"><i>${i + 1}</i></div>`).join('');
    el.innerHTML = `
      <div class="lay-thing lay-bar" data-k="bar"><div class="lay-slot item"></div>${slots}<span class="lay-tag">Ataques</span></div>
      <div class="lay-thing lay-pause" data-k="pause"><b></b><b></b></div>
      <div class="lay-thing lay-stick" data-k="stick"><div class="knob"></div><span class="lay-tag">Joystick</span></div>
      <div class="box lay-panel">
        <h3>Arrastra los botones a donde quieras</h3>
        <p class="lay-turn">Puedes jugar en vertical o en horizontal.</p>
        <div class="chips set-chips" id="lay-mode"><b>Joystick</b>
          <button class="chip" data-m="float">Flotante</button><button class="chip" data-m="fixed">Fijo</button>
        </div>
        <small class="lay-help">Flotante: aparece donde pones el dedo. Fijo: siempre en el mismo sitio.</small>
        <div class="row wrap lay-btns">
          <button class="btn small ghost" id="lay-cancel">Cancelar</button>
          <button class="btn small" id="lay-reset">Restablecer</button>
          <button class="btn small gold" id="lay-save">Guardar</button>
        </div>
      </div>`;
    document.body.appendChild(el);
    el.querySelectorAll('.lay-thing').forEach(drag);
    el.querySelectorAll('#lay-mode .chip').forEach(b => { b.onclick = () => { mode = b.dataset.m; paint(); }; });
    el.querySelector('#lay-cancel').onclick = close;
    el.querySelector('#lay-reset').onclick = () => {
      moved = {}; mode = 'float';
      const w = innerWidth, h = innerHeight;
      const layout = G.Touch.controlLayout(w, h, N, { defaults: true });
      const stick = G.Touch.stickBase(w,h,{defaults:true});
      pos = { bar: [layout.bar.x + layout.bar.w / 2, layout.bar.y + layout.bar.h / 2],
              pause: [layout.pause.x + layout.pause.w / 2, layout.pause.y + layout.pause.h / 2],
              stick: [stick.x,stick.y] };
      for (const k in pos) pos[k] = fit(k, pos[k][0], pos[k][1], w, h);
      paint();
    };
    el.querySelector('#lay-save').onclick = save;
    addEventListener('resize', () => { if (isOpen()) { load(); paint(); } });
  }

  function drag(node) {
    const k = node.dataset.k;
    let off = null;
    node.addEventListener('pointerdown', e => {
      e.preventDefault();
      off = [e.clientX - pos[k][0], e.clientY - pos[k][1]];
      node.classList.add('held');
      try { node.setPointerCapture(e.pointerId); } catch (err) { /* nada */ }
    });
    node.addEventListener('pointermove', e => {
      if (!off) return;
      pos[k] = fit(k, e.clientX - off[0], e.clientY - off[1], innerWidth, innerHeight);
      moved[k] = true;
      paint();
    });
    const up = () => { off = null; node.classList.remove('held'); };
    node.addEventListener('pointerup', up);
    node.addEventListener('pointercancel', up);
  }

  function load() {
    const w = innerWidth, h = innerHeight;
    pos = {}; moved = {};
    for (const k of ['bar', 'pause', 'stick']) {
      const c = current(k, w, h);
      pos[k] = fit(k, c[0], c[1], w, h);
      moved[k] = !!G.Touch.spot(k);
    }
  }

  function paint() {
    const r = G.Touch.R();
    const place = (k, ww, hh) => {
      const n = el.querySelector(`[data-k="${k}"]`);
      n.style.left = (pos[k][0] - ww / 2) + 'px'; n.style.top = (pos[k][1] - hh / 2) + 'px';
      n.style.width = ww + 'px'; n.style.height = hh + 'px';
      return n;
    };
    const layout = G.Touch.controlLayout(innerWidth, innerHeight, N);
    const bar = place('bar', layout.bar.w, layout.bar.h);
    bar.classList.toggle('portrait', layout.portrait);
    const slots = bar.querySelectorAll('.lay-slot');
    [layout.item, ...layout.slots].forEach((rect, i) => {
      const node = slots[i];
      node.style.position = 'absolute';
      node.style.left = rect.x - layout.bar.x + 'px';
      node.style.top = rect.y - layout.bar.y + 'px';
      node.style.width = rect.w + 'px';
      node.style.height = rect.h + 'px';
      node.style.margin = '0';
      node.style.transform = i === 1 ? 'translateY(-4px) scale(1.12)' : '';
    });
    place('pause', layout.pause.w, layout.pause.h);
    place('stick', r * 2, r * 2).classList.toggle('hidden', mode !== 'fixed');
    el.querySelectorAll('#lay-mode .chip').forEach(b => b.classList.toggle('on', b.dataset.m === mode));
    el.querySelector('.lay-turn').classList.remove('hidden');
  }

  function save() {
    const w = innerWidth, h = innerHeight, pad = {};
    for (const k in pos) if (moved[k]) pad[k] = [+(pos[k][0] / w).toFixed(4), +(pos[k][1] / h).toFixed(4)];
    G.Settings.set(G.Touch.padKey(), Object.keys(pad).length ? pad : null);
    G.Settings.set('stickMode', mode);
    G.UI.toast('Botones colocados');
    close();
  }

  function open() {
    if (!el) build();
    mode = G.Settings.get('stickMode') === 'fixed' ? 'fixed' : 'float';
    load();
    el.classList.remove('hidden');
    paint();
  }
  function close() { if (el) el.classList.add('hidden'); }
  const isOpen = () => !!el && !el.classList.contains('hidden');

  return { open, close, get isOpen() { return isOpen(); } };
})();
