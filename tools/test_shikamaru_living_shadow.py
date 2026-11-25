"""Focused Shadow Possession geometry, foot-flow and paired native evidence.

The fixed-seed arenas and legal upgrade cards are controlled fixtures. Native
recordings use the production RAF and real keyboard input, not natural growth.
Baseline routes only the two changed runtimes from fb7924e6.
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

BASELINE = 'fb7924e6'
OUT = base.ROOT / '.omx/state/shikamaru-living-shadow/qa'
RUNTIME = ['.omx/naruto-shikamaru.js', 'art-review/shikamaru/reference-shadow-geometry.js']
SOURCES = RUNTIME + ['.omx/digimon.html', '.omx/naruto-skills.js', '.omx/jujutsu-growth.js', '.omx/naruto.js']
base.URL = os.environ.get('SHIKAMARU_URL', 'http://127.0.0.1:8350/.omx/digimon.html?lang=zh-TW&layout=wide')


def manifest():
    return {name: hashlib.sha256((base.ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def baseline_routes(page, report):
    def handler(payload):
        def serve(route):
            route.fulfill(body=payload, content_type='application/javascript')
        return serve
    report['baselineRuntime'] = {}
    for name in RUNTIME:
        payload = subprocess.check_output(['git', 'show', BASELINE+':'+name], cwd=base.ROOT)
        report['baselineRuntime'][name] = hashlib.sha256(payload).hexdigest()
        page.route('**/'+name+'*', handler(payload))


SETUP = r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry,ID='naruto-shikamaru';
 A.livingBuild=(rank=1)=>{A.reset();G.World.reset(93517021);G.World.setBiome(0,true);p.level=rank;p.statsTaken={};p.moves=[G.Moves.instance(ID)];p.anim.loop('Idle');p.anim.dir=2;p.aim=0;
  const ledger=[];for(let i=1;i<rank;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+ID);A.assert(c&&c.apply(p)!==false,'true shadow rank card unavailable');ledger.push(c.key)}return {m:p.moves[0],ledger};};
 A.livingStep=(dt=.01)=>{A.resume();try{G.Combat.updateFields(dt);p.anim.update(dt)}finally{A.pause()}};
 A.livingAdvance=seconds=>{let left=seconds;while(left>1e-8){const dt=Math.min(.01,left);A.livingStep(dt);left-=dt}};
 A.livingCast=(actor=p)=>{A.resume();try{A.assert(S.cast(actor,actor.moves.find(m=>m.id===ID)),'actual Shadow Possession cast rejected')}finally{A.pause()}return S.casts.findLast(b=>b.owner===actor&&b.kind==='shadow'&&b.chain)};
 A.livingWait=(condition,limit=2)=>{for(let i=0;i<limit*100&&!condition();i++)A.livingStep();A.assert(condition(),'shadow fixture did not reach actual alpha capture')};
 A.livingPixels=(kind='all')=>{const canvas=document.createElement('canvas');canvas.width=512;canvas.height=440;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.translate(256-p.x,180-p.y);
  const projection=S.projectionFor(p);if(kind==='foot')R.drawProjection(ctx,projection);else G.Combat.drawGroundFields(ctx);
  const rgba=ctx.getImageData(0,0,512,440).data,mask=[],roi=kind==='mid'?[301,90,371,290]:[0,0,512,440];let count=0,opaque=0,dark=0,hash=2166136261;
  for(let y=roi[1];y<roi[3];y++)for(let x=roi[0];x<roi[2];x++){const i=(y*512+x)*4,on=rgba[i+3]>127?1:0;mask.push(on);hash=Math.imul(hash^on,16777619)>>>0;count+=on;if(rgba[i+3]>240){opaque++;if(Math.max(rgba[i],rgba[i+1],rgba[i+2])<16)dark++;}}
  return {png:canvas.toDataURL(),mask,count,opaque,dark,hash:hash.toString(16),bodyKey:projection?.body.key,flow:projection?.flow??null,matrix:projection?.matrix};};
 A.livingDiff=(a,b)=>a.mask.reduce((n,v,i)=>n+(v!==b.mask[i]),0);
 A.livingSnapshot=()=>{const s=S.stateFor(p);return JSON.stringify({clock:s?.clock,material:s?.material,hp:p.hp,stats:S.stats(p),casts:S.casts.map(b=>({serial:b.serial,age:b.age,emitted:b.emitted,kunai:b.kunai?.map(k=>({x:k.x,y:k.y,done:k.done})),segments:b.chain?.segments.map(g=>({points:g.grownPoints,polygon:g.polygon,flow:g.flow,contact:g.contact}))})),last:s?.lastChain?.chain?.segments.map(g=>({points:g.grownPoints,polygon:g.polygon,flow:g.flow,contact:g.contact})),returns:s?.shadowReturns?.map(r=>({age:r.age,remaining:r.remainingLength})),leases:[...S.leases].filter(([,l])=>l.cast.owner===p).map(([e,l])=>({id:e.id,x:e.x,y:e.y,hp:e.hp,until:l.until}))})};
 A.livingSample=b=>({clock:S.stateFor(p)?.clock,material:S.stateFor(p)?.material,owner:{x:p.x,y:p.y},foot:A.livingPixels('foot'),mid:A.livingPixels('mid'),segments:b?.chain.segments.map(g=>({path:g.path.map(p=>({...p})),travelled:g.travelled,points:g.grownPoints.map(p=>({...p})),polygon:g.polygon.map(p=>({...p})),flow:g.flow?JSON.parse(JSON.stringify(g.flow)):null,contact:g.contact}))});
}'''


FLOW = r'''baseline => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry,out={idle:[],held:[]};
 A.livingBuild();A.resume();try{G.Combat.tick(.01,p,0)}finally{A.pause()}
 for(let i=0;i<3;i++){A.livingAdvance(.23);out.idle.push(A.livingSample())}
 const built=A.livingBuild(),enemy=A.spawn(170,40),b=A.livingCast();A.livingWait(()=>S.held(enemy));A.livingAdvance(Math.max(0,1.1-b.age));
 const origin={x:p.x,y:p.y},target={x:enemy.x,y:enemy.y};
 for(let i=0;i<3;i++){if(i)A.livingAdvance(.22);A.assert(S.held(enemy),'control expired before temporal held samples');out.held.push(A.livingSample(b));A.assert(p.x===origin.x&&p.y===origin.y&&enemy.x===target.x&&enemy.y===target.y,'stationary flow fixture drifted');
  const g=b.chain.segments[0],tip=g.grownPoints.at(-1);A.assert(R.contains(S.projectionFor(enemy),tip.x,tip.y),'held connector endpoint left actual current enemy shadow alpha');}
 const diffs=samples=>({foot:[A.livingDiff(samples[0].foot,samples[1].foot),A.livingDiff(samples[1].foot,samples[2].foot)],mid:[A.livingDiff(samples[0].mid,samples[1].mid),A.livingDiff(samples[1].mid,samples[2].mid)]});
 out.idleDiff=diffs(out.idle);out.heldDiff=diffs(out.held);out.ledger=built.ledger;
 out.spineDrift=out.held.slice(1).map(s=>{const a=out.held[0].segments[0].points,z=s.segments[0].points;return {countEqual:a.length===z.length,interior:Math.max(0,...a.slice(1,-1).map((p,i)=>Math.hypot(p.x-(z[i+1]?.x??1e6),p.y-(z[i+1]?.y??1e6)))),tip:Math.hypot(a.at(-1).x-z.at(-1).x,a.at(-1).y-z.at(-1).y)}});window.LivingFlowProof=out;
 out.transportError=out.held.map(s=>{const g=s.segments[0],path=[{...g.path[0]}];let remaining=g.travelled;for(let i=1;i<g.path.length;i++){const a=g.path[i-1],b=g.path[i],d=Math.hypot(b.x-a.x,b.y-a.y);if(remaining>=d){path.push({...b});remaining-=d}else{if(remaining>0)path.push({x:a.x+(b.x-a.x)*remaining/d,y:a.y+(b.y-a.y)*remaining/d});break}}const points=g.points,start=path[0],end=path.at(-1),root=points[0],tip=points.at(-1),ox=end.x-start.x,oy=end.y-start.y,oldLength=Math.hypot(ox,oy),dx=tip.x-root.x,dy=tip.y-root.y,length=Math.hypot(dx,dy),scale=Math.min(1,length/oldLength),nx=-dy/length,ny=dx/length;A.assert(path.length===points.length,'flow inserted independent centreline points');return Math.max(0,...path.map((p,i)=>{const px=p.x-start.x,py=p.y-start.y,u=Math.max(0,Math.min(1,(px*ox+py*oy)/(oldLength*oldLength))),bend=(-oy*px+ox*py)/oldLength*scale;return Math.hypot(points[i].x-(root.x+dx*u+nx*bend),points[i].y-(root.y+dy*u+ny*bend))}));});
 A.assert(out.transportError.every(e=>e<1e-5),'material flow independently shook the stationary path instead of only transporting the endpoint chord');
 A.assert(out.held.map(s=>s.foot.bodyKey).every(k=>k===out.held[0].foot.bodyKey),'held footprint comparison changed the underlying body pose');
 if(!baseline){A.assert(out.idleDiff.foot.every(n=>n>8),'idle caster foot shadow has no real silhouette flow');A.assert(out.heldDiff.foot.every(n=>n>8),'held caster foot shadow only changed alpha or stayed static');A.assert(out.heldDiff.mid.every(n=>n>12),'connector contour stayed fixed while bound');
  for(const sample of out.held){const flow=sample.segments[0].flow;A.assert(flow?.stations?.length>3,'missing actual animated width stations');const widths=flow.stations.map(s=>s.left+s.right);A.assert(Math.max(...widths)>8&&Math.max(...widths)-Math.min(...widths)>3,'shadow is still a uniform thin cable');A.assert(sample.foot.opaque>100&&sample.foot.dark/sample.foot.opaque>.98,'foot shadow gained lit or coloured internal texture');}
 }
 const before=A.livingSnapshot(),projection=JSON.stringify(S.projectionFor(p)?.flow),canvas=document.createElement('canvas');canvas.width=600;canvas.height=500;const ctx=canvas.getContext('2d');ctx.translate(250,250);
 for(let i=0;i<40;i++){G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);S.projectionFor(p);S.projectionFor(enemy)}
 A.assert(before===A.livingSnapshot()&&projection===JSON.stringify(S.projectionFor(p)?.flow),'draw/query advanced flow, control or damage');S.update(3);A.assert(before===A.livingSnapshot(),'paused flow advanced');out.readOnly=true;out.pause=true;
 return out;
}'''


CONTROL = r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry,out={captures:[],cleanup:[],callbacks:[]};
 let built=A.livingBuild(3),es=[[150,0],[30,150],[-150,20]].map(([x,y])=>A.spawn(x,y)),outside=A.spawn(700,0),hits=es.map(A.watch),outsideHits=A.watch(outside),b=A.livingCast(),seen=new Set();
 for(let i=0;i<240&&!es.every(S.held);i++){A.livingStep();for(const g of b.chain.segments)if(g.contact&&!seen.has(g.target.id)){seen.add(g.target.id);const point=g.liveContactPoint||g.contactPoint;A.assert(R.contains(S.projectionFor(g.target),point.x,point.y),'capture without actual warped alpha contact');out.captures.push({target:g.target.id,point,flow:S.projectionFor(g.target)?.flow})}}
 A.assert(es.every(S.held)&&seen.size===3,'rank3 failed three independent captures');A.livingAdvance(.65);A.assert(hits.every(h=>h.some(e=>e.loss>0))&&!outsideHits.length,'native contacts missed or exceeded range');out.ledger=built.ledger;
 A.livingBuild();const blocked=A.spawn(150,0),blockedHits=A.watch(blocked);b=A.livingCast();G.World.projectilePathClear=(ax,ay,bx,by)=>Math.max(ax,bx)<65;A.livingAdvance(2);A.assert(!S.held(blocked)&&!blockedHits.length,'wide shadow captured through wall');out.wall=true;
 for(const reason of ['clear','death','world','unlearn','epoch']){A.livingBuild();const e=A.spawn(130,0),h=A.watch(e);b=A.livingCast();A.livingWait(()=>S.held(e));const world=G.World;
  if(reason==='clear')S.clear(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};if(reason==='unlearn')p.moves=[];if(reason==='epoch')G.CombatPulse.beginRun();
  const count=h.length;try{A.livingAdvance(.7);A.assert(!S.held(e)&&!S.casts.some(c=>c.owner===p)&&h.length===count,'flow retained control, cast or pending damage after '+reason)}finally{p.dead=false;G.World=world}out.cleanup.push(reason);}
 // Different live foot silhouettes can contact in either order, even at the
 // same position. Cancel the first real callback and count both targets.
 for(const mode of ['hurt','onDealt']){A.livingBuild(3);es=[A.spawn(120,0),A.spawn(120,0)];hits=es.map(A.watch);const dealt=p.onDealt;if(mode==='hurt'){for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const result=hurt.apply(this,args);S.clear(p);return result}}}else p.onDealt=()=>S.clear(p);
  try{A.livingCast();A.livingAdvance(2);A.assert(hits.reduce((n,h)=>n+h.length,0)===1&&!S.casts.some(c=>c.owner===p),'same-wave cancellation leaked a later target '+mode+': '+hits.map(h=>h.length))}finally{p.onDealt=dealt}out.callbacks.push(mode);}
 for(const clone of [false,true]){A.livingBuild();const actor=clone?G.SelfClones.summon(p):p;actor.x=actor.y=0;const e=A.spawn(140,30),start={x:e.x,y:e.y};A.livingCast(actor);A.livingWait(()=>S.held(e));
  for(let i=0;i<15;i++){actor.x+=2;actor.y+=.5;A.resume();try{G.Combat.tick(.01,actor,0);e.update(.01,p);G.Combat.updateFields(.01)}finally{A.pause()}A.assert(S.held(e)&&e.x===start.x&&e.y===start.y,'flow dragged/released a bound enemy '+clone)}
  if(clone){S.clear(p);A.assert(S.held(e),'parent clear removed clone-owned shadow');actor.dead=true;A.livingAdvance(.01);A.assert(!S.held(e),'dead clone retained flow capture')}else S.clear(actor);
 }out.stationaryAndClone=true;return out;
}'''


NATIVE = r'''({rank,moving}) => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry,built=A.livingBuild(rank);G.Spawner.update=()=>{};
 const targets=(rank===1?[[170,40]]:[[150,0],[30,150],[-150,20]]).map(([x,y])=>A.spawn(x,y));p.target=targets[0];
 const Q=window.LivingShadow={rank,moving,ledger:built.ledger,frames:[],samples:[],seen:new Set(),first:null,joined:null,last:-1,heldBody:null,heldSamples:0,lastHeld:-1};
 const original=G.Combat.drawAirFields;
 G.Combat.drawAirFields=function(ctx){const result=original.call(this,ctx),s=S.stateFor(p);Q.first??=S.casts.find(b=>b.owner===p&&b.kind==='shadow'&&b.chain);const b=Q.first;if(!b)return result;
  const held=targets.filter(S.held),allHeld=held.length===targets.length;Q.joined??=allHeld?s.clock:null;
  const segments=b.chain.segments,state={clock:s.clock,owner:{x:p.x,y:p.y},targets:targets.map(e=>({id:e.id,x:e.x,y:e.y,held:S.held(e)})),bodyKey:S.projectionFor(p)?.body.key,material:s.material,projectionFlow:S.projectionFor(p)?.flow??null,segments:segments.map(g=>({points:g.grownPoints,polygon:g.polygon,flow:g.flow??null,contact:g.contact}))},keys=[];
  if(b.age<b.spec.release)keys.push('source');if(segments.some(g=>!g.contact&&g.travelled/g.totalLength>.2&&g.travelled/g.totalLength<.8))keys.push('extend');if(allHeld)keys.push('joined');
  if(allHeld&&['blast','finish'].includes(s.plan?.phase)&&Q.heldSamples<3){const bodyKey=state.bodyKey;Q.heldBody??=bodyKey;if(bodyKey===Q.heldBody&&(Q.lastHeld<0||s.clock-Q.lastHeld>=.18)){keys.push('held-'+(++Q.heldSamples));Q.lastHeld=s.clock}}
  if(Q.joined!=null&&!held.length)keys.push('released');if(s.clock-Q.last>.1){Q.samples.push({clock:s.clock,owner:state.owner,targets:state.targets,bodyKey:state.bodyKey,held:held.length});Q.last=s.clock}
  for(const key of keys)if(!Q.seen.has(key)){Q.seen.add(key);const foot=A.livingPixels('foot'),mid=A.livingPixels('mid');delete foot.mask;delete mid.mask;queueMicrotask(()=>Q.frames.push({...JSON.parse(JSON.stringify(state)),key,foot,mid,png:ctx.canvas.toDataURL()}))}return result;
 };A.resume();
}'''


def observe(page, report):
    page.on('pageerror', lambda e: report['errors'].append({'message':str(e),'stack':e.stack}))
    page.on('requestfailed', lambda r: report['failedRequests'].append({'url':r.url,'failure':r.failure}))


def boot(page, baseline, report, mobile=False):
    if baseline:
        baseline_routes(page, report)
    saved=base.URL
    if mobile:
        base.URL=saved.replace('&layout=wide','')
    try:
        base.boot(page)
    finally:
        base.URL=saved
    page.evaluate('window.LivingWarm=Acceptance.spawn(1000,1000)')
    page.wait_for_function('!!G.ShikamaruReferenceGeometry.bodyFor(LivingWarm)')
    page.evaluate(SETUP)


def save_png(folder, name, png):
    (folder/name).write_bytes(base64.b64decode(png.split(',',1)[1]))


def save_flow(folder, data):
    for kind in ['idle','held']:
        for i,sample in enumerate(data[kind]):
            for region in ['foot','mid']:
                pixels=sample[region];save_png(folder,f'{kind}-{i+1}-{region}.png',pixels.pop('png'));pixels.pop('mask',None)


def native(browser, report, baseline, folder):
    for label,width,height in [('desktop',1100,850),('mobile390',390,844)]:
        for rank,moving in [(1,False),(3,False),(1,True)]:
            scene=f'rank{rank}-'+('moving' if moving else 'stationary');target=folder/label/scene;target.mkdir(parents=True,exist_ok=True)
            context=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<600,has_touch=width<600,service_workers='block',record_video_dir=str(target/'raw'),record_video_size={'width':width,'height':height})
            context.set_default_timeout(60000);page=context.new_page();observe(page,report);boot(page,baseline,report,width<600);page.evaluate(NATIVE,{'rank':rank,'moving':moving})
            held=None;started=time.monotonic();step=0;required=['source','extend','joined','released']
            if not moving: required += ['held-1','held-2','held-3']
            while time.monotonic()-started<12:
                seen=page.evaluate('[...LivingShadow.seen]')
                if all(key in seen for key in required):break
                if moving:
                    key=['KeyD','KeyS','KeyA','KeyW'][step%4]
                    if held:page.keyboard.up(held)
                    page.keyboard.down(key);held=key;step+=1
                page.wait_for_timeout(120)
            if held:page.keyboard.up(held)
            page.evaluate('Acceptance.pause()');data=page.evaluate('({frames:LivingShadow.frames,samples:LivingShadow.samples,seen:[...LivingShadow.seen],ledger:LivingShadow.ledger})')
            missing=[key for key in required if key not in data['seen']];assert not missing,{'viewport':label,'scene':scene,'missing':missing}
            for frame in data['frames']:
                save_png(target,frame['key']+'.png',frame.pop('png'))
                for region in ['foot','mid']:save_png(target,frame['key']+'-'+region+'.png',frame[region].pop('png'))
            if not moving:
                frames=[next(f for f in data['frames'] if f['key']==key) for key in ['held-1','held-2','held-3']]
                assert len({json.dumps(f['owner'],sort_keys=True) for f in frames})==1,'stationary native actor moved'
                assert len({json.dumps(f['targets'],sort_keys=True) for f in frames})==1,'stationary native targets moved'
                assert len({f['bodyKey'] for f in frames})==1,'native temporal proof changed body pose'
                if not baseline:
                    assert len({f['foot']['hash'] for f in frames})>1,'native foot silhouette stayed fixed'
                    assert len({f['mid']['hash'] for f in frames})>1,'native connector contour stayed fixed'
            else:
                assert len({(s['owner']['x'],s['owner']['y']) for s in data['samples']})>2,'native keyboard movement did not reach the caster'
            report.setdefault('native',{}).setdefault(label,{})[scene]=data
            video=page.video;context.close();video.save_as(str(target/'native-cycle.webm'));video.delete();print(label,scene,'native PASS',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',action='store_true');parser.add_argument('--capture-only',action='store_true');parser.add_argument('--checks-only',action='store_true');args=parser.parse_args()
    folder=OUT/('baseline' if args.baseline else 'current');folder.mkdir(parents=True,exist_ok=True)
    report={'baseline':args.baseline,'controlled':True,'policy':'Solo Shadow Possession only; fixed seed and actual upgrade cards; native RAF/keyboard captures are controlled, not natural growth.','url':base.URL,'sourceBefore':manifest(),'errors':[],'failedRequests':[],'checks':{}}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
            if not args.capture_only:
                page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block');page.set_default_timeout(60000);observe(page,report);boot(page,args.baseline,report)
                report['checks']['flow']=page.evaluate(FLOW,args.baseline);save_flow(folder,report['checks']['flow']);print('Stationary foot and connector samples PASS',flush=True)
                if not args.baseline:report['checks']['control']=page.evaluate(CONTROL);print('Capture, wall, lifecycle and ownership PASS',flush=True)
                page.close()
            if not args.checks_only:native(browser,report,args.baseline,folder)
            browser.close()
        assert not report['errors'] and not report['failedRequests'],{'errors':report['errors'],'failedRequests':report['failedRequests']}
        report['ok']=True
    except Exception as error:
        report['failure']=str(error)
        try:
            report['flowFailureProof']=page.evaluate('''()=>window.LivingFlowProof?{idleDiff:LivingFlowProof.idleDiff,heldDiff:LivingFlowProof.heldDiff,spineDrift:LivingFlowProof.spineDrift,bodyKeys:LivingFlowProof.held.map(s=>s.foot.bodyKey)}:null''')
        except Exception:
            pass
        raise
    finally:
        report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')


if __name__=='__main__':main()
