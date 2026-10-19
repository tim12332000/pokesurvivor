"""Browser regression for Naruto integration, source sprites and real skill damage."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
import json
import mimetypes
import os

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=naruto'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(locale='zh-TW',viewport={'width':1280,'height':820},service_workers='block')
    if os.environ.get('PAGES_LIVE')!='1':
        def proxy(route):
            name=unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            file=ROOT / name
            if file.is_file():route.fulfill(status=200,body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            else:route.fulfill(status=404,body='Not found')
        context.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    page=context.new_page();errors=[];missing=[];cloud=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:missing.append(r.url) if r.status>=400 else None)
    page.on('request',lambda r:cloud.append(r.url) if any(s in r.url for s in ['firebaseio.com','firestore.googleapis.com','identitytoolkit.googleapis.com']) else None)
    page.goto(URL);page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.locator('#btn-naruto').click()
    page.wait_for_function('[...G.Naruto.records.values()].every(r=>r.ready)')
    assert page.locator('#scr-naruto [data-naruto]').count()==2
    assert page.locator('#scr-digimon').is_hidden()
    page.screenshot(path=str(ROOT/'.omx/naruto-picker.png'),animations='disabled')
    page.locator('#naruto-skill-guide').click()
    assert page.locator('.naruto-skill-entry').count()==2
    assert page.locator('.naruto-skill-entry a[href^="https://naruto-official.com/"]').count()==8
    page.screenshot(path=str(ROOT/'.omx/naruto-guide.png'),animations='disabled')
    page.locator('#naruto-skills-close').click()
    page.locator('[data-naruto="30001"]').click()
    assert page.locator('#menu-partner-name').inner_text()=='漩渦鳴人'
    report=page.evaluate('''() => {
      const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
      assert(G.MenuUI.GEN_NAMES.filter(Boolean).length===10&&G.Gacha.BANNERS.filter(Boolean).length===10,'Section registration');
      assert(G.NarutoSkillCatalog.definitions.size===28,'Skill registry');
      const pixels=[];
      for(const r of G.Naruto.records.values()) {
        assert(G.startMoveOf(r.dex)===r.start,'Starter signature '+r.dex);
        assert(G.Moves.poolFor(r).every(id=>id.startsWith('naruto-')),'Foreign move in Naruto pool');
        const canvas=document.createElement('canvas');canvas.width=canvas.height=180;
        const ctx=canvas.getContext('2d',{willReadFrequently:true});
        const animator=new G.Sprites.Animator(r.dex);
        for(let dir=0;dir<8;dir++) {
          animator.dir=dir;animator.loop('Walk');animator.update(.15);ctx.clearRect(0,0,180,180);animator.draw(ctx,90,140);
          const rgba=ctx.getImageData(0,0,180,180).data;
          const count=rgba.reduce((n,v,i)=>n+(i%4===3&&v>0?1:0),0);
          assert(count>100&&count<9000,'Sprite empty or background visible '+r.dex);pixels.push(count);
        }
      }
      assert(!G.Moves.poolFor(G.DEX_BY[1]).some(id=>id.startsWith('naruto-')),'Pokemon pool changed');
      assert(!G.Moves.poolFor(G.DEX_BY[20001]).some(id=>id.startsWith('naruto-')),'Digimon pool changed');
      for(let i=0;i<10;i++)assert(G.Gacha.pull(G.DB.save,10,11,'t10').every(r=>G.Naruto.availableDexes.includes(r.dex)&&!r.shiny),'Naruto gacha leaked');
      return {characters:G.Naruto.records.size,skills:G.NarutoSkillCatalog.definitions.size,direction_renders:pixels.length};
    }''')
    page.locator('#scr-menu [data-go="dex"]').click()
    assert page.locator('#dex-gens .gen-tab').count()==10
    page.locator('#dex-gens .gen-tab').last.click()
    assert page.locator('#dex-grid .cell').count()==2
    page.screenshot(path=str(ROOT/'.omx/naruto-collection.png'),animations='disabled')
    page.evaluate('G.Flow.goMenu();G.GachaUI.open()')
    page.locator('#gacha-gens [data-gen="11"]').click()
    assert page.locator('#gacha-gens .gen-tab').count()==10
    page.screenshot(path=str(ROOT/'.omx/naruto-gacha.png'),animations='disabled')
    page.evaluate('G.Flow.goMenu()')
    for dex in (30001,30002):
        page.evaluate('(dex)=>G.Naruto.choose(dex)',dex)
        page.locator('#scr-menu [data-go="play"]').click()
        page.wait_for_function('G.Game.state==="playing"')
        assert page.evaluate('G.Game.player.dex')==dex
        assert page.evaluate('G.Game.player.moves[0].id').startswith('naruto-')
        page.keyboard.down('d');page.wait_for_timeout(100);page.keyboard.up('d')
        if dex==30001:page.screenshot(path=str(ROOT/'.omx/naruto-gameplay.png'))
        page.evaluate('G.Game.quit();G.Flow.goMenu()')
    page.evaluate('G.Naruto.choose(30001);G.Flow.play();G.Game.togglePause()')
    damage=page.evaluate('''() => {
      const pl=G.Game.player,saved={isWall:G.World.isWall,isFree:G.World.isFree,collide:G.World.collide,propsInCircle:G.World.propsInCircle,projectileBlock:G.World.projectileBlock};
      Object.assign(G.World,{isWall:()=>false,isFree:()=>true,collide:()=>{},propsInCircle:()=>[],projectileBlock:()=>false});
      const results=[];
      try {
        for(const def of G.NarutoSkillCatalog.definitions.values()) {
          if(def.dmg===0)continue; // Support behavior has dedicated roster checks.
          G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();pl.x=pl.y=0;G.Camera.x=G.Camera.y=0;pl.aim=0;pl.hp=pl.maxHp;pl.dead=false;pl.critChance=0;
          const owner=[...G.Naruto.records.values()].find(mon=>{const level=pl.level;pl.level=9;try{return G.Moves.poolFor(mon).includes(def.id);}finally{pl.level=level;}})||G.Naruto.records.get(30001);
          pl.mon=owner;pl.dex=owner.dex;
          const targets=[[60,0],[110,10],[160,-15]].map(([x,y])=>{
            const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);return e;
          });G.EnemyMgr.rebuildGrid();pl.target=targets[0];
          // Maintained weapons require an actually learned move before activation.
          const maintained=def.id==='naruto-kusanagi'&&!pl.hasMove(def.id)?G.Moves.instance(def.id):null;
          const previousSlots=pl.slots,previousActive=pl.active;
          if(maintained){pl.moves.push(maintained);pl.slots=[...pl.slots,[maintained]];pl.active=pl.slots.length-1;}
          G.DigimonSkills.cast(pl,G.Moves.instance(def.id));
          for(let t=0;t<2;t+=1/60){G.Projectiles.update(1/60,pl,G.EnemyMgr.all());G.Combat.resolve(1/60,pl,t);G.Combat.updateFields(1/60);G.FX.update(1/60);}
          const damage=300000-targets.reduce((s,e)=>s+e.hp,0);
          if(!Number.isFinite(damage)||damage<=0)throw Error('No damage '+def.id);
          results.push({skill:def.id,damage});
          if(maintained){pl.moves.splice(pl.moves.indexOf(maintained),1);pl.slots=previousSlots;pl.active=previousActive;}
        }
      }finally{Object.assign(G.World,saved);G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();}
      return results;
    }''')
    page.evaluate('G.Game.quit();G.Naruto.choose(30002);G.DB.commit()')
    page.reload();page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    page.wait_for_function("!document.getElementById('tap-start').classList.contains('hidden')||!document.getElementById('topbar').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    assert page.evaluate('G.DB.save.partner')==30002
    page.locator('#btn-naruto').click()
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(ROOT/'.omx/naruto-mobile.png'),animations='disabled')
    page.locator('[data-naruto="30001"]').scroll_into_view_if_needed();page.locator('[data-naruto="30001"]').click()
    assert page.evaluate('G.DB.save.partner')==30001
    assert not errors,errors
    assert not missing,missing
    assert not cloud,cloud
    report.update(damage=damage,combat_starts=2,save_reload='passed',mobile='passed',errors=errors)
    print(json.dumps(report,ensure_ascii=True));browser.close()
