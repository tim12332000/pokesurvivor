"""Real-browser orbit contacts, progression, owner credit and portrait slot geometry."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright
import json, mimetypes

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=kusanagi'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
 errors=[]
 def proxy(route):
  f=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
  route.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'',content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
 try:
  for mobile in [False,True]:
   c=browser.new_context(viewport={'width':360,'height':640} if mobile else {'width':1280,'height':820},is_mobile=mobile,has_touch=mobile,locale='zh-TW',service_workers='block')
   c.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
   c.route('**api.ipify.org**',lambda r:r.fulfill(json={'ip':'198.51.100.10'}))
   pg=c.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(URL)
   pg.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
   if pg.locator('#tap-start').is_visible():pg.locator('#tap-start').click()
   pg.evaluate("G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()")
   result=pg.evaluate(r'''() => {
    const p=G.Game.player,id='naruto-kusanagi',assert=(v,m)=>{if(!v)throw Error(m)},out={};
    p.level=12;p.critChance=0;G.Combat.clearFields();G.EnemyMgr.clear();
    for(const key of ['naruto-fireball','naruto-sharingan','naruto-fuma-shuriken'])assert(p.addMove(key),'existing signature missing');
    const index=p.slots.findIndex(s=>s.some(m=>m.id==='naruto-fireball'));p.setActive(index);
    let card=G.LevelUp.offer(p,3).find(c=>c.key==='new:'+id);assert(p.hasMove(id)||card&&card.apply(p),'fifth skill not offered/learnable');
    assert(p.slots.length===5&&p.active===index,'lost signature or active offensive skill');out.fifthSlot=true;assert(G.Moves.BY_ID[id].learnLevel===1,'level1 unlock missing');
    p.moves=p.moves.filter(m=>m.id!=='naruto-sharingan');G.NarutoSharingan.sync(p);
    const m=p.moves.find(m=>m.id===id),radius=m.radius;
    const enemy=(x,y)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);return e};
    const es=[enemy(p.x+radius,p.y-9),enemy(p.x+radius,p.y),enemy(p.x+radius,p.y+9),enemy(p.x+radius+65,p.y)];G.EnemyMgr.rebuildGrid();
    p.percentHealthDamage=.01;p.lifestealRate=.01;p.hp=p.maxHp/2;
    const damage=m.dmg*p.atk*G.Types.mult('steel',['normal'])*G.Weather.mult('steel'),before=p.dmgDealt,hp=p.hp;
    G.Combat.updateFields(.001);assert(!G.NarutoKusanagi.states.size,'learning auto-activated sword');
    const swordSlot=p.slots.findIndex(s=>s.some(m=>m.id===id));p.setActive(swordSlot);m.t=0;G.Combat.tick(.001,p,0);G.Combat.updateFields(.001);
    assert(es.slice(0,3).every(e=>100000-e.hp===Math.round(damage+1000))&&es[3].hp===100000,'three real AOE contacts/outside failed');
    assert(Math.abs(p.dmgDealt-before-(damage+1000)*3)<.001,'owner percent/base credited twice');
    assert(Math.abs(p.hp-hp-(damage+1000)*.03)<.001,'lifesteal ownership mismatch');
    const unchanged=es.map(e=>e.hp);G.Combat.updateFields(.01);assert(es.every((e,i)=>e.hp===unchanged[i]),'frame-rate damage runaway');
    out.aoe='3 contacts, outside safe, combined maxHP and lifesteal counted once, .35s shared target guard';
    p.percentHealthDamage=0;p.lifestealRate=0;
    out.levels=[];for(let lvl=1;lvl<=5;lvl++){
     if(lvl>1){card=G.LevelUp.offer(p,40).find(c=>c.key==='up:'+id);assert(card&&card.apply(p)!==false,'upgrade card absent '+lvl)}
     G.Combat.updateFields(.001);out.levels.push({lvl:m.lvl,count:G.NarutoKusanagi.states.get(p).blades.length,dmg:m.dmg,radius:m.radius});
    }
    assert(out.levels.map(v=>v.count).join(',')==='1,2,2,3,3','five-stage count ladder wrong');
    p.quantityBonus=0;const qty=G.LevelUp.STATS.find(s=>s.id==='quantity');qty.apply(p);qty.apply(p);G.Combat.updateFields(.001);assert(G.NarutoKusanagi.states.get(p).blades.length===5,'quantity card bonus missing');const eye=G.Moves.instance('naruto-sharingan',3);p.moves.push(eye);G.Combat.updateFields(.001);assert(G.NarutoKusanagi.states.get(p).blades.length===6,'Sharingan projectile +1 missing');p.moves=p.moves.filter(v=>v!==eye);G.NarutoSharingan.sync(p);
    p.setActive(0);assert(!G.NarutoKusanagi.states.has(p),'switch did not immediately remove orbit');
    const switchedHp=es.map(e=>e.hp);G.Combat.updateFields(.4);assert(es.every((e,i)=>e.hp===switchedHp[i]),'sword still damages after switch');
    assert(!G.NarutoKusanagi.activate(p),'inactive sword could be cast');
    p.setActive(swordSlot);assert(!G.NarutoKusanagi.states.has(p),'switching back bypassed cast');m.t=0;G.Combat.tick(.001,p,1);G.Combat.updateFields(.001);assert(G.NarutoKusanagi.states.has(p),'reselected sword failed to cast');
    out.switching='immediate removal, no residual damage, recast on return';
    G.Combat.clearFields(p);assert(!G.NarutoKusanagi.states.size,'owner cleanup failed');G.NarutoKusanagi.activate(p);G.Combat.updateFields(.001);
    p.dead=true;G.Combat.updateFields(.001);assert(!G.NarutoKusanagi.states.size,'death cleanup failed');p.dead=false;G.Combat.updateFields(.001);assert(!G.NarutoKusanagi.states.size,'revive auto-activated');G.NarutoKusanagi.activate(p);
    G.Combat.updateFields(.001);const moveIndex=p.moves.indexOf(m);p.moves.splice(moveIndex,1);G.Combat.updateFields(.001);assert(!G.NarutoKusanagi.states.size,'unlearn cleanup failed');p.moves.push(m);G.NarutoKusanagi.activate(p);
    G.Combat.updateFields(.001);const world=G.World;G.World={...world};G.Combat.updateFields(0);assert(!G.NarutoKusanagi.states.size,'world cleanup failed');G.World=world;G.NarutoKusanagi.activate(p);
    G.Combat.updateFields(.001);p.quantityBonus=0;G.Combat.updateFields(.001);out.cleanup='owner clear/death/unlearn/world';
    const layout=G.Touch.controlLayout(innerWidth,innerHeight,5,{defaults:true});
    assert(layout.slots.length===5&&layout.slots.every(s=>s.x>=0&&s.y>=0&&s.x+s.w<=innerWidth&&s.y+s.h<=innerHeight),'five touch slots clipped');
    out.slots=layout.slots.length;return out;
   }''')
   pg.evaluate("G.Game.togglePause()")
   pg.wait_for_timeout(100)
   pg.screenshot(path=str(ROOT/('.omx/kusanagi-mobile.png' if mobile else '.omx/kusanagi-desktop.png')))
   print(json.dumps({'mobile':mobile,'checks':result},ensure_ascii=False));c.close()
  assert not errors,errors
 finally:browser.close()
