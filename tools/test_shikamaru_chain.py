"""One-root organic Shikamaru chain acceptance.

New chain behavior is isolated from older radial capture evidence. Controlled
geometry checks and native genuine-card observations are reported separately.
"""
from __future__ import annotations
import base64,hashlib,json,os,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_shikamaru as base
import test_shikamaru_feel as feel

ROOT=base.ROOT
OUT=Path(os.environ.get('SHIKAMARU_CHAIN_OUT',ROOT/'art-review/shikamaru/qa/chain'))

def manifest():
    names=['.omx/naruto-shikamaru.js','.omx/naruto-skills.js','.omx/jujutsu-growth.js','art-review/shikamaru-art.js','art-review/shikamaru-frames.json','.omx/digimon.html']
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}



SETUP=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;
 A.chainBuild=(rank=1,q=0)=>{A.reset();p.statsTaken={};p.moves=[G.Moves.instance('naruto-shikamaru',1)];p.level=rank+q+1;const ledger=[];for(let i=1;i<rank;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='up:naruto-shikamaru');A.assert(c&&c.apply(p)!==false,'real basic upgrade missing');ledger.push('up:naruto-shikamaru')}for(let i=0;i<q;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');A.assert(c&&c.apply(p)!==false,'real quantity card missing');ledger.push('stat:quantity')}return ledger};
 A.chainSpawn=()=>[A.spawn(80,0),A.spawn(160,50),A.spawn(245,-15),A.spawn(310,70)];
 A.chainWatch=es=>{const events=[];es.forEach((e,i)=>{const hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);if(hp>this.hp)events.push({index:i,time:S.stateFor(p)?.clock,loss:hp-this.hp,id:args[7],x:this.x,y:this.y,owner:args[6]===p});return result}});return events};
 A.chainCast=es=>{p.target=es[0];A.cast(p.moves[0]);const b=S.casts.at(-1);A.assert(b?.chain,'new single-root chain runtime missing');return b};
 A.chainSnapshot=b=>({age:b.age,ended:b.chain.ended,lastContact:b.chain.lastContact,segments:b.chain.segments.map(s=>({origin:s.origin,path:s.path,grownPoints:s.grownPoints,polygon:s.polygon,contactPoint:s.contactPoint,contact:s.contact,targetPosition:s.target?{x:s.target.x,y:s.target.y,dead:s.target.dead}:null}))});
 A.chainRun=(b,seconds=4)=>{const trace=[];for(let i=0;i<seconds*100;i++){A.step(.01);if(i%5===0)trace.push(A.chainSnapshot(b))}return trace};
}"""

GROWTH=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const [rank,q]of [[1,0],[2,0],[3,0],[1,1],[1,3]]){const ledger=A.chainBuild(rank,q),es=A.chainSpawn(),events=A.chainWatch(es),b=A.chainCast(es),initial=A.chainSnapshot(b);A.assert(b.spec.simultaneousRoots===1&&b.chain.segments.length===1,'cast fanned before first contact');A.assert(b.spec.chainTargets===Math.min(16,rank+q),'chain profile budget differs');const trace=A.chainRun(b),unique=[...new Set(events.map(e=>e.index))];
  A.assert(unique.length===Math.min(4,rank+q),'real distinct chain targets did not consume cards '+rank+'/'+q+': '+unique);A.assert(events.every(e=>e.owner&&e.id==='naruto-shikamaru'),'chain bypassed owned hurt');A.assert(unique.every((n,i)=>events.find(e=>e.index===n).time>=(i?events.find(e=>e.index===unique[i-1]).time:0)),'later target was pre-hit');out.push({rank,q,cost:ledger.length,ledger,initial,events,trace,final:A.chainSnapshot(b),visual:S.shadowVisualFor(p)});
 }
 return out;
}"""

STOPPING=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const reason of ['miss','target-dead-before-contact','wall','callback-clear','owner-death','world']){A.chainBuild(1,3);const es=A.chainSpawn(),events=A.chainWatch(es),b=A.chainCast(es),world=G.World,block=G.World.projectileBlock,path=G.World.projectilePathClear;
  if(reason==='miss'){es[0].x=1000;es[0].y=1000;G.EnemyMgr.rebuildGrid()}
  if(reason==='target-dead-before-contact'){es[0].hp=0;es[0].dead=true;G.EnemyMgr.rebuildGrid()}
  if(reason==='wall'){G.World.projectileBlock=(x)=>x>=120?{wall:true}:false;G.World.projectilePathClear=(ax,ay,bx,by)=>Math.max(ax,bx)<120}
  if(reason==='callback-clear'){const hurt=es[0].hurt;es[0].hurt=function(...args){const r=hurt.apply(this,args);S.clear(p);return r}}
  if(reason==='owner-death')p.dead=true;if(reason==='world')G.World={...world};
  try{A.chainRun(b)}finally{p.dead=false;G.World=world;G.World.projectileBlock=block;G.World.projectilePathClear=path}
  A.assert(!events.some(e=>e.index>0),'chain continued without legal A contact '+reason);if(reason==='wall'||reason==='callback-clear')A.assert(events.some(e=>e.index===0),'stopping fixture failed to contact A '+reason);out.push({reason,events,final:A.chainSnapshot(b)});
 }
 return out;
}"""

LETHAL=r"""() => {
 const A=Acceptance,p=A.p();A.chainBuild(1,1);const es=A.chainSpawn();es[0].hp=1;const events=A.chainWatch(es),b=A.chainCast(es);A.chainRun(b);A.assert(es[0].dead&&events.some(e=>e.index===1),'true lethal A contact failed to relay B');const second=b.chain.segments[1];A.assert(second&&Math.hypot(second.origin.x-80,second.origin.y)<1e-6,'dead A relay used a moving corpse instead of confirmed contact point');return {events,final:A.chainSnapshot(b)};
}"""




PATH_AND_POOL=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out={};
 A.chainBuild(1,1);const es=A.chainSpawn(),events=A.chainWatch(es),b=A.chainCast(es);for(let i=0;i<100&&b.chain.segments.length<2;i++)A.step(.01);A.assert(b.chain.segments.length===2&&b.chain.segments[0].contact,'source fixture failed to hit A');
 const first=JSON.stringify(b.chain.segments[0].grownPoints.slice(1,-1)),point={...b.chain.segments[0].contactPoint};es[0].x+=15;A.step(.01);const second=b.chain.segments[1];A.assert(Math.hypot(second.grownPoints[0].x-es[0].x,second.grownPoints[0].y-es[0].y)<1e-6,'B source did not follow living A endpoint');A.assert(JSON.stringify(b.chain.segments[0].grownPoints.slice(1,-1))===first&&Math.hypot(b.chain.segments[0].grownPoints.at(-1).x-es[0].x,b.chain.segments[0].grownPoints.at(-1).y-es[0].y)<1e-6&&Math.hypot(b.chain.segments[0].contactPoint.x-point.x,b.chain.segments[0].contactPoint.y-point.y)<1e-6,'live endpoints did not preserve fixed interior/contact point');
 es[0].hp=0;es[0].dead=true;es[0].x=1000;A.step(.01);A.assert(Math.hypot(second.grownPoints[0].x-point.x,second.grownPoints[0].y-point.y)<1e-6,'B source followed moved corpse instead of confirmed contact');out.liveAndDeadSource={contactPoint:point,liveMovedX:point.x+15,deadSource:second.grownPoints[0]};
 A.chainBuild(1,3);const targets=A.chainSpawn(),initial=S.shadowVisualFor(p),c=A.chainCast(targets);A.finish(.45);const mid=S.shadowVisualFor(p),snapshot=JSON.stringify(A.chainSnapshot(c)),clock=S.stateFor(p).clock,canvas=document.createElement('canvas');canvas.width=canvas.height=800;const ctx=canvas.getContext('2d');ctx.translate(400,400);for(let i=0;i<100;i++){S.shadowVisualFor(p);G.Combat.drawGroundFields(ctx)}A.assert(JSON.stringify(A.chainSnapshot(c))===snapshot&&S.stateFor(p).clock===clock,'draw/query regenerated organic path or advanced chain');A.assert(mid.poolRadius<initial.poolRadius&&mid.extensionTotal>0,'organic chain extension did not consume visual pool');A.finish(3);const held=S.shadowVisualFor(p);S.clear(p);const restored=S.shadowVisualFor(p);A.assert(restored.poolRadius===34,'cleared organic path did not restore pool');out.pool={initial,mid,held,restored};
 for(const inside of [true,false]){A.chainBuild();const target=A.spawn(300,0);const cast=A.chainCast([target]);A.finish(.4);const segment=cast.chain.segments[0],v=segment.grownPoints[Math.floor(segment.grownPoints.length/2)],x=v.x,y=v.y+(inside?0:60),ground=document.createElement('canvas');ground.width=ground.height=800;const g=ground.getContext('2d');g.translate(400,400);G.Combat.drawGroundFields(g);const alpha=g.getImageData(Math.round(x+400),Math.round(y+400),1,1).data[3];target.x=x;target.y=y;target.r=1;G.EnemyMgr.rebuildGrid();const hits=A.chainWatch([target]);A.step(.01);A.assert(inside?alpha>0&&hits.length>0:alpha===0&&hits.length===0,'organic path true hit did not match drawn polygon '+inside);out[inside?'organicInside':'organicOutside']={x,y,alpha,hits,polygon:segment.polygon};}
 return out;
}"""



PROPS=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.chainBuild();const prop={x:80,y:0,r:14,hp:100000,type:'rock',destructible:true,tx:2,ty:0};G.World.propsInCircle=()=>[prop];for(let i=0;i<300;i++){A.resume();try{G.Combat.tick(.01,p,0);S.update(.01)}finally{A.pause()}}A.assert(prop.hp<100000,'single-root prop fallback failed native damageProp');A.assert(!S.stateFor(p).plan&&S.stats(p).cycles===0&&!S.leases.size,'prop invented captured enemy/chain climax');return {damage:100000-prop.hp,stats:S.stats(p)};
}"""



HIGH_BUDGET=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.chainBuild(1,15);const es=Array.from({length:16},(_,i)=>A.spawn(80+i*200,0)),events=A.chainWatch(es);p.target=es[0];let b=null;const phases=[];
 for(let i=0;i<1800;i++){A.resume();try{G.Combat.tick(.01,p,0);S.update(.01)}finally{A.pause()}b??=S.casts.find(c=>c.owner===p&&c.chain);if(i%20===0)phases.push({time:S.stateFor(p)?.clock,phase:S.stateFor(p)?.plan?.phase,segments:b?.chain.segments.length,current:b?.chain.current});if(b?.chain.ended)break;}
 A.assert(b?.chain.ended&&b.chain.visited.size===16,'high-budget chain lost legal later contacts');A.assert(b.age>2.4,'high-budget fixture never exceeded old timeout');A.assert(new Set(events.map(e=>e.index)).size===16,'high-budget profile had no 16 real hurt targets');return {budget:b.spec.chainTargets,age:b.age,events,phases,final:A.chainSnapshot(b)};
}"""


NATURAL_OBSERVE=r"""() => {
 const R=window.ChainQA={hits:[],ledger:[],offers:[],inputs:[],samples:[],chains:[],frames:[],current:null};
 const S=G.NarutoShikamaru,nativeHurt=G.Enemy.prototype.hurt;G.Enemy.prototype.hurt=function(...args){const hp=this.hp,owner=args[6],id=args[7],chain=[...S.casts].reverse().find(b=>b.owner===G.Game.player&&b.kind==='shadow'&&b.chain?.segments.some(s=>s.target===this&&!s.contact)),index=chain?.chain.segments.findIndex(s=>s.target===this&&!s.contact),result=nativeHurt.apply(this,args);if(owner===G.Game.player&&id==='naruto-shikamaru'&&chain&&hp>this.hp)R.hits.push({time:G.Game.st.time,serial:chain.serial,index,target:this.id,x:this.x,y:this.y,loss:hp-this.hp});return result};
 R.snapshot=()=>{const p=G.Game.player;return p?{time:G.Game.st.time,level:p.level,hp:p.hp,dead:!!p.dead,x:p.x,y:p.y,quantity:p.quantityPicks||0,nearestEnemy:Math.min(1e9,...G.EnemyMgr.all().filter(e=>!e.dead).map(e=>Math.hypot(e.x-p.x,e.y-p.y))),moves:p.moves.map(m=>({id:m.id,rank:m.lvl})),profile:S.profile(p,p.moves.find(m=>m.id==='naruto-shikamaru')),visual:S.shadowVisualFor(p),stats:S.stats(p)}:null};
 const show=G.RunUI.showLevelUp;G.RunUI.showLevelUp=function(level,list,cb,...args){const offer={serial:R.offers.length,time:G.Game.st.time,level,options:list.map(c=>({key:c.key,type:c.type,title:c.title,desc:c.desc}))};R.offers.push(offer);R.current=offer;return show.call(this,level,list,c=>{const before=R.snapshot();cb(c);R.ledger.push({cost:R.ledger.length+1,key:c.key,before,after:R.snapshot()});R.current=null},...args)};
 const draw=G.Combat.drawGroundFields,seen=new Set();G.Combat.drawGroundFields=function(ctx){const result=draw.call(this,ctx);for(const b of S.casts.filter(b=>b.owner===G.Game.player&&b.chain)){const contacts=b.chain.segments.filter(s=>s.contact).length,key=b.spec.chainTargets>=3?'chain-'+Math.min(3,contacts):'Lv1-single-root';if(!seen.has(key)){seen.add(key);const state={time:G.Game.st.time,key,serial:b.serial,budget:b.spec.chainTargets,contacts,visual:S.shadowVisualFor(G.Game.player),segments:b.chain.segments.map(s=>({origin:s.origin,grownPoints:s.grownPoints,contact:s.contact,contactPoint:s.contactPoint}))};queueMicrotask(()=>R.frames.push({...state,png:ctx.canvas.toDataURL()}))}}return result};
 let last=-1;function observe(){if(G.Game.state==='playing'&&G.Game.st.time-last>=.1){last=G.Game.st.time;R.samples.push(R.snapshot());for(const b of S.casts.filter(b=>b.owner===G.Game.player&&b.chain))if(b.chain.ended&&b.chain.visited.size>=3&&!R.chains.some(x=>x.serial===b.serial))R.chains.push({serial:b.serial,time:G.Game.st.time,budget:b.spec.chainTargets,contacts:b.chain.visited.size,segments:b.chain.segments.map(s=>({origin:s.origin,path:s.path,contact:s.contact,contactPoint:s.contactPoint}))})}requestAnimationFrame(observe)}requestAnimationFrame(observe);
}"""

def natural():
    out=OUT/'natural';out.mkdir(parents=True,exist_ok=True);report={'sourceBefore':manifest(),'errors':[],'policy':'Native keyboard D/S/A/W two native seconds per side; prioritize actual shadow upgrade, quantity, new, other upgrade; no XP/HP/invulnerability/AI/clock changes.'}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True);context=browser.new_context(viewport={'width':1100,'height':850},service_workers='block',record_video_dir=str(out/'raw'),record_video_size={'width':1100,'height':850});page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(base.URL);page.wait_for_function('window.PS_REDRAWN_READY&&window.G?.NarutoShikamaru&&document.getElementById("boot").classList.contains("hidden")')
        if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
        page.locator('[data-quick-naruto="30017"]').click();report['permanent']=page.evaluate('G.DB.upgradesOf(G.DB.save.partner)');assert not any(report['permanent'].values());page.evaluate(NATURAL_OBSERVE);page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30017&&G.Game.state==="playing"');report['initial']=page.evaluate('ChainQA.snapshot()');assert report['initial']['level']==1
        held=None;serial=None;started=time.monotonic();last_progress=-30
        while time.monotonic()-started<600:
            data=page.evaluate('({state:G.Game.state,snapshot:ChainQA.snapshot(),offer:ChainQA.current,chains:ChainQA.chains,hits:ChainQA.hits})');a=data['snapshot'];t=a['time']
            complete=next((c for c in data['chains'] if len({h['index'] for h in data['hits'] if h['serial']==c['serial']})>=3),None)
            if complete:report['completeChain']=complete;break
            if a['dead'] or data['state']=='over' or t>=300:break
            if t-last_progress>=30:print('chain natural',round(t),'Lv',a['level'],'budget',a['profile']['chainTargets'],flush=True);last_progress=t;(out/'progress.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
            if data['state']=='levelup' and data['offer'] and data['offer']['serial']!=serial:
                if held:page.keyboard.up(held);held=None
                offer=data['offer'];priority=lambda c:0 if c['key']=='up:naruto-shikamaru' else 1 if c['key']=='stat:quantity' else 2 if c['type']=='new' else 3 if c['type']=='up' else 9
                chosen=min(range(len(offer['options'])),key=lambda i:(priority(offer['options'][i]),i));page.screenshot(path=str(out/f'card-{offer["serial"]}.png'));page.locator('#cards .card').nth(chosen).click();serial=offer['serial']
            elif page.locator('#scr-item').is_visible():page.locator('#item-cards .card').first.click()
            elif page.locator('#scr-bond').is_visible():page.locator('#bond-cards .card').first.click()
            elif data['state']=='playing':
                key=['KeyD','KeyS','KeyA','KeyW'][int(t//2)%4]
                if key!=held:
                    if held:page.keyboard.up(held)
                    page.keyboard.down(key);held=key;page.evaluate('x=>ChainQA.inputs.push(x)',{'time':t,'key':key})
            elif data['state']=='paused':page.locator('#btn-resume').click()
            page.wait_for_timeout(50)
        if held:page.keyboard.up(held)
        report.update(page.evaluate('({hits:ChainQA.hits,ledger:ChainQA.ledger,offers:ChainQA.offers,inputs:ChainQA.inputs,samples:ChainQA.samples,chains:ChainQA.chains,final:ChainQA.snapshot(),state:G.Game.state})'));report['frames']=[]
        for frame in page.evaluate('ChainQA.frames'):
            png=frame.pop('png');name=frame['key']+'.png';(out/name).write_bytes(base64.b64decode(png.split(',',1)[1]));report['frames'].append({'image':name,**frame})
        page.screenshot(path=str(out/'final.png'));video=page.video;context.close();video.save_as(str(out/'single-root-chain-native.webm'));video.delete();browser.close()
    report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'complete':bool(report.get('completeChain')),'time':report['final']['time'],'level':report['final']['level'],'cards':len(report['ledger']),'sourceStable':report['sourceStable']}))



def native_demo():
    out=OUT/'native-spaced';out.mkdir(parents=True,exist_ok=True);report={'controlled':True,'fixture':'Normal entry/native RAF; rank3 Q0 via two true basic upgrade cards, three static million-HP native enemies; no manual sim, clock or player HP changes.','sourceBefore':manifest(),'errors':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True);context=browser.new_context(viewport={'width':1100,'height':850},service_workers='block',record_video_dir=str(out/'raw'),record_video_size={'width':1100,'height':850});page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));base.boot(page);page.evaluate(SETUP)
        page.evaluate(r"""()=>{const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;window.DemoLedger=A.chainBuild(3,0);window.DemoFrames=[];window.DemoHits=[];window.DemoCast=null;const es=[[180,0],[160,180],[-20,220]].map(([x,y])=>A.spawn(x,y));A.chainWatch(es);es.forEach((e,index)=>{const hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);if(hp>this.hp)DemoHits.push({index,time:G.Game.st.time,wall:performance.now()/1000,loss:hp-this.hp});return result}});p.target=es[0];const draw=G.Combat.drawGroundFields,seen=new Set();G.Combat.drawGroundFields=function(ctx){const r=draw.call(this,ctx);DemoCast??=S.casts.find(b=>b.owner===p&&b.chain);const b=DemoCast;if(b){const contacts=b.chain.segments.filter(s=>s.contact).length,key=['single-root','first-A','A-B','A-B-C'][contacts];if(key&&!seen.has(key)){seen.add(key);const frame={key,time:G.Game.st.time,wall:performance.now()/1000,serial:b.serial,contacts,ended:b.chain.ended,visual:S.shadowVisualFor(p),segments:b.chain.segments.map(s=>({origin:s.origin,path:s.path,grownPoints:s.grownPoints,polygon:s.polygon,contact:s.contact,contactPoint:s.contactPoint}))};queueMicrotask(()=>DemoFrames.push({...frame,png:ctx.canvas.toDataURL()}))}}return r};Acceptance.resume()}""")
        started=time.monotonic()
        while time.monotonic()-started<5:
            complete=page.evaluate('DemoFrames.some(f=>f.contacts===3)');
            if complete:break
            page.wait_for_timeout(25)
        page.wait_for_timeout(200);report.update(page.evaluate('({ledger:DemoLedger,hits:DemoHits,final:DemoCast?{serial:DemoCast.serial,ended:DemoCast.chain.ended,visited:DemoCast.chain.visited.size}:null})'));report['frames']=[]
        for frame in page.evaluate('DemoFrames'):
            png=frame.pop('png');name=frame['key']+'.png';(out/name).write_bytes(base64.b64decode(png.split(',',1)[1]));report['frames'].append({'image':name,**frame})
        video=page.video;context.close();video.save_as(str(out/'same-cast-ABC-native.webm'));video.delete();browser.close()
    report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'frames':[(f['key'],f['serial'],f['time']) for f in report['frames']],'sourceStable':report['sourceStable'],'errors':report['errors']}))


def main():
    OUT.mkdir(parents=True,exist_ok=True);report={'sourceBefore':manifest(),'controlled':True,'checks':{},'errors':[]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=base.CHROME,headless=True);page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block');page.on('pageerror',lambda e:report['errors'].append(str(e)));base.boot(page);page.evaluate(SETUP)
            for name,check in [('growth',GROWTH),('stopping',STOPPING),('lethal',LETHAL),('pathAndPool',PATH_AND_POOL),('props',PROPS),('highBudget',HIGH_BUDGET)]:report['checks'][name]=page.evaluate(check);print(name,'PASS',flush=True)
            report['validLegacyControl']=page.evaluate(base.CONTROL);print('legacy control PASS',flush=True)
            browser.close()
        report['ok']=True
    except Exception as error:report['failure']=str(error);raise
    finally:
        report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':
    if '--natural' in sys.argv:natural()
    elif '--native' in sys.argv:native_demo()
    else:main()
