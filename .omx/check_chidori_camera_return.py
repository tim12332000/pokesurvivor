"""Actual frame order verifies fixed camera, screen-limited targets and safe return."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright
import json, mimetypes

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=chidori-camera'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    reports=[]
    for mobile in (False,True):
        context=browser.new_context(locale='zh-TW',viewport={'width':390 if mobile else 1280,'height':844 if mobile else 820},is_mobile=mobile,has_touch=mobile,service_workers='block')
        def proxy(route):
            f=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            route.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'',content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
        context.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(URL);page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
        page.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
        report=page.evaluate(r'''() => {
          const A=G.NarutoChidori,C=G.Camera,pl=G.Game.player,assert=(v,m)=>{if(!v)throw Error(m)};
          const original={isFree:G.World.isFree,isLiquid:G.World.isLiquid,collide:G.World.collide},axis=G.Input.axis;
          Object.assign(G.World,{isFree:()=>true,isLiquid:()=>false,collide:()=>{}});G.Input.axis=()=>[1,1];
          let hitEvents=[];
          function setup(points=[100]){
            hitEvents=[];
            G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();G.FX.clear();
            pl.x=pl.y=0;pl.hp=pl.maxHp;pl.dead=false;pl.invuln=0;pl.quantityBonus=0;pl.critChance=0;pl.item=null;
            C.x=C.y=C.shake=C._sx=C._sy=0;
            pl.moves=[G.Moves.instance('naruto-sasuke')];pl.slots=[[pl.moves[0]]];pl.active=0;
            const es=points.map(x=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,0,{hp:1,spd:1,dmg:1});e.types=['normal'];const hurt=e.hurt;e.hurt=function(...args){hitEvents.push(e);return hurt.apply(this,args);};G.EnemyMgr.add(e);return e;});
            G.EnemyMgr.rebuildGrid();pl.target=es[0];return es;
          }
          function cast(){assert(G.DigimonSkills.cast(pl,pl.moves[0]),'cast rejected');}
          function fields(dt){G.Combat.updateFields(dt);}
          function frame(dt){pl.update(dt);C.follow(pl.x,pl.y,dt);fields(dt);}
          const es=setup([100,200]);C.x=12;C.y=-9;C.shake=1;cast();
          assert(A.active.origin.x===0&&A.active.camera.x===12,'missing position snapshots');
          const phases=new Set();let moved=false;
          for(let i=0;i<240&&A.active;i++){
            const state=A.active,phase=state.phase,x=pl.x,y=pl.y;phases.add(phase);
            C.kick(1);frame(1/240);
            assert(C.x===12&&C.y===-9&&C.shake===0&&C._sx===0&&C._sy===0,'camera moved/shook in '+phase);
            if(phase==='charge'||phase==='retarget')assert(pl.x===x&&pl.y===y,'phase update drift');
            if(pl.x>1)moved=true;
          }
          assert(moved&&phases.has('charge')&&phases.has('dash')&&phases.has('retarget')&&phases.has('return'),'missing phase/movement');
          assert(!A.active&&pl.x===0&&pl.y===0&&es.every(e=>e.hp<e.maxHp),'failed exact origin return');
          C.follow(200,100,.1);assert(C.x!==12&&C.y!==-9,'normal follow remained frozen');
          setup();cast();fields(.09);while(A.active.phase==='dash')fields(1/240);
          assert(A.active.phase==='return'&&pl.x>0&&pl.invuln===0&&pl.moves[0].t===0,'end protection applied before return');
          const endpoint=pl.x,damage=pl.dmgDealt,hp=pl.hp;pl.hurt(10000,null,true);assert(pl.hp===hp,'return flight vulnerable');
          pl.moves.push(G.Moves.instance('naruto-sharingan',2));G.NarutoSharingan.sync(pl);
          const random=Math.random,projectiles=G.Projectiles.count;let rolls=0;
          try{Math.random=()=>{rolls++;return 0;};pl.hurt(100,'fire');}
          finally{Math.random=random;}
          assert(pl.hp===hp&&rolls===0&&G.Projectiles.count===projectiles&&pl.invuln===0,'Sharingan consumed dodge/counter during return immunity');
          fields(.06);assert(pl.x>0&&pl.x<endpoint&&A.active.phase==='return','return did not interpolate');
          fields(.06);assert(!A.active&&pl.x===0&&pl.y===0&&pl.invuln===.3&&pl.moves[0].t===.5&&pl.dmgDealt===damage,'return completion damaged/failed cooldown');
          const edge=C.w/2+48;
          const clipped=setup([100,edge,edge+.01]);cast();for(let i=0;i<400&&A.active;i++)fields(1/240);
          assert(clipped[0].hp<clipped[0].maxHp&&clipped[1].hp<clipped[1].maxHp&&clipped[2].hp===clipped[2].maxHp,'padding edge inclusion/exclusion');
          setup([edge+.01]);pl.x=edge-30;assert(!G.DigimonSkills.cast(pl,pl.moves[0]),'initial target outside screen accepted');
          setup([edge]);pl.x=edge-30;cast();G.Combat.clearFields();
          const moving=setup([100]);cast();fields(.09);fields(.01);moving[0].x=edge+1;fields(.001);
          assert(A.active.phase==='return'&&moving[0].hp===moving[0].maxHp,'offscreen moving target chased/hit');G.Combat.clearFields();
          const maxTargets=setup([70,100,130,160,190,220]);cast();for(let i=0;i<400&&A.active;i++)fields(1/240);
          assert(!A.active&&pl.x===0&&hitEvents.length===5&&hitEvents.every((e,i)=>!i||e!==hitEvents[i-1]),'maximum-hit completion did not return');
          const dead=setup([100]);cast();fields(.09);fields(.01);dead[0].dead=true;fields(.001);
          assert(A.active.phase==='return','dead last target failed return');G.Combat.clearFields();
          for(const reason of ['clear','death','world']){
            setup();cast();fields(.09);fields(.02);const x=pl.x;assert(x>0,'cancellation fixture never moved');
            if(reason==='clear')G.Combat.clearFields(pl);
            if(reason==='death'){pl.dead=true;fields(.01);}
            if(reason==='world'){const world=G.World;G.World={...world};fields(.01);G.World=world;}
            assert(!A.active&&pl.x===x&&pl.invuln===0,'cancel teleported/protected '+reason);
            C.follow(200,100,.1);assert(C.x!==0,'camera remained frozen after '+reason);
          }
          setup();cast();G.Combat.clearFields();assert(pl.x===0&&pl.invuln===0,'charge cancellation returned/protected');
          setup();const other=new G.Player(G.Naruto.records.get(30002));assert(!G.DigimonSkills.cast(other,G.Moves.instance('naruto-sasuke')),'foreign player cast accepted');
          pl.dex=30001;assert(!G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke')),'Naruto used Sasuke camera lock');C.follow(200,100,.1);assert(C.x!==0,'Naruto camera affected');pl.dex=30002;
          Object.assign(G.World,original);G.Input.axis=axis;G.Combat.clearFields();
          return {viewport:{w:C.w,h:C.h},phases:[...phases],camera:'fixed during actual frame order, no shake; normal follow restored',targets:'48px edge accepted; outside rejected first/follow-up/moving target',return:'0.12s exact origin, no damage, invulnerable flight; end protection/cooldown afterward',cancellation:'clear/death/world change do not teleport or protect'};
        }''')
        assert not errors,errors
        report['mobile']=mobile;reports.append(report);context.close()
    browser.close();print(json.dumps({'ok':True,'checks':reports},ensure_ascii=False))
