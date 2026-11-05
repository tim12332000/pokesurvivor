"""Acceptance for the three Sendai characters through the production entry.

Run tools/serve_animation_lab.py --port 8337 first. Fixtures only clear terrain
and hold the clock; casts, collision, cards, damage accounting and art are native.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('JUJUTSU_OUT',str(ROOT / '.omx/state/jujutsu')))
URL = os.environ.get('JUJUTSU_URL', 'http://127.0.0.1:8337/.omx/digimon.html?lang=zh-TW&test=jujutsu')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
HEROES = {30013: 'yuta', 30014: 'ryu', 30015: 'uro'}

SETUP = r"""() => {
 const p=()=>G.Game.player,assert=(ok,msg)=>{if(!ok)throw Error(msg)};
 function pause(){if(G.Game.state==='playing')G.Game.togglePause();G.UI.hide('scr-pause')}
 function resume(){if(G.Game.state==='paused')G.Game.togglePause();assert(G.Game.state==='playing','not playing '+G.Game.state)}
 function reset(){G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();G.SelfClones?.clear();G.Pickups.clear();
  G.World.collide=()=>{};G.World.isWall=()=>false;G.World.isFree=()=>true;G.World.isLiquid=()=>false;
  G.World.projectileBlock=()=>false;G.World.propsInCircle=()=>[];
  const a=p();a.x=a.y=0;a.hp=a.maxHp;a.dead=false;a.frozen=false;a.flash=0;a.invuln=0;
  a.target=null;a.aim=0;a.attackFace=0;a.walking=false;a.critChance=0;a.item=null;
  a.percentHealthDamage=a.lifestealRate=a.damageSplashPicks=a.quantityPicks=a.quantityBonus=0;
  a.cdMul=1;a.xp=0;a.xpNext=1e12;G.Camera.x=G.Camera.y=0;for(const m of a.moves)m.t=999;pause();}
 function spawn(x,y,special=null){const e=new G.Enemy({dex:19,hp:1000000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1},special==='boss');
  e.types=['normal'];if(special)e[special]=true;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e}
 function watch(e){const events=[],hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);
  events.push({raw:args[0],loss:hp-this.hp,owner:args[6]===p(),id:args[7]});return result};return events}
 function fixture(id,rank=1){const a=p();G.Combat.clearFields(a);a.level=30;a.moves=[];a.slots=[];a.active=0;a.maxMoves=5;a.bind={};
  assert(a.addMove(id),'cannot add fixture '+id);const m=a.moves.find(m=>m.id===id);Object.assign(m,G.Moves.instance(id,rank));a.arrange();
  const slot=a.slots.findIndex(g=>g.includes(m));if(slot>=0)a.setActive(slot);for(const move of a.moves)move.t=move===m?0:999;return m}
 function step(dt=.01,tick=false){resume();try{if(tick)G.Combat.tick(dt,p(),0);p().anim.update(dt);
  G.Projectiles.update(dt,p(),G.EnemyMgr.all());G.Combat.resolve(dt,p(),0);G.Combat.updateFields(dt)}finally{pause()}}
 function advance(seconds,tick=false){let left=seconds;while(left>1e-9){const dt=Math.min(.01,left);step(dt,tick);left-=dt}}
 function cast(id){const a=p(),m=a.moves.find(m=>m.id===id);assert(m,'unlearned '+id);
  const slot=a.slots.findIndex(g=>g.includes(m));if(slot>=0)a.setActive(slot);advance(.11);
  for(const move of a.moves)move.t=move===m?0:999;let calls=0;const original=a.cast;
  a.cast=function(move,...args){if(move.id===id)calls++;return original.call(this,move,...args)};
  // Deliberate isolated casts exercise production geometry; identity suites
  // separately drive Combat.tick to verify conditional automatic decisions.
  const module=a.dex===30013?G.JujutsuYuta:a.dex===30014?G.JjkRyu:G.JjkUro;
  resume();try{module.cast(a,m)}finally{a.cast=original;pause()}
  assert(calls===1,'native cast count '+id+': '+calls);return m}
 function pose(){const c=document.createElement('canvas');c.width=340;c.height=280;const ctx=c.getContext('2d',{willReadFrequently:true}),calls=[],draw=ctx.drawImage.bind(ctx);
  ctx.drawImage=(im,...rect)=>{calls.push({source:im.src||im.dataset?.source||'',rect});return draw(im,...rect)};
  p().anim.draw(ctx,170,220);const rgba=ctx.getImageData(0,0,c.width,c.height).data;let pixels=0;
  for(let i=3;i<rgba.length;i+=4)if(rgba[i]>30)pixels++;
  assert(pixels>80&&calls.length,'empty production actor');assert(calls.every(c=>/jjk|jujutsu/i.test(c.source)),'wrong/fallback art '+JSON.stringify(calls));
  return {calls,pixels,animation:p().anim.cur,png:c.toDataURL()}}
 window.JAcceptance={p,assert,pause,resume,reset,spawn,watch,fixture,step,advance,cast,pose};pause();
}"""

PROGRESSION = r"""slug => {
 const A=JAcceptance,p=A.p(),prefix='jjk-'+slug,ids=Object.keys(G.Moves.BY_ID).filter(id=>id===prefix||id.startsWith(prefix+'-'));
 A.assert(ids.length>=3,'fewer than three skills '+ids);A.assert(p.moves.length===1&&p.moves[0].id===prefix,'unexpected starter '+p.moves.map(m=>m.id));
 const out={starter:p.moves[0].id,skills:ids,levels:[]};
 for(const level of [1,2,3,5,6,8,9,11,12]){p.level=level;const pool=G.Moves.poolFor(p.mon),cards=G.LevelUp.offer(p,100);
  for(const id of ids){const expected=level>=G.Moves.BY_ID[id].learnLevel;A.assert(pool.includes(id)===expected,'wrong level gate '+id+' at '+level);
    if(id!==prefix)A.assert(cards.some(c=>c.key==='new:'+id)===expected,'wrong learn card gate '+id+' at '+level);}
  A.assert(!pool.some(id=>id.startsWith('jjk-')&&!ids.includes(id)),'foreign JJK pool');
  A.assert(!cards.some(c=>c.key?.startsWith('new:jjk-')&&!ids.includes(c.key.slice(4))),'foreign JJK card');
  out.levels.push({level,pool:pool.filter(id=>id.startsWith('jjk-')),cards:cards.filter(c=>c.key?.startsWith('new:jjk-')).map(c=>c.key)});}
 p.level=30;for(const id of ids.filter(id=>id!==prefix)){const c=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(c&&c.apply(p)!==false,'native learn '+id)}
 A.assert(ids.every(id=>p.hasMove(id)),'missing learned skills');const mon=p.mon;
 for(const dex of [30001,30007,30011,30012,30013,30014,30015]){if(dex===mon.dex)continue;p.mon=G.DEX_BY[dex];
  A.assert(!G.Moves.poolFor(p.mon).some(id=>ids.includes(id)),'own skills leaked to '+dex)}p.mon=mon;
 return out;
}"""

def hashes():
    names=['.omx/jujutsu.js','.omx/jujutsu-art.js','.omx/jjk-yuta.js','.omx/jjk-ryu.js','.omx/jjk-uro.js','.omx/naruto.js','.omx/redrawn-init.js','.omx/digimon.html','js/game.js']
    runtime=ROOT/'dist-digimon' if '/dist-digimon/' in URL else ROOT
    for name in ['art-review/jjk-frames.json','art-review/jjk-skills-v2.json']:
        if not (runtime/name).exists():continue
        names.append(name)
        metadata=json.loads((runtime/name).read_text(encoding='utf8'))
        names.extend('art-review/'+sheet['source'] for sheet in metadata['sheets'].values())
    return {name: hashlib.sha256((runtime/name).read_bytes()).hexdigest() for name in names if (runtime/name).exists()}


def frame_for(page):
    for _ in range(300):
        for frame in page.frames:
            try:
                if frame.evaluate("typeof G==='object'&&!!G.Game&&!!G.JujutsuYuta&&!!G.JjkRyu&&!!G.JjkUro"):
                    return frame
            except Exception:
                pass
        page.wait_for_timeout(100)
    raise AssertionError('JJK production runtime did not load')


def save_pose(name, data):
    (OUT/f'{name}.png').write_bytes(base64.b64decode(data.pop('png').split(',',1)[1]))
    return data


def boot(page, dex, label):
    page.goto(URL+('&layout=wide' if label=='desktop' else ''))
    frame=frame_for(page)
    frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if frame.locator('#tap-start').is_visible():frame.locator('#tap-start').click()
    frame.locator(f'[data-quick-naruto="{dex}"]').click()
    assert frame.evaluate(f'G.DB.save.partner==={dex}'), 'normal picker failed'
    frame.wait_for_function(f'G.NarutoAssets.ready({dex})')
    page.wait_for_timeout(80)
    page.screenshot(path=str(OUT/f'{label}-{dex}-selection.png'))
    frame.locator('#scr-menu [data-go="play"]').click()
    frame.wait_for_function(f'G.Game.player?.dex==={dex}&&G.Game.state==="playing"')
    page.screenshot(path=str(OUT/f'{label}-{dex}-normal-entry.png'))
    frame.evaluate(SETUP)
    return frame


def input_art(page,frame,label,slug,context,mobile):
    frame.evaluate('JAcceptance.reset()')
    if frame!=page.main_frame:page.locator('iframe').first.focus()
    result={}
    for direction,key in [('right','KeyD'),('left','KeyA'),('down','KeyS'),('up','KeyW')]:
        page.keyboard.down(key)
        result[direction]=frame.evaluate("""()=>{const A=JAcceptance,p=A.p(),before=[p.x,p.y];A.resume();try{p.update(.08)}finally{A.pause()}
          A.assert(p.walking&&Math.hypot(p.x-before[0],p.y-before[1])>0,'keyboard did not move');return {dx:p.x-before[0],dy:p.y-before[1],dir:p.anim.dir}}""")
        page.keyboard.up(key)
        result[direction]['pose']=save_pose(f'{label}-{slug}-{direction}',frame.evaluate('JAcceptance.pose()'))
    if mobile:
        frame.evaluate('JAcceptance.reset();JAcceptance.resume()')
        client=context.new_cdp_session(page);base=frame.evaluate('G.Touch.stickBase()');offset={'x':0,'y':0}
        if frame!=page.main_frame:
            box=page.locator('iframe').first.bounding_box();offset={'x':box['x'],'y':box['y']}
        point={'x':base['x']+offset['x'],'y':base['y']+offset['y']}
        client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]})
        client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':point['x']+42,'y':point['y']}]})
        result['touch']=frame.evaluate("""()=>{const A=JAcceptance,p=A.p(),x=p.x;A.assert(G.Touch.vector()[0]>0,'touch vector missing');p.update(.08);A.pause();A.assert(p.x>x,'touch did not move');return p.x-x}""")
        client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
    assert not frame.evaluate('document.documentElement.scrollWidth>innerWidth'), 'horizontal overflow'
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'url':URL,'sourceHashes':hashes(),'viewports':{},'errors':[],'failedRequests':[],'failures':[]}
    selected=os.environ.get('JUJUTSU_HEROES','yuta,ryu,uro').split(',')
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME,headless=True)
        for label,viewport,mobile in [('desktop',{'width':1280,'height':900},False),('mobile',{'width':390,'height':844},True)]:
            for dex,slug in HEROES.items():
                if slug not in selected:continue
                context=browser.new_context(viewport=viewport,is_mobile=mobile,has_touch=mobile,service_workers='block');page=context.new_page()
                page.on('pageerror',lambda e:report['errors'].append(e.stack or str(e)))
                page.on('response',lambda response:report['failedRequests'].append({'url':response.url,'status':response.status}) if response.status>=400 else None)
                result=report['viewports'][label+'-'+slug]={}
                try:
                    print(label,slug,'boot',flush=True);frame=boot(page,dex,label)
                    result['progression']=frame.evaluate(PROGRESSION,slug)
                    result['inputAndArt']=input_art(page,frame,label,slug,context,mobile)
                    result['combat']=combat(page,frame,label,slug)
                    result['special']=special(frame,slug,label)
                    result['props']=frame.evaluate(r"""slug=>{const A=JAcceptance,p=A.p();A.reset();const id='jjk-'+slug;A.fixture(id);
                      const prop={x:65,y:0,r:12,type:'chest',solid:true,destructible:true,hp:1,tx:999999,ty:999999};
                      G.World.propsInCircle=(x,y,r)=>prop.hp>0&&Math.hypot(prop.x-x,prop.y-y)<=r+prop.r?[prop]:[];
                      G.World.projectileBlock=(x,y,r)=>prop.hp>0&&Math.hypot(prop.x-x,prop.y-y)<prop.r+r?prop:false;
                      const damage=G.World.damageProp,events=[];G.World.damageProp=function(target,amount,...rest){events.push({same:target===prop,amount});return damage.call(this,target,amount,...rest)};
                      try{A.cast(id);A.advance(1)}finally{G.World.damageProp=damage}
                      A.assert(prop.hp<=0&&events.length&&events.every(e=>e.same),'no-enemy chest could not be destroyed');return {hp:prop.hp,events};}""",slug)
                except Exception as e:
                    report['failures'].append(label+':'+slug+': '+str(e))
                    page.screenshot(path=str(OUT/f'{label}-{slug}-failure.png'))
                finally:
                    context.close();(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        browser.close()
    report['sourceHashesAfter']=hashes()
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime changed during acceptance; rerun')
    report['ok']=not(report['errors'] or report['failedRequests'] or report['failures'])
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'errors':report['errors'],'evidence':str(OUT)},ensure_ascii=True))
    if not report['ok']:raise SystemExit(1)


def combat(page,frame,label,slug):
    cases={
        'yuta': [('jjk-yuta', [[65,0],[85,25],[90,-25]], [350,0], .45),
                 ('jjk-yuta-rika', [[170,0],[205,30],[210,-30]], [410,210], 1.8),
                 ('jjk-yuta-speech', [[70,0],[-75,40],[35,-95]], [390,0], .6)],
        'ryu': [('jjk-ryu', [[90,0],[165,0],[240,0]], [170,100], .6),
                ('jjk-ryu-spread', [[140,0],[120,91],[120,-91]], [270,0], .85),
                ('jjk-ryu-impact', [[180,0],[210,35],[210,-35]], [410,0], .7),
                ('jjk-ryu-maximum', [[100,0],[200,0],[320,0]], [170,300], 1)],
        'uro': [('jjk-uro', [[70,0],[100,25],[115,-25]], [-250,0], .6),
                ('jjk-uro-thin-ice', [[90,0],[145,55],[145,-55]], [-250,0], .7),
                 ('jjk-uro-collapse', [[180,0],[210,35],[210,-35]], [1000,400], .9)]}
    results=[]
    for skill,inside,outside,seconds in cases[slug]:
        print(label,slug,skill,flush=True)
        result=frame.evaluate(r"""({skill,inside,outside,seconds})=>{
          const A=JAcceptance,p=A.p();A.reset();const m=A.fixture(skill);
          const enemies=inside.map(([x,y])=>A.spawn(x,y)),out=A.spawn(...outside),logs=enemies.map(A.watch),outLog=A.watch(out);
          p.target=enemies[0];const dealt=p.dmgDealt;A.cast(skill);A.advance(seconds);
          const losses=enemies.map(e=>e.maxHp-e.hp);
          A.assert(losses.every(d=>d>0),'AOE missed valid target '+skill+' '+losses);
          A.assert(out.hp===out.maxHp&&!outLog.length,'AOE hit out-of-range target '+skill);
          A.assert(logs.flat().every(h=>h.owner&&h.id===skill&&h.loss>0),'wrong damage attribution '+skill);
          A.assert(m.dealt>0&&p.dmgDealt>dealt,'damage stats missing '+skill);
          return {skill,inside,outside,losses,hits:logs,moveDealt:m.dealt,ownerDealt:p.dmgDealt-dealt,art:A.pose()};
        }""",{'skill':skill,'inside':inside,'outside':outside,'seconds':seconds})
        result['art']=save_pose(f'{label}-{slug}-{skill}-cast',result['art']);results.append(result)
    # A cancelled telegraph must never deal its pending hit, including after a
    # pause/death/clear; use a delayed attack for each character.
    skill=cases[slug][1][0]
    lifecycle=frame.evaluate(r"""skill=>{
      const A=JAcceptance,p=A.p(),out={};
      for(const kind of ['pause','clear','death']){A.reset();A.fixture(skill);const e=A.spawn(100,0);p.target=e;A.cast(skill);
        if(kind==='pause'){G.Combat.updateFields(2);A.assert(e.hp===e.maxHp,'paused cast dealt damage');A.advance(1);A.assert(e.hp<e.maxHp,'resume did not release cast');}
        else{if(kind==='clear')G.Combat.clearFields(p);else p.dead=true;
          A.advance(1);A.assert(e.hp===e.maxHp,'cancelled cast dealt damage '+kind);}
        out[kind]={loss:e.maxHp-e.hp};}
      A.reset();const m=A.fixture(skill),e=A.spawn(100,0);p.target=e;A.cast(skill);const first=m.t;
      A.advance(.1,true);A.assert(e.hp===e.maxHp,'attack released before telegraph');out.cooldown={afterCast:first,afterTick:m.t};
      A.reset();A.fixture('jjk-'+(p.dex===30013?'yuta':p.dex===30014?'ryu':'uro'));const victim=A.spawn(60,0);victim.hp=1;const kills=p.kills;
      p.target=victim;A.cast(p.moves[0].id);A.advance(1);A.assert(victim.dead,'real damage did not kill');
      A.resume();try{G.EnemyMgr.update(.001,p,0)}finally{A.pause()};A.assert(p.kills===kills+1,'native kill accounting missing');out.killDelta=p.kills-kills;
      A.reset();A.fixture(skill);const abandoned=A.spawn(100,0);p.target=abandoned;A.cast(skill);const previous=p;
      G.Game.startRun();A.pause();const current=A.p();A.assert(current!==previous,'native restart did not create fresh player');
      const api=current.dex===30013?G.JujutsuYuta:current.dex===30014?G.JjkRyu:G.JjkUro;
      A.assert(!api.stateFor(previous),'previous run combat state survived restart');
      A.assert(current.moves.length===1&&current.moves[0].id==='jjk-'+(current.dex===30013?'yuta':current.dex===30014?'ryu':'uro'),'restart leaked learned skills');
      A.advance(1);A.assert(abandoned.hp===abandoned.maxHp,'old pending cast damaged after new run');out.restart=true;
      return out;
    }""",skill)
    frame.evaluate('JAcceptance.reset();JAcceptance.resume()');page.wait_for_timeout(100)
    page.screenshot(path=str(OUT/f'{label}-{slug}-gameplay.png'));frame.evaluate('JAcceptance.pause()')
    return {'aoe':results,'lifecycle':lifecycle}


def special(frame,slug,label):
    if slug=='yuta':
        result=frame.evaluate(r"""()=>{
          const A=JAcceptance,p=A.p(),Y=G.JujutsuYuta,out={forms:[]};
          function blade(rank){A.reset();const m=A.fixture('jjk-yuta'),e=A.spawn(70,0);p.target=e;
            if(rank){p.addMove('jjk-yuta-manifest');Object.assign(p.moves.find(m=>m.id==='jjk-yuta-manifest'),G.Moves.instance('jjk-yuta-manifest',rank));
              A.cast('jjk-yuta-manifest');A.advance(.6);}
            A.cast('jjk-yuta');A.advance(.3);return e.maxHp-e.hp;}
          const base=blade(0),rank1=blade(1),rank5=blade(5);A.assert(rank1>base&&rank5>rank1,'manifest rank damage did not scale');out.damage={base,rank1,rank5};
          A.reset();A.fixture('jjk-yuta-manifest');const e=A.spawn(150,0);p.target=e;const before={atk:p.atk,maxHp:p.maxHp};
          A.cast('jjk-yuta-manifest');A.assert(Y.manifested(p),'manifest never entered');A.advance(8.1);
          A.assert(!Y.manifested(p)&&p.atk===before.atk&&p.maxHp===before.maxHp,'manifest expiration/stat drift');out.expiry={before,after:{atk:p.atk,maxHp:p.maxHp}};
          A.reset();A.fixture('jjk-yuta-speech');const normal=A.spawn(100,0),boss=A.spawn(120,30,'boss');normal.spd=boss.spd=60;p.target=normal;
          A.cast('jjk-yuta-speech');A.advance(.3);const x=[normal.x,boss.x];A.resume();try{normal.update(.1,p,0);boss.update(.1,p,0)}finally{A.pause()}
          A.assert(normal.x===x[0]&&boss.x<x[1],'speech normal/boss movement resistance failed');out.speech={normal:normal.x-x[0],boss:boss.x-x[1]};
          A.reset();A.fixture('jjk-yuta-rika');p.target=A.spawn(130,0);A.cast('jjk-yuta-rika');A.advance(.25);
          const c=document.createElement('canvas');c.width=700;c.height=400;const ctx=c.getContext('2d'),calls=[],draw=ctx.drawImage.bind(ctx);
          ctx.drawImage=(im,...rect)=>{calls.push({source:im.src||'',rect});return draw(im,...rect)};ctx.translate(250,250);
          for(const node of Y.drawables(G.Camera))node.draw(ctx);G.Combat.drawAirFields(ctx);
          A.assert(calls.some(c=>/rika/i.test(c.source)),'independent Rika sprite missing');out.rika={calls,png:c.toDataURL()};
          return out;
        }""")
        result['rika']=save_pose(f'{label}-yuta-rika-independent',result['rika'])
        return result
    if slug=='uro':
        return frame.evaluate(r"""()=>{
          const A=JAcceptance,p=A.p(),U=G.JjkUro;A.reset();const m=A.fixture('jjk-uro-screen');p.target=A.spawn(70,0);
          G.Projectiles.spawn({x:150,y:0,vx:-200,vy:0,r:6,friendly:false,dmg:7,mtype:'psychic',life:2});A.cast(m.id);G.Projectiles.clear();
          const first=m.t,s=U.stateFor(p),capacity=s.screen.budget,reflected=[];
          const friendly=G.Projectiles.spawn({x:60,y:30,vx:-100,vy:0,friendly:true,owner:p,mid:'test-friendly'});
          function incoming(){return G.Projectiles.spawn({x:60,y:0,px:120,py:0,vx:-100,vy:0,friendly:false,dmg:7,mtype:'psychic',life:2})}
          for(let i=0;i<capacity;i++){const shot=incoming();A.resume();try{U.intercept()}finally{A.pause()};
            A.assert(!G.Projectiles.all().includes(shot),'hostile projectile was not removed');}
          for(const shot of G.Projectiles.all().filter(p=>p.uroReturned)){A.assert(shot.friendly&&shot.owner===p&&shot.mid===m.id&&shot.vx>0,'reflection owner/direction');reflected.push({mid:shot.mid,vx:shot.vx})}
          A.assert(reflected.length===capacity&&G.Projectiles.all().includes(friendly),'friendly affected or finite budget mismatch');
          const extra=incoming();A.resume();try{U.intercept()}finally{A.pause()};A.assert(G.Projectiles.all().includes(extra),'screen exceeded finite budget');
          A.advance(2.4);A.assert(!U.stateFor(p).screen,'screen did not expire');A.assert(first===9,'screen base CD must be9s');
          A.advance(.1,true);A.assert(m.t>6&&m.t<9,'screen cooldown reset or not progressing');
          return {capacity,reflected,initialCooldown:first,remainingCooldown:m.t,intercepted:U.stateFor(p).intercepted};
        }""")
    return {'artillery':'all four telegraphed damage modes and cleanup checked above'}


if __name__=='__main__':main()
