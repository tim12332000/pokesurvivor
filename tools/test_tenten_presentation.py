"""Capture actual normal-entry Tenten sequences, including the ignition gap.

Frames use native casts, combat updates and the game's own renderer. The video
plays the captured .05-second simulation steps at 12 fps for readable slow motion.
"""
import json
import os
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_tenten import CHROME, HARNESS, SETUP, PROGRESSION, COMBOS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/tenten-presentation'
URL = os.environ.get('TENTEN_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW')


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
            page.evaluate(HARNESS)
            page.evaluate(SETUP)
            page.evaluate(PROGRESSION)
            result = {'combos': page.evaluate(COMBOS), 'phases': []}
            report['viewports'][label] = result
            frame = 0

            def capture(name=None):
                nonlocal frame
                page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                path = OUT / f'{label}-frame-{frame:03}.jpg'
                page.screenshot(path=str(path), quality=92)
                if name:
                    page.screenshot(path=str(OUT / f'{label}-{name}.png'))
                frame += 1

            page.evaluate("Acceptance.reset();G.Game.player.aim=0;G.Game.player.anim.dir=2;G.Game.player.target=Acceptance.spawn(190,0);Acceptance.castNative('naruto-tenten-fuma')")
            for i in range(29):
                page.evaluate('Acceptance.advance(.05)')
                capture('wire' if i == 6 else 'return' if i == 13 else 'sealed' if i == 28 else None)
            assert page.evaluate('G.NarutoTenten.stateFor(G.Game.player).chargeRemaining>0')
            page.evaluate("Acceptance.castNative('naruto-tenten-twin')")
            for i in range(22):
                page.evaluate('Acceptance.advance(.05)')
                capture('unseal' if i == 1 else 'twin' if i == 6 else None)
            page.evaluate("Acceptance.reset();G.Game.player.aim=0;G.Game.player.anim.dir=2;G.Game.player.moves.find(m=>m.id==='naruto-tenten-tags').count=1;G.Game.player.target=Acceptance.spawn(150,0);Acceptance.castNative('naruto-tenten-tags')")
            for i in range(10):
                page.evaluate('Acceptance.advance(.05)')
                capture('armed' if i == 9 else None)
            page.evaluate('''() => {const T=G.NarutoTenten,tag=T.weapons.find(w=>w.landed),p=G.Game.player;
              p.target.dead=true;G.EnemyMgr.rebuildGrid();const witness=Acceptance.spawn(tag.x,tag.y+38),hurt=witness.hurt;
              window.tagHits=0;witness.hurt=function(...args){if(args[7]==='naruto-tenten-tags')window.tagHits++;return hurt.apply(this,args)};
              p.target=Acceptance.spawn(220,0);Acceptance.castNative('naruto-tenten')}''')
            found = set()
            for i in range(22):
                page.evaluate('Acceptance.advance(.05)')
                phase = page.evaluate('''() => {const T=G.NarutoTenten,w=T.weapons.find(w=>w.triggered&&!w.dead),b=T.blasts[0];
                  return {ignition:!!w,blast:!!b,blastAge:b?.age||0,tagHits:window.tagHits,hp:G.Game.player.target.hp}}''')
                if phase['ignition']:
                    assert phase['tagHits'] == 0, 'Tag damaged the witness before ignition finished'
                name = None
                if phase['ignition'] and 'ignition' not in found:
                    name = 'ignition'
                    found.add(name)
                if phase['blast'] and phase['blastAge'] >= .1 and 'blast' not in found:
                    name = 'blast'
                    found.add(name)
                result['phases'].append(phase)
                capture(name)
            assert found == {'ignition', 'blast'}, (label, found)
            assert result['phases'][-1]['tagHits'] == 1, 'Ignited tag did not damage the witness exactly once'
            # The ignition is an actual combat phase, not a renderer-only effect.
            assert next(i for i, p in enumerate(result['phases']) if p['ignition']) < next(i for i, p in enumerate(result['phases']) if p['blast'])
            page.evaluate('''() => {const A=Acceptance,p=A.p();A.reset();p.target=A.spawn(190,0);A.castNative('naruto-tenten-twin');A.advance(.25);
              const pose=G.NarutoTenten.activeFor(p),age=pose.age,count=pose.emitted;
              const cv=document.createElement('canvas'),ctx=cv.getContext('2d');
              G.Settings.set('calm',true);G.Combat.drawAirFields(ctx);G.Combat.drawAirFields(ctx);
              A.assert(pose.age===age&&pose.emitted===count,'drawing advanced the action');}''')
            capture('calm')
            result['frames'] = frame
            context.close()
            ffmpeg = Path(os.environ.get('LOCALAPPDATA', '')) / 'ms-playwright/ffmpeg-1011/ffmpeg-win64.exe'
            assert ffmpeg.is_file(), 'Existing Playwright ffmpeg is required for the review clip'
            frames = b''.join((OUT / f'{label}-frame-{i:03}.jpg').read_bytes() for i in range(frame))
            subprocess.run([str(ffmpeg), '-y', '-f', 'image2pipe', '-framerate', '12', '-c:v', 'mjpeg', '-i', 'pipe:0',
                            '-c:v', 'libvpx', '-b:v', '1800k', str(OUT / f'{label}-showcase.webm')],
                           check=True, input=frames, capture_output=True)
            print(label, 'presentation and native combos PASS', flush=True)
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
