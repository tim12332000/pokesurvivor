/* Naruto signature identities; combat rules and balance are this edition's adaptation. */
(() => {
  if (!G.Naruto || !G.DigimonSkills) return;

  Object.assign(G.VFX.PAL, {
    'naruto-blue': ['#102851', '#1767aa', '#35bfff', '#9feaff', '#ffffff'],
    'naruto-red': ['#250b12', '#751626', '#d93443', '#ff8b83', '#ffe9d5'],
    'naruto-sand': ['#4d3014', '#91622b', '#c79a53', '#edd395', '#fff0ca']
  });

  G.VFX.SHAPES['naruto-wind-shuriken'] = {
    w: 19, h: 19, frames: 3, spin: true, gen(P, frame) {
      for (let blade = 0; blade < 4; blade++) {
        const a = blade * Math.PI / 2 + frame * .18;
        P.line(9 + Math.cos(a) * 3, 9 + Math.sin(a) * 3,
          9 + Math.cos(a) * 8, 9 + Math.sin(a) * 8, 'l', 1, 'm');
        P.line(9 + Math.cos(a) * 7, 9 + Math.sin(a) * 7,
          9 + Math.cos(a + .6) * 4, 9 + Math.sin(a + .6) * 4, 'w');
      }
      P.fill((x, y) => { const r = Math.hypot(x - 9, y - 9); return r < 1.7 ? 'w' : r < 3 ? 'l' : r < 4 ? 'm' : null; });
      P.arc(9, 9, 2.4, frame, frame + Math.PI * 1.5, 'w');
      P.outline();
    }
  };
  // East-facing horned dragon: streaming neck, upper/lower jaw and open mouth.
  G.VFX.SHAPES['naruto-water-dragon'] = {
    w: 21, h: 17, frames: 2, dir: true, gen(P, frame) {
      P.line(1, 12 + frame, 7, 8, 'm', 1, 'd');
      P.line(7, 8, 10, 6, 'l', 1, 'm');
      for (let x = 9; x <= 15; x++) for (let y = 5; y <= 10; y++) P.set(x, y, y < 7 ? 'l' : 'm');
      P.line(11, 5, 8, 1, 'l');
      P.line(14, 5, 15, 1, 'w');
      P.line(14, 6, 19, 6, 'l', 1, 'm');
      P.line(13, 11, 18, 12, 'm', 1, 'd');
      P.set(17, 8, 'w'); P.set(15, 10, 'w');
      P.set(14, 5, 'w'); P.set(15, 5, 'o');
      P.line(10, 10, 7, 14, 'l');
      P.set(3 + frame, 5, 'l'); P.set(1, 8 - frame, 'w');
      P.outline();
    }
  };

  const profiles = [
    [30001, 'naruto', '多重影分身之術', 'Multi Shadow Clone Jutsu', '01_1423', {
      mode: 'shadow-clones', type: 'fighting', cd: 10, dmg: 8, range: 240,
      cloneDuration: 6, punchCd: .65, vis: { pal: 'naruto-blue' },
      desc: '召出 3 個會選敵、移動與出拳的影分身，存在 6 秒；受擊後化煙消散。技能 Lv.3 最多 4 個、Lv.5 最多 5 個。切換招式後現存分身仍會作戰；技能 Lv.3 起，使用螺旋丸可讓最多 2 個分身追加連擊。數量、時限與傷害皆為本作改編。',
      ups: [{t:'分身傷害 +20%',m:{dmg:1.2}},{t:'同時存在上限提高為 4，解鎖分身螺旋丸連擊',m:{}},
        {t:'分身存在時間增加至 7 秒',m:{cloneDuration:7}},{t:'同時存在上限提高為 5',m:{}}]
    }],
    [30002, 'sasuke', '千鳥', 'Chidori', '01_1296', {
      mode: 'dash', type: 'electric', cd: 1.05, dmg: 44, charge: .09,
      range: 170, radius: 170, width: 34, knock: 50,
      vis: { proj: 'bolt', melee: 'claw', pal: 'naruto-blue' },
      desc: '以雷遁集中穿刺前方，突進距離較長、命中路徑較窄。'
    }],
    [30003, 'sakura', '櫻花衝', 'Cherry Blossom Impact', '01_1743', {
      mode: 'slam', type: 'fighting', cd: 1.3, dmg: 55,
      range: 115, radius: 105, knock: 145,
      vis: { melee: 'impact', pal: 'fairy' },
      desc: '朝前方地面重擊，引發圓形衝擊波，將近處敵人推開。'
    }],
    [30004, 'kakashi', '雷切', 'Lightning Blade', '01_1327', {
      mode: 'beam', type: 'electric', cd: 1.1, dmg: 41, charge: .1,
      range: 280, radius: 260, width: 26,
      vis: { beam: 'bolt', proj: 'bolt', pal: 'naruto-blue' },
      desc: '集中雷遁打出狹長直線穿刺，可貫穿多名敵人，遇牆停止。'
    }],
    [30005, 'hinata', '柔步雙獅拳', 'Gentle Step Twin Lion Fists', '01_2199', {
      mode: 'melee', type: 'fighting', cd: .82, dmg: 40, count: 2, burstInterval: .12,
      range: 118, radius: 94, arc: 1.85, knock: 45,
      vis: { melee: 'impact', proj: 'fire', pal: 'naruto-blue' },
      desc: '以雙拳打出兩段近身查克拉攻擊；總傷害分攤於左右兩拳。'
    }],
    [30006, 'lee', '木葉旋風', 'Leaf Whirlwind', '01_1489', {
      mode: 'melee', type: 'fighting', cd: .86, dmg: 37,
      range: 145, radius: 124, arc: 3.9, knock: 95,
      vis: { melee: 'claw', proj: 'wind', pal: 'grass' },
      desc: '旋身踢出大角度橫掃，適合清開貼身與側面的敵人。'
    }],
    [30007, 'gaara', '流砂瀑流・砂瀑大葬', 'Sand Tsunami — automatic burial follow-up (game adaptation)', '01_1695', {
      mode: 'sand-wave', type: 'ground', cd: 2.8, dmg: 72,
      range: 310, radius: 310, width: 240, knock: 55,
      waveDuration: .65, bindDuration: .5, slow: 0,
      vis: { pal: 'naruto-sand' },
      desc: '前方寬扇形砂浪掃過多名敵人，造成 25% 傷害，再短暫束縛並以整片砂地壓葬造成 75% 傷害。束縛期間普通敵人減速 95%、首領減速 35%。官方遊戲的砂浪與追加區域攻擊為參考；自動銜接壓葬、比例與範圍為本作改編。'
    }],
    [30008, 'itachi', '月讀', 'Tsukuyomi', '01_1287', {
      mode: 'aura', type: 'psychic', cd: 1.9, dmg: 38, radius: 156, slow: .78,
      vis: { proj: 'ring', aura: 'ring', pal: 'naruto-red' },
      desc: '展開紅色幻術波動，傷害並減速身邊敵人；群體範圍為本作控場改編，並非聲稱原作月讀可同時控制整群。'
    }]
  ];
  const shared = [
    ['naruto-kunai', {
      name: '苦無投擲', mode: 'shot', type: 'steel', cd: .68, dmg: 17,
      speed: 530, life: 1.1, size: 5, pierce: 1, range: 500,
      vis: { proj: 'needle', pal: 'steel' }, desc: '快速投擲苦無，貫穿前方一名敵人。'
    }],
    ['naruto-shuriken', {
      name: '手裏劍散射', mode: 'nova', type: 'steel', cd: 1.4, dmg: 9,
      count: 8, speed: 325, life: .9, size: 5,
      vis: { proj: 'star', pal: 'steel' }, desc: '向八個方向投出手裏劍，補足周圍火力。'
    }]
  ];
  const extra = [
    ['naruto-naruto', [30001], {
      name: '螺旋丸', mode: 'dash', type: 'fighting', cd: 1.25, dmg: 48, charge: .12,
      range: 125, radius: 125, width: 56, knock: 100,
      vis: { proj: 'wind', melee: 'impact', pal: 'naruto-blue' },
      desc: '凝聚旋轉查克拉後向前突進。鳴人 Lv.3 起保證出現學習選項；多重影分身達技能 Lv.3 時，最多 2 個現存分身可追加螺旋丸連擊，總追加傷害受限。',
      source_url: 'https://naruto-official.com/en/news/01_1423'
    }],
    ['naruto-rasenshuriken', [30001], {
      name: '風遁・螺旋手裏劍', mode: 'shot', type: 'flying', cd: 2.5, dmg: 58,
      speed: 350, life: 1.3, size: 15, range: 455, blastRadius: 110, knock: 65,
      vis: { proj: 'naruto-wind-shuriken', trail: 'wind', pal: 'naruto-blue' },
      desc: '投出四刃旋轉查克拉手裏劍，命中後爆發風刃並傷害周圍敵人。此為鳴人後期習得的忍術，本跨界版可學；不代表少年造型在原作當時已會使用。爆發半徑、傷害與冷卻為遊戲改編。',
      source_url: 'https://naruto-official.com/en/news/01_1423'
    }],
    ['naruto-fireball', [30002, 30008], {
      name: '火遁・豪火球之術', mode: 'shot', type: 'fire', cd: 2.3, dmg: 49,
      speed: 300, life: 1.4, size: 19, range: 420, blastRadius: 95, burn: .12,
      vis: { proj: 'fire', trail: 'fire', pal: 'fire' },
      desc: '吐出大型火球，命中後爆發火焰，傷害爆心周圍多名敵人並施加短暫燃燒。佐助與鼬使用此招有官方資料；命中爆炸半徑與燃燒數值為本作改編。',
      source_url: 'https://naruto-official.com/en/anime/naruto1/list/01_354',
      owner_sources: { 30008: 'https://naruto-official.com/en/news/01_2332' }
    }],
    ['naruto-water-dragon', [30004], {
      name: '水遁・水龍彈之術', mode: 'shot', type: 'water', cd: 2.65, dmg: 56,
      speed: 320, life: 1.45, size: 18, range: 464, blastRadius: 95, knock: 90,
      vis: { proj: 'naruto-water-dragon', trail: 'bubble', pal: 'water' },
      desc: '水龍張口衝向目標，身後拖出水泡，命中後化成水浪衝擊周圍敵人。官方記載卡卡西複製水龍忍術；水浪範圍與擊退數值為本作改編。',
      source_url: 'https://naruto-official.com/en/news/01_2665'
    }]
  ];
  const kinds = { dash: 'dash', melee: 'melee', slam: 'melee', beam: 'beam', shot: 'projectile', aura: 'aura', nova: 'nova', 'sand-wave': 'cone', 'shadow-clones': 'buff' };
  const definitions = new Map(), byDex = new Map(), references = new Map();
  const extraPools = new Map();

  function register(id, design) {
    const definition = {
      speed: 340, life: 1.5, size: 7, count: 1, arc: 1.6, spread: 0, pierce: 0,
      radius: 140, range: 480, width: 24, homing: 0, knock: 0, burn: 0, poison: 0, slow: 0,
      ...design, id, kind: kinds[design.mode], digimonSkill: true, narutoSkill: true,
      digiMode: design.mode, digiVis: design.vis || {}, maxLvl: 5,
      ups: design.ups || [
        { t: '傷害 +20%', m: { dmg: 1.2 } },
        { t: '冷卻 -10%', m: { cd: .9 } },
        { t: '攻擊範圍與持續時間 +12%', m: {
          radius: 1.12, width: 1.12, life: 1.12,
          // The base upgrade system assigns unknown fields instead of multiplying them.
          ...(design.range != null ? { range: design.range * 1.12 } : {}),
          ...(design.blastRadius != null ? { blastRadius: design.blastRadius * 1.12 } : {})
        } },
        { t: '傷害 +25%', m: { dmg: 1.25 } }
      ]
    };
    delete definition.mode;
    delete definition.vis;
    const existing = G.Moves.BY_ID[id];
    if (existing) {
      for (const key of Object.keys(existing)) delete existing[key];
      Object.assign(existing, definition);
    } else {
      G.Moves.BY_ID[id] = definition;
      G.Moves.ALL.push(definition);
    }
    definitions.set(id, G.Moves.BY_ID[id]);
    return G.Moves.BY_ID[id];
  }

  for (const [dex, slug, name, english, article, design] of profiles) {
    const record = G.Naruto.records.get(dex);
    if (!record) continue;
    const definition = register(record.start || `naruto-${slug}`, { ...design, name });
    record.attack = name;
    const label = document.querySelector(`[data-naruto-attack="${dex}"]`);
    if (label) label.textContent = name;
    byDex.set(dex, definition);
    references.set(dex, { name: english, source_url: `https://naruto-official.com/en/news/${article}` });
  }
  shared.forEach(([id, design]) => register(id, design));
  for (const [id, owners, design] of extra) {
    register(id, design);
    for (const dex of owners) {
      if (!extraPools.has(dex)) extraPools.set(dex, []);
      extraPools.get(dex).push(id);
    }
  }

  const poolFor = G.Moves.poolFor;
  G.Moves.poolFor = mon => {
    if (!mon.naruto) return poolFor(mon);
    const signature = byDex.get(mon.dex);
    return signature ? [signature.id, ...shared.map(([id]) => id), ...(extraPools.get(mon.dex) || [])] : [];
  };
  G.NarutoSkillCatalog = { definitions, byDex, references, extraPools };

  const guide = document.createElement('section');
  guide.id = 'scr-naruto-skills';
  guide.className = 'scr dim hidden';
  guide.translate = false;
  guide.innerHTML = '<div class="box"><div class="naruto-skill-heading"><h2>忍術圖鑑與來源</h2><button class="btn small ghost" id="naruto-skills-close">返回</button></div><p class="sub">角色與忍術參考官方動畫、角色資料與遊戲說明；範圍、突進、減速、傷害、冷卻及自動連段為本遊戲改編。此跨界版可混用角色後期忍術，不代表原作相同造型、時期已掌握。中文名稱採常見譯名。每位忍者皆可學習苦無與手裏劍，專屬範圍技限定對應角色。</p><div class="naruto-skill-entries"></div></div>';
  for (const [dex, definition] of byDex) {
    const record = G.Naruto.records.get(dex), reference = references.get(dex);
    const item = document.createElement('article');
    item.className = 'naruto-skill-entry';
    const title = document.createElement('h3');
    title.textContent = `${record.chinese || record.name} · ${definition.name}`;
    const description = document.createElement('p');
    description.textContent = definition.desc;
    const stats = document.createElement('small');
    stats.textContent = `冷卻 ${definition.cd} 秒 · 基礎傷害 ${definition.dmg} · 可升至 Lv.5`;
    const source = document.createElement('a');
    source.href = reference.source_url;
    source.target = '_blank';
    source.rel = 'noopener noreferrer';
    source.textContent = `官方參考 · ${reference.name}`;
    item.append(title, description, stats, source);
    for (const id of extraPools.get(dex) || []) {
      const move = definitions.get(id);
      const heading = document.createElement('h4');
      heading.textContent = `可學範圍忍術 · ${move.name}`;
      const detail = document.createElement('p');
      detail.textContent = move.desc;
      const extraStats = document.createElement('small');
      extraStats.textContent = `冷卻 ${move.cd} 秒 · 基礎傷害 ${move.dmg}${move.blastRadius ? ' · 爆發半徑 '+move.blastRadius : ''} · 可升至 Lv.5`;
      const link = document.createElement('a');
      link.href = move.owner_sources?.[dex] || move.source_url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = `官方招式來源 · ${move.name}`;
      item.append(heading, detail, extraStats, link);
    }
    guide.querySelector('.naruto-skill-entries').append(item);
  }
  document.body.append(guide);
  const button = document.createElement('button');
  button.id = 'naruto-skill-guide';
  button.className = 'btn small';
  button.textContent = '忍術圖鑑與來源';
  button.onclick = () => guide.classList.remove('hidden');
  const heading = document.querySelector('#scr-naruto .naruto-actions');
  if (heading) heading.append(button);
  guide.querySelector('#naruto-skills-close').onclick = () => guide.classList.add('hidden');
  const style = document.createElement('style');
  style.textContent = `
    #scr-naruto-skills{z-index:175;background:#08152bed}
    #scr-naruto-skills>.box{width:min(850px,100%);max-height:92vh;overflow:auto}
    .naruto-skill-heading{display:flex;align-items:center;justify-content:space-between;gap:12px}
    .naruto-skill-heading h2{color:#ffcf7c;margin:0}
    .naruto-skill-entry{padding:14px 0;border-bottom:1px solid #ffffff33}
    .naruto-skill-entry h3{color:#ffd58b;font-size:15px;margin:0}
    .naruto-skill-entry p{margin:7px 0;line-height:1.6}
    .naruto-skill-entry small{display:block;color:#bed0ee}
    .naruto-skill-entry a{display:inline-block;margin-top:7px;font-size:12px;color:#ffbf78}
    @media(max-width:480px){.naruto-skill-heading h2{font-size:19px}.naruto-skill-entry{padding:12px 0}}
  `;
  document.head.append(style);
})();
