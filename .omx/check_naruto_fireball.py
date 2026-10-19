from pathlib import Path
from urllib.parse import unquote,urlsplit
from playwright.sync_api import sync_playwright
import json,mimetypes,os
ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=great-fireball'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
 def proxy(route):
  f=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
  route.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'Not found',content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
 def boot(mobile=False):
  c=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':820},is_mobile=mobile,has_touch=mobile,locale='zh-TW',service_workers='block')
  if os.environ.get('PAGES_LIVE')!='1':c.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
  c.route('**api.ipify.org**',lambda route:route.fulfill(json={'ip':'198.51.100.10'}))
  pg=c.new_page();pg.on('pageerror',lambda error:errors.append(str(error)));pg.goto(URL)
  pg.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
  if pg.locator('#tap-start').is_visible():pg.locator('#tap-start').click()
  pg.evaluate("G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause();G.Game.player.addMove('naruto-fireball')")
  return c,pg
 errors=[]
 try:
  context,page=boot()
  capture=r'''() => {
   const pl=G.Game.player;G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();
   pl.aim=0;pl.anim.update(10);pl.anim.loop('Idle');const m=pl.moves.find(m=>m.id==='naruto-fireball');pl.cast(m);pl.anim.update(.12);
   G.DigimonSkills.cast(pl,m);G.Combat.updateFields(.5);const shot=G.Projectiles.all()[0];shot.x=pl.x+110;shot.y=pl.y;shot.t=.12;
   G.Camera.x=pl.x;G.Camera.y=pl.y;document.getElementById('scr-pause').style.visibility='hidden';
  }'''
  page.evaluate(capture);page.wait_for_timeout(60)
  suffix='before' if os.environ.get('FIREBALL_BEFORE') else 'desktop'
  page.screenshot(path=str(ROOT/f'.omx/naruto-fireball-{suffix}.png'),animations='disabled')
  if os.environ.get('FIREBALL_BEFORE'):print('baseline captured')
  else:
   report=page.evaluate(r'''() => {
    const assert=(v,m)=>{if(!v)throw Error(m)},pl=G.Game.player,id='naruto-fireball',def=G.Moves.BY_ID[id],saved={};
    for(const key of ['isWall','isFree','collide','propsInCircle','projectileBlock','isLiquid','damageProp'])saved[key]=G.World[key];
    const sees=G.Camera.sees;G.Camera.sees=()=>true;
    Object.assign(G.World,{isWall:()=>false,isFree:()=>true,collide:()=>{},propsInCircle:()=>[],projectileBlock:()=>false,isLiquid:()=>false});
    const setup=(points=[])=>{
     G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();pl.x=pl.y=0;pl.aim=0;pl.dead=false;pl.hp=pl.maxHp;pl.quantityBonus=0;pl.critChance=0;
     const es=points.map(([x,y])=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);return e});G.EnemyMgr.rebuildGrid();pl.target=es[0]||null;return es;
    };
    let time=0;const step=seconds=>{for(let t=0;t<seconds;t+=1/240){const dt=Math.min(1/240,seconds-t);time+=dt;G.Projectiles.update(dt,pl,G.EnemyMgr.all());G.Combat.resolve(dt,pl,time);G.Combat.updateFields(dt)}};
    const out={};try{
     assert(def.dmg===49&&def.cd===2.3&&def.burn===.12&&def.blastRadius===95,'Balance changed');
     assert(def.size===52&&def.digiVis.proj==='naruto-great-fireball','Large collision/shape absent');
     for(const mon of G.Naruto.records.values()){pl.level=9;assert(G.Moves.poolFor(mon).includes(id)===[30002,30008].includes(mon.dex),'Pool escaped '+mon.dex)}
     setup();pl.quantityBonus=2;const learned=G.Moves.instance(id),before=JSON.stringify(learned);G.DigimonSkills.cast(pl,learned);
     assert(G.Projectiles.count===3&&G.Projectiles.all().every(s=>s.r===52&&s.owner===pl&&Math.abs(s.dmg-49*pl.atk*.2)<.001),'Quantity, full damage, or owner failed');
     assert(JSON.stringify(learned)===before,'Definition mutated');out.quantity='1 + 2 passive stacks = 3 full damage fireballs';
     const es=setup([[150,0],[90,82],[90,-82],[90,170]]),m=G.Moves.instance(id),expected=m.dmg*pl.atk*G.Types.mult(m.type,['normal'])*G.Weather.mult(m.type),credit=pl.dmgDealt;
     G.DigimonSkills.cast(pl,m);step(.65);const damage=es.map(e=>100000-e.hp);
     assert(damage[0]===Math.round(expected*.2)+Math.round(expected*.8),'Direct hit doubled: '+damage);
     assert(damage[1]===Math.round(expected*.8)&&damage[2]===Math.round(expected*.8)&&damage[3]===0,'AOE mismatch '+damage);
     assert(Math.abs(pl.dmgDealt-credit-expected*2.6)<.001,'Damage credit mismatch');assert(es.slice(0,3).every(e=>e.burn>0||e.burnT>0||e.burnPct>0),'Burn absent');out.damage=damage;
     const blocked=setup([[300,0]]);G.World.projectileBlock=x=>x>=65;G.World.isWall=G.World.projectileBlock;G.DigimonSkills.cast(pl,G.Moves.instance(id));step(.8);assert(blocked[0].hp===100000&&!G.Projectiles.count,'Crossed wall');
     G.World.projectileBlock=()=>false;G.World.isWall=()=>false;setup();let propDamage=0;const prop={id:98765,x:130,y:0,r:12,solid:true};
     G.World.propsInCircle=(x,y,r)=>Math.hypot(x-prop.x,y-prop.y)<=r+prop.r?[prop]:[];G.World.damageProp=(p,d)=>{propDamage+=d};
     G.DigimonSkills.cast(pl,G.Moves.instance(id));step(.8);assert(Math.abs(propDamage-49*pl.atk)<.001,'Prop damage duplicate or missing '+propDamage);out.collision='walls block; props receive one 20% + 80% budget';G.World.propsInCircle=()=>[];
     setup();G.DigimonSkills.cast(pl,G.Moves.instance(id));pl.dead=true;pl.hp=0;step(.01);assert(!G.Projectiles.count,'Dead owner retained shot');pl.dead=false;pl.hp=pl.maxHp;
     setup();G.DigimonSkills.cast(pl,G.Moves.instance(id));G.Combat.clearFields();G.Projectiles.clear();assert(!G.Projectiles.count&&G.DigimonSkills.activeEffects.length===0,'Clear retained effects');
     assert(G.Moves.instance('naruto-rasenshuriken').digiVis.proj==='naruto-wind-shuriken'&&G.VFX.SHAPES.fire.w===15,'Unrelated VFX changed');out.lifecycle='dead owner and scene cleanup pass';return out;
    }finally{Object.assign(G.World,saved);G.Camera.sees=sees;G.Combat.clearFields();G.Projectiles.clear()}
   }''')
   mobile,phone=boot(True);phone.evaluate(capture);phone.wait_for_timeout(60);phone.screenshot(path=str(ROOT/'.omx/naruto-fireball-portrait.png'),animations='disabled');mobile.close()
   assert not errors,errors
   print(json.dumps({'ok':True,'checks':report},ensure_ascii=False))
 finally:browser.close()
