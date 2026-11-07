"""Frozen before/after Madara fire visuals, native recordings and combat invariance.

Controlled scene screenshots are native RAF, never synthetic recordings. The
independent fixed-step geometry checks are labelled separately from natural play.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_jujutsu as base
import test_madara_legion as legion
import test_madara_performance as perf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art-review/madara-fire-20261108/qa'
LABEL=os.environ.get('MADARA_FIRE_LABEL','baseline')
FOLDER=OUT/LABEL
URL=os.environ.get('MADARA_FIRE_URL','http://127.0.0.1:8347/.omx/digimon.html?lang=zh-TW')
ART=FOLDER/'art-runtime.js'
COMBAT=FOLDER/'combat-runtime.js'

def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

SET=r'''opts=>{
 const A=JAcceptance,p=A.p(),M=G.NarutoMadara;A.reset();const m=A.fixture('naruto-madara-fire',opts.rank);p.quantityPicks=opts.quantity;p.critChance=0;
 const spec=M.profile(p,m),c=Math.cos(opts.aim),sn=Math.sin(opts.aim),positions=[[140,0],[170,spec.width*.35],[170,-spec.width*.35],[170,spec.width*.7]],targets=positions.map(([f,l])=>A.spawn(c*f-sn*l,sn*f+c*l));
 const hits=targets.map(A.watch);window.FireCase={hits,targets,spec,startClock:0};m.t=0;G.Spawner.update=()=>{};A.resume();A.assert(M.cast(p,m),'native fire rejected');FireCase.startClock=M.stateFor(p).clock;
 return {rank:opts.rank,quantity:opts.quantity,aim:opts.aim,width:spec.width,fronts:spec.fronts};
}'''
STATE=r'''()=>{const s=G.NarutoMadara.stateFor(G.Game.player),F=FireCase;return {wallSeconds:performance.now()/1000,clock:(s?.clock||0)-F.startClock,body:s?.body?.phase,fronts:s?.fires.map(f=>({index:f.index,age:f.age,x:f.x,y:f.y,distance:f.distance,width:f.currentWidth??f.spec.width,aim:f.aim}))||[],flames:s?.flames.length||0,hits:F.hits.map(h=>h.length)}}'''

GEOMETRY=r'''()=>{
 const A=JAcceptance,p=A.p(),M=G.NarutoMadara,out=[];
 for(const rank of [1,5])for(const aim of [0,Math.PI/2,Math.PI,-Math.PI/2]){
  A.reset();const m=A.fixture('naruto-madara-fire',rank);p.quantityPicks=rank===5?3:0;const spec=M.profile(p,m),c=Math.cos(aim),sn=Math.sin(aim),targets=[[140,0],[170,spec.width*.35],[170,-spec.width*.35],[170,spec.width*.7]].map(([f,l])=>A.spawn(c*f-sn*l,sn*f+c*l)),hits=targets.map(A.watch);
  let seed=1823;Math.random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};A.resume();try{A.assert(M.cast(p,m),'geometry cast')}finally{A.pause()}A.advance(.65);
  const s=M.stateFor(p);A.assert(s.fires.length>0,'read-only test has no live fire');
  const before=JSON.stringify({body:s.body,fires:s.fires.map(f=>({age:f.age,x:f.x,y:f.y,distance:f.distance,width:f.width})),clock:s.clock,hits:s.hits}),random=Math.random;let randomCalls=0;Math.random=()=>{randomCalls++;return random()};
  const canvas=document.createElement('canvas');canvas.width=1200;canvas.height=900;const ctx=canvas.getContext('2d');
  for(let i=0;i<10;i++){M.draw(ctx);M.draw(ctx,true);G.MadaraArt.drawElement(ctx,{kind:'fire',phase:'wall',x:300,y:300,width:spec.width,depth:72,aim,age:.3,progress:.4});}
  Math.random=random;A.assert(randomCalls===0,'drawing consumed combat RNG');A.assert(before===JSON.stringify({body:s.body,fires:s.fires.map(f=>({age:f.age,x:f.x,y:f.y,distance:f.distance,width:f.width})),clock:s.clock,hits:s.hits}),'draw mutated simulation');
  A.advance(2.25);A.assert(hits.slice(0,3).every(h=>h.length>0)&&hits[3].length===0,'true fire width differs');
  out.push({rank,aim,width:spec.width,fronts:spec.fronts,hits:hits.map(h=>h.length),damage:hits.map(h=>h.reduce((n,e)=>n+e.loss,0)),contacts:s.hitContacts.filter(c=>c.kind==='fire').map(c=>({channel:c.channel,segment:c.segment,geometry:c.geometry,hits:c.primaryHits,damage:c.primaryDamage})),randomCalls});
 }
 A.reset();const m=A.fixture('naruto-madara-fire',5);A.spawn(150,0);A.resume();try{M.cast(p,m)}finally{A.pause()}A.advance(.5);const s=M.stateFor(p),clock=s.clock;M.update(1);A.assert(s.clock===clock,'paused fire progressed');p.dead=true;A.resume();try{M.update(.01)}finally{A.pause()}A.assert(!M.stateFor(p)&&M.drawables().length===0,'dead fire ghost state');p.dead=false;p.hp=p.maxHp;return {cases:out,lifecycle:{pause:true,deathNoGhost:true}};
}'''

FIRE_PERF=r'''()=>{
 const A=JAcceptance,p=A.p(),M=G.NarutoMadara;A.resume();let frames=0;
 while(frames++<240){MadaraPerf.step(1/30);if([p,...G.SelfClones.actors()].reduce((n,a)=>n+(M.stateFor(a)?.fires.length||0),0)>=120)break}A.pause();
 const actors=[p,...G.SelfClones.actors()],canvas=document.createElement('canvas');canvas.width=1280;canvas.height=900;const ctx=canvas.getContext('2d'),times=[];
 const totalFronts=actors.reduce((n,a)=>n+(M.stateFor(a)?.fires.length||0),0);
 for(let i=0;i<120;i++){ctx.clearRect(0,0,1280,900);const t=performance.now();G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);times.push(performance.now()-t)}
 const firstColdMs=times[0],sorted=times.sort((a,b)=>a-b),dynamic=[],frontCounts=[];
 A.resume();try{for(let i=0;i<90;i++){MadaraPerf.step(1/60);frontCounts.push(actors.reduce((n,a)=>n+(M.stateFor(a)?.fires.length||0),0));ctx.clearRect(0,0,1280,900);const t=performance.now();G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);dynamic.push(performance.now()-t)}}finally{A.pause()}
 dynamic.sort((a,b)=>a-b);return {scope:'controlled full ground+air field render, first cold frame then120fixedsnapshot renders and90actualadvancingframes; headless canvas, no physical FPS claim',totalFronts,owners:actors.length,armyPerOwner:actors.map(a=>M.stateFor(a)?.army.length||0),firstColdMs,medianMs:sorted[60],p95Ms:sorted[114],maxMs:sorted.at(-1),dynamicMedianMs:dynamic[45],dynamicP95Ms:dynamic[85],dynamicMaxMs:dynamic.at(-1),dynamicFrontCountRange:[Math.min(...frontCounts),Math.max(...frontCounts)],quality:G.Settings.get('quality'),fx:G.Settings.fx,viewport:innerWidth};
}'''

def context_for(browser,width,height,video=None):
    args=dict(viewport={'width':width,'height':height},is_mobile=width<500,has_touch=width<500,service_workers='block')
    if video:args.update(record_video_dir=str(video),record_video_size={'width':width,'height':height})
    context=browser.new_context(**args)
    context.route('**/art-review/madara/runtime.js*',lambda route:route.fulfill(status=200,body=ART.read_text(encoding='utf8'),content_type='application/javascript'))
    context.route('**/.omx/naruto-madara.js*',lambda route:route.fulfill(status=200,body=COMBAT.read_text(encoding='utf8'),content_type='application/javascript'))
    return context

class NaturalBrowser:
    def __init__(self,browser):self.browser=browser
    def new_context(self,**kwargs):
        context=self.browser.new_context(**kwargs)
        context.route('**/art-review/madara/runtime.js*',lambda route:route.fulfill(status=200,body=ART.read_text(encoding='utf8'),content_type='application/javascript'))
        context.route('**/.omx/naruto-madara.js*',lambda route:route.fulfill(status=200,body=COMBAT.read_text(encoding='utf8'),content_type='application/javascript'))
        return context

def boot(page):
    legion.URL=URL+('&layout=wide' if (page.viewport_size or {}).get('width',0)>700 else '')
    frame=legion.boot(page);frame.locator('#scr-menu [data-go="play"]').click();frame.wait_for_function('G.Game.state==="playing"');frame.evaluate(base.SETUP);return frame

def stress_native(browser,report):
    for label,width,height in [('stress-desktop',1280,900),('stress-mobile360',360,800)]:
        folder=FOLDER/label;folder.mkdir(parents=True,exist_ok=True)
        context=context_for(browser,width,height,folder/'video');page=context.new_page();frame=boot(page)
        frame.evaluate("G.Settings.set('quality','high')")
        frame.evaluate(perf.SCENE,{'clones':5,'enemies':120})
        config=frame.evaluate(r'''()=>{const A=JAcceptance,M=G.NarutoMadara;A.resume();let count=0;for(let i=0;i<240;i++){MadaraPerf.step(1/30);count=[G.Game.player,...G.SelfClones.actors()].reduce((n,a)=>n+(M.stateFor(a)?.fires.length||0),0);if(count>=120)break}A.pause();return {owners:MadaraPerf.state(),fronts:count,fx:G.Settings.fx,viewport:innerWidth}}''')
        page.wait_for_timeout(100);page.screenshot(path=str(folder/'live-130-fronts.png'))
        frame.evaluate('JAcceptance.resume()');samples=[];started=time.monotonic()
        while time.monotonic()-started<2.5:
            data=frame.evaluate("() => ({clock:G.NarutoMadara.stateFor(G.Game.player).clock,fronts:[G.Game.player,...G.SelfClones.actors()].reduce((n,a)=>n+(G.NarutoMadara.stateFor(a)?.fires.length||0),0)})")
            name=f'live-{data["clock"]:.2f}.png';page.screenshot(path=str(folder/name));samples.append({'path':name,**data});page.wait_for_timeout(120)
        frame.evaluate('JAcceptance.pause()');video=page.video;context.close();video.save_as(str(folder/'native-fire-stress.webm'));video.delete()
        save(folder/'scene.json',{'scope':'controlled actual native game renderer, real5SelfClones+eacharmy16,120targets; not natural growth','sources':report['sources'],'config':config,'samples':samples})
        print(label,config['fronts'],'fronts',flush=True)

def compare(label):
    a=json.loads((OUT/'baseline/report.json').read_text(encoding='utf8'))
    b=json.loads((OUT/label/'report.json').read_text(encoding='utf8'))
    def near(x,y):
        if isinstance(x,(int,float)) and isinstance(y,(int,float)):return math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-7)
        if isinstance(x,dict) and isinstance(y,dict):return x.keys()==y.keys() and all(near(x[k],y[k]) for k in x)
        if isinstance(x,list) and isinstance(y,list):return len(x)==len(y) and all(near(v,w) for v,w in zip(x,y))
        return x==y
    rows=[]
    for x,y in zip(a['geometry']['cases'],b['geometry']['cases']):
        rows.append({'rank':x['rank'],'aim':x['aim'],'fronts':y['fronts'],'width':y['width'],
            'hitCountsEqual':x['hits']==y['hits'],'damageEqual':x['damage']==y['damage'],
            'contactGeometryEqual':near(x['contacts'],y['contacts']),'drawRngCalls':y['randomCalls']})
    result={'technicalOk':all(r['hitCountsEqual'] and r['damageEqual'] and r['contactGeometryEqual'] and r['drawRngCalls']==0 for r in rows) and not b['errors'] and not b['missing'],
        'candidate':label,'baselineSources':a['sources'],'candidateSources':b['sources'],'geometryRows':rows,
        'baselineRender':a['renderPerformance'],'candidateRender':b['renderPerformance'],
        'visualApproval':'Independent art/root review required; technical checks do not override visual blockers.'}
    save(OUT/label/'comparison.json',result);print(json.dumps(result),flush=True)

def main():
    if os.environ.get('MADARA_FIRE_COMPARE_LABEL'):
        compare(os.environ['MADARA_FIRE_COMPARE_LABEL']);return
    FOLDER.mkdir(parents=True,exist_ok=True)
    quick=os.environ.get('MADARA_FIRE_QUICK')=='1'
    report={'label':LABEL,'mode':'quick-native-visual-only' if quick else 'full-bounded-fire-acceptance','sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ART,COMBAT]},'cases':{},'errors':[],'missing':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        if os.environ.get('MADARA_FIRE_STRESS')=='1':
            stress_native(browser,report);browser.close();return
        if not quick:
            context=context_for(browser,1280,900);page=context.new_page();frame=boot(page)
            report['geometry']=frame.evaluate(GEOMETRY)
            context.close();context=context_for(browser,1280,900);page=context.new_page();frame=boot(page)
            frame.evaluate("G.Settings.set('quality','high')")
            combined='opts=>{const config=('+perf.SCENE+')(opts);return ('+FIRE_PERF+')()}'
            report['renderPerformance']=frame.evaluate(combined,{'clones':5,'enemies':120});context.close()
            print(LABEL,'geometry passed',report['renderPerformance'],flush=True)
            if os.environ.get('MADARA_FIRE_CHECKS_ONLY')=='1':
                report['ok']=not report['errors'] and not report['missing'];save(FOLDER/'report.json',report);browser.close();return
        surfaces=[('desktop',1280,900)] if quick else [('desktop',1280,900),('desktop-low',1280,900),('mobile390',390,844),('mobile360',360,800)]
        for label,width,height in surfaces:
            folder=FOLDER/label;folder.mkdir(parents=True,exist_ok=True)
            context=context_for(browser,width,height,folder/'video');page=context.new_page()
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.on('response',lambda r:report['missing'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            frame=boot(page);frame.evaluate("value=>G.Settings.set('quality',value)",'high' if label=='desktop' else 'low');page.screenshot(path=str(folder/'normal-entry.png'))
            result=[]
            directions=[('right',0),('up',-1.5707963267948966),('left',3.141592653589793),('down',1.5707963267948966)] if label=='desktop' else [('right',0),('up',-1.5707963267948966)]
            if quick:directions=[('right',0),('down',1.5707963267948966)]
            for rank,q in ([(1,0)] if quick else [(1,0),(5,3)]):
                for direction,aim in directions:
                    scene=f'r{rank}-q{q}-{direction}'
                    config=frame.evaluate(SET,{'rank':rank,'quantity':q,'aim':aim})
                    if rank==5:page.keyboard.down('KeyS')
                    samples=[];last=-1;started=time.monotonic()
                    while time.monotonic()-started<5:
                        state=frame.evaluate(STATE)
                        if state['clock']>=last+.25:
                            name=f'{scene}-{state["clock"]:.2f}.png';page.screenshot(path=str(folder/name));samples.append({'path':name,**state});last=state['clock']
                        if state['clock']>=2.4:break
                        page.wait_for_timeout(35)
                    if rank==5:page.keyboard.up('KeyS')
                    frame.evaluate('JAcceptance.pause()');result.append({'scene':scene,'config':config,'samples':samples,'nativeRealInput':rank==5})
            report['cases'][label]=result
            video=page.video;context.close();video.save_as(str(folder/'native-fire.webm'));video.delete();save(folder/'scenes.json',result)
            save(FOLDER/'report.json',report)
            print(LABEL,label,'done',flush=True)
        if not quick:
            legion.OUT=FOLDER/'natural';legion.URL=URL+'&layout=wide'
            legion.hashes=lambda:report['sources']
            report['naturalFireLearning']=legion.natural(NaturalBrowser(browser),'desktop',1280,900,34)
        browser.close()
    report['ok']=not report['errors'] and not report['missing']
    save(FOLDER/'report.json',report)
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':main()
