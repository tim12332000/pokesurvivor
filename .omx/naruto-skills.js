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
      desc: `各級分身數量：${clones.counts.join('、')} 隻；結印 ${clones.sealDuration} 秒後化煙出現，存在 ${clones.duration} 秒、冷卻 ${clones.cooldown} 秒。切換到已學的螺旋丸、螺旋手裏劍或忍具時，每隻分身都使用完整招式傷害，不分攤、不設定總傷害上限。受擊後化煙消散，不會再召出分身。數量與數值為本作改編。`,
      ups: clones.counts.slice(1).map(count=>({t:`影分身數量增加 → ${count} 隻；每隻完整傷害`,m:{}}))
    }],
    [30002, 'sasuke', '千鳥', 'Chidori', '01_1296', {
      mode: 'chidori-chain', type: 'electric', cd: 1.05, dmg: 44, charge: .09,
      minCooldown: G.NarutoChidori.config.minCooldown,
      range: 170, radius: 170, width: 34, knock: 50,
      vis: { proj: 'bolt', melee: 'claw', pal: 'naruto-blue' },
      desc: `千鳥 Lv.1～5 基礎追擊上限為 ${G.NarutoChidori.config.counts.join('、')} 次，數量增幅每層再增加 1 次。同一目標可以隔次重複追擊，例如 A→B→A，但不能連續命中同一人。發動時固定鏡頭，目標限制於該畫面與邊界外少量緩衝範圍；沒有其他合格目標或連段結束時快速返回發動原位，回程不額外攻擊。每輪第一擊維持原傷，之後每次命中讓下一擊傷害再乘 1.05，不設增傷上限，重新施放時重置。命中後自動追擊下一人，後續搜尋與突進距離擴大三倍，仍受畫面邊界限制。同一輪連招越往後突進越快、轉向間隔越短，速度最多達初始的 3 倍；下一輪重新由原速開始。突進可穿過牆壁與障礙物，去回程飛行期間無敵，回到原位後再保護 0.3 秒；結印與轉向間隔仍可受傷。實際冷卻與回到原位後的再次施放間隔至少 ${G.NarutoChidori.config.minCooldown} 秒，冷卻加成不會突破下限。追擊次數以施放時的技能等級與數量增幅為準，此連擊為本作改編。`,
      ups: G.NarutoChidori.config.counts.slice(1).map((count,index)=>({
        t: `追擊上限 → ${count} 名；${['傷害 +20%','冷卻 -10%','攻擊範圍 +12%','傷害 +25%'][index]}`,
        m: [{dmg:1.2},{cd:.9},{radius:1.12,width:1.12,life:1.12,range:170*1.12},{dmg:1.25}][index]
      }))
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
      desc: '凝聚旋轉查克拉後向前突進。鳴人 Lv.3 起保證出現學習選項；選用此招時，現存影分身會各自接近敵人並使用完整傷害的螺旋丸，沒有總模仿傷害上限。',
      source_url: 'https://naruto-official.com/en/news/01_1423'
    }],
    ['naruto-rasenshuriken', [30001], {
      name: '風遁・螺旋手裏劍', mode: 'shot', type: 'flying', cd: 2.5, dmg: 58,
      speed: 350, life: 1.3, size: 15, range: 455, blastRadius: 110, knock: 65,
      vis: { proj: 'naruto-wind-shuriken', trail: 'wind', pal: 'naruto-blue' },
      desc: '投出四刃旋轉查克拉手裏劍，命中後爆發風刃並傷害周圍敵人。此為鳴人後期習得的忍術，本跨界版可學；不代表少年造型在原作當時已會使用。爆發半徑、傷害與冷卻為遊戲改編。',
      source_url: 'https://naruto-official.com/en/news/01_1423'
    }],
    ['naruto-nine-tails-cloak', [30001], {
      name:'九尾查克拉外衣', mode:'nine-tails-cloak', type:'fighting', cd:18, dmg:0, learnLevel:9,
      fieldDuration:8, atkMul:1.5, speedMul:1.25, damageTakenMul:.75,
      radius:76, pulseDamage:12, pulseInterval:.65, knock:18,
      vis:{pal:'naruto-red'},
      desc:'鳴人 Lv.9 可學。紅色一尾外衣持續 8 秒：攻擊 +50%、移速 +25%、一般傷害 -25%，每 0.65 秒反擊近身敵人。切換招式後仍有效，不能疊加。數值與範圍為本作改編。',
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
      desc: '從嘴前吐出小火團，越往外飛越大，飛行 300 距離後達最大尺寸；外觀與碰撞範圍同步成長。初次接觸立即造成一次範圍傷害，同一敵人之後每 0.2 秒最多一次，碰到敵人繼續飛；碰到牆或實體障礙物則停在前方燃燒，仍於火球發射後 1.4 秒消散。每顆獨立計算每秒 49 基礎傷害，不會永久殘留。持續傷害、成長與時限為本作改編。',
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
      name:'寫輪眼・進化', mode:'sharingan-evolution', passive:true, type:'psychic', cd:0, dmg:0,
      range:320,
      vis:{pal:'naruto-red'},
      desc:'學會後被動生效，不必切到此技能。Lv.1 一勾玉：閃避 +5%、寶石拾取範圍 +20%；Lv.2 二勾玉：閃避成功向四周投出 3 枚看破手裏劍，反擊傷害 +35%；Lv.3 三勾玉：紅色殘影、遠程彈道 +1；Lv.4 天照：牽引渦流收束後留下本局不熄的黑炎，每秒造成最大生命 2% 傷害（首領 0.5%）；Lv.5 須佐能乎：紫色護體減傷 30%，並自動範圍斬擊。各階段效果累加；數量增幅增加反擊彈數。牽引黑洞與進化階段為本作改編，並非佐助的神威。',
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
      name:'表蓮華', mode:'lee-lotus', type:'fighting', learnLevel:3, cd:3, dmg:70,
      range:145, radius:60,
      vis:{pal:'grass'}, desc:'小李 Lv.3 解鎖。踏入近身、上踢挑空，再旋身摔落。首領保持接地；落地小範圍震擊為本作改編。',
      source_url:'https://naruto-official.com/en/news/01_1652'
    }],
    ['naruto-gates', [30006], {
      name:'八門遁甲・開門', mode:'gates-passive', passive:true, type:'fighting', learnLevel:6, cd:0, dmg:0,
      vis:{pal:'grass'},
      desc:'小李 Lv.6 解鎖。學會即持續生效，不佔主動技能欄。N 為技能等級，LV 為角色等級：回血量與跑速皆增加 (10×N＋LV)%。例如 N=1、LV=6 時 +16%；N=5、LV=30 時 +80%。只增幅既有回血來源，不額外產生回血。五階攻擊加成依序 +30%、+35%、+40%、+45%、+50%。開門起切換紅膚、白眼、豎髮形態；移動與突進留下紅色殘影，門數越高，殘影越大、拖尾越長；生門起氣焰增強。前兩門形態與五階常駐效果為本作改編，沒有倒數或結束疲勞。',
      ups:[
        {t:'第二門・休門：攻擊 +35%；回血量、跑速增加 (20＋角色等級)%',m:{}},
        {t:'第三門・生門：攻擊 +40%；回血量、跑速增加 (30＋角色等級)%，氣焰增強',m:{}},
        {t:'第四門・傷門：攻擊 +45%；回血量、跑速增加 (40＋角色等級)%',m:{}},
        {t:'第五門・杜門：攻擊 +50%；回血量、跑速增加 (50＋角色等級)%',m:{}}
      ],
      source_url:'https://naruto-official.com/en/news/01_1652'
    }],
    ['naruto-reverse-lotus', [30006], {
      name:'裏蓮華', mode:'lee-reverse-lotus', type:'fighting', learnLevel:9, cd:5, dmg:145,
      range:180, radius:64,
      vis:{pal:'grass'}, desc:'小李 Lv.9 解鎖。近身上踢後五段高速體術連擊，最後重摔；首領不浮空。可獨立施放，開門期間享攻擊加成；獨立施放、數值與落地範圍為本作改編。',
      source_url:'https://naruto-official.com/en/anime/naruto1/list/01_273'
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
    }],
    ['naruto-kusanagi', [30002], {
      name:'草薙劍・環繞', mode:'kusanagi-orbit', type:'steel', learnLevel:1,
      cd:1,dmg:28,radius:58,count:1,knock:8,
      desc:'佐助 Lv.1 即可學。選用此技能並施放後，飛行劍持續環繞；切換其他招式立即消失並停止傷害，切回後需再次施放。學會本身不會啟動。可同時斬中多名敵人，同一目標每 0.35 秒最多命中一次。數量增幅每層、三勾玉寫輪眼彈道加成都各多一把劍。自動環繞為本版改編。',
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
      desc:'佐助 Lv.9 可學。大型旋轉鋼刃先繞大弧線擊中投出時鎖定的位置，再弧形返回佐助；去、回各最多命中 4 名敵人，每名每程一次。數量增幅增加枚數與穿透，多枚交錯繞向同目標，各枚完整傷害；牆壁仍會擋下。軌跡為本作改編。',
      ups:[{t:'手裏劍 +1 枚、穿透 +1',m:{count:1,pierce:1}},
        {t:'手裏劍傷害 +20%',m:{dmg:1.2}},
        {t:'冷卻 -15%',m:{cd:.85}},
        {t:'手裏劍 +1 枚、傷害 +25%',m:{count:1,dmg:1.25}}],
      source_url:'https://tamashiiweb.com/item/14256/?wovn=en'
    }]
  );
  const kinds = { 'chidori-chain': 'dash', dash: 'dash', melee: 'melee', slam: 'melee', beam: 'beam', shot: 'projectile', aura: 'aura', nova: 'nova', 'sand-wave': 'cone', 'shadow-clones': 'buff',
    sharingan:'buff', 'sharingan-evolution':'buff', 'medical-heal':'buff', regeneration:'buff', 'earth-wall':'buff', byakugan:'buff', gates:'buff', 'gates-passive':'buff', 'sand-shield':'buff', 'nine-tails-cloak':'buff',
    'lee-lotus':'melee', 'lee-reverse-lotus':'melee', lotus:'melee', 'sand-coffin':'meteor', 'single-illusion':'meteor', 'black-flames':'meteor', 'kusanagi-orbit':'orbit' };
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
    return signature ? [signature.id, ...(extraPools.get(mon.dex) || [])] : [];
  };
  G.NarutoSkillCatalog = { definitions, byDex, references, extraPools };

  const nameSharingan = move => {
    if(move.id==='naruto-sharingan')move.name='寫輪眼・'+G.NarutoSharingan.config.stageNames[Math.max(0,Math.min(4,move.lvl-1))];
    if(move.id==='naruto-gates')move.name='八門遁甲・'+G.NarutoGates.config.stageNames[Math.max(0,Math.min(4,move.lvl-1))];
    return move;
  };
  const instance=G.Moves.instance,levelUp=G.Moves.levelUp;
  G.Moves.instance=(...args)=>nameSharingan(instance(...args));
  G.Moves.levelUp=move=>{const changed=levelUp(move);if(changed)nameSharingan(move);return changed;};

  const guide = document.createElement('section');
  guide.id = 'scr-naruto-skills';
  guide.className = 'scr dim hidden';
  guide.translate = false;
  guide.innerHTML = '<div class="box"><div class="naruto-skill-heading"><h2>忍術圖鑑與來源</h2><button class="btn small ghost" id="naruto-skills-close">返回</button></div><p class="sub">角色與忍術參考官方動畫、角色資料與遊戲說明；傷害、冷卻、範圍、回復與自動連段皆為本跨界版改編，也包含角色後期能力。中文採常見譯名。鳴人 Lv.9 可學九尾查克拉外衣；佐助 Lv.1 可學草薙劍環繞、Lv.9 可學風魔手裏劍。草薙劍僅在選用並施放後環繞，切換別招立即消失。僅開放各角色的特色忍術。Lv.3、Lv.6 起保證出現特色技能選項；角色招式池互不混用。控制、輔助與直線貫穿不等同全周範圍傷害。</p><div class="naruto-skill-entries"></div></div>';
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
    stats.textContent = definition.passive ? '學會即生效 · 五階段進化' : `冷卻 ${definition.cd} 秒 · ${definition.dmg ? '基礎傷害 '+definition.dmg : '輔助技能'} · 可升至 Lv.5`;
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
      extraStats.textContent = move.passive ? '學會即生效 · 五階段進化' : `冷卻 ${move.cd} 秒 · ${move.dmg ? '基礎傷害 '+move.dmg : '輔助技能'}${move.blastRadius ? ' · 爆發半徑 '+move.blastRadius : ''} · 可升至 Lv.5`;
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
