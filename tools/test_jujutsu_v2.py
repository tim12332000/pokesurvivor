"""Experience, presentation and bounded native-loop measurements for Sendai v2.

--baseline preserves before screenshots; defaults to v2 final evidence. A real
20-game-second opening precedes isolated level-nine and 50-enemy fixtures.
"""
from __future__ import annotations
import argparse
import base64
import html
import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT=Path(__file__).resolve().parents[1]


def sample(frame):
    return frame.evaluate("""()=>{const p=G.Game.player,api=p.dex===30013?G.JujutsuYuta:p.dex===30014?G.JjkRyu:G.JjkUro,s=api.stateFor(p);
      const action=s?.action||s?.pose;return {state:G.Game.state,time:G.Game.st.time,hp:p.hp,level:p.level,kills:p.kills,damage:p.dmgDealt,enemies:G.EnemyMgr.all().length,
       animation:p.anim.cur,frame:p.anim.frame,skills:p.moves.map(m=>({id:m.id,t:m.t,dealt:m.dealt})),
       action:action?{kind:action.kind||action.mode,age:action.age,released:action.released??action.done}:null,
       rika:s?.rika?{phase:s.rika.phase,age:s.rika.age}:null,screen:s?.screen?{age:s.screen.age,budget:s.screen.budget}:null,
       projectiles:G.Projectiles.all().length};}""")


def opening(page,frame,out,slug):
    frame.evaluate('JAcceptance.resume();G.Game.toggleAutoPickUpgrades()')
    started=time.perf_counter();snaps=[]
    for target in [5,12,20]:
        while frame.evaluate('G.Game.st.time')<target:
            if time.perf_counter()-started>40:raise AssertionError('opening stalled '+str(sample(frame)))
            page.wait_for_timeout(150)
            state=frame.evaluate('G.Game.state')
            if state=='over':raise AssertionError('unattended opening died '+str(sample(frame)))
        page.screenshot(path=str(out/f'{slug}-opening-{target}s.png'));snaps.append(sample(frame))
    frame.evaluate('JAcceptance.pause()');return {'wallSeconds':time.perf_counter()-started,'samples':snaps,'autoPickUpgrades':True,'input':'stationary native opening'}


def learned_loop(page,frame,out,slug):
    frame.evaluate("""slug=>{const A=JAcceptance,p=A.p();A.reset();p.level=9;for(const id of G.Moves.poolFor(p.mon))if(!p.hasMove(id)){const c=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(c&&c.apply(p)!==false,'level9 native learn '+id)}
      for(const m of p.moves)m.t=0;p.hp=p.maxHp;p.invuln=0;
      for(let i=0;i<12;i++){const angle=i*Math.PI/6,r=i===0?65:135,e=A.spawn(Math.cos(angle)*r,Math.sin(angle)*r);e.spd=0;e.dmg=0;}
      A.resume();G.Game.debugSpeed(1);window.JV2Start=G.Game.st.time;
    }""",slug)
    samples=[]
    for at in [.15,.35,.6,1.2,3,6.3]:
        frame.wait_for_function('at=>G.Game.st.time-window.JV2Start>=at',arg=at,polling=10)
        samples.append(sample(frame));page.screenshot(path=str(out/f'{slug}-level9-{at}s.png'))
    frame.evaluate('JAcceptance.pause()');return samples


STRESS=r"""()=>{
 const A=JAcceptance,p=A.p();A.reset();p.level=9;
 for(const id of G.Moves.poolFor(p.mon))if(!p.hasMove(id))p.addMove(id);
 for(const m of p.moves)m.t=0;p.invuln=1000;
 for(let i=0;i<50;i++){const a=i*Math.PI*2/50,r=65+(i%5)*30;A.spawn(Math.cos(a)*r,Math.sin(a)*r);}
 const timings=[],counts=[],dt=1/60,started=performance.now(),damageBefore=p.dmgDealt;A.resume();
 try{for(let i=0;i<3600;i++){
   const begin=performance.now();p.update(dt);G.EnemyMgr.update(dt,[p]);G.EnemyMgr.rebuildGrid();
   G.Combat.tick(dt,p,i*dt);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,i*dt);G.Combat.updateFields(dt);G.FX.update(dt);
   timings.push(performance.now()-begin);
   if(i%60===0){const api=p.dex===30013?G.JujutsuYuta:p.dex===30014?G.JjkRyu:G.JjkUro,s=api.stateFor(p);
     counts.push({second:i/60,projectiles:G.Projectiles.all().length,effects:s?.effects?.length??api.effects?.length??s?.marks?.length??0,rika:!!s?.rika});}
 }}finally{A.pause()}
 timings.sort((a,b)=>a-b);A.assert(!p.dead,'stress fixture unexpectedly died');A.assert(p.dmgDealt>damageBefore,'no native auto-loop damage during stress');
 const maxEffects=Math.max(...counts.map(c=>c.effects)),maxProjectiles=Math.max(...counts.map(c=>c.projectiles));
 A.assert(maxEffects<=64&&maxProjectiles<=256,'unbounded attack effects/projectiles during stress');
 return {scope:'60 simulated seconds / 50 static native enemies, full player/enemy/combat/VFX update; no render, spawning or pickups',
   wallMs:performance.now()-started,steps:3600,p50:timings[1800],p95:timings[3420],p99:timings[3564],max:timings.at(-1),counts,maxEffects,maxProjectiles,kills:p.kills,damage:p.dmgDealt-damageBefore};
}"""


def phase_checks(frame,out,slug):
    cases={'yuta':[('jjk-yuta',.14),('jjk-yuta-speech',.24)],
           'ryu':[('jjk-ryu',.22),('jjk-ryu-spread',.35),('jjk-ryu-impact',.45),('jjk-ryu-maximum',.75)],
           'uro':[('jjk-uro',.18),('jjk-uro-thin-ice',.34),('jjk-uro-collapse',.55)]}
    results=[]
    for skill,release in cases[slug]:
        if skill=='jjk-ryu-spread':
            data=frame.evaluate('''() => {
              const A=JAcceptance,p=A.p();A.reset();A.fixture('jjk-ryu-spread');const e=A.spawn(100,0);p.target=e;A.cast('jjk-ryu-spread');
              A.advance(.34);const before={loss:e.maxHp-e.hp,pose:A.pose()};
              A.advance(.02);const launch={loss:e.maxHp-e.hp,pose:A.pose(),bolts:G.JjkRyu.stateFor(p).scatter.length};
              A.assert(before.loss===0&&launch.loss===0&&launch.bolts===3,'scatter hit instantly instead of launching three bolts');
              A.assert(JSON.stringify(before.pose.calls)!==JSON.stringify(launch.pose.calls),'scatter windup and release reuse exact frame');
              A.advance(.3);const hit={loss:e.maxHp-e.hp,pose:A.pose()};A.assert(hit.loss>0,'travelling scatter never contacted target');
              A.advance(.3);A.assert(e.maxHp-e.hp===hit.loss,'scatter repeated direct damage');
              return {skill:'jjk-ryu-spread',release:.35,before,launch,hit};
            }''')
            for state in ['before','launch','hit']:data[state]['pose']=base.save_pose(f'{slug}-{skill}-{state}',data[state]['pose'])
            results.append(data)
            continue
        data=frame.evaluate("""({skill,release})=>{const A=JAcceptance,p=A.p();A.reset();const m=A.fixture(skill),e=A.spawn(80,0);p.target=e;A.cast(skill);
          A.advance(release-.01);const before={loss:e.maxHp-e.hp,pose:A.pose()};A.assert(before.loss===0,'damage before hit frame '+skill);
          A.advance(.02);const hit={loss:e.maxHp-e.hp,pose:A.pose()};A.assert(hit.loss>0,'missing release-frame damage '+skill);
          A.advance(.13);const recover={loss:e.maxHp-e.hp,pose:A.pose()};A.assert(recover.loss===hit.loss,'recoil dealt duplicate damage '+skill);
          A.assert(JSON.stringify(before.pose.calls)!==JSON.stringify(hit.pose.calls),'windup and hit reuse exact physical frame '+skill);
          if(skill!=='jjk-uro')A.assert(JSON.stringify(hit.pose.calls)!==JSON.stringify(recover.pose.calls),'hit and recovery reuse exact physical frame '+skill);
          return {skill,release,before,hit,recover};}""",{'skill':skill,'release':release})
        for state in ['before','hit','recover']:data[state]['pose']=base.save_pose(f'{slug}-{skill}-{state}',data[state]['pose'])
        results.append(data)
    return results


def semantic_contacts(frame,out,slug):
    if slug=='uro':
        result=frame.evaluate("""()=>{const A=JAcceptance,p=A.p(),art=G.JujutsuArt;A.reset();A.fixture('jjk-uro');p.target=A.spawn(80,0);A.cast('jjk-uro');
          const stages=[];for(const dt of [.03,.09,.08]){A.advance(dt);const pose=G.JjkUro.poseFor(p),f=art.sample(p.dex,'cast',0,0,pose);stages.push({phase:pose.phase,frame:f.name,art:A.pose()})}
          A.assert(stages.map(s=>s.frame).join(',')==='skyGrab,skyPull,skyRelease','Uro grab/pull/hit semantic frame order '+stages.map(s=>s.frame));return stages;}""")
        for item in result:item['art']=base.save_pose('uro-sky-'+item['phase'],item['art'])
        return result
    if slug=='yuta':
        result=frame.evaluate("""()=>{const A=JAcceptance,p=A.p(),Y=G.JujutsuYuta;A.reset();const m=A.fixture('jjk-yuta-rika');p.target=A.spawn(100,0);A.cast(m.id);
          for(let i=0;i<100&&Y.inspect(p).rika?.phase!=='strike';i++)A.advance(.01);
          A.assert(Y.inspect(p).rika?.phase==='strike','Rika never entered native strike');A.advance(.21-Y.inspect(p).rika.phaseAge);
          function shot(){const r=Y.inspect(p).rika,c=document.createElement('canvas');c.width=500;c.height=300;const ctx=c.getContext('2d'),calls=[],draw=ctx.drawImage.bind(ctx);
            ctx.drawImage=(im,...rect)=>{calls.push({source:im.src||'',rect});return draw(im,...rect)};ctx.translate(200,220);G.JujutsuArt.drawRika(ctx,r);
            const frames=calls.map(call=>G.JujutsuArt.metadata.sheets['rika-skills'].frames.find(f=>f.rect.every((v,i)=>v===call.rect[i]))?.name);
            return {frames,dealt:m.dealt,png:c.toDataURL()};}
          const before=shot();A.assert(before.dealt===0,'Rika damage before .22 strike');A.advance(.02);const hit=shot();
          A.assert(hit.dealt>0,'Rika missing .22 contact damage');A.assert(before.frames.every(f=>f==='strikeWindup'),'Rika contact art appeared before hit '+before.frames);
          A.assert(hit.frames.every(f=>f==='strikeContact'),'Rika actual hit did not show contact frame '+hit.frames);return {before,hit};}""")
        for state in ['before','hit']:result[state]=base.save_pose('rika-contact-'+state,result[state])
        return result
    results=[]
    for skill,release in [('jjk-ryu',.22),('jjk-ryu-maximum',.75)]:
        for angle in [0,.9,-.9]:
            result=frame.evaluate("""({skill,release,angle})=>{const A=JAcceptance,p=A.p();A.reset();A.fixture(skill);p.target=A.spawn(200*Math.cos(angle),200*Math.sin(angle));A.cast(skill);A.advance(release+.01);
              const s=G.JjkRyu.stateFor(p),f=s.action,beam=s.effects.find(e=>e.kind==='beam');A.assert(f&&beam,'missing native beam after release');
              const releasePose={...f,phase:'fire',frameName:skill==='jjk-ryu'?'lightRelease':'maxRelease'},name=Math.abs(Math.sin(f.aim))>.55?'muzzle':'beamEnd',expected=G.JujutsuArt.pointFor(p,releasePose,name);
              A.assert(expected&&Math.hypot(beam.renderX-expected.x,beam.renderY-expected.y)<1e-6,'beam detached from measured art '+skill);
              const end={x:beam.renderX+Math.cos(beam.renderAim)*beam.renderLength,y:beam.renderY+Math.sin(beam.renderAim)*beam.renderLength},logical={x:beam.x+Math.cos(beam.aim)*beam.length,y:beam.y+Math.sin(beam.aim)*beam.length-48};
              A.assert(Math.hypot(end.x-logical.x,end.y-logical.y)<1e-6,'art join moved clipped far endpoint');
              return {skill,angle,name,expected,renderStart:{x:beam.renderX,y:beam.renderY},end,logical,damage:p.target.maxHp-p.target.hp};}""",{'skill':skill,'release':release,'angle':angle})
            frame.page.wait_for_timeout(35);frame.page.screenshot(path=str(out/f'ryu-measured-{skill}-{angle}.png'));results.append(result)
    return results


def manifestation(frame,out):
    frame.evaluate("""()=>{const A=JAcceptance,p=A.p();A.reset();A.fixture('jjk-yuta-manifest');p.target=A.spawn(100,0);A.cast('jjk-yuta-manifest');}""")
    frames=[];previous=0
    for at in [.7,3,5.9]:
        frame.evaluate('dt=>JAcceptance.advance(dt)',at-previous);previous=at
        result=frame.evaluate("""()=>{const A=JAcceptance,p=A.p(),Y=G.JujutsuYuta,s=Y.inspect(p);A.assert(s.companion?.visible,'manifested companion vanished between attacks');
          const c=document.createElement('canvas');c.width=600;c.height=400;const ctx=c.getContext('2d'),calls=[],draw=ctx.drawImage.bind(ctx);
          ctx.drawImage=(im,...rect)=>{calls.push({source:im.src||'',rect});return draw(im,...rect)};ctx.translate(300,300);
          for(const node of Y.drawables(G.Camera))node.draw(ctx);G.Combat.drawAirFields(ctx);
          A.assert(calls.some(c=>/rika/i.test(c.source)),'manifested companion not drawn from real Rika atlas');return {calls,remaining:s.manifestRemaining,png:c.toDataURL()};}""")
        frames.append(base.save_pose(f'yuta-manifest-companion-{at}s',result))
    frame.evaluate('JAcceptance.advance(.2);JAcceptance.assert(!G.JujutsuYuta.inspect().companion?.visible,"manifest companion persisted after expiry")')
    return frames


def companion_order(page,frame,out):
    frame.evaluate("""()=>{const A=JAcceptance,p=A.p();A.reset();A.fixture('jjk-yuta-manifest');p.target=A.spawn(100,0);A.cast('jjk-yuta-manifest');A.advance(3);}""")
    result=frame.evaluate("""()=>new Promise(resolve=>{const ctx=document.getElementById('game').getContext('2d'),draw=ctx.drawImage,clear=ctx.clearRect;let calls=[];
      ctx.drawImage=function(im,...args){calls.push({source:im.src||'',rect:args});return draw.call(this,im,...args)};
      ctx.clearRect=function(...args){calls=[];return clear.apply(this,args)};
      requestAnimationFrame(()=>requestAnimationFrame(()=>{ctx.drawImage=draw;ctx.clearRect=clear;
        const rika=calls.findIndex(c=>/rika/i.test(c.source)),hero=calls.findIndex(c=>/yuta-(common|skills)/i.test(c.source));
        resolve({calls,rikaIndex:rika,heroIndex:hero});}));})""")
    assert result['rikaIndex']>=0 and result['heroIndex']>result['rikaIndex'],'native scene did not paint player after large Rika companion'
    page.screenshot(path=str(out/'yuta-manifest-native-draw-order.png'))
    return result


def death_restart(frame,out,slug):
    frame.evaluate("""()=>{const A=JAcceptance,p=A.p();A.reset();p.hp=1;p.invuln=0;A.resume();try{p.hurt(100000,null,true)}finally{A.pause()}
      A.assert(p.dead&&p.anim.cur==='Faint','native lethal damage did not enter death animation');}""")
    poses=[]
    for dt in [.03,.18,.35]:
        frame.evaluate('dt=>JAcceptance.advance(dt)',dt)
        poses.append(base.save_pose(f'{slug}-death-{dt}',frame.evaluate('JAcceptance.pose()')))
    frame.evaluate("""()=>{const A=JAcceptance,old=A.p();G.Game.startRun();A.pause();A.assert(A.p()!==old&&!A.p().dead&&A.p().hp===A.p().maxHp,'native restart kept dead body');}""")
    return poses


def comparison_gallery():
    folder=ROOT/'.omx/state/jujutsu-v2';rows=[]
    for dex,slug in base.HEROES.items():
        title={'yuta':'乙骨憂太與里香','ryu':'石流龍','uro':'烏鷺亨子'}[slug]
        for caption,filename in [('正常入口',f'desktop-{dex}-normal-entry.png'),('開局20秒',f'{slug}-opening-20s.png'),
                                 ('Lv.9 自動戰鬥0.35秒',f'{slug}-level9-0.35s.png'),('Lv.9 自動戰鬥3秒',f'{slug}-level9-3s.png'),
                                 ('Lv.9 自動戰鬥6.3秒',f'{slug}-level9-6.3s.png')]:
            if not all((folder/phase/filename).exists() for phase in ['before','final']):continue
            rows.append(f'<section><h2>{title} · {caption}</h2><div class="pair">'+''.join(
                f'<figure><figcaption>{label}</figcaption><a href="{phase}/{filename}"><img loading="lazy" src="{phase}/{filename}" alt="{html.escape(title+caption+label)}"></a></figure>'
                for phase,label in [('before','第一版'),('final','第二版')])+'</div></section>')
    videos=''.join(f'<figure><figcaption>{label} · 原生自動戰鬥6秒</figcaption><video controls muted loop preload="metadata" style="width:100%" src="final/clips/{slug}-native-level9.webm"></video></figure>'
                   for slug,label in [('yuta','乙骨與里香'),('ryu','石流龍'),('uro','烏鷺亨子')] if (folder/'final/clips'/f'{slug}-native-level9.webm').exists())
    document='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>仙台三人組：遊戲實畫面比較</title><style>body{margin:24px auto;padding:0 18px;max-width:1500px;background:#101820;color:#e6edf3;font:16px/1.6 system-ui}h1{font-size:26px}h2{font-size:18px;margin-top:32px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0}img{width:100%;display:block}figcaption{padding:7px;background:#263544}a{color:#9edcff}p{max-width:1000px}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style>
<h1>仙台三人組：遊戲實畫面比較</h1><p>每張均從正常遊戲畫面擷取，可點開原圖。開局為原生敵人生成；Lv.9 使用固定敵群，讓所有已學技能自行施放。標示相同取樣時間不代表相同動作影格；新版的施術排程及目標位置也有調整。</p>
<p>第一版 Lv.9 測試設定曾開啟無敵，會讓人物半透明；透明度不作為畫質改善的證據。20秒開局與短程效能測試不足以證明長期平衡。</p>
<p><a href="before/report.json">第一版取樣紀錄</a> · <a href="final/report.json">第二版取樣與效能紀錄</a></p>'''+('<h2>第二版原生動畫實錄</h2>'+videos if videos else '')+''.join(rows)+'</html>'
    (folder/'comparison.html').write_text(document,encoding='utf8')


def switch_assets(page,frame,out):
    results=[]
    for dex,slug in [(30015,'uro'),(30013,'yuta')]:
        frame.evaluate('G.Game.toUI();G.MenuUI.open()')
        frame.locator(f'[data-quick-naruto="{dex}"]').click()
        frame.wait_for_function('dex=>G.NarutoAssets.ready(dex)',arg=dex)
        state=frame.evaluate("""dex=>{const art=G.JujutsuArt,slug=dex===30015?'uro':'yuta',keys=Object.keys(art.images);
          JAcceptance.assert(art.isReady(dex)&&keys.includes(slug+'-common')&&keys.includes(slug+'-skills'),'selected switch art not ready');
          if(dex===30013)JAcceptance.assert(keys.includes('rika-skills'),'Yuta switch omitted Rika');return {dex,keys};}""",dex)
        frame.locator('#scr-menu [data-go="play"]').click()
        frame.wait_for_function('dex=>G.Game.player?.dex===dex&&G.Game.state==="playing"',arg=dex)
        frame.evaluate('JAcceptance.pause()');state['pose']=base.save_pose(f'switch-ryu-to-{slug}',frame.evaluate('JAcceptance.pose()'))
        results.append(state)
    return results


def record_clips():
    out=ROOT/'.omx/state/jujutsu-v2/final/clips';out.mkdir(parents=True,exist_ok=True);base.OUT=out
    report={'scope':'native canvas.captureStream24fps / MediaRecorder WebM, level9 automatic combat, stationary12-enemy fixture','clips':{},'failures':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        for dex,slug in base.HEROES.items():
            context=browser.new_context(viewport={'width':1280,'height':900},service_workers='block');page=context.new_page()
            try:
                print(slug,'recording native clip',flush=True);frame=base.boot(page,dex,'desktop')
                mime=frame.evaluate("""()=>{const stream=document.getElementById('game').captureStream(24),mime=MediaRecorder.isTypeSupported('video/webm;codecs=vp9')?'video/webm;codecs=vp9':'video/webm',recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:2500000}),chunks=[];
                  window.JV2RecordingDone=new Promise((resolve,reject)=>{recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};recorder.onerror=e=>reject(Error(e.error?.message||'recorder failed'));
                    recorder.onstop=async()=>{const bytes=new Uint8Array(await new Blob(chunks,{type:mime}).arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));
                      stream.getTracks().forEach(track=>track.stop());resolve({mime,bytes:bytes.length,base64:btoa(binary)});};});recorder.start(200);setTimeout(()=>recorder.stop(),6000);return mime;}""")
                learned_loop(page,frame,out,slug)
                data=frame.evaluate('window.JV2RecordingDone');(out/f'{slug}-native-level9.webm').write_bytes(base64.b64decode(data.pop('base64')));report['clips'][slug]=data
                assert data['bytes']>10000,'empty native clip'
            except Exception as e:report['failures'].append(slug+': '+str(e))
            finally:context.close()
        browser.close()
    report['ok']=not report['failures'];(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');comparison_gallery()
    print(json.dumps(report,ensure_ascii=True));return report['ok']


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',action='store_true');parser.add_argument('--clips-only',action='store_true');args=parser.parse_args()
    if args.clips_only:
        if not record_clips():raise SystemExit(1)
        return
    out=ROOT/'.omx/state/jujutsu-v2'/('before' if args.baseline else 'final');out.mkdir(parents=True,exist_ok=True);base.OUT=out
    report={'scope':'real opening and actual native automatic loop, isolated stress separately labeled','baseline':args.baseline,'sourceHashes':base.hashes(),'heroes':{},'errors':[],'failedRequests':[],'failures':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        for dex,slug in base.HEROES.items():
            context=browser.new_context(viewport={'width':1280,'height':900},service_workers='block');page=context.new_page()
            page.on('pageerror',lambda e:report['errors'].append(e.stack or str(e)))
            page.on('response',lambda r:report['failedRequests'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            result=report['heroes'][slug]={}
            try:
                print(slug,'native opening',flush=True);frame=base.boot(page,dex,'desktop')
                if not args.baseline:
                    result['selectedAssets']=frame.evaluate("""({dex,slug})=>{const keys=Object.keys(G.JujutsuArt.images).sort(),expected=[slug+'-common',slug+'-skills',...(slug==='yuta'?['rika-skills']:[])].sort();
                      JAcceptance.assert(JSON.stringify(keys)===JSON.stringify(expected),'unselected character atlases eagerly loaded '+keys);return {dex,keys};}""",{'dex':dex,'slug':slug})
                result['opening']=opening(page,frame,out,slug)
                print(slug,'level9 loop',flush=True);result['level9']=learned_loop(page,frame,out,slug)
                if not args.baseline:
                    result['phases']=phase_checks(frame,out,slug)
                    result['semanticContacts']=semantic_contacts(frame,out,slug)
                    if slug=='yuta':
                        result['manifestCompanion']=manifestation(frame,out)
                        result['companionDrawOrder']=companion_order(page,frame,out)
                    result['icons']=frame.evaluate("""()=>{const p=G.Game.player,icons=[...G.Jujutsu.owners].filter(([id,dex])=>dex===p.dex).map(([id])=>({id,url:G.Icons.url('move:'+id)}));
                      JAcceptance.assert(new Set(icons.map(i=>i.url)).size===icons.length,'skill icons are indistinguishable');return icons.map(({id,url})=>({id,bytes:url.length}));}""")
                    print(slug,'stress',flush=True);result['stress']=frame.evaluate(STRESS)
                    result['renderFrames']=frame.evaluate("""()=>new Promise(resolve=>{const intervals=[];let last=performance.now();JAcceptance.resume();
                      function frame(now){intervals.push(now-last);last=now;if(intervals.length<180)requestAnimationFrame(frame);else{JAcceptance.pause();intervals.shift();intervals.sort((a,b)=>a-b);
                      resolve({scope:'actual native RAF render with50-enemy fixture for180frames',p50:intervals[89],p95:intervals[170],p99:intervals[177],max:intervals.at(-1)})}}requestAnimationFrame(frame);})""")
                    result['deathRestart']=death_restart(frame,out,slug)
                    if slug=='ryu':result['assetSwitching']=switch_assets(page,frame,out)
            except Exception as e:
                report['failures'].append(slug+': '+str(e));page.screenshot(path=str(out/f'{slug}-failure.png'))
            finally:
                context.close();(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            if not args.baseline:
                context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,service_workers='block');page=context.new_page()
                page.on('pageerror',lambda e:report['errors'].append(e.stack or str(e)))
                page.on('response',lambda r:report['failedRequests'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
                try:
                    frame=base.boot(page,dex,'mobile');result['mobileLoop']=learned_loop(page,frame,out,'mobile-'+slug)
                    result['mobileHud']=frame.evaluate("""()=>{const p=G.Game.player,n=p.slots.length+p.moves.filter(m=>m.passive&&!p.slots.some(g=>g.includes(m))).length,
                      layout=G.Touch.controlLayout(innerWidth,innerHeight,n);for(const s of layout.slots)JAcceptance.assert(s.x>=0&&s.y>=0&&s.x+s.w<=innerWidth&&s.y+s.h<=innerHeight,'HUD slot clipped');
                      JAcceptance.assert(document.documentElement.scrollWidth<=innerWidth,'horizontal overflow');return {width:innerWidth,height:innerHeight,slots:layout.slots};}""")
                except Exception as e:
                    report['failures'].append('mobile-'+slug+': '+str(e));page.screenshot(path=str(out/f'mobile-{slug}-failure.png'))
                finally:context.close()
        browser.close()
    report['sourceHashesAfter']=base.hashes();report['ok']=not(report['errors']or report['failedRequests']or report['failures'])
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime changed during capture');report['ok']=False
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if not args.baseline:comparison_gallery()
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'evidence':str(out)},ensure_ascii=True))
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':main()
