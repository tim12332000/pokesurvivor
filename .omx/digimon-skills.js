// Source-backed signature identities; every combat value is a local game design choice.
(() => {
  const fire = { proj: 'fire', pal: 'fire', trail: 'ember' };
  const blue = { proj: 'fire', pal: 'blueflame', trail: 'wisp' };
  const holy = { proj: 'ball', pal: 'holy', trail: 'spark' };
  const ice = { proj: 'ice', pal: 'ice', trail: 'spark' };
  const missile = { proj: 'digi-missile', pal: 'steel', trail: 'ember' };
  const profiles = [
    [20001, { name:'小型火焰', mode:'shot', type:'fire', cd:.62, dmg:18, speed:320, size:7, burn:1, vis:fire,
      desc:'吐出小火球，命中附帶燃燒；穩定的單體遠程攻擊。' }],
    [20002, { name:'爆炎火焰彈', mode:'shot', type:'fire', cd:.8, dmg:12, count:2, arc:.16, speed:350, pierce:1, burn:1, vis:blue,
      desc:'連發藍色火焰，狹窄扇形穿透敵人；藍色火焰不附帶冰凍。' }],
    [20003, { name:'魔法火焰', mode:'shot', type:'fire', cd:1.05, dmg:20, speed:225, life:1.7, size:10, pierce:3, homing:.8,
      burn:1, vis:{proj:'wind',pal:'fire',trail:'wisp'}, desc:'發射旋轉的幻影火焰，緩慢追蹤並穿透一列敵人。' }],
    [20004, { name:'飛翼閃電', mode:'shot', type:'electric', cd:.58, dmg:15, speed:540, pierce:2, slow:.18,
      vis:{proj:'spark',pal:'electric',trail:'spark'}, desc:'快速放出電擊，貫穿敵群並造成短暫遲緩。' }],
    [20005, { name:'毒蔓藤', mode:'melee', type:'poison', cd:.95, dmg:24, radius:122, range:145, arc:1.8, poison:1, slow:.35,
      vis:{melee:'vine',pal:'grass'}, desc:'伸出帶毒藤蔓橫掃前方，毒傷與纏繞遲緩適合牽制近敵。' }],
    [20006, { name:'魚群大暴走', mode:'shot', type:'water', cd:1.25, dmg:7, count:5, arc:.65, speed:240, life:1.9, homing:3,
      vis:{proj:'digi-fish',pal:'water',trail:'bubbles'}, desc:'召來五條小魚追擊目標，魚群會轉向附近敵人。' }],
    [20007, { name:'空氣炮', mode:'shot', type:'flying', cd:.72, dmg:20, speed:370, size:11, pierce:1, knock:135,
      vis:{proj:'wind',pal:'flying'}, desc:'壓縮空氣成炮彈，重點在擊退與突破包圍。' }],
    [20008, { name:'貓貓拳', mode:'melee', type:'fighting', cd:.65, dmg:30, count:2, burstInterval:.1, radius:90, range:115, arc:1.65, knock:45,
      vis:{melee:'claw',pal:'holy'}, desc:'以銳爪快速二連擊；距離短，但能持續壓制貼身敵人。' }],
    [20101, { name:'超級火焰', mode:'shot', type:'fire', cd:1.15, dmg:36, speed:285, size:11, blastRadius:54, burn:1, vis:fire,
      desc:'吐出高熱大火球，命中或碰撞時爆炸並灼燒附近敵人。' }],
    [20102, { name:'究極破壞砲', mode:'shot', type:'fire', cd:1.55, dmg:30, count:2, arc:.35, speed:280, size:8, homing:2.3,
      blastRadius:62, vis:missile, desc:'胸口雙發追蹤飛彈，各自爆炸；適合清除散開的中距離敵群。' }],
    [20103, { name:'蓋亞能量砲', mode:'shot', type:'fire', cd:2.6, dmg:112, charge:.48, speed:205, life:2.4, size:18,
      blastRadius:122, burn:2, knock:95, vis:{proj:'digi-gaia',pal:'fire',trail:'ember'},
      desc:'蓄力凝聚高熱能量球，命中產生大範圍爆炸；空檔較長。' }],
    [20111, { name:'妖狐火焰', mode:'shot', type:'fire', cd:.95, dmg:13, count:3, arc:.55, speed:340, pierce:2, life:1.25,
      burn:1, vis:blue, desc:'吐出三道藍焰掃過前方，持續燃燒；不是冷凍吐息。' }],
    [20112, { name:'凱撒銳爪', mode:'melee', type:'fighting', cd:.85, dmg:57, count:3, burstInterval:.09,
      radius:112, range:140, arc:2.1, knock:60, vis:{melee:'claw',pal:'fighting'}, desc:'三連爪擊切開前方敵群，單次施放分三段造成傷害。' }],
    [20113, { name:'絕對冷凍氣', mode:'blizzard', type:'ice', cd:1.65, dmg:50, range:210, radius:102, arc:1.2, slow:.68,
      fieldDuration:2.1, fieldTick:.5, vis:ice, desc:'零度吐息凍慢前方敵人，留下一塊短暫冰霜區持續牽制。' }],
    [20121, { name:'隕石巨翼', mode:'shot', type:'fire', cd:1.2, dmg:13, count:6, arc:1.0, speed:330, size:7, pierce:1,
      burn:1, vis:{proj:'feather',pal:'fire',trail:'ember'}, desc:'雙翼射出六枚火焰羽毛，以寬扇形壓制前方。' }],
    [20122, { name:'影翼斬', mode:'shot', type:'flying', cd:1.15, dmg:25, count:3, arc:.28, speed:520, life:1.1, pierce:4, size:9,
      vis:{proj:'feather',pal:'fire',trail:'spark'}, desc:'高速羽翼刃穿過一整列目標，偏重長距離貫穿。' }],
    [20123, { name:'星光爆破', mode:'aura', type:'fairy', cd:2.2, dmg:76, charge:.3, radius:164, knock:75,
      vis:{proj:'star',pal:'holy',aura:'feather'}, desc:'振翼散出金色光芒，在身邊形成一次大範圍淨化爆發。' }],
    [20131, { name:'米加巨砲', mode:'shot', type:'electric', cd:1.15, dmg:38, speed:340, size:10, blastRadius:48, slow:.25,
      vis:{proj:'ball',pal:'electric',trail:'spark'}, desc:'發射壓縮電氣彈，接觸爆炸並讓敵人短暫遲緩。' }],
    [20132, { name:'超大角砲', mode:'dash', type:'electric', cd:1.5, dmg:62, charge:.16, range:175, radius:175, width:62, knock:125,
      vis:{proj:'streak',pal:'electric',melee:'impact'}, desc:'把力量集中在巨角後衝刺撞穿敵群；會沿可通行路徑前進。' }],
    [20133, { name:'千兆爆破', mode:'shot', type:'electric', cd:2.05, dmg:93, charge:.2, speed:320, size:15, blastRadius:108, slow:.35,
      vis:{proj:'digi-gaia',pal:'electric',trail:'spark'}, desc:'釋放大型高壓電球，撞擊爆炸覆蓋廣範圍。' }],
    [20141, { name:'尖尖碰碰拳', mode:'nova', type:'grass', cd:1.5, dmg:9, count:18, speed:325, life:.85, size:5, pierce:1,
      vis:{proj:'needle',pal:'grass'}, desc:'向四周射出十八根尖刺，擅長防止被包圍。' }],
    [20142, { name:'花仙砲', mode:'beam', type:'grass', cd:1.3, dmg:49, charge:.2, radius:300, range:330, width:25,
      vis:{beam:'petal',pal:'grass',proj:'petal'}, desc:'雙手形成花砲，短暫蓄力後射出細長的貫穿光束。' }],
    [20143, { name:'荊棘鞭', mode:'melee', type:'grass', cd:.98, dmg:46, radius:164, range:190, arc:1.95, slow:.58, knock:35,
      vis:{melee:'vine',pal:'electric'}, desc:'帶電荊棘鞭橫掃較遠的前方，讓被纏住的敵人遲緩。' }],
    [20151, { name:'魚叉機關砲', mode:'shot', type:'water', cd:1.25, dmg:40, speed:255, size:9, homing:2.4, blastRadius:65,
      vis:{proj:'digi-missile',pal:'water',trail:'bubbles'}, desc:'射出魚叉型追蹤彈，命中後炸開，兼具追擊與濺射。' }],
    [20152, { name:'重槌火花', mode:'slam', type:'electric', cd:1.4, dmg:60, radius:104, range:125, knock:130, slow:.25,
      vis:{melee:'impact',pal:'electric'}, desc:'重槌敲擊前方地面，電光衝擊擊退一群敵人。' }],
    [20153, { name:'極寒暴風雪', mode:'blizzard', type:'ice', cd:1.9, dmg:66, range:235, radius:128, arc:1.85, slow:.72,
      fieldDuration:2.7, fieldTick:.55, vis:ice, desc:'用寬闊冰風凍慢敵群，留下範圍更大的持續冰霜區。' }],
    [20161, { name:'天堂之拳', mode:'beam', type:'fairy', cd:1.05, dmg:38, radius:190, range:215, width:44, knock:90,
      vis:{beam:'star',pal:'holy',melee:'impact'}, desc:'神聖拳勁直線打穿敵人，較寬但射程中等。' }],
    [20162, { name:'天國之門', mode:'gate', type:'fairy', cd:2.9, dmg:83, charge:.25, range:290, radius:102, slow:.4, pull:.65,
      fieldDuration:1.9, fieldTick:.35, vis:{proj:'ring',pal:'holy'}, desc:'在目標處開啟異次元之門，吸引與遲緩敵人並分段傷害；首領不會被即死放逐。' }],
    [20163, { name:'七重天堂', mode:'shot', type:'fairy', cd:1.8, dmg:18, count:7, arc:.9, speed:340, life:1.8, size:8, homing:2.7,
      charge:.16, vis:holy, desc:'同時射出七顆神聖能量球，向敵人彎曲追蹤。' }],
    [20172, { name:'神聖弓箭', mode:'shot', type:'fairy', cd:.95, dmg:40, speed:620, life:1.3, size:6, pierce:5,
      vis:{proj:'needle',pal:'holy',trail:'spark'}, desc:'發射高速神聖箭矢，直線穿透多名敵人。' }],
    [20173, { name:'神聖火焰', mode:'shot', type:'fairy', cd:1.15, dmg:25, count:3, arc:.4, speed:330, life:1.5, pierce:3, burn:1,
      vis:{proj:'fire',pal:'holy',trail:'wisp'}, desc:'吐出三道神聖能量火焰，貫穿並淨化前方敵群。' }],
    [20174, { name:'伊甸園標槍', mode:'beam', type:'fairy', cd:1.5, dmg:71, charge:.18, radius:340, range:365, width:32,
      vis:{beam:'streak',pal:'holy',proj:'needle'}, desc:'以神聖標槍釋放集中光束，貫穿遠方一列敵人。' }],
    [20201, { name:'暴龍劍・加魯魯砲', mode:'dual', type:'fire', cd:1.8, dmg:83, radius:172, range:370, width:37, arc:2.5,
      vis:{melee:'claw',pal:'fire'}, secondary:{type:'ice',dmg:78,slow:.68,range:370,width:37,digiVis:{beam:'ice',pal:'ice'}},
      desc:'暴龍劍橫斬近敵，同時用加魯魯砲貫穿遠方並凍慢目標。' }]
  ];
  const extras = [
    [20103, 'digimon-wargreymon-tornado', { name:'戰鬥龍捲風', mode:'dash', type:'fire', cd:1.55, dmg:64, charge:.12,
      range:200, radius:200, width:70, knock:95, vis:{proj:'wind',pal:'fire',melee:'claw'}, desc:'高速旋轉後向前突進，沿途切開敵人；是蓋亞能量砲之外的近戰選擇。' }],
    [20113, 'digimon-metalgarurumon-missiles', { name:'優雅十字冷凍者', mode:'shot', type:'ice', cd:1.65, dmg:20, count:4,
      arc:.7, homing:3, speed:310, size:7, blastRadius:40, slow:.4, vis:{proj:'digi-missile',pal:'ice',trail:'spark'}, desc:'展開四發冷凍追蹤飛彈，追打分散的目標。' }],
    [20008, 'digimon-gatomon-catseye', { name:'貓眼', mode:'aura', type:'psychic', cd:2, dmg:10, radius:140, slow:.75,
      vis:{proj:'ring',pal:'holy',aura:'star'}, desc:'以銳利目光牽制近敵；本作以大幅遲緩改編控制效果。' }],
    [20143, 'digimon-rosemon-temptation', { name:'禁斷誘惑', mode:'aura', type:'grass', cd:2.25, dmg:64, radius:142, slow:.65,
      charge:.2, vis:{proj:'petal',pal:'fairy',aura:'petal'}, desc:'散出花瓣能量淨化身邊敵人，並讓敵群短暫遲緩。' }],
    [20172, 'digimon-angewomon-charm', { name:'天堂紫光', mode:'aura', type:'fairy', cd:2.3, dmg:53, radius:136,
      vis:{proj:'star',pal:'holy',aura:'star'}, desc:'散出神聖光芒攻擊近敵，補足神聖弓箭較弱的近身範圍。' }]
  ];
  const kinds = {shot:'projectile',nova:'nova',melee:'melee',beam:'beam',dash:'dash',slam:'melee',gate:'meteor',aura:'aura',blizzard:'cone',dual:'beam'};
  const byDex = new Map(), definitions = new Map(), secondary = new Map();
  const references = new Map(window.PS_DIGIMON_SKILL_REFERENCES.records.map(r => [r.dex,r]));
  function register(dex, id, design) {
    const definition = { speed:340, life:1.5, size:7, count:1, arc:1.6, spread:0, pierce:0,
      radius:140, range:480, width:24, homing:0, knock:0, burn:0, poison:0, slow:0,
      ...design, id, kind:kinds[design.mode], digiMode:design.mode, digimonSkill:true,
      digiVis:design.vis || {}, maxLvl:5,
      ups:[{t:'傷害 +20%',m:{dmg:1.2}},{t:'冷卻 -10%',m:{cd:.9}},
        {t:'攻擊範圍與飛行時間 +12%',m:{radius:1.12,width:1.12,life:1.12}},
        {t:'傷害 +25%',m:{dmg:1.25}}] };
    delete definition.mode; delete definition.vis;
    const shapeAliases={ice:'shard',spark:'bolt',petal:'leaf',feather:'digi-feather'};
    definition.digiVis={...definition.digiVis};
    for(const key of ['proj','beam','aura']) {
      if(shapeAliases[definition.digiVis[key]]) definition.digiVis[key]=shapeAliases[definition.digiVis[key]];
    }
    const existing=G.Moves.BY_ID[id];
    if (existing) { for(const key of Object.keys(existing)) delete existing[key]; Object.assign(existing,definition); }
    else { G.Moves.BY_ID[id]=definition;G.Moves.ALL.push(definition); }
    definitions.set(id,G.Moves.BY_ID[id]);
    const record=G.Digimon.records.get(dex);
    if(id===record.start) { record.attack=design.name;byDex.set(dex,G.Moves.BY_ID[id]); }
    else { if(!secondary.has(dex))secondary.set(dex,[]);secondary.get(dex).push(id); }
  }
  profiles.forEach(([dex,design]) => register(dex,G.Digimon.records.get(dex).start,design));
  extras.forEach(([dex,id,design]) => register(dex,id,design));
  const poolFor=G.Moves.poolFor;
  G.Moves.poolFor=mon => {
    const current=G.Digimon.records.get(mon.dex);
    if(!current)return poolFor(mon);
    const roots=current.stage===4?[20001,20002]:[current.baseDex];
    const family=[...G.Digimon.records.values()].filter(r=>r.dex===current.dex || (roots.includes(r.baseDex)&&r.stage<current.stage));
    return [...new Set([current.start,...family.flatMap(r=>[r.start,...(secondary.get(r.dex)||[])])])];
  };
  G.DigimonSkillCatalog={byDex,definitions,references,secondary};
  // Runtime-generated guide: official identity/source next to this edition's explicit game rules.
  const guide=document.createElement('section');guide.id='scr-digimon-skills';guide.className='scr dim hidden';guide.translate=false;
  guide.innerHTML='<div class="box"><div class="digimon-heading"><h2>數碼寶貝技能圖鑑</h2><button class="btn small ghost" id="digimon-skills-close">返回</button></div><p class="sub">招式身份參考官方圖鑑與動畫；傷害、冷卻、追蹤與控場強度為本地生存遊戲改編。</p><div class="digimon-skill-guide"></div></div>';
  const body=guide.querySelector('.digimon-skill-guide');
  for(const record of G.Digimon.records.values()) {
    const def=byDex.get(record.dex),ref=references.get(record.dex);
    const item=document.createElement('article');item.className='digimon-skill-entry';
    item.innerHTML=`<h3>${record.chinese} · ${def.name}</h3><p>${def.desc}</p><small>冷卻 ${def.cd} 秒 · 基礎傷害 ${def.dmg} · 可升至 Lv.5</small>`;
    for(const attack of ref.attacks) {
      const link=document.createElement('a');link.href=attack.source_url;link.target='_blank';link.rel='noopener noreferrer';
      link.textContent='來源：'+attack.name;item.appendChild(link);
    }
    for(const id of secondary.get(record.dex)||[]) {
      const text=document.createElement('p');text.textContent='可學招式：'+definitions.get(id).name+' — '+definitions.get(id).desc;item.append(text);
    }
    body.append(item);
  }
  document.body.append(guide);
  const button=document.createElement('button');button.className='btn small';button.id='digimon-skill-guide';button.textContent='技能圖鑑與來源';
  button.onclick=()=>guide.classList.remove('hidden');
  document.querySelector('#scr-digimon .digimon-evo-tabs').after(button);
  guide.querySelector('#digimon-skills-close').onclick=()=>guide.classList.add('hidden');
  const style=document.createElement('style');style.textContent=`#scr-digimon-skills{z-index:170;background:#08152be8}
    #scr-digimon-skills>.box{width:min(850px,100%)}.digimon-skill-entry{padding:14px 0;border-bottom:1px solid #ffffff33}
    .digimon-skill-entry p{margin:6px 0}.digimon-skill-entry small{display:block;color:#b9cbf0}.digimon-skill-entry a{display:inline-block;margin:6px 14px 0 0;font-size:12px;color:#ffe38b}`;
  document.head.append(style);
})();
