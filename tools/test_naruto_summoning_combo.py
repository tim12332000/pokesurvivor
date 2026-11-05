"""Five-rank Gamabunta combo: native contacts, stage geometry, art and cleanup."""
import hashlib
import json
import mimetypes
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright

from test_naruto_summoning import CHROME, ROOT, URL, start_naruto_run

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
  assert(!(f.events||[]).some(event=>/fire|fox/i.test(event.kind)),'late stage triggered before its time');
 }
 reports.tiers=tiers;checks.push('all ranks arrival timing and three-target boundary','rank-gated sword events','no early fire or fox');
 let {m,f,anchor}=cast(2);at(f,2.16);anchor.dead=true;anchor.hp=0;
 let victims=[enemy(185,0),enemy(185,35),enemy(185,-35),enemy(-50,0),enemy(100,190)];rebuild();let before=victims.map(e=>e.hp);
 at(f,2.44);assert(victims.every((e,i)=>e.hp===before[i]),'sword damaged before contact');reports.swordArt=art(f,'gamabunta-sword-v1.png');
 at(f,2.46);reports.swordDamage=delta(victims,before);assert(reports.swordDamage.slice(0,3).every(value=>value>0)&&reports.swordDamage.slice(3).every(value=>value===0),'sword sector missed inside or hit behind/outside');
 const swordHP=victims.map(e=>e.hp);at(f,2.79);assert(victims.every((e,i)=>e.hp===swordHP[i]),'sword hit repeated');
 assert(hitLog.filter(hit=>hit.age>2.4).every(hit=>hit.owner&&hit.mid===id),'sword lost damage attribution');checks.push('dedicated sword art','sword contact timing','sword sector three inside and two outside','sword once and attribution');
 function fireSetup(rank=4,mirror=false){
  const state=cast(rank);at(state.f,2.85);state.anchor.dead=true;state.anchor.hp=0;for(const shot of projectiles())G.Projectiles.remove(shot);
  const target=enemy(mirror?-80:280,0);rebuild();return {...state,target};
 }
 let setup=fireSetup();({m,f}=setup);at(f,3.09);assert(f.fireAt==null,'fire started early');
 const origin=S.flameMouth(f),aim=Math.atan2(.25,1),c=Math.cos(aim),sn=Math.sin(aim);
 const point=(along,side)=>enemy(origin.x+c*along-sn*side,origin.y+sn*along+c*side);
 victims=[setup.target,point(140,20),point(160,-20),point(150,140),point(280,0)];rebuild();before=victims.map(e=>e.hp);
 at(f,3.12);assert(f.fireAt!=null&&f.fireOrigin&&f.fireHits.size===0,'breath did not start at mouth before reaching targets');
 assert(!projectiles('oil').length&&!projectiles('tag').length&&!S.poseFor(p),'breath still depends on oil or Naruto tag');
 assert(Math.hypot(f.fireOrigin.x-origin.x,f.fireOrigin.y-origin.y)<.01,'fire origin missed mouth');
 reports.fireArt=art(f,'gamabunta-breath-actor-v1.png');at(f,3.5);reports.fireDamage=delta(victims,before);reports.flameAtlas=art(f,'gamabunta-oil-flame-v1.png');
 const pausedFire=JSON.stringify({age:f.age,hp:victims.map(e=>e.hp),hits:[...f.fireHits]});
 G.Combat.updateFields(0);art(f,'gamabunta-breath-actor-v1.png');
 assert(pausedFire===JSON.stringify({age:f.age,hp:victims.map(e=>e.hp),hits:[...f.fireHits]}),'paused fire advanced or rendering changed damage');
 assert(reports.fireDamage.slice(0,3).every(value=>value>0)&&reports.fireDamage.slice(3).every(value=>value===0),'fire cone three inside / side and range outside: '+JSON.stringify({damage:reports.fireDamage,origin,actual:f.fireOrigin,aim:f.fireAim,targets:victims.map(e=>({x:e.x,y:e.y,r:e.r}))}));
 const fireHP=victims.map(e=>e.hp);at(f,4.1);assert(victims.every((e,i)=>e.hp===fireHP[i]),'fire repeated damage');
 assert(f.events.filter(e=>e.kind==='fire').length===1,'fire repeated event');
 checks.push('direct mouth-origin flame without oil/tag','growing cone three inside and two outside','once-only fire damage');
 setup=fireSetup(4,true);({f}=setup);at(f,3.5);assert(f.mirror&&f.fireHits.has(setup.target.id),'left breath missed');checks.push('left direct fire');
 setup=cast(4);({f}=setup);at(f,3.5);assert(f.fireAt!=null&&Math.cos(f.fireAim)>0,'under-body target made breath fire backwards or disappear');
 checks.push('under-body target still emits forward breath');
 setup=cast(5);({f}=setup);at(f,2.85);G.EnemyMgr.clear();G.Projectiles.clear();at(f,3.5);
 assert(f.fireAt!=null&&S.phaseFor(f)==='fire','cleared wave silently cancelled the fire stage');
 reports.emptyWaveFireArt=art(f,'gamabunta-breath-actor-v1.png');
 checks.push('fire still plays after other max-rank skills clear the wave');
 setup=fireSetup();({f}=setup);reports.flameAnimation=[];
 for(const age of [3.14,3.22,3.29,3.37,3.45,3.76]){
  at(f,age);art(f,'gamabunta-oil-flame-v1.png');reports.flameAnimation.push(S.flameFrame(f));
 }
 assert(JSON.stringify(reports.flameAnimation)==='[0,1,2,3,4,5]','authored ignition/loop/recovery frames missing');
 checks.push('six dedicated ignition/build/loop/recovery art frames');
 setup=fireSetup();({f}=setup);at(f,3.12);G.World.projectileBlock=(x,y)=>x>225&&x<245?'wall':false;const wallHP=setup.target.hp;at(f,3.8);assert(setup.target.hp===wallHP,'fire crossed wall');checks.push('wall blocks fire');
 for(const cleanup of ['death','world','owner','skill']){
  setup=fireSetup();({f}=setup);at(f,3.12);const world=G.World,hp=setup.target.hp;
  if(cleanup==='death'){p.dead=true;p.hp=0}if(cleanup==='world')G.World=Object.create(world);if(cleanup==='owner')G.Combat.clearFields(p);if(cleanup==='skill')G.DigimonSkills.clear(p);
  try{G.Combat.updateFields(.1);assert(!S.effects.length&&setup.target.hp===hp,'fire survived '+cleanup)}finally{G.World=world}
 }
 checks.push('active fire cleanup death/world/owner/skill');
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
 setup=cast(4);({f}=setup);enemy(280,0);rebuild();G.Combat.updateFields(6);G.Combat.updateFields(.01);
 const lateStages=f.events.filter(event=>['sword','fire'].includes(event.kind));
 assert(!lateStages.length,'large frame released missed sword/oil phases: '+JSON.stringify(lateStages));
 checks.push('large in-lifetime frame discards missed sword and fire windows');
 setup=cast(5);({f}=setup);enemy(280,0);rebuild();G.Combat.updateFields(8.5);G.Combat.updateFields(.01);
 const lateRankFive=f.events.filter(event=>['sword','fire','transform','fox'].includes(event.kind));
 assert(!lateRankFive.length,'large rank-five frame replayed missed phases: '+JSON.stringify(lateRankFive));
 checks.push('large rank-five in-lifetime frame skips missed transform and fox');
 window.summonComboEvidence={reset,cast,at,step,enemy,rebuild,fireSetup,art};
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
            start_naruto_run(view)
            report = view.evaluate(CHECK)
            for stage, rank, age in [('sword', 2, 2.46), ('heavy-drop', 3, .91), ('fire', 4, 3.5), ('fire-start', 4, 3.14), ('fire-build', 4, 3.22), ('fire-loop-a', 4, 3.29), ('fire-loop-b', 4, 3.37), ('fire-loop-c', 4, 3.45), ('fire-end', 4, 3.76), ('transform', 5, 7.5), ('fox', 5, 8.05)]:
                view.evaluate("""([stage,rank,age])=>{const A=summonComboEvidence,state=stage.startsWith('fire')?A.fireSetup(rank):A.cast(rank);if(stage==='sword'||stage==='fox'){A.enemy(240,0);A.rebuild()}A.at(state.f,age,true);G.Camera.x=80;}""", [stage, rank, age])
                page.wait_for_timeout(70)
                page.screenshot(path=str(OUT / f'{label}-{stage}.png'))
            view.evaluate("""()=>{const A=summonComboEvidence,state=A.fireSetup(4,true);A.at(state.f,3.5,true);G.Camera.x=-20;}""")
            page.wait_for_timeout(70)
            page.screenshot(path=str(OUT / f'{label}-left-fire.png'))
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
