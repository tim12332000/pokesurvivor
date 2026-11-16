"""Exercise shared cloak transitions and real shadow actors in the local game."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import BASE, CHROME, start

OUT = Path(__file__).resolve().parents[1] / 'art-review/naruto-cloak-20261116'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for width in (1100, 390):
            page = browser.new_page(viewport={'width': width, 'height': 850}, service_workers='block')
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(BASE)
            page.wait_for_function('GameplayLab.ready')
            tap = page.frame_locator('#game').locator('#tap-start')
            if tap.is_visible():
                tap.click()
            frame = start(page, 30001)
            report = frame.evaluate("""() => {
              const A=Acceptance,p=G.Game.player;
              A.cast('naruto-nine-tails-cloak');
              G.NarutoClones.cast(p,G.Moves.instance('naruto-shadow-clones',1));
              const clone=G.NarutoClones.actors[0];
              const pose=()=>G.KyuubiForm.poseFor(p.anim);
              A.assert(G.KyuubiForm.poseFor(clone.anim),'shadow clone did not transform');
              const early=pose().blend;
              A.step(.3);const middle=pose().blend;
              A.step(.4);const full=pose().blend;
              A.assert(early<middle&&middle<full&&full===1,'transition is not gradual');
              A.assert(G.KyuubiForm.poseFor(clone.anim).blend===full,'clone clock differs');
              A.assert(clone.anim.scale===p.anim.scale,'base actor sizes differ');
              const before=JSON.stringify(pose());p.anim.update(.2);
              A.assert(JSON.stringify(pose())===before,'paused transition advanced');
              const f=G.NarutoSupport.effects.find(f=>f.owner===p&&f.mode==='nine-tails-cloak');
              A.step(f.ttl-f.age-.2);const ending=pose().blend;
              A.assert(ending>0&&ending<1,'expiry snaps to normal');
              A.step(.3);
              A.assert(!pose()&&!G.KyuubiForm.poseFor(clone.anim),'form survived expiry');
              for(const move of p.moves)move.t=999;
              A.cast('naruto-nine-tails-cloak');A.step(.7);
              G.NarutoClones.cast(p,G.Moves.instance('naruto-shadow-clones',2));
              A.assert(G.NarutoClones.actors.every(a=>G.KyuubiForm.poseFor(a.anim)),'new clones missing form');
              G.Camera.x=p.x;G.Camera.y=p.y;
              // Freeze the actual actors in formation for the paired size/readability capture.
              G.EnemyMgr.clear();G.Projectiles.clear();
              for(const a of G.NarutoClones.actors){a.comboT=0;a.anim.once=false;a.anim.base='Idle';}
              return {early,middle,full,ending,clones:G.NarutoClones.actors.length};
            }""")
            page.screenshot(path=str(OUT / f'after-{width}.png'))
            frame.evaluate("G.Combat.clearFields();Acceptance.assert(!G.KyuubiForm.poseFor(G.Game.player.anim),'form survived clear')")
            assert not errors, errors
            (OUT / f'report-{width}.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            page.close()
        browser.close()
    print('PASS: gradual entry/expiry, existing/new shadow clones, pause, cleanup, desktop/mobile')


if __name__ == '__main__':
    main()
