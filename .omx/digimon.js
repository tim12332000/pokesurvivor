// Local crossover prototype. Pixel sprites: DS-era sheets; see pixel-manifest.json.
(() => {
  // Keep registration/assets for later work, but disable every public selector.
  const enabled = false;
  const definitions = [
    ['Agumon', '亞古獸', '太一', ['fire'], 'ember', '小型火焰', 'Baby Flame', ['valiente', 'impulsivo'], 3, 263, 284],
    ['Gabumon', '加布獸', '阿和', ['fire', 'ice'], 'ember', '爆炎火焰彈', 'Petit Fire', ['leal', 'prudente'], 3, 194, 276],
    ['Biyomon', '比丘獸', '阿空', ['flying', 'fire'], 'flamethrower', '魔法火焰', 'Magical Fire', ['dulce', 'alegre'], 2, 161, 283],
    ['Tentomon', '甲蟲獸', '光子郎', ['bug', 'electric'], 'thunder-shock', '飛翼閃電', 'Petit Thunder', ['astuto', 'sereno'], 2, 295, 258],
    ['Palmon', '巴魯獸', '美美', ['grass', 'poison'], 'vine-whip', '毒蔓藤', 'Poison Ivy', ['alegre', 'dulce'], 1, 221, 301],
    ['Gomamon', '哥瑪獸', '阿助', ['water'], 'bubble', '魚群大暴走', 'Marching Fishes', ['travieso', 'leal'], 1, 275, 243],
    ['Patamon', '巴達獸', '阿武', ['normal', 'flying'], 'gust', '空氣炮', 'Air Shot', ['dulce', 'valiente'], 4, 245, 272],
    ['Gatomon', '迪路獸', '小光', ['fairy', 'fighting'], 'karate-chop', '貓貓拳', 'Cat Punch', ['astuto', 'leal'], 5, 246, 286]
  ];
  const records = new Map();
  const dictionary = { Digimon: '數碼寶貝', 'Digimon Misterioso': '數碼世界 · 主角團',
    'Los iniciales de todas las regiones, y dos amigos más.': '各地區初始夥伴，以及數碼寶貝主角團。' };
  definitions.forEach(([name, chinese, partner, types, template, attack, english, traits, rarity, width, height], i) => {
    const dex = 20001 + i, move = 'digimon-' + name.toLowerCase();
    const mon = { dex, name, types, hp: 102 + i * 2, spd: 107 + (i % 3) * 4, atk: 1.18,
      rarity, bst: 410 + i * 12, starter: true, gen: 10, start: move, digimon: true };
    G.DEX.push(mon); G.DEX_BY[dex] = mon;
    const starter = { dex, start: move, traits };
    G.STARTERS.push(starter); G.STARTER_BY[dex] = starter;
    const base = G.Moves.BY_ID[template];
    const definition = { ...base, id: move, name: attack,
      desc: `數碼寶貝 ${chinese} 的招牌招式（${english}）。此測試版沿用既有戰鬥效果。` };
    G.Moves.BY_ID[move] = definition;
    G.Moves.ALL.push(definition);
    dictionary[name] = chinese;
    const pixel = window.PS_DIGIMON_PIXEL[name.toLowerCase()];
    const geometry = { w: pixel.cell_width * pixel.scale, h: pixel.cell_height * pixel.scale,
      ax: pixel.anchor[0] * pixel.scale, ay: pixel.anchor[1] * pixel.scale, n: 1, r: 1, d: [24] };
    G.SPRITE_META[dex] = { s: 1, sh: false,
      a: Object.fromEntries(G.Sprites.ANIMS.map(a => [a, a === 'Walk'
        ? { ...geometry, n: 4, d: [7, 7, 7, 7] } : { ...geometry }])) };
    const image = new Image();
    const record = { ...mon, chinese, partner, attack, english, pixel, image, ready: false };
    record.loaded = new Promise(resolve => {
      image.onload = () => { record.ready = true; resolve(true); };
      image.onerror = () => resolve(false);
    });
    image.src = `.omx/digimon/pixel/${name.toLowerCase()}.png`;
    records.set(dex, record);
  });
  G.I18n.add(dictionary, 'zh-TW');
  G.Gacha.BANNERS.push({ gen: 10, name: 'Digimon', color: ['#08395e', '#155985', '#42236d'] });
  G.MenuUI.GEN_NAMES.push('Digimon');
  const featured = G.Gacha.featured;
  G.Gacha.featured = gen => gen === 10 ? [20001, 20002, 20008] : featured(gen);
  const poolFor = G.Moves.poolFor;
  G.Moves.poolFor = mon => mon.digimon ? [mon.start, ...poolFor(mon)] : poolFor(mon);

  // DS sheets have four diagonal directions, with a rest pose and two walk steps.
  const Animator = G.Sprites.Animator;
  G.Sprites.Animator = class extends Animator {
    draw(ctx, x, y, opts = {}) {
      const record = records.get(this.dex);
      if (!record) return super.draw(ctx, x, y, opts);
      if (!record.ready) return;
      const meta = G.Sprites.animMeta(this.dex, 'Idle');
      const k = G.Sprites.PX * this.scale;
      const attacking = ['Attack', 'Shoot', 'Charge'].includes(this.cur);
      const direction = ['down_left', 'down_right', 'down_right', 'up_right', 'up_left', 'up_left', 'down_left', 'down_left'][this.dir];
      const pixel = record.pixel, group = pixel.directions.indexOf(direction);
      const phase = this.cur === 'Walk' ? [0, 1, 0, 2][this.frame % 4] : 0;
      const rect = pixel.frame_rects ? pixel.frame_rects[this.cur === 'Walk'
        ? pixel.direction_frames[group][phase] : pixel.idle_frame] : null;
      const sourceX = rect ? rect[0] : (group * pixel.frames_per_direction + phase) * pixel.cell_width;
      ctx.save();
      ctx.translate(Math.round(x), Math.round(y));
      if (pixel.mirror_groups && pixel.mirror_groups.includes(group)) ctx.scale(-1, 1);
      if (this.cur === 'Faint') ctx.scale(1, .5);
      // Keep transforms on integer pixels; attack effects are handled by combat.js.
      if (attacking) ctx.translate(0, -Math.round(Math.sin(this.progress() * Math.PI) * k));
      ctx.globalAlpha *= opts.alpha == null ? 1 : opts.alpha;
      ctx.imageSmoothingEnabled = false;
      const image = opts.flash ? G.Sprites.white(record.image) : record.image;
      if (rect) {
        ctx.drawImage(image, rect[0], rect[1], rect[2], rect[3],
          Math.round(-rect[2] * k / 2), Math.round(-rect[3] * k), Math.round(rect[2] * k), Math.round(rect[3] * k));
      } else ctx.drawImage(image, sourceX, 0, pixel.cell_width, pixel.cell_height,
        Math.round(-meta.ax * k), Math.round(-meta.ay * k), Math.round(meta.w * k), Math.round(meta.h * k));
      ctx.restore();
    }
  };
  const preload = G.Sprites.preload;
  G.Sprites.preload = (dexes, timeout, shiny) => Promise.all([
    preload(dexes.filter(dex => !records.has(dex)), timeout, shiny),
    ...dexes.filter(dex => records.has(dex)).map(dex => records.get(dex).loaded)
  ]);
  const spriteCanvas = G.UI.spriteCanvas;
  G.UI.spriteCanvas = (dex, width, height, opts = {}) => {
    if (!records.has(dex)) return spriteCanvas(dex, width, height, opts);
    const meta = G.Sprites.animMeta(dex, 'Idle');
    const preferred = width >= 150 ? 4 : opts.scale || 2;
    const scale = Math.max(1, Math.min(preferred, Math.floor(width * .9 / meta.w), Math.floor(height * .9 / meta.ay)));
    return spriteCanvas(dex, width, height, { ...opts, scale });
  };

  const style = document.createElement('style');
  style.textContent = `
    #scr-digimon { z-index: 150; padding: 20px; background: rgba(4,12,32,.9); }
    #scr-digimon .box { width: min(960px,100%); max-height: 92vh; overflow: auto; }
    .digimon-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
    .digimon-grid { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 12px; }
    .digimon-card { display: flex; flex-direction: column; align-items: center; gap: 5px; padding: 12px 8px; color: #fff;
      background: #173564; border: 2px solid #597fae; border-radius: 12px; font: inherit; cursor: pointer; }
    .digimon-card:hover,.digimon-card:focus-visible { border-color: #ffd23f; background: #244b80; }
    .digimon-card canvas { display: block; width:128px; height:112px; max-width:100%; image-rendering:pixelated; }
    .digimon-card b { font-size: 20px; color: #ffd23f; }
    .digimon-card small { color: #b9cbf0; }
    .digimon-card.on { border-color: #ffd23f; box-shadow: 0 0 0 2px #ffd23f44; }
    .digimon-group-label { grid-column: 1/-1; margin: 12px 0 4px; color: #ffd23f; }
    @media(max-width:650px) { .digimon-grid { grid-template-columns: repeat(2,minmax(0,1fr)); } }
    @media(max-height:500px) and (min-width:651px) { .digimon-card { padding:7px; } }
  `;
  document.head.appendChild(style);
  const picker = document.createElement('section');
  picker.id = 'scr-digimon'; picker.className = 'scr dim hidden'; picker.translate = false;
  picker.innerHTML = `<div class="box"><div class="digimon-heading"><h2>挑選數碼寶貝夥伴</h2>
    <button class="btn small ghost" id="digimon-close">返回</button></div>
    <p class="sub">第九世代後的新分類 · 大冒險主角團 8 隻夥伴 · 全部可直接選用</p>
    <div class="digimon-grid">${[...records.values()].map(r => `<button class="digimon-card" data-digimon="${r.dex}">
      <div class="digimon-portrait" data-portrait="${r.dex}" aria-label="${r.chinese}"></div>
      <b>${r.chinese}</b><small>${r.name} · ${r.partner}的夥伴</small><span>${r.attack}</span></button>`).join('')}</div>
    <p class="note">本地同人測試版 · DS 像素角色 · 4 向行走動畫 · 數值與招式效果為本作測試設定</p></div>`;
  document.body.appendChild(picker);
  for (const record of records.values()) {
    picker.querySelector(`[data-portrait="${record.dex}"]`).appendChild(
      G.UI.spriteCanvas(record.dex, 128, 112, { scale: 3, dir: 1, shadow: true }));
  }
  const openPicker = () => {
    if (!enabled) return false;
    G.UI.show('scr-menu');
    if (!G.DB.save.partner) document.getElementById('scr-menu').classList.add('hidden');
    G.UI.chrome(!!G.DB.save.partner);
    picker.classList.remove('hidden');
    document.getElementById('digimon-close').hidden = !G.DB.save.partner;
    picker.querySelectorAll('[data-digimon]').forEach(b => b.classList.toggle('on', +b.dataset.digimon === G.DB.save.partner));
    picker.dispatchEvent(new Event('digimon-open'));
  };
  const choose = dex => {
    if (!enabled) return false;
    if (!records.has(dex)) throw new Error('Unknown Digimon partner');
    const save = G.DB.save;
    save.partner = dex; save.starter = records.get(dex).baseDex || dex; save.partnerShiny = false;
    G.DB.grant(dex, 'starter'); G.DB.commit(true);
    picker.classList.add('hidden'); G.Flow.goMenu();
  };
  picker.querySelectorAll('[data-digimon]').forEach(b => { b.onclick = () => choose(+b.dataset.digimon); });
  document.getElementById('digimon-close').onclick = () => { picker.classList.add('hidden'); G.Flow.goMenu(); };
  const switcher = document.createElement('button');
  switcher.id = 'btn-digimon'; switcher.className = 'btn small gold'; switcher.textContent = '數碼寶貝';
  switcher.translate = false; switcher.onclick = openPicker;
  switcher.hidden = !enabled;
  document.getElementById('btn-settings').before(switcher);
  const gacha = document.getElementById('scr-gacha');
  const customizeGacha = () => {
    const tab = document.querySelector('#gacha-gens [data-gen="10"]');
    if (!tab) return;
    const subtitle = tab.querySelector('small');
    if (subtitle.textContent !== '主角團') subtitle.textContent = '主角團';
    if (!tab.classList.contains('on')) return;
    const description = document.getElementById('banner-desc');
    const copy = '數碼寶貝大冒險 · 8 條進化線 · 使用抽卡券召喚';
    if (description.textContent !== copy) description.textContent = copy;
    const rates = document.getElementById('gacha-rates');
    const shinyRow = rates.querySelectorAll(':scope > div')[5];
    if (shinyRow) shinyRow.remove();
    const note = rates.querySelector('.note');
    const noteText = '十連抽保底史詩以上；70 抽保底傳說。收錄初始夥伴、成熟期、完全體、究極體與合體形態，沒有異色。';
    if (note && note.textContent !== noteText) { note.textContent = noteText; note.style.whiteSpace = 'pre-line'; }
  };
  new MutationObserver(customizeGacha).observe(gacha, {
    childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['class']
  });
  const afterLogin = G.Flow.afterLogin;
  G.Flow.afterLogin = function () { if (enabled && !G.DB.save.partner) openPicker(); else afterLogin.call(this); };
  const ready = G.DB.ready;
  G.DB.ready = async () => {
    const restored = await ready();
    for (const dex of records.keys()) G.DB.grant(dex, 'starter');
    G.DB.commit();
    return restored;
  };
  const starterGrid = document.getElementById('starter-grid');
  new MutationObserver(() => {
    if (enabled && starterGrid.querySelectorAll('.cell').length === G.STARTERS.length && !starterGrid.querySelector('.digimon-group-label')) {
      const heading = document.createElement('h3'); heading.className = 'digimon-group-label'; heading.textContent = '數碼寶貝';
      starterGrid.insertBefore(heading, starterGrid.querySelectorAll('.cell')[G.STARTERS.findIndex(s => s.dex === 20001)]);
    }
  }).observe(starterGrid, { childList: true });
  document.querySelector('#scr-menu .logo .t2').textContent = '數碼寶貝 × 寶可夢 · 本地版';
  document.querySelector('#scr-menu [data-go="gacha"] small').textContent = '9 大世代 + 數碼寶貝';
  document.title = 'PokéSurvivor × 數碼寶貝 · 本地版';
  G.Digimon = { enabled, records, choose, openPicker };
})();
