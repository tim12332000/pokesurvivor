"""Persistent Rika, real multi-contact duet and finisher-triggered sword burst.

Controlled checks isolate origins, ledgers and cancellation. Native RAF clips
show actual automatic choreography; they do not establish subjective enjoyment.
"""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('YUTA_DUET_OUT', ROOT / '.omx/state/duet-fracture/yuta/duet'))

CHECK = r"""() => {
 const A=JAcceptance,Y=G.JujutsuYuta,p=A.p(),assert=A.assert,out={},nativePath=G.World.projectilePathClear;
 const ids={rika:'jjk-yuta-rika',blade:'jjk-yuta',manifest:'jjk-yuta-manifest',resonance:'jjk-yuta-resonance',speech:'jjk-yuta-speech'};
 function setup(names=['rika'],rank=1,q=0){
   A.reset();G.World.projectilePathClear=nativePath;A.fixture(ids[names[0]],rank);for(const name of names.slice(1))assert(p.addMove(ids[name]),'learn '+name);
   for(const m of p.moves){Object.assign(m,G.Moves.instance(m.id,rank));m.t=999;}
   p.quantityPicks=p.quantityBonus=q;p.invuln=999;return Object.fromEntries(names.map(n=>[n,p.moves.find(m=>m.id===ids[n])]));
 }
 function cast(m,owner=p){m.t=0;A.resume();try{assert(Y.cast(owner,m),'cast '+m.id)}finally{A.pause()};return Y.stateFor(owner);}
 function full(s){cast(s.manifest);return cast(s.rika);}
 function hits(e,id){return e.filter(h=>h.id===id);}
 function pulses(cast){return G.CombatPulse.telemetry.filter(t=>t.castId===cast.castId&&t.runEpoch===cast.runEpoch);}
 for(const [rank,q,fullForm,count] of [[1,0,false,4],[1,1,false,5],[5,20,false,16],[1,0,true,8],[5,20,true,24]]){
   const m=setup(fullForm?['rika','manifest']:['rika'],rank,q),e=A.spawn(100,0),events=A.watch(e);
   const s=fullForm?full(m):cast(m.rika),r=s.rika,actor=s.companion,profile=Y.rikaProfile(p,m.rika,fullForm),castRecord=r.cast;
   assert(profile.count===count&&r.strikeCount===count,'wrong quantity/rank count');
   assert(s.rika===s.companion&&Y.drawables(null).length===1,'duplicate or missing persistent actor');
   A.advance(4.5);
   const dealt=hits(events,ids.rika);assert(dealt.length===count,'real punch count '+rank+'/'+q+'/'+fullForm+': '+dealt.length);
   assert(pulses(castRecord).length===count&&new Set(pulses(castRecord).map(t=>t.contactPulseIndex)).size===count,'punch ledger missing/duplicated');
   assert(Math.abs(dealt.at(-1).raw/dealt[0].raw-(fullForm?1.2:1)/.65)<1e-8,'finisher multiplier differs');
   assert(Y.stateFor(p).companion===actor&&actor.visible&&Y.drawables(null).length===1,'companion disappeared after excursion');
   out['rank'+rank+'q'+q+(fullForm?'Full':'Normal')]={profile,hits:dealt.map(h=>h.raw),pulses:pulses(castRecord).map(t=>t.contactPulseIndex),persistent:true};
 }

 let m=setup(),e=A.spawn(100,0);cast(m.rika);A.advance(.01);const actor=Y.stateFor(p).companion;
 assert(actor.visible&&!actor.full&&actor.height===88,'learned normal Rika is not visible');A.advance(3);
 const old={x:actor.x,y:actor.y};p.x=100;A.advance(.01);
 assert(Math.hypot(actor.x-old.x,actor.y-old.y)<=7.21,'idle follow teleported');
 out.persistentFollow={old,next:{x:actor.x,y:actor.y}};

 // Ring-only builds use manifestation's own release, never free Rika punches.
 for(const [rank,height] of [[1,156],[5,180]]){
   m=setup(['manifest'],rank);e=A.spawn(100,0);const ringHits=A.watch(e);cast(m.manifest);const ringState=Y.stateFor(p),ringActor=ringState.companion;
   A.advance(.1,true);
   assert(ringActor.visible&&ringActor.full&&ringActor.height===height&&Y.drawables(null).length===1,'ring-only full companion missing or wrong rank');
   A.advance(2,true);assert(!p.hasMove(ids.rika)&&!ringState.rika&&!(ringState.casts.rika>0)&&!hits(ringHits,ids.rika).length,'ring-only build gained free Rika damage/learning');
   assert(hits(ringHits,ids.manifest).length===2&&ringState.casts.release===1,'ring-only manifestation lacks its two-source release');
   A.advance(7.01,true);assert(ringState.companion===ringActor&&!ringActor.visible&&!ringActor.full&&!Y.drawables(null).length,'ring-only expiry left a companion');
   out['ringOnly'+rank]={height,visibleDuringForm:true,freeRikaPunches:0,manifestReleaseHits:2,hiddenOnExpiry:true};
 }

 // Legal card application changes a real consumer on the first quantity pick.
 m=setup();const before=Y.rikaProfile(p,m.rika,false).count;
 const card=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');assert(card&&card.apply(p)!==false,'first quantity card missing');
 assert(before===4&&Y.rikaProfile(p,m.rika,false).count===5,'legal first quantity did not add a punch');out.firstQuantity={before,after:5};

 // Full Rika and the owner slash have independent physical origins/ledgers.
 m=setup(['rika','manifest','blade']);const near=A.spawn(90,0),far=A.spawn(430,0),nearHits=A.watch(near),farHits=A.watch(far);
 full(m);let s=Y.stateFor(p),r=s.rika,ownCast=r.bladeCast,rikaCast=r.cast;
 while(r.strikeIndex<1)A.advance(.01);
 assert(s.duetPose&&Y.pose(p).duet,'duet body pose missing at actual punch');
 const ownBefore=hits(nearHits,ids.blade).length,rikaBefore=hits(farHits,ids.rika).length;
 assert(ownBefore===1&&rikaBefore===1&&!hits(nearHits,ids.rika).length&&!hits(farHits,ids.blade).length,'independent origins collapsed');
 assert(pulses(ownCast).length===1&&pulses(rikaCast).length===1&&ownCast.castId!==rikaCast.castId,'duet reused contact ledger');
 assert(!Y.canCast(p,m.speech||G.Moves.instance(ids.speech))&&!Y.canCast(p,m.blade),'duet allowed overlapping body cast');
 const ownerBefore={x:p.x,y:p.y};p.x=20;A.advance(.01);assert(p.x===20&&ownerBefore.y===p.y,'duet blocked movement');
 out.dualOrigins={owner:{x:0,y:0},rika:{x:r.x,y:r.y},ownerCast:ownCast.castId,rikaCast:rikaCast.castId};

 // A normal excursion is never upgraded or duplicated by ring activation.
 m=setup(['rika','manifest']);e=A.spawn(150,0);cast(m.rika);s=Y.stateFor(p);r=s.rika;A.advance(.1);cast(m.manifest);
 assert(s.rika===r&&!r.full&&r.strikeCount===4,'activation upgraded an already-snapshotted normal excursion');
 A.advance(3);m.rika.t=0;cast(m.rika);assert(s.rika===r&&r.full&&r.strikeCount===8,'next excursion did not use full profile');
 out.activationSnapshot=true;

 // Full form expiry ends future full punches while preserving a normal actor.
 m=setup(['rika','manifest','blade']);e=A.spawn(100,0);const expiryHits=A.watch(e);full(m);s=Y.stateFor(p);r=s.rika;
 s.manifestUntil=s.clock+.95;A.advance(.9);const atExpiry=expiryHits.length;A.advance(.1);const finalHits=expiryHits.length;A.advance(1);
 assert(expiryHits.length===finalHits&&finalHits>=atExpiry&&!r.full&&!s.duetPose&&s.companion.visible&&s.companion.height===88,'full expiry retained beats or removed normal actor');
 out.expiry={atExpiry,finalHits,normalVisible:true};

 // A true finisher queues one owner-origin burst with its own damage attribution.
 m=setup(['rika','resonance']);e=A.spawn(100,0);let watched=A.watch(e);cast(m.rika);A.advance(3);
 const burst=hits(watched,ids.resonance);assert(burst.length===1&&Y.inspect(p).casts.resonance===1,'finisher resonance missing or recursive');
 const burstPulse=G.CombatPulse.telemetry.filter(t=>t.moveId===ids.resonance);assert(burstPulse.length===1&&burstPulse[0].channel==='resonance','burst missing independent ledger');
 out.resonance={punches:hits(watched,ids.rika).length,bursts:burst.length,pulse:burstPulse[0]};

 // Killing an excursion target must transfer the same finite combo, not waste
 // its remaining quantity investment on the corpse or create a fresh actor.
 for(const phase of ['travel','strike']){
   m=setup(['rika','resonance']);e=A.spawn(phase==='travel'?300:100,0);watched=A.watch(e);
   cast(m.rika);s=Y.stateFor(p);r=s.rika;const actor=r,record=r.cast;
   if(phase==='travel')A.advance(.04);else while(r.strikeIndex<1)A.advance(.01);
   const next=A.spawn(phase==='travel'?330:360,40),nextHits=A.watch(next);
   e.dead=true;e.hp=0;A.advance(3);
   const contacts=G.CombatPulse.telemetry.filter(t=>t.castId===record.castId),nextPunches=hits(nextHits,ids.rika);
   assert(nextPunches.length>0,'dead '+phase+' target did not transfer remaining punches');
   assert(s.companion===actor&&contacts.length===4&&new Set(contacts.map(t=>t.contactPulseIndex)).size===4,'retarget reset actor or combo budget '+phase);
   assert(r.travelDistance<=r.travelBudget+1e-8,'retarget exceeded original travel budget '+phase);
   assert(hits(nextHits,ids.resonance).length<=1&&s.casts.resonance===1,'retarget duplicated or lost finisher '+phase);
   out['retarget-'+phase]={punches:nextPunches.length,contacts:contacts.length,actorPreserved:true,resonance:s.casts.resonance};
 }
 // A removed live actor can remain in the spatial grid until its next rebuild.
 // It must not be selected again or receive another contact from that cache.
 m=setup(['rika','resonance']);e=A.spawn(100,0);watched=A.watch(e);cast(m.rika);s=Y.stateFor(p);r=s.rika;
 while(r.strikeIndex<1)A.advance(.01);
 const next=A.spawn(360,40),nextHits=A.watch(next),ghostBefore=watched.length;
 G.EnemyMgr.removeRemote(e.id,false);
 assert(!G.EnemyMgr.all().includes(e)&&G.EnemyMgr.queryCircle(e.x,e.y,200).includes(e),'stale grid fixture did not retain removed target');
 A.advance(3);
 assert(watched.length===ghostBefore&&hits(nextHits,ids.rika).length===3,'removed live target stole retarget or received ghost damage');
 assert(s.casts.resonance===1,'stale-grid transfer lost or repeated finisher');
 out.retargetStaleGrid={ghostHitsAfterRemoval:watched.length-ghostBefore,nextPunches:hits(nextHits,ids.rika).length,resonance:s.casts.resonance};
 for(const boundary of ['wall','range','budget','empty']){
   m=setup(['rika']);e=A.spawn(100,0);cast(m.rika);s=Y.stateFor(p);r=s.rika;
   while(r.strikeIndex<1)A.advance(.01);
   const origin={x:r.x,y:r.y},before=r.strikeIndex;
   const next=boundary==='empty'?null:A.spawn(boundary==='range'?800:400,0),events=next?A.watch(next):[];
   e.dead=true;e.hp=0;
   if(boundary==='wall')G.World.projectilePathClear=(x,y,tx,ty)=>Math.max(x,tx)<250;
   if(boundary==='budget')r.travelBudget=r.travelDistance+5;
   A.advance(3);
   assert(!events.length&&!s.rika,'invalid retarget hit or failed to return '+boundary);
   assert(r.strikeIndex===before,'empty combo kept punching '+boundary);
   out['retargetBoundary-'+boundary]={origin,punches:r.strikeIndex,returned:true};
 }
 for(const cancel of ['clear','unlearn','dead']){
   m=setup(['rika','resonance']);e=A.spawn(100,0);cast(m.rika);s=Y.stateFor(p);r=s.rika;
   while(r.strikeIndex<1)A.advance(.01);
   const next=A.spawn(400,0),events=A.watch(next);e.dead=true;e.hp=0;
   A.advance(.07);assert(r.phase==='travel'&&r.pursuitTarget===next,'retarget travel not reached '+cancel);
   if(cancel==='clear')G.Combat.clearFields(p);
   if(cancel==='unlearn')p.moves=p.moves.filter(move=>move.id!==ids.rika);
   if(cancel==='dead'){p.dead=true;p.hp=0;}
   A.advance(2);
   assert(!events.length&&!Y.stateFor(p)?.rika&&!s.pendingResonance.length,'cancelled retarget retained attacks '+cancel);
   out['retargetCancel-'+cancel]=true;
 }
 m=setup(['rika','manifest','blade'],5,20);e=A.spawn(300,0);full(m);s=Y.stateFor(p);r=s.rika;
 while(r.strikeIndex<1)A.advance(.01);
 const pursuing={x:r.x,y:r.y};
 for(let i=0;i<35;i++){e.x+=2;G.EnemyMgr.rebuildGrid();A.advance(.01);}
 assert(r.x>pursuing.x+1,'24-punch recovery has no physical pursuit window');
 out.highQuantityPursuit={before:pursuing,after:{x:r.x,y:r.y},interval:r.interval};

 m=setup(['rika','resonance']);e=A.spawn(100,0);cast(m.rika);s=Y.stateFor(p);
 while(!s.action)A.advance(.01);assert(s.action.kind==='resonance'&&!s.action.released,'burst skipped windup');
 watched=A.watch(e);p.moves=p.moves.filter(move=>move.id!==ids.resonance);A.advance(.2);assert(!hits(watched,ids.resonance).length,'unlearned burst still hit');out.unlearnedBurst=true;

 // Cancel inside damage callbacks, including the finisher, cannot queue later hits.
 for(const cancel of ['first','finisher']){
   m=setup(['rika','resonance']);e=A.spawn(100,0);watched=A.watch(e);cast(m.rika);s=Y.stateFor(p);const record=s.rika.cast;
   const previous=G.CombatPulse.onPulse;G.CombatPulse.onPulse=info=>{
     previous?.(info);if(info.castId===record.castId&&info.contactPulseIndex===(cancel==='first'?0:3))G.Combat.clearFields(p);
   };
   try{A.advance(3)}finally{G.CombatPulse.onPulse=previous;}
   assert(!Y.stateFor(p)&&!hits(watched,ids.resonance).length&&hits(watched,ids.rika).length===(cancel==='first'?1:4),'callback clear retained future hits '+cancel);
   out['callback-'+cancel]=true;
 }

 for(const cancel of ['pause','frozen','dead','wall']){
   m=setup(['rika','resonance']);e=A.spawn(300,0);watched=A.watch(e);cast(m.rika);s=Y.stateFor(p);r=s.rika;A.advance(.05);
   if(cancel==='pause'){const age=r.age;G.Combat.updateFields(.5);assert(r.age===age,'pause advanced combo');}
   if(cancel==='frozen'){const age=r.age;p.frozen=true;A.advance(.5);assert(r.age===age,'frozen advanced combo');p.frozen=false;}
   if(cancel==='dead'){p.dead=true;p.hp=0;A.advance(.1);assert(!Y.stateFor(p),'dead owner retained actor');}
   if(cancel==='wall'){G.World.projectilePathClear=(x,y,tx,ty)=>tx<150;A.advance(2);assert(!watched.length,'wall pursuit hit through obstacle');}
   G.Combat.clearFields(p);assert(!Y.stateFor(p),'clear retained state '+cancel);out[cancel]=true;
 }
 for(const cancel of ['clear','unlearn']){
   m=setup(['rika','resonance']);const victims=[A.spawn(100,0),A.spawn(120,0)];let direct=0;
   for(const victim of victims){const hurt=victim.hurt;victim.hurt=function(...args){direct++;const result=hurt.apply(this,args);
     if(cancel==='clear')G.Combat.clearFields(p);else p.moves=p.moves.filter(move=>move.id!==ids.rika);return result;};}
   cast(m.rika);s=Y.stateFor(p);while(s.rika.phase!=='strike')A.advance(.01);
   A.resume();try{Y.update(2)}finally{A.pause()}
   A.advance(.2);assert(direct===1&&!G.CombatPulse.telemetry.some(t=>t.moveId===ids.resonance&&t.castId>s.companion.castId),'hurt callback kept same-pulse/future hits '+cancel);
   out['hurtCallback-'+cancel]={direct};
 }
 // Native clones own a separate companion, ledger and cancellation scope.
 m=setup(['rika']);e=A.spawn(100,0);const clone=G.SelfClones.summon(p);assert(clone,'native clone missing');
 clone.moves.find(move=>move.id===ids.rika).t=0;cast(m.rika);const copied=clone.moves.find(move=>move.id===ids.rika);cast(copied,clone);
 assert(Y.stateFor(p).companion!==Y.stateFor(clone).companion&&Y.stateFor(p).rika.cast.ownerId!==Y.stateFor(clone).rika.cast.ownerId,'clone shared companion/ledger');
 Y.clear(p);assert(!Y.stateFor(p)&&Y.stateFor(clone),'module owner clear removed clone companion');
 clone.dead=true;clone.hp=0;A.advance(.1);assert(!Y.stateFor(clone),'dead clone retained companion');out.clones=true;
 return out;
}"""

NATIVE = r"""mobile => {
 const A=JAcceptance,p=A.p();A.reset();A.fixture('jjk-yuta');p.level=12;
 for(const id of ['jjk-yuta-rika','jjk-yuta-speech','jjk-yuta-manifest','jjk-yuta-resonance']){
   const card=G.LevelUp.offer(p,1000).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'native learn '+id);
 }
 for(const m of p.moves)m.t=0;p.invuln=0;p.xpNext=1e12;G.Spawner.update=()=>{};
 const positions=mobile?[[0,-90],[0,-220],[50,-280],[-50,-320]]:[[90,0],[300,0],[360,50],[430,-30]];
 positions.forEach(([x,y],index)=>{const e=A.spawn(x,y);e.touchCd=999;if(index===1)e.elite=true;});
 const cast=p.cast,events=[];p.cast=function(m,...args){events.push({id:m.id,time:G.Game.st.time});return cast.call(this,m,...args)};
 window.YutaDuetNative={events,started:G.Game.st.time};G.Game.debugSpeed(1);A.resume();
 return {level:p.level,skills:p.moves.map(m=>({id:m.id,rank:m.lvl})),fixture:'native RAF; legal learning, controlled persistent enemies'};
}"""

SHOWCASE = r"""mobile=>{
 const A=JAcceptance,p=A.p();A.reset();A.fixture('jjk-yuta',5);p.addMove('jjk-yuta-rika');
 for(const m of p.moves){Object.assign(m,G.Moves.instance(m.id,5));m.t=999;}
 p.invuln=0;A.advance(.01,true);
 window.YutaShowcase={mobile};
}"""


def presentation(page, frame, label, mobile):
    frame.evaluate(SHOWCASE, mobile)
    page.wait_for_timeout(30)
    page.screenshot(path=str(OUT / f'{label}-normal-persistent.png'))
    frame.evaluate("""mobile=>{
      const A=JAcceptance,p=A.p();p.addMove('jjk-yuta-manifest');p.addMove('jjk-yuta-resonance');
      for(const m of p.moves){Object.assign(m,G.Moves.instance(m.id,5));m.t=999;}p.quantityPicks=p.quantityBonus=4;
      for(const [x,y] of (mobile?[[0,-100],[0,-220],[60,-270]]:[[100,0],[270,0],[360,50]])){const e=A.spawn(x,y);e.touchCd=999;}
      const manifest=p.moves.find(m=>m.id==='jjk-yuta-manifest'),rika=p.moves.find(m=>m.id==='jjk-yuta-rika');manifest.t=rika.t=0;
      A.resume();try{G.JujutsuYuta.cast(p,manifest);G.JujutsuYuta.cast(p,rika)}finally{A.pause()};
      while(G.JujutsuYuta.stateFor(p).rika.phase!=='strike')A.advance(.01);
      while(G.JujutsuYuta.stateFor(p).action)A.advance(.01);A.advance(.1);
    }""", mobile)
    for phase, advance in [('full-windup', 0), ('full-contact', .13), ('full-recoil', .055)]:
        if advance:
            frame.evaluate('dt=>JAcceptance.advance(dt)', advance)
        page.wait_for_timeout(30)
        page.screenshot(path=str(OUT / f'{label}-{phase}.png'))
    frame.evaluate("""()=>{const A=JAcceptance,s=G.JujutsuYuta.stateFor(A.p());
      for(let i=0;i<400&&s.rika&&s.rika.strikeIndex<s.rika.strikeCount;i++)A.advance(.01);
    }""")
    page.wait_for_timeout(30)
    page.screenshot(path=str(OUT / f'{label}-full-finisher.png'))
    frame.evaluate("""()=>{const A=JAcceptance,s=G.JujutsuYuta.stateFor(A.p());
      for(let i=0;i<100&&s.action?.kind!=='resonance';i++)A.advance(.01);A.advance(.15);
    }""")
    page.wait_for_timeout(30)
    page.screenshot(path=str(OUT / f'{label}-resonance-contact.png'))


def record_native(frame, label, mobile):
    frame.evaluate(NATIVE, mobile)
    clip = frame.evaluate("""async()=>{
      const canvas=document.getElementById('game'),stream=canvas.captureStream(24),audio=G.Audio.debugStream(true);
      if(audio)for(const track of audio.getAudioTracks())stream.addTrack(track);
      const mime=MediaRecorder.isTypeSupported('video/webm;codecs=vp9,opus')?'video/webm;codecs=vp9,opus':'video/webm';
      const recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:2200000}),chunks=[];
      recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
      const done=new Promise(resolve=>recorder.onstop=()=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:mime}))});
      recorder.start();await new Promise(resolve=>setTimeout(resolve,4500));JAcceptance.pause();recorder.stop();
      const data=await done;for(const track of stream.getTracks())track.stop();return data;
    }""")
    path = OUT / f'{label}-native-duet.webm'
    path.write_bytes(base64.b64decode(clip.split(';base64,', 1)[1]))
    return str(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base.OUT = OUT
    base.URL = os.environ.get('JUJUTSU_URL', 'http://127.0.0.1:8351/.omx/digimon.html?lang=zh-TW')
    report = {'url': base.URL, 'cases': {}, 'errors': [], 'missing': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        for mobile in [False, True]:
            label = 'mobile' if mobile else 'desktop'
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.on('response', lambda r: report['missing'].append(r.url) if r.status >= 400 else None)
            frame = base.boot(page, 30013, label)
            report['cases'][label] = frame.evaluate(CHECK)
            presentation(page, frame, label, mobile)
            report['cases'][label]['native'] = frame.evaluate(NATIVE, mobile)
            for at, phase in [(.15, 'full-approach'), (1.0, 'duet-contact'), (2.25, 'resonance'), (4, 'full-follow')]:
                frame.wait_for_function('at=>G.Game.st.time-YutaDuetNative.started>=at', arg=at, polling=10)
                frame.evaluate('JAcceptance.pause()')
                page.wait_for_timeout(30)
                page.screenshot(path=str(OUT / f'{label}-{phase}.png'))
                frame.evaluate('JAcceptance.resume()')
            frame.evaluate('JAcceptance.pause()')
            native = frame.evaluate("""()=>{const run=YutaDuetNative,counts={};for(const e of run.events)counts[e.id]=(counts[e.id]||0)+1;
              JAcceptance.assert(counts['jjk-yuta-rika']>0&&counts['jjk-yuta-manifest']>0&&counts['jjk-yuta-resonance']>0,'native auto duet/resonance missing '+JSON.stringify(counts));
              return {counts,events:run.events,damage:G.Game.player.dmgDealt};}""")
            report['cases'][label]['native'].update(native)
            report['cases'][label]['clip'] = record_native(frame, label, mobile)
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    assert not report['missing'], report['missing']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({'ok': True, 'views': list(report['cases']), 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
