"""Pain fixtures and compatibility entry for current automatic combat acceptance.

Controlled arenas omit procedural terrain, except explicit wall fixtures.
Enemy.hurt, projectile collision, upgrade cards and input are never replaced.
Run against the workspace HTTP server on 8004; PAIN_URL may target a build.
"""
import base64
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_gaara import CHROME, HARNESS

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('PAIN_OUT', str(ROOT / '.omx/state/pain')))
URL = os.environ.get('PAIN_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&layout=wide&test=pain')

SETUP = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;A.assert(P,'native Pain module missing');
 A.reset=()=>{A.arena();G.SelfClones.clear();G.Pickups.clear();p.xp=0;p.xpNext=1e9;
   p.target=null;p.quantityBonus=p.quantityPicks=0;p.percentHealthDamage=p.lifestealRate=p.critChance=0;p.cdMul=1;
   for(const m of p.moves)m.t=999;A.advance(.01);A.finish(1.6);for(const b of P.actorsFor(p))b.cooldown=999};
 A.spawn=(x,y,boss=false)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
   e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
 A.advance=(dt=.01)=>{A.resume();try{G.Combat.updateFields(dt);p.anim.update(dt);
   G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,0)}finally{A.pause()}};
 A.finish=(seconds=2)=>{for(let i=0;i<seconds*100;i++)A.advance(.01)};
 A.castNative=id=>{const m=p.moves.find(m=>m.id===id);A.assert(m,'unlearned '+id);
   if(!m.passive)A.select(id);else m.t=0;
   const moves=p.moves;if(id!=='naruto-pain')p.moves=moves.filter(m=>m.id!=='naruto-pain');
   let calls=0,old=p.cast;p.cast=function(move,...args){if(move.id===id)calls++;return old.call(this,move,...args)};
   try{A.resume();G.Combat.tick(.001,p,0)}finally{p.cast=old;p.moves=moves;A.pause()}
   A.assert(calls===1,'native cast count '+id+' '+calls);return m};
 A.actors=()=>P.actors();
 A.reset();
}"""

PROGRESSION = r"""() => {
 const A=Acceptance,p=A.p(),ids=['gravity','missiles','absorb','summon','soul','repair','planet'],levels=[3,6,6,9,12,12,15],out=[];
 A.assert(p.dex===30010&&p.moves.length===1&&p.moves[0].id==='naruto-pain','fresh native Pain starter missing');
 A.assert(p.maxMoves===5,'Pain must have five native active slots');
 A.assert(p.moves[0].passive&&p.slots.length===0,'black rods must be slotless automatic basic');
 for(const level of [...new Set(levels)]){
   const group=ids.filter((_,i)=>levels[i]===level);
   p.level=level-1;for(const suffix of group)A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='new:naruto-pain-'+suffix),'premature '+suffix);
   p.level=level;const cards=G.LevelUp.offer(p,3);
   for(const suffix of group)A.assert(cards.find(c=>c.key==='new:naruto-pain-'+suffix)?.guaranteed,'missing first milestone '+suffix);
   G.RunUI.showLevelUp(p.level,cards,c=>c.apply(p));G.RunUI.closeLevelUp();
   for(const suffix of group){
     const id='naruto-pain-'+suffix,passive=['absorb','repair'].includes(suffix);
     A.assert(p.narutoMilestonesShown.has(id),'display did not consume '+id);
     A.assert(!G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id)?.guaranteed,'declined milestone forced again '+id);
     const n=p.slots.length;if(passive)p.maxMoves=n;
     const learn=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
     A.assert(learn&&learn.apply(p)!==false,'actual card cannot learn '+id);p.maxMoves=5;
     A.assert(p.slots.length===n+(passive?0:1),'wrong active/passive slots '+id);out.push({id,level,slots:p.slots.length});
   }
 }
 A.assert(p.moves.length===8&&p.slots.length===5,'complete five active/two passive/basic loadout missing');
 const mon=p.mon;p.mon=G.DEX.find(m=>m.dex===30009);
 try{A.assert(!G.Moves.poolFor(p.mon).some(id=>id.startsWith('naruto-pain')),'Pain skills leaked into Tenten')}finally{p.mon=mon}
 return out;
}"""

FORMATION = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;A.reset();
 const actors=A.actors();A.assert(actors.length===5,'need five support bodies '+actors.length);
 A.assert(new Set(actors.map(a=>a.path)).size===5,'support paths are duplicated');
 A.assert(actors.every(a=>a.hp>0&&a.maxHp===p.maxHp*(['human','preta'].includes(a.path)?.8:.6)),'support role durability mismatch');
 p.quantityBonus=p.quantityPicks=20;
 const clone=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');A.assert(clone,'self-clone card absent');clone.apply(p);clone.apply(p);
 A.finish(.3);A.assert(G.SelfClones.actors().length===2,'self clone fixture missing');
 A.assert(A.actors().length===5&&A.actors().every(a=>actors.includes(a)),'quantity/clones duplicated six paths');
 const s=P.snapshot(p),snapshot={count:s.count,queue:s.queue,sharedRecovery:s.sharedRecovery};G.SelfClones.clear();return {paths:actors.map(a=>a.path),snapshot};
}"""

COMBAT = r"""() => {
 const A=Acceptance,p=A.p(),out={};
 for(const id of ['naruto-pain-gravity','naruto-pain-missiles','naruto-pain-summon','naruto-pain-planet']){
   A.reset();const es=[A.spawn(100,0),A.spawn(115,18),A.spawn(115,-18),A.spawn(-500,400)];p.target=es[0];p.aim=0;
   const hits=es.map(()=>[]);es.forEach((e,i)=>{const hurt=e.hurt;e.hurt=function(...args){const before=this.hp,result=hurt.apply(this,args);hits[i].push({owner:args[6]===p,id:args[7],damage:before-this.hp});return result}});
   A.castNative(id);A.finish(3.5);const damage=es.map(e=>100000-e.hp);
   A.assert(damage.slice(0,3).every(d=>d>0)&&damage[3]===0,'AOE three inside/one outside '+id+' '+damage);
   A.assert(hits.slice(0,3).every(h=>h.some(v=>v.id===id&&v.damage>0))&&!hits[3].some(h=>h.id===id),'each inside HP loss must belong to tested skill '+id);
   const expected=id.endsWith('planet')?4:id.endsWith('missiles')?3:1;
   A.assert(hits.slice(0,3).every(h=>h.filter(v=>v.id===id).length===expected),'missing/duplicate skill damage phases '+id+' '+hits.map(h=>h.filter(v=>v.id===id).length));
   A.assert(hits.flat().every(h=>h.owner),'native damage ownership '+id);
   const before=hits.map(h=>h.filter(v=>v.id===id).length);A.finish(1);
   A.assert(hits.every((h,i)=>h.filter(v=>v.id===id).length===before[i]),'completed action repeated damage '+id);
   out[id]={damage,hits};
 }
 return out;
}"""

QUANTITY = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out=[];
 for(const id of ['naruto-pain','naruto-pain-missiles']){
   const m=p.moves.find(m=>m.id===id);
   for(let tier=1;tier<=5;tier++){
     if(tier>1){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(card&&card.apply(p)!==false,'upgrade '+id+' '+tier)}
     for(const picks of [0,4,20]){
       A.reset();p.quantityBonus=p.quantityPicks=picks;p.target=A.spawn(180,0);A.castNative(id);A.advance();
       const base=(id==='naruto-pain'?[5,5,6,7,8]:[10,10,12,14,16])[tier-1],cap=id==='naruto-pain'?40:60;
       const expected=Math.min(cap,Math.floor(base*Math.pow(1.25,picks))),actual=P.snapshot(p).count;
       A.assert(actual===expected,'quantity applied incorrectly '+id+' tier'+tier+' picks'+picks+' '+actual+' expected'+expected);
       A.assert(P.shots.filter(s=>s.kind===(id==='naruto-pain'?'rod':'missile')).length<=cap,'live entity cap exceeded');
       A.assert(A.actors().length===5,'quantity duplicated unique bodies');out.push({id,tier,picks,count:actual});
     }
   }
 }
 A.reset();return out;
}"""

ART = r"""() => {
 const A=Acceptance,p=A.p();A.reset();A.assert(G.PainArt.loaded,'production atlas not loaded');
 const out=[];
 for(const actor of [p,...A.actors()]){
   const canvas=document.createElement('canvas');canvas.width=240;canvas.height=200;
   const ctx=canvas.getContext('2d',{willReadFrequently:true}),sources=[],rects=[],draw=ctx.drawImage.bind(ctx);
   ctx.drawImage=(image,...args)=>{sources.push(image.src||'');rects.push(args);return draw(image,...args)};
   if(actor===p)p.anim.draw(ctx,120,150);
   else{ctx.save();ctx.translate(120-actor.x,150-actor.y);actor.draw(ctx);ctx.restore()}
   const path=actor===p?'tendo':actor.path,expected=G.PainArt.images[path].src;
   A.assert(sources.includes(expected)&&sources.every(s=>s===expected),'native actor used wrong atlas '+path+' '+sources);
   const rgba=ctx.getImageData(0,0,240,200).data;let pixels=0,x0=240,y0=200,x1=-1,y1=-1;
   for(let y=0;y<200;y++)for(let x=0;x<240;x++)if(rgba[(y*240+x)*4+3]>20){pixels++;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}
   A.assert(pixels>100&&pixels<8000,'empty or opaque atlas rectangle '+path+' '+pixels);
   A.assert(x0>0&&x1<239&&y0>0&&y1<199,'native actor canvas clipped '+path);
   A.assert([0,239,240*199,240*200-1].every(i=>rgba[i*4+3]===0),'atlas has opaque evidence-canvas corners '+path);
   out.push({path,sources,rects,pixels,bounds:[x0,y0,x1,y1],png:canvas.toDataURL()});
 }
 A.assert(new Set(out.map(a=>a.sources[0])).size===6,'six bodies share duplicate source artwork');return out;
}"""

COLLISION = r"""() => {
 const A=Acceptance,p=A.p(),out=[];
 for(const id of ['naruto-pain','naruto-pain-missiles','naruto-pain-summon','naruto-pain-planet']){
   A.reset();const e=A.spawn(160,0);p.target=e;p.aim=0;
   A.actors().forEach((a,i)=>{a.x=-80;a.y=(i-2)*30});
   const W=G.World,saved={isFree:W.isFree,projectileBlock:W.projectileBlock,isWall:W.isWall};
   Object.assign(W,{isFree:x=>x<50,projectileBlock:x=>x>=50&&x<=90?{destructible:false}:false,isWall:x=>x>=50&&x<=90});
   try{const m=p.moves.find(m=>m.id===id);if(!m.passive)A.select(id);
     A.assert(!G.NarutoPain.canCast(p,m),'occluded target acquired '+id);
     A.finish(3.5);A.assert(e.hp===100000,'damage crossed solid wall '+id);A.assert(A.actors().every(a=>a.x<50),'support crossed wall '+id)}finally{Object.assign(W,saved)}
   out.push(id);
 }
 // Inserting a wall after launch also proves physical flight collision,
 // independently of the LOS acquisition rejection above.
 for(const id of ['naruto-pain','naruto-pain-missiles','naruto-pain-summon']){
   A.reset();A.actors().forEach((a,i)=>{a.x=-80;a.y=(i-2)*5});
   const e=A.spawn(160,0);p.target=e;p.aim=0;A.castNative(id);A.finish(.14);
   const W=G.World,saved={isFree:W.isFree,projectileBlock:W.projectileBlock,isWall:W.isWall};
   Object.assign(W,{isFree:x=>x<80,projectileBlock:x=>x>=80&&x<=110?{destructible:false}:false,isWall:x=>x>=80&&x<=110});
   try{A.finish(3);A.assert(e.hp===100000,'in-flight object crossed inserted wall '+id)}finally{Object.assign(W,saved)}
   out.push('flight:'+id);
 }
 return out;
}"""

RESISTANCE = r"""() => {
 const A=Acceptance,p=A.p(),out=[];
 for(const special of [null,'boss','elite','legend','judge']){
   A.reset();const e=A.spawn(220,0);if(special)e[special]=true;p.target=e;p.aim=0;const x=e.x;
   A.castNative('naruto-pain-gravity');A.finish(.34);
   const distance=Math.abs(e.x-x);A.assert(distance>0,'gravity never pulled '+special);out.push(distance);
   A.assert(!e.dead&&!(e.slow>0),'gravity hard controlled native enemy');
 }
 A.assert(out.slice(1).every(d=>d<=out[0]*.3),'special enemy lost displacement resistance '+out);return out;
}"""

LIFECYCLE = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out=[];
 for(const reason of ['pause','switch','clear','death','world']){
   A.reset();p.target=A.spawn(110,0);A.castNative('naruto-pain-planet');A.finish(.25);
   const active=P.activeFor(p);A.assert(active,'planet fixture missing');const age=active.age,world=G.World;
   if(reason==='pause'){G.Combat.updateFields(.5);A.assert(active.age===age,'pause advanced action');}
   if(reason==='switch'){A.select('naruto-pain-gravity');A.advance();A.assert(!P.activeFor(p),'switch retained black core');}
   if(reason==='clear'){G.Combat.clearFields(p);A.assert(!P.activeFor(p)&&!A.actors().length,'clear retained family');}
   if(reason==='death'){const naraka=P.actorsFor(p).find(b=>b.path==='naraka');naraka.hurt(naraka.maxHp+1,null,true);
     p.invuln=0;p.hurt(p.maxHp+1,null,true);A.advance();
     A.assert(p.dead&&p.hp===0&&!P.activeFor(p)&&!A.actors().length,'native lethal hit retained family');A.finish(17);
     A.assert(p.dead&&p.hp===0&&!A.actors().length,'dead Naraka revived player after terminal death');p.dead=false;}
   if(reason==='world'){G.World={...world};try{A.advance();A.assert(!P.activeFor(p),'world switch retained action')}finally{G.World=world}}
   out.push(reason);
 }
 A.reset();return out;
}"""

SOUL = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out=[];
 for(const cancel of [null,'distance','wall','body-death','switch']){
   A.reset();const b=A.actors().find(b=>b.path==='human');b.x=b.y=0;
   const e=A.spawn(140,0);p.target=e;p.aim=0;const hits=[];const hurt=e.hurt;
   e.hurt=function(...args){if(args[7]==='naruto-pain-soul')hits.push(args[0]);return hurt.apply(this,args)};
   A.castNative('naruto-pain-soul');A.advance();const action=P.activeFor(p);A.assert(action,'soul action missing');
   A.assert(e.hp===100000&&action.phase==='approach'&&b.x<10,'soul teleported or instant damage');
   for(let i=0;i<200&&P.activeFor(p)?.phase!=='grasp';i++)A.advance();
   A.assert(P.activeFor(p)?.phase==='grasp'&&Math.hypot(b.x-e.x,b.y-e.y)<=36,'soul never walked to contact');
   A.assert(e.hp===100000,'soul damage before grasp delay');
   const block=G.World.projectileBlock;
   if(cancel==='distance')e.x+=100;
   if(cancel==='wall')G.World.projectileBlock=()=>({destructible:false});
   if(cancel==='body-death')b.hurt(b.maxHp+1,null,true);
   if(cancel==='switch')A.select('naruto-pain-missiles');
   try{A.finish(.7)}finally{G.World.projectileBlock=block}
   A.assert(hits.length===(cancel?0:1),'soul cancel/single native hit '+cancel+' '+hits);
   A.assert(!e.dead,'soul became instant kill');out.push({cancel,hits});
 }
 return out;
}"""

PASSIVES = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out={absorb:[],revives:[]};
 for(const mode of ['eligible','physical','beam','ground','unmarked','outside','cooldown']){
   A.reset();const preta=A.actors().find(b=>b.path==='preta');
   A.actors().forEach((b,i)=>{b.x=-100-i*25;b.y=-200});preta.x=60;preta.y=0;
   const make=(opts={})=>G.Projectiles.spawn({friendly:false,x:85,y:0,px:120,py:0,r:3,dmg:7,painAbsorbable:true,...opts});
   if(mode==='cooldown'){const first=make();A.resume();G.Combat.resolve(.01,p,0);A.pause();A.assert(!G.Projectiles.all().includes(first),'first eligible shot not absorbed');}
   const options=mode==='physical'?{physical:true}:mode==='beam'?{beam:true}:mode==='ground'?{ground:true}:mode==='unmarked'?{painAbsorbable:false}:mode==='outside'?{y:45,py:45}:{};
   const shot=make(options),hp=p.hp,bodyHp=preta.hp;
   A.resume();G.Combat.resolve(.01,p,0);A.pause();
   const consumed=!G.Projectiles.all().includes(shot);A.assert(consumed===(mode==='eligible'),'absorption eligibility/contact/cooldown '+mode);
   A.assert(p.hp===hp&&preta.hp===bodyHp,'palm fixture unexpectedly damaged actor');out.absorb.push({mode,consumed});
 }
 // Native shooters must author eligibility; a synthetic marker alone would
 // not establish that this passive works against enemies in a real run.
 out.nativeShots=[];
 for(const type of ['fire','steel']){
   A.reset();const preta=A.actors().find(b=>b.path==='preta');A.actors().forEach((b,i)=>{b.x=-100-i*25;b.y=-200});preta.x=60;preta.y=0;
   const shooter=A.spawn(120,0);shooter.atkType=type;shooter.dmg=10;shooter.def={...shooter.def,dmg:10,shotDmg:10};
   shooter.shoot(-1,0);const shot=G.Projectiles.all().find(s=>!s.friendly);A.assert(shot,'native Enemy.shoot did not produce projectile');
   const hp=p.hp,bodyHp=preta.hp;A.resume();try{for(let i=0;i<10;i++){G.Projectiles.update(.01,p,G.EnemyMgr.all());G.Combat.resolve(.01,p,0)}}finally{A.pause()}
   const consumed=!G.Projectiles.all().includes(shot);A.assert(consumed===(type==='fire'),'native shooter absorb classification '+type);
   A.assert(p.hp===hp&&preta.hp===bodyHp,'native palm interception harmed actor');out.nativeShots.push({type,consumed,marked:shot.painAbsorbable===true||shot.ninjutsuAbsorbable===true||shot.absorbable===true});
 }
 const original=p.moves;
 try{
   p.moves=original.filter(m=>m.id!=='naruto-pain-repair');A.reset();let b=A.actors().find(b=>b.path==='asura');
   b.hurt(b.maxHp+1,null,true);const serial=b.deathSerial;A.assert(b.dead&&b.reviveRemaining===16,'body death lacks timer');
   G.Combat.updateFields(2);A.assert(b.reviveRemaining===16,'paused resurrection advanced');
   A.finish(15.9);A.assert(b.dead,'auto body revival too early');A.finish(.2);
   A.assert(!b.dead&&b.hp===b.maxHp&&b.deathSerial===serial,'16 second auto revival missing');out.revives.push('auto16');
   p.moves=original;A.reset();A.finish(12);b=A.actors().find(b=>b.path==='asura');b.hurt(b.maxHp+1,null,true);
   A.finish(9.9);A.assert(b.dead&&!P.stateFor(p).repair,'Naraka precharged or skipped initial ten second wait');A.finish(.2);
   A.assert(P.stateFor(p).repair?.target===b,'learned Naraka did not schedule repair after wait');A.finish(.9);
   A.assert(!b.dead&&P.stateFor(p).revives===1,'repair did not revive exactly once');A.finish(.5);A.assert(P.stateFor(p).revives===1,'duplicate repair revival');out.revives.push('repair');
   A.reset();b=A.actors().find(b=>b.path==='asura');const naraka=A.actors().find(b=>b.path==='naraka');
   b.hurt(b.maxHp+1,null,true);A.finish(10.1);A.assert(P.stateFor(p).repair,'cancel fixture missing repair animation');
   const remaining=b.reviveRemaining;naraka.hurt(naraka.maxHp+1,null,true);A.finish(1);
   A.assert(b.dead&&naraka.dead&&!P.stateFor(p).repair,'dead Naraka finished repair');A.assert(b.reviveRemaining<remaining&&b.reviveRemaining>remaining-1.1,'cancel reset auto revive progress');out.revives.push('cancel-naraka');
   A.reset();b=A.actors().find(b=>b.path==='preta');b.hurt(10,null,true);const before=b.hp,capacity=b.maxHp,ownerMax=p.maxHp;
   p.maxHp+=20;A.advance();A.assert(Math.abs(b.hp-before-(b.maxHp-capacity))<1e-6,'max HP upgrade failed capacity delta');
   const current=b.hp;A.finish(.5);A.assert(b.hp===current,'body regenerated missing HP every frame');p.maxHp=ownerMax;out.revives.push('capacity');
 }finally{p.moves=original;A.reset()}
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'failedRequests': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for label, viewport, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
                context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('response', lambda r: report['failedRequests'].append(r.url) if r.status >= 400 and '127.0.0.1' in r.url else None)
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.NarutoPain && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30010"]').click()
                assert page.evaluate('G.DB.save.partner===30010'), 'normal picker did not select Pain'
                page.screenshot(path=str(OUT / f'{label}-menu.png'))
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30010 && G.Game.state==="playing"')
                page.evaluate(HARNESS)
                page.evaluate(SETUP)
                report['viewports'][label] = result = {}
                for name, check in [('progression', PROGRESSION), ('formation', FORMATION), ('combat', COMBAT), ('collision', COLLISION), ('resistance', RESISTANCE), ('soul', SOUL), ('passives', PASSIVES), ('lifecycle', LIFECYCLE), ('quantity', QUANTITY)]:
                    print(label, name, flush=True)
                    result[name] = page.evaluate(check)
                result['art'] = page.evaluate(ART)
                for pose in result['art']:
                    (OUT / f'{label}-actor-{pose["path"]}.png').write_bytes(base64.b64decode(pose.pop('png').split(',', 1)[1]))
                page.evaluate('Acceptance.reset();Acceptance.select("naruto-pain-gravity");Acceptance.resume()')
                page.keyboard.press('Digit2')
                page.wait_for_function('G.Game.player.active===1')
                result['keyboardSwitch'] = page.evaluate('Acceptance.pause();G.Game.player.activeGroup().map(m=>m.id)')
                page.evaluate('Acceptance.reset()')
                page.keyboard.down('KeyD')
                result['keyboardMovement'] = page.evaluate('''() => {const A=Acceptance,p=A.p(),x=p.x;A.resume();p.update(.08);A.pause();A.assert(p.x>x&&p.walking,'keyboard movement failed');return p.x-x}''')
                page.keyboard.up('KeyD')
                if mobile:
                    page.evaluate('Acceptance.reset();Acceptance.resume()')
                    slot = page.evaluate('''() => {const p=G.Game.player,n=p.slots.length+p.moves.filter(m=>m.passive&&!p.slots.some(g=>g.includes(m))).length;return G.Touch.controlLayout(innerWidth,innerHeight,n).slots[2]}''')
                    page.touchscreen.tap(slot['x']+slot['w']/2, slot['y']+slot['h']/2)
                    page.wait_for_function('G.Game.player.active===2')
                    result['touchSwitch'] = page.evaluate('Acceptance.pause();G.Game.player.activeGroup().map(m=>m.id)')
                    page.evaluate('Acceptance.reset();Acceptance.resume()')
                    cdp = context.new_cdp_session(page)
                    base = page.evaluate('G.Touch.stickBase()')
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': base['x'], 'y': base['y']}]})
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': base['x']+45, 'y': base['y']}]})
                    result['touchMovement'] = page.evaluate('''() => {const A=Acceptance,p=A.p(),x=p.x;A.assert(G.Touch.vector()?.[0]>0,'touch vector absent');p.update(.08);A.pause();A.assert(p.x>x,'touch movement failed');return p.x-x}''')
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                for suffix in ['gravity', 'missiles', 'summon', 'soul', 'planet']:
                    page.evaluate('''suffix=>{const A=Acceptance;A.reset();A.p().target=A.spawn(100,0);A.castNative('naruto-pain-'+suffix);A.finish(.25)}''', suffix)
                    page.screenshot(path=str(OUT / f'{label}-{suffix}.png'))
                result['overflow'] = page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert result['overflow'], 'horizontal overflow'
                result['restart'] = page.evaluate('''() => {const A=Acceptance,old=G.Game.player;G.Game.toUI();G.Naruto.choose(30010);G.Flow.play();A.pause();
                  const p=G.Game.player;A.assert(p!==old&&p.dex===30010&&p.moves.length===1&&p.moves[0].id==='naruto-pain','fresh starter failed');
                  A.assert(!G.SelfClones.actors().length&&!G.NarutoPain.activeFor(old),'old run retained effects');return {dex:p.dex,moves:p.moves.map(m=>m.id)}}''')
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        assert not report['failedRequests'], report['failedRequests']
        report['ok'] = True
    except Exception as error:
        report['ok'] = False
        report['failure'] = str(error)
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': report['ok'], 'evidence': str(OUT)}))


if __name__ == '__main__':
    # Selected-skill cases above describe the original beta; movement-only
    # acceptance is now canonical. PASSIVES remains shared regression coverage.
    from test_pain_auto import main as automatic_main
    automatic_main()
