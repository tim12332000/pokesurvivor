"""Classic Freeze acceptance through the production menu and native combat.

The controlled checks isolate geometry/lifecycle. --natural uses only real
keyboard/card/item UI input on a fresh save and records an observer-only ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art-review/freeze/qa'
URL = os.environ.get('LF2_URL', 'http://127.0.0.1:8766/.omx/digimon.html?lang=zh-TW&layout=wide&hero=freeze')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
IDS = ['lf2-iceball', 'lf2-sword', 'lf2-column', 'lf2-whirlwind']


def hashes():
    paths = ['.omx/lf2.js', '.omx/lf2-freeze-combat.js', '.omx/lf2-art.js', '.omx/naruto.js',
             '.omx/digimon.html', 'js/entities/enemy.js']
    paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/'assets/lf2').rglob('*') if p.is_file()]
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths if (ROOT/name).is_file()}


def boot(page, label='desktop'):
    page.goto(URL.replace('&layout=wide','') if label.startswith('mobile') else URL)
    page.wait_for_function("window.G?.LF2Freeze&&G.LF2Art&&document.getElementById('boot').classList.contains('hidden')", timeout=60000)
    if page.locator('#tap-start').is_visible():
        page.locator('#tap-start').click()
    page.locator('[data-quick-naruto="30018"]').click()
    page.wait_for_function('G.NarutoAssets.ready(30018)', timeout=30000)
    page.screenshot(path=str(OUT/f'{label}-selection.png'))
    page.locator('#scr-menu [data-go="play"]').click()
    page.wait_for_function('G.Game.player?.dex===30018&&G.Game.state==="playing"')
    page.screenshot(path=str(OUT/f'{label}-normal-entry.png'))


SETUP = r'''() => {
 const assert=(ok,msg)=>{if(!ok)throw Error(msg)},p=()=>G.Game.player,F=G.LF2Freeze;
 function pause(){if(G.Game.state==='playing')G.Game.togglePause();G.UI.hide('scr-pause')}
 function resume(){if(G.Game.state==='paused')G.Game.togglePause();assert(G.Game.state==='playing','not playing '+G.Game.state)}
 function reset(){G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();G.SelfClones?.clear();G.Pickups.clear();
  G.World.collide=()=>{};G.World.isWall=()=>false;G.World.isFree=()=>true;G.World.isLiquid=()=>false;
  G.World.projectileBlock=()=>false;G.World.propsInCircle=()=>[];
  const a=p();a.x=a.y=0;a.hp=a.maxHp;a.dead=false;a.frozen=false;a.flash=0;a.invuln=0;
  a.target=null;a.aim=0;a.attackFace=0;a.walking=false;a.critChance=0;a.item=null;
  a.percentHealthDamage=a.lifestealRate=a.damageSplashPicks=a.quantityPicks=a.quantityBonus=0;
  a.cdMul=1;a.xp=0;a.xpNext=1e12;G.Camera.x=G.Camera.y=0;for(const m of a.moves)m.t=999;pause();}
 function spawn(x,y,boss=false){const e=new G.Enemy({dex:19,hp:1000000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1},boss);
  e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e}
 function watch(e){const hits=[],hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);hits.push({raw:args[0],loss:hp-this.hp,owner:args[6]===p(),id:args[7]});return result};return hits}
 function fixture(id,rank=1){const a=p();F.clear(a);a.level=30;a.moves=[G.Moves.instance(id,rank)];a.arrange();const m=a.moves[0];m.t=0;return m}
 function step(dt=.01,tick=false){resume();try{if(tick)G.Combat.tick(dt,p(),0);p().anim.update(dt);G.Combat.updateFields(dt)}finally{pause()}}
 function advance(seconds,tick=false){let left=seconds;while(left>1e-9){const dt=Math.min(.01,left);step(dt,tick);left-=dt}}
 function cast(m){resume();try{assert(F.cast(p(),m),'cast rejected '+m.id)}finally{pause()}}
 window.FAcceptance={assert,p,F,pause,resume,reset,spawn,watch,fixture,step,advance,cast};pause();
}'''

PROGRESSION = r'''() => {
 const A=FAcceptance,p=A.p(),ids=['lf2-iceball','lf2-sword','lf2-column','lf2-whirlwind'],out={offers:[],growth:[]};
 A.assert(p.level===1&&p.moves.length===1&&p.moves[0].id===ids[0],'wrong fresh Lv1 starter');
 const mon=p.mon;
 for(const level of [1,2,3,4,5,7,8]){p.level=level;const pool=G.Moves.poolFor(p.mon),cards=G.LevelUp.offer(p,100);
  for(const id of ids)A.assert(pool.includes(id)===(level>=G.Moves.BY_ID[id].learnLevel),'pool gate '+id+' at '+level);
  for(const id of ids.slice(1))A.assert(cards.some(c=>c.key==='new:'+id)===(level>=G.Moves.BY_ID[id].learnLevel),'card gate '+id+' at '+level);
  out.offers.push({level,pool,cards:cards.map(c=>c.key)});
 }
 p.level=30;for(const id of ids.slice(1)){const c=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(c&&c.apply(p)!==false,'learn card failed '+id)}
 A.assert(ids.every(id=>p.hasMove(id)),'all specials did not learn');
 for(const dex of [30001,30006,30014,30017]){p.mon=G.DEX_BY[dex];A.assert(!G.Moves.poolFor(p.mon).some(id=>ids.includes(id)),'Freeze pool leaked to '+dex)}p.mon=mon;
 for(const id of ids){A.reset();const m=A.fixture(id);const before=A.F.profile(p,m);p.quantityPicks=p.quantityBonus=3;const after=A.F.profile(p,m);out.growth.push({id,before,after});}
 return out;
}'''

MECHANICS = r'''() => {
 const A=FAcceptance,p=A.p,F=A.F,out={};
 A.reset();let m=A.fixture('lf2-iceball'),enemy=A.spawn(300,0),hits=A.watch(enemy);A.cast(m);A.advance(.3);
 A.assert(hits.length===0,'iceball dealt instant beam damage');A.advance(1);
 A.assert(hits.length===1&&hits[0].owner&&hits[0].id===m.id,'iceball flight failed/duplicate/wrong owner');out.flight=hits;
 A.reset();m=A.fixture('lf2-iceball');enemy=A.spawn(300,0);hits=A.watch(enemy);A.cast(m);G.World.isWall=(x,y)=>x>=110&&x<=130;A.advance(1.5);
 A.assert(!hits.length,'iceball crossed wall');out.wall=true;
 for(const id of ['lf2-sword','lf2-column','lf2-whirlwind']){
  A.reset();m=A.fixture(id);const coords=id==='lf2-sword'?[[48,0],[56,8],[62,-8]]:id==='lf2-column'?[[30,0],[95,0],[165,0]]:[[85,0],[105,8],[120,-8]];
  const inside=coords.map(([x,y])=>A.spawn(x,y)),outside=A.spawn(-500,500),insideHits=inside.map(A.watch),outsideHits=A.watch(outside);A.cast(m);
  if(id==='lf2-sword'){A.advance(.6);A.assert(F.stateFor(p()).swordOwned&&insideHits.every(h=>!h.length),'summoning sword dealt phantom damage');m.t=0;A.cast(m);}
  A.advance(3.6);
  A.assert(insideHits.every(h=>h.some(x=>x.loss>0)),id+' missed distributed targets');A.assert(!outsideHits.length,id+' damaged outside');
  A.assert(insideHits.every(h=>h.every(x=>x.owner&&x.id===id)),id+' lost attribution');out[id]={hits:insideHits,outside:outsideHits};
  if(id==='lf2-whirlwind')A.assert(insideHits.some(h=>h.length>=2),'whirlwind had no repeat native contacts');
 }
 out.advertisedReach=[];
 for(const id of ['lf2-column','lf2-whirlwind']){
  A.reset();m=A.fixture(id);const profile=F.profile(p(),m),edge=A.spawn(profile.range,0),edgeHits=A.watch(edge);A.cast(m);A.advance(6);
  A.assert(edgeHits.length>0,id+' acquires enemy at advertised reach but never contacts it');out.advertisedReach.push({id,range:profile.range,hits:edgeHits});
 }
 A.reset();m=A.fixture('lf2-iceball');enemy=A.spawn(100,0);hits=A.watch(enemy);A.cast(m);A.advance(.45);
 A.assert(F.stopped(enemy),'ice impact did not freeze');const x=enemy.x,y=enemy.y;enemy.spd=80;enemy.dmg=30;enemy.touchCd=0;
 A.resume();try{enemy.update(.2,p(),0)}finally{A.pause()};A.assert(enemy.x===x&&enemy.y===y,'frozen enemy AI moved');
 p().x=enemy.x;p().y=enemy.y;p().invuln=0;p().flash=0;enemy.touchCd=0;G.EnemyMgr.rebuildGrid();const hp=p().hp;
 A.resume();try{G.Combat.resolve(.01,p(),0)}finally{A.pause()};A.assert(p().hp===hp,'frozen enemy still dealt contact damage');
 out.freeze={status:F.freezeStatus?.(enemy),x,y,contactDamage:hp-p().hp};
 out.props=[];
 for(const id of ['lf2-iceball','lf2-sword','lf2-column','lf2-whirlwind']){
  A.reset();m=A.fixture(id);const prop={x:45,y:0,r:10,hp:10000,destructible:true},damage=G.World.damageProp,calls=[];
  G.World.propsInCircle=(x,y,r)=>prop.hp>0&&Math.hypot(prop.x-x,prop.y-y)<=r+prop.r?[prop]:[];
  G.World.projectileBlock=(x,y,r)=>prop.hp>0&&Math.hypot(prop.x-x,prop.y-y)<=prop.r+r?prop:false;
  G.World.damageProp=(target,amount)=>{A.assert(target===prop,'wrong prop');calls.push(amount);target.hp-=amount};
  try{A.cast(m);if(id==='lf2-sword'){A.advance(.6);m.t=0;A.cast(m)}A.advance(3)}finally{G.World.damageProp=damage}
  A.assert(calls.length>0,id+' cannot attack destructible without enemy');out.props.push({id,calls,hp:prop.hp});
 }
 return out;
}'''

IDENTITY = r'''() => {
 const A=FAcceptance,p=A.p,F=A.F,out={};
 A.reset();let m=A.fixture('lf2-iceball'),e=A.spawn(40,0),hits=A.watch(e);m.t=999;A.advance(.35,true);
 A.assert(hits.length>0&&F.stats(p()).casts['lf2-punch']>0,'unarmed fallback never hit');A.assert(!F.stopped(e),'normal punch incorrectly froze enemy');out.punch=hits;
 A.reset();m=A.fixture('lf2-sword');e=A.spawn(40,0);hits=A.watch(e);A.cast(m);A.advance(.6);
 A.assert(!hits.length&&F.stateFor(p()).swordOwned,'sword summon incorrect');A.advance(1);A.assert(F.stateFor(p()).swordOwned,'sword vanished between actions');
 m.t=0;A.cast(m);A.advance(.12);A.assert(!hits.length,'sword hit before original active frame22/27');
 A.advance(.08);A.assert(hits.length>0&&F.stopped(e),'persistent sword did not freeze within original active frames');const count=hits.length;
 A.advance(.45);A.assert(hits.length===count,'sword recovery repeated damage');
 p().moves=[];A.advance(.01);A.assert(!F.stateFor(p()).swordOwned,'unlearn retained sword');out.sword={hits,removed:true};return out;
}'''

GROWTH = r'''() => {
 const A=FAcceptance,p=A.p(),F=A.F;A.reset();const m=A.fixture('lf2-sword'),baseline=F.profile(p,m);
 const original={scale:p.anim.scale,r:p.r,bodyH:p.bodyH,maxHp:p.maxHp,hp:p.hp,spdMul:p.spdMul,cdMul:p.cdMul,giantPicks:p.giantPicks};
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:giant');A.assert(card,'real giant card missing');
 try{
  A.assert(card.apply(p)!==false,'giant card rejected');const grown=F.profile(p,m);
  A.assert(grown.range>baseline.range&&p.anim.scale>original.scale,'giant blade art/collision did not grow');
  const e=A.spawn(baseline.range+18,0),hits=A.watch(e);A.cast(m);A.advance(.6);m.t=0;A.cast(m);A.advance(.5);
  A.assert(hits.length>0,'giant sword missed real extended reach');return {baseline,grown,hits};
 }finally{Object.assign(p,original);p.anim.scale=original.scale;delete p.scale;A.reset();}
}'''

LIFECYCLE = r'''() => {
 const A=FAcceptance,p=A.p,F=A.F,out=[];
 for(const reason of ['pause','clear','death','unlearn','world','epoch']){
  A.reset();const m=A.fixture('lf2-column'),enemy=A.spawn(30,0),hits=A.watch(enemy);A.cast(m);
  const world=G.World;
  if(reason==='pause'){F.update(3);A.assert(!hits.length,'pause advanced damage');out.push({reason,hits});continue}
  if(reason==='clear')G.Combat.clearFields(p());if(reason==='death')p().dead=true;if(reason==='unlearn')p().moves=[];
  if(reason==='world')G.World={...world};if(reason==='epoch')G.CombatPulse.beginRun();
  try{A.advance(3)}finally{G.World=world;p().dead=false}
  A.assert(!hits.length,'cancel damage '+reason);out.push({reason,hits});
 }
 for(const reason of ['clear','unlearn','world']){
  A.reset();const m=A.fixture('lf2-column'),first=A.spawn(30,-3),second=A.spawn(30,3),h1=A.watch(first),h2=A.watch(second),world=G.World,hurt=first.hurt;
  first.hurt=function(...args){const result=hurt.apply(this,args);if(reason==='clear')G.Combat.clearFields(p());if(reason==='unlearn')p().moves=[];if(reason==='world')G.World={...world};return result};
  A.cast(m);try{A.advance(3)}finally{G.World=world}
  A.assert(h1.length===1,'first cancel victim never hit '+reason);A.assert(!h2.length,'same pulse second victim hit after '+reason);out.push({reason:'same-wave-'+reason,first:h1,second:h2});
 }
 A.reset();const m=A.fixture('lf2-column'),enemy=A.spawn(30,0),events=[],native=enemy.hurt;
 const clone=G.SelfClones.summon(p());A.assert(clone&&clone.moves!==p().moves,'clone failed independent move state');clone.x=clone.y=0;
 const cm=clone.moves.find(move=>move.id===m.id);cm.t=0;
 enemy.hurt=function(...args){events.push({ownerMain:args[6]===p(),ownerClone:args[6]===clone,id:args[7]});return native.apply(this,args)};
 A.resume();try{A.assert(F.cast(clone,cm),'clone cast rejected')}finally{A.pause()};F.clear(p());A.advance(.6);
 A.assert(events.length&&events.every(e=>e.ownerClone&&!e.ownerMain&&e.id===cm.id),'clone damage attribution/isolation failed');
 const before=events.length;clone.dead=true;A.advance(2);A.assert(events.length===before,'dead clone continued damage');out.push({cloneIsolation:true,events});
 return out;
}'''

OBSERVE = r'''() => {
 const Q=window.FreezeNatural={ledger:[],offers:[],offer:null,inputs:[],hits:[],samples:[],frames:[]};let last=-1;const seen=new Set();
 Q.snapshot=()=>{const p=G.Game.player;return p?{time:G.Game.st.time,level:p.level,hp:p.hp,maxHp:p.maxHp,dead:!!p.dead,x:p.x,y:p.y,moves:p.moves.map(m=>({id:m.id,rank:m.lvl})),stats:G.LF2Freeze.stats(p)}:null};
 const show=G.RunUI.showLevelUp;G.RunUI.showLevelUp=function(level,list,cb,...args){const offer={serial:Q.offers.length+1,time:G.Game.st.time,level,options:list.map(c=>({key:c.key,type:c.type,title:c.title,desc:c.desc}))};Q.offers.push(offer);Q.offer=offer;return show.call(this,level,list,c=>{const before=Q.snapshot();cb(c);Q.ledger.push({time:G.Game.st.time,level,key:c.key,before,after:Q.snapshot()});Q.offer=null},...args)};
 const hurt=G.Enemy.prototype.hurt;G.Enemy.prototype.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);if(args[6]===G.Game.player&&args[7]?.startsWith('lf2-'))Q.hits.push({time:G.Game.st.time,id:args[7],loss:hp-this.hp,target:this.id});return result};
 const draw=G.Combat.drawAirFields;G.Combat.drawAirFields=function(ctx){const result=draw.call(this,ctx),p=G.Game.player,s=p&&G.LF2Freeze.stateFor(p),pose=s?.action,keys=[];
  if(pose)keys.push((pose.kind||pose.mode)+'-'+pose.phase);
  for(const e of s?.effects||[]){if(e.age>=.4&&e.age<e.life-.2)keys.push(e.kind+'-independent');if(e.age>=e.life-.15)keys.push(e.kind+'-fade');}
  for(const key of keys)if(!seen.has(key)){seen.add(key);const snapshot=Q.snapshot(),state={key,snapshot,pose:pose?{mode:pose.mode,kind:pose.kind,phase:pose.phase,age:pose.age,aim:pose.aim}:null,effects:(s?.effects||[]).map(e=>({kind:e.kind,age:e.age,life:e.life,x:e.x,y:e.y,radius:e.radius}))};queueMicrotask(()=>Q.frames.push({...state,png:ctx.canvas.toDataURL()}));}
  return result;
 };
 function sample(){if(G.Game.state==='playing'){const s=Q.snapshot();if(s&&s.time-last>=1){last=s.time;Q.samples.push(s)}}requestAnimationFrame(sample)}requestAnimationFrame(sample);
}'''


def controlled(browser, report):
    context=browser.new_context(viewport={'width':1100,'height':850}, service_workers='block')
    page=context.new_page()
    page.on('pageerror',lambda e:report['errors'].append(e.stack or str(e)))
    boot(page)
    page.evaluate(SETUP)
    for name, check in [('progression',PROGRESSION),('mechanics',MECHANICS),('identity',IDENTITY),('growth',GROWTH),('lifecycle',LIFECYCLE)]:
        report['checks'][name]=page.evaluate(check)
        print(name,'PASS',flush=True)
    context.close()


def natural(browser, report, mobile=False):
    label='mobile390' if mobile else 'desktop'
    folder=OUT/f'natural-{label}'
    folder.mkdir(parents=True,exist_ok=True)
    viewport={'width':390,'height':844} if mobile else {'width':1100,'height':850}
    context=browser.new_context(viewport=viewport,is_mobile=mobile,has_touch=mobile,service_workers='block',record_video_dir=str(folder/'raw'),record_video_size=viewport)
    page=context.new_page()
    page.on('pageerror',lambda e:report['errors'].append(e.stack or str(e)))
    boot(page,label)
    # Install observers after the normal start; they change no game state.
    page.evaluate(OBSERVE)
    record={'policy':'Fresh save; native Lv1/HP/XP/AI/time; visible cards/items and '+('native touch joystick input only.' if mobile else 'keyboard input only.'),
            'initial':page.evaluate('FreezeNatural.snapshot()'),
            'permanent':page.evaluate('G.DB.upgradesOf(30018)')}
    assert record['initial']['level']==1 and not any(record['permanent'].values())
    started=time.monotonic();held=None;serial=None;last=-30;completed_at=None
    client=context.new_cdp_session(page) if mobile else None
    touch_active=False
    while time.monotonic()-started<360:
        data=page.evaluate('({state:G.Game.state,snapshot:FreezeNatural.snapshot(),offer:FreezeNatural.offer,hitIds:[...new Set(FreezeNatural.hits.filter(h=>h.loss>0).map(h=>h.id))],activeWhirlwind:!!G.LF2Freeze.stateFor(G.Game.player)?.effects.some(e=>e.kind==="whirlwind")})')
        snap=data['snapshot'];now=snap['time']
        if completed_at is None and all(id in data['hitIds'] for id in IDS):completed_at=now
        if completed_at is not None and now>=completed_at+5 and not data['activeWhirlwind']:break
        if snap['dead'] or data['state']=='over':break
        if now-last>=30:
            print(label,'natural',round(now),'Lv',snap['level'],'HP',round(snap['hp']),'moves',','.join(m['id'] for m in snap['moves']),flush=True);last=now
        if data['state']=='levelup' and data['offer'] and data['offer']['serial']!=serial:
            if held:
                if mobile:
                    client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});touch_active=False
                else:page.keyboard.up(held)
                held=None
            offer=data['offer']
            def priority(card):
                key=card['key']
                if key.startswith('new:lf2-'):return 0
                if key=='up:lf2-iceball':return 1
                if key=='stat:atk':return 2
                if key.startswith('up:lf2-'):return 3
                if key=='stat:quantity':return 4
                if key=='stat:cd':return 5
                return 9
            selected=min(range(len(offer['options'])),key=lambda i:(priority(offer['options'][i]),i))
            page.screenshot(path=str(folder/f'card-{offer["serial"]}-Lv{offer["level"]}.png'))
            page.locator('#cards .card').nth(selected).click();serial=offer['serial']
        elif page.locator('#scr-item').is_visible():page.locator('#item-cards .card').first.click()
        elif page.locator('#scr-bond').is_visible():page.locator('#bond-cards .card').first.click()
        elif data['state']=='paused':page.locator('#btn-resume').click()
        elif data['state']=='playing':
            key=['KeyD','KeyS','KeyA','KeyW'][int(now//1.4)%4]
            if key!=held:
                if mobile:
                    if touch_active:client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                    point=page.evaluate('G.Touch.stickBase()')
                    dx,dy={'KeyD':(36,0),'KeyS':(0,36),'KeyA':(-36,0),'KeyW':(0,-36)}[key]
                    client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]})
                    client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':point['x']+dx,'y':point['y']+dy}]})
                    touch_active=True
                else:
                    if held:page.keyboard.up(held)
                    page.keyboard.down(key)
                held=key
                page.evaluate('event=>FreezeNatural.inputs.push(event)',{'time':now,'key':key,'input':'touch' if mobile else 'keyboard'})
        page.wait_for_timeout(65)
    if held:
        if mobile:client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        else:page.keyboard.up(held)
    page.screenshot(path=str(folder/'final.png'))
    record.update(page.evaluate('({ledger:FreezeNatural.ledger,offers:FreezeNatural.offers,inputs:FreezeNatural.inputs,hits:FreezeNatural.hits,samples:FreezeNatural.samples,final:FreezeNatural.snapshot(),state:G.Game.state})'))
    record['frames']=[]
    import base64
    for frame in page.evaluate('FreezeNatural.frames'):
        png=frame.pop('png');name=frame['key']+'.png'
        (folder/name).write_bytes(base64.b64decode(png.split(',',1)[1]))
        record['frames'].append({'image':name,**frame})
    record['allSpecialsHit']=all(any(h['id']==id and h['loss']>0 for h in record['hits']) for id in IDS)
    record['allSpecialsFirstHitAt']=completed_at
    record['fullWhirlwindClosed']=completed_at is not None and record['final']['time']>=completed_at+5 and not data['activeWhirlwind']
    video=page.video;context.close();video.save_as(str(folder/'native-growth.webm'));video.delete()
    (folder/'report.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
    report['natural'][label]=record
    assert record['allSpecialsHit'] and record['fullWhirlwindClosed'],f'Natural run did not complete all four specials and cyclone closure: {record["final"]}'


def blade_clip(browser, report):
    """Short final-source native playback proving original blade contact frames."""
    import base64
    folder=OUT/'blade-current';folder.mkdir(parents=True,exist_ok=True)
    viewport={'width':1100,'height':850}
    context=browser.new_context(viewport=viewport,service_workers='block',record_video_dir=str(folder/'raw'),record_video_size=viewport)
    page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(e.stack or str(e)))
    boot(page,'blade-current')
    page.evaluate(SETUP)
    page.evaluate(r'''() => {
     const A=FAcceptance;A.reset();A.fixture('lf2-sword');const e=A.spawn(50,0),Q=window.BladeCurrent={frames:[],enemy:e,started:G.Game.st.time};
     const seen=new Set(),draw=G.Combat.drawAirFields;
     G.Combat.drawAirFields=function(ctx){const result=draw.call(this,ctx),p=A.p(),f=G.LF2Freeze.pose(p);
      if(f?.kind==='sword'&&f.age>=4/30&&f.age<=6/30&&!p.flash){const key=Math.cos(f.aim)<0?'left':'right';if(!seen.has(key)){seen.add(key);const frame={key,time:G.Game.st.time,age:f.age,aim:f.aim,swordOwned:G.LF2Freeze.stateFor(p).swordOwned,actorFlash:p.flash};queueMicrotask(()=>Q.frames.push({...frame,png:ctx.canvas.toDataURL()}));}}
      return result;
     };A.resume();
    }''')
    page.wait_for_function('G.Game.st.time-BladeCurrent.started>=3',timeout=15000)
    page.evaluate('BladeCurrent.enemy.x=-50;G.EnemyMgr.rebuildGrid()')
    page.wait_for_function('G.Game.st.time-BladeCurrent.started>=7',timeout=15000)
    data=page.evaluate('({frames:BladeCurrent.frames,stats:G.LF2Freeze.stats(G.Game.player),time:G.Game.st.time-BladeCurrent.started})')
    data['scope']='Controlled Lv30/rank1 sword only; zero-damage high-HP target; native RAF/body playback, no simulation clock stepping. Not natural progression.'
    for frame in data['frames']:
        png=frame.pop('png');name='active-'+frame['key']+'.png'
        (folder/name).write_bytes(base64.b64decode(png.split(',',1)[1]));frame['image']=name
    assert {f['key'] for f in data['frames']}=={'left','right'},'missing native blade direction active frames'
    video=page.video;context.close();video.save_as(str(folder/'native-blade.webm'));video.delete()
    report['blade']=data
    (folder/'report.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')


def final_clip(browser, report):
    """All four final-source cycles, isolated targets but native playback."""
    import base64
    folder=OUT/'final-cycles';folder.mkdir(parents=True,exist_ok=True)
    viewport={'width':1100,'height':850}
    context=browser.new_context(viewport=viewport,service_workers='block',record_video_dir=str(folder/'raw'),record_video_size=viewport)
    page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(e.stack or str(e)))
    boot(page,'final-cycles');page.evaluate(SETUP)
    page.evaluate(r'''() => {const A=FAcceptance;A.reset();const p=A.p();p.level=30;p.moves=['lf2-iceball','lf2-sword','lf2-column','lf2-whirlwind'].map(id=>G.Moves.instance(id,1));p.arrange();for(const m of p.moves)m.t=0;
     A.spawn(350,0);window.FinalCycleStart=G.Game.st.time;}''')
    page.evaluate(OBSERVE);page.evaluate('FAcceptance.resume()')
    page.wait_for_function('G.Game.st.time-FinalCycleStart>=1.7',timeout=10000)
    page.evaluate('for(const [x,y] of [[45,0],[125,20],[225,-20]])FAcceptance.spawn(x,y)')
    page.wait_for_function('G.Game.st.time-FinalCycleStart>=14',timeout=20000)
    data=page.evaluate('({frames:FreezeNatural.frames,stats:G.LF2Freeze.stats(G.Game.player),hits:FreezeNatural.hits,time:G.Game.st.time-FinalCycleStart})')
    data['scope']='Controlled Lv30/four rank1 skills, isolated zero-damage high-HP enemies; native RAF. No manual combat-clock stepping; not natural progression.'
    for frame in data['frames']:
        png=frame.pop('png');name=frame['key']+'.png';(folder/name).write_bytes(base64.b64decode(png.split(',',1)[1]));frame['image']=name
    assert all(data['stats']['casts'].get(id,0)>0 for id in IDS),'final native showcase omitted special'
    assert any(f['key']=='whirlwind-fade' for f in data['frames']),'final native showcase omitted cyclone wind-down'
    assert any(f['key']=='iceball-independent' for f in data['frames']),'final native showcase omitted flying ball'
    video=page.video;context.close();video.save_as(str(folder/'native-cycles.webm'));video.delete()
    report['finalCycles']=data
    (folder/'report.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--natural',action='store_true')
    parser.add_argument('--mobile',action='store_true')
    parser.add_argument('--blade',action='store_true')
    parser.add_argument('--final-cycles',action='store_true')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    report={'url':URL,'errors':[],'checks':{},'natural':{},'sourceBefore':hashes()}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            if args.final_cycles:final_clip(browser,report)
            elif args.blade:blade_clip(browser,report)
            elif args.natural:natural(browser,report,args.mobile)
            else:controlled(browser,report)
            browser.close()
        assert not report['errors'],report['errors']
        report['ok']=True
    except Exception as error:
        report['failure']=str(error)
        raise
    finally:
        report['sourceAfter']=hashes();report['sourceStable']=report['sourceBefore']==report['sourceAfter']
        name='final-cycles-source.json' if args.final_cycles else 'blade-current-source.json' if args.blade else 'natural-mobile-report.json' if args.natural and args.mobile else 'natural-report.json' if args.natural else 'report.json'
        (OUT/name).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')


if __name__=='__main__':main()
