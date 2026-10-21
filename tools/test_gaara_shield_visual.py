"""Capture native sand-shield reactions through the normal Gaara picker.

Requires the repository HTTP server on port 8004. Full game screenshots are
the evidence; contact sheets only enlarge crops of those screenshots.
Run: uv run --with playwright --with pillow python tools/test_gaara_shield_visual.py
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from test_gaara import CHROME, HARNESS, SETUP, PROGRESSION, URL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/gaara-shield'
DIRECTIONS = {
    'right': {'fromX': 100, 'fromY': 0},
    'down': {'fromX': 0, 'fromY': 100},
    'left': {'fromX': -100, 'fromY': 0},
    'up': {'fromX': 0, 'fromY': -100},
    'neutral': None,
}

FIXTURE = r"""([kind,context]) => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara;
 A.gaaraArena();A.select('naruto-sand-shield');p.cdMul=1;A.advance(.8);
 const original=N.shieldState(p),hp=p.hp;
 if(kind==='low'){
   p.invuln=0;p.hurt(original.capacity-5,null,true,context);A.advance(.8);
 }else if(kind==='break'){
   p.invuln=0;p.hurt(original.capacity+7,null,true,context);
 }else if(kind==='hit'){
   p.invuln=0;p.hurt(2,null,true,context);
 }
 const s=N.shieldState(p);
 A.assert(s.capacity===45+p.level,'visual fixture changed level-scaled capacity');
 if(kind==='hit')A.assert(p.hp===hp&&s.amount===original.amount-2,'hit absorption changed');
 if(kind==='low')A.assert(p.hp===hp&&s.amount===5,'low-shield fixture failed');
 if(kind==='break')A.assert(p.hp===hp-7&&s.amount===0&&s.broken,'break overflow changed');
 A.shieldVisualSnapshot=()=>{
   const s=N.shieldState(p);
   return {hp:p.hp,amount:s.amount,capacity:s.capacity,flash:s.flash,
     flashAim:s.flashAim,hitAim:s.hitAim,broken:s.broken,age:s.age,
     progress:s.progress,remaining:s.remaining};
 };
 return A.shieldVisualSnapshot();
}"""


def save_frame(page, label, name, result, captures):
    path = OUT / f'{label}-{name}.png'
    page.locator('#game').screenshot(path=str(path))
    state = page.evaluate('Acceptance.shieldVisualSnapshot()')
    result[name] = state
    captures.append((name, path))


def contact_sheet(page, label, captures):
    # Coordinates come from the same native camera used by the game. Cropping
    # does not call a VFX draw function or substitute a separate renderer.
    camera = page.evaluate("""() => ({scale:G.Camera.scale,
      x:(G.Game.player.x-G.Camera.left())*G.Camera.scale,
      y:(G.Game.player.y-G.Camera.top())*G.Camera.scale})""")
    cols, cell_w, cell_h = 4, 300, 260
    rows = (len(captures) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cell_w, rows * cell_h), '#171c24')
    draw = ImageDraw.Draw(sheet)
    half_w, half_h = 80 * camera['scale'], 62 * camera['scale']
    for index, (name, path) in enumerate(captures):
        image = Image.open(path).convert('RGB')
        cx, cy = camera['x'], camera['y'] - 14 * camera['scale']
        crop = image.crop((round(cx-half_w), round(cy-half_h),
                           round(cx+half_w), round(cy+half_h)))
        factor = min((cell_w-12)/crop.width, (cell_h-30)/crop.height)
        crop = crop.resize((round(crop.width*factor), round(crop.height*factor)),
                           Image.Resampling.NEAREST)
        x, y = (index % cols) * cell_w, (index // cols) * cell_h
        sheet.paste(crop, (x+(cell_w-crop.width)//2, y+25))
        draw.text((x+8, y+6), name, fill='#ffffff')
    sheet.save(OUT / f'{label}-contact-sheet.png')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'failedRequests': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in (False, True):
                label = 'mobile' if mobile else 'desktop'
                context = browser.new_context(
                    locale='zh-TW', service_workers='block',
                    viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900},
                    is_mobile=mobile, has_touch=mobile)
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('response', lambda r: report['failedRequests'].append(r.url)
                        if r.status >= 400 and '127.0.0.1' in r.url else None)
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click()
                assert page.evaluate('G.DB.save.partner===30007')
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                page.evaluate(HARNESS)
                page.evaluate(SETUP)
                page.evaluate(PROGRESSION)
                # Shield overflow also triggers native player flash. Advance
                # the real player and particles alongside fields so settle
                # evidence does not freeze that transient white silhouette.
                page.evaluate("""() => {
                  const A=Acceptance;
                  A.advance=dt=>{A.resume();try{
                    G.Combat.updateFields(dt);A.p().update(dt);G.FX.update(dt);
                  }finally{A.pause()}};
                }""")
                result, captures = {}, []
                report['viewports'][label] = result
                for kind in ('idle', 'low'):
                    page.evaluate(FIXTURE, [kind, DIRECTIONS['right']])
                    save_frame(page, label, kind, result, captures)
                    if kind == 'idle':
                        page.evaluate('Acceptance.advance(.7)')
                        save_frame(page, label, 'idle-flow', result, captures)
                for name, direction in DIRECTIONS.items():
                    page.evaluate(FIXTURE, ['hit', direction])
                    for age in (0, .08, .16):
                        if age:
                            page.evaluate('Acceptance.advance(.08)')
                        save_frame(page, label, f'hit-{name}-{age:.2f}', result, captures)
                    page.evaluate('Acceptance.advance(.64)')
                    save_frame(page, label, f'settle-{name}', result, captures)
                page.evaluate(FIXTURE, ['break', DIRECTIONS['right']])
                for age in (0, .08, .16):
                    if age:
                        page.evaluate('Acceptance.advance(.08)')
                    save_frame(page, label, f'break-{age:.2f}', result, captures)
                page.evaluate('Acceptance.advance(.64)')
                save_frame(page, label, 'break-settle', result, captures)
                before = page.evaluate('Acceptance.shieldVisualSnapshot()')
                page.evaluate('G.Combat.updateFields(.5)')
                after = page.evaluate('Acceptance.shieldVisualSnapshot()')
                assert before == after, f'{label}: paused shield advanced'
                result['pausedSnapshotUnchanged'] = True
                contact_sheet(page, label, captures)
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        assert not report['failedRequests'], report['failedRequests']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT / 'visual-report.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
