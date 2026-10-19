"""Actual growing fireball bodies retain themselves and deal bounded periodic AOE."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright
import json, mimetypes, os

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=fireball-persistent'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
 errors=[]
 def proxy(route):
  f=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
  route.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'Not found',content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
 def boot(mobile=False):
  c=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':820},is_mobile=mobile,has_touch=mobile,locale='zh-TW',service_workers='block')
  if os.environ.get('PAGES_LIVE')!='1':c.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
  c.route('**api.ipify.org**',lambda r:r.fulfill(json={'ip':'198.51.100.10'}))
  pg=c.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(URL)
  pg.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
  if pg.locator('#tap-start').is_visible():pg.locator('#tap-start').click()
  pg.evaluate("G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause();G.Game.player.addMove('naruto-fireball')")
  return c,pg
 try:
  context,page=boot()
  result=page.evaluate(r'''() => {
   const pl=G.Game.player,id='naruto-fireball',assert=(ok,m)=>{if(!ok)throw Error(m)},out={};
   const saved={};for(const k of ['isWall','projectileBlock','propsInCircle','damageProp'])saved[k]=G.World[k];
   const sees=G.Camera.sees,weather=G.Weather.mult,types=G.Types.mult;G.Camera.sees=()=>true;
   const reset=()=>{
    G.Combat.clearFields();G.Projectiles.clear();G.FX.clear();G.EnemyMgr.clear();
    Object.assign(G.World,{isWall:()=>false,projectileBlock:()=>false,propsInCircle:()=>[],damageProp:()=>{}});
    G.Weather.mult=weather;G.Types.mult=types;pl.dead=false;pl.hp=pl.maxHp;pl.aim=0;pl.quantityBonus=0;pl.critChance=0;pl.target=null;
    pl.moves=pl.moves.filter(m=>m.id!=='naruto-sharingan');G.NarutoSharingan?.sync(pl);
   };
   const enemy=(x,y)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
   const launch=()=>{G.DigimonSkills.cast(pl,G.Moves.instance(id));G.Combat.updateFields(.241);return G.Projectiles.all()[0]};
   let now=0;const step=dt=>{now+=dt;G.Projectiles.update(dt,pl,G.EnemyMgr.all());G.Combat.resolve(dt,pl,now)};
   try{
    reset();let shot=launch();const close=enemy(shot.x+25,shot.y);step(1/120);
    assert(close.hp<100000&&G.Projectiles.all().includes(shot)&&shot.vx>0,'Early mouth-path contact missed or consumed flame');out.firstContact='enemy 25 pixels in front is hit before .2s and flame continues';
    reset();shot=launch();assert(shot.fireballAOE&&!shot.digiBomb,'Still using impact bomb');
    G.Projectiles.update(.6,pl,[]);G.Combat.resolve(.6,pl,now+=.6);
    const es=[enemy(shot.x,shot.y),enemy(shot.x-25,shot.y+24),enemy(shot.x+25,shot.y-24),enemy(shot.x,shot.y+140)];
    const credit=pl.dmgDealt,base=49*pl.atk*.2*types('fire',['normal'])*weather('fire'),beforeX=shot.x;
    step(.2);const hp=es.map(e=>100000-e.hp);
    assert(hp.slice(0,3).some(v=>v>0)&&hp[3]===0,'Moving flame failed actual body AOE '+hp);
    assert(G.Projectiles.all().includes(shot)&&shot.x>beforeX,'Enemy hit consumed or stopped fireball');
    // A retained body covers multiple spread targets at the same tick, without hits per frame.
    shot.vx=shot.vy=0;for(let i=0;i<3;i++){es[i].x=shot.x+(i-1)*25;es[i].y=shot.y+(i===1?24:-20)}G.EnemyMgr.rebuildGrid();
    const h=es.map(e=>e.hp),d=pl.dmgDealt;step(.199);assert(es.every((e,i)=>e.hp===h[i]),'Damaged every frame');step(.001);
    assert(es.slice(0,3).every((e,i)=>h[i]-e.hp===Math.round(base))&&es[3].hp===h[3],'Three-target tick mismatch');
    assert(Math.abs(pl.dmgDealt-d-base*3)<.001,'AOE owner credit mismatch');assert(es.slice(0,3).every(e=>e.burn>0),'Burn missing');out.aoe='moving hit retained; three spread body targets per .2s; outside untouched';
    reset();shot=launch();const wall=shot.x+75;G.World.projectileBlock=(x,y,r)=>x+r>=wall?'wall':false;G.World.isWall=x=>x>=wall;
    for(let i=0;i<60;i++)step(1/120);assert(G.Projectiles.all().includes(shot)&&shot.fireballAOE.blocked&&shot.x<wall,'Wall consumed or crossed flame');
    const parked=shot.x,remaining=shot.life-shot.t,victim=enemy(shot.x-8,shot.y),behind=enemy(wall+8,shot.y),old=victim.hp;
    for(let i=0;i<24;i++)step(1/120);assert(shot.x===parked&&victim.hp<old&&behind.hp===100000,'Wall flame stopped burning or leaked through wall');
    G.World.projectileBlock=()=>false;G.World.isWall=()=>false;step(.1);assert(shot.x===parked,'Blocked flame teleported after obstacle disappeared');
    step(2);assert(!G.Projectiles.all().includes(shot)&&G.NarutoFireballAOE.active.length===0,'TTL retained a permanent flame');out.wall='parks, burns accessible side, no wall leak, no restart, expires at original TTL';
    reset();shot=launch();const prop={id:921,x:shot.x+70,y:shot.y,r:14,solid:true,destructible:true,hp:1000};let propDamage=0;
    G.World.projectileBlock=(x,y,r)=>Math.hypot(x-prop.x,y-prop.y)<=r+prop.r?prop:false;
    G.World.propsInCircle=(x,y,r)=>Math.hypot(x-prop.x,y-prop.y)<=r+prop.r?[prop]:[];
    G.World.damageProp=(p,dmg)=>{assert(p===prop,'Unexpected prop damaged');propDamage+=dmg};
    for(let i=0;i<72;i++)step(1/120);assert(shot.fireballAOE.blocked&&G.Projectiles.all().includes(shot)&&propDamage>0,'Solid prop did not retain and burn');
    assert(propDamage<=49*pl.atk*.6+.001,'Prop received per-frame damage');out.prop='solid obstacle retains flame and receives bounded periodic damage';
    reset();shot=launch();shot.vx=shot.vy=0;let e=enemy(shot.x,shot.y);pl.item='shellbell';pl.bellHeal=0;const deal=pl.dmgDealt;
    G.Combat.resolve(0,pl,now);assert(100000-e.hp===Math.round(base),'First contact did not damage immediately');
    step(.61);assert(100000-e.hp===4*Math.round(base),'Large dt overcounted cadence');assert(Math.abs(pl.dmgDealt-deal-base*4)<.001&&pl.bellHeal>0,'Damage/lifesteal credit missing');
    step(.01);assert(100000-e.hp===4*Math.round(base),'Fractional tick duplicated');step(4);assert(100000-e.hp===7*Math.round(base)&&!G.Projectiles.count,'TTL catch-up exceeds seven ticks');pl.item=null;out.cadence='first contact immediate; 3 further ticks by .61s; maximum 7 ticks in original 1.4s';
    reset();shot=launch();shot.vx=shot.vy=0;e=enemy(shot.x,shot.y);G.Combat.resolve(0,pl,now);e.x+=200;G.EnemyMgr.rebuildGrid();step(.6);
    const outsideHP=e.hp;e.x=shot.x;G.EnemyMgr.rebuildGrid();step(.01);assert(outsideHP-e.hp===Math.round(base),'Re-entry caught up damage from outside');out.reentry='one contact tick on return; no damage catch-up for time outside';
    reset();pl.quantityBonus=2;pl.addMove('naruto-sharingan');const eye=pl.moves.find(m=>m.id==='naruto-sharingan');eye.lvl=3;
    const m=G.Moves.instance(id);G.DigimonSkills.cast(pl,m);pl.quantityBonus=8;eye.lvl=1;m.dmg=999;G.Combat.updateFields(.241);
    const shots=G.Projectiles.all();assert(shots.length===4&&shots.every(p=>Math.abs(p.fireballAOE.damage-49*pl.atk)<.001),'Quantity/Sharingan snapshot duplicated or damage mutated');out.quantity='1 base + 2 quantity + 1 Sharingan = 4 full-DPS bodies, snapshot once';
    reset();shot=launch();shot.vx=shot.vy=0;e=enemy(shot.x,shot.y);G.Types.mult=()=>0;const immune=pl.dmgDealt;step(.2);assert(e.hp===100000&&pl.dmgDealt===immune,'Immune target generated damage credit');
    reset();shot=launch();shot.vx=shot.vy=0;e=enemy(shot.x,shot.y);G.Types.mult=()=>2;G.Weather.mult=()=>1.5;step(.2);assert(100000-e.hp===Math.round(49*pl.atk*.2*3),'Type/weather bypassed');out.types='type/weather multipliers and zero immunity credit respected';
    reset();shot=launch();pl.dead=true;pl.hp=0;step(.01);assert(!G.Projectiles.count&&!G.NarutoFireballAOE.active.length,'Dead owner retained flame');
    reset();launch();G.Combat.clearFields();assert(!G.Projectiles.count&&!G.NarutoFireballAOE.active.length,'Scene clear retained flame');out.cleanup='death and scene clear remove bodies';
    return out;
   }finally{reset();Object.assign(G.World,saved);G.Camera.sees=sees;G.Weather.mult=weather;G.Types.mult=types}
  }''')
  capture=r'''()=>{
   const pl=G.Game.player;G.Combat.clearFields();G.Projectiles.clear();G.FX.clear();G.EnemyMgr.clear();pl.quantityBonus=0;pl.aim=0;
   const m=G.Moves.instance('naruto-fireball');pl.cast(m);G.DigimonSkills.cast(pl,m);G.Combat.updateFields(.241);
   G.Projectiles.update(.5,pl,[]);G.Combat.resolve(.5,pl,1);G.Camera.x=pl.x+60;G.Camera.y=pl.y;
   document.getElementById('scr-pause').style.visibility='hidden';
  }'''
  page.evaluate(capture);page.wait_for_timeout(60);page.screenshot(path=str(ROOT/'.omx/fireball-persistent-desktop.png'),animations='disabled')
  mobile,phone=boot(True);phone.evaluate(capture);phone.wait_for_timeout(60);phone.screenshot(path=str(ROOT/'.omx/fireball-persistent-mobile.png'),animations='disabled');mobile.close()
  assert not errors,errors
  print(json.dumps({'ok':True,'checks':result},ensure_ascii=False))
 finally:browser.close()
