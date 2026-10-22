"""Native flowing-sand acceptance and ordered visual evidence.

Uses real combat/projectile entry points. Canvas spies measure guard paint calls,
not timing; the separate baseline harness owns performance measurements.
"""
import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_gaara import SETUP, URL
from test_gaara_sand_guard import FIXTURE, PROGRESSION, CLEANUP

OUT = Path(__file__).resolve().parents[1] / '.omx/state/gaara-sand-flow'

FLOW = r"""() => {
 const A=Acceptance,p=A.p();
 A.flowSnapshot=()=>{const g=A.guard();return {
   count:g.count,readyCount:g.readyCount,range:g.range,speed:g.speed,
   pairChecks:g.flowPairChecks,
   groups:(g.flowGroups||[]).map(f=>({id:f.id,x:f.x,y:f.y,active:f.active,blend:f.blend,members:[...f.members]})),
   guardians:g.guardians.map(s=>({index:s.index,x:s.x,y:s.y,heading:s.heading,phase:s.phase,
     ready:s.ready,recharge:s.rechargeProgress,group:s.flowGroupId,blend:s.flowBlend,target:!!s.target}))}};
 A.flowSettle=(count=10)=>{p.level=count-2;p.moves.find(m=>m.id===A.guardId).lvl=1;
   const g=A.guardReset();A.advanceGuard(12);return g};
 A.flowDraw=()=>{
   const g=A.guard(),canvas=document.createElement('canvas');canvas.width=1000;canvas.height=1000;
   const ctx=canvas.getContext('2d');ctx.translate(500-p.x,500-p.y);
   const counts={fill:0,fillRect:0,stroke:0,drawImage:0};
   for(const k of Object.keys(counts)){const original=ctx[k].bind(ctx);ctx[k]=(...args)=>{counts[k]++;return original(...args)}}
   const snapshot=JSON.stringify(A.flowSnapshot()),shots=[...G.Projectiles.all()];
   G.NarutoSandVFX.drawGuardGroup(ctx,g);
   A.assert(snapshot===JSON.stringify(A.flowSnapshot()),'render mutated simulation');
   A.assert(shots.length===G.Projectiles.all().length&&shots.every((s,i)=>s===G.Projectiles.all()[i]),'renderer changed projectiles');
   const total=Object.values(counts).reduce((a,b)=>a+b,0);
   A.assert(total<=200,'whole guard paint budget exceeded '+JSON.stringify(counts));
   return {counts,total};
 };
 A.flowFrame=()=>{
   // Native scene layer functions, with the same world coordinates and actual
   // actor renderer; evidence is deterministic while simulation stays paused.
   const canvas=document.createElement('canvas');canvas.width=900;canvas.height=700;
   const ctx=canvas.getContext('2d');ctx.fillStyle='#27382a';ctx.fillRect(0,0,900,700);
   ctx.translate(450-p.x,350-p.y);
   G.Combat.drawAirFields(ctx);p.anim.draw(ctx,p.x,p.y);
   return canvas.toDataURL('image/png');
 };
}"""

IDLE = r"""count=>{
 const A=Acceptance,p=A.p(),g=A.flowSettle(count),out={settled:A.flowSnapshot()};
 A.assert(g.count===count&&g.range===400&&g.speed===p.spd+200,'count/range/speed changed');
 A.assert(Array.isArray(g.flowGroups),'flow group API absent');
 const active=g.flowGroups.filter(f=>f.active&&f.members.length);
 A.assert(active.length>=1&&active.length<=3,'idle sand not pooled into one to three flows');
 A.assert(g.flowPairChecks<=45,'pair comparison budget exceeded');
 const members=active.flatMap(f=>f.members);
 A.assert(members.length===count&&new Set(members).size===count,'idle pooled membership lost/duplicated guardians');
 for(const f of active){
   const nodes=f.members.map(i=>g.guardians[i]);
   A.assert(nodes.every(Boolean),'flow refers to absent physical guardian');
   const spread=Math.max(...nodes.flatMap(a=>nodes.map(b=>Math.hypot(a.x-b.x,a.y-b.y))));
   A.assert(spread<=40,'pooled actual nodes still separate '+spread);
 }
 const refs=[...g.guardians],groups=[...g.flowGroups];let maxStep=0,maxTurn=0;
 for(let n=0;n<120;n++){
   const before=g.guardians.map(s=>({x:s.x,y:s.y,heading:s.heading}));
   if(n<60){p.x+=.6;p.y+=.3}A.guardStep(.01);
   g.guardians.forEach((s,i)=>{const d=Math.hypot(s.x-before[i].x,s.y-before[i].y),
     turn=Math.abs(Math.atan2(Math.sin(s.heading-before[i].heading),Math.cos(s.heading-before[i].heading)));
     maxStep=Math.max(maxStep,d);maxTurn=Math.max(maxTurn,turn);
     A.assert(s===refs[i]&&d<=s.speed*.01+.001,'pooling replaced or teleported physical node');
     A.assert(turn<=G.NarutoSandGuard.config.turnRate*.01+.001,'pool turn exceeded angular bound');
   });
 }
 A.assert(groups.every((f,i)=>g.flowGroups[i]===f),'flow groups allocated/replaced every update');
 out.maxStep=maxStep;out.maxTurn=maxTurn;out.paint=A.flowDraw();return out;
}"""

SPLIT = r"""() => {
 const A=Acceptance,p=A.p(),g=A.flowSettle(10),shots=[];
 // Native Enemy.shoot creates all ten bullets; slow their flight only to keep
 // all ten separate and observable through assignment before physical contact.
 g.guardians.forEach((s,i)=>{const angle=i*Math.PI*2/10;s.x=170*Math.cos(angle);s.y=170*Math.sin(angle);s.heading=angle;
   const q=A.nativeShot(310*Math.cos(angle),310*Math.sin(angle),-Math.cos(angle),-Math.sin(angle));
   q.vx*=.1;q.vy*=.1;q.life=20;shots.push(q)});
 A.guardStep(.01);
 const assigned=g.guardians.map(s=>s.target);
 A.assert(assigned.every(q=>shots.includes(q))&&new Set(assigned).size===10,'ten native projectiles not independently assigned');
 A.assert(shots.every(q=>G.Projectiles.all().includes(q)),'split erased bullets at a distance');
 const out={assignment:A.flowSnapshot(),paint:A.flowDraw()};
 for(let i=0;i<40;i++)A.guardStep();
 out.inFlight=A.flowSnapshot();out.flightPaint=A.flowDraw();return out;
}"""

CONTACT = r"""() => {
 const A=Acceptance,p=A.p(),g=A.flowSettle(10);G.Projectiles.clear();
 g.guardians.forEach((s,i)=>{s.x=130;s.y=-270+i*60;s.heading=0});
 const shots=g.guardians.map(s=>{const q=A.nativeShot(s.x+18,s.y,-1,0);q.life=20;return q});
 const remove=G.Projectiles.remove,counts=new Map();
 G.Projectiles.remove=function(q){counts.set(q,(counts.get(q)||0)+1);return remove.call(this,q)};
 try{A.guardStep(.01)}finally{G.Projectiles.remove=remove}
 A.assert(shots.every(q=>!G.Projectiles.all().includes(q)&&counts.get(q)===1),'front contact not removed exactly once');
 A.assert(g.guardians.every(s=>!s.ready),'front contact did not consume independent guardian');
 const out={contact:A.flowSnapshot(),paint:A.flowDraw(),contactFrame:A.flowFrame()};
 // Return/fusion must not grant early charges or change independent cooldowns.
 const before=g.guardians.map(s=>s.rechargeProgress);A.guardStep(.01);
 A.assert(g.guardians.every((s,i)=>!s.ready&&s.rechargeProgress===before[i]),'remote return/fusion reset recharge');
 A.advanceGuard(1);out.returning=A.flowSnapshot();out.returnPaint=A.flowDraw();out.returnFrame=A.flowFrame();
 let readyAt=null;for(let i=0;i<1800;i++){
   const old=g.guardians.map(s=>({ready:s.ready,recharge:s.rechargeProgress,x:s.x,y:s.y}));A.guardStep(.01);
   for(let j=0;j<g.count;j++){
     const s=g.guardians[j],was=old[j];
     if(!was.ready&&s.ready)A.assert(was.recharge>=.99,'fusion granted charge before native recharge');
     if(!s.ready&&Math.hypot(s.x-p.x,s.y-p.y)>40.001)A.assert(s.rechargeProgress===was.recharge,'remote fusion advanced recharge');
   }
   if(g.guardians.every(s=>s.ready)){readyAt=i*.01;break}
 }
 A.assert(readyAt!==null,'native guardians never returned/reformed');
 A.advanceGuard(8);out.reformed=A.flowSnapshot();out.reformPaint=A.flowDraw();return out;
}"""

HYSTERESIS = r"""() => {
 const A=Acceptance,g=A.flowSettle(3);g.flowClock=0;g.flowJoined.fill(0);g.flowDwell.fill(0);
 const pin=(distance,steps)=>{for(let n=0;n<steps;n++){
   g.guardians.forEach((s,i)=>{s.x=100+(i===1?distance:i===2?100:0);s.y=100;s.heading=0});
   A.guardStep(.01);
 }};
 pin(17,10);A.assert(!g.flowJoined[1],'merged before .15 second dwell');
 pin(17,11);A.assert(g.flowJoined[1],'near aligned nodes did not merge after dwell');
 const joined=[];
 for(const distance of [19,23,29,21,27]){pin(distance,11);joined.push(!!g.flowJoined[1]);A.assert(g.flowJoined[1],'merge flickered inside leave threshold')}
 pin(34,11);A.assert(!g.flowJoined[1],'did not split beyond 30');
 pin(22,22);A.assert(!g.flowJoined[1],'rejoined outside join threshold');
 return {joinDistance:17,heldDistances:[19,23,29,21,27],joined,splitDistance:34};
}"""

MOVING = r"""() => {
 const A=Acceptance,p=A.p(),g=A.flowSettle(10);let maxStep=0,maxTurn=0;
 for(let n=0;n<240;n++){
   const heading=Math.floor(n/60)*Math.PI/2;
   p.x+=Math.cos(heading)*p.spd*.01;p.y+=Math.sin(heading)*p.spd*.01;
   const old=g.guardians.map(s=>({x:s.x,y:s.y,heading:s.heading}));A.guardStep(.01);
   g.guardians.forEach((s,i)=>{const distance=Math.hypot(s.x-old[i].x,s.y-old[i].y),turn=Math.abs(Math.atan2(Math.sin(s.heading-old[i].heading),Math.cos(s.heading-old[i].heading)));
     maxStep=Math.max(maxStep,distance);maxTurn=Math.max(maxTurn,turn);
     A.assert(distance<=s.speed*.01+.001&&turn<=3.6*.01+.001,'rapid moving owner caused node teleport/right angle')});
 }
 return {maxStep,maxTurn,paint:A.flowDraw(),state:A.flowSnapshot()};
}"""

DECORATIVE = r"""() => {
 const A=Acceptance,g=A.flowSettle(3);G.Projectiles.clear();
 // A real hostile sits midway between separated nodes. All physical circles
 // are far away; visual connections may never become collision volumes.
 g.guardians.forEach((s,i)=>{s.x=100+i*70;s.y=100;s.heading=Math.PI});
 const q=A.shot({x:135,y:100,vx:0,vy:0});
 A.assert(g.guardians.every(s=>Math.hypot(s.x-q.x,s.y-q.y)>G.NarutoSandGuard.config.radius+q.r),'bridge fixture intersects a physical node');
 const paint=A.flowDraw();A.guardStep(.01);
 A.assert(G.Projectiles.all().includes(q)&&g.guardians.every(s=>s.ready),'decorative bridge erased projectile');
 return {paint,bulletSurvived:true,state:A.flowSnapshot()};
}"""

LIFECYCLE = r"""() => {
 const A=Acceptance,p=A.p(),g=A.flowSettle(3),first=g.guardians[0],out={};
 A.spend(first);first.x=first.y=0;first.rechargeProgress=.3;
 const refs=[...g.guardians];p.level=8;A.guard();
 A.assert(g.count===10&&refs.every((s,i)=>g.guardians[i]===s)&&!first.ready&&first.rechargeProgress===.3,'growth destroyed independent charge/ref');
 const snapshot=JSON.stringify(A.flowSnapshot());G.Combat.resolve(.5,p,0);
 A.assert(snapshot===JSON.stringify(A.flowSnapshot()),'paused flow advanced');
 p.frozen=true;A.guardStep(.5);p.frozen=false;
 A.assert(snapshot===JSON.stringify(A.flowSnapshot()),'frozen flow advanced');
 let queries=0;const wall=G.World.isWall,block=G.World.projectileBlock;
 G.World.isWall=()=>{queries++;return true};G.World.projectileBlock=()=>{queries++;return 'wall'};
 // No projectile update: this specifically spies guardian movement, not native
 // projectile terrain collision, which legitimately queries terrain.
 try{A.resume();G.Combat.resolve(.01,p,0)}finally{A.pause();G.World.isWall=wall;G.World.projectileBlock=block}
 A.assert(queries===0,'flow reintroduced guardian wall queries');
 const q=A.shot({x:600,y:0,vx:0,vy:0});A.guardStep(.01);
 A.assert(g.guardians.every(s=>s.target!==q),'flow acquired projectile outside 400');
 out.growthPreserved=true;out.pauseFrozen=true;out.wallQueries=queries;return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in (False, True):
                label = 'mobile' if mobile else 'desktop'
                context = browser.new_context(locale='zh-TW', viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.NarutoSandGuard && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                for setup in (HARNESS, SETUP, FIXTURE, FLOW):
                    page.evaluate(setup)
                result = report['viewports'][label] = {'progression': page.evaluate(PROGRESSION)}
                for count in (3, 10):
                    result[f'idle{count}'] = page.evaluate(IDLE, count)
                    page.wait_for_timeout(70)
                    page.locator('#game').screenshot(path=str(OUT / f'{label}-0{1 if count == 3 else 2}-idle{count}.png'))
                result['split'] = page.evaluate(SPLIT)
                page.wait_for_timeout(70)
                page.locator('#game').screenshot(path=str(OUT / f'{label}-03-split.png'))
                result['contact'] = page.evaluate(CONTACT)
                for key, stage in [('contactFrame', '04-contact'), ('returnFrame', '05-return')]:
                    data = result['contact'].pop(key)
                    (OUT / f'{label}-{stage}.png').write_bytes(base64.b64decode(data.split(',', 1)[1]))
                page.wait_for_timeout(70)
                page.locator('#game').screenshot(path=str(OUT / f'{label}-06-reformed.png'))
                result['decorative'] = page.evaluate(DECORATIVE)
                result['hysteresis'] = page.evaluate(HYSTERESIS)
                result['moving'] = page.evaluate(MOVING)
                page.wait_for_timeout(70)
                page.locator('#game').screenshot(path=str(OUT / f'{label}-07-moving-owner.png'))
                result['lifecycle'] = page.evaluate(LIFECYCLE)
                result['cleanup'] = page.evaluate(CLEANUP)
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
