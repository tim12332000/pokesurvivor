"""Foot-reservoir causality through production Shadow Possession.

Matched-clock and lifecycle arenas are controlled. Paired recordings use native
RAF and keyboard input; they do not claim natural growth or phone-hardware QA.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from playwright.sync_api import sync_playwright
import test_shikamaru as base
import test_shikamaru_living_shadow as living
import test_shikamaru_ready_shadow as ready

BASELINE = 'dc50aeee'
OUT = base.ROOT / '.omx/state/shikamaru-shadow-causality/qa'
RUNTIME = ['.omx/naruto-shikamaru.js', 'art-review/shikamaru/reference-shadow-geometry.js']
SOURCES = RUNTIME + ['.omx/digimon.html', '.omx/naruto-skills.js', '.omx/naruto.js']
base.URL = os.environ.get('SHIKAMARU_URL', 'http://127.0.0.1:8350/.omx/digimon.html?lang=zh-TW&layout=wide')


def manifest():
    return {name: hashlib.sha256((base.ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def baseline_routes(page, report):
    report['baselineRuntime'] = {}
    for name in RUNTIME:
        data = subprocess.check_output(['git', 'show', BASELINE+':'+name], cwd=base.ROOT)
        report['baselineRuntime'][name] = hashlib.sha256(data).hexdigest()
        def handler(payload):
            return lambda route: route.fulfill(body=payload, content_type='application/javascript')
        page.route('**/'+name+'*', handler(data))


SETUP = r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry;
 A.causeBuild=(rank=1)=>{const ledger=A.livingBuild(rank);G.Spawner.update=()=>{};return ledger};
 A.causePixels=(direction={x:1,y:0})=>{
  const projection=S.projectionFor(p),canvas=document.createElement('canvas');canvas.width=canvas.height=256;
  const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.translate(128-p.x,128-p.y);R.drawProjection(ctx,projection);
  const rgba=ctx.getImageData(0,0,256,256).data,mask=[];let count=0,extent=-Infinity,left=256,top=256,right=-1,bottom=-1;
  for(let y=0;y<256;y++)for(let x=0;x<256;x++){const on=rgba[(y*256+x)*4+3]>127?1:0;mask.push(on);if(on){count++;extent=Math.max(extent,(x+.5-128)*direction.x+(y+.5-128)*direction.y);left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y)}}
  // A white diagnostic backdrop is painted after measuring transparent alpha.
  ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.globalCompositeOperation='destination-over';ctx.fillStyle='#fff';ctx.fillRect(0,0,256,256);ctx.restore();
  return {png:canvas.toDataURL(),mask,count,extent,bounds:count?[left,top,right,bottom]:null,bodyKey:projection.body.key,kind:projection.body.kind,matrix:{...projection.matrix},flow:projection.flow,outline:projection.readyOutline||null,footInside:R.contains(projection,p.x,p.y)};
 };
 A.causeFeeds=()=>JSON.parse(JSON.stringify(S.stateFor(p)?.reservoir?.feeds||[]));
 A.causeSnapshot=()=>JSON.stringify({physics:A.livingSnapshot(),reservoir:S.stateFor(p)?.reservoir,projection:S.projectionFor(p)?.readyOutline});
 A.causeDiff=(a,b)=>a.mask.reduce((n,v,i)=>n+(v!==b.mask[i]),0);
 A.causeProbe=(point,age,casting)=>{
  A.causeBuild();let cast=null;
  if(casting){A.spawn(point[0],point[1]);cast=A.livingCast()}
  else{A.resume();try{G.Combat.tick(.000001,p,0)}finally{A.pause()}}
  A.livingAdvance(age);const feeds=A.causeFeeds(),feed=feeds.find(f=>f.sourceCast===cast?.serial)||feeds[0],n=Math.hypot(feed?.dx??point[0],feed?.dy??point[1])||1;
  const dir={x:(feed?.dx??point[0])/n,y:(feed?.dy??point[1])/n};
  const s=S.stateFor(p);return {clock:s.clock,phase:s.material.phase,owner:{x:p.x,y:p.y},pixels:A.causePixels(dir),feeds,dir,cast:cast?{serial:cast.serial,age:cast.age,release:cast.spec.release,segments:cast.chain.segments.map(g=>({contact:g.contact,travelled:g.travelled,total:g.totalLength,sourceJoin:g.sourceJoin,rootExit:g.rootExit,polygon:g.polygon,points:g.grownPoints}))}:null};
 };
 A.causeBoundaryDistance=(outline,point)=>Math.min(...outline.map((a,i)=>{const b=outline[(i+1)%outline.length];return S.segmentDistance(point.x,point.y,a.x,a.y,b.x,b.y)}));
}'''


MATCHED = r'''baseline => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry,out={directions:[]};
 for(const [name,point]of [['right',[160,0]],['left',[-160,0]],['down',[0,160]]]){
  const record={name,point,samples:[]};
  for(const age of [.08,.15,.28,.65]){
   const idle=A.causeProbe(point,age,false),cast=A.causeProbe(point,age,true);
   A.assert(Math.abs(idle.clock-cast.clock)<1e-9&&idle.phase===cast.phase,'counterfactual clocks differ');
   A.assert(idle.owner.x===cast.owner.x&&idle.owner.y===cast.owner.y&&idle.pixels.bodyKey===cast.pixels.bodyKey,'counterfactual source or anchor differs');
   // Compare the idle foot along the active feed direction, not a fixed axis.
   const idleAgain=A.causeProbe(point,age,false);idle.pixels.extent=A.causePixels(cast.dir).extent;
   const delta=A.causeDiff(idle.pixels,cast.pixels),extentGain=cast.pixels.extent-idle.pixels.extent;
   if(!baseline){A.assert(cast.pixels.footInside&&cast.pixels.count>300,'attack consumed or detached foot core');
    if(age<cast.cast.release)A.assert(delta>8,'pre-release base remains an unrelated idle sticker '+name+'/'+age);
    if(age===.28)A.assert(extentGain>2,'growing attack did not stretch its own foot lobe '+name+': '+extentGain);
    A.assert(cast.feeds.some(f=>f.sourceCast===cast.cast.serial),'foot has no actual cast-owned material feed');
   }
   delete idle.pixels.mask;delete cast.pixels.mask;delete idleAgain.pixels.mask;
   record.samples.push({age,delta,extentGain,idle,cast});
  }out.directions.push(record);
 }
 return out;
}'''


CONTROL = r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry,out={cleanup:[],joins:[]};
 A.causeBuild();const near=A.spawn(20,0),hits=A.watch(near),b=A.livingCast();
 A.livingAdvance(b.spec.release-.02);A.assert(!S.held(near)&&!hits.length,'gathering base attacked before true release');out.preRelease=true;
 const before=A.causeSnapshot(),canvas=document.createElement('canvas');canvas.width=canvas.height=500;const ctx=canvas.getContext('2d');ctx.translate(250,250);
 for(let i=0;i<40;i++){G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);S.projectionFor(p)}
 A.assert(before===A.causeSnapshot(),'render/query advanced feed or simulation');S.update(5);A.assert(before===A.causeSnapshot(),'paused feed advanced');out.readOnly=true;out.pause=true;
 A.causeBuild(3);const es=[[150,0],[-150,20],[20,150]].map(([x,y])=>A.spawn(x,y)),cast=A.livingCast();A.livingWait(()=>es.every(S.held));
 const projection=S.projectionFor(p),outline=projection.readyOutline;
 A.assert(outline?.length>3,'ready base does not expose the actual deformed outline');
 for(const g of cast.chain.segments){const point=g.sourceJoin||g.rootExit;
  A.assert(point&&Number.isFinite(point.x)&&Number.isFinite(point.y),'connector has no deformed-base boundary join');
  const distance=Math.hypot(point.x-p.x,point.y-p.y),boundary=A.causeBoundaryDistance(outline,point);
  A.assert(distance>8&&boundary<2,'connector source is only a foot-center overlap');
  A.assert(R.contains(projection,point.x,point.y)||boundary<.6,'connector source left the base');
  out.joins.push({point,distance,boundary});
 }
 for(const reason of ['clear','death','unlearn','world','epoch']){
  A.causeBuild();const e=A.spawn(140,20),h=A.watch(e);A.livingCast();A.livingWait(()=>S.held(e));const world=G.World,count=h.length;
  if(reason==='clear')S.clear(p);if(reason==='death')p.dead=true;if(reason==='unlearn')p.moves=[];if(reason==='world')G.World={...world};if(reason==='epoch')G.CombatPulse.beginRun();
  try{A.livingAdvance(.7);A.assert(!S.held(e)&&!S.casts.some(c=>c.owner===p)&&h.length===count,'cancelled causal feed retained damage/control '+reason);A.assert(!(S.stateFor(p)?.reservoir?.feeds||[]).length,'cancelled cast retained a base feed '+reason)}finally{p.dead=false;G.World=world}out.cleanup.push(reason);
 }
 // Reuse the established real-alpha, wall, two-target callbacks and clone checks.
 return out;
}'''


NATIVE = r'''({rank,point,moving}) => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,built=A.causeBuild(rank);
 const targets=(rank===1?[point]:[[150,0],[-150,20],[20,150]]).map(([x,y])=>A.spawn(x,y));
 for(const e of targets)e.hp=e.maxHp=Math.max(20,S.profile(p,p.moves[0]).damage*2.3);
 p.target=targets[0];
 const Q=window.CauseShadow={frames:[],samples:[],seen:new Set(),first:null,joined:null,ledger:built.ledger,moving,last:-1};
 const original=G.Combat.drawAirFields;
 G.Combat.drawAirFields=function(ctx){const result=original.call(this,ctx),s=S.stateFor(p);Q.first??=S.casts.find(c=>c.owner===p&&c.kind==='shadow'&&c.chain);const b=Q.first;if(!b||!s)return result;
  const feeds=A.causeFeeds(),feed=feeds.find(f=>f.sourceCast===b.serial)||feeds[0],projection=S.projectionFor(p),allHeld=targets.every(S.held),keys=[];
  if(allHeld)Q.joined??=s.clock;
  const f=b.age/b.spec.release;
  if(f>.04&&f<.4)keys.push('gather-early');if(f>=.4&&f<.7)keys.push('gather-mid');if(f>=.7&&f<1)keys.push('gather-late');
  if(b.age>b.spec.release&&b.chain.segments.some(g=>!g.contact&&g.travelled>35&&g.travelled<g.totalLength))keys.push('growing');
  if(allHeld)keys.push('joined');if(Q.joined!==null&&s.clock-Q.joined>.13&&allHeld)keys.push('hold-feed');
  const returning=feeds.find(f=>f.stage==='return');
  if(s.shadowReturns?.length){keys.push('return-far');if(returning&&returning.reach<55)keys.push('return-near')}
  if(Q.joined!==null&&!S.casts.includes(b)&&!s.shadowReturns?.length&&!feeds.length)keys.push('restored');
  const state={clock:s.clock,owner:{x:p.x,y:p.y},bodyKey:projection.body.key,outline:projection.readyOutline||null,feeds,cast:{serial:b.serial,age:b.age,release:b.spec.release,segments:b.chain.segments.map(g=>({contact:g.contact,travelled:g.travelled,total:g.totalLength,points:g.grownPoints,polygon:g.polygon,sourceJoin:g.sourceJoin,rootExit:g.rootExit}))},returns:s.shadowReturns?.map(t=>({remaining:t.remainingLength,points:t.remainingPoints})),footInside:G.ShikamaruReferenceGeometry.contains(projection,p.x,p.y),held:targets.map(S.held),targets:targets.map(e=>({id:e.id,x:e.x,y:e.y,dead:e.dead}))};
  if(s.clock-Q.last>.06){Q.last=s.clock;Q.samples.push(state)}
  for(const key of keys)if(!Q.seen.has(key)){Q.seen.add(key);const pixels=A.causePixels();delete pixels.mask;queueMicrotask(()=>Q.frames.push({...JSON.parse(JSON.stringify(state)),key,foot:pixels,png:ctx.canvas.toDataURL()}))}
  return result;
 };A.resume();
}'''


def observe(page, report):
    page.on('pageerror', lambda e: report['errors'].append({'message':str(e),'stack':e.stack}))
    page.on('requestfailed', lambda r: report['failedRequests'].append({'url':r.url,'failure':r.failure}))


def boot(page, baseline, report, mobile=False):
    if baseline: baseline_routes(page, report)
    old=base.URL
    if mobile: base.URL=old.replace('&layout=wide','')
    try: base.boot(page)
    finally: base.URL=old
    page.evaluate(living.SETUP);page.evaluate(ready.SETUP);page.evaluate(SETUP)
    page.evaluate('window.CauseWarm=Acceptance.spawn(1000,1000)')
    page.wait_for_function('!!G.ShikamaruReferenceGeometry.bodyFor(CauseWarm)')


def png(path, payload):
    path.write_bytes(base64.b64decode(payload.split(',',1)[1]))


def save_matched(folder, data):
    for direction in data['directions']:
        target=folder/direction['name'];target.mkdir(exist_ok=True)
        for sample in direction['samples']:
            for kind in ['idle','cast']:
                pixels=sample[kind]['pixels'];name=f'{sample["age"]}-{kind}.png';png(target/name,pixels.pop('png'));pixels['image']=name


def native(browser, report, baseline, folder):
    scenes=[('right',1,[160,0],False),('left',1,[-160,0],False),('down',1,[0,160],False),('multi-moving',3,[150,0],True)]
    for label,width,height in [('desktop',1100,850),('mobile390',390,844)]:
        for name,rank,point,moving in scenes:
            target=folder/label/name;target.mkdir(parents=True,exist_ok=True)
            context=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<600,has_touch=width<600,service_workers='block',record_video_dir=str(target/'raw'),record_video_size={'width':width,'height':height})
            context.set_default_timeout(60000);page=context.new_page();observe(page,report);boot(page,baseline,report,width<600);page.evaluate(NATIVE,{'rank':rank,'point':point,'moving':moving})
            required=['gather-early','gather-mid','gather-late','growing','joined','hold-feed','restored']
            if not baseline: required += ['return-far','return-near']
            held=False;started=time.monotonic()
            while time.monotonic()-started<14:
                seen=page.evaluate('[...CauseShadow.seen]')
                if all(key in seen for key in required): break
                if moving and 'hold-feed' in seen and not held: page.keyboard.down('KeyD');held=True
                page.wait_for_timeout(35)
            if held: page.keyboard.up('KeyD')
            page.evaluate('Acceptance.pause()')
            data=page.evaluate('({frames:CauseShadow.frames,samples:CauseShadow.samples,seen:[...CauseShadow.seen],ledger:CauseShadow.ledger})')
            missing=[key for key in required if key not in data['seen']]
            assert not missing, {'viewport':label,'scene':name,'missing':missing,'seen':data['seen']}
            if not baseline:
                assert all(s['footInside'] for s in data['samples']), 'causal deformation consumed the persistent core'
                assert any(s['feeds'] for s in data['samples']), 'native cast did not feed its base'
                if moving: assert len({(s['owner']['x'],s['owner']['y']) for s in data['samples']})>2,'moving return actor did not move'
            for frame in data['frames']:
                png(target/(frame['key']+'.png'),frame.pop('png'));png(target/(frame['key']+'-foot.png'),frame['foot'].pop('png'))
            report.setdefault('native',{}).setdefault(label,{})[name]=data
            video=page.video;context.close();video.save_as(str(target/'native-cycle.webm'));video.delete();print(label,name,'causal native PASS',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',action='store_true');parser.add_argument('--checks-only',action='store_true');parser.add_argument('--capture-only',action='store_true');args=parser.parse_args()
    folder=OUT/('baseline' if args.baseline else 'current');folder.mkdir(parents=True,exist_ok=True)
    report={'baseline':args.baseline,'controlled':True,'url':base.URL,'sourceBefore':manifest(),'policy':'Matched-clock controlled foot-only probes and fixed-seed native RAF/keyboard scenes. No claim of natural growth or physical phones.','errors':[],'failedRequests':[],'checks':{}}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
            if not args.capture_only:
                page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block');page.set_default_timeout(60000);observe(page,report);boot(page,args.baseline,report)
                report['checks']['matched']=page.evaluate(MATCHED,args.baseline);save_matched(folder,report['checks']['matched']);print('Matched-clock foot-only causality PASS',flush=True)
                if not args.baseline:
                    report['checks']['causalControl']=page.evaluate(CONTROL)
                    report['checks']['control']=page.evaluate(living.CONTROL);print('True contact, join, pause, lifecycle and callbacks PASS',flush=True)
                page.close()
            if not args.checks_only: native(browser,report,args.baseline,folder)
            browser.close()
        assert not report['errors'] and not report['failedRequests'],{'errors':report['errors'],'failedRequests':report['failedRequests']};report['ok']=True
    except Exception as error:
        report['failure']=str(error);raise
    finally:
        report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')


if __name__=='__main__': main()
