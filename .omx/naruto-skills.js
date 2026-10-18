/* Naruto signature identities; combat rules and balance are this edition's adaptation. */
(() => {
  if (!G.Naruto || !G.DigimonSkills) return;

  Object.assign(G.VFX.PAL, {
    'naruto-blue': ['#102851', '#1767aa', '#35bfff', '#9feaff', '#ffffff'],
    'naruto-red': ['#250b12', '#751626', '#d93443', '#ff8b83', '#ffe9d5'],
    'naruto-sand': ['#4d3014', '#91622b', '#c79a53', '#edd395', '#fff0ca']
  });

  const profiles = [
    [30001, 'naruto', '螺旋丸', 'Rasengan', '01_1296', {
      mode: 'dash', type: 'fighting', cd: 1.25, dmg: 48, charge: .12,
      range: 125, radius: 125, width: 56, knock: 100,
      vis: { proj: 'wind', melee: 'impact', pal: 'naruto-blue' },
      desc: '凝聚藍色旋轉查克拉後向前突進，擊退路徑上的敵人。'
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
    [30007, 'gaara', '砂縛柩', 'Sand Coffin', '01_1555', {
      mode: 'shot', type: 'ground', cd: 1.38, dmg: 45, speed: 235, size: 12,
      homing: 3.5, life: 1.7, blastRadius: 74, slow: .72,
      vis: { proj: 'blob', trail: 'dirt', pal: 'naruto-sand' },
      desc: '砂縛柩的遊戲改編：操控追蹤砂團包圍目標，命中時壓縮周圍砂流並使敵人減速。'
    }],
    [30008, 'itachi', '月讀', 'Tsukuyomi', '01_1287', {
      mode: 'aura', type: 'psychic', cd: 1.9, dmg: 38, radius: 156, slow: .78,
      vis: { proj: 'ring', aura: 'ring', pal: 'naruto-red' },
      desc: '展開紅色幻術波動，傷害並減速身邊敵人；以短暫控場呈現幻術。'
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
  const kinds = { dash: 'dash', melee: 'melee', slam: 'melee', beam: 'beam', shot: 'projectile', aura: 'aura', nova: 'nova' };
  const definitions = new Map(), byDex = new Map(), references = new Map();

  function register(id, design) {
    const definition = {
      speed: 340, life: 1.5, size: 7, count: 1, arc: 1.6, spread: 0, pierce: 0,
      radius: 140, range: 480, width: 24, homing: 0, knock: 0, burn: 0, poison: 0, slow: 0,
      ...design, id, kind: kinds[design.mode], digimonSkill: true, narutoSkill: true,
      digiMode: design.mode, digiVis: design.vis || {}, maxLvl: 5,
      ups: [
        { t: '傷害 +20%', m: { dmg: 1.2 } },
        { t: '冷卻 -10%', m: { cd: .9 } },
        { t: '攻擊範圍與持續時間 +12%', m: { radius: 1.12, width: 1.12, life: 1.12 } },
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

  const poolFor = G.Moves.poolFor;
  G.Moves.poolFor = mon => {
    if (!mon.naruto) return poolFor(mon);
    const signature = byDex.get(mon.dex);
    return signature ? [signature.id, ...shared.map(([id]) => id)] : [];
  };
  G.NarutoSkillCatalog = { definitions, byDex, references };

  const guide = document.createElement('section');
  guide.id = 'scr-naruto-skills';
  guide.className = 'scr dim hidden';
  guide.translate = false;
  guide.innerHTML = '<div class="box"><div class="naruto-skill-heading"><h2>忍術圖鑑與來源</h2><button class="btn small ghost" id="naruto-skills-close">返回</button></div><p class="sub">角色與招式名稱參考官方角色專欄；突進、射程、減速、傷害與冷卻為本遊戲改編。中文名稱採常見譯名。每位忍者皆可學習苦無與手裏劍。</p><div class="naruto-skill-entries"></div></div>';
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
    source.textContent = `官方角色專欄 · ${reference.name}`;
    item.append(title, description, stats, source);
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
