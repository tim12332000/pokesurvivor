"""Verify Sasuke's distinct fireball hand seal, mouth release, and cleanup."""
from pathlib import Path
from urllib.parse import unquote,urlsplit
from playwright.sync_api import sync_playwright
import json,mimetypes,os
ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=fireball-cast'
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
  pg.wait_for_function('!!G.NarutoFireball')
  return c,pg
 try:
  context,page=boot()
  result=page.evaluate(r'''() => {
   const api=G.NarutoFireball,pl=G.Game.player,id='naruto-fireball',assert=(ok,m)=>{if(!ok)throw Error(m)},out={};
   const saved={isWall:G.World.isWall,projectileBlock:G.World.projectileBlock},sees=G.Camera.sees;
   G.World.isWall=()=>false;G.World.projectileBlock=()=>false;G.Camera.sees=()=>true;
   const reset=()=>{G.Combat.clearFields();G.Projectiles.clear();G.FX.clear();G.EnemyMgr.clear();pl.dead=false;pl.hp=pl.maxHp;pl.aim=0;pl.quantityBonus=0;pl.target=null};
   const tick=dt=>G.Combat.updateFields(dt);
   try{
    reset();const move=G.Moves.instance(id),original=JSON.stringify(move);pl.cast(move);
    assert(G.DigimonSkills.cast(pl,move),'Cast refused');assert(api.active?.phase==='seal','Missing visible seal phase');assert(!G.Projectiles.count,'Immediate shot before seal');
    const nearby=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},pl.x+50,pl.y,{hp:1,spd:1,dmg:1});G.EnemyMgr.add(nearby);
    assert(!G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke'))&&!G.NarutoChidori.active,'Chidori interrupted the fireball pose');G.EnemyMgr.clear();
    tick(.239);assert(!G.Projectiles.count,'Shot before .24 second seal');tick(.002);assert(G.Projectiles.count===1,'Missing single release');
    const shot=G.Projectiles.all()[0],origin=api.origin(pl,0);assert(Math.hypot(shot.x-origin.x,shot.y-origin.y)<4,'Shot did not leave mouth');
    assert(shot.owner===pl&&Math.abs(shot.dmg-move.dmg*pl.atk*.2)<.001&&shot.digiBomb.r===95,'Damage or ownership changed');
    tick(2);assert(G.Projectiles.count===1&&!api.active,'Large dt repeats emission or pose lingers');
    assert(JSON.stringify(move)===original,'Learned skill mutated');out.timing='seal .239: 0; .241: 1; after large dt: still 1';
    reset();G.DigimonSkills.cast(pl,G.Moves.instance(id));tick(1);assert(G.Projectiles.count===1&&!api.active,'Single large frame skipped or duplicated release');out.largeFrame='one release even when all phases elapse in one frame';
    reset();pl.quantityBonus=2;const snap=G.Moves.instance(id);G.DigimonSkills.cast(pl,snap);pl.quantityBonus=7;snap.dmg=999;pl.aim=Math.PI;tick(.25);
    assert(G.Projectiles.count===3&&G.Projectiles.all().every(s=>s.vx>0&&Math.abs(s.dmg-49*pl.atk*.2)<.001),'Pending cast did not snapshot quantity, damage, and aim');out.snapshot='3 full-damage shots; quantity, damage, and facing locked during seal';
    reset();const right=api.origin(pl,0),left=api.origin(pl,Math.PI);
    assert(right.x>pl.x&&left.x<pl.x&&Math.abs(right.x+left.x-2*pl.x)<.01&&Math.abs(right.y-left.y)<.01,'Mouth origin not mirrored');
    pl.aim=Math.PI;G.DigimonSkills.cast(pl,G.Moves.instance(id));tick(.25);assert(G.Projectiles.all().every(s=>s.x<pl.x&&s.vx<0),'Left release faces right');out.direction={right,left};
    reset();const wallStart=pl.x+30,wallEnd=pl.x+40;
    const protectedEnemy=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},pl.x+140,pl.y-22,{hp:1,spd:1,dmg:1});
    protectedEnemy.types=['normal'];G.EnemyMgr.add(protectedEnemy);G.EnemyMgr.rebuildGrid();pl.target=protectedEnemy;
    G.World.isWall=x=>x>=wallStart&&x<=wallEnd;G.World.projectileBlock=G.World.isWall;
    G.DigimonSkills.cast(pl,G.Moves.instance(id));tick(.25);
    assert(!G.Projectiles.all().some(s=>s.x>wallEnd),'Mouth offset skipped a nearby thin wall');
    for(let i=0;i<96;i++){G.Projectiles.update(1/240,pl,G.EnemyMgr.all());G.Combat.resolve(1/240,pl,1+i/240)}assert(protectedEnemy.hp===100000,'Thin-wall protected enemy was hit');
    G.World.isWall=()=>false;G.World.projectileBlock=()=>false;out.nearWall='30–40 pixel wall blocks the forward mouth offset';
    reset();G.DigimonSkills.cast(pl,G.Moves.instance(id));tick(.1);pl.dead=true;pl.hp=0;tick(.3);assert(!G.Projectiles.count&&!api.active,'Death released pending fireball');
    reset();G.DigimonSkills.cast(pl,G.Moves.instance(id));tick(.1);G.Combat.clearFields();tick(.3);assert(!G.Projectiles.count&&!api.active,'Scene clear released pending fireball');
    reset();G.DigimonSkills.cast(pl,G.Moves.instance(id));tick(.1);api.clear(pl);tick(.3);assert(!G.Projectiles.count&&!api.active,'Owner clear did not cancel');out.cleanup='death, scene clear, owner clear cancel pending release';
    return out;
   }finally{Object.assign(G.World,saved);G.Camera.sees=sees;reset()}
  }''')
  page.evaluate("G.Game.quit();G.Flow.goMenu();G.Naruto.choose(30008);G.Flow.play();G.Game.togglePause();G.Game.player.addMove('naruto-fireball');G.DigimonSkills.cast(G.Game.player,G.Moves.instance('naruto-fireball'))")
  assert page.evaluate('G.Projectiles.count===1&&!G.NarutoFireball.active'),'Itachi acquired Sasuke delay or pose'
  result['itachi']='unchanged immediate fireball; no Sasuke casting pose'
  page.evaluate("G.Game.quit();G.Flow.goMenu();G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause();G.Game.player.addMove('naruto-fireball')")
  capture=r'''({phase,left=false})=>{
   const pl=G.Game.player;G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();
   pl.aim=left?Math.PI:0;pl.quantityBonus=0;pl.anim.update(10);pl.anim.loop('Idle');
   const m=G.Moves.instance('naruto-fireball');pl.cast(m);G.DigimonSkills.cast(pl,m);
   G.Combat.updateFields(phase==='seal'?.12:.27);pl.anim.update(.12);
   if(phase!=='seal'){G.Projectiles.update(.04,pl,[])}
   G.Camera.x=pl.x;G.Camera.y=pl.y;document.getElementById('scr-pause').style.visibility='hidden';
  }'''
  for name,phase,left in [('seal','seal',False),('breath','breath',False),('left','breath',True)]:
   page.evaluate(capture,{'phase':phase,'left':left});page.wait_for_timeout(60);page.screenshot(path=str(ROOT/f'.omx/sasuke-fireball-cast-{name}.png'),animations='disabled')
  mobile,phone=boot(True);phone.evaluate(capture,{'phase':'breath'});phone.wait_for_timeout(60);phone.screenshot(path=str(ROOT/'.omx/sasuke-fireball-cast-portrait.png'),animations='disabled');mobile.close()
  assert not errors,errors
  print(json.dumps({'ok':True,'checks':result},ensure_ascii=False))
 finally:browser.close()
