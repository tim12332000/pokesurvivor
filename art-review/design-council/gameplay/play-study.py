import json,time,math,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
CHROME=r'C:\Program Files\Google\Chrome\Application\chrome.exe'
CASES=[('yuta-normal','jjk-yuta','',70),('temari-normal','temari','',70),('yuta20-trial','jjk-yuta','&startLevel=20',20)]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=CHROME,headless=True)
 report={'scope':'native world/input/cards; read-only state sampling; no HP/XP/world/spawn overrides','cases':[]}
 for label,hero,extra,seconds in CASES:
  ctx=browser.new_context(viewport={'width':1280,'height':900},service_workers='block');page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto('http://127.0.0.1:8337/.omx/digimon.html?lang=zh-TW&layout=wide&hero='+hero+extra)
  page.wait_for_function("typeof G==='object'&&G.NarutoAssets&&document.getElementById('boot').classList.contains('hidden')")
  if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
  page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function("G.Game.state==='playing'&&G.Game.player")
  case={'label':label,'hero':hero,'wallTarget':seconds,'cards':[],'snapshots':[],'errors':errors}
  case['start']=page.evaluate("""()=>{const p=G.Game.player;return {level:p.level,hp:p.hp,atk:p.atk,spd:p.spd,cdMul:p.cdMul,xpMul:p.xpMul,crit:p.critChance,regen:p.regen,magnet:p.magnet,maxHp:p.maxHp,slots:p.slots.length,moves:p.moves.map(m=>({id:m.id,lvl:m.lvl,passive:m.passive,autoCast:m.autoCast})),stats:G.LevelUp.STATS.map(s=>({id:s.id,title:s.title,max:s.max??null,eligible:!s.eligible||s.eligible(p)}))}}""")
  start=time.perf_counter();last=-1;held=set()
  while time.perf_counter()-start<seconds:
   info=page.evaluate("""()=>{const p=G.Game.player,es=G.EnemyMgr.all().filter(e=>!e.dead);return {state:G.Game.state,time:G.Game.st.time,level:p.level,hp:p.hp,maxHp:p.maxHp,kills:p.kills,x:p.x,y:p.y,xp:p.xp,xpNext:p.xpNext,moves:p.moves.map(m=>({id:m.id,lvl:m.lvl,dealt:m.dealt,t:m.t})),slots:p.slots.length,stats:p.statsTaken,pickups:G.Pickups.all().filter(a=>a.kind==='xp').map(a=>({x:a.x,y:a.y})),enemies:es.map(e=>({x:e.x,y:e.y,r:e.r,hp:e.hp,behavior:e.behavior})),cards:[...document.querySelectorAll('#cards .card')].map(c=>({title:c.querySelector('.nm')?.textContent,desc:c.querySelector('.ds')?.textContent}))}}""")
   if info['state']=='levelup':
    for k in held:page.keyboard.up(k)
    held=set();names=[c['title'] or '' for c in info['cards']]
    priority=next((i for i,n in enumerate(names) if any(x in n for x in ['里香','三星','鐮鼬','大鐮','宇守羅','刀斬'])),0)
    case['cards'].append({'gameTime':info['time'],'level':info['level'],'offered':info['cards'],'pickedIndex':priority})
    page.locator('#cards .card').nth(priority).click();continue
   if info['state']=='over':case['endedEarly']='native death';break
   if info['state']!='playing':
    for k in held:page.keyboard.up(k)
    held=set();page.wait_for_timeout(200);continue
   t=time.perf_counter()-start
   if int(t//15)!=last:
    last=int(t//15);case['snapshots'].append({k:v for k,v in info.items() if k not in ['pickups','enemies','cards']});page.screenshot(path=str(OUT/f'{label}-{last*15}s.png'))
   # Input-only controller: collect the nearest visible XP, otherwise stay in
   # effective attack distance while avoiding contact; no world/state edits.
   x,y=info['x'],info['y'];dx=dy=0
   drops=info['pickups']
   if drops:
    q=min(drops,key=lambda q:(q['x']-x)**2+(q['y']-y)**2);dx=q['x']-x;dy=q['y']-y
   elif info['enemies']:
    e=min(info['enemies'],key=lambda e:(e['x']-x)**2+(e['y']-y)**2);ex,ey=e['x']-x,e['y']-y;dist=math.hypot(ex,ey)
    if dist>95:dx,dy=ex,ey
    elif dist<55:dx,dy=-ex,-ey
    else:dx,dy=-ey,ex
   else:dx,dy=math.cos(t*.4),math.sin(t*.4)
   near=[e for e in info['enemies'] if math.hypot(e['x']-x,e['y']-y)<48]
   for e in near:dx+=(x-e['x'])*4;dy+=(y-e['y'])*4
   desired=set()
   if abs(dx)>abs(dy)*.35:desired.add('KeyD' if dx>0 else 'KeyA')
   if abs(dy)>abs(dx)*.35:desired.add('KeyS' if dy>0 else 'KeyW')
   for k in held-desired:page.keyboard.up(k)
   for k in desired-held:page.keyboard.down(k)
   held=desired;page.wait_for_timeout(200)
  for k in held:page.keyboard.up(k)
  case['end']=page.evaluate("""()=>{const p=G.Game.player;return {state:G.Game.state,time:G.Game.st.time,level:p.level,hp:p.hp,maxHp:p.maxHp,kills:p.kills,xp:p.xp,xpNext:p.xpNext,moves:p.moves.map(m=>({id:m.id,lvl:m.lvl,dealt:m.dealt})),stats:p.statsTaken}}""")
  page.screenshot(path=str(OUT/f'{label}-end.png'));report['cases'].append(case);(OUT/'native-play-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');ctx.close();print(label,json.dumps(case['end'],ensure_ascii=True),flush=True)
 browser.close()
