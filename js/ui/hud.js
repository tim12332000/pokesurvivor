/* ============ hud.js — interfaz dentro del canvas ============
 * Se dibuja en coordenadas de PANTALLA (sin la transformación de cámara).
 */
G.HUD = (() => {
  const F = (w, s) => `${w} ${s}px Pixelify,"Segoe UI",system-ui,sans-serif`;

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function bar(ctx, x, y, w, h, frac, col, bg = 'rgba(0,0,0,.55)') {
    roundRect(ctx, x, y, w, h, h / 2); ctx.fillStyle = bg; ctx.fill();
    if (frac > 0) {
      ctx.save();
      roundRect(ctx, x, y, w, h, h / 2); ctx.clip();
      ctx.fillStyle = col;
      ctx.fillRect(x, y, w * G.U.clamp(frac, 0, 1), h);
      ctx.restore();
    }
  }

  function draw(ctx, w, h, pl, st) {
    ctx.save();
    ctx.textBaseline = 'alphabetic';
    G.Touch.clearButtons();
    const touch = G.Touch.active;
    const groups = [...pl.slots, ...pl.moves.filter(move => move.passive && !pl.slots.some(group => group.includes(move))).map(move => [move])];
    const controls = touch ? G.Touch.controlLayout(w, h, Math.max(1, groups.length)) : null;
    const portrait = !!(controls && controls.portrait);
    const safeTop = portrait ? Math.min(44, G.Touch.safeArea().top) : 0;

    // ---------- barra de experiencia (borde superior) ----------
    const xpF = pl.xp / pl.xpNext;
    ctx.fillStyle = 'rgba(0,0,0,.5)';
    ctx.fillRect(0, 0, w, 7);
    const g = ctx.createLinearGradient(0, 0, w, 0);
    g.addColorStop(0, '#4fd1ff'); g.addColorStop(1, '#a98bff');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w * G.U.clamp(xpF, 0, 1), 7);

    // ---------- vida + nivel ----------
    const px = 16, py = 20 + safeTop;
    ctx.font = F(800, 13);
    ctx.fillStyle = '#eaf2ff';
    ctx.textAlign = 'left';
    ctx.fillText(pl.mon.name, px, py + 10, portrait ? w - 90 : w);

    ctx.font = F(700, 11);
    ctx.fillStyle = '#ffcb3d';
    ctx.fillText('Nv. ' + pl.level, px, py + 26);

    bar(ctx, px + 48, py + 17, 168, 11, pl.hp / pl.maxHp, '#ff5f6d');
    ctx.font = F(700, 10);
    ctx.fillStyle = 'rgba(255,255,255,.95)';
    ctx.textAlign = 'center';
    ctx.fillText(Math.ceil(pl.hp) + ' / ' + Math.round(pl.maxHp), px + 48 + 84, py + 26);

    // buffs activos
    const COL = { atk: '#ff6b4d', spd: '#7fe0ff', def: '#b0b8c8', regen: '#5fe08a' };
    const LBL = { atk: 'ATK', spd: 'VEL', def: 'DEF', regen: 'REG' };
    let bx = px;
    ctx.textAlign = 'left';
    for (const k in pl.buffs) {
      const b = pl.buffs[k];
      if (b.n <= 0) continue;
      ctx.font = F(800, 9);
      const txt = LBL[k] + ' ×' + b.n;
      const tw = ctx.measureText(txt).width + 12;
      roundRect(ctx, bx, py + 34, tw, 15, 7);
      ctx.fillStyle = 'rgba(0,0,0,.5)'; ctx.fill();
      ctx.fillStyle = COL[k];
      ctx.fillText(txt, bx + 6, py + 45);
      bx += tw + 5;
    }

    // Run controls stay below health/buffs, with room for touch targets.
    const runButtonY = py + 56;
    const runButton = (x, width, text, on, action, enabled = true) => {
      roundRect(ctx, x, runButtonY, width, 36, 8);
      ctx.fillStyle = on ? 'rgba(45,57,79,.96)' : 'rgba(10,16,28,.9)'; ctx.fill();
      ctx.strokeStyle = on ? '#ffd23f' : 'rgba(140,170,210,.55)'; ctx.lineWidth = 1.5; ctx.stroke();
      ctx.font = F(700, 12); ctx.textAlign = 'center';
      ctx.fillStyle = enabled ? (on ? '#ffd23f' : '#eaf2ff') : '#8fa3c4';
      ctx.fillText(text, x + width / 2, runButtonY + 23);
      if (enabled) G.Touch.addButton(x, runButtonY, width, 36, () => {
        if (G.Game.state === 'playing' && !pl.dead) action();
      }, 4);
    };
    runButton(16, 100, '倍速 ×' + G.Game.playbackSpeed, G.Game.playbackSpeed > 1,
      () => G.Game.cyclePlaybackSpeed(), !G.Coop.active);
    runButton(124, 124, '自動選卡：' + (G.Game.autoPickUpgrades ? '開' : '關'), G.Game.autoPickUpgrades,
      () => G.Game.toggleAutoPickUpgrades());

    // ---------- reloj / bioma / kills ----------
    ctx.textAlign = 'center';
    ctx.font = F(800, 26);
    ctx.fillStyle = 'rgba(255,255,255,.95)';
    ctx.fillText(G.U.mmss(st.time), w / 2, portrait ? 145 + safeTop : 42);
    ctx.font = F(600, 10);
    ctx.fillStyle = '#8fa3c4';
    ctx.fillText(G.World.biomeName().toUpperCase() + '  ·  ' + pl.kills + ' DERROTADOS  ·  ' + pl.coins + ' MONEDAS', w / 2, portrait ? 161 + safeTop : 58, portrait ? w - 24 : w);

    // ---------- clima (arriba a la derecha) ----------
    const wx = G.Weather.current;
    if (wx) {
      ctx.font = F(800, 11);
      ctx.textAlign = 'left';
      const txt = wx.name.toUpperCase() + ' · ' + Math.ceil(wx.left) + 's';
      const tw = Math.min(portrait ? w - 24 : w, ctx.measureText(txt).width + 40);
      const x0 = portrait ? (w - tw) / 2 : w - tw - 16 - (touch ? 56 : 0), y0 = portrait ? 110 + safeTop : 14;
      roundRect(ctx, x0, y0, tw, 26, 9);
      ctx.fillStyle = 'rgba(0,0,0,.55)'; ctx.fill();
      G.Icons.draw(ctx, wx.icon, x0 + 6, y0 + 3, 20);
      ctx.fillStyle = wx.color;
      ctx.fillText(txt, x0 + 32, y0 + 17, tw - 36);
    }

    // ---------- barra del jefe ----------
    const boss = G.EnemyMgr.all().find(e => e.boss && !e.dead);
    if (boss) {
      const bw = Math.min(420, w - 80);
      bar(ctx, (w - bw) / 2, portrait ? 145 + safeTop : 70, bw, 12, boss.hp / boss.maxHp, '#ffcb3d');
      ctx.font = F(800, 10);
      ctx.fillStyle = '#20160a';
      ctx.textAlign = 'center';
      ctx.fillText(boss.name.toUpperCase(), w / 2, portrait ? 155 + safeTop : 80, bw - 8);
    }

    // ---------- aviso ----------
    // ---------- shinies fuera de pantalla: destello en el borde ----------
    const cam = G.Camera, pulse = 0.6 + Math.sin(performance.now() / 160) * 0.4;
    for (const e of G.EnemyMgr.shinies()) {
      const sx = (e.x - cam.left()) * cam.scale, sy = (e.y - cam.top()) * cam.scale;
      if (sx > 0 && sx < w && sy > 0 && sy < h) continue;
      const M = 34;
      const ex = G.U.clamp(sx, M, w - M), ey = G.U.clamp(sy, M + 60, h - M - 70);
      const a = Math.atan2(sy - ey, sx - ex);
      ctx.save();
      ctx.globalAlpha = pulse;
      ctx.translate(ex, ey);
      ctx.fillStyle = '#9ae6ff';
      ctx.beginPath();
      ctx.moveTo(Math.cos(a) * 24, Math.sin(a) * 24);
      ctx.lineTo(Math.cos(a + 2.5) * 12, Math.sin(a + 2.5) * 12);
      ctx.lineTo(Math.cos(a - 2.5) * 12, Math.sin(a - 2.5) * 12);
      ctx.fill();
      ctx.globalAlpha = 1;
      G.Icons.draw(ctx, 'shiny', -12, -12, 24);
      ctx.restore();
    }

    // Poder de altar activo.
    if (pl.power) {
      const pw = pl.power, txt = pw.def.name.toUpperCase() + ' ' + Math.ceil(pw.t) + 's';
      ctx.font = F(800, 9);
      ctx.textAlign = 'left';
      const tw = ctx.measureText(txt).width + 12;
      roundRect(ctx, bx, py + 34, tw, 15, 7);
      ctx.fillStyle = 'rgba(0,0,0,.6)'; ctx.fill();
      ctx.fillStyle = pw.def.color;
      ctx.fillText(txt, bx + 6, py + 45);
      bx += tw + 5;
    }

    if (G.Coop.active) drawCoop(ctx, w, h, pl, px, py + (bx > px ? 56 : 40));

    // Grieta: flecha grande que late en el borde si no se ve, y si se ve, una
    // flecha que bota encima; en la arena, cuenta atrás.
    const rift = G.Rift.rift;
    if (rift) {
      const sx = (rift.x - cam.left()) * cam.scale, sy = (rift.y - 40 - cam.top()) * cam.scale;
      const now = performance.now() / 1000, beat = 0.5 + Math.sin(now * 7) * 0.5;
      const label = 'GRIETA · ' + Math.round(G.U.dist(pl.x, pl.y, rift.x, rift.y) / 32) + ' m · ' + Math.ceil(rift.ttl) + ' s';
      const off = sx < 0 || sx > w || sy < 0 || sy > h;
      ctx.save();
      if (off) {
        const M = 52, ex = G.U.clamp(sx, M, w - M), ey = G.U.clamp(sy, M + 70, h - M - 80);
        const a = Math.atan2(sy - ey, sx - ex), ca = Math.cos(a), sa = Math.sin(a);
        ctx.translate(ex, ey);
        // Halo que late.
        ctx.globalAlpha = 0.18 + beat * 0.22;
        ctx.fillStyle = '#b48aff';
        ctx.beginPath(); ctx.arc(0, 0, 30 + beat * 8, 0, 6.2832); ctx.fill();
        ctx.globalAlpha = 1;
        const tri = (k) => {
          ctx.beginPath();
          ctx.moveTo(ca * 40 * k, sa * 40 * k);
          ctx.lineTo(Math.cos(a + 2.45) * 20 * k, Math.sin(a + 2.45) * 20 * k);
          ctx.lineTo(Math.cos(a - 2.45) * 20 * k, Math.sin(a - 2.45) * 20 * k);
          ctx.closePath();
        };
        tri(1.12); ctx.fillStyle = '#1a0b33'; ctx.fill();
        tri(1); ctx.fillStyle = beat > 0.5 ? '#e2d0ff' : '#a06bff'; ctx.fill();
        ctx.font = F(800, 12);
        ctx.textAlign = ca > 0.3 ? 'right' : ca < -0.3 ? 'left' : 'center';
        const lx = -ca * 34, ly = -sa * 30 + 4;
        ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(0,0,0,.85)';
        ctx.strokeText(label, lx, ly);
        ctx.fillStyle = '#e2d0ff';
        ctx.fillText(label, lx, ly);
      } else {
        // Encima de la grieta: flecha hacia abajo que bota.
        const by = sy - 46 - Math.abs(Math.sin(now * 4)) * 10;
        ctx.translate(sx, by);
        ctx.beginPath(); ctx.moveTo(-15, -12); ctx.lineTo(15, -12); ctx.lineTo(0, 8); ctx.closePath();
        ctx.lineWidth = 4; ctx.strokeStyle = '#1a0b33'; ctx.stroke();
        ctx.fillStyle = beat > 0.5 ? '#e2d0ff' : '#a06bff'; ctx.fill();
        ctx.font = F(800, 11); ctx.textAlign = 'center';
        ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(0,0,0,.85)';
        const l2 = 'GRIETA · ' + Math.ceil(rift.ttl) + ' s';
        ctx.strokeText(l2, 0, -18); ctx.fillStyle = '#e2d0ff'; ctx.fillText(l2, 0, -18);
      }
      ctx.restore();
    }
    if (G.Rift.inArena) {
      ctx.textAlign = 'center';
      ctx.font = F(800, 12);
      ctx.fillStyle = '#d9c2ff';
      ctx.fillText('GRIETA · ' + G.U.mmss(G.Rift.timeLeft), w / 2, portrait ? (boss ? 176 : 155) + safeTop : boss ? 98 : 76);
    }

    // Eventos: cuenta atrás, flecha al Pokémon perdido / a la marca y a los duendes.
    G.Events.drawHud(ctx, w, h, pl, F);

    // Aviso propio al abrirse una grieta (no lo tapan los otros avisos).
    if (rift && rift.t < 4.5) {
      const a = Math.min(1, rift.t * 4, (4.5 - rift.t) * 2), pop = 1 + Math.max(0, 0.25 - rift.t) * 1.6;
      const y0 = portrait ? Math.max(200 + safeTop, h * 0.26) : h * 0.2;
      ctx.save();
      ctx.globalAlpha = a;
      ctx.translate(w / 2, y0); ctx.scale(pop, pop);
      ctx.font = F(800, 20);
      const t1 = '¡SE HA ABIERTO UNA GRIETA!', t2 = 'Sigue la flecha morada: dentro te espera un legendario';
      const bw = Math.min(w - 24, Math.max(ctx.measureText(t1).width, (ctx.font = F(700, 11), ctx.measureText(t2).width)) + 36);
      roundRect(ctx, -bw / 2, -26, bw, 52, 10);
      ctx.fillStyle = 'rgba(26,11,51,.88)'; ctx.fill();
      ctx.lineWidth = 2; ctx.strokeStyle = '#b48aff'; ctx.stroke();
      ctx.textAlign = 'center';
      ctx.font = F(800, 20); ctx.fillStyle = '#e2d0ff'; ctx.fillText(t1, 0, -2, bw - 20);
      ctx.font = F(700, 11); ctx.fillStyle = '#c9b0ff'; ctx.fillText(t2, 0, 16, bw - 20);
      ctx.restore();
    }

    const ban = G.Spawner.banner();
    if (ban) {
      const a = Math.min(1, ban.t * 1.6);
      ctx.save();
      ctx.globalAlpha = a;
      // Siempre centrado (antes heredaba la alineación de lo último dibujado, p.
      // ej. la flecha de un duende del tesoro, y salía descolocado).
      ctx.textAlign = 'center';
      ctx.font = F(800, 22);
      ctx.fillStyle = '#ffcb3d';
      ctx.strokeStyle = 'rgba(0,0,0,.7)'; ctx.lineWidth = 4;
      ctx.strokeText(ban.text, w / 2, h * 0.3, w - 24);
      ctx.fillText(ban.text, w / 2, h * 0.3, w - 24);
      ctx.restore();
    }

    // ---------- ranura de movimientos ----------
    const S = controls ? controls.S : 54, GAP = controls ? controls.GAP : 9;
    const n = touch ? controls.slots.length : Math.max(1, groups.length);
    const totalW = n * S + (n - 1) * GAP;
    const sx = controls ? controls.slots[0].x : (w - totalW) / 2;
    const sy = controls ? controls.slots[0].y : h - S - 18;
    const BOND = '#ff8ad8';
    const cdOf = m => m.passive || m.kind === 'orbit' || (m.id !== 'naruto-sand-armor' && G.NarutoGaara?.maintains(pl, m)) ? 0 : G.U.clamp(m.t / Math.max(m.minCooldown || 0, m.cd * pl.cdMul), 0, 1);
    const tentenState = pl.dex === 30009 ? G.NarutoTenten?.stateFor(pl) : null;
    const tentenPose = pl.dex === 30009 ? G.NarutoTenten?.activeFor(pl) : null;
    const tentenGuard = pl.dex === 30009 ? G.NarutoTenten?.guardFor?.(pl) : null;

    for (let i = 0; i < n; i++) {
      const g = groups[i] || [];
      const m = g[0];
      const displayPassive = i >= pl.slots.length && !!m?.passive;
      const fused = g.length > 1;
      const on = !displayPassive && i === pl.active;
      const slot = controls && controls.slots[i];
      const x = slot ? slot.x : sx + i * (S + GAP);
      const y0 = slot ? slot.y : sy;
      const y = on ? y0 - (touch ? 4 : 6) : y0;
      // Tocar (o hacer clic en) un icono activa ese movimiento.
      const grow = touch && on ? S * 0.06 : 0;
      if (m) G.Touch.addButton(x - grow, y - grow, S + grow * 2, S + grow * 2, () => {
        if (G.Game.state !== 'playing') return;
        if (displayPassive) { G.UI.toast(m.name + ' · Lv.' + m.lvl, 1600); return; }
        if (pl.active !== i) { pl.setActive(i); G.Audio.sfx('click'); }
      }, touch ? 1 : GAP / 2 + 3);
      const col = m ? G.U.TYPE_COLOR[m.type] : '#4a5468';
      ctx.save();
      if (touch && on) {
        ctx.translate(x + S / 2, y + S / 2);
        ctx.scale(1.12, 1.12);
        ctx.translate(-x - S / 2, -y - S / 2);
      }

      // fondo
      roundRect(ctx, x, y, S, S, 12);
      ctx.fillStyle = on ? 'rgba(20,30,50,.95)' : 'rgba(10,16,28,.8)';
      ctx.fill();
      ctx.lineWidth = on ? 2.5 : fused || (m && m.evolved) ? 2 : 1.2;
      // Vínculo: borde rosa. Evolucionado: dorado.
      ctx.strokeStyle = fused ? BOND : m && m.evolved ? '#ffd23f' : on ? col : 'rgba(140,170,210,.22)';
      ctx.stroke();

      if (!m) { ctx.restore(); continue; }

      if (fused) {
        // Vínculo: los movimientos en una cuadrícula de 2×2, cada uno con su recarga.
        const C = 22, P = (S - C * 2) / 3;
        g.forEach((gm, k) => {
          const cx = x + P + (k % 2) * (C + P), cy = y + P + Math.floor(k / 2) * (C + P);
          G.Icons.draw(ctx, G.SharinganIcons?.forMove(gm) || 'move:' + gm.id, cx, cy, C);
          const f = cdOf(gm);
          if (f > 0) { ctx.fillStyle = 'rgba(0,0,0,.55)'; ctx.fillRect(cx, cy, C, C * f); }
          if (gm.evolved) { ctx.strokeStyle = '#ffd23f'; ctx.lineWidth = 1; ctx.strokeRect(cx + 0.5, cy + 0.5, C - 1, C - 1); }
          // Destello al lanzarse.
          const fl = 1 - (performance.now() - (gm.castAt || 0)) / 180;
          if (fl > 0) { ctx.fillStyle = 'rgba(255,255,255,' + (fl * 0.55).toFixed(2) + ')'; ctx.fillRect(cx, cy, C, C); }
        });
      } else {
        // recarga: se vacía de abajo a arriba
        const cdFrac = cdOf(m);
        if (cdFrac > 0) {
          ctx.save();
          roundRect(ctx, x, y, S, S, 12); ctx.clip();
          ctx.fillStyle = 'rgba(0,0,0,.6)';
          ctx.fillRect(x, y, S, S * cdFrac);
          ctx.restore();
        }

        // emblema del tipo + insignia de la familia
        G.Icons.draw(ctx, G.SharinganIcons?.forMove(m) || 'move:' + m.id, x + (S - 32) / 2, y + (S - 32) / 2 - 2, 32);

        // nivel del movimiento (puntitos)
        const dots = m.def.maxLvl;
        const dw = 4, dgap = 2;
        const tw = dots * dw + (dots - 1) * dgap;
        for (let d = 0; d < dots; d++) {
          ctx.fillStyle = d < m.lvl ? col : 'rgba(255,255,255,.18)';
          ctx.fillRect(x + (S - tw) / 2 + d * (dw + dgap), y + S - 9, dw, 3);
        }
      }

      // tecla
      ctx.font = F(800, 9);
      ctx.fillStyle = fused ? BOND : on ? col : 'rgba(180,200,230,.6)';
      ctx.textAlign = 'left';
      ctx.fillText(displayPassive ? '∞' : String(i + 1), x + 3, y + 10);
      if (m.id === 'naruto-sand-shield') {
        const shield = G.NarutoGaara?.shieldState(pl);
        if (shield) {
          ctx.font = F(800, 9); ctx.textAlign = 'right'; ctx.fillStyle = '#edd395';
          ctx.fillText(Math.ceil(shield.amount) + '/' + Math.ceil(shield.capacity), x + S - 3, y + 10);
          ctx.textAlign = 'center'; ctx.fillText(shield.remaining.toFixed(1) + 's', x + S / 2, y - 4);
        }
        const guard = G.NarutoSandGuard?.state(pl);
        if (guard) {
          ctx.fillStyle = 'rgba(10,16,28,.82)'; ctx.fillRect(x + 3, y + S - 26, S - 6, 12);
          ctx.font = F(800, 8); ctx.textAlign = 'center'; ctx.fillStyle = '#d4cdbb';
          ctx.fillText('護衛 ' + guard.readyCount + '/' + guard.count, x + S / 2, y + S - 17, S - 8);
          const reforming = guard.guardians.filter(cloud => !cloud.ready);
          if (reforming.length) {
            const progress = reforming.reduce((sum, cloud) => sum + cloud.rechargeProgress, 0) / reforming.length;
            bar(ctx, x + 7, y + S - 13, S - 14, 2, progress, '#d4cdbb');
          }
        }
      }
      if (m.digiMode === 'chidori-chain' && G.NarutoChidori) {
        const chain = G.NarutoChidori.active;
        const activeChain = chain?.owner === pl && chain.move.id === m.id ? chain : null;
        const count = activeChain ? activeChain.limit : G.NarutoChidori.limitOf(m, pl);
        ctx.fillStyle = 'rgba(10,16,28,.88)'; ctx.fillRect(x + 3, y + S - 26, S - 6, 12);
        ctx.font = F(800, 8); ctx.textAlign = 'center'; ctx.fillStyle = '#9feaff';
        ctx.fillText('連招 ' + (activeChain ? activeChain.hitCount + '/' : '') + count, x + S / 2, y + S - 17, S - 8);
      }
      if (G.NarutoLee?.supports(m.digiMode) && G.NarutoLee.bindLimitOf) {
        const chain = G.NarutoLee.activeFor(pl);
        const activeChain = chain?.move.id === m.id ? chain : null;
        const count = activeChain ? activeChain.bindLimit : G.NarutoLee.bindLimitOf(m, pl);
        const label = activeChain && !activeChain.pullable ? '近身' :
          '綁定 ' + (activeChain ? activeChain.boundTargets.length + '/' : '') + count;
        ctx.fillStyle = 'rgba(10,16,28,.88)'; ctx.fillRect(x + 3, y + S - 26, S - 6, 12);
        ctx.font = F(800, 8); ctx.textAlign = 'center'; ctx.fillStyle = '#eee8d4';
        ctx.fillText(label, x + S / 2, y + S - 17, S - 8);
      }
      if (G.NarutoTenten?.supports(m.digiMode)) {
        const state = tentenState, pose = tentenPose;
        const count = m.digiMode === 'tenten-guard' ? 0 : pose?.m?.id === m.id ? pose.count : G.Quantity.count(pl, m.count || 1);
        let label = '忍具 ' + count;
        if (m.digiMode === 'tenten-guard') {
          const guard = tentenGuard;
          label = guard?.phase === 'prepare' && guard.age < .12 ? '展卷' :
            guard?.phase === 'sweep' && guard.age < .47 ? '護身' :
            guard?.boostRemaining > 0 ? '疾退 ' + guard.boostRemaining.toFixed(1) + 's' :
            guard?.cooldownRemaining > 0 ? '冷卻 ' + guard.cooldownRemaining.toFixed(1) + 's' : '就緒';
        }
        else if (m.digiMode === 'tenten-mastery') label = '貫穿 +' + [2, 3, 4, 5, 6][Math.max(0, Math.min(4, m.lvl - 1))];
        else if (m.digiMode === 'tenten-bounce') label = '連彈 ' + G.NarutoTenten.bounceCount(pl);
        else if (m.digiMode === 'tenten-tags') label = '爆符 ' + (state?.tagCount || count);
        else if (m.digiMode === 'tenten-fuma') label = state?.returning ? '回收 ' + state.returning : '迴刃 ' + count;
        else if (m.digiMode === 'tenten-twin' && pose?.m?.id === m.id) label = '忍具 ' + pose.emitted + '/' + pose.count;
        ctx.fillStyle = 'rgba(10,16,28,.88)'; ctx.fillRect(x + 3, y + S - 26, S - 6, 12);
        ctx.font = F(800, 8); ctx.textAlign = 'center'; ctx.fillStyle = '#eee4c7';
        ctx.fillText(label, x + S / 2, y + S - 17, S - 8);
        if (!m.passive && state?.chargeRemaining > 0) {
          ctx.fillStyle = '#ffe3a0'; ctx.font = F(800, 8);
          ctx.fillText('蓄勢 +30% ' + Math.ceil(state.chargeRemaining) + 's', x + S / 2, y + 10, S - 6);
        }
      }
      if (m.id === 'naruto-sand-prison') {
        const prison = G.NarutoGaara?.sandPrisonState(pl);
        const cooldown = G.NarutoGaara?.prisonCooldownState(pl);
        ctx.font = F(800, 9); ctx.textAlign = 'center'; ctx.fillStyle = '#edd395';
        if (prison) ctx.fillText(prison.remaining.toFixed(1) + 's', x + S / 2, y - 4);
        else if (cooldown) ctx.fillText(cooldown.remaining.toFixed(1) + 's', x + S / 2, y - 4);
      }
      ctx.restore();

      // nombre encima del activo (con un vínculo: "Ascuas +2")
      if (on) {
        ctx.font = F(700, 10);
        ctx.textAlign = 'center';
        ctx.fillStyle = fused ? BOND : col;
        ctx.fillText(fused ? m.name + ' +' + (g.length - 1) : m.name, touch ? controls.bar.x + (controls.bar.w - S - GAP) / 2 : x + S / 2, touch ? controls.bar.y + S / 2 : y - 7, touch ? controls.bar.w - S - GAP - 8 : w);
      }
    }

    // ---------- vínculo guardado (aún no hay dos movimientos sueltos) ----------
    if (pl.bonds > 0) {
      const bx = portrait ? controls.bar.x - 30 : sx + totalW + 12, by = sy + S / 2 - 12;
      G.Icons.draw(ctx, 'bond', bx, by, 24);
      if (pl.bonds > 1) {
        ctx.font = F(800, 10);
        ctx.textAlign = 'left';
        ctx.fillStyle = BOND;
        ctx.fillText('×' + pl.bonds, bx + 25, by + 20);
      }
    }

    // ---------- objeto equipado (a la izquierda de los movimientos) ----------
    {
      const ix = controls ? controls.item.x : sx - S - 18, iy = controls ? controls.item.y : sy;
      roundRect(ctx, ix, iy, S, S, 12);
      ctx.fillStyle = pl.item ? 'rgba(40,30,10,.9)' : 'rgba(10,16,28,.55)';
      ctx.fill();
      ctx.lineWidth = pl.item ? 2 : 1;
      ctx.strokeStyle = pl.item ? '#ffd23f' : 'rgba(140,170,210,.18)';
      ctx.stroke();
      if (pl.item) {
        G.Icons.draw(ctx, pl.item, ix + (S - 36) / 2, iy + (S - 36) / 2, 36);
        ctx.font = F(700, 9);
        ctx.textAlign = 'center';
        ctx.fillStyle = '#ffd23f';
        ctx.fillText(G.Items.BY[pl.item].name, ix + S / 2, iy - 6, touch ? S + 12 : w);
      }
    }

    // ---------- botón de pausa (táctil) ----------
    if (touch) {
      const { x: bx, y: by, w: bs } = controls.pause;
      roundRect(ctx, bx, by, bs, bs, 10);
      ctx.fillStyle = 'rgba(10,16,28,.7)'; ctx.fill();
      ctx.lineWidth = 2; ctx.strokeStyle = 'rgba(244,248,255,.8)'; ctx.stroke();
      ctx.fillStyle = '#f4f8ff';
      ctx.fillRect(bx + bs / 2 - 7, by + bs / 2 - 9, 5, 18); ctx.fillRect(bx + bs / 2 + 2, by + bs / 2 - 9, 5, 18);
      G.Touch.addButton(bx, by, bs, bs, () => G.Game.togglePause(), 8);
    }

    // pista de controles
    if (st.time < 14 && !portrait) {
      ctx.font = F(600, 10);
      ctx.textAlign = 'center';
      ctx.fillStyle = 'rgba(180,200,230,.55)';
      ctx.fillText(touch ? 'Arrastra el dedo para moverte  ·  toca un ataque para cambiarlo'
                         : `WASD moverse  ·  1-${Math.max(4, pl.slots.length)} / Q / E o clic en un ataque para cambiarlo  ·  Esc pausa`, w / 2, portrait ? h - Math.min(44, G.Touch.safeArea().bottom) - 5 : h - 4, w - 24);
    }

    ctx.restore();
  }

  // ---------------- cooperativo ----------------

  /**
   * - Vida de cada compañero debajo de la tuya.
   * - Flecha en el borde de la pantalla hacia los que no se ven, con su nombre
   *   y a cuántos metros están (roja y parpadeando si está caído).
   * - Si has caído tú: aviso y barra de "te están levantando".
   */
  function drawCoop(ctx, w, h, pl, px, top) {
    const cam = G.Camera;
    const t = performance.now() / 1000;
    let y = top;
    ctx.textAlign = 'left';
    for (const m of G.Coop.mates) {
      if (!m.connected) continue;
      const o = m.pl;
      ctx.font = F(800, 10);
      ctx.fillStyle = m.color;
      ctx.fillText(m.name, px, y + 9);
      const lx = px + 78;
      bar(ctx, lx, y + 1, 110, 8, o.dead ? 0 : o.hp / o.maxHp, o.dead ? '#ff5f6d' : '#5fe08a');
      if (o.dead) {
        ctx.font = F(800, 9);
        ctx.fillStyle = Math.sin(t * 8) > 0 ? '#ff8a96' : '#ffd0d5';
        ctx.fillText('CAÍDO', lx + 116, y + 9);
      }
      y += 15;
    }

    // Flechas hacia los compañeros fuera de la vista.
    for (const m of G.Coop.mates) {
      if (!m.connected) continue;
      const o = m.pl;
      const sx = (o.x - cam.left()) * cam.scale, sy = (o.y - o.bodyH * 0.5 - cam.top()) * cam.scale;
      if (sx > 0 && sx < w && sy > 0 && sy < h) continue;
      const M = 42;
      const ex = G.U.clamp(sx, M, w - M), ey = G.U.clamp(sy, M + 70, h - M - 80);
      const a = Math.atan2(sy - ey, sx - ex);
      const metres = Math.round(G.U.dist(pl.x, pl.y, o.x, o.y) / 32);
      const col = o.dead ? (Math.sin(t * 8) > 0 ? '#ff5f6d' : '#ffd0d5') : m.color;
      ctx.save();
      ctx.translate(ex, ey);
      // Flecha
      ctx.fillStyle = 'rgba(0,0,0,.55)';
      ctx.beginPath(); ctx.arc(0, 0, 17, 0, 6.2832); ctx.fill();
      ctx.fillStyle = col;
      ctx.beginPath();
      ctx.moveTo(Math.cos(a) * 28, Math.sin(a) * 28);
      ctx.lineTo(Math.cos(a + 2.4) * 14, Math.sin(a + 2.4) * 14);
      ctx.lineTo(Math.cos(a - 2.4) * 14, Math.sin(a - 2.4) * 14);
      ctx.closePath(); ctx.fill();
      // Inicial del compañero dentro del círculo
      ctx.font = F(800, 14);
      ctx.textAlign = 'center';
      ctx.fillStyle = '#fff';
      ctx.fillText(m.name.charAt(0).toUpperCase(), 0, 5);
      // Nombre y distancia: al lado contrario de la flecha, para que no se salga
      const lx = -Math.cos(a) * 30, ly = -Math.sin(a) * 26 + 4;
      ctx.font = F(800, 12);
      const label = (o.dead ? '¡' + m.name + ' necesita ayuda! ' : m.name + ' ') + '· ' + metres + ' m';
      ctx.textAlign = Math.cos(a) > 0.3 ? 'right' : Math.cos(a) < -0.3 ? 'left' : 'center';
      ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,.8)';
      ctx.strokeText(label, lx, ly);
      ctx.fillStyle = col;
      ctx.fillText(label, lx, ly);
      ctx.restore();
    }

    // Tú, caído.
    if (pl.dead) {
      ctx.save();
      ctx.textAlign = 'center';
      ctx.font = F(800, 20);
      ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(0,0,0,.75)';
      const msg = G.Coop.players().every(p => p.dead) ? 'Habéis caído todos…' : 'Has caído: un compañero puede levantarte';
      ctx.strokeText(msg, w / 2, h * 0.62);
      ctx.fillStyle = '#ffb0b8';
      ctx.fillText(msg, w / 2, h * 0.62);
      const f = (pl.reviveT || 0) / G.Player.REVIVE_TIME;
      if (f > 0) bar(ctx, w / 2 - 110, h * 0.62 + 12, 220, 10, f, '#5fe08a');
      ctx.restore();
    }
  }

  return { draw, roundRect, bar };
})();
