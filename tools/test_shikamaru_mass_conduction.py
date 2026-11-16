"""Production-entry conduction acceptance, using real target hurt and actual cards.

The open arena and explicit simulation steps are controlled fixtures. This does
not replace normal-entry animation or natural-growth verification.
"""
import hashlib
import json
from playwright.sync_api import sync_playwright
import test_shikamaru as base
import test_shikamaru_mass as mass

OUT=base.ROOT/'art-review/shikamaru/qa/mass/conduction'
SOURCE='.omx/naruto-shikamaru-mass.js'

SETUP=r'''() => {
 const A=Acceptance,p=A.p(),M=G.NarutoShikamaruMass,ID='naruto-shikamaru-mass';
 A.conductionArena=(count=3)=>{const {m,ledger}=A.massBuild(),es=Array.from({length:count},(_,i)=>{const angle=i*Math.PI*2/count;return A.spawn(Math.cos(angle)*180,Math.sin(angle)*180,i%75===0)}),events=[];
  for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const before=this.hp,b=M.stateFor(p)?.cast,result=hurt.apply(this,args);if(args[7]===ID)events.push({targetId:this.id,owner:args[6]===p,at:b?.age,stage:b?.exploded?'bomb':'shock',raw:args[0],loss:before-this.hp});return result}}
  const b=A.massCast();return {m,ledger,es,events,b};};
 A.conductionFlight=b=>{A.massWait(()=>b.conductAt!==null&&[...b.rays.values()].some(r=>r.shocks.some(packet=>packet.progress>.05&&packet.progress<.65)),3,'no travelling electric front');return [...b.rays.values()].find(r=>r.shocks.some(packet=>packet.progress>.05&&packet.progress<.65))};
 A.conductionSnapshot=b=>JSON.stringify({age:b.age,cooldown:M.stateFor(p)?.cooldown,center:b.center,bomb:b.bomb,hits:M.stateFor(p)?.hits,rays:[...b.rays.values()].map(r=>({source:r.source,body:r.bodyPoint,shocks:r.shocks,events:r.shockEvents}))});
}'''

CHECK=r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,M=G.NarutoShikamaruMass,ID='naruto-shikamaru-mass',out={};
 let {m,ledger,es,events,b}=A.conductionArena(),outside=A.spawn(700,0),outsideHits=A.watch(outside);
 A.assert(b.spec.cd===32&&b.spec.radius===260&&b.spec.shockPulses===3,'conduction changed cooldown/radius or pulse count');
 A.massWait(()=>es.every(M.held),2,'initial rays did not bind');A.assert(!events.length,'possession caused damage before conduction');
 const near=M.rayVisualFor(b,b.rays.get(es[0])).width,ray=A.conductionFlight(b),packet=ray.shocks.find(packet=>packet.progress>0&&!packet.done);
 A.assert(packet&&packet.progress<1&&!events.length&&M.stateFor(p).shockHits===0,'electric hurt preceded travelling front arrival');
 const early={castAge:b.age,conductAt:b.conductAt,progress:packet.progress,firstDuration:packet.duration,shockHits:0};
 const beforeProgress=packet.progress;A.step(.03);A.assert(packet.progress>beforeProgress&&packet.progress<1&&!events.length,'packet did not advance independently before hurt');
 A.massWait(()=>!!b.bomb,4,'bomb never followed conduction');
 A.assert(es.every(e=>{const r=b.rays.get(e);return r.shocks.length===3&&r.shocks.every(q=>q.done&&!q.cancelled)&&r.shockEvents.length===3}),'bomb launched before all initial circuits arrived');
 const lastShock=Math.max(...events.filter(e=>e.stage==='shock').map(e=>e.at));A.assert(lastShock<=b.age&&events.every(e=>e.stage==='shock'),'bomb fixture has premature explosion');
 const thin=M.rayVisualFor(b,ray).width;A.assert(thin<1&&near>thin+1,'captured spear did not settle into a thin tether');
 A.finish(b.blastAt-b.age+.04);
 A.assert(M.stateFor(p).shockHits===9&&M.stateFor(p).bombHits===3&&M.stateFor(p).hits===12,'three-target conduction ledger mismatch');
 for(const e of es){const hits=events.filter(h=>h.targetId===e.id);A.assert(hits.length===4&&hits.filter(h=>h.stage==='shock').length===3&&hits.filter(h=>h.stage==='bomb').length===1&&hits.every(h=>h.owner),'target did not receive 3 electric arrivals + 1 bomb');
  const spec=M.profile(p,m),electric=(G.Types?.mult?.('electric',e.types)??1)*(G.Weather?.mult?.('electric')??1),fire=(G.Types?.mult?.('fire',e.types)??1)*(G.Weather?.mult?.('fire')??1),expected=spec.damage*(3*.15*electric+.55*fire),actual=hits.reduce((n,h)=>n+h.raw,0);
  A.assert(Math.abs(actual-expected)<1e-6,'damage budget differs from the real electric/fire multipliers');
  const r=b.rays.get(e);A.assert(r.shockEvents.every((v,i)=>v.pulse===i+1&&v.at>=r.shocks[i].born+r.shocks[i].duration-1e-6),'hurt event predates its packet arrival');}
 A.assert(!A.massHits(outsideHits).length&&!b.rays.has(outside),'outside enemy joined the conduction');
 A.assert(M.stateFor(p).contacts.filter(c=>c.stage==='shock').length===9&&M.stateFor(p).contacts.filter(c=>c.stage==='bomb').length===3,'stage attribution missing from actual hurt contacts');
 out.sequence={ledger,early,nearWidth:near,heldWidth:thin,lastShock,bombObservedAt:b.throwAt,shockHits:9,bombHits:3,contacts:M.stateFor(p).contacts};

 ({m,b,es,events}=A.conductionArena(300));A.massWait(()=>!!b.bomb,5,'uncapped circuits blocked the bomb');A.finish(b.blastAt-b.age+.04);
 A.assert(b.rays.size===300&&es.every(e=>b.rays.get(e).shockEvents.length===3),'uncapped circuit count was capped');
 A.assert(M.stateFor(p).shockHits===900&&M.stateFor(p).bombHits===300&&M.stateFor(p).hits===1200,'uncapped native damage count was capped');
 A.assert(es.every(e=>events.filter(h=>h.targetId===e.id).length===4),'uncapped native hurt missing a real electric pulse or bomb');
 out.uncapped={targets:300,bosses:es.filter(e=>e.boss).length,rays:b.rays.size,shockHits:M.stateFor(p).shockHits,bombHits:M.stateFor(p).bombHits,totalHurt:events.length};

 ({b,es,events}=A.conductionArena(1));const movingRay=A.conductionFlight(b),movingPacket=movingRay.shocks.find(q=>!q.done&&q.progress>0),movingCenter={...b.center},progress=movingPacket.progress;
 p.x=-35;p.y=30;A.step(.02);A.assert(movingPacket.progress>progress&&movingPacket.progress<1,'moving source reset or instantly completed packet');
 A.assert(movingRay.source.x===p.x&&movingRay.source.y===p.y&&movingRay.bodyPoint.x===es[0].x&&movingRay.bodyPoint.y===es[0].y,'packet no longer follows the live conductor endpoints');
 const point=M.shockPoint(movingRay,movingPacket),u=movingPacket.progress;
 A.assert(Math.abs(point.x-(p.x+(es[0].x-p.x)*u))<1e-6&&Math.abs(point.y-(p.y+(es[0].y-p.y)*u))<1e-6&&Math.abs(point.z-movingRay.bodyPoint.z*u)<1e-6,'electric front departed from its actual straight wire');
 A.assert(b.center.x===movingCenter.x&&b.center.y===movingCenter.y,'source motion dragged the fixed field');
 A.massWait(()=>movingRay.shockEvents.length>=1,2,'moving circuit never arrived');const frozen=JSON.stringify(movingRay.shockEvents[0].point);p.x-=30;p.y+=30;A.step(.02);A.assert(frozen===JSON.stringify(movingRay.shockEvents[0].point),'settled electric contact followed the player');out.movingSource=true;

 ({b}=A.conductionArena(1));const readRay=A.conductionFlight(b),readPacket=readRay.shocks.find(q=>!q.done&&q.progress>0),canvas=document.createElement('canvas');canvas.width=canvas.height=600;const ctx=canvas.getContext('2d'),snapshot=A.conductionSnapshot(b);
 for(let i=0;i<30;i++){M.rayVisualFor(b,readRay);M.shockPoint(readRay,readPacket);G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx)}A.assert(snapshot===A.conductionSnapshot(b),'render/query advanced a packet or damage');out.readOnly=true;

 const lifecycle=[];for(const reason of ['pause','wall','clear','death','world','unlearn']){({b,es,events}=A.conductionArena(3));const r=A.conductionFlight(b),q=r.shocks.find(q=>!q.done&&q.progress>0);A.assert(!events.length,'lifecycle fixture already hurt');const world=G.World,age=b.age,front=q.progress;
  if(reason==='wall')G.World.projectilePathClear=()=>false;if(reason==='clear')S.clear(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};if(reason==='unlearn')p.moves=[];
  try{if(reason==='pause'){S.update(5);A.assert(b.age===age&&q.progress===front,'pause advanced a travelling front');}else A.finish(7);A.assert(!events.length,'cancelled conductor leaked a future electric/bomb hit '+reason)}finally{p.dead=false;G.World=world}
  lifecycle.push(reason);
 }out.lifecycle=lifecycle;

 const callbacks=[];for(const stage of ['shock','bomb'])for(const callback of ['hurt','onDealt']){({b,es}=A.conductionArena(3));
  if(stage==='shock')A.conductionFlight(b);else{A.massWait(()=>!!b.bomb,5,'bomb callback fixture not charged');A.finish(Math.max(0,b.blastAt-b.age-.03));}
  let count=0;const dealt=p.onDealt;
  for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const result=hurt.apply(this,args);if(args[7]===ID){count++;if(callback==='hurt'&&count===1)S.clear(p)}return result}}
  if(callback==='onDealt')p.onDealt=()=>{if(count)S.clear(p)};
  try{A.finish(7);A.assert(count===1&&!M.casts.length&&es.every(e=>!M.held(e)),'first '+stage+' '+callback+' did not cancel same-wave second target/future packets')}finally{p.onDealt=dealt}
  callbacks.push({stage,callback,hurt:count});
 }out.callbacks=callbacks;

 ({m,b,es}=A.conductionArena(1));const clone=G.SelfClones.summon(p);A.assert(clone,'native clone unavailable');clone.x=clone.y=0;const cloneMove=clone.moves.find(m=>m.id===ID);A.resume();try{A.assert(M.cast(clone,cloneMove),'clone conduction cast rejected')}finally{A.pause()}
 A.massWait(()=>M.leases.get(es[0])?.size===2,2,'owner circuits did not share target independently');let main=0,other=0;const hurt=es[0].hurt;es[0].hurt=function(...args){const result=hurt.apply(this,args);if(args[7]===ID){if(args[6]===p)main++;else if(args[6]===clone)other++;}return result};
 S.clear(p);A.assert(M.held(es[0]),'clearing main released clone circuit');A.finish(7);A.assert(main===0&&other===4,'owner cleanup crossed into clone conduction or damage');out.ownerIsolation={mainHits:main,cloneHits:other};
 return out;
}'''


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    digest=lambda:hashlib.sha256((base.ROOT/SOURCE).read_bytes()).hexdigest()
    report={'controlled':True,'sourceBefore':digest(),'errors':[],'checks':{}}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
            page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block')
            page.on('pageerror',lambda error:report['errors'].append(str(error)))
            base.boot(page)
            page.evaluate('window.ConductionWarmEnemy=Acceptance.spawn(1000,1000)')
            page.wait_for_function('!!G.ShikamaruReferenceGeometry.bodyFor(ConductionWarmEnemy)')
            page.evaluate(mass.SETUP);page.evaluate(SETUP)
            report['checks']=page.evaluate(CHECK)
            browser.close()
        assert not report['errors'],report['errors']
        report['ok']=True
        print('Conduction: arrival-gated 3 shocks + bomb, 300 targets, movement, lifecycle and callbacks PASS')
    except Exception as error:
        report['failure']=str(error)
        raise
    finally:
        report['sourceAfter']=digest();report['sourceStable']=report['sourceBefore']==report['sourceAfter']
        (OUT/'mechanics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')


if __name__=='__main__':main()
