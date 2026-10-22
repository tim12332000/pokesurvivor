"""Native Rift travel preserves live clones; learned Gaara shields remain independent."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/self-clone-recall-passives'
CHECK = r"""() => {
 const A=Acceptance,assert=A.assert,S=G.SelfClones,N=G.NarutoGaara,H=G.NarutoSandGuard;
 const near=(a,b,label)=>assert(Math.abs(a-b)<1e-6,label+': '+a+' != '+b);
 G.Naruto.choose(30007);G.Flow.play();A.pause();A.arena();
 const p=G.Game.player;p.level=12;p.critChance=0;p.lifestealRate=0;p.percentHealthDamage=0;p.addMove('naruto-sand-shield');
 const c=S.summon(p),e=new G.Enemy({dex:19,hp:1000000,spd:0,dmg:0,xp:0,behavior:'chase'},60,0,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();c.target=e;
 const step=dt=>{A.resume();try{G.Combat.updateFields(dt)}finally{A.pause()}};
 step(.001);let armor=N.armorState(c);assert(armor,'automatic armor fixture');
 c.invuln=0;A.resume();c.hurt((N.shieldState(c).amount+2)/(1-armor.reduction),null,true);A.pause();assert(N.armorState(c).hits===1,'armor hit fixture');
 G.Moves.levelUp(p.moves.find(m=>m.id==='naruto-sand-shield'));step(.001);
 const shield=N.shieldState(c),guard=H.state(c),priorArmor=N.armorState(c),ownerShield=N.shieldState(p);
 assert(shield.amount>0&&shield.amount<shield.capacity,'partial barrier fixture');
 c.buffs.def={n:1,amount:.1,t:10};c.invuln=.2;const hp=c.hp,max=c.maxHp,identity=c.cloneId,atk=c.atk;
 c.x=p.x+900;c.y=p.y;step(.01);
 const after=N.shieldState(c),afterArmor=N.armorState(c);
 assert(S.actors()[0]===c&&c.cloneId===identity&&!c.dead,'recall replaced actor');near(c.hp,hp,'recall healed/damaged clone');near(c.maxHp,max,'recall changed maxHP');near(c.atk,atk,'recall changed attack');
 assert(Math.hypot(c.x-p.x,c.y-p.y)<220,'hard recall failed');near(after.amount,shield.amount,'hard recall refilled barrier');near(after.capacity,shield.capacity,'hard recall changed capacity');near(after.age,shield.age+.01,'barrier state was recreated');
 assert(afterArmor&&afterArmor.move===priorArmor.move&&afterArmor.hits===priorArmor.hits,'hard recall recreated armor/counter');near(afterArmor.age,priorArmor.age+.01,'armor age reset');assert(H.state(c)===guard,'hard recall recreated guardians');
 near(N.shieldState(p).amount,ownerShield.amount,'source shield changed');assert(c.buffs.def.n===1&&c.buffs.def.amount===.1,'buff removed on recall');near(c.invuln,.19,'invulnerability status reset');
 // An actual scoped Chidori action is cancelled without touching another actor.
 S.clear();G.Naruto.choose(30002);G.Flow.play();A.pause();A.arena();const sasuke=G.Game.player;sasuke.level=12;sasuke.addMove('naruto-chidori');const clone=S.summon(sasuke),foe=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},60,0,{hp:1,spd:1,dmg:1});G.EnemyMgr.add(foe);G.EnemyMgr.rebuildGrid();clone.target=foe;
 const move=clone.moves.find(m=>m.digiMode==='chidori-chain');assert(move,'Chidori fixture move');assert(G.NarutoChidori.cast(clone,move),'native Chidori cast fixture');clone.x=sasuke.x+900;const health=clone.hp;step(.01);
 assert(!G.NarutoChidori.activeFor(clone)&&Math.hypot(clone.x-sasuke.x,clone.y-sasuke.y)<220,'old movement action pulled clone away after recall');near(clone.hp,health,'movement cancel changed HP');
 return {sameActor:true,remainingHp:true,shieldAmountCapacityAge:true,armorIdentityHitsAge:true,guardiansIdentity:true,buffAndInvulnerability:true,nativeMovementCancelled:true};
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
