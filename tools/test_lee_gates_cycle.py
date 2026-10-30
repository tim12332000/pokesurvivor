"""Native Gates: five-second opening plus ten-second buff, with a 30-second cycle."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

OUT = Path(__file__).resolve().parents[1] / '.omx/state/lee-gates-cycle'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=lee&layout=wide&test=gates-cycle'
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),g=G.NarutoGates,near=(a,b)=>Math.abs(a-b)<1e-7,out={};
 A.leeArena();p.level=6;p.maxHp=20000;p.hp=100;p.regenFlat=0;
 const base={atk:p.atk,spd:p.spd,max:p.maxHp,slots:p.slots.length};
 A.assert(p.addMove('naruto-gates'),'native learning failed');p.hp=100;
 A.assert(g.learnedStage(p)===1&&g.stage(p)===1&&g.status(p).activeRemaining===15,'initial active state wrong');
 A.assert(p.slots.length===base.slots&&near(p.maxHp,base.max+6),'passive occupied slot or health bonus wrong');
 A.assert(near(p.atk,base.atk*1.3)&&near(p.spd,base.spd*1.1),'active stats missing');
 const clone=G.SelfClones.summon(p),cloneHp=clone.hp;
 A.assert(clone&&g.stage(clone)===1,'native clone did not mirror active Gates');
 A.advance(1);A.assert(near(p.hp,100),'uninjured opening granted free healing');
 const paused=JSON.stringify(g.status(p)),hp=p.hp;G.Combat.updateFields(3);
 A.assert(JSON.stringify(g.status(p))===paused&&p.hp===hp,'pause advanced cycle or healing');
 A.advance(4);A.assert(near(p.hp,100)&&!g.performing(p)&&g.stage(p)===1,'five-second opening failed');
 A.assert(clone.hp===cloneHp&&!g.performing(clone),'clone received duplicate opening heal or cycle');
 const x=p.x;A.resume();p.update(.02);A.pause();A.assert(p.x>x,'opening did not release movement at five seconds');
 const afterNativeRegen=p.hp;A.advance(5);
 A.assert(g.active(p)&&g.status(p).activeRemaining===5,'buff expired at ten seconds');
 A.advance(4.99);A.assert(g.active(p)&&g.stage(clone)===1,'buff expired before fifteen seconds');
 A.advance(.01);
 A.assert(g.learnedStage(p)===1&&g.stage(p)===0&&!g.redSkin(p),'buff did not expire at fifteen seconds');
 A.assert(g.stage(clone)===0,'clone retained source Gates after expiry');
 A.assert(near(p.hp,afterNativeRegen)&&near(p.maxHp,base.max),'expiry leaked healing or maximum HP');
 A.assert(near(p.atk,base.atk)&&near(p.spd,base.spd)&&near(g.healingMultiplier(p),1),'temporary stat bonus survived expiry');
 A.assert(!G.AnimationLab.stateFor(p.anim).key.startsWith('lee-opened-'),'red actor art survived expiry');
 A.assert(g.status(p).cooldownRemaining===15&&g.status(p).activeRemaining===0,'off-window countdown wrong');
 A.advance(14.99);A.assert(!g.active(p)&&!g.performing(p),'cycle restarted before thirty seconds');
 A.advance(.01);A.assert(g.stage(p)===1&&g.performing(p)&&g.status(p).cooldownRemaining===25,'cycle did not restart at thirty seconds '+JSON.stringify({status:g.status(p),stage:g.stage(p),opening:g.openingFor(p)?.age}));
 A.assert(near(p.maxHp,base.max+6),'second cycle accumulated maximum HP');
 A.assert(G.SelfClones.actors().includes(clone)&&!clone.dead&&g.stage(clone)===1,'automatic activation deleted the native clone');
 out.boundaries={opening:5,postOpeningBuff:10,duration:15,cooldown:25,cycle:30};
 // Native flat and percentage cards survive removal/reapplication of the temporary component.
 p.addMaxHp(40);const grown=p.maxHp;p.addMaxHp(p.maxHp*.1);const withCards=p.maxHp;
 A.advance(15);A.assert(near(p.maxHp,withCards-6),'expiry removed native card growth');
 A.advance(15);A.assert(near(p.maxHp,withCards),'next cycle compounded the temporary maximum HP');
 out.cards={flat:40,percentage:.1,before:grown,active:withCards};
 // Upgrading during an off-window starts the next stage immediately and resets the clock.
 A.advance(15);const m=p.moves.find(move=>move.id==='naruto-gates');
 A.assert(G.Moves.levelUp(m),'upgrade failed');
 A.assert(g.stage(p)===2&&g.performing(p)&&g.status(p).cooldownRemaining===25,'upgrade did not restart at new stage');
 A.assert(near(p.maxHp,withCards-6+12),'upgrade maximum HP delta stacked');
 // An external clear cancels presentation and buffs while retaining the ordinary deadline.
 A.advance(2);const remaining=28;G.Combat.clearFields(p);
 A.assert(!g.active(p)&&!g.performing(p)&&g.status(p).cooldownRemaining===remaining,'clear retained buff or reset timer');
 A.advance(remaining-.01);A.assert(!g.active(p),'clear immediately reactivated');
 A.advance(.01);A.assert(g.stage(p)===2&&g.performing(p),'clear prevented the next ordinary activation');
 const beforeDeath=p.hp;p.dead=true;A.advance(3);
 A.assert(!g.active(p)&&!g.performing(p)&&p.hp===beforeDeath,'death retained opening heal or buff');
 p.dead=false;p.hp=100;A.advance(.01);A.assert(!g.active(p),'revival immediately reapplied cancelled buff');
 const world=G.World;G.World={...world};A.advance(.01);G.World=world;
 A.assert(!g.active(p)&&!g.performing(p),'world transition retained active state');
 // Large deltas have bounded work and do not retroactively produce skipped cycles.
 G.Moves.levelUp(m);p.hp=100;A.advance(19);
 A.assert(!g.active(p)&&!g.performing(p)&&near(p.hp,100),'oversized delta granted free healing');
 out.cleanup=['clear','death','world'];out.cloneSurvivesAutomaticActivation=true;return out;
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in (False, True):
            label = 'mobile' if mobile else 'desktop'
            ctx = browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = ctx.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY&&G.NarutoGates&&document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30006"]').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
            page.evaluate(HARNESS)
            page.evaluate(SETUP)
            page.keyboard.down('KeyD')
            report['viewports'][label] = page.evaluate(CHECK)
            page.keyboard.up('KeyD')
            ctx.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))

if __name__ == '__main__':
    main()
