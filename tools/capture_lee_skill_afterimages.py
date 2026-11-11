"""Bounded native RAF captures for Lee skill afterimages, without Gates.

Scenes use production poses, enemies and combat. Static open-ground fixtures
are labeled controlled; they do not claim natural growth or device performance.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_jujutsu as base
import test_madara_rework_play as native

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art-review/lee-skill-afterimages-20261112/qa/visual' / os.environ.get('LEE_TRAIL_LABEL', 'initial')
URL = 'http://127.0.0.1:8347/.omx/digimon.html?lang=zh-TW'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


OBSERVER = r'''() => {
 const p=G.Game.player,R=window.LeeTrailVisual={running:true,seen:new Set(),samples:[],frames:[]};
 const canvas=[...document.querySelectorAll('canvas')].sort((a,b)=>b.width*b.height-a.width*a.height)[0];
 function sample(){if(!R.running)return;
  if(G.Game.state==='playing'){
   const pose=G.AnimationLab.stateFor(p.anim),ghosts=G.NarutoGates.afterimagesFor(p);
   const row={time:G.Game.st.time,x:p.x,y:p.y,hp:p.hp,stage:G.NarutoGates.stage(p),pose:pose?{id:pose.id,key:pose.key,phase:pose.phase,frame:pose.frame,offsetX:pose.offsetX||0,offsetY:pose.offsetY||0,visualLift:pose.visualLift||0,rotation:pose.rotation||0}:null,ghosts};
   R.samples.push(row);
   if(pose?.state==='skill'&&ghosts.some(g=>g.natural)){
    const phase=pose.phase+(pose.visualLift>=30?'-high':''),key=phase+'-'+pose.key;
    if(!R.seen.has(key)){R.seen.add(key);R.frames.push({key,state:row,png:canvas.toDataURL()});}
   }
  }requestAnimationFrame(sample);
 }requestAnimationFrame(sample);
}'''

SCENE = r'''opts=>{
 const A=JAcceptance,p=A.p();A.reset();const m=A.fixture(opts.id,opts.rank||1);
 p.quantityPicks=0;p.quantityBonus=0;p.critChance=0;p.xpNext=1e12;
 G.Spawner.update=()=>{};const e=A.spawn(opts.id==='naruto-lee-pursuit'?140:35,0);e.dmg=0;
 p.target=e;p.aim=0;m.t=0;A.resume();
 if(opts.id==='naruto-lotus'||opts.id==='naruto-reverse-lotus')A.assert(G.NarutoLee.cast(p,m),'lotus cast rejected');
 else if(opts.id==='naruto-lee'){G.Combat.tick(.001,p,0);A.assert(G.DigimonSkills.whirlwindFor(p),'whirlwind did not start');}
 else if(opts.id==='naruto-lee-drunken'){const rng=Math.random;Math.random=()=>0;try{p.hurt(20,'normal',false,{fromX:e.x,fromY:e.y})}finally{Math.random=rng}A.assert(G.NarutoDrunkenFist.activeFor(p),'drunken reaction did not start');}
 return {id:opts.id,rank:m.lvl,stage:G.NarutoGates.stage(p),target:e.id};
}'''


def boot(page, label, folder):
    page.goto(URL + ('&layout=wide' if label == 'desktop' else ''))
    frame = native.frame_for(page)
    frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if frame.locator('#tap-start').is_visible():
        frame.locator('#tap-start').click()
    frame.locator('[data-quick-naruto="30006"]').click()
    frame.wait_for_function('G.NarutoAssets.ready(30006)')
    page.screenshot(path=str(folder / 'selection.png'))
    frame.locator('#scr-menu [data-go="play"]').click()
    frame.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
    page.screenshot(path=str(folder / 'normal-entry.png'))
    frame.evaluate(base.SETUP)
    return frame


def collect(frame, folder, slug):
    data = frame.evaluate('()=>{LeeTrailVisual.running=false;return {samples:LeeTrailVisual.samples,frames:LeeTrailVisual.frames}}')
    for item in data['frames']:
        path = folder / f'{slug}-{item["key"]}.png'
        path.write_bytes(base64.b64decode(item.pop('png').split(',', 1)[1]))
    save(folder / f'{slug}.json', data)
    return {'samples': len(data['samples']), 'frames': [f['key'] for f in data['frames']], 'maxGhosts': max((len(s['ghosts']) for s in data['samples']), default=0)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / '.omx/naruto-gates.js'
    report = {'scope': 'Controlled native RAF, stage0 no Gates; real artwork and combat.', 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'surfaces': {}, 'errors': []}
    scenes = [('whirlwind', 'naruto-lee', 1.2), ('front', 'naruto-lotus', 3.0), ('reverse', 'naruto-reverse-lotus', 3.0), ('pursuit', 'naruto-lee-pursuit', 1.2), ('drunken', 'naruto-lee-drunken', .65)]
    if os.environ.get('LEE_TRAIL_QUICK') == '1':
        scenes = scenes[:3]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        for label, width, height in [('desktop', 1280, 900), ('mobile390-low', 390, 844)]:
            folder = OUT / label
            folder.mkdir(parents=True, exist_ok=True)
            context = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=width < 500, has_touch=width < 500, service_workers='block', record_video_dir=str(folder / 'video'), record_video_size={'width': width, 'height': height})
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            frame = boot(page, label, folder)
            frame.evaluate("q=>G.Settings.set('quality',q)", 'low' if width < 500 else 'high')
            cases = {}
            for slug, skill, seconds in scenes:
                frame.evaluate(OBSERVER)
                spec = frame.evaluate(SCENE, {'id': skill, 'rank': 1})
                page.wait_for_timeout(seconds * 1000)
                frame.evaluate('JAcceptance.pause()')
                cases[slug] = {'spec': spec, **collect(frame, folder, slug)}
                print(label, slug, cases[slug]['frames'], flush=True)
            idle = frame.evaluate('''()=>{const A=JAcceptance,p=A.p();A.reset();p.moves=[];p.slots=[];A.resume();return true}''')
            page.wait_for_timeout(300)
            idle_ghosts = frame.evaluate('G.NarutoGates.afterimagesFor(G.Game.player).length')
            assert idle_ghosts == 0
            frame.evaluate('JAcceptance.pause()')
            page.screenshot(path=str(folder / 'idle-no-trail.png'))
            frame.evaluate("()=>{JAcceptance.reset();JAcceptance.fixture('naruto-gates');JAcceptance.resume()}")
            page.wait_for_timeout(600)
            opening_ghosts = frame.evaluate('G.NarutoGates.afterimagesFor(G.Game.player).length')
            assert opening_ghosts == 0
            frame.evaluate('JAcceptance.pause()')
            page.screenshot(path=str(folder / 'gates-opening-no-skill-trail.png'))
            video = page.video
            context.close()
            video.save_as(str(folder / 'native-lee-skill-trails.webm'))
            video.delete()
            report['surfaces'][label] = {'cases': cases, 'idleGhosts': idle_ghosts, 'openingGhosts': opening_ghosts}
            save(OUT / 'report.json', report)
        browser.close()
    report['endingSourceSha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    report['stableSource'] = report['sourceSha256'] == report['endingSourceSha256']
    save(OUT / 'report.json', report)


if __name__ == '__main__':
    main()
