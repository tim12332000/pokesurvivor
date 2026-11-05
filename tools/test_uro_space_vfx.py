"""Normal-entry spatial folds: no range diagrams, tethers or arrow guides."""
import base64,json,os
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT=Path(__file__).resolve().parents[1]
STAGE=os.environ.get('URO_SPACE_STAGE','after')
OUT=ROOT/'.omx/state/uro-space-vfx'/STAGE
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 OUT.mkdir(parents=True,exist_ok=True);base.OUT=OUT
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)))
 Thread(target=server.serve_forever,daemon=True).start();base.URL=f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW'
 report={}
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
   for mobile in [False,True]:
    label='mobile' if mobile else 'desktop';context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));f=base.boot(page,30015,label)
    f.evaluate("""()=>{const A=JAcceptance;A.reset();A.fixture('jjk-uro-thin-ice',3);A.p().invuln=0;for(const [x,y]of [[130,0],[200,60],[230,-70]])A.spawn(x,y);A.cast('jjk-uro-thin-ice');A.advance(.2)}""")
    phases={}
    for phase,dt in [('pull',0),('contact',.16),('later',.65),('finish',.55)]:
     if dt:f.evaluate('dt=>JAcceptance.advance(dt)',dt)
     page.wait_for_timeout(80);page.screenshot(path=str(OUT/f'{label}-{phase}.png'));phases[phase]=f.evaluate('G.JujutsuVFX.inspect()')
    frozen=f.evaluate('G.JujutsuVFX.inspect().capturesTotal');page.wait_for_timeout(120);assert frozen==f.evaluate('G.JujutsuVFX.inspect().capturesTotal'),'pause recapture'
    f.evaluate("""()=>{const A=JAcceptance;A.reset();A.fixture('jjk-uro-screen',3);const p=A.p();A.spawn(250,0);G.Projectiles.spawn({x:170,y:0,vx:-240,vy:0,r:6,life:3,dmg:7,friendly:false});A.cast('jjk-uro-screen');G.Projectiles.clear();G.Projectiles.spawn({x:70,y:0,px:170,py:0,vx:-240,vy:0,r:6,life:3,dmg:7,friendly:false});A.resume();try{G.JjkUro.intercept()}finally{A.pause()};A.advance(.10)}""")
    page.wait_for_timeout(80);page.screenshot(path=str(OUT/f'{label}-reflection.png'));reflection=f.evaluate('G.JujutsuVFX.inspect()')
    if STAGE!='before':
     assert not any(d['kind']=='counter-fold-link' for d in reflection['draws']),'counter tether remains'
     assert any(d['kind']=='spatial-refraction' for d in reflection['draws']),'reflection fold missing'
    f.evaluate("G.JujutsuVFX.setQuality('low')");page.wait_for_timeout(80);page.screenshot(path=str(OUT/f'{label}-low.png'));low=f.evaluate('G.JujutsuVFX.inspect()');assert low['triangles']<=12 and low['shards']<=24
    f.evaluate("""()=>{const A=JAcceptance;A.reset();A.fixture('jjk-uro-thin-ice',3);const p=A.p();p.invuln=0;G.Spawner.update=()=>{};for(let i=0;i<8;i++)A.spawn(150+i*15,(i-4)*32);p.moves[0].t=0;A.resume()}""")
    clip=f.evaluate("""async()=>{const stream=document.getElementById('game').captureStream(24),rec=new MediaRecorder(stream,{mimeType:'video/webm',videoBitsPerSecond:2000000}),chunks=[];rec.ondataavailable=e=>chunks.push(e.data);const done=new Promise(resolve=>rec.onstop=()=>{const reader=new FileReader;reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}))});rec.start();await new Promise(r=>setTimeout(r,3300));JAcceptance.pause();rec.stop();const data=await done;stream.getTracks().forEach(t=>t.stop());return data}""")
    (OUT/f'{label}-native-space.webm').write_bytes(base64.b64decode(clip.split(',',1)[1]))
    f.evaluate('G.Combat.clearFields();G.JujutsuVFX.clear()');page.wait_for_timeout(80);clear=f.evaluate('G.JujutsuVFX.inspect()');assert clear['snapshots']==0 and not clear['folds']
    assert not errors,errors;report[label]={'phases':phases,'reflection':reflection,'low':low,'cleared':True,'nativeClipSeconds':3.3,'errors':errors};context.close()
   browser.close()
  report['ok']=True;(OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'ok':True,'evidence':str(OUT)}))
 finally:server.shutdown();server.server_close()

if __name__=='__main__':main()
