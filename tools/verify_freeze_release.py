"""Compare a live classic LF2 package to its artifact and open each selected hero."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://tim12332000.github.io/pokesurvivor/'
OUT = ROOT / '.omx/state/freeze/public'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('artifact', type=Path)
    parser.add_argument('source')
    parser.add_argument('--heroes', nargs='+', choices=['freeze','firzen','julian','firen'], default=['freeze'])
    args = parser.parse_args()
    artifact = args.artifact.resolve()
    assert artifact.is_relative_to(ROOT)
    scope='firen' if 'firen' in args.heroes else 'lf2-bosses' if any(hero!='freeze' for hero in args.heroes) else 'freeze'
    OUT=ROOT/'.omx/state'/scope/'public'
    OUT.mkdir(parents=True, exist_ok=True)
    paths = ['index.html', '.omx/digimon.html', '.omx/naruto.js', '.omx/redrawn-init.js',
             '.omx/lf2.js', '.omx/lf2-art.js', '.omx/lf2-audio.js', '.omx/lf2-freeze-combat.js',
             'js/core/audio.js', 'js/entities/enemy.js', 'js/systems/combat.js', 'js/systems/self-clone.js', 'js/systems/hazards.js',
             'assets/lf2/freeze/manifest.json']
    if scope!='freeze':
        paths += ['.omx/lf2-bosses.js','.omx/lf2-boss-art.js','.omx/lf2-firzen-combat.js','.omx/lf2-julian-combat.js']
    if 'firen' in args.heroes:
        paths += ['.omx/lf2-firen.js','.omx/lf2-firen-art.js','.omx/lf2-firen-combat.js']
    for hero in dict.fromkeys(['freeze',*args.heroes]):
        paths += [p.relative_to(artifact).as_posix() for p in (artifact/'assets/lf2'/hero).iterdir()
                  if p.is_file() and p.suffix in {'.png','.wav','.json'}]
    paths=list(dict.fromkeys(paths))
    checked = {}
    for name in paths:
        expected = hashlib.sha256((artifact/name).read_bytes()).hexdigest()
        with urllib.request.urlopen(BASE + name + '?verify=' + args.source, timeout=45) as response:
            actual = hashlib.sha256(response.read()).hexdigest()
        assert actual == expected, 'Public file differs: ' + name
        checked[name] = actual
    (OUT/'bytes.json').write_text(json.dumps(checked, indent=2), 'utf-8')
    browser_report = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
        for hero in args.heroes:
            dex,starter={'freeze':(30018,'lf2-iceball'),'firzen':(30019,'lf2-firzen-cannon'),'julian':(30020,'lf2-julian-skull'),'firen':(30021,'lf2-firen-ball')}[hero]
            for name, viewport, mobile in [('desktop', {'width':1100,'height':850}, False),
                                           ('mobile390', {'width':390,'height':844}, True)]:
                context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile)
                page = context.new_page()
                errors, failed = [], []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('response', lambda r: failed.append({'status':r.status,'url':r.url}) if r.status >= 400 and 'github.io/pokesurvivor/' in r.url else None)
                url = BASE + '?lang=zh-TW&hero='+hero+'&release=' + args.source[:8]
                if not mobile: url += '&layout=wide'
                page.goto(url)
                page.wait_for_function("window.G?.LF2Freeze&&document.getElementById('boot').classList.contains('hidden')", timeout=60000)
                if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
                page.locator(f'[data-quick-naruto="{dex}"]').click()
                page.wait_for_function('(dex)=>G.NarutoAssets.ready(dex)', arg=dex, timeout=30000)
                kit=page.evaluate('''() => {
                  const dex=+G.DB.save.partner,rows=dex===30018?G.LF2.kit[1]:G.LF2Bosses.kits.find(row=>row[0]===dex)[1];
                  return {ids:rows.map(row=>row[0]),labels:[...document.querySelectorAll('.launch-kit b')].map(el=>el.textContent)};
                }''')
                expected={'freeze':['lf2-iceball','lf2-sword','lf2-column','lf2-whirlwind'],
                          'firzen':['lf2-firzen-cannon','lf2-firzen-disaster','lf2-firzen-volcano'],
                          'firen':['lf2-firen-ball','lf2-firen-blaze','lf2-firen-inferno','lf2-firen-explosion'],
                          'julian':['lf2-julian-skull','lf2-julian-punch','lf2-julian-uppercut','lf2-julian-mirror','lf2-julian-ball','lf2-julian-blast']}[hero]
                assert kit['ids']==expected and len(kit['labels'])==len(expected),kit
                page.screenshot(path=str(OUT/(hero+'-'+name+'-selection.png')))
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('(dex)=>G.Game.player?.dex===dex&&G.Game.state==="playing"',arg=dex)
                initial=page.evaluate('G.Game.player.level');assert initial==1
                page.keyboard.down('KeyD')
                page.wait_for_timeout(1500)
                page.keyboard.up('KeyD')
                page.screenshot(path=str(OUT/(hero+'-'+name+'-play.png')))
                state = page.evaluate('({dex:G.Game.player.dex,level:G.Game.player.level,ready:G.NarutoAssets.ready(G.Game.player.dex),moves:G.Game.player.moves.map(m=>m.id),label:document.querySelector(".launch-name")?.textContent||null})')
                assert state['dex'] == dex and state['ready'] and state['moves'][0] == starter
                assert not errors and not failed, {'errors':errors,'failed':failed}
                browser_report[hero+'-'+name] = {'initialLevel':initial,**state, 'kit':kit, 'errors':errors, 'failed':failed, 'url':page.url}
                context.close()
        browser.close()
    (OUT/'browser.json').write_text(json.dumps(browser_report, indent=2), 'utf-8')
    print(json.dumps({'ok':True,'files':len(checked),'browsers':list(browser_report)}))


if __name__ == '__main__':
    main()
