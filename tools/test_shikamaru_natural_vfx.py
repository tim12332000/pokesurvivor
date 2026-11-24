"""Paired production-entry evidence for Shikamaru's shadow material and motion.

The arenas and legal cards are controlled fixtures. Native RAF recordings use
real keyboard input; they are not natural growth or physical-phone validation.
--baseline serves the four relevant runtime files from the published 73356e21
commit while retaining the same entry, arena, cards and input sequence.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import time

from playwright.sync_api import sync_playwright
import test_shikamaru as base

OUT = base.ROOT / '.omx/state/shikamaru-natural-vfx/qa'
BASELINE = '73356e21'
RUNTIME = ['.omx/naruto-shikamaru.js',
           'art-review/shikamaru/reference-shadow-geometry.js',
           'art-review/shikamaru-art.js', '.omx/naruto-shikamaru-decoy.js']
SOURCES = RUNTIME + ['.omx/naruto-shikamaru-mass.js', '.omx/digimon.html']


def manifest():
    return {name: hashlib.sha256((base.ROOT / name).read_bytes()).hexdigest()
            for name in SOURCES}


def baseline_routes(page, report):
    def handler_for(data):
        def handle(route):
            route.fulfill(body=data, content_type='application/javascript')
        return handle

    report['baselineRuntime'] = {}
    for name in RUNTIME:
        payload = subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=base.ROOT)
        report['baselineRuntime'][name] = hashlib.sha256(payload).hexdigest()
        page.route('**/' + name + '*', handler_for(payload))


SETUP = r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,D=G.NarutoShikamaruDecoy,M=G.NarutoShikamaruMass;
 A.vfxBuild=({decoy=false,sewing=false,mass=false}={})=>{
  A.reset();G.World.reset(73356021);G.World.setBiome(0,true);p.level=6;p.statsTaken={};p.moves=[G.Moves.instance('naruto-shikamaru')];
  const ledger=[];
  for(let i=0;i<2;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='up:naruto-shikamaru');A.assert(c&&c.apply(p)!==false,'actual shadow rank card missing');ledger.push(c.key)}
  for(const id of [sewing?'naruto-shikamaru-sewing':null,decoy?'naruto-shikamaru-decoy':null,mass?'naruto-shikamaru-mass':null].filter(Boolean)){
   const c=G.LevelUp.offer(p,1000).find(c=>c.key==='new:'+id);A.assert(c&&c.apply(p)!==false,'actual skill card missing '+id);ledger.push(c.key);
  }return ledger;
 };
 A.vfxStep=(dt=.01)=>{A.resume();try{G.Combat.updateFields(dt);p.anim.update(dt)}finally{A.pause()}};
 A.vfxAdvance=seconds=>{let left=seconds;while(left>1e-8){const dt=Math.min(.01,left);A.vfxStep(dt);left-=dt}};
 A.vfxDecoy=()=>{const ledger=A.vfxBuild({decoy:true});p.moves=p.moves.filter(m=>m.id==='naruto-shikamaru-decoy');const e=A.spawn(100,60);A.resume();try{A.assert(D.cast(p,p.moves[0]),'decoy cast rejected')}finally{A.pause()}return {ledger,e,d:D.decoys().find(d=>d.owner===p)}};
 A.vfxPhysics=()=>({hp:p.hp,moves:p.moves.map(m=>({id:m.id,t:m.t})),
  decoys:D.decoys().map(d=>({id:d.id,x:d.x,y:d.y,age:d.age,hp:d.hp})),
  shadow:S.stats(p),casts:S.casts.map(b=>({serial:b.serial,age:b.age,emitted:b.emitted,arcs:b.arcs?.map(a=>({progress:a.progress,phase:a.phase,hit:a.hit}))})),
  returns:S.stateFor(p)?.shadowReturns?.map(r=>({age:r.age,remainingLength:r.remainingLength,points:r.remainingPoints})),
  mass:M.stateFor(p)?{casts:M.stateFor(p).casts,hits:M.stateFor(p).hits,age:M.stateFor(p).cast?.age}:null});
 A.vfxPixels=()=>{const canvas=document.createElement('canvas');canvas.width=256;canvas.height=220;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.translate(128-p.x,180-p.y);G.Combat.drawGroundFields(ctx);const rgba=ctx.getImageData(0,0,256,220).data;let left=256,top=220,right=-1,bottom=-1,count=0;for(let y=0;y<220;y++)for(let x=0;x<256;x++)if(rgba[(y*256+x)*4+3]>24){left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);count++}return {bounds:count?[left,top,right,bottom]:null,height:count?bottom-top+1:0,count,png:canvas.toDataURL()}};
}'''

DECOY_CHECK = r'''() => {
 const A=Acceptance,p=A.p(),D=G.NarutoShikamaruDecoy,out={samples:[],cleanup:[]};
 let {ledger,e,d}=A.vfxDecoy();out.ledger=ledger;const origin={x:d.x,y:d.y};
 for(const fraction of [.025,.3,.94]){
  A.vfxAdvance(Math.max(0,d.life*fraction-d.age));const pixels=A.vfxPixels();out.samples.push({fraction,age:d.age,visual:D.visualFor?.(d)||null,pixels});
  A.assert(d.x===origin.x&&d.y===origin.y,'animated lure moved its AI anchor');
 }
 A.assert(out.samples[1].pixels.height>20,'formed lure has no readable body');
 A.assert(out.samples[0].pixels.height<out.samples[1].pixels.height*.8,'formation only changed opacity, not rendered extent');
 A.assert(out.samples[2].pixels.height<out.samples[1].pixels.height*.8,'collapse only changed opacity, not rendered extent');
 p.x=140;e.x=60;e.y=70;e.spd=35;e.flying=true;
 A.resume();try{e.update(.01,p)}finally{A.pause()}
 A.assert(e._shikamaruDecoyTarget===d,'collapsing visible lure lost actual AI redirection early');
 const before=JSON.stringify(A.vfxPhysics()),canvas=document.createElement('canvas');canvas.width=canvas.height=500;const ctx=canvas.getContext('2d');ctx.translate(250,300);
 for(let i=0;i<40;i++){G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);D.visualFor?.(d)}
 A.assert(before===JSON.stringify(A.vfxPhysics()),'drawing advanced actors, clocks or damage');
 D.update(d.life);A.assert(before===JSON.stringify(A.vfxPhysics()),'paused visual clocks advanced');
 A.vfxAdvance(d.life-d.age+.1);A.assert(!D.decoys().length,'expired material retained its lure actor');out.readOnly=true;out.pause=true;out.expiry=true;
 for(const reason of ['clear','death','world','unlearn','epoch']){
  ({d}=A.vfxDecoy());A.vfxAdvance(d.life*.3);const world=G.World;
  if(reason==='clear')G.Combat.clearFields(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};if(reason==='unlearn')p.moves=[];if(reason==='epoch')G.CombatPulse.beginRun();
  A.resume();try{D.update(.01)}finally{A.pause();p.dead=false;G.World=world}
  A.assert(!D.decoys().length,'material actor retained after '+reason);out.cleanup.push(reason);
 }
 return out;
}'''

RETURN_CHECK = r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 function setup(){A.vfxBuild();const es=[A.spawn(160,0),A.spawn(0,160),A.spawn(-160,0)],hits=es.map(A.watch);A.cast(p.moves[0]);let captured=false,returns=[];for(let i=0;i<450;i++){A.vfxStep();captured||=es.every(S.held);returns=S.stateFor(p)?.shadowReturns||[];if(captured&&returns.length)break}A.assert(captured&&returns.length,'no visual withdrawal after real shadow release');A.assert(es.every(e=>!S.held(e)),'visual withdrawal prolonged control');return {es,hits,returns};}
 for(const reason of ['finish','clear','death','world','unlearn']){
  const {es,hits,returns}=setup(),hitCount=hits.reduce((n,h)=>n+h.length,0),age=returns[0].age,world=G.World;
  S.update(.5);A.assert(returns[0].age===age,'paused withdrawal advanced');
  if(reason==='clear')S.clear(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};if(reason==='unlearn')p.moves=[];
  try{A.vfxAdvance(Math.max(...returns.map(r=>r.life))+.1);A.assert(!S.stateFor(p)?.shadowReturns?.length,'withdrawal did not end '+reason);A.assert(es.every(e=>!S.held(e))&&hits.reduce((n,h)=>n+h.length,0)===hitCount,'visual withdrawal added damage or binding '+reason)}finally{p.dead=false;G.World=world}
  out.push({reason,hitCount});
 }
 return out;
}'''

NATIVE_SETUP = r'''scene => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,D=G.NarutoShikamaruDecoy,M=G.NarutoShikamaruMass;
 const ledger=A.vfxBuild(scene==='mass'?{mass:true}:scene==='decoy'?{decoy:true}:{decoy:true,sewing:true});
 // Freeze only procedural arrivals, so paired arenas contain the same native
 // actors while their normal updates, casts, collision and render clocks run.
 G.Spawner.update=()=>{};
 const targets=scene==='mass'?[[120,-60],[-140,60],[30,160]].map(([x,y],i)=>A.spawn(x,y,i===0)):scene==='decoy'?[A.spawn(40,90)]:[[130,0],[40,140],[-130,25]].map(([x,y])=>A.spawn(x,y));
 if(scene==='decoy'){p.moves=p.moves.filter(m=>m.id==='naruto-shikamaru-decoy');A.resume();try{A.assert(D.cast(p,p.moves[0]),'isolated native lure cast rejected')}finally{A.pause()}p.x=100;}
 p.target=targets[0];
 const Q=window.NaturalVfx={scene,ledger,frames:[],samples:[],seen:new Set(),firstDecoy:null,hadHeld:false,last:-1,started:performance.now()};
 const draw=G.Combat.drawAirFields;
 G.Combat.drawAirFields=function(ctx){const result=draw.call(this,ctx),s=S.stateFor(p),pose=S.activeFor(p),samplePose=pose?{...pose,walkTime:(p.anim.frame*6+p.anim.t)/60}:pose,frame=G.ShikamaruArt.sample('cast',pose?.age||0,p.anim.dir,samplePose),decoys=D.decoys().filter(d=>d.owner===p),arcs=S.casts.filter(b=>b.owner===p).flatMap(b=>b.arcs||[]),held=targets.filter(S.held),b=M.stateFor(p)?.cast;
  Q.firstDecoy??=decoys[0]?.id;const d=decoys.find(d=>d.id===Q.firstDecoy),visual=d?D.visualFor?.(d):null,keys=[];
  if(held.length>=2){keys.push('shadow-connected');Q.hadHeld=true}
  if(arcs.some(a=>a.pulseIndex===1&&a.progress>.3&&a.progress<.8))keys.push('sewing-first');
  if(arcs.some(a=>a.pulseIndex>=2&&a.progress>.3&&a.progress<.8))keys.push('sewing-later');
  if(d){if(visual?(visual.phase==='form'&&visual.height>.1&&visual.height<.65):d.age>d.life*.02&&d.age<d.life*.07)keys.push('decoy-form');if(d.age>d.life*.3&&d.age<d.life*.6)keys.push('decoy-hold');if(visual?(visual.phase==='collapse'&&visual.height>.1&&visual.height<.65):d.age>d.life*.9)keys.push('decoy-collapse')}
  if(s?.shadowReturns?.some(r=>r.age>r.life*.15&&r.remainingLength>0))keys.push('shadow-return');
  if(Q.hadHeld&&!held.length)keys.push('shadow-released');if(Q.firstDecoy&&!d)keys.push('decoy-release');
  let bomb=null;if(b?.bomb){const u=Math.max(0,Math.min(1,(b.age-b.throwAt)/b.spec.bombFlight)),source=b.bomb.source,side=Math.cos(b.bomb.aim)<-.25?-1:1,point={x:source.x+(b.center.x-source.x)*u+Math.sin(Math.PI*u)*24*side,y:source.y+(b.center.y-source.y)*u-Math.sin(Math.PI*u)*84};bomb={progress:u,point,distanceFromBody:Math.hypot(point.x-p.x,point.y-(p.y-18))};}
  if(b){if(b.age>b.spec.prepare+.06&&b.age<b.full)keys.push('mass-stab');if(pose?.phase==='mass-conduct')keys.push('mass-conduct');if(pose?.phase==='mass-throw-prepare')keys.push('mass-throw-prepare');if(pose?.phase==='mass-throw-release')keys.push('mass-throw');if(bomb&&bomb.progress>0&&bomb.distanceFromBody>30&&['mass-throw-release','mass-throw-recover'].includes(pose?.phase))keys.push('mass-throw-travel');if(b.exploded&&b.age<b.blastAt+.3)keys.push('mass-blast');if(b.age>b.releaseAt+.1)keys.push('mass-release')}
  const clock=s?.clock??D.stateFor(p)?.clock??G.Game.st.time,state={time:G.Game.st.time,clock,worldSeed:73356021,owner:{x:p.x,y:p.y,moving:s?.moving??p.walking,dir:p.anim.dir},pose:pose?{kind:pose.kind,phase:pose.phase,stage:pose.stage,phaseAge:pose.phaseAge,phaseDuration:pose.phaseDuration,moving:pose.moving}:null,body:frame?{key:frame.key,direction:frame.direction,lowerKey:frame.lowerFrame?.key,lowerDirection:frame.lowerFrame?.direction}:null,held:held.length,arcs:arcs.map(a=>({progress:a.progress,phase:a.phase,pulseIndex:a.pulseIndex})),decoy:d?{id:d.id,x:d.x,y:d.y,age:d.age,life:d.life,visual}:null,bomb};
  if(clock-Q.last>.06){Q.last=clock;Q.samples.push(state)}
  for(const key of keys)if(!Q.seen.has(key)){Q.seen.add(key);queueMicrotask(()=>Q.frames.push({...state,key,png:ctx.canvas.toDataURL()}))}
  return result;
 };A.resume();
}'''


def observe(page, report):
    page.on('pageerror', lambda e: report['errors'].append({'message':str(e),'stack':e.stack}))
    page.on('requestfailed', lambda r: report.setdefault('failedRequests', []).append({'url':r.url,'failure':r.failure}))


def boot(page, baseline, report, width):
    if baseline:
        baseline_routes(page, report)
    saved = base.URL
    if width < 600:
        base.URL = saved.replace('&layout=wide', '')
    try:
        base.boot(page)
    finally:
        base.URL = saved
    page.evaluate('window.NaturalWarmEnemy=Acceptance.spawn(1000,1000)')
    page.wait_for_function('!!G.ShikamaruReferenceGeometry.bodyFor(NaturalWarmEnemy)')
    page.evaluate(SETUP)


def save_frames(folder, data):
    for frame in data.get('frames', []):
        png = frame.pop('png')
        name = frame['key'] + '.png'
        (folder / name).write_bytes(base64.b64decode(png.split(',', 1)[1]))
        frame['image'] = name


def native(browser, report, baseline):
    for label, width, height in [('desktop',1100,850),('mobile390',390,844)]:
        for scene in ['kit','mass','decoy']:
            folder = OUT / ('baseline' if baseline else 'current') / label / scene
            folder.mkdir(parents=True, exist_ok=True)
            context = browser.new_context(viewport={'width':width,'height':height}, is_mobile=width<600,
                                          has_touch=width<600, service_workers='block',
                                          record_video_dir=str(folder/'raw'), record_video_size={'width':width,'height':height})
            context.set_default_timeout(60000)
            page = context.new_page(); observe(page, report)
            boot(page, baseline, report, width)
            page.evaluate(NATIVE_SETUP, scene)
            required = (['shadow-connected','sewing-first','sewing-later','decoy-form','decoy-hold','decoy-collapse','shadow-released']
                        if scene=='kit' else ['decoy-form','decoy-hold','decoy-collapse','decoy-release'] if scene=='decoy'
                        else ['mass-conduct','mass-throw-prepare','mass-throw','mass-throw-travel','mass-blast','mass-release'])
            if not baseline and scene=='kit': required.append('shadow-return')
            held = None; step = 0; started = time.monotonic()
            while time.monotonic()-started < 12:
                seen = page.evaluate('[...NaturalVfx.seen]')
                if all(key in seen for key in required): break
                key = ['KeyD','KeyS','KeyA','KeyW'][step%4]
                if held: page.keyboard.up(held)
                page.keyboard.down(key);held=key;step+=1
                page.wait_for_timeout(150)
            if held: page.keyboard.up(held)
            page.evaluate('Acceptance.pause()')
            data = page.evaluate('({ledger:NaturalVfx.ledger,frames:NaturalVfx.frames,samples:NaturalVfx.samples,seen:[...NaturalVfx.seen]})')
            missing = [key for key in required if key not in data['seen']]
            assert not missing, {'viewport':label,'scene':scene,'missing':missing,'seen':data['seen']}
            if not baseline:
                if scene=='kit':
                    later = next(f for f in data['frames'] if f['key']=='sewing-later')
                    assert later['pose'] and later['pose']['kind']=='sewing' and later['pose']['moving'] and later['body'].get('lowerKey'), later
                elif scene=='mass':
                    throw = next(f for f in data['frames'] if f['key']=='mass-throw')
                    assert throw['pose']['moving'] and throw['body'].get('lowerKey') and 'throw' in throw['body']['key'].lower(), throw
            save_frames(folder, data)
            report.setdefault('native', {}).setdefault(label, {})[scene] = data
            video = page.video;context.close();video.save_as(str(folder/'native-cycle.webm'));video.delete()
            print(label, scene, 'paired native capture PASS', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--capture-only', action='store_true')
    args = parser.parse_args()
    folder = OUT / ('baseline' if args.baseline else 'current')
    folder.mkdir(parents=True, exist_ok=True)
    if args.capture_only and (folder/'report.json').is_file():
        previous = json.loads((folder/'report.json').read_text('utf8'))
        if previous.get('ok') and previous.get('checks'):
            (folder/'mechanics-report.json').write_text(json.dumps(previous,ensure_ascii=False,indent=2),encoding='utf8')
    report = {'baseline':args.baseline,'controlled':True,'url':base.URL,'sourceBefore':manifest(),
              'captureOnly':args.capture_only,'worldSeed':73356021,
              'policy':'Controlled legal-card arenas and native RAF keyboard captures. No claim of natural growth or physical phones.',
              'errors':[],'checks':{}}
    if args.capture_only and (folder/'mechanics-report.json').is_file():
        report['mechanicsEvidence'] = 'mechanics-report.json'
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            if not args.baseline and not args.capture_only:
                page = browser.new_page(viewport={'width':1100,'height':850}, service_workers='block')
                page.set_default_timeout(60000);observe(page,report);boot(page,False,report,1100)
                report['checks']['decoy'] = page.evaluate(DECOY_CHECK)
                for sample in report['checks']['decoy']['samples']:
                    png = sample['pixels'].pop('png');name='decoy-'+str(sample['fraction'])+'.png'
                    (folder/name).write_bytes(base64.b64decode(png.split(',',1)[1]));sample['pixels']['image']=name
                report['checks']['withdrawal'] = page.evaluate(RETURN_CHECK)
                page.close();print('Readonly, decoy deformation and visual-only withdrawal PASS',flush=True)
            native(browser,report,args.baseline)
            browser.close()
        assert not report['errors'] and not report.get('failedRequests'), report
        report['ok'] = True
    except Exception as error:
        report['failure'] = str(error)
        raise
    finally:
        report['sourceAfter'] = manifest()
        report['sourceStable'] = report['sourceBefore']==report['sourceAfter']
        (folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')


if __name__=='__main__': main()
