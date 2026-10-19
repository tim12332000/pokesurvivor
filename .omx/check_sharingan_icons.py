"""Verify evolving eye icons through the actual icon cache, cards, and HUD."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import mimetypes
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    def route_file(route):
        file = ROOT / unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
        route.fulfill(status=200 if file.is_file() else 404, body=file.read_bytes() if file.is_file() else b'', content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
    context = browser.new_context(viewport={'width':1280,'height':820},locale='zh-TW',service_workers='block')
    context.route('https://tim12332000.github.io/pokesurvivor/**',route_file)
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    def start(page):
        page.goto(URL,wait_until='domcontentloaded')
        page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
        page.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
    start(page)
    report=page.evaluate(r'''() => {
      const assert=(ok,msg)=>{if(!ok)throw Error(msg);},I=G.Icons,S=G.SharinganIcons,pl=G.Game.player,id='naruto-sharingan',generic='move:'+id;
      assert(S,'Missing evolving eye icon runtime');
      const before=[I.url('heart'),I.url('move:naruto-kunai')];
      const urls=[],pixels=[];
      for(let lv=1;lv<=5;lv++){
        const key=S.key(lv),def=I.UI[key];assert(key==='sharingan-'+lv&&def,'Missing stage '+lv);
        assert(def.rows.length===64&&def.rows.every(row=>row.length===64),'Eye must use 64 by 64 cached source rows');
        assert(def.rows.every(row=>/^[.krd]+$/.test(row)),'Circular iris contains sclera or a non-red eye rim');
        for(let y=0;y<64;y++)for(let x=0;x<64;x++){
          const radius=Math.hypot(x-31.5,y-31.5)/32,pixel=def.rows[y][x];
          if(radius>.94)assert(pixel==='.' ,'Iris has an eyelid outside the circle');
          if(radius<.88)assert(pixel!=='.','Iris has a transparent gap inside the red disc');
        }
        urls.push(I.url(key));pixels.push(I.canvas(key).toDataURL());
      }
      assert(new Set(urls).size===5&&new Set(pixels).size===5,'Stages reused identical URL or canvas pixels');
      assert(S.key(-3)==='sharingan-1'&&S.key(9)==='sharingan-5','Stage key did not clamp');
      assert(S.forMove({id,lvl:4})==='sharingan-4'&&S.forMove({id:'naruto-kunai',lvl:5})==='move:naruto-kunai','Per-move stage resolver changed unrelated skills');
      G.Combat.clearFields();pl.moves=[];pl.slots=[];pl.bind={};pl.active=0;pl.dead=false;pl.hp=pl.maxHp;
      pl.addMove('naruto-kunai');pl.addMove('naruto-fireball');pl.level=6;
      assert(I.url(generic)===urls[0],'Unlearned Sharingan did not default to one tomoe');
      const card=G.LevelUp.offer(pl,100).find(c=>c.key==='new:'+id);assert(card?.icon==='sharingan-1','New Sharingan card must preview stage 1');card.apply(pl);
      const learned=pl.moves.find(m=>m.id===id);
      for(let lv=1;lv<=5;lv++){
        assert(learned.lvl===lv&&I.url(generic)===urls[lv-1],'Generic icon URL remained cached at previous stage '+lv);
        assert(I.canvas(generic).toDataURL()===pixels[lv-1],'Generic icon canvas did not evolve '+lv);
        const a=document.createElement('canvas'),b=document.createElement('canvas');a.width=b.width=a.height=b.height=64;
        I.draw(a.getContext('2d'),generic,0,0,64);I.draw(b.getContext('2d'),S.key(lv),0,0,64);
        assert(a.toDataURL()===b.toDataURL(),'Canvas HUD draw did not resolve current stage '+lv);
        assert(I.html(generic,32).includes(urls[lv-1]),'DOM icon did not resolve current stage '+lv);
        assert(I.html(generic,24).includes('width="24" height="24"'),'Higher-resolution eye enlarged the requested UI size');
        if(lv<5){const up=G.LevelUp.offer(pl,100).find(c=>c.key==='up:'+id);assert(up?.icon===S.key(lv+1),'Upgrade card must preview next stage '+(lv+1));G.Moves.levelUp(learned);}
      }
      pl.dead=true;pl.hp=0;assert(I.url(generic)===urls[4],'Death summary lost evolved eye icon');pl.dead=false;pl.hp=pl.maxHp;
      assert(I.url('heart')===before[0]&&I.url('move:naruto-kunai')===before[1],'Unrelated icon cache changed');
      const oldMoves=pl.moves;pl.moves=[];assert(I.url(generic)===urls[0],'New-run empty loadout retained stage 5');pl.moves=oldMoves;
      return {art:'five unique 64x64 source eye maps, rendered at requested UI size',dynamic:'generic URL, canvas, HTML and HUD draw evolve through all five levels; death retains stage',cards:'new stage 1; upgrade cards preview next stage',regression:'unrelated move and heart unchanged; empty loadout defaults stage 1'};
    }''')
    # Show and click a real upgrade card while the learned skill is still stage 4.
    page.evaluate(r'''() => {
      const pl=G.Game.player,m=pl.moves.find(m=>m.id==='naruto-sharingan');Object.assign(m,G.Moves.instance(m.id,4));
      const card=G.LevelUp.offer(pl,100).find(c=>c.key==='up:'+m.id);
      G.RunUI.showLevelUp(7,[card],picked=>picked.apply(pl));
    }''')
    card=page.locator('#cards .card').first
    assert card.locator('img').get_attribute('src') == page.evaluate("G.Icons.url('sharingan-5')"),'Rendered card did not show stage 5 preview'
    page.screenshot(path=str(ROOT/'.omx/sharingan-icons-next-card.png'),animations='disabled')
    card.click();assert page.evaluate("G.Game.player.moves.find(m=>m.id==='naruto-sharingan').lvl===5")
    capture=r'''() => {
      const pl=G.Game.player;G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();G.FX.clear();
      let m=pl.moves.find(m=>m.id==='naruto-sharingan');if(!m){pl.addMove('naruto-sharingan');m=pl.moves.find(m=>m.id==='naruto-sharingan');}
      Object.assign(m,G.Moves.instance(m.id,5));G.Combat.updateFields(.01);
      document.getElementById('scr-pause').style.visibility='hidden';
      window.eyeHudCalls=[];window.eyeHudDraw=G.Icons.draw;
      G.Icons.draw=function(ctx,name,...args){if(name==='move:naruto-sharingan'||name.startsWith('sharingan-'))window.eyeHudCalls.push(G.Icons.url(name));return window.eyeHudDraw.call(this,ctx,name,...args);};
    }'''
    page.evaluate(capture);page.wait_for_timeout(100)
    assert page.evaluate("window.eyeHudCalls.length>0&&window.eyeHudCalls.every(u=>u===G.Icons.url('sharingan-5'))"),'Actual HUD did not render evolved eye'
    page.screenshot(path=str(ROOT/'.omx/sharingan-icons-desktop.png'),animations='disabled')
    page.evaluate('() => {G.Icons.draw=window.eyeHudDraw;}')
    mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='zh-TW',service_workers='block')
    mobile.route('https://tim12332000.github.io/pokesurvivor/**',route_file)
    phone=mobile.new_page();phone.on('pageerror',lambda e:errors.append(str(e)));start(phone);phone.evaluate(capture);phone.wait_for_timeout(100)
    assert phone.evaluate("window.eyeHudCalls.length>0&&window.eyeHudCalls.every(u=>u===G.Icons.url('sharingan-5'))"),'Mobile HUD did not render evolved eye'
    phone.screenshot(path=str(ROOT/'.omx/sharingan-icons-mobile.png'),animations='disabled');phone.evaluate('() => {G.Icons.draw=window.eyeHudDraw;}')
    page.evaluate(r'''() => {
      const cv=document.createElement('canvas');cv.id='eye-review';cv.width=760;cv.height=190;
      cv.style.cssText='position:fixed;left:0;top:0;z-index:30000;max-width:100vw;height:auto';
      const ctx=cv.getContext('2d');ctx.fillStyle='#142036';ctx.fillRect(0,0,cv.width,cv.height);ctx.fillStyle='#fff';ctx.font='16px sans-serif';
      for(let lv=1;lv<=5;lv++){const x=12+(lv-1)*150;G.Icons.draw(ctx,'sharingan-'+lv,x,10,128);ctx.fillText('Lv.'+lv,x+44,165);}
      document.body.append(cv);
    }''')
    page.locator('#eye-review').screenshot(path=str(ROOT/'.omx/sharingan-icons-review.png'))
    assert not errors,errors
    print(json.dumps({'ok':True,'checks':report,'screenshots':['sharingan-icons-review.png','sharingan-icons-next-card.png','sharingan-icons-desktop.png','sharingan-icons-mobile.png']},ensure_ascii=False),flush=True)
    browser.close()
