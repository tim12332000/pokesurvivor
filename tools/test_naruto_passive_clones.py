"""Browser checks for shadow clone actors, training choices and lifecycle."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
import json
import mimetypes
import os

ROOT=Path(__file__).resolve().parent.parent
URL='http://127.0.0.1:8004/pokesurvivor/.omx/digimon.html?lang=zh-TW&layout=wide&v=naruto-shadow-clones'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(locale='zh-TW',viewport={'width':1280,'height':820},service_workers='block')
    if os.environ.get('PAGES_LIVE')!='1':
        def proxy(route):
            file=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            if file.is_file():route.fulfill(status=200,body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            else:route.fulfill(status=404,body='Not found')
        context.route('http://127.0.0.1:8004/pokesurvivor/**',proxy)
    page=context.new_page();errors=[];missing=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:missing.append(r.url) if r.status>=400 else None)
    page.goto(URL)
    try: page.wait_for_function("window.PS_REDRAWN_READY && G.SelfClones && document.getElementById('boot').classList.contains('hidden')")
    except Exception:
        print({'errors':errors,'missing':missing,'state':page.evaluate('({ready:!!window.PS_REDRAWN_READY,g:!!window.G,clone:!!window.G?.SelfClones})')},flush=True)
        raise
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    results=page.evaluate("""async () => {
      const assert=(ok,msg)=>{if(!ok)throw Error(msg)},N=G.NarutoClones,id='naruto-shadow-clones';
      G.Naruto.choose(30001);await G.Flow.play();if(G.Game.state==='playing')G.Game.togglePause();
      const p=G.Game.player;
      assert(p.moves.find(m=>m.id===id)?.passive,'starting skill is not passive');
      assert(!p.slots.some(s=>s.some(m=>m.id===id)),'starting passive occupies slot');
      Object.assign(G.World,{isFree:()=>true,collide:()=>{},projectileBlock:()=>false,isWall:()=>false,isLiquid:()=>false});
      const reset=rank=>{G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();p.x=p.y=0;p.hp=p.maxHp;p.dead=false;p.cdMul=1;p.quantityBonus=p.quantityPicks=0;p.moves=[];p.slots=[];p.bind={};p.active=0;p.addMove(id);const m=p.moves[0];while(m.lvl<rank)G.Moves.levelUp(m);return m;};
      const step=seconds=>{for(let t=0;t<seconds-1e-9;){const dt=Math.min(.01,seconds-t);G.Combat.tick(dt,p,0);G.Combat.updateFields(dt);t+=dt;}};
      const counts=[];
      for(let rank=1;rank<=5;rank++){
        const m=reset(rank);assert(m.passive&&!p.slots.length,'slotless rank '+rank);
        assert(m.cd===12&&m.cloneDuration===10,'timing rank '+rank);
        step(.42);counts.push(N.actors.length);assert(N.actors.length===N.config.counts[rank-1],'quantity rank '+rank);
      }
      assert(JSON.stringify(counts)==='[8,10,12,14,16]','counts');
      let m=reset(1);p.addMove('naruto-naruto');p.moves[1].t=999;
      step(.42);assert(N.actors.length===8,'passive while rasengan selected');
      const first=N.actors.map(a=>a.id);step(9.5);assert(N.actors.length===8,'expired before ten seconds');
      step(.6);assert(!N.actors.length,'did not expire');step(1.3);assert(!N.actors.length,'recast before twelve seconds');
      step(.7);assert(N.actors.length===8&&N.actors.every(a=>!first.includes(a.id)),'automatic repeat');
      m=reset(1);step(.42);const remaining=m.t;G.Moves.levelUp(m);assert(N.actors.length===8&&m.t===remaining,'upgrade bypassed cooldown');
      step(12.1);assert(N.actors.length===10,'upgraded next wave');
      m=reset(1);p.cdMul=.5;step(.42);assert(N.actors.length===8&&m.t<6,'cooldown cards ignored');
      p.dead=true;step(.5);assert(!N.actors.length,'death cleanup');p.dead=false;
      m=reset(1);G.Combat.tick(.01,p,0);p.dead=true;step(.5);assert(!N.actors.length,'pending summon after death');
      m=reset(1);p.quantityBonus=p.quantityPicks=1;step(.42);assert(N.actors.length===10,'quantity card');
      m=reset(1);step(.7);
      const victim=N.actors[0],other=N.actors[1],initialHP=p.hp;
      const projectileHit=()=>{
        const bullet={friendly:false,x:victim.x,y:victim.y,px:victim.x,py:victim.y,r:2};
        G.Projectiles.all().push(bullet);G.Combat.resolve(.01,p,0);
        assert(!G.Projectiles.all().includes(bullet),'intercepted bullet not consumed');
      };
      for(let hit=1;hit<=4;hit++){
        projectileHit();assert(!victim.dead&&victim.hitsRemaining===5-hit,'projectile hit '+hit);
        assert(other.hitsRemaining===5,'hit counter shared between clones');
      }
      projectileHit();assert(victim.dead&&victim.hitsRemaining===0,'fifth projectile did not dismiss');
      assert(p.hp===initialHP,'intercepted projectile hurt player');
      m=reset(1);step(.7);
      const contact=N.actors[0],enemy=new G.Enemy({dex:19,hp:100000,spd:0,dmg:5,xp:0,behavior:'chase'},contact.x,contact.y,{hp:1,spd:1,dmg:1});
      G.EnemyMgr.add(enemy);G.EnemyMgr.rebuildGrid();
      for(let hit=1;hit<=5;hit++){
        enemy.x=contact.x;enemy.y=contact.y;enemy.touchCd=0;G.EnemyMgr.rebuildGrid();
        G.Combat.updateFields(.01);
        assert(contact.hitsRemaining===5-hit,'contact hit '+hit);
        assert(contact.dead===(hit===5),'contact dismissal '+hit);
        if(hit<5){G.Combat.updateFields(.01);assert(contact.hitsRemaining===5-hit,'contact counted again during enemy cooldown');}
      }
      m=reset(1);step(.7);const mixed=N.actors[0];
      const mixEnemy=new G.Enemy({dex:19,hp:100000,spd:0,dmg:5,xp:0,behavior:'chase'},mixed.x,mixed.y,{hp:1,spd:1,dmg:1});
      G.EnemyMgr.add(mixEnemy);G.EnemyMgr.rebuildGrid();G.Combat.updateFields(.01);
      for(let hit=0;hit<4;hit++){
        G.Projectiles.all().push({friendly:false,x:mixed.x,y:mixed.y,px:mixed.x,py:mixed.y,r:2});G.Combat.resolve(.01,p,0);
      }
      assert(mixed.dead&&mixed.hitsRemaining===0,'mixed contact/projectile counter');
      reset(1);step(.42);assert(N.actors.every(a=>a.hitsRemaining===5),'new wave did not reset hit counters');
      // Exercise actual clone hits, including the projectile's delayed explosion.
      const damage=[];
      p.critChance=0;
      const oldType=G.Types.mult,oldWeather=G.Weather.mult;
      G.Types.mult=G.Weather.mult=()=>1;
      try {
        for(let rank=1;rank<=5;rank++)for(const technique of [null,'naruto-naruto','naruto-rasenshuriken']){
          reset(rank);
          if(technique){p.addMove(technique);p.active=p.slots.findIndex(g=>g.some(m=>m.id===technique));}
          const skill=technique?p.moves.find(m=>m.id===technique):p.moves[0];
          const originalDamage=skill.dmg;
          N.cast(p,p.moves[0]);const a=N.actors[0];
          for(const other of N.actors)if(other!==a)other.dead=true;
          a.x=a.y=0;a.cd=0;for(const id of a.cooldowns.keys())a.cooldowns.set(id,0);
          const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},20,0,{hp:1,spd:1,dmg:1});
          e.touchCd=999;const hits=[];e.hurt=(amount)=>hits.push(amount);
          G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();G.Combat.updateFields(.01);
          if(technique==='naruto-rasenshuriken'){
            const shots=G.Projectiles.all().filter(b=>b.narutoClone);
            assert(shots.length===1,'clone projectile missing');
            const shot=shots[0];
            assert(Math.abs(shot.dmg-originalDamage*p.atk*.3*.2)<1e-6,'projectile direct damage');
            shot.x=e.x;shot.y=e.y;shot.hits.add(e);G.Combat.resolve(.01,p,0);
            assert(hits.some(v=>Math.abs(v-originalDamage*p.atk*.3*.8)<1e-6),'explosion not scaled');
          }else{
            assert(hits.length===1&&Math.abs(hits[0]-originalDamage*p.atk*.3)<1e-6,'30% hit '+rank+' '+technique);
          }
          assert(skill.dmg===originalDamage,'clone changed owner damage');
          damage.push({rank,technique:technique||'punch',multiplier:.3});
        }
      } finally {G.Types.mult=oldType;G.Weather.mult=oldWeather;}
      G.Combat.clearFields();assert(!N.actors.length,'clear fields');
      return {counts,damage,duration:10,cooldown:12,passive:true,checks:['slotless','automatic repeat','expiry','upgrade cooldown','cooldown card','quantity card','death','pending cancellation','five projectile hits','five contact hits','contact cooldown','independent hit counters','mixed hits','new wave counters','clear']};
    }""")
    assert not errors,errors
    print(json.dumps(results));browser.close()
