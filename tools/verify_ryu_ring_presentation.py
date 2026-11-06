"""Controlled ring presentation through the normal game entry; native RAF clips."""
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
OUT=ROOT/'art-review/ryu-ring-20261106/qa/presentation'

class LabServer(ThreadingHTTPServer):
    request_queue_size=128
    def handle_error(self,request,client_address): pass  # Normal desktop redirect may abort obsolete asset requests.

class Handler(SimpleHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*args): pass

SETUP=r"""({rank,q})=>{
 const A=JAcceptance;A.reset();const m=A.fixture('jjk-ryu-ring',rank),p=A.p();
 p.quantityPicks=p.quantityBonus=q;p.invuln=999;
 const h=G.JjkRyu.ringProfile(p,m);
 for(const angle of [0,Math.PI/2,Math.PI,Math.PI*1.5])A.spawn(Math.cos(angle)*h.radius,Math.sin(angle)*h.radius);
 return {rank,q,profile:h};
}"""
STATE=r"""()=>{
 const p=JAcceptance.p(),s=G.JjkRyu.stateFor(p),m=p.moves[0];
 return {position:[p.x,p.y],action:s.action?{mode:s.action.mode,age:s.action.age,released:s.action.released}:null,
 rings:s.rings.map(r=>({age:r.age,lapIndex:r.lapIndex,count:r.count,segments:r.segments.length})),
 status:G.JjkRyu.statusFor(p,m),hud:G.RunInsights.skillState(p,m)};
}"""


def legal_cards(frame):
    return frame.evaluate(r"""()=>{
      const A=JAcceptance,p=A.p();A.reset();p.moves=[];p.slots=[];p.level=1;p.statsTaken={};
      p.quantityPicks=p.quantityBonus=0;p.addMove('jjk-ryu');p.arrange();const picks=[];
      for(let level=2;level<=5;level++){
        p.level=level;const offers=G.LevelUp.offer(p,100),key=level===3?'new:jjk-ryu-spread':level===5?'new:jjk-ryu-ring':'stat:atk';
        const card=offers.find(c=>c.key===key);A.assert(card,'missing legal choice '+key);
        A.assert(card.apply(p)!==false,'legal card apply failed '+key);card.onShown?.(p);picks.push({level,key,title:card.title,description:card.desc});
      }
      A.assert(p.hasMove('jjk-ryu-ring'),'legal path failed to learn ring');
      return {method:'Lv1 blank run; staged character levels 2–5 with one genuine LevelUp card per level. This is legal card-contract evidence, not natural XP play.',picks};
    }""")


def selection_bounds(frame):
    return frame.evaluate(r"""()=>{
      const kit=document.querySelector('.launch-kit'),cells=[...kit.children];
      const rect=e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);return {text:e.textContent,x:r.x,y:r.y,width:r.width,height:r.height,visible:c.visibility!=='hidden'&&c.display!=='none'&&r.width>0&&r.height>0,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth}};
      const out={viewport:innerWidth,kit:rect(kit),cells:cells.map(rect),overflow:document.documentElement.scrollWidth>innerWidth};
      if(cells.length!==5||out.overflow||out.cells.some(c=>!c.visible||c.x<0||c.x+c.width>innerWidth+1||c.scrollWidth>c.clientWidth+1))throw Error('ring learning row invisible or clipped '+JSON.stringify(out));
      return out;
    }""")


def screenshots(page,frame,label):
    result={}
    for rank,q in [(1,0),(1,1),(5,4)]:
        key=f'{label}-rank{rank}-q{q}'
        config=frame.evaluate(SETUP,{'rank':rank,'q':q})
        frame.evaluate('()=>{const A=JAcceptance;A.resume();try{G.JjkRyu.cast(A.p(),A.p().moves[0])}finally{A.pause()}}')
        h=config['profile'];end=h['charge']+h['duration']
        stages=[(.16,'windup'),(.4,'growing'),(.57,'full'),(end-.09,'late'),(end+.24,'recovered')]
        previous=0;states=[]
        for at,phase in stages:
            frame.evaluate('dt=>JAcceptance.advance(dt)',at-previous);previous=at
            page.wait_for_timeout(60)
            path=OUT/f'{key}-{phase}.png';page.screenshot(path=str(path))
            states.append({'phase':phase,'at':at,'screenshot':str(path.relative_to(ROOT)),**frame.evaluate(STATE)})
        result[key]={'fixture':'controlled static durable enemies at four ring quadrants; production cast/update/draw','config':config,'stages':states}
    return result


def native_clip(page,frame,context,label,mobile):
    config=frame.evaluate(SETUP,{'rank':5,'q':4})
    frame.evaluate(r"""()=>{
      const A=JAcceptance;G.Game.debugSpeed(1);
      const stream=document.getElementById('game').captureStream(30),chunks=[];
      const recorder=new MediaRecorder(stream,{mimeType:'video/webm',videoBitsPerSecond:2200000});
      recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
      const done=new Promise(resolve=>recorder.onstop=()=>{const reader=new FileReader;reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}))});
      window.RingClip={stream,recorder,done};recorder.start();A.resume();G.JjkRyu.cast(A.p(),A.p().moves[0]);
    }""")
    page.wait_for_timeout(650)
    before=frame.evaluate(STATE)
    assert before['rings'],'ring not active during native input'
    if mobile:
        client=context.new_cdp_session(page);point=frame.evaluate('G.Touch.stickBase()')
        if frame!=page.main_frame:
            box=page.locator('iframe').first.bounding_box();point={'x':point['x']+box['x'],'y':point['y']+box['y']}
        client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]})
        client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':point['x']+42,'y':point['y']}]})
        page.wait_for_timeout(180)
        client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
    else:
        if frame!=page.main_frame: page.locator('iframe').first.focus()
        page.keyboard.down('KeyD');page.wait_for_timeout(180);page.keyboard.up('KeyD')
    after=frame.evaluate(STATE)
    assert after['position'][0]>before['position'][0]+1,'native keyboard/touch failed to move while ring active'
    page.screenshot(path=str(OUT/f'{label}-native-input-active.png'))
    page.wait_for_timeout(3400)
    final=frame.evaluate(STATE)
    assert not final['rings'],'native full ring cycle failed to end'
    data=frame.evaluate(r"""async()=>{JAcceptance.pause();const c=window.RingClip;c.recorder.stop();const result=await c.done;for(const track of c.stream.getTracks())track.stop();return result;}""")
    path=OUT/f'{label}-rank5-q4-native-ring.webm';path.write_bytes(base64.b64decode(data.split(';base64,',1)[1]))
    return {'method':'production RAF canvas.captureStream(30), unstitched complete cycle, actual dispatched keyboard/touch input; controlled rank5 quantity4 durable enemies','config':config,'before':before,'after':after,'final':final,'video':str(path.relative_to(ROOT))}


def main():
    OUT.mkdir(parents=True,exist_ok=True);base.OUT=OUT
    server=None
    if not os.environ.get('JUJUTSU_URL'):
        server=LabServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start()
        base.URL=f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW&test=jujutsu'
    else:base.URL=os.environ['JUJUTSU_URL']
    source_names=['.omx/jjk-ryu.js','.omx/jujutsu-vfx.js','.omx/jujutsu.js','.omx/jujutsu-growth.js','.omx/naruto.js','.omx/naruto-skills-en.js','.omx/run-insights.js']
    hashes=lambda:{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_names}
    report={'sourceHashes':hashes(),'url':base.URL,'fixture':'controlled presentation; no claim of natural XP growth or physical-device verification','viewports':{},'errors':[],'failedRequests':[],'failures':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        for label,width,mobile in [('desktop1280',1280,False),('mobile360',360,True),('mobile390',390,True)]:
            context=browser.new_context(viewport={'width':width,'height':900 if not mobile else 844},is_mobile=mobile,has_touch=mobile,service_workers='block');page=context.new_page()
            page.on('pageerror',lambda e:report['errors'].append(e.stack or str(e)))
            page.on('response',lambda r:report['failedRequests'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            try:
                print(label,'boot',flush=True)
                frame=base.boot(page,30014,label)
                # Native picker is exercised by boot; inspect its visible row before the run.
                frame.evaluate('G.Game.quit();G.MenuUI.open()');page.wait_for_timeout(100)
                row=selection_bounds(frame);page.screenshot(path=str(OUT/f'{label}-five-skills.png'))
                frame.locator('#scr-menu [data-go="play"]').click();frame.wait_for_function('G.Game.state==="playing"');frame.evaluate(base.SETUP)
                cards=legal_cards(frame)
                report['viewports'][label]={'selection':row,'legalCards':cards,'screenshots':screenshots(page,frame,label),'native':native_clip(page,frame,context,label,mobile)}
            except Exception as e:
                report['failures'].append(label+': '+str(e));page.screenshot(path=str(OUT/f'{label}-failure.png'))
            finally:
                context.close();(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
        browser.close()
    if server:server.shutdown()
    report['sourceHashesAfter']=hashes()
    if report['sourceHashes']!=report['sourceHashesAfter']:report['failures'].append('Runtime changed during presentation; rerun final evidence')
    report['ok']=not(report['errors'] or report['failedRequests'] or report['failures'])
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'errors':report['errors'],'output':str(OUT)},ensure_ascii=False))
    if not report['ok']:raise SystemExit(1)

if __name__=='__main__':main()
