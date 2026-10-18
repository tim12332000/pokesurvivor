from pathlib import Path
from playwright.sync_api import sync_playwright
import json

URL='http://127.0.0.1:8002/.omx/digimon.html?lang=zh-TW&v=signature-skills'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(locale='zh-TW',viewport={'width':1280,'height':820})
    page=context.new_page();errors=[];missing=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:missing.append(r.url) if r.status>=400 else None)
    page.goto(URL);page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.locator('#digimon-skill-guide').click()
    assert page.locator('#scr-digimon-skills .digimon-skill-entry').count()==33
    assert page.locator('#scr-digimon-skills a[href^="https://"]').count()>=33
    page.screenshot(path='.omx/digimon-skill-guide.png',animations='disabled')
    page.locator('#digimon-skills-close').click()
    page.locator('[data-digimon="20001"]').click()
    page.locator('#scr-menu [data-go="play"]').click()
    page.wait_for_function('G.Game.state==="playing"')
    page.evaluate('G.Game.togglePause()')
    report=page.evaluate('''() => {
      const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
      const catalog=G.DigimonSkillCatalog, pl=G.Game.player;
      assert(catalog.byDex.size===33,'Primary skill coverage');
      assert(catalog.definitions.size===38,'Expected primary and secondary skills');
      const supported=new Set(['shot','nova','melee','beam','dash','slam','gate','aura','blizzard','dual']);
      for(const d of catalog.definitions.values()){
        assert(supported.has(d.digiMode),'Unsupported mode '+d.id);
        assert(Number.isFinite(d.dmg)&&d.dmg>0&&d.cd>0,'Invalid balance '+d.id);
        assert(d.ups.length===4&&d.maxLvl===5,'Missing upgrades '+d.id);
        for(const key of ['proj','beam','aura']) if(d.digiVis[key])assert(G.VFX.SHAPES[d.digiVis[key]],'Missing VFX '+d.digiVis[key]);
        const upgraded=G.Moves.instance(d.id,5);assert(Number.isFinite(upgraded.dmg)&&upgraded.dmg>d.dmg,'Broken upgrades '+d.id);
      }
      for(const record of G.Digimon.records.values()){
        const pool=G.Moves.poolFor(record.mon);
        assert(pool.includes(record.start)&&pool.every(id=>catalog.definitions.has(id)),'Pokemon move leaked into Digimon pool '+record.name);
        assert(catalog.references.has(record.dex),'Missing source '+record.name);
      }
      assert(!G.Moves.poolFor(G.DEX_BY[1]).some(id=>catalog.definitions.has(id)),'Vanilla pool changed');
      assert(catalog.byDex.get(20111).type==='fire'&&!catalog.byDex.get(20111).slow,'Fox Fire incorrectly freezes');
      assert(catalog.byDex.get(20163).count===7,'Seven Heavens must have seven spheres');
      const saved={isWall:G.World.isWall,projectileBlock:G.World.projectileBlock,propsInCircle:G.World.propsInCircle,
        isFree:G.World.isFree,collide:G.World.collide,damageProp:G.World.damageProp};
      G.World.isWall=()=>false;G.World.projectileBlock=()=>false;G.World.propsInCircle=()=>[];
      G.World.isFree=()=>true;G.World.collide=()=>{};
      let now=0;
      const setup=(positions=[[60,0],[95,14],[132,-15],[170,20],[220,0]])=>{
        G.Combat.clearFields();G.Projectiles.clear();G.FX.clear();G.EnemyMgr.clear();
        pl.x=pl.y=0;pl.aim=0;pl.hp=pl.maxHp;pl.dead=false;pl.dmgDealt=0;pl.critChance=0;
        const enemies=positions.map(([x,y])=>{
          const e=new G.Enemy({dex:19,hp:1000000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
          e.types=['normal'];e.r=10;G.EnemyMgr.add(e);return e;
        });
        G.EnemyMgr.rebuildGrid();pl.target=enemies[0]||null;return enemies;
      };
      const step=(seconds)=>{for(let t=0;t<seconds;t+=1/60){now+=1/60;G.Projectiles.update(1/60,pl,G.EnemyMgr.all());G.Combat.resolve(1/60,pl,now);G.Combat.updateFields(1/60);G.FX.update(1/60);}};
      const cast=(definition)=>G.DigimonSkills.cast(pl,G.Moves.instance(definition.id));
      const results=[];
      try{
        for(const d of catalog.definitions.values()){
          const enemies=setup();const before=enemies.reduce((sum,e)=>sum+e.hp,0);
          assert(cast(d),'Cast rejected '+d.id);step(2.4);
          const damage=before-enemies.reduce((sum,e)=>sum+e.hp,0);
          assert(Number.isFinite(damage)&&damage>0,'Skill dealt no damage '+d.id);
          results.push({id:d.id,mode:d.digiMode,damage});
        }
        // Separate blows must land at separate times.
        let enemies=setup([[60,0]]);const m=G.Moves.instance('digimon-gatomon');cast(m);
        step(.02);const first=1000000-enemies[0].hp;step(.15);const second=1000000-enemies[0].hp;
        assert(first>0&&second>first,'Combo was not staggered');
        // One direct impact plus one blast must total one skill budget, not double it.
        enemies=setup([[80,0]]);const bomb=catalog.byDex.get(20101);cast(bomb);step(.8);
        const actual=1000000-enemies[0].hp,expected=Math.round(bomb.dmg*pl.atk*.2)+Math.round(bomb.dmg*pl.atk*.8);
        assert(Math.abs(actual-expected)<.01,'Explosion damage counted twice '+actual+' != '+expected);
        step(.5);assert(Math.abs((1000000-enemies[0].hp)-actual)<.01,'Explosion repeated');
        // Charging snapshots survive evolution replacing the live move object.
        setup();const charged=G.Moves.instance('digimon-wargreymon');G.DigimonSkills.cast(pl,charged);
        charged.dmg=999999;charged.count=99;step(.5);
        assert(G.Projectiles.all().length===1&&G.Projectiles.all()[0].dmg<1000,'Charge did not snapshot the move');
        // Targeted gate appears at the target and bosses are less affected by pull.
        enemies=setup([[80,0],[115,0],[115,20]]);enemies[2].boss=true;
        cast(catalog.byDex.get(20162));step(.7);
        const gate=G.DigimonSkills.activeEffects.find(f=>f.kind==='gate');
        assert(gate&&gate.x===80&&gate.y===0,'Portal not centered on target');
        assert(enemies[1].kx<0&&Math.abs(enemies[2].kx)<Math.abs(enemies[1].kx),'Boss pull resistance broken');
        assert(enemies.every(e=>e.hp>0),'Portal instantly deleted a boss');
        G.Combat.clearFields();assert(G.DigimonSkills.activeEffects.length===0,'Effects survived clear');
        // Wall stops a beam. Props outside the actual line stay intact.
        enemies=setup([[150,0]]);G.World.isWall=(x)=>x>=80;
        cast(catalog.byDex.get(20142));step(.3);assert(enemies[0].hp===1000000,'Beam passed a wall');
        G.World.isWall=()=>false;setup();const props=[{id:'on',x:80,y:0,r:8},{id:'off',x:70,y:100,r:8}],hitProps=[];
        G.World.propsInCircle=()=>props;G.World.damageProp=p=>hitProps.push(p.id);
        cast(catalog.byDex.get(20161));assert(hitProps.includes('on')&&!hitProps.includes('off'),'Beam damaged off-line prop');
        G.World.propsInCircle=()=>[];
        // A mixed bonded slot executes vanilla and custom members without corrupting it.
        setup();const custom=G.Moves.instance('digimon-agumon'),normal=G.Moves.instance('ember');
        const priorGroup=pl.activeGroup;pl.activeGroup=()=>[custom,normal];const mixed=pl.activeGroup;
        G.Combat.tick(.02,pl,now);assert(G.Projectiles.all().length===2&&pl.activeGroup===mixed,'Mixed slot broken');pl.activeGroup=priorGroup;
        const pokemon=new G.Player(G.DEX_BY[1],{});pokemon.addMove('ember');pokemon.target=pl.target;pokemon.aim=0;
        const vanillaGroup=pokemon.activeGroup;G.Combat.tick(.02,pokemon,now);
        assert(pokemon.activeGroup===vanillaGroup,'Vanilla activeGroup was patched');
        // Stale owners cannot finish queued attacks after death or a scene reset.
        setup();cast(catalog.byDex.get(20103));pl.dead=true;G.DigimonSkills.update(1);
        assert(G.DigimonSkills.activeEffects.length===0&&G.Projectiles.all().length===0,'Dead owner fired a delayed attack');
        pl.dead=false;G.Combat.clearFields();
        return {primary:catalog.byDex.size,skills:catalog.definitions.size,modes:[...new Set(results.map(r=>r.mode))],
          casts:results,combo:'staggered',explosion:'single budget',source_coverage:catalog.references.size,
          snapshot:'passed',gate:'passed',walls_and_props:'passed',vanilla_and_mixed:'passed',cleanup:'passed'};
      }finally{Object.assign(G.World,saved);G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();pl.dead=false;}
    }''')
    assert not errors,errors
    assert not missing,missing
    print(json.dumps(report,ensure_ascii=True))
    # Fresh live runs exercise automatic firing, animation and render callbacks.
    page.evaluate('G.Game.quit();G.Flow.goMenu();G.Digimon.choose(20006);G.Flow.play()')
    page.wait_for_timeout(2800)
    page.screenshot(path='.omx/digimon-fish-skill.png',animations='disabled')
    page.evaluate('G.Game.quit();G.Flow.goMenu();G.Digimon.choose(20162);G.Flow.play()')
    page.wait_for_timeout(3200)
    page.screenshot(path='.omx/digimon-gate-skill.png',animations='disabled')
    assert not errors,errors
    print('Live fish/gate firing and rendering: passed; JavaScript errors: 0')
    browser.close()
