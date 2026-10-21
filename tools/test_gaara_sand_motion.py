"""Capture native Gaara sand phases at fixed simulation ages on desktop/mobile.

Requires the project HTTP server at 8004. This is visual evidence collection,
not a replacement combat implementation or a screenshot-derived assertion.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from test_animation_complete import CHROME, HARNESS
from test_gaara import SETUP, URL
from test_gaara_armor import SETUP_ARMOR

OUT = Path(__file__).resolve().parents[1] / '.omx/state/gaara-sand-motion'
CASES = {
    'armor': ('naruto-sand-armor', [.12, .5, 1.4, 2.8]),
    'burst': ('naruto-sand-armor', [.04, .14, .3, .5]),
    'coffin': ('naruto-sand-coffin', [.18, .48, 1.15, 1.35]),
    'tsunami': ('naruto-sand-tsunami', [.3, .6, .85, 1.3, 1.65]),
    'prison': ('naruto-sand-prison', [.05, .3, 1.1, 2.6]),
    'shower': ('naruto-gaara', [.12, .2, .3, .42]),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill', choices=CASES)
    selected = parser.parse_args().skill
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'failedRequests': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in [False, True]:
            label = 'mobile' if mobile else 'desktop'
            context = browser.new_context(locale='zh-TW', viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.on('response', lambda r: report['failedRequests'].append(r.url) if r.status >= 400 and '127.0.0.1' in r.url else None)
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30007"]').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
            page.evaluate(HARNESS)
            page.evaluate(SETUP)
            page.evaluate(SETUP_ARMOR)
            results = report['viewports'][label] = {}
            for skill, (move, ages) in CASES.items():
                if selected and skill != selected:
                    continue
                page.evaluate("""id => {const A=Acceptance,p=A.p();p.level=15;
                  if(!p.hasMove(id)){
                    // Retain genuine native learning, with one skill per fixture.
                    p.moves=p.moves.filter(m=>m.id==='naruto-gaara');
                    p.slots=p.slots.filter(s=>s.some(m=>m.id==='naruto-gaara'));p.active=0;
                    const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
                    A.assert(card&&card.apply(p)!==false,'native learn fixture '+id);
                  }}""", move)
                frames = []
                results[skill] = []
                for i, age in enumerate(ages):
                    state = page.evaluate("""([skill,id,age])=>{
                      const A=Acceptance,p=A.p(),N=G.NarutoGaara;
                      A.gaaraArena();A.select(id);p.cdMul=1;p.aim=0;p.attackFace=0;
                      const e=A.spawn(skill==='armor'||skill==='burst'?80:170,0);p.target=e;
                      if(skill==='armor'||skill==='burst'){
                        A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()}
                        if(skill==='burst'){A.realArmorHit();A.realArmorHit();A.realArmorHit()}
                      }else if(skill==='prison'){A.advance(6)}else{A.actualCast(id)}
                      for(let t=0;t<age-1e-8;t+=.01)A.advance(Math.min(.01,age-t));
                      if(skill==='armor'&&age>1)A.realArmorHit();
                      p.flash=0;G.EnemyMgr.all().forEach(enemy=>enemy.flash=0);
                      const a=N.active(p),armor=N.armorState(p),prison=N.sandPrisonState(p);
                      return {time:age,phase:a?.phase,armorAge:armor?.age,prisonAge:prison?.age};
                    }""", [skill, move, age])
                    page.wait_for_timeout(35)
                    path = OUT / f'{label}-{skill}-{i}.png'
                    page.locator('#game').screenshot(path=str(path))
                    results[skill].append({**state, 'screenshot': str(path)})
                    with Image.open(path) as im:
                        # Crops retain native pixels and the entire controlled effect.
                        w, h = im.size
                        crop = im.crop((max(0, w//2-110), max(0, h//2-160), min(w, w//2+380), min(h, h//2+150))).convert('RGB')
                    tile = Image.new('RGB', (crop.width, crop.height+28), '#18201e')
                    tile.paste(crop, (0, 28))
                    ImageDraw.Draw(tile).text((8, 7), f'{skill} {age:.2f}s {state.get("phase", "")}', fill='white')
                    frames.append(tile)
                sheet = Image.new('RGB', (sum(f.width for f in frames), max(f.height for f in frames)), '#18201e')
                x = 0
                for frame in frames:
                    sheet.paste(frame, (x, 0)); x += frame.width
                sheet.save(OUT / f'{label}-{skill}-sequence.png')
            context.close()
        browser.close()
    report['ok'] = not report['errors'] and not report['failedRequests']
    report_name = f'capture-{selected}-report.json' if selected else 'capture-report.json'
    (OUT / report_name).write_text(json.dumps(report, indent=2), 'utf-8')
    assert report['ok'], report
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
