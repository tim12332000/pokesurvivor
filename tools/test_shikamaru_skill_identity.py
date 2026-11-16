"""Focused Shikamaru skill identity: true contacts, read-only rendering and native phases."""
from __future__ import annotations
import base64,hashlib,json,os,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_shikamaru as base
import test_shikamaru_chain as chain

ROOT=base.ROOT
OUT=ROOT/'art-review/shikamaru/qa/skill-identity'

def manifest():
    names=['.omx/naruto-shikamaru.js','art-review/shikamaru-art.js','art-review/shikamaru-frames.json','.omx/naruto-skills.js','.omx/digimon.html']
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}

SETUP=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;
 A.identityBuild=()=>{A.chainBuild(3,0);p.level=5;const ledger=['up:naruto-shikamaru','up:naruto-shikamaru'];for(const id of ['naruto-shikamaru-sewing','naruto-shikamaru-strangle']){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='new:'+id);A.assert(c&&c.apply(p)!==false,'identity true skill card missing '+id);ledger.push('new:'+id)}return ledger};
 A.identityEffects=()=>S.effects.filter(e=>e.owner===p).map(e=>({kind:e.kind,x:e.x,y:e.y,age:e.age,life:e.life,castId:e.castId,moveId:e.moveId,pulseIndex:e.pulseIndex,sourceX:e.sourceX,sourceY:e.sourceY,targetId:e.targetId,bodyH:e.bodyH,lastPulseAt:e.lastPulseAt}));
 A.identityState=()=>({clock:S.stateFor(p)?.clock,stats:S.stats(p),effects:A.identityEffects(),casts:S.casts.filter(b=>b.owner===p).map(b=>({serial:b.serial,age:b.age,emitted:b.emitted,kind:b.kind,chain:b.chain?{current:b.chain.current,ended:b.chain.ended,segments:b.chain.segments.map(s=>({origin:s.origin,grownPoints:s.grownPoints,polygon:s.polygon,contact:s.contact,contactPoint:s.contactPoint}))}:null})),pose:S.activeFor(p)?{kind:S.activeFor(p).kind,phase:S.activeFor(p).phase,age:S.activeFor(p).age,key:G.ShikamaruArt.sample('cast',S.activeFor(p).age,G.Sprites.dirFromAngle(S.activeFor(p).aim||0),S.activeFor(p))?.key}:null});
 A.identityArena=()=>{const ledger=A.identityBuild(),es=[[180,0],[160,180],[-20,220]].map(([x,y])=>A.spawn(x,y));p.target=es[0];return {ledger,es}};
 A.identityTick=()=>{A.resume();try{G.Combat.tick(.01,p,0);S.update(.01);p.anim.update(.01)}finally{A.pause()}};
}"""


EVENTS=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,{ledger,es}=A.identityArena(),hits=[],objects=new WeakMap(),perKey=new Map(),snapshots=[],heights=[],armSamples=[];let nextObject=1;
 for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);if(hp>this.hp)hits.push({targetId:this.id,id:args[7],x:this.x,y:this.y,time:S.stateFor(p)?.clock,loss:hp-this.hp});return result}}
 const canvas=document.createElement('canvas');canvas.width=128;canvas.height=160;const ctx=canvas.getContext('2d');
 for(let i=0;i<450;i++){A.identityTick();const state=S.stateFor(p),effects=S.effects.filter(e=>e.owner===p),keys=new Set();
  for(const e of effects){A.assert(e.castId!=null&&e.moveId&&Number.isFinite(e.pulseIndex)&&Number.isFinite(e.sourceX)&&Number.isFinite(e.sourceY)&&e.targetId!=null,'effect missing true event metadata '+e.kind);const key=e.kind+':'+e.castId+':'+e.targetId;A.assert(!keys.has(key),'duplicate active effect actors '+key);keys.add(key);if(!objects.has(e))objects.set(e,nextObject++);if(!perKey.has(key))perKey.set(key,new Set());perKey.get(key).add(objects.get(e));
   if(e.pulseIndex>0){A.assert(Number.isFinite(e.lastPulseAt),'effect event timestamp is not finite '+key);const c=state.contacts.find(c=>c.cast===e.castId&&c.moveId===e.moveId&&c.targetId===e.targetId&&c.pulse===e.pulseIndex);A.assert(c,'visual pulse lacks real contact ledger '+key+'/'+e.pulseIndex);A.assert(hits.some(h=>h.targetId===e.targetId&&h.id===e.moveId&&Math.abs(h.x-c.x)<1e-6&&Math.abs(h.y-c.y)<1e-6),'visual contact bypassed real target hurt '+key);A.assert(Math.hypot(e.sourceX-c.x,e.sourceY-c.y)<1e-6,'ground/body effect source differs from true victim footprint '+key)}
  }
  for(const e of effects.filter(e=>e.kind==='strangle'&&e.pulseIndex>0))armSamples.push({clock:state.clock,castId:e.castId,targetId:e.targetId,pulseIndex:e.pulseIndex,age:e.age,sample:S.effectVisualFor(e)});
  if(i%5===0)snapshots.push(A.identityState());
  const spike=effects.find(e=>e.kind==='sewing'&&e.target===es[0]);if(spike){ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,128,160);ctx.translate(64-es[0].x,130-es[0].y);G.Combat.drawAirFields(ctx);const rgba=ctx.getImageData(0,0,128,160).data;let top=160;for(let y=0;y<160;y++)for(let x=20;x<108;x++)if(rgba[(y*128+x)*4+3]>20)top=Math.min(top,y);heights.push({clock:state.clock,castId:spike.castId,pulseIndex:spike.pulseIndex,age:spike.age,height:130-top,sample:S.effectVisualFor(spike)})}
 }
 const expected=['shadow','sewing','net','strangle'];for(const kind of expected)A.assert(snapshots.some(s=>s.effects.some(e=>e.kind===kind)),'normal cycle never rendered identity '+kind);
 const actorIds=[...perKey].map(([key,ids])=>({key,objects:[...ids]}));A.assert(actorIds.filter(x=>x.key.startsWith('sewing:')||x.key.startsWith('strangle:')).every(x=>x.objects.length===1),'pulse recreated a spike cluster or arm actor');
 const firstSewing=heights[0]?.castId,firstPulse=heights.find(h=>h.castId===firstSewing&&h.pulseIndex===1);A.assert(firstPulse&&firstPulse.height>35&&firstPulse.sample.height>.75,'true first sewing hurt did not coincide with visible tall spike');
 A.assert(heights.some(h=>h.castId===firstSewing&&h.pulseIndex===1&&h.height<firstPulse.height*.7),'sewing failed to retract between true pulses');
 A.assert(snapshots.some(s=>s.pose?.kind==='sewing'),'normal cycle swallowed the sewing body window');
 const arm=armSamples[0],firstByPulse=arm?armSamples.filter(a=>a.castId===arm.castId&&a.targetId===arm.targetId).filter((a,i,list)=>list.findIndex(b=>b.pulseIndex===a.pulseIndex)===i):[];A.assert(firstByPulse.length>=3&&firstByPulse.every(a=>a.sample.progress===1),'strangle rose again instead of retaining one full-height arm');A.assert(firstByPulse.every((a,i)=>!i||a.sample.close>firstByPulse[i-1].sample.close),'true strangle pulses did not progressively close the same hand');
 return {ledger,hits,contacts:S.stateFor(p).contacts,snapshots,actorIds,heights,armSamples,firstByPulse};
}"""

READ_ONLY=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.identityArena();for(let i=0;i<75;i++)A.identityTick();const before=JSON.stringify(A.identityState()),canvas=document.createElement('canvas');canvas.width=canvas.height=500;const ctx=canvas.getContext('2d');ctx.translate(250,250);
 for(let i=0;i<100;i++){G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);for(const e of S.effects)S.effectVisualFor(e)}
 const after=JSON.stringify(A.identityState());A.assert(before===after,'render/query advanced skill effect or damage');const paused=JSON.stringify(A.identityState());S.update(.5);A.assert(paused===JSON.stringify(A.identityState()),'paused update advanced pending cues or effects');return {readOnly:true,pause:true,state:A.identityState()};
}"""

CLEANUP=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const reason of ['clear','death','world']){A.identityArena();for(let i=0;i<75;i++)A.identityTick();A.assert(S.effects.some(e=>e.owner===p)||S.casts.some(b=>b.owner===p),'cleanup fixture has no effects/pending cast');const world=G.World;if(reason==='clear')S.clear(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};A.resume();try{S.update(.01)}finally{A.pause();p.dead=false;G.World=world}A.assert(!S.effects.some(e=>e.owner===p)&&!S.casts.some(b=>b.owner===p)&&!S.activeFor(p),'cleanup left pending actor/body hint '+reason);out.push(reason)}return out;
}"""




CALLBACK_CANCEL=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const id of ['naruto-shikamaru-sewing','naruto-shikamaru-strangle']){const {es}=A.identityArena();let hits=0,cancelled=false;for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const result=hurt.apply(this,args);if(args[7]===id){hits++;if(hits===2){S.clear(p);cancelled=true}}return result}}
  for(let i=0;i<500&&!cancelled;i++)A.identityTick();A.assert(cancelled&&hits===2,'callback fixture failed to reach active skill '+id);A.assert(!S.effects.some(e=>e.owner===p)&&!S.casts.some(b=>b.owner===p)&&!S.activeFor(p),'callback clear left actor/pending hint '+id);A.resume();try{S.update(1)}finally{A.pause()}A.assert(hits===2,'cancelled skill continued another target or pulse '+id);out.push({id,hits,actors:0,pending:0});
 }
 return out;
}"""


NATIVE_OBSERVE=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;window.IdentityFrames=[];window.IdentityTimeline=[];const primary={},targets={},seen=new Set();let firstChain=null,lastSample=-1;
 const draw=G.Combat.drawAirFields;G.Combat.drawAirFields=function(ctx){const result=draw.call(this,ctx),s=S.stateFor(p),clock=s?.clock||0,list=S.effects.filter(e=>e.owner===p);firstChain??=S.casts.find(b=>b.owner===p&&b.chain);
  const capture=(key,extra={})=>{if(seen.has(key))return;seen.add(key);const pose=S.activeFor(p),state={key,time:G.Game.st.time,clock,pose:pose?{kind:pose.kind,phase:pose.phase,age:pose.age,phaseAge:pose.phaseAge,phaseDuration:pose.phaseDuration,key:G.ShikamaruArt.sample('cast',pose.age,G.Sprites.dirFromAngle(pose.aim||0),pose)?.key}:null,effects:A.identityEffects(),visual:S.shadowVisualFor(p),...extra};queueMicrotask(()=>IdentityFrames.push({...state,png:ctx.canvas.toDataURL()}))};
  if(firstChain){const count=firstChain.chain.segments.filter(s=>s.contact).length;if(count===0)capture('shadow-prepare',{castId:firstChain.serial});if(count>=1)capture('shadow-first',{castId:firstChain.serial,contacts:count});if(count>=2)capture('shadow-middle',{castId:firstChain.serial,contacts:count});if(count>=3)capture('shadow-last',{castId:firstChain.serial,contacts:count});if(firstChain.chain.ended&&!S.casts.includes(firstChain)&&![...S.leases].some(([e,l])=>l.cast.owner===p&&S.held(e)))capture('shadow-dissipated',{castId:firstChain.serial});}
  const pendingSewing=S.casts.find(b=>b.owner===p&&b.kind==='sewing');if(pendingSewing){const target=pendingSewing.followChain.chain.segments.find(s=>s.contact)?.target,sample=target?S.sewingVisualFor(pendingSewing,target,S.effects.find(e=>e.kind==='sewing'&&e.castId===pendingSewing.serial&&e.target===target)):null;if(sample?.stage==='rise'&&sample.height>.15&&sample.height<.85)capture('sewing-rise',{castId:pendingSewing.serial,targetId:target.id,sample})}
  const pendingArm=S.casts.find(b=>b.owner===p&&b.kind==='strangle'&&b.age>=.05&&b.age<.18);if(pendingArm)capture('strangle-rise',{castId:pendingArm.serial,castAge:pendingArm.age,targetId:pendingArm.rays[0]?.target?.id});
  for(const kind of ['sewing','net','strangle']){
   const available=list.filter(e=>e.kind===kind);if(!primary[kind]&&available.length){primary[kind]=available[0].castId;targets[kind]=available[0].targetId}
   const e=available.find(e=>e.castId===primary[kind]&&e.targetId===targets[kind]);
   if(e){const b=e.castRef,sample=S.effectVisualFor(e),pulses=b?.spec?.pulses||1,extra={castId:e.castId,targetId:e.targetId,pulseIndex:e.pulseIndex,effectAge:e.age,sample};if(kind==='net'){capture(kind+'-first',extra);if(e.age>=e.life*.35)capture(kind+'-middle',extra);if(e.age>=e.life*.75)capture(kind+'-last',extra)}else{if(e.pulseIndex>=1)capture(kind+'-first',extra);if(e.pulseIndex>=Math.ceil(pulses/2))capture(kind+'-middle',extra);if(e.pulseIndex>=pulses)capture(kind+'-last',extra)}}
   if(primary[kind]&&!available.length&&!S.casts.some(b=>b.owner===p&&b.kind===kind))capture(kind+'-dissipated',{castId:primary[kind]});
  }
  const pose=S.activeFor(p);if(pose?.kind==='sewing')capture('sewing-body',{body:true});if(clock-lastSample>=.05){lastSample=clock;IdentityTimeline.push(A.identityState())}return result;
 };Acceptance.resume();
}"""

def native():
    out=OUT/'native';out.mkdir(parents=True,exist_ok=True);report={'controlled':True,'sameConfiguration':'Rank3 Q0 shadow, rank1 sewing/strangle, four true cards; same close three static million-HP native enemies at (85,0),(75,95),(-25,105). Normal shared-plan RAF auto-casts. No manual sim or skill clock stepping.','sourceBefore':manifest(),'viewports':{},'errors':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        for label,width,height in [('desktop',1100,850),('mobile360',360,780),('mobile390',390,844)]:
            folder=out/label;folder.mkdir(parents=True,exist_ok=True);context=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<600,has_touch=width<600,service_workers='block',record_video_dir=str(folder/'raw'),record_video_size={'width':width,'height':height});page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));saved_url=base.URL
            if width<600:base.URL=base.URL.replace('&layout=wide','')
            try:base.boot(page)
            finally:base.URL=saved_url
            page.evaluate(chain.SETUP);page.evaluate(SETUP);ledger=page.evaluate("()=>{const ledger=Acceptance.identityBuild(),p=G.Game.player;for(const [x,y]of [[85,0],[75,95],[-25,105]])Acceptance.spawn(x,y);p.target=G.EnemyMgr.all()[0];return ledger}");page.evaluate(NATIVE_OBSERVE)
            started=time.monotonic()
            while time.monotonic()-started<7:
                keys=page.evaluate('IdentityFrames.map(f=>f.key)')
                if all(k in keys for k in ['shadow-last','sewing-last','net-last','strangle-last','strangle-dissipated','sewing-dissipated']):break
                page.wait_for_timeout(40)
            data=page.evaluate('({frames:IdentityFrames,timeline:IdentityTimeline,final:Acceptance.identityState()})');data['ledger']=ledger;data['frameFiles']=[]
            for frame in data.pop('frames'):
                png=frame.pop('png');name=frame['key']+'.png';(folder/name).write_bytes(base64.b64decode(png.split(',',1)[1]));data['frameFiles'].append({'image':name,**frame})
            video=page.video;context.close();video.save_as(str(folder/'skill-identity-native.webm'));video.delete();report['viewports'][label]=data;print(label,'frames',len(data['frameFiles']),flush=True)
        browser.close()
    report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'sourceStable':report['sourceStable'],'errors':report['errors']}))


def main():
    OUT.mkdir(parents=True,exist_ok=True);report={'sourceBefore':manifest(),'controlled':True,'checks':{},'errors':[]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=base.CHROME,headless=True);page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block');page.on('pageerror',lambda e:report['errors'].append(str(e)));base.boot(page);page.evaluate(chain.SETUP);page.evaluate(SETUP)
            for name,check in [('events',EVENTS),('readOnly',READ_ONLY),('cleanup',CLEANUP),('callbackCancel',CALLBACK_CANCEL),('chainGrowth',chain.GROWTH),('chainStopping',chain.STOPPING)]:report['checks'][name]=page.evaluate(check);print(name,'PASS',flush=True)
            browser.close()
        assert not report['errors'],report['errors'];report['ok']=True
    except Exception as error:report['failure']=str(error);raise
    finally:
        report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':
    if '--native' in sys.argv:native()
    else:main()
