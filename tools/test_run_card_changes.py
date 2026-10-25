"""Native run-card selection and application acceptance at desktop/mobile sizes."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

OUT = Path(__file__).resolve().parents[1] / '.omx/state/run-card-changes'
CHECK = r"""() => {
 const A=Acceptance,p=A.p();A.pause();
 const stats=G.LevelUp.STATS;
 A.assert(!stats.some(s=>['hp','rgn'].includes(s.id)),'removed cards still registered');
 const candidates=G.LevelUp.offer(p,1000);
 A.assert(!candidates.some(c=>['stat:hp','stat:rgn'].includes(c.key)),'removed cards offered');
 const heal=candidates.find(c=>c.key==='stat:heal'),giant=candidates.find(c=>c.key==='stat:giant');
 A.assert(heal?.title==='軍糧丸'&&heal.icon==='rationPill','ration card title/icon');
 A.assert(giant?.title==='倍化之術','size card title');
 A.assert(G.Icons.url('rationPill')!==G.Icons.url('berry'),'ration icon reuses berry');
 p.hp=p.maxHp*.1;const max=p.maxHp;heal.apply(p);
 A.assert(Math.abs(p.hp-max*.55)<1e-7&&p.maxHp===max,'ration must heal45% max');
 const before={scale:p.anim.scale,r:p.r,bodyH:p.bodyH,max:p.maxHp,speed:p.spdMul,cd:p.cdMul};
 giant.apply(p);
 for(const [value,expected]of [[p.anim.scale,before.scale*1.25],[p.r,before.r*1.25],[p.bodyH,before.bodyH*1.25],
   [p.maxHp,before.max*1.25],[p.hp,max*.8],[p.spdMul,before.speed*.9],[p.cdMul,before.cd/.9]])
   A.assert(Math.abs(value-expected)<1e-7,'size effect changed '+value+' != '+expected);
 const rows=G.RunAttributes.rows(p);
 A.assert(rows.some(r=>r.id==='giant'&&r.text.startsWith('倍化之術')),'renamed HUD missing');
 const predicate={id:'acceptanceIneligible',icon:'star',title:'hidden',desc:'',eligible:()=>false,apply:()=>{}};
 stats.push(predicate);try{A.assert(!G.LevelUp.offer(p,1000).some(c=>c.key==='stat:acceptanceIneligible'),'eligibility ignored')}
 finally{stats.splice(stats.indexOf(predicate),1)}
 G.RunUI.showLevelUp(p.level,[heal,giant,candidates.find(c=>c.key==='stat:atk')],card=>card.apply(p));
 return {offered:candidates.map(c=>c.key),heal:{title:heal.title,icon:heal.icon,max,hp:max*.55},giant:{title:giant.title,rows},before};
}"""

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 report={'errors':[],'viewports':{}}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=CHROME,headless=True)
  for name,viewport,mobile in [('desktop',{'width':1200,'height':900},False),('mobile',{'width':390,'height':844},True)]:
   context=browser.new_context(viewport=viewport,is_mobile=mobile,has_touch=mobile,service_workers='block')
   outer=context.new_page();outer.on('pageerror',lambda err:report['errors'].append(str(err)))
   outer.goto(URL);page=game_frame(outer);enter(page)
   report['viewports'][name]=page.evaluate(CHECK)
   page.wait_for_timeout(100)
   assert page.locator('#cards .card').count()==3
   assert '軍糧丸' in page.locator('#cards').inner_text()
   assert '倍化之術' in page.locator('#cards').inner_text()
   report['viewports'][name]['overflow']=page.evaluate('document.documentElement.scrollWidth>innerWidth')
   assert not report['viewports'][name]['overflow']
   outer.screenshot(path=str(OUT/f'{name}-selection.png'))
   page.locator('#cards .card').first.click()
   assert page.evaluate('Acceptance.p().statsTaken.heal')==2
   context.close()
  browser.close()
 assert not report['errors'],report['errors']
 (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
