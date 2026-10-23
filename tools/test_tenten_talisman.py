"""Additional physical charm; the original guard regression remains unchanged."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_tenten_guard import CHROME, HARNESS, SETUP, SETUP_GUARD, PROGRESSION, URL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/tenten-talisman'

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,out={};
 A.charmReset=()=>{A.guardReset();p.dead=false;p.hp=p.maxHp;p.invuln=0;A.advance(.001)};
 A.charm=()=>T.talismanFor(p);
 A.shot=(extra={})=>G.Projectiles.spawn({x:p.x+160,y:p.y,vx:-200,vy:0,r:4,dmg:12,life:10,friendly:false,...extra});
 const run=()=>{const before=A.charm().intercepted;for(let i=0;i<150&&A.charm().intercepted===before;i++)A.advance(.01)};
 A.charmReset();A.assert(A.charm()?.ready&&A.guard().ready,'both defenses not ready');
 A.assert(p.slots.flat().every(m=>m.id!==A.guardID),'charm consumed active slot');
 A.finish(.4);A.assert(A.charm().ready&&A.charm().intercepted===0,'idle spent charge');
 out.idle=true;
 out.directions=[];
 for(const angle of [0,Math.PI/2,Math.PI,-Math.PI/2]){
   A.charmReset();const hp=p.hp,shot=A.shot({x:Math.cos(angle)*160,y:Math.sin(angle)*160,vx:-Math.cos(angle)*200,vy:-Math.sin(angle)*200});
   run();A.assert(A.charm().intercepted===1&&!G.Projectiles.all().includes(shot)&&p.hp===hp,'physical block failed direction '+angle);
   A.assert(A.guard().activations===0&&A.guard().ready,'charm triggered old sweep');
   out.directions.push({angle,remaining:A.charm().cooldownRemaining});
 }
 for(const mul of [.2,1,2]){
   A.charmReset();p.cdMul=mul;A.shot({bossSpecial:true,special:true,interceptable:false});run();
   const remaining=A.charm().cooldownRemaining;A.assert(remaining>2.98&&remaining<=3,'wrong fixed cooldown');
   A.finish(2.9);A.assert(!A.charm().ready,'charm recharged early');A.finish(.12);A.assert(A.charm().ready,'charm failed to recharge');
   A.shot();run();A.assert(A.charm().intercepted===2,'recharged charm did not block');
 }
 out.fixedCooldown=true;
 A.charmReset();const boss=A.spawn(200,0,true);boss.ai={cast:{id:'nova'}};boss.shoot(-1,0);
 run();A.assert(A.charm().intercepted===1,'native boss shot not intercepted');out.nativeBoss=true;
 A.charmReset();const hp=p.hp;A.shot();A.shot();A.finish(1);
 A.assert(A.charm().intercepted===1&&p.hp<hp,'one charge blocked whole volley');out.singleCharge=true;
 for(const flag of ['unblockable','guardUnblockable','uninterceptable','hazard','laser','beam','ground','groundField','orb']){
   A.charmReset();A.shot({[flag]:true});A.finish(.6);A.assert(A.charm().intercepted===0&&A.charm().ready,'blocked excluded '+flag);
 }
 A.charmReset();A.shot({friendly:true});A.finish(.6);A.assert(A.charm().intercepted===0,'blocked friendly shot');
 A.charmReset();A.shot({vx:200});A.finish(.6);A.assert(A.charm().intercepted===0,'chased receding shot');out.exclusions=true;
 A.charmReset();const fastHP=p.hp;A.shot({x:120,vx:-4000});A.advance(.05);
 A.assert(A.charm().intercepted===1&&p.hp===fastHP,'fast swept shot tunneled through charm');out.fastShot=true;
 A.charmReset();const wall=G.World.projectileBlock;G.World.projectileBlock=(x,y)=>x>55&&x<65?{destructible:false}:false;
 try{A.shot();A.finish(.25);A.assert(A.charm().intercepted===0,'charm intercepted through wall')}finally{G.World.projectileBlock=wall}
 out.wall=true;
 A.charmReset();A.shot();run();const remaining=A.charm().cooldownRemaining,x=A.charm().x;
 G.Projectiles.update(.5,p,G.EnemyMgr.all());A.near(A.charm().cooldownRemaining,remaining,'paused charm cooldown');
 p.frozen=true;A.advance(.5);A.near(A.charm().cooldownRemaining,remaining,'frozen charm cooldown');A.near(A.charm().x,x,'frozen charm moved');p.frozen=false;
 out.pauseFreeze=true;
 // A charm block does not spend the original sweep; the sweep does not reset the charm.
 A.charmReset();A.shot();run();const charmCD=A.charm().cooldownRemaining,spd=p.spd;
 A.spawn(60,0);A.finish(.14);
 A.assert(A.guard().activations===1&&A.guard().pushed===1&&p.spd>spd,'original sweep/escape lost');
 A.assert(A.charm().cooldownRemaining<charmCD&&A.charm().cooldownRemaining>2.7,'sweep reset charm cooldown');
 A.finish(3);A.assert(A.charm().ready&&!A.guard().ready,'independent cooldowns not preserved');
 A.shot();run();A.assert(A.charm().intercepted===2&&A.guard().activations===1,'charm blocked by sweep cooldown');out.coexistence=true;
 A.charmReset();p.quantityPicks=p.quantityBonus=20;A.shot();run();A.assert(A.charm().intercepted===1,'quantity changed charm charges');
 A.assert(!T.weapons.length,'charm generated damage weapons');out.quantity=true;
 A.charmReset();const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');card.apply(p);card.apply(p);
 const [a,b]=G.SelfClones.actors();a.x=150;a.y=0;b.x=-150;b.y=0;
 const cloneStep=()=>{A.resume();try{G.Projectiles.update(.01,p,G.EnemyMgr.all());G.Combat.resolve(.01,p,0)}finally{A.pause()}};
 cloneStep();
 A.assert(T.talismanFor(a)?.ready&&T.talismanFor(b)?.ready,'clone missing charm');
 A.shot({x:150,y:160,vx:0,vy:-200});for(let i=0;i<50;i++)cloneStep();
 A.assert(T.talismanFor(a).intercepted===1&&T.talismanFor(b).intercepted===0&&A.charm().intercepted===0,'clone charm state leaked '+JSON.stringify({a:T.talismanFor(a),b:T.talismanFor(b).intercepted,p:A.charm().intercepted,x:a.x,y:a.y,spd:a.spd,shots:G.Projectiles.all().map(s=>[s.x,s.y])}));out.clones=true;
 for(const reason of ['clear','death','world','role','unlearn']){
   A.charmReset();const world=G.World,dex=p.dex,mon=p.mon,moves=p.moves;
   if(reason==='clear')G.Combat.clearFields(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};
   if(reason==='role'){p.dex=30001;p.mon=G.DEX.find(m=>m.dex===30001)}
   if(reason==='unlearn')p.moves=p.moves.filter(m=>m.id!==A.guardID);
   try{A.assert(!T.talismanFor(p),'charm leaked '+reason)}finally{p.dead=false;G.World=world;p.dex=dex;p.mon=mon;p.moves=moves}
 }
 out.cleanup=true;A.charmReset();return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, size, mobile in [('desktop', {'width': 1200, 'height': 900}, False),
                                    ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=size, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30009"]').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30009 && G.Game.state==="playing"')
            for setup in [HARNESS, SETUP, SETUP_GUARD, PROGRESSION]:
                page.evaluate(setup)
            report['viewports'][label] = page.evaluate(CHECK)
            for phase in ['ready', 'cooldown', 'coexist']:
                page.evaluate("""phase=>{const A=Acceptance;A.charmReset();
                  if(phase!=='ready'){A.shot();for(let i=0;i<100&&A.charm().intercepted===0;i++)A.advance(.01)}
                  if(phase==='coexist'){A.spawn(60,0);A.finish(.24)}
                  G.UI.hide('ach-pop');document.querySelectorAll('.toast').forEach(e=>e.style.display='none');
                }""", phase)
                page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                page.screenshot(path=str(OUT / f'{label}-{phase}.png'))
            context.close()
            print(label, 'talisman PASS', flush=True)
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')


if __name__ == '__main__':
    main()
