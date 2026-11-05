"""Independent gameplay observation and executable-prototype smoke/measurement."""
import json,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent/'evidence';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tools'))
from test_jujutsu import CHROME,frame_for

prototype_only='--prototype-only' in sys.argv
report={'gameplay':[],'prototype':{}}
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=CHROME,headless=True)
 for hero,query,duration in ([] if prototype_only else [('jjk-ryu','',32),('jjk-uro','&startLevel=20',12)]):
  context=browser.new_context(viewport={'width':1280,'height':900},service_workers='block');page=context.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto('http://127.0.0.1:8337/.omx/digimon.html?lang=zh-TW&hero='+hero+query)
  f=frame_for(page);f.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
  if f.locator('#tap-start').is_visible():f.locator('#tap-start').click()
  f.locator('#scr-menu [data-go="play"]').click();f.wait_for_function('G.Game.state==="playing"')
  observations=[];choices=[];start=time.perf_counter();key=None
  while time.perf_counter()-start<duration:
   current=f.evaluate("({state:G.Game.state,t:G.Game.st.time,level:G.Game.player.level,hp:G.Game.player.hp,kills:G.Game.player.kills,slots:G.Game.player.slots.length,moves:G.Game.player.moves.map(m=>({id:m.id,rank:m.lvl,t:m.t})),enemies:G.EnemyMgr.all().length})")
   observations.append(current)
   if current['state']=='over':break
   if current['state']=='levelup':
    cards=f.locator('#cards .card');choices.append(cards.all_text_contents());cards.first.click()
   next_key=['KeyD','KeyW','KeyA','KeyS'][int((time.perf_counter()-start)/4)%4]
   if key!=next_key:
    if key:page.keyboard.up(key)
    page.keyboard.down(next_key);key=next_key
   page.wait_for_timeout(350)
  if key:page.keyboard.up(key)
  page.screenshot(path=str(OUT/(hero+'-gameplay.png')))
  report['gameplay'].append({'hero':hero,'query':query,'wallSeconds':time.perf_counter()-start,'observation':'Native movement and first displayed upgrade card; no terrain/stat/enemy fixture changes. Level20 URL is a debug skill-unlock trial, not natural progression.','observations':observations,'displayedChoices':choices,'errors':errors})
  context.close()
 context=browser.new_context(viewport={'width':1280,'height':900});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8337/art-review/design-council/combat-vfx/prototype.html');page.wait_for_function('!!window.VFXDemo')
 for demo,at in [('beam',.74),('sky',.80),('slash',.47)]:
  page.evaluate('name=>VFXDemo.setDemo(name)',demo);page.evaluate('t=>VFXDemo.seek(t)',at);page.wait_for_timeout(80)
  page.screenshot(path=str(OUT/(('peer-' if prototype_only else '')+demo+'-prototype.png')))
  result=page.evaluate("""()=>{const start=performance.now();for(let i=0;i<300;i++)VFXDemo.draw();const elapsed=performance.now()-start;
   const c=document.getElementById('view'),data=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let pixels=0;for(let i=3;i<data.length;i+=4)if(data[i])pixels++;
   return {draw300Ms:elapsed,meanDrawMs:elapsed/300,opaquePixels:pixels,state:VFXDemo.state};}""")
  assert result['opaquePixels']>400000
  before=page.evaluate('VFXDemo.state.time');page.wait_for_timeout(100);assert page.evaluate('VFXDemo.state.time')==before
  page.select_option('#quality','low');page.wait_for_timeout(30);result['lowQualityState']=page.evaluate('VFXDemo.state');assert result['lowQualityState']['events']==result['state']['events'];page.select_option('#quality','high')
  report['prototype'][demo]=result
 page.evaluate("VFXDemo.setDemo('sky');VFXDemo.seek(.8)");page.check('#double');page.check('#camera');page.select_option('#density','2');page.wait_for_timeout(100)
 high=page.evaluate('({state:VFXDemo.state,w:document.getElementById("view").width,h:document.getElementById("view").height})')
 assert high['w']==1720 and high['h']==980 and high['state']['lastStats']['texturedTriangles']==48,high
 page.screenshot(path=str(OUT/'sky-dpr2-camera-twofold-high.png'))
 page.select_option('#quality','low');page.wait_for_timeout(80);low=page.evaluate('VFXDemo.state')
 assert low['lastStats']=={'texturedTriangles':12,'fallbackPanels':2,'folds':2},low
 assert low['events']==high['state']['events'] and low['time']==high['state']['time']
 page.screenshot(path=str(OUT/'sky-dpr2-camera-twofold-low.png'))
 report['prototype']['twoFoldDprCamera']={'high':high,'low':low}
 assert not errors,errors
 report['prototype']['errors']=errors
 context.close();browser.close()
(OUT/('prototype-peer-review.json' if prototype_only else 'report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'gameplayCases':len(report['gameplay']),'prototypeModes':list(report['prototype']),'ok':True}))
