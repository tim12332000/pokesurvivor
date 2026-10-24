"""Native wind-return acceptance; production picker, learned cards and combat."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_temari as native

OUT = Path(__file__).resolve().parents[1] / '.omx/state/temari-reflect'
SETUP = r"""() => {
 const A=Acceptance,p=A.p();A.rf='naruto-temari-reflect';
 A.assert(G.NarutoTemariReflect,'reflection module absent');
 A.rfLearn=()=>{p.level=30;if(!p.hasMove(A.rf)){const c=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+A.rf);
   A.assert(c&&c.apply(p)!==false,'native reflection learning card absent')}};
 A.rfReset=(Q=0,rank=1)=>{A.reset();A.rfLearn();A.rank(A.rf,rank);p.quantityPicks=p.quantityBonus=Q;
   const e=A.spawn(210,0,'boss');p.target=e;G.NarutoTemariReflect.sync(p);return e};
 A.rfShot=(o={})=>G.Projectiles.spawn({x:160,y:0,px:160,py:0,vx:-800,vy:0,r:7,dmg:40,life:3,
   friendly:false,color:'#ff5070',mtype:'normal',vis:G.VFX.forType('normal'),...o});
 A.rfStep=(dt=.01)=>{A.resume();try{G.EnemyMgr.rebuildGrid();G.Projectiles.update(dt,p,G.EnemyMgr.all());
   G.Combat.resolve(dt,p,0);G.Combat.updateFields(dt);G.Hazards.update(dt)}finally{A.pause()}};
 A.rfFinish=s=>{for(let i=0;i<Math.ceil(s/.01);i++)A.rfStep(.01)};
}"""

PROGRESSION = r"""() => {
 const A=Acceptance,p=A.p(),out=[];A.assert(!p.hasMove(A.rf),'fresh character starts with reflection');
 for(const level of [14,15]){p.level=level;const c=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+A.rf);
   A.assert(!!c===(level===15),'reflection Lv15 gate');out.push({level,eligible:!!c})}
 const max=p.maxMoves;p.maxMoves=p.slots.length;A.rfLearn();p.maxMoves=max;A.assert(G.NarutoTemariReflect.activeFor(p),'learning with full active slots failed');for(let rank=1;rank<=5;rank++){A.rfReset(0,rank);const w=G.NarutoTemariReflect.activeFor(p);
   A.near(w.radius,[85,95,110,125,140][rank-1],'wall radius');A.assert(w.permanent&&w.duration===0,'wall is not permanent');A.assert(p.moves.find(m=>m.id===A.rf).passive&&!p.slots.some(g=>g.some(m=>m.id===A.rf)),'passive consumed active slot');
   A.near(w.multiplier,[1,1.2,1.4,1.7,2][rank-1],'return multiplier');out.push({rank,radius:w.radius,duration:w.duration,multiplier:w.multiplier})}
 return out;
}"""

PROJECTILES = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemariReflect,out=[];
 for(const flags of [{},{interceptable:false,bossSpecial:true},{unblockable:true,special:true},{beam:true,laser:true}]){
   const e=A.rfReset(),hits=A.watch(e),before=p.hp;A.rfShot(flags);A.rfFinish(.6);
   const s=T.stateFor(p);A.assert(s.intercepted===1&&s.returned===1,'source not reflected '+JSON.stringify(flags));
   A.assert(p.hp===before,'incoming crossed shield and hurt player');A.assert(hits.length===1&&hits[0].owner&&hits[0].id===A.rf,'no real attributed return hit');
   out.push({flags,hits:hits.length,damage:hits[0].damage,intercepted:s.intercepted})}
 A.rfReset();const before=p.hp;A.rfShot({x:10,px:10,vx:-100});A.rfFinish(.01);
 A.assert(p.hp===before&&T.stateFor(p).intercepted===1,'inside-origin projectile bypassed permanent wind');
 A.rfReset();A.rfShot({x:10,px:10,vx:0,vy:0,bossSpecial:true,unblockable:true});A.rfStep();A.assert(T.stateFor(p).intercepted===1,'stationary hostile overlapping wind bypassed');
 A.rfReset();A.rfShot({x:600,px:600,vx:-10000});A.rfStep(.08);A.assert(T.stateFor(p).intercepted===1,'fast projectile tunneled through wall');
 return out;
}"""

HAZARDS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemariReflect,out=[];
 A.rfReset();let before=p.hp;
 const beam=G.Hazards.add({kind:'beam',x:250,y:0,angle:Math.PI,len:500,w:24,delay:.1,dmg:40,type:'normal',color:'#f55'});
 A.rfFinish(.2);A.assert(p.hp===before&&beam.len<180&&T.stateFor(p).intercepted===1,'native beam not physically truncated');
 out.push({beamLength:beam.len,hp:p.hp});
 A.rfReset();before=p.hp;G.Hazards.add({kind:'zone',ranged:true,sourceX:250,sourceY:0,x:0,y:0,r:45,delay:.1,dmg:40,type:'normal',color:'#f55'});
 A.rfFinish(.2);A.assert(p.hp===before&&T.stateFor(p).intercepted===1,'ranged rain not returned');
 A.rfReset();before=p.hp;G.Hazards.add({kind:'beam',x:10,y:0,angle:Math.PI,len:200,w:24,delay:.1,dmg:40,color:'#f55'});
 A.rfFinish(.2);A.assert(p.hp===before&&T.stateFor(p).intercepted===1,'inside-origin beam bypassed wind');
 A.rfReset();before=p.hp;G.Hazards.add({kind:'zone',ranged:true,x:0,y:0,r:45,delay:.1,dmg:40,color:'#f55'});
 A.rfFinish(.2);A.assert(p.hp===before&&T.stateFor(p).intercepted===1,'source-less ranged zone bypassed wind');
 A.rfReset();before=p.hp;G.Hazards.add({kind:'zone',ranged:false,x:0,y:0,r:45,delay:.1,dmg:10,color:'#f55'});
 A.rfFinish(.2);A.assert(p.hp<before&&T.stateFor(p).intercepted===0,'melee/environment zone cancelled');
 A.rfReset();before=p.hp;G.Hazards.add({kind:'beam',ranged:false,x:250,y:0,angle:Math.PI,len:500,w:24,delay:.1,dmg:10,color:'#f55'});
 A.rfFinish(.2);A.assert(p.hp<before&&T.stateFor(p).intercepted===0,'melee dash beam cancelled');
 A.rfReset();before=p.hp;G.Hazards.add({kind:'beam',x:250,y:0,angle:Math.PI,len:500,w:24,delay:.1,dmg:1,pct:.35,pure:true,color:'#f55'});
 A.rfFinish(.2);A.assert(p.hp===before&&T.stateFor(p).intercepted===1,'Judgment pure percentage beam bypassed wall');return out;
}"""

GROWTH = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemariReflect,out=[];
 for(const Q of [0,5,10]){const e=A.rfReset(Q,5),hits=A.watch(e);A.rfShot();A.rfFinish(.6);const s=T.stateFor(p),n=Math.floor(1.25**Q);
   A.assert(s.intercepted===1&&s.returned===n,'quantity source removal/copy count');A.assert(hits.length===n,'quantity did not create real native hits');
   A.assert(hits.every(h=>h.owner&&h.id===A.rf&&h.damage>0),'unattributed reflection damage');out.push({Q,copies:n,hits:hits.length,totalDamage:e.maxHp-e.hp})}
 A.rfReset(0,1);p.percentHealthDamage=.01;p.lifestealRate=.1;p.hp=p.maxHp*.5;
 const e=A.spawn(210,0,'boss'),hits=A.watch(e);G.EnemyMgr.all().filter(x=>x!==e).forEach(x=>{x.dead=true});G.EnemyMgr.rebuildGrid();
 const before=p.hp;A.rfShot();A.rfFinish(.6);A.assert(hits.length===1&&p.hp>before,'native percent/lifesteal contract lost');return out;
}"""

LIFECYCLE = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemariReflect;A.rfReset();const w=T.activeFor(p),m=p.moves.find(m=>m.id===A.rf);
 A.learn();const slot=p.slots.findIndex(g=>g.some(n=>n.id==='naruto-temari-great-scythe'));p.setActive(slot);
 A.assert(T.activeFor(p)===w&&!T.canCast(p,m),'switch removed permanent wall');
 const age=w.age;T.update(5);A.near(w.age,age,'pause advanced wall');A.rfFinish(10.1);A.assert(T.activeFor(p)===w,'permanent wall expired');
 const before=p.hp;A.rfShot();A.rfFinish(.6);A.assert(T.stateFor(p).intercepted===1&&p.hp===before,'late incoming shot bypassed wall');
 A.assert(!T.cast(p,m)&&T.stateFor(p).casts===0,'passive became active cast');
 let syncs=0;const hook=T.onSync;T.onSync=(...args)=>{syncs++;hook?.(...args)};const ageDraw=w.age,QDraw=p.quantityPicks;p.quantityPicks=2;const ctx=document.createElement('canvas').getContext('2d');T.draw(ctx);A.assert(syncs===0&&w.age===ageDraw&&T.activeFor(p)===w,'draw mutated wall or published sync');p.quantityPicks=QDraw;T.onSync=hook;
 const castId=w.castId;A.rank(A.rf,5);p.quantityPicks=p.quantityBonus=5;T.sync(p);const grown=T.activeFor(p);
 A.assert(grown.castId===castId&&grown.radius===140&&grown.copies===3,'rank/quantity did not refresh permanent wall');
 const world=G.World;G.World=Object.create(world);A.rfStep();A.assert(T.activeFor(p)?.world===G.World,'wall did not follow world lifecycle');G.World=world;
 A.rfReset();p.dead=true;p.hp=0;A.rfStep();A.assert(!T.activeFor(p),'dead caster wall survived');
 p.dead=false;p.hp=p.maxHp;A.reset();return {switchPreservesWall:true,pauseFrozen:true,afterTenSeconds:true,automaticGrowth:true,deathClears:true};
}"""

CLONES_ITEMS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemariReflect,e=A.rfReset(5,1),hits=A.watch(e);
 A.rfShot();A.rfFinish(.6);const baseline=hits[0].raw;
 G.Combat.clearFields();hits.length=0;e.hp=e.maxHp;
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');A.assert(card,'native clone card absent');card.apply(p);
 const clone=G.SelfClones.actors()[0];A.assert(clone,'clone absent');clone.x=clone.y=0;clone.target=e;clone.critChance=0;
 p.x=500;T.sync(clone);A.rfShot();p.frozen=true;try{A.rfFinish(.6)}finally{p.frozen=false}
 const own=hits.filter(h=>h.clone&&h.id===A.rf);A.assert(own.length===3,'clone lost full quantity '+JSON.stringify({hits,wall:T.stateFor(clone)?.wall&&{copies:T.stateFor(clone).wall.copies},state:T.stateFor(clone)&&{intercepted:T.stateFor(clone).intercepted,returned:T.stateFor(clone).returned},clone:{x:clone.x,y:clone.y,hp:clone.hp},e:{x:e.x,y:e.y,hp:e.hp},shots:G.Projectiles.all().map(s=>({x:s.x,y:s.y,vx:s.vx,owner:s.owner===clone})),Q:G.Quantity.bonus(clone)}));
 own.forEach(h=>A.near(h.raw*3,baseline,'clone multiplier applied incorrectly'));
 A.assert(T.stateFor(clone).returned===3&&T.stateFor(p).intercepted===0,'actor reflection counters shared');
 G.SelfClones.clear();A.rfStep();A.assert(!T.stateFor(clone),'removed clone wall retained');
 A.reset();A.rfLearn();A.rank(A.rf,1);p.item='lifeorb';p.hp=p.maxHp;const before=p.hp;
 p.target=A.spawn(210,0,'boss');T.sync(p);const afterCast=p.hp;
 A.assert(afterCast===before,'passive activation paid lifeorb recoil');for(let i=0;i<4;i++)A.rfShot({y:i*3,py:i*3});A.rfFinish(.6);
 A.near(p.hp,afterCast,'reflection copies charged lifeorb again');p.item=null;
 return {cloneCopies:own.length,cloneRatio:own[0].raw/baseline,lifeorbPassiveCost:before-afterCast,noExtraReflectionCost:true};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'ok': False, 'errors': [], 'failures': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
        for label, viewport, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            native.boot(page)
            page.evaluate(SETUP)
            result = report['viewports'][label] = {}
            for name, check in [('progression', PROGRESSION), ('projectiles', PROJECTILES), ('hazards', HAZARDS), ('growth', GROWTH), ('lifecycle', LIFECYCLE), ('clonesItems', CLONES_ITEMS)]:
                print(label, name, flush=True)
                try:
                    result[name] = page.evaluate(check)
                except Exception as error:
                    report['failures'].append(f'{label}:{name}: {error}')
                (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
            page.evaluate('Acceptance.rfReset(5,5);Acceptance.rfShot({x:190,px:190,vx:-800});Acceptance.rfFinish(.15)')
            page.screenshot(path=str(OUT / f'{label}-wind-return.png'))
            context.close()
        browser.close()
    report['ok'] = not report['errors'] and not report['failures']
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps(report, ensure_ascii=False))
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
