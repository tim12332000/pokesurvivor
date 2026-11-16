"""Focused Shikamaru source-pool/tapered-shadow acceptance, separate from core-play evidence."""
import base64,hashlib,json,os,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_shikamaru as base
import test_shikamaru_feel as feel
ROOT=base.ROOT
OUT=ROOT/'art-review/shikamaru/qa/shadow-shape'

NATIVE_GEOMETRY=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.reset();const m=A.fixture('naruto-shikamaru'),far=A.spawn(300,0);p.target=far;A.cast(m);A.finish(.75);
 const visual=S.shadowVisualFor(p),cases=[['root-inner',5,-18,true],['root-outer',5,-25,false],['middle-inner',165,-8,true],['middle-outer',165,-14,false],['tip-inner',325,-.1,true],['tip-outer',325,-5,false],['behind-root',-20,0,false],['beyond-tip',332,0,false]],results=[];
 const canvas=document.createElement('canvas');canvas.width=canvas.height=800;const ctx=canvas.getContext('2d');ctx.translate(400,400);G.Combat.drawGroundFields(ctx);
 for(const [name,x,y,expected]of cases){const e=A.spawn(x,y);e.r=1;G.EnemyMgr.rebuildGrid();results.push({name,x,y,expected,e,hits:A.watch(e),pixelAlpha:ctx.getImageData(Math.round(400+x),Math.round(400+y),1,1).data[3]});}
 A.step(.01);return {visual,cases:results.map(({e,...r})=>({...r,actual:r.hits.some(h=>h.loss>0)})),png:canvas.toDataURL()};
}"""

POOL=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.reset();const m=A.fixture('naruto-shikamaru'),initial=S.shadowVisualFor(p),e=A.spawn(300,0);p.target=e;A.cast(m);A.finish(.75);const extended=S.shadowVisualFor(p),state=S.stateFor(p),before={clock:state.clock,castAges:S.casts.map(b=>b.age),leases:S.leases.size};for(let i=0;i<100;i++)S.shadowVisualFor(p);const after={clock:state.clock,castAges:S.casts.map(b=>b.age),leases:S.leases.size};A.assert(JSON.stringify(before)===JSON.stringify(after),'visual query mutated simulation');
 A.finish(.55);const held=S.shadowVisualFor(p),heldNow=S.held(e),rays=S.casts.length;A.finish(1.5);const recovered=S.shadowVisualFor(p);
 A.assert(initial.poolRadius===34&&extended.poolRadius<initial.poolRadius,'extended ribbons did not reduce source pool');A.assert(heldNow&&rays===0&&held.poolRadius<34,'pool refilled while lease still used shadow');A.assert(recovered.poolRadius===34&&recovered.extensionTotal===0,'pool failed to recover after all shadow released');return {initial,extended,held,heldNow,rays,recovered,before,after};
}"""


WALL=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.reset();const m=A.fixture('naruto-shikamaru'),far=A.spawn(300,0);p.target=far;A.cast(m);const before=A.spawn(70,0),behind=A.spawn(150,0);before.r=behind.r=1;G.EnemyMgr.rebuildGrid();const nearHits=A.watch(before),farHits=A.watch(behind),block=G.World.projectileBlock;
 G.World.projectileBlock=(x,y,r)=>x>=100?{kind:'wall'}:false;try{A.finish(.75);const tips=S.casts.flatMap(b=>b.rays.map(r=>r.tip)).filter(Boolean);A.assert(tips.length&&tips.every(p=>p.x<100),'native ray passed wall clipping');A.assert(nearHits.some(h=>h.loss>0)&&!farHits.some(h=>h.loss>0),'clipped ribbon hit behind wall or missed before');return {tips,nearHits,farHits};}finally{G.World.projectileBlock=block}
}"""

BOUNDARIES=r"""() => {
 const A=Acceptance,S=G.NarutoShikamaru,g=S.ribbonGeometry(0,0,200,0,22),cases=[['root-axis',0,0,0,true],['root-side',0,21,0,true],['root-outer',0,23,0,false],['root-behind',-1,0,0,false],['circle-touches-root',-1,0,2,true],['circle-misses-root',-3,0,2,false],['mid-in',100,10,0,true],['mid-out',100,12,0,false],['tip-in',199,.05,0,true],['tip-out',199,1,0,false],['beyond-tip',201,0,0,false],['circle-touches-tip',201,0,2,true],['circle-misses-tip',203,0,2,false]];
 return cases.map(([name,x,y,r,expected])=>{const actual=S.ribbonContains(g,x,y,r);A.assert(actual===expected,'triangle boundary '+name+' '+actual+'/'+expected);return {name,x,y,r,expected,actual}});
}"""


def manifest():
 return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['.omx/naruto-shikamaru.js','art-review/shikamaru-art.js','art-review/shikamaru-frames.json','.omx/digimon.html']}


def native():
 out=OUT/'native';out.mkdir(parents=True,exist_ok=True);report={'controlled':True,'fixture':'Normal entry/native RAF automatic Lv1 shadow; one static 100HP enemy, no manual sim/skill clock stepping; read-only native draw snapshots.','sourceBefore':manifest(),'errors':[]}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=base.CHROME,headless=True);context=browser.new_context(viewport={'width':1100,'height':850},service_workers='block',record_video_dir=str(out/'raw'),record_video_size={'width':1100,'height':850});page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));base.boot(page)
  page.evaluate(r"""()=>{Acceptance.reset();Acceptance.fixture('naruto-shikamaru');window.PoolFrames=[];window.PoolTimeline=[];const draw=G.Combat.drawGroundFields,seen=new Set();let extended=false,last=-1;G.Combat.drawGroundFields=function(ctx){const result=draw.call(this,ctx),S=G.NarutoShikamaru,p=G.Game.player,v=S.shadowVisualFor(p),liveRays=S.casts.filter(b=>b.owner===p&&['shadow','sewing'].includes(b.kind)).length,held=[...S.leases].filter(([e,l])=>l.cast.owner===p&&S.held(e)).length;const state={time:G.Game.st.time,visual:v,liveRays,held,phase:S.stateFor(p)?.plan?.phase||null};if(state.time-last>=.05){last=state.time;PoolTimeline.push(state)}let key=null;if(!extended&&v.extensionTotal===0)key='initial';if(v.poolRadius<18){extended=true;key='extended'}if(extended&&liveRays===0&&held>0)key='held-after-rays';if(extended&&v.extensionTotal===0&&held===0)key='recovered';if(key&&!seen.has(key)){seen.add(key);queueMicrotask(()=>PoolFrames.push({...state,key,png:ctx.canvas.toDataURL()}))}return result};Acceptance.resume()}""")
  page.wait_for_timeout(250);page.evaluate("()=>{const e=Acceptance.spawn(300,0);e.hp=e.maxHp=100;G.Game.player.target=e}")
  page.wait_for_timeout(3600);report['samples']=page.evaluate('PoolTimeline');report['frames']=[]
  for frame in page.evaluate('PoolFrames'):
   png=frame.pop('png');name=frame['key']+'.png';(out/name).write_bytes(base64.b64decode(png.split(',',1)[1]));report['frames'].append({'image':name,**frame})
  video=page.video;context.close();video.save_as(str(out/'pool-tapered-native.webm'));video.delete();browser.close()
 report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'keys':[f['key'] for f in report['frames']],'sourceStable':report['sourceStable'],'errors':report['errors']}))


def main():
 OUT.mkdir(parents=True,exist_ok=True);report={'sourceBefore':manifest(),'controlled':True,'checks':{},'errors':[]}
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=base.CHROME,headless=True);page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block');page.on('pageerror',lambda e:report['errors'].append(str(e)));base.boot(page)
   r=page.evaluate(NATIVE_GEOMETRY);png=r.pop('png');(OUT/'native-ground-mask.png').write_bytes(base64.b64decode(png.split(',',1)[1]));report['checks']['geometry']=r
   report['checks']['pool']=page.evaluate(POOL)
   report['checks']['boundaries']=page.evaluate(BOUNDARIES)
   report['checks']['wall']=page.evaluate(WALL)
   page.evaluate(feel.SETUP);report['checks']['quantityCapture']=page.evaluate(feel.COVERAGE)
   failures=[c['name'] for c in r['cases'] if c['actual']!=c['expected']];report['failures']=failures;print(json.dumps({'failures':failures,'geometry':r,'pool':report['checks']['pool']},ensure_ascii=False));browser.close()
   assert not failures,failures
  report['ok']=True
 except Exception as error:report['failure']=str(error);raise
 finally:
  report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':
 if '--native' in sys.argv:native()
 else:main()
