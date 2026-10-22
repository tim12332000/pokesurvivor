"""Native Rift travel preserves live clones; learned Gaara shields remain independent."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/self-clone-scene-shield'
CHECK = r"""() => {
 const A=Acceptance,assert=A.assert,S=G.SelfClones,N=G.NarutoGaara,H=G.NarutoSandGuard;
 const near=(a,b,label)=>assert(Math.abs(a-b)<1e-6,label+': '+a+' != '+b);
 G.Naruto.choose(30007);G.Flow.play();A.pause();
 const p=G.Game.player,home={x:p.x,y:p.y};p.level=3;p.critChance=0;p.lifestealRate=0;p.percentHealthDamage=0;
 const terrain=Object.fromEntries(['isFree','isWall','projectileBlock','collide','isLiquid'].map(k=>[k,G.World[k]]));
 A.arena();
 const step=(dt=.01)=>{A.resume();try{G.Combat.updateFields(dt);G.Combat.resolve(dt,p,0)}finally{A.pause()}};
 const a=S.summon(p);assert(a&&!N.shieldState(a),'clone shield must be learned');
 assert(p.addMove('naruto-sand-shield'),'learn owner shield');step();
 const m=p.moves.find(m=>m.id==='naruto-sand-shield');
 assert(a.moves.find(m=>m.id==='naruto-sand-shield')?.lvl===1,'existing clone did not acquire shield');
 let own=N.shieldState(p),copy=N.shieldState(a);assert(own&&copy&&own.owner===p&&copy.owner===a,'shield owner identity');
 const ownAmount=own.amount,hp=a.hp;a.invuln=0;A.resume();a.hurt(7,null,true);A.pause();
 near(a.hp,hp,'shield failed to protect clone HP');near(N.shieldState(a).amount,copy.amount-7,'clone absorption');near(N.shieldState(p).amount,ownAmount,'clone consumed owner shield');
 const oldCapacity=copy.capacity,missing=7;assert(G.Moves.levelUp(m),'owner shield upgrade');step();copy=N.shieldState(a);
 assert(a.moves.find(move=>move.id==='naruto-sand-shield').lvl===2&&copy.capacity>oldCapacity,'existing clone did not upgrade shield');
 near(copy.capacity-copy.amount,missing,'upgrade healed existing missing shield');
 const b=S.summon(p);assert(b.moves.find(m=>m.id==='naruto-sand-shield').lvl===2&&N.shieldState(b),'new clone did not inherit shield');
 step();const ga=H.state(a),gb=H.state(b),gp=H.state(p);assert(ga&&gb&&gp&&ga!==gb&&ga!==gp&&ga.guardians[0]!==gb.guardians[0],'guardians share state');
 const age=ga.flowAge;step(.02);near(H.state(a).flowAge-age,.02,'clone guardians advanced more than once');
 const armorEnemy=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},p.x+80,p.y,{hp:1,spd:1,dmg:1});G.EnemyMgr.add(armorEnemy);G.EnemyMgr.rebuildGrid();
 A.resume();G.Combat.tick(.001,p,0);A.pause();step();
 const playerArmor=N.armorState(p),cloneArmor=N.armorState(b);assert(playerArmor&&cloneArmor&&playerArmor.owner!==cloneArmor.owner,'clone armor missing/shared');
 const type=Object.keys(G.Types.CHART||{}).find(t=>G.Types.mult(t,b.mon.types)>1)||'water';
 const factor=G.Types.mult(type,b.mon.types)*G.Weather.mult(type),beforeHp=b.hp,playerArmorHits=playerArmor.hits,playerShieldBefore=N.shieldState(p).amount;
 b.invuln=0;A.resume();b.hurt((N.shieldState(b).amount+.5)/(1-cloneArmor.reduction)/factor,type,true);A.pause();
 near(b.hp,beforeHp-.5,'typed fractional shield overflow');assert(N.armorState(b).hits===1&&N.armorState(p).hits===playerArmorHits,'armor hit counter shared');near(N.shieldState(p).amount,playerShieldBefore,'typed clone overflow consumed owner shield');G.EnemyMgr.clear();
 const playerShield=N.shieldState(p).amount;a.invuln=0;A.resume();a.hurt(N.shieldState(a).amount+a.maxHp*10,null,true);A.pause();
 assert(a.dead&&!S.actors().includes(a),'dead clone retained');near(N.shieldState(p).amount,playerShield,'dead clone drained player shield');
 b.hp=b.maxHp*.6;const health=b.hp,identity=b.cloneId;
 // Return to real terrain before exercising both native scene transitions.
 Object.assign(G.World,terrain);p.x=home.x;p.y=home.y;b.x=p.x;b.y=p.y;
 const enemy=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},p.x+80,p.y,{hp:1,spd:1,dmg:1});G.EnemyMgr.add(enemy);G.EnemyMgr.rebuildGrid();
 const basic=b.moves.find(m=>m.id==='naruto-gaara');
 // A queued action/projectile must not survive travel, even while its actor does.
 G.World.isWall=()=>false;G.World.projectileBlock=()=>false;assert(N.cast(b,basic),'temporary action fixture');Object.assign(G.World,terrain);
 G.Projectiles.all().push({owner:b,friendly:true,x:b.x,y:b.y,vx:0,vy:0,r:2});
 const oldGuard=H.state(b);A.resume();G.Rift.debugArena('fire');A.pause();
 assert(G.Rift.inArena,'native Rift entry failed');assert(S.actors().includes(b)&&b.cloneId===identity&&S.actors().length===1,'entry replaced/lost clone or resurrected dead clone');near(b.hp,health,'entry changed HP');
 assert(!N.active(b)&&!G.Projectiles.all().some(q=>q.owner===b),'old scene effects survived');
 assert(H.state(b)!==oldGuard,'old guardians survived scene clear');
 assert(Math.hypot(b.x-p.x,b.y-p.y)<220&&G.World.isFree(b.x,b.y,b.r,true),'entry placement unsafe');
 p.bonds=0;A.resume();G.Rift.onEvent(['al']);G.Rift.update(1.3,p,G.Game.st.time);A.pause();
 assert(!G.Rift.inArena&&S.actors().length===1&&S.actors()[0]===b,'return replaced/lost clone or resurrected dead clone');near(b.hp,health,'return changed HP');
 assert(Math.hypot(b.x-p.x,b.y-p.y)<220&&G.World.isFree(b.x,b.y,b.r,true),'return placement unsafe');
 G.Combat.clearFields();assert(!S.actors().length&&b.dead,'ordinary clear persisted clone');
 const doomed=S.summon(p);p.dead=true;step();assert(doomed.dead&&!S.actors().length,'owner death retained clone');p.dead=false;
 const replaced=S.summon(p),game=G.Game;G.Game={...game,player:new G.Player(p.mon),state:'playing'};G.Combat.updateFields(.01);G.Game=game;assert(replaced.dead&&!S.actors().length,'owner replacement retained clone');
 const neverReturn=S.summon(p);A.resume();G.Rift.debugArena('fire');A.pause();p.dead=true;p.hp=0;
 A.resume();G.Rift.onEvent(['al']);G.Rift.update(1.3,p,G.Game.st.time);A.pause();
 assert(!p.dead&&neverReturn.dead&&!S.actors().length,'native Rift owner revival resurrected clone');
 const reset=S.summon(p);S.clear();assert(reset.dead&&!S.actors().length,'explicit clone clear persisted actor');
 const fresh=S.summon(p);G.Flow.play();A.pause();assert(fresh.dead&&!S.actors().length,'new run retained clone');
 return {nativeEntry:true,nativeReturn:true,sameIdentity:true,sameRemainingHp:true,deadNeverReturned:true,learnAndUpgrade:true,independentShield:true,independentGuardians:true,explicitLifecycleClears:true};
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
