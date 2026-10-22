"""Permanent card clones through native cards, combat, damage and run lifecycle.

Run against the repository HTTP server on port 8004. The shared acceptance
harness opens terrain for deterministic fights; attacks and damage stay native.
"""
import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/self-clone'

CHECK = r"""dex => {
 const A=Acceptance,assert=A.assert,near=(a,b,label)=>assert(Math.abs(a-b)<1e-6*Math.max(1,Math.abs(b)),label+': '+a+' != '+b);
 G.Naruto.choose(dex);G.Flow.play();A.pause();A.arena();
 const p=G.Game.player,S=G.SelfClones,C=G.NarutoSkillCatalog;
 const defs=[C.byDex.get(dex),...(C.extraPools.get(dex)||[]).map(id=>G.Moves.BY_ID[id])];
 p.level=30;p.critChance=0;p.percentHealthDamage=0;p.lifestealRate=0;
 for(const def of defs)if(!p.hasMove(def.id))assert(p.addMove(def.id),'learn '+def.id);
 const step=(dt=.01)=>{A.resume();try{
   G.Combat.updateFields(dt);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,0);p.anim.update(dt);
 }finally{A.pause()}};
 const clean=()=>{G.Combat.clearFields();S.clear();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();
   p.hp=p.maxHp;p.dead=false;p.frozen=false;p.x=p.y=0;p.target=null;p.invuln=0;
   for(const m of p.moves)m.t=999;};
 const enemy=(x,y)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:9,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
   e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;};
 const card=()=>{const c=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');assert(c,'clone card absent from real offer');
   const n=S.actors().length;assert(c.apply(p)!==false,'clone card rejected');assert(S.actors().length===n+1,'one card must summon exactly one actor');return S.actors().at(-1);};
 const damage=(actor,...args)=>{A.resume();try{return actor.hurt(...args)}finally{A.pause()}};
 const withoutDodge=run=>{const random=Math.random;Math.random=()=>.99;try{return run()}finally{Math.random=random}};
 const resolveHit=()=>withoutDodge(()=>{A.resume();try{G.Combat.resolve(.01,p,0)}finally{A.pause()}});
 const exposeHp=actor=>{
   // Shield behavior has its own native suite. Remove existing armor and spend
   // the shield through native damage to isolate this actor's underlying HP.
   if(actor.dex!==30007)return;
   G.NarutoGaara.clear(actor);const shield=G.NarutoGaara.shieldState(actor),hp=actor.hp;
   if(shield?.amount>0){actor.invuln=0;damage(actor,shield.amount,null,true);near(actor.hp,hp,'shield-drain fixture lost HP')}
   actor.invuln=0;
 };
 const definition=G.LevelUp.STATS.find(c=>c.id==='selfClone');
 assert(definition&&!definition.max&&definition.icon==='selfClone','repeatable card/icon definition');
 const art=G.Icons.UI.selfClone;assert(art&&art.rows.length===12&&art.rows.every(r=>r.length===12),'dedicated pixel icon');
 for(const id of ['giant','heart','healthGrowth','lifesteal'])assert(G.Icons.url(id)!==G.Icons.url('selfClone'),'reused icon '+id);
 clean();const slots=p.slots.length,a=card(),b=card();
 assert(p.slots.length===slots,'stat card consumed active slot');
 for(const actor of [a,b]){
   assert(S.isActor(actor)&&S.isControlled(actor)&&actor!==p&&actor.sourceOwner===p,'actor identity');
   assert(actor.dex===p.dex&&actor.anim.dex===p.anim.dex,'clone appearance differs from owner');
   near(actor.hp,p.maxHp/3,'initial HP');near(actor.maxHp,p.maxHp/3,'max HP');near(actor.atk,p.atk/3,'attack');
   assert(actor.anim!==p.anim&&actor.moves!==p.moves&&actor.slots!==p.slots,'shared actor state');
   const passiveIds=['naruto-gaara','naruto-sand-shield','naruto-sharingan','naruto-gates'];
   assert(!actor.moves.some(m=>m.passive&&!passiveIds.includes(m.id)),'clone duplicated unsupported learned passive');
   for(const move of p.moves.filter(m=>m.passive)){
     const copy=actor.moves.find(m=>m.id===move.id);
     assert(copy&&copy!==move&&copy.lvl===move.lvl,'learned passive not mirrored independently '+move.id);
     assert(!actor.slots.some(group=>group.includes(copy)),'mirrored passive consumed clone active slot '+move.id);
   }
 }
 assert(a.moves!==b.moves&&a.anim!==b.anim,'clones share mutable state');
 const canvas=document.createElement('canvas');canvas.width=400;canvas.height=220;const ctx=canvas.getContext('2d');
 ctx.fillStyle='#101820';ctx.fillRect(0,0,400,220);
 for(const [actor,x] of [[p,100],[a,220],[b,320]]){ctx.save();ctx.translate(x-actor.x,180-actor.y);actor.draw(ctx);ctx.restore()}
 G.Icons.draw(ctx,'selfClone',16,16,36);const appearancePng=canvas.toDataURL();
 const spawnHp=a.maxHp,atkMul=p.atkMul;p.maxHp*=1.1;p.atkMul*=1.1;step(.001);
 near(a.maxHp,spawnHp,'spawn HP snapshot');near(a.atk,p.atk/3,'updated owner attack ratio');
 p.maxHp/=1.1;p.atkMul=atkMul;p.hp=p.maxHp;
 const hp=p.hp;exposeHp(a);a.invuln=0;damage(a,7,null,true);near(p.hp,hp,'clone damage touched player HP');near(a.hp,spawnHp-7,'clone hurt');
 a.invuln=0;damage(a,spawnHp*2,null,true);step(.01);assert(a.dead&&!S.actors().includes(a),'lethal damage retained clone');
 for(let n=0;n<40;n++)step(.1);assert(S.actors().length===1&&S.actors()[0]===b,'dead clone respawned or survivor timed out');

 // Every active signature must execute on a separate actor through the real
 // global update. Player cooldowns are held so only clone damage is measured.
 const skills=[];
 for(const def of defs.filter(d=>!d.passive||d.id==='naruto-gaara')){
   clean();if(!def.passive)A.select(def.id);
   for(const m of p.moves)m.t=999;
   const actor=card();actor.x=0;actor.y=0;actor.critChance=0;actor.invuln=999;
   const target=enemy(55,0);p.target=target;actor.target=target;actor.aim=p.aim=0;
   for(const m of actor.moves)m.t=999;
   const m=actor.moves.find(m=>m.id===def.id);assert(m,'clone missing selected move '+def.id);m.t=0;
   const ownerMove=p.moves.find(n=>n.id===def.id),ownerCd=ownerMove.t;
   assert(m!==ownerMove,'shared cooldown '+def.id);
   const calls=[],hits=[],nativeCast=actor.cast,nativeHurt=target.hurt;
   actor.cast=function(move,...args){calls.push(move.id);return nativeCast.call(this,move,...args)};
   target.hurt=function(...args){hits.push({damage:args[0],source:args[6],move:args[7]});return nativeHurt.apply(this,args)};
   // Ongoing fields and long windups use small native steps, not a fake cast.
   for(let n=0;n<850;n++){
     step(.01);
     // Enemy AI stays stationary; native dash/grab actions may position it.
     target.kx=target.ky=0;G.EnemyMgr.rebuildGrid();
     if(calls.includes(def.id)&&n>220&&def.id!=='naruto-sand-prison')break;
   }
   assert(calls.includes(def.id)||def.id==='naruto-sand-prison'&&G.NarutoGaara.sandPrisonState(actor),'clone failed selected skill '+def.id);
   near(ownerMove.t,ownerCd,'clone changed owner cooldown '+def.id);
   assert(calls.every(id=>id===def.id||id==='naruto-gaara'||!defs.some(d=>d.id===id)),'unselected learned skill cast '+def.id+': '+calls);
   // The real owner's selected prison advances globally without Combat.tick;
   // its legitimate hits coexist with the separately owned clone field.
   const skillHits=hits.filter(h=>h.move===def.id&&(def.id!=='naruto-sand-prison'||h.source!==p));
   assert(skillHits.every(h=>h.source===actor),'lost clone damage source '+def.id);
   const support=['naruto-shadow-clones','naruto-nine-tails-cloak'];
   if(!support.includes(def.id))assert(skillHits.some(h=>h.damage>0),'clone attack never hurt target '+def.id);
   skills.push({id:def.id,casts:calls.length,hits:skillHits.length,damage:skillHits.reduce((sum,h)=>sum+h.damage,0)});
   if(def.id==='naruto-gaara'){
     // Compare native hit payloads against the real player, including the
     // technique's level bonus and type/weather multipliers, before rounding.
     const cloneDamage=skillHits[0].damage;S.clear();G.NarutoGaara.clear(p);G.EnemyMgr.clear();G.Projectiles.clear();
     const target=enemy(55,0);p.target=target;const damage=[];const hurt=target.hurt;
     target.hurt=function(...args){if(args[7]===def.id)damage.push(args[0]);return hurt.apply(this,args)};
     A.resume();try{G.Combat.tick(.61,p,0)}finally{A.pause()}
     for(let n=0;n<100&&!damage.length;n++)step(.01);
     assert(damage.length,'real-owner damage baseline missing');near(cloneDamage*3,damage[0],'native clone damage must equal one third');
     skills.at(-1).verifiedDamageRatio=cloneDamage/damage[0];
   }
 }

 // Selection changes must reach existing clones without replacing their owned
 // move objects or borrowing the player's cooldown.
 const selectable=defs.filter(d=>!d.passive);
 if(selectable.length>1){
   clean();A.select(selectable[0].id);const actor=card();
   const oldMoves=actor.moves,oldAnim=actor.anim;
   A.select(selectable[1].id);for(const m of p.moves)m.t=999;
   enemy(55,0);step(.001);
   assert(actor.activeGroup().some(m=>m.id===selectable[1].id),'existing clone did not follow selected slot');
   assert(oldMoves.every(m=>actor.moves.find(n=>n.id===m.id)===m)&&actor.anim===oldAnim,'switch replaced clone move/animation state');
 }
 let cloakRegression=null;
 if(dex===30001){
   clean();A.select('naruto-nine-tails-cloak');for(const m of p.moves)m.t=999;
   const actor=card();actor.x=actor.y=0;const target=enemy(60,0);p.target=actor.target=target;
   for(const m of actor.moves)m.t=999;const move=actor.moves.find(m=>m.id==='naruto-nine-tails-cloak');
   const baseAtk=actor.atk,baseSpd=actor.spd,ownerAtk=p.atk,ownerSpd=p.spd;
   actor.invuln=0;let before=actor.hp;damage(actor,8);const plain=before-actor.hp;actor.hp=actor.maxHp;
   move.t=0;step(.01);move.t=999;
   const effect=G.NarutoSupport.effects.find(f=>f.owner===actor&&f.mode==='nine-tails-cloak');
   assert(effect&&!G.NarutoSupport.effects.some(f=>f.owner===p&&f.mode==='nine-tails-cloak'),'cloak fixture must affect clone only');
   assert(actor.atk>baseAtk&&actor.spd>baseSpd,'clone-only cloak failed attack/speed bonuses');
   near(p.atk,ownerAtk,'clone cloak changed owner attack');near(p.spd,ownerSpd,'clone cloak changed owner speed');
   actor.invuln=0;before=actor.hp;damage(actor,8);const protectedDamage=before-actor.hp;
   near(protectedDamage,plain*effect.m.damageTakenMul,'clone-only cloak damage reduction');
   const duration=effect.ttl;for(let age=0;age<duration+.2;age+=.1)step(.1);
   assert(!G.NarutoSupport.effects.some(f=>f.owner===actor&&f.mode==='nine-tails-cloak'),'clone cloak never expired');
   near(actor.atk,baseAtk,'expired clone cloak attack');near(actor.spd,baseSpd,'expired clone cloak speed');
   cloakRegression={boosted:true,reducedDamage:protectedDamage/plain,expired:true};
 }
 // Simultaneous long actions must preserve independent owner states. The
 // first frame is sufficient to catch singleton chain/state implementations.
 const concurrentId=dex===30002?C.byDex.get(dex).id:dex===30006?'naruto-reverse-lotus':dex===30007?'naruto-sand-coffin':null;
 if(concurrentId&&p.hasMove(concurrentId)){
   clean();A.select(concurrentId);const group=[p,card(),card()];
   group.forEach((actor,i)=>{actor.x=i*15;actor.y=0;actor.invuln=999;actor.target=enemy(i*15+60,i*15);
     for(const m of actor.moves)m.t=m.id===concurrentId?0:999;});
   A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()}step(.001);
   const state=actor=>dex===30002?G.NarutoChidori.activeFor(actor):dex===30006?G.NarutoLee.activeFor(actor):G.NarutoGaara.active(actor);
   const states=group.map(state);assert(states.every(Boolean)&&new Set(states).size===3,'concurrent action states interfere '+concurrentId);
   S.clear(p);assert(state(p)===states[0],'clearing clones cancelled real owner action');
 }
 clean();const clone=card(),other=card();clone.x=240;clone.y=0;other.x=-240;other.y=0;
 for(const actor of [clone,other])for(const m of actor.moves)m.t=999;
 exposeHp(clone);const e=enemy(clone.x,clone.y);clone.invuln=0;const before=clone.hp,ownerHp=p.hp;
 resolveHit();
 assert(clone.hp<before&&p.hp===ownerHp,'enemy contact did not damage independent clone');
 G.EnemyMgr.clear();clone.invuln=0;const beforeShot=clone.hp;
 G.Projectiles.all().push({friendly:false,x:clone.x,y:clone.y,r:3,dmg:7,mtype:'normal',color:'#f00',vx:0,vy:0});
 resolveHit();
 assert(clone.hp<beforeShot&&p.hp===ownerHp,'enemy shot did not damage independent clone');
 const state=()=>JSON.stringify(S.actors().map(a=>[a.x,a.y,a.hp,...a.moves.filter(m=>!m.passive).map(m=>m.t)]));
 const paused=state();G.Combat.updateFields(.5);assert(state()===paused,'paused clones advanced '+dex+': '+paused+' -> '+state());
 p.frozen=true;const frozen=state();step(.5);assert(state()===frozen,'frozen owner clones advanced');p.frozen=false;
 const camera={x:G.Camera.x,y:G.Camera.y};step(.01);assert(G.Camera.x===camera.x&&G.Camera.y===camera.y,'clone movement drove owner camera');
 clean();const doomed=card();doomed.x=240;doomed.y=0;doomed.invuln=0;
 const ownedShot=G.Projectiles.spawn({owner:doomed,x:2000,y:2000,hits:new Set()});
 const hostile=G.Projectiles.spawn({friendly:false,x:doomed.x,y:doomed.y,dmg:doomed.maxHp*100,r:3});
 const unrelated=G.Projectiles.spawn({owner:p,x:50000,y:50000,hits:new Set()});
 const touching=enemy(doomed.x,doomed.y);let strikes=0;const strike=touching.strike;
 touching.strike=function(...args){strikes++;return strike.apply(this,args)};
 resolveHit();
 assert(doomed.dead&&!G.Projectiles.all().includes(hostile)&&!G.Projectiles.all().includes(ownedShot),'lethal hostile left dead clone projectiles');
 assert(G.Projectiles.all().includes(unrelated),'lethal clone cleanup removed unrelated projectile');
 assert(strikes===0,'enemy contact struck clone after lethal projectile');
 clean();const lavaActor=card();lavaActor.x=240;lavaActor.y=0;exposeHp(lavaActor);lavaActor.invuln=0;
 for(const m of lavaActor.moves)m.t=999;const isLiquid=G.World.isLiquid,liquidEffect=G.World.liquidEffect;
 const lavaHp=lavaActor.hp,safeHp=p.hp;
 G.World.isLiquid=(x,y)=>x>100;G.World.liquidEffect=()=>({slow:.5,dmg:.02,flat:4,every:.5});
 try{withoutDodge(()=>step(.05));A.resume();try{p.update(.05)}finally{A.pause()}
   assert(lavaActor.hp<lavaHp&&p.hp===safeHp,'clone lava failed independent tile damage');
   assert(lavaActor.inLiquid&&!p.inLiquid&&lavaActor.spd<p.spd,'clone liquid slowdown used owner tile');
 }finally{G.World.isLiquid=isLiquid;G.World.liquidEffect=liquidEffect}
 // Existing generic actors learn upgraded passive ranks through actual cards.
 // Effective attack must remain one third after every derived passive sync.
 clean();const upgradedActor=card(),passiveUpgrades=[];
 for(const move of p.moves.filter(m=>m.passive)){
   while(move.lvl<5){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+move.id);
     assert(card&&card.apply(p)!==false,'real passive upgrade unavailable '+move.id);step(.001);
     const copy=upgradedActor.moves.find(m=>m.id===move.id);
     assert(copy&&copy!==move&&copy.lvl===move.lvl,'existing clone did not inherit passive rank '+move.id);
     near(upgradedActor.atk,p.atk/3,'duplicated effective passive attack '+move.id+' '+move.lvl);
   }
   passiveUpgrades.push({id:move.id,level:move.lvl});
 }
 const lifecycle=[];
 for(const reason of ['clear','owner-death','world','owner','new-run']){
   clean();const actor=card();const game=G.Game,world=G.World;
   if(reason==='clear')G.Combat.clearFields(p);
   if(reason==='owner-death')p.dead=true;
   if(reason==='world')G.World={...world};
   if(reason==='owner')G.Game={...game,get state(){return game.state},player:Object.assign(Object.create(Object.getPrototypeOf(p)),p)};
   if(reason==='new-run')G.Game.startRun();
   try{step(.01)}finally{G.Game=game;G.World=world;p.dead=false}
   assert(!S.actors().includes(actor),'clone leaked after '+reason);lifecycle.push(reason);
   if(reason==='new-run')break;
 }
 return {dex,ratio:1/3,repeatable:true,skills,enemyContact:true,enemyShot:true,pause:true,freeze:true,
   inventory:defs.map(d=>({id:d.id,category:d.id==='naruto-gaara'?'automatic':d.passive?'passive':'active'})),passiveUpgrades,
   lethalProjectileCleanup:true,lava:true,cloakRegression,lifecycle,appearancePng};
}"""

EXTRAS = r"""() => {
 const A=Acceptance,assert=A.assert,near=(a,b,label)=>assert(Math.abs(a-b)<1e-6,label+': '+a+' != '+b),out=[];
 for(const dex of [25,G.Digimon.records.keys().next().value]){
   G.DB.save.partner=dex;G.DB.save.partnerShiny=false;
   // The public beta hides Digimon; temporarily permit its existing registered
   // partner to exercise the retained battle implementation through startRun.
   const enabled=G.Digimon.enabled;if(G.Digimon.records.has(dex))G.Digimon.enabled=true;
   try{G.Game.startRun()}finally{G.Digimon.enabled=enabled}A.pause();A.arena();
   const p=G.Game.player,S=G.SelfClones;p.critChance=0;p.percentHealthDamage=0;p.damageSplashPicks=0;
   assert(p.dex===dex,'generic partner was replaced by beta roster fallback '+dex+' -> '+p.dex);
   const ownerMove=p.activeMove();assert(ownerMove&&!ownerMove.passive,'generic hero starter unavailable '+dex);ownerMove.t=999;
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');assert(card&&card.apply(p)!==false,'generic clone card missing '+dex);
   const actor=S.actors()[0];actor.x=actor.y=0;actor.invuln=999;
   const spawn=(x,y)=>{const e=new G.Enemy({dex:19,hp:30000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
     e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;};
   const target=spawn(60,0);p.target=target;actor.target=target;const hits=[],hurt=target.hurt;
   target.hurt=function(...args){hits.push({amount:args[0],source:args[6],move:args[7]});return hurt.apply(this,args)};
   const step=dt=>{A.resume();try{G.Combat.updateFields(dt);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,0)}finally{A.pause()}};
   for(let n=0;n<400&&!hits.length;n++)step(.01);
   assert(hits.some(h=>h.source===actor&&h.move===ownerMove.id&&h.amount>0),'generic selected skill clone damage missing '+dex);
   S.clear();G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();
   p.percentHealthDamage=.03;p.damageSplashPicks=2;
   const c=S.summon(p);near(c.percentHealthDamage,p.percentHealthDamage/3,'percent-health clone rate');
   const full=spawn(200,0),third=spawn(400,0);
   full.hurt(90,'#fff',0,0,0,null,p,ownerMove.id);third.hurt(90,'#fff',0,0,0,null,c,ownerMove.id);
   const ownerBonus=full.maxHp-full.hp-90,cloneBonus=third.maxHp-third.hp-90;
   assert(ownerBonus>0&&cloneBonus>0,'owned percent-health bonus rejected generic actor '+dex);
   near(cloneBonus*3,ownerBonus,'native percent-health damage ratio');
   const primary=spawn(1000,0),secondary=spawn(1030,0),before=secondary.hp;
   const dealt=G.DamageSplash.hit(c,primary,150,'#fff',ownerMove.id);
   near(before-secondary.hp,30,'clone splash damage must omit secondary percent-health bonus');near(dealt,30,'clone accepted by splash ownership');
   out.push({dex,move:ownerMove.id,nativeCloneDamage:true,ownerBonus,cloneBonus,splash:dealt});S.clear();
 }
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'viewports': {}, 'errors': []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in [False, True]:
                context = browser.new_context(
                    viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900},
                    is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.SelfClones && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.evaluate(HARNESS)
                label = 'mobile' if mobile else 'desktop'
                results = report['viewports'][label] = []
                for dex in [30001, 30002, 30006, 30007]:
                    result = page.evaluate(CHECK, dex)
                    png = result.pop('appearancePng')
                    (OUT / f'{label}-{dex}.png').write_bytes(base64.b64decode(png.split(',', 1)[1]))
                    results.append(result)
                report.setdefault('genericHeroes', {})[label] = page.evaluate(EXTRAS)
                page.screenshot(path=str(OUT / f'{label}.png'))
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'viewports': list(report['viewports']), 'heroes': 4,
                      'skills': sum(len(r['inventory']) for r in report['viewports']['desktop'])}))


if __name__ == '__main__':
    main()
