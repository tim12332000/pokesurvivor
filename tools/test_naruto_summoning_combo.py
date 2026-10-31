"""Five-rank Gamabunta combo: native contacts, stage geometry, art and cleanup."""
import hashlib
import json
import mimetypes
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright

from test_naruto_summoning import CHROME, ROOT, URL

OUT = ROOT / '.omx/state/naruto-summoning/combo'

CHECK = r"""() => {
 const assert=(value,message)=>{if(!value)throw Error(message)},S=G.NarutoSummoning,p=G.Game.player,id='naruto-toad-summon';
 const reports={},checks=[];let current,hitLog=[];
 const open=()=>Object.assign(G.World,{isWall:()=>false,isFree:()=>true,collide:()=>{},propsInCircle:()=>[],projectileBlock:()=>false,isLiquid:()=>false});
 const enemy=(x,y)=>{
  const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];e.touchCd=999;
  const hurt=e.hurt;e.hurt=function(amount,color,dx,dy,knock,eff,owner,mid){hitLog.push({enemy:this.id,amount,age:current?.age,owner:owner===p,mid});return hurt.apply(this,arguments)};
  G.EnemyMgr.add(e);return e;
 };
 function reset(tier=1){
  G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();G.NarutoClones.clear();open();G.Camera.sees=()=>true;
  p.x=p.y=0;p.aim=0;p.hp=p.maxHp;p.dead=false;p.flash=p.invuln=0;p.critChance=0;p.percentHealthDamage=0;p.lifestealRate=0;
  p.level=12;p.quantityBonus=p.quantityPicks=0;p.cdMul=1;p.moves=[G.Moves.instance(id,tier)];p.slots=[[p.moves[0]]];p.bind={};p.active=0;hitLog=[];current=null;
  G.Camera.x=G.Camera.y=0;return p.moves[0];
 }
 function cast(tier=1,quantity=0){const m=reset(tier),anchor=enemy(100,0);G.EnemyMgr.rebuildGrid();p.target=anchor;p.quantityBonus=p.quantityPicks=quantity;assert(S.cast(p,G.Quantity.snapshot(p,m)),'rank '+tier+' rejected');current=S.effects[0];return {m,f:current,anchor}}
 function step(seconds,native=false){for(let elapsed=0;elapsed<seconds-1e-9;){const dt=Math.min(.005,seconds-elapsed);if(native){G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,elapsed)}G.Combat.updateFields(dt);G.FX.update(dt);p.anim.update(dt);elapsed+=dt}}
 const at=(f,time,native=false)=>step(Math.max(0,time-f.age),native);
 const projectiles=kind=>G.Projectiles.all().filter(shot=>shot.mid===id&&(!kind||shot.summonKind===kind));
 const delta=(enemies,before)=>enemies.map((e,i)=>before[i]-e.hp);
 const rebuild=()=>G.EnemyMgr.rebuildGrid();
 const cv=document.createElement('canvas');cv.width=900;cv.height=700;const ctx=cv.getContext('2d');ctx.translate(250,350);
 function art(f,expected){
  const used=[],draw=ctx.drawImage;ctx.drawImage=function(source,...args){used.push(source.src||'');return draw.call(this,source,...args)};
  const before=JSON.stringify({age:f.age,x:f.x,y:f.y,foxX:f.foxX,foxY:f.foxY,events:f.events});
  try{G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);G.Projectiles.draw(ctx)}finally{ctx.drawImage=draw}
  assert(used.some(source=>source.includes(expected)),'phase '+S.phaseFor(f)+' did not draw '+expected);
  assert(before===JSON.stringify({age:f.age,x:f.x,y:f.y,foxX:f.foxX,foxY:f.foxY,events:f.events}),'drawing mutated phase state');return [...new Set(used)];
 }
 const tiers=[];
 for(let rank=1;rank<=5;rank++){
  let {m,f,anchor}=cast(rank);assert(m.duration===[2.6,3,3,7.2,8.8][rank-1]&&m.windup===[.65,.65,.9,.9,.9][rank-1],'rank timing differs');
  const victims=[anchor,enemy(130,40),enemy(70,-40),enemy(100,190)];rebuild();const before=victims.map(e=>e.hp);
  at(f,m.windup-.01);assert(victims.every((e,i)=>e.hp===before[i]),'rank '+rank+' arrival damaged early');
  at(f,m.windup+.01);const damage=delta(victims,before),expected=Math.max(1,Math.round(m.dmg*p.atk*(rank>=3?.75:.5)));
  assert(damage.slice(0,3).every(value=>value===expected)&&damage[3]===0,'rank '+rank+' arrival three inside / one outside');
  const arrived=victims.map(e=>e.hp);step(.1);assert(victims.every((e,i)=>e.hp===arrived[i]),'arrival repeated');
  tiers.push({rank,duration:m.duration,windup:m.windup,radius:m.radius,arrivalDamage:damage});
  at(f,rank===1?2.59:2.81);assert((f.events||[]).filter(event=>/sword/i.test(event.kind)).length===(rank>=2?1:0),'sword rank gate or once-only event differs');
  assert(!(f.events||[]).some(event=>/oil|ignite|fox/i.test(event.kind)),'late stage triggered before its time');
 }
 reports.tiers=tiers;checks.push('all ranks arrival timing and three-target boundary','rank-gated sword events','no early oil or fox');
 let {m,f,anchor}=cast(2);at(f,2.16);anchor.dead=true;anchor.hp=0;
 let victims=[enemy(185,0),enemy(185,35),enemy(185,-35),enemy(-50,0),enemy(100,190)];rebuild();let before=victims.map(e=>e.hp);
 at(f,2.44);assert(victims.every((e,i)=>e.hp===before[i]),'sword damaged before contact');reports.swordArt=art(f,'gamabunta-sword-v1.png');
 at(f,2.46);reports.swordDamage=delta(victims,before);assert(reports.swordDamage.slice(0,3).every(value=>value>0)&&reports.swordDamage.slice(3).every(value=>value===0),'sword sector missed inside or hit behind/outside');
 const swordHP=victims.map(e=>e.hp);at(f,2.79);assert(victims.every((e,i)=>e.hp===swordHP[i]),'sword hit repeated');
 assert(hitLog.filter(hit=>hit.age>2.4).every(hit=>hit.owner&&hit.mid===id),'sword lost damage attribution');checks.push('dedicated sword art','sword contact timing','sword sector three inside and two outside','sword once and attribution');
 function oilSetup(rank=4){
  const state=cast(rank);at(state.f,2.85);state.anchor.dead=true;state.anchor.hp=0;for(const shot of projectiles())G.Projectiles.remove(shot);
  const target=enemy(280,0);rebuild();return {...state,target};
 }
 let setup=oilSetup();({m,f}=setup);at(f,3.09);assert(!projectiles('oil').length&&!f.oil,'oil started early');
 at(f,3.12);const oil=projectiles('oil')[0];assert(oil&&oil.ghost&&oil.dmg===0&&oil.owner===p&&oil.mid===id,'oil did not use native harmless projectile');reports.oilArt=art(f,'gamabunta-oil-v1.png');
 const oilHp=setup.target.hp;assert(!f.oil&&!f.fireAt,'oil pool/fire created before real contact');
 for(let i=0;i<250&&!f.oil;i++)step(.005,true);
 assert(f.oil&&setup.target.hp===oilHp,'real oil contact failed or dealt damage');assert(!f.oil.ignited&&!f.fireAt,'oil ignited before tag contact');
 const tag=projectiles('tag')[0];assert(tag&&tag.owner===p&&tag.mid===id&&Math.hypot(tag.x-p.x,tag.y-p.y)<50,'tag did not originate from Naruto');
 const pool={x:f.oil.x,y:f.oil.y},inside=[setup.target,enemy(pool.x+35,pool.y+35),enemy(pool.x-35,pool.y-35)],outside=enemy(pool.x,pool.y+170);rebuild();
 before=[...inside,outside].map(e=>e.hp);
 for(let i=0;i<350&&!f.oil.ignited;i++)step(.005,true);
 assert(f.oil.ignited&&f.fireAt!=null,'native tag failed to ignite contacted oil: '+JSON.stringify({pool,tag:{x:tag.x,y:tag.y,hits:[...tag.hits]},distance:Math.hypot(tag.x-pool.x,tag.y-pool.y)}));reports.fireDamage=delta([...inside,outside],before);
 assert(reports.fireDamage.slice(0,3).every(value=>value>0)&&reports.fireDamage[3]===0,'fire three inside / one outside failed');
 const fireHP=[...inside,outside].map(e=>e.hp);step(.5,true);assert([...inside,outside].every((e,i)=>e.hp===fireHP[i]),'oil fire damaged repeatedly');
 const oilOrder=['heavy','sword','oil-fired','oil-coated','tag-fired','fire'];
 assert(oilOrder.every((kind,index)=>f.events[index]?.kind===kind)&&f.events.length===oilOrder.length,'oil/fire stage event order or once-only count differs');
 assert(f.events.every((event,index)=>!index||event.age>=f.events[index-1].age),'stage event ages are not monotonic');
 reports.oilEvents=f.events;checks.push('oil native ghost contact before pool','dedicated oil art','tag owner-origin','tag actual contact before ignition','fire single three-target AoE','explicit once-only heavy/sword/oil/tag/fire event order');
 setup=oilSetup();({f}=setup);at(f,3.12);const miss=projectiles('oil')[0];assert(miss,'oil miss setup missing');setup.target.dead=true;setup.target.hp=0;step(1.7,true);assert(!f.oil&&!f.fireAt,'missed oil created pool/fire');checks.push('missed oil never ignites');
 setup=oilSetup();({f}=setup);at(f,3.12);for(let i=0;i<250&&!f.oil;i++)step(.005,true);assert(f.oil,'tag wall setup missing pool');
 G.World.projectileBlock=(x,y,r)=>x>40&&x<60?'wall':false;step(1.7,true);assert(!f.oil.ignited&&!f.fireAt,'blocked tag ignited oil');checks.push('wall-blocked tag never ignites');
 setup=oilSetup();({f}=setup);at(f,3.12);assert(projectiles('oil').length===1,'oil wall setup did not fire');G.World.projectileBlock=(x,y,r)=>x>225&&x<245?'wall':false;
 step(1.7,true);assert(!f.oil&&!f.fireAt,'blocked oil created pool or fire');checks.push('wall-blocked oil never coats');
 for(const cleanup of ['death','world','owner','skill']){
  setup=oilSetup();({f}=setup);at(f,3.12);for(let i=0;i<250&&!f.oil;i++)step(.005,true);
  assert(f.oil&&projectiles('tag').length===1&&!f.oil.ignited,'coated-oil cleanup setup missing live tag');const world=G.World,hp=setup.target.hp;
  if(cleanup==='death'){p.dead=true;p.hp=0}if(cleanup==='world')G.World=Object.create(world);if(cleanup==='owner')G.Combat.clearFields(p);if(cleanup==='skill')G.DigimonSkills.clear(p);
  try{G.Combat.resolve(0,p,0);step(1,true);assert(!S.effects.length&&!projectiles().length&&!f.oil.ignited&&setup.target.hp===hp,'pending actual tag ignited after '+cleanup)}finally{G.World=world}
 }
 checks.push('coated oil and in-flight native tag cleanup before ignition');
 setup=cast(5);({m,f,anchor}=setup);at(f,7.5);reports.transformArt=art(f,'gamabunta-combo-fox-v2.png');
 anchor.dead=true;anchor.hp=0;victims=[enemy(150,0),enemy(205,20),enemy(240,-20),enemy(180,140),enemy(-80,0)];rebuild();before=victims.map(e=>e.hp);
 at(f,7.79);assert(victims.every((e,i)=>e.hp===before[i]),'fox hit before dash');
 const playerOrigin={x:p.x,y:p.y};at(f,8.26);reports.foxDamage=delta(victims,before);
 assert(reports.foxDamage.slice(0,3).every(value=>value>0)&&reports.foxDamage.slice(3).every(value=>value===0),'fox swept capsule geometry failed');
 assert(Math.abs(f.foxX-f.x)<=140.001&&p.x===playerOrigin.x&&p.y===playerOrigin.y,'fox dash moved Naruto or exceeded range');
 const foxHP=victims.map(e=>e.hp);at(f,8.65);assert(victims.every((e,i)=>e.hp===foxHP[i]),'fox hit repeated');reports.foxArt=art(f,'gamabunta-combo-fox-v2.png');
 assert(f.events.filter(event=>event.kind==='transform').length===1&&f.events.filter(event=>event.kind==='fox').length===1&&f.events.find(event=>event.kind==='transform').age<f.events.find(event=>event.kind==='fox').age,'transformation did not precede one fox dash');
 checks.push('dedicated transformation and fox art','fox timing','fox swept three-target capsule and outside','fox once-only damage','fox displacement bounds and stationary Naruto');
 setup=cast(5);({f}=setup);at(f,7.79);const start=f.x;G.World.projectileBlock=(x,y,r)=>x>=start+50?'wall':false;G.World.isWall=(x,y)=>x>=start+50;
 const protectedEnemy=enemy(start+100,0);rebuild();const protectedHP=protectedEnemy.hp;at(f,8.26);assert(f.foxX<start+50&&protectedEnemy.hp===protectedHP,'fox crossed wall');checks.push('fox wall collision');
 function quantityStage(rank,quantity){
  const state=cast(rank,quantity);at(state.f,rank===2?2.16:7.79);state.anchor.dead=true;state.anchor.hp=0;
  const inside=[enemy(185,0),enemy(205,20),enemy(220,-20)],outside=enemy(180,190);rebuild();const hp=[...inside,outside].map(e=>e.hp);
  at(state.f,rank===2?2.8:8.26);return delta([...inside,outside],hp);
 }
 reports.quantitySword=[quantityStage(2,0),quantityStage(2,4)];reports.quantityFox=[quantityStage(5,0),quantityStage(5,4)];
 assert(JSON.stringify(reports.quantitySword[0])===JSON.stringify(reports.quantitySword[1])&&JSON.stringify(reports.quantityFox[0])===JSON.stringify(reports.quantityFox[1]),'quantity multiplied sword or fox damage');checks.push('higher-rank sword and fox quantity damage equality');
 for(const time of [.4,2.3,3.2,7.5,8.0])for(const kind of ['death','world','owner','skill']){
  setup=cast(5);({f}=setup);at(f,time);const world=G.World,hp=setup.anchor.hp;
  if(kind==='death'){p.dead=true;p.hp=0}if(kind==='world')G.World=Object.create(world);if(kind==='owner')G.Combat.clearFields(p);if(kind==='skill')G.DigimonSkills.clear(p);
  try{G.Combat.resolve(0,p,0);step(.1);assert(!S.effects.length&&!projectiles().length&&setup.anchor.hp===hp,'phase '+time+' survived '+kind)}finally{G.World=world}
 }
 checks.push('every-stage death/world/owner/skill cleanup');
 setup=cast(5);({f}=setup);at(f,2.3);const frozen=JSON.stringify({age:f.age,events:f.events,hp:setup.anchor.hp});G.Combat.updateFields(0);art(f,'gamabunta-sword-v1.png');
 assert(frozen===JSON.stringify({age:f.age,events:f.events,hp:setup.anchor.hp}),'paused combo advanced');checks.push('pause and rendering purity');
 setup=oilSetup();({f}=setup);at(f,3.12);for(let i=0;i<250&&!f.oil;i++)step(.005,true);
 assert(f.oil,'moving coated-target repro missing real oil contact');const fixedPool={x:f.oil.x,y:f.oil.y},remoteTag=projectiles('tag')[0];
 setup.target.x=90;setup.target.y=0;rebuild();step(.4,true);
 const remoteIgnition={tagHitMovedTarget:remoteTag.hits.has(setup.target.id),distanceFromPool:Math.hypot(setup.target.x-fixedPool.x,setup.target.y-fixedPool.y),ignited:f.oil.ignited};
 assert(remoteIgnition.tagHitMovedTarget&&remoteIgnition.distanceFromPool>f.oil.radius+50,'moving target repro did not intercept native tag far outside fixed oil');
 setup=oilSetup();({f}=setup);setup.target.x=-80;rebuild();at(f,3.12);for(let i=0;i<250&&!f.oil;i++)step(.005,true);
 assert(f.oil&&projectiles('tag')[0]?.vx<0,'left oil repro missing actual leftward native tag');
 const ownerPose=S.poseFor(p),authoredPose=G.AnimationLab.stateFor(p.anim);
 const leftTagPose={kind:ownerPose?.kind,mirror:ownerPose?.mirror,aim:ownerPose?.aim,authoredMirror:authoredPose.mirror,authoredAim:authoredPose.aim,tagVx:projectiles('tag')[0].vx};
 reports.remoteIgnition=remoteIgnition;reports.leftTagPose=leftTagPose;
 assert(!remoteIgnition.ignited&&ownerPose?.kind==='tag'&&ownerPose.mirror===true&&Math.cos(ownerPose.aim)<0&&authoredPose.mirror===true,'review regressions: '+JSON.stringify({remoteIgnition,leftTagPose}));
 const leftStationaryHP=setup.target.hp;for(let i=0;i<350&&!f.oil.ignited;i++)step(.005,true);
 assert(f.oil.ignited&&setup.target.hp<leftStationaryHP,'left stationary coated target failed native pool ignition');
 reports.leftStationaryIgnition={radius:setup.target.r,damage:leftStationaryHP-setup.target.hp,ignited:f.oil.ignited};
 checks.push('left and right stationary coated target actual ignition');
 setup=cast(4);({f}=setup);enemy(280,0);rebuild();G.Combat.updateFields(6);G.Combat.updateFields(.01);
 const lateStages=f.events.filter(event=>['sword','oil-fired'].includes(event.kind));
 assert(!lateStages.length,'large frame released missed sword/oil phases: '+JSON.stringify(lateStages));
 checks.push('large in-lifetime frame discards missed sword and oil windows');
 setup=cast(5);({f}=setup);enemy(280,0);rebuild();G.Combat.updateFields(8.5);G.Combat.updateFields(.01);
 const lateRankFive=f.events.filter(event=>['sword','oil-fired','transform','fox'].includes(event.kind));
 assert(!lateRankFive.length,'large rank-five frame replayed missed phases: '+JSON.stringify(lateRankFive));
 checks.push('large rank-five in-lifetime frame skips missed transform and fox');
 checks.push('moved coated target cannot remotely ignite fixed oil','left native tag uses left authored throw pose');
 window.summonComboEvidence={reset,cast,at,step,enemy,rebuild,oilSetup,art};
 reports.checks=checks;return reports;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reports = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in [False, True]:
            label = 'mobile' if mobile else 'desktop'
            errors = []
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1100, 'height': 850},
                                          is_mobile=mobile, has_touch=mobile, locale='zh-TW', service_workers='block')

            def route(request):
                file = ROOT / unquote(urlsplit(request.request.url).path).removeprefix('/pokesurvivor/')
                request.fulfill(status=200 if file.is_file() else 404, body=file.read_bytes() if file.is_file() else b'Not found',
                                content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')

            context.route('https://tim12332000.github.io/pokesurvivor/**', route)
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(URL.replace('digimon.html', 'portrait.html').replace('layout=wide', 'layout=portrait') if mobile else URL)
            view = page
            if mobile:
                page.wait_for_selector('#portrait-game')
                view = page.locator('#portrait-game').element_handle().content_frame()
            view.wait_for_function('window.PS_REDRAWN_READY && G.NarutoSummoning?.phaseFor && document.getElementById("boot").classList.contains("hidden")')
            if view.locator('#tap-start').is_visible():
                view.locator('#tap-start').click()
            view.evaluate("""async()=>{await PS_REDRAWN_READY;const loaded=await G.NarutoSummoning.ready;if(!loaded.every(Boolean))throw Error('Missing combo art');G.Naruto.choose(30001);await G.Flow.play();if(G.Game.state==='playing')G.Game.togglePause();G.UI.hideAll();document.querySelector('#tap-start').style.display='none';document.querySelectorAll('.toast,#ach-pop').forEach(e=>e.style.display='none')}""")
            report = view.evaluate(CHECK)
            for stage, rank, age in [('sword', 2, 2.46), ('heavy-drop', 3, .91), ('oil', 4, 3.12), ('transform', 5, 7.5), ('fox', 5, 8.05)]:
                view.evaluate("""([stage,rank,age])=>{const A=summonComboEvidence,state=stage==='oil'?A.oilSetup(rank):A.cast(rank);if(stage==='sword'||stage==='fox'){A.enemy(240,0);A.rebuild()}A.at(state.f,age,true);G.Camera.x=80;}""", [stage, rank, age])
                page.wait_for_timeout(70)
                page.screenshot(path=str(OUT / f'{label}-{stage}.png'))
            view.evaluate("""()=>{const A=summonComboEvidence,state=A.oilSetup();A.at(state.f,3.12);for(let i=0;i<250&&!state.f.oil;i++)A.step(.005,true);if(!state.f.oil)throw Error('tag screenshot missing contacted oil');window.summonCapture=state;}""")
            page.wait_for_timeout(70)
            page.screenshot(path=str(OUT / f'{label}-tag.png'))
            view.evaluate("""()=>{const A=summonComboEvidence,state=summonCapture;for(let i=0;i<350&&!state.f.oil.ignited;i++)A.step(.005,true);if(!state.f.oil.ignited)throw Error('fire screenshot missing ignition');A.step(.08,true)}""")
            view.evaluate('(mobile)=>{G.Camera.x=mobile?summonCapture.f.oil.x:80}', mobile)
            page.wait_for_timeout(70)
            page.screenshot(path=str(OUT / f'{label}-fire.png'))
            view.evaluate("""()=>{const A=summonComboEvidence,state=A.oilSetup();state.target.x=-80;A.rebuild();A.at(state.f,3.12);for(let i=0;i<250&&!state.f.oil;i++)A.step(.005,true);if(!state.f.oil||!G.NarutoSummoning.poseFor(G.Game.player)?.mirror)throw Error('left tag screenshot missing mirrored throw');G.Camera.x=-20;}""")
            page.wait_for_timeout(70)
            page.screenshot(path=str(OUT / f'{label}-left-tag.png'))
            assert not errors, errors
            if mobile:
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'mobile overflow'
            report['errors'] = errors
            report['runtimeSHA256'] = hashlib.sha256((ROOT / '.omx/naruto-summoning.js').read_bytes()).hexdigest()
            reports[label] = report
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    print(json.dumps(reports))


if __name__ == '__main__':
    main()
