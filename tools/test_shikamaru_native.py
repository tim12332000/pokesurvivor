"""Controlled native RAF demonstrations; no synthetic frame stepping or montage."""
from __future__ import annotations
import base64,hashlib,json,os,time
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_shikamaru as base
OUT=Path(os.environ.get('SHIKAMARU_VISUAL_OUT',base.ROOT/'art-review/shikamaru/qa/native-v3'))

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 sources=['.omx/naruto-shikamaru.js','art-review/shikamaru-art.js','art-review/shikamaru-frames.json','js/entities/enemy.js','js/systems/combat.js','js/systems/self-clone.js','.omx/naruto-skills.js']
 sources += [str(p.relative_to(base.ROOT)).replace('\\','/') for p in (base.ROOT/'art-review/shikamaru').glob('*.png')]
 hashes=lambda:{s:hashlib.sha256((base.ROOT/s).read_bytes()).hexdigest() for s in sources if (base.ROOT/s).exists()}
 report={'controlled':True,'sourceBefore':hashes(),'samples':[],'errors':[],'url':base.URL}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
  context=browser.new_context(viewport={'width':1100,'height':850},service_workers='block',record_video_dir=str(OUT/'raw'),record_video_size={'width':1100,'height':850})
  page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));base.boot(page)
  page.evaluate(r'''()=>{window.NativePoseCaptures=[];const draw=G.ShikamaruArt.draw,seen=new Set();G.ShikamaruArt.draw=function(ctx,actor,options){const result=draw.call(this,ctx,actor,options),pose=options?.pose;if(actor===G.Game.player&&pose?.kind==='trap'){const phase=pose.age<.65*.24?'prepare':pose.age<.65*.65?'release':'recover',key=window.NativeCaptureDirection+'-'+phase;if(!seen.has(key)){seen.add(key);const state={direction:window.NativeCaptureDirection,phase,age:pose.age,aim:pose.aim,gameTime:G.Game.st.time,wall:performance.now()/1000,frame:G.ShikamaruArt.sample('cast',pose.age,G.Sprites.dirFromAngle(pose.aim),pose)?.key};queueMicrotask(()=>window.NativePoseCaptures.push({...state,png:ctx.canvas.toDataURL()}));}}if(actor===G.Game.player){const effect=G.NarutoShikamaru.effects.find(e=>e.kind==='strangle'&&e.age>=.14&&e.age<=.18);if(effect&&!seen.has('strangle-settled')){seen.add('strangle-settled');const state={kind:'strangle',direction:window.NativeCaptureDirection,phase:'settled',effectAge:effect.age,bodyH:effect.bodyH,gameTime:G.Game.st.time,wall:performance.now()/1000};queueMicrotask(()=>window.NativePoseCaptures.push({...state,png:ctx.canvas.toDataURL()}));}const b=G.NarutoShikamaru.casts.find(b=>b.owner===actor&&b.kind==='strangle');if(b&&b.emitted){const phase=b.emitted>=b.spec.pulses?'last':b.emitted>=Math.ceil(b.spec.pulses/2)?'middle':'first',key='strangle-'+phase;if(!seen.has(key)){seen.add(key);const state={kind:'strangle',direction:window.NativeCaptureDirection,phase,age:b.age,emitted:b.emitted,pulses:b.spec.pulses,gameTime:G.Game.st.time,wall:performance.now()/1000,effects:G.NarutoShikamaru.effects.filter(e=>e.kind==='strangle').map(e=>({x:e.x,y:e.y,age:e.age,bodyH:e.bodyH}))};queueMicrotask(()=>window.NativePoseCaptures.push({...state,png:ctx.canvas.toDataURL()}));}}}return result}}''')
  for mode,direction in ([('strangle','right')] if os.environ.get('SHIKAMARU_ONLY_STRANGLE') else [('trap',d) for d in ['right','down','left','up']] if os.environ.get('SHIKAMARU_ONLY_TRAPS') else [('shadow','right'),('sewing','right'),('strangle','right'),('trap','right'),('trap','down'),('trap','left'),('trap','up')]):
   page.evaluate(r'''([mode,direction])=>{const A=Acceptance,p=A.p();window.NativeCaptureDirection=direction;A.reset();p.level=30;p.invuln=999;p.quantityPicks=p.quantityBonus=2;p.moves=[G.Moves.instance(mode==='shadow'?'naruto-shikamaru':'naruto-shikamaru-'+mode,3)];if(mode==='strangle')p.moves.unshift(G.Moves.instance('naruto-shikamaru',3));
    const angle={right:0,down:Math.PI/2,left:Math.PI,up:-Math.PI/2}[direction];p.anim.dir={down:0,right:2,up:4,left:6}[direction];for(const [x,y]of [[90,0],[125,-40],[125,40]])A.spawn(Math.cos(angle)*x-Math.sin(angle)*y,Math.sin(angle)*x+Math.cos(angle)*y);for(const m of p.moves)m.t=0;p.target=G.EnemyMgr.all()[0];A.resume();}''',[mode,direction])
   started=time.monotonic();index=0
   while time.monotonic()-started<4:
    page.wait_for_timeout(120)
    state=page.evaluate(r'''()=>{const p=G.Game.player,S=G.NarutoShikamaru;return {t:G.Game.st.time,wall:performance.now()/1000,moves:p.moves.map(m=>({id:m.id,rank:m.lvl})),casts:S.casts.filter(b=>b.owner===p).map(b=>({serial:b.serial,kind:b.kind,age:b.age,emitted:b.emitted,pulses:b.spec.pulses,rays:b.rays.map(r=>({source:r.source,tip:r.tip})),traps:b.traps.map(t=>({x:t.x,y:t.y,age:t.age,detonated:t.detonated}))})),animDirection:p.anim.dir,artFrame:G.ShikamaruArt.sample('idle',S.activeFor(p)?.age||0,S.activeFor(p)?G.Sprites.dirFromAngle(S.activeFor(p).aim):p.anim.dir,S.activeFor(p))?.key,artPose:S.activeFor(p)?{kind:S.activeFor(p).kind,age:S.activeFor(p).age}:null,stats:S.stats(p)}}''')
    name=f'{mode}-{direction}-{index:02d}.png';page.screenshot(path=str(OUT/name));report['samples'].append({'mode':mode,'direction':direction,'image':name,**state});index+=1
   page.evaluate('Acceptance.pause()')
  captures=page.evaluate('NativePoseCaptures');report['nativePhaseCaptures']=[]
  for capture in captures:
   png=capture.pop('png');name='native-'+capture.get('kind','trap')+'-'+capture['direction']+'-'+capture['phase']+'.png';(OUT/name).write_bytes(base64.b64decode(png.split(',',1)[1]));report['nativePhaseCaptures'].append({'image':name,**capture})
  video=page.video;context.close();video.save_as(str(OUT/'native-demonstration.webm'));video.delete();browser.close()
 report['sourceAfter']=hashes();report['sourceStable']=report['sourceAfter']==report['sourceBefore']
 (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'samples':len(report['samples']),'sourceStable':report['sourceStable'],'errors':report['errors']}))
if __name__=='__main__':main()
