"""Native-browser acceptance for defense-first sand guardian attacks."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_gaara import SETUP, URL
from test_gaara_sand_guard import FIXTURE

OUT = Path(__file__).resolve().parents[1] / '.omx/state/gaara-guard-offense'

SETUP_OFFENSE = r"""() => {
 const A=Acceptance,p=A.p();p.level=1;
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+A.guardId);
 A.assert(card&&card.apply(p)!==false,'cannot learn merged shield');
 A.offenseReset=()=>{
   const g=A.guardReset();A.clock=0;
   g.guardians.forEach((s,i)=>{s.x=i? -300:100;s.y=i? -300:0;s.heading=0;
     if(i){A.spend(s);s.rechargeProgress=0}});
   return g.guardians[0];
 };
 A.offenseStep=(dt=.01)=>{A.guardStep(dt);A.clock+=dt};
 A.waitFor=(condition,seconds=3)=>{for(let i=0;i<Math.ceil(seconds*100)&&!condition();i++)A.offenseStep();return condition()};
 A.watchEnemy=(x=240,y=0)=>{
   const e=A.spawn(x,y),hurt=e.hurt;e.hits=[];
   e.hurt=function(...args){e.hits.push({time:A.clock,damage:args[0],owner:args[6]===p,id:args[7],x:this.x,y:this.y});return hurt.apply(this,args)};
   return e;
 };
 A.guardSummary=s=>({x:s.x,y:s.y,phase:s.phase,ready:s.ready,attackCooldown:s.attackCooldown,attackTarget:!!s.attackTarget,target:!!s.target});
}"""

ATTACK = r"""() => {
 const A=Acceptance,p=A.p(),s=A.offenseReset(),e=A.watchEnemy(),move=p.moves.find(m=>m.id===A.guardId);
 const before=move.dealt||0,x=s.x;A.offenseStep();
 A.assert(s.attackTarget===e&&s.phase==='pursue','idle guardian did not attack native enemy');
 A.assert(e.hp===e.maxHp&&s.x>x&&s.x-x<=s.speed*.01+.001,'offense hit remotely or exceeded speed');
 A.assert(A.waitFor(()=>e.hits.length===1,2),'physical enemy hit never happened');
 const first=e.hits[0],contact=A.clock;
 A.assert(e.hp<e.maxHp&&first.owner&&first.id===A.guardId,'hit bypassed native owned Enemy.hurt');
 A.assert((move.dealt||0)>before,'shield damage attribution missing');
 A.assert(s.ready&&s.charges===1&&s.attackCooldown>.9,'attack consumed defense readiness or wrong cooldown');
 A.assert(Math.hypot(s.x-e.x,s.y-e.y)<=G.NarutoSandGuard.config.radius+e.r+3,'attack applied without physical contact');
 while(A.clock<contact+.97)A.offenseStep();
 A.assert(e.hits.length===1,'guardian repeated hit before one second');
 A.assert(A.waitFor(()=>e.hits.length>=2,1.6),'guardian failed to attack again after cooldown');
 A.assert(e.hits[1].time-e.hits[0].time>=.98,'offensive cooldown shorter than one second');
 return {first,second:e.hits[1],state:A.guardSummary(s),damage:e.maxHp-e.hp};
}"""

DEFENSE = r"""() => {
 const A=Acceptance,p=A.p(),out={};let s=A.offenseReset(),e=A.watchEnemy(240,0);
 // A native Enemy.shoot establishes a real projectile instead of a target stub.
 const q=A.nativeShot(320,120,-1,0);A.offenseStep();
 A.assert(s.target===q&&!s.attackTarget&&e.hits.length===0,'incoming projectile lost to enemy attack');
 out.initialPriority=true;
 s=A.offenseReset();e=A.watchEnemy();A.offenseStep();A.assert(s.attackTarget===e,'preemption fixture never attacked');
 const incoming=A.nativeShot(320,120,-1,0);A.offenseStep();
 A.assert(s.target===incoming&&!s.attackTarget&&e.hits.length===0,'ongoing attack did not immediately yield to defense');
 out.preempted=true;
 // All ready guardians suspend offense, including guardians not assigned a shot.
 const g=A.guardReset();g.guardians.forEach((c,i)=>{c.x=40+i*20;c.y=0;c.heading=0});e=A.watchEnemy(230,0);
 A.nativeShot(340,160,-1,0);A.offenseStep();
 A.assert(g.guardians.every(c=>!c.attackTarget),'unassigned guardian attacked during local defense threat');
 out.globalPriority=true;
 // Offensive cooldown must not delay an actual projectile interception.
 s=A.offenseReset();e=A.watchEnemy();A.assert(A.waitFor(()=>e.hits.length>0,2),'cooldown defense fixture did not hit');
 const cooldown=s.attackCooldown;A.assert(cooldown>.9,'missing attack cooldown');
 const shot=A.shot({x:s.x+65,y:s.y,vx:-90,vy:0});A.offenseStep();
 A.assert(s.target===shot&&!s.attackTarget,'attack cooldown suppressed defense acquisition');
 A.assert(A.waitFor(()=>!G.Projectiles.all().includes(shot),1),'cooling attacker did not intercept physically');
 A.assert(!s.ready&&s.rechargeProgress===0,'projectile interception omitted independent reform');
 s.x=p.x;s.y=p.y;s.heading=0;G.EnemyMgr.clear();G.Projectiles.clear();A.offenseStep(2.48);
 A.assert(!s.ready,'interception reform shortened to offense cooldown');A.offenseStep(.04);A.assert(s.ready,'interception reform did not finish at 2.5 seconds');
 out.cooldownDefense={attackCooldown:cooldown,reformSeconds:2.5};
 return out;
}"""

TIERS_AND_BOUNDS = r"""() => {
 const A=Acceptance,p=A.p(),move=p.moves.find(m=>m.id===A.guardId),out={tiers:[]};
 for(let tier=1;tier<=5;tier++){
   move.lvl=tier;const s=A.offenseReset(),e=A.watchEnemy(110,0);
   const expected=[20,25,30,35,40][tier-1]*p.atk*G.Types.mult(move.type,e.types)*G.Weather.mult(move.type);
   A.offenseStep();A.assert(e.hits.length===1&&Math.abs(e.hits[0].damage-expected)<1e-7,'wrong native damage tier '+tier);
   out.tiers.push({tier,base:[20,25,30,35,40][tier-1],nativeDamage:e.hits[0].damage});
 }
 move.lvl=1;p.level=20;const g=A.guardReset();A.assert(g.count===10,'query fixture missing ten guardians');
 A.watchEnemy(390,0);let queries=0,terrain=0,baselineQueries=0;
 const query=G.EnemyMgr.queryCircle,wall=G.World.isWall,block=G.World.projectileBlock;
 G.EnemyMgr.queryCircle=function(...args){queries++;return query.apply(this,args)};
 G.World.isWall=()=>{terrain++;return false};G.World.projectileBlock=()=>{terrain++;return false};
 try{
   p.frozen=true;A.offenseStep(.5);p.frozen=false;baselineQueries=queries;queries=0;terrain=0;
   A.offenseStep(.5);
 }finally{p.frozen=false;G.EnemyMgr.queryCircle=query;G.World.isWall=wall;G.World.projectileBlock=block}
 A.assert(queries-baselineQueries===1,'enemy search duplicated across ten guardians/substeps: '+queries+' control '+baselineQueries);
 A.assert(terrain===0,'phasing offense queried terrain: '+terrain);
 out.bounds={guardians:g.count,seconds:.5,queries,baselineQueries,guardQueries:queries-baselineQueries,terrain};p.level=1;return out;
}"""

CANCELLATION = r"""() => {
 const A=Acceptance,p=A.p(),out={};let s=A.offenseReset(),e=A.watchEnemy();A.offenseStep();
 A.assert(s.attackTarget===e,'cancellation fixture never attacked');e.dead=true;A.offenseStep();
 A.assert(s.attackTarget!==e&&e.hits.length===0,'dead enemy retained offensive target');out.dead=true;
 s=A.offenseReset();e=A.watchEnemy();A.offenseStep();e.x=600;G.EnemyMgr.rebuildGrid();A.offenseStep();
 A.assert(s.attackTarget!==e&&e.hits.length===0,'enemy outside 400 retained offensive target');out.outOfRange=true;
 s=A.offenseReset();e=A.watchEnemy(600,0);A.offenseStep(.5);
 A.assert(!s.attackTarget&&e.hits.length===0,'guardian attacked outside activity radius');
 s=A.offenseReset();e=A.watchEnemy();A.assert(A.waitFor(()=>e.hits.length>0,2),'pause fixture never hit');
 const snapshot=JSON.stringify(A.guardSummary(s)),age=s.age;G.Combat.resolve(.5,p,0);
 A.assert(JSON.stringify(A.guardSummary(s))===snapshot&&s.age===age,'pause advanced offense cooldown/movement');
 p.frozen=true;try{A.offenseStep(.5)}finally{p.frozen=false}
 A.assert(JSON.stringify(A.guardSummary(s))===snapshot&&s.age===age,'freeze advanced offense cooldown/movement');out.pauseAndFreeze=true;
 const previous=A.guard();G.Combat.clearFields(p);const fresh=A.guard();
 A.assert(fresh!==previous&&fresh.guardians.every(c=>!c.attackTarget&&!c.attackCooldown),'clear leaked attack target/cooldown');out.clear=true;
 G.Game.startRun();A.pause();A.assert(!G.NarutoSandGuard.state(p)&&!G.NarutoSandGuard.state(G.Game.player),'new run leaked offense');out.newRun=true;
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'failedRequests': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in [False, True]:
                label = 'mobile' if mobile else 'desktop'
                context = browser.new_context(
                    locale='zh-TW', viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900},
                    is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda error: report['errors'].append(str(error)))
                page.on('response', lambda response: report['failedRequests'].append(response.url)
                        if response.status >= 400 and '127.0.0.1' in response.url else None)
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.NarutoSandGuard && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                for setup in [HARNESS, SETUP, FIXTURE, SETUP_OFFENSE]:
                    page.evaluate(setup)
                result = report['viewports'][label] = {}
                for name, script in [('attack', ATTACK), ('defense', DEFENSE), ('tiersAndBounds', TIERS_AND_BOUNDS), ('cancellation', CANCELLATION)]:
                    result[name] = page.evaluate(script)
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        assert not report['failedRequests'], report['failedRequests']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
