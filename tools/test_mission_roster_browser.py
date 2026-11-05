"""Verify roster-aware mission repair, real reward claiming and saved data."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME

URL = os.environ.get('MISSION_ROSTER_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW')
OUT = Path(__file__).resolve().parents[1] / '.omx/state/mission-roster'
SETUP = '''()=>{
  const assert=(ok,message)=>{if(!ok)throw Error(message)},s=G.DB.save;
  const roster=G.Catalog.playable(),types=new Set(roster.flatMap(mon=>mon.types));
  assert(roster.length===11 && roster.every(mon=>mon.naruto),'wrong picker roster');
  assert([30013,30014,30015].every(dex=>roster.some(mon=>mon.dex===dex)),'Sendai trio missing from playable roster');
  assert(G.Catalog.all().length===G.DEX.length && G.DEX.length>roster.length,'complete catalog was filtered');
  for(let created=0;created<500;created++){
    const fresh={created};G.Progress.ensure(fresh);
    for(const m of [...fresh.missions.daily,...fresh.missions.weekly]){
      assert(!['evolve','wevolve'].includes(m.id),'impossible evolution mission');
      assert(m.id!=='playType'||types.has(m.param),'impossible player-type mission');
    }
  }
  G.Progress.ensure(s);
  s.missions.rerolled=true;
  s.missions.daily=[{id:'playType',param:'water',goal:3,prog:1,claimed:false,told:false},
    {id:'evolve',goal:1,prog:0,claimed:false,told:false},
    {id:'evolve',goal:1,prog:1,claimed:false,told:true}];
  s.missions.weekly=[{id:'wevolve',goal:3,prog:1,claimed:false,told:false},
    {id:'wrift',goal:1,prog:0,claimed:false,told:false}];
  s.owned[25]={at:1,from:'rescue'};s.shiny[25]={at:2,from:'wild'};
  G.Progress.checkAch();
  const before={coins:s.coins,t1:s.tickets.t1};
  G.Progress.ensure(s);
  assert(types.has(s.missions.daily[0].param)&&s.missions.daily[0].prog===1,'type progress was lost');
  assert(s.missions.daily[1].id!=='evolve'&&s.missions.weekly[0].id!=='wevolve','unavailable mission not repaired');
  assert(s.missions.daily[2].id==='evolve'&&s.missions.daily[2].prog===1,'completed reward was removed');
  G.GoalsUI.open('missions');
  return before;
}'''

if __name__ == '__main__':
    report = {}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=CHROME,headless=True)
        for mobile in (False,True):
            context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},
                                       is_mobile=mobile,has_touch=mobile,service_workers='block')
            page=context.new_page();errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(URL+('' if mobile else '&layout=wide'))
            page.wait_for_function("window.G?.NarutoAssets && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
            before=page.evaluate(SETUP)
            page.locator('.mission.ready button').click()
            after=page.evaluate('({coins:G.DB.save.coins,t1:G.DB.save.tickets.t1,claimed:G.DB.save.missions.daily[2].claimed})')
            assert after == {'coins':before['coins']+250,'t1':before['t1']+3,'claimed':True},(before,after)
            page.evaluate('G.DB.commit()');page.reload()
            page.wait_for_function("window.G?.NarutoAssets && document.getElementById('boot').classList.contains('hidden')")
            saved=page.evaluate('''()=>({claimed:G.DB.save.missions.daily[2].claimed,rerolled:G.DB.save.missions.rerolled,
              owned:G.DB.save.owned[25].at,shiny:G.DB.save.shiny[25].at,types:G.Catalog.playable().flatMap(mon=>mon.types),
              repairedType:G.DB.save.missions.daily[0].param})''')
            assert saved['claimed'] and saved['rerolled'] and saved['owned']==1 and saved['shiny']==2,saved
            assert saved['repairedType'] in saved['types'],saved
            assert not errors,errors
            report['mobile' if mobile else 'desktop']={'generatedAccounts':500,'repairAndClaim':True,'saveRestored':True}
            context.close()
        browser.close()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
