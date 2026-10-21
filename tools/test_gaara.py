"""Gaara acceptance through the default picker, native combat and authored art.

Run with the repository HTTP server on port 8004. Terrain is opened only for
controlled combat fixtures; enemy hurt, player hurt and input remain native.
"""
import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_redrawn_heroes import AUDIT
from test_gaara_redesign import PROJECTILES, PRIORITY, TIMING, SHIELD_CONTEXT
from test_gaara_growth import GROWTH, PRISON, RESTART, capture_prison

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/gaara'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=gaara'

SETUP = r"""() => {
 const A=Acceptance,p=A.p();
 A.gaaraArena=()=>{A.arena();p.percentHealthDamage=0;p.lifestealRate=0;p.critChance=0;p.quantityBonus=0;p.target=null};
 A.spawn=(x,y,boss=false)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
   e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
 A.actualCast=id=>{const m=A.select(id);let n=0;const cast=p.cast;
   p.cast=function(...args){n++;return cast.apply(this,args)};
   try{A.resume();G.Combat.tick(.001,p,0)}finally{p.cast=cast;A.pause()}
   A.assert(n===1,'native Combat.tick did not cast '+id+' count='+n);return m};
 A.advance=dt=>{A.resume();try{G.Combat.updateFields(dt);p.anim.update(dt)}finally{A.pause()}};
 A.finish=(limit=4)=>{const phases=[];for(let n=0;n<limit*100&&G.NarutoGaara.active(p);n++){
   const s=G.NarutoGaara.active(p);phases.push(s.phase);A.advance(.01)}
   A.assert(!G.NarutoGaara.active(p),'Gaara action did not finish');return [...new Set(phases)]};
 A.gaaraArena();
}"""

PROGRESSION = r"""() => {
 const A=Acceptance,p=A.p(),out={levels:[],isolated:[]},starter='naruto-gaara',ids=['naruto-sand-coffin','naruto-sand-shield','naruto-sand-tsunami'];
 A.assert(p.moves.length===1&&p.hasMove(starter),'Gaara must start with sandburst only');
 for(const level of [1,3,6,9]){
   p.level=level;const pool=G.Moves.poolFor(p.mon),cards=G.LevelUp.offer(p,100);
   ids.forEach((id,i)=>{const eligible=level>=[3,6,9][i];A.assert(pool.includes(id)===eligible,'pool gate '+id+' Lv'+level);
     A.assert(cards.some(c=>c.key==='new:'+id)===eligible,'learn card gate '+id+' Lv'+level)});
   out.levels.push({level,pool,cards:cards.map(c=>c.key)});
 }
 const original=p.mon;
 for(const dex of [30001,30002,30006,20001]){
   p.mon=G.DEX.find(m=>m.dex===dex)||{dex,gen:10,types:['normal']};
   A.assert(!G.Moves.poolFor(p.mon).some(id=>[starter,...ids].includes(id)),'Gaara skills leaked into '+dex);out.isolated.push(dex);
 }p.mon=original;p.level=12;
 for(const id of ids){const n=p.slots.length,card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
   A.assert(card&&card.apply(p)!==false,'learn actual signature '+id);
   if(id==='naruto-sand-shield'){
     A.assert(p.slots.length===n&&!p.slots.some(s=>s.some(m=>m.id===id)),'passive consumed active slot');
     A.advance(.001);A.shieldPose=A.render();
     A.assert(A.shieldPose.state.key==='gaara-shield','learned shield never used dedicated animation');
   }
 }
 A.assert(p.moves.length===4&&p.slots.length===3,'incomplete Gaara loadout');
 return {...out,slots:p.slots.length};
}"""

COMBAT = r"""() => {
 const A=Acceptance,p=A.p(),out={};
 for(const id of ['naruto-gaara','naruto-sand-coffin','naruto-sand-tsunami']){
   A.gaaraArena();const es=[A.spawn(70,-25),A.spawn(95,0),A.spawn(70,25),A.spawn(-250,300)];p.target=es[1];p.aim=0;
   const hits=es.map(()=>0),owned=es.map(()=>true);
   es.forEach((e,i)=>{const hurt=e.hurt;e.hurt=function(...args){hits[i]++;owned[i]&&=args[6]===p;return hurt.apply(this,args)}});
   const m=A.actualCast(id),s=G.NarutoGaara.active(p);
   A.assert(s&&s.owner===p&&s.move.id===m.id,'missing owned Gaara action '+id);
   const phases=A.finish(),damage=es.map(e=>100000-e.hp);
   if(id==='naruto-sand-coffin')A.assert(damage[es.indexOf(s.target)]>0&&damage.filter(n=>n>0).length===1,'coffin hit another target '+damage);
   else if(id==='naruto-gaara')A.assert(damage[1]>0&&damage.filter(n=>n>0).length===1,'sand shower splashed '+damage);
   else A.assert(damage.slice(0,3).every(n=>n>0)&&damage[3]===0,'dispersed AOE coverage '+id+' '+damage);
   A.assert(owned.every(Boolean),'Gaara bypassed native owned hurt '+id);
   const expected=id==='naruto-gaara'?['windup','release','recovery']:id==='naruto-sand-coffin'?['seal','bind','crush','recovery']:['seal','raise','surge','burial','impact','recovery'];
   A.assert(phases.join(',')===expected.join(','),'missing/out-of-order phases '+id+' '+phases);
   const count=id==='naruto-gaara'?3:id==='naruto-sand-tsunami'?2:1;
   A.assert(hits.every((n,i)=>n===(damage[i]>0?count:0)),'duplicate/missing native damage '+id+' '+hits);
   const before=damage.slice();for(let n=0;n<100;n++)A.advance(.01);
   A.assert(es.every((e,i)=>100000-e.hp===before[i]),'completed action dealt duplicate damage '+id);
   out[id]={damage,hits,phases,cooldown:m.cd};
 }
 // The far fan corner belongs to the authored rectangular footprint even when
 // its radial distance exceeds the forward reach.
 A.gaaraArena();const center=A.spawn(300,0),corner=A.spawn(300,100),outside=A.spawn(300,130);p.target=center;p.aim=0;
 A.actualCast('naruto-sand-tsunami');A.finish();
 A.assert(center.hp<100000&&corner.hp<100000&&outside.hp===100000,'tsunami fan corner clipped or outside width hit');
 out.farCorner=[center,corner,outside].map(e=>100000-e.hp);
 return out;
}"""

CLEANUP = r"""() => {
 const A=Acceptance,p=A.p(),out=[];
 for(const reason of ['clear','owner-death','world','owner']){
   A.gaaraArena();p.target=A.spawn(90,0);p.aim=0;A.actualCast('naruto-sand-coffin');A.advance(.12);
   A.assert(G.NarutoGaara.active(p),'cleanup fixture missing');
   const world=G.World,game=G.Game;
   if(reason==='clear')G.Combat.clearFields(p);
   if(reason==='owner-death')p.dead=true;
   if(reason==='world')G.World={...world};
   if(reason==='owner')G.Game={...game,get state(){return game.state},player:{...p}};
   try{A.advance(.01)}finally{G.World=world;G.Game=game;p.dead=false}
   A.assert(!G.NarutoGaara.active(p),'action leaked after '+reason);out.push(reason);
 }
 A.gaaraArena();p.target=A.spawn(90,0);A.actualCast('naruto-sand-coffin');A.advance(.1);
 const s=G.NarutoGaara.active(p),age=s.age;G.Combat.updateFields(.5);
 A.assert(G.NarutoGaara.active(p)===s&&s.age===age,'paused action advanced');G.Combat.clearFields(p);out.push('pause');
 return out;
}"""

CONTROL = r"""() => {
 const A=Acceptance,p=A.p(),out=[];
 for(const id of ['naruto-sand-coffin','naruto-sand-tsunami'])for(const boss of [false,true]){
   A.gaaraArena();const e=A.spawn(90,0,boss);p.target=e;p.aim=0;A.actualCast(id);
   const states=[];for(let n=0;n<100&&!(e.slow>0);n++){A.advance(.01);states.push(G.NarutoGaara.active(p)?.phase)}
   const expected=boss?(id==='naruto-sand-coffin'?.3:.35):.95;
   A.assert(Math.abs(e.slow-expected)<1e-6,'boss/normal control strength '+id+' '+boss+' '+e.slow);
   const age=G.NarutoGaara.active(p).age;G.Combat.updateFields(.3);
   A.assert(G.NarutoGaara.active(p).age===age&&e.slow===expected,'pause changed control');
   G.Combat.clearFields(p);A.assert(e.slow===0&&e.slowT===0,'cancel left sand control');
   out.push({id,boss,strength:expected,phases:states});
 }
 // Expiry of our pulse preserves a stronger pre-existing native slow.
 A.gaaraArena();const e=A.spawn(90,0);e.applySlow(.99,5);p.target=e;
 A.actualCast('naruto-sand-coffin');A.advance(.3);G.Combat.clearFields(p);
 A.assert(e.slow===.99&&e.slowT>0,'sand cancellation removed external control');
 for(const natural of [false,true]){
   A.gaaraArena();const e=A.spawn(90,0);e.applySlow(.2,5);p.target=e;A.actualCast('naruto-sand-coffin');
   let elapsed=0;const nativeStep=()=>{A.advance(.01);A.resume();try{e.update(.01,p)}finally{A.pause()}elapsed+=.01};
   for(let n=0;n<40;n++)nativeStep();A.assert(e.slow===.95,'sand failed to override weaker external slow');
   if(natural){while(G.NarutoGaara.active(p)&&elapsed<4)nativeStep()}else G.Combat.clearFields(p);
   A.assert(Math.abs(e.slow-.2)<1e-6&&Math.abs(e.slowT-(5-elapsed))<.04,'Gaara extended strong control or lost weaker baseline '+natural+' '+e.slow+'/'+e.slowT+'/'+elapsed);
   while(elapsed<5.03)nativeStep();A.assert(e.slow===0,'native enemy remained controlled after baseline expiry');
   out.push({externalWeak:true,natural,elapsed});
 }
 A.gaaraArena();const mid=A.spawn(90,0);p.target=mid;A.actualCast('naruto-sand-coffin');A.advance(.3);
 mid.applySlow(.99,3);G.Combat.clearFields(p);A.assert(mid.slow===.99&&mid.slowT>2.9,'new external strong control removed');
 // A dead target cancels coffin without a delayed damage event.
 A.gaaraArena();p.target=A.spawn(90,0);A.actualCast('naruto-sand-coffin');A.advance(.3);
 p.target.dead=true;A.advance(.01);A.assert(!G.NarutoGaara.active(p)&&p.target.slow===0,'dead target retained coffin');
 return out;
}"""

UPGRADES = r"""() => {
 const A=Acceptance,p=A.p(),out={},original=p.cdMul;
 for(const id of ['naruto-gaara','naruto-sand-coffin','naruto-sand-tsunami']){
   const m=p.moves.find(m=>m.id===id),cd=id==='naruto-gaara'?1.2:id==='naruto-sand-tsunami'?8:5;out[id]=[];
   for(let level=1;level<=5;level++){
     if(level>1){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(card&&card.apply(p)!==false,'upgrade card '+id+' '+level)}
     A.assert(m.lvl===level&&m.cd===cd&&!m.minCooldown,'skill upgrade changed base CD '+id+' '+level);
     A.gaaraArena();p.cdMul=.92;p.target=A.spawn(90,0);A.actualCast(id);
     A.assert(Math.abs(m.t-cd*.92)<1e-6,'cooldown modifier ignored '+id);
     if(id==='naruto-gaara'){
       const bases=[3,3,4,4,5],totals=[28,34,34,42,52],ranges=[260,260,280,280,300];
       A.assert(m.count===bases[level-1]&&Math.abs(m.dmg-totals[level-1])<1e-6&&m.range===ranges[level-1],'sand shower level contract '+level);
       G.Combat.clearFields(p);
       for(const bonus of [0,2,20]){
         A.gaaraArena();p.quantityBonus=bonus;const e=A.spawn(230,0);p.target=e;let hits=0,raw=0;const hurt=e.hurt;e.hurt=function(...args){hits++;raw+=args[0];return hurt.apply(this,args)};
         A.actualCast(id);const f=G.NarutoGaara.active(p);A.assert(f.count===m.count+bonus,'quantity applied twice');
         for(let n=0;n<200;n++)A.advance(.01);
         const expected=m.dmg*(m.count+bonus)/m.count*p.atk*G.Types.mult(m.type,e.types)*G.Weather.mult(m.type);
         A.assert(hits===m.count+bonus&&Math.abs(raw-expected)<1e-5&&100000-e.hp===Math.round(expected/(m.count+bonus))*(m.count+bonus),'upgraded bullet count/damage '+level+'/'+bonus+' '+hits+'/'+(100000-e.hp));
         A.assert(!G.NarutoGaara.active(p)&&!G.NarutoGaara.bullets.length,'quantity burst remained active');
       }
     }
     out[id].push({level,damage:m.dmg,count:m.count,cd:m.cd,actual:m.t});
   }
 }p.cdMul=original;A.gaaraArena();return out;
}"""

SHIELD = r"""() => {
 const A=Acceptance,p=A.p(),out=[],near=(a,b)=>Math.abs(a-b)<1e-6;
 const m=p.moves.find(m=>m.id==='naruto-sand-shield'),baseHp=p.maxHp,cd=p.cdMul;
 for(let level=1;level<=5;level++){
   if(level>1){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+m.id);A.assert(card&&card.apply(p)!==false,'shield upgrade card '+level)}
   A.gaaraArena();A.advance(.001);
   const capacity=[45,60,75,90,110][level-1]+p.level*level,s=G.NarutoGaara.shieldState(p);
   A.assert(s&&s.capacity===capacity&&s.amount===capacity&&G.NarutoGaara.shieldStage(p)===level,'shield stage capacity '+level);
   const hp=p.hp;p.invuln=0;p.hurt(capacity-5,null,true);
   A.assert(p.hp===hp&&near(G.NarutoGaara.shieldState(p).amount,5),'shield failed real hurt absorption');
   p.invuln=0;p.hurt(12,null,true);
   A.assert(near(p.hp,hp-7)&&G.NarutoGaara.shieldState(p).amount===0,'shield overflow native damage wrong');
   const hurtHp=p.hp;A.advance(.3);A.assert(p.hp===hurtHp,'shield healed HP');
   const remaining=G.NarutoGaara.shieldState(p).remaining;A.advance(remaining-.01);
   A.assert(G.NarutoGaara.shieldState(p).amount===0,'shield refreshed early');A.advance(.02);
   A.assert(G.NarutoGaara.shieldState(p).amount===capacity&&p.hp===hurtHp,'shield did not refresh without HP heal');
   A.advance(.2);A.assert(G.NarutoGaara.shieldState(p).amount===capacity,'shield stacked above capacity');
   A.assert(p.maxHp===baseHp&&!p.slots.some(s=>s.includes(m)),'shield mutated health or active slots');
   out.push({level,capacity,hpOverflow:hp-p.hp,refresh:12*p.cdMul});
 }
 // Obtain a real cooldown card and check the passive refresh's remaining time.
 const counts={...p.statsTaken};p.statsTaken={...counts,cd:0};
 try{
   p.cdMul=1;let card;for(let n=0;n<40&&!card;n++)card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:cd');
   A.assert(card&&card.apply(p)!==false,'real cooldown card unavailable');
   A.gaaraArena();A.advance(.001);const s=G.NarutoGaara.shieldState(p);
   A.assert(near(s.remaining,12*.92-.001),'cooldown card did not optimize shield refresh');
   const progress=s.progress;G.Combat.updateFields(1);A.assert(G.NarutoGaara.shieldState(p).progress===progress,'paused shield refreshed');
 }finally{p.statsTaken=counts;p.cdMul=cd}
 // The native HUD must include the slotless passive card.
 for(const lethal of [false,true]){
   A.gaaraArena();A.advance(.001);const s=G.NarutoGaara.shieldState(p);if(lethal)p.hp=.25;
   const hp=p.hp;p.invuln=0;p.hurt(s.amount+.5,null,true);
   A.assert(G.NarutoGaara.shieldState(p)?.amount===0||lethal,'fractional overflow shield not depleted');
   A.assert(lethal?p.dead&&p.hp===0:!p.dead&&near(p.hp,hp-.5),'fractional native overflow wrong '+lethal);
 }
 A.gaaraArena();A.advance(.001);
 const cv=document.createElement('canvas');cv.width=innerWidth;cv.height=innerHeight;const ctx=cv.getContext('2d'),texts=[],draw=ctx.fillText.bind(ctx);
 ctx.fillText=(text,...args)=>{texts.push(String(text));return draw(text,...args)};
 G.HUD.draw(ctx,cv.width,cv.height,p,{time:30});
 A.assert(texts.some(s=>s.includes(m.name)||s.includes('砂')),'native HUD omitted sand shield');
 return {stages:out,cooldownCard:true,pause:true,hudTexts:texts};
}"""

BASIC = r"""() => {
 const A=Acceptance,p=A.p(),out=[];
 for(const id of ['naruto-sand-coffin','naruto-sand-tsunami']){
   G.Combat.clearFields(p);A.gaaraArena();const m=A.select(id);m.t=10;p.target=A.spawn(90,0);const casts=[],cast=p.cast;
   const slots=p.slots.slice(),active=p.active,shield=G.NarutoGaara.shieldStage(p),fn=p.activeGroup;
   p.cast=function(move,...args){casts.push(move.id);return cast.call(this,move,...args)};
   try{A.resume();G.Combat.tick(.61,p,0)}finally{p.cast=cast;A.pause()}
   A.assert(casts.length===1&&casts[0]==='naruto-gaara','cooldown window did not use real sand basic '+id+' '+casts);
   A.assert(G.NarutoGaara.active(p)?.move.id==='naruto-gaara','basic had no actual sand action');
   A.assert(Math.abs(m.t-9.39)<1e-6,'selected timer advanced twice during basic');
   A.assert(p.active===active&&p.activeGroup===fn&&p.slots.every((s,i)=>s===slots[i]),'basic changed selected slots');
   A.assert(G.NarutoGaara.shieldStage(p)===shield,'switch/basic lost passive shield');
   out.push({selected:id,basic:casts[0],cooldown:m.t});
 }
 return out;
}"""

ART = r"""() => {
 const A=Acceptance,p=A.p(),out={shield:A.shieldPose};A.gaaraArena();
 for(const [direction,dir] of [['down',0],['right',2],['up',4],['left',6]]){
   p.anim.dir=dir;p.walking=false;p.anim.loop('Idle');p.anim.play('Idle');out['idle-'+direction]=A.render();
   p.walking=true;p.anim.play('Walk');out['movement-'+direction]=A.render();
   A.assert(out['idle-'+direction].state.key==='gaara-idle'&&out['movement-'+direction].state.key==='gaara-movement','common direction mapping '+direction);
 }
 A.gaaraArena();A.advance(.001);p.invuln=0;p.hurt(G.NarutoGaara.shieldState(p).amount+1,null,true);out.hurt=A.render();out.flash=A.render(p.anim,{flash:true,alpha:.5});
 A.assert(out.hurt.state.key==='gaara-hurt','native HP damage did not render hurt');
 A.gaaraArena();p.dead=true;p.hp=0;p.anim.play('Faint',{hold:true});out.death=A.render();
 A.assert(out.death.state.key==='gaara-death','dead actor did not render dedicated death');
 p.dead=false;p.hp=p.maxHp;p.anim.play('Idle');
 for(const [id,key] of [['naruto-gaara','gaara-sand-burst'],['naruto-sand-coffin','gaara-coffin'],['naruto-sand-tsunami','gaara-tsunami']]){
   A.gaaraArena();p.target=A.spawn(90,0);p.aim=0;A.actualCast(id);
   for(let n=0;n<12;n++){if(n)A.advance(.08);out[id+'-'+n]=A.render()}
   A.assert(Object.entries(out).some(([name,sample])=>name.startsWith(id+'-')&&sample.state.key===key),'dedicated art missing '+id);
 }
 for(const [name,sample] of Object.entries(out)){
   A.assert(sample.sources.length&&sample.sources.every(src=>new URL(src).pathname.includes('/redrawn/gaara-')),'non-Gaara source '+name);
   A.assert(sample.state.key.startsWith('gaara-'),'non-Gaara sequence '+name);
 }
 return out;
}"""


def capture_effects(page, label):
    """Capture the native game canvas, including ground and air effects."""
    cases = [
        ('sand-flight', 'naruto-gaara', .25),
        ('coffin-bind', 'naruto-sand-coffin', .5),
        ('coffin-crush', 'naruto-sand-coffin', 1.35),
        ('tsunami-surge', 'naruto-sand-tsunami', .8),
        ('tsunami-burial', 'naruto-sand-tsunami', 1.35),
        ('tsunami-impact', 'naruto-sand-tsunami', 1.65),
    ]
    result = {}
    for name, move, age in cases:
        result[name] = page.evaluate("""([id,age]) => {
          const A=Acceptance,p=A.p();A.gaaraArena();p.target=A.spawn(230,0);p.aim=0;A.actualCast(id);
          for(let elapsed=0;elapsed<age-1e-8;elapsed+=.01)A.advance(Math.min(.01,age-elapsed));
          const f=G.NarutoGaara.active(p);return {phase:f?.phase,age:f?.age,bullets:G.NarutoGaara.bullets.length};
        }""", [move, age])
        page.locator('#game').screenshot(path=str(OUT / f'{label}-effect-{name}.png'))
    for name, context in [('right', {'fromX': 100, 'fromY': 0}),
                          ('down', {'fromX': 0, 'fromY': 100}),
                          ('left', {'fromX': -100, 'fromY': 0}),
                          ('up', {'fromX': 0, 'fromY': -100}),
                          ('neutral', None), ('broken', {'fromX': 100, 'fromY': 0})]:
        result['shield-' + name] = page.evaluate("""([name,context]) => {
          const A=Acceptance,p=A.p();A.gaaraArena();A.advance(.001);p.invuln=0;
          const amount=name==='broken'?G.NarutoGaara.shieldState(p).amount:2;p.hurt(amount,null,true,context);
          const s=G.NarutoGaara.shieldState(p);return {aim:s.flashAim,amount:s.amount,broken:s.broken};
        }""", [name, context])
        page.locator('#game').screenshot(path=str(OUT / f'{label}-effect-shield-{name}.png'))
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'failedRequests': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in [False, True]:
                label = 'mobile' if mobile else 'desktop'
                context = browser.new_context(locale='zh-TW', viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('response', lambda r: report['failedRequests'].append(r.url) if r.status >= 400 and '127.0.0.1' in r.url else None)
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click()
                assert page.evaluate('G.DB.save.partner===30007'), 'normal picker did not select Gaara'
                page.screenshot(path=str(OUT / f'{label}-menu.png'))
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                page.evaluate(HARNESS)
                page.evaluate(SETUP)
                page.evaluate(AUDIT)
                result = {'progression': page.evaluate(PROGRESSION)}
                report['viewports'][label] = result
                result['preview'] = page.evaluate("""() => {
                  const cv=document.createElement('canvas');cv.width=240;cv.height=200;document.body.append(cv);
                  const preview=G.UI.sprite(cv,30007,{shadow:false}),result=Acceptance.render(preview.a);cv.remove();
                  Acceptance.assert(result.state.key==='gaara-idle','native menu preview did not use Gaara common');
                  Acceptance.assert(result.sources.every(s=>new URL(s).pathname.includes('/redrawn/gaara-common')),'native menu preview used fallback');return result;
                }""")
                (OUT / f'{label}-preview.png').write_bytes(base64.b64decode(result['preview'].pop('png').split(',', 1)[1]))
                page.evaluate('Acceptance.gaaraArena();Acceptance.select("naruto-gaara");Acceptance.resume()')
                page.keyboard.press('Digit2')
                page.wait_for_function('G.Game.player.active===1')
                result['keyboardSkillSwitch'] = page.evaluate('Acceptance.pause();G.Game.player.activeGroup().map(m=>m.id)')
                if mobile:
                    slot = page.evaluate('G.Touch.controlLayout(innerWidth,innerHeight,G.Game.player.slots.length).slots[2]')
                    page.evaluate('Acceptance.resume()')
                    page.touchscreen.tap(slot['x'] + slot['w'] / 2, slot['y'] + slot['h'] / 2)
                    page.wait_for_function('G.Game.player.active===2')
                    result['touchSkillSwitch'] = page.evaluate('Acceptance.pause();G.Game.player.activeGroup().map(m=>m.id)')
                page.evaluate('Acceptance.gaaraArena()')
                page.keyboard.down('KeyD')
                result['keyboard'] = page.evaluate("""() => {const A=Acceptance,p=A.p(),x=p.x;
                  A.resume();p.update(.08);A.pause();A.assert(p.x>x&&p.walking,'real keyboard movement');return {dx:p.x-x}}""")
                page.keyboard.up('KeyD')
                if mobile:
                    page.evaluate('Acceptance.gaaraArena();Acceptance.resume()')
                    client = context.new_cdp_session(page)
                    base = page.evaluate('G.Touch.stickBase()')
                    client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': base['x'], 'y': base['y']}]})
                    client.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': base['x'] + 45, 'y': base['y']}]})
                    result['touch'] = page.evaluate("""() => {const A=Acceptance,p=A.p(),x=p.x;
                      A.assert(G.Touch.vector()?.[0]>0,'real joystick absent');p.update(.08);A.pause();
                      A.assert(p.x>x,'touch did not move Gaara');return {dx:p.x-x}}""")
                    client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                result['combat'] = page.evaluate(COMBAT)
                result['projectiles'] = page.evaluate(PROJECTILES)
                result['priority'] = page.evaluate(PRIORITY)
                result['timing'] = page.evaluate(TIMING)
                result['shieldContext'] = page.evaluate(SHIELD_CONTEXT)
                result['effects'] = capture_effects(page, label)
                result['cleanup'] = page.evaluate(CLEANUP)
                result['control'] = page.evaluate(CONTROL)
                result['shield'] = page.evaluate(SHIELD)
                result['cooldownBasic'] = page.evaluate(BASIC)
                result['upgrades'] = page.evaluate(UPGRADES)
                result['art'] = page.evaluate(ART)
                result['shieldGrowth'] = page.evaluate(GROWTH)
                result['sandPrison'] = page.evaluate(PRISON)
                result['sandPrisonEffects'] = capture_prison(page, label, OUT)
                for name, pose in result['art'].items():
                    (OUT / f'{label}-{name}.png').write_bytes(base64.b64decode(pose.pop('png').split(',', 1)[1]))
                page.screenshot(path=str(OUT / f'{label}.png'))
                result['prisonNativeRestart'] = page.evaluate(RESTART)
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
    print(json.dumps({'ok': report['ok'], 'viewports': list(report['viewports']), 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
