/* Final design-preview data only. Never loaded by the normal game entry. */
(() => {
  'use strict';
  const phase = (start, end, label, pose) => ({ start, end, label, pose });
  const strike = (t, share, kind = 'hit') => ({ t, share, kind });
  const skill = (id, name, unlock, damage, cd, duration, description, feel, extra) =>
    ({ id, name, unlock, damage, cd, duration, description, feel, ...extra });
  const skills = [
    skill('willow', '柳之舞', 1, [30,36,42,51,60], .9, .64,
      '常駐近身骨刃；四連逐漸加速，數量卡最多八連。', '短斬連接交叉回斬，最後一擊更俐落。', {
        kind:'melee', passiveAttack:true, quantityMode:'hits', baseCount:4, maxCount:8,
        radius:[72,72,80,80,88], angleDegrees:80, targetLimit:1, playerLock:[],
        hits:[], hitSchedule:'accelerating', hitStart:.12, hitEnd:.60, intervalRatio:.85,
        phases:[phase(0,.12,'沉肩展骨','prepare'),phase(.12,.60,'加速連斬','slash'),phase(.60,.64,'收刃回位','recover')],
        aiming:'每擊同步轉身重瞄最近合法敵人，原目標死亡可換下一名。',
        audio:'短骨刃擦切逐步加密，末擊略重。'
      }),
    skill('camellia', '椿之舞', 3, [120,144,168,204,240], 5, .74,
      '細骨劍三連刺，末刺占一半傷害；可邊退邊刺。', '兩次輕刺鋪陳，第三次腰背發力送劍。', {
        kind:'melee', quantityMode:'targets', baseCount:4, maxCount:12,
        length:[145,145,165,165,185], halfWidth:[20,20,24,24,28], playerLock:[],
        hits:[strike(.30,.25),strike(.43,.25),strike(.57,.50)],
        phases:[phase(0,.16,'骨劍成形','prepare'),phase(.16,.30,'第一刺','thrust'),phase(.30,.43,'第二刺','thrust'),phase(.43,.57,'重刺','thrust'),phase(.57,.74,'收劍','recover')],
        aiming:'起手與首刺前更新方向，首刺後固定方向；移動僅改變出手原點。',
        audio:'三次短刺由輕到重，末刺低頻加強。'
      }),
    skill('bullets', '十指穿彈', 3, [45,54,63,76.5,90], 2.4, .60,
      '指骨五拍連射；基礎五枚，數量卡最多十五枚，可正常走位。', '雙手交替彈指，骨鳴形成俐落射擊節奏。', {
        kind:'ranged', quantityMode:'projectiles', baseCount:5, maxCount:15,
        length:[260,260,280,280,300], projectileSpeed:600, targetLimit:3, playerLock:[],
        hits:[], releaseTimes:[.16,.23,.30,.37,.44], perProjectileShare:.20,
        phases:[phase(0,.12,'抬掌瞄準','prepare'),phase(.12,.16,'張開手指','shoot'),phase(.16,.44,'五拍連射','shoot'),phase(.44,.60,'收手回位','recover')],
        aiming:'逐彈輪流瞄最多三名最近合法目標；離手後直線飛行，命中首名敵人即消失。',
        audio:'五拍銳利骨鳴；同拍多枚用手指位置分離，不加槍火。'
      }),
    skill('larch', '唐松之舞', 6, [96,115.2,134.4,163.2,192], 6, .70,
      '胸肋與肩肘展骨，近身兩輪反掃並提供短防護。', '骨刺貼身張開，硬質展骨聲與第二輪推退表達解圍。', {
        kind:'melee', quantityMode:'none', radius:[78,78,88,88,98], playerLock:[],
        hits:[strike(.30,.50),strike(.52,.50)], guard:{start:.18,end:.88,reduction:.20}, normalPush:35,
        phases:[phase(0,.18,'縮身蓄骨','prepare'),phase(.18,.30,'骨刺展開','guard'),phase(.30,.52,'扭身反掃','guard'),phase(.52,.70,'縮骨回防','recover')],
        aiming:'以玩家當下腳底為圓心；第二輪只推退普通敵人，首領不位移。',
        audio:'短硬展骨聲；受擊僅在接觸側閃骨質亮點。'
      }),
    skill('vine', '鐵線花・蔓', 6, [48,57.6,67.2,81.6,96], 8, .70,
      '脊骨鞭鎖一名目標；普通怪短拉到接觸圈外的安全接斬位置。', '鞭節展開、接觸後繃直，讓拉近的重量看得見。', {
        kind:'melee', quantityMode:'none', length:[220,220,240,240,260], targetLimit:1,
        playerLock:[{start:.42,end:.62}], control:{start:.42,end:.62,kind:'pull',bossImmune:true,safeMargin:8},
        hits:[strike(.42,1)],
        phases:[phase(0,.20,'抽出脊骨鞭','prepare'),phase(.20,.42,'甩鞭接觸','whip'),phase(.42,.62,'繃緊短拉','pull'),phase(.62,.70,'鬆鞭回收','recover')],
        aiming:'單目標，無安全落點或視線不開招；首領可受傷但不搬動。',
        audio:'骨節輕碰後短促繃緊；沒有持續全鞭發光。'
      }),
    skill('flower', '鐵線花・花', 9, [192,230.4,268.8,326.4,384], 8, .86,
      '前臂長出層疊骨鑽，一次重刺；不用先學蔓也能施放。', '成鑽、壓身、刺入三拍分明，命中用局部硬停與碎骨。', {
        kind:'melee', quantityMode:'none', length:[135,135,150,150,165], halfWidth:[24,24,24,24,24],
        targetLimit:1, secondaryTargetLimit:3, secondaryShare:.5, playerLock:[{start:.46,end:.58}],
        hits:[strike(.58,1)], hitStop:.045,
        phases:[phase(0,.12,'收臂壓身','prepare'),phase(.12,.30,'骨片疊鑽','drillGrow'),phase(.30,.46,'對準蓄勢','drillGrow'),phase(.46,.58,'重刺接觸','drill'),phase(.58,.86,'抽鑽回位','recover')],
        aiming:'優先鑽線內可傷害首領／精英，再最近普通怪；.30秒最後修瞄，之後固定方向。',
        audio:'低沉鑽擊和向前碎骨；空招不播放假命中重音。'
      }),
    skill('bracken', '早蕨之舞', 12, [300,360,420,510,600], 12, 1.48,
      '固定圓心骨林三波拔地而起；同一敵人整次最多一次傷害。', '低骨先冒、高柱後拔，三波地裂逐層擴張。', {
        kind:'area', quantityMode:'none', radius:[180,180,210,210,240], playerLock:[{start:0,end:.30}],
        hits:[{...strike(.48,1,'wave'),radiusFraction:1/3},{...strike(.68,1,'wave'),radiusFraction:2/3},{...strike(.90,1,'wave'),radiusFraction:1}],
        castDedup:true, hitStop:.035, fixedCenter:true, bossDamage:true,
        phases:[phase(0,.30,'低身按地','plant'),phase(.30,.48,'裂地預告','plant'),phase(.48,.68,'內圈拔骨','forest'),phase(.68,.90,'中圈擴張','forest'),phase(.90,1.18,'外圈成林','forest'),phase(1.18,1.48,'骨柱碎沉','recover')],
        aiming:'完整圓盤逐波擴大；首領不因地形用flying旗標免傷，真跳躍略過當波。',
        audio:'三波地裂逐次加重，最後一波短重拍。'
      }),
    skill('lily', '鬼百合', 9, [100,120,140,170,200], 6, .90,
      '手持長骨鞭周身雙圈掃掠，範圍比唐松更寬。', '第一圈甩開，反向第二圈收回；髮束、袖口與腰繩一起轉。', {
        kind:'melee', quantityMode:'none', radius:[120,120,135,135,150], playerLock:[],
        hits:[strike(.32,.5),strike(.62,.5)], phaseDedup:true,
        phases:[phase(0,.14,'展鞭側後','prepare'),phase(.14,.32,'順向全周掃','sweep'),phase(.32,.44,'換重心','turn'),phase(.44,.62,'反向全周掃','sweep'),phase(.62,.90,'收鞭回位','recover')],
        aiming:'兩次完整360度各自去重；無內圈死區、減傷、吸附或推退。',
        audio:'兩次寬幅破風與骨節聲，與唐松短硬展骨聲區分。',
        sourceNote:'取手游咒印版本語意；本作學會後普通形態可用，屬改編。'
      })
  ];
  const curse = {
    id:'curse', name:'地之咒印', unlock:15, duration:1, previewDuration:10, activeDuration:8, cycle:30,
    damageBonus:[.10,.125,.15,.175,.20], speedBonus:.10, playerLock:[], hits:[],
    description:'1秒轉形後進入8秒咒印二，30秒周期；無自動付血。',
    feel:'咒紋沿皮膚蔓延，背骨、肉身長尾與低重心姿態形成完整轉變。',
    phases:[phase(0,.20,'收肩轉形','prepare'),phase(.20,.45,'咒紋蔓延','curseMarks'),phase(.45,.75,'背骨與尾展開','transform'),phase(.75,1,'二階待機','curseIdle')],
    triggerRange:220, priority:'周期就緒且有有效敵人時，下一身體空檔獲一次轉形優先，不打斷正在施放招式。',
    restore:'到期後不啟動新變身傷段；已起手招式按快照完成。死亡／換場／新局立即清理。'
  };
  const combo = {
    id:'combo', name:'蔓 → 花', duration:1.40, cd:8.54, damage:[240,288,336,408,480],
    description:'同組蔓接花：鞭先繃緊、骨鑽再刺入；各耗自己的冷卻，沒有免費第三擊。',
    feel:'1.40秒內完成拉緊、成鑽、重擊高潮，省去重複中立站姿。',
    members:['vine','flower'], vineStart:0, flowerStart:.54, maxWait:.54,
    independentCooldowns:true, normalEnemyControl:{start:.42,end:1.12,bossImmune:true},
    playerLock:[{start:.42,end:.62},{start:1,end:1.12}], hitStop:.045,
    hits:[{t:.42,share:.2,kind:'hit',skillId:'vine'},{t:1.12,share:.8,kind:'hit',skillId:'flower'}],
    phases:[phase(0,.20,'抽出骨鞭','prepare'),phase(.20,.42,'甩鞭接觸','whip'),phase(.42,.54,'拉緊目標','pull'),phase(.54,.62,'雙手接鑽','drillGrow'),phase(.62,1,'骨鑽成形','drillGrow'),phase(1,1.12,'重刺終結','drill'),phase(1.12,1.4,'抽鑽回位','recover')],
    pairing:'按同組技能ID辨識，不要求加入順序或組內相鄰。',
    fairness:'不越過等待更久的合法主動；另一招剩餘CD≤.54秒可短等，不啟動跨預約時點的柳。',
    reservation:'只用原預約目標；花.54秒起手前目標失效不花花CD，起手後失效照花CD但不補遠端傷害。'
  };
  function getCount(id, q = 0) {
    const item = skills.find(s => s.id === id);
    if (!item || item.quantityMode === 'none') return 1;
    return Math.min(item.maxCount, Math.floor(item.baseCount * 1.25 ** Math.max(0, Math.floor(q))));
  }
  function willowTimes(n = 4) {
    const count = Math.max(4, Math.min(8, Math.floor(n)));
    const gaps = Array.from({length:count - 1}, (_, i) => .85 ** i);
    const sum = gaps.reduce((a,b) => a+b, 0);
    const out = [.12];
    for (const gap of gaps) out.push(out[out.length-1] + .48 * gap / sum);
    return out;
  }
  skills[0].hits = willowTimes(4).map(t => strike(t,.25));
  function getSkill(id) { return skills.find(s => s.id === id) || (id === 'combo' ? combo : id === 'curse' ? curse : null); }
  function getHitEvents(id, q = 0) {
    const item = getSkill(id);
    if (!item) return [];
    if (id === 'willow') return willowTimes(getCount(id,q)).map((t,index) => ({t,share:.25,kind:'hit',index}));
    if (id === 'bullets') {
      const count = getCount(id,q);
      return Array.from({length:count}, (_,index) => ({
        t:item.releaseTimes[Math.floor(index * item.releaseTimes.length / count)],
        share:.20,kind:'release',index,targetIndex:index % 3
      }));
    }
    return item.hits.map((hit,index) => ({...hit,index}));
  }
  const design = {
    version:'final', date:'2026-10-27', title:'君麻呂・屍骨脈', scope:'獨立設計演出預覽；未接入正式遊戲',
    stats:{hp:160,speed:122,attack:1.32}, previewBodyHeight:64, gameLogicalBodyHeight:48, skills, curse, combo,
    quantity:{perPick:1.25,maxPicks:20,willowCap:8,bulletCap:15,camelliaTargetCap:12},
    common:{maxBondSkills:4,switchCooldownFactor:.35,cancelExit:.10,meleeReceivedFactor:.75,
      groundShape:'circle',bossPullImmune:true,defaultCameraShake:false,
      cancel:'切招恢復移動，取消未命中身體攻擊／未發射骨彈／後續骨林波；已發射骨彈繼續。',
      cleanup:'死亡／換角色／換場／新局清除所有在途招式、控制、護甲和形態；暫停凍結。',
      bodyQueue:'一身體一動作；主動依等待時間公平排程，柳只在空檔補攻。'},
    assets:{concept:'concept-extra-skills-v3.png',normalConcept:'concept-five-dances-v1.png',curseConcept:'concept-transformation-storyboard-v1.png'},
    getSkill,getCount,willowTimes,getHitEvents
  };
  if (typeof window !== 'undefined') window.KIMIMARO_DESIGN = design;
  if (typeof module !== 'undefined' && module.exports) module.exports = design;
})();
