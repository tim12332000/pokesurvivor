"""Native Rift travel preserves live clones; learned Gaara shields remain independent."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/self-clone-gaara-passives'
CHECK = r"""() => {
 const A=Acceptance,assert=A.assert,S=G.SelfClones,N=G.NarutoGaara,H=G.NarutoSandGuard;
 const near=(a,b,label)=>assert(Math.abs(a-b)<1e-5*Math.max(1,Math.abs(b)),label+': '+a+' != '+b);
 G.Naruto.choose(30007);G.Flow.play();A.pause();A.arena();
 const p=G.Game.player;p.level=12;p.critChance=0;p.lifestealRate=0;p.percentHealthDamage=0;p.addMove('naruto-sand-coffin');p.addMove('naruto-sand-prison');
 A.select('naruto-sand-coffin');
 const c=S.summon(p),initialMax=c.maxHp;assert(!N.shieldState(c)&&!H.state(c),'innate shield');
 const step=(dt=.01,resolve=true)=>{A.resume();try{G.Combat.updateFields(dt);if(resolve)G.Combat.resolve(dt,p,0)}finally{A.pause()}};
 const hit=(amount,type=null)=>{c.invuln=0;A.resume();try{c.hurt(amount,type,true)}finally{A.pause()}};
 const advance=dt=>{A.resume();try{N.update(dt)}finally{A.pause()}};
 const spawn=(boss=false)=>{const e=new G.Enemy({dex:19,hp:1000000,spd:0,dmg:0,xp:0,behavior:'chase'},60,0,{hp:1,spd:1,dmg:1});e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
 const reset=()=>{G.EnemyMgr.clear();G.Projectiles.clear();N.clear(c);H.clear(c);c.x=c.y=0;c.hp=c.maxHp;c.invuln=0;c.percentHealthDamage=0;p.percentHealthDamage=0;c.target=p.target=null;};
 assert(p.addMove('naruto-sand-shield'),'learn shield');step(.001,false);
 const move=p.moves.find(m=>m.id==='naruto-sand-shield'),tiers=[];
 for(let tier=1;tier<=5;tier++){
  if(tier>1){assert(G.Moves.levelUp(move),'upgrade shield');step(.001,false)}
  assert(c.moves.find(m=>m.id===move.id)?.lvl===tier,'late shield tier sync');
  const newClone=S.summon(p);assert(newClone.moves.find(m=>m.id===move.id)?.lvl===tier,'new clone shield tier');S.clear(newClone);
  assert(!c.slots.some(g=>g.some(m=>['naruto-gaara','naruto-sand-shield'].includes(m.id))),'passive became selectable');
  near(c.maxHp,initialMax,'snapshot max HP');near(c.atk,p.atk/3,'one-third direct attack');
  reset();let shield=N.shieldState(c),source=N.shieldState(p);const capacity=2*(N.capacities[tier-1]+p.level*tier);
  near(shield.capacity,capacity,'tier capacity');const own=source.amount;hit(4);near(c.hp,c.maxHp,'barrier protects HP');near(N.shieldState(c).amount,capacity-4,'barrier consumes clone shield');near(N.shieldState(p).amount,own,'barrier consumed source shield');
  advance(12*c.cdMul-.01);assert(N.shieldState(c).amount<capacity,'early refill');advance(.011);near(N.shieldState(c).amount,capacity,'refill');
  const group=H.state(c);assert(group.count===G.Quantity.count(c,H.config.capacities[tier-1]+c.level),'guardian count');
  assert(group!==H.state(p)&&group.guardians[0]!==H.state(p).guardians[0],'shared guardian state');
  // A physical hostile projectile reaches the cloud before the clone body.
  group.guardians.forEach((g,i)=>{g.x=i?-300:100;g.y=i?-300:0;g.ready=i===0;g.charges=i===0?1:0});
  const shot=G.Projectiles.spawn({friendly:false,x:110,y:0,vx:-190,vy:0,r:6,life:2,dmg:17,mtype:'fire'});
  const hp=c.hp,shieldBefore=N.shieldState(c).amount;A.resume();G.Projectiles.update(.01,p,[]);G.Combat.resolve(.01,p,0);A.pause();
  assert(!G.Projectiles.all().includes(shot)&&!group.guardians[0].ready,'clone guardian did not intercept');near(c.hp,hp,'interception hurt clone');near(N.shieldState(c).amount,shieldBefore,'interception consumed barrier');
  // Own automatic armor works without occupying the selected coffin slot.
  reset();const target=spawn();c.target=target;p.target=target;const hits=[],native=target.hurt;
  target.hurt=function(...args){if(args[6]===c)hits.push({amount:args[0],move:args[7]});return native.apply(this,args)};
  A.resume();G.Combat.tick(.001,c,0);A.pause();let armor=N.armorState(c);assert(armor&&armor.move.lvl===tier,'automatic tier armor');
  const reduction=G.Moves.instance('naruto-sand-armor',tier).armorReduction;near(armor.reduction,reduction,'armor reduction');
  hit(1);assert(N.armorState(c).hits===0,'shield-only damage counted as armor hit');
  hit(N.shieldState(c).amount/(1-reduction));assert(N.armorState(c).hits===0,'shield depletion counted as HP damage');
  const before=c.hp;hit(4);near(c.hp,before-4*(1-reduction),'armor actual HP reduction');assert(N.armorState(c).hits===1,'first armor HP hit');
  A.resume();c.hurt(4,null,true);A.pause();assert(N.armorState(c).hits===1,'invulnerable armor hit counted');hit(0);assert(N.armorState(c).hits===1,'zero armor hit counted');hit(4);hit(4);
  assert(!N.armorState(c)&&hits.filter(h=>h.move==='naruto-sand-armor').length===1,'third HP hit did not burst once');
  near(hits.find(h=>h.move==='naruto-sand-armor').amount,G.Moves.instance('naruto-sand-armor',tier).dmg*c.atk*G.Types.mult('ground',target.types)*G.Weather.mult('ground'),'armor one-third attack');
  reset();const expiry=spawn(),expiryHits=[];c.target=expiry;const nativeExpiry=expiry.hurt;expiry.hurt=function(...args){if(args[6]===c&&args[7]==='naruto-sand-armor')expiryHits.push(args[0]);return nativeExpiry.apply(this,args)};
  A.resume();G.Combat.tick(.001,c,0);A.pause();advance(2.99);assert(N.armorState(c),'armor expired early');advance(.01);assert(!N.armorState(c)&&expiryHits.length===1,'armor expiry burst');advance(.5);assert(expiryHits.length===1,'duplicate expiry burst');
  // Percent-health cards must remain disabled for guardian hits against kings.
  reset();p.percentHealthDamage=.9;step(.001,false);const boss=spawn(true),bg=H.state(c),expected=H.config.attackDamages[tier-1]*c.atk*G.Types.mult(bg.move.type,boss.types)*G.Weather.mult(bg.move.type);
  H.state(p).guardians.forEach(g=>{g.ready=false;g.charges=0;g.x=g.y=-300});
  bg.guardians.forEach((g,i)=>{g.x=i?-300:boss.x;g.y=i?-300:boss.y;g.ready=i===0;g.charges=i===0?1:0});const bossHp=boss.hp;
  A.resume();G.Combat.resolve(.01,p,0);A.pause();near(bossHp-boss.hp,Math.round(expected),'guardian boss bonus percent or wrong attack');
  tiers.push({tier,capacity,guardians:bg.count,reduction,armorCounter:true,armorExpiry:true,bossPercentDisabled:true});
 }
 reset();p.percentHealthDamage=0;step(.001,false);const giant=G.LevelUp.STATS.find(s=>s.id==='giant');giant.apply(p);step(.001,false);near(c.maxHp,initialMax,'Giant changed clone HP snapshot');near(c.cdMul,p.cdMul,'Giant cooldown mirror');
 N.clear(c);let s=N.shieldState(c);hit(4);advance(12*c.cdMul-.01);assert(N.shieldState(c).amount<s.capacity,'Giant barrier refilled early');advance(.011);near(N.shieldState(c).amount,s.capacity,'Giant barrier refill');
 reset();const boss=spawn(true),g=H.state(c),times=[];g.guardians.forEach((cloud,i)=>{cloud.x=boss.x;cloud.y=boss.y;cloud.ready=i===0;cloud.charges=i===0?1:0});const hurt=boss.hurt;let time=0;
 boss.hurt=function(...args){if(args[6]===c&&args[7]==='naruto-sand-shield')times.push(time);return hurt.apply(this,args)};
 let cooldown=null;for(let n=0;n<500&&times.length<2;n++){time+=.01;A.resume();G.Combat.resolve(.01,p,0);A.pause();if(times.length===1&&cooldown===null)cooldown=g.guardians[0].attackCooldown}
 assert(times.length===2&&times[1]-times[0]>=G.Giant.interval(c)-.02,'Giant guardian cadence');near(cooldown,G.Giant.interval(c)-.01,'Giant guardian cooldown');
 // Leave coffin selected: independent passive basic still casts and deals damage.
 reset();const e=spawn(),calls=[],dealt=[],cast=c.cast,enemyHurt=e.hurt;c.target=p.target=e;
 c.cast=function(m,...args){calls.push(m.id);return cast.call(this,m,...args)};e.hurt=function(...args){if(args[6]===c)dealt.push(args[7]);return enemyHurt.apply(this,args)};
 for(let n=0;n<650&&!dealt.includes('naruto-gaara');n++)step(.01);
 assert(c.activeGroup().some(m=>m.id==='naruto-sand-coffin')&&calls.includes('naruto-gaara')&&dealt.includes('naruto-gaara')&&N.shieldState(c),'constant basic disabled alongside selected active');
 assert(!c.slots.some(g=>g.some(m=>m.id==='naruto-gaara')),'basic selectable');
 return {tiers,giantRefill:true,giantGuardianCadence:true,selectedActiveAndAutomaticBasic:true,damageRatio:1/3,hpSnapshot:true};
}"""



def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'viewports': {}, 'errors': []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in [False, True]:
                context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.SelfClones && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.evaluate(HARNESS)
                report['viewports']['mobile' if mobile else 'desktop'] = page.evaluate(CHECK)
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
