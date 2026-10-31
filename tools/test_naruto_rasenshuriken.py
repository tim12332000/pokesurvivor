"""Normal-entry Rasenshuriken VFX, combat invariance, ownership and lifecycle checks."""
import hashlib
import json
import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/naruto-rasenshuriken/gameplay'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&layout=wide'

CHECK = r"""() => {
 const assert=(v,m)=>{if(!v)throw Error(m)},p=G.Game.player,V=G.NarutoRasenshurikenVFX,id='naruto-rasenshuriken';
 assert(V&&G.AnimationLab.enabled,'normal entry did not load approved art');
 Object.assign(G.World,{isWall:()=>false,isFree:()=>true,collide:()=>{},propsInCircle:()=>[],projectileBlock:()=>false,isLiquid:()=>false});
 G.Camera.sees=()=>true;
 const enemy=(x,y)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];e.touchCd=999;G.EnemyMgr.add(e);return e};
 function reset(){
  G.NarutoRasenshurikenVFX=V;G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();G.NarutoClones.clear();
  p.x=p.y=0;p.aim=0;p.hp=p.maxHp;p.dead=false;p.flash=p.invuln=0;p.critChance=0;p.percentHealthDamage=0;p.lifestealRate=0;
  p.quantityBonus=p.quantityPicks=0;p.cdMul=1;p.moves=[];p.slots=[];p.bind={};p.active=0;p.addMove(id);
  G.Camera.x=G.Camera.y=0;return p.moves[0];
 }
 const step=seconds=>{for(let t=0;t<seconds-1e-9;){const dt=Math.min(.005,seconds-t);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,t);G.Combat.updateFields(dt);G.FX.update(dt);p.anim.update(dt);t+=dt}};
 function combat(enabled,clone=false){
  const m=reset(),es=[[100,0],[110,65],[110,-65],[100,190]].map(([x,y])=>enemy(x,y));
  G.EnemyMgr.rebuildGrid();p.target=es[0];if(!enabled)G.NarutoRasenshurikenVFX=undefined;
  const bursts=V.activeBursts.length;
  if(clone)G.DigimonSkills.fireFrom(p,m,0,0,0,.3);else {p.cast(m);assert(G.DigimonSkills.cast(p,m),'cast rejected')}
  const shots=G.Projectiles.all();assert(shots.length===1,'base count changed');
  assert(shots[0].r===15&&shots[0].life===1.3&&shots[0].vx===350,'flight or collision changed');
  assert(m.cd===6&&m.passive&&m.autoCast&&m.dmg===58&&!m.charge,'timing or automatic status changed');
  assert(!!shots[0].narutoClone===clone,'clone ownership tag changed');
  step(.35);const hp=es.map(e=>100000-e.hp);
  assert(hp.slice(0,3).every(n=>n>0)&&hp[3]===0,'AoE boundary changed');
  if(enabled)assert(V.activeBursts.length===bursts+1,'one collision must create exactly one wind burst');
  const after=es.map(e=>e.hp);G.Combat.resolve(0,p,0);assert(es.every((e,i)=>e.hp===after[i]),'visual burst dealt repeated damage');
  G.NarutoRasenshurikenVFX=V;return hp;
 }
 const baseline=combat(false),styled=combat(true),cloneBaseline=combat(false,true),cloneStyled=combat(true,true);
 assert(JSON.stringify(baseline)===JSON.stringify(styled),'VFX changed main damage');
 assert(JSON.stringify(cloneBaseline)===JSON.stringify(cloneStyled),'VFX changed clone damage');
 step(.8);assert(!V.activeBursts.length,'wind burst never expired');
 let m=reset();G.DigimonSkills.cast(p,m);const shot=G.Projectiles.all()[0],cv=document.createElement('canvas');cv.width=260;cv.height=180;
 const ctx=cv.getContext('2d');ctx.translate(100,100);
 const state=()=>JSON.stringify({x:shot.x,y:shot.y,t:shot.t,r:shot.r,dmg:shot.dmg,hp:p.hp,cd:m.t});
 const frames=[];
 for(const t of [.04,.09,.14,.19]){shot.t=t;ctx.clearRect(-100,-100,260,180);const before=state();G.Projectiles.draw(ctx);assert(before===state(),'drawing mutated simulation');frames.push(cv.toDataURL())}
 assert(new Set(frames).size===4,'rotation is stationary or aliased');
 const before=state();ctx.clearRect(-100,-100,260,180);G.Projectiles.draw(ctx);const frozen=cv.toDataURL();ctx.clearRect(-100,-100,260,180);G.Projectiles.draw(ctx);
 assert(frozen===cv.toDataURL()&&before===state(),'paused rendering advances spin');
 const ordinary={...shot,mid:'naruto-shuriken'};assert(V.drawProjectile(ctx,ordinary)===false,'unrelated projectile intercepted');
 const victim=enemy(shot.x,shot.y);G.EnemyMgr.rebuildGrid();shot.hits.add(victim.id);G.Combat.resolve(0,p,0);
 assert(V.activeBursts.length===1,'missing impact');p.dead=true;G.Combat.updateFields(.01);assert(!V.activeBursts.length,'dead owner retained burst');
 m=reset();V.impact(p,0,0,110);G.Combat.clearFields(p);assert(!V.activeBursts.length,'owner clear retained burst');
 V.impact(p,0,0,110);G.DigimonSkills.clear(p);assert(!V.activeBursts.length,'skill clear retained burst');
 V.impact(p,0,0,110);const world=G.World;G.World=Object.create(world);try{G.Combat.updateFields(.01);assert(!V.activeBursts.length,'world switch retained burst')}finally{G.World=world}
 m=reset();G.DigimonSkills.cast(p,m);p.dead=true;G.Combat.resolve(0,p,0);assert(!G.Projectiles.all().length&&!V.activeBursts.length,'death created an explosion');
 m=reset();p.quantityBonus=p.quantityPicks=4;const count=G.Quantity.snapshot(p,m).count;G.DigimonSkills.cast(p,m);assert(G.Projectiles.all().length===count&&count>1,'quantity count changed');
 // Exercise real autonomous shadow actors, then trace the renderer they use.
 m=reset();[[150,0],[0,150],[-150,0],[0,-150]].forEach(([x,y])=>enemy(x,y));G.EnemyMgr.rebuildGrid();
 assert(G.NarutoClones.cast(p,G.Moves.instance('naruto-shadow-clones')),'shadow summon failed');
 let cloneFrames=0;const draw=V.drawProjectile;V.drawProjectile=function(context,projectile){if(projectile.narutoClone&&projectile.mid===id)cloneFrames++;return draw(context,projectile)};
 try{for(let i=0;i<100;i++){step(.01);ctx.clearRect(-100,-100,260,180);G.Projectiles.draw(ctx)}}finally{V.drawProjectile=draw}
 assert(cloneFrames>0,'autonomous shadow clones did not use approved renderer');
 // Skill-card clones are independent controlled owners; clearing one must not erase the player's burst.
 m=reset();const card=G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);
 assert(card&&G.SelfClones.isControlled(card),'card clone missing');
 const cardShots=G.DigimonSkills.fireFrom(card,card.moves.find(move=>move.id===id),card.x,card.y,0);
 assert(cardShots.length===1&&cardShots[0].owner===card&&V.drawProjectile(ctx,cardShots[0]),'card clone renderer or ownership missing');
 const cardVictim=enemy(cardShots[0].x,cardShots[0].y);G.EnemyMgr.rebuildGrid();cardShots[0].hits.add(cardVictim.id);
 V.impact(p,0,0,110);G.Combat.resolve(0,p,0);
 assert(V.activeBursts.some(f=>f.owner===card)&&V.activeBursts.some(f=>f.owner===p),'card clone impact missing');
 G.Combat.clearFields(card);assert(V.activeBursts.length===1&&V.activeBursts[0].owner===p,'clearing card clone erased another owner');
 // Leave a genuine native projectile active for desktop/mobile captures.
 m=reset();p.aim=-.65;p.target=enemy(160,-115);G.EnemyMgr.rebuildGrid();m.t=0;G.Combat.tick(.001,p,0);
 assert(G.Projectiles.all().length===1&&m.t>0,'native automatic cast failed');step(.21);
 window.rasenEvidence={step,reset,enemy};
 return {damage:styled,cloneDamage:cloneStyled,quantity:count,cloneFrames,rotationFrames:new Set(frames).size,
  checks:['normal entry','native automatic cast','unchanged immediate release and cooldown','unchanged direct and splash damage','three targets inside / one outside','one burst per collision','no repeat damage','clone damage invariant','native shadow clone renderer','card clone renderer and independent owner cleanup','quantity','render purity','pause','death','owner clear','skill clear','world change','expiry']};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        reports={}
        for mobile in [False,True]:
            context = browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1100,'height':850}, is_mobile=mobile, has_touch=mobile, locale='zh-TW', service_workers='block')

            def route(request):
                file = ROOT / unquote(urlsplit(request.request.url).path).removeprefix('/pokesurvivor/')
                request.fulfill(status=200 if file.is_file() else 404,
                                body=file.read_bytes() if file.is_file() else b'Not found',
                                content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')

            context.route('https://tim12332000.github.io/pokesurvivor/**', route)
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(URL.replace('digimon.html','portrait.html').replace('layout=wide','layout=portrait') if mobile else URL)
            view = page
            if mobile:
                page.wait_for_selector('#portrait-game')
                view = page.locator('#portrait-game').element_handle().content_frame()
            view.wait_for_function('window.PS_REDRAWN_READY && G.Flow && G.NarutoRasenshurikenVFX && document.getElementById("boot").classList.contains("hidden")')
            if view.locator('#tap-start').is_visible():
                view.locator('#tap-start').click()
            view.evaluate("""async()=>{await PS_REDRAWN_READY;G.Naruto.choose(30001);await G.Flow.play();if(G.Game.state==='playing')G.Game.togglePause();G.UI.hideAll();document.querySelector('#tap-start').style.display='none';document.querySelectorAll('.toast,#ach-pop').forEach(e=>e.style.display='none')}""")
            report = view.evaluate(CHECK)
            page.wait_for_timeout(100)
            page.screenshot(path=str(OUT/('mobile-flight.png' if mobile else 'desktop-flight.png')))
            if mobile:
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'Mobile overflow'
                view.evaluate("""()=>{const A=rasenEvidence,m=A.reset(),p=G.Game.player;A.enemy(90,0);G.EnemyMgr.rebuildGrid();p.cast(m);G.DigimonSkills.cast(p,m);A.step(.3)}""")
                page.wait_for_timeout(100)
                page.screenshot(path=str(OUT/'mobile-impact.png'))
            assert not errors, errors
            report['errors'] = errors
            report['rendererSHA256'] = hashlib.sha256((ROOT/'.omx/naruto-rasenshuriken-vfx.js').read_bytes()).hexdigest()
            reports['mobile' if mobile else 'desktop']=report
            context.close()
        (OUT/'report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
        print(json.dumps(reports))
        browser.close()


if __name__ == '__main__':
    main()
