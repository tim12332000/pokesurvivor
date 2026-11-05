"""Read-only native-input study. No terrain, damage, clock or card injection."""
import json,time,sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent/'evidence'
OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tools'))
from test_jujutsu import CHROME,frame_for

CASES=[('yuta-normal','jjk-yuta',''),('temari-normal','temari',''),('uro-trial20','jjk-uro','&startLevel=20')]
report={'method':'Native keyboard movement toward nearby XP, otherwise orbit near closest enemy; real offered card clicks. No world/stat/time injection. Concurrent browser contexts. Not a human playtest or matched-seed balance experiment.','cases':{}}
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=CHROME,headless=True)
 sessions=[]
 for name,hero,query in CASES:
  ctx=browser.new_context(viewport={'width':1280,'height':900},service_workers='block')
  page=ctx.new_page();page.goto('http://127.0.0.1:8337/.omx/digimon.html?lang=zh-TW&layout=wide&hero='+hero+query)
  f=frame_for(page);f.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
  if f.locator('#tap-start').is_visible():f.locator('#tap-start').click()
  f.locator('#scr-menu [data-go="play"]').click();f.wait_for_function('G.Game.state==="playing"')
  info={'samples':[],'choices':[],'initial':f.evaluate('({level:G.Game.player.level,hp:G.Game.player.hp,atkMul:G.Game.player.atkMul,cdMul:G.Game.player.cdMul,stats:G.Game.player.statsTaken,moves:G.Game.player.moves.map(m=>({id:m.id,lvl:m.lvl})),speed:G.Game.speed})')}
  report['cases'][name]=info;sessions.append((ctx,page,f,name,info,set()))
 start=time.monotonic();last_sample=-1
 while time.monotonic()-start<92:
  elapsed=time.monotonic()-start
  for ctx,page,f,name,info,held in sessions:
   data=f.evaluate("""()=>{const p=G.Game.player,st=G.Game.state;
    const out={state:st,time:G.Game.st.time,level:p.level,xp:p.xp,xpNext:p.xpNext,hp:p.hp,kills:p.kills,damage:p.dmgDealt,x:p.x,y:p.y,stats:p.statsTaken,moves:p.moves.map(m=>({id:m.id,lvl:m.lvl})),slots:p.slots.length};
    if(st==='playing'){
      const xp=G.Pickups.all().filter(a=>a.kind==='xp').sort((a,b)=>Math.hypot(a.x-p.x,a.y-p.y)-Math.hypot(b.x-p.x,b.y-p.y))[0];
      const e=G.EnemyMgr.all().filter(a=>!a.dead).sort((a,b)=>Math.hypot(a.x-p.x,a.y-p.y)-Math.hypot(b.x-p.x,b.y-p.y))[0];
      let dx=0,dy=0;if(xp){dx=xp.x-p.x;dy=xp.y-p.y;}else if(e){const d=Math.hypot(e.x-p.x,e.y-p.y);dx=e.x-p.x;dy=e.y-p.y;if(d<80){const x=dx;dx=-dy;dy=x;}}else{dx=Math.cos(G.Game.st.time*.2);dy=Math.sin(G.Game.st.time*.2)}
      out.keys=[...(Math.abs(dx)>5?[dx>0?'KeyD':'KeyA']:[]),...(Math.abs(dy)>5?[dy>0?'KeyS':'KeyW']:[])];
    }return out;}""")
   if data['state']=='levelup':
    cards=f.locator('#cards .card');texts=cards.all_text_contents()
    rank=next((i for i,t in enumerate(texts) if '特色' in t or '首次' in t),0)
    info['choices'].append({'wallSeconds':elapsed,'level':data['level'],'offers':texts,'chosen':rank})
    cards.nth(rank).click()
   desired=set(data.get('keys',[]))
   for key in held-desired:page.keyboard.up(key)
   for key in desired-held:page.keyboard.down(key)
   held.clear();held.update(desired)
   if int(elapsed//15)>last_sample:info['samples'].append(data)
  if int(elapsed//15)>last_sample:
   last_sample=int(elapsed//15)
   print('snapshot',round(elapsed),[(name,inf['samples'][-1]['level'],inf['samples'][-1]['kills']) for _,_,_,name,inf,_ in sessions],flush=True)
  time.sleep(.45)
 for ctx,page,f,name,info,held in sessions:
  for key in held:page.keyboard.up(key)
  page.screenshot(path=str(OUT/(name+'-end.png')))
  info['final']=f.evaluate('({state:G.Game.state,time:G.Game.st.time,level:G.Game.player.level,hp:G.Game.player.hp,kills:G.Game.player.kills,stats:G.Game.player.statsTaken,moves:G.Game.player.moves.map(m=>({id:m.id,lvl:m.lvl})),slots:G.Game.player.slots.length})')
  ctx.close()
 browser.close()
report['wallSeconds']=time.monotonic()-start
(OUT/'native-playstudy.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({name:info['final'] for name,info in report['cases'].items()},ensure_ascii=False))
