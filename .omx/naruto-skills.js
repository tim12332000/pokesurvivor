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

  G.VFX.SHAPES['naruto-lion'] = {
    w:19,h:19,frames:2,dir:true,gen(P,frame){
      P.fill((x,y)=>{const r=Math.hypot(x-9,y-9);return r<5?'m':r<7+((x+y+frame)%3===0)?'l':null;});
      P.line(8,5,14,3,'w',1,'l'); P.line(8,13,14,15,'l',1,'m');
      P.line(12,7,17,8,'l',1,'m'); P.line(12,11,16,12,'m',1,'d');
      P.set(12,6,'w');P.set(13,6,'o');P.set(15,10,'w');P.outline();
    }
  };
  const profiles = [
    [30001, 'naruto', '多重影分身之術', 'Multi Shadow Clone Jutsu', '01_1423', {
      mode: 'shadow-clones', type: 'fighting', cd: 4, dmg: 8, range: 240,
      cloneDuration: 6, punchCd: .65, vis: { pal: 'naruto-blue' },
      desc: 'Lv.1 召出 8 隻，每次技能升級數量翻倍：16、32、64、128 隻；存在 6 秒、冷卻 4 秒。切換到已學的螺旋丸、螺旋手裏劍或忍具時，每隻分身都使用完整招式傷害，不分攤、不設定總傷害上限。受擊後化煙消散，不會再召出分身。數量與數值為本作改編。',
      ups: [16,32,64,128].map(count=>({t:`影分身數量翻倍 → ${count} 隻；每隻完整傷害`,m:{}}))
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
      mode: 'dash', type: 'electric', cd: 1.3, dmg: 46, charge: .1,
      range: 95, radius: 95, width: 32,
      vis: { beam: 'bolt', proj: 'bolt', pal: 'naruto-blue' },
      desc: '集中雷遁後短距離突進穿刺，傷害衝刺路徑上的敵人；遇牆停止，不是遠距雷射。'
    }],
    [30005, 'hinata', '柔拳', 'Gentle Fist', '01_1668', {
      mode: 'melee', type: 'fighting', cd: .72, dmg: 30, count: 3, burstInterval: .08,
      range: 100, radius: 78, arc: 1.5, knock: 15,
      vis: { melee: 'impact', proj: 'fire', pal: 'naruto-blue' },
      desc: '向前連打三掌近身查克拉攻擊，總傷害分攤於三掌；維持狹窄、快速的近戰定位，不借用寧次的回天。'
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
    [30008, 'itachi', '月讀', 'Tsukuyomi', '01_1316', {
      mode: 'single-illusion', type: 'psychic', cd: 3.6, dmg: 30, range: 260,
      fieldDuration: 1.5, slow: .9, bossSlow: .25,
      vis: { proj: 'ring', aura: 'ring', pal: 'naruto-red' },
      desc: '鎖定一名可見敵人施加紅色幻術，造成一次精神傷害並短暫減速；首領抗性較高。這是單體控制，不會直接消滅整群。'
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
      desc: '凝聚旋轉查克拉後向前突進。鳴人 Lv.3 起保證出現學習選項；選用此招時，現存影分身會各自接近敵人並使用螺旋丸，總模仿傷害受限。',
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
  extra.push(
    ['naruto-sharingan', [30002], {
      name:'寫輪眼預判', mode:'sharingan', type:'psychic', cd:12, dmg:0,
      range:180, fieldDuration:3, nextDamageMul:1.25, dodge:1,
      vis:{pal:'naruto-red'},
      desc:'附近有敵人時開眼預判，短暫準備一次閃避，並強化下一次攻擊；不會在安全空地反覆浪費冷卻。加成與時限為本作改編。',
      source_url:'https://naruto-official.com/en/news/01_1296'
    }],
    ['naruto-medical-heal', [30003], {
      name:'醫療忍術', mode:'medical-heal', type:'fairy', cd:7, dmg:0, healFraction:.22,
      vis:{pal:'grass'}, desc:'受傷時為自己恢復最大生命的 22%；滿血不消耗冷卻。回復量為本作改編，不能使倒下角色復活。',
      source_url:'https://naruto-official.com/en/news/01_1743'
    }],
    ['naruto-regeneration', [30003], {
      name:'創造再生', mode:'regeneration', type:'fairy', cd:18, dmg:0,
      fieldDuration:5, healFraction:.045,
      vis:{pal:'grass'}, desc:'受傷時短暫持續自癒，每秒恢復最大生命的 4.5%，持續 5 秒；有長冷卻，不提供無限生命或復活。此招屬小櫻後期能力。',
      source_url:'https://naruto-official.com/en/news/01_1743'
    }],
    ['naruto-earth-wall', [30004], {
      name:'土遁・土流壁', mode:'earth-wall', type:'ground', cd:9, dmg:0,
      fieldDuration:3, width:100, range:72,
      vis:{pal:'naruto-sand'}, desc:'面對附近敵人升起短暫土牆，阻擋敵方接觸與飛行攻擊；不修改地圖格子，不阻擋玩家移動，也不永久封路。',
      source_url:'https://naruto-official.com/en/news/01_2541'
    }],
    ['naruto-twin-lions', [30005], {
      name:'柔步雙獅拳', mode:'melee', type:'fighting', cd:1.25, dmg:52,
      count:2, burstInterval:.14, radius:100, range:125, arc:1.9, knock:35,
      vis:{melee:'naruto-lion',pal:'naruto-blue'},
      desc:'雙拳凝聚獅形查克拉，先後打出兩段較強的前方近戰；總傷害分攤於兩拳。屬雛田後期能力，不等同全周圍回天。',
      source_url:'https://naruto-official.com/en/news/01_2199'
    }],
    ['naruto-byakugan', [30005], {
      name:'白眼偵察', mode:'byakugan', type:'psychic', cd:10, dmg:0,
      fieldDuration:5, radius:280, damageMul:1.2,
      vis:{pal:'naruto-blue'}, desc:'附近有敵人時短暫標記周圍敵人，強化柔拳與柔步雙獅拳的近身精準傷害；不把拳擊改成全圖遠距離攻擊。',
      source_url:'https://naruto-official.com/en/news/01_1668'
    }],
    ['naruto-lotus', [30006], {
      name:'表蓮華', mode:'lotus', type:'fighting', cd:3, dmg:70,
      range:145, radius:60, windup:.25, liftDuration:.35,
      vis:{pal:'grass'}, desc:'選定近身敵人，踢起後短暫滯空，再以落地重擊收尾；首領不會被完整浮空。落地小範圍衝擊為本作改編。',
      source_url:'https://naruto-official.com/en/news/01_1652'
    }],
    ['naruto-gates', [30006], {
      name:'八門遁甲強化', mode:'gates', type:'fighting', cd:15, dmg:0,
      fieldDuration:5, atkMul:1.3, speedMul:1.2, fatigueDuration:2, fatigueSpeedMul:.8,
      vis:{pal:'grass'}, desc:'附近有敵人時短暫提升攻擊 30% 與移速 20%，結束後疲勞 2 秒、移速降低 20%；不可疊加或藉切換技能繞過疲勞。本版只採部分開門強化。',
      source_url:'https://naruto-official.com/en/news/01_1652'
    }],
    ['naruto-sand-coffin', [30007], {
      name:'砂縛柩・砂瀑送葬', mode:'sand-coffin', type:'ground', cd:3.5, dmg:80,
      range:280, fieldDuration:1.1, slow:.95, bossSlow:.3,
      vis:{pal:'naruto-sand'}, desc:'以砂包住一名敵人，短暫束縛後壓縮造成一次傷害；首領僅受較弱減速，不是無條件即死。與流砂瀑流的群攻分工不同。',
      source_url:'https://naruto-official.com/en/news/01_1555'
    }],
    ['naruto-sand-shield', [30007], {
      name:'砂之盾', mode:'sand-shield', type:'ground', cd:12, dmg:0,
      fieldDuration:8, shieldAmount:45, range:180,
      vis:{pal:'naruto-sand'}, desc:'危險接近時形成可吸收 45 傷害的砂盾，最長 8 秒；盾量耗盡會消失，不能疊加成永久無敵。',
      source_url:'https://naruto-official.com/en/news/01_1555'
    }],
    ['naruto-black-flames', [30008], {
      name:'天照', mode:'black-flames', type:'fire', cd:4.8, dmg:12,
      range:280, radius:80, fieldDuration:3, fieldTick:.5, maxFields:2,
      vis:{pal:'naruto-red'}, desc:'在鎖定敵人腳下留下有限時間的黑炎區域，傷害踏入範圍的敵人；最多同時兩片。持續時間、可閃避範圍與傷害為遊戲平衡改編。',
      source_url:'https://naruto-official.com/en/news/01_1316'
    }]
  );
  const kinds = { dash: 'dash', melee: 'melee', slam: 'melee', beam: 'beam', shot: 'projectile', aura: 'aura', nova: 'nova', 'sand-wave': 'cone', 'shadow-clones': 'buff',
    sharingan:'buff', 'medical-heal':'buff', regeneration:'buff', 'earth-wall':'buff', byakugan:'buff', gates:'buff', 'sand-shield':'buff',
    lotus:'melee', 'sand-coffin':'meteor', 'single-illusion':'meteor', 'black-flames':'meteor' };
  const definitions = new Map(), byDex = new Map(), references = new Map();
  const extraPools = new Map();

  function supportUps(design) {
    const power = design.healFraction != null ? {healFraction:design.healFraction*1.2}
      : design.shieldAmount != null ? {shieldAmount:design.shieldAmount*1.2}
      : design.nextDamageMul != null ? {nextDamageMul:1.35}
      : design.damageMul != null ? {damageMul:1.3}
      : design.atkMul != null ? {atkMul:1.4} : {width:1.2};
    return [
      {t:'冷卻 -10%',m:{cd:.9}},
      {t:design.fieldDuration ? '持續時間增加' : '回復量增加',m:design.fieldDuration ? {fieldDuration:design.fieldDuration*1.2} : {healFraction:design.healFraction*1.15}},
      {t:design.healFraction != null ? '回復量提高' : design.shieldAmount != null ? '護盾量提高' : design.mode==='earth-wall' ? '牆體寬度提高' : '強化效果提高',m:power},
      {t:'冷卻再減少 10%',m:{cd:.9}}
    ];
  }

  function register(id, design) {
    const definition = {
      speed: 340, life: 1.5, size: 7, count: 1, arc: 1.6, spread: 0, pierce: 0,
      radius: 140, range: 480, width: 24, homing: 0, knock: 0, burn: 0, poison: 0, slow: 0,
      ...design, id, kind: kinds[design.mode], digimonSkill: true, narutoSkill: true,
      digiMode: design.mode, digiVis: design.vis || {}, maxLvl: 5,
      ups: design.ups || (design.dmg === 0 ? supportUps(design) : [
        { t: '傷害 +20%', m: { dmg: 1.2 } },
        { t: '冷卻 -10%', m: { cd: .9 } },
        { t: '攻擊範圍與持續時間 +12%', m: {
          radius: 1.12, width: 1.12, life: 1.12,
          // The base upgrade system assigns unknown fields instead of multiplying them.
          ...(design.range != null ? { range: design.range * 1.12 } : {}),
          ...(design.blastRadius != null ? { blastRadius: design.blastRadius * 1.12 } : {}),
          ...(design.fieldDuration != null ? {fieldDuration:design.fieldDuration*1.12} : {})
        } },
        { t: '傷害 +25%', m: { dmg: 1.25 } }
      ])
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
  guide.innerHTML = '<div class="box"><div class="naruto-skill-heading"><h2>忍術圖鑑與來源</h2><button class="btn small ghost" id="naruto-skills-close">返回</button></div><p class="sub">角色與忍術參考官方動畫、角色資料與遊戲說明；傷害、冷卻、範圍、回復與自動連段皆為本跨界版改編，也包含角色後期能力。中文採常見譯名。每位忍者有三招特色技能，另可學共通忍具：苦無投擲、手裏劍散射。Lv.3、Lv.6 起保證出現兩招特色技能選項；角色招式池互不混用。控制與輔助招式不等同範圍傷害。</p><div class="naruto-skill-entries"></div></div>';
  for (const [dex, definition] of byDex) {
    const record = G.Naruto.records.get(dex), reference = references.get(dex);
    const item = document.createElement('article');
    item.className = 'naruto-skill-entry';
    const title = document.createElement('h3');
    title.textContent = `${record.chinese || record.name} · ${definition.name}`;
    const description = document.createElement('p');
    description.textContent = definition.desc;
    const stats = document.createElement('small');
    stats.textContent = `冷卻 ${definition.cd} 秒 · ${definition.dmg ? '基礎傷害 '+definition.dmg : '輔助技能'} · 可升至 Lv.5`;
    const source = document.createElement('a');
    source.href = reference.source_url;
    source.target = '_blank';
    source.rel = 'noopener noreferrer';
    source.textContent = `官方參考 · ${reference.name}`;
    item.append(title, description, stats, source);
    for (const id of extraPools.get(dex) || []) {
      const move = definitions.get(id);
      const heading = document.createElement('h4');
      heading.textContent = `可學忍術 · ${move.name}`;
      const detail = document.createElement('p');
      detail.textContent = move.desc;
      const extraStats = document.createElement('small');
      extraStats.textContent = `冷卻 ${move.cd} 秒 · ${move.dmg ? '基礎傷害 '+move.dmg : '輔助技能'}${move.blastRadius ? ' · 爆發半徑 '+move.blastRadius : ''} · 可升至 Lv.5`;
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
