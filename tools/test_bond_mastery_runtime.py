"""Mastery choices must render safely before Yuta has a combat state.

Uses production entry, real choice buttons and native RAF. Controlled inventory
isolates learning/upgrade rewards; it is not natural long-run progression.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('BOND_MASTERY_OUT', ROOT / '.omx/state/bond-mastery-runtime'))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base.OUT = OUT
    base.URL = os.environ.get('JUJUTSU_URL', 'http://127.0.0.1:8368/.omx/digimon.html?lang=zh-TW')
    report = {'ok': False, 'cases': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        for mobile in [False, True]:
            label = 'mobile' if mobile else 'desktop'
            context = browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
            frame = base.boot(page, 30013, label)
            errors.clear()
            results = report['cases'][label] = {}
            # Learning the ring is a real mastery option, selected by its button.
            options = frame.evaluate("""()=>{
              const A=JAcceptance,p=A.p();A.reset();A.fixture('jjk-yuta');p.bonds=1;
              p.banned=new Set(['jjk-yuta-rika','jjk-yuta-speech','jjk-yuta-resonance']);
              G.Spawner.update=()=>{};p.invuln=999;A.resume();G.Game.offerBond(true);
              return G.JujutsuGrowth.bondState(p).options.map(c=>c.key);
            }""")
            index = options.index('new:jjk-yuta-manifest')
            frame.locator('#council-choice button').nth(index).click()
            page.wait_for_timeout(200)
            learned = frame.evaluate("""()=>({state:G.Game.state,bonds:G.Game.player.bonds,learned:G.Game.player.hasMove('jjk-yuta-manifest')})""")
            assert learned == {'state':'playing','bonds':0,'learned':True}, learned
            results['learnManifest'] = learned
            for scenario in ['neverCast', 'cleared']:
                before = frame.evaluate("""scenario=>{
                  const A=JAcceptance,p=A.p();A.reset();A.fixture('jjk-yuta-manifest');p.bonds=1;p.banned=new Set();
                  A.resume();if(scenario==='cleared'){G.Combat.tick(.01,p,0);G.Combat.clearFields(p)}
                  const missing=!G.JujutsuYuta.stateFor(p);G.Game.offerBond(true);
                  return {missing,state:G.Game.state,bonds:p.bonds,time:G.Game.st.time};
                }""", scenario)
                assert before['missing'] and before['state'] == 'choice', before
                # Exceeds 180 native frames on common 60Hz hosts: the old null
                # dereference repeatedly faults and invokes the run-exit guard.
                page.wait_for_timeout(3600)
                held = frame.evaluate("""()=>({state:G.Game.state,bonds:G.Game.player.bonds,time:G.Game.st.time,dialog:!!document.getElementById('council-choice')})""")
                results[scenario] = {'before':before, 'held':held, 'errors':list(errors)}
                (OUT/'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
                assert not errors, errors
                assert held['state'] == 'choice' and held['dialog'] and held['time'] == before['time'], held
                page.screenshot(path=str(OUT/f'{label}-{scenario}-choice.png'))
                frame.locator('#council-choice button').first.click()
                page.wait_for_timeout(250)
                after = frame.evaluate("""()=>({state:G.Game.state,bonds:G.Game.player.bonds,dialog:!!document.getElementById('council-choice')})""")
                results[scenario]['after'] = after
                assert after == {'state':'playing','bonds':0,'dialog':False}, after
                assert not errors, errors
            context.close()
        browser.close()
    report['ok'] = True
    (OUT/'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({'ok':True,'evidence':str(OUT)}))


if __name__ == '__main__':
    main()
