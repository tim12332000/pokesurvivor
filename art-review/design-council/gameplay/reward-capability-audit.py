import json
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(__file__).resolve().parent
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
 rows=[]
 for hero in ['naruto','pain','kimimaro','temari','gaara','jjk-yuta']:
  c=b.new_context(service_workers='block');p=c.new_page();p.goto('http://127.0.0.1:8337/.omx/digimon.html?lang=zh-TW&layout=wide&startLevel=20&hero='+hero)
  p.wait_for_function("typeof G==='object'&&G.NarutoAssets&&document.getElementById('boot').classList.contains('hidden')")
  if p.locator('#tap-start').is_visible():p.locator('#tap-start').click()
  p.locator('#scr-menu [data-go="play"]').click();p.wait_for_function("G.Game.state==='playing'&&G.Game.player?.level===20")
  row=p.evaluate("""()=>{const p=G.Game.player,o=p.bondOptions();return {dex:p.dex,level:p.level,slots:p.slots.map(g=>g.map(m=>m.id)),moves:p.moves.map(m=>({id:m.id,passive:m.passive,autoCast:m.autoCast})),fusionOption:o?{mode:o.mode,loose:o.loose.map(m=>m.id),group:o.group?.map(m=>m.id)||null}:null}}""");row['hero']=hero;rows.append(row);c.close()
 b.close()
(out/'reward-capability-audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps([{'hero':r['hero'],'slots':len(r['slots']),'fusion':r['fusionOption'] is not None} for r in rows]))
