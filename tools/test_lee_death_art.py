"""Check three real gate upgrades, all Death Gate sources, and expiry on desktop/mobile."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

OUT = Path(__file__).resolve().parents[1] / '.omx/state/lee-death'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, width, height in [('desktop', 1280, 800), ('mobile', 390, 844)]:
            ctx = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=label == 'mobile', has_touch=label == 'mobile')
            page = ctx.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto('http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=lee&layout=wide')
            page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30006"]').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
            page.evaluate(HARNESS)
            page.evaluate(SETUP)
            result = page.evaluate(r"""() => {
              const A=Acceptance,p=A.p(),g=G.NarutoGates,out={stages:[],sources:[]};p.level=12;
              p.addMove('naruto-gates');const m=p.moves.find(m=>m.id==='naruto-gates');
              for(let n=1;n<=3;n++){
                if(n>1)A.assert(G.Moves.levelUp(m),'upgrade failed');
                A.advance(5.01);p.walking=false;
                const pose=G.AnimationLab.stateFor(p.anim);
                A.assert(m.lvl===n&&m.def.maxLvl===3,'wrong stage limit');
                A.assert(pose.key.startsWith(n===3?'lee-death-':'lee-opened-'),'wrong form '+pose.key);
                out.stages.push({level:n,name:m.name,pose});
              }
              A.assert(!G.Moves.levelUp(m)&&m.lvl===3,'fourth stage accepted');
              A.assert(g.effectTier(p)===5&&g.attackSpeedMultiplier(p)===1.5,'death lost old fifth tier');
              for(const key of AnimationAssets.keys.filter(k=>k.startsWith('lee-death-'))){
                const asset=AnimationAssets.get(key);A.assert(asset.image&&asset.source.includes('lee-death-')&&asset.source.endsWith('-v3.png'),'missing final death source');
                for(let i=0;i<asset.frames.length;i++){
                  const c=document.createElement('canvas');c.width=240;c.height=200;
                  A.assert(AnimationAssets.draw(c.getContext('2d'),key,i,120,160),'empty death frame');
                }
                out.sources.push({key,source:asset.source,frames:asset.frames.length});
              }
              A.assert(out.sources.length===12,'missing action sequence');
              out.actor=A.render();
              A.advance(10);
              const closed=G.AnimationLab.stateFor(p.anim);
              A.assert(!g.active(p)&&!g.redSkin(p)&&!g.redForm(p)&&closed.key.startsWith('lee-')&&!closed.key.startsWith('lee-opened-')&&!closed.key.startsWith('lee-death-'),'closing did not directly restore normal Lee');
              out.closed={stage:g.stage(p),pose:closed};out.normalActor=A.render();
              return out;
            }""")
            (OUT / f'{label}-actor.png').write_bytes(base64.b64decode(result['actor'].pop('png').split(',')[1]))
            (OUT / f'{label}-closed.png').write_bytes(base64.b64decode(result['normalActor'].pop('png').split(',')[1]))
            report['viewports'][label] = result
            ctx.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'art-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), 'utf-8')
    print(json.dumps({'ok': True, 'viewports': list(report['viewports']), 'sequences': 12}))


if __name__ == '__main__':
    main()
