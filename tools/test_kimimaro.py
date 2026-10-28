"""Kimimaro acceptance through the normal game picker and native combat.

No standalone preview or replacement combat renderer is used. After proving a
normal start and actual input, explicit fixtures open terrain to measure native
casts, damage, cards, ownership and cleanup without procedural obstructions.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('KIMIMARO_OUT', str(ROOT/'.omx/state/kimimaro-game')))
URL = os.environ.get('KIMIMARO_URL', 'http://127.0.0.1:8341/.omx/digimon.html?lang=zh-TW&test=kimimaro')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
REPORT = OUT/os.environ.get('KIMIMARO_REPORT_NAME', 'report-focused.json' if os.environ.get('KIMIMARO_CHECKS') else 'report.json')


def runtime_hashes():
    paths=['.omx/digimon.html','.omx/naruto.js','.omx/naruto-skills.js','.omx/naruto-training.js',
           '.omx/naruto-kimimaro.js','.omx/digimon-skill-combat.js','.omx/redrawn-init.js',
           'art-review/kimimaro-art.js','art-review/kimimaro-frames.json','js/ui/hud.js','js/systems/self-clone.js',
           '.omx/naruto/portraits/kimimaro.png']
    metadata=json.loads((ROOT/'art-review/kimimaro-frames.json').read_text(encoding='utf8'))
    paths.extend('art-review/'+sheet['source'] for sheet in metadata['sheets'].values())
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}


def asset_inventory():
    metadata=json.loads((ROOT/'art-review/kimimaro-frames.json').read_text(encoding='utf8'))
    result={'sheets':{},'decodedBytes':0}
    required={'frontIdle','backIdle','frontRun','backRun','hurt1','hurt2','death1','death2'}
    for name,sheet in metadata['sheets'].items():
        path=ROOT/'art-review'/sheet['source']
        image=Image.open(path).convert('RGBA')
        assert image.size==(sheet['width'],sheet['height'])
        assert image.getextrema()[3][0]==0, (name,'missing real transparency')
        for key,frame in sheet['frames'].items():
            x,y,w,h=frame['rect'];ax,ay=frame['anchor']
            assert w>0 and h>0 and 0<=x<=image.width-w and 0<=y<=image.height-h,(name,key)
            assert 0<=ax<=w and 0<=ay<=h,(name,key,'invalid foot anchor')
            assert image.crop((x,y,x+w,y+h)).getbbox(),(name,key,'empty physical frame')
        if name in ('normal','curse'):
            assert required<=set(sheet['frames']),(name,'missing authored common poses')
            assert len(sheet['frames'])>=24
        result['decodedBytes']+=image.width*image.height*4
        result['sheets'][name]={'source':sheet['source'],'size':image.size,'frames':len(sheet['frames']),
            'transferBytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    assert result['decodedBytes']<=4*1024*1024,'runtime body/effect atlas budget exceeded'
    return result

SETUP = r"""() => {
 const p=()=>G.Game.player,K=G.NarutoKimimaro;
 const assert=(ok,msg)=>{if(!ok)throw Error(msg)};
 const near=(a,b,msg)=>assert(Math.abs(a-b)<1e-7*Math.max(1,Math.abs(b)),msg+' '+a+' != '+b);
 assert(K&&G.KimimaroArt?.loaded,'playable Kimimaro combat/art not loaded');
 function pause(){if(G.Game.state==='playing')G.Game.togglePause();G.UI.hide('scr-pause')}
 function resume(){if(G.Game.state==='paused')G.Game.togglePause();assert(G.Game.state==='playing','not playing '+G.Game.state)}
 const nativeWorld={collide:G.World.collide,isWall:G.World.isWall,isFree:G.World.isFree,isLiquid:G.World.isLiquid,
   projectileBlock:G.World.projectileBlock,propsInCircle:G.World.propsInCircle};
 function reset(){
   G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();
   G.SelfClones?.clear();G.NarutoClones?.clear();G.Pickups.clear();
   G.World.collide=()=>{};G.World.isWall=()=>false;G.World.isFree=()=>true;G.World.isLiquid=()=>false;
   G.World.projectileBlock=()=>false;G.World.propsInCircle=()=>[];
   const a=p();a.mon=G.DEX_BY[30012];a.x=a.y=0;a.hp=a.maxHp;a.dead=false;a.frozen=false;a.flash=0;a.invuln=0;
   a.attackFace=0;a.walking=false;a.target=null;a.aim=0;a.critChance=0;a.item=null;
   a.percentHealthDamage=a.lifestealRate=a.damageSplashPicks=a.quantityPicks=a.quantityBonus=0;
   a.cdMul=1;a.atk=1;a.xp=0;a.xpNext=1e12;a.anim.once=false;a.anim.done=false;
   G.Camera.x=G.Camera.y=0;for(const move of a.moves)move.t=999;pause();
 }
 function spawn(x,y,special=null){
   const e=new G.Enemy({dex:19,hp:1000000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1},special==='boss');
   e.types=['normal'];if(special)e[special]=true;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;
 }
 function watch(e){const events=[],hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);
   events.push({raw:args[0],loss:hp-this.hp,owner:args[6]===p(),id:args[7],x:this.x,y:this.y});return result};return events}
 function fixture(id,rank=1){
   const a=p();G.Combat.clearFields(a);a.level=30;a.moves=[];a.slots=[];a.active=0;a.maxMoves=5;a.bind={};
   if(!a.hasMove(id))assert(a.addMove(id),'cannot learn fixture '+id);
   const m=a.moves.find(m=>m.id===id);Object.assign(m,G.Moves.instance(id,rank));a.arrange();
   const slot=a.slots.findIndex(group=>group.includes(m));if(slot>=0)a.setActive(slot);
   for(const move of a.moves)move.t=move===m?0:999;return m;
 }
 function cast(id,actor=p()){
   const m=actor.moves.find(m=>m.id===id);assert(m,'unlearned '+id);
   const slot=actor.slots.findIndex(group=>group.includes(m));if(slot>=0)actor.setActive(slot);
   for(const move of actor.moves)move.t=move===m?0:999;
   // Respect the real .10s switch/merge exit pose instead of bypassing it.
   advance(.11);
   let calls=0;const original=actor.cast;actor.cast=function(move,...args){if(move.id===id)calls++;return original.call(this,move,...args)};
   resume();try{G.Combat.tick(.001,actor,0)}finally{actor.cast=original;pause()}
   assert(calls===1,'native Combat.tick cast '+id+' count '+calls);return m;
 }
 function step(dt=.01,tick=false){resume();try{
   if(tick)G.Combat.tick(dt,p(),0);
   p().anim.update(dt);G.Projectiles.update(dt,p(),G.EnemyMgr.all());G.Combat.resolve(dt,p(),0);G.Combat.updateFields(dt);
 }finally{pause()}}
 function advance(seconds,tick=false){let left=seconds;while(left>1e-9){const dt=Math.min(.01,left);step(dt,tick);left-=dt}}
 function pose(actor=p()){
   const c=document.createElement('canvas');c.width=340;c.height=270;const ctx=c.getContext('2d',{willReadFrequently:true});
   const calls=[],draw=ctx.drawImage.bind(ctx);ctx.drawImage=(image,...rect)=>{calls.push({source:image.src||image.dataset?.source||'',rect});return draw(image,...rect)};
   actor.anim.draw(ctx,170,210);
   const alpha=ctx.getImageData(0,0,c.width,c.height).data;let n=0;
   for(let i=3;i<alpha.length;i+=4)if(alpha[i]>30)n++;
   assert(n>80&&calls.length,'empty actual game actor');
   assert(calls.every(call=>/kimimaro/i.test(call.source)),'wrong/fallback character art '+JSON.stringify(calls));
   return {calls,pixels:n,png:c.toDataURL(),animation:actor.anim.cur};
 }
 function action(){return K.activeFor(p())}
 function fields(){const c=document.createElement('canvas');c.width=860;c.height=560;const ctx=c.getContext('2d'),sources=[],draw=ctx.drawImage.bind(ctx);
   ctx.drawImage=(image,...args)=>{sources.push(image.src||image.dataset?.source||'');return draw(image,...args)};
   ctx.translate(330,370);G.Combat.drawGroundFields(ctx);p().draw(ctx);G.Combat.drawAirFields(ctx);
   return {sources,png:c.toDataURL()}}
 function summarize(){const a=action();return a?{kind:a.kind,age:a.age,phase:a.phase,aim:a.aim,castId:a.castId}:null}
 function expected(m,share=1,e={types:['normal']}){
   const normal=m.dmg*share*p().atk*G.Types.mult(m.type,e.types)*G.Weather.mult(m.type);
   return Math.max(1,Math.round(Math.max(normal,Math.ceil((e.maxHp||0)*(m.minMaxHpFraction||0)))));
 }
 window.KAcceptance={p,K,assert,near,pause,resume,reset,spawn,watch,fixture,cast,step,advance,pose,fields,action,summarize,expected,nativeWorld};pause();
}"""

PROGRESSION = r"""() => {
 const A=KAcceptance,p=A.p(),out={levels:[],ranks:[],learn:[]};
 A.assert(p.dex===30012&&p.moves.length===1&&p.moves[0].id==='naruto-kimimaro','fresh starter contains unexpected skills');
 A.assert(p.moves[0].passive&&p.slots.length===0,'willow must start without an active slot');
 const gates={camellia:3,bullets:3,larch:6,vine:6,'bone-guard':6,flower:9,lily:9,bracken:12,curse:15};
 for(const level of [1,2,3,5,6,8,9,11,12,14,15]){
   p.level=level;const pool=G.Moves.poolFor(p.mon),cards=G.LevelUp.offer(p,100);
   for(const [key,unlock] of Object.entries(gates)){const id='naruto-kimimaro-'+key,eligible=level>=unlock;
     A.assert(pool.includes(id)===eligible,'pool gate '+key+' Lv'+level);
     A.assert(cards.some(c=>c.key==='new:'+id)===eligible,'card gate '+key+' Lv'+level)}
   out.levels.push({level,pool,cards:cards.map(c=>c.key)});
 }
 const stats=[['naruto-kimimaro',[30,36,42,51,60],.9],['camellia',[120,144,168,204,240],5],
  ['bullets',[45,54,63,76.5,90],2.4],['larch',[96,115.2,134.4,163.2,192],6],
  ['vine',[48,57.6,67.2,81.6,96],8],['flower',[192,230.4,268.8,326.4,384],8],
  ['lily',[100,120,140,170,200],6],['bracken',[600,720,840,1020,1200],12]];
 for(const [key,damage,cd] of stats){const id=key==='naruto-kimimaro'?key:'naruto-kimimaro-'+key;
   for(let rank=1;rank<=5;rank++){const move=G.Moves.instance(id,rank);A.near(move.dmg,damage[rank-1],'five-rank damage '+id+' '+rank);A.near(move.cd,cd,'fixed CD '+id);out.ranks.push({id,rank,dmg:move.dmg,cd:move.cd})}}
 const mon=p.mon;for(const dex of [30001,30007,30011,20001]){
   p.mon=G.DEX_BY[dex]||{dex,gen:10,types:['normal']};A.assert(!G.Moves.poolFor(p.mon).some(id=>id.startsWith('naruto-kimimaro')),'Kimimaro pool leaked '+dex)
 }p.mon=mon;
 for(const [key,unlock] of Object.entries(gates)){
   A.reset();p.level=unlock;p.moves=[G.Moves.instance('naruto-kimimaro')];p.slots=[];p.active=0;p.bind={};p.maxMoves=5;p.arrange();
   const id='naruto-kimimaro-'+key,card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
   A.assert(card&&card.apply(p)!==false,'native learn card '+id);
   A.assert(p.hasMove(id)&&p.moves.find(m=>m.id===id).passive&&p.slots.length===0,'slot cost '+id);out.learn.push({id,slots:p.slots.length});
 }
 // Learning a passive leaves an existing full common-tool slot untouched.
 A.reset();p.level=30;p.moves=[G.Moves.instance('naruto-kimimaro')];p.slots=[];p.bind={};p.maxMoves=1;p.arrange();
 A.assert(p.addMove('naruto-kunai'),'replacement fixture common tool');const old=p.moves.find(m=>m.id==='naruto-kunai'),group=p.slots[0];p.bind[old.id]=0;
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-kimimaro-camellia');
 A.assert(card&&card.apply(p)!==false,'slotless learning unavailable with full common-tool slots');
 A.assert(p.slots[0]===group&&group.includes(old)&&old.id==='naruto-kunai'&&p.bind[old.id]===0,'learning changed common-tool group or binding');
 A.assert(p.hasMove('naruto-kimimaro-camellia')&&!p.slots.flat().some(m=>m.id==='naruto-kimimaro-camellia'),'learned Camellia consumed a slot');
 p.maxMoves=5;out.fullSlotLearning=true;return out;
}"""

COMBAT = r"""() => {
 const A=KAcceptance,p=A.p(),out={};
 const fixtures=[
  ['naruto-kimimaro',[[50,0],[350,250]],4,[.25,.25,.25,.25]],
  ['camellia',[[60,-10],[90,0],[110,10],[350,250]],3,[.25,.25,.5]],
  ['larch',[[55,-20],[60,0],[50,25],[350,250]],2,[.5,.5]],
  ['vine',[[150,0],[350,250]],1,[1]],
  ['flower',[[90,0],[105,-15],[115,15],[350,250]],1,[1]],
  ['lily',[[65,-35],[-55,40],[90,25],[350,250]],2,[.5,.5]],
  ['bracken',[[35,-20],[95,30],[-145,30],[350,250]],1,[1]]];
 for(const [key,positions,count,shares] of fixtures){
   const id=key==='naruto-kimimaro'?key:'naruto-kimimaro-'+key;A.reset();const move=A.fixture(id);
   const es=positions.map(([x,y])=>A.spawn(x,y)),logs=es.map(A.watch);p.target=es[0];p.aim=0;
   A.cast(id);A.assert(A.action()?.owner===p,'owned live action missing '+id);A.advance(2);
   const losses=es.map(e=>e.maxHp-e.hp);A.assert(losses[0]>0,'main target not damaged '+id);
   A.assert(losses.at(-1)===0,'outside target damaged '+id);
   A.assert(logs.flat().every(h=>h.owner&&h.id===id),'native owned hurt bypassed '+id);
   if(['camellia','larch','lily','bracken'].includes(key))A.assert(losses.slice(0,3).every(x=>x>0),'three separated inside enemies not all hit '+id);
   A.assert(logs[0].length===count,'wrong hit count '+id+' '+logs[0].length);
   const expected=shares.reduce((sum,share)=>sum+A.expected(move,share,es[0]),0);
   A.assert(losses[0]===expected,'segment damage '+id+' got '+losses[0]+' expected '+expected);
   const after=es.map(e=>e.hp);A.advance(1);A.assert(es.every((e,i)=>e.hp===after[i]),'completed attack re-hit '+id);
   out[id]={losses,hits:logs.map(a=>a.length),raw:logs,action:A.summarize()};
 }
 return out;
}"""

PROJECTILES = r"""() => {
 const A=KAcceptance,p=A.p(),out={};
 for(const q of [0,1,5,20]){
   A.reset();const m=A.fixture('naruto-kimimaro-bullets');p.quantityPicks=p.quantityBonus=q;
   const e=A.spawn(190,0),hits=A.watch(e);p.target=e;A.cast(m.id);A.advance(.15);
   A.assert(e.hp===e.maxHp,'finger bones damaged before release/flight');A.advance(1.2);
   const count=Math.min(15,Math.floor(5*1.25**q));
   A.assert(hits.length===count,'actual projectile count Q'+q+' '+hits.length+' != '+count);
   A.assert(e.maxHp-e.hp===count*A.expected(m,.2,e),'quantity duplicated per-bullet multiplier');
   out[q]={count,hits,damage:e.maxHp-e.hp};
 }
 // A foreground victim catches each bone; none pierce to the second body.
 A.reset();const m=A.fixture('naruto-kimimaro-bullets'),front=A.spawn(150,0),rear=A.spawn(260,0);p.target=rear;
 A.cast(m.id);A.advance(1.4);A.assert(front.hp<front.maxHp&&rear.hp===rear.maxHp,'bones pierce a foreground body');out.noPierce=true;
 A.reset();A.fixture('naruto-kimimaro-bullets');const blocked=A.spawn(190,0);p.target=blocked;
 // Cast while target visible, then introduce an obstacle before the first shot.
 A.cast('naruto-kimimaro-bullets');A.advance(.17);A.assert(A.K.stateFor(p).emitted>=1,'wall fixture has no real in-flight bone');G.World.isWall=(x,y)=>x>=60&&x<=68;
 A.advance(1.4);A.assert(blocked.hp===blocked.maxHp,'bone crossed an actual path wall');out.wall=true;
 return out;
}"""

PROPS = r"""() => {
 const A=KAcceptance,p=A.p(),out={};
 for(const [id,x] of [['naruto-kimimaro',45],['naruto-kimimaro-bullets',110]]){
   A.reset();const move=A.fixture(id),prop={x,y:0,r:12,type:'chest',solid:true,destructible:true,hp:1000000,tx:3,ty:0};
   p.target=id==='naruto-kimimaro'?prop:A.spawn(190,0);
   if(id==='naruto-kimimaro-bullets'){A.cast(id);A.advance(.17);A.assert(A.K.stateFor(p).emitted>=1,'prop fixture has no real in-flight bone')}
   G.World.propsInCircle=(cx,cy,r)=>Math.hypot(prop.x-cx,prop.y-cy)<=r+prop.r?[prop]:[];
   G.World.projectileBlock=(cx,cy,r)=>Math.hypot(prop.x-cx,prop.y-cy)<prop.r+r?prop:false;
   const original=G.World.damageProp,events=[];G.World.damageProp=function(target,amount,...args){events.push({same:target===prop,amount});return original.call(this,target,amount,...args)};
   try{if(id==='naruto-kimimaro')A.cast(id);A.advance(1.6)}finally{G.World.damageProp=original}
   A.assert(prop.hp<1000000&&events.every(e=>e.same),'native destructible prop cannot be hit '+id);
   out[id]={damage:1000000-prop.hp,events};
 }
 return out;
}"""

CONTROL = r"""() => {
 const A=KAcceptance,p=A.p(),out={};
 for(const special of [null,'boss','elite','legend','judge']){
   A.reset();A.fixture('naruto-kimimaro-vine');const e=A.spawn(155,0,special),start={x:e.x,y:e.y};p.target=e;e.slow=.15;e.slowT=5;
   if(special){
     // Standalone support Vine intentionally does not auto-target specials.
     A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()}
     A.assert(!A.K.activeFor(p),'standalone Vine automatically targeted '+special);
     // Explicit engine cast separately proves that the no-pull safeguard is
     // intrinsic to the technique, including non-scheduler callers.
     const vine=p.moves.find(m=>m.id==='naruto-kimimaro-vine');
     A.resume();try{A.assert(G.DigimonSkills.cast(p,vine),'explicit special Vine cast')}finally{A.pause()}
   }else A.cast('naruto-kimimaro-vine');
   A.advance(.60);
   if(special)A.assert(e.x===start.x&&e.y===start.y,'special target moved by bone vine '+special);
   else{A.assert(e.x<start.x,'ordinary vine did not pull');A.assert(Math.hypot(e.x-p.x,e.y-p.y)>=(p.r||0)+e.r+7.9,'vine overlapped player contact circle')}
   G.Combat.clearFields(p);A.advance(.2);const end=[e.x,e.y];A.advance(.3);A.assert(e.x===end[0]&&e.y===end[1],'cancel left a continuing pull');
   A.near(e.slow,.15,'bone control overwrote unrelated slow');A.near(e.slowT,5,'bone control overwrote unrelated slow timer');
   out[special||'normal']={start,end};
 }
 A.reset();A.fixture('naruto-kimimaro-bracken');const boss=A.spawn(70,0,'boss');p.target=boss;
 A.assert(boss.flying,'boss fixture must cover actual flying flag');A.cast('naruto-kimimaro-bracken');A.advance(1.6);
 A.assert(boss.hp<boss.maxHp,'boss incorrectly immune to ground bones');out.bossFlyingDamage=boss.maxHp-boss.hp;
 A.reset();A.fixture('naruto-kimimaro-bracken');const jumper=A.spawn(75,0);p.target=jumper;A.cast('naruto-kimimaro-bracken');A.advance(.43);
 jumper.startJump(p);jumper.jump.t=.01;jumper.updateJump(0);
 for(let n=0;n<50;n++){jumper.updateJump(.01);const lift=jumper.jumpLift;A.step(.01);A.near(jumper.jumpLift,lift,'bone forest overwrote native jump height')}
 A.assert(jumper.hp===jumper.maxHp,'actual jumping target hit by ground forest');out.nativeJump=true;
 return out;
}"""

LIFECYCLE = r"""() => {
 const A=KAcceptance,p=A.p(),out={};
 for(const reason of ['clear','death','world','role']){
   A.reset();A.fixture('naruto-kimimaro-bracken');const e=A.spawn(70,0);p.target=e;A.cast('naruto-kimimaro-bracken');A.advance(.20);
   const oldWorld=G.World,oldMon=p.mon;
   if(reason==='clear')G.Combat.clearFields(p);
   if(reason==='death'){p.dead=true;p.hp=0}
   if(reason==='world')G.World={...G.World};
   if(reason==='role')p.mon=G.DEX_BY[30007];
   try{A.advance(.9);A.assert(!A.action(),'state leaked after '+reason);A.assert(e.hp===e.maxHp,'cancelled delayed damage '+reason)}
   finally{G.World=oldWorld;p.mon=oldMon;p.dead=false;p.hp=p.maxHp}
   out[reason]=true;
 }
 A.reset();A.fixture('naruto-kimimaro-flower');p.target=A.spawn(80,0);A.cast('naruto-kimimaro-flower');A.advance(.20);
 const action=A.action(),age=action.age;G.Combat.updateFields(.5);A.near(action.age,age,'pause advanced body action');out.pause=true;
 A.reset();A.fixture('naruto-kimimaro-bracken');const e=A.spawn(110,0);p.target=e;A.cast('naruto-kimimaro-bracken');A.advance(.20);
 p.level=30;p.addMove('naruto-kimimaro-lily');A.advance(.65);
 A.assert(e.hp<e.maxHp&&A.action()?.kind==='bracken','learning another passive cancelled the existing forest');out.learnDuringCast=true;
 A.reset();A.fixture('naruto-kimimaro-bracken');const cancelled=A.spawn(110,0);p.target=cancelled;A.cast('naruto-kimimaro-bracken');A.advance(.20);
 p.moves=p.moves.filter(m=>m.id!=='naruto-kimimaro-bracken');p.arrange();
 A.advance(1.4);A.assert(cancelled.hp===cancelled.maxHp&&!A.action(),'unlearned skill left future bone waves');out.unlearn=true;
 return out;
}"""

CURSE = r"""() => {
 const A=KAcceptance,p=A.p(),K=A.K;A.reset();const curse=A.fixture('naruto-kimimaro-curse',5),enemy=A.spawn(80,0);
 p.target=enemy;const hp=p.hp,baseAtk=p.atk,baseSpeed=p.spd;
 A.cast(curse.id);A.advance(.90);
 A.assert(K.curseState(p).transforming&&!K.curseState(p).active,'curse buff began before one-second transformation');
 A.near(p.spd,baseSpeed,'speed increased during transformation');
 A.advance(.12);A.assert(K.curseState(p).active&&K.formFor(p)==='curse','dedicated curse form absent');
 A.near(K.curseState(p).bonus,.20,'five-rank curse bonus');A.near(p.spd,baseSpeed*1.1,'curse speed bonus once');A.near(p.atk,baseAtk,'curse mutated base attack');
 const flowerId='naruto-kimimaro-flower';A.assert(p.addMove(flowerId),'learn flower in curse fixture');const flower=p.moves.find(m=>m.id===flowerId),hits=A.watch(enemy);
 A.cast(flowerId);A.advance(.7);A.assert(hits.length===1,'curse flower hit count');
 const enhanced=Math.round(flower.dmg*baseAtk*1.2*G.Types.mult(flower.type,enemy.types)*G.Weather.mult(flower.type));
 A.assert(hits[0].loss===enhanced,'curse damage multiplied incorrectly '+hits[0].loss+' != '+enhanced);
 A.near(p.hp,hp,'curse charged HP');
 const state=K.stateFor(p);A.advance(Math.max(0,9.05-state.clock));
 A.assert(!K.curseState(p).active&&K.formFor(p)==='normal','curse did not expire');A.near(p.spd,baseSpeed,'curse speed leaked after expiry');A.near(p.atk,baseAtk,'base attack leaked after curse');
 flower.t=999;A.advance(Math.max(0,29.9-K.stateFor(p).clock),true);
 A.assert(K.stateFor(p).castCounts.curse===1,'curse retriggered before fixed30s cycle');
 A.advance(.2,true);A.assert(K.stateFor(p).castCounts.curse===2,'curse did not become ready after30s');
 const beforeClear=K.curseState(p);G.Combat.clearFields(p);A.assert(K.stateFor(p)===null&&K.formFor(p)==='normal','clear retained curse state');
 A.near(p.spd,baseSpeed,'clear retained curse movement bonus');
 return {baseSpeed,baseAtk,enhancedDamage:enhanced,hpUnchanged:p.hp===hp,secondStart:beforeClear,slots:p.slots.map(g=>g.map(m=>m.id))};
}"""

COMBO = r"""() => {
 const A=KAcceptance,p=A.p(),K=A.K,ids=['naruto-kimimaro-vine','naruto-kimimaro-flower'];
 function prepare(){A.reset();A.fixture(ids[0]);A.assert(p.addMove(ids[1]),'learn linked flower');const vine=p.moves.find(m=>m.id===ids[0]),flower=p.moves.find(m=>m.id===ids[1]);
   A.assert(vine.passive&&!p.slots.some(g=>g.includes(vine)),'Vine must remain slotless');
   A.assert(flower.passive&&!p.slots.length,'Flower must remain slotless');vine.t=flower.t=0;
   const e=A.spawn(155,0),hits=A.watch(e);p.target=e;p.aim=0;A.advance(.11);return {vine,flower,e,hits}}
 let f=prepare();A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()}
 A.assert(K.activeFor(p)?.kind==='combo','learned passive Vine and Flower did not link');
 A.advance(.53);A.assert((K.stateFor(p).castCounts.flower||0)===0&&f.flower.t===0,'flower charged before actual start');
 A.advance(.02);A.assert(K.stateFor(p).castCounts.flower===1,'flower did not start at .54');
 A.near(f.flower.t,8,'independent flower cooldown');A.advance(.90);
 A.assert(f.hits.length===2,'combo added or lost hit');
 const expected=A.expected(f.vine,1,f.e)+A.expected(f.flower,1,f.e);
 A.assert(f.e.maxHp-f.e.hp===expected,'linked combo duplicated full damage');
 const firstLog=K.stateFor(p).castLog.map(x=>({kind:x.kind,time:x.time}));
 // Reset and drive all production cooldowns, fields and the bounded pair wait.
 f=prepare();A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()};A.advance(9.20,true);
 const log=K.stateFor(p).castLog,starts=log.filter(x=>x.kind==='vine');
 A.assert(starts.length===2,'linked pair did not recur exactly once '+JSON.stringify(log));
 A.assert(Math.abs((starts[1].time-starts[0].time)-8.54)<=.02+1e-8,'independent CD or short-wait interval '+JSON.stringify(starts));
 // Waiting learned techniques all get a turn without a selected or fused group.
 A.reset();A.fixture('naruto-kimimaro-camellia');for(const id of ['naruto-kimimaro-larch','naruto-kimimaro-lily'])A.assert(p.addMove(id),'learn fair fixture');
 A.assert(!p.slots.length,'fair fixture unexpectedly requires active slots');for(const m of p.moves)m.t=0;
 p.target=A.spawn(45,0);A.advance(3,true);const counts=K.stateFor(p).castCounts;
 for(const key of ['camellia','larch','lily'])A.assert(counts[key]>=1,'group skill starved '+key+' '+JSON.stringify(counts));
 return {firstLog,starts,damage:expected,fairCounts:counts};
}"""

RESTART = r"""() => {
 const A=KAcceptance,old=A.p();A.reset();A.fixture('naruto-kimimaro-bracken');old.target=A.spawn(80,0);A.cast('naruto-kimimaro-bracken');A.advance(.2);
 A.resume();G.Game.startRun();A.pause();const next=A.p();
 A.assert(next!==old&&next.dex===30012,'normal restart did not create a new Kimimaro');
 A.assert(next.moves.length===1&&next.moves[0].id==='naruto-kimimaro','new run retained learned skill pool');
 A.assert(!A.K.activeFor(old)&&A.K.formFor(next)==='normal','old owner action/form retained on restart');
 return {freshOwner:true,moves:next.moves.map(m=>m.id),slots:next.slots.length};
}"""

CLONES = r"""() => {
 const A=KAcceptance,p=A.p(),K=A.K;A.reset();const move=A.fixture('naruto-kimimaro-larch');move.t=999;
 A.assert(p.addMove('naruto-kimimaro'),'clone fixture retains native starter Willow');
 p.moves.find(m=>m.id==='naruto-kimimaro').t=999;
 const clone=G.SelfClones.summon(p);A.assert(clone&&G.SelfClones.actors().includes(clone),'native self clone summon failed');
 const enemy=A.spawn(clone.x+32,clone.y),events=[],hurt=enemy.hurt;enemy.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);
   events.push({ownerIsClone:args[6]===clone,loss:hp-this.hp,id:args[7]});return result};
 p.target=enemy;A.advance(.43);const action=K.activeFor(clone),copy=clone.moves.find(m=>m.id===move.id);
 A.assert(action?.owner===clone&&!K.activeFor(p),'clone action shared player body state');
 A.assert(copy!==move&&copy.t<move.t,'clone shares or resets owner cooldown object');
 A.assert(events.length&&events.every(e=>e.ownerIsClone&&e.id===move.id),'clone hit did not use native clone ownership');
 const expected=Math.round(move.dmg*.5*clone.atk*G.Types.mult(move.type,enemy.types)*G.Weather.mult(move.type));
 A.assert(events[0].loss===expected,'clone damage applied ratio or curse twice');
 const ownerHp=p.hp,before=clone.hp;clone.invuln=0;A.resume();try{clone.hurt(20,null,false)}finally{A.pause()}
 const expectedGuard=20*(1-clone.reduction)*.75*.8;
 A.near(before-clone.hp,expectedGuard,'clone Larch guard must multiply .8 and existing melee .75 once after native reduction');A.near(p.hp,ownerHp,'clone hurt reduced owner HP');
 const guarded={loss:before-clone.hp,cloneHp:clone.hp,ownerHp:p.hp};const clonePose=A.pose(clone);delete clonePose.png;
 A.reset();const baseSpeed=p.spd;A.fixture('naruto-kimimaro-curse',5);p.target=A.spawn(100,0);A.cast('naruto-kimimaro-curse');A.advance(1.1);
 const ownSpeed=p.spd,transformed=G.SelfClones.summon(p);A.advance(.20);
 A.assert(K.curseState(transformed).transforming&&!K.curseState(transformed).active,'clone did not own its transformation clock');
 A.near(transformed.spd,baseSpeed,'clone inherited parent curse speed before its own form');
 A.advance(1.0);A.assert(K.curseState(transformed).active,'clone curse did not activate');
 A.near(transformed.spd,baseSpeed*1.1,'clone curse speed doubled parent bonus');A.near(p.spd,ownSpeed,'clone curse altered owner speed');
 const curseSpeeds={base:baseSpeed,owner:p.spd,clone:transformed.spd};
 G.Combat.clearFields(p);A.advance(.01);A.assert(!G.SelfClones.actors().length&&!K.stateFor(transformed),'clone cleanup retained combat state');
 return {independentCooldown:true,ownedDamage:events,guarded,clonePose,curseSpeeds,cleanup:true};
}"""

TERMINAL = r"""() => {
 const A=KAcceptance,K=A.K,out=[];
 for(const method of ['quit','toUI'])for(const mode of ['curse','vine']){
   G.Game.startRun();A.pause();A.reset();const p=A.p();
   const id='naruto-kimimaro-'+mode;A.fixture(id,mode==='curse'?5:1);const e=A.spawn(mode==='vine'?155:80,0);p.target=e;
   const normalSpeed=p.spd;A.cast(id);A.advance(mode==='curse'?1.10:.55);
   A.assert(mode==='curse'?K.curseState(p).active:K.held(e),'terminal fixture did not activate '+mode);
   // Invoke the public native exit. Do not manually tick/clear combat to make
   // these assertions pass: terminal cleanup must happen on the real event.
   G.Game[method]();
   A.assert(['ui','over'].includes(G.Game.state),'native terminal method did not leave playing');
   A.assert(K.stateFor(p)===null&&!K.activeFor(p)&&K.formFor(p)==='normal','terminal owner state leaked '+method+' '+mode);
   A.assert(!K.curseState(p).active&&!K.held(e),'terminal buff or held target leaked '+method+' '+mode);
   A.near(p.spd,normalSpeed,'terminal speed buff leaked '+method);
   out.push({method,mode,state:G.Game.state,cleared:true});
 }
 G.Game.startRun();A.pause();return out;
}"""

def game_frame(page):
    for _ in range(300):
        for frame in page.frames:
            try:
                if frame.evaluate("typeof G==='object' && !!G.Game && !!G.NarutoKimimaro"):
                    return frame
            except Exception:
                pass
        page.wait_for_timeout(100)
    raise AssertionError('normal game frame did not load Kimimaro runtime')


def boot(page, label):
    url = URL + ('&layout=wide' if label == 'desktop' and 'layout=' not in URL else '')
    page.goto(url)
    frame = game_frame(page)
    frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')", polling=20)
    if frame.locator('#tap-start').is_visible():
        frame.locator('#tap-start').click()
    frame.locator('[data-quick-naruto="30012"]').click()
    assert frame.evaluate('G.DB.save.partner===30012'), 'normal picker failed'
    # Capture selection/portrait before invoking any controlled fixture.
    page.screenshot(path=str(OUT/f'{label}-selection.png'))
    frame.locator('#scr-menu [data-go="play"]').click()
    frame.wait_for_function('G.Game.player?.dex===30012 && G.Game.state==="playing"', polling=20)
    page.screenshot(path=str(OUT/f'{label}-normal-entry.png'))
    frame.evaluate(SETUP)
    return frame


def save_pose(name, result):
    png=result.pop('png')
    (OUT/f'{name}.png').write_bytes(base64.b64decode(png.split(',',1)[1]))
    return result


def input_art(page, frame, context, label, mobile):
    result={'movement':{},'poses':{}}
    frame.evaluate("KAcceptance.reset();KAcceptance.fixture('naruto-kimimaro')")
    if frame != page.main_frame:
        page.locator('iframe').first.focus()
    for direction,key in [('right','KeyD'),('left','KeyA'),('down','KeyS'),('up','KeyW')]:
        page.keyboard.down(key)
        result['movement'][direction]=frame.evaluate("""()=>{const A=KAcceptance,p=A.p(),before=[p.x,p.y];A.resume();try{p.update(.08)}finally{A.pause()};
          A.assert(p.walking&&Math.hypot(p.x-before[0],p.y-before[1])>0,'native keyboard did not move');return {dx:p.x-before[0],dy:p.y-before[1],dir:p.anim.dir}}""")
        page.keyboard.up(key)
        result['poses'][direction]=save_pose(f'{label}-walk-{direction}',frame.evaluate('KAcceptance.pose()'))
    frame.evaluate("KAcceptance.reset();KAcceptance.fixture('naruto-kimimaro');KAcceptance.resume();KAcceptance.p().hurt(7,null,true);KAcceptance.pause()")
    result['poses']['hurt']=save_pose(f'{label}-hurt',frame.evaluate('KAcceptance.pose()'))
    frame.evaluate('KAcceptance.reset();KAcceptance.p().hp=1;KAcceptance.resume();KAcceptance.p().hurt(100,null,true);KAcceptance.p().anim.update(.5);KAcceptance.pause()')
    result['poses']['death']=save_pose(f'{label}-death',frame.evaluate('KAcceptance.pose()'))
    assert result['poses']['hurt']['calls'] != result['poses']['death']['calls'], 'hurt and death reuse the same frame'
    frame.evaluate("KAcceptance.reset();KAcceptance.fixture('naruto-kimimaro-camellia');KAcceptance.p().addMove('naruto-kimimaro-lily');KAcceptance.resume()")
    page.keyboard.press('Digit2')
    result['keyboardNoSelection']=frame.evaluate("(()=>{KAcceptance.pause();const p=KAcceptance.p();KAcceptance.assert(!p.slots.length&&p.activeGroup().length===0,'keyboard created an active passive slot');return p.moves.map(m=>m.id)})()")
    if mobile:
        frame.evaluate("KAcceptance.reset();KAcceptance.fixture('naruto-kimimaro');KAcceptance.resume()")
        client=context.new_cdp_session(page)
        base=frame.evaluate('G.Touch.stickBase()')
        offset={'x':0,'y':0}
        if frame!=page.main_frame:
            box=page.locator('iframe').first.bounding_box();offset={'x':box['x'],'y':box['y']}
        point={'x':base['x']+offset['x'],'y':base['y']+offset['y']}
        client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]})
        client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':point['x']+42,'y':point['y']}]})
        result['touch']=frame.evaluate("""()=>{const A=KAcceptance,p=A.p(),x=p.x;A.assert(G.Touch.vector()[0]>0,'touch vector missing');p.update(.08);A.pause();A.assert(p.x>x,'touch did not move');return p.x-x}""")
        client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        frame.evaluate("KAcceptance.fixture('naruto-kimimaro-camellia');KAcceptance.p().addMove('naruto-kimimaro-lily');KAcceptance.resume()")
        slot=frame.evaluate("(()=>{const p=G.Game.player,n=p.slots.length+p.moves.filter(m=>m.passive&&!p.slots.some(g=>g.includes(m))).length;return G.Touch.controlLayout(innerWidth,innerHeight,n).slots[1]})()")
        page.touchscreen.tap(slot['x']+slot['w']/2+offset['x'],slot['y']+slot['h']/2+offset['y'])
        result['touchNoSelection']=frame.evaluate("(()=>{KAcceptance.pause();const p=KAcceptance.p();KAcceptance.assert(!p.slots.length&&p.activeGroup().length===0,'touch selected a passive');return p.moves.map(m=>m.id)})()")
    return result


def capture_gameplay(page, frame, label):
    result={}
    cases=[('naruto-kimimaro',.30,50),('camellia',.43,85),('bullets',.25,170),
           ('larch',.40,55),('vine',.55,155),('flower',.58,90),('lily',.52,70),('bracken',1.02,70)]
    for key,at,distance in cases:
        skill=key if key=='naruto-kimimaro' else 'naruto-kimimaro-'+key
        info=frame.evaluate('''({skill,at,distance})=>{
          const A=KAcceptance,p=A.p();A.reset();A.fixture(skill);const e=A.spawn(distance,0);p.target=e;
          if(['naruto-kimimaro-larch','naruto-kimimaro-lily','naruto-kimimaro-bracken'].includes(skill)){
            A.spawn(-35,35);A.spawn(40,-30)}
          A.cast(skill);A.advance(at);return {age:A.action()?.age,kind:A.action()?.kind,art:A.pose(),fields:A.fields()};
        }''',{'skill':skill,'at':at,'distance':distance})
        info['art']=save_pose(f'{label}-{key}-actor',info['art'])
        info['fields']=save_pose(f'{label}-{key}-field',info['fields'])
        if key in ('bracken','flower'):
            assert any('kimimaro' in source.lower() and ('effect' in source.lower() or 'vfx' in source.lower()) for source in info['fields']['sources']), (key,info['fields']['sources'])
        page.wait_for_timeout(35)
        page.screenshot(path=str(OUT/f'{label}-{key}-game.png'))
        result[key]=info
    # Use the actual passive transformation before checking a transformed cast.
    frame.evaluate("KAcceptance.reset();KAcceptance.fixture('naruto-kimimaro-curse',5);KAcceptance.p().target=KAcceptance.spawn(80,0);KAcceptance.cast('naruto-kimimaro-curse');KAcceptance.advance(1.10)")
    result['curse']=save_pose(f'{label}-curse-actor',frame.evaluate('KAcceptance.pose()'))
    frame.evaluate("KAcceptance.p().addMove('naruto-kimimaro-flower');KAcceptance.cast('naruto-kimimaro-flower');KAcceptance.advance(.58)")
    result['curse-flower']=save_pose(f'{label}-curse-flower-actor',frame.evaluate('KAcceptance.pose()'))
    page.wait_for_timeout(35);page.screenshot(path=str(OUT/f'{label}-curse-flower-game.png'))
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'url':URL,'scope':'actual normal game entry, native actors/combat/cards/art','viewports':{},'errors':[],'failedRequests':[],'failures':[],
            'sourceHashes':runtime_hashes(),'assets':asset_inventory()}
    checks=[('progression',PROGRESSION),('combat',COMBAT),('projectiles',PROJECTILES),('props',PROPS),('control',CONTROL),('lifecycle',LIFECYCLE),('curse',CURSE),('combo',COMBO),('clones',CLONES),('restart',RESTART),('terminal',TERMINAL)]
    selected=set(os.environ.get('KIMIMARO_CHECKS','').split(','))-{''}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME,headless=True)
        for label,viewport,mobile in [('desktop',{'width':1280,'height':900},False),('mobile',{'width':390,'height':844},True)]:
            context=browser.new_context(viewport=viewport,is_mobile=mobile,has_touch=mobile,service_workers='block')
            page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(e.stack or str(e)))
            page.on('response',lambda response:report['failedRequests'].append({'url':response.url,'status':response.status}) if response.status>=400 else None)
            result=report['viewports'][label]={}
            try:
                frame=boot(page,label)
                for name,check in checks:
                    if selected and name not in selected:continue
                    print(label,name,flush=True)
                    try:result[name]=frame.evaluate(check)
                    except Exception as error:
                        result[name]={'failure':str(error)};report['failures'].append(label+':'+name+': '+str(error))
                    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
                if not selected or 'input' in selected:
                    try:result['inputAndArt']=input_art(page,frame,context,label,mobile)
                    except Exception as error:report['failures'].append(label+':inputAndArt: '+str(error))
                if not selected or 'art' in selected:
                    try:result['gameplayArt']=capture_gameplay(page,frame,label)
                    except Exception as error:report['failures'].append(label+':gameplayArt: '+str(error))
                assert not frame.evaluate('document.documentElement.scrollWidth>innerWidth'), 'game viewport horizontal overflow'
            except Exception as error:report['failures'].append(label+':boot: '+str(error))
            finally:context.close()
        browser.close()
    report['sourceHashesAfter']=runtime_hashes()
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime source changed during acceptance run; rerun frozen sources')
    report['ok']=not(report['errors'] or report['failedRequests'] or report['failures'])
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'evidence':str(OUT)},ensure_ascii=True))
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':
    main()
