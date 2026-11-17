"""Controlled production-entry acceptance for uncapped mass shadow possession.

Native actors, hurt, stopped/contact gates and actual upgrade cards are used.
The open arena and manual sim stepping are explicit fixtures, not natural play.
"""
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_shikamaru as base

OUT = base.ROOT / 'art-review/shikamaru/qa/mass'
SOURCES = ['.omx/naruto-shikamaru-mass.js', '.omx/naruto-skills.js',
           '.omx/jujutsu-growth.js', '.omx/naruto.js', '.omx/digimon.html']

SETUP = r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,M=G.NarutoShikamaruMass,ID='naruto-shikamaru-mass';
 A.assert(M,'production mass module absent');
 A.massBuild=(rank=1,q=0)=>{A.reset();p.statsTaken={};p.level=6;p.moves=[G.Moves.instance('naruto-shikamaru')];
  const ledger=[],c=G.LevelUp.offer(p,1000).find(c=>c.key==='new:'+ID);A.assert(c&&c.apply(p)!==false,'real Lv6 learn card missing');ledger.push(c.key);
  for(let i=1;i<rank;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+ID);A.assert(c&&c.apply(p)!==false,'mass upgrade card missing');ledger.push(c.key)}
  for(let i=0;i<q;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');A.assert(c&&c.apply(p)!==false,'real quantity card missing');ledger.push(c.key)}
  const m=p.moves.find(m=>m.id===ID);p.moves=[m];return {m,ledger};
 };
 A.massCast=()=>{const m=p.moves.find(m=>m.id===ID);A.resume();try{A.assert(M.cast(p,m),'self-centered mass cast rejected')}finally{A.pause()}const b=M.casts.at(-1);A.assert(b.center.x===p.x&&b.center.y===p.y,'mass field not centered on caster start');return b};
 A.massWait=(condition,limit=3,message='mass phase did not complete')=>{for(let i=0;i<Math.ceil(limit/.01)&&!condition();i++)A.step(.01);A.assert(condition(),message)};
 A.massHits=hits=>hits.filter(h=>h.id===ID);
 A.massTick=dt=>{A.resume();try{G.Combat.tick(dt,p,0)}finally{A.pause()}};
}'''

CHECK = r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,M=G.NarutoShikamaruMass,ID='naruto-shikamaru-mass',out={};
 A.reset();p.moves=[G.Moves.instance('naruto-shikamaru')];p.level=5;A.assert(!G.LevelUp.offer(p,1000).some(c=>c.key==='new:'+ID),'mass offered before Lv6');
 const growth=[];for(const [rank,q]of [[1,0],[1,1],[3,0],[5,12]]){const {m,ledger}=A.massBuild(rank,q),profile=M.profile(p,m),card=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');growth.push({rank,q,ledger,profile});A.assert(profile.cd===32,'skill upgrade lowered long cooldown');if(q===0)A.assert(card?.desc.includes('圓區半徑'),'quantity preview misses real mass radius')}
 A.assert(growth[0].profile.radius===260&&growth[1].profile.radius===265&&growth[2].profile.radius===300&&growth[3].profile.radius===400,'radius consumer disagrees with profile');out.growth=growth;

 let {m,ledger}=A.massBuild(),es=Array.from({length:300},(_,i)=>{const angle=i*2.399963229728653,r=20+210*Math.sqrt(i/300);return A.spawn(Math.cos(angle)*r,Math.sin(angle)*r,i%75===0)}),hits=es.map(A.watch),outside=A.spawn(650,0),outsideHits=A.watch(outside),b=A.massCast();
 A.assert(!b.rays.size&&es.every(e=>!M.held(e)),'instant ray/possession at cast');A.finish(b.spec.prepare-.03);A.assert(!b.rays.size&&es.every(e=>!M.held(e)),'ray/possession before preparation');
 const rayEvidence=[];A.massWait(()=>{for(const e of es)if(M.held(e)){const ray=b.rays.get(e);A.assert(ray?.contact&&Number.isFinite(ray.contactAge)&&Number.isFinite(ray.boundAt)&&ray.contactAge<=ray.boundAt,'held without prior body sweep contact');const dx=e.x-ray.source.x,dy=e.y-ray.source.y,d=Math.hypot(dx,dy)||1,reach=((ray.current.x-ray.source.x)*dx+(ray.current.y-ray.source.y)*dy)/d;A.assert(reach>d+(e.r||0),'held before tip extended beyond victim body');}return es.every(M.held)},2,'uncapped rays did not bind every victim');
 A.assert(b.bound.size===300&&b.rays.size===300&&es.every(e=>M.held(e)&&S.held(e)&&S.stopped(e)),'uncapped per-target rays missing '+b.bound.size+'/'+b.rays.size);
 A.assert(!b.bomb,'bomb released before confirming initial possession');for(const e of es){const ray=b.rays.get(e);rayEvidence.push({targetId:e.id,contactAge:ray.contactAge,boundAt:ray.boundAt,contact:{...ray.contact}})}
 A.assert(!M.held(outside),'outside circle possessed');const heldAtFull=b.bound.size;
 A.assert(b.conductAt!==null&&b.age<b.conductAt&&hits.every(h=>A.massHits(h).length===0),'capture dealt damage before conduction phase');A.massWait(()=>!!b.bomb,3,'bomb did not follow completed possession');A.assert([...b.initialTargets].every(e=>{const r=b.rays.get(e);return r?.hit&&r.shocks.length===6&&r.shocks.every(packet=>packet.done)&&r.shockEvents.length===6}),'bomb released before every valid victim received six travelling electric pulses');out.bindBeforeBomb={lastBoundAt:Math.max(...rayEvidence.map(r=>r.boundAt)),throwAt:b.throwAt,bombObservedAt:b.age};A.assert(out.bindBeforeBomb.lastBoundAt<=out.bindBeforeBomb.throwAt,'bomb schedule precedes final binding');A.finish(b.blastAt-b.age+.05);
 A.assert(b.exploded&&b.hitSet.size===300,'single terminal explosion missed target count '+b.hitSet.size);
 A.assert(hits.every(h=>A.massHits(h).length===7&&A.massHits(h).every(event=>event.owner)),'uncapped six-shock plus one-bomb attribution wrong');A.assert(!A.massHits(outsideHits).length,'out-of-circle explosion damage');
 const expected=M.profile(p,m),perTargetRaw=hits.map(h=>A.massHits(h).map(event=>event.raw)),perTargetLoss=hits.map(h=>A.massHits(h).reduce((sum,event)=>sum+event.loss,0)),lowDamage=Math.max(...perTargetRaw.map(raw=>raw.reduce((sum,n)=>sum+n,0))),oldShock=Math.round(expected.damage*.15);
 A.assert(perTargetRaw.every(raw=>raw.slice(0,6).every((n,i)=>n===Math.max(1,i%2?Math.ceil(oldShock/2):Math.floor(oldShock/2)))&&Math.abs(raw[6]-expected.damage*.55)<1e-6),'electric pair rounding or bomb damage differs from profile');
 const oldTotalLoss=3*Math.max(1,oldShock)+Math.max(1,Math.round(expected.damage*.55));A.assert(perTargetLoss.every(loss=>loss===oldTotalLoss),'six shocks plus bomb changed actual HP loss');
 A.assert(expected.shockPulses===6&&Math.abs(expected.shockScale-.075)<1e-8&&Math.abs(expected.shockScale*6+expected.bombScale-1)<1e-8&&Math.abs(M.stateFor(p).damage-expected.damage*300)<1e-6,'six shocks plus bomb changed nominal damage budget');A.finish(b.duration-b.age+.2);A.assert(!M.casts.length&&es.every(e=>!M.held(e)),'full window did not release everyone');
 A.assert(M.stateFor(p).hits===2100&&M.stateFor(p).shockHits===1800&&M.stateFor(p).bombHits===300,'telemetry hit cap became gameplay cap');out.uncapped={targets:300,bosses:es.filter(e=>e.boss).length,heldAtFull,hits:M.stateFor(p).hits,shockHits:M.stateFor(p).shockHits,bombHits:M.stateFor(p).bombHits,oneBomb:!!b.bomb,oneExplosion:b.exploded,perTargetRaw:lowDamage,perTargetLoss:perTargetLoss[0],normalizedBaseNominal:M.stateFor(p).damage/(300*(p.atk??1)),damageSplit:{shocks:perTargetRaw[0].slice(0,6),bomb:perTargetRaw[0][6]},ledger,individualRays:b.rays.size,rayEvidence};

 ({m}=A.massBuild());const target=A.spawn(200,0),late=A.spawn(620,0);b=A.massCast();A.massWait(()=>M.held(target),2,'entry fixture target not bound');A.assert(!M.held(late),'entry fixture outside victim already bound');late.x=220;late.y=40;G.EnemyMgr.rebuildGrid();A.step(.01);A.assert(b.rays.has(late)&&!M.held(late),'late target bound without a travelling ray');A.massWait(()=>M.held(late),1,'enemy entering circle was not hit/bound by its new ray');out.lateEntry=true;

 const invalidInitial=[];for(const reason of ['death','outside','wall']){({m}=A.massBuild());const live=A.spawn(180,0),invalid=A.spawn(235,40);b=A.massCast();A.assert(b.initialTargets.size===2,'invalid-target fixture was not acquired');
  if(reason==='death'){invalid.hp=0;invalid.dead=true}if(reason==='outside'){invalid.x=600;G.EnemyMgr.rebuildGrid()}if(reason==='wall')G.World.projectilePathClear=(ax,ay,bx,by)=>by<=20;
  A.massWait(()=>!!b.bomb,3,'invalid initial target blocked bomb forever '+reason);A.assert(M.held(live)&&!M.held(invalid),'bomb skipped still-valid target or bound invalid one '+reason);invalidInitial.push(reason);
 }out.invalidInitial=invalidInitial;

 ({m}=A.massBuild());es=[A.spawn(200,0),A.spawn(225,0,true)];b=A.massCast();A.massWait(()=>es.every(M.held),2,'native control targets not bound');
 const native=[];for(const e of es){e.spd=120;e.dmg=40;e.kx=300;e.ky=-250;e.shotCd=0;const before={x:e.x,y:e.y};A.resume();try{e.update(.2,p)}finally{A.pause()}A.assert(e.x===before.x&&e.y===before.y&&e._yutaSpeechStopped===true,'native enemy AI did not enter stopped gate '+e.boss);native.push({boss:e.boss,stopped:e._yutaSpeechStopped,x:e.x,y:e.y})}
 p.x=es[0].x;p.y=es[0].y;p.flash=p.invuln=0;es[0].touchCd=0;const hp=p.hp;A.resume();try{G.Combat.resolve(.02,p,0)}finally{A.pause()}A.assert(p.hp===hp,'bound native target caused contact damage');out.nativeControl={native,contactHpStable:true};

 ({m}=A.massBuild());A.spawn(200,0);b=A.massCast();const center={...b.center},origin={...b.origin};A.massWait(()=>b.bound.size===1,2,'fixed circle target not bound');p.x=-45;p.y=35;A.massWait(()=>!!b.bomb,3,'bomb not released after confirmed binds');const source={...b.bomb.source};p.x=-140;p.y=90;A.step(.2);A.assert(JSON.stringify(center)===JSON.stringify(b.center)&&JSON.stringify(origin)===JSON.stringify(b.origin),'circle/cast origin dragged with body');A.assert(JSON.stringify(source)===JSON.stringify(b.bomb.source),'in-flight bomb dragged with body');out.fixedGeometry={center,origin,source};

 ({m}=A.massBuild());A.spawn(200,0);b=A.massCast();A.massWait(()=>!M.casts.includes(b),6,'long CD fixture did not complete conduction/bomb/release');A.assert(M.stateFor(p).cooldown===32&&!M.canCast(p,m),'manual update incorrectly reset cast cooldown');A.massTick(31.5);A.assert(M.stateFor(p).casts===1&&Math.abs(M.stateFor(p).cooldown-.5)<1e-6,'long cooldown elapsed early');A.massTick(.51);A.assert(M.stateFor(p).casts===2,'native tick failed to recast after cooldown');out.cooldown={seconds:32,recastAfter32:true};

 ({m}=A.massBuild());const visible=A.spawn(200,-40),wallBehind=A.spawn(200,90),wh=A.watch(wallBehind);G.World.projectilePathClear=(ax,ay,bx,by)=>!((ay<40&&by>40)||(ay>40&&by<40));b=A.massCast();A.massWait(()=>M.held(visible),2,'visible wall fixture not reached');A.assert(M.held(visible)&&!M.held(wallBehind),'field possession crossed wall');A.massWait(()=>!!b.bomb,3,'wall fixture conduction did not finish');A.finish(b.blastAt-b.age+.03);A.assert(b.exploded&&!A.massHits(wh).length,'electric/bomb damage crossed wall');out.wall=true;

 for(const reason of ['clear','death','world','unlearn','pause']){({m}=A.massBuild());es=[A.spawn(200,0),A.spawn(230,20)];hits=es.map(A.watch);b=A.massCast();A.massWait(()=>es.every(M.held),2,'cleanup fixture missing ray binding');const world=G.World,age=b.age;
  if(reason==='clear')S.clear(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};if(reason==='unlearn')p.moves=[];
  try{if(reason==='pause'){S.update(10);A.assert(b.age===age,'paused fields advanced');}else{A.finish(6);A.assert(!M.casts.length&&es.every(e=>!M.held(e)),'lifecycle left leases/casts '+reason)}A.assert(hits.every(h=>!A.massHits(h).length),'lifecycle leaked pending bomb damage '+reason)}finally{p.dead=false;G.World=world}
 }out.lifecycle=true;

 for(const callback of ['hurt','onDealt']){({m}=A.massBuild());es=[A.spawn(200,0),A.spawn(230,20)];b=A.massCast();A.massWait(()=>es.every(M.held),2,'callback targets not bound');A.massWait(()=>!!b.bomb,3,'callback fixture did not finish conduction');A.finish(b.blastAt-b.age-.04);let count=0;const dealt=p.onDealt;
  for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const result=hurt.apply(this,args);if(args[7]===ID){count++;if(callback==='hurt')S.clear(p)}return result}}
  if(callback==='onDealt')p.onDealt=()=>{if(count)S.clear(p)};
  try{A.finish(2);A.assert(count===1&&!M.casts.length&&es.every(e=>!M.held(e)),'first callback failed to cancel same-wave damage '+callback)}finally{p.onDealt=dealt}
 }out.callbacks=true;

 ({m}=A.massBuild());const overlap=A.spawn(200,0),clone=G.SelfClones.summon(p);A.assert(clone,'native self clone unavailable');clone.x=0;clone.y=0;const cloneMove=clone.moves.find(m=>m.id===ID);A.assert(cloneMove,'clone did not inherit skill');b=A.massCast();A.resume();try{A.assert(M.cast(clone,cloneMove),'clone field rejected')}finally{A.pause()}A.massWait(()=>M.leases.get(overlap)?.size===2,2,'overlap rays did not reach target');A.assert(M.leases.get(overlap)?.size===2,'overlapping owners did not have separate leases');S.clear(p);A.assert(M.held(overlap)&&M.leases.get(overlap)?.size===1,'clearing one owner released other field');S.clear(clone);A.assert(!M.held(overlap),'last owner cleanup left lease');out.ownerIsolation=true;

 ({m}=A.massBuild());A.spawn(200,0);b=A.massCast();A.massWait(()=>b.bound.size===1,2,'render fixture missing ray binding');A.massWait(()=>[...b.rays.values()].some(ray=>ray.shocks.some(packet=>!packet.done&&packet.progress>0)),2,'render fixture has no travelling electric packet');const canvas=document.createElement('canvas');canvas.width=canvas.height=600;const ctx=canvas.getContext('2d'),snapshot=()=>JSON.stringify({age:b.age,captured:M.stateFor(p).captured,hits:M.stateFor(p).hits,bound:b.bound.size,bomb:b.bomb,conductAt:b.conductAt,shocks:[...b.rays.values()].map(ray=>({shocks:ray.shocks.map(packet=>({...packet})),events:ray.shockEvents.map(event=>({...event}))}))}),before=snapshot();for(let i=0;i<15;i++){G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx)}A.assert(snapshot()===before,'drawing changed simulation/damage');out.readOnly=true;
 ({m}=A.massBuild());A.spawn(200,0);A.resume();try{A.assert(M.cast(p,m,{x:190,y:20})!==false,'extra argument unexpectedly blocked self-centered cast')}finally{A.pause()}b=M.casts.at(-1);A.assert(b.center.x===0&&b.center.y===0,'arbitrary remote point displaced self-centered cast');out.selfCenter=true;
 ({m}=A.massBuild());A.spawn(180,0);const hintCanvas=document.createElement('canvas');hintCanvas.width=hintCanvas.height=600;const hintCtx=hintCanvas.getContext('2d');hintCtx.translate(300,300);
 const sampleHint=radius=>[.5,.98].map(t=>hintCtx.getImageData(Math.floor(300+radius*t),300,1,1).data[3]);G.Combat.drawGroundFields(hintCtx);const baselineHint=sampleHint(M.profile(p,m).radius);b=A.massCast();A.step(.05);A.assert(!b.rays.size&&!b.bound.size,'range hint fixture already has ray/bound decoration');hintCtx.clearRect(-300,-300,600,600);G.Combat.drawGroundFields(hintCtx);const afterHint=sampleHint(b.radius),alpha=afterHint.map((v,i)=>v-baselineHint[i]);
 A.assert(alpha[0]>0&&alpha[0]<=13&&alpha[1]>=0&&alpha[1]<alpha[0],'range hint became an opaque/sharp disk '+JSON.stringify({baselineHint,afterHint,alpha}));out.faintRangeHint={baseline:baselineHint,after:afterHint,alpha};
 ({m}=A.massBuild());const largeBoss=A.spawn(180,0,true);largeBoss.r=52;largeBoss.bodyH=100;const Ref=G.ShikamaruReferenceGeometry,initialBody=Ref.bodyFor(largeBoss);if(initialBody)largeBoss.anim.scale*=100/initialBody.bodyHeight;b=A.massCast();const largeHits=A.watch(largeBoss);A.massWait(()=>M.held(largeBoss),2,'large boss not pierced/bound');const largeRay=b.rays.get(largeBoss),largeBody=Ref.bodyFor(largeBoss),largeReach=Math.hypot(largeRay.current.x-largeRay.source.x,largeRay.current.y-largeRay.source.y);
 A.assert(largeRay.contact&&largeRay.contactAge<=largeRay.boundAt&&largeReach>180+largeBoss.r,'large boss bound without actual overrun');A.assert(largeRay.contact.z<=largeBody.bodyHeight+2&&b.age<b.conductAt&&!A.massHits(largeHits).length,'large boss contact above body or damage before conduction');out.largeBoss={radius:largeBoss.r,bodyH:largeBoss.bodyH,alphaHeight:largeBody.bodyHeight,contact:largeRay.contact,contactAge:largeRay.contactAge,boundAt:largeRay.boundAt,tipReach:largeReach};
 return out;
}'''


def manifest():
    return {name: hashlib.sha256((base.ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'controlled': True, 'sourceBefore': manifest(), 'errors': [], 'checks': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            page = browser.new_page(viewport={'width':1100,'height':850}, service_workers='block')
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            base.boot(page)
            page.wait_for_function('!!G.NarutoShikamaruMass')
            page.evaluate('window.MassWarmEnemy=Acceptance.spawn(1000,1000)')
            page.wait_for_function('!!G.ShikamaruReferenceGeometry.bodyFor(MassWarmEnemy)')
            page.evaluate(SETUP)
            report['checks'] = page.evaluate(CHECK)
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
        print('Mass possession: 300 targets, native control, damage, cooldown, lifecycle and ownership PASS')
    except Exception as error:
        report['failure'] = str(error)
        raise
    finally:
        report['sourceAfter'] = manifest()
        report['sourceStable'] = report['sourceBefore'] == report['sourceAfter']
        (OUT/'mechanics.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')


if __name__ == '__main__':
    main()
