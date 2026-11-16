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
 A.massCast=(center={x:200,y:0})=>{const m=p.moves.find(m=>m.id===ID);A.resume();try{A.assert(M.cast(p,m,center),'specified mass cast rejected')}finally{A.pause()}return M.casts.at(-1)};
 A.massHits=hits=>hits.filter(h=>h.id===ID);
 A.massTick=dt=>{A.resume();try{G.Combat.tick(dt,p,0)}finally{A.pause()}};
}'''

CHECK = r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,M=G.NarutoShikamaruMass,ID='naruto-shikamaru-mass',out={};
 A.reset();p.moves=[G.Moves.instance('naruto-shikamaru')];p.level=5;A.assert(!G.LevelUp.offer(p,1000).some(c=>c.key==='new:'+ID),'mass offered before Lv6');
 const growth=[];for(const [rank,q]of [[1,0],[1,1],[3,0],[5,12]]){const {m,ledger}=A.massBuild(rank,q),profile=M.profile(p,m),card=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');growth.push({rank,q,ledger,profile});A.assert(profile.cd===32,'skill upgrade lowered long cooldown');if(q===0)A.assert(card?.desc.includes('圓區半徑'),'quantity preview misses real mass radius')}
 A.assert(growth[0].profile.radius===260&&growth[1].profile.radius===265&&growth[2].profile.radius===300&&growth[3].profile.radius===400,'radius consumer disagrees with profile');out.growth=growth;

 let {m,ledger}=A.massBuild(),es=Array.from({length:300},(_,i)=>{const angle=i*2.399963229728653,r=20+210*Math.sqrt(i/300);return A.spawn(200+Math.cos(angle)*r,Math.sin(angle)*r,i%75===0)}),hits=es.map(A.watch),outside=A.spawn(650,0),outsideHits=A.watch(outside),b=A.massCast();
 A.assert(es.every(e=>!M.held(e)),'instant possession before shadow flight');A.finish(b.arrive-.03);A.assert(es.every(e=>!M.held(e)),'shadow captured before arriving');
 A.finish(b.full-b.age+.05);A.assert(b.bound.size===300&&es.every(e=>M.held(e)&&S.held(e)&&S.stopped(e)),'uncapped circle missed enemies/bosses '+b.bound.size);
 A.assert(!M.held(outside),'outside circle possessed');const heldAtFull=b.bound.size;
 A.assert(hits.every(h=>A.massHits(h).length===0),'capture itself dealt damage');A.finish(b.blastAt-b.age+.05);
 A.assert(b.exploded&&b.hitSet.size===300,'single terminal explosion missed target count '+b.hitSet.size);
 A.assert(hits.every(h=>A.massHits(h).length===1&&A.massHits(h)[0].owner),'uncapped one-hit attribution wrong');A.assert(!A.massHits(outsideHits).length,'out-of-circle explosion damage');
 const lowDamage=Math.max(...hits.map(h=>A.massHits(h)[0].raw));A.assert(Math.abs(lowDamage-M.profile(p,m).damage)<1e-6,'explosion damage exceeded advertised low damage');A.finish(b.duration-b.age+.2);A.assert(!M.casts.length&&es.every(e=>!M.held(e)),'full window did not release everyone');
 A.assert(M.stateFor(p).hits===300,'telemetry hit cap became gameplay cap');out.uncapped={targets:300,bosses:es.filter(e=>e.boss).length,heldAtFull,hits:M.stateFor(p).hits,oneBomb:!!b.bomb,oneExplosion:b.exploded,perTargetRaw:lowDamage,ledger};

 ({m}=A.massBuild());const target=A.spawn(200,0),late=A.spawn(620,0);b=A.massCast();A.finish(b.full+.03);A.assert(M.held(target)&&!M.held(late),'entry fixture bad');late.x=220;late.y=40;G.EnemyMgr.rebuildGrid();A.step(.03);A.assert(M.held(late),'enemy entering live circle not captured');out.lateEntry=true;

 ({m}=A.massBuild());es=[A.spawn(200,0),A.spawn(225,0,true)];b=A.massCast();A.finish(b.full+.03);
 const native=[];for(const e of es){e.spd=120;e.dmg=40;e.kx=300;e.ky=-250;e.shotCd=0;const before={x:e.x,y:e.y};A.resume();try{e.update(.2,p)}finally{A.pause()}A.assert(e.x===before.x&&e.y===before.y&&e._yutaSpeechStopped===true,'native enemy AI did not enter stopped gate '+e.boss);native.push({boss:e.boss,stopped:e._yutaSpeechStopped,x:e.x,y:e.y})}
 p.x=es[0].x;p.y=es[0].y;p.flash=p.invuln=0;es[0].touchCd=0;const hp=p.hp;A.resume();try{G.Combat.resolve(.02,p,0)}finally{A.pause()}A.assert(p.hp===hp,'bound native target caused contact damage');out.nativeControl={native,contactHpStable:true};

 ({m}=A.massBuild());A.spawn(200,0);b=A.massCast();const center={...b.center},origin={...b.origin};p.x=-45;p.y=35;A.finish(b.throwAt+.03);A.assert(b.bomb,'bomb not released');const source={...b.bomb.source};p.x=-140;p.y=90;A.step(.2);A.assert(JSON.stringify(center)===JSON.stringify(b.center)&&JSON.stringify(origin)===JSON.stringify(b.origin),'circle/cast origin dragged with body');A.assert(JSON.stringify(source)===JSON.stringify(b.bomb.source),'in-flight bomb dragged with body');out.fixedGeometry={center,origin,source};

 ({m}=A.massBuild());A.spawn(200,0);b=A.massCast();A.finish(b.duration+.03);A.assert(M.stateFor(p).cooldown===32&&!M.canCast(p,m),'manual update incorrectly reset cast cooldown');A.massTick(31.5);A.assert(M.stateFor(p).casts===1&&Math.abs(M.stateFor(p).cooldown-.5)<1e-6,'long cooldown elapsed early');A.massTick(.51);A.assert(M.stateFor(p).casts===2,'native tick failed to recast after cooldown');out.cooldown={seconds:32,recastAfter32:true};

 ({m}=A.massBuild());const visible=A.spawn(200,-40),wallBehind=A.spawn(200,90),wh=A.watch(wallBehind);G.World.projectilePathClear=(ax,ay,bx,by)=>!((ay<40&&by>40)||(ay>40&&by<40));b=A.massCast({x:200,y:0});A.finish(b.full+.03);A.assert(M.held(visible)&&!M.held(wallBehind),'field possession crossed wall');A.finish(b.blastAt-b.age+.03);A.assert(!A.massHits(wh).length,'bomb blast crossed wall');out.wall=true;

 for(const reason of ['clear','death','world','unlearn','pause']){({m}=A.massBuild());es=[A.spawn(200,0),A.spawn(230,20)];hits=es.map(A.watch);b=A.massCast();A.finish(b.full+.03);A.assert(es.every(M.held),'cleanup fixture missing binding');const world=G.World,age=b.age;
  if(reason==='clear')S.clear(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};if(reason==='unlearn')p.moves=[];
  try{if(reason==='pause'){S.update(10);A.assert(b.age===age,'paused fields advanced');}else{A.finish(6);A.assert(!M.casts.length&&es.every(e=>!M.held(e)),'lifecycle left leases/casts '+reason)}A.assert(hits.every(h=>!A.massHits(h).length),'lifecycle leaked pending bomb damage '+reason)}finally{p.dead=false;G.World=world}
 }out.lifecycle=true;

 for(const callback of ['hurt','onDealt']){({m}=A.massBuild());es=[A.spawn(200,0),A.spawn(230,20)];b=A.massCast();A.finish(b.blastAt-.04);let count=0;const dealt=p.onDealt;
  for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const result=hurt.apply(this,args);if(args[7]===ID){count++;if(callback==='hurt')S.clear(p)}return result}}
  if(callback==='onDealt')p.onDealt=()=>{if(count)S.clear(p)};
  try{A.finish(2);A.assert(count===1&&!M.casts.length&&es.every(e=>!M.held(e)),'first callback failed to cancel same-wave damage '+callback)}finally{p.onDealt=dealt}
 }out.callbacks=true;

 ({m}=A.massBuild());const overlap=A.spawn(200,0),clone=G.SelfClones.summon(p);A.assert(clone,'native self clone unavailable');clone.x=0;clone.y=0;const cloneMove=clone.moves.find(m=>m.id===ID);A.assert(cloneMove,'clone did not inherit skill');b=A.massCast();A.resume();try{A.assert(M.cast(clone,cloneMove,{x:200,y:0}),'clone field rejected')}finally{A.pause()}A.finish(b.full+.03);A.assert(M.leases.get(overlap)?.size===2,'overlapping owners did not have separate leases');S.clear(p);A.assert(M.held(overlap)&&M.leases.get(overlap)?.size===1,'clearing one owner released other field');S.clear(clone);A.assert(!M.held(overlap),'last owner cleanup left lease');out.ownerIsolation=true;

 ({m}=A.massBuild());A.spawn(200,0);b=A.massCast();A.finish(b.full+.03);const canvas=document.createElement('canvas');canvas.width=canvas.height=600;const ctx=canvas.getContext('2d'),snapshot=()=>JSON.stringify({age:b.age,captured:M.stateFor(p).captured,hits:M.stateFor(p).hits,bound:b.bound.size,bomb:b.bomb}),before=snapshot();for(let i=0;i<15;i++){G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx)}A.assert(snapshot()===before,'drawing changed simulation/damage');out.readOnly=true;
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
