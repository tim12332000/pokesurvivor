"""Actual-browser coverage for Fuma's bounded, curved outward/return legs."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright
import json
import mimetypes

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    def route_file(route):
        file = ROOT / unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
        route.fulfill(status=200 if file.is_file() else 404, body=file.read_bytes() if file.is_file() else b'', content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
    context = browser.new_context(viewport={'width':1280,'height':820}, service_workers='block')
    context.route('https://tim12332000.github.io/pokesurvivor/**', route_file)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(URL,wait_until='domcontentloaded')
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
    page.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
    report = page.evaluate(r'''() => {
      const pl=G.Game.player,id='naruto-fuma-shuriken';
      const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
      const saved={};for(const k of ['projectileBlock','propsInCircle','isWall','collide'])saved[k]=G.World[k];
      const sees=G.Camera.sees;G.Camera.sees=()=>true;
      Object.assign(G.World,{projectileBlock:()=>false,propsInCircle:()=>[],isWall:()=>false,collide:()=>{}});
      let now=0;
      const reset=()=>{G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();pl.x=pl.y=0;pl.aim=0;pl.dead=false;pl.hp=pl.maxHp;pl.critChance=0;pl.quantityBonus=0;};
      const tick=(dt=1/240)=>{now+=dt;G.Projectiles.update(dt,pl,G.EnemyMgr.all());G.Combat.resolve(dt,pl,now);G.Combat.updateFields(dt);};
      const step=s=>{for(let t=0;t<s;t+=1/240)tick(Math.min(1/240,s-t));};
      const cast=()=>{G.DigimonSkills.cast(pl,G.Moves.instance(id));step(.21);return G.Projectiles.all()[0];};
      const enemy=(x,y,r=10)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.r=r;e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;};
      try {
        reset();let blade=cast();step(.4);assert(!blade.back&&blade.x>170,'Missing outward flight');
        step(.45);assert(blade.back&&Math.abs(blade.y)>12,'Return must curve, not reverse on same line');
        pl.x=-110;pl.y=95;step(2);assert(!G.Projectiles.count,'Did not follow moving owner and get caught');
        reset();const e=enemy(110,0,55);blade=cast();step(2.5);
        const expected=blade.dmg*G.Types.mult(blade.mtype,e.types)*G.Weather.mult(blade.mtype);
        assert(100000-e.hp===2*Math.round(expected),'Enemy must take one full hit per leg: '+(100000-e.hp));
        assert(!G.Projectiles.count,'Two-pass shot remained after catch');
        reset();const crowded=Array.from({length:8},()=>enemy(100,0));blade=cast();
        step(.17);assert(G.Projectiles.all().includes(blade),'Piercing exhausted and destroyed blade');
        assert(crowded.filter(e=>e.hp<100000).length===4,'Outbound piercing limit lost');
        step(2);assert(!G.Projectiles.count,'Spent blade cannot get stuck');
        assert(crowded.every(e=>100000-e.hp<=2*Math.round(expected)),'Enemy damaged more than once per leg');
        reset();pl.quantityBonus=2;blade=cast();const shots=[...G.Projectiles.all()];assert(shots.length===3&&shots.every(s=>s.fumaPierce===5),'Quantity must add independent shots and piercing');
        assert(new Set(shots.map(s=>s.hits)).size===3,'Shots share hit sets');
        assert(shots.every(s=>s.dmg===blade.dmg),'Extra shots lost full damage');step(2.5);assert(!G.Projectiles.count,'Quantity return failed');
        reset();blade=cast();pl.dead=true;tick();assert(!G.Projectiles.count,'Dead owner retained a Fuma blade');pl.dead=false;
        reset();const ordinary=G.Projectiles.spawn({x:200,y:0,vx:200,vy:0,boom:.1,bsp:220,owner:pl,life:3,hits:new Set(),pierce:0});
        step(.15);assert(ordinary.back&&!ordinary.fumaReturn&&ordinary.pierce===0,'Ordinary boomerang modified');
        reset();blade=cast();G.World.projectileBlock=()=> 'wall';tick();assert(!G.Projectiles.count,'Ordinary wall blocking changed');
        return {outwardReturn:'curved; moving owner caught',damage:'once per enemy per leg; full damage',limits:'four hits per leg; spent blades return',quantity:'three independent full-damage blades with +2 piercing',lifecycle:'death and catch remove blades',regression:'normal boomerang and wall behavior preserved'};
      } finally {Object.assign(G.World,saved);G.Camera.sees=sees;G.Combat.clearFields();G.Projectiles.clear();}
    }''')
    # Capture the actual turning projectile in desktop and true mobile contexts.
    capture = r'''() => {
      const pl=G.Game.player;G.EnemyMgr.clear();G.Combat.clearFields();G.Projectiles.clear();
      const block=G.World.projectileBlock,sees=G.Camera.sees;G.World.projectileBlock=()=>false;G.Camera.sees=()=>true;
      pl.aim=0;G.DigimonSkills.cast(pl,G.Moves.instance('naruto-fuma-shuriken'));G.Combat.updateFields(.21);
      for(let t=0;t<1.15;t+=1/120)G.Projectiles.update(1/120,pl,[]);
      G.World.projectileBlock=block;G.Camera.sees=sees;G.Camera.x=pl.x;G.Camera.y=pl.y;
      document.getElementById('scr-pause').style.visibility='hidden';
    }'''
    page.evaluate(capture)
    page.wait_for_timeout(60)
    page.screenshot(path=str(ROOT/'.omx/fuma-return-desktop.png'))
    mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,service_workers='block')
    mobile.route('https://tim12332000.github.io/pokesurvivor/**',route_file)
    phone=mobile.new_page();phone.on('pageerror',lambda e:errors.append(str(e)));phone.goto(URL,wait_until='domcontentloaded')
    phone.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if phone.locator('#tap-start').is_visible():phone.locator('#tap-start').click()
    phone.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()');phone.evaluate(capture)
    phone.wait_for_timeout(60)
    phone.screenshot(path=str(ROOT/'.omx/fuma-return-mobile.png'))
    page.evaluate('G.Game.quit();G.Flow.goMenu();G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
    assert page.evaluate('!G.Projectiles.count&&!G.DigimonSkills.activeEffects.length'),'New run retains old effect'
    assert not errors,errors
    print(json.dumps({'ok':True,'checks':report},ensure_ascii=False))
    browser.close()
