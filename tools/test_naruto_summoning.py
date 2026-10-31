"""Normal-entry Gamabunta summon gameplay and desktop/mobile evidence."""
import hashlib
import json
import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/naruto-summoning/gameplay'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&layout=wide'

CHECK = r"""() => {
 const assert=(v,m)=>{if(!v)throw Error(m)},p=G.Game.player,S=G.NarutoSummoning,id='naruto-toad-summon';
 assert(S&&G.AnimationLab.enabled,'normal entry did not load summon and approved art');
 const open=()=>Object.assign(G.World,{isWall:()=>false,isFree:()=>true,collide:()=>{},propsInCircle:()=>[],projectileBlock:()=>false,isLiquid:()=>false});
 open();G.Camera.sees=()=>true;
 const enemy=(x,y)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];e.touchCd=999;G.EnemyMgr.add(e);return e};
 function reset(){
  G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();G.NarutoClones.clear();open();
  G.SelfClones.clear(p);
  p.x=p.y=0;p.aim=0;p.hp=p.maxHp;p.dead=false;p.flash=p.invuln=0;p.critChance=0;p.percentHealthDamage=0;p.lifestealRate=0;
  p.level=12;p.quantityBonus=p.quantityPicks=0;p.cdMul=1;p.moves=[];p.slots=[];p.bind={};p.active=0;p.addMove(id);
  G.Camera.x=G.Camera.y=0;return p.moves.find(m=>m.id===id);
 }
 const step=seconds=>{for(let t=0;t<seconds-1e-9;){const dt=Math.min(.005,seconds-t);G.Combat.updateFields(dt);G.FX.update(dt);p.anim.update(dt);t+=dt}};
 const fly=seconds=>{for(let t=0;t<seconds-1e-9;){const dt=Math.min(.005,seconds-t);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,t);G.Combat.updateFields(dt);G.FX.update(dt);p.anim.update(dt);t+=dt}};
 const water=()=>G.Projectiles.all().filter(shot=>shot.mid===id&&shot.mtype==='water');
 function seed(){const es=[[100,0],[100,65],[145,-40],[100,180]].map(([x,y])=>enemy(x,y));G.EnemyMgr.rebuildGrid();p.target=es[0];return es}
 let m=reset();assert(m&&m.cd===12&&m.dmg===160&&m.radius===115&&m.range===320&&m.duration===2.6,'base skill balance differs');
 p.level=11;assert(!G.Moves.poolFor(p.mon).includes(id),'summon offered before level 12');
 p.level=12;assert(G.Moves.poolFor(p.mon).includes(id),'summon missing at level 12');
 for(const dex of [30002,30003,30004,30005,30006,30007,30008,30009,30010,30011,30012])assert(!G.Moves.poolFor(G.DEX_BY[dex]).includes(id),'summon leaked to another ninja '+dex);
 p.moves=[];p.slots=[];p.narutoMilestonesShown=new Set();p.level=11;
 const maxMoves=p.maxMoves;p.addMove('naruto-kunai');p.maxMoves=1;const selectedBeforeLearn=p.activeGroup();
 assert(!G.LevelUp.offer(p,100).some(card=>card.key==='new:'+id),'summon learning card offered before level 12');
 p.level=12;const learn=G.LevelUp.offer(p,100).find(card=>card.key==='new:'+id);
 assert(learn&&learn.guaranteed&&learn.apply(p)&&p.hasMove(id),'level-12 milestone card failed to teach summon');
 m=p.moves.find(move=>move.id===id);assert(m.passive&&m.autoCast&&!p.slots.some(group=>group.includes(m)),'learned summon occupied an active slot');
 assert(p.slots.length===1&&p.activeGroup()===selectedBeforeLearn,'learning summon at full slots changed selection');p.maxMoves=maxMoves;
 const tiers=[],tierDamage=[160,192,192,192,240],tierCd=[12,12,10.8,10.8,10.8],tierRadius=[115,115,128.8,128.8,128.8];
 for(let i=0;i<5;i++){
  assert(m.lvl===i+1&&Math.abs(m.dmg-tierDamage[i])<1e-8&&Math.abs(m.cd-tierCd[i])<1e-8&&Math.abs(m.radius-tierRadius[i])<1e-8,'tier '+(i+1)+' upgrade balance differs');
  const rebuilt=G.Moves.instance(id,i+1);assert(rebuilt.dmg===m.dmg&&rebuilt.cd===m.cd&&rebuilt.radius===m.radius,'loaded tier differs from sequential upgrades');
  tiers.push({level:m.lvl,damage:m.dmg,cooldown:m.cd,radius:m.radius});if(i<4)assert(G.Moves.levelUp(m),'upgrade rejected before max tier');
 }
 assert(!G.Moves.levelUp(m),'summon upgraded past tier five');m=reset();
 assert(!S.canCast(p,m)&&!S.cast(p,m),'summon cast without an eligible target');
 const es=seed(),before=es.map(e=>e.hp);assert(S.cast(p,m),'summon rejected');assert(S.effects.length===1,'missing summon');
 step(.64);assert(es.every((e,i)=>e.hp===before[i]),'damage before landing');
 step(.02);const damage=es.map((e,i)=>before[i]-e.hp);assert(damage.slice(0,3).every(d=>d>0)&&damage[3]===0,'three inside / one outside AoE boundary failed');
 const landed=es.map(e=>e.hp);step(.3);assert(es.every((e,i)=>e.hp===landed[i]),'landing damage repeated');
 step(2);assert(!S.effects.length,'summon did not expire');
 m=reset();let targets=seed();assert(S.cast(p,m),'fixed site cast rejected');targets[0].dead=true;targets[0].hp=0;targets[0].x=800;step(.7);assert(targets[1].hp<100000&&targets[2].hp<100000,'target death canceled fixed landing AoE');
 m=reset();targets=seed();targets[2].x=200;targets[2].y=0;G.EnemyMgr.rebuildGrid();
 G.World.isWall=(x,y)=>x>=165&&x<=175;G.World.projectileBlock=G.World.isWall;
 assert(S.cast(p,m),'unblocked target rejected');step(.7);assert(targets[0].hp<100000&&targets[2].hp===100000,'landing damaged through a wall');
 m=reset();targets=seed();G.World.isWall=(x,y)=>x>=45&&x<=55;G.World.projectileBlock=G.World.isWall;
 assert(!S.canCast(p,m)&&!S.cast(p,m),'cast acquired a target behind wall');
 m=reset();targets=seed();p.quantityBonus=p.quantityPicks=4;assert(S.cast(p,G.Quantity.snapshot(p,m)),'quantity cast rejected');assert(S.effects.length===1,'quantity multiplied summons');
 step(.7);const quantityDamage=targets.map(e=>100000-e.hp);assert(JSON.stringify(quantityDamage)===JSON.stringify(damage),'quantity changed summon impact damage');
 m=reset();targets=seed();S.cast(p,m);
 const cv=document.createElement('canvas');cv.width=420;cv.height=340;const ctx=cv.getContext('2d');ctx.translate(120,180);
 const state=()=>JSON.stringify({effects:S.effects.map(f=>Object.fromEntries(Object.entries(f).filter(([k,v])=>v==null||['number','string','boolean'].includes(typeof v)))),hp:targets.map(e=>e.hp),cooldown:m.t});
 const snap=state();G.Combat.updateFields(0);G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);const first=cv.toDataURL();
 ctx.clearRect(-120,-180,420,340);G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);
 assert(state()===snap&&cv.toDataURL()===first,'pause or drawing changed simulation / animation');
 p.dead=true;G.Combat.updateFields(.01);assert(!S.effects.length&&targets.every(e=>e.hp===100000),'owner death retained summon or dealt damage');
 m=reset();seed();S.cast(p,m);G.Combat.clearFields(p);assert(!S.effects.length,'owner field clear retained summon');
 S.cast(p,m);G.DigimonSkills.clear(p);assert(!S.effects.length,'skill clear retained summon');
 S.cast(p,m);const world=G.World;G.World=Object.create(world);try{G.Combat.updateFields(.01);assert(!S.effects.length,'world switch retained summon')}finally{G.World=world}
 m=reset();seed();m.t=0;G.Combat.tick(.001,p,0);assert(S.effects.length===1&&m.t>0,'native automatic selected-skill cast failed');
 const nativeCooldown=m.t;G.Combat.clearFields();m.t=0;p.cdMul=.5;G.Combat.tick(.001,p,0);assert(m.t<nativeCooldown,'cooldown card had no effect');
 m=reset();targets=seed();p.addMove('naruto-kunai');const other=p.moves.find(move=>move.id==='naruto-kunai');other.t=999;
 const selected=p.activeGroup();m.t=0;G.Combat.tick(.001,p,0);assert(S.effects.length===1&&p.activeGroup()===selected,'automatic summon failed or changed selected skill');
 m.t=0;G.Combat.tick(.001,p,0);assert(S.effects.length===1,'automatic summon overlapped itself');
 step(.7);assert(targets[0].hp<100000,'automatic summon did not finish landing');
 step(2);m.t=0;G.Combat.tick(.001,p,0);assert(S.effects.length===1,'automatic summon did not repeat after expiry');
 G.Combat.clearFields();m.passive=false;m.autoCast=false;m.t=4;m.dealt=123;p.slots=[[m,other]];p.active=0;p.bind[id]='Digit1';
 const legacyGroup=p.slots[0];p.arrange();
 assert(m.autoCast&&m.passive&&m.t===4&&m.dealt===123&&!p.bind[id]&&p.activeGroup()===legacyGroup&&legacyGroup.length===1&&legacyGroup[0]===other,'legacy summon migration lost timer, stats or selected group');
 m=reset();targets=seed();const actor=G.LevelUp.STATS.find(card=>card.id==='selfClone').apply(p);
 assert(actor&&G.SelfClones.isControlled(actor),'self-card clone was not created');
 const actorMove=actor.moves.find(move=>move.id===id);assert(actorMove&&S.cast(actor,actorMove)&&S.cast(p,m)&&S.effects.length===2,'independent owners did not summon');
 step(.7);enemy(270,0);G.EnemyMgr.rebuildGrid();step(.42);assert(water().some(shot=>shot.owner===actor)&&water().some(shot=>shot.owner===p),'independent owners did not fire water');
 G.Combat.clearFields(actor);assert(S.effects.length===1&&S.effects[0].owner===p,'clearing self-card clone erased player summon');
 assert(water().length===1&&water()[0].owner===p,'clearing clone erased player water or retained clone water');
 assert(targets[0].hp<100000,'player summon failed after clone clear');
 function prepareWater(quantity=0){
  const move=reset(),anchor=enemy(100,0);G.EnemyMgr.rebuildGrid();p.target=anchor;p.quantityBonus=p.quantityPicks=quantity;
  assert(S.cast(p,G.Quantity.snapshot(p,move)),'water setup summon rejected');step(.7);anchor.dead=true;anchor.hp=0;
  const victim=enemy(270,0);G.EnemyMgr.rebuildGrid();return {move,victim};
 }
 m=reset();const bodyTarget=enemy(100,0);G.EnemyMgr.rebuildGrid();S.cast(p,m);step(.7);
 const frontTarget=enemy(270,0);G.EnemyMgr.rebuildGrid();step(.42);
 assert(water().length===1&&water()[0].vx>0,'right-facing water fired backwards at the under-body target');
 const rightFacingOrigin={x:water()[0].x,y:water()[0].y,vx:water()[0].vx};
 m=reset();enemy(100,0);G.EnemyMgr.rebuildGrid();S.cast(p,m);step(.7);
 enemy(-80,0);G.EnemyMgr.rebuildGrid();step(.42);
 assert(water().length===1&&water()[0].vx<0&&S.effects[0].mirror,'left-facing water did not use the mirrored mouth');
 const leftFacingOrigin={x:water()[0].x,y:water()[0].y,vx:water()[0].vx};
 m=reset();enemy(100,0);G.EnemyMgr.rebuildGrid();S.cast(p,m);step(1.95);
 assert(!water().length,'under-body-only target made the toad fire backwards');
 m=reset();enemy(100,0);G.EnemyMgr.rebuildGrid();S.cast(p,m);step(.7);
 enemy(270,0);enemy(-80,0);G.EnemyMgr.rebuildGrid();
 G.World.projectileBlock=(x,y)=>x>=220&&x<=230&&y<-10?'wall':false;
 step(.42);assert(water().length===1&&water()[0].vx<0,'blocked right mouth path prevented valid left support shot');
 let lethal=prepareWater();step(.42);assert(water().length===1,'lethal setup missing shot');
 p.item=null;p.invuln=0;p.hurt(p.maxHp*10,null,true);
 assert(p.dead&&!water().length&&!S.effects.length,'lethal hurt left frozen summon water before faint rendering');
 m=reset();enemy(100,0);G.EnemyMgr.rebuildGrid();const dependent=G.LevelUp.STATS.find(card=>card.id==='selfClone').apply(p);
 S.cast(p,m);S.cast(dependent,dependent.moves.find(move=>move.id===id));step(.7);enemy(270,0);G.EnemyMgr.rebuildGrid();step(.42);
 assert(water().some(shot=>shot.owner===dependent),'dependent clone setup missing shot');
 p.item=null;p.invuln=0;p.hurt(p.maxHp*10,null,true);
 assert(!water().length&&!S.effects.length,'summoner death left dependent clone water frozen');
 lethal=prepareWater();step(.42);p.dead=true;p.hp=0;p.update(.01);
 assert(!water().length&&!S.effects.length,'native faint player update retained water without field updates');
 lethal=prepareWater();step(.42);p.item=null;p.invuln=0;p.hurt(1,null,true);
 assert(!p.dead&&water().length===1&&S.effects.length===1,'nonlethal hurt canceled living summon support');
 let setup=prepareWater();step(.39);assert(!water().length&&setup.victim.hp===100000,'water released or damaged before 1.1 seconds');
 step(.03);assert(water().length===1&&setup.victim.hp===100000,'first volley did not release one contact-only shot');
 const shot=water()[0],source={x:shot.x,y:shot.y};assert(shot.owner===p&&shot.mid===id&&shot.mtype==='water'&&shot.r===13&&shot.life===1.25&&shot.pierce===0&&shot.damageSplash===false,'native water projectile payload differs');
 const mouth=S.mouth(S.effects[0]);assert(Math.abs(shot.x-mouth.x)<1e-8&&Math.abs(shot.y-mouth.y)<1e-8,'native origin differs from authored mouth anchor');
 assert(Math.abs(shot.dmg-setup.move.dmg*p.atk/6)<1e-8,'water damage budget differs');
 assert(p.x===0&&p.y===0&&Math.hypot(shot.x-p.x,shot.y-p.y)>100&&Math.hypot(shot.x-100,shot.y)<100,'water did not originate at summoned toad mouth');
 const paused=JSON.stringify({x:shot.x,y:shot.y,t:shot.t,age:S.effects[0].age,volley:S.effects[0].volley,hp:setup.victim.hp});
 G.Combat.updateFields(0);G.Projectiles.update(0,p,G.EnemyMgr.all());G.Combat.resolve(0,p,0);
 assert(JSON.stringify({x:shot.x,y:shot.y,t:shot.t,age:S.effects[0].age,volley:S.effects[0].volley,hp:setup.victim.hp})===paused,'pause advanced airborne water');
 step(.37);assert(water().length===1,'second volley fired early');step(.03);assert(water().length===2,'second volley missing');
 step(.37);assert(water().length===2,'third volley fired early');step(.03);assert(water().length===3,'third volley missing');
 step(.7);assert(water().length===3&&!S.effects.length,'volley cap or summon expiry differs');
 setup=prepareWater(4);step(1.25);assert(water().length===3,'quantity multiplied water volleys');
 const quantityWaterDamage=water().map(projectile=>projectile.dmg);assert(quantityWaterDamage.every(value=>Math.abs(value-shot.dmg)<1e-8),'quantity changed per-shot water damage');
 setup=prepareWater();setup.victim.dead=true;setup.victim.hp=0;step(1.25);assert(!water().length,'summon fired water without living target');
 setup=prepareWater();setup.victim.types=['rock'];const waterNeighbor=enemy(270,55);G.EnemyMgr.rebuildGrid();step(.42);const typedShot=water()[0],waterBefore=setup.victim.hp;
 const expectedWater=Math.max(1,Math.round(typedShot.dmg*G.Types.mult('water',setup.victim.types)*G.Weather.mult('water')));
 fly(.5);const waterDamage=waterBefore-setup.victim.hp;
 assert(Math.abs(waterDamage-expectedWater)<1e-7&&waterDamage>0,'native projectile contact / water type damage differs');
 assert(waterNeighbor.hp===100000,'water hit caused unintended splash damage');
 assert(!G.Projectiles.all().includes(typedShot)&&p.x===0&&p.y===0,'water pierced target or moved summoner');
 const afterWater=setup.victim.hp;G.Combat.resolve(0,p,0);assert(setup.victim.hp===afterWater,'water collision repeated damage');
 setup=prepareWater();step(.42);const blockedShot=water()[0];G.World.projectileBlock=(x,y,r)=>x>=190&&x<=210?'wall':false;
 fly(.5);assert(setup.victim.hp===100000&&!G.Projectiles.all().includes(blockedShot),'water crossed wall or damaged target behind it');
 setup=prepareWater();step(.42);const expiringShot=water()[0];setup.victim.dead=true;setup.victim.hp=0;fly(1.3);
 assert(!G.Projectiles.all().includes(expiringShot),'native water projectile did not expire');
 for(const cleanup of ['death','world','owner','skill']){
  setup=prepareWater();step(.42);const pending=water()[0];setup.victim.x=pending.x;setup.victim.y=pending.y;G.EnemyMgr.rebuildGrid();const hp=setup.victim.hp,world=G.World;
  if(cleanup==='death')p.dead=true;
  if(cleanup==='world')G.World=Object.create(world);
  if(cleanup==='owner')G.Combat.clearFields(p);
  if(cleanup==='skill')G.DigimonSkills.clear(p);
  try{G.Combat.resolve(0,p,0);assert(!G.Projectiles.all().includes(pending)&&setup.victim.hp===hp,'airborne shot survived '+cleanup+' before resolve')}finally{G.World=world}
 }
 m=reset();targets=seed();S.cast(p,m);G.Combat.updateFields(3);
 assert(!S.effects.length&&!water().length&&targets.every(target=>target.hp===100000),'expired huge frame released late damage or water');
 m=reset();targets=seed();S.cast(p,m);enemy(270,0);G.EnemyMgr.rebuildGrid();G.Combat.updateFields(1.95);
 assert(S.effects.length===1&&water().length===1,'slow frame burst all missed water volleys');G.Combat.updateFields(.05);assert(water().length===1,'discarded volleys fired on next frame');
 m=reset();targets=seed();S.cast(p,m);
 const prop={id:'summon-fixture-prop',x:180,y:0,r:12,destructible:true,solid:true,hp:100000,type:'rock'};
 G.World.propsInCircle=()=>[prop];G.World.projectileBlock=(x,y,r)=>Math.hypot(x-prop.x,y-prop.y)<prop.r+r?prop:false;
 assert(!G.World.projectilePathClear(100,0,prop.x,prop.y)&&G.World.projectilePathClear(100,0,prop.x,prop.y,prop),'native path helper did not exclude target prop');
 step(.7);assert(Math.abs(100000-prop.hp-m.dmg*.5*p.atk)<1e-7,'landing did not damage destructible target through its own collision');
 m=reset();seed();S.cast(p,m);step(.35);window.summonEvidence={step,fly,reset,seed,prepareWater};
 window.summonReviewEvidence={rightFacingOrigin,leftFacingOrigin,checks:['forward right shot skips under-body target','mirrored forward left shot','under-body-only target does not fire backwards','blocked mouth path selects valid alternative','native lethal damage clears before faint rendering','summoner death clears dependent clone water','native faint player update clears without combat updates','nonlethal damage retains support']};
 return {damage,quantityDamage,quantityWaterDamage,waterDamage,expectedWater,mouthOrigin:source,tiers,nativeCooldown,checks:['normal entry','level-12 pool gate','level-12 milestone learning card','slotless learning at full slots','all five upgrade tiers','ninja-exclusive pool','no-target rejection','three inside / one outside','landing delay','single hit','expiry','fixed site survives target death','wall occlusion','quantity does not multiply actors','quantity damage equality','render purity','pause','owner death','owner clear','skill clear','world switch','native automatic cast','selection-independent automatic cast and repeat','legacy timer and selected-group migration','self-card clone owner and shot isolation','cooldown card','water volley timing and three-shot cap','native water projectile payload','exact authored mouth source and stationary Naruto','no water damage before native contact','water quantity count and damage equality','no water without living target','water type effectiveness and native rounded damage','single native water hit and no splash','water wall collision','water projectile expiry','airborne pause','airborne death/world/owner/skill cleanup before resolve','huge frame expires without late damage','slow frame discards missed volleys','native destructible prop target exclusion']};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reports = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in [False, True]:
            errors = []
            label = 'mobile' if mobile else 'desktop'
            context = browser.new_context(
                viewport={'width': 390, 'height': 844} if mobile else {'width': 1100, 'height': 850},
                is_mobile=mobile, has_touch=mobile, locale='zh-TW', service_workers='block')

            def route(request):
                file = ROOT / unquote(urlsplit(request.request.url).path).removeprefix('/pokesurvivor/')
                request.fulfill(status=200 if file.is_file() else 404,
                                body=file.read_bytes() if file.is_file() else b'Not found',
                                content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')

            context.route('https://tim12332000.github.io/pokesurvivor/**', route)
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(URL.replace('digimon.html', 'portrait.html').replace('layout=wide', 'layout=portrait') if mobile else URL)
            view = page
            if mobile:
                page.wait_for_selector('#portrait-game')
                view = page.locator('#portrait-game').element_handle().content_frame()
            view.wait_for_function('window.PS_REDRAWN_READY && G.Flow && G.NarutoSummoning && document.getElementById("boot").classList.contains("hidden")')
            if view.locator('#tap-start').is_visible():
                view.locator('#tap-start').click()
            view.evaluate("""async()=>{await PS_REDRAWN_READY;await G.NarutoSummoning.ready;G.Naruto.choose(30001);await G.Flow.play();if(G.Game.state==='playing')G.Game.togglePause();G.UI.hideAll();document.querySelector('#tap-start').style.display='none';document.querySelectorAll('.toast,#ach-pop').forEach(e=>e.style.display='none')}""")
            report = view.evaluate(CHECK)
            review = view.evaluate('window.summonReviewEvidence')
            report['checks'].extend(review.pop('checks'))
            report['independentReview'] = review
            page.wait_for_timeout(100)
            page.screenshot(path=str(OUT / f'{label}-descent.png'))
            view.evaluate('summonEvidence.step(.36)')
            page.wait_for_timeout(100)
            page.screenshot(path=str(OUT / f'{label}-landing.png'))
            view.evaluate('summonEvidence.prepareWater();summonEvidence.step(.42)')
            page.wait_for_timeout(100)
            page.screenshot(path=str(OUT / f'{label}-water.png'))
            if mobile:
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'Mobile overflow'
            restart = view.evaluate("""async()=>{const S=G.NarutoSummoning,id='naruto-toad-summon';await G.Flow.play();if(G.Game.state==='playing')G.Game.togglePause();return {effects:S.effects.length,level:G.Game.player.level,known:G.Game.player.hasMove(id),offered:G.Moves.poolFor(G.Game.player.mon).includes(id)}}""")
            assert restart == {'effects': 0, 'level': 1, 'known': False, 'offered': False}, restart
            report['checks'].extend(['restart cleanup', 'no level-12 skill in new-run starter'])
            assert not errors, errors
            report['errors'] = errors
            report['restart'] = restart
            report['runtimeSHA256'] = hashlib.sha256((ROOT / '.omx/naruto-summoning.js').read_bytes()).hexdigest()
            reports[label] = report
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    print(json.dumps(reports))


if __name__ == '__main__':
    main()
