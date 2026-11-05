"""Catalog coherence, playable UI and legacy saves through actual entry pages."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME

URL = os.environ.get('CATALOG_URL','http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW')
OUT = Path(__file__).resolve().parents[1] / '.omx/state/catalog-refactor'
CHECK = '''()=>{
  const assert=(ok,message)=>{if(!ok)throw Error(message)},C=G.Catalog;
  const expected=G.Naruto.availableDexes,ids=records=>records.map(record=>record.dex);
  assert(JSON.stringify(ids(C.playable()))===JSON.stringify(expected),'playable order changed');
  assert(JSON.stringify(ids(C.starters()))===JSON.stringify(expected),'starter order changed');
  assert(C.all().length===G.DEX.length && C.all().length>expected.length,'complete catalog was truncated');
  assert(G.STARTERS.length===Object.keys(G.STARTER_BY).length,'starter map/list drift');
  assert(G.DEX.every(mon=>G.DEX_BY[mon.dex]===mon),'character map/list identity drift');
  assert(G.STARTERS.every(starter=>G.STARTER_BY[starter.dex]===starter),'starter map/list identity drift');
  const cards=[...document.querySelectorAll('[data-quick-naruto]')].map(el=>+el.dataset.quickNaruto);
  assert(JSON.stringify(cards)===JSON.stringify(expected),'visible ninja picker changed');
  assert(document.querySelectorAll('#rk-dl option').length===expected.length,'ranking roster leaked hidden records');
  for(let i=0;i<20;i++)assert(C.isPlayable(G.personalityResult({valiente:i%3,leal:i%4}).dex),'personality selected hidden starter');
  assert(G.DB.save.partner===30001 && G.DB.save.owned[25]?.at===1 && G.DB.save.shiny[25]?.at===2,'legacy save was lost');
  for(const go of ['dex','gacha'])assert(document.querySelector('[data-go='+go+']').hidden,'closed screen reopened');
  assert(G.AchDefs.LIST.filter(a=>a.dex).length===87,'legend achievements changed');
  for(const policy of [null,[25,30001]]){
    C.restrictTo(policy);G.DB.save.partner=G.DB.save.starter=25;G.Flow.goMenu();
    assert(document.querySelector('.launch-detail').classList.contains('launch-fallback'),'non-Naruto fallback missing');
    assert(!document.querySelector('.partner-card').classList.contains('hidden'),'fallback partner card hidden');
  }
  C.restrictTo(expected);G.DB.save.partner=G.DB.save.starter=30001;G.Flow.goMenu();
  return {characters:C.all().length,playable:ids(C.playable()),starters:C.starters().length,legacySave:true,coherent:true};
}'''

if __name__ == '__main__':
    report={}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=CHROME,headless=True)
        for mobile in (False,True):
            context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},
                                       is_mobile=mobile,has_touch=mobile,service_workers='block')
            context.add_init_script("""localStorage.setItem('ps.sandbox.digimon.v1',JSON.stringify({
              partner:25,starter:25,owned:{25:{at:1,from:'rescue'}},shiny:{25:{at:2,from:'wild'}}}));""")
            page=context.new_page();errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(URL+('' if mobile else '&layout=wide'))
            page.wait_for_function("window.G?.NarutoAssets && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
            result=page.evaluate(CHECK)
            page.locator('#scr-menu [data-go="upgrades"]').click()
            assert page.locator('#upg-mon option').count()==11
            assert page.locator('#upg-mon').evaluate("el=>[...el.options].every(o=>G.Catalog.isPlayable(o.value))")
            assert not errors,errors
            report['mobile' if mobile else 'desktop']=result
            context.close()
        # The ordinary source entry is intentionally unrestricted.
        context=browser.new_context(service_workers='block')
        context.route('**/js/core/firebase-config.js*',lambda route:route.fulfill(content_type='application/javascript',body='G.FIREBASE_CONFIG=null;'))
        page=context.new_page();errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:8004/dev.html?lang=zh-TW')
        page.wait_for_function("window.G?.Flow && document.getElementById('boot').classList.contains('hidden')")
        normal=page.evaluate('''()=>({characters:G.Catalog.all().length,playable:G.Catalog.playable().length,
          starters:G.Catalog.starters().length,legacy:G.DEX.length})''')
        assert normal=={'characters':966,'playable':966,'starters':29,'legacy':966},normal
        assert not errors,errors
        report['unrestricted']=normal
        browser.close()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'browser-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
