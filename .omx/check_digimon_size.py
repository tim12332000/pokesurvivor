from playwright.sync_api import sync_playwright
import json

URL='http://127.0.0.1:8002/.omx/digimon.html?lang=zh-TW&v=large-forms'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(locale='zh-TW',viewport={'width':1580,'height':900})
    page=context.new_page()
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(URL)
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.wait_for_function('[...G.Digimon.records.values()].every(r=>r.ready)')
    results=page.evaluate('''() => {
      const canvas=document.createElement('canvas');canvas.width=canvas.height=640;
      const ctx=canvas.getContext('2d',{willReadFrequently:true});
      const bounds=() => {
        const data=ctx.getImageData(0,0,640,640).data;let x0=640,y0=640,x1=-1,y1=-1;
        for(let y=0;y<640;y++)for(let x=0;x<640;x++)if(data[(y*640+x)*4+3]>0){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}
        return {width:x1-x0+1,height:y1-y0+1,bottom:y1};
      };
      const lines=[[20001,20101,20102,20103,20201],[20002,20111,20112,20113],
        [20003,20121,20122,20123],[20004,20131,20132,20133],
        [20005,20141,20142,20143],[20006,20151,20152,20153],
        [20007,20161,20162,20163],[20008,20172,20173]];
      return lines.map(line=>line.map(dex=>{
        ctx.clearRect(0,0,640,640);const actor=new G.Sprites.Animator(dex,1);actor.dir=1;actor.draw(ctx,320,560);
        if(actor.scale!==1)throw Error('Temporary visual scale leaked');
        const sprite=bounds();ctx.clearRect(0,0,640,640);G.Sprites.drawShadow(ctx,dex,320,560);
        return {dex,name:G.T(G.DEX_BY[dex].name),...sprite,shadowWidth:bounds().width,bodyHeight:G.Sprites.bodyHeight(dex)};
      }));
    }''')
    for line in results:
        assert all(a['height']<b['height'] for a,b in zip(line,line[1:])),line
        assert all(a['shadowWidth']<b['shadowWidth'] for a,b in zip(line,line[1:])),line
        assert all(abs(r['bottom']-560)<=6 for r in line),line
    assert results[0][0]['height']*1.8 <= results[0][3]['height'] <= results[0][0]['height']*2.4
    # Use the actual renderer for a side-by-side stage comparison.
    page.evaluate('''() => {
      const overlay=document.createElement('div');overlay.id='size-comparison';
      overlay.style.cssText='position:fixed;inset:0;z-index:100000;background:#102b3d;overflow:auto;padding:20px;color:white';
      overlay.innerHTML='<h2 style="font:24px sans-serif;margin:0 0 10px">進化體型對照 · 相同地圖縮放</h2>';
      const cv=document.createElement('canvas');cv.width=1500;cv.height=430;
      const ctx=cv.getContext('2d');ctx.font='18px sans-serif';ctx.textAlign='center';
      [20001,20101,20102,20103,20201].forEach((dex,i)=>{
        const x=150+i*295;const actor=new G.Sprites.Animator(dex,1);actor.dir=1;
        G.Sprites.drawShadow(ctx,dex,x,325);actor.draw(ctx,x,325);
        ctx.fillStyle='#ffd23f';ctx.fillText(G.T(G.DEX_BY[dex].name),x,380);
        ctx.fillStyle='#b9cbf0';ctx.fillText('×'+G.Digimon.sizeOf(dex),x,410);
      });overlay.append(cv);document.body.append(overlay);
    }''')
    page.locator('#size-comparison').screenshot(path='.omx/digimon-size-comparison.png')
    page.evaluate('document.getElementById("size-comparison").remove()')
    page.locator('[data-evo-tab="3"]').click()
    page.screenshot(path='.omx/digimon-large-picker.png',animations='disabled')
    page.locator('[data-digimon="20103"]').click()
    page.locator('#scr-menu [data-go="play"]').click()
    page.wait_for_function('G.Game.state==="playing"')
    page.wait_for_timeout(1000)
    assert page.evaluate('G.Game.player.bodyH===G.Sprites.bodyHeight(G.Game.player.dex)')
    page.screenshot(path='.omx/digimon-large-gameplay.png',animations='disabled')
    assert not errors,errors
    context.close()
    mobile=browser.new_context(locale='zh-TW',viewport={'width':844,'height':390},is_mobile=True,has_touch=True)
    page=mobile.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(URL);page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.locator('[data-evo-tab="4"]').click();page.locator('[data-digimon="20201"]').click()
    page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.state==="playing"')
    page.wait_for_timeout(1200)
    framing=page.evaluate('''() => {
      const pl=G.Game.player,cam=G.Camera;
      const foot=(pl.y-cam.top())*cam.scale;
      return {top:foot-pl.bodyH*cam.scale,foot,viewport:innerHeight};
    }''')
    assert framing['top']>=60,framing
    assert framing['foot']<=framing['viewport']-80,framing
    page.screenshot(path='.omx/digimon-large-mobile.png',animations='disabled')
    assert not errors,errors
    print(json.dumps({'world_size_bounds':results,'mobile_framing':framing,'page_errors':errors},ensure_ascii=True))
    browser.close()
