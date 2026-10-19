"""Render the code-native black/silver Fuma on desktop and true mobile."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright
import json
import mimetypes

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    def proxy(route):
        f=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
        route.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'',content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
    def start(mobile=False):
        c=browser.new_context(viewport={'width':390 if mobile else 1280,'height':844 if mobile else 820},is_mobile=mobile,has_touch=mobile,service_workers='block')
        c.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
        page=c.new_page();page.goto(URL,wait_until='domcontentloaded')
        page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
        page.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
        return page
    page=start()
    report=page.evaluate(r'''() => {
      const assert=(ok,msg)=>{if(!ok)throw Error(msg);},id='naruto-fuma-shuriken',pal='naruto-fuma-steel';
      const d=G.Moves.BY_ID[id],s=G.VFX.SHAPES[id],cv=G.VFX.sprite(id,pal),ctx=cv.getContext('2d');
      assert(s.w===35&&s.h===35&&s.spin,'Shape geometry/spin changed');
      assert(d.digiVis.pal===pal&&d.digiVis.projScale===.9&&d.size===32,'Palette/scale mismatch');
      assert(d.speed===460&&d.life===4&&d.boom===.65&&d.cd===1.6&&d.dmg===34&&d.count===1&&d.fumaReturn,'Appearance edit changed mechanics');
      assert(G.VFX.PAL.steel.join(',')==='#232d38,#56667a,#8c9caf,#cad6e2,#ffffff','Global steel palette changed');
      const pixel=(x,y)=>[...ctx.getImageData(x,y,1,1).data];
      assert(pixel(17,17)[3]===255&&pixel(16,16)[0]>220,'Central rivet missing');
      assert(pixel(0,0)[3]===0&&pixel(34,34)[3]===0,'Transparent corners lost');
      for(const [x,y] of [[31,6],[28,31],[3,28],[6,3]])assert(pixel(x,y)[3]===255,'Missing recurved blade tip');
      const data=ctx.getImageData(0,0,35,35).data;let dark=0,silver=0;
      for(let i=0;i<data.length;i+=4)if(data[i+3]){if(data[i]<80)dark++;else silver++;}
      assert(dark>silver*2&&silver>35,'Black blade body / silver bevel ratio wrong');
      assert(G.VFX.sprite(id,pal)===cv&&G.VFX.sprite(id,'steel')!==cv,'Unique palette cache alias');
      return {darkPixels:dark,silverPixels:silver,shape:'four recurved black blades / silver cutting edges / tiny center rivet',mechanics:'unchanged'};
    }''')
    capture=r'''() => {
      G.EnemyMgr.clear();G.Projectiles.clear();G.Combat.clearFields();const pl=G.Game.player;pl.aim=0;
      G.DigimonSkills.cast(pl,G.Moves.instance('naruto-fuma-shuriken'));G.Combat.updateFields(.21);
      const p=G.Projectiles.all()[0];p.x=pl.x+150;p.y=pl.y-40;p.t=.95;
      G.Camera.x=pl.x;G.Camera.y=pl.y;document.getElementById('scr-pause').style.visibility='hidden';
    }'''
    page.evaluate(capture);page.wait_for_timeout(60);page.screenshot(path=str(ROOT/'.omx/fuma-reference-desktop.png'))
    phone=start(True);phone.evaluate(capture);phone.wait_for_timeout(60);phone.screenshot(path=str(ROOT/'.omx/fuma-reference-mobile.png'))
    page.evaluate(r'''() => {
      const cv=document.createElement('canvas');cv.width=800;cv.height=400;cv.id='fuma-review';cv.style.cssText='position:fixed;left:0;top:0;z-index:999999;width:800px;height:400px';
      const ctx=cv.getContext('2d');ctx.fillStyle='#d0d2d4';ctx.fillRect(0,0,800,200);ctx.fillStyle='#3e6334';ctx.fillRect(0,200,800,200);
      for(let i=0;i<4;i++)for(let row=0;row<2;row++){
        const x=100+i*200,y=100+row*200;G.VFX.draw(ctx,'naruto-fuma-shuriken','naruto-fuma-steel',x,y,{angle:i*Math.PI/8,scale:1.9});
        ctx.fillStyle=row?'#fff':'#17202b';ctx.font='14px sans-serif';ctx.fillText((i*22.5)+' deg',x-25,y+86);
      }
      document.body.append(cv);
    }''')
    page.locator('#fuma-review').screenshot(path=str(ROOT/'.omx/fuma-reference-review.png'))
    print(json.dumps({'ok':True,'checks':report}))
    browser.close()
