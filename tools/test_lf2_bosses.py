"""Production-entry verification for classic Firzen and Julian.

Controlled geometry/lifecycle fixtures and native high-level visual clips are
separate from fresh Lv1 progression, which uses only real UI and input.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art-review/lf2-bosses/qa'
BASE = os.environ.get('LF2_BOSSES_URL', 'http://127.0.0.1:8767/.omx/digimon.html')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
HEROES = {'firzen': {'dex': 30019, 'api': 'LF2Firzen'}, 'julian': {'dex': 30020, 'api': 'LF2Julian'}}


def hashes():
    names = ['.omx/lf2-bosses.js', '.omx/lf2-boss-art.js', '.omx/lf2-firzen-combat.js',
             '.omx/lf2-julian-combat.js', '.omx/naruto.js', '.omx/digimon.html',
             'js/entities/enemy.js', 'js/systems/combat.js', 'js/systems/self-clone.js', 'js/systems/hazards.js']
    for hero in HEROES:
        folder = ROOT / 'assets/lf2' / hero
        if folder.exists(): names.extend(p.relative_to(ROOT).as_posix() for p in folder.rglob('*') if p.is_file())
    result={}
    for name in names:
        path=ROOT/name
        if not path.is_file(): continue
        payload=path.read_bytes();digest=hashlib.sha256(payload).hexdigest();result[name]=digest
        if path.suffix in {'.js','.html'}:
            snapshot=OUT/'source-snapshots'/digest/path.name
            snapshot.parent.mkdir(parents=True,exist_ok=True)
            if not snapshot.exists(): snapshot.write_bytes(payload)
    return result


def boot(page, hero, label):
    spec = HEROES[hero]
    url = BASE + ('&' if '?' in BASE else '?') + 'lang=zh-TW&hero=' + hero
    if not label.startswith('mobile'): url += '&layout=wide'
    page.goto(url)
    try:
        page.wait_for_function("api=>window.G?.[api]&&G.LF2BossArt&&document.getElementById('boot').classList.contains('hidden')", arg=spec['api'], timeout=60000)
    except Exception:
        page.screenshot(path=str(OUT/f'{hero}-{label}-boot-failure.png'))
        (OUT/f'{hero}-{label}-boot-failure.html').write_text(page.content(),'utf-8')
        raise
    if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
    page.locator(f'[data-quick-naruto="{spec["dex"]}"]').click()
    page.wait_for_function('dex=>G.NarutoAssets.ready(dex)', arg=spec['dex'], timeout=30000)
    page.screenshot(path=str(OUT/f'{hero}-{label}-selection.png'))
    page.locator('#scr-menu [data-go="play"]').click()
    page.wait_for_function('dex=>G.Game.player?.dex===dex&&G.Game.state==="playing"', arg=spec['dex'])
    page.screenshot(path=str(OUT/f'{hero}-{label}-normal-entry.png'))


SETUP = r'''({api,dex}) => {
 const assert=(ok,msg)=>{if(!ok)throw Error(msg)},p=()=>G.Game.player,F=G[api];
 const ids=G.LF2Bosses.idsFor(dex),world=G.World,nativeAxis=G.Input.axis;
 function pause(){if(G.Game.state==='playing')G.Game.togglePause();G.UI.hide('scr-pause')}
 function resume(){if(G.Game.state==='paused')G.Game.togglePause();assert(G.Game.state==='playing','not playing '+G.Game.state)}
 function reset(){G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();G.SelfClones?.clear();G.Pickups.clear();
  G.World=world;G.Input.axis=nativeAxis;G.Hazards.clear();G.World.collide=()=>{};G.World.isWall=()=>false;G.World.isFree=()=>true;G.World.isLiquid=()=>false;
  G.World.projectileBlock=()=>false;G.World.propsInCircle=()=>[];
  const a=p();a.x=a.y=0;a.hp=a.maxHp;a.dead=false;a.frozen=false;a.flash=0;a.invuln=0;
  a.target=null;a.aim=0;a.attackFace=0;a.walking=false;a.critChance=0;a.item=null;a._vx=a._vy=0;
  a.percentHealthDamage=a.lifestealRate=a.damageSplashPicks=a.quantityPicks=a.quantityBonus=0;a.statsTaken={};
  a.cdMul=1;a.xp=0;a.xpNext=1e12;G.Camera.x=G.Camera.y=0;for(const m of a.moves)m.t=999;pause();}
 function spawn(x,y,boss=false){const e=new G.Enemy({dex:19,hp:1000000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1},boss);
  e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e}
 function watch(e){const hits=[],hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);hits.push({raw:args[0],loss:hp-this.hp,owner:args[6]===p(),id:args[7]});return result};return hits}
 function fixture(id,rank=1){const a=p();F.clear(a);a.level=30;a.moves=[G.Moves.instance(id,rank)];a.arrange();const m=a.moves[0];m.t=0;return m}
 function step(dt=.01,tick=false){resume();try{if(tick)G.Combat.tick(dt,p(),0);p().anim.update(dt);G.Combat.updateFields(dt)}finally{pause()}}
 function advance(seconds,tick=false){let left=seconds;while(left>1e-9){const dt=Math.min(.01,left);step(dt,tick);left-=dt}}
 function cast(m){resume();try{assert(F.cast(p(),m),'cast rejected '+m.id)}finally{pause()}}
 const input=(x,y)=>{G.Input.axis=()=>[x,y]};
 window.BAcceptance={assert,p,F,ids,dex,pause,resume,reset,spawn,watch,fixture,step,advance,cast,input};pause();
}'''

PROGRESSION = r'''() => {
 const A=BAcceptance,p=A.p(),ids=A.ids,out={offers:[],growth:[]};
 A.assert(p.level===1&&p.moves.length===1&&p.moves[0].id===ids[0],'wrong fresh Lv1 starter');
 const mon=p.mon,levels=[...new Set([1,2,...ids.flatMap(id=>[G.Moves.BY_ID[id].learnLevel-1,G.Moves.BY_ID[id].learnLevel])])].filter(n=>n>0).sort((a,b)=>a-b);
 for(const level of levels){p.level=level;const pool=G.Moves.poolFor(p.mon),cards=G.LevelUp.offer(p,100);
  for(const id of ids)A.assert(pool.includes(id)===(level>=G.Moves.BY_ID[id].learnLevel),'pool gate '+id+' at '+level);
  for(const id of ids.slice(1))A.assert(cards.some(c=>c.key==='new:'+id)===(level>=G.Moves.BY_ID[id].learnLevel),'card gate '+id+' at '+level);
  out.offers.push({level,pool,cards:cards.map(c=>c.key)});
 }
 p.level=30;for(const id of ids.slice(1)){const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'learn card failed '+id)}
 A.assert(ids.every(id=>p.hasMove(id)),'kit failed learning');
 for(const dex of [30001,30006,30014,30017,30018,30019,30020].filter(d=>d!==A.dex)){
  p.mon=G.DEX_BY[dex];A.assert(!G.Moves.poolFor(p.mon).some(id=>ids.includes(id)),'pool leaked to '+dex)
 }p.mon=mon;
 for(const id of ids){A.reset();const m=A.fixture(id),before=A.F.profile(p,m);p.quantityPicks=p.quantityBonus=3;const after=A.F.profile(p,m);out.growth.push({id,before,after});}
 return out;
}'''

# Per-move geometry cases are added after reading the original-data contract,
# rather than changing test expectations to fit a candidate implementation.
MECHANICS = r'''() => {
 const A=BAcceptance,p=A.p,F=A.F,out={};
 for(const id of A.ids.filter(id=>G.Moves.BY_ID[id].dmg>0)){A.reset();const m=A.fixture(id),profile=F.profile(p(),m);A.assert(profile&&profile.damage>0,'missing combat profile '+id);
  const distance=/cannon|skull|julian-ball/.test(id)?Math.min(250,profile.range*.5):Math.min(50,profile.range*.5);
  const e=A.spawn(distance,0),hits=A.watch(e);if(id==='lf2-julian-punch')A.input(1,0);A.cast(m);A.advance(8);
  A.assert(hits.some(h=>h.loss>0),'move never caused native damage '+id);A.assert(hits.every(h=>h.owner&&h.id===id),'damage attribution '+id);out[id]={profile,hits};
 }
 return out;
}'''

JULIAN_IDENTITY = r'''() => {
 const A=BAcceptance,p=A.p,F=A.F,out={};
 A.reset();let m=A.fixture('lf2-julian-skull'),e=A.spawn(300,0),hits=A.watch(e);A.cast(m);
 A.advance(.12);A.assert(!F.stateFor(p()).effects.length&&!hits.length,'skulls emitted before source261');
 A.advance(.04);A.assert(F.stateFor(p()).effects.filter(x=>x.kind==='skull').length===1&&!hits.length,'first skull/source startup timing differs');
 A.advance(3);A.assert(hits.length===5&&hits.every(h=>h.owner&&h.id===m.id),'source5 seeking skulls did not independently contact');out.skulls=hits;
 A.reset();m=A.fixture('lf2-julian-skull');e=A.spawn(300,0);hits=A.watch(e);A.cast(m);G.World.isWall=(x,y)=>x>=120&&x<=140;A.advance(4);
 A.assert(!hits.length,'skulls crossed solid wall');out.skullWall=true;
 A.reset();m=A.fixture('lf2-julian-ball');const inside=[[180,0],[320,0],[470,0]].map(([x,y])=>A.spawn(x,y)),outside=A.spawn(320,250),hs=inside.map(A.watch),ho=A.watch(outside);A.cast(m);A.advance(3);
 A.assert(hs.every(h=>h.length===1)&&!ho.length,'SoulBomb true penetration/3in1out differs');out.sphere={hits:hs,outside:ho};
 A.reset();m=A.fixture('lf2-julian-ball');e=A.spawn(320,0);hits=A.watch(e);A.cast(m);A.advance(.42);A.assert(!hits.length,'sphere teleported damage at release');
 G.World.isWall=(x,y)=>x>=150&&x<=165;A.advance(3);A.assert(!hits.length,'sphere or impact crossed wall');out.sphereDelayWall=true;
 A.reset();m=A.fixture('lf2-julian-blast');const ring=[[55,0],[-55,20],[0,-75]].map(([x,y])=>A.spawn(x,y)),far=A.spawn(170,0),rh=ring.map(A.watch),fh=A.watch(far);A.cast(m);A.advance(.39);
 A.assert(rh.every(h=>!h.length),'BigBang hit before source318 release');A.advance(.03);A.assert(rh.every(h=>h.length===1)&&!fh.length,'BigBang actual radial3in1out');A.advance(2);
 A.assert(rh.every(h=>h.length===1),'BigBang visual fade repeated damage');out.bigBang={hits:rh,outside:fh};
 A.reset();m=A.fixture('lf2-julian-blast');e=A.spawn(80,0);hits=A.watch(e);A.cast(m);G.World.isWall=(x,y)=>x>=30&&x<=40;A.advance(2);A.assert(!hits.length,'radial blast crossed wall');out.blastWall=true;
 A.reset();m=A.fixture('lf2-julian-blast');const edge=F.profile(p(),m).radius;e=A.spawn(edge,0);hits=A.watch(e);A.cast(m);A.advance(2);A.assert(hits.length===1,'BigBang misses advertised edge');out.blastEdge={edge,hits};
 A.reset();m=A.fixture('lf2-julian-uppercut');e=A.spawn(40,0);hits=A.watch(e);A.cast(m);A.advance(.05);A.assert(!hits.length,'uppercut before source86');A.advance(.04);A.assert(hits.length===1,'uppercut missing first active phase');
 A.advance(.7);A.assert(hits.length===1,'uppercut same victim repeated in same chain');out.uppercut=hits;
 A.reset();m=A.fixture('lf2-julian-skull');m.t=999;e=A.spawn(40,0);hits=A.watch(e);A.step(.01,true);A.assert(F.pose(p()).kind==='punch','stationary fallback not ordinary punch');A.advance(.08);A.assert(!hits.length,'ordinary punch before source61 active');A.advance(.04);A.assert(hits.length===1,'ordinary punch missing');out.punch=hits;
 A.reset();m=A.fixture('lf2-julian-skull');m.t=999;e=A.spawn(45,0);A.input(1,0);A.step(.01,true);
 A.assert(F.pose(p()).kind==='punch'&&!F.stats(p()).casts['lf2-julian-punch'],'unlearned SoulPunch was supplied free');out.noFreeSoulPunch=true;
 A.reset();m=A.fixture('lf2-julian-punch');e=A.spawn(60,0);hits=A.watch(e);A.input(1,0);A.cast(m);A.advance(.1);
 A.assert(hits.length===1&&p().x>0&&p().x<=30.0001&&F.pose(p()).sourceStart===300,'formal SoulPunch original hit/run budget missing');const pos=p().x;A.advance(.3);
 A.assert(p().x===pos&&hits.length===1,'SoulPunch boost continued after original first2ticks');out.soulPunch={hits,moved:pos};
 A.reset();m=A.fixture('lf2-julian-punch');A.spawn(45,0);A.input(-1,0);A.resume();try{A.assert(!F.canCast(p(),m),'retreat intent started formal SoulPunch')}finally{A.pause()};A.assert(p().x===0,'retreat changed owner position');out.retreat=true;
 A.reset();m=A.fixture('lf2-julian-punch');e=A.spawn(40,0);hits=A.watch(e);p().quantityPicks=p().quantityBonus=4;A.input(1,0);A.cast(m);A.advance(.1);A.input(-1,0);A.advance(1.2);
 A.assert(hits.length===1&&p().x<=30.0001,'retreat failed to stop repeated SoulPunch or pursuit');out.retreatRepeats=hits;
 A.reset();m=A.fixture('lf2-julian-punch');A.spawn(60,0);A.input(1,0);G.World.isFree=(x,y)=>x<=10;A.cast(m);A.advance(.3);A.assert(p().x<=10,'SoulPunch boost crossed blocking geometry');out.runWall=p().x;
 return out;
}'''

FIRZEN_IDENTITY = r'''() => {
 const A=BAcceptance,p=A.p,F=A.F,out={};
 A.reset();let m=A.fixture('lf2-firzen-cannon'),e=A.spawn(300,0),hits=A.watch(e);A.cast(m);A.advance(.5);A.assert(!hits.length,'cannon became instant beam');A.advance(3);
 A.assert(hits.length===4,'cannon initial/following bullets missing');A.assert(Math.abs(hits[1].raw/hits[0].raw-.32)<1e-6,'held stream lost firstshot/continuation damage distinction');out.cannon=hits;
 A.reset();m=A.fixture('lf2-firzen-cannon');const line=[[180,0],[300,0],[420,0]].map(([x,y])=>A.spawn(x,y)),outside=A.spawn(300,180),hs=line.map(A.watch),ho=A.watch(outside);A.cast(m);A.advance(3);
 A.assert(hs.every(h=>h.length===4)&&!ho.length,'cannon traveling stream3in1out');out.cannonLine={hits:hs,outside:ho};
 A.reset();m=A.fixture('lf2-firzen-cannon');e=A.spawn(300,0);hits=A.watch(e);A.cast(m);G.World.isWall=(x,y)=>x>=120&&x<=140;A.advance(3);A.assert(!hits.length,'cannon crossed wall');out.cannonWall=true;
 A.reset();m=A.fixture('lf2-firzen-cannon');A.spawn(300,0);A.cast(m);A.advance(.4);const first=F.stateFor(p()).effects.find(e=>e.kind==='cannon'),firstY=first.y;p().y=200;A.spawn(300,200);A.advance(.35);
 A.assert(first.y===firstY&&F.stateFor(p()).effects.some(e=>e.kind==='cannon'&&e.y>100),'released projectile dragged or later socket failed to follow owner');out.movingSource={firstY,newY:F.stateFor(p()).effects.filter(e=>e.kind==='cannon').map(e=>e.y)};
 A.reset();m=A.fixture('lf2-firzen-disaster');e=A.spawn(160,0);hits=A.watch(e);A.cast(m);A.advance(.42);A.assert(!hits.length&&F.stateFor(p()).effects.some(e=>e.kind==='chase'&&e.phase==='rise'),'disaster skipped rise before real chase');
 for(let i=0;i<60&&!F.stopped(e);i++)A.advance(.05);A.assert(F.stopped(e),'real ice seeker never froze');
 const x=e.x,y=e.y;e.spd=80;e.dmg=30;e.touchCd=0;A.resume();try{e.update(.2,p(),0)}finally{A.pause()};A.assert(e.x===x&&e.y===y,'ice lease did not stop native AI');
 p().x=e.x;p().y=e.y;p().invuln=p().flash=0;e.touchCd=0;G.EnemyMgr.rebuildGrid();const hp=p().hp;A.resume();try{G.Combat.resolve(.01,p(),0)}finally{A.pause()};A.assert(p().hp===hp,'frozen Firzen victim still hurt by contact');out.freeze={hits,status:F.freezeStatus(e)};
 A.reset();m=A.fixture('lf2-firzen-volcano');const inside=[[25,0],[-25,0],[0,35]].map(([x,y])=>A.spawn(x,y)),far=A.spawn(1200,0),ih=inside.map(A.watch),fh=A.watch(far);A.cast(m);A.advance(.6);
 A.assert(ih.every(h=>!h.length),'eruption fire109 hurt before110 active');A.advance(.06);A.assert(ih.every(h=>h.length>0)&&!fh.length,'central eruption true area3in1out');A.advance(4);A.assert(!fh.length,'eruption/seekers exceeded full reach');out.volcano={hits:ih,outside:fh};
 A.reset();m=A.fixture('lf2-firzen-cannon');m.t=999;e=A.spawn(40,0);hits=A.watch(e);A.advance(.3,true);A.assert(hits.length>0&&F.stats(p()).casts['lf2-firzen-punch']>0,'empty-hand fallback missing');out.punch=hits;
 return out;
}'''

CONTACT_BOUNDARY = r'''() => {
 const A=BAcceptance,p=A.p,F=A.F,id=A.ids.at(-1),out={sameWave:[],props:[],clone:null};
 for(const reason of ['clear','unlearn','world']){
  A.reset();const m=A.fixture(id),first=A.spawn(25,-3),second=A.spawn(25,3),h1=A.watch(first),h2=A.watch(second),world=G.World,hurt=first.hurt;
  first.hurt=function(...args){const result=hurt.apply(this,args);if(reason==='clear')G.Combat.clearFields(p());if(reason==='unlearn')p().moves=[];if(reason==='world')G.World={...world};return result};
  A.cast(m);try{A.advance(6)}finally{G.World=world}
  A.assert(h1.length===1&&!h2.length,'samewave callback cancellation failed '+reason);out.sameWave.push({reason,first:h1,second:h2});
 }
 for(const id of A.ids.filter(id=>G.Moves.BY_ID[id].dmg>0)){
  A.reset();const m=A.fixture(id),prop={x:40,y:0,r:12,hp:100000,destructible:true},damage=G.World.damageProp,calls=[];
  G.World.propsInCircle=(x,y,r)=>prop.hp>0&&Math.hypot(prop.x-x,prop.y-y)<=r+prop.r?[prop]:[];
  G.World.projectileBlock=(x,y,r)=>prop.hp>0&&Math.hypot(prop.x-x,prop.y-y)<=prop.r+r?prop:false;
  G.World.damageProp=(target,amount)=>{A.assert(target===prop,'wrong prop');calls.push(amount);prop.hp-=amount};
  try{if(id==='lf2-julian-punch')A.input(1,0);A.cast(m);A.advance(8)}finally{G.World.damageProp=damage}
  A.assert(calls.length>0,'no-enemy destructible unsupported '+id);out.props.push({id,calls});
 }
 A.reset();const m=A.fixture(id),enemy=A.spawn(30,0),events=[],native=enemy.hurt,clone=G.SelfClones.summon(p());
 A.assert(clone&&clone.moves!==p().moves,'clone has shared move state');clone.x=clone.y=0;const cm=clone.moves.find(move=>move.id===id);cm.t=0;
 enemy.hurt=function(...args){events.push({ownerMain:args[6]===p(),ownerClone:args[6]===clone,id:args[7]});return native.apply(this,args)};
 A.resume();try{A.assert(F.cast(clone,cm),'clone cast rejected')}finally{A.pause()};F.clear(p());A.advance(.8);
 A.assert(events.length&&events.every(e=>e.ownerClone&&!e.ownerMain&&e.id===id),'clone attribution/owner clear isolation');
 const n=events.length;clone.dead=true;A.advance(8);A.assert(events.length===n,'dead clone retained damage');out.clone=events;
 return out;
}'''

MIRROR_UTILITY = r'''() => {
 const A=BAcceptance,p=A.p,F=A.F,out={phases:[],lifecycle:[]},id='lf2-julian-mirror';
 const mine=()=>F.decoys().filter(d=>d.owner===p());
 function start(time=.8){A.reset();const m=A.fixture(id),e=A.spawn(100,0);A.cast(m);A.advance(time);return {m,e};}
 function ranged(e){e.behavior='ranged';e.spd=0;e.dmg=25;e.def={...e.def,dmg:25,shotDmg:25,range:500,shotCd:10};e.shotCd=0;e.touchCd=99;return e;}
 function enemyUpdate(e,dt=.01){A.resume();try{e.update(dt,p())}finally{A.pause()}}
 function resolve(){A.resume();try{G.Combat.resolve(.01,p(),0)}finally{A.pause()}}
 function projectiles(seconds){for(let i=0;i<Math.ceil(seconds/.01);i++){A.resume();try{G.Projectiles.update(.01,p(),G.EnemyMgr.all());G.Combat.resolve(.01,p(),0);F.update(.01)}finally{A.pause()}}}
 // Every threat is a native enemy attack against the real, current body point.
 for(const time of [0,.06,.10,.45])for(const kind of ['contact','projectile','hazard']){
  const {e}=start(time);let exempt;A.resume();try{exempt=F.collisionExempt(p())}finally{A.pause()};const expected=time>=2/30&&time<13/30;
  A.assert(exempt===expected,'Mirror collision phase boundary '+time);e.x=p().x;e.y=p().y;e.dmg=25;e.def={...e.def,dmg:25,shotDmg:25};e.touchCd=0;G.EnemyMgr.rebuildGrid();p().invuln=p().flash=0;
  const hp=p().hp;
  if(kind==='projectile'){e.touchCd=99;e.shoot(1,0);resolve();A.assert(G.Projectiles.all().length===(expected?1:0),'Mirror consumed or retained hostile bullet incorrectly '+time);}
  else if(kind==='hazard'){G.Hazards.add({kind:'zone',x:p().x,y:p().y,r:30,delay:0,dmg:25,type:'normal',color:'#a0f'});A.resume();try{G.Hazards.update(.01)}finally{A.pause()}}
  else{resolve();A.assert(expected?e.touchCd===0:e.touchCd>0,'Mirror consumed enemy contact cooldown '+time);}
  A.assert(expected?p().hp===hp:p().hp<hp,'Mirror native '+kind+' wrong at '+time);out.phases.push({time,kind,exempt,loss:hp-p().hp});
 }
 // The source body remains invisible even if an earlier hit flash still exists.
 start(.10);p().flash=.09;const frame=G.LF2BossArt.sample(30020,'hurt',.1,0,F.pose(p()));A.assert(frame.id===103,'Hurt replaced original invisible source103');
 const canvas=document.createElement('canvas');canvas.width=canvas.height=256;const ctx=canvas.getContext('2d');G.LF2BossArt.draw(ctx,p(),{state:'hurt',pose:F.pose(p()),x:128,y:180,flash:true});
 A.assert(!ctx.getImageData(0,0,256,256).data.some((n,i)=>i%4===3&&n),'source103 rendered body pixels during flash');out.source103Invisible=true;
 // Native terrain damage and timed status still run during the exact body gap.
 start(.10);const effect=G.World.liquidEffect;G.World.isLiquid=()=>true;G.World.liquidEffect=()=>({dmg:.1,flat:7,every:.5});p().lavaTick=0;p().invuln=0;p().slowT=1;const hp=p().hp;
 A.resume();try{p().update(.01)}finally{A.pause();G.World.liquidEffect=effect}A.assert(p().hp<hp&&p().slowT<1,'Mirror granted terrain/status immunity');out.terrainStatus={loss:hp-p().hp,slowT:p().slowT};
 // Real native chase and aim use the old phantom, which never becomes solid.
 let {e}=start(.8),d=mine()[0];A.assert(d&&d.intangible&&d.life===59/30,'original stationary phantom missing/lifetime');const old=[d.x,d.y];
 e.x=d.x+70;e.y=d.y+50;e.spd=60;e.flying=true;enemyUpdate(e,.1);A.assert(e._lf2MirrorTarget===d&&Math.hypot(e.x-d.x,e.y-d.y)<Math.hypot(70,50),'native enemy failed to chase phantom');
 A.advance(.2);A.assert(d.x===old[0]&&d.y===old[1],'phantom followed moving real owner');out.chase={target:d.id,enemyXY:[e.x,e.y],phantom:old};
 ({e}=start(.8));d=mine()[0];e.x=60;e.y=80;ranged(e);const ownerXY=[p().x,p().y];enemyUpdate(e);
 const shot=G.Projectiles.all().find(b=>!b.friendly);A.assert(shot&&e._lf2MirrorTarget===d,'native ranged AI did not shoot at phantom');
 const a=Math.atan2(shot.vy,shot.vx),wanted=Math.atan2(d.y-e.y,d.x-e.x),real=Math.atan2(p().y-e.y,p().x-e.x);
 A.assert(Math.abs(Math.atan2(Math.sin(a-wanted),Math.cos(a-wanted)))<.001&&Math.abs(a-real)>.1,'native ranged aim did not differ from real body');
 const activeHP=p().hp;projectiles(.55);A.assert(G.Projectiles.all().includes(shot),'phantom physically absorbed a bullet');projectiles(.85);A.assert(p().hp===activeHP,'shot aimed at old phantom still hit displaced real body');
 A.assert(d.hp===10,'nonphysical phantom lost physical health');
 A.reset();A.fixture('lf2-julian-skull');p().x=ownerXY[0];p().y=ownerXY[1];e=A.spawn(60,80);ranged(e);const baseHP=p().hp;enemyUpdate(e);projectiles(1.4);
 A.assert(p().hp<baseHP,'same encounter without Mirror did not threaten real body');out.realDefense={withMirrorLoss:0,withoutMirrorLoss:baseHP-p().hp,aim:a,realAim:real,passedPhantom:true};
 // A real player behind a phantom remains hittable after source103 ends.
 ({e}=start(.8));d=mine()[0];p().x=d.x-30;p().y=d.y;e.x=d.x+50;e.y=d.y;ranged(e);const behindHP=p().hp;enemyUpdate(e);projectiles(.8);
 A.assert(p().hp<behindHP&&d.hp===10,'phantom blocked a real hit behind it');out.noShield={loss:behindHP-p().hp};
 ({e}=start(.8));d=mine()[0];e.x=d.x+30;e.y=d.y+30;enemyUpdate(e);A.assert(e._lf2MirrorTarget===d,'retarget fixture failed');A.advance(1.4);enemyUpdate(e);A.assert(!e._lf2MirrorTarget&&!mine().length,'expired phantom retained enemy target');out.expiryRetarget=true;
 ({e}=start(.8));d=mine()[0];e.x=d.x+80;e.y=d.y;G.World.isWall=(x,y)=>x>d.x+30&&x<d.x+40;enemyUpdate(e);A.assert(!e._lf2MirrorTarget,'phantom lured enemy through a wall');out.lureWall=true;
 // Real movement direction can steer the short original evade and it respects walls.
 A.reset();let m=A.fixture(id);A.spawn(100,0);A.input(0,1);A.cast(m);A.advance(.3);A.assert(p().y>0&&Math.abs(p().x)<.001,'Mirror overrode perpendicular/flee input');A.input(-1,0);A.advance(.12);A.assert(p().x<0,'Mirror ignored changed retreat direction');out.flee={x:p().x,y:p().y};
 A.reset();m=A.fixture(id);A.spawn(100,0);A.input(1,0);A.cast(m);A.advance(.4);A.assert(p().x>0&&Math.abs(p().y)<.001,'Mirror reversed forward player input');out.forward=p().x;
 A.reset();m=A.fixture(id);A.spawn(100,0);G.World.isFree=(x,y)=>x>=-20;A.cast(m);A.advance(.5);A.assert(p().x>=-20,'Mirror crossed blocking geometry');out.evadeWall=p().x;
 for(const reason of ['pause','clear','death','unlearn','world','epoch']){
  ({e}=start(.2));const world=G.World,initial=mine().map(d=>({id:d.id,age:d.age,x:d.x,y:d.y}));A.assert(initial.length,'lifecycle phantom not created');
  if(reason==='pause'){F.update(8);A.assert(JSON.stringify(mine().map(d=>({id:d.id,age:d.age,x:d.x,y:d.y})))===JSON.stringify(initial),'pause advanced phantom');}
  else{if(reason==='clear')G.Combat.clearFields(p());if(reason==='death')p().dead=true;if(reason==='unlearn')p().moves=[];if(reason==='world')G.World={...world};if(reason==='epoch')G.CombatPulse.beginRun();
   A.resume();try{F.update(.01)}finally{A.pause()};A.assert(!F.decoys().length&&!F.collisionExempt(p()),'cancel retained phantom or body exclusion '+reason);}
  G.World=world;p().dead=false;out.lifecycle.push({reason,ok:true});
 }
 A.reset();m=A.fixture(id);A.spawn(100,0);const clone=G.SelfClones.summon(p());clone.x=clone.y=0;const cm=clone.moves.find(m=>m.id===id);cm.t=0;
 A.resume();try{A.assert(F.cast(clone,cm),'clone Mirror cast rejected')}finally{A.pause()};A.advance(.1);F.clear(p());A.resume();try{A.assert(F.decoys().some(d=>d.owner===clone)&&F.collisionExempt(clone)&&!F.collisionExempt(p()),'Mirror actor ownership mixed')}finally{A.pause()};
 clone.dead=true;A.advance(.01);A.assert(!F.decoys().length&&!F.collisionExempt(clone),'dead clone retained ghost/exemption');out.cloneIsolation=true;
 return out;
}'''

SHARED_TARGET_REGRESSION = r'''() => {
 const A=BAcceptance,p=A.p,F=A.F,out=[];A.assert(A.dex===30019,'shared regression expects Firzen');
 for(const kind of ['contact','projectile','hazard']){
  A.reset();const e=A.spawn(0,0);e.dmg=25;e.def={...e.def,dmg:25,shotDmg:25};e.touchCd=0;G.EnemyMgr.rebuildGrid();
  A.resume();try{
   e.update(.01,p());A.assert(!e._lf2MirrorTarget&&!G.LF2Julian.collisionExempt(p()),'Julian Mirror modified unrelated Firzen');
   const hp=p().hp;
   if(kind==='projectile'){e.touchCd=99;e.shoot(1,0);G.Combat.resolve(.01,p(),0)}
   else if(kind==='hazard'){G.Hazards.add({kind:'zone',x:0,y:0,r:40,delay:0,dmg:25,type:'normal',color:'#a0f'});G.Hazards.update(.01)}
   else G.Combat.resolve(.01,p(),0);
   A.assert(p().hp<hp,'native '+kind+' stopped threatening unrelated Firzen');out.push({kind,loss:hp-p().hp});
  }finally{A.pause()}
 }
 A.reset();const m=A.fixture('lf2-firzen-disaster'),e=A.spawn(160,0);A.cast(m);
 for(let i=0;i<80&&!F.stopped(e);i++)A.advance(.05);A.assert(F.stopped(e),'shared target patch broke actual Firzen ice contact');
 const xy=[e.x,e.y];e.spd=80;e.dmg=25;e.touchCd=0;A.resume();try{e.update(.1,p())}finally{A.pause()};A.assert(e.x===xy[0]&&e.y===xy[1],'native stopped enemy resumed moving');
 p().x=e.x;p().y=e.y;p().invuln=0;e.touchCd=0;G.EnemyMgr.rebuildGrid();const hp=p().hp;A.resume();try{G.Combat.resolve(.01,p(),0)}finally{A.pause()};A.assert(p().hp===hp,'frozen enemy regained contact damage');out.push({firzenFreeze:true});
 return out;
}'''

LIFECYCLE = r'''() => {
 const A=BAcceptance,p=A.p,F=A.F,out=[];
 for(const id of A.ids)for(const reason of ['pause','clear','death','unlearn','world','epoch']){
  A.reset();const m=A.fixture(id),enemy=A.spawn(50,0),hits=A.watch(enemy);if(id==='lf2-julian-punch')A.input(1,0);A.cast(m);const world=G.World;
  if(reason==='pause'){F.update(8);A.assert(!hits.length,'pause advanced damage '+id);out.push({id,reason,hits});continue}
  if(reason==='clear')G.Combat.clearFields(p());if(reason==='death')p().dead=true;if(reason==='unlearn')p().moves=[];
  if(reason==='world')G.World={...world};if(reason==='epoch')G.CombatPulse.beginRun();
  try{A.advance(8)}finally{G.World=world;p().dead=false}
  A.assert(!hits.length,'cancelled move damaged '+id+'/'+reason);out.push({id,reason,hits});
 }
 return out;
}'''

GROWTH = r'''() => {
 const A=BAcceptance,p=A.p(),F=A.F,out=[];
 for(const id of A.ids){
  A.reset();const m=A.fixture(id),before=F.profile(p,m),picks=[];
  for(let i=0;i<4;i++){
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');
   if(!card){A.assert(i>0&&F.profile(p,m).count>before.count,'quantity card missing before any effective investment '+id);break;}
   A.assert(card.apply(p)!==false,'real quantity card failed '+id);picks.push(card.desc);
  }
  const after=F.profile(p,m);
  A.assert(Number.isFinite(before.count)&&Number.isFinite(after.count)&&after.count>before.count,'quantity has no real count consumer '+id);
  const first=G.Moves.instance(id,1),last=G.Moves.instance(id,5),rank1=F.profile(p,first),rank5=F.profile(p,last);
  A.assert(rank5.damage>rank1.damage||rank5.count>rank1.count||rank5.range>rank1.range||rank5.radius>rank1.radius,'rank progression has no real consumer '+id);
  p.quantityPicks=p.quantityBonus=20;const capped=F.profile(p,m);
  A.assert(capped.count===F.specs[id].cap,'quantity cap differs '+id);
  A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='stat:quantity'),'dead quantity offer after actual consumer cap '+id);
  out.push({id,before,after,rank1,rank5,picks,capped});
 }
 if(A.dex===30020){
  A.reset();const m=A.fixture('lf2-julian-uppercut'),before=F.profile(p,m),saved={scale:p.anim.scale,r:p.r,bodyH:p.bodyH,maxHp:p.maxHp,hp:p.hp,spdMul:p.spdMul,cdMul:p.cdMul,giantPicks:p.giantPicks};
  const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:giant');A.assert(card,'real giant card absent');
  try{
   A.assert(card.apply(p)!==false,'giant card rejected');const after=F.profile(p,m),e=A.spawn(before.range+13,0),hits=A.watch(e);
   A.assert(after.range>before.range&&p.anim.scale>saved.scale,'giant body and melee reach did not grow');A.cast(m);A.advance(.4);
   A.assert(hits.length===1,'giant uppercut missed actual extended arm reach');out.push({giant:true,before,after,hits});
  }finally{Object.assign(p,saved);p.anim.scale=saved.scale;delete p.scale;A.reset()}
 }
 return out;
}'''

OBSERVE = r'''({api,dex}) => {
 const F=G[api],ids=G.LF2Bosses.idsFor(dex),damageIds=ids.filter(id=>G.Moves.BY_ID[id].dmg>0),Q=window.BossNatural={ledger:[],offers:[],offer:null,inputs:[],hits:[],samples:[],frames:[],utility:[],hud:null};let last=-1;const seen=new Set(),utilitySeen=new Set();
 Q.snapshot=()=>{const p=G.Game.player;return p?{time:G.Game.st.time,level:p.level,hp:p.hp,maxHp:p.maxHp,dead:!!p.dead,x:p.x,y:p.y,moves:p.moves.map(m=>({id:m.id,rank:m.lvl})),stats:F.stats(p)}:null};
 Q.ids=ids;Q.damageIds=damageIds;Q.activeLast=()=>{const s=F.stateFor(G.Game.player),id=ids.at(-1);return !!(s?.action?.m?.id===id||s?.effects?.some(e=>(e.action?.m?.id||e.m?.id||e.id)===id&&!e.dead))};
 Q.activeMirror=()=>!!(F.stateFor(G.Game.player)?.action?.m?.id==='lf2-julian-mirror'||F.decoys?.(G.Game.player)?.length);
 Q.mirrorUseful=()=>!ids.includes('lf2-julian-mirror')||(F.stats(G.Game.player)?.mirrorRedirects>0&&Q.utility.some(e=>e.kind==='native-target'||e.kind==='native-aim'));
 const show=G.RunUI.showLevelUp;G.RunUI.showLevelUp=function(level,list,cb,...args){const offer={serial:Q.offers.length+1,time:G.Game.st.time,level,options:list.map(c=>({key:c.key,type:c.type,title:c.title,desc:c.desc}))};Q.offers.push(offer);Q.offer=offer;return show.call(this,level,list,c=>{const before=Q.snapshot();cb(c);Q.ledger.push({time:G.Game.st.time,level,key:c.key,before,after:Q.snapshot()});Q.offer=null},...args)};
 const hurt=G.Enemy.prototype.hurt;G.Enemy.prototype.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);if(args[6]===G.Game.player&&ids.includes(args[7]))Q.hits.push({time:G.Game.st.time,id:args[7],loss:hp-this.hp,target:this.id});return result};
 const enemyUpdate=G.Enemy.prototype.update;G.Enemy.prototype.update=function(...args){const result=enemyUpdate.apply(this,args),target=this._lf2MirrorTarget;if(F.isDecoy?.(target)){const key='target:'+this.id+':'+target.id;if(!utilitySeen.has(key)){utilitySeen.add(key);Q.utility.push({kind:'native-target',time:G.Game.st.time,enemy:this.id,target:target.id,enemyXY:[this.x,this.y],targetXY:[target.x,target.y],ownerXY:[G.Game.player.x,G.Game.player.y]});}}return result};
 const shoot=G.Enemy.prototype.shoot;G.Enemy.prototype.shoot=function(...args){const result=shoot.apply(this,args),target=this._lf2MirrorTarget;if(F.isDecoy?.(target))Q.utility.push({kind:'native-aim',time:G.Game.st.time,enemy:this.id,target:target.id,direction:args.slice(0,2),ownerXY:[G.Game.player.x,G.Game.player.y]});return result};
 const hud=G.HUD.draw;G.HUD.draw=function(ctx,w,h,...args){const icons=G.Icons.draw;Q.hud={width:w,height:h,items:[]};G.Icons.draw=function(c,id,x,y,size,...rest){if(typeof id==='string'&&id.startsWith('move:')&&ids.includes(id.slice(5)))Q.hud.items.push({id:id.slice(5),x,y,size});return icons.call(this,c,id,x,y,size,...rest)};try{return hud.call(this,ctx,w,h,...args)}finally{G.Icons.draw=icons}};
 const draw=G.Combat.drawAirFields;G.Combat.drawAirFields=function(ctx){const result=draw.call(this,ctx),p=G.Game.player,s=p&&F.stateFor(p),pose=s?.action,keys=[];
  if(pose)keys.push((pose.kind||pose.mode)+'-'+pose.phase);
  if(F.collisionExempt?.(p))keys.push('mirror-body-evasion');
  const decoys=F.decoys?.(p)||[];
  for(const d of decoys){if(d.age>=.1)keys.push('mirror-decoy-visible');if(d.life-d.age<=.15)keys.push('mirror-decoy-fade');}
  if(decoys.some(d=>d.age<26/30&&Math.hypot(p.x-d.x,p.y-d.y)>30)&&(!pose||pose.mode!=='lf2-julian-mirror'||pose.sourceAge>=13/30))keys.push('mirror-reappeared-with-decoy');
  for(const e of s?.effects||[]){if(e.age>=.3&&e.age<e.life-.2)keys.push(e.kind+'-independent');if(e.age>=e.life-.15)keys.push(e.kind+'-fade');}
  for(const key of keys)if(!seen.has(key)){seen.add(key);const snapshot=Q.snapshot(),state={key,snapshot,pose:pose?{mode:pose.mode,kind:pose.kind,phase:pose.phase,age:pose.age,aim:pose.aim}:null,effects:(s?.effects||[]).map(e=>({kind:e.kind,age:e.age,life:e.life,x:e.x,y:e.y,radius:e.radius}))};queueMicrotask(()=>Q.frames.push({...state,png:ctx.canvas.toDataURL()}));}
  return result;
 };
 function sample(){if(G.Game.state==='playing'){const s=Q.snapshot();if(s&&s.time-last>=1){last=s.time;Q.samples.push(s)}}requestAnimationFrame(sample)}requestAnimationFrame(sample);
}'''


def context_for(browser, folder=None, mobile=False):
    viewport = {'width':390,'height':844} if mobile else {'width':1100,'height':850}
    opts = dict(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
    if folder:
        opts.update(record_video_dir=str(folder/'raw'), record_video_size=viewport)
    return browser.new_context(**opts)


def observe_errors(page, report):
    page.on('pageerror',lambda e:report['errors'].append(e.stack or str(e)))
    page.on('requestfailed',lambda request:report.setdefault('failedRequests',[]).append({'url':request.url,'failure':request.failure}))
    page.on('response',lambda response:report.setdefault('httpErrors',[]).append({'url':response.url,'status':response.status}) if response.status>=400 else None)


def controlled(browser, report, hero, shared_only=False):
    context=context_for(browser);page=context.new_page()
    observe_errors(page,report)
    boot(page,hero,'desktop');page.evaluate(SETUP,HEROES[hero])
    checks=[('progression',PROGRESSION),('mechanics',MECHANICS),('identity',FIRZEN_IDENTITY if hero=='firzen' else JULIAN_IDENTITY),('growth',GROWTH),('lifecycle',LIFECYCLE),('contactBoundary',CONTACT_BOUNDARY)]
    if hero=='julian':checks.append(('mirrorUtility',MIRROR_UTILITY))
    if shared_only:checks=[('sharedNativeTargetRegression',SHARED_TARGET_REGRESSION)]
    for name,check in checks:
        report['checks'][name]=page.evaluate(check);print(hero,name,'PASS',flush=True)
    context.close()


def save_frames(folder, frames):
    result=[]
    for frame in frames:
        png=frame.pop('png');name=frame['key']+'.png'
        (folder/name).write_bytes(base64.b64decode(png.split(',',1)[1]))
        result.append({'image':name,**frame})
    return result


def natural(browser, report, hero, mobile=False):
    label='mobile390' if mobile else 'desktop';folder=OUT/hero/f'natural-{label}'
    folder.mkdir(parents=True,exist_ok=True)
    context=context_for(browser,folder,mobile);page=context.new_page()
    observe_errors(page,report)
    boot(page,hero,label);page.evaluate(OBSERVE,HEROES[hero])
    record={'policy':'Fresh save; native Lv1/HP/XP/AI/time; visible cards/items and '+('native touch joystick only.' if mobile else 'native keyboard only.'),
            'initial':page.evaluate('BossNatural.snapshot()'),'permanent':page.evaluate('dex=>G.DB.upgradesOf(dex)',HEROES[hero]['dex'])}
    assert record['initial']['level']==1 and not any(record['permanent'].values())
    ids=page.evaluate('BossNatural.ids');damage_ids=page.evaluate('BossNatural.damageIds');started=time.monotonic();held=None;serial=None;last=-30;completed_at=None
    client=context.new_cdp_session(page) if mobile else None;touch_active=False
    while time.monotonic()-started<420:
        data=page.evaluate('({state:G.Game.state,snapshot:BossNatural.snapshot(),offer:BossNatural.offer,hitIds:[...new Set(BossNatural.hits.filter(h=>h.loss>0).map(h=>h.id))],activeLast:BossNatural.activeLast(),activeMirror:BossNatural.activeMirror(),mirrorUseful:BossNatural.mirrorUseful()})')
        snap=data['snapshot'];now=snap['time']
        useful=all(id in data['hitIds'] for id in damage_ids) and data['mirrorUseful'] and all(id in [m['id'] for m in snap['moves']] for id in ids)
        if completed_at is None and useful:completed_at=now
        if completed_at is not None and now>=completed_at+8 and not data['activeLast'] and not data['activeMirror']:break
        if snap['dead'] or data['state']=='over':break
        if now-last>=30:print(hero,label,'natural',round(now),'Lv',snap['level'],'HP',round(snap['hp']),flush=True);last=now
        if data['state']=='levelup' and data['offer'] and data['offer']['serial']!=serial:
            if held:
                if mobile:client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});touch_active=False
                else:page.keyboard.up(held)
                held=None
            offer=data['offer']
            def priority(card):
                key=card['key']
                if key.startswith('new:') and key[4:] in ids:return 0
                if key=='up:'+ids[0]:return 1
                if key=='stat:atk':return 2
                if key.startswith('up:') and key[3:] in ids:return 3
                if key=='stat:quantity':return 4
                if key=='stat:cd':return 5
                return 9
            selected=min(range(len(offer['options'])),key=lambda i:(priority(offer['options'][i]),i))
            page.screenshot(path=str(folder/f'card-{offer["serial"]}-Lv{offer["level"]}.png'))
            page.locator('#cards .card').nth(selected).click();serial=offer['serial']
        elif page.locator('#scr-item').is_visible():page.locator('#item-cards .card').first.click()
        elif page.locator('#scr-bond').is_visible():page.locator('#bond-cards .card').first.click()
        elif data['state']=='paused':page.locator('#btn-resume').click()
        elif data['state']=='playing':
            key=['KeyD','KeyS','KeyA','KeyW'][int(now//1.4)%4]
            if key!=held:
                if mobile:
                    if touch_active:client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                    point=page.evaluate('G.Touch.stickBase()');dx,dy={'KeyD':(36,0),'KeyS':(0,36),'KeyA':(-36,0),'KeyW':(0,-36)}[key]
                    client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]})
                    client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':point['x']+dx,'y':point['y']+dy}]});touch_active=True
                else:
                    if held:page.keyboard.up(held)
                    page.keyboard.down(key)
                held=key;page.evaluate('event=>BossNatural.inputs.push(event)',{'time':now,'key':key,'input':'touch' if mobile else 'keyboard'})
        page.wait_for_timeout(65)
    if held:
        if mobile:client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        else:page.keyboard.up(held)
    page.screenshot(path=str(folder/'final.png'))
    record.update(page.evaluate('({ledger:BossNatural.ledger,offers:BossNatural.offers,inputs:BossNatural.inputs,hits:BossNatural.hits,utility:BossNatural.utility,hud:BossNatural.hud,samples:BossNatural.samples,final:BossNatural.snapshot(),state:G.Game.state})'))
    record['frames']=save_frames(folder,page.evaluate('BossNatural.frames'))
    record['allSpecialsHit']=all(any(h['id']==id and h['loss']>0 for h in record['hits']) for id in damage_ids)
    record['allSkillsLearned']=all(id in [m['id'] for m in record['final']['moves']] for id in ids)
    record['mirrorUseful']=data['mirrorUseful']
    record['allSpecialsFirstHitAt']=completed_at
    record['fullSignatureClosed']=completed_at is not None and record['final']['time']>=completed_at+8 and not data['activeLast'] and not data['activeMirror']
    video=page.video;context.close();video.save_as(str(folder/'native-growth.webm'));video.delete()
    (folder/'report.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf-8');report['natural'][label]=record
    assert record['allSpecialsHit'] and record['allSkillsLearned'] and record['mirrorUseful'] and record['fullSignatureClosed'],f'Natural run did not complete all offensive/utility skills and signature closure: {record["final"]}'
    hud=record['hud'];assert {x['id'] for x in hud['items']}==set(ids),'HUD omitted learned formal skill'
    assert all(x['x']>=0 and x['y']>=0 and x['x']+x['size']<=hud['width'] and x['y']+x['size']<=hud['height'] for x in hud['items']),'HUD skill icon outside actual canvas'


def final_clip(browser, report, hero):
    folder=OUT/hero/'final-cycles';folder.mkdir(parents=True,exist_ok=True)
    context=context_for(browser,folder);page=context.new_page()
    observe_errors(page,report)
    boot(page,hero,'final-cycles');page.evaluate(SETUP,HEROES[hero])
    page.evaluate(r'''() => {const A=BAcceptance;A.reset();const p=A.p();p.level=30;p.moves=A.ids.map(id=>G.Moves.instance(id,1));p.arrange();for(const m of p.moves)m.t=0;A.spawn(350,0);window.FinalCycleStart=G.Game.st.time;}''')
    page.evaluate(OBSERVE,HEROES[hero]);page.evaluate('BAcceptance.resume()')
    page.wait_for_function('G.Game.st.time-FinalCycleStart>=1.7',timeout=10000)
    page.evaluate('for(const [x,y] of [[45,0],[125,20],[225,-20],[-40,0],[0,45],[0,-45],[90,80],[-90,-80]])BAcceptance.spawn(x,y)')
    held=None
    while page.evaluate('G.Game.st.time-FinalCycleStart')<36:
        scene=page.evaluate('''() => {const p=G.Game.player,F=BAcceptance.F,e=G.EnemyMgr.all().filter(e=>!e.dead).sort((a,b)=>Math.hypot(a.x-p.x,a.y-p.y)-Math.hypot(b.x-p.x,b.y-p.y))[0];return {mode:F.pose(p)?.mode,dx:e?e.x-p.x:0,dy:e?e.y-p.y:0}}''')
        key=None if scene['mode'] in ['lf2-julian-blast','lf2-julian-uppercut'] else ('KeyD' if scene['dx']>=0 else 'KeyA') if abs(scene['dx'])>=abs(scene['dy']) else ('KeyS' if scene['dy']>=0 else 'KeyW')
        if key!=held:
            if held:page.keyboard.up(held)
            if key:page.keyboard.down(key)
            held=key
        page.wait_for_timeout(65)
    if held:page.keyboard.up(held)
    data=page.evaluate('({frames:BossNatural.frames,stats:BAcceptance.F.stats(G.Game.player),hits:BossNatural.hits,utility:BossNatural.utility,hud:BossNatural.hud,time:G.Game.st.time-FinalCycleStart,ids:BossNatural.ids,damageIds:BossNatural.damageIds,mirrorUseful:BossNatural.mirrorUseful()})')
    data['scope']='Controlled Lv30/rank1 kit; isolated zero-damage high-HP targets; real keyboard movement/native RAF, no manual combat-clock stepping. Separate from natural growth.'
    data['frames']=save_frames(folder,data['frames'])
    data['missingOffensiveHits']=[id for id in data['damageIds'] if not any(h['id']==id and h['loss']>0 for h in data['hits'])]
    video=page.video;context.close();video.save_as(str(folder/'native-cycles.webm'));video.delete()
    report['finalCycles']=data;(folder/'report.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')
    assert not data['missingOffensiveHits'],'showcase omitted offensive skill damage: '+','.join(data['missingOffensiveHits'])
    assert data['mirrorUseful'],'showcase omitted actual Mirror target diversion'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--hero',choices=list(HEROES),required=True)
    parser.add_argument('--natural',action='store_true');parser.add_argument('--mobile',action='store_true');parser.add_argument('--final-cycles',action='store_true');parser.add_argument('--shared-target-regression',action='store_true')
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    report={'hero':args.hero,'url':BASE,'errors':[],'checks':{},'natural':{},'sourceBefore':hashes()}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            if args.final_cycles:final_clip(browser,report,args.hero)
            elif args.natural:natural(browser,report,args.hero,args.mobile)
            else:controlled(browser,report,args.hero,args.shared_target_regression)
            browser.close()
        assert not report['errors'],report['errors'];report['ok']=True
    except Exception as error:
        report['failure']=str(error);raise
    finally:
        report['sourceAfter']=hashes();report['sourceStable']=report['sourceBefore']==report['sourceAfter']
        report['changedPaths']=[name for name in set(report['sourceBefore'])|set(report['sourceAfter']) if report['sourceBefore'].get(name)!=report['sourceAfter'].get(name)]
        suffix='shared-target-regression' if args.shared_target_regression else 'final-cycles-source' if args.final_cycles else 'natural-mobile-report' if args.natural and args.mobile else 'natural-report' if args.natural else 'report'
        (OUT/f'{args.hero}-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')


if __name__=='__main__':main()
