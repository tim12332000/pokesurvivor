"""Roaming tornado acceptance through native learning, fields, damage and rendering."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_temari import CHROME, URL, boot

OUT = Path(__file__).resolve().parents[1] / '.omx/state/temari-roaming'

FIXTURE = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.roamId='naruto-temari-roaming';
 A.roamReset=(rank=1,Q=0)=>{A.reset();p.moves=p.moves.filter(m=>m.id==='naruto-temari');
   p.level=4;A.assert(p.addMove(A.roamId),'native add roaming');A.rank(A.roamId,rank);
   p.quantityBonus=p.quantityPicks=Q;return p.moves.find(m=>m.id===A.roamId)};
 A.roamStep=(dt=.01)=>{A.resume();try{G.Combat.updateFields(dt);G.FX.update(dt);p.anim.update(dt)}finally{A.pause()}};
 A.roamStart=()=>{A.roamStep(.001);A.assert(T.roamers.length,'passive failed to spawn');return T.roamers[0]};
}"""

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out={};A.reset();
 p.moves=p.moves.filter(m=>m.id==='naruto-temari');
 out.levels=[];for(const level of [3,4]){p.level=level;const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+A.roamId);
   A.assert(!!card===(level===4),'Lv4 learning gate '+level);if(card)A.assert(card.apply(p)!==false,'native learn');out.levels.push({level,eligible:!!card})}
 A.assert(p.moves.find(m=>m.id===A.roamId).passive&&!p.slots.some(g=>g.some(m=>m.id===A.roamId)),'roaming consumed active slot');
 for(const dex of [30001,30006,30009,30010])A.assert(!G.Moves.poolFor(G.DEX.find(m=>m.dex===dex)).includes(A.roamId),'pool leaked '+dex);
 out.growth=[];for(const [rank,Q] of [[1,0],[2,0],[1,1],[5,20]]){const m=A.roamReset(rank,Q),profile=T.roamingProfile(p,m);A.roamStart();
   A.assert(T.roamers.length===Math.min(12,rank+Q),'physical count differs '+rank+'/'+Q);
   out.growth.push({rank,Q,profile,count:T.roamers.length,damage:m.dmg})}
 A.roamReset();const tornado=A.roamStart(),start={x:tornado.x,y:tornado.y},path=[];
 const far=A.spawn(2000,2000),farHp=far.hp;
 for(let i=0;i<100;i++){A.roamStep(.01);if(i%10===0)path.push({x:tornado.x,y:tornado.y})}
 A.assert(Math.hypot(tornado.x-start.x,tornado.y-start.y)>40,'tornado did not roam');
 A.assert(far.hp===farHp,'distant enemy damaged');out.movement={start,path};
 // Real enemy follows the moving footprint to isolate the per-target contact clock.
 const enemy=A.spawn(tornado.x,tornado.y),hits=A.watch(enemy),times=[];let last=0;
 for(let i=0;i<105;i++){enemy.x=tornado.x;enemy.y=tornado.y;G.EnemyMgr.rebuildGrid();A.roamStep(.01);
   if(hits.length!==last){times.push(i*.01);last=hits.length}}
 A.assert(hits.length>=3&&hits.length<=4,'contact repeat cadence '+hits.length);
 A.assert(times.slice(1).every((time,i)=>time-times[i]>=.39),'damage every frame');
 A.assert(hits.every(h=>h.id===A.roamId&&h.owner&&h.damage>0),'native damage ownership missing');out.contact={times,hits};
 A.roamReset();const paused=A.roamStart(),before={x:paused.x,y:paused.y,age:paused.age};T.update(.5);
 A.assert(paused.x===before.x&&paused.y===before.y&&paused.age===before.age,'pause advanced tornado');
 out.lifecycle=['pause'];for(const mode of ['clear','dead','unlearn','world']){A.roamReset();const old=A.roamStart();
   if(mode==='clear')T.clear(p);
   if(mode==='dead'){p.dead=true;A.roamStep(.01);p.dead=false}
   if(mode==='unlearn'){p.moves=p.moves.filter(m=>m.id!==A.roamId);A.roamStep(.01)}
   if(mode==='world'){const world=G.World;try{G.World=Object.create(world);A.roamStep(.01)}finally{G.World=world}}
   A.assert(!T.roamers.includes(old)&&(mode==='world'||!T.roamers.length),'stale tornado after '+mode);out.lifecycle.push(mode)}
 A.roamReset();const finite=A.roamStart();for(let i=0;i<510;i++)A.roamStep(.01);
 A.assert(!T.roamers.includes(finite),'expired tornado retained');out.expiry=true;
 A.roamReset();const cancel=A.roamStart(),targets=[A.spawn(cancel.x,cancel.y),A.spawn(cancel.x,cancel.y)],native=targets[0].hurt;
 targets[0].hurt=function(...args){const result=native.apply(this,args);T.clear(p);return result};
 A.roamStep(.01);A.assert(targets[0].hp<targets[0].maxHp&&targets[1].hp===targets[1].maxHp&&!T.roamers.length,'callback cancellation damaged second enemy');
 out.callbackCancellation=true;
 const growthMove=A.roamReset();(p.statsTaken??={}).quantity=0;
 const preview=G.JujutsuGrowth.quantityBenefit(p).consumers.find(c=>c.id===A.roamId);
 A.assert(preview&&preview.before['小龍捲']===1&&preview.after['小龍捲']===2,'quantity card preview disagrees');
 const quantity=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');
 A.assert(quantity&&quantity.apply(p)!==false&&T.roamingProfile(p,growthMove).count===2,'native quantity card has no actual benefit');
 A.roamStart();A.assert(T.roamers.length===2,'quantity card did not create second tornado');out.quantityPreview=preview;
 A.roamReset();const cloneCard=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');
 A.assert(cloneCard&&cloneCard.apply(p)!==false,'native clone card missing');const clone=G.SelfClones.actors()[0];
 A.assert(clone,'clone absent');clone.x=clone.y=400;
 try{A.roamStep(.001);const wind=T.roamers.find(a=>a.owner===clone);A.assert(wind,'clone did not spawn own tornado '+JSON.stringify({dex:clone.dex,mon:clone.mon?.dex,hp:clone.hp,dead:clone.dead,frozen:clone.frozen,moves:clone.moves.map(m=>m.id),owners:T.roamers.map(a=>a.owner.cloneId)}));
   const mob=A.spawn(wind.x,wind.y),cloneHits=A.watch(mob);A.roamStep(.01);
   A.assert(cloneHits.length===1&&cloneHits[0].clone&&cloneHits[0].id===A.roamId,'clone damage lost ownership');out.clone={hits:cloneHits};
   G.SelfClones.clear();A.roamStep(.01);A.assert(!T.roamers.some(a=>a.owner===clone),'deleted clone retained tornado');
 }finally{p.frozen=false}
 return out;
}"""

WALL = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.roamReset();const a=A.roamStart();
 const origin={x:a.x,y:a.y},limit=70,block=G.World.projectileBlock,free=G.World.isFree;
 const solid=(x,y,r=0)=>Math.abs(x-origin.x)+r>limit||Math.abs(y-origin.y)+r>limit;
 G.World.projectileBlock=(x,y,r=0)=>solid(x,y,r)?{wall:true}:false;G.World.isFree=(x,y,r=0)=>!solid(x,y,r);
 let maxStep=0;try{for(let i=0;i<350;i++){const previous={x:a.x,y:a.y};A.roamStep(.01);
   A.assert(!solid(a.x,a.y),'tornado crossed wall');maxStep=Math.max(maxStep,Math.hypot(a.x-previous.x,a.y-previous.y))}}
 finally{G.World.projectileBlock=block;G.World.isFree=free}
 A.assert(maxStep<3,'tornado bounced by teleport');return {origin,last:{x:a.x,y:a.y},maxStep};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'ok': False, 'errors': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for label, viewport in [('desktop', {'width': 1200, 'height': 900}), ('mobile', {'width': 390, 'height': 844})]:
                print(label, flush=True)
                ctx = browser.new_context(viewport=viewport, is_mobile=label == 'mobile', has_touch=label == 'mobile', service_workers='block')
                ctx.add_init_script('window.requestAnimationFrame=callback=>{window.__roamFrame=callback;return 0}')
                page = ctx.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                boot(page)
                page.evaluate(FIXTURE)
                result = report['viewports'][label] = {'mechanics': page.evaluate(CHECK), 'wall': page.evaluate(WALL)}
                page.evaluate('Acceptance.roamReset(3,1);Acceptance.roamStart();for(let i=0;i<80;i++)Acceptance.roamStep(.01);window.__roamFrame(performance.now())')
                page.screenshot(path=str(OUT / f'{label}-roaming.png'))
                result['overflow'] = page.evaluate('document.documentElement.scrollWidth>innerWidth')
                assert not result['overflow'], 'horizontal overflow'
                ctx.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report['failure'] = str(error)
        raise
    finally:
        path = OUT / 'report.json'
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(path, flush=True)


if __name__ == '__main__':
    main()
