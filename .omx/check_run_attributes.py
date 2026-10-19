"""Acquire real cards and verify live HUD text, portrait layout and run reset."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import mimetypes
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(locale='zh-TW',viewport={'width':1280,'height':800},is_mobile=True,has_touch=True,service_workers='block')
    def proxy(route):
        f=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
        route.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'',content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
    context.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW')
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
    assert page.evaluate('G.RunAttributes.rows(G.Game.player).length===0')
    page.evaluate('''() => {
      const original=G.LevelUp.offer;
      window.requestedCard='atk';
      G.LevelUp.offer=(pl,n=3)=>{
        for(let i=0;i<100;i++){
          const cards=original(pl,100),card=cards.find(c=>c.key==='stat:'+window.requestedCard);
          if(card)return [card,...cards.filter(c=>c!==card)].slice(0,n);
        }
        throw Error('Missing card '+window.requestedCard);
      };
    }''')
    for card in ['atk','atk','quantity','lifesteal','percentHealthDamage','percentHealthDamage']:
        page.evaluate("id=>{window.requestedCard=id;if(G.Game.state==='paused')G.Game.togglePause();G.Game.debugLevelUp()}",card)
        page.locator('#scr-levelup').wait_for(state='visible')
        page.locator('#cards .card').first.click()
        page.evaluate("if(G.Game.state==='playing')G.Game.togglePause()")
    rows=page.evaluate('G.RunAttributes.rows(G.Game.player)')
    assert [r['text'] for r in rows]==['攻擊 +21%','數量 +1','吸血 1%','生命剝奪 2%'],rows
    page.evaluate("G.UI.hide('scr-pause');G.EnemyMgr.clear()")
    page.wait_for_timeout(4500)
    for width,height in [(1280,800),(390,844),(360,640)]:
        page.set_viewport_size({'width':width,'height':height})
        drawn=page.evaluate('''({w,h})=>{
          const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
          const ctx=canvas.getContext('2d'),texts=[],fill=ctx.fillText;
          ctx.fillText=function(text,x,y,...rest){texts.push({text,x,y});return fill.call(this,text,x,y,...rest)};
          G.HUD.draw(ctx,w,h,G.Game.player,{time:0});
          return texts.filter(t=>t.text==='已獲得屬性'||t.text==='生命剝奪 2%');
        }''',{'w':width,'h':height})
        assert len(drawn)==2 and all(t['x']>width/2 and 0<t['y']<height/2 for t in drawn),drawn
        page.wait_for_timeout(100)
        page.screenshot(path=str(ROOT/f'.omx/run-attributes-{width}.png'))
    # All card types render; one-off healing never becomes a permanent attribute.
    assert page.evaluate('''()=>{
      const pl=G.Game.player,save={...pl.statsTaken},slots=pl.slots;
      for(const s of G.LevelUp.STATS)pl.statsTaken[s.id]=1;
      const rows=G.RunAttributes.rows(pl);
      // Five skills plus all acquired attributes must fit a short portrait screen.
      pl.slots=Array.from({length:5},(_,i)=>slots[i%slots.length]);
      const canvas=document.createElement('canvas');canvas.width=360;canvas.height=640;
      const original=G.HUD.roundRect;let panel;
      G.HUD.roundRect=function(ctx,x,y,w,h,r){panel={x,y,w,h};return original(ctx,x,y,w,h,r)};
      try{G.HUD.draw(canvas.getContext('2d'),360,640,pl,{time:0});}
      finally{G.HUD.roundRect=original;pl.statsTaken=save;pl.slots=slots;}
      return rows.length===11&&!rows.some(r=>r.id==='heal')&&panel.y+panel.h<=G.Touch.controlLayout(360,640,5).bar.y;
    }''')
    page.evaluate('G.Game.quit();G.Flow.goMenu();G.Flow.play();G.Game.togglePause()')
    assert page.evaluate('G.RunAttributes.rows(G.Game.player).length===0')
    assert not errors,errors
    print(json.dumps({'ok':True,'actualCards':rows,'viewports':[1280,390,360],'freshRun':'empty','errors':errors},ensure_ascii=False))
    browser.close()
