"""Shikamaru production entry and read-only art sampling evidence."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'art-review/shikamaru/art-qa';OUT.mkdir(parents=True,exist_ok=True)
URL='http://127.0.0.1:8348/.omx/digimon.html?lang=zh-TW'
def main():
 report={}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
  for label,viewport in [('desktop',{'width':1280,'height':850}),('mobile390',{'width':390,'height':844}),('mobile360',{'width':360,'height':800})]:
   context=browser.new_context(viewport=viewport,is_mobile=label!='desktop',has_touch=label!='desktop',service_workers='block');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(URL+('&layout=wide' if label=='desktop' else ''),wait_until='domcontentloaded');frame=page.main_frame
   for _ in range(300):
    match=next((f for f in page.frames if f.evaluate("typeof G==='object'&&!!G.NarutoShikamaru")),None)
    if match:frame=match;break
    page.wait_for_timeout(100)
   frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
   if frame.locator('#tap-start').is_visible():frame.locator('#tap-start').click()
   frame.locator('[data-quick-naruto="30017"]').click();frame.wait_for_function('G.NarutoAssets.ready(30017)')
   page.screenshot(path=str(OUT/f'{label}-selection.png'))
   frame.locator('#scr-menu [data-go="play"]').click();frame.wait_for_function("G.Game.player?.dex===30017&&G.Game.state==='playing'")
   page.wait_for_timeout(1000);page.screenshot(path=str(OUT/f'{label}-normal-entry.png'))
   report[label]={'errors':errors,'entry':frame.evaluate("({dex:G.Game.player.dex,level:G.Game.player.level,ready:G.ShikamaruArt.loaded})"),'poses':frame.evaluate("() => { const art=G.ShikamaruArt;return ['down','up','right','left'].map(dir=>({dir,walk:[0,.1].map(t=>art.sample('walk',t,dir).key),cast:[0,.2,.4,.6].map(t=>art.sample('cast',t,dir,{kind:'shadow',duration:.65}).key)}))}")}
   if label=='desktop':
    for key in ['KeyD','KeyS','KeyA','KeyW']:
     page.keyboard.down(key);page.wait_for_timeout(250);page.screenshot(path=str(OUT/f'{label}-input-{key}.png'));page.keyboard.up(key)
   context.close()
  browser.close()
 (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
