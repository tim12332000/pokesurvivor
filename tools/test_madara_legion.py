"""Madara legion: independent behavior regression and native Lv1/card play evidence.

Requires the existing local server. No production code is patched by this tool.
Controlled fixtures and unmodified natural runs are stored separately.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_jujutsu as base
import test_madara_rework_play as native

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('MADARA_LEGION_OUT',ROOT / 'art-review/madara-legion-20261107/qa'))
URL = os.environ.get('MADARA_LEGION_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def hashes():
    names = ['.omx/naruto-madara.js', '.omx/naruto-madara-camera.js', 'art-review/madara/runtime.js', 'art-review/madara/frames.json']
    return {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in names}


def boot(page):
    page.goto(URL)
    frame = native.frame_for(page)
    frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if frame.locator('#tap-start').is_visible():
        frame.locator('#tap-start').click()
    frame.locator('[data-quick-naruto="30016"]').click()
    frame.wait_for_function('G.NarutoAssets.ready(30016)')
    return frame


EXTRA_OBSERVE = r"""() => {
 const R=Rework;R.legion=[];R.contactEvents=[];let last=-1,seen=new Set();
 function sample(){const p=G.Game.player,s=G.NarutoMadara.stateFor(p),t=G.Game.st.time;
  if(s&&G.Game.state==='playing'&&t-last>=.1){last=t;
   R.legion.push({t,army:s.army.map(a=>({serial:a.serial,age:a.age,rank:a.rank,phase:a.phase,
    x:a.x,y:a.y,body:a.body?.spec.kind||null,guardian:a.guardian?{form:a.guardian.form,age:a.guardian.age,index:a.guardian.index}:null})),
    perfect:!!s.guardian?.perfect,perfectAge:s.guardian?.perfect?s.guardian.age:null,perfectCount:s.perfectCount});
   for(const c of s.hitContacts){const key=[c.time,c.castId,c.segment,c.source].join(':');if(!seen.has(key)){seen.add(key);R.contactEvents.push(c)}}
  }requestAnimationFrame(sample);
 }requestAnimationFrame(sample);
}"""


def priority(card, current):
    ranks = {m['id']:m['rank'] for m in current['moves']}
    if card['key'] == 'up:naruto-madara-clones' and ranks.get('naruto-madara-clones',0) >= 2:
        return 6
    if card['key'] == 'up:naruto-madara-susanoo' and ranks.get('naruto-madara-susanoo',0) >= 2:
        return 7
    return {'new:naruto-madara-fire': 0, 'new:naruto-madara-susanoo': 1,
            'up:naruto-madara-clones': 2, 'up:naruto-madara-susanoo': 3,
            'new:naruto-madara-meteor': 4, 'stat:quantity': 5,
            'stat:atk': 8, 'stat:cd': 9}.get(card['key'], 6 if card['type'] == 'up' else 20)


def natural(browser, label, width, height, target):
    folder = OUT / label
    folder.mkdir(parents=True, exist_ok=True)
    mobile = width < 500
    context = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=mobile,
        has_touch=mobile, service_workers='block', record_video_dir=str(folder / 'video'),
        record_video_size={'width': width, 'height': height})
    page = context.new_page()
    errors, missing = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('response', lambda r: missing.append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
    before = hashes()
    frame = boot(page)
    page.screenshot(path=str(folder / 'selection.png'))
    permanent = frame.evaluate('G.DB.upgradesOf(G.DB.save.partner)')
    assert not any(permanent.values()), permanent
    frame.evaluate(native.OBSERVE, 231106)
    frame.evaluate(EXTRA_OBSERVE)
    frame.locator('#scr-menu [data-go="play"]').click()
    frame.wait_for_function('G.Game.player?.dex===30016&&G.Game.state==="playing"')
    initial = frame.evaluate('Rework.snapshot()')
    assert initial['level'] == 1, initial
    assert sorted(m['id'] for m in initial['moves']) == ['naruto-madara', 'naruto-madara-clones'], initial
    page.screenshot(path=str(folder / 'normal-lv1.png'))
    client = context.new_cdp_session(page) if mobile else None
    touch_point = None
    def release():
        nonlocal touch_point
        if client and touch_point:
            client.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
            touch_point = None
        elif held:
            page.keyboard.up(held)
    started, held, last_offer, next_image, next_log = time.monotonic(), None, None, 0, 20
    while time.monotonic() - started < max(180, target * 2):
        state = frame.evaluate('({state:G.Game.state,t:G.Game.st.time,dead:!!G.Game.player?.dead,offer:Rework.currentOffer})')
        t = state['t']
        if state['dead'] or state['state'] == 'over' or t >= target:
            break
        if t >= next_log:
            print(label, round(t, 1), frame.evaluate('({level:G.Game.player.level,hp:G.Game.player.hp,cards:Rework.ledger.length,perfect:G.NarutoMadara.stateFor(G.Game.player)?.perfectCount})'), flush=True)
            next_log += 20
        if state['state'] == 'levelup' and state['offer'] and state['offer']['serial'] != last_offer:
            if held:
                release()
                held = None
            offer = state['offer']
            current = frame.evaluate('Rework.snapshot()')
            chosen = min(range(len(offer['options'])), key=lambda i: (priority(offer['options'][i],current), i))
            page.wait_for_timeout(170)
            page.screenshot(path=str(folder / f'card-{offer["serial"]}-{t:.1f}.png'))
            frame.locator('#cards .card').nth(chosen).click()
            last_offer = offer['serial']
        elif frame.locator('#scr-item').is_visible():
            frame.locator('#item-cards .card').first.click()
        elif frame.locator('#scr-bond').is_visible():
            frame.locator('#bond-cards .card').first.click()
        elif state['state'] == 'playing':
            direction = frame.evaluate("""() => {const p=G.Game.player,items=G.Pickups.all().filter(x=>Math.hypot(x.x-p.x,x.y-p.y)<1200 && (!G.World.projectilePathClear||G.World.projectilePathClear(p.x,p.y,x.x,x.y,null,{radius:1,spacing:8,includeStart:false}))).sort((a,b)=>Math.hypot(a.x-p.x,a.y-p.y)-Math.hypot(b.x-p.x,b.y-p.y));const v=items[0];return v?{dx:v.x-p.x,dy:v.y-p.y}:null}""")
            key = ('KeyD' if direction['dx']>0 else 'KeyA') if direction and abs(direction['dx'])>abs(direction['dy']) else ('KeyS' if direction['dy']>0 else 'KeyW') if direction else ['KeyD', 'KeyS', 'KeyA', 'KeyW'][int(t // 1.5) % 4]
            if key != held:
                if held:
                    release()
                if client:
                    touch_point = frame.evaluate('G.Touch.stickBase()')
                    if frame != page.main_frame:
                        box = page.locator('iframe').first.bounding_box()
                        touch_point = {'x':touch_point['x']+box['x'],'y':touch_point['y']+box['y']}
                    client.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[touch_point]})
                    dx,dy = {'KeyD':(42,0),'KeyS':(0,42),'KeyA':(-42,0),'KeyW':(0,-42)}[key]
                    client.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':touch_point['x']+dx,'y':touch_point['y']+dy}]})
                else:
                    page.keyboard.down(key)
                held = key
            if t >= next_image:
                page.screenshot(path=str(folder / f'play-{t:.1f}.png'))
                next_image += 8
        elif state['state'] == 'paused':
            frame.locator('#btn-resume').click()
        page.wait_for_timeout(70)
    if held:
        release()
    run = frame.evaluate('({initial:null,ledger:Rework.ledger,offers:Rework.offers,samples:Rework.samples,legion:Rework.legion,contacts:Rework.contactEvents,pulses:Rework.pulses,final:Rework.snapshot(),t:G.Game.st.time,dead:!!G.Game.player.dead})')
    run.update(initial=initial, permanent=permanent, sourceHashes=before, sourceHashesAfter=hashes(), errors=errors, missing=missing,
        constraints='Fresh save, native default speed, real keyboard/joystick and card UI; nearest reachable native pickup route, square fallback; no XP/level/HP/spawner/AI/manual skill timing changes. Seed fixed for reproducibility; no paired-DPS claim.')
    page.screenshot(path=str(folder / 'final.png'))
    save(folder / 'run.json', run)
    video = page.video
    context.close()
    video.save_as(str(folder / 'native-play.webm'))
    video.delete()
    army_hits = [c for c in run['contacts'] if c['channel'].startswith('army-')]
    full_perfect = []
    for count in sorted({s['perfectCount'] for s in run['legion'] if s['perfect']}):
        ss = [s for s in run['legion'] if s['perfect'] and s['perfectCount'] == count]
        if ss and max(s['perfectAge'] for s in ss) >= 5.8 and any(s['t'] > ss[-1]['t'] and not s['perfect'] for s in run['legion']):
            full_perfect.append(count)
    summary = {'seconds':run['t'], 'level':run['final']['level'], 'dead':run['dead'], 'cards':len(run['ledger']),
        'firstArmy':next((s['t'] for s in run['legion'] if len(s['army']) == 2),None),
        'firstAllCloneGuardians':next((s['t'] for s in run['legion'] if s['army'] and all(a['guardian'] for a in s['army'])),None),
        'armyHitChannels':sorted({c['channel'] for c in army_hits}), 'armyHits':len(army_hits),
        'bodyGuardianOverlap':sum(any(a['body'] and a['guardian'] for a in s['army']) for s in run['legion']),
        'perfectFullWindows':full_perfect, 'meteorMainHits':sum(c['kind']=='meteor' and c['segment']<2 for c in run['contacts']),
        'errors':errors,'missing':missing,'sourceStable':before==hashes()}
    save(folder / 'summary.json', summary)
    print(label, json.dumps(summary), flush=True)
    return summary


CONTROLLED = r"""() => {
 const A=JAcceptance,p=A.p(),M=G.NarutoMadara,assert=A.assert,out={};
 function setup(){A.reset();A.fixture('naruto-madara');for(const id of ['naruto-madara-clones','naruto-madara-fire','naruto-madara-susanoo','naruto-madara-meteor'])assert(p.addMove(id),'fixture learn '+id);for(const m of p.moves)m.t=0;return p.moves.find(m=>m.id==='naruto-madara-clones')}
 const army=setup();for(const [x,y]of [[40,0],[90,30],[120,-50],[180,80],[250,0]])A.spawn(x,y);
 const pulses=[],original=G.CombatPulse.onPulse;G.CombatPulse.onPulse=i=>{pulses.push({channel:i.channel,hits:i.primaryHits||0});original?.(i)};
 try{
  A.advance(1.5,true);let s=M.stateFor(p);assert(s.army.length===2,'starter army missing');
  const before=s.army.map(a=>({serial:a.serial,x:a.x,y:a.y,age:a.age,body:a.body,guardian:a.guardian,cooldown:a.cooldown}));
  Object.assign(army,G.Moves.instance(army.id,2));A.advance(.01);
  s=M.stateFor(p);assert(s.army.length===4,'rank2 must add two clones');
  for(const old of before){const a=s.army.find(a=>a.serial===old.serial);assert(a&&a.age>=old.age&&a.age<old.age+.02,'growth reset old actor age');assert(Math.hypot(a.x-old.x,a.y-old.y)<=4,'growth reset old actor position');}
  out.growth={before:before.map(a=>({serial:a.serial,age:a.age})),after:s.army.map(a=>({serial:a.serial,age:a.age}))};
  let overlap=0;for(let i=0;i<1000;i++){A.step(.01,true);if(M.stateFor(p).army.some(a=>a.body&&a.guardian))overlap++}
  assert(overlap>0,'guardian monopolized army body');
  assert(pulses.some(i=>i.channel==='army-guardian'&&i.hits),'clone guardians did not contact');
  assert(pulses.some(i=>(i.channel==='army-body'||i.channel==='army-fire')&&i.hits),'clone body/fire did not contact');
  out.concurrent={overlap,pulses};
  A.advance(24,true);assert(M.stateFor(p).army.length===4,'persistent army expired');
  const serial=M.stateFor(p).army.map(a=>a.serial);p.quantityPicks=1;A.advance(.01);assert(M.stateFor(p).army.length===5,'quantity growth missing');assert(serial.every(n=>M.stateFor(p).army.some(a=>a.serial===n)),'quantity replaced army');
  out.persistent={count:M.stateFor(p).army.length,serials:M.stateFor(p).army.map(a=>a.serial)};
  p.moves=p.moves.filter(m=>m.id!==army.id);A.advance(.01);assert(!M.stateFor(p).army.length,'unlearn left army');
  out.unlearn=true;
  setup();const first=A.spawn(100,0),second=A.spawn(100,0),fire=p.moves.find(m=>m.id==='naruto-madara-fire');for(const m of p.moves)m.t=999;fire.t=0;
  let firstHits=0,secondHits=0;const hurt=first.hurt;first.hurt=function(...args){firstHits++;const r=hurt.apply(this,args);G.Combat.clearFields(p);return r};const hurt2=second.hurt;second.hurt=function(...args){secondHits++;return hurt2.apply(this,args)};
  A.resume();try{assert(M.cast(p,fire),'fire cast rejected')}finally{A.pause()}A.advance(2);
  assert(firstHits===1&&secondHits===0,'first target cancel allowed same-wave second or future hit');out.cancel={firstHits,secondHits};
  setup();G.EnemyMgr.clear();A.advance(.8,true);s=M.stateFor(p);assert(s.army.length===2,'lifecycle fixture army missing');
  const clock=s.clock,ages=s.army.map(a=>a.age);M.update(1);assert(s.clock===clock&&s.army.every((a,i)=>a.age===ages[i]),'paused persistent actors advanced');
  p.frozen=true;A.advance(.3,true);assert(s.clock===clock,'frozen owner army advanced');p.frozen=false;
  const world=G.World,oldPath=world.projectilePathClear,oldFree=world.isFree;
  world.projectilePathClear=(x,y,tx,ty)=>!(Math.min(x,tx)<100&&Math.max(x,tx)>=100);world.isFree=(x,y)=>x<100;
  p.x=500;let maxStep=0;for(let i=0;i<180;i++){const prev=new Map(s.army.map(a=>[a.serial,{x:a.x,y:a.y}]));A.step(.01,true);for(const a of s.army){const b=prev.get(a.serial);maxStep=Math.max(maxStep,Math.hypot(a.x-b.x,a.y-b.y));assert(a.x<100,'army crossed solid wall/follow teleported');}}
  world.projectilePathClear=oldPath;world.isFree=oldFree;assert(maxStep<=4.01,'army follow exceeded400px/s');out.follow={maxStep,wallRespected:true};
  p.dead=true;A.resume();try{M.update(.01)}finally{A.pause()}assert(!M.stateFor(p),'death retained army state');p.dead=false;p.hp=p.maxHp;
  setup();A.advance(.8,true);assert(M.stateFor(p).army.length===2,'world fixture army missing');const originalWorld=G.World;G.World={...originalWorld};A.resume();try{M.update(.01)}finally{G.World=originalWorld;A.pause()}assert(!M.stateFor(p),'world change retained persistent army');
  out.lifecycle={pause:true,freeze:true,death:true,world:true};
  return out;
 }finally{G.CombatPulse.onPulse=original}
}"""


def stress(browser):
    report = {}
    for label,width,height in [('stress-desktop',1280,900),('stress-mobile360',360,800)]:
        folder=OUT/label
        folder.mkdir(parents=True,exist_ok=True)
        context=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<500,has_touch=width<500,
            service_workers='block',record_video_dir=str(folder/'video'),record_video_size={'width':width,'height':height})
        page=context.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        frame=boot(page)
        frame.locator('#scr-menu [data-go="play"]').click()
        frame.wait_for_function('G.Game.state==="playing"')
        frame.evaluate(base.SETUP)
        config=frame.evaluate(r'''() => {
          const A=JAcceptance,p=A.p();A.reset();A.fixture('naruto-madara',5);
          for(const id of ['naruto-madara-clones','naruto-madara-fire','naruto-madara-susanoo','naruto-madara-meteor']){A.assert(p.addMove(id),'stress learn '+id);Object.assign(p.moves.find(m=>m.id===id),G.Moves.instance(id,5))}
          for(let i=0;i<3;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');A.assert(c,'stress quantity card');c.apply(p)}
          for(const [x,y] of [[50,0],[80,100],[150,-80],[220,150],[300,-180],[420,20],[520,80],[-200,80],[-150,-100]])A.spawn(x,y);
          for(const m of p.moves)m.t=0;
          window.LegionStress={samples:[],last:0};
          function sample(){const s=G.NarutoMadara.stateFor(p);if(s&&s.clock-LegionStress.last>=.1){LegionStress.last=s.clock;LegionStress.samples.push({clock:s.clock,army:s.army.length,perfect:!!s.guardian?.perfect,age:s.guardian?.age,cloneGuardians:s.army.filter(a=>a.guardian).length,contacts:s.hits})}requestAnimationFrame(sample)}requestAnimationFrame(sample);A.resume();
          return {scope:'controlled native rendering only, not natural growth',level:p.level,ranks:p.moves.map(m=>({id:m.id,rank:m.lvl})),quantity:p.quantityPicks};
        }''')
        started=time.monotonic();images=[];last_image=0
        while time.monotonic()-started<16:
            state=frame.evaluate('({state:G.Game.state,clock:G.NarutoMadara.stateFor(G.Game.player)?.clock||0,army:G.NarutoMadara.stateFor(G.Game.player)?.army.length||0,perfect:!!G.NarutoMadara.stateFor(G.Game.player)?.guardian?.perfect,age:G.NarutoMadara.stateFor(G.Game.player)?.guardian?.age||0})')
            if state['state']=='levelup':
                page.wait_for_timeout(200)
                frame.locator('#cards .card').first.click()
            if state['army']==16 and state['perfect'] and state['clock']-last_image>.7:
                name=f'perfect-{state["clock"]:.2f}.png';page.screenshot(path=str(folder/name));images.append({'path':name,**state});last_image=state['clock']
            page.wait_for_timeout(70)
        data=frame.evaluate('({samples:LegionStress.samples,stats:G.NarutoMadara.stats(G.Game.player),viewport:{width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth}})')
        data.update(config=config,images=images,errors=errors,sourceHashes=hashes())
        save(folder/'run.json',data)
        video=page.video;context.close();video.save_as(str(folder/'native-stress.webm'));video.delete()
        report[label]={'maxArmy':max((s['army'] for s in data['samples']),default=0),'perfectImages':len(images),'errors':errors,'config':config,'viewport':data['viewport']}
        print(label,report[label],flush=True)
    return report


def meteor_scene(browser):
    folder=OUT/'meteor-scene';folder.mkdir(parents=True,exist_ok=True)
    context=browser.new_context(viewport={'width':1280,'height':900},service_workers='block',
        record_video_dir=str(folder/'video'),record_video_size={'width':1280,'height':900})
    page=context.new_page();frame=boot(page)
    frame.locator('#scr-menu [data-go="play"]').click();frame.wait_for_function('G.Game.state==="playing"')
    frame.evaluate(base.SETUP)
    frame.evaluate("() => {const A=JAcceptance;A.reset();A.fixture('naruto-madara-meteor',1);A.spawn(70,20);window.MeteorScene=[];A.resume()}")
    started=time.monotonic();last=0;images=[]
    while time.monotonic()-started<4:
        state=frame.evaluate("() => {const s=G.NarutoMadara.stateFor(G.Game.player);return {clock:s?.clock||0,rocks:(s?.meteors||[]).filter(m=>!m.fragment).map(m=>({age:m.age,delay:m.delay,second:!!m.second,landed:!!m.landed,x:m.x,y:m.y})),contacts:s?.hitContacts.filter(c=>c.kind==='meteor')||[]}}")
        if state['clock']-last>.12:
            name=f'meteor-{state["clock"]:.2f}.png';page.screenshot(path=str(folder/name));images.append({'path':name,**state});last=state['clock']
        page.wait_for_timeout(30)
    save(folder/'run.json',{'scope':'Controlled isolated twin meteor native rendering; not natural growth','sourceHashes':hashes(),'images':images})
    video=page.video;context.close();video.save_as(str(folder/'native-meteors.webm'));video.delete()
    return {'images':len(images)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url':URL,'sourceHashes':hashes()}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        if os.environ.get('MADARA_LEGION_STRESS') == '1':
            report['stress'] = stress(browser)
            report['meteorScene'] = meteor_scene(browser)
            save(OUT / 'stress-report.json',report)
            browser.close()
            return
        if os.environ.get('MADARA_LEGION_SKIP_CONTROLLED') != '1':
            context = browser.new_context(viewport={'width':1280,'height':900},service_workers='block')
            page = context.new_page()
            frame = boot(page)
            frame.locator('#scr-menu [data-go="play"]').click()
            frame.wait_for_function('G.Game.state==="playing"')
            frame.evaluate(base.SETUP)
            report['controlled'] = frame.evaluate(CONTROLLED)
            save(OUT / 'controlled.json',report['controlled'])
            context.close()
        labels=os.environ.get('MADARA_LEGION_LABELS','desktop,mobile390').split(',')
        for label,width,height,seconds in [('desktop',1280,900,120),('mobile390',390,844,110),('mobile360',360,800,80)]:
            if label in labels:
                report[label]=natural(browser,label,width,height,float(os.environ.get('MADARA_LEGION_SECONDS',seconds)))
                save(OUT / 'report.json',report)
        browser.close()
    report['sourceHashesAfter']=hashes()
    natural_cases=[v for k,v in report.items() if k in ('desktop','mobile390','mobile360')]
    report['ok']=all(v['sourceStable'] and not v['errors'] and not v['missing'] and not v['dead'] for v in natural_cases)
    if 'desktop' in report:
        report['ok'] = report['ok'] and bool(report['desktop']['perfectFullWindows']) and report['desktop']['meteorMainHits']>=2 and report['desktop']['bodyGuardianOverlap']>0
    save(OUT / 'report.json',report)
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
