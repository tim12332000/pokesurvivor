"""Native RAF phase evidence for the controlled Perfect Susanoo finisher."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_jujutsu as base
import test_madara_rework_play as native

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art-review/madara-final-slash-20261111/qa/visual'
URL = 'http://127.0.0.1:8347/.omx/digimon.html?lang=zh-TW'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


SCENE = r'''() => {
 const A=JAcceptance,M=G.NarutoMadara,p=A.p();A.reset();const m=A.fixture('naruto-madara-susanoo',5);
 p.hp=p.maxHp;p.xpNext=1e12;p.critChance=0;G.Spawner.update=()=>{};
 const targets=[[160,0],[700,-280],[700,280],[900,0]].map(v=>A.spawn(...v));
 for(const e of targets){e.spd=0;e.dmg=0;}
 A.resume();A.assert(M.canCast(p,m),'guardian cannot cast');M.stateFor(p).impetus=3;A.assert(M.cast(p,m),'perfect cast rejected');
 return {rank:m.lvl,spec:M.profile(p,m),guardianDuration:M.stateFor(p).guardian.duration,scope:'controlled actual perfect cast, native RAF'};
}'''

OBSERVE = r'''() => {
 const M=G.NarutoMadara,p=G.Game.player,R=window.FinalVisual={running:true,samples:[],frames:[],seen:new Set()};
 const canvas=[...document.querySelectorAll('canvas')].sort((a,b)=>b.width*b.height-a.width*a.height)[0];
 function sample(){if(!R.running)return;if(G.Game.state!=='playing'){requestAnimationFrame(sample);return;}
  const s=M.stateFor(p),g=s?.guardian,w=s?.pressures.find(f=>f.curved);
  const row={clock:s?.clock,time:G.Game.st.time,guardian:g?{age:g.age,index:g.index,phase:g.phase,finisher:!!g.finisher,charge:g.chargeProgress,progress:g.swing?.progress,aim:g.aim,remaining:g.duration-g.age}:null,wave:w?{distance:w.distance,radius:w.startRadius+w.distance,arcAngle:w.arcAngle,depth:w.depth,x:w.x,y:w.y,aim:w.aim}:null,hits:s?.hits};
  R.samples.push(row);const keys=[];
  if(g?.finisher&&g.phase==='draw'){if(g.chargeProgress>.12)keys.push('charge');if(g.chargeProgress>.85)keys.push('charged');}
  if(g?.finisher&&g.phase==='sweep')keys.push('sweep');
  if(g?.finisher&&g.phase==='recover')keys.push('recovery');
  if(w){if(w.distance>150)keys.push('wave-near');if(w.distance>650)keys.push('wave-far');if(w.distance>1000)keys.push('wave-late');}
  for(const key of keys)if(!R.seen.has(key)){R.seen.add(key);R.frames.push({key,state:row,png:canvas.toDataURL()});}
  requestAnimationFrame(sample);
 }requestAnimationFrame(sample);
}'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / '.omx/naruto-madara.js'
    report = {'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'scope': 'Controlled production renderer, actual perfect cast and native RAF. Phase images are samples, not full-video or audio review.', 'surfaces': {}, 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        for label, width, height in [('desktop', 1280, 900), ('mobile390-low', 390, 844)]:
            folder = OUT / label
            folder.mkdir(parents=True, exist_ok=True)
            context = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=width < 500, has_touch=width < 500, service_workers='block', record_video_dir=str(folder / 'video'), record_video_size={'width': width, 'height': height})
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL + ('&layout=wide' if width >= 500 else ''))
            frame = native.frame_for(page)
            frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
            if frame.locator('#tap-start').is_visible():
                frame.locator('#tap-start').click()
            frame.locator('[data-quick-naruto="30016"]').click()
            frame.wait_for_function('G.NarutoAssets.ready(30016)')
            frame.locator('#scr-menu [data-go="play"]').click()
            frame.wait_for_function('G.Game.player?.dex===30016&&G.Game.state==="playing"')
            page.screenshot(path=str(folder / 'normal-entry.png'))
            frame.evaluate(base.SETUP)
            frame.evaluate("v=>G.Settings.set('quality',v)", 'low' if width < 500 else 'high')
            frame.evaluate(OBSERVE)
            config = frame.evaluate(SCENE)
            page.wait_for_timeout(14000)
            frame.evaluate('JAcceptance.pause()')
            data = frame.evaluate('()=>{FinalVisual.running=false;return {samples:FinalVisual.samples,frames:FinalVisual.frames}}')
            for item in data['frames']:
                (folder / (item['key'] + '.png')).write_bytes(base64.b64decode(item.pop('png').split(',', 1)[1]))
            save(folder / 'phases.json', data)
            video = page.video
            context.close()
            video.save_as(str(folder / 'native-final-slash.webm'))
            video.delete()
            charge = [x for x in data['samples'] if x.get('guardian') and x['guardian'].get('finisher') and x['guardian']['phase'] == 'draw']
            sweep = [x for x in data['samples'] if x.get('guardian') and x['guardian'].get('finisher') and x['guardian']['phase'] == 'sweep']
            waves = [x for x in data['samples'] if x.get('wave')]
            timing = {'sampledChargeSeconds': charge[-1]['clock'] - charge[0]['clock'], 'firstChargeClock': charge[0]['clock'], 'firstSweepClock': sweep[0]['clock'], 'firstWaveClock': waves[0]['clock'], 'configuredCharge': config['spec']['finisherCharge']}
            report['surfaces'][label] = {'config': config, 'frames': [x['key'] for x in data['frames']], 'sampleCount': len(data['samples']), 'timing': timing}
            save(OUT / 'report.json', report)
            print(label, report['surfaces'][label]['frames'], flush=True)
        browser.close()
    report['endingSourceSha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    report['stableSource'] = report['sourceSha256'] == report['endingSourceSha256']
    save(OUT / 'report.json', report)


if __name__ == '__main__':
    main()
