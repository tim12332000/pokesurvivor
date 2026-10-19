"""Verify Chidori chaining against actual browser Player/Enemy combat objects."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
import mimetypes, json
ROOT=Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    c=b.new_context(viewport={'width':1280,'height':820},locale='zh-TW',service_workers='block')
    def proxy(route):
        f=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
        route.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'',content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
    c.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW')
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
    result=page.evaluate(r'''() => {
      const pl=G.Game.player,A=G.NarutoChidori,assert=(v,m)=>{if(!v)throw Error(m)},report={};
      const orig={isFree:G.World.isFree,isLiquid:G.World.isLiquid,collide:G.World.collide};
      G.World.isFree=()=>true;G.World.isLiquid=()=>false;G.World.collide=()=>{};
      function setup(n){G.Combat.clearFields();G.EnemyMgr.clear();G.FX.clear();pl.x=pl.y=0;pl.hp=pl.maxHp;pl.dead=false;pl.invuln=0;pl.critChance=0;pl.quantityBonus=0;pl.item=null;
        return Array.from({length:n},(_,i)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},100+i*100,0,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);return e;});}
      function cast(){const m=G.Moves.instance('naruto-sasuke');assert(G.DigimonSkills.cast(pl,m),'cast rejected');return m;}
      function step(t){for(let i=0;i<Math.ceil(t*240);i++)G.Combat.updateFields(1/240);}
      for(let n=1;n<=7;n++){const es=setup(n);const m=cast();const before=pl.dmgDealt;step(2);const hit=es.filter(e=>e.hp<e.maxHp).length;
        assert(hit===Math.min(n,5),'target count '+n+': '+hit);assert(!A.active,'chain remained');
        const expected=Math.min(n,5)*m.dmg*pl.atk*G.Types.mult(m.type,['normal'])*G.Weather.mult(m.type);
        assert(Math.abs(pl.dmgDealt-before-expected)<.01,'owner damage credit mismatch');
      }report.chain='1..7 targets: distinct hits capped at 5; owner/type damage accounting';
      const limits=[];
      for(let lv=1;lv<=5;lv++){
        const es=setup(27),m=G.Moves.instance('naruto-sasuke',lv);pl.quantityBonus=20;
        assert(m.lvl===lv&&A.limitOf(m)===lv*5,'wrong level field or limit');
        assert(G.DigimonSkills.cast(pl,m),'level cast rejected');step(6);
        const hits=es.filter(e=>e.hp<e.maxHp).length;
        assert(hits===lv*5&&!A.active,'wrong count at level '+lv+': '+hits);limits.push(hits);
      }
      const snapshotEnemies=setup(27),snapshotMove=G.Moves.instance('naruto-sasuke');
      assert(G.DigimonSkills.cast(pl,snapshotMove),'snapshot cast rejected');
      while(snapshotMove.lvl<5)G.Moves.levelUp(snapshotMove);
      step(6);assert(snapshotEnemies.filter(e=>e.hp<e.maxHp).length===5,'mid-cast upgrade changed chain limit');
      assert(G.DigimonSkills.cast(pl,snapshotMove),'upgraded next cast rejected');
      assert(A.active.limit===25,'next cast did not use upgraded limit');G.Combat.clearFields();
      report.levels={limits,quantity:'20 bonus cannot exceed per-level limit',snapshot:'upgrade during cast applies next cast only'};
      setup(0);assert(!G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke')),'zero targets cast');
      const distant=setup(5);distant.forEach((e,i)=>e.x=100+i*350);cast();step(3);
      assert(distant.every(e=>e.hp<e.maxHp)&&!A.active,'350-spaced targets broke follow-up chain');
      const outside=setup(2);outside[1].x=700;cast();step(1);
      assert(outside[0].hp<outside[0].maxHp&&outside[1].hp===outside[1].maxHp&&!A.active,'follow-up exceeded 510 range');
      const firstOutside=setup(1);firstOutside[0].x=171;
      assert(!G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke'))&&!A.active,'first acquisition exceeded 170');
      const upgraded=setup(2);upgraded[1].x=600;
      assert(G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke',4)),'upgraded cast rejected');step(2);
      assert(upgraded.every(e=>e.hp<e.maxHp),'upgraded follow-up range did not scale');
      report.followup='five targets spaced 350 reached; beyond 510 stops; first cast remains 170; upgrades scale follow-up range';
      const es=setup(7);pl.quantityBonus=20;const m=cast();m.dmg=999;step(2);assert(es.filter(e=>e.hp<e.maxHp).length===5,'quantity exceeded cap');assert(es[0].maxHp-es[0].hp<900,'snapshot mutated');report.snapshot='quantity +20 stays 5; learned damage snapshot immutable';
      setup(2);cast();let hp=pl.hp;pl.hurt(1,null,true);assert(pl.hp<hp,'charge invulnerable');pl.invuln=0;step(.095);assert(A.active?.phase==='dash','dash not begun');hp=pl.hp;pl.hurt(10000,null,true);assert(pl.hp===hp,'dash pure damage got through');pl.invuln=0;pl.hurt(10,'fire');assert(pl.hp===hp,'dash typed damage got through');
      let oldx=pl.x,oldy=pl.y;const axis=G.Input.axis;G.Input.axis=()=>[1,1];pl.update(.01);G.Input.axis=axis;assert(pl.x===oldx&&pl.y===oldy,'normal movement fought dash');
      while(A.active?.phase==='dash')step(1/240);assert(A.active?.phase==='retarget','missing retarget window');pl.invuln=0;hp=pl.hp;pl.hurt(1,null,true);assert(pl.hp<hp,'retarget invulnerable');pl.invuln=0;step(1);assert(!A.active,'end pending');assert(pl.invuln===.3,'missing end protection');hp=pl.hp;pl.hurt(1,null,true);assert(pl.hp===hp,'end protection did not block');pl.update(.31);pl.hurt(1,null,true);assert(pl.hp<hp,'end protection did not expire');report.immunity='actual dash invulnerable; charge/retarget vulnerable; end protected 0.3 seconds then expires; joystick suppressed';
      setup(2);pl.invuln=3;cast();step(.095);G.Combat.clearFields();assert(pl.invuln===3,'overwrote independent invulnerability');
      setup(1);pl.invuln=3;cast();step(1);assert(pl.invuln===3,'end shortened existing protection');
      setup(1);cast();G.Combat.clearFields();assert(pl.invuln===0,'charge clear gave end protection');
      setup(1);cast();G.EnemyMgr.all()[0].dead=true;step(.2);assert(pl.invuln===0,'charge cancellation gave end protection');
      setup(2);cast();G.World.isFree=(x)=>x<40;step(1);assert(pl.x<40&&!A.active&&pl.invuln===.3,'wall crossed or missing end protection');G.World.isFree=()=>true;report.walls='solid geometry stops chain without remote damage and grants end protection';
      setup(2);cast();step(.095);G.World.isFree=()=>false;step(.01);assert(!A.active,'solid prop did not stop');G.World.isFree=()=>true;
      setup(2);cast();step(.095);pl.dead=true;step(.01);assert(!A.active&&pl.invuln===0,'death residue or added protection');
      setup(2);cast();step(.095);const world=G.World;G.World={...world};step(.01);assert(!A.active&&pl.invuln===0,'world residue or added protection');G.World=world;
      setup(2);cast();step(.095);G.Combat.clearFields(pl);assert(!A.active&&pl.invuln===0,'clear residue or added protection');
      setup(1);cast();step(1);pl.update(.1);const remaining=pl.invuln;step(1);assert(pl.invuln===remaining,'end protection refreshed repeatedly');
      setup(1);cast();G.EnemyMgr.all()[0].dead=true;step(.2);assert(!A.active,'dead target remained');
      assert(G.Moves.BY_ID['naruto-kakashi'].digiMode==='dash','Raikiri changed');assert(G.Moves.instance('naruto-sasuke',5).dmg>44,'upgrades lost');
      report.lifecycle='death/world change/dead target/owner clear clean; independent invulnerability preserved; Raikiri unchanged';
      Object.assign(G.World,orig);return report;
    }''')
    capture=r'''() => {
      const pl=G.Game.player;G.Combat.clearFields();G.EnemyMgr.clear();G.FX.clear();
      pl.x=pl.y=0;pl.hp=pl.maxHp;pl.dead=false;pl.flash=0;pl.invuln=0;pl.aim=0;
      const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},130,0,{hp:1,spd:1,dmg:1});
      G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();pl.target=e;
      G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke'));G.Combat.updateFields(.095);
      G.World.isFree=()=>true;G.Combat.updateFields(.025);
      G.Camera.x=pl.x;G.Camera.y=pl.y;document.getElementById('scr-pause').style.visibility='hidden';
    }'''
    page.evaluate(capture);page.wait_for_timeout(60)
    page.screenshot(path=str(ROOT/'.omx/chidori-desktop.png'),animations='disabled')
    mobile=b.new_context(viewport={'width':390,'height':844},locale='zh-TW',is_mobile=True,has_touch=True,service_workers='block')
    mobile.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    phone=mobile.new_page();phone.on('pageerror',lambda e:errors.append(str(e)))
    phone.goto('https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW')
    phone.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if phone.locator('#tap-start').is_visible():phone.locator('#tap-start').click()
    phone.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
    phone.evaluate(capture);phone.wait_for_timeout(60)
    phone.screenshot(path=str(ROOT/'.omx/chidori-portrait.png'),animations='disabled')
    assert not errors, errors
    print(json.dumps({'ok':True,'checks':result},ensure_ascii=False));b.close()
