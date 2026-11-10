"""Native RAF recordings and phase images for Madara pursuit; no runtime edits.

Controlled open-ground scenes are distinct from the unmodified Lv1 opening.
Uses the existing Playwright/Chrome installation and local lab server on 8347.
"""
from __future__ import annotations

import base64
import hashlib
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_jujutsu as base
import test_madara_rework_play as native

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art-review/madara-pursuit-20261111/qa/visual'
URL = 'http://127.0.0.1:8347/.omx/digimon.html?lang=zh-TW'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


OBSERVE = r'''() => {
 const M=G.NarutoMadara,p=G.Game.player;
 const R=window.PursuitVisual={samples:[],frames:[],seen:new Set(),running:true};
 const canvas=[...document.querySelectorAll('canvas')].sort((a,b)=>b.width*b.height-a.width*a.height)[0];
 function sample(){if(!R.running)return;if(G.Game.state!=='playing'){requestAnimationFrame(sample);return;}const s=M.stateFor(p),f=s?.body,pose=M.pose(p);
  const row={time:G.Game.st.time,clock:s?.clock,state:G.Game.state,level:p.level,hp:p.hp,x:p.x,y:p.y,
   body:f?{pursuit:!!f.pursuit,index:f.index,contacts:f.spec.contacts,phase:f.pursuitPhase,pose:pose?.contact,posePhase:pose?.phase,target:f.target?.id}:null,
   hits:s?.hits||0,impetus:s?.impetus||0};R.samples.push(row);
  const key=f?.pursuit?(f.pursuitPhase==='contact'&&pose?.phase==='contact'?`${f.index}-${pose.contact}`:f.pursuitPhase==='return'?'return':null):null;
  if(key&&!R.seen.has(key)){R.seen.add(key);R.frames.push({key,state:row,png:canvas.toDataURL()});}
  requestAnimationFrame(sample);
 }requestAnimationFrame(sample);
}'''

SCENE = r'''opts=>{
 const A=JAcceptance,p=A.p();A.reset();const m=A.fixture('naruto-madara',opts.rank);
 p.quantityPicks=opts.quantity;p.hp=p.maxHp;p.xpNext=1e12;p.critChance=0;
 const positions=opts.weak?[[150,0],[230,90],[160,-100],[70,-130],[-30,70]]:[[150,0],[230,90],[160,-100]];
 const targets=positions.map(v=>A.spawn(...v));if(opts.weak)for(const e of targets)e.hp=e.maxHp=1;
 G.Spawner.update=()=>{};for(const e of targets){e.spd=0;e.dmg=0;}
 window.PursuitScene={targets,hits:targets.map(A.watch),rank:opts.rank,quantity:opts.quantity};
 m.t=0;A.resume();A.assert(G.NarutoMadara.cast(p,m),'native pursuit rejected');
 return {rank:opts.rank,quantity:opts.quantity,spec:G.NarutoMadara.profile(p,m)};
}'''


def boot(page, label):
    page.goto(URL + ('&layout=wide' if label.startswith('desktop') else ''))
    frame = native.frame_for(page)
    frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if frame.locator('#tap-start').is_visible():
        frame.locator('#tap-start').click()
    frame.locator('[data-quick-naruto="30016"]').click()
    frame.wait_for_function('G.NarutoAssets.ready(30016)')
    page.screenshot(path=str(OUT / label / 'selection.png'))
    frame.locator('#scr-menu [data-go="play"]').click()
    frame.wait_for_function('G.Game.player?.dex===30016&&G.Game.state==="playing"')
    page.screenshot(path=str(OUT / label / 'normal-entry.png'))
    return frame


def collect(frame, folder, name):
    data = frame.evaluate('''()=>{const R=PursuitVisual;R.running=false;
      return {samples:R.samples,frames:R.frames,scene:window.PursuitScene?{rank:PursuitScene.rank,quantity:PursuitScene.quantity,hits:PursuitScene.hits.map(h=>h.length)}:null}}''')
    for previous in folder.glob(f'{name}-*.png'):
        previous.unlink()
    for item in data['frames']:
        (folder / f'{name}-{item["key"]}.png').write_bytes(base64.b64decode(item.pop('png').split(',', 1)[1]))
    save(folder / f'{name}.json', data)
    return {'samples': len(data['samples']), 'frames': [v['key'] for v in data['frames']], 'scene': data['scene']}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'Native RAF evidence; open-ground fixtures are controlled, Lv1 opening is unmodified.', 'sourceSha256': hashlib.sha256((ROOT / '.omx/naruto-madara.js').read_bytes()).hexdigest(), 'surfaces': {}, 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        for label, width, height in [('desktop', 1280, 900), ('mobile390-low', 390, 844)]:
            folder = OUT / label
            folder.mkdir(parents=True, exist_ok=True)
            context = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=width < 500, has_touch=width < 500, service_workers='block', record_video_dir=str(folder / 'video'), record_video_size={'width': width, 'height': height})
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            frame = boot(page, label)
            frame.evaluate("q=>G.Settings.set('quality',q)", 'low' if width < 500 else 'high')
            frame.evaluate(OBSERVE)
            page.wait_for_timeout(6500)
            natural = collect(frame, folder, 'natural-lv1')
            page.screenshot(path=str(folder / 'natural-lv1.png'))
            frame.evaluate(base.SETUP)
            scenes = []
            for rank, quantity in [(1, 0), (1, 1), (5, 4)]:
                frame.evaluate(OBSERVE)
                spec = frame.evaluate(SCENE, {'rank': rank, 'quantity': quantity})
                page.wait_for_timeout(4200)
                frame.evaluate('JAcceptance.pause()')
                scenes.append({'spec': spec, **collect(frame, folder, f'r{rank}-q{quantity}')})
                page.screenshot(path=str(folder / f'r{rank}-q{quantity}-end.png'))
            frame.evaluate(OBSERVE)
            weak_spec = frame.evaluate(SCENE, {'rank': 1, 'quantity': 0, 'weak': True})
            page.wait_for_timeout(3000)
            frame.evaluate('JAcceptance.pause()')
            scenes.append({'spec': weak_spec, 'scope': 'controlled one-hit enemies, actual vulnerability unchanged', **collect(frame, folder, 'weak-enemy-gestures')})
            # A real keyboard retreat checks native movement precedence on desktop.
            retreat = None
            if width >= 500:
                frame.evaluate(SCENE, {'rank': 1, 'quantity': 1})
                page.wait_for_timeout(140)
                before = frame.evaluate('()=>({x:G.Game.player.x,y:G.Game.player.y,pursuit:!!G.NarutoMadara.stateFor(G.Game.player)?.body?.pursuit})')
                page.keyboard.down('KeyA')
                page.wait_for_timeout(350)
                after = frame.evaluate('()=>({x:G.Game.player.x,y:G.Game.player.y,pursuit:!!G.NarutoMadara.stateFor(G.Game.player)?.body?.pursuit,axis:G.Input.axis()})')
                frame.evaluate('JAcceptance.pause()')
                page.keyboard.up('KeyA')
                retreat = {'before': before, 'after': after}
                page.screenshot(path=str(folder / 'keyboard-retreat.png'))
            else:
                frame.evaluate(SCENE, {'rank': 1, 'quantity': 1})
                page.wait_for_timeout(140)
                before = frame.evaluate('()=>({x:G.Game.player.x,y:G.Game.player.y,pursuit:!!G.NarutoMadara.stateFor(G.Game.player)?.body?.pursuit})')
                client = context.new_cdp_session(page)
                stick = frame.evaluate('G.Touch.stickBase()')
                if frame != page.main_frame:
                    box = page.locator('iframe').first.bounding_box()
                    stick = {'x': stick['x'] + box['x'], 'y': stick['y'] + box['y']}
                client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [stick]})
                client.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': stick['x'] - 42, 'y': stick['y']}]})
                page.wait_for_timeout(350)
                after = frame.evaluate('()=>({x:G.Game.player.x,y:G.Game.player.y,pursuit:!!G.NarutoMadara.stateFor(G.Game.player)?.body?.pursuit,touch:G.Touch.vector()})')
                client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                frame.evaluate('JAcceptance.pause()')
                retreat = {'before': before, 'after': after, 'input': 'native CDP touch joystick'}
                page.screenshot(path=str(folder / 'touch-retreat.png'))
            video = page.video
            context.close()
            video.save_as(str(folder / 'native-pursuit.webm'))
            video.delete()
            report['surfaces'][label] = {'natural': natural, 'controlled': scenes, 'keyboardRetreat': retreat}
            save(OUT / 'report.json', report)
            print(label, 'saved', flush=True)
        browser.close()
    report['endingSourceSha256'] = hashlib.sha256((ROOT / '.omx/naruto-madara.js').read_bytes()).hexdigest()
    report['stableSource'] = report['sourceSha256'] == report['endingSourceSha256']
    save(OUT / 'report.json', report)


if __name__ == '__main__':
    main()
