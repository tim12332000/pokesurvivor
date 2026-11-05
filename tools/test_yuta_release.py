"""Manifestation's single, two-source high-output release through native entry."""
from __future__ import annotations
import json
import base64
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_jujutsu as base

OUT=Path(os.environ.get('YUTA_RELEASE_OUT',base.ROOT/'.omx/state/yuta-release'))
CHECK=r"""() => {
 const A=JAcceptance,Y=G.JujutsuYuta,p=A.p(),assert=A.assert,out={},ids={manifest:'jjk-yuta-manifest',rika:'jjk-yuta-rika',blade:'jjk-yuta',speech:'jjk-yuta-speech'};
 const nativePath=G.World.projectilePathClear;
 function setup(names=['manifest'],rank=1,q=0){A.reset();G.World.projectilePathClear=nativePath;A.fixture(ids[names[0]],rank);
  for(const name of names.slice(1))assert(p.addMove(ids[name]),'learn '+name);
  for(const m of p.moves){Object.assign(m,G.Moves.instance(m.id,rank));m.t=999;}p.quantityPicks=p.quantityBonus=q;p.invuln=999;
  return Object.fromEntries(names.map(name=>[name,p.moves.find(m=>m.id===ids[name])]));}
 function cast(m){m.t=0;A.resume();try{assert(Y.cast(p,m),'cast '+m.id)}finally{A.pause()};return Y.stateFor(p);}
 function wait(test,seconds=6){for(let t=0;t<seconds&&!test();t+=.01)A.advance(.01);assert(test(),'release phase timeout');}
 for(const rank of [1,3,5]){
  const m=setup(['manifest'],rank),targets=[A.spawn(250,0),A.spawn(400,0),A.spawn(520,0)],events=targets.map(e=>A.watch(e)),outside=A.spawn(1000,250),outsideHits=A.watch(outside);
  const s=cast(m.manifest),actor=s.companion;wait(()=>s.release?.phase==='charge');
  assert(s.companion===actor&&!s.rika&&Y.drawables(null).length===1,'release duplicated actor or granted free punches');
  wait(()=>s.release?.phase==='release');const f=s.release,sources=f.sources.map(source=>({...source}));
  assert(sources.length===2&&new Set(sources.map(source=>source.castId)).size===2,'release lacks two independent casts');
  assert(Math.hypot(sources[0].x-sources[1].x,sources[0].y-sources[1].y)>10,'release origins collapsed');
  assert(f.range===G.Jujutsu.power.yuta.releaseRanges[rank-1]&&f.radius===G.Jujutsu.power.yuta.releaseRadii[rank-1],'release profile differs');
  assert(events.every(h=>h.filter(x=>x.id===ids.manifest).length===2)&&!outsideHits.length,'two-source real multi-target/range damage differs '+JSON.stringify({hits:events.map(h=>h.length),sources}));
  const marks=s.marks.filter(mark=>mark.kind==='release'),snapshot=JSON.stringify(marks.map(mark=>[mark.x,mark.y,mark.aim]));p.x+=60;A.advance(.05);
  assert(JSON.stringify(marks.map(mark=>[mark.x,mark.y,mark.aim]))===snapshot,'released geometry followed moving owner');
  A.advance(4);assert(s.casts.release===1&&events.every(h=>h.filter(x=>x.id===ids.manifest).length===2),'manifest repeated its release');
  out['rank'+rank]={sources:sources.map(({x,y,aim,length,radius,castId,channel})=>({x,y,aim,length,radius,castId,channel})),hits:events.map(h=>h.length),releaseCount:s.casts.release};
 }
 let m=setup(['rika','manifest','blade','speech'],5,20),e=A.spawn(300,0),events=A.watch(e),s=cast(m.manifest);cast(m.rika);
 const actor=s.companion,rikaCast=s.rika.castId;wait(()=>s.rika?.strikeIndex===24);
 assert(!s.release&&s.rika.castId===rikaCast,'release interrupted the 24-punch finisher');
 wait(()=>s.release?.phase==='charge');assert(s.companion===actor&&!s.rika,'release replaced companion after combo');
 const release=s.release;cast(m.speech);A.advance(.25);assert(s.release===release&&Y.stopped(e),'speech interrupted release or failed during charge');
 wait(()=>s.release?.phase==='release');assert(events.filter(h=>h.id===ids.rika).length===24&&events.filter(h=>h.id===ids.manifest).length===2,'duet/release damage chronology differs');
 out.duetThenRelease={punches:24,releaseHits:2,sameActor:true,speechConcurrent:true};
 m=setup();e=A.spawn(300,0);s=cast(m.manifest);wait(()=>s.release?.phase==='charge');
 const frozen=s.release,age=frozen.age;G.Combat.updateFields(.5);assert(frozen.age===age,'pause advanced release');
 p.frozen=true;A.advance(.4);assert(frozen.age===age,'frozen owner advanced release');p.frozen=false;A.advance(.6);assert(s.casts.release===1,'unfrozen release did not resume');out.pauseFrozen=true;
 for(const cancel of ['expire','clear','unlearn','dead','wall']){
  m=setup();e=A.spawn(300,0);events=A.watch(e);s=cast(m.manifest);wait(()=>s.release?.phase==='charge');
  if(cancel==='expire')s.manifestUntil=s.clock+.01;
  if(cancel==='clear')G.Combat.clearFields(p);
  if(cancel==='unlearn')p.moves=[];
  if(cancel==='dead'){p.dead=true;p.hp=0;}
  if(cancel==='wall')G.World.projectilePathClear=(x,y,tx,ty)=>tx<200;
  A.advance(1);assert(!events.length,'cancelled release dealt damage '+cancel);out['cancel-'+cancel]=true;
 }
 for(const cancel of ['clear','unlearn']){
  m=setup();const victims=[A.spawn(250,0),A.spawn(400,0)];let calls=0;
  for(const victim of victims){const hurt=victim.hurt;victim.hurt=function(...args){calls++;const result=hurt.apply(this,args);if(cancel==='clear')G.Combat.clearFields(p);else p.moves=[];return result;};}
  cast(m.manifest);A.advance(2);assert(calls===1,'release callback retained same-wave or second-source damage '+cancel);out['callback-'+cancel]=true;
 }
 for(const callback of ['hurt','onDealt','freeze']){
  m=setup();const victims=[A.spawn(250,0),A.spawn(400,0)],events=victims.map(e=>A.watch(e));s=cast(m.manifest);
  const previous=p.onDealt;
  if(callback==='hurt')for(const victim of victims){const hurt=victim.hurt;victim.hurt=function(...args){const result=hurt.apply(this,args);s.manifestUntil=s.clock;return result;};}
  else p.onDealt=function(...args){if(callback==='freeze')p.frozen=true;else s.manifestUntil=s.clock;return previous.apply(this,args)};
  const props=G.World.propsInCircle,damageProp=G.World.damageProp;let propHits=0;
  G.World.propsInCircle=()=>[{x:300,y:0,r:12,hp:100,destructible:true}];G.World.damageProp=()=>propHits++;
  try{A.advance(2)}finally{p.onDealt=previous;G.World.propsInCircle=props;G.World.damageProp=damageProp}
  assert(events.reduce((n,events)=>n+events.length,0)===1,'expired manifestation retained same-source or next-source damage in '+callback);
  assert(propHits===0,'cancelled/frozen release retained prop damage '+callback);
  out['callback-expire-'+callback]={hits:events.map(events=>events.length)};
 }
 m=setup(['blade']);e=A.spawn(100,0);events=A.watch(e);cast(m.blade);A.advance(2);assert(!events.some(h=>h.id===ids.manifest),'unlearned manifest released');out.noFreeRelease=true;
 return out;
}"""

NATIVE=r"""mobile=>{
 const A=JAcceptance,p=A.p();A.reset();A.fixture('jjk-yuta',5);p.level=12;p.invuln=0;p.quantityPicks=p.quantityBonus=4;p.xpNext=1e12;
 for(const id of ['jjk-yuta-rika','jjk-yuta-manifest','jjk-yuta-speech','jjk-yuta-resonance'])A.assert(p.addMove(id),'native learn '+id);
 for(const m of p.moves){Object.assign(m,G.Moves.instance(m.id,5));m.t=0;}
 // Delay pressure until the duet is already striking: speech must then react
 // without replacing the existing full companion or skipping the finisher.
 p.moves.find(m=>m.id==='jjk-yuta-speech').t=1.2;G.Spawner.update=()=>{};
 for(const [x,y] of (mobile?[[0,-90],[0,-230],[40,-300],[-40,-370]]:[[90,0],[260,0],[330,30],[430,-30]])){
  const e=A.spawn(x,y);e.touchCd=999;e.elite=true;
 }
 const label=document.createElement('div');label.id='release-evidence-label';label.style='position:fixed;top:90px;left:8px;right:8px;z-index:99999;background:#241d35e8;color:#fff;padding:8px;font:13px sans-serif;pointer-events:none';
 label.textContent='完全顯現＋別動＋高出力放出｜五階・4數量卡｜受控敵人／原生自動戰鬥';document.body.append(label);
 const run=window.ReleaseNative={started:G.Game.st.time,ownerDraws:0};const draw=G.JujutsuArt.draw;
 G.JujutsuArt.draw=function(ctx,actor,...args){if(actor===p)run.ownerDraws++;return draw.call(this,ctx,actor,...args)};
 G.Game.debugSpeed(1);A.resume();return {level:12,rank:5,quantityCards:4,controlledEnemies:true,playerInvulnerability:0};
}"""

def record_native(page,frame,label,mobile):
    fixture=frame.evaluate(NATIVE,mobile)
    frame.evaluate("""()=>{const stream=document.getElementById('game').captureStream(24),recorder=new MediaRecorder(stream,{mimeType:'video/webm',videoBitsPerSecond:2200000}),chunks=[];
     recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
     window.ReleaseClip={recorder,stream,done:new Promise(resolve=>recorder.onstop=()=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}))})};recorder.start();}""")
    frame.wait_for_function("G.JujutsuYuta.stateFor(JAcceptance.p())?.speech?.released&&G.JujutsuYuta.stateFor(JAcceptance.p())?.rika?.full",timeout=12000,polling=10)
    page.screenshot(path=str(OUT/f'{label}-duet-speech.png'))
    frame.wait_for_function("G.JujutsuYuta.stateFor(JAcceptance.p())?.release?.phase==='charge'",timeout=12000,polling=10)
    charge=frame.evaluate("""()=>{const p=JAcceptance.p(),s=G.JujutsuYuta.stateFor(p),a=s.companion;return {owner:{x:p.x,y:p.y},actor:{x:a.x,y:a.y,height:a.height,frame:a.releasePose?.frameName},drawableY:G.JujutsuYuta.drawables(null)[0]?.y,sources:s.release.sources,ownerDraws:ReleaseNative.ownerDraws};}""")
    page.screenshot(path=str(OUT/f'{label}-release-charge.png'))
    frame.wait_for_function("G.JujutsuYuta.stateFor(JAcceptance.p())?.marks.some(m=>m.kind==='release')",timeout=12000,polling=10)
    page.screenshot(path=str(OUT/f'{label}-release-contact.png'))
    page.wait_for_timeout(900)
    result=frame.evaluate("""async()=>{JAcceptance.pause();const c=ReleaseClip;c.recorder.stop();const data=await c.done;for(const t of c.stream.getTracks())t.stop();
     const s=G.JujutsuYuta.inspect(JAcceptance.p());document.getElementById('release-evidence-label')?.remove();
     JAcceptance.assert(s.casts.speech>0&&s.casts.release===1,'native speech/release missing or repeated');
     return {data,casts:s.casts,elapsed:G.Game.st.time-ReleaseNative.started,drawableCount:G.JujutsuYuta.drawables(null).length,ownerDraws:ReleaseNative.ownerDraws};}""")
    path=OUT/f'{label}-native-manifest-speech-release.webm';path.write_bytes(base64.b64decode(result.pop('data').split(';base64,',1)[1]))
    return {**fixture,**result,'chargeSnapshot':charge,'clip':str(path)}

def main():
    OUT.mkdir(parents=True,exist_ok=True);base.OUT=OUT;base.URL=os.environ.get('JUJUTSU_URL','http://127.0.0.1:8383/.omx/digimon.html?lang=zh-TW')
    report={'url':base.URL,'cases':{},'errors':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        for mobile in [False,True]:
            label='mobile' if mobile else 'desktop'
            context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
            page=context.new_page();page.on('pageerror',lambda error:report['errors'].append(str(error)));frame=base.boot(page,30013,label)
            report['cases'][label]=frame.evaluate(CHECK)
            report['cases'][label]['native']=record_native(page,frame,label,mobile);context.close()
        browser.close()
    assert not report['errors'],report['errors'];report['ok']=True;(OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({'ok':True,'views':list(report['cases']),'evidence':str(OUT)}))

if __name__=='__main__':main()
