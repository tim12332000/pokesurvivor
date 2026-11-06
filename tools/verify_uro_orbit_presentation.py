"""Uro orbit presentation from the production picker and game canvas.

Controlled durable targets and known hostile bullets; does not claim natural XP
play or verification on a physical phone.
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

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('URO_ORBIT_PRESENTATION_OUT',ROOT/'art-review/uro-orbit-20261106/visual'))

class Handler(SimpleHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*args): pass

SETUP=r'''()=>{
 const A=JAcceptance;A.reset();const p=A.p(),m=A.fixture('jjk-uro-screen');p.invuln=0;
 const source=A.spawn(320,0);window.OrbitPresentation={source};G.Spawner.update=()=>{};
 G.Projectiles.spawn({x:175,y:0,vx:-240,vy:0,r:7,life:4,dmg:7,mtype:'fire',color:'#ff8258',friendly:false,sourceEnemy:source});
 A.resume();try{A.assert(G.JjkUro.cast(p,m),'screen did not cast')}finally{A.pause()}
 G.Projectiles.clear();G.Projectiles.spawn({x:90,y:0,px:175,py:0,vx:-240,vy:0,r:7,life:4,dmg:7,mtype:'fire',color:'#ff8258',friendly:false,sourceEnemy:source});
 A.resume();try{G.JjkUro.intercept()}finally{A.pause()}
 return {fixture:'rank1, quantity0, known projectile swept into active screen, durable shooter 320px right',screenRadius:G.JjkUro.stateFor(p).screen.radius};
}'''
STATE=r'''()=>{
 const p=JAcceptance.p(),s=G.JjkUro.stateFor(p),shots=G.Projectiles.all();
 return {position:[p.x,p.y],intercepted:s?.intercepted,
  orbits:(G.JjkUro.orbits||[]).map(o=>({age:o.age,duration:o.duration,x:o.x,y:o.y,radius:o.radius,angle:o.angle})),
  returned:shots.filter(b=>b.uroReturned).map(b=>({x:b.x,y:b.y,vx:b.vx,vy:b.vy})),
  shooterHp:window.OrbitPresentation.source.hp,
  draws:G.JujutsuVFX.inspect().draws?.filter(d=>/orbit|return/.test(d.kind))};
}'''

def phase_shots(page,frame,label,quality):
    frame.evaluate('q=>G.JujutsuVFX.setQuality(q)',quality)
    config=frame.evaluate(SETUP)
    states=[];previous=0
    for at,phase in [(0,'capture'),(.2,'quarter'),(.4,'half'),(.6,'three-quarter'),(.79,'near-full'),(.85,'return'),(1.7,'hit')]:
        frame.evaluate('dt=>JAcceptance.advance(dt)',at-previous);previous=at
        page.wait_for_timeout(50)
        path=OUT/f'{label}-{quality}-{phase}.png';page.screenshot(path=str(path))
        states.append({'phase':phase,'at':at,'screenshot':str(path.relative_to(ROOT)),**frame.evaluate(STATE)})
    assert all(len(s['orbits'])==1 and not s['returned'] for s in states[:5]),'orbit escaped before completing a full lap'
    assert not states[5]['orbits'] and states[5]['returned'],'full lap did not release the native returned projectile'
    assert states[3]['orbits'][0]['angle']>4.7 and states[4]['orbits'][0]['angle']>6.2,'quarter samples did not span a complete lap'
    return {'config':config,'states':states}


def native_clip(page,frame,context,label,mobile):
    frame.evaluate("G.JujutsuVFX.setQuality('auto')")
    config=frame.evaluate(SETUP)
    frame.evaluate(r'''()=>{
      const stream=document.getElementById('game').captureStream(30),chunks=[];
      const recorder=new MediaRecorder(stream,{mimeType:'video/webm',videoBitsPerSecond:2200000});
      recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
      const done=new Promise(resolve=>recorder.onstop=()=>{const reader=new FileReader;reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}))});
      window.OrbitClip={stream,recorder,done};G.Game.debugSpeed(1);recorder.start();JAcceptance.resume();
    }''')
    before=frame.evaluate(STATE)
    if mobile:
        client=context.new_cdp_session(page);point=frame.evaluate('G.Touch.stickBase()')
        if frame!=page.main_frame:
            box=page.locator('iframe').first.bounding_box();point={'x':point['x']+box['x'],'y':point['y']+box['y']}
        client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]})
        client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':point['x']+42,'y':point['y']}]})
        page.wait_for_timeout(200)
        client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
    else:
        if frame!=page.main_frame:page.locator('iframe').first.focus()
        page.keyboard.down('KeyD');page.wait_for_timeout(200);page.keyboard.up('KeyD')
    after=frame.evaluate(STATE)
    assert after['position'][0]>before['position'][0]+1,'native movement did not move during orbit'
    page.screenshot(path=str(OUT/f'{label}-moving-orbit.png'))
    page.wait_for_timeout(1600)
    final=frame.evaluate(STATE)
    data=frame.evaluate(r'''async()=>{JAcceptance.pause();const c=OrbitClip;c.recorder.stop();const data=await c.done;for(const t of c.stream.getTracks())t.stop();return data}''')
    path=OUT/f'{label}-native-moving-orbit.webm';path.write_bytes(base64.b64decode(data.split(';base64,',1)[1]))
    return {'config':config,'method':'unstitched canvas capture at native RAF with actual keyboard/touch movement','before':before,'after':after,'final':final,'video':str(path.relative_to(ROOT))}


def main():
    OUT.mkdir(parents=True,exist_ok=True);base.OUT=OUT
    server=None
    if not os.environ.get('JUJUTSU_URL'):
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start()
        base.URL=f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW&test=jujutsu'
    else:base.URL=os.environ['JUJUTSU_URL']
    source_names=['.omx/jjk-uro.js','.omx/jujutsu-vfx.js']
    hashes=lambda:{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_names}
    report={'sourceHashes':hashes(),'url':base.URL,'viewports':{},'errors':[],'failedRequests':[],'failures':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        for label,width,mobile in [('desktop',1280,False),('mobile360',360,True),('mobile390',390,True)]:
            context=browser.new_context(viewport={'width':width,'height':844 if mobile else 900},is_mobile=mobile,has_touch=mobile,service_workers='block');page=context.new_page()
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.on('response',lambda r:report['failedRequests'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            try:
                print(label,'boot',flush=True);frame=base.boot(page,30015,label)
                report['viewports'][label]={'auto':phase_shots(page,frame,label,'auto'),'low':phase_shots(page,frame,label,'low'),'native':native_clip(page,frame,context,label,mobile)}
            except Exception as e:
                report['failures'].append(label+': '+str(e));page.screenshot(path=str(OUT/f'{label}-failure.png'))
            finally:
                context.close();(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
        browser.close()
    if server:server.shutdown()
    report['sourceHashesAfter']=hashes()
    if report['sourceHashes']!=report['sourceHashesAfter']:report['failures'].append('runtime source changed during capture')
    report['ok']=not(report['errors'] or report['failedRequests'] or report['failures'])
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'errors':report['errors'],'output':str(OUT)},ensure_ascii=False))
    if not report['ok']:raise SystemExit(1)

if __name__=='__main__':main()
