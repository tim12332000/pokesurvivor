"""Read-only design study of native entry; writes evidence only beside this file."""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:8337/.omx/digimon.html?lang=zh-TW&hero='
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

def boot(browser, hero, trial=False):
    context = browser.new_context(viewport={'width':1280,'height':900},service_workers='block')
    page=context.new_page()
    page.goto(URL+hero+'&layout=wide'+('&startLevel=20' if trial else ''))
    frame=None
    for _ in range(200):
        for item in page.frames:
            if item.evaluate("typeof G==='object'&&!!G.NarutoAssets"):
                frame=item;break
        if frame:break
        page.wait_for_timeout(100)
    assert frame,'Game frame not loaded'
    frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if frame.locator('#tap-start').is_visible():frame.locator('#tap-start').click()
    frame.locator('#scr-menu [data-go="play"]').click()
    frame.wait_for_function("G.Game.state==='playing'&&G.Game.player")
    page.study_frame=frame
    return context,page

def snapshot(page):
    return page.study_frame.evaluate("""()=>{const p=G.Game.player;return {state:G.Game.state,time:G.Game.st.time,
      level:p.level,hp:p.hp,maxHp:p.maxHp,x:p.x,y:p.y,xp:p.xp,xpNext:p.xpNext,kills:p.kills,
      slots:p.slots.map(g=>g.map(m=>m.id)),maxMoves:p.maxMoves,quantity:p.quantityPicks||0,
      moves:p.moves.map(m=>({id:m.id,lvl:m.lvl,passive:m.passive,autoCast:m.autoCast,cd:m.cd,t:m.t,dealt:m.dealt})),
      cards:G.LevelUp.offer(p,100).map(c=>({key:c.key,title:c.title,desc:c.desc,guaranteed:!!c.guaranteed}))}}""")

def main():
    report={'normal':{},'trial':{},'limits':['A sixty-second desktop movement sample is not a whole-run balance test.','The level20 URL grants eligible moves at rank1 without nineteen earned card picks.']}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME,headless=True)
        context,page=boot(browser,'jjk-yuta')
        start=time.monotonic();report['normal']['before']=snapshot(page);choices=[]
        page.screenshot(path=str(OUT/'native-yuta-start.png'))
        for step in range(60):
            state=page.study_frame.evaluate('G.Game.state')
            if state=='over':break
            if state=='levelup':
                cards=page.study_frame.locator('#cards .card');text=cards.all_text_contents();choices.append(text)
                preferred=next((i for i,t in enumerate(text) if '里香' in t or '刀斬' in t),0)
                cards.nth(preferred).click()
            if state=='playing':
                key=['KeyD','KeyS','KeyA','KeyW'][(step//5)%4]
                page.keyboard.down(key);page.wait_for_timeout(900);page.keyboard.up(key)
            else:page.wait_for_timeout(900)
            if step==29:page.screenshot(path=str(OUT/'native-yuta-middle.png'))
        report['normal'].update(after=snapshot(page),wallSeconds=time.monotonic()-start,choices=choices)
        page.screenshot(path=str(OUT/'native-yuta-end.png'));context.close()
        for hero in ['jjk-yuta','jjk-ryu','jjk-uro']:
            context,page=boot(browser,hero,True)
            report['trial'][hero]=snapshot(page);page.screenshot(path=str(OUT/(hero+'-trial20.png')))
            context.close()
        browser.close()
    (OUT/'runtime-study.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'normal':{k:v for k,v in report['normal'].items() if k!='choices'},'trialLevels':{k:v['level'] for k,v in report['trial'].items()}},ensure_ascii=True))

if __name__=='__main__':main()
