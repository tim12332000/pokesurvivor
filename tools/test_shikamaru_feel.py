"""Shikamaru shared-loop acceptance and equal-cost encounter measurements.

Controlled fixtures are explicitly marked; no result asserts subjective fun.
Old six-group tests remain historical safety regressions, not the new contract.
"""
from __future__ import annotations
import base64,hashlib,json,os,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_shikamaru as base

ROOT=base.ROOT
OUT=Path(os.environ.get('SHIKAMARU_FEEL_OUT',ROOT/'art-review/shikamaru/qa/feel'))

SETUP=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;
 A.assert(S.version>=4,'shared-loop runtime not loaded; refusing legacy green result');
 const reset=A.reset;
 A.reset=()=>{reset();p.moves=[G.Moves.instance('naruto-shikamaru',1)];p.level=1;};
 A.build=(cards=[])=>{A.reset();p.level=Math.max(1,cards.length+1);const ledger=[];
  for(const key of cards){const c=G.LevelUp.offer(p,1000).find(c=>c.key===key);A.assert(c&&c.apply(p)!==false,'legal build card missing '+key);ledger.push(key)}
  A.assert(ledger.length===cards.length,'card cost mismatch');return ledger;
 };
 A.sim=(dt=.01,dx=0,dy=0)=>{p.x+=dx;p.y+=dy;A.resume();try{G.Combat.tick(dt,p,0);S.update(dt);p.anim.update(dt)}finally{A.pause()}};
 A.run=(seconds,velocity=()=>[0,0])=>{for(let i=0;i<Math.ceil(seconds/.01);i++){const [vx,vy]=velocity(i*.01);A.sim(.01,vx*.01,vy*.01)}};
 A.realHits=(es)=>{const events=[];for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);if(hp>this.hp)events.push({id:args[7],owner:args[6]===p,loss:hp-this.hp,target:es.indexOf(this),time:S.stateFor(p)?.clock});return result}}return events};
 A.reset();
}"""

PROFILES=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const q of [0,1,3]){A.build(['new:naruto-shikamaru-sewing','new:naruto-shikamaru-trap',...Array(q).fill('stat:quantity')]);
  const shadow=S.profile(p,p.moves[0]),trap=S.profile(p,p.moves.find(m=>m.id==='naruto-shikamaru-trap'));
  A.assert(shadow.branches===4+2*q,'real branch profile '+q);A.assert(trap.traps===3+2*q,'real board capacity '+q);A.assert(trap.blastRounds===1+q,'real blast rounds '+q);
  out.push({q,cost:2+q,shadow,trap});
 }
 return out;
}"""

COVERAGE=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const q of [0,1,3]){const cards=Array(q).fill('stat:quantity');A.build(cards);const es=Array.from({length:12},(_,i)=>A.spawn(Math.cos(i*Math.PI/6)*160,Math.sin(i*Math.PI/6)*160)),hits=A.realHits(es);p.target=es[0];
  A.run(12);const times=[0,...new Set(hits.map(h=>h.time)),12].sort((a,b)=>a-b);out.push({q,cost:cards.length,hits,distinctTargets:new Set(hits.map(h=>h.target)).size,firstCaptureTargets:new Set(hits.filter(h=>h.time<=.55).map(h=>h.target)).size,damage:hits.reduce((s,h)=>s+h.loss,0),maxNoHitSeconds:Math.max(...times.slice(1).map((n,i)=>n-times[i])),stats:S.stats(p)});
 }
 A.assert(out[1].firstCaptureTargets===out[0].firstCaptureTargets+2&&out[2].firstCaptureTargets===out[0].firstCaptureTargets+6,'first quantity did not add real distinct target coverage');
 return out;
}"""




MOVEMENT=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const boss of [false,true]){A.build([]);const e=A.spawn(80,0,boss);p.target=e;A.run(.4);A.assert(S.held(e),'delta fixture not captured');
  const old={x:e.x,y:e.y};A.sim(.01,10,0);const moved=e.x-old.x;A.assert(Math.abs(moved-(boss?0:10))<1e-6,'actual delta copied incorrectly '+boss+' '+moved);
  const stopped={x:e.x,y:e.y};A.sim(.01);A.assert(e.x===stopped.x&&e.y===stopped.y,'stopped owner pulled enemy');
  const limit=e.x+5,nativeFree=G.World.isFree;G.World.isFree=(x,y)=>x<limit;
  const before=e.x;try{A.sim(.01,12,0)}finally{G.World.isFree=nativeFree}
  A.assert(boss?e.x===before:e.x<limit&&e.x-before<12,'delta dragged target through wall');out.push({boss,old,moved,wallDelta:e.x-before});
 }
 return out;
}"""

BOARD=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const q of [0,1,3]){A.build(['new:naruto-shikamaru-sewing','new:naruto-shikamaru-trap',...Array(q).fill('stat:quantity')]);A.sim();A.run(4,()=>[150,0]);const s=S.stateFor(p),nodes=s.board.map(t=>({x:t.x,y:t.y,born:t.born,blastAt:t.blastAt,round:t.round}));
  A.assert(nodes.length===3+2*q,'quantity did not deploy real nodes '+q+' '+nodes.length);A.assert(nodes.every((t,i)=>Math.abs(t.x-(i+1)*54)<1e-6&&t.y===0),'nodes not fixed to true path');
  const originals=s.board.slice(),before=originals.map(t=>({x:t.x,y:t.y,born:t.born,blastAt:t.blastAt}));A.run(.5,()=>[0,80]);A.assert(originals.every((t,i)=>s.board.includes(t)&&t.x===before[i].x&&t.y===before[i].y&&t.born===before[i].born&&t.blastAt===before[i].blastAt),'new movement reset old node lifetime or fuse');
  A.run(11);A.assert(!S.stateFor(p).board.length,'expired fixed nodes remained');out.push({q,nodes,afterExpiry:S.stateFor(p).board.length});
 }
 return out;
}"""

STRATEGIES=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const strategy of ['stop','timeout','loop','retreat']){A.build(['new:naruto-shikamaru-sewing','new:naruto-shikamaru-trap','new:naruto-shikamaru-tactics','new:naruto-shikamaru-strangle']);const es=Array.from({length:6},(_,i)=>A.spawn(80+20*i,(i%2?1:-1)*20)),hits=A.realHits(es);p.target=es[0];const phases=[],boards=[],initialHeld=[],keyed=new Set();let netAt=null;
  for(let i=0;i<900;i++){const t=i*.01,s=S.stateFor(p),phase=s?.plan?.phase;let vx=strategy==='retreat'?-90:90,vy=0;if(strategy==='stop'&&t>=1)vx=0;if(strategy==='loop'){vx=t<1?90:t<2?0:t<3?-90:0;vy=t<1?0:t<2?90:t<3?0:-90}
   A.sim(.01,vx*.01,vy*.01);const st=S.stateFor(p),ph=st?.plan?.phase||'none';if(ph==='net'&&netAt===null)netAt=st.clock;if(!keyed.has(ph)){keyed.add(ph);phases.push({phase:ph,time:st?.clock})}if(i%20===0)boards.push({time:st?.clock,nodes:st?.board.map(t=>({x:t.x,y:t.y,born:t.born,round:t.round,blastAt:Number.isFinite(t.blastAt)?t.blastAt:null}))});
  }
  A.assert(phases.some(x=>x.phase==='blast')&&phases.some(x=>x.phase==='finish')&&phases.some(x=>x.phase==='recover'),'strategy lost complete climax '+strategy);
  A.assert(S.stats(p).detonations>0,'strategy failed to execute actual node blast rounds '+strategy);A.assert(hits.some(h=>h.id==='naruto-shikamaru-strangle'),'strategy lost net-triggered finisher '+strategy);
  out.push({strategy,netAt,phases,boards,hits,stats:S.stats(p)});
 }
 A.assert(out[0].netAt<out[1].netAt,'stopping did not advance eligible net');A.assert(out[2].hits.some(h=>h.id==='naruto-shikamaru-trap')&&out[3].hits.some(h=>h.id==='naruto-shikamaru-trap'),'loop never brought enemies into actual fixed-node geometry');A.assert(JSON.stringify(out[1].boards)!==JSON.stringify(out[2].boards),'straight and loop laid identical nodes');return out;
}"""


CANCELLATION=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const reason of ['death','world','shadow-removed','clear']){A.build(['new:naruto-shikamaru-sewing','new:naruto-shikamaru-trap']);const e=A.spawn(80,0);p.target=e;A.run(.9,()=>[-90,0]);A.assert(S.stateFor(p)?.board.length&&S.held(e),'cleanup fixture lacks live plan/board/lease');const world=G.World;
  if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};if(reason==='shadow-removed')p.moves=p.moves.filter(m=>m.id!=='naruto-shikamaru');if(reason==='clear')S.clear(p);
  try{A.resume();S.update(.01)}finally{A.pause();p.dead=false;G.World=world}
  A.assert(!S.stateFor(p)&&!S.held(e)&&!S.casts.some(b=>b.owner===p),'shared state leaked after '+reason);out.push(reason);
 }
 A.build(['new:naruto-shikamaru-sewing','new:naruto-shikamaru-trap']);const es=[A.spawn(80,-10),A.spawn(90,10)];p.target=es[0];let trapHits=0;
 for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const result=hurt.apply(this,args);if(args[7]==='naruto-shikamaru-trap'){trapHits++;S.clear(p)}return result}}
 for(let i=0;i<500&&trapHits===0;i++)A.sim(.01,i<100?-.9:0,0);
 A.assert(trapHits===1,'chain callback never fired or hit later target');for(let i=0;i<200;i++){A.resume();try{S.update(.01)}finally{A.pause()}}A.assert(trapHits===1&&!S.stateFor(p),'cancelled chain fired future nodes/rounds');out.push({chainCancellation:trapHits});return out;
}"""

LV1=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.build([]);const es=[A.spawn(80,-10),A.spawn(90,10)],hits=A.realHits(es);p.target=es[0];const phases=[];let netAt=null,previous='',releaseCount=0;
 for(let i=0;i<500;i++){A.sim();const s=S.stateFor(p),phase=s?.plan?.phase||'none';if(phase!==previous){phases.push({phase,time:s.clock,hits:hits.length,held:es.filter(S.held).length});if(phase==='net')netAt=s.clock;previous=phase}if(phase==='recover'){releaseCount++;A.assert(es.every(e=>!S.held(e)),'recover left live possession')}}
 A.assert(netAt!==null&&hits.some(h=>h.time>netAt),'Lv1 net has no true second attack');A.assert(!S.stateFor(p).board.length&&S.stats(p).detonations===0,'unlearned traps created nodes or explosions');A.assert(releaseCount>0,'Lv1 failed to recover/release');return {phases,hits,releaseCount};
}"""


EMPTY=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 A.build([]);const prop={x:80,y:0,r:14,hp:100000,type:'rock',destructible:true,tx:2,ty:0};G.World.propsInCircle=()=>[prop];A.run(3);A.assert(prop.hp<100000,'props-only basic failed native damageProp');A.assert(!S.stateFor(p).plan&&S.stats(p).cycles===0&&!S.stateFor(p).board.length,'props-only invented enemy climax');out.push({propsDamage:100000-prop.hp,cycles:S.stats(p).cycles});
 A.build([]);const e=A.spawn(80,0);p.target=e;A.sim();e.y=500;G.EnemyMgr.rebuildGrid();const phases=[];for(let i=0;i<200;i++){A.sim();phases.push(S.stateFor(p)?.plan?.phase||'none')}
 A.assert(!phases.some(p=>['drag','net','blast','finish'].includes(p)),'missed capture entered empty climax');out.push({dodgedPhases:[...new Set(phases)]});
 A.build([]);const target=A.spawn(80,0);p.target=target;A.run(.4);A.assert(S.held(target),'kill fixture never captured');target.hp=0;target.dead=true;G.EnemyMgr.rebuildGrid();const after=[];for(let i=0;i<200;i++){A.sim();after.push(S.stateFor(p)?.plan?.phase||'none')}
 A.assert(!after.some(p=>['net','blast','finish'].includes(p)),'dead captured group continued empty climax');out.push({deadGroupPhases:[...new Set(after)]});return out;
}"""


BLAST_ROUNDS=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const q of [0,1,3]){A.build(['new:naruto-shikamaru-sewing','new:naruto-shikamaru-trap',...Array(q).fill('stat:quantity')]);const es=[A.spawn(80,-15),A.spawn(90,15)],hits=A.realHits(es);p.target=es[0];let scheduled=null,blastTarget=null,blastEvents=[];
  for(let i=0;i<700;i++){A.sim(.01,-.9,0);const s=S.stateFor(p);if(s.plan?.phase==='blast'&&!scheduled){scheduled=s.board.filter(t=>Number.isFinite(t.blastAt)).slice();if(scheduled.length){blastTarget=A.spawn(scheduled[0].x,scheduled[0].y,true);const hurt=blastTarget.hurt;blastTarget.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);if(args[7]==='naruto-shikamaru-trap'&&hp>this.hp)blastEvents.push({clock:S.stateFor(p)?.clock,loss:hp-this.hp});return result}}}if(scheduled&&s.plan?.phase==='finish')break;}
  A.assert(scheduled?.length>0,'no actual chain nodes scheduled '+q);A.assert(scheduled.every(t=>t.round===1+q),'actual node rounds lost/duplicated '+q+' '+scheduled.map(t=>t.round));const expected=scheduled.filter(t=>Math.hypot(t.x-blastTarget.x,t.y-blastTarget.y)<=t.cast.spec.radius+blastTarget.r).reduce((sum,t)=>sum+t.cast.spec.blastRounds,0);A.assert(expected>0&&blastEvents.length===expected,'in-range native hurt did not consume every planned node round '+q+' '+blastEvents.length+'/'+expected);
  out.push({q,scheduled:scheduled.map(t=>({x:t.x,y:t.y,born:t.born,blastAt:t.blastAt,round:t.round})),blastTarget:{x:blastTarget.x,y:blastTarget.y,r:blastTarget.r},expected,blastEvents,trapHits:hits.filter(h=>h.id==='naruto-shikamaru-trap'),stats:S.stats(p)});
 }
 return out;
}"""

CLONES=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.build(['new:naruto-shikamaru-sewing','new:naruto-shikamaru-trap']);const clone=G.SelfClones.summon(p);clone.x=0;clone.y=80;A.spawn(90,0);A.spawn(90,80);
 A.resume();try{G.Combat.tick(.01,p,0);G.Combat.tick(.01,clone,0);S.update(.01)}finally{A.pause()}
 for(let i=0;i<100;i++){p.x-=1;clone.x+=1;A.resume();try{G.Combat.tick(.01,p,0);G.Combat.tick(.01,clone,0);S.update(.01)}finally{A.pause()}}
 const own=S.stateFor(p),other=S.stateFor(clone);A.assert(own&&other&&own!==other&&own.plan!==other.plan&&own.board!==other.board,'clone shared phase/board state');A.assert(own.board.length&&other.board.length&&own.board.every(t=>t.cast.owner===p)&&other.board.every(t=>t.cast.owner===clone),'clone node attribution missing');
 const cloneNodes=other.board.slice();S.clear(p);A.assert(!S.stateFor(p)&&S.stateFor(clone)===other&&cloneNodes.every(t=>other.board.includes(t)),'owner clear erased independent clone route');return {ownerNodes:own.board.map(t=>({x:t.x,y:t.y})),cloneNodes:other.board.map(t=>({x:t.x,y:t.y}))};
}"""

NATURAL_OBSERVE=r"""() => {
 const R=window.FeelQA={hits:[],ledger:[],offers:[],events:[],samples:[],inputs:[],current:null};
 const nativeHurt=G.Enemy.prototype.hurt;G.Enemy.prototype.hurt=function(...args){const hp=this.hp,result=nativeHurt.apply(this,args);if(args[6]===G.Game.player&&hp>this.hp)R.hits.push({time:G.Game.st.time,id:args[7],loss:hp-this.hp,x:this.x,y:this.y});return result};
 R.snapshot=()=>{const p=G.Game.player,s=p&&G.NarutoShikamaru.stateFor(p);return p?{time:G.Game.st.time,level:p.level,hp:p.hp,maxHp:p.maxHp,dead:!!p.dead,x:p.x,y:p.y,moves:p.moves.map(m=>({id:m.id,rank:m.lvl})),quantity:p.quantityPicks||0,strangleHits:R.hits.filter(h=>h.id==='naruto-shikamaru-strangle').length,phase:s?.plan?.phase||null,cycle:s?.cycles||0,clock:s?.clock||0,phaseStarted:s?.plan?.started,captureAt:s?.plan?.captureAt,stop:s?.plan?.stop||0,moving:s?.moving,board:s?.board?.map(t=>({x:t.x,y:t.y,born:t.born,blastAt:Number.isFinite(t.blastAt)?t.blastAt:null,round:t.round}))||[],captured:[...G.NarutoShikamaru.leases].filter(([e,l])=>l.cast.owner===p&&G.NarutoShikamaru.held(e)).length,nearestEnemy:Math.min(1e9,...G.EnemyMgr.all().filter(e=>!e.dead).map(e=>Math.hypot(e.x-p.x,e.y-p.y))),stats:G.NarutoShikamaru.stats(p)}:null};
 const show=G.RunUI.showLevelUp;G.RunUI.showLevelUp=function(level,list,cb,...args){const offer={serial:R.offers.length,time:G.Game.st.time,level,options:list.map(c=>({key:c.key,type:c.type,title:c.title,desc:c.desc}))};R.offers.push(offer);R.current=offer;return show.call(this,level,list,card=>{const before=R.snapshot();cb(card);R.ledger.push({cost:R.ledger.length+1,key:card.key,offer:offer.serial,before,after:R.snapshot()});R.current=null},...args)};
 let lastPhase='',lastSample=-1;function observe(){if(G.Game.state==='playing'){const s=R.snapshot();if(s){const key=s.cycle+':'+s.phase;if(key!==lastPhase){R.events.push(s);lastPhase=key}if(s.time-lastSample>=.1){R.samples.push(s);lastSample=s.time}}}requestAnimationFrame(observe)}requestAnimationFrame(observe);
}"""

def natural():
    import test_shikamaru_play as old
    out=OUT/'natural';out.mkdir(parents=True,exist_ok=True)
    report={'natural':True,'sourceBefore':manifest(),'errors':[],'policy':'Real keyboard square path D/S/A/W (two native seconds per side); alternate learned-trap cycles stop after mature fixed node plus >=2 captures, then continue; other cycles keep moving for timeout; new > upgrade > quantity cards via actual UI.'}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        context=browser.new_context(viewport={'width':1100,'height':850},service_workers='block',record_video_dir=str(out/'raw'),record_video_size={'width':1100,'height':850})
        page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(base.URL)
        page.wait_for_function('window.PS_REDRAWN_READY&&window.G?.NarutoShikamaru&&document.getElementById("boot").classList.contains("hidden")')
        if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
        page.locator('[data-quick-naruto="30017"]').click();report['permanent']=page.evaluate('G.DB.upgradesOf(G.DB.save.partner)');assert not any(report['permanent'].values())
        page.evaluate(NATURAL_OBSERVE);page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30017&&G.Game.state==="playing"')
        report['initial']=page.evaluate('FeelQA.snapshot()');assert report['initial']['level']==1
        held=None;serial=None;stop_until=-1;stop_cycles=set();timeout_cycles=set();seen_trap_cycle=None;last_progress=-30;started=time.monotonic()
        while time.monotonic()-started<600:
            s=page.evaluate('({state:G.Game.state,snapshot:FeelQA.snapshot(),offer:FeelQA.current})');a=s['snapshot'];t=a['time']
            if a['dead'] or s['state']=='over' or t>300:break
            if t-last_progress>=30:
                print('feel natural',round(t),'Lv',a['level'],a['phase'],'nodes',len(a['board']),'captured',a['captured'],flush=True);last_progress=t;(out/'progress.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
            if s['state']=='levelup' and s['offer'] and s['offer']['serial']!=serial:
                if held:page.keyboard.up(held);held=None
                offer=s['offer'];chosen=min(range(len(offer['options'])),key=lambda i:(old.priority(offer['options'][i]),i));page.screenshot(path=str(out/f'card-{offer["serial"]}.png'));page.locator('#cards .card').nth(chosen).click();serial=offer['serial']
            elif page.locator('#scr-item').is_visible():page.locator('#item-cards .card').first.click()
            elif page.locator('#scr-bond').is_visible():page.locator('#bond-cards .card').first.click()
            elif s['state']=='playing':
                has_trap=any(m['id']=='naruto-shikamaru-trap' for m in a['moves'])
                if has_trap and seen_trap_cycle is None:seen_trap_cycle=a['cycle']
                stop_cycle=has_trap and (a['cycle']-(seen_trap_cycle or 0))%2==0
                ready=a['phase']=='drag' and a['captured']>=2 and any(a['clock']-n['born']>=.55 for n in a['board']) and a.get('captureAt') is not None and a['clock']-a['captureAt']>=.7
                if stop_cycle and ready and a['cycle'] not in stop_cycles:stop_until=t+.45;stop_cycles.add(a['cycle'])
                if has_trap and not stop_cycle:timeout_cycles.add(a['cycle'])
                key=None if t<stop_until else ['KeyD','KeyS','KeyA','KeyW'][int(t//2)%4]
                if key!=held:
                    if held:page.keyboard.up(held)
                    if key:page.keyboard.down(key)
                    page.evaluate('entry=>FeelQA.inputs.push(entry)',{'time':t,'key':key,'phase':a['phase'],'cycle':a['cycle'],'reason':'early-net-stop' if key is None else 'path-and-timeout' if not stop_cycle else 'path-and-return'});held=key
                completed=page.evaluate('FeelQA.events.filter(e=>e.phase==="recover"&&(e.strangleHits||0)>0).map(e=>e.cycle)')
                if any(c in stop_cycles for c in completed) and any(c in timeout_cycles for c in completed):report['coreComplete']=True;break
            elif s['state']=='paused':page.locator('#btn-resume').click()
            page.wait_for_timeout(55)
        if held:page.keyboard.up(held)
        report.update(page.evaluate('({hits:FeelQA.hits,ledger:FeelQA.ledger,offers:FeelQA.offers,events:FeelQA.events,samples:FeelQA.samples,inputs:FeelQA.inputs,final:FeelQA.snapshot(),state:G.Game.state})'))
        report['stopCycles']=sorted(stop_cycles);report['timeoutCycles']=sorted(timeout_cycles);page.screenshot(path=str(out/'final.png'));video=page.video;context.close();video.save_as(str(out/'native-play.webm'));video.delete();browser.close()
    report['sourceAfter']=manifest();report['sourceStable']=report['sourceAfter']==report['sourceBefore'];(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'coreComplete':report.get('coreComplete',False),'final':report['final'],'sourceStable':report['sourceStable']},ensure_ascii=False))



def native_demo():
    out=OUT/'native';out.mkdir(parents=True,exist_ok=True)
    report={'controlled':True,'sourceBefore':manifest(),'errors':[],'scenes':[],'fixture':'Eight actual cards, rank1 except tactics2, Q3, native keyboard and RAF only after controlled arena setup; zero permanent upgrades; static million-HP targets.'}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True);context=browser.new_context(viewport={'width':1100,'height':850},service_workers='block',record_video_dir=str(out/'raw'),record_video_size={'width':1100,'height':850});page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));base.boot(page);page.evaluate(SETUP);page.evaluate(NATURAL_OBSERVE)
        page.evaluate(r"""()=>{window.FeelFrames=[];const draw=G.ShikamaruArt.draw,seen=new Set();G.ShikamaruArt.draw=function(ctx,actor,opts){const result=draw.call(this,ctx,actor,opts),s=G.NarutoShikamaru.stateFor(actor);if(actor===G.Game.player&&s?.plan){const key=window.FeelScene+':'+s.plan.phase+':'+s.moving;if(!seen.has(key)){seen.add(key);const record={scene:window.FeelScene,phase:s.plan.phase,moving:s.moving,pose:opts.pose?{kind:opts.pose.kind,phaseAge:opts.pose.phaseAge,phaseDuration:opts.pose.phaseDuration}:null,clock:s.clock,cycle:s.cycles,player:{x:actor.x,y:actor.y},board:s.board.map(t=>({x:t.x,y:t.y,born:t.born,round:t.round})),captured:[...G.NarutoShikamaru.leases].filter(([e,l])=>l.cast.owner===actor&&G.NarutoShikamaru.held(e)).map(([e])=>({x:e.x,y:e.y})),stats:G.NarutoShikamaru.stats(actor)};queueMicrotask(()=>FeelFrames.push({...record,png:ctx.canvas.toDataURL()}));}}return result}}""")
        for scene in ['early-stop','continuous-timeout']:
            page.evaluate(r"""scene=>{window.FeelScene=scene;Acceptance.build(['new:naruto-shikamaru-sewing','new:naruto-shikamaru-trap','new:naruto-shikamaru-tactics','new:naruto-shikamaru-strangle','stat:quantity','stat:quantity','stat:quantity','up:naruto-shikamaru-tactics']);for(let i=0;i<8;i++)Acceptance.spawn(80+(i%4)*25,(i<4?-1:1)*25);const p=Acceptance.p();p.invuln=999;p.target=G.EnemyMgr.all()[0];Acceptance.resume();}""",scene)
            held=None;stopped=False;stop_until=-1;started=time.monotonic();initial_time=page.evaluate('G.Game.st.time');inputs=[]
            while time.monotonic()-started<8:
                a=page.evaluate('FeelQA.snapshot()');elapsed=a['time']-initial_time
                if elapsed>=12:break
                ready=a['phase']=='drag' and a['captured']>=2 and any(a['clock']-n['born']>=.55 for n in a['board']) and a.get('captureAt') is not None and a['clock']-a['captureAt']>=.7
                if scene=='early-stop' and ready and not stopped:stopped=True;stop_until=a['time']+.45
                key=None if a['time']<stop_until else ['KeyA','KeyW','KeyD','KeyS'][int(elapsed//1.1)%4]
                if key!=held:
                    if held:page.keyboard.up(held)
                    if key:page.keyboard.down(key)
                    inputs.append({'time':a['time'],'key':key,'phase':a['phase'],'captured':a['captured']});held=key
                page.wait_for_timeout(45)
            if held:page.keyboard.up(held)
            page.evaluate('Acceptance.pause()');report['scenes'].append({'scene':scene,'inputs':inputs,'final':page.evaluate('FeelQA.snapshot()')})
        report['frames']=[]
        for index,c in enumerate(page.evaluate('FeelFrames')):
            png=c.pop('png');name=f'{index:02d}-{c["scene"]}-{c["phase"]}-'+('moving' if c['moving'] else 'still')+'.png';(out/name).write_bytes(base64.b64decode(png.split(',',1)[1]));report['frames'].append({'image':name,**c})
        report.update(page.evaluate('({events:FeelQA.events,samples:FeelQA.samples})'));video=page.video;context.close();video.save_as(str(out/'shared-cycle.webm'));video.delete();browser.close()
    report['sourceAfter']=manifest();report['sourceStable']=report['sourceAfter']==report['sourceBefore'];(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'frames':len(report['frames']),'sourceStable':report['sourceStable'],'errors':report['errors']}))


def manifest():
    names=['.omx/naruto-shikamaru.js','.omx/naruto-skills.js','.omx/naruto-training.js','.omx/jujutsu-growth.js','js/entities/enemy.js','js/systems/combat.js','js/systems/self-clone.js','art-review/shikamaru-art.js','art-review/shikamaru-frames.json','.omx/digimon.html']
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'url':base.URL,'controlled':True,'sourceBefore':manifest(),'checks':{},'errors':[],'fixture':'Fixed zero permanent stats, true card application; native Combat.tick/module.update, dt .01; explicit player displacement only in controlled movement fixtures.'}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
            page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block');page.on('pageerror',lambda e:report['errors'].append(str(e)))
            base.boot(page);page.evaluate(SETUP)
            for name,check in [('profiles',PROFILES),('coverage',COVERAGE),('movement',MOVEMENT),('board',BOARD),('strategies',STRATEGIES),('cancellation',CANCELLATION),('lv1',LV1),('empty',EMPTY),('blastRounds',BLAST_ROUNDS),('clones',CLONES)]:
                report['checks'][name]=page.evaluate(check);print(name,'PASS',flush=True)
            report['legacySafety']={}
            for name,check in [('progression',base.PROGRESSION),('geometry',base.GEOMETRY),('lifecycle',base.LIFECYCLE),('control',base.CONTROL),('strangle',base.STRANGLE)]:
                page.evaluate('Acceptance.reset()');report['legacySafety'][name]=page.evaluate(check);print('legacy',name,'PASS',flush=True)
            report['retiredLegacyContracts']={'growth-three-targets':'The old three-target consumer fixture saturates at the new four-branch Lv1 baseline, so it cannot distinguish quantity. Replaced by 12 dispersed targets and first-capture-window true contacts (Q0/Q1/Q3=4/6/10); no old expected value rewritten.'}
            browser.close()
        assert not report['errors'],report['errors'];report['ok']=True
    except Exception as error:report['failure']=str(error);raise
    finally:
        report['sourceAfter']=manifest();report['sourceStable']=report['sourceAfter']==report['sourceBefore']
        (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':
    if '--natural' in sys.argv:natural()
    elif '--native' in sys.argv:native_demo()
    else:main()
