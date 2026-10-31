/* Standalone motion study. Does not import or modify the game's combat runtime. */
(() => {
  'use strict';
  const TAU = Math.PI * 2;
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, Number(v) || 0));
  const ease = v => { const t = clamp(v); return t * t * (3 - 2 * t); };
  const lerp = (a, b, t) => a + (b - a) * t;
  const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
  const seeded = seed => { let n = seed >>> 0; return () => { n = (Math.imul(n, 1664525) + 1013904223) >>> 0; return n / 4294967296; }; };
  const rankValue = (v, rank, fallback) => Array.isArray(v) ? v[rank - 1] : Number.isFinite(v) ? v : fallback;
  const fallback = {
    willow: { name: '柳之舞', damage: [30, 36, 42, 51, 60], duration: .64, radius: [72, 72, 80, 80, 88] },
    camellia: { name: '椿之舞', damage: [120, 144, 168, 204, 240], duration: .74, length: [145, 145, 165, 165, 185] },
    bullets: { name: '十指穿彈', damage: [45, 54, 63, 76.5, 90], duration: .60, length: [260, 260, 280, 280, 300] },
    larch: { name: '唐松之舞', damage: [96, 115.2, 134.4, 163.2, 192], duration: .70, radius: [78, 78, 88, 88, 98] },
    vine: { name: '鐵線花・蔓', damage: [48, 57.6, 67.2, 81.6, 96], duration: .70, length: [220, 220, 240, 240, 260] },
    flower: { name: '鐵線花・花', damage: [192, 230.4, 268.8, 326.4, 384], duration: .86, length: [135, 135, 150, 150, 165] },
    bracken: { name: '早蕨之舞', damage: [300, 360, 420, 510, 600], duration: 1.48, radius: [180, 180, 210, 210, 240] },
    lily: { name: '鬼百合', damage: [100, 120, 140, 170, 200], duration: .90, radius: [120, 120, 135, 135, 150] },
    combo: { name: '蔓 → 花', damage: [240, 288, 336, 408, 480], duration: 1.40 },
    curse: { name: '地之咒印', damage: [0, 0, 0, 0, 0], duration: 10 }
  };
  const frameKeys = new Set(['idle', 'run1', 'run2', 'run3', 'willow1', 'willow2', 'camellia1', 'camellia2', 'bullets', 'larch', 'vine1', 'vine2', 'flower1', 'flower2', 'bracken', 'lily']);

  class KimimaroScene {
    constructor(canvas, options = {}) {
      if (!canvas?.getContext) throw new Error('KimimaroScene requires a canvas.');
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.width = 900;
      this.height = 560;
      this.skill = options.skill || 'willow';
      this.rank = 1;
      this.quantity = 0;
      this.form = 'normal';
      this.scenario = 'crowd';
      this.time = 0;
      this.showRange = true;
      this.cancelAt = null;
      this.assets = {};
      this.effects = null;
      this.effectStatus = 'not-loaded';
      this.forestCache = null;
      this.frameClipCache = new WeakMap();
      this.stage = null;
      this.stageStatus = 'not-loaded';
      this.groundCache = null;
      this.whiteSheets = new WeakMap();
      this.assetStatus = 'not-loaded';
      this.baseURL = new URL('.', document.currentScript?.src || location.href);
      this._cache = null;
    }

    async loadAssets() {
      try {
        const response = await fetch(new URL('actors.json', this.baseURL));
        if (!response.ok) throw new Error(`actors.json ${response.status}`);
        const metadata = await response.json();
        const forms = { normal: metadata.normal || metadata, curse: metadata.curse || metadata.cursed };
        await Promise.all(Object.entries(forms).map(async ([name, meta]) => {
          if (!meta?.image || !meta?.frames) return;
          const img = new Image();
          await new Promise((resolve, reject) => {
            img.onload = resolve;
            img.onerror = () => reject(new Error(`Cannot load ${meta.image}`));
            img.src = new URL(meta.image, this.baseURL).href;
          });
          this.assets[name] = { ...meta, image: img };
        }));
        this.assetStatus = this.assets.normal ? 'loaded' : 'missing-normal';
      } catch (error) {
        this.assetStatus = 'procedural-fallback';
        this.assetError = String(error.message || error);
      }
      try {
        const response = await fetch(new URL('effects.json', this.baseURL));
        if (!response.ok) throw new Error(`effects.json ${response.status}`);
        const meta = await response.json();
        const image = new Image();
        await new Promise((resolve, reject) => {
          image.onload = resolve;
          image.onerror = reject;
          image.src = new URL(meta.image, this.baseURL).href;
        });
        this.effects = { ...meta, image };
        this.effectStatus = 'loaded';
      } catch (error) {
        this.effectStatus = 'not-loaded';
      }
      try {
        const response = await fetch(new URL('stage-assets.json', this.baseURL));
        if (!response.ok) throw new Error(`stage-assets.json ${response.status}`);
        const meta = await response.json();
        const definitions = {};
        const sources = [];
        await Promise.all(meta.sprites.map(async sprite => {
          const definition = {...sprite};
          for (const name of ['idle','hurt']) {
            if (!sprite[name]?.image) continue;
            const animation = {...sprite[name]};
            const image = new Image();
            await new Promise((resolve,reject) => {
              image.onload=resolve;image.onerror=reject;
              image.src=new URL(animation.image,this.baseURL).href;
            });
            animation.sheet=image;animation.visualFrames=this.spriteVisualFrames(animation);
            definition[name]=animation;sources.push(image.src);
          }
          definitions[String(sprite.id)]=definition;
        }));
        const props={};
        await Promise.all(Object.entries(meta.props||{}).map(async([name,prop])=>{
          const image=new Image();
          await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src=new URL(prop.image,this.baseURL).href;});
          props[name]={...prop,sheet:image};sources.push(image.src);
        }));
        this.stage={...meta,definitions,props,sources:sources.sort()};
        this.stageStatus='loaded';this.groundCache=null;
      } catch (error) {
        this.stageStatus='not-loaded';this.stageError=String(error.message||error);
      }
      this.draw();
      return this.assetStatus;
    }

    data(id = this.skill) {
      return (window.KIMIMARO_DESIGN?.skills || []).find(s => s.id === id) || fallback[id] || fallback.willow;
    }
    damage(id = this.skill) { return rankValue(this.data(id).damage, this.rank, 30); }
    radius(id = this.skill) { return rankValue(this.data(id).radius, this.rank, rankValue(this.data(id).length, this.rank, 120)); }
    get duration() { return this.skill === 'curse' ? 10 : this.skill === 'combo' ? 1.4 : this.data().duration || fallback[this.skill]?.duration || 1; }
    setSkill(id) { if (!fallback[id]) return; this.skill = id; this.reset(); }
    setRank(rank) { this.rank = Math.round(clamp(rank, 1, 5)); this._cache = null; this.forestCache = null; }
    setQuantity(q) { this.quantity = Math.round(clamp(q, 0, 20)); this._cache = null; }
    setForm(form) { this.form = form === 'curse' ? 'curse' : 'normal'; this._cache = null; }
    setScenario(scenario) { this.scenario = scenario === 'boss' ? 'boss' : 'crowd'; this._cache = null; }
    setRangeVisible(visible) { this.showRange = Boolean(visible); }
    setTime(seconds) { this.time = Math.max(0, Number(seconds) || 0); this._cache = null; }
    update(dt) { this.setTime(this.time + clamp(dt, 0, .1)); }
    reset() { this.time = 0; this.cancelAt = null; this._cache = null; }
    cancel() { this.cancelAt = this.time; this._cache = null; }
    destroy() { this.assets = {}; this.effects = null; this.stage=null;this.groundCache=null;this.forestCache = null; this._cache = null; }

    actorPosition(at = this.time) {
      // Small moving-footwork study; does not relocate the skill's ground origin.
      const moving = ['camellia', 'bullets', 'lily', 'curse'].includes(this.skill) || (this.skill === 'bracken' && at > .30);
      const walk = moving ? Math.min(at, this.duration) * 10 : 0;
      return { x: 365 - walk, y: 324 + (moving ? Math.sin(at * 5) * 2 : 0) };
    }

    willowTimes() {
      const n = Math.min(8, Math.floor(4 * 1.25 ** this.quantity));
      const gaps = Array.from({ length: n - 1 }, (_, i) => .85 ** i);
      const sum = gaps.reduce((a, b) => a + b, 0);
      const times = [.12];
      for (const gap of gaps) times.push(times.at(-1) + .48 * gap / sum);
      return times;
    }

    initialTargets() {
      const p = this.actorPosition(0);
      const d = this.damage();
      const r = this.radius();
      let positions;
      if (this.skill === 'bracken') positions = [[42, -20], [104, 20], [-108, -80], [r + 42, 30]];
      else if (this.skill === 'larch') positions = [[53, -12], [-47, 25], [12, 65], [r + 50, -28]];
      else if (this.skill === 'lily') positions = [[85, -10], [-70, 45], [15, 97], [r + 55, -20]];
      else if (this.skill === 'willow') positions = [[53, 1], [58, 18], [63, -21], [180, 60]];
      else if (this.skill === 'bullets') positions = [[183, -42], [230, 2], [206, 62], [330, -90]];
      else if (this.skill === 'vine' || this.skill === 'combo') positions = [[160, 0], [111, -16], [126, 18], [275, 70]];
      else positions = [[101, 0], [116, -14], [130, 16], [210, 72]];
      if (this.scenario === 'boss') positions[0] = [this.skill === 'bullets' ? 210 : this.skill === 'bracken' ? 110 : 105, 0];
      return positions.map(([x, y], i) => ({
        id: `target-${i + 1}`, x: p.x + x, y: p.y + y, startX: p.x + x, startY: p.y + y,
        r: i === 0 && this.scenario === 'boss' ? 27 : 13,
        maxHp: Math.max(48, d * (this.skill === 'bullets' ? .55 : 1.12)), hp: Math.max(48, d * (this.skill === 'bullets' ? .55 : 1.12)),
        boss: i === 0 && this.scenario === 'boss', flying: i === 0 && this.scenario === 'boss', jumpLift: 0,
        outside: i === 3, hits: 0, dead: false
      }));
    }

    evaluate() {
      if (this._cache) return this._cache;
      const t = this.time, base = this.damage(), targets = this.initialTargets();
      const queue = [], events = [], projectiles = [];
      const cancelled = this.cancelAt;
      const isAllowed = time => cancelled == null || time <= cancelled + 1e-8;
      const enqueue = (time, kind, extra = {}) => queue.push({ time, kind, ...extra });
      if (this.skill === 'willow') this.willowTimes().forEach((time, index) => enqueue(time, 'willow', { phase: index, share: .25 }));
      if (this.skill === 'camellia') [.30, .43, .57].forEach((time, phase) => enqueue(time, 'line', { phase, share: [.25, .25, .5][phase] }));
      if (this.skill === 'larch') [.30, .52].forEach((time, phase) => enqueue(time, 'circle', { phase, share: .5 }));
      if (this.skill === 'lily') [.32, .62].forEach((time, phase) => enqueue(time, 'circle', { phase, share: .5 }));
      if (this.skill === 'vine' || this.skill === 'combo') enqueue(.42, 'vine', { phase: 0, share: this.skill === 'combo' ? .2 : 1 });
      if (this.skill === 'flower' || this.skill === 'combo') enqueue(this.skill === 'combo' ? 1.12 : .58, 'flower', { phase: 1, share: this.skill === 'combo' ? .8 : 1 });
      if (this.skill === 'bracken') [.48, .68, .90].forEach((time, phase) => enqueue(time, 'wave', { phase, share: 1, fraction: (phase + 1) / 3 }));
      if (this.skill === 'bullets') {
        const count = Math.min(15, Math.floor(5 * 1.25 ** this.quantity));
        for (let i = 0; i < count; i++) enqueue([.16, .23, .30, .37, .44][Math.floor(i * 5 / count)], 'release', { phase: i, share: .2 });
      }
      const castSeen = new Set();
      let cursor = 0;
      while (queue.length) {
        queue.sort((a, b) => a.time - b.time || (a.phase || 0) - (b.phase || 0));
        const item = queue.shift();
        if (item.time > t + 1e-8) break;
        if (item.kind !== 'projectile-hit' && !isAllowed(item.time)) continue;
        const p = this.actorPosition(item.time);
        const primary = targets[0];
        const legal = target => !target.dead;
        const hit = (target, amount, extra = {}) => {
          if (!legal(target)) return;
          target.hp = Math.max(0, target.hp - amount);
          target.hits++;
          target.dead = target.hp <= 0;
          events.push({ id: `hit-${events.length}`, type: 'hit', time: item.time, phase: item.phase, targetId: target.id, damage: amount, x: target.x, y: target.y, ...extra });
        };
        if (item.kind === 'release') {
          const choices = targets.filter(e => legal(e) && distance(e, p) <= this.radius()).sort((a,b)=>distance(a,p)-distance(b,p)).slice(0, 3);
          if (!choices.length) continue;
          const target = choices[cursor++ % choices.length];
          const source = { x: p.x + 15, y: p.y - 35 };
          const aim = { x: target.x, y: target.y - (target.boss ? 43 : 27) };
          const aimDistance=distance(source,aim),ux=(aim.x-source.x)/aimDistance,uy=(aim.y-source.y)/aimDistance;
          // Bone shots stop on the first body along their fixed ray. The named
          // aim target is not an exemption from an intervening enemy.
          let struck=target,travel=aimDistance;
          for(const candidate of targets.filter(legal)){
            const center={x:candidate.x,y:candidate.y-(candidate.boss?43:27)};
            const dx=center.x-source.x,dy=center.y-source.y,along=dx*ux+dy*uy;
            const perpendicular=dx*dx+dy*dy-along*along;
            if(along<0||perpendicular>candidate.r*candidate.r)continue;
            const entry=Math.max(0,along-Math.sqrt(Math.max(0,candidate.r*candidate.r-perpendicular)));
            if(entry<travel){travel=entry;struck=candidate;}
          }
          const end={x:source.x+ux*travel,y:source.y+uy*travel};
          const flight = Math.max(.04, travel / 600);
          const projectile = { id: `bone-${item.phase}`, release: item.time, hitTime: item.time + flight, source, end, aimTargetId:target.id,targetId: struck.id, damage: base * .2 };
          projectiles.push(projectile);
          events.push({ id: projectile.id, type: 'release', time: item.time, phase: item.phase, targetId: target.id, x: source.x, y: source.y });
          enqueue(projectile.hitTime, 'projectile-hit', { phase: item.phase, projectile, target:struck });
        } else if (item.kind === 'projectile-hit') {
          if (item.target && legal(item.target)) hit(item.target, item.projectile.damage, { projectileId: item.projectile.id });
        } else if (item.kind === 'willow') {
          const target = targets.filter(e => legal(e) && distance(e, p) <= this.radius()).sort((a, b) => distance(a, p) - distance(b, p))[0];
          if (target) hit(target, base * item.share);
        } else if (item.kind === 'line') {
          const half = rankValue(this.data().halfWidth, this.rank, 24);
          targets.filter(e => legal(e) && e.x >= p.x && e.x - p.x <= this.radius() && Math.abs(e.y - p.y) <= half).forEach(e => hit(e, base * item.share));
        } else if (item.kind === 'circle') {
          targets.filter(e => legal(e) && distance(e, p) <= this.radius()).forEach(e => hit(e, base * item.share));
        } else if (item.kind === 'wave') {
          const center = this.actorPosition(0);
          targets.filter(e => legal(e) && !castSeen.has(e.id) && e.jumpLift <= 0 && (!e.flying || e.boss) && distance(e, center) <= this.radius() * item.fraction).forEach(e => {
            castSeen.add(e.id); hit(e, base, { wave: item.phase + 1 });
          });
        } else if (item.kind === 'vine') {
          if (legal(primary) && distance(primary, p) <= (this.skill === 'combo' ? this.radius('vine') : this.radius())) hit(primary, base * item.share);
        } else if (item.kind === 'flower') {
          const reach = this.skill === 'combo' ? this.radius('flower') : this.radius();
          const mainX = this.skill === 'combo' && !primary.boss ? this.actorPosition(0).x + 64 : primary.x;
          const amount = base * item.share;
          if (legal(primary) && mainX - p.x >= 0 && mainX - p.x <= reach && Math.abs(primary.y-p.y)<=24) hit(primary, amount, { x: mainX });
          targets.slice(1, 4).filter(e => legal(e) && e.x-p.x>=0 && e.x - p.x <= reach && Math.abs(e.y - p.y) <= 24).forEach(e => hit(e, amount * .5));
        }
      }
      const hits = events.filter(e => e.type === 'hit');
      if ((this.skill === 'vine' || this.skill === 'combo') && !targets[0].boss && t >= .42 && isAllowed(.42)) {
        const pull = ease((Math.min(t, .62) - .42) / .20);
        targets[0].x = lerp(targets[0].startX, this.actorPosition(0).x + 64, pull);
      }
      const guard = this.skill === 'larch' && t >= .18 && t < .88 && (cancelled == null || t <= cancelled);
      const asset=this.assets[this.currentForm()]||this.assets.normal;
      const activeFrame=asset?.frames?.[this.poseAt(t)]||asset?.frames?.idle;
      const result = {
        skill: this.skill, time: t, duration: this.duration, rank: this.rank, quantity: this.quantity, form: this.currentForm(), scenario: this.scenario,
        phase: this.phaseName(t), actor: this.actorPosition(t), targets, events, hits, projectiles,
        totalDamage: hits.reduce((sum, e) => sum + e.damage, 0), guard, cancelled: cancelled != null, cancelAt: cancelled,
        assetStatus: this.assetStatus, actorsLoaded: Object.keys(this.assets), pose: this.poseAt(t),
        actorSource: (this.assets[this.currentForm()] || this.assets.normal)?.image?.src || 'procedural-fallback',
        renderedForm: this.assets[this.currentForm()] ? this.currentForm() : this.assets.normal ? 'normal' : 'procedural-fallback',
        clipApplied: Boolean(activeFrame?.clipRuns?.length && asset?.image),
        clipRunCount: activeFrame?.clipRuns?.length || 0,
        weapon: this.drillGeometry(t),
        effectsLoaded: this.effectStatus === 'loaded', effectSource: this.effects?.image?.src || null,
        stageAssetsLoaded:this.stageStatus==='loaded',stageAssetSources:this.stage?.sources||[],
        targetRenderSources:targets.map(target=>({id:target.id,...this.targetRenderInfo(target,t,hits)})),
        groundStyle:'game-forest-pixel',groundPixelScale:2,stagePixelScale:2,
        camera:{...this.cameraFrame(),worldViewWidth:900/this.cameraFrame().zoom},
        diagnosticRange:this.showRange,
        effectAtlas: this.effects?.image ? {width:this.effects.image.naturalWidth,height:this.effects.image.naturalHeight,
          decodedBytes:this.effects.image.naturalWidth*this.effects.image.naturalHeight*4} : null,
        forestLayout: this.skill === 'bracken' ? this.forestColumns(t, targets) : [],
        forestCenter: this.skill === 'bracken' ? this.actorPosition(0) : null,
        forestRadius: this.skill === 'bracken' ? this.radius() : null,
        forestSeed: this.skill === 'bracken' ? 0x51b073 + this.rank * 173 : null,
        vfxBudget: this.skill === 'bracken' ? {forestCount:this.forestColumns(t,targets).length,
          activeParticleCount:this.forestParticles(this.forestColumns(t,targets),t,hits).length+this.impactParticles(hits,t).length,
          maxForestColumns:36,maxSecondaryParticles:20} : {forestCount:0,activeParticleCount:this.impactParticles(hits,t).length,maxForestColumns:36,maxSecondaryParticles:20}
      };
      this._cache = result;
      return result;
    }

    getSnapshot() { return JSON.parse(JSON.stringify(this.evaluate())); }
    forestColumns(at = this.time, targets = []) {
      const center = this.actorPosition(0), R = this.radius();
      const seed = 0x51b073 + this.rank * 173;
      if (!this.forestCache || this.forestCache.seed !== seed) {
        const random = seeded(seed), points = [];
        const clumps = [
          [-.47,-.30,.26], [.24,-.52,.25], [.53,.05,.30],
          [-.25,.49,.31], [.22,.43,.25], [-.60,.18,.24]
        ];
        let attempts = 0;
        while (points.length < 36 && attempts++ < 3000) {
          const clustered = random() < .73;
          const cluster = clumps[Math.floor(random() * clumps.length)];
          const angle = random() * TAU;
          const radius = Math.sqrt(random()) * (clustered ? cluster[2] : .97);
          const nx = (clustered ? cluster[0] : 0) + Math.cos(angle) * radius;
          const ny = (clustered ? cluster[1] : 0) + Math.sin(angle) * radius;
          const d = Math.hypot(nx,ny);
          if (d > .97 || d < .09) continue;
          // A few broken lanes keep moving enemies and the caster readable.
          if (Math.abs(nx + .25 * ny) < .055 && ny > -.1 && random() < .80) continue;
          if (points.some(p => Math.hypot(p.nx-nx,p.ny-ny) < .072)) continue;
          const wave = Math.min(2,Math.floor(d * 3));
          points.push({ nx,ny,wave,variant:1+Math.floor(random()*8),
            height:42+random()**.67*103+(random()<.14?24:0),
            width:8+random()*13,lean:(random()-.5)*.58,
            delay:(random()-.5)*.065,shapeSeed:random() });
        }
        points.sort((a,b)=>a.ny-b.ny);
        // Eight clear silhouettes carry the forest; the remaining columns are
        // lower colonies. This avoids thirty-six equally tall twig-like trees.
        const majorOrder=points.map((point,index)=>({index,weight:point.shapeSeed})).sort((a,b)=>b.weight-a.weight);
        const majors=new Set(majorOrder.slice(0,8).map(item=>item.index));
        points.forEach((point,index)=>{
          point.major=majors.has(index);
          point.variant=point.major?1+(index%4):5+(index%4);
          point.height=point.major?100+point.shapeSeed*48:25+point.shapeSeed*47;
          point.width=point.major?14+point.shapeSeed*8:10+point.shapeSeed*9;
        });
        this.forestCache = {seed,points};
      }
      const actor = this.actorPosition(at);
      return this.forestCache.points.map((point,index) => {
        const x=center.x+point.nx*R,y=center.y+point.ny*R;
        const start=[.48,.68,.90][point.wave]+point.delay;
        const grow=ease((at-start+.025)/.145)*(1-ease((at-1.19)/.30));
        const height=point.height*grow;
        const tipX=x+Math.sin(point.lean)*height,tipY=y-Math.cos(point.lean)*height;
        const occludes = object => y >= object.y-8 && tipY <= object.y-20 &&
          Math.max(x,tipX)+point.width >= object.x-18 && Math.min(x,tipX)-point.width <= object.x+18;
        const occluding = occludes(actor);
        return {...point,index,x,y,height,width:point.width,baseHeight:point.height,start,grow,
          opacity:occluding?.36:.98,occluding,visible:grow>.005 && at>=.30 && at<1.65 && !(this.cancelAt!=null&&at>this.cancelAt)};
      });
    }
    forestParticles(columns,at=this.time,hits=[]) {
      if(this.cancelAt!=null&&at>this.cancelAt)return [];
      const limit=Math.floor((20-this.impactParticles(hits,at).length)/2);
      const candidates=columns.filter(col=>at-col.start>=-.02&&at-col.start<.30)
        .sort((a,b)=>b.start-a.start).slice(0,Math.max(0,limit));
      const particles=[];
      for(const col of candidates){
        const age=at-col.start,q=clamp((age+.02)/.32),a=col.shapeSeed*TAU;
        particles.push({kind:'rock',x:col.x+Math.cos(a)*(8+q*23),
          y:col.y+Math.sin(a)*6-Math.sin(q*Math.PI)*(11+col.shapeSeed*9),q,size:2+col.shapeSeed*2});
        particles.push({kind:'dust',x:col.x-Math.cos(a)*(3+q*11),
          y:col.y-2-q*8,q,size:7+q*8});
      }
      return particles;
    }
    impactParticles(hits,at=this.time) {
      const particles=[];
      for(const hit of [...hits].sort((a,b)=>b.time-a.time)){
        const age=at-hit.time;if(age<0||age>.32)continue;
        const q=age/.32,random=seeded((hit.phase+1)*1237+Math.floor(hit.x*17+hit.y*29));
        for(let i=0;i<3&&particles.length<12;i++){
          const a=random()*TAU,d=4+q*(15+random()*22);
          particles.push({x:hit.x+Math.cos(a)*d,y:hit.y-28+Math.sin(a)*d+q*q*16,
            q,size:1.6+random()*2.3,a,color:i%2?'#b5afc1':'#f8f3e7'});
        }
      }
      return particles;
    }
    drillGeometry(at=this.time) {
      if(!['flower','combo'].includes(this.skill))return null;
      if(this.cancelAt!=null&&at>this.cancelAt)return null;
      const age=this.skill==='combo'?at-.54:at;
      if(age<.12||age>=.86)return null;
      const p=this.actorPosition(at),reach=this.skill==='combo'?this.radius('flower'):this.radius();
      const grow=ease((age-.12)/.18),back=1-ease((age-.64)/.22);
      const front=lerp(46,reach,ease((age-.22)/.36));
      const horizontalLength=Math.max(0,front-28)*back,power=grow*back;
      const target=this.initialTargets()[0];
      const body=this.targetRenderInfo(target,at,[]).bodyCenter;
      const rise=(body.y-(p.y-31))*clamp(horizontalLength/Math.max(1,reach-28));
      const length=Math.hypot(horizontalLength,rise),angle=Math.atan2(rise,horizontalLength);
      return {kind:'bone-drill',base:{x:p.x+28,y:p.y-31},tip:{x:p.x+28+horizontalLength,y:p.y-31+rise},halfWidth:10*power,visible:length>2&&power>.02,length,power,angle};
    }
    cameraFrame() {
      const mobile = (this.canvas.getBoundingClientRect?.().width || this.canvas.clientWidth || 900) < 600;
      if(this.skill==='bracken'&&this.showRange) return {zoom:this.rank>=3?.88:1.02,x:450,y:280,origin:this.actorPosition(0)};
      // A full-screen mobile stage has less CSS area than desktop. The whole
      // study gets one closer frame, preserving body/effect proportions.
      const zoom = mobile ? 1.72 : 1.32;
      return {zoom,x:450,y:mobile?285:306,origin:{x:425,y:310}};
    }
    currentForm() { return this.skill === 'curse' ? (this.time >= .75 && this.time < 9 ? 'curse' : 'normal') : this.form; }
    phaseName(t = this.time) {
      if (this.cancelAt != null && t >= this.cancelAt) return '取消・回位';
      if (this.skill === 'curse') return t < .20 ? '收肩' : t < .45 ? '咒紋蔓延' : t < 1 ? '背骨・長尾成形' : t < 9 ? '咒印二・戰鬥姿態' : '還原';
      const phases = this.data().phases;
      const phase = phases?.find(p => t >= p.start && t < p.end);
      if (phase) return phase.label;
      if (t > this.duration) return '收勢完成';
      return t < .16 ? '蓄勢' : t < this.duration * .75 ? '出手・命中' : '收勢';
    }

    poseAt(t) {
      if (this.cancelAt != null && t >= this.cancelAt) return 'idle';
      if (t > this.duration && this.skill !== 'curse') return 'idle';
      if (this.skill === 'curse') return t < 1 ? 'larch' : ['run1', 'run2', 'run3'][Math.floor(t * 6) % 3];
      if (this.skill === 'willow') return t < .12 ? 'idle' : Math.floor(t * 16) % 2 ? 'willow1' : 'willow2';
      if (this.skill === 'camellia') return t < .16 ? 'camellia1' : Math.floor(t * 12) % 2 ? 'camellia2' : 'camellia1';
      if (this.skill === 'bullets') return t < .12 ? 'idle' : t < .46 ? 'bullets' : 'run2';
      if (this.skill === 'larch') return t < .18 || t > .62 ? 'idle' : 'larch';
      if (this.skill === 'vine') return t < .30 || t > .62 ? 'vine1' : 'vine2';
      if (this.skill === 'flower') return t < .43 ? 'flower1' : 'flower2';
      if (this.skill === 'combo') return t < .30 ? 'vine1' : t < .54 ? 'vine2' : t < .97 ? 'flower1' : 'flower2';
      if (this.skill === 'bracken') return t < .3 ? 'bracken' : t < .9 ? 'idle' : 'run1';
      if (this.skill === 'lily') return t < .14 ? 'vine1' : t > .72 ? 'idle' : 'lily';
      return 'idle';
    }

    draw() {
      const c = this.ctx;
      const sx = this.canvas.width / this.width, sy = this.canvas.height / this.height;
      c.setTransform(sx, 0, 0, sy, 0, 0);
      c.clearRect(0, 0, this.width, this.height);
      const s = this.evaluate();
      // Camera framing is fixed for an entire study, never a hit-triggered zoom.
      c.save();
      const camera=this.cameraFrame();
      c.translate(camera.x,camera.y);c.scale(camera.zoom,camera.zoom);c.translate(-camera.origin.x,-camera.origin.y);
      this.drawGround();
      if (this.showRange && this.skill !== 'curse') this.drawRange(s);
      if (this.skill === 'bracken') this.drawForest(s, true);
      this.drawGroundEffects(s);
      const actors = [...s.targets.map(target => ({ y: target.y, target })), { y: s.actor.y, actor: true }].sort((a, b) => a.y - b.y);
      for (const item of actors) {
        if (item.actor) this.drawActor(s);
        else this.drawTarget(item.target, s);
      }
      this.drawWeapons(s);
      if (this.skill === 'bracken') this.drawForest(s, false);
      this.drawImpacts(s);
      this.drawProjectiles(s);
      c.restore();
      this.drawLabels(s);
    }

    drawGround() {
      const c = this.ctx;
      if(!this.groundCache)this.groundCache=this.paintGround();
      c.save();c.imageSmoothingEnabled=false;
      c.fillStyle='#3e7a39';c.fillRect(-600,-500,1800,1500);
      c.drawImage(this.groundCache,-64,-104,1024,768);c.restore();
    }

    paintGround() {
      // Same two-world-unit art pixel and forest palette as js/world/tiles.js.
      // This is a cached procedural surface, not another background texture.
      const canvas=document.createElement('canvas');canvas.width=512;canvas.height=384;
      const c=canvas.getContext('2d'),pixels=c.createImageData(512,384);
      const colors={grass:[[62,122,57],[68,129,61],[57,113,52]],
        dirt:[[125,103,66],[115,94,59],[134,112,74]],speck:[47,95,43],light:[95,157,80]};
      const hash=(x,y,seed)=>{
        let n=Math.imul(x+seed*137,374761393)^Math.imul(y+seed*31,668265263);
        n=Math.imul(n^(n>>>13),1274126177);return ((n^(n>>>16))>>>0)/4294967295;
      };
      for(let y=0;y<384;y++)for(let x=0;x<512;x++){
        const worldX=x*2-64,worldY=y*2-104;
        const boundary=1+Math.sin(x*.047+y*.023)*.15+Math.sin(y*.081-x*.031)*.10;
        const pathAxis=349+Math.sin(worldX*.009)*22;
        const path=worldX>520&&Math.abs(worldY-pathAxis)<(30+Math.sin(worldX*.037)*7);
        const inlet=Math.sin(worldX*.021+worldY*.014)>.86&&worldX<325&&worldY<330;
        const clearing=!inlet&&(path||Math.min(((worldX-421)/178)**2+((worldY-326)/91)**2,
          ((worldX-589)/121)**2+((worldY-354)/80)**2,
          ((worldX-285)/92)**2+((worldY-288)/68)**2,
          ((worldX-454)/126)**2+((worldY-421)/61)**2)<boundary);
        const fine=hash(x,y,12),band=hash(x>>3,y>>3,11)*.7+fine*.5;
        let color=(clearing?colors.dirt:colors.grass)[Math.min(2,Math.floor(band*2.5))];
        if(!clearing&&fine<.027)color=colors.speck;
        else if(!clearing&&fine>.989)color=colors.light;
        else if(clearing&&fine<.018)color=[104,87,59];
        const offset=(y*512+x)*4;
        pixels.data[offset]=color[0];pixels.data[offset+1]=color[1];pixels.data[offset+2]=color[2];pixels.data[offset+3]=255;
      }
      c.putImageData(pixels,0,0);
      const random=seeded(0x91f041),grass=['#2f5f2b','#4c9a3f','#5f9d50'];
      // Edge vegetation frames the clearing. Its frequency follows the game
      // tile language, with the fight center deliberately quiet.
      for(let i=0;i<132;i++){
        const x=Math.floor(random()*512),y=Math.floor(random()*384);
        const wx=x*2-64,wy=y*2-104;
        if(Math.min(((wx-421)/190)**2+((wy-326)/98)**2,((wx-589)/132)**2+((wy-354)/88)**2,
          ((wx-285)/100)**2+((wy-288)/74)**2,((wx-454)/134)**2+((wy-421)/68)**2)<1.10)continue;
        c.fillStyle=grass[i%3];c.fillRect(x,y,1,3);c.fillRect(x-1,y+1,3,1);
      }
      for(const [x,y,k] of [[33,236,9],[412,219,8],[74,44,6],[391,49,7],[20,160,5],[431,117,5]]){
        c.fillStyle='#2f5f2b';c.fillRect(x-k-2,y+k-2,k*2+4,3);
        c.fillStyle='#5e6670';c.beginPath();c.moveTo(x-k,y);c.lineTo(x-k*.55,y-k*.72);c.lineTo(x+k*.3,y-k);c.lineTo(x+k,y-k*.15);c.lineTo(x+k*.75,y+k*.35);c.lineTo(x-k*.6,y+k*.42);c.closePath();c.fill();
        c.fillStyle='#7f8893';c.beginPath();c.moveTo(x-k*.55,y-k*.72);c.lineTo(x+k*.3,y-k);c.lineTo(x+k*.8,y-k*.2);c.lineTo(x,y);c.closePath();c.fill();
        c.fillStyle='#a1aab4';c.fillRect(x-2,y-k+1,3,1);
      }
      const prop=(name,wx,wy)=>{
        const sheet=this.stage?.props?.[name]?.sheet;if(!sheet)return;
        c.imageSmoothingEnabled=false;c.drawImage(sheet,Math.round((wx+64)/2-sheet.width/2),Math.round((wy+104)/2-sheet.height));
      };
      for(const [x,y] of [[95,140],[248,151],[615,123],[759,181],[106,472],[735,508]])prop('tree',x,y);
      for(const [x,y] of [[218,264],[563,229],[661,300],[291,431],[649,440],[169,357]])prop('grass',x,y);
      for(const [x,y] of [[704,209],[159,459],[755,424]])prop('rock',x,y);
      return canvas;
    }

    drawRange(s) {
      const c = this.ctx, center = this.skill === 'bracken' ? this.actorPosition(0) : s.actor;
      c.save(); c.setLineDash([5, 8]); c.lineWidth = 1;
      c.strokeStyle = '#799a8d'; c.globalAlpha = .32;
      if (['bracken', 'larch', 'lily'].includes(this.skill)) {
        c.beginPath(); c.arc(center.x, center.y, this.radius(), 0, TAU); c.stroke();
      } else if (['flower', 'camellia', 'combo'].includes(this.skill)) {
        const length = this.skill === 'combo' ? this.radius('flower') : this.radius();
        c.strokeRect(center.x, center.y - 24, length, 48);
      } else if (this.skill === 'willow') {
        c.beginPath(); c.moveTo(center.x, center.y); c.arc(center.x, center.y, this.radius(), -.7, .7); c.closePath(); c.stroke();
      }
      c.restore();
    }

    drawGroundEffects(s) {
      const c = this.ctx, t = s.time, p = s.actor;
      if (this.skill === 'curse' && t >= .2 && t < 1.3) {
        const progress=ease((t-.2)/.8),fade=1-ease((t-.8)/.5);
        c.save();c.strokeStyle='#3f344e';c.lineWidth=1.8;c.globalAlpha=fade*.8;
        for(let i=0;i<4;i++){
          const side=i%2?-1:1,y=p.y-26-i*7;
          c.beginPath();c.moveTo(p.x+side*8,y);c.lineTo(p.x+side*(13+progress*4),y-3-progress*7);c.lineTo(p.x+side*12,y-8-progress*9);c.stroke();
        }
        c.restore();
      }
    }

    drawTarget(target, s) {
      const rendered=this.targetRenderInfo(target,s.time,s.hits);
      if(rendered.source){
        const c=this.ctx,definition=this.stage.definitions[rendered.dex];
        const animation=definition[rendered.animation];
        const source=animation.sheet;
        const f=rendered.frame,dir=rendered.direction,k=rendered.scale;
        c.save();c.imageSmoothingEnabled=false;
        c.fillStyle='#172c1f';c.globalAlpha=.31;
        const shadow=[5,8,12][Math.max(0,Math.min(2,definition.shadow||0))]*2*(target.boss?1.25:1);
        c.beginPath();c.ellipse(target.x,target.y+1,shadow,shadow*.42,0,0,TAU);c.fill();
        c.globalAlpha=target.dead?.3:1;
        c.drawImage(source,f*animation.w,dir*animation.h,animation.w,animation.h,
          target.x+rendered.recoil-animation.ax*k,target.y-animation.ay*k,animation.w*k,animation.h*k);
        if(rendered.flash){
          c.globalAlpha*=.52;
          c.drawImage(this.whiteSprite(animation.sheet),f*animation.w,dir*animation.h,animation.w,animation.h,
            target.x+rendered.recoil-animation.ax*k,target.y-animation.ay*k,animation.w*k,animation.h*k);
        }
        c.restore();
        const barW=target.boss?56:29,barY=rendered.visualBounds.top-8;
        c.fillStyle='#20352c';c.fillRect(target.x-barW/2-1,barY-1,barW+2,4);
        c.fillStyle='#639447';c.fillRect(target.x-barW/2,barY,barW*Math.max(0,target.hp/target.maxHp),2);
        if(this.showRange&&target.outside){c.fillStyle='#273e31';c.font='9px system-ui';c.textAlign='center';c.fillText('範圍外',target.x,barY-5);c.textAlign='left';}
        return;
      }
      this.drawTargetFallback(target,s);
    }

    spriteVisualFrames(animation) {
      const canvas=document.createElement('canvas');canvas.width=animation.sheet.width;canvas.height=animation.sheet.height;
      const c=canvas.getContext('2d');c.drawImage(animation.sheet,0,0);
      const pixels=c.getImageData(0,0,canvas.width,canvas.height).data;
      const frames=[];
      for(let row=0;row<animation.r;row++)for(let frame=0;frame<animation.n;frame++){
        let left=animation.w,top=animation.h,right=0,bottom=0;
        for(let y=0;y<animation.h;y++)for(let x=0;x<animation.w;x++){
          const index=((row*animation.h+y)*canvas.width+frame*animation.w+x)*4;
          if(pixels[index+3]<30)continue;
          left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x+1);bottom=Math.max(bottom,y+1);
        }
        frames[row*animation.n+frame]=right>left?{left,top,right,bottom}:{left:0,top:0,right:animation.w,bottom:animation.h};
      }
      return frames;
    }

    whiteSprite(image) {
      let white=this.whiteSheets.get(image);
      if(!white){
        white=document.createElement('canvas');white.width=image.width;white.height=image.height;
        const c=white.getContext('2d');c.drawImage(image,0,0);c.globalCompositeOperation='source-in';
        c.fillStyle='#fffbea';c.fillRect(0,0,white.width,white.height);this.whiteSheets.set(image,white);
      }
      return white;
    }

    targetRenderInfo(target,at=this.time,hits=[]) {
      const normalIds=this.stage?.normalIds||['19','43'];
      const targetIndex=Math.max(0,Number(target.id.split('-').at(-1))-1);
      const dex=String(target.boss?(this.stage?.bossId||'217'):normalIds[targetIndex%normalIds.length]);
      const definition=this.stage?.definitions?.[dex];
      if(!definition)return {dex,source:null,bodyCenter:{x:target.x,y:target.y-(target.boss?43:16)},visualBounds:{left:target.x-13,right:target.x+13,top:target.y-32,bottom:target.y}};
      const recent=hits.filter(hit=>hit.targetId===target.id).at(-1),age=recent?at-recent.time:999;
      const name=age>=0&&age<.14?'hurt':'idle',animation=definition[name]||definition.idle;
      const direction=Math.min(animation.r-1,target.x<this.actorPosition(at).x?2:6);
      const durations=animation.d||Array(animation.n).fill(8);
      const total=durations.reduce((a,b)=>a+b,0);
      let frame=0,ticks=(name==='hurt'?Math.max(0,age):at)*60;
      if(name==='idle')ticks%=total;
      while(frame<animation.n-1&&ticks>=durations[frame]){ticks-=durations[frame];frame++;}
      const scale=2*(target.boss?1.25:1),bounds=animation.visualFrames[direction*animation.n+frame];
      const recoil=age>=0&&age<.16?Math.sin(age/.16*Math.PI)*(target.boss?1.2:4):0;
      const left=target.x+recoil+(bounds.left-animation.ax)*scale,right=target.x+recoil+(bounds.right-animation.ax)*scale;
      const top=target.y+(bounds.top-animation.ay)*scale,bottom=target.y+(bounds.bottom-animation.ay)*scale;
      return {dex,source:animation.sheet.src,animation:name,frame,direction,scale,recoil,flash:age>=0&&age<.035,
        visualBounds:{left,top,right,bottom},bodyCenter:{x:(left+right)/2,y:(top+bottom)/2}};
    }

    drawTargetFallback(target, s) {
      const c = this.ctx;
      const recent = s.hits.filter(h => h.targetId === target.id).at(-1);
      const age = recent ? s.time - recent.time : 999;
      const recoil = age >= 0 && age < .18 ? Math.sin(age / .18 * Math.PI) * (target.boss ? 1.5 : 7) : 0;
      const scale = target.boss ? 1.65 : 1;
      c.save(); c.translate(target.x + recoil, target.y);
      c.fillStyle = '#080f12'; c.globalAlpha = .5; c.beginPath(); c.ellipse(0, 0, 16 * scale, 5 * scale, 0, 0, TAU); c.fill();
      c.globalAlpha = target.dead ? .30 : 1;
      c.scale(scale, scale);
      c.strokeStyle = '#111c27'; c.lineWidth = 2.3;
      const flash = age < .065;
      c.fillStyle = flash ? '#f9eee0' : target.boss ? '#626184' : '#5f7f85';
      const paths = [[[-8,-25],[-12,-10],[-8,-2],[-2,-3],[0,-15],[4,-3],[11,-3],[9,-13],[8,-26]], [[-9,-27],[-14,-18],[-18,-24],[-12,-35],[8,-35],[16,-25],[13,-20],[7,-26]]];
      for (const points of paths) this.polygon(points, c.fillStyle, '#17232b');
      c.fillStyle = flash ? '#fff9ef' : '#839b9d'; c.beginPath(); c.arc(0, -43, 10, 0, TAU); c.fill(); c.stroke();
      c.fillStyle = '#182a35'; c.fillRect(-9,-44,18,7);
      c.fillStyle = target.boss ? '#e1b2d7' : '#bfd1c0'; c.fillRect(-5,-42,3,2); c.fillRect(3,-42,3,2);
      this.polygon([[-10,-34],[8,-34],[14,-30],[0,-28],[-10,-30]], '#32364e', '#202637');
      if (target.boss) {
        this.polygon([[-10,-49],[-16,-62],[-3,-53],[4,-60],[12,-49]], '#8a779b', '#23263b');
      }
      c.restore();
      const barW = target.boss ? 68 : 42, barY = target.y - (target.boss ? 98 : 61);
      c.fillStyle = '#0b151a'; c.fillRect(target.x - barW/2,barY,barW,4);
      c.fillStyle = target.boss ? '#cd8bb6' : '#c1b27d'; c.fillRect(target.x-barW/2,barY,barW*Math.max(0,target.hp/target.maxHp),4);
      if (target.outside) { c.fillStyle = '#7a9292'; c.font = '10px system-ui'; c.textAlign='center'; c.fillText('範圍外',target.x,barY-7); c.textAlign='left'; }
    }

    drawActor(s) {
      const c = this.ctx, p = s.actor;
      let visualT = s.time;
      const heavy = s.hits.find(h => (this.skill === 'flower' || this.skill === 'combo') && h.phase === 1 && s.time >= h.time && s.time < h.time + .045);
      if (heavy) visualT = heavy.time;
      const pose = this.poseAt(visualT), form = this.currentForm(), assets = this.assets[form] || this.assets.normal;
      const motion = ['willow', 'lily'].includes(this.skill) && s.time < this.duration ? Math.sin(s.time * 18) * 2 : 0;
      c.save(); c.translate(p.x + motion, p.y);
      c.fillStyle = '#071015'; c.globalAlpha = .65; c.beginPath(); c.ellipse(0, 0, 22, 6, 0, 0, TAU); c.fill(); c.globalAlpha = 1;
      const frame = assets?.frames?.[pose] || assets?.frames?.idle;
      if (this.skill === 'lily' && s.time >= .44 && s.time < .72) c.scale(-1,1);
      if (frame?.rect && assets.image) {
        const [x,y,w,h] = frame.rect;
        const anchor = frame.anchor || [w/2,h];
        const nominal = assets.bodyHeight || assets.sourceBodyHeight || assets.frames.idle?.rect?.[3] || h;
        const scale = 64 / nominal;
        c.imageSmoothingEnabled = false;
        if(frame.clipRuns?.length){
          let cached=this.frameClipCache.get(frame);
          if(!cached||cached.scale!==scale||cached.ax!==anchor[0]||cached.ay!==anchor[1]){
            const path=new Path2D();
            for(const [rx,ry,rw,rh] of frame.clipRuns){
              path.rect((rx-anchor[0])*scale,(ry-anchor[1])*scale,rw*scale,rh*scale);
            }
            cached={path,scale,ax:anchor[0],ay:anchor[1]};
            this.frameClipCache.set(frame,cached);
          }
          c.clip(cached.path);
        }
        c.drawImage(assets.image,x,y,w,h,-anchor[0]*scale,-anchor[1]*scale,w*scale,h*scale);
      } else this.proceduralActor(pose, form, visualT);
      c.restore();
      // A clear actor locator stays visible between large bone columns.
      if(this.showRange){c.save();c.strokeStyle='#394552';c.globalAlpha=.6;c.lineWidth=1.2;c.beginPath();c.arc(p.x,p.y,19,.12,Math.PI-.12);c.stroke();c.restore();}
    }

    proceduralActor(pose, form, t) {
      const c = this.ctx, cursed = form === 'curse';
      const low = ['larch','bracken','flower1','flower2'].includes(pose);
      const y = low ? 6 : Math.sin(t * 5) * .5;
      c.save(); c.translate(0,y);
      const skin = cursed ? '#9c918a' : '#f0ddd1';
      const outfit = cursed ? '#9c918a' : '#dedad5';
      if(cursed){
        c.save(); c.strokeStyle='#8e837e';c.lineWidth=8;c.lineCap='round';c.beginPath();c.moveTo(-6,-22);c.bezierCurveTo(-50,-2,-43,-42,-70,-35);c.stroke();c.strokeStyle='#d5c7ae';c.lineWidth=2;c.stroke();c.restore();
        for(let i=0;i<4;i++) this.polygon([[-8,-29-i*5],[-33-i*2,-44-i*5],[-12,-42-i*4]], '#eee2c8','#6a6669');
      }
      this.polygon([[-11,-23],[-17,-3],[-9,-2],[-2,-16],[7,-2],[16,-3],[10,-25]],'#353242','#18222d');
      this.polygon([[-17,-4],[-20,0],[-6,0],[-8,-5]],'#253d4b','#142533');
      this.polygon([[6,-4],[7,0],[21,0],[17,-5]],'#253d4b','#142533');
      this.polygon([[-10,-50],[-18,-29],[-9,-22],[12,-23],[16,-32],[10,-50]],outfit,'#26303b');
      this.polygon([[-4,-48],[1,-29],[6,-48]],skin,'#5c5459');
      c.strokeStyle='#83709d';c.lineWidth=6;c.beginPath();c.moveTo(-14,-24);c.lineTo(13,-24);c.stroke();
      c.strokeStyle='#51425f';c.lineWidth=1;c.beginPath();c.moveTo(-14,-25);c.lineTo(13,-25);c.stroke();
      const attack = ['willow1','willow2','camellia2','bullets','vine2','flower2','lily'].includes(pose);
      const hand = pose === 'bracken' ? [22,-1] : attack ? [26,-33] : [14,-34];
      c.strokeStyle='#28313d';c.lineWidth=11;c.lineCap='round';c.beginPath();c.moveTo(8,-44);c.lineTo(hand[0]-6,hand[1]);c.stroke();
      c.strokeStyle=outfit;c.lineWidth=7;c.stroke();c.fillStyle=skin;c.beginPath();c.arc(hand[0],hand[1],4.5,0,TAU);c.fill();
      c.fillStyle=skin;c.strokeStyle='#28313d';c.lineWidth=1.5;c.beginPath();c.ellipse(1,-59,12,14,0,0,TAU);c.fill();c.stroke();
      this.polygon([[-12,-57],[-15,-68],[-7,-76],[0,-73],[6,-76],[15,-69],[15,-51],[9,-57],[6,-67],[0,-70],[-6,-65],[-8,-48]],'#d7d7db','#333845');
      c.fillStyle='#57977e';c.fillRect(-3,-59,3,2);c.fillRect(7,-59,3,2);
      c.fillStyle='#a75050';c.fillRect(0,-66,2,2);c.fillRect(5,-66,2,2);
      if (this.skill==='curse' && t>.2 && t<.75) { c.strokeStyle='#333044';c.lineWidth=2;c.beginPath();c.moveTo(8,-65);c.lineTo(4,-60);c.lineTo(9,-56);c.moveTo(10,-44);c.lineTo(6,-37);c.lineTo(11,-32);c.stroke(); }
      c.restore();
    }

    drawWeapons(s) {
      const c=this.ctx,t=s.time,p=s.actor, hand={x:p.x+22,y:p.y-35};
      if (this.cancelAt != null && t > this.cancelAt) return;
      if (t > this.duration + .1) return;
      if(this.skill==='willow'){
        this.willowTimes().forEach((hit,i)=>{
          const age=t-hit;
          if(age<-.07||age>.11)return;
          const a=lerp(i%2?1:-1,i%2?-1:1,clamp((age+.07)/.18));
          this.drawSlash(hand.x,hand.y,48,a,1-clamp((age+.01)/.12));
        });
      }
      if(this.skill==='camellia' && t>=.12){
        const pulses=[.30,.43,.57].map(h=>Math.max(0,1-Math.abs(t-h)/.12));
        const ext=Math.max(...pulses);
        this.drawBone(hand.x,hand.y,hand.x+35+70*ext,hand.y-3,5);
        if(ext>.3)this.drawSlash(hand.x+25,hand.y,75,0,ext*.5);
      }
      if(this.skill==='larch'&&t>.14&&t<.88){
        const out=ease((t-.14)/.16)*(1-ease((t-.62)/.26));
        const ribs=[[-6,-36,-40,-59,6],[7,-35,48,-63,5],[-11,-26,-57,-32,7],
          [12,-27,60,-31,6],[-5,-15,-34,8,4],[8,-17,38,7,5]];
        for(const [rx,ry,tx,ty,w] of ribs){
          this.drawBone(p.x+rx,p.y+ry,p.x+lerp(rx,tx,out),p.y+lerp(ry,ty,out),w);
        }
      }
      if((this.skill==='vine'||this.skill==='combo')&&t>.12&&t<(this.skill==='combo'?1.12:.70)) this.drawVine(s,hand);
      if(this.skill==='flower'||this.skill==='combo'){
        const drill=this.drillGeometry(t);
        // The extension overlaps the source sprite's native short forearm bone.
        // It shares that exact axis and continues as one solid tapered weapon.
        if(drill?.visible)this.drawDrill(drill.base.x,drill.base.y,0,drill.length,drill.power,10,drill.angle);
      }
      if(this.skill==='lily'&&t>.10&&t<.90){
        const phase=t<.40?0:1;
        const start=phase===0?.14:.44,end=phase===0?.32:.62;
        const progress=clamp((t-start)/(end-start));
        const direction=phase===0?1:-1;
        const angle=-.8+direction*progress*TAU;
        const radius=this.radius()*ease((t-.1)/.08)*(1-ease((t-.65)/.25));
        const points=[];
        const grip={x:p.x+(phase?-20:20),y:p.y-32};
        for(let i=0;i<=34;i++){
          const q=i/34,a=angle-direction*(1-q)*2.8;
          const rad=lerp(15,radius,q);
          const curve={x:p.x+Math.cos(a)*rad,y:p.y-29+Math.sin(a)*rad};
          const emerge=ease(q/.18);
          points.push({x:lerp(grip.x,curve.x,emerge),y:lerp(grip.y,curve.y,emerge)});
        }
        this.drawWhip(points,.96);
        c.save();c.strokeStyle='#f0ecdf';c.globalAlpha=.16;c.lineWidth=4;c.beginPath();c.arc(p.x,p.y-29,radius,angle-direction*.38,angle,direction<0);c.stroke();c.restore();
      }
    }

    drawVine(s,hand){
      const t=s.time,target=s.targets[0],end=t<.42?{x:lerp(hand.x,target.x,ease((t-.12)/.30)),y:lerp(hand.y,target.y-26,ease((t-.12)/.30))}:{x:target.x,y:target.y-27};
      const points=[];
      for(let i=0;i<=26;i++){
        const q=i/26;
        points.push({x:lerp(hand.x,end.x,q),y:lerp(hand.y,end.y,q)+Math.sin(q*Math.PI)*Math.sin(t*10)*((t<.42)?33:4)});
      }
      this.drawWhip(points,1);
      if(t>=.42&&t<(this.skill==='combo'?1.12:.62)){
        const c=this.ctx;c.save();c.strokeStyle='#e7d7b8';c.lineWidth=4;c.beginPath();c.ellipse(target.x,target.y-29,15,9,-.3,0,TAU);c.stroke();c.restore();
      }
    }

    drawWhip(points,alpha){
      const c=this.ctx;c.save();c.globalAlpha=alpha;c.lineJoin='round';c.lineCap='round';
      c.strokeStyle='#303344';c.lineWidth=6.7;c.beginPath();points.forEach((p,i)=>i?c.lineTo(p.x,p.y):c.moveTo(p.x,p.y));c.stroke();
      c.strokeStyle='#eee9dc';c.lineWidth=4.3;c.stroke();
      for(let i=1;i<points.length;i+=2){
        const p=points[i],prev=points[i-1],next=points[Math.min(i+1,points.length-1)];
        const a=Math.atan2(next.y-prev.y,next.x-prev.x),q=i/(points.length-1),size=(1-q*.42)*(3.7+Math.sin(i*2.1)*.45);
        c.save();c.translate(p.x,p.y);c.rotate(a);
        // Vertebrae have paired transverse processes, a dark joint and a ridge,
        // rather than a row of identical jewellery beads.
        this.polygon([[-3.7,-size*.65],[-1.4,-size*.72],[-.3,-size*1.52],[1.2,-size*.8],[3.1,-size*.45],[3.5,size*.5],[1.1,size*.75],[.1,size*1.28],[-1.4,size*.72],[-3.6,size*.56]],i%3?'#f0eadb':'#fff6e3','#414351');
        c.strokeStyle='#fff9ed';c.lineWidth=.9;c.beginPath();c.moveTo(-1.5,-size*.62);c.lineTo(1.5,-size*.48);c.stroke();
        c.strokeStyle='#9a94a9';c.lineWidth=.8;c.beginPath();c.moveTo(2.8,-size*.3);c.lineTo(2.8,size*.35);c.stroke();
        c.restore();
      }
      c.restore();
    }

    drawDrill(x,y,offset,length,grow,baseRadius=19,angle=0){
      if(grow<=0||length<2)return;
      const c=this.ctx;c.save();c.translate(x+offset,y);c.rotate(angle);c.fillStyle='#f0ecdf';c.strokeStyle='#454258';c.lineWidth=1.4;
      const frame=this.effects?.frames?.drill2||this.effects?.frames?.drill1;
      if(frame?.rect&&this.effects?.image){
        const [sx,sy,sw,sh]=frame.rect,origin=frame.origin||[0,sh/2],tip=frame.tip||[sw,sh/2];
        const scaleX=length/Math.max(1,tip[0]-origin[0]),scaleY=baseRadius*2.25*grow/sh;
        c.imageSmoothingEnabled=false;
        c.drawImage(this.effects.image,sx,sy,sw,sh,-origin[0]*scaleX,-origin[1]*scaleY,sw*scaleX,sh*scaleY);
      }else{
        const r=baseRadius*grow;
        c.fillStyle='#ddceb0';c.strokeStyle='#685e6a';
        c.beginPath();c.moveTo(-2,-r*.8);c.bezierCurveTo(length*.25,-r*1.12,length*.67,-r*.45,length,0);c.bezierCurveTo(length*.66,r*.55,length*.20,r*1.1,-2,r*.82);c.closePath();c.fill();c.stroke();
        for(let i=0;i<8;i++){
          const q=(i/8)**1.13,xx=q*length,rr=(1-q)**.8*r,step=length/8;
          c.fillStyle=i%2?'#d1bea0':'#f2e4c5';c.strokeStyle='#8b7a80';c.lineWidth=1;
          c.beginPath();c.moveTo(xx,-rr*.93);c.bezierCurveTo(xx-step*.25,-rr*.4,xx+step*.72,rr*.4,Math.min(length,xx+step*.75),rr*.78);c.lineTo(Math.min(length,xx+step*.98),rr*.45);c.bezierCurveTo(xx+step*.45,rr*.1,xx+step*.18,-rr*.72,xx+step*.4,-rr*.88);c.closePath();c.fill();c.stroke();
        }
      }
      c.restore();
    }

    drawForest(s,back){
      const t=s.time;if(t<.30||t>1.65||this.cancelAt!=null&&t>this.cancelAt)return;
      const c=this.ctx,center=this.actorPosition(0);
      const columns=s.forestLayout.filter(col=>col.visible);
      // Ground rupture belongs below every actor, independent of pillar depth.
      if(back)for(const col of s.forestLayout){
        const age=t-col.start;
        if(age<-.10||age>.70)continue;
        const arrival=ease((age+.1)/.12),fade=1-ease((age-.30)/.40);
        c.save();c.translate(col.x,col.y);c.globalAlpha=arrival*fade*.85;
        this.polygon([[-col.width-5,2],[-8,-5],[3,-7],[col.width+5,-2],[col.width+8,3],[2,6],[-12,5]],'#111e1d','#76634e');
        const random=seeded(Math.floor(col.shapeSeed*1e8));
        for(let j=0;j<3;j++){
          const a=random()*TAU,d=col.width+6+random()*11;
          c.strokeStyle=j%2?'#4b453a':'#756149';c.lineWidth=1.2;
          c.beginPath();c.moveTo(Math.cos(a)*7,Math.sin(a)*3);
          c.lineTo(Math.cos(a+.12)*d*.65,Math.sin(a+.12)*d*.35);
          c.lineTo(Math.cos(a)*d,Math.sin(a)*d*.45);c.stroke();
        }
        c.restore();
      }
      if(back)for(const particle of this.forestParticles(s.forestLayout,t,s.hits)){
        c.save();c.globalAlpha=(1-particle.q)*(particle.kind==='rock'?.85:.22);
        if(particle.kind==='rock'){
          const x=particle.x,y=particle.y,k=particle.size;
          this.polygon([[x-k,y],[x,y-k],[x+k*1.3,y+1],[x+1,y+k]],'#89745a','#2c352d');
        }else{
          c.fillStyle='#99886d';c.beginPath();c.ellipse(particle.x,particle.y,particle.size,particle.size*.45,0,0,TAU);c.fill();
        }
        c.restore();
      }
      for(const col of columns){
        if((col.y<center.y)!==back)continue;
        const age=t-col.start;
        c.save();c.translate(col.x,col.y);
        const columnAlpha=col.opacity*(1-ease((t-1.22)/.30));
        c.globalAlpha=columnAlpha*.28;
        c.fillStyle='#071414';c.beginPath();c.ellipse(0,2,col.width+5,4.5,col.lean,0,TAU);c.fill();
        c.globalAlpha=columnAlpha;
        c.rotate(col.lean);
        const frame=this.effects?.frames?.[`pillar${col.variant}`];
        if(frame?.rect&&this.effects?.image){
          const [x,y,w,h]=frame.rect,anchor=frame.anchor||[w/2,h];
          const width=col.width*2.3,height=col.height;
          c.imageSmoothingEnabled=false;
          c.drawImage(this.effects.image,x,y,w,h,-anchor[0]/w*width,-anchor[1]/h*height,width,height);
        }else{
          // Sculpted fallback remains rooted and irregular while atlas loads.
          const h=col.height,w=col.width;
          this.polygon([[-w,0],[-w*.72,-h*.24],[-w*.95,-h*.33],[-w*.44,-h*.63],[-w*.55,-h*.70],[w*.15,-h],[w*.45,-h*.62],[w*.9,-h*.30],[w,0]],'#ded0b5','#635d66');
          this.polygon([[w*.15,-h],[w*.15,-h*.42],[w,0],[w*.9,-h*.30],[w*.45,-h*.62]],'#a99c98',null);
        }
        c.restore();
      }
    }

    drawProjectiles(s){
      const c=this.ctx;
      for(const projectile of s.projectiles){
        if(s.time<projectile.release||s.time>=projectile.hitTime)continue;
        const q=clamp((s.time-projectile.release)/(projectile.hitTime-projectile.release));
        const x=lerp(projectile.source.x,projectile.end.x,q),y=lerp(projectile.source.y,projectile.end.y,q),a=Math.atan2(projectile.end.y-projectile.source.y,projectile.end.x-projectile.source.x);
        c.save();c.translate(x,y);c.rotate(a);
        c.strokeStyle='#d9cab2';c.globalAlpha=.34;c.lineWidth=2;c.beginPath();c.moveTo(-18,0);c.lineTo(-5,0);c.stroke();c.globalAlpha=1;
        this.polygon([[-6,-2],[-3,-3],[3,-2.6],[9,-1.2],[11,0],[7,1.8],[-2,2.5],[-6,1.5]],'#f2ecdf','#3d4053');
        this.polygon([[-2,0],[8,.2],[4,1.6],[-3,1.8]],'#a5a0b2',null);
        c.strokeStyle='#fff9ee';c.lineWidth=.8;c.beginPath();c.moveTo(-2,-1.8);c.lineTo(5,-1.2);c.stroke();
        c.restore();
      }
    }

    drawImpacts(s){
      const c=this.ctx;
      for(const particle of this.impactParticles(s.hits,s.time)){
        c.save();c.translate(particle.x,particle.y);c.rotate(particle.a+particle.q*2);c.globalAlpha=1-particle.q;
        const k=particle.size;
        this.polygon([[-k,-k*.6],[k*.8,-k*.8],[k*.45,k],[-k*.6,k*.5]],particle.color,'#827581');
        c.restore();
      }
      const newest=new Map();
      for(const hit of s.hits){
        const age=s.time-hit.time;if(age>=0&&age<=.30)newest.set(hit.targetId,hit);
      }
      const labels=[...newest.values()].sort((a,b)=>a.x-b.x);
      for(const [lane,hit] of labels.entries()){
        const age=s.time-hit.time,q=age/.30,heavy=['flower','combo','bracken'].includes(this.skill);
        const target=s.targets.find(e=>e.id===hit.targetId);
        const rendered=target?this.targetRenderInfo(target,s.time,s.hits):null;
        const point=rendered?.bodyCenter||{x:hit.x,y:hit.y-24};
        c.save();c.globalAlpha=1-q;
        if(age<.055){
          const k=(1-age/.055)*(heavy?5:3),x=point.x,y=point.y;
          this.polygon([[x-k,y-1],[x-2,y-3],[x+4,y-k],[x+2,y-1],[x+k,y+2],[x+1,y+3],[x-4,y+k],[x-2,y+1]],'#fff9e9','#343548');
        }
        const x=point.x+(lane-(labels.length-1)/2)*16;
        const y=(rendered?.visualBounds?.top??hit.y-34)-8-q*16-(lane%2)*9;
        c.font=`700 ${heavy?13:11}px system-ui, sans-serif`;c.textAlign='center';c.fillStyle='#fff9e9';c.strokeStyle='#292d3d';c.lineWidth=2.5;
        const label=Number.isInteger(hit.damage)?String(hit.damage):hit.damage.toFixed(1);
        c.strokeText(label,x,y);c.fillText(label,x,y);c.restore();
      }
    }

    drawLabels(s){
      if(!this.showRange)return;
      const c=this.ctx;
      c.fillStyle='#0a151bdc';c.fillRect(18,503,864,40);c.fillStyle='#dce1d7';c.font='13px system-ui, sans-serif';c.fillText(s.phase,33,528);
      c.textAlign='right';c.fillStyle='#93aaa3';c.fillText(`${s.hits.length} 次接觸  ·  ${Number(s.totalDamage.toFixed(1))} 基礎傷害`,866,528);c.textAlign='left';
      if(this.scenario==='boss'){c.fillStyle='#bd9abb';c.font='11px system-ui';c.fillText('首領：可受骨林傷害・不被拉動',27,80);}
      if(s.cancelled){c.fillStyle='#e2bd8b';c.font='12px system-ui';c.fillText('已取消後續出手',27,100);}
    }

    drawSlash(x,y,r,a,alpha){
      const c=this.ctx;c.save();c.translate(x,y);c.rotate(a);c.globalAlpha=clamp(alpha);
      c.fillStyle='#f5e8ca';c.beginPath();c.moveTo(r*.76,-r*.55);c.bezierCurveTo(r*1.05,-r*.30,r*1.02,r*.27,r*.72,r*.52);c.bezierCurveTo(r*.93,r*.20,r*.94,-r*.25,r*.76,-r*.55);c.fill();
      c.globalAlpha*=.42;c.strokeStyle='#b5a5a0';c.lineWidth=1;c.beginPath();c.bezierCurveTo(r*.82,-r*.45,r*1.03,.05*r,r*.79,r*.47);c.stroke();c.restore();
    }
    drawBone(x1,y1,x2,y2,width){
      const c=this.ctx,a=Math.atan2(y2-y1,x2-x1),d=Math.hypot(x2-x1,y2-y1);c.save();c.translate(x1,y1);c.rotate(a);
      this.polygon([[-2,-width*.45],[d*.12,-width*.62],[d*.42,-width*.43],[d*.72,-width*.32],[d,0],[d*.77,width*.25],[d*.46,width*.37],[d*.1,width*.5],[-2,width*.35]],'#efe9dd','#3d4053');
      this.polygon([[d*.08,0],[d*.65,-width*.03],[d,0],[d*.46,width*.37],[d*.1,width*.5]],'#a29cac',null);
      c.strokeStyle='#fff9ed';c.lineWidth=.8;c.beginPath();c.moveTo(d*.12,-width*.43);c.lineTo(d*.67,-width*.22);c.stroke();
      if(d>20){c.strokeStyle='#aaa2ad';c.lineWidth=.7;c.beginPath();c.moveTo(d*.26,-width*.5);c.lineTo(d*.22,0);c.moveTo(d*.56,-width*.35);c.lineTo(d*.52,width*.1);c.stroke();}
      c.restore();
    }
    polygon(points,fill,stroke){
      const c=this.ctx;c.beginPath();points.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));c.closePath();if(fill){c.fillStyle=fill;c.fill();}if(stroke){c.strokeStyle=stroke;c.stroke();}
    }
  }
  KimimaroScene.logicalSize = { width: 900, height: 560 };
  KimimaroScene.frameKeys = [...frameKeys];
  window.KimimaroScene = KimimaroScene;
})();
