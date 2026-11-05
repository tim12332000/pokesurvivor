"""Yuta's independent spoken stop against native enemy attacks and contact."""
from __future__ import annotations
import json
import base64
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_jujutsu as base

OUT = Path(os.environ.get('YUTA_SPEECH_OUT', base.ROOT / '.omx/state/yuta-speech'))
CHECK = r"""() => {
 const A=JAcceptance,Y=G.JujutsuYuta,p=A.p(),assert=A.assert,out={},ids={blade:'jjk-yuta',rika:'jjk-yuta-rika',manifest:'jjk-yuta-manifest',speech:'jjk-yuta-speech'};
 const nativePath=G.World.projectilePathClear;
 function setup(names=['speech'],rank=1){A.reset();G.World.projectilePathClear=nativePath;A.fixture(ids[names[0]],rank);
  for(const name of names.slice(1))assert(p.addMove(ids[name]),'learn '+name);
  for(const m of p.moves){Object.assign(m,G.Moves.instance(m.id,rank));m.t=999;}p.invuln=0;p.atk=1;
  return Object.fromEntries(names.map(name=>[name,p.moves.find(m=>m.id===ids[name])]));}
 function cast(m){m.t=0;A.resume();try{assert(Y.cast(p,m),'cast '+m.id)}finally{A.pause()};return Y.stateFor(p);}
 function enemy(x,y,behavior='chase',boss=false){const e=new G.Enemy({dex:19,hp:1000000,spd:90,dmg:12,xp:0,behavior,range:360,shotCd:1,shotDmg:10},x,y,{hp:1,spd:1,dmg:1},boss);
  e.types=['normal'];e.shotCd=0;e.touchCd=0;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;}
 function tickEnemy(e,dt){A.resume();try{e.update(dt,p)}finally{A.pause()}}
 let m=setup(['blade','speech']),e=enemy(70,0);cast(m.blade);let s=Y.stateFor(p),body=s.action;
 A.resume();try{assert(Y.canCast(p,Object.assign(m.speech,{t:0})),'speech blocked by sword body action')}finally{A.pause()};cast(m.speech);
 assert(s.action===body&&s.speech&&s.speech.cast.channel==='reaction','speech replaced body or lacks reaction clock');
 A.advance(.25);assert(Y.stopped(e)&&s.casts.speech===1,'speech did not stop native enemy');out.bodyReaction=true;

 m=setup(['rika','manifest','blade','speech'],5);e=enemy(300,0);cast(m.manifest);cast(m.rika);s=Y.stateFor(p);
 while(!s.rika||s.rika.phase!=='strike'||s.action)A.advance(.01);
 const actor=s.rika,castId=actor.castId,index=actor.strikeIndex;cast(m.speech);A.advance(.25);
 assert(s.rika===actor&&actor.castId===castId&&actor.strikeIndex>=index&&Y.stopped(e),'speech interrupted full duet');
 out.duetReaction={sameActor:true,castId,continuedPunches:actor.strikeIndex-index};

 // The same real ranged enemy fires without the skill; its pending shot and
 // movement stay frozen with the skill while unrelated status clocks age.
 for(const useSpeech of [false,true]){
  m=setup();e=enemy(170,0,'ranged');let shots=0;const special=e.special;e.special=function(...args){shots++;return special.apply(this,args)};
  if(useSpeech){cast(m.speech);A.advance(.25);}
  const origin={x:e.x,y:e.y},shotCd=e.shotCd;e.applySlow(.35,1);e.burn=1;e.burnT=1;e.burnTick=0;e.poison=1;e.poisonT=1;e.poisonTick=0;
  const hp=e.hp;for(let i=0;i<5;i++){tickEnemy(e,.1);A.advance(.1);}
  if(useSpeech)assert(shots===0&&e.shotCd===shotCd&&e.x===origin.x&&e.y===origin.y,'stopped enemy acted');else assert(shots>0,'no-skill ranged enemy did not attack');
  assert(e.hp<hp&&e.slowT<.6&&e.burnT<.6&&e.poisonT<.6,'stop froze DOT or external status aging');
  out[useSpeech?'withSpeech':'withoutSpeech']={shots,displacement:Math.hypot(e.x-origin.x,e.y-origin.y),dotLoss:hp-e.hp,slowRemaining:e.slowT};
 }

 // Control protects an actual contact overlap, then restores native contact.
 m=setup();e=enemy(10,0);cast(m.speech);A.advance(.25);p.invuln=0;let hurt=0,oldHurt=p.hurt;p.hurt=function(...args){hurt++;return oldHurt.apply(this,args)};
 try{A.step(.01);assert(hurt===0,'stopped enemy dealt contact damage');A.advance(2.1);e.touchCd=0;p.invuln=0;A.step(.01);assert(hurt>0,'contact failed to resume');}finally{p.hurt=oldHurt}
 out.contact={stoppedHits:0,resumedHits:hurt};

 // A projectile already in flight remains a separate live threat.
 m=setup();e=enemy(100,0);const bullet=G.Projectiles.spawn({x:220,y:0,vx:-80,vy:0,dmg:10,r:5,life:5,friendly:false,color:'#ff7755',mtype:'normal'});
 cast(m.speech);A.advance(.25);assert(G.Projectiles.all().includes(bullet)&&bullet.x<220,'speech deleted or froze a fired projectile');
 out.inFlight={alive:true,x:bullet.x};

 for(const rank of [1,3,5])for(const boss of [false,true]){
  m=setup(['speech'],rank);e=enemy(100,0,'ranged',boss);cast(m.speech);A.advance(.25);
  const expected=G.Jujutsu.power.yuta[boss?'speechBossDurations':'speechDurations'][rank-1],status=Y.stopStatus(e);
  assert(status&&Math.abs(status.duration-expected)<1e-8,'rank/strong duration differs');
  e.shotCd=0;let shots=0;const special=e.special;e.special=function(...args){shots++;return special.apply(this,args)};
  tickEnemy(e,.1);assert(e.shotCd===0,'pending attack countdown advanced');
  A.advance(expected+.02);assert(!Y.stopped(e),'stop duration failed to expire');tickEnemy(e,.01);
  assert(shots===0,'expired control instantly fired without a readable restart');
  tickEnemy(e,.2);if(!boss)assert(shots===1,'pending shot did not resume after short read');
  out['duration'+rank+(boss?'Boss':'Normal')]={expected,expired:true};
 }
 m=setup();const inRange=[enemy(80,0),enemy(-100,60),enemy(0,-180)],outside=enemy(500,0),blocked=enemy(0,200);
 G.World.projectilePathClear=(x,y,tx,ty)=>ty<190;cast(m.speech);A.advance(.25);
 assert(inRange.every(e=>Y.stopped(e))&&!Y.stopped(outside)&&!Y.stopped(blocked),'speech radius/obstacle contract failed');out.geometry=true;
 m=setup();const dense=[enemy(80,0),enemy(81,0),enemy(82,0)];cast(m.speech);A.advance(.25);
 const denseBefore=dense.map(e=>({x:e.x,y:e.y}));
 A.resume();try{G.EnemyMgr.update(.1,[p])}finally{A.pause()};
 assert(dense.every((e,i)=>e.x===denseBefore[i].x&&e.y===denseBefore[i].y),'enemy manager separation moved stopped crowd');out.denseCrowd=true;
 for(const rank of [1,3,5]){
  m=setup(['speech'],rank);const near=enemy(230,0),middle=enemy(270,0),far=enemy(310,0);cast(m.speech);A.advance(.25);
  const count=[near,middle,far].filter(e=>Y.stopped(e)).length;
  assert(count===(rank===1?1:rank===3?2:3),'rank radius did not add real targets');out['rankCoverage'+rank]=count;
 }
 for(const cancel of ['clear','unlearn']){
  m=setup();const victims=[enemy(80,0),enemy(100,20)];let direct=0;
  for(const victim of victims){const hurt=victim.hurt;victim.hurt=function(...args){direct++;const result=hurt.apply(this,args);
   if(cancel==='clear')G.Combat.clearFields(p);else p.moves=[];return result;};}
  cast(m.speech);A.advance(.3);assert(direct===1&&victims.every(e=>!Y.stopped(e)),'same-wave cancellation retained damage/control '+cancel);out['sameWave-'+cancel]=true;
 }
 for(const cancel of ['clear','unlearn','dead','world']){
  m=setup();e=enemy(100,0);cast(m.speech);A.advance(.25);assert(Y.stopped(e),'cancel fixture not stopped');
  if(cancel==='clear')G.Combat.clearFields(p);if(cancel==='unlearn')p.moves=[];if(cancel==='dead'){p.dead=true;p.hp=0;}
  if(cancel==='world'){const world=G.World;G.World={...world};assert(!Y.stopped(e),'world change retained control');G.World=world;G.Combat.clearFields(p);}
  assert(!Y.stopped(e),'stop survived '+cancel);out['cancel-'+cancel]=true;
 }
 return out;
}"""

NATIVE = r"""useSpeech => {
 const A=JAcceptance,p=A.p();A.reset();A.fixture('jjk-yuta');p.level=6;p.maxHp=p.hp=1000;p.invuln=0;p.atk=1;p.xpNext=1e12;
 if(useSpeech)A.assert(p.addMove('jjk-yuta-speech'),'native learn speech');
 for(const m of p.moves)m.t=m.id==='jjk-yuta-speech'?0:999;
 G.Spawner.update=()=>{};const run=window.SpeechNative={useSpeech,shots:0,contactAttempts:0,started:G.Game.st.time,initialHp:p.hp,controlSamples:0};
 for(const [x,y,behavior] of [[60,0,'chase'],[-60,0,'chase'],[0,70,'chase'],[170,-50,'ranged']]){
  const e=new G.Enemy({dex:19,hp:1000000,spd:40,dmg:12,xp:0,behavior,range:360,shotCd:1,shotDmg:10},x,y,{hp:1,spd:1,dmg:1});
  e.types=['normal'];e.shotCd=.1;e.touchCd=0;const special=e.special;e.special=function(...args){run.shots++;return special.apply(this,args)};
  G.EnemyMgr.add(e);
 }
 G.EnemyMgr.rebuildGrid();const hurt=p.hurt;p.hurt=function(damage,type,ignore,info,...args){if(info?.cause==='contact')run.contactAttempts++;return hurt.call(this,damage,type,ignore,info,...args)};
 const label=document.createElement('div');label.id='speech-evidence-label';label.style='position:fixed;top:90px;left:8px;right:8px;z-index:99999;background:#241d35e8;color:#fff;padding:8px;font:13px sans-serif;pointer-events:none';
 label.textContent=(useSpeech?'有別動':'無別動')+'｜Lv6・一階・0成長卡｜受控敵人，原生自動戰鬥';document.body.append(label);
 G.Game.debugSpeed(1);A.resume();return {level:6,rank:1,cards:0,useSpeech,controlledEnemies:true};
}"""

def record_native(page,frame,label,use_speech):
    fixture=frame.evaluate(NATIVE,use_speech)
    frame.evaluate("""()=>{const stream=document.getElementById('game').captureStream(24),recorder=new MediaRecorder(stream,{mimeType:'video/webm',videoBitsPerSecond:1800000}),chunks=[];
     recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
     window.SpeechClip={recorder,stream,done:new Promise(resolve=>recorder.onstop=()=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}))})};recorder.start();}""")
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT/f'{label}-stopped.png'))
    page.wait_for_timeout(2700)
    result=frame.evaluate("""async()=>{JAcceptance.pause();const c=SpeechClip;c.recorder.stop();const data=await c.done;for(const t of c.stream.getTracks())t.stop();
     const run=SpeechNative,p=JAcceptance.p();document.getElementById('speech-evidence-label')?.remove();
     return {data,shots:run.shots,contactAttempts:run.contactAttempts,hpLoss:run.initialHp-p.hp,speechCasts:G.JujutsuYuta.inspect(p)?.casts.speech||0,elapsed:G.Game.st.time-run.started};}""")
    path=OUT/f'{label}-native.webm';path.write_bytes(base64.b64decode(result.pop('data').split(';base64,',1)[1]))
    return {**fixture,**result,'clip':str(path)}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base.OUT=OUT
    base.URL=os.environ.get('JUJUTSU_URL','http://127.0.0.1:8383/.omx/digimon.html?lang=zh-TW')
    report={'url':base.URL,'cases':{},'errors':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        for mobile in [False,True]:
            label='mobile' if mobile else 'desktop'
            context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
            page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
            frame=base.boot(page,30013,label)
            report['cases'][label]=frame.evaluate(CHECK)
            report['cases'][label]['native']={}
            for use_speech in [False,True]:
                # Fresh page restores the actual enemy/player methods between
                # the paired native runs; both begin with identical threats.
                if use_speech:
                    page.close();page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));frame=base.boot(page,30013,label)
                name='with-speech' if use_speech else 'without-speech'
                report['cases'][label]['native'][name]=record_native(page,frame,f'{label}-{name}',use_speech)
            context.close()
        browser.close()
    assert not report['errors'],report['errors']
    report['ok']=True
    (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({'ok':True,'views':list(report['cases']),'evidence':str(OUT)}))

if __name__=='__main__':main()
