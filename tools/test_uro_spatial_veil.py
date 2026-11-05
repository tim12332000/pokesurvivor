"""Uro optical covering: all registered frames, opaque fallback and scene sampling."""
import base64,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('URO_VEIL_OUT',ROOT/'.omx/state/uro-space-body/after'))
CHECK=r"""() => {
 const art=G.JujutsuArt,A=JAcceptance,assert=A.assert,p=A.p(),out={};
 const keys=['uro-common','uro-skills'];
 function draw(frame,left,bg,scene,alpha=1,flash=false){
  const c=document.createElement('canvas');c.width=300;c.height=260;const ctx=c.getContext('2d');
  ctx.fillStyle=bg;ctx.fillRect(0,0,c.width,c.height);
  ctx.fillStyle=bg==='#325923'?'#8eae4c':'#baa28b';
  for(let x=0;x<300;x+=16)ctx.fillRect(x,0,6,260);
  if(scene)art.captureUroBackground(ctx);
  art.draw(ctx,p,{state:'idle',height:120,x:150,y:235,pose:null,alpha,flash});
  return c;
 }
 // Exercise each exact native frame using public sample's registered semantic.
 const atlas=document.createElement('canvas');atlas.width=1440;atlas.height=Math.ceil(keys.reduce((n,k)=>n+art.metadata.sheets[k].frames.length*2,0)/6)*150;
 const ac=atlas.getContext('2d');ac.fillStyle='#345c30';ac.fillRect(0,0,atlas.width,atlas.height);let index=0,coverage=[];
 for(const key of keys)for(const [fi,frame]of art.metadata.sheets[key].frames.entries()){
  const semantic=Object.entries(art.metadata.animations.uro).find(([s,a])=>a.sheet===key&&a.frames.includes(fi));
  for(const left of [false,true]){
   const x=(index%6)*240+120,y=Math.floor(index/6)*150+143;
   ac.save();ac.translate(x,y);art.captureUroBackground(ac);
   assert(art.drawFrame(ac,key,fi,{x:0,y:0,height:80,direction:left?'left':'right'}),'frame missing');ac.restore();
   coverage.push({sheet:key,name:frame.name,mirror:left,registered:!!semantic});index++;
  }
 }
 // A scene of a different colour must change the covered torso, not retain
 // a fixed cyan garment; the head/limbs remain authored sprite pixels.
 const first=draw(null,false,'#325923',true),second=draw(null,false,'#725342',true),fallback=draw(null,false,'#325923',false);
 const a=first.getContext('2d').getImageData(0,0,300,260).data,b=second.getContext('2d').getImageData(0,0,300,260).data;
 let changed=0;for(let y=155;y<205;y++)for(let x=130;x<170;x++){const i=(y*300+x)*4;if(a[i]!==b[i]||a[i+1]!==b[i+1])changed++;assert(a[i+3]===255&&b[i+3]===255,'cover became transparent');}
 assert(changed>500,'cover does not follow background');
 const alphaSamples=[];
 for(const [alpha,flash]of [[.45,false],[.45,true],[1,true]]){
  const c=draw(null,false,'#725342',true,alpha,flash),pixel=[...c.getContext('2d').getImageData(150,170,1,1).data];
  assert(pixel[3]===255&&pixel[0]>pixel[2],'old cyan cloth leaked through flash/clone alpha '+pixel);
  alphaSamples.push({alpha,flash,pixel});
 }
 out.alphaSamples=alphaSamples;
 out.coverage=coverage;out.sceneChangedPixels=changed;out.inspect=art.spatialVeil.inspect();
 assert(out.inspect.bytes<=1024*1024*4,'snapshot exceeds cap');
 out.images={atlas:atlas.toDataURL(),grass:first.toDataURL(),earth:second.toDataURL(),fallback:fallback.toDataURL()};return out;
}"""

def native_clip(page,frame,context,mobile,label):
 frame.evaluate("""()=>{const A=JAcceptance,p=A.p();A.reset();A.fixture('jjk-uro',3);p.level=30;p.invuln=0;
  for(const id of ['jjk-uro-thin-ice','jjk-uro-screen','jjk-uro-collapse','jjk-uro-echo'])p.addMove(id);
  for(const m of p.moves){Object.assign(m,G.Moves.instance(m.id,3));m.t=0}
  for(const [x,y]of [[130,0],[200,100],[-130,30]])A.spawn(x,y);
  G.SelfClones.summon(p);G.Spawner.update=()=>{};G.Game.debugSpeed(1);
  const stream=document.getElementById('game').captureStream(24),rec=new MediaRecorder(stream),chunks=[];
  rec.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
  window.VeilClip={rec,stream,done:new Promise(resolve=>rec.onstop=()=>{const reader=new FileReader;reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}))})};
  rec.start();A.resume();}""")
 page.wait_for_timeout(400)
 if mobile:
  session=context.new_cdp_session(page);stick=frame.evaluate('G.Touch.stickBase()');offset={'x':0,'y':0}
  if frame!=page.main_frame:
   box=page.locator('iframe').first.bounding_box();offset={'x':box['x'],'y':box['y']}
  x,y=stick['x']+offset['x'],stick['y']+offset['y']
  session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
  for dx,dy in [(40,0),(-40,0),(0,-40)]:
   session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+dx,'y':y+dy}]});page.wait_for_timeout(700)
  session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 else:
  for key in ['d','a','w']:
   page.keyboard.down(key);page.wait_for_timeout(700);page.keyboard.up(key)
 page.wait_for_timeout(900)
 data=frame.evaluate("""async()=>{JAcceptance.pause();VeilClip.rec.stop();const data=await VeilClip.done;for(const t of VeilClip.stream.getTracks())t.stop();return {data,cloneCount:G.SelfClones.actors().length,inspect:G.JujutsuArt.spatialVeil.inspect()}}""")
 (OUT/f'{label}-native-spatial-movement-clone.webm').write_bytes(base64.b64decode(data.pop('data').split(',',1)[1]));page.screenshot(path=str(OUT/f'{label}-native-movement-end.png'));return data

def main():
 OUT.mkdir(parents=True,exist_ok=True);base.OUT=OUT;base.URL=os.environ.get('JUJUTSU_URL','http://127.0.0.1:8368/.omx/digimon.html?lang=zh-TW')
 report={}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
  for label,mobile in [('desktop',False),('mobile',True)]:
   context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   frame=base.boot(page,30015,label);data=frame.evaluate(CHECK)
   for name,png in data.pop('images').items():(OUT/f'{label}-{name}.png').write_bytes(base64.b64decode(png.split(',',1)[1]))
   assert data['inspect']['bytes']<=(512 if mobile else 1024)**2*4
   before=frame.evaluate('G.JujutsuArt.spatialVeil.inspect().captures');page.wait_for_timeout(150);after=frame.evaluate('G.JujutsuArt.spatialVeil.inspect().captures');assert after<=before+1,'paused optical background recaptured continuously'
   page.screenshot(path=str(OUT/f'{label}-normal-paused.png'));data['native']=native_clip(page,frame,context,mobile,label);assert not errors,errors;report[label]=data;context.close()
  browser.close()
 report['ok']=True;(OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'ok':True,'evidence':str(OUT)}))

if __name__=='__main__':main()
