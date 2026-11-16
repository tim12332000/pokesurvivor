"""Bound enemies stay put when the owner walks; old imitation-delta is retired."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_shikamaru as base
import test_shikamaru_chain as chain

OUT = base.ROOT / 'art-review/shikamaru/qa/stationary-bind'
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 A.waitForStationaryBind=e=>{for(let i=0;i<200&&!S.held(e);i++)A.step(.01);A.assert(S.held(e),'controlled tip did not capture within 2s')};
 for(const clone of [false,true])for(const boss of [false,true]){
   A.chainBuild(2,0);
   const actor=clone?G.SelfClones.summon(p):p;
   actor.x=actor.y=0;
   const es=[A.spawn(100,0,boss),A.spawn(180,70,boss)];
   actor.target=es[0];
   A.resume();try{A.assert(S.cast(actor,actor.moves.find(m=>m.id==='naruto-shikamaru')),'cast rejected')}finally{A.pause()}
   // Actual tip travel may ease into contact; gate on capture, not old speed.
   for(let i=0;i<200&&!es.every(e=>S.held(e));i++)A.step(.01);
   A.assert(es.every(e=>S.held(e)),'fixture did not complete A-B capture within 2s');
   const before=es.map(e=>({x:e.x,y:e.y})),poolBefore=S.shadowVisualFor(actor),clock=S.stateFor(actor).clock;
   for(let i=0;i<20;i++){
     actor.x+=3;actor.y+=1;
     A.resume();try{
       G.Combat.tick(.01,actor,0);
       for(const e of es)e.update(.01,p);
       S.update(.01);
     }finally{A.pause()}
     es.forEach((e,j)=>{
       A.assert(S.held(e),'movement unexpectedly released a clear connected shadow');
       A.assert(Math.hypot(e.x-before[j].x,e.y-before[j].y)<1e-7,'owner movement dragged a bound enemy '+clone+'/'+boss);
       // A real Hurt one-shot may finish; its background must remain idle.
       if(!boss)A.assert(e.anim.base==='Idle'&&e.anim.cur!=='Walk','stationary captive played walking animation');
     });
   }
   const visual=S.shadowVisualFor(actor),s=S.stateFor(actor),after=es.map(e=>({x:e.x,y:e.y}));
   A.assert(actor.x===60&&actor.y===20,'fixture failed to move actual owner');
   A.assert(s.dragged===0,'movement recorded enemy drag');
   A.assert(visual.x===actor.x&&visual.y===actor.y,'foot shadow did not follow owner');
   A.assert(s.clock>clock&&visual.extensionTotal!==poolBefore.extensionTotal,'shadow connection failed to respond to owner movement');
   S.clear(actor);A.assert(es.every(e=>!S.held(e)),'clear did not release stationary captives');
   out.push({clone,boss,owner:{x:actor.x,y:actor.y},before,after,dragged:s.dragged,poolBefore,visual});
 }
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    names=['.omx/naruto-shikamaru.js','.omx/naruto-skills.js','.omx/naruto.js']
    hashes=lambda:{s:hashlib.sha256((base.ROOT/s).read_bytes()).hexdigest() for s in names}
    baseline='--baseline' in sys.argv
    report={'controlled':True,'baseline':baseline,'sourceBefore':hashes(),'errors':[]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
            page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block')
            if baseline:
                old=subprocess.check_output(['git','show','11149aee:.omx/naruto-shikamaru.js'],cwd=base.ROOT)
                page.route('**/.omx/naruto-shikamaru.js*',lambda route:route.fulfill(body=old,content_type='application/javascript'))
                report['baselineRuntimeSha256']=hashlib.sha256(old).hexdigest()
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            base.boot(page);page.evaluate(chain.SETUP)
            report['stationary']=page.evaluate(CHECK)
            report['chainGrowth']=page.evaluate(chain.GROWTH)
            report['chainStopping']=page.evaluate(chain.STOPPING)
            # Retain the contact/DOT/in-flight assertions; old .4s travel is not
            # a binding rule now that the physical tip accelerates into contact.
            control=base.CONTROL.replace('A.cast(m);A.finish(.4);A.assert(S.held(e)',
                'A.cast(m);A.waitForStationaryBind(e);A.assert(S.held(e)')
            control=control.replace('A.cast(m);A.finish(.4);A.assert(S.held(enemy)',
                'A.cast(m);A.waitForStationaryBind(enemy);A.assert(S.held(enemy)')
            assert control.count('A.waitForStationaryBind(')==2
            report['controlTiming']='Bounded real-contact gate replaces two old fixed .4s waits; all original control assertions retained.'
            report['control']=page.evaluate(control)
            page.screenshot(path=str(OUT/'entry.png'));browser.close()
        assert not report['errors'],report['errors']
        report['ok']=True
    except Exception as error:
        report['failure']=str(error)
        if not baseline or 'owner movement dragged a bound enemy' not in str(error):
            raise
        report['expectedRegressionFailure']=True
    finally:
        report['sourceAfter']=hashes();report['sourceStable']=report['sourceBefore']==report['sourceAfter']
        (OUT/('baseline-report.json' if baseline else 'report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'ok':report.get('ok'), 'expectedRegressionFailure':report.get('expectedRegressionFailure',False),'stationaryCases':len(report.get('stationary',[])),'sourceStable':report['sourceStable']}))


if __name__=='__main__':
    main()
