// Local-only Adventure evolution layer; game balance and level rules are custom.
(() => {
  const api = G.Digimon, records = api.records;
  const baseIds = [...records.keys()];
  const stageNames = ['成長期', '成熟期', '完全體', '究極體', '合體'];
  const levels = [0, 5, 10, 15, 20];
  const dictionary = {};
  for (const record of records.values()) {
    record.baseDex = record.dex;
    record.stage = record.dex === 20008 ? 1 : 0;
    record.mon = G.DEX_BY[record.dex];
  }
  for (const [dex, name, chinese, baseDex, stage, slug, template, attack] of window.PS_DIGIMON_EVOLUTIONS) {
    const parent = records.get(baseDex), pixel = window.PS_DIGIMON_PIXEL[slug];
    const types = [...parent.types];
    const mon = { dex, name, types, hp: 104 + stage * 42, spd: 108 + stage * 5,
      atk: 1.18 + stage * .32, rarity: stage === 1 ? 3 : stage === 2 ? 4 : 5,
      bst: 420 + stage * 80, starter: false, gen: 10, digimon: true, start: 'digimon-' + slug };
    const source = G.Moves.BY_ID[template];
    G.Moves.BY_ID[mon.start] = { ...source, id: mon.start, name: attack,
      type: slug === 'lillymon' ? 'grass' : source.type,
      dmg: source.dmg * (1 + stage * .15),
      desc: `${chinese}的進化招式。此本地版沿用既有招式效果與自訂數值。` };
    G.Moves.ALL.push(G.Moves.BY_ID[mon.start]);
    G.DEX.push(mon); G.DEX_BY[dex] = mon;
    const geometry = { w: pixel.cell_width * pixel.scale, h: pixel.cell_height * pixel.scale,
      ax: pixel.anchor[0] * pixel.scale, ay: pixel.anchor[1] * pixel.scale, n: 1, r: 1, d: [24] };
    G.SPRITE_META[dex] = { s: stage >= 3 ? 2 : 1, sh: false,
      a: Object.fromEntries(G.Sprites.ANIMS.map(a => [a, a === 'Walk'
        ? { ...geometry, n: 4, d: [7,7,7,7] } : { ...geometry }])) };
    const image = new Image();
    const record = { ...mon, mon, chinese, baseDex, stage, pixel, image,
      partner: stage === 4 ? '太一與阿和' : parent.partner, attack, ready: false };
    api.lazyImage(record, `.omx/digimon/pixel/${slug}.png`);
    records.set(dex, record);
    dictionary[name] = chinese;
  }
  G.I18n.add(dictionary, 'zh-TW');
  const settings = () => {
    const save = G.DB.save;
    if (!save) return { auto: true, branch: 'holydramon', history: [] };
    save.digimon = Object.assign({ auto: true, branch: 'holydramon', history: [] }, save.digimon);
    return save.digimon;
  };
  const nextOf = dex => {
    const current = records.get(dex);
    if (!current || current.stage === 4) return null;
    if (current.stage === 3 && [20001,20002].includes(current.baseDex)) return records.get(20201);
    if (current.stage >= 3) return null;
    if (dex === 20172) return records.get(settings().branch === 'ophanimon' ? 20174 : 20173);
    return [...records.values()].find(r => r.baseDex === current.baseDex && r.stage === current.stage + 1) || null;
  };
  const evolve = (player = G.Game.player, force = false) => {
    if (!player || !records.has(player.dex) || player.dead || player.hp <= 0) return false;
    const next = nextOf(player.dex);
    if (!next || (!force && player.level < levels[next.stage])) return false;
    // The local sandbox makes both partners available; require both mega forms for fusion.
    if (next.stage === 4 && (!G.DB.owns(20103) || !G.DB.owns(20113))) return false;
    const old = player.mon, direction = player.anim.dir;
    const health = player.maxHp ? player.hp / player.maxHp : 1;
    const hpBonus = player.maxHp - old.hp;
    player.mon = next.mon; player.dex = next.dex;
    player.anim = new G.Sprites.Animator(next.dex, 1, false); player.anim.dir = direction;
    player.r = G.Sprites.bodyRadius(next.dex); player.bodyH = G.Sprites.bodyHeight(next.dex);
    player.maxHp = next.hp + hpBonus; player.hp = Math.max(1, player.maxHp * health);
    player.baseAtk = next.atk; player.baseSpd = next.spd; player.shiny = false;
    const signature = player.moves.find(m => m.id === old.start) || player.moves[0];
    if (signature) {
      const previousId = signature.id;
      const replacement = G.Moves.instance(next.start, Math.min(signature.lvl, G.Moves.BY_ID[next.start].maxLvl));
      // The evolved signature continues the same run-local damage history.
      Object.assign(replacement, { dealt: signature.dealt || 0, since: signature.since || 0,
        damageIds: [...(signature.damageIds || []), previousId] });
      for (const key of Object.keys(signature)) delete signature[key];
      Object.assign(signature, replacement);
      if (player.bind[previousId] !== undefined) {
        player.bind[next.start] = player.bind[previousId]; delete player.bind[previousId];
      }
    } else player.addMove(next.start);
    G.Projectiles.clearOrbs(player);
    G.Sprites.preload([next.dex]);
    G.DB.save.partner = next.dex; G.DB.save.starter = next.baseDex;
    G.DB.grant(next.dex, 'starter');
    const history = settings().history;
    if (!history.includes(next.dex)) history.push(next.dex);
    G.DB.commit(true);
    G.FX.ring(player.x, player.y, 8, 120, '#ffd23f', .8, 4);
    G.UI.toast(`${G.T(old.name)} → ${next.chinese}！`);
    G.Audio.sfx('levelup');
    return true;
  };
  const update = G.Player.prototype.update;
  G.Player.prototype.update = function(dt) {
    update.call(this, dt);
    if (this === G.Game.player && G.Game.state === 'playing' && settings().auto) {
      // A late unlock can cross more than one stage; normal play crosses one at a time.
      for (let guard = 0; guard < 4 && evolve(this); guard++) { /* bounded */ }
    }
  };
  const upgradesOf = G.DB.upgradesOf;
  G.DB.upgradesOf = dex => upgradesOf(records.get(+dex)?.baseDex || dex);

  const picker = document.getElementById('scr-digimon');
  const tabs = document.createElement('div'); tabs.className = 'digimon-evo-tabs';
  const tabNames = ['初始夥伴', '成熟期', '完全體', '究極體', '合體'];
  let selectedTab = 0;
  tabs.innerHTML = tabNames.map((label, i) => `<button class="btn small" data-evo-tab="${i}">${label}</button>`).join('');
  const options = document.createElement('div'); options.className = 'digimon-evo-options';
  options.innerHTML = `<label><input id="digimon-auto-evolve" type="checkbox">隨等級自動進化</label>
    <label>迪路獸究極體 <select id="digimon-evo-branch"><option value="holydramon">聖龍獸</option><option value="ophanimon">神聖天女獸</option></select></label>`;
  const hint = document.createElement('p'); hint.className = 'sub';
  hint.textContent = 'Lv.5 成熟期 → Lv.10 完全體 → Lv.15 究極體；戰鬥暴龍獸／鋼鐵加魯魯獸 Lv.20 可合體。也能直接挑選下列形態。';
  const grid = picker.querySelector('.digimon-grid');
  grid.before(tabs, options, hint);
  picker.querySelector('.box > .sub').textContent = '8 條主角進化線 · 33 種形態 · 本地無限資源版本';
  const originalChoose = api.choose;
  api.choose = dex => {
    if (dex === 20174) settings().branch = 'ophanimon';
    if (dex === 20173) settings().branch = 'holydramon';
    originalChoose(dex);
  };
  const renderPicker = () => {
    const prefs = settings();
    options.querySelector('#digimon-auto-evolve').checked = prefs.auto;
    options.querySelector('#digimon-evo-branch').value = prefs.branch;
    tabs.querySelectorAll('[data-evo-tab]').forEach(b => b.classList.toggle('gold', +b.dataset.evoTab === selectedTab));
    const forms = selectedTab === 0 ? baseIds.map(id => records.get(id))
      : [...records.values()].filter(r => r.stage === selectedTab);
    grid.innerHTML = '';
    for (const record of forms) {
      const button = document.createElement('button');
      button.className = 'digimon-card' + (G.DB.save?.partner === record.dex ? ' on' : '');
      button.dataset.digimon = record.dex;
      button.innerHTML = `<b>${record.chinese}</b><small>${stageNames[record.stage]} · ${record.partner}的夥伴</small><span>${record.attack}</span>`;
      button.prepend(G.UI.spriteCanvas(record.dex, 128, 112, { scale: 3, dir: 1, shadow: true }));
      button.onclick = () => api.choose(record.dex);
      grid.appendChild(button);
    }
  };
  tabs.querySelectorAll('[data-evo-tab]').forEach(b => { b.onclick = () => { selectedTab = +b.dataset.evoTab; renderPicker(); }; });
  options.querySelector('#digimon-auto-evolve').onchange = event => { settings().auto = event.target.checked; G.DB.commit(); };
  options.querySelector('#digimon-evo-branch').onchange = event => { settings().branch = event.target.value; G.DB.commit(); };
  picker.addEventListener('digimon-open', renderPicker);

  const evolveButton = document.createElement('button');
  evolveButton.id = 'digimon-evolve-now'; evolveButton.className = 'btn small gold hidden';
  evolveButton.translate = false; evolveButton.onclick = () => evolve();
  document.body.appendChild(evolveButton);
  const style = document.createElement('style');
  style.textContent = `.digimon-evo-tabs,.digimon-evo-options {display:flex;gap:8px;flex-wrap:wrap;margin:10px 0;align-items:center}
    .digimon-evo-options{gap:18px;font-size:14px}.digimon-evo-options select{background:#173564;color:white;border:1px solid #7595bc;border-radius:5px;padding:4px;font:inherit}
    #digimon-evolve-now{position:fixed;right:12px;top:64px;z-index:45;max-width:240px;font-size:13px}
    @media(max-height:500px){#digimon-evolve-now{top:45px;max-width:210px}}
  `;
  document.head.appendChild(style);
  setInterval(() => {
    const player = G.Game.player, inRun = G.Game.state === 'playing';
    const next = player && nextOf(player.dex);
    evolveButton.classList.toggle('hidden', !inRun || !next);
    if (!inRun || !next) return;
    const copy = `${settings().auto ? '自動' : '進化'}：${next.chinese}（Lv.${levels[next.stage]}）`;
    if (evolveButton.textContent !== copy) evolveButton.textContent = copy;
    evolveButton.disabled = player.level < levels[next.stage];
  }, 200);
  Object.assign(api, { baseIds, stageNames, levels, nextOf, evolve, renderPicker });
})();
