"""Normal-entry airborne scatter phases, native input and complete RAF clips.

Builds spend genuine card callbacks at staged levels. This is controlled
presentation evidence, not natural-XP progression or physical-phone testing.
"""
from __future__ import annotations

import base64
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import os
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('RYU_SKY_PRESENTATION_OUT', ROOT / 'art-review/ryu-sky-scatter-20261106/qa/presentation'))


class Server(ThreadingHTTPServer):
    request_queue_size = 128


class Handler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_args):
        pass

    def do_GET(self):
        try:
            super().do_GET()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass


BUILD = r"""({rank,q})=>{
 const A=JAcceptance,p=A.p(),id='jjk-ryu-spread';A.reset();p.moves=[];p.slots=[];p.level=1;p.statsTaken={};
 p.quantityPicks=p.quantityBonus=0;A.assert(p.addMove('jjk-ryu'),'normal starter absent');p.arrange();
 const keys=rank===1?['stat:atk','new:'+id]:['stat:atk','new:'+id,'up:'+id,'new:jjk-ryu-ring','up:'+id,'up:'+id,'up:'+id,...Array(q).fill('stat:quantity')];
 const picks=[];
 for(let i=0;i<keys.length;i++){
  p.level=i+2;const card=G.LevelUp.offer(p,1000).find(c=>c.key===keys[i]);
  A.assert(card&&card.apply(p)!==false,'missing legal build choice '+p.level+'/'+keys[i]);card.onShown?.(p);
  picks.push({level:p.level,key:keys[i],title:card.title,description:card.desc});
 }
 const m=p.moves.find(m=>m.id===id);A.assert(m.lvl===rank&&p.quantityPicks===q,'legal build rank/quantity differs');
 p.invuln=999;for(const move of p.moves)move.t=999;m.t=0;
 const targets=[[210,-95],[230,100],[-190,70],[80,210],[650,-160]].map(v=>A.spawn(...v));
 window.SkyVisualTargets=targets;
 return {rank,q,level:p.level,profile:G.JjkRyu.scatterFor(p,m),picks,
  method:'Normal Lv1 starter; staged character levels with exactly one real native card choice at each level. Ring is learned as a legal quantity consumer in the high-cost build and held inactive. No natural XP claim.'};
}"""

CAST = r"""()=>{
 const A=JAcceptance,p=A.p(),m=p.moves.find(m=>m.id==='jjk-ryu-spread');
 A.resume();try{A.assert(G.JjkRyu.cast(p,m),'production sky cast failed')}finally{A.pause()}
 // Prevent another automatic volley after the cooldown while recording this
 // single complete cycle; already flying bolts retain their native identity.
 for(const move of p.moves)move.t=999;
}"""

STATE = r"""()=>{
 const p=JAcceptance.p(),s=G.JjkRyu.stateFor(p),m=p.moves.find(m=>m.id==='jjk-ryu-spread');
 return {position:[p.x,p.y],action:s?.action?{age:s.action.age,phase:s.action.phase,released:s.action.released}:null,
  shots:(s?.scatter||[]).map(e=>({x:e.x,y:e.y,lift:e.lift,phase:e.phase,age:e.age,aim:e.aim,visualAngle:e.visualAngle,
   target:e.target?.id??null,trail:e.trail.length,distance:e.distance,orbitDuration:e.orbitDuration})),
  impacts:(s?.effects||[]).filter(e=>e.kind==='impact'&&e.scatter).map(e=>({age:e.age,life:e.life,x:e.x,y:e.y})),
  hits:s?.hits||0,damage:SkyVisualTargets.map(e=>e.maxHp-e.hp),hud:G.RunInsights.skillState(p,m),
  overflow:document.documentElement.scrollWidth>innerWidth};
}"""


def selection_bounds(frame):
    return frame.evaluate(r"""()=>{
      const cells=[...document.querySelectorAll('.launch-kit>span')];
      const result={count:cells.length,overflow:document.documentElement.scrollWidth>innerWidth,
       cells:cells.map(e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);return {text:e.textContent,x:r.x,width:r.width,
        visible:c.display!=='none'&&c.visibility!=='hidden'&&r.width>0&&r.height>0,overflow:e.scrollWidth>e.clientWidth+1}})};
      JAcceptance.assert(result.count===5&&!result.overflow&&result.cells.every(e=>e.visible&&!e.overflow&&e.x>=0&&e.x+e.width<=innerWidth+1),'selection skill row clipped');
      return result;
    }""")


def screenshots(page, frame, label):
    result = {}
    for rank, q in [(1, 0), (5, 4)]:
        key = f'{label}-rank{rank}-q{q}'
        config = frame.evaluate(BUILD, {'rank': rank, 'q': q})
        frame.evaluate(CAST)
        stages = []
        previous = 0
        def capture(tag, at):
            state = frame.evaluate(STATE)
            phases = sorted({shot['phase'] for shot in state['shots']})
            actual = 'impact' if state['impacts'] else '+'.join(phases) if phases else 'windup' if state['action'] else 'recovered'
            path = OUT / f'{key}-{tag}.png'
            page.screenshot(path=str(path))
            assert not state['overflow'], state
            stages.append({'phase': actual, 'capture': tag, 'at': at, 'screenshot': str(path.relative_to(ROOT)), **state})

        for at, phase in [(.16, 'charge'), (.47, 'rise'), (.85, 'orbit'), (1.38, 'depart')]:
            frame.evaluate('dt=>JAcceptance.advance(dt)', at - previous)
            previous = at
            page.wait_for_timeout(55)
            capture(phase, at)
        # Record a genuine contact window. A fixed late timestamp can already
        # be empty and must not be presented as an impact frame.
        while previous < 3.6 and not frame.evaluate('()=>G.JjkRyu.stateFor(JAcceptance.p())?.effects.some(e=>e.kind==="impact"&&e.scatter&&e.age<.07)'):
            frame.evaluate('JAcceptance.advance(.01)')
            previous += .01
        assert frame.evaluate('()=>G.JjkRyu.stateFor(JAcceptance.p())?.effects.some(e=>e.kind==="impact"&&e.scatter&&e.age<.07)'), 'no actual scatter contact effect captured'
        page.wait_for_timeout(55)
        capture('first-impact', round(previous, 3))
        for at, phase in [(max(2.10, previous + .12), 'seek'), (max(3.40, previous + .24), 'late'), (6.40, 'recovered')]:
            frame.evaluate('dt=>JAcceptance.advance(dt)', at - previous)
            previous = at
            page.wait_for_timeout(55)
            capture(phase, at)
        assert not stages[-1]['shots'] and not stages[-1]['action'], 'full controlled sky cycle did not recover'
        assert any(value > 0 for value in stages[-1]['damage']), 'controlled sky volley produced no actual damage'
        result[key] = {'config': config, 'stages': stages}
    return result


def native_clip(page, frame, context, label, mobile, rank, q):
    config = frame.evaluate(BUILD, {'rank': rank, 'q': q})
    frame.evaluate(r"""()=>{
      const A=JAcceptance;G.Game.debugSpeed(1);const stream=document.getElementById('game').captureStream(30),chunks=[];
      const recorder=new MediaRecorder(stream,{mimeType:'video/webm',videoBitsPerSecond:2200000});
      recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
      const done=new Promise(resolve=>recorder.onstop=()=>{const reader=new FileReader;reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}))});
      window.SkyNativeClip={stream,recorder,done};recorder.start();
    }""")
    frame.evaluate(CAST)
    frame.evaluate('JAcceptance.resume()')
    page.wait_for_timeout(940)
    before = frame.evaluate(STATE)
    assert before['shots'], 'no actual airborne projectiles during native input'
    if mobile:
        client = context.new_cdp_session(page)
        point = frame.evaluate('G.Touch.stickBase()')
        if frame != page.main_frame:
            box = page.locator('iframe').first.bounding_box()
            point = {'x': point['x'] + box['x'], 'y': point['y'] + box['y']}
        client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [point]})
        client.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': point['x'] + 42, 'y': point['y']}]})
        page.wait_for_timeout(180)
        client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    else:
        if frame != page.main_frame:
            page.locator('iframe').first.focus()
        page.keyboard.down('KeyD')
        page.wait_for_timeout(180)
        page.keyboard.up('KeyD')
    after = frame.evaluate(STATE)
    assert after['position'][0] > before['position'][0] + 1, 'native keyboard/touch failed to move while volley was airborne'
    page.screenshot(path=str(OUT / f'{label}-rank{rank}-q{q}-native-input.png'))
    page.wait_for_timeout(5400)
    final = frame.evaluate(STATE)
    assert not final['shots'] and not final['action'], 'native full sky cycle did not end'
    data = frame.evaluate(r"""async()=>{
      JAcceptance.pause();const c=window.SkyNativeClip;c.recorder.stop();const data=await c.done;for(const t of c.stream.getTracks())t.stop();return data;
    }""")
    path = OUT / f'{label}-rank{rank}-q{q}-native-sky.webm'
    path.write_bytes(base64.b64decode(data.split(';base64,', 1)[1]))
    return {'method': 'Unstitched production RAF canvas recording, complete single volley, real dispatched keyboard/touch input; controlled enemies/staged native cards',
            'config': config, 'before': before, 'after': after, 'final': final, 'video': str(path.relative_to(ROOT))}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base.OUT = OUT
    base.URL = os.environ.get('RYU_SKY_URL') or os.environ.get('JUJUTSU_URL')
    server = None
    if not base.URL:
        server = Server(('127.0.0.1', 0), partial(Handler, directory=str(ROOT)))
        Thread(target=server.serve_forever, daemon=True).start()
        base.URL = f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW'
    names = ['.omx/jjk-ryu.js', '.omx/jujutsu-vfx.js', '.omx/jujutsu.js', '.omx/jujutsu-growth.js', '.omx/naruto.js', '.omx/naruto-skills-en.js', '.omx/run-insights.js']
    hashes = lambda: {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}
    report = {'url': base.URL, 'sourceHashes': hashes(), 'views': {}, 'errors': [], 'failedRequests': [], 'failures': [],
              'fixture': 'Controlled native-card builds, not natural XP progression or physical-device testing'}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            for label, width, mobile in [('desktop1280', 1280, False), ('mobile360', 360, True), ('mobile390', 390, True)]:
                context = browser.new_context(viewport={'width': width, 'height': 900 if not mobile else 844}, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('response', lambda r: report['failedRequests'].append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
                try:
                    print(label, 'boot', flush=True)
                    frame = base.boot(page, 30014, label)
                    frame.evaluate('G.Game.quit();G.MenuUI.open()')
                    page.wait_for_timeout(80)
                    row = selection_bounds(frame)
                    page.screenshot(path=str(OUT / f'{label}-selection.png'))
                    frame.locator('#scr-menu [data-go="play"]').click()
                    frame.wait_for_function('G.Game.state==="playing"')
                    frame.evaluate(base.SETUP)
                    phases = screenshots(page, frame, label)
                    native = {f'rank{rank}q{q}': native_clip(page, frame, context, label, mobile, rank, q) for rank, q in [(1, 0), (5, 4)]}
                    report['views'][label] = {'selection': row, 'screenshots': phases, 'native': native}
                except Exception as error:
                    report['failures'].append(label + ': ' + str(error))
                    page.screenshot(path=str(OUT / f'{label}-failure.png'))
                finally:
                    context.close()
                    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
            browser.close()
    finally:
        if server:
            server.shutdown()
            server.server_close()
    report['sourceHashesAfter'] = hashes()
    if report['sourceHashesAfter'] != report['sourceHashes']:
        report['failures'].append('Runtime changed during presentation; rerun frozen evidence')
    report['ok'] = not (report['errors'] or report['failedRequests'] or report['failures'])
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'ok': report['ok'], 'failures': report['failures'], 'errors': report['errors'], 'output': str(OUT)}, ensure_ascii=False))
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
