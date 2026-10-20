"""Render current four-direction poses using the game's own sprite renderer."""
from pathlib import Path
from urllib.parse import unquote,urlsplit
import mimetypes
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(viewport={'width':900,'height':900},service_workers='block')
    def route(request):
        f=ROOT/unquote(urlsplit(request.request.url).path).removeprefix('/pokesurvivor/')
        request.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'',content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
    context.route('https://review.local/pokesurvivor/**',route)
    page=context.new_page();page.goto('https://review.local/pokesurvivor/.omx/digimon.html?lang=zh-TW')
    page.wait_for_function('window.G?.Naruto&&[...G.Naruto.records.values()].every(r=>r.ready)')
    for hero,dex in [('naruto',30001),('sasuke',30002)]:
        page.evaluate('''dex=>{
          document.getElementById('baseline-sheet')?.remove();
          const cv=document.createElement('canvas');cv.id='baseline-sheet';cv.width=cv.height=512;
          cv.style.cssText='position:fixed;left:0;top:0;z-index:30000';document.body.append(cv);
          const ctx=cv.getContext('2d');ctx.fillStyle='#17243a';ctx.fillRect(0,0,512,512);
          const labels=['Down','Up','Left','Right'],dirs=[0,4,6,2];
          for(let row=0;row<4;row++)for(let col=0;col<4;col++){
            const anim=new G.Sprites.Animator(dex);anim.cur='Walk';anim.dir=dirs[row];anim.frame=col;
            anim.draw(ctx,64+col*128,100+row*128);ctx.fillStyle='#dce8ff';ctx.font='12px sans-serif';
            ctx.fillText(labels[row]+' '+(col+1),38+col*128,120+row*128);
          }
        }''',dex)
        page.locator('#baseline-sheet').screenshot(path=str(ROOT/f'art-review/previews/{hero}-original-movement.png'))
    browser.close()
