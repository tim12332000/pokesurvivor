/* Naruto signature identities; combat rules and balance are this edition's adaptation. */
(() => {
  if (!G.Naruto || !G.DigimonSkills) return;

  Object.assign(G.VFX.PAL, {
    'naruto-blue': ['#102851', '#1767aa', '#35bfff', '#9feaff', '#ffffff'],
    'naruto-red': ['#250b12', '#751626', '#d93443', '#ff8b83', '#ffe9d5'],
    'naruto-sand': ['#4d3014', '#91622b', '#c79a53', '#edd395', '#fff0ca'],
    'naruto-fireball': ['#601509', '#bf3010', '#f66b13', '#ffbd36', '#fff3b0'],
    'naruto-fuma-steel': ['#090c10', '#171b22', '#46515d', '#bdc7ce', '#eef3f5']
  });

  // Chapter 223's broad exhaled fire mass, drawn separately from small Ember flames.
  // 36-pixel body × PX 2 × base scale 1.6; flight growth scales art and collision together.
  G.VFX.SHAPES['naruto-great-fireball'] = {
    w:51,h:43,frames:3,dir:true,gen(P,frame) {
      P.fill((x,y)=>{
        const dx=x-29,dy=y-21,r=Math.hypot(dx,dy),a=Math.atan2(dy,dx);
        const edge=17.5+1.1*Math.sin(a*7+frame*2)+.7*Math.cos(a*11-frame);
        // An irregular round front with flame tongues pointing back toward the caster.
        if(r>edge){
          const neck=6+3*Math.sin((x+frame*3)*.55);
          if(x>2&&x<24&&Math.abs(dy)<neck*(x/24))return Math.abs(dy)<2?'l':'d';
          return null;
        }
        const curl=Math.sin(a*3+r*.4-frame*1.6);
        if(r>edge-2.3)return 'd';
        if(r>13+curl*1.5)return 'm';
        if(Math.hypot(dx-3,dy+1)<7+curl)return 'w';
        return r<12+curl*2?'l':'m';
      });
      P.line(2,19+frame,16,17,'m',1,'d');
      P.line(6,28-frame,17,25,'l',1,'m');
      P.line(12,8+frame,20,12,'m',1,'d');
      P.outline();
    }
  };
  G.VFX.SHAPES['naruto-great-fireball-burst'] = {
    w:51,h:51,frames:3,gen(P,frame) {
      P.fill((x,y)=>{
        const dx=x-25,dy=y-25,r=Math.hypot(dx,dy),a=Math.atan2(dy,dx);
        const edge=20+2*Math.sin(a*9+frame*2)+Math.cos(a*13);
        return r>edge?null:r>edge-3?'d':r>14?'m':r>7?'l':'w';
      });P.outline();
    }
  };

  // Reference prop: black recurved blades, narrow silver cutting edges, small central rivet.
  G.VFX.SHAPES['naruto-fuma-shuriken'] = {
    w:35,h:35,frames:1,spin:true,gen(P) {
      const blade=[[2,-1],[7,-3],[11,-6],[14,-11],[16,-7],[16,-2],[14,2],[10,4],[6,3],[3,1]];
      const inside=(x,y)=>{
        let yes=false;
        for(let i=0,j=blade.length-1;i<blade.length;j=i++){
          const [ax,ay]=blade[i],[bx,by]=blade[j];
          if((ay>y)!==(by>y)&&x<(bx-ax)*(y-ay)/(by-ay)+ax)yes=!yes;
        }
        return yes;
      };
      P.fill((x,y)=>{
        const dx=x-17,dy=y-17;
        if(Math.hypot(dx,dy)<2.8)return 'd';
        for(const [u,v] of [[dx,dy],[dy,-dx],[-dx,-dy],[-dy,dx]])
          if(inside(u,v))return 'd';
        return null;
      });
      for(let q=0;q<4;q++){
        const rotate=([x,y])=>q===0?[x,y]:q===1?[-y,x]:q===2?[-x,-y]:[y,-x];
        for(let i=4;i<8;i++){
          const [ax,ay]=rotate(blade[i]),[bx,by]=rotate(blade[i+1]);
          P.line(17+ax,17+ay,17+bx,17+by,'l',1,'m');
        }
        const [tx,ty]=rotate(blade[3]);P.set(17+tx,17+ty,'l');
      }
      P.outline();
      for(let y=16;y<=18;y++)for(let x=16;x<=18;x++)P.set(x,y,'m');
      P.set(17,16,'l');P.set(16,16,'w');P.set(17,17,'d');
    }
  };
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
  const clones=G.NarutoClones.config;
  const profiles = [
    [30001, 'naruto', '多重影分身之術', 'Multi Shadow Clone Jutsu', '01_1423', {
      mode: 'shadow-clones', icon:'shadowClones', passive: true, type: 'fighting', cd: clones.cooldown, dmg: clones.punchDamage, range: 240,
      cloneDuration: clones.duration, punchCd: clones.punchCooldown, vis: { pal: 'naruto-blue' },
      desc:`學會後自動召喚，不占主動槽；冷卻 ${clones.cooldown} 秒。結印 ${clones.sealDuration} 秒後召喚基礎 ${clones.counts.join('／')} 隻分身，持續 ${clones.duration} 秒；數量卡每張使分身數 ×1.25，累乘後取整。分身模仿螺旋丸、螺旋手裏劍與忍具，各自造成完整傷害；每隻受擊 ${clones.hitsToDismiss} 次後消散。`,
      ups: clones.counts.slice(1).map(count=>({t:`分身基礎數量 → ${count} 隻；每隻完整傷害`,m:{}}))
    }],
    [30002, 'sasuke', '千鳥', 'Chidori', '01_1296', {
      mode: 'chidori-chain', icon:'chidori', type: 'electric', cd: 1.05, dmg: 44, charge: .09,
      minCooldown: G.NarutoChidori.config.minCooldown,
      range: 170, radius: 170, width: 34, knock: 50,
      vis: { proj: 'bolt', melee: 'claw', pal: 'naruto-blue' },
      desc:`基礎連續突進 ${G.NarutoChidori.config.counts.join('／')} 次，數量卡每張使追擊次數 ×1.25，累乘後取整；不能連續攻擊同一目標。第二擊起每擊傷害再 ×1.05，速度逐擊加快、最高 ×3；施放時固定鏡頭，僅追擊畫面附近目標，結束返回原位。飛行可穿牆且無敵，返回後無敵 0.3 秒，結印與轉向仍可受傷；再次施放間隔至少 ${G.NarutoChidori.config.minCooldown} 秒。`,
      ups: G.NarutoChidori.config.counts.slice(1).map((count,index)=>({
        t: `基礎追擊次數 → ${count} 次；${['傷害 +20%','冷卻 -10%','攻擊範圍 +12%','傷害 +25%'][index]}`,
        m: [{dmg:1.2},{cd:.9},{radius:1.12,width:1.12,life:1.12,range:170*1.12},{dmg:1.25}][index]
      }))
    }],
    [30003, 'sakura', '櫻花衝', 'Cherry Blossom Impact', '01_1743', {
      mode: 'slam', type: 'fighting', cd: 1.3, dmg: 55,
      range: 115, radius: 105, knock: 145,
      vis: { melee: 'impact', pal: 'fairy' },
      desc:'重擊前方地面，造成圓形範圍傷害並擊退敵人。'
    }],
    [30004, 'kakashi', '雷切', 'Lightning Blade', '01_1327', {
      mode: 'dash', type: 'electric', cd: 1.3, dmg: 46, charge: .1,
      range: 95, radius: 95, width: 32,
      vis: { beam: 'bolt', proj: 'bolt', pal: 'naruto-blue' },
      desc:'短距離突進穿刺，傷害路徑上的敵人；遇牆停止。'
    }],
    [30005, 'hinata', '柔拳', 'Gentle Fist', '01_1668', {
      mode: 'melee', type: 'fighting', cd: .72, dmg: 30, count: 3, burstInterval: .08,
      range: 100, radius: 78, arc: 1.5, knock: 15,
      vis: { melee: 'impact', proj: 'fire', pal: 'naruto-blue' },
      desc:'向前連打三掌，總傷害由三掌分攤。'
    }],
    [30006, 'lee', '木葉旋風', 'Leaf Whirlwind', '01_1489', {
      mode: 'melee', type: 'fighting', cd: 2, icon:'leafWhirlwind', dmg: 37,
      range: 72.5, radius: 62, arc: 3.9, knock: 95,
      vis: { melee: 'claw', proj: 'wind', pal: 'grass' },
      desc:'旋身大角度橫掃，踢開近身與側面敵人。'
    }],
    [30007, 'gaara', '砂時雨', 'Sand Shower (game adaptation)', '01_1695', {
      mode: 'gaara-sand-burst', icon:'sandShower', passive: true, type: 'ground', cd: 1.2, dmg: 28,
      range: 260, count: 3, knock: 12,
      ups:[{t:'整輪基礎傷害 34＋角色等級',m:{dmg:34/28}},
        {t:'砂彈 4 枚・距離 280',m:{count:1,range:280}},
        {t:'整輪基礎傷害 42＋角色等級',m:{dmg:42/34}},
        {t:'整輪基礎傷害 52＋角色等級・砂彈 5 枚・距離 300',m:{dmg:52/42,count:1,range:300}}],
      vis: { pal: 'naruto-sand' },
      desc:'常駐自動普攻，不占主動槽、不需選招。連發追蹤砂流，沿用護衛的碎砂與尾流演出，平滑轉彎追擊目標。整輪基礎傷害＝當階傷害（28／34／34／42／52）＋角色等級，每級 +1，平均分配至當階原有彈數。首次碰到敵人或牆即消散，不爆炸、不貫穿，追蹤不增加飛行射程。數量卡增加彈數，單彈傷害不變；基礎冷卻 1.2 秒，冷卻卡有效。'
    }],
    [30008, 'itachi', '月讀', 'Tsukuyomi', '01_1316', {
      mode: 'single-illusion', type: 'psychic', cd: 3.6, dmg: 30, range: 260,
      fieldDuration: 1.5, slow: .9, bossSlow: .25,
      vis: { proj: 'ring', aura: 'ring', pal: 'naruto-red' },
      desc:'對一名可見敵人造成精神傷害並短暫減速；首領減速較弱。'
    }]
  ];
  const tentenSource='https://naruto-official.com/es/anime/naruto1/list/01_267';
  profiles.push([30009,'tenten','忍具連投','Ninja Tools (game adaptation)','tenten',{
    mode:'tenten-kunai',passive:true,icon:'tentenKunai',type:'steel',cd:1.1,dmg:8,
    range:300,count:3,speed:490,life:1,size:5,burstInterval:.07,
    ups:[{t:'單枚傷害 +20%',m:{dmg:1.2}},{t:'基礎苦無 4 枚',m:{count:1}},
      {t:'單枚傷害 +20%',m:{dmg:1.2}},{t:'基礎苦無 5 枚・單枚傷害 +25%',m:{count:1,dmg:1.25}}],
    desc:'常駐自動普攻，不占主動槽、不需選招。小卷軸解封後短連投苦無，基礎 3／3／4／4／5 枚，單枚傷害 8／9.6／9.6／11.52／14.4。射程 300，冷卻 1.1 秒。苦無實際飛行並被牆遮擋，優先分配不同敵人；數量卡使枚數 ×1.25，累乘取整，單枚傷害不變。可穿過自己的落地爆符，提前引爆並使該次爆炸傷害 +25%。'
  }]);
  const painSource='https://naruto-official.com/en/news/01_1321';
  const painUps=(counts=null)=>[1.2,1.4/1.2,1.7/1.4,2/1.7].map((ratio,i)=>({
    t:`傷害倍率 → ${[1.2,1.4,1.7,2][i]}${counts?`・基礎數量 ${counts[i+1]}`:''}`,
    m:{dmg:ratio,...(counts&&counts[i+1]!==counts[i]?{count:counts[i+1]-counts[i]}:{})}
  }));
  profiles.push([30010,'pain','黑棒連射','Six Paths of Pain','01_1321',{
    mode:'pain-basic',passive:true,icon:'painRod',type:'psychic',cd:1.2,dmg:10,
    count:5,range:280,speed:440,size:4,ups:painUps([5,5,6,7,8]),
    desc:'常駐普攻，不占主動槽。黑棒從天而降，空中預判移動並修正落點，觸地前短暫鎖定，落地時單體命中；快速轉向或瞬移仍可躲開，牆會阻擋。忍具連彈在命中後接續彈向附近敵人。基礎 5／5／6／7／8 根，每根傷害倍率 1／1.2／1.4／1.7／2。數量卡 ×1.25 累乘取整，最多 40 根。五具支援道生命皆為天道的 2 倍；有吸血時，攻擊的支援道與天道各自回復完整比例，互不分攤。低血撤回，安全脫戰後恢復至半血。出生／復歸整備 1.5 秒；倒下 16 秒後尋找安全位置復歸。天道倒下時，已現身且存活的地獄道可用閻王救回；兩道都倒下則結束。'
  }]);
  const temariSource='https://naruto-official.com/it/anime/naruto1/list/01_267';
  const temariDamageUps=(values,ranges=null)=>values.slice(1).map((damage,i)=>({
    t:`每次傷害 ${damage}${ranges?`・射程 ${ranges[i+1]}`:''}`,
    m:{dmg:damage/values[i],...(ranges?{range:ranges[i+1]}:{})}
  }));
  profiles.push([30011,'temari','鐮鼬之術','Temari — Wind Release','temari',{
    mode:'temari-wind',passive:true,icon:'temariFan',type:'flying',cd:1.6,dmg:8,
    count:3,range:240,speed:420,size:9,arc:Math.PI/4,contactRadius:30,
    ups:temariDamageUps([8,9.6,11.52,14.4,18],[240,250,270,290,310]).map((up,i)=>({...up,
      t:up.t+`・角度${[75,105,135,180][i]}°`,m:{...up.m,arc:[75/45,105/75,135/105,180/135][i]}})),source_url:temariSource,
    desc:'常駐風浪，不占主動槽。角度隨階級擴大45／75／105／135／180度，最高階掃過前方半圈。每輪floor(3×1.25^數量卡)道風浪造成鐮鼬切割，短暫吹起小怪、阻止前進；同輪連切不重置吹起時間，特殊敵人免疫。每次傷害8／9.6／11.52／14.4／18，冷卻1.6秒，射程240／250／270／290／310；牆會阻擋。精通使每波連切1＋精通等級＋數量卡次，每次重新檢查接觸。'
  }]);
  const shared = [
    ['naruto-kunai', {
      name: '苦無投擲', mode: 'shot', type: 'steel', cd: .68, dmg: 17,
      speed: 530, life: 1.1, size: 5, pierce: 1, range: 500,
      vis: { proj: 'needle', pal: 'steel' }, desc:'快速投擲苦無，貫穿前方一名敵人。'
    }],
    ['naruto-shuriken', {
      name: '手裏劍散射', mode: 'nova', type: 'steel', cd: 1.4, dmg: 9,
      count: 8, speed: 325, life: .9, size: 5,
      vis: { proj: 'star', pal: 'steel' }, desc:'向八個方向投出手裏劍。'
    }]
  ];
  const extra = [
    ['naruto-naruto', [30001], {
      icon:'rasengan', name: '螺旋丸', mode: 'dash', type: 'fighting', cd: 2, dmg: 48, charge: .6,
      range: 125, radius: 125, width: 56, knock: 100,
      vis: { proj: 'wind', melee: 'impact', pal: 'naruto-blue' },
      desc:'原地集氣 0.6 秒後向前突進，突進中免傷；收招衝擊推開周圍一般敵人，並獲得 0.5 秒保護。每個沿途目標只受一次傷害；選用時，現存影分身各自接近敵人並施放完整傷害的螺旋丸。',
      source_url: 'https://naruto-official.com/en/news/01_1423'
    }],
    ['naruto-rasenshuriken', [30001], {
      icon:'rasenshuriken', name: '風遁・螺旋手裏劍', mode: 'shot', type: 'flying', cd: 2.5, dmg: 58,
      speed: 350, life: 1.3, size: 15, range: 455, blastRadius: 110, knock: 65,
      vis: { proj: 'naruto-wind-shuriken', trail: 'wind', pal: 'naruto-blue' },
      desc:'投擲旋轉手裏劍，命中後爆發風刃，傷害周圍敵人。',
      source_url: 'https://naruto-official.com/en/news/01_1423'
    }],
    ['naruto-nine-tails-cloak', [30001], {
      icon:'nineTailsCloak', name:'九尾查克拉外衣', mode:'nine-tails-cloak', type:'fighting', cd:18, dmg:0, learnLevel:9,
      fieldDuration:8, atkMul:1.5, speedMul:1.25, damageTakenMul:.75,
      radius:76, pulseDamage:12, pulseInterval:.65, knock:18,
      vis:{pal:'naruto-red'},
      desc:'需選中才會施放。一尾外衣持續 8 秒：攻擊 +50%、移速 +25%、一般傷害 -25%，每 0.65 秒反擊近身敵人。切招仍有效，不能疊加。',
      ups:[{t:'外衣持續時間 → 9 秒',m:{fieldDuration:9}},
        {t:'外衣攻擊加成 → +65%',m:{atkMul:1.65}},
        {t:'外衣移速加成 → +35%',m:{speedMul:1.35}},
        {t:'冷卻 -15%、持續時間 → 10 秒',m:{cd:.85,fieldDuration:10}}],
      source_url:'https://naruto-official.com/en/news/01_1296'
    }],
    ['naruto-fireball', [30002, 30008], {
      icon:'greatFireball', name: '火遁・豪火球之術', mode: 'shot', type: 'fire', cd: 2.3, dmg: 49,
      speed: 300, life: 1.4, size: 52, range: 420, burn: .12,
      fireballAOE:true, fireballTick:.2,
      fireballGrowth: {startRatio:.2,endRatio:1.4,distance:300},
      vis: { proj: 'naruto-great-fireball', projScale: 1.6, trail: 'ember', pal: 'naruto-fireball' },
      desc:'吐出逐漸變大的穿透火球，持續造成範圍傷害；同一敵人每 0.2 秒最多命中一次。遇牆停留燃燒，發射後 1.4 秒消散。',
      source_url: 'https://naruto-official.com/en/anime/naruto1/list/01_354',
      owner_sources: { 30008: 'https://naruto-official.com/en/news/01_2332' }
    }],
    ['naruto-water-dragon', [30004], {
      name: '水遁・水龍彈之術', mode: 'shot', type: 'water', cd: 2.65, dmg: 56,
      speed: 320, life: 1.45, size: 18, range: 464, blastRadius: 95, knock: 90,
      vis: { proj: 'naruto-water-dragon', trail: 'bubble', pal: 'water' },
      desc:'水龍衝向目標，命中後爆發水浪，傷害並擊退周圍敵人。',
      source_url: 'https://naruto-official.com/en/news/01_2665'
    }]
  ];
  extra.push(
    ['naruto-tenten-guard',[30009],{
      name:'操具・護身陣',mode:'tenten-guard',icon:'tentenGuard',passive:true,type:'steel',learnLevel:4,
      cd:8,dmg:0,guardRadius:100,guardKnock:70,guardSpeedBonus:.15,
      ups:[{t:'護身半徑 110・擊退 80・疾退速度 +20%',m:{guardRadius:110,guardKnock:80,guardSpeedBonus:.20}},
        {t:'護身半徑 120・擊退 90・疾退速度 +25%',m:{guardRadius:120,guardKnock:90,guardSpeedBonus:.25}},
        {t:'護身半徑 130・擊退 100・疾退速度 +30%',m:{guardRadius:130,guardKnock:100,guardSpeedBonus:.30}},
        {t:'護身半徑 140・擊退 110・疾退速度 +35%',m:{guardRadius:140,guardKnock:110,guardSpeedBonus:.35}}],
      desc:'常駐被動，不占主動槽。可見敵人靠近 80 距離時自動開卷，0.12 秒後掃開周圍普通敵人並攔截普通敵彈，再獲得 1.5 秒疾退加速。五階半徑 100／110／120／130／140，擊退 70／80／90／100／110，加速 +15／20／25／30／35%。護身陣基礎冷卻 8 秒，冷卻縮減有效、最低 3 秒。另外常駐一枚護身符，移動接觸後擋下一發來襲飛行彈，包含 Boss 飛行彈，獨立固定冷卻 3 秒。護符五階索敵 180／200／220／240／260，移速為角色有效移速加 240；不擋光束、地面、環繞或明確不可攔截攻擊，不穿牆。兩者均不造成傷害，護身陣不擊退首領與精英；數量卡不增加護符。招名與機制為本作改編。',source_url:tentenSource
    }],
    ['naruto-sharingan', [30002], {
      name:'寫輪眼・進化', mode:'sharingan-evolution', passive:true, type:'psychic', cd:0, dmg:0,
      range:320,
      vis:{pal:'naruto-red'},
      desc:'常駐被動，學會即生效、不占主動槽。五階效果累加：閃避 +5%、拾取範圍 +20%；閃避反擊手裏劍、反擊傷害 +35%；遠程彈道 +1；牽引後留下本局永久黑炎，每秒傷害最大生命 2%（首領 0.5%）；減傷 30% 並自動範圍斬擊。數量加成增加反擊彈數。',
      ups:[
        {t:'進化二勾玉：閃避成功發射 3 枚看破手裏劍',m:{}},
        {t:'進化三勾玉：殘影、所有遠程彈道 +1',m:{}},
        {t:'開啟天照：牽引渦流留下本局永久百分比黑炎',m:{}},
        {t:'開啟須佐能乎：護體減傷 30%、自動範圍斬擊',m:{}}
      ],
      source_url:'https://naruto-official.com/en/news/01_1296'
    }],
    ['naruto-medical-heal', [30003], {
      name:'醫療忍術', mode:'medical-heal', type:'fairy', cd:7, dmg:0, healFraction:.22,
      vis:{pal:'grass'}, desc:'恢復自身最大生命 22%；滿血不消耗冷卻，不能復活。',
      source_url:'https://naruto-official.com/en/news/01_1743'
    }],
    ['naruto-regeneration', [30003], {
      name:'創造再生', mode:'regeneration', type:'fairy', cd:18, dmg:0,
      fieldDuration:5, healFraction:.045,
      vis:{pal:'grass'}, desc:'每秒恢復最大生命 4.5%，持續 5 秒；不能復活。',
      source_url:'https://naruto-official.com/en/news/01_1743'
    }],
    ['naruto-earth-wall', [30004], {
      name:'土遁・土流壁', mode:'earth-wall', type:'ground', cd:9, dmg:0,
      fieldDuration:3, width:100, range:72,
      vis:{pal:'naruto-sand'}, desc:'升起短暫土牆，阻擋敵方接觸與飛行攻擊；玩家可穿過。',
      source_url:'https://naruto-official.com/en/news/01_2541'
    }],
    ['naruto-twin-lions', [30005], {
      name:'柔步雙獅拳', mode:'melee', type:'fighting', cd:1.25, dmg:52,
      count:2, burstInterval:.14, radius:100, range:125, arc:1.9, knock:35,
      vis:{melee:'naruto-lion',pal:'naruto-blue'},
      desc:'先後打出兩拳，總傷害由兩拳分攤。',
      source_url:'https://naruto-official.com/en/news/01_2199'
    }],
    ['naruto-byakugan', [30005], {
      name:'白眼偵察', mode:'byakugan', type:'psychic', cd:10, dmg:0,
      fieldDuration:5, radius:280, damageMul:1.2,
      vis:{pal:'naruto-blue'}, desc:'標記周圍敵人，強化柔拳與柔步雙獅拳的近身傷害。',
      source_url:'https://naruto-official.com/en/news/01_1668'
    }],
    ['naruto-lotus', [30006], {
      icon:'frontLotus', name:'表蓮華', mode:'lee-lotus', type:'fighting', learnLevel:3, cd:5, dmg:110,
      range:145, radius:60,
      ups:[
        {t:'傷害 +20%',m:{dmg:1.2}},
        {t:'基礎冷卻維持 5 秒，可用冷卻縮減卡縮短',m:{}},
        {t:'攻擊範圍與持續時間 +12%',m:{radius:1.12,width:1.12,life:1.12,range:162.4}},
        {t:'傷害 +25%',m:{dmg:1.25}}
      ],
      vis:{pal:'grass'}, desc:'基礎冷卻 5 秒，冷卻縮減卡有效。繃帶同時拉近 3 名一般地面敵人，數量卡使綁定數 ×1.25，取整後最多 12 名。主目標接挑空、抱身重摔，其餘吃落地震擊；主目標空中倒下仍完成落地。冷卻自動近身普攻，連段中不插普攻；首領不被拉動、不浮空，由小李接近。',
      source_url:'https://naruto-official.com/en/news/01_1652'
    }],
    ['naruto-gates', [30006], {
      icon:'eightGates', name:'八門遁甲・開門', mode:'gates-passive', passive:true, type:'fighting', learnLevel:6, cd:0, dmg:0,
      vis:{pal:'grass'},
      desc:'常駐被動，學會即生效、不占主動槽：生命上限＋LV×N；每秒回血 N%；回血量／跑速＋(10N＋LV)%，並提高攻擊。N＝技能等級，LV＝角色等級。',
      ups:[
        {t:'休門：生命加成改為 LV×2；回血 2%/秒；攻擊＋35%；回血量／跑速＋(20＋LV)%',m:{}},
        {t:'生門：生命加成改為 LV×3；回血 3%/秒；攻擊＋40%；回血量／跑速＋(30＋LV)%',m:{}},
        {t:'傷門：生命加成改為 LV×4；回血 4%/秒；攻擊＋45%；回血量／跑速＋(40＋LV)%',m:{}},
        {t:'杜門：生命加成改為 LV×5；回血 5%/秒；攻擊＋50%；回血量／跑速＋(50＋LV)%',m:{}}
      ],
      source_url:'https://naruto-official.com/en/news/01_1652'
    }],
    ['naruto-reverse-lotus', [30006], {
      icon:'reverseLotus', name:'裏蓮華', mode:'lee-reverse-lotus', type:'fighting', learnLevel:9, cd:5, dmg:210,
      range:180, radius:100,
      ups:[
        {t:'空中連擊 +2（7 次）・傷害 +20%・落地範圍擴大至 120',m:{dmg:1.2,radius:1.2}},
        {t:'空中連擊 +2（9 次）・落地範圍擴大至 140',m:{radius:7/6}},
        {t:'空中連擊 +2（11 次）・繃帶射程 +12%・落地範圍擴大至 160',m:{range:201.6,radius:8/7}},
        {t:'空中連擊 +2（13 次）・傷害 +25%・落地範圍擴大至 180',m:{dmg:1.25,radius:9/8}}
      ],
      vis:{pal:'grass'}, desc:'基礎冷卻 5 秒，冷卻卡有效，全程最多 3.3 秒。繃帶同時拉近 3 名一般地面敵人，數量卡使綁定數 ×1.25，最多 12 名。主目標接空中連擊，其餘吃落地震擊。基礎空中連擊 5／7／9／11／13 次；數量卡每張使連擊數 ×1.25，累乘取整。第 n 擊傷害 ×1.10^n，越踢越快、空中無敵。致命傷延至落地才擊倒；冷卻自動普攻。首領不被拉動、不浮空，由小李接近。',
      source_url:'https://naruto-official.com/en/anime/naruto1/list/01_273'
    }],
    ['naruto-sand-coffin', [30007], {
      icon:'sandCoffin', name:'砂縛柩・砂瀑送葬', mode:'gaara-coffin', type:'ground', learnLevel:3, cd:5, dmg:110,
      range:280, count:1, fieldDuration:1.1, slow:.95, bossSlow:.3,
      ups:[{t:'傷害 +20%',m:{dmg:1.2}},{t:'索敵距離提高至 310',m:{range:310}},
        {t:'傷害 +25%',m:{dmg:1.25}},{t:'傷害 +25%・索敵距離 340',m:{dmg:1.25,range:340}}],
      vis:{pal:'naruto-sand'}, desc:'優先鎖定可見精英或首領，基礎束縛數量＝1＋角色等級，最多 10 名；數量卡每張使目標數 ×1.25，累乘取整後最多 30 名。束縛 1.1 秒後每名壓縮一次，單體基礎傷害＝當階傷害（110／132／132／165／206.25）＋角色等級，每級 +1，不造成起手傷害；首領僅減速 30%。基礎冷卻 5 秒，冷卻期間自動砂彈普攻。',
      source_url:'https://naruto-official.com/en/news/01_1555'
    }],
    ['naruto-sand-shield', [30007], {
      icon:'sandShield', name:'砂之盾', mode:'gaara-shield', passive:true, type:'ground', learnLevel:1, cd:12, dmg:0,
      shieldAmount:45, range:400, guardCount:2, guardSpeedBonus:200,
      ups:[{t:'基礎盾量 120・基礎護衛數 2 團・砂鎧減傷 35%・反擊 85',m:{shieldAmount:60,guardCount:2}},
        {t:'基礎盾量 150・基礎護衛數 3 團・反擊半徑 125',m:{shieldAmount:75,guardCount:3}},
        {t:'基礎盾量 180・基礎護衛數 3 團・砂鎧減傷 40%・反擊 105',m:{shieldAmount:90,guardCount:3}},
        {t:'基礎盾量 220・基礎護衛數 4 團・砂鎧減傷 45%・反擊 130・半徑 140',m:{shieldAmount:110,guardCount:4}}],
      vis:{pal:'naruto-sand'},
      desc:'常駐被動，不占主動槽。護盾總量×2（含等級與加血轉盾），每 12 秒補滿；游砂護衛分工攔彈，其餘持續攻敵，數量卡可增加，最多 100 團；五階接觸基礎傷害 10／12.5／15／17.5／20。護衛命中首領、傳說與審判者時不觸發生命剝奪。附近有敵人時每 10 秒獲得 3 秒砂鎧，減傷 30%～45%；扣血 3 次或到期時崩砂反擊。切招不中斷，冷卻卡有效。',
      descEn:'Always active; uses no active slot. Shield refills every 12s; all shield capacity is doubled, including level and maximum-HP growth bonuses. Assigned sand guardians intercept bullets while the others keep attacking; quantity bonuses add guardians, up to 100. Tier base contact damage is 10/12.5/15/17.5/20. Guardian hits cannot trigger percent-health damage against bosses, legends or judges. With enemies nearby, gain 3s of armor every 10s for 30%-45% damage reduction; counter after three HP-damaging hits or expiry. Persists when switching skills. Cooldown bonuses apply.',
      source_url:'https://naruto-official.com/en/news/01_1555'
    }],
    ['naruto-sand-tsunami', [30007], {
      icon:'sandTsunami', name:'流砂瀑流・砂瀑大葬', mode:'gaara-tsunami', type:'ground', learnLevel:9, cd:8, dmg:240,
      range:310, radius:310, width:240, knock:0, waveDuration:.65, bindDuration:.5,
      ups:[{t:'傷害 +20%',m:{dmg:1.2}},{t:'距離 345・寬 270',m:{range:345,radius:345/310,width:270/240}},
        {t:'傷害 +25%',m:{dmg:1.25}},{t:'傷害 +25%・距離 380・寬 300',m:{dmg:1.25,range:380,radius:380/345,width:300/270}}],
      vis:{pal:'naruto-sand'}, desc:'砂浪推進造成 25% 傷害，完整束縛 0.5 秒後下壓大葬造成 75%；離開砂地不受大葬，晚進場不補傷。普通敵人減速 95%、首領 35%。基礎冷卻 8 秒，冷卻卡有效，冷卻期間自動砂彈普攻。',
      source_url:'https://naruto-official.com/en/news/01_1695'
    }],
    ['naruto-sand-prison', [30007], {
      icon:'sandPrison', name:'流砂牢', mode:'gaara-sand-prison', type:'ground', learnLevel:12,
      cd:6, dmg:12, range:300, radius:90, fieldDuration:5, fieldTick:.5, bossSlow:.35,
      ups:[{t:'每次傷害提高至 15',m:{dmg:1.25}},
        {t:'砂地半徑提高至 105',m:{radius:105/90}},
        {t:'每次傷害提高至 18',m:{dmg:1.2}},
        {t:'每次傷害提高至 24・半徑 120',m:{dmg:24/18,radius:120/105}}],
      vis:{pal:'naruto-sand'},
      desc:'選中後每 6 秒在附近敵人腳下生成圓形砂地，持續 5 秒，每 0.5 秒傷害一次、共 10 次。困住普通地面敵人並持續捲向中心；精英與首領減速 35%，受到較弱牽引。飛行與跳躍中無效，不穿牆拉人。切走立即解除，重選重新計時；冷卻卡有效。',
      source_url:'https://naruto-official.com/en/news/01_1695'
    }],
    ['naruto-sand-armor', [], {
      name:'砂鎧・崩砂反擊', nameEn:'Sand Armor: Shattering Counter', mode:'gaara-sand-armor', type:'ground', learnLevel:15,
      cd:10, dmg:70, range:180, radius:110, armorReduction:.3, fieldDuration:3,
      ups:[{t:'減傷提高至 35%・崩砂傷害 85',m:{armorReduction:.35,dmg:85/70}},
        {t:'崩砂半徑提高至 125',m:{radius:125/110}},
        {t:'減傷提高至 40%・崩砂傷害 105',m:{armorReduction:.4,dmg:105/85}},
        {t:'減傷提高至 45%・崩砂傷害 130・半徑 140',m:{armorReduction:.45,dmg:130/105,radius:140/125}}],
      vis:{pal:'naruto-sand'},
      desc:'砂之盾附帶的常駐效果，不單獨學習或選用。附近有敵人時凝聚砂鎧，持續 3 秒並減傷 30%～45%。實際受傷三次或時間結束時，崩砂造成周圍傷害並擊退普通敵人。切招仍有效；冷卻自起手計算 10 秒，傷害、範圍與冷卻卡有效，數量卡無效。本作改編。',
      descEn:'A permanent component of Sand Shield, not a separately learned or selected skill. With a nearby enemy, gain sand armor for 3 seconds and reduce damage by 30%–45%. After three damaging hits or expiry, shatter to damage nearby enemies and knock back ordinary foes. Switching skills preserves the armor and the 10-second cast cooldown. Quantity has no effect. Game adaptation.',
      source_url:'https://naruto-official.com/en/news/01_1555'
    }],
    ['naruto-black-flames', [30008], {
      name:'天照', mode:'black-flames', type:'fire', cd:4.8, dmg:12,
      range:280, radius:80, fieldDuration:3, fieldTick:.5, maxFields:2,
      vis:{pal:'naruto-red'}, desc:'在目標腳下留下持續 3 秒的黑炎，傷害區域內敵人；最多兩片。',
      source_url:'https://naruto-official.com/en/news/01_1316'
    }],
    ['naruto-kusanagi', [30002], {
      icon:'kusanagi', name:'草薙劍・環繞', mode:'kusanagi-orbit', type:'steel', learnLevel:1,
      cd:1,dmg:28,radius:58,count:1,knock:8,
      desc:'選用並施放後，飛行劍持續環繞攻擊，切招即消失。同一敵人每 0.35 秒最多命中一次；數量卡每張使劍數 ×1.25，累乘取整後，三勾玉再額外加一把劍。',
      ups:[{t:'環繞劍 +1 把',m:{count:1}},
        {t:'劍刃傷害 +30%、環繞範圍 +10%',m:{dmg:1.3,radius:1.1}},
        {t:'環繞劍再 +1 把',m:{count:1}},
        {t:'劍刃傷害 +35%、環繞範圍 +10%',m:{dmg:1.35,radius:1.1}}],
      source_url:'https://naruto-official.com/en/news/01_1710'
    }],
    ['naruto-fuma-shuriken', [30002], {
      icon:'fumaShuriken', name:'風魔手裏劍', mode:'shot', type:'steel', learnLevel:9,
      cd:1.6,dmg:34,speed:460,life:4,range:552,size:32,count:1,pierce:3,arc:.24,charge:.2,knock:24,
      fumaReturn:true,boom:.65,fumaCurve:130,
      vis:{proj:'naruto-fuma-shuriken',pal:'naruto-fuma-steel',projScale:.9},
      desc:'旋轉鋼刃沿弧線出擊並返回，基礎去、回各最多命中四名敵人，每名每程一次；牆壁會擋下。數量卡每張使枚數 ×1.25，累乘後取整，穿透每張 +1；每枚造成完整傷害。',
      ups:[{t:'手裏劍 +1 枚、穿透 +1',m:{count:1,pierce:1}},
        {t:'手裏劍傷害 +20%',m:{dmg:1.2}},
        {t:'冷卻 -15%',m:{cd:.85}},
        {t:'手裏劍 +1 枚、傷害 +25%',m:{count:1,dmg:1.25}}],
      source_url:'https://tamashiiweb.com/item/14256/?wovn=en'
    }]
  );
  const kinds = { 'gaara-sand-burst':'projectile', 'gaara-coffin':'meteor', 'gaara-tsunami':'cone', 'gaara-shield':'buff', 'gaara-sand-prison':'buff', 'gaara-sand-armor':'buff', 'chidori-chain': 'dash', dash: 'dash', melee: 'melee', slam: 'melee', beam: 'beam', shot: 'projectile', aura: 'aura', nova: 'nova', 'sand-wave': 'cone', 'shadow-clones': 'buff',
    sharingan:'buff', 'sharingan-evolution':'buff', 'medical-heal':'buff', regeneration:'buff', 'earth-wall':'buff', byakugan:'buff', gates:'buff', 'gates-passive':'buff', 'sand-shield':'buff', 'nine-tails-cloak':'buff',
    'lee-lotus':'melee', 'lee-reverse-lotus':'melee', lotus:'melee', 'sand-coffin':'meteor', 'single-illusion':'meteor', 'black-flames':'meteor', 'kusanagi-orbit':'orbit' };
  extra.push(
    ['naruto-tenten-bounce',[30009],{
      name:'忍具連彈',mode:'tenten-bounce',icon:'tentenBounce',passive:true,type:'steel',learnLevel:2,
      cd:0,dmg:0,
      ups:[{t:'基礎連彈 2 次',m:{}},{t:'基礎連彈 3 次',m:{}},{t:'基礎連彈 4 次',m:{}},{t:'基礎連彈 5 次',m:{}}],
      desc:'常駐被動，不占主動槽。原有連彈次數＝技能等級＋數量卡張數；單體忍具再加通用「忍具連彈 +1」卡張數，首擊另計。原有連彈優先選 160 內未命中的小怪，無新目標時可每隔至少 0.08 秒追打同一目標；雙昇龍另可選 Boss。通用卡的額外跳數只彈向未命中的其他敵人。牆會阻擋，傷害維持原值；附札苦無只吃原有連彈，最後落點才引爆。',source_url:tentenSource
    }],
    ['naruto-tenten-fuma',[30009],{
      name:'風魔迴刃',mode:'tenten-fuma',icon:'tentenFuma',type:'steel',learnLevel:3,
      cd:3.2,dmg:12,count:2,range:260,speed:390,size:12,pierce:3,
      ups:[{t:'每程單枚傷害 +20%',m:{dmg:1.2}},{t:'飛行距離 380',m:{range:380}},
        {t:'飛行距離 500・傷害 +20%',m:{range:500,dmg:1.2}},{t:'每程單枚傷害 +25%',m:{dmg:1.25}}],
      desc:'兩枚大型四刃手裏劍沿弧線飛出再返回。未學連彈時，去、回每程每敵人最多命中一次；學會後可消耗連彈額度重複追擊，牆壁會擋下。每程單枚傷害 12／14.4／14.4／17.28／21.6，飛行距離 260／260／380／500／500。數量卡使枚數 ×1.25，累乘取整；每張穿透 +1。選中後自動施放，切招保留已發射忍具。命中後成功回收獲得 6 秒蓄勢，下一次主動整輪傷害 +30%，不疊加；普攻不消耗。可穿過落地爆符提前引爆。招式路線與數值為本作改編。',source_url:tentenSource
    }],
    ['naruto-tenten-mastery',[30009],{
      name:'忍具精通',mode:'tenten-mastery',icon:'tentenMastery',passive:true,type:'steel',learnLevel:6,
      cd:0,dmg:0,pierceBonus:2,speedMul:1.1,
      ups:[{t:'苦無額外穿透 +3・忍具速度 +20%・飛行與索敵距離 +200',m:{pierceBonus:3,speedMul:1.2}},{t:'苦無額外穿透 +4・忍具速度 +40%・飛行與索敵距離 +300',m:{pierceBonus:4,speedMul:1.4}},
        {t:'苦無額外穿透 +5・忍具速度 +80%・飛行與索敵距離 +400',m:{pierceBonus:5,speedMul:1.8}},{t:'苦無額外穿透 +6・忍具速度 +100%・飛行與索敵距離 +500',m:{pierceBonus:6,speedMul:2}}],
      desc:'常駐被動，學會即生效、不占主動槽。苦無額外穿透 +2／3／4／5／6，忍具飛行速度 +10／20／40／80／100%。所有忍具飛行、索敵與每跳連彈距離各 +100／200／300／400／500。重複命中次數依忍具連彈額度計算。分身完整繼承技能等級，傷害只套用一次 1/3。被動機制為本作改編。',source_url:tentenSource
    }],
    ['naruto-tenten-tags',[30009],{
      name:'起爆卷・散華',mode:'tenten-tags',icon:'tentenTags',type:'fire',learnLevel:9,
      cd:5.5,dmg:36,count:2,range:280,radius:60,fieldDuration:.65,speed:420,
      ups:[{t:'每枚爆炸傷害 +20%',m:{dmg:1.2}},{t:'爆炸半徑 66',m:{radius:1.1}},
        {t:'每枚爆炸傷害 +20%',m:{dmg:1.2}},{t:'每枚爆炸傷害 +25%・半徑 72',m:{dmg:1.25,radius:72/66}}],
      desc:'投出基礎兩枚附札苦無，落點固定，紙札顯示 0.65 秒後各爆炸一次。接觸與落地不額外傷害，敵人可走出爆炸圈。每枚基傷 36／43.2／43.2／51.84／64.8，半徑 60／60／66／66／72。數量卡使枚數 ×1.25，累乘取整。落地 0.08 秒後，被自己的苦無、迴刃或雙昇龍穿過可提前引爆，該次爆炸傷害 +25%，不連鎖引爆其他爆符。招名與機制為本作改編。',source_url:tentenSource
    }],
    ['naruto-tenten-twin',[30009],{
      name:'雙昇龍',mode:'tenten-twin',icon:'tentenTwin',type:'steel',learnLevel:12,
      cd:7,dmg:8,count:24,range:680,speed:510,size:5,pierce:1,arc:Math.PI*110/180,burstInterval:.05,burstDuration:.6,
      ups:[{t:'基礎忍具 28 枚',m:{count:4}},{t:'基礎忍具 32 枚・單枚傷害 +20%',m:{count:4,dmg:1.2}},
        {t:'基礎忍具 36 枚',m:{count:4}},{t:'基礎忍具 40 枚・單枚傷害 +25%',m:{count:4,dmg:1.25}}],
      desc:'兩張卷軸繞身螺旋升空，放卷 0.12 秒後分四批射出八種忍具，形成約 110° 前方扇面。基礎 24／28／32／36／40 枚，單枚傷害 8／8／9.6／9.6／12，射程 680。數量卡使枚數 ×1.25，累乘取整，每輪上限 300 枚；超出時單枚傷害乘以原枚數 ÷ 300，保留整輪總傷害。基礎穿透 1 次，每張數量卡再 +1。整輪發射約 0.6 秒。忍具連彈可追擊其他敵人或同一 Boss，重複追擊至少間隔 0.08 秒。可走位；回收蓄勢強化整輪傷害 +30%，忍具可提前引爆自己的落地爆符。卷軸與尾跡不造成傷害。',source_url:tentenSource
    }]
  );
  extra.push(
    ['naruto-pain-gravity',[30010],{
      name:'萬象天引・神羅天征',mode:'pain-gravity',icon:'painGravity',type:'psychic',learnLevel:3,passive:true,
      cd:3,dmg:70,range:400,triggerRadius:400,pullRadius:100,radius:300,pushRadius:380,pushDuration:.24,ups:painUps(),
      desc:'學會後天道自動施放，基礎冷卻 3 秒。400 內有可見有效敵人時，萬象天引先在 0.35 秒內由慢至快將普通地面敵人拉到距天道 100，再對 300 內全部有效敵人造成單次群傷。受擊普通地面敵人在 0.24 秒內由慢至快彈到距釋放位置 380，無人數上限；特殊敵人僅承受原拉取與彈開距離的 25%。近身也先拉後推；飛行或浮空敵人不受位移，牆會阻擋，施術沒有無敵。',source_url:painSource
    }],
    ['naruto-pain-missiles',[30010],{
      name:'修羅道・飛彈齊射',mode:'pain-missiles',icon:'painMissile',type:'steel',learnLevel:6,passive:true,
      cd:4,dmg:22,count:10,range:320,radius:48,speed:400,ups:painUps([10,10,12,14,16]),
      desc:'修羅道展開機械臂，飛彈先升空 0.22 秒，每發使用不同高度與繞行半徑，朝不同方向水平散開，各自繞行 0.65～1.55 秒，再錯開時機尋敵、沿弧線俯衝。目標倒下時平滑改鎖範圍內敵人。碰敵或牆後爆炸，基礎 10／10／12／14／16 枚，爆炸半徑 48，每枚各命中一次。數量卡 ×1.25，最多 60 枚；修羅道倒下不能起手，已離架飛彈可飛完。',source_url:painSource
    }],
    ['naruto-pain-absorb',[30010],{
      name:'餓鬼道・封術吸印',mode:'pain-absorb',icon:'painAbsorb',type:'psychic',learnLevel:6,
      passive:true,cd:0,dmg:0,absorbCooldown:2.5,
      ups:[2.3,2.1,1.9,1.7].map(value=>({t:`吸收恢復週期 ${value} 秒`,m:{absorbCooldown:value}})),
      desc:'學會即自動守衛，不占主動槽。餓鬼道在天道 300 內時，一次吸收雙掌半徑 36 內全部合格忍術彈，牆會阻擋；恢復 2.5／2.3／2.1／1.9／1.7 秒，受冷卻卡影響。物理忍具、雷射、地面技不吸收，沒有額外無敵或回血。',source_url:'https://naruto-official.com/en/anime/naruto2/list/01_609'
    }],
    ['naruto-pain-summon',[30010],{
      name:'畜生道・通靈衝陣',mode:'pain-summon',icon:'painSummon',type:'ground',learnLevel:9,passive:true,
      cd:6,dmg:90,range:300,width:90,speed:500,ups:painUps(),
      desc:'學會後畜生道自動伏手召出犀牛，沿起手方向衝 300、通道寬 90，每敵人只受傷一次。最多一隻，不吃數量卡；遇牆停止。畜生道倒下不能施放，不用切招。',source_url:painSource
    }],
    ['naruto-pain-soul',[30010],{
      name:'人間道・魂魄牽引',mode:'pain-soul',icon:'painSoul',type:'psychic',learnLevel:12,passive:true,
      cd:5,dmg:140,range:180,fieldDuration:.6,ups:painUps(),
      desc:'學會後人間道瞬移至 180 內目標身邊的安全落點，抓取 0.6 秒後單次傷害，抓住才開始冷卻。普通敵人減速 70%，特殊敵人 20%；越距、隔牆或人間道倒下即取消。無安全落點不施放，不穿牆、不即死。技能演出為本作改編。',source_url:painSource
    }],
    ['naruto-pain-repair',[30010],{
      name:'地獄道・閻王修復',mode:'pain-repair',icon:'painRepair',type:'psychic',learnLevel:12,
      passive:true,cd:0,dmg:0,repairCooldown:10,
      ups:[9.5,9,8.5,8].map(value=>({t:`修復等待週期 ${value} 秒`,m:{repairCooldown:value}})),
      desc:'學會即常駐，不占主動槽。五具支援道最大生命皆為天道的 2 倍，隨本體生命成長同步。有其他支援道倒下才等待 10／9.5／9／8.5／8 秒，再以 0.8 秒閻王演出修復一位，冷卻卡有效。天道倒下時優先救天道，半血復活並保護 2 秒，復活後 5 秒跑速翻倍；尚未學此招也能以第一階週期救天道。不能修復自己，不重複復歸、不刷新其他道生命或冷卻。危險位置延後復活，地獄道倒下則救援失敗。',source_url:painSource
    }],
    ['naruto-pain-planet',[30010],{
      name:'天道・地爆天星',mode:'pain-planet',icon:'painPlanet',type:'psychic',learnLevel:15,passive:true,
      cd:18,dmg:240,pulseDamage:30,normalImpactHealthRatio:.3,range:640,radius:640,impactRadius:960,visualScale:1.5,fieldDuration:1.5,ups:painUps(),
      desc:'黑核吸起岩石凝成月球，再整顆下墜砸地。牽引半徑 640，1.5 秒內每 0.5 秒傷害一次共三次，前置傷害另算；撞地震波在 0.6 秒內向外擴散至半徑 960，各命中一次。小怪落地傷害固定為最大生命 30%＋施放時攻擊力，不受暴擊、屬性或天氣倍率影響；首領維持原傷害，第一階全中基傷 330。基礎冷卻 18 秒。特殊敵人牽引僅 25%，不硬定身。最多一顆，施放後家族引斥技至少恢復 5 秒。',source_url:painSource
    }]
  );
  extra.push(
    ['naruto-temari-three-stars',[30011],{
      name:'三星扇精通',mode:'temari-mastery',icon:'temariMastery',type:'flying',passive:true,learnLevel:3,cd:0,dmg:0,
      masterySpeed:1.15,masteryReach:40,empowerMultiplier:1.15,deflectBase:1,
      ups:[1,2,3,4].map(i=>({t:`普攻總斬擊 ${i+2}＋數量・大鐮鼬推距 +${18*(i+1)}・速度 ×${[1.15,1.25,1.4,1.6,1.85][i]}・射程 +${[40,70,110,160,220][i]}`,
        m:{masterySpeed:[1.15,1.25,1.4,1.6,1.85][i],masteryReach:[40,70,110,160,220][i],empowerMultiplier:[1.15,1.2,1.25,1.3,1.35][i],deflectBase:[1,1,2,2,3][i]}})),
      desc:'常駐被動，不占主動槽。普攻每波總斬擊＝1＋精通等級＋數量卡；大鐮鼬仍只重擊一次，精通改加推距18／36／54／72／90。風浪速度×1.15／1.25／1.4／1.6／1.85、射程+40／70／110／160／220。每第三輪普攻傷害×1.15／1.20／1.25／1.30／1.35；前方短暫掃開實體飛彈，額度floor([1,1,2,2,3]×1.25^數量卡)。本作改編。',source_url:temariSource
    }],
    ['naruto-temari-great-scythe',[30011],{
      name:'風遁・大鐮鼬之術',mode:'temari-great-scythe',icon:'temariScythe',type:'flying',learnLevel:6,cd:5,dmg:56,
      count:1,range:300,speed:720,radius:160,width:90,arc:Math.PI*110/180,knock:0,
      ups:temariDamageUps([56,67.2,80.64,100.8,126],[300,330,360,390,420]).map((up,i)=>({...up,
        t:up.t+`・扇角${[120,130,140,150][i]}°・推距${[145,170,195,220][i]}`})),
      desc:'主動解圍技，冷卻5秒。一次強力揮扇，每敵只受一次重擊56／67.2／80.64／100.8／126，並在0.35秒內將普通怪群推遠。升階增加傷害、範圍與推距；數量卡擴大扇角／射程，精通強化速度／射程／推距。此招不連切、不因數量重複傷害；遇牆停止，特殊敵人只受傷不搬動。本作改編。',source_url:temariSource
    }],
    ['naruto-temari-blade-dance',[30011],{
      name:'通靈・斬斬舞',mode:'temari-blade-dance',icon:'temariSummon',type:'flying',passive:true,learnLevel:9,cd:10,dmg:25.6,
      count:1,range:360,speed:480,radius:65,slashCount:4,
      ups:temariDamageUps([25.6,31.2,37.6,45.6,55.2]).map((up,i)=>({...up,m:{...up.m,slashCount:[4,4,5,5,6][i+1]}})),
      desc:'常駐被動，不占主動欄。學會後floor(1.25^數量卡)隻鐮多利在附近自主遊走、停留，走遠會自行回到附近。自動接敵、斬擊後繼續閒逛，每隻獨立冷卻10秒。基礎斬擊4／4／5／5／6次；精通另加精通等級＋數量卡。每斬間隔0.12秒，傷害25.6／31.2／37.6／45.6／55.2，不分攤傷害；敵人可離開範圍。',source_url:temariSource
    }],
    ['naruto-temari-typhoon',[30011],{
      name:'風遁・颱風迴旋',mode:'temari-typhoon',icon:'temariTyphoon',type:'flying',learnLevel:12,cd:8,dmg:24,
      count:1,range:240,radius:240,pulseCount:3,sweepDuration:1.2,orbitDuration:1.2,
      ups:temariDamageUps([24,28.8,35.2,43.2,52.8],[240,270,300,330,360]).map((up,i)=>({...up,
        t:`每次傷害 ${[28.8,35.2,43.2,52.8][i]}・半徑 ${[270,300,330,360][i]}・基礎切割 ${[4,5,6,8][i]} 次`,
        m:{...up.m,radius:[270/240,300/270,330/300,360/330][i],pulseCount:[4,5,6,8][i]}})),
      desc:'選中後每 8 秒以起手位置為風眼，揮出 floor(1.25^數量卡) 道風流，各掃滿 360°。掃到的普通敵人沿真實弧線繞風眼一圈，最後掃到者也繞完整一圈；遇牆中止，強敵不搬動。每股對各目標基礎切割 3／4／5／6／8 次，精通另加技能階＋數量卡，每次基傷 24／28.8／35.2／43.2／52.8。半徑 240／270／300／330／360，不同風流與分身各自傷害；同敵不重設位移。本作改編。',
      source_url:'https://naruto-official.com/en/news/01_1602'
    }],
    ['naruto-temari-reflect',[30011],{
      name:'風遁・返風壁',mode:'temari-reflect',icon:'temariReflect',type:'flying',passive:true,learnLevel:15,cd:0,dmg:0,
      radius:85,reflectMultiplier:0.8,
      ups:[1,2,3,4].map(i=>({t:`半徑 ${[85,95,110,125,140][i]}・反射倍率 ${[0.8,0.96,1.12,1.36,1.6][i]}`,
        m:{radius:[95/85,110/95,125/110,140/125][i-1],reflectMultiplier:[0.8,0.96,1.12,1.36,1.6][i]}})),
      desc:'常駐被動，不占主動欄。持續以360度返風壁擋下並反射範圍內的敵方飛彈、首領特殊彈、光束與遠程落點攻擊，無開盾冷卻。每次反打floor(1.25^數量卡)道攻擊；每道為原攻擊傷害×反射倍率×攻擊力。倍率0.8／0.96／1.12／1.36／1.6，半徑85／95／110／125／140。近戰與環境傷害照常。本作改編。',
      source_url:temariSource
    }]
  );
  Object.assign(kinds,{'temari-wind':'cone','temari-mastery':'buff','temari-great-scythe':'cone','temari-blade-dance':'dash','temari-typhoon':'meteor','temari-reflect':'buff'});
  Object.assign(kinds,{'pain-basic':'projectile','pain-gravity':'aura','pain-missiles':'projectile','pain-summon':'dash','pain-soul':'melee','pain-absorb':'buff','pain-repair':'buff','pain-planet':'meteor'});
  kinds['gaara-sand-guard'] = 'buff';
  Object.assign(kinds,{'tenten-kunai':'projectile','tenten-fuma':'projectile','tenten-mastery':'buff','tenten-bounce':'buff','tenten-guard':'buff','tenten-tags':'meteor','tenten-twin':'projectile'});
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
      digiMode: design.mode, digiVis: design.vis || {}, maxLvl: design.mode==='shadow-clones'?clones.counts.length:5,
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
    references.set(dex, { name: english, source_url: dex===30011?temariSource:dex===30009?tentenSource:`https://naruto-official.com/en/news/${article}` });
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
    return signature ? [signature.id, ...(extraPools.get(mon.dex) || [])] : [];
  };
  G.NarutoSkillCatalog = { definitions, byDex, references, extraPools };

  const nameSharingan = move => {
    if(move.id==='naruto-sharingan')move.name='寫輪眼・'+G.NarutoSharingan.config.stageNames[Math.max(0,Math.min(4,move.lvl-1))];
    if(move.id==='naruto-gates')move.name='八門遁甲・'+G.NarutoGates.config.stageNames[Math.max(0,Math.min(4,move.lvl-1))];
    return move;
  };
  const instance=G.Moves.instance,levelUp=G.Moves.levelUp;
  G.Moves.instance=(id,...args)=>nameSharingan(instance(id==='naruto-sand-guard'?'naruto-sand-shield':id,...args));
  G.Moves.levelUp=move=>{const changed=levelUp(move);if(changed)nameSharingan(move);return changed;};

  const guide = document.createElement('section');
  guide.id = 'scr-naruto-skills';
  guide.className = 'scr dim hidden';
  guide.translate = false;
  guide.innerHTML = '<div class="box"><div class="naruto-skill-heading"><h2>忍術圖鑑與來源</h2><button class="btn small ghost" id="naruto-skills-close">返回</button></div><p class="sub">角色與忍術參考官方動畫、角色資料與遊戲說明；傷害、冷卻、範圍、回復與自動連段皆為本跨界版改編，也包含角色後期能力。中文採常見譯名。鳴人 Lv.9 可學九尾查克拉外衣；佐助 Lv.1 可學草薙劍環繞、Lv.9 可學風魔手裏劍。草薙劍僅在選用並施放後環繞，切換別招立即消失。僅開放各角色的特色忍術。特色技能達學習等級時會優先出現一次；略過後仍可隨機抽到；角色招式池互不混用。控制、輔助與直線貫穿不等同全周範圍傷害。</p><div class="naruto-skill-entries"></div></div>';
  function activationLabel(move) {
    if (['naruto-gaara','naruto-tenten','naruto-pain','naruto-temari'].includes(move.id)) return '常駐普攻 · 不用選招 · 不占主動槽';
    if (move.passive) return '常駐被動 · 學會即生效 · 不占主動槽';
    if (['naruto-kusanagi', 'naruto-sand-prison'].includes(move.id)) return '主動 · 需保持選中';
    if (['naruto-shadow-clones', 'naruto-nine-tails-cloak'].includes(move.id)) return '主動 · 選中施放 · 切招後保留至到期';
    return '主動 · 選中後自動施放';
  }
  for (const [dex, definition] of byDex) {
    if(!G.Naruto.availableDexes.includes(dex))continue;
    const record = G.Naruto.records.get(dex), reference = references.get(dex);
    const item = document.createElement('article');
    item.className = 'naruto-skill-entry';
    const title = document.createElement('h3');
    title.textContent = `${record.chinese || record.name} · ${definition.name}`;
    const description = document.createElement('p');
    description.textContent = definition.desc;
    const stats = document.createElement('small');
    stats.textContent = `${activationLabel(definition)} · 冷卻 ${definition.cd} 秒 · 可升至 Lv.5`;
    const source = document.createElement('a');
    source.href = reference.source_url;
    source.target = '_blank';
    source.rel = 'noopener noreferrer';
    source.textContent = dex===30009?'官方動畫參考 · 忍具機制為本作改編':`官方參考 · ${reference.name}`;
    item.append(title, description, stats, source);
    for (const id of extraPools.get(dex) || []) {
      const move = definitions.get(id);
      const heading = document.createElement('h4');
      heading.textContent = `可學忍術 · ${move.name}`;
      const detail = document.createElement('p');
      detail.textContent = move.desc;
      const extraStats = document.createElement('small');
      extraStats.textContent = `Lv.${move.learnLevel||1} 可學 · ${activationLabel(move)} · 冷卻 ${move.cd} 秒 · 可升至 Lv.5`;
      const link = document.createElement('a');
      link.href = move.owner_sources?.[dex] || move.source_url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = dex===30009 ? '官方動畫參考 · 招式與數值依本作改編' : move.id==='naruto-sand-shield' ? '官方砂術參考 · 護盾與護衛機制為本作改編' : `官方招式來源 · ${move.name}`;
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
