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
      mode: 'shadow-clones', type: 'fighting', cd: clones.cooldown, dmg: clones.punchDamage, range: 240,
      cloneDuration: clones.duration, punchCd: clones.punchCooldown, vis: { pal: 'naruto-blue' },
      desc:`需選中才會召喚，切招後既有分身保留至到期。結印 ${clones.sealDuration} 秒後召喚基礎 ${clones.counts.join('／')} 隻分身，持續 ${clones.duration} 秒；數量卡每張使分身數 ×1.25，累乘後取整。分身模仿螺旋丸、螺旋手裏劍與忍具，各自造成完整傷害；受擊消散。`,
      ups: clones.counts.slice(1).map(count=>({t:`分身基礎數量 → ${count} 隻；每隻完整傷害`,m:{}}))
    }],
    [30002, 'sasuke', '千鳥', 'Chidori', '01_1296', {
      mode: 'chidori-chain', type: 'electric', cd: 1.05, dmg: 44, charge: .09,
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
      mode: 'melee', type: 'fighting', cd: 2, dmg: 37,
      range: 72.5, radius: 62, arc: 3.9, knock: 95,
      vis: { melee: 'claw', proj: 'wind', pal: 'grass' },
      desc:'旋身大角度橫掃，踢開近身與側面敵人。'
    }],
    [30007, 'gaara', '砂時雨', 'Sand Shower (game adaptation)', '01_1695', {
      mode: 'gaara-sand-burst', passive: true, type: 'ground', cd: 1.2, dmg: 28,
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
      name: '螺旋丸', mode: 'dash', type: 'fighting', cd: 1.25, dmg: 48, charge: .12,
      range: 125, radius: 125, width: 56, knock: 100,
      vis: { proj: 'wind', melee: 'impact', pal: 'naruto-blue' },
      desc:'向前突進攻擊；選用時，現存影分身各自接近敵人並施放完整傷害的螺旋丸。',
      source_url: 'https://naruto-official.com/en/news/01_1423'
    }],
    ['naruto-rasenshuriken', [30001], {
      name: '風遁・螺旋手裏劍', mode: 'shot', type: 'flying', cd: 2.5, dmg: 58,
      speed: 350, life: 1.3, size: 15, range: 455, blastRadius: 110, knock: 65,
      vis: { proj: 'naruto-wind-shuriken', trail: 'wind', pal: 'naruto-blue' },
      desc:'投擲旋轉手裏劍，命中後爆發風刃，傷害周圍敵人。',
      source_url: 'https://naruto-official.com/en/news/01_1423'
    }],
    ['naruto-nine-tails-cloak', [30001], {
      name:'九尾查克拉外衣', mode:'nine-tails-cloak', type:'fighting', cd:18, dmg:0, learnLevel:9,
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
      name: '火遁・豪火球之術', mode: 'shot', type: 'fire', cd: 2.3, dmg: 49,
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
      name:'表蓮華', mode:'lee-lotus', type:'fighting', learnLevel:3, cd:5, dmg:110,
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
      name:'八門遁甲・開門', mode:'gates-passive', passive:true, type:'fighting', learnLevel:6, cd:0, dmg:0,
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
      name:'裏蓮華', mode:'lee-reverse-lotus', type:'fighting', learnLevel:9, cd:5, dmg:210,
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
      name:'砂縛柩・砂瀑送葬', mode:'gaara-coffin', type:'ground', learnLevel:3, cd:5, dmg:110,
      range:280, count:1, fieldDuration:1.1, slow:.95, bossSlow:.3,
      ups:[{t:'傷害 +20%',m:{dmg:1.2}},{t:'索敵距離提高至 310',m:{range:310}},
        {t:'傷害 +25%',m:{dmg:1.25}},{t:'傷害 +25%・索敵距離 340',m:{dmg:1.25,range:340}}],
      vis:{pal:'naruto-sand'}, desc:'優先鎖定可見精英或首領，基礎束縛數量＝1＋角色等級，最多 10 名；數量卡每張使目標數 ×1.25，累乘取整後最多 30 名。束縛 1.1 秒後每名壓縮一次，單體基礎傷害＝當階傷害（110／132／132／165／206.25）＋角色等級，每級 +1，不造成起手傷害；首領僅減速 30%。基礎冷卻 5 秒，冷卻期間自動砂彈普攻。',
      source_url:'https://naruto-official.com/en/news/01_1555'
    }],
    ['naruto-sand-shield', [30007], {
      name:'砂之盾', mode:'gaara-shield', passive:true, type:'ground', learnLevel:1, cd:12, dmg:0,
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
      name:'流砂瀑流・砂瀑大葬', mode:'gaara-tsunami', type:'ground', learnLevel:9, cd:8, dmg:240,
      range:310, radius:310, width:240, knock:0, waveDuration:.65, bindDuration:.5,
      ups:[{t:'傷害 +20%',m:{dmg:1.2}},{t:'距離 345・寬 270',m:{range:345,radius:345/310,width:270/240}},
        {t:'傷害 +25%',m:{dmg:1.25}},{t:'傷害 +25%・距離 380・寬 300',m:{dmg:1.25,range:380,radius:380/345,width:300/270}}],
      vis:{pal:'naruto-sand'}, desc:'砂浪推進造成 25% 傷害，完整束縛 0.5 秒後下壓大葬造成 75%；離開砂地不受大葬，晚進場不補傷。普通敵人減速 95%、首領 35%。基礎冷卻 8 秒，冷卻卡有效，冷卻期間自動砂彈普攻。',
      source_url:'https://naruto-official.com/en/news/01_1695'
    }],
    ['naruto-sand-prison', [30007], {
      name:'流砂牢', mode:'gaara-sand-prison', type:'ground', learnLevel:12,
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
      name:'草薙劍・環繞', mode:'kusanagi-orbit', type:'steel', learnLevel:1,
      cd:1,dmg:28,radius:58,count:1,knock:8,
      desc:'選用並施放後，飛行劍持續環繞攻擊，切招即消失。同一敵人每 0.35 秒最多命中一次；數量卡每張使劍數 ×1.25，累乘取整後，三勾玉再額外加一把劍。',
      ups:[{t:'環繞劍 +1 把',m:{count:1}},
        {t:'劍刃傷害 +30%、環繞範圍 +10%',m:{dmg:1.3,radius:1.1}},
        {t:'環繞劍再 +1 把',m:{count:1}},
        {t:'劍刃傷害 +35%、環繞範圍 +10%',m:{dmg:1.35,radius:1.1}}],
      source_url:'https://naruto-official.com/en/news/01_1710'
    }],
    ['naruto-fuma-shuriken', [30002], {
      name:'風魔手裏劍', mode:'shot', type:'steel', learnLevel:9,
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
      desc:'常駐被動，不占主動槽。每枚忍具額外連彈次數＝技能等級＋數量卡張數，不設上限；首擊另計。命中後飛向 160 範圍內尚未被這枚忍具打過的小怪，雙昇龍另可連彈至 Boss；牆壁會擋下，其他忍具不選首領，精英或傳說敵人不列入一般連彈目標。苦無、迴刃與雙昇龍每次命中維持原傷害；附札苦無彈到最後落點才引爆。',source_url:tentenSource
    }],
    ['naruto-tenten-fuma',[30009],{
      name:'風魔迴刃',mode:'tenten-fuma',icon:'tentenFuma',type:'steel',learnLevel:3,
      cd:3.2,dmg:12,count:2,range:260,speed:390,size:12,pierce:3,
      ups:[{t:'每程單枚傷害 +20%',m:{dmg:1.2}},{t:'飛行距離 380',m:{range:380}},
        {t:'飛行距離 500・傷害 +20%',m:{range:500,dmg:1.2}},{t:'每程單枚傷害 +25%',m:{dmg:1.25}}],
      desc:'兩枚大型四刃手裏劍沿弧線飛出再返回。去、回每程每敵人最多命中一次，每枚對單一目標最多兩次，牆壁會擋下。每程單枚傷害 12／14.4／14.4／17.28／21.6，飛行距離 260／260／380／500／500。數量卡使枚數 ×1.25，累乘取整；每張穿透 +1。選中後自動施放，切招保留已發射忍具。命中後成功回收獲得 6 秒蓄勢，下一次主動整輪傷害 +30%，不疊加；普攻不消耗。可穿過落地爆符提前引爆。招式路線與數值為本作改編。',source_url:tentenSource
    }],
    ['naruto-tenten-mastery',[30009],{
      name:'忍具精通',mode:'tenten-mastery',icon:'tentenMastery',passive:true,type:'steel',learnLevel:6,
      cd:0,dmg:0,pierceBonus:2,speedMul:1.1,
      ups:[{t:'苦無額外穿透 +3・忍具速度 +20%・飛行與索敵距離 +200',m:{pierceBonus:3,speedMul:1.2}},{t:'苦無額外穿透 +4・忍具速度 +40%・飛行與索敵距離 +300',m:{pierceBonus:4,speedMul:1.4}},
        {t:'苦無額外穿透 +5・忍具速度 +80%・飛行與索敵距離 +400',m:{pierceBonus:5,speedMul:1.8}},{t:'苦無額外穿透 +6・忍具速度 +100%・飛行與索敵距離 +500',m:{pierceBonus:6,speedMul:2}}],
      desc:'常駐被動，學會即生效、不占主動槽。苦無額外穿透 +2／3／4／5／6，忍具飛行速度 +10／20／40／80／100%。所有忍具飛行、索敵與每跳連彈距離各 +100／200／300／400／500。不增加同一枚忍具對 Boss 的重複命中。分身完整繼承技能等級，傷害只套用一次 1/3。被動機制為本作改編。',source_url:tentenSource
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
      desc:'兩張卷軸繞身螺旋升空，放卷 0.12 秒後從卷軸分四批射出八種忍具，形成約 110° 前方扇面。基礎 24／28／32／36／40 枚，單枚傷害 8／8／9.6／9.6／12，射程 680，基礎穿透 1 次。整輪發射約 0.6 秒，數量卡使枚數 ×1.25，累乘取整，每張另加穿透 1 次。學會忍具連彈後可彈向 160 範圍內其他小怪或 Boss，同一枚不重複命中同一目標。可走位、沒有額外無敵。回收蓄勢可強化整輪傷害 +30%；忍具可提前引爆自己的落地爆符。螺旋紙卷與尾跡不造成傷害。',source_url:tentenSource
    }]
  );
  kinds['gaara-sand-guard'] = 'buff';
  Object.assign(kinds,{'tenten-kunai':'projectile','tenten-fuma':'projectile','tenten-mastery':'buff','tenten-bounce':'buff','tenten-tags':'meteor','tenten-twin':'projectile'});
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
    references.set(dex, { name: english, source_url: dex===30009?tentenSource:`https://naruto-official.com/en/news/${article}` });
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
    if (['naruto-gaara','naruto-tenten'].includes(move.id)) return '常駐普攻 · 不用選招 · 不占主動槽';
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
