"""Rock Lee acceptance through the ordinary game entry, actual combat and artwork.

Requires the repository HTTP server on 8004. Controlled arenas omit procedural
terrain except the explicit wall test; no actors, hits or art are substituted.
"""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_redrawn_heroes import AUDIT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/rock-lee'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=rock-lee'

SETUP = r"""() => {
 const A=Acceptance,p=A.p();
 A.leeArena=()=>{A.arena();p.percentHealthDamage=0;p.lifestealRate=0;p.critChance=0;p.quantityBonus=0;};
 A.spawn=(x,y,boss=false)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
   e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;};
 A.actualCast=id=>{const m=A.select(id);let n=0;const cast=p.cast;
   p.cast=function(...args){n++;return cast.apply(this,args)};
   try{A.resume();G.Combat.tick(.001,p,0)}finally{p.cast=cast;A.pause()}
   A.assert(n===1,'Combat.tick did not cast '+id+' count='+n);return m;};
 A.advance=dt=>{A.resume();try{G.Combat.updateFields(dt);p.anim.update(dt)}finally{A.pause()}};
 A.leeArena();
}"""

PROGRESSION = r"""() => {
 const A=Acceptance,p=A.p(),out={levels:[],isolated:[]},ids=['naruto-lotus','naruto-gates','naruto-reverse-lotus'];
 A.assert(p.moves.length===1&&p.hasMove('naruto-lee'),'Lee must start with signature only');
 for(const level of [1,3,6,9,12]){
   p.level=level;const pool=G.Moves.poolFor(p.mon),cards=G.LevelUp.offer(p,100);
   ids.forEach((id,i)=>{const eligible=level>=[3,6,9][i];A.assert(pool.includes(id)===eligible,'wrong pool gate '+id+' Lv'+level);
     A.assert(cards.some(c=>c.key==='new:'+id)===eligible,'wrong card gate '+id+' Lv'+level)});
   out.levels.push({level,pool,cards:cards.map(c=>c.key)});
 }
 const originalMon=p.mon;
 for(const dex of [30001,30002,20001]){
   p.mon=G.DEX.find(m=>m.dex===dex)||{dex,gen:10,types:['normal']};
   const pool=G.Moves.poolFor(p.mon);A.assert(!pool.some(id=>ids.includes(id)||id==='naruto-lee'),'Lee leaked into '+dex);out.isolated.push(dex);
 }p.mon=originalMon;
 p.level=12;
 // A genuinely full legacy loadout must replace a retired tool, not drop a card.
 const primary=p.moves[0];p.moves=[primary];p.slots=[[primary]];p.active=0;
 for(const id of ['naruto-kunai','naruto-shuriken','tackle','scratch']){
   if(p.slots.length<p.maxMoves&&G.Moves.BY_ID[id])p.addMove(id);
 }
 A.assert(p.slots.length===p.maxMoves,'full-slot fixture incomplete '+p.slots.length);
 for(const id of ids)if(!p.hasMove(id)){
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
   // Two retired tool slots can be reclaimed; a truly full signature loadout
   // must not silently overwrite another skill to fit a third new technique.
   if(id!=='naruto-gates'&&p.slots.length>=p.maxMoves&&!p.moves.some(m=>['naruto-kunai','naruto-shuriken'].includes(m.id))){
     A.assert(!card,'offered impossible full-slot card '+id);break;
   }
   A.assert(card&&card.apply(p)!==false,'full-slot signature unavailable '+id);
 }
 for(const id of ids)if(!p.hasMove(id)){
   const removable=p.moves.find(m=>m.id!==primary.id&&!ids.includes(m.id));
   p.moves=p.moves.filter(m=>m!==removable);p.slots=p.slots.filter(s=>!s.includes(removable));
   A.assert(p.addMove(id),'final test loadout missing '+id);
 }
 A.assert(ids.every(id=>p.hasMove(id)),'Lee loadout incomplete');
 out.slots=p.slots.length;return out;
}"""

COMBAT = r"""() => {
 const A=Acceptance,p=A.p(),out={},near=(a,b)=>Math.abs(a-b)<.001;
 // Wide fan must damage three separated real enemies and spare the outside one.
 A.leeArena();const m=A.select('naruto-lee'),r=m.radius;
 const es=[A.spawn(65,-45),A.spawn(80,0),A.spawn(65,45),A.spawn(r+80,0)];p.target=es[1];p.aim=0;
 A.actualCast(m.id);A.advance(.02);
 A.assert(es.slice(0,3).every(e=>e.hp<100000)&&es[3].hp===100000,'whirlwind AOE coverage');
 out.whirlwind=es.map(e=>100000-e.hp);
 for(const [id,hits,quantity] of [['naruto-lotus',2,0],['naruto-reverse-lotus',7,0],['naruto-lotus',2,3],['naruto-reverse-lotus',7,3]]){
   A.leeArena();const e=A.spawn(110,0),outside=A.spawn(400,0);p.target=e;p.aim=0;p.percentHealthDamage=.01;p.lifestealRate=.001;p.hp=p.maxHp/2;
   let n=0,owned=true,crit=true,total=0;const hurt=e.hurt;e.hurt=function(...args){n++;owned&&=args[6]===p;crit&&=args[5]==='crit';total+=args[0]+1000;return hurt.apply(this,args)};
   p.critChance=1;p.quantityBonus=quantity;const before=p.dmgDealt,hp=p.hp;A.actualCast(id);
   const phases=[],positions=[];for(let i=0;i<180&&G.NarutoLee.active;i++){
     phases.push(G.NarutoLee.active.phase);positions.push(p.x);A.advance(.01);
   }
   A.assert(!G.NarutoLee.active,'combo did not finish '+id);
   A.assert(n===hits&&owned&&crit,'wrong owned critical hit count '+id+' '+n);
   A.assert(near(p.dmgDealt-before,total),'damage credit recursion '+id);
   A.assert(near(p.hp-hp,total*.001*(G.NarutoGates?.healingMultiplier(p)||1)),'lifesteal credit '+id);
   A.assert(outside.hp===100000,'outside target damaged');
   A.assert(phases.includes('approach')&&phases.includes('windup')&&phases.includes('lift')&&phases.includes('slam')&&phases.includes('recovery'),'missing motion phases '+id);
   A.assert(positions.some(x=>x>0)&&positions.every((x,i)=>!i||x-positions[i-1]<=4.81),'approach teleported');
   A.assert(!G.NarutoLee.liftFor(e)&&!e.jumpLift,'target lift survived completion');out[id+(quantity?'-quantity3':'')]={hits:n,phases:[...new Set(phases)],damage:p.dmgDealt-before};
 }
 A.leeArena();let e=A.spawn(35,0,true);p.target=e;A.actualCast('naruto-lotus');A.advance(.3);
 A.assert(!e.jumpLift&&!G.NarutoLee.liftFor(e)&&!G.NarutoLee.active?.visualLift,'boss was lifted');G.Combat.clearFields();
 for(const reason of ['clear','target-death','owner-death','world']){
   A.leeArena();e=A.spawn(35,0);p.target=e;A.actualCast('naruto-lotus');A.advance(.3);A.assert(G.NarutoLee.liftFor(e)>0&&!e.jumpLift,'lift fixture missing or native jump altered');
   const world=G.World;
   if(reason==='clear')G.Combat.clearFields(p);
   if(reason==='target-death')e.dead=true;
   if(reason==='owner-death')p.dead=true;
   if(reason==='world')G.World={...world};
   A.advance(.01);G.World=world;p.dead=false;
   A.assert(!G.NarutoLee.active&&!G.NarutoLee.liftFor(e)&&!e.jumpLift,'cleanup failed '+reason);
 }
 A.leeArena();e=A.spawn(35,0);p.target=e;A.actualCast('naruto-lotus');A.advance(.3);
 const age=G.NarutoLee.active.age,lift=G.NarutoLee.liftFor(e);G.Combat.updateFields(.5);
 A.assert(G.NarutoLee.active.age===age&&G.NarutoLee.liftFor(e)===lift&&!e.jumpLift,'paused chain advanced');G.Combat.clearFields();
 // Native jumping owns jumpLift; Lee contributes only a separate render offset.
 A.leeArena();e=A.spawn(35,0);e.flying=false;e.startJump(p);e.updateJump(.55);
 A.assert(e.jump&&e.jumpLift>0,'real native jump fixture absent');p.target=e;A.actualCast('naruto-lotus');
 let native=e.jumpLift;A.advance(.3);
 A.assert(e.jumpLift===native&&G.NarutoLee.liftFor(e)>0,'Lee overwrote native jump height');
 for(let i=0;i<3;i++){
   e.updateJump(.04);native=e.jumpLift;A.advance(.01);
   A.assert(e.jumpLift===native&&G.NarutoLee.liftFor(e)>0,'native update and Lee lift interfered');
 }
 const canvas=document.createElement('canvas');canvas.width=canvas.height=240;const ctx=canvas.getContext('2d');
 let drawY=null;const draw=e.anim.draw;e.anim.draw=function(context,x,y,options){drawY=y;return draw.call(this,context,x,y,options)};
 try{e.draw(ctx)}finally{e.anim.draw=draw}
 A.assert(near(drawY,e.y-native-G.NarutoLee.liftFor(e)),'enemy draw did not combine native and Lee heights');
 G.Combat.clearFields(p);A.assert(e.jumpLift===native&&!G.NarutoLee.liftFor(e),'cancel altered native jump');
 e.updateJump(.1);native=e.jumpLift;A.advance(.01);A.assert(e.jumpLift===native&&native>=0,'native jump corrupted after cancellation');
 out.nativeJump={separateLift:true,combinedDrawHeight:true,cancelPreservesNative:true};
 A.leeArena();e=A.spawn(100,0);p.target=e;
 const wall=G.World.isWall;G.World.isWall=(x,y)=>x>40&&x<60;
 A.assert(!G.NarutoLee.canCast(p,A.select('naruto-lotus')),'target acquired through wall');G.World.isWall=wall;
 A.leeArena();e=A.spawn(120,0);p.target=e;A.actualCast('naruto-lotus');
 const free=G.World.isFree;G.World.isFree=(x,y)=>x<=20;
 A.advance(.2);G.World.isFree=free;
 A.assert(!G.NarutoLee.active&&p.x<=20&&e.hp===100000,'approach passed blocked ground');
 out.cleanup=['clear','target-death','owner-death','world','pause','wall','blocked-approach','boss-no-lift'];
 A.leeArena();const gates=p.moves.find(m=>m.id==='naruto-gates');
 A.assert(gates?.passive&&G.NarutoGates.stage(p)===1,'gates learned passive missing');
 A.assert(!p.slots.some(group=>group.includes(gates)),'gates consumed active slot');
 const atk=p.atk,spd=p.spd;A.select('naruto-lee');
 for(let n=0;n<100;n++)A.advance(.1);
 A.assert(near(p.atk,atk)&&near(p.spd,spd),'passive gates timed out or stacked');
 G.Combat.clearFields(p);A.advance(.01);
 A.assert(near(p.atk,atk)&&near(p.spd,spd),'field clear disabled learned gates');
 out.gates='permanent learned passive, slotless, switch/clear safe, no fatigue';return out;
}"""

ART = r"""() => {
 const A=Acceptance,p=A.p(),out={};
 A.leeArena();
 for(const [direction,dir] of [['down',0],['right',2],['up',4],['left',6]]){
   p.anim.dir=dir;p.walking=false;p.anim.play('Idle');out['idle-'+direction]=A.render();
   p.walking=true;p.anim.play('Walk');out['movement-'+direction]=A.render();
 }
 A.leeArena();p.hurt(10,null,true);out.hurt=A.render();out.flash=A.render(p.anim,{flash:true,alpha:.5});
 A.leeArena();p.dead=true;p.hp=0;p.anim.play('Faint',{hold:true});out.death=A.render();
 p.dead=false;p.hp=p.maxHp;p.anim.play('Idle');
 for(const id of ['naruto-lee','naruto-lotus','naruto-reverse-lotus']){
   A.leeArena();const e=A.spawn(65,0);p.target=e;p.aim=0;A.actualCast(id);
   for(const [i,dt] of [0,.12,.16,.18,.18,.18,.18,.24,.24].entries()){
     if(dt)A.advance(dt);out[id+'-'+i]=A.render();
   }
   const expected={'naruto-lee':'lee-whirlwind','naruto-lotus':'lee-lotus','naruto-reverse-lotus':'lee-reverse'}[id].replace(/^lee-/,G.NarutoGates.redSkin(p)?'lee-opened-':'lee-');
   A.assert(Object.entries(out).some(([name,sample])=>name.startsWith(id+'-')&&sample.state.key===expected),'dedicated skill art never used '+id);
 }
 for(const [name,sample] of Object.entries(out)){
   A.assert(sample.sources.length&&sample.sources.every(src=>new URL(src).pathname.includes('/redrawn/lee-')),'non-Lee authored source '+name);
   A.assert(sample.state.key.startsWith('lee-'),'non-Lee animation mapping '+name);
 }
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
                context = browser.new_context(locale='zh-TW', viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('response', lambda r: report['failedRequests'].append(r.url) if r.status>=400 and '127.0.0.1' in r.url else None)
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
                button = page.locator('[data-quick-naruto="30006"]')
                button.click()
                assert page.evaluate('G.DB.save.partner===30006'), 'normal menu did not select Lee'
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30006 && G.Game.state==="playing"')
                page.evaluate(HARNESS)
                page.evaluate(SETUP)
                result = {'progression': page.evaluate(PROGRESSION)}
                report['viewports'][label]=result
                result['fractionalContact'] = page.evaluate("""() => {
                  const A=Acceptance,p=A.p(),radius=p.r,out=[];
                  try {
                    for(const id of ['naruto-lotus','naruto-reverse-lotus']) {
                      A.leeArena();p.r=12;p.x=245.2212490607053;p.y=607.796689029783;
                      p.target=A.spawn(264.44099647663217,639.8360687385729);p.target.r=10;
                      A.actualCast(id);A.advance(1/60);
                      A.assert(G.NarutoLee.active?.phase==='windup','fractional contact did not finish approach');
                      for(let n=0;n<90;n++)A.advance(1/60);
                      A.assert(!G.NarutoLee.active,'fractional contact did not finish recovery');out.push(id);
                    }
                  } finally {p.r=radius;A.leeArena()}
                  return out;
                }""")
                page.evaluate('Acceptance.leeArena()')
                page.keyboard.down('KeyD')
                result['keyboard'] = page.evaluate("""() => {const A=Acceptance,p=A.p(),x=p.x;
                  A.resume();p.update(.08);A.pause();A.assert(p.x>x&&p.walking,'real keyboard movement');return {dx:p.x-x}}""")
                page.keyboard.up('KeyD')
                if mobile:
                    page.evaluate('Acceptance.leeArena();Acceptance.resume()')
                    client=context.new_cdp_session(page)
                    base=page.evaluate('G.Touch.stickBase()')
                    client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':base['x'],'y':base['y']}]})
                    client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':base['x']+45,'y':base['y']}]})
                    result['touch']=page.evaluate("""() => {const A=Acceptance,p=A.p(),x=p.x;
                      A.assert(G.Touch.vector()?.[0]>0,'real touchscreen joystick absent');p.update(.08);A.pause();
                      A.assert(p.x>x,'touchscreen did not move Lee');return {dx:p.x-x}}""")
                    client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                result['combat']=page.evaluate(COMBAT)
                result['upgrades']=page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p(),out={};
                  for(const id of ['naruto-lee','naruto-lotus','naruto-reverse-lotus']){
                    const m=p.moves.find(m=>m.id===id);out[id]=[];
                    for(let lvl=1;lvl<=5;lvl++){
                      if(lvl>1){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);
                        A.assert(card&&card.apply(p)!==false,'missing upgrade '+id+' '+lvl)}
                      A.assert(m.lvl===lvl&&Number.isFinite(m.dmg)&&Number.isFinite(m.cd),'invalid level '+id+' '+lvl);
                      out[id].push({level:m.lvl,damage:m.dmg,cooldown:m.cd,radius:m.radius||null});
                    }
                  }return out;
                }""")
                page.evaluate(AUDIT)
                result['art'] = page.evaluate(ART)
                for name, pose in result['art'].items():
                    (OUT/f'{label}-{name}.png').write_bytes(base64.b64decode(pose.pop('png').split(',',1)[1]))
                result['restart']=page.evaluate("""() => {
                  const A=Acceptance,p=A.p();A.leeArena();p.target=A.spawn(35,0);A.actualCast('naruto-lotus');A.advance(.3);
                  const target=p.target;A.assert(G.NarutoLee.liftFor(target)>0&&!target.jumpLift,'restart fixture lift');
                  G.Game.toUI();A.assert(!G.NarutoLee.active&&!G.NarutoLee.liftFor(target)&&!target.jumpLift,'menu left active combo');
                  G.Flow.play();G.Game.togglePause();
                  A.assert(G.Game.player!==p&&G.Game.player.dex===30006&&!G.NarutoLee.active,'restart retained chain');return true;
                }""")
                page.evaluate('G.UI.hide("scr-pause")')
                page.screenshot(path=str(OUT/f'{label}.png'))
                # The technique's input hold is simulation behavior and survives
                # the original-art diagnostic entry (no AnimationLab installed).
                page.goto(URL+'&originalArt=1')
                page.wait_for_function("window.G?.Game && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30006"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
                page.evaluate("""() => {
                  G.Game.togglePause();const p=G.Game.player;
                  G.World.isFree=()=>true;G.World.isWall=()=>false;G.World.projectileBlock=()=>false;G.World.collide=()=>{};
                  p.x=p.y=0;p.addMove('naruto-lotus');p.setActive(p.slots.findIndex(s=>s.some(m=>m.id==='naruto-lotus')));
                  G.EnemyMgr.clear();const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},35,0,{hp:1,spd:1,dmg:1});
                  G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();p.target=e;
                  G.Game.togglePause();G.Combat.tick(.001,p,0);
                  if(!G.NarutoLee.active)throw Error('baseline contact cast failed');
                }""")
                if mobile:
                    base=page.evaluate('G.Touch.stickBase()')
                    client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':base['x'],'y':base['y']}]})
                    client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':base['x']+45,'y':base['y']}]})
                else:page.keyboard.down('KeyD')
                result['originalArtInputHold']=page.evaluate("""() => {
                  const p=G.Game.player,x=p.x,y=p.y,frozen=p.frozen;
                  if(!(G.Input.axis()[0]>0))throw Error('baseline movement input absent');
                  p.update(.08);if(p.x!==x||p.y!==y||p.frozen!==frozen)throw Error('input escaped contact hold');
                  p.invuln=0;const hp=p.hp;p.hurt(5,null,true);if(p.hp>=hp)throw Error('contact hold granted invulnerability');return true;
                }""")
                if mobile:client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                else:page.keyboard.up('KeyD')
                report['viewports'][label] = result
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        assert not report['failedRequests'], report['failedRequests']
        report['ok'] = True
    except Exception as error:
        report['ok'] = False
        report['failure'] = str(error)
        raise
    finally:
        (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':report['ok'],'viewports':list(report['viewports']),
                      'poses':sum(len(v['art']) for v in report['viewports'].values()),
                      'errors':report['errors'],'evidence':str(OUT)},ensure_ascii=False))


if __name__ == '__main__':
    main()
