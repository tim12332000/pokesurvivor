"""Verify actual multi-target sand phases, scope, cleanup and new area skills."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
import json
import mimetypes
import os

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=gaara-aoe'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(locale='zh-TW',viewport={'width':1280,'height':820},service_workers='block')
    if os.environ.get('PAGES_LIVE')!='1':
        def proxy(route):
            file=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            if file.is_file():route.fulfill(status=200,body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            else:route.fulfill(status=404,body='Not found')
        context.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(URL);page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.evaluate('G.Naruto.choose(30007);G.Flow.play();G.Game.togglePause()')
    page.evaluate('G.Sprites.preload([19])')
    result=page.evaluate('''() => {
      const assert=(ok,msg)=>{if(!ok)throw Error(msg);},pl=G.Game.player;
      const saved={isWall:G.World.isWall,isFree:G.World.isFree,collide:G.World.collide,propsInCircle:G.World.propsInCircle,projectileBlock:G.World.projectileBlock};
      Object.assign(G.World,{isWall:()=>false,isFree:()=>true,collide:()=>{},propsInCircle:()=>[],projectileBlock:()=>false});
      const sand=G.Moves.BY_ID['naruto-gaara'];let time=0;
      const setup=(points=[[95,-20],[170,30],[245,-50],[180,200],[-40,0]])=>{
        G.Combat.clearFields();G.Projectiles.clear();G.FX.clear();G.EnemyMgr.clear();
        pl.x=pl.y=0;pl.aim=0;pl.hp=pl.maxHp;pl.dead=false;pl.critChance=0;
        const enemies=points.map(([x,y])=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);return e;});
        G.EnemyMgr.rebuildGrid();pl.target=enemies[0];return enemies;
      };
      const step=seconds=>{for(let t=0;t<seconds;t+=1/120){time+=1/120;G.Projectiles.update(1/120,pl,G.EnemyMgr.all());G.Combat.resolve(1/120,pl,time);G.Combat.updateFields(1/120);G.FX.update(1/120);}};
      const cast=()=>G.DigimonSkills.cast(pl,G.Moves.instance(sand.id));
      const loss=e=>100000-e.hp;
      try {
        let e=setup();e[1].boss=true;cast();step(.72);
        assert(G.Projectiles.all().length===0,'Gaara still fires an orb');
        const first=e.map(loss);assert(first.slice(0,3).every(n=>n>0),'Wave did not hit three spread targets');
        assert(first[3]===0&&first[4]===0,'Wave hit outside/behind');
        assert(e[0].slow===.95&&e[1].slow===.35,'Boss control resistance');
        step(.3);assert(e.every((v,i)=>loss(v)===first[i]),'Damage repeated during binding');
        step(.2);const final=e.map(loss);assert(final.slice(0,3).every((n,i)=>n>first[i]),'Area burial missing');
        const budget=Math.round(sand.dmg*pl.atk*.25)+Math.round(sand.dmg*pl.atk*.75);
        assert(final.slice(0,3).every(n=>n===budget),'Sand damage exceeded one cast budget');
        assert(final[3]===0&&final[4]===0,'Burial hit outside/behind');
        step(.5);assert(e.every((v,i)=>loss(v)===final[i]),'Burial repeated');
        assert(!G.DigimonSkills.activeEffects.some(f=>f.kind==='sand-wave'),'Sand field leaked');
        // A visual cocoon cap must never limit AoE damage or binding in a crowd.
        e=setup(Array.from({length:40},(_,i)=>[80+(i%8)*24,(Math.floor(i/8)-2)*15]));cast();step(.72);
        assert(e.every(v=>loss(v)>0&&v.slow===.95),'Crowd targets escaped wave or binding');step(.5);
        assert(e.every(v=>loss(v)===budget),'Crowd targets missed the full damage budget');
        // Entering the swept area after the wave still receives the area eruption.
        e=setup([[100,0],[500,0]]);cast();step(.72);e[1].x=200;G.EnemyMgr.rebuildGrid();step(.5);
        assert(loss(e[1])>0,'Burial only damages the initial target list');
        // Terrain must block an otherwise in-range target.
        e=setup([[220,0]]);G.World.isWall=x=>x>120&&x<140;cast();step(1.3);
        assert(loss(e[0])===0,'Sand damaged through a wall');G.World.isWall=()=>false;
        e=setup();cast();step(.3);const before=e.map(loss);G.Combat.clearFields();step(1.3);
        assert(e.every((v,i)=>loss(v)===before[i]),'Scene clear left a delayed burial');
        e=setup();cast();step(.3);const alive=e.map(loss);pl.dead=true;step(1.3);
        assert(e.every((v,i)=>loss(v)===alive[i]),'Dead owner completed burial');pl.dead=false;
        // All added AoE projectiles must splash across several rows, not just one line.
        const extra=[];
        for(const id of ['naruto-rasenshuriken','naruto-fireball','naruto-water-dragon']) {
          e=setup([[80,0],[110,35],[130,-35],[100,200]]);
          G.DigimonSkills.cast(pl,G.Moves.instance(id));step(1.5);
          const damage=e.map(loss);assert(damage.slice(0,3).every(n=>n>0)&&damage[3]===0,'Not true AoE '+id);
          extra.push({id,damage});
          assert(G.Moves.instance(id,4).blastRadius>G.Moves.instance(id).blastRadius,'AoE range upgrade ineffective '+id);
        }
        assert(G.Moves.instance(sand.id,4).range>sand.range&&G.Moves.instance(sand.id,4).width>sand.width,'Sand range upgrade ineffective');
        for(const id of ['naruto-sakura','naruto-hinata','naruto-lee']) {
          e=setup([[55,0],[70,25],[70,-25],[220,150]]);G.DigimonSkills.cast(pl,G.Moves.instance(id));step(.5);
          assert(e.slice(0,3).every(v=>loss(v)>0)&&loss(e[3])===0,'Existing melee AoE broken '+id);
        }
        const owners={'naruto-rasenshuriken':[30001],'naruto-fireball':[30002,30008],'naruto-water-dragon':[30004]};
        for(const [id,allowed]of Object.entries(owners))for(const r of G.Naruto.records.values())
          assert(G.Moves.poolFor(r).includes(id)===allowed.includes(r.dex),'Wrong extra move owner '+id);
        // A clean deterministic scene for visual review of all three phases.
        e=setup();e[1].boss=true;cast();step(.38);
        const snapshot=()=>{const f=G.DigimonSkills.activeEffects.find(f=>f.kind==='sand-wave');return {...f,victims:[...f.victims]};};
        const stages=[snapshot()];step(.67);stages.push(snapshot());step(.22);stages.push(snapshot());
        window.gaaraVisual={stages,enemies:e,player:pl};
        return {wave:first,burial:final,crowd_40:'passed',boss_resistance:'passed',walls:'passed',late_entry:'passed',single_burst:'passed',cleanup:'passed',extra};
      }finally{Object.assign(G.World,saved);}
    }''')
    page.evaluate('''() => {
      const {stages,enemies,player}=window.gaaraVisual;
      const panel=document.createElement('div');panel.id='sand-review';panel.style.cssText='position:fixed;inset:0;z-index:20000;background:#0a1730;color:white;padding:18px;display:flex;gap:12px;align-items:center;font:16px sans-serif';
      for(const [index,label]of ['流砂橫掃','砂縛控場','整片壓葬'].entries()) {
        const box=document.createElement('section');box.style.cssText='flex:1;min-width:0;text-align:center';
        const title=document.createElement('h3');title.textContent=label;
        const canvas=document.createElement('canvas');canvas.width=400;canvas.height=480;canvas.style.cssText='width:100%;image-rendering:pixelated;border:1px solid #7d92b8';
        const ctx=canvas.getContext('2d');ctx.fillStyle='#31613b';ctx.fillRect(0,0,400,480);ctx.translate(38,245);
        const pose=stages[index];
        G.NarutoSandVFX.drawGround(ctx,pose);
        player.anim.dir=G.Sprites.dirFromAngle(0);player.anim.cur='Shoot';player.anim.frame=1;player.anim.draw(ctx,0,0);
        for(const e of enemies)e.anim.draw(ctx,e.x,e.y);
        G.NarutoSandVFX.drawAir(ctx,pose);
        box.append(title,canvas);panel.append(box);
      }document.body.append(panel);
    }''')
    page.screenshot(path=str(ROOT/'.omx/gaara-sand-phases.png'),animations='disabled')
    page.evaluate('''() => {
      document.getElementById('sand-review').remove();
      const canvas=document.createElement('canvas');canvas.width=900;canvas.height=260;
      canvas.style.cssText='position:fixed;top:80px;left:20px;z-index:20000;background:#173564';
      const ctx=canvas.getContext('2d');
      for(const [i,id]of ['naruto-rasenshuriken','naruto-fireball','naruto-water-dragon'].entries()) {
        const move=G.Moves.BY_ID[id];ctx.fillStyle='white';ctx.font='18px sans-serif';ctx.fillText(move.name,i*290+20,35);
        for(let frame=0;frame<3;frame++)G.VFX.draw(ctx,move.digiVis.proj,move.digiVis.pal,i*290+50+frame*75,140,{scale:3,frame});
      }document.body.append(canvas);
    }''')
    page.screenshot(path=str(ROOT/'.omx/naruto-aoe-projectiles.png'),animations='disabled')
    assert not errors,errors
    print(json.dumps(result,ensure_ascii=True));browser.close()
