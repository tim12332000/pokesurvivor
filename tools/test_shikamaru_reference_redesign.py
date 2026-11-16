"""New reference-driven Shikamaru runtime acceptance in the isolated worktree.

Projection alpha and 3D descent contacts must be real simulation, not prototype
frames or old renderer expectations. Natural play is separate from fixtures.
"""
from __future__ import annotations
import base64,hashlib,json,os,sys,time
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import test_shikamaru as base
import test_shikamaru_chain as legacy_chain
import test_shikamaru_stationary_bind as stationary

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_ROOT=Path('C:/Git/pokesurvivor/.omx/worktrees/shikamaru-reference-redesign').resolve()
assert ROOT.resolve()==EXPECTED_ROOT, f'Reference redesign QA must run only in isolated tree: {ROOT}'
OUT=ROOT/'art-review/shikamaru/qa/reference-redesign'
URL=os.environ.get('SHIKAMARU_REFERENCE_URL','http://127.0.0.1:8351/.omx/digimon.html?lang=zh-TW&layout=wide')
base.URL=URL


def manifest():
    names=['.omx/naruto-shikamaru.js','.omx/naruto-skills.js','.omx/jujutsu-growth.js','art-review/shikamaru-art.js','art-review/shikamaru-frames.json','art-review/shikamaru/reference-shadow-geometry.js','.omx/digimon.html']
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}


def verify_served_source(page):
    expected=hashlib.sha256((ROOT/'.omx/naruto-shikamaru.js').read_bytes()).hexdigest()
    response=page.request.get(urljoin(URL,'/.omx/naruto-shikamaru.js'),headers={'Cache-Control':'no-cache'})
    assert response.ok, '8351 runtime missing'
    actual=hashlib.sha256(response.body()).hexdigest()
    assert actual==expected, '8351 served another worktree runtime; refuse old-root evidence'
    return {'runtimeSha256':actual,'matchesIsolatedWorktree':True}



PREPARE=r"""() => {
 const A=Acceptance,p=A.p(),R=G.ShikamaruReferenceGeometry;A.assert(R,'new reference geometry unavailable');A.reset();p.moves=[G.Moves.instance('naruto-shikamaru',1)];p.level=1;window.ReferenceEnemy=A.spawn(180,0);ReferenceEnemy.anim.loop('Idle');return true;
}"""

ALPHA=r"""() => {
 const A=Acceptance,p=A.p(),R=G.ShikamaruReferenceGeometry,e=ReferenceEnemy,owner=R.bodyFor(p),body=R.bodyFor(e);A.assert(owner&&body,'real sprite alpha not ready');A.assert(owner.sourceURL!==body.sourceURL&&!/shikamaru/i.test(body.sourceURL),'monster projection copied Shikamaru art');
 const native=document.createElement('canvas'),mask=document.createElement('canvas');native.width=mask.width=260;native.height=mask.height=260;const nc=native.getContext('2d'),mc=mask.getContext('2d');nc.imageSmoothingEnabled=mc.imageSmoothingEnabled=false;e.anim.draw(nc,120,180);mc.drawImage(body.canvas,Math.round(120-body.foot.x),Math.round(180-body.foot.y));const a=nc.getImageData(0,0,260,260).data,b=mc.getImageData(0,0,260,260).data;let opaque=0,mismatch=0;for(let i=3;i<a.length;i+=4){if(a[i]>=24)opaque++;if((a[i]>=24)!==(b[i]>=24))mismatch++}A.assert(opaque>20&&mismatch===0,'body mask differs from actual native frame alpha '+mismatch);
 const projection=R.project(e,1,0,90,.7,()=>true),pixels=projection.pixels;let inside=null,outside=null;for(let y=2;y<projection.height-2;y++)for(let x=2;x<projection.width-2;x++){const alpha=pixels[(y*projection.width+x)*4+3];if(alpha>=200&&!inside)inside={x:projection.x+x+.5,y:projection.y+y+.5,alpha};if(alpha===0&&!outside)outside={x:projection.x+x+.5,y:projection.y+y+.5,alpha}}A.assert(inside&&outside,'projection fixture lacks true inner/empty bbox points');A.assert(R.contains(projection,inside.x,inside.y)&&!R.contains(projection,outside.x,outside.y),'projection hit ignores real alpha');
 const square=point=>[{x:point.x-.2,y:point.y-.2},{x:point.x+.2,y:point.y-.2},{x:point.x+.2,y:point.y+.2},{x:point.x-.2,y:point.y+.2}],insidePoly=(poly,x,y)=>x>=poly[0].x&&x<=poly[2].x&&y>=poly[0].y&&y<=poly[2].y;A.assert(R.groundContact(projection,square(inside),insidePoly)&&!R.groundContact(projection,square(outside),insidePoly),'ground contact used bounding box instead of drawn alpha');
 const before={key:owner.key,x:p.x,y:p.y};p.x+=31;p.y+=17;p.anim.loop('Walk');p.anim.dir=6;p.anim.update(.14);const movedBody=R.bodyFor(p),moved=R.project(p,1,0,100,.65,()=>true);A.assert(movedBody.key!==owner.key,'current body animation/direction mask was stale');A.assert(moved.matrix.e===p.x&&moved.matrix.f===p.y,'projection source did not follow current true actor feet');
 return {owner:{key:owner.key,sourceURL:owner.sourceURL,rect:owner.rect,anchor:owner.anchor,bodyHeight:owner.bodyHeight},enemy:{key:body.key,sourceURL:body.sourceURL,rect:body.rect,anchor:body.anchor,bodyHeight:body.bodyHeight},nativeOpaquePixels:opaque,nativeAlphaMismatches:mismatch,inside,outside,currentFrame:{before,after:{key:movedBody.key,x:p.x,y:p.y},matrix:moved.matrix},png:projection.canvas.toDataURL()};
}"""

CACHE=r"""() => {
 const A=Acceptance,R=G.ShikamaruReferenceGeometry,e=ReferenceEnemy;const open=R.project(e,1,0,100,.7,()=>true),wallX=e.x+25,blocked=R.project(e,1,0,100,.7,(ax,ay,bx,by)=>bx<wallX),leaked=blocked.points.filter(p=>p.x>=wallX);A.assert(!leaked.length,'same-position projection reused stale wall clip '+leaked.length);let wall=Infinity;const samePolicy=(ax,ay,bx,by)=>bx<wall;R.project(e,1,0,101,.7,samePolicy);wall=e.x+25;A.resume();try{G.NarutoShikamaru.update(.01)}finally{A.pause()}const same=R.project(e,1,0,101,.7,samePolicy);A.assert(same.points.every(p=>p.x<wall),'next sim reused changed same-closure wall');const world=G.World;G.World={...world};let next;try{next=R.project(e,1,0,100,.7,()=>false)}finally{G.World=world}A.assert(next.points.length===0,'projection alpha cache survived changed world obstacle state');return {openPixels:open.points.length,wallX,blockedPixels:blocked.points.length,leakedPixels:leaked.length,changedWorldPixels:next.points.length};
}"""

ARCH=r"""() => {
 const A=Acceptance,p=A.p(),R=G.ShikamaruReferenceGeometry,e=ReferenceEnemy,body=R.bodyFor(e);p.x=p.y=0;e.x=160;e.y=0;const arc=R.makeArch(p,e,{x:0,y:0},0,5),samples=[],hits=[];
 for(let i=1;i<=100;i++){R.advanceArch(arc,i/100,()=>true);const hit=R.sweptBody(arc,arc.previous,arc.current,body,()=>true);samples.push({u:arc.progress,phase:arc.phase,previous:arc.previous,current:arc.current,hit});if(hit)hits.push({u:arc.progress,phase:arc.phase,point:hit})}
 A.assert(samples.some(s=>s.current.z>body.bodyHeight+5),'arch never truly passed above a person');A.assert(samples.filter(s=>Math.min(s.previous.z,s.current.z)>body.bodyHeight+2).every(s=>!s.hit),'overhead tip falsely hit body');A.assert(hits.length&&hits.every(h=>h.phase==='descent'||h.phase==='contact'),'arch lacked descending body-alpha contact');
 const shifted=R.makeArch(p,e,{x:0,y:0},0,5);R.advanceArch(shifted,.8,()=>true);e.y=200;const evaded=R.sweptBody(shifted,R.archPoint(shifted,.8),R.archPoint(shifted,1),body,()=>true);A.assert(!evaded,'moving target took scheduled hit away from sweep');e.y=0;const blocked=R.makeArch(p,e,{x:0,y:0},0,5);R.advanceArch(blocked,.9,(ax,ay,bx,by)=>bx<80);A.assert(blocked.blocked,'3D front ignored a ground wall');A.assert(!R.sweptBody(blocked,blocked.previous,blocked.current,body,()=>false),'wall-blocked sweep damaged target');
 const canvas=document.createElement('canvas');canvas.width=canvas.height=400;const ctx=canvas.getContext('2d');ctx.translate(100,300);const before=JSON.stringify(arc);for(let i=0;i<50;i++){R.drawArch(ctx,arc);R.archPoint(arc,.5)}A.assert(before===JSON.stringify(arc),'arch render/sample mutated true sweep');return {bodyHeight:body.bodyHeight,lift:arc.lift,maximumZ:Math.max(...samples.map(s=>s.current.z)),firstDescendingContact:hits[0],samples,evaded,wallBlocked:blocked.blocked,readOnly:true,png:canvas.toDataURL()};
}"""


def geometry():
    OUT.mkdir(parents=True,exist_ok=True);report={'stage':'geometry-module-slice','notFullRuntimeCandidate':True,'url':URL,'sourceBefore':manifest(),'checks':{},'errors':[]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=base.CHROME,headless=True);page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block');page.on('pageerror',lambda e:report['errors'].append(str(e)));base.boot(page);report['servedSource']=verify_served_source(page);normal=page.evaluate('!!G.ShikamaruReferenceGeometry');report['moduleLoadedByNormalEntry']=normal
            if not normal:page.add_script_tag(url=urljoin(URL,'/art-review/shikamaru/reference-shadow-geometry.js'))
            page.evaluate(PREPARE);page.wait_for_function('!!G.ShikamaruReferenceGeometry.bodyFor(ReferenceEnemy)',polling=25)
            for name,check in [('alpha',ALPHA),('cache',CACHE),('arch',ARCH)]:
                data=page.evaluate(check)
                if 'png' in data:(OUT/(name+'.png')).write_bytes(base64.b64decode(data.pop('png').split(',',1)[1]))
                report['checks'][name]=data;print(name,'PASS',flush=True)
            browser.close()
        report['ok']=True
    except Exception as error:report['failure']=str(error);raise
    finally:
        report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(OUT/'geometry-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')



CORE_SETUP=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry;
 A.buildNew=(rank=1,q=0,sewing=false)=>{A.reset();p.statsTaken={};p.moves=[G.Moves.instance('naruto-shikamaru',1)];p.level=Math.max(2,rank+q+2);const ledger=[];for(let i=1;i<rank;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='up:naruto-shikamaru');A.assert(c&&c.apply(p)!==false,'real rank card missing');ledger.push(c.key)}for(let i=0;i<q;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');A.assert(c&&c.apply(p)!==false,'real quantity card missing');ledger.push(c.key)}if(sewing){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='new:naruto-shikamaru-sewing');A.assert(c&&c.apply(p)!==false,'new arch skill card missing');ledger.push(c.key)}return ledger};
 A.watchNew=es=>{const events=[];for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const body=R.bodyFor(this),hp=this.hp,source=args[6],id=args[7],result=hurt.apply(this,args);if(hp>this.hp)events.push({time:S.stateFor(p)?.clock,id,targetId:this.id,x:this.x,y:this.y,loss:hp-this.hp,owner:source===p,bodyKey:body?.key,bodyHeight:body?.bodyHeight});return result}}return events};
 A.castShadow=es=>{p.target=es[0];A.cast(p.moves.find(m=>m.id==='naruto-shikamaru'));return S.casts.findLast(b=>b.owner===p&&b.kind==='shadow')};
 A.captureNew=(es,limit=3)=>{const b=A.castShadow(es);for(let i=0;i<limit*100&&!b.chain.ended;i++)A.step(.01);A.assert(b.chain.visited.size===Math.min(es.length,b.spec.chainTargets),'new ground-alpha chain failed to capture fixture');return b};
}"""

GROUND=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry,out=[];
 for(const [rank,q]of [[1,0],[2,0],[1,1],[1,2]]){const ledger=A.buildNew(rank,q),es=[A.spawn(100,0),A.spawn(180,55),A.spawn(260,-15)],hits=A.watchNew(es),b=A.castShadow(es);A.assert(b.chain.segments.length===1,'new ground attack fanned before contact');let radiusWouldHitWhileAlphaMiss=0;
  for(let i=0;i<300&&!b.chain.ended;i++){const seg=b.chain.segments[b.chain.current],beforeHits=hits.length;A.step(.01);if(seg){const projection=S.projectionFor(seg.target),contact=R.groundContact(projection,seg.polygon,S.polygonContains);if(!contact&&S.segmentDistance(seg.target.x,seg.target.y,seg.grownPoints[0].x,seg.grownPoints[0].y,seg.grownPoints.at(-1).x,seg.grownPoints.at(-1).y)<seg.target.r+b.spec.radius)radiusWouldHitWhileAlphaMiss++;}}
  const contacts=S.stats(p).contacts.filter(c=>c.geometry?.kind==='ground-alpha');A.assert(contacts.length===Math.min(es.length,rank+q)&&new Set(hits.map(h=>h.targetId)).size===contacts.length,'true cards did not add distinct real shadow contacts');for(const c of contacts){const seg=b.chain.segments.find(s=>s.target.id===c.targetId);A.assert(seg&&R.contains(seg.targetProjection,c.geometry.point.x,c.geometry.point.y),'actual hurt point outside actual captured alpha');A.assert(hits.some(h=>h.targetId===c.targetId&&h.id===c.moveId),'ground contact telemetry bypassed native hurt')}
  out.push({rank,q,cost:ledger.length,ledger,hits,contacts,radiusWouldHitWhileAlphaMiss});
 }
 return out;
}"""

FUSION=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry;A.buildNew(2);const es=[A.spawn(80,0),A.spawn(120,30)],b=A.captureNew(es),links=b.chain.segments.filter(s=>s.contact).map(seg=>{const projection=S.projectionFor(seg.target),endpoint=seg.grownPoints.at(-1);return {targetId:seg.target.id,held:S.held(seg.target),endpoint,insideCurrentAlpha:R.contains(projection,endpoint.x,endpoint.y),bodyKey:projection?.body.key}});A.assert(links.every(l=>!l.held||l.insideCurrentAlpha),'fusion changed alpha but held link endpoint fell into transparent region');return {links};
}"""

ARC_HURT=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry;const ledger=A.buildNew(3,0,true),es=[A.spawn(100,0),A.spawn(180,55),A.spawn(260,-15)];A.captureNew(es);const hits=A.watchNew(es),move=p.moves.find(m=>m.id==='naruto-shikamaru-sewing');A.cast(move);const b=S.casts.findLast(b=>b.owner===p&&b.kind==='sewing'),samples=[];
 for(let i=0;i<250;i++){const oldCount=hits.length;A.step(.01);for(const arc of b.arcs){const body=R.bodyFor(arc.target);if(Math.min(arc.previous.z,arc.current.z)>body.bodyHeight+2)A.assert(!arc.contact||arc.contact.progress<arc.progress,'overhead arc caused body hurt');}if(i%3===0)samples.push({clock:S.stateFor(p).clock,age:b.age,arcs:b.arcs.map(a=>({pulse:a.pulseIndex,targetId:a.target.id,phase:a.phase,previous:a.previous,current:a.current,progress:a.progress,hit:a.hit,contact:a.contact}))});}
 const contacts=S.stats(p).contacts.filter(c=>c.moveId===move.id);A.assert(hits.length&&contacts.length===hits.length,'new arcs did not produce real hurt events');for(const c of contacts){A.assert(c.geometry?.kind==='xyz-tip-sweep'&&['descent','contact'].includes(c.geometry.phase),'arch hurt was scheduled before descending body contact');A.assert(c.geometry.point.z<=R.bodyFor(es.find(e=>e.id===c.targetId)).bodyHeight+2,'arch hurt above actual body height');A.assert(hits.some(h=>h.id===move.id&&h.targetId===c.targetId),'arc metadata without actual hurt');}const perTargetPulse=new Set();for(const c of contacts){const key=c.targetId+':'+c.pulse;A.assert(!perTargetPulse.has(key),'arc rehit same body twice within one pulse');perTargetPulse.add(key)}return {ledger,hits,contacts,samples};
}"""



SAFETY=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const reason of ['pause','clear','death','world','unlearn']){A.buildNew(2,0,true);const es=[A.spawn(100,0),A.spawn(180,55)];A.captureNew(es);const hits=A.watchNew(es);A.cast(p.moves.find(m=>m.id==='naruto-shikamaru-sewing'));A.finish(.25);const world=G.World,clock=S.stateFor(p).clock;
  if(reason==='pause'){S.update(1);A.assert(S.stateFor(p).clock===clock&&hits.length===0,'paused arch advanced or hurt');out.push({reason,hits:0});continue}
  if(reason==='clear')S.clear(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};if(reason==='unlearn')p.moves=[];
  try{for(let i=0;i<100;i++)A.step(.01)}finally{G.World=world;p.dead=false}
  A.assert(!hits.length&&!S.casts.some(b=>b.owner===p)&&!es.some(e=>S.held(e))&&!S.activeFor(p),'cancelled new alpha/arc state survived '+reason);out.push({reason,hits:hits.length});
 }
 for(const callback of ['hurt','onDealt']){A.buildNew(3,0,true);const es=[A.spawn(100,0),A.spawn(180,55),A.spawn(260,-15)];A.captureNew(es);const hits=A.watchNew(es);let cancelled=false;const original=p.onDealt;
  if(callback==='hurt')for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const result=hurt.apply(this,args);if(args[7]==='naruto-shikamaru-sewing'&&!cancelled){cancelled=true;S.clear(p)}return result}}
  else p.onDealt=function(...args){const result=original.apply(this,args);if(!cancelled){cancelled=true;S.clear(p)}return result};
  try{A.cast(p.moves.find(m=>m.id==='naruto-shikamaru-sewing'));A.finish(2)}finally{p.onDealt=original}
  A.assert(cancelled&&hits.length===1&&!S.casts.some(b=>b.owner===p),'same-wave '+callback+' cancellation hit later target/pulse');out.push({callback,hits});
 }
 return out;
}"""

READ_ONLY=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.buildNew(2,0,true);const es=[A.spawn(100,0),A.spawn(180,55)];A.captureNew(es);A.cast(p.moves.find(m=>m.id==='naruto-shikamaru-sewing'));A.finish(.45);const snapshot=()=>JSON.stringify({clock:S.stateFor(p)?.clock,hits:S.stats(p).hits,contacts:S.stats(p).contacts,casts:S.casts.map(b=>({age:b.age,arcs:b.arcs?.map(a=>({previous:a.previous,current:a.current,progress:a.progress,phase:a.phase,hit:a.hit,points:a.points})),chain:b.chain?{current:b.chain.current,segments:b.chain.segments.map(s=>({path:s.path,grownPoints:s.grownPoints,contact:s.contact}))}:null}))});const before=snapshot(),canvas=document.createElement('canvas');canvas.width=canvas.height=500;const ctx=canvas.getContext('2d');ctx.translate(200,300);for(let i=0;i<50;i++){G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx)}A.assert(before===snapshot(),'new reference renderer advanced simulation or hurt');return {readOnly:true,iterations:50};
}"""


def core():
    OUT.mkdir(parents=True,exist_ok=True);report={'stage':'new-runtime-controlled','url':URL,'sourceBefore':manifest(),'checks':{},'errors':[]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=base.CHROME,headless=True);page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block');page.on('pageerror',lambda e:report['errors'].append(str(e)));base.boot(page);report['servedSource']=verify_served_source(page);page.evaluate(PREPARE);page.wait_for_function('!!G.ShikamaruReferenceGeometry.bodyFor(ReferenceEnemy)',polling=25);page.evaluate(legacy_chain.SETUP);page.evaluate(CORE_SETUP)
            for name,check in [('groundAlpha',GROUND),('fusion',FUSION),('archHurt',ARC_HURT),('safety',SAFETY),('stationary',stationary.CHECK),('readOnly',READ_ONLY)]:report['checks'][name]=page.evaluate(check);print(name,'PASS',flush=True)
            browser.close()
        report['ok']=True
    except Exception as error:report['failure']=str(error);raise
    finally:
        report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(OUT/'core-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')



NATURAL_OBSERVE=r"""() => {
 const S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry,Q=window.ReferenceQA={hits:[],ledger:[],offers:[],samples:[],frames:[],events:[],inputs:[],current:null,groupEver:false,firstArch:null};
 const hurt=G.Enemy.prototype.hurt;G.Enemy.prototype.hurt=function(...args){const hp=this.hp,owner=args[6],id=args[7],p=G.Game.player,s=S.stateFor(p);let geometry=null;
  if(owner===p&&id==='naruto-shikamaru-sewing'){const arcs=S.casts.filter(b=>b.owner===p&&b.kind==='sewing').flatMap(b=>(b.arcs||[]).filter(a=>a.target===this&&a.hit&&a.contact).map(a=>({castId:b.serial,pulse:a.pulseIndex,...a.contact})));if(arcs.length)geometry={kind:'xyz-tip-sweep',...arcs.at(-1)}}
  if(owner===p&&id==='naruto-shikamaru'){const b=[...S.casts].reverse().find(b=>b.owner===p&&b.kind==='shadow'&&b.chain?.segments.some(g=>g.target===this&&!g.contact)),segment=b?.chain.segments.find(g=>g.target===this&&!g.contact),projection=S.projectionFor(this),point=segment&&R.groundContact(projection,segment.polygon,S.polygonContains);if(point)geometry={kind:'ground-alpha',castId:b.serial,point,bodyKey:projection.body.key,sourceURL:projection.sourceURL}}
  const result=hurt.apply(this,args);if(owner===p&&hp>this.hp){const event={time:G.Game.st.time,wall:performance.now()/1000,id,targetId:this.id,hpBefore:hp,hpAfter:this.hp,maxHp:this.maxHp,loss:hp-this.hp,x:this.x,y:this.y,geometry};Q.hits.push(event);if(geometry?.kind==='xyz-tip-sweep')Q.firstArch??=event;}return result};
 Q.snapshot=()=>{const p=G.Game.player,s=p&&S.stateFor(p);if(!p)return null;const held=[...S.leases].filter(([e,l])=>l.cast.owner===p&&S.held(e)).map(([e])=>{const projection=s?.projections?.get(e);return {id:e.id,x:e.x,y:e.y,projection:projection?{bodyKey:projection.body.key,sourceURL:projection.sourceURL,across:projection.across,length:projection.length}:null}}),flying=S.casts.filter(b=>b.owner===p&&b.kind==='sewing').flatMap(b=>(b.arcs||[]).filter(a=>a.progress<1&&!a.blocked&&a.target.hp>0).map(a=>({castId:b.serial,pulse:a.pulseIndex,phase:a.phase,progress:a.progress,z:a.current.z,targetId:a.target.id})));if(held.filter(h=>(h.projection?.across||0)>1).length>=2)Q.groupEver=true;
  return {time:G.Game.st.time,wall:performance.now()/1000,level:p.level,hp:p.hp,maxHp:p.maxHp,dead:!!p.dead,x:p.x,y:p.y,quantity:p.quantityPicks||0,moves:p.moves.map(m=>({id:m.id,rank:m.lvl})),phase:s?.plan?.phase||null,cycle:s?.cycles||0,held,flying,groupEver:Q.groupEver,stats:s?{casts:{...s.casts},hits:s.hits,damage:s.damage}:null};};
 const show=G.RunUI.showLevelUp;G.RunUI.showLevelUp=function(level,list,cb,...args){const offer={serial:Q.offers.length,time:G.Game.st.time,level,options:list.map(c=>({key:c.key,type:c.type,title:c.title,desc:c.desc}))};Q.offers.push(offer);Q.current=offer;return show.call(this,level,list,c=>{const before=Q.snapshot();cb(c);Q.ledger.push({cost:Q.ledger.length+1,key:c.key,before,after:Q.snapshot()});Q.current=null},...args)};
 const draw=G.Combat.drawAirFields,seen=new Set();G.Combat.drawAirFields=function(ctx){const result=draw.call(this,ctx),state=Q.snapshot();if(!state)return result;const keys=[];if(state.level===1)keys.push('Lv1-alpha-source');if(Q.hits.some(h=>h.geometry?.kind==='ground-alpha'))keys.push('real-ground-contact');if(Q.ledger.length)keys.push('first-true-card');if(state.held.filter(h=>(h.projection?.across||0)>1).length>=2)keys.push('fused-native-projections');if(state.flying.some(a=>a.phase==='rise'))keys.push('arch-rising');if(state.flying.some(a=>a.z>65))keys.push('arch-overhead');if(Q.firstArch)keys.push('actual-descent-hurt');if(Q.firstArch&&state.phase==='recover'&&!state.flying.length)keys.push('arch-full-recover');for(const key of keys)if(!seen.has(key)){seen.add(key);queueMicrotask(()=>Q.frames.push({key,state,png:ctx.canvas.toDataURL()}))}return result};
 let last=-1,phase='';function observe(){if(G.Game.state==='playing'){const state=Q.snapshot();if(state&&state.time-last>=.2){last=state.time;Q.samples.push(state)}if(state&&state.phase!==phase){phase=state.phase;Q.events.push(state)}}requestAnimationFrame(observe)}requestAnimationFrame(observe);
}"""


def natural():
    import subprocess
    out=OUT/'natural';out.mkdir(parents=True,exist_ok=True);report={'stage':'new-runtime-natural','sourceBefore':manifest(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'errors':[],'policy':'Native D/S/A/W square,1.5 native seconds per side. Actual UI cards: learn new arch/sewing, quantity, shadow upgrade, other valid new/upgrade. No HP/XP/invulnerability/AI/clock mutation.'}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True);context=browser.new_context(viewport={'width':1100,'height':850},service_workers='block',record_video_dir=str(out/'raw'),record_video_size={'width':1100,'height':850});page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(URL);page.wait_for_function('window.PS_REDRAWN_READY&&window.G?.NarutoShikamaru?.version>=6&&document.getElementById("boot").classList.contains("hidden")')
        report['servedSource']=verify_served_source(page)
        if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
        page.locator('[data-quick-naruto="30017"]').click();report['permanent']=page.evaluate('G.DB.upgradesOf(G.DB.save.partner)');assert not any(report['permanent'].values());page.evaluate(NATURAL_OBSERVE);page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30017&&G.Game.state==="playing"');report['initial']=page.evaluate('ReferenceQA.snapshot()');assert report['initial']['level']==1
        held=None;serial=None;started=time.monotonic();progress=-30
        while time.monotonic()-started<420:
            data=page.evaluate('({state:G.Game.state,snapshot:ReferenceQA.snapshot(),offer:ReferenceQA.current,firstArch:ReferenceQA.firstArch,cards:ReferenceQA.ledger.length})');a=data['snapshot'];t=a['time']
            if data['firstArch'] and a['groupEver'] and data['cards'] and a['phase']=='recover' and not a['flying']:report['newCoreComplete']=True;break
            if a['dead'] or data['state']=='over' or t>=240:break
            if t-progress>=30:print('reference natural',round(t),'Lv',a['level'],'phase',a['phase'],'group',a['groupEver'],'arch',bool(data['firstArch']),flush=True);progress=t;(out/'progress.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
            if data['state']=='levelup' and data['offer'] and data['offer']['serial']!=serial:
                if held:page.keyboard.up(held);held=None
                offer=data['offer'];priority=lambda c:0 if c['key']=='new:naruto-shikamaru-sewing' else 1 if c['key']=='stat:quantity' else 2 if c['key']=='up:naruto-shikamaru' else 99 if 'strangle' in c['key'] else 3 if c['type']=='new' else 4 if c['type']=='up' else 9
                selected=min(range(len(offer['options'])),key=lambda i:(priority(offer['options'][i]),i));page.screenshot(path=str(out/f'card-{offer["serial"]}.png'));page.locator('#cards .card').nth(selected).click();serial=offer['serial']
            elif page.locator('#scr-item').is_visible():page.locator('#item-cards .card').first.click()
            elif page.locator('#scr-bond').is_visible():page.locator('#bond-cards .card').first.click()
            elif data['state']=='playing':
                key=['KeyD','KeyS','KeyA','KeyW'][int(t//1.5)%4]
                if key!=held:
                    if held:page.keyboard.up(held)
                    page.keyboard.down(key);held=key;page.evaluate('e=>ReferenceQA.inputs.push(e)',{'time':t,'key':key})
            elif data['state']=='paused':page.locator('#btn-resume').click()
            page.wait_for_timeout(65)
        if held:page.keyboard.up(held)
        report.update(page.evaluate('({hits:ReferenceQA.hits,ledger:ReferenceQA.ledger,offers:ReferenceQA.offers,samples:ReferenceQA.samples,events:ReferenceQA.events,inputs:ReferenceQA.inputs,groupEver:ReferenceQA.groupEver,firstArch:ReferenceQA.firstArch,final:ReferenceQA.snapshot(),state:G.Game.state})'));report['frames']=[]
        for frame in page.evaluate('ReferenceQA.frames'):
            png=frame.pop('png');name=frame['key']+'.png';(out/name).write_bytes(base64.b64decode(png.split(',',1)[1]));report['frames'].append({'image':name,**frame})
        page.screenshot(path=str(out/'final.png'));video=page.video;context.close();video.save_as(str(out/'reference-new-core-native.webm'));video.delete();browser.close()
    report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'core':report.get('newCoreComplete',False),'time':report['final']['time'],'level':report['final']['level'],'cards':len(report['ledger']),'group':report['groupEver'],'arch':report['firstArch'],'sourceStable':report['sourceStable']},ensure_ascii=False))



NATIVE_OBSERVE=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry;window.RefNativeFrames=[];window.RefNativeScene=null;const draw=G.Combat.drawAirFields;
 G.Combat.drawAirFields=function(ctx){const result=draw.call(this,ctx),scene=window.RefNativeScene,s=S.stateFor(p);if(!scene||!s)return result;scene.seen??=new Set();const active=S.casts.filter(b=>b.owner===p&&b.kind==='sewing').flatMap(b=>(b.arcs||[]).map(a=>({castId:b.serial,pulse:a.pulseIndex,targetId:a.target.id,progress:a.progress,phase:a.phase,previous:a.previous,current:a.current,hit:a.hit,contact:a.contact}))),contacts=s.contacts.filter(c=>c.geometry?.kind==='xyz-tip-sweep'),held=[...S.leases].filter(([e,l])=>l.cast.owner===p&&S.held(e)).map(([e])=>({id:e.id,x:e.x,y:e.y,sourceURL:s.projections?.get(e)?.sourceURL,bodyKey:s.projections?.get(e)?.body.key}));
 const keys=[];if(s.projection)keys.push('ground-source');if(held.length>=2)keys.push('fused-captured-projections');if(active.some(a=>a.progress===0))keys.push('same-shadow-ground-bulge');if(active.some(a=>a.phase==='rise'))keys.push('arch-rise');if(active.some(a=>a.current.z>65))keys.push('arch-overhead');if(active.some(a=>a.phase==='descent'&&!a.hit))keys.push('arch-descent-before-contact');if(contacts.length)keys.push('actual-xyz-body-hurt');if(contacts.length&&s.plan?.phase==='recover'&&!active.some(a=>a.progress<1))keys.push('full-recover');
 for(const key of keys)if(!scene.seen.has(key)){scene.seen.add(key);const frame={key,direction:scene.direction,time:G.Game.st.time,clock:s.clock,phase:s.plan?.phase,held,arcs:active,contacts:s.contacts.slice(),sourceProjection:s.projection?{bodyKey:s.projection.body.key,sourceURL:s.projection.sourceURL,matrix:s.projection.matrix}:null};queueMicrotask(()=>RefNativeFrames.push({...frame,png:ctx.canvas.toDataURL()}))}return result;
 };
}"""


def native():
    out=OUT/'native';out.mkdir(parents=True,exist_ok=True);report={'stage':'new-runtime-controlled-native','sourceBefore':manifest(),'viewports':{},'errors':[],'configuration':'Three actual cards: basic rank3 plus learn sewing rank1; Q0. Native million-HP static fixture, open collision arena, four directions. Real Combat/RAF/hurt, not prototype or natural growth.'}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        for label,width,height in [('desktop',1100,850),('mobile390',390,844)]:
            folder=out/label;folder.mkdir(parents=True,exist_ok=True);context=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<600,has_touch=width<600,service_workers='block',record_video_dir=str(folder/'raw'),record_video_size={'width':width,'height':height});page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));saved_url=base.URL
            if width<600:base.URL=URL.replace('&layout=wide','')
            try:base.boot(page)
            finally:base.URL=saved_url
            page.evaluate(PREPARE);page.wait_for_function('!!G.ShikamaruReferenceGeometry.bodyFor(ReferenceEnemy)',polling=25);page.evaluate(CORE_SETUP);page.evaluate(NATIVE_OBSERVE);data={'scenes':[]}
            for direction,angle in [('right',0),('left',3.141592653589793),('up',-1.5707963267948966),('down',1.5707963267948966)]:
                ledger=page.evaluate(r"""({direction,angle})=>{const A=Acceptance,p=A.p(),ledger=A.buildNew(3,0,true);for(const [x,y]of [[70,0],[110,25],[130,-20]])A.spawn(Math.cos(angle)*x-Math.sin(angle)*y,Math.sin(angle)*x+Math.cos(angle)*y);p.target=G.EnemyMgr.all()[0];window.RefNativeScene={direction,seen:new Set()};A.resume();return ledger}""",{'direction':direction,'angle':angle})
                started=time.monotonic()
                while time.monotonic()-started<4:
                    complete=page.evaluate('RefNativeScene.seen.has("full-recover")')
                    if complete:break
                    page.wait_for_timeout(35)
                page.evaluate('Acceptance.pause()');data['scenes'].append({'direction':direction,'ledger':ledger,'observed':page.evaluate('[...RefNativeScene.seen]'),'stats':page.evaluate('G.NarutoShikamaru.stats(G.Game.player)')});print(label,direction,'new reference native recorded',flush=True)
            data['frames']=[]
            for frame in page.evaluate('RefNativeFrames'):
                png=frame.pop('png');name=frame['direction']+'-'+frame['key']+'.png';(folder/name).write_bytes(base64.b64decode(png.split(',',1)[1]));data['frames'].append({'image':name,**frame})
            video=page.video;context.close();video.save_as(str(folder/'reference-four-direction-native.webm'));video.delete();report['viewports'][label]=data
        browser.close()
    report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'sourceStable':report['sourceStable'],'errors':report['errors']}))


def main():
    if '--natural' in sys.argv:natural()
    elif '--native' in sys.argv:native()
    elif '--core' in sys.argv:core()
    else:geometry()

if __name__=='__main__':main()
