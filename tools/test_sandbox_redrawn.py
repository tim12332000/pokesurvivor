"""Exercise the standalone sandbox's default hero art without the lab wrapper."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_animation_complete as acceptance
from test_redrawn_heroes import AUDIT

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / '.omx/state/sandbox-redrawn'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'viewports': {}, 'errors': [], 'failedRequests': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=acceptance.CHROME, headless=True)
        for mobile in [False, True]:
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else
                                          {'width': 1200, 'height': 900}, is_mobile=mobile,
                                          has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.on('response', lambda r: report['failedRequests'].append(r.url) if r.status >= 400 else None)
            page.goto('http://127.0.0.1:8318/.omx/digimon.html?lang=zh-TW')
            page.wait_for_function('!!G.AnimationLab && !!G.KyuubiForm && G.DB.save && document.querySelector("#boot").classList.contains("hidden")')
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            assert page.locator('iframe, #continuity, #candidate, #cast-audit').count() == 0
            poses = {}
            for dex in [30001, 30002]:
                page.evaluate('''dex => {
                  if(G.Game.player){G.Game.quit();G.Flow.goMenu()}
                  G.Naruto.choose(dex);G.Flow.play();
                  const p=G.Game.player,c=G.NarutoSkillCatalog;
                  const ids=[...new Set([c.byDex.get(dex)?.id,...(c.extraPools.get(dex)||[]),'naruto-kunai','naruto-shuriken'].filter(Boolean))];
                  p.maxMoves=ids.length;for(const id of ids)if(!p.hasMove(id))p.addMove(id);
                }''', dex)
                page.evaluate(acceptance.HARNESS)
                page.evaluate(AUDIT)
                page.evaluate('Acceptance.arena()')
                result = page.evaluate('''() => {
                  const p=Acceptance.p(),poses={};
                  for(const [name,options] of [['idle',{}],['flash',{flash:true}],['alpha',{alpha:.5}]]){
                    const r=Acceptance.render(p.anim,options);delete r.png;poses[name]=r;
                  }
                  p.walking=true;p.anim.play('Walk');
                  const moving=Acceptance.render();delete moving.png;poses.movement=moving;
                  p.walking=false;
                  const cv=document.createElement('canvas');cv.width=240;cv.height=200;
                  document.body.append(cv);const preview=G.UI.sprite(cv,p.dex,{shadow:false});
                  const r=Acceptance.render(preview.a);delete r.png;poses.menu=r;cv.remove();
                  Acceptance.resume();p.invuln=0;p.hurt(5,null,true);Acceptance.pause();
                  const h=Acceptance.render();delete h.png;poses.damage=h;
                  return poses;
                }''')
                if dex == 30001:
                    result['clones'] = page.evaluate('''() => {
                      Acceptance.arena();Acceptance.cast('naruto-shadow-clones');Acceptance.step(.8);
                      Acceptance.assert(G.NarutoClones.actors.length,'clone spawn missing');
                      return G.NarutoClones.actors.map(a=>{const r=Acceptance.render(a.anim);delete r.png;return r});
                    }''')
                    page.evaluate('Acceptance.arena()')
                    result['cloak'] = page.evaluate('''() => {
                      Acceptance.cast('naruto-nine-tails-cloak');Acceptance.step(.1);
                      const r=Acceptance.render();delete r.png;
                      Acceptance.assert(r.form,'cloak form missing');
                      G.Combat.clearFields();
                      Acceptance.assert(!G.KyuubiForm.poseFor(Acceptance.p().anim),'form survived clear');
                      return r;
                    }''')
                poses[str(dex)] = result
            if mobile:
                page.evaluate('Acceptance.arena();Acceptance.resume();G.Game.player.invuln=99999')
                before = page.evaluate('G.Game.player.x')
                bounds = page.locator('#game').bounding_box()
                assert bounds and bounds['y'] + bounds['height'] <= 844.5, bounds
                cdp = context.new_cdp_session(page)
                x, y = bounds['x'] + 85, bounds['y'] + bounds['height'] * .6
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x+48, 'y': y}]})
                page.wait_for_timeout(140)
                after = page.evaluate('({x:G.Game.player.x,walking:G.Game.player.walking})')
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                assert after['walking'] and after['x'] > before, (before, after)
            report['viewports']['mobile' if mobile else 'desktop'] = poses
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    assert not report['errors'], report['errors']
    assert not report['failedRequests'], report['failedRequests']
    print('Standalone sandbox redraw: desktop/mobile actors, flash, movement and cloak lifecycle passed')


if __name__ == '__main__':
    main()
