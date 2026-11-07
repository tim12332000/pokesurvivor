"""Controlled Madara/SelfClone performance benchmark; frozen JS routes isolate versions.

Run MADARA_PERF_LABEL=baseline or candidate. Baseline defaults to frozen QA copy.
Uses existing Playwright/Chrome and production combat/rendering, no new dependencies.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_jujutsu as base
import test_madara_legion as legion

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art-review/madara-performance-20261108/qa'
LABEL=os.environ.get('MADARA_PERF_LABEL','baseline')
SOURCE=Path(os.environ.get('MADARA_PERF_SOURCE',OUT/'baseline/runtime.js' if LABEL=='baseline' else ROOT/'.omx/naruto-madara.js'))
URL=os.environ.get('MADARA_PERF_URL','http://127.0.0.1:8347/.omx/digimon.html?lang=zh-TW&layout=wide')

SCENE=r'''opts => {
 const A=JAcceptance,p=A.p(),M=G.NarutoMadara;A.reset();A.fixture('naruto-madara',5);
 for(const id of ['naruto-madara-clones','naruto-madara-fire','naruto-madara-susanoo','naruto-madara-meteor']){A.assert(p.addMove(id),'learn '+id);Object.assign(p.moves.find(m=>m.id===id),G.Moves.instance(id,5))}
 p.quantityPicks=p.quantityBonus=3;p.critChance=0;p.cdMul=1;p.xpNext=1e12;for(const m of p.moves)m.t=0;
 let seed=617234;Math.random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
 G.Spawner.update=()=>{};
 for(let i=0;i<opts.enemies;i++){const angle=i*2.399963229728653,r=65+(i%10)*34,e=A.spawn(Math.cos(angle)*r,Math.sin(angle)*r);e.hp=e.maxHp=1e10;e.spd=0;e.dmg=0;}
 for(let i=0;i<opts.clones;i++)A.assert(G.SelfClones.summon(p),'summon actual selfclone');
 const counts={},originals=[];
 for(const [obj,key]of [[G.EnemyMgr,'all'],[G.EnemyMgr,'queryCircle'],[G.EnemyMgr,'get'],[G.World,'projectilePathClear'],[G.MadaraArt,'avatarSocketFor'],[G.MadaraArt,'socketFor']])if(typeof obj?.[key]==='function'){const fn=obj[key];originals.push([obj,key,fn]);obj[key]=function(...args){counts[key]=(counts[key]||0)+1;return fn.apply(this,args)}}
 const pulse=G.CombatPulse.onPulse,events=[];G.CombatPulse.onPulse=i=>{if(i.primaryHits)events.push({owner:i.owner===p?'main':i.owner?.cloneId||'other',channel:i.channel,hits:i.primaryHits,damage:i.primaryDamage});pulse?.(i)};
 const step=dt=>{G.Combat.tick(dt,p,0);p.anim.update(dt);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,0);G.Combat.updateFields(dt)};
 A.resume();for(let i=0;i<60;i++)step(1/30);
 const owners=()=>[p,...G.SelfClones.actors()];
 const state=()=>owners().map(a=>{const s=M.stateFor(a);return {owner:a===p?'main':a.cloneId,army:s?.army.length||0,casts:s?.casts||{},hits:s?.hits||0,clock:s?.clock||0}});
 window.MadaraPerf={opts,counts,events,step,state,owners,originals,pulse,frameTimes:[],lastFrame:0};
 A.pause();return {actors:state(),enemies:G.EnemyMgr.all().length,quality:G.Settings.get('quality')};
}'''

MEASURE=r'''samples => {
 const A=JAcceptance,R=MadaraPerf,times=[],before={...R.counts},startEvents=R.events.length;
 A.resume();try{for(let i=0;i<samples;i++){const t=performance.now();R.step(1/30);times.push(performance.now()-t)}}finally{A.pause()}
 const sorted=[...times].sort((a,b)=>a-b),quantile=q=>sorted[Math.min(sorted.length-1,Math.floor(sorted.length*q))];
 const counts=Object.fromEntries(Object.entries(R.counts).map(([k,v])=>[k,v-(before[k]||0)]));
 return {samples,timestepSeconds:1/30,medianMs:quantile(.5),p95Ms:quantile(.95),maxMs:sorted.at(-1),totalMs:times.reduce((a,b)=>a+b,0),counts,countsPerStep:Object.fromEntries(Object.entries(counts).map(([k,v])=>[k,v/samples])),owners:R.state(),events:R.events.slice(startEvents)};
}'''

NATIVE_START=r'''() => {
 const R=MadaraPerf;R.frameTimes=[];R.running=true;R.lastFrame=0;
 function sample(t){if(!R.running)return;if(R.lastFrame)R.frameTimes.push(t-R.lastFrame);R.lastFrame=t;requestAnimationFrame(sample)}requestAnimationFrame(sample);JAcceptance.resume();
}'''
NATIVE_END=r'''() => {
 const R=MadaraPerf;R.running=false;JAcceptance.pause();const sorted=[...R.frameTimes].sort((a,b)=>a-b),q=v=>sorted[Math.min(sorted.length-1,Math.floor(sorted.length*v))]||0;
 return {samples:sorted.length,medianFrameMs:q(.5),p95FrameMs:q(.95),maxFrameMs:sorted.at(-1)||0,over33ms:sorted.filter(x=>x>33.4).length,owners:R.state()};
}'''

REGRESSION=r'''() => {
 const A=JAcceptance,p=A.p(),M=G.NarutoMadara,assert=A.assert,R=MadaraPerf,out={};
 let s=M.stateFor(p);assert(s.army.length===16,'main army reduced');assert(G.SelfClones.actors().every(a=>M.stateFor(a)?.army.length===16),'selfclone army reduced');
 const active=R.events.reduce((o,e)=>(o[e.owner]=1,o),{});assert(Object.keys(active).length===1+R.opts.clones,'some owner lost real damage');out.realDamageOwners=Object.keys(active);
 const channels=[...new Set(R.events.map(e=>e.channel))];assert(channels.includes('army-guardian')&&channels.includes('army-body')&&channels.includes('army-fire'),'real attack channel dropped');out.channels=channels;
 const stale=G.EnemyMgr.all()[0];G.EnemyMgr.removeRemote(stale.id,false);const hurt=stale.hurt;let staleHits=0;stale.hurt=function(...args){staleHits++;return hurt.apply(this,args)};
 A.resume();try{for(let i=0;i<30;i++)R.step(1/30)}finally{A.pause()}assert(staleHits===0,'removed registered enemy still damaged');out.removalRetarget=true;
 const actors=G.SelfClones.actors();if(actors.length){const a=actors[0];a.dead=true;A.resume();try{M.update(.01)}finally{A.pause()}assert(!M.stateFor(a),'dead selfclone kept army');out.selfCloneDeath=true;}
 const world=G.World;G.World={...world};A.resume();try{M.update(.01)}finally{G.World=world;A.pause()}assert(!M.stateFor(p),'world swap retained army');out.worldClear=true;
 A.reset();A.fixture('naruto-madara-fire',3);let removalFire=p.moves[0],r1=A.spawn(100,0),r2=A.spawn(100,0),r1Hits=0,r2Hits=0;
 const r1hurt=r1.hurt;r1.hurt=function(...args){r1Hits++;const value=r1hurt.apply(this,args);G.EnemyMgr.removeRemote(r2.id,false);return value};const r2hurt=r2.hurt;r2.hurt=function(...args){r2Hits++;return r2hurt.apply(this,args)};
 A.resume();try{assert(M.cast(p,removalFire),'live identity cast rejected')}finally{A.pause()}A.advance(2);assert(r1Hits>0&&r2Hits===0,'hurt callback removed enemy still damaged from same-wave stale list');out.sameWaveLiveIdentity={r1Hits,r2Hits};
 A.reset();A.fixture('naruto-madara-fire',3);const fire=p.moves[0],one=A.spawn(100,0),two=A.spawn(100,0);let h1=0,h2=0;
 const old=one.hurt;one.hurt=function(...args){h1++;const r=old.apply(this,args);G.Combat.clearFields(p);return r};const old2=two.hurt;two.hurt=function(...args){h2++;return old2.apply(this,args)};
 A.resume();try{assert(M.cast(p,fire),'cancel fixture cast rejected')}finally{A.pause()}A.advance(2);assert(h1===1&&h2===0,'same-wave second target/future pulse survived cancellation');out.cancel={h1,h2};return out;
}'''


def compare():
    before=json.loads((OUT/'baseline/report.json').read_text(encoding='utf8'))
    after=json.loads((OUT/'candidate/report.json').read_text(encoding='utf8'))
    rows=[]
    for name,a in before['cases'].items():
        b=after['cases'][name]
        def totals(case):
            result={}
            for event in case['simulation']['events']:
                key=str(event['owner'])+'/'+event['channel']
                item=result.setdefault(key,{'hits':0,'damage':0})
                item['hits']+=event['hits'];item['damage']+=event['damage']
            return result
        at,bt=totals(a),totals(b)
        equal=set(at)==set(bt) and all(at[k]['hits']==bt[k]['hits'] and math.isclose(at[k]['damage'],bt[k]['damage'],rel_tol=1e-10,abs_tol=1e-6) for k in at)
        sa,sb=a['simulation'],b['simulation']
        rows.append({'case':name,'baselineMedianMs':sa['medianMs'],'candidateMedianMs':sb['medianMs'],
            'baselineP95Ms':sa['p95Ms'],'candidateP95Ms':sb['p95Ms'],'medianReductionPercent':100*(1-sb['medianMs']/sa['medianMs']),
            'baselineCountsPerStep':sa['countsPerStep'],'candidateCountsPerStep':sb['countsPerStep'],
            'damageByOwnerChannelEqual':equal,'baselineOwnerChannelTotals':at,'candidateOwnerChannelTotals':bt,
            'armyCountsEqual':[x['army'] for x in sa['owners']]==[x['army'] for x in sb['owners']],
            'baselineNative':a.get('native'),'candidateNative':b.get('native'),
            'baselineRegression':a['regression'],'candidateRegression':b['regression']})
    report={'ok':all(r['damageByOwnerChannelEqual'] and r['armyCountsEqual'] for r in rows) and before['ok'] and after['ok'],
        'baselineHash':before['sourceHash'],'candidateHash':after['sourceHash'],
        'timingOrder':'Final baseline completed before final candidate started, no overlap; exploratory-report.json files excluded from timing comparison.',
        'rows':rows,'limits':'Controlled stationary enemies, allrank5Q3, fixed1/30step. NativeRAF includes fullgame+render on headless desktop; physicalmobile performance and long-run memory not established.'}
    (OUT/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'rows':[{k:r[k] for k in ['case','baselineMedianMs','candidateMedianMs','baselineP95Ms','candidateP95Ms','damageByOwnerChannelEqual','armyCountsEqual']} for r in rows]}),flush=True)
    if not report['ok']:raise SystemExit(1)


def main():
    if os.environ.get('MADARA_PERF_COMPARE')=='1':
        compare();return
    (OUT/LABEL).mkdir(parents=True,exist_ok=True)
    source=SOURCE.read_text(encoding='utf8')
    digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    report={'label':LABEL,'source':str(SOURCE),'sourceHash':digest,'url':URL,
        'scope':'Controlled stationary enemies and all rank5/Q3 actual SelfClone armies. Fixed combat step1/30; synchronous combat pipeline timing excludes renderer, native RAF includes full game+render. Headless desktop benchmark is machine-specific, not physical phone FPS.',
        'cases':{},'errors':[]}
    legion.URL=URL
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        requested=os.environ.get('MADARA_PERF_CASES','0:60,1:60,3:60,5:60,0:120,1:120,3:120,5:120')
        for spec in requested.split(','):
            clones,enemies=map(int,spec.split(':'));name=f'clones{clones}-enemies{enemies}'
            context=browser.new_context(viewport={'width':1280,'height':900},service_workers='block')
            context.route('**/.omx/naruto-madara.js*',lambda route:route.fulfill(status=200,body=source,content_type='application/javascript'))
            page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
            frame=legion.boot(page);frame.locator('#scr-menu [data-go="play"]').click();frame.wait_for_function('G.Game.state==="playing"');frame.evaluate(base.SETUP)
            config=frame.evaluate(SCENE,{'clones':clones,'enemies':enemies})
            measured=frame.evaluate(MEASURE,int(os.environ.get('MADARA_PERF_SAMPLES','120')))
            case={'config':config,'simulation':measured}
            if clones in (0,5) and enemies==120:
                frame.evaluate(NATIVE_START);page.wait_for_timeout(6000);case['native']=frame.evaluate(NATIVE_END)
                page.screenshot(path=str(OUT/LABEL/f'{name}-native.png'))
            case['regression']=frame.evaluate(REGRESSION)
            report['cases'][name]=case
            context.close()
            (OUT/LABEL/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            print(name,'median',round(measured['medianMs'],2),'p95',round(measured['p95Ms'],2),'all',measured['countsPerStep'].get('all'),'path',round(measured['countsPerStep'].get('projectilePathClear',0)),flush=True)
        browser.close()
    report['ok']=not report['errors']
    (OUT/LABEL/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':main()
