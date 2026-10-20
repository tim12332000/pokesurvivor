"""Reverse Lotus completes every planned hit and landing within 3.3 simulated seconds."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.omx/state/lee-reverse-deadline'
URL='http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=lee-reverse-deadline'

HELPERS=r"""() => {
 const A=Acceptance,p=A.p();p.level=12;
 for(const id of ['naruto-lotus','naruto-reverse-lotus','naruto-gates']){const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'learn '+id)}
 A.deadlineCast=p.cast;
 A.deadlineFixture=(level,quantity,mode,id='naruto-reverse-lotus')=>{
   A.leeArena();G.Weather.reset();p.statsTaken.quantity=0;
   const m=A.select(id);while(m.lvl<level){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(card&&card.apply(p)!==false,'skill level card')}
   for(let n=0;n<quantity;n++){let card;for(let k=0;k<150&&!card;k++)card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');A.assert(card,'quantity card missing');card.apply(p)}
   const e=A.spawn(mode==='far'?m.range:mode==='chase'?140:35,0),side=[0,2*Math.PI/3,4*Math.PI/3].map(a=>A.spawn(e.x+Math.cos(a)*m.radius*.7,Math.sin(a)*m.radius*.7)),outside=A.spawn(e.x,e.y+m.radius+40),ledger=[],counts=new Map(),casts=[];
   for(const enemy of [e,...side,outside]){enemy.hp=enemy.maxHp=10000000;counts.set(enemy,0);const hurt=enemy.hurt;
     enemy.hurt=function(...args){counts.set(this,counts.get(this)+1);ledger.push({primary:this===e,outside:this===outside,amount:args[0],age:G.NarutoLee.active?.age,phase:G.NarutoLee.active?.phase,n:G.NarutoLee.active?.ticks,lift:G.NarutoLee.active?.visualLift});return hurt.apply(this,args)};
   }
   p.cast=function(m,...args){casts.push(m.id);return A.deadlineCast.call(this,m,...args)};p.target=e;p.aim=0;A.actualCast(id);
   const f=G.NarutoLee.active;
   // Explicit boundary-state fixture, not a claim that travel permits a .58s chase.
   if(mode==='approach-age-boundary')f.age=.58;
   return {m,e,side,outside,ledger,counts,casts,f};
 };
}"""

MATRIX=r"""() => {
 const A=Acceptance,p=A.p(),L=G.NarutoLee,out=[],patterns={'30fps':[1/30],'60fps':[1/60],'144fps':[1/144],irregular:[.019,.041,.007,.063,.011],bigDelta:[4]};
 for(const [level,quantity,air] of [[1,0,5],[5,2,15],[5,20,33]])for(const mode of ['near','far','chase','approach-age-boundary'])for(const [pattern,deltas] of Object.entries(patterns)){
   const r=A.deadlineFixture(level,quantity,mode),f=r.f,original={duration:f.durations.combo,deadlines:[...f.comboDeadlines],damage:f.move.dmg,hits:f.comboHits,quantity:f.move.quantityBonusAtCast},events=[];
   A.assert(Math.abs(original.duration-1.65/(1+.025*(air-5)))<1e-10,'previous cast approach budget leaked into a fresh cast');
   let approach=0,steps=0;A.resume();
   try{for(;steps<1600&&L.active;steps++){
     const dt=mode==='chase'&&f.phase==='approach'&&pattern==='bigDelta'?1/144:deltas[steps%deltas.length];
     if(mode==='chase'&&f.phase==='approach'){
       const dx=160*dt;r.e.x+=dx;r.side.forEach(e=>e.x+=dx);r.outside.x+=dx;G.EnemyMgr.rebuildGrid();
     }
     G.Combat.tick(dt,p,0);G.Combat.updateFields(dt);p.anim.update(dt);G.FX.update(dt);
     if(!approach&&f.phase==='windup')approach=f.age-f.phaseAge;
     if(L.active&&['lift','combo','descent'].includes(f.phase))A.assert(L.isInvulnerable(p),'deadline compression lost aerial immunity');
     events.push(f.phase);
   }}finally{A.pause()}
   A.assert(!L.active&&f.phase==='recovery','deadline cancelled/truncated rather than finishing');
   A.assert(f.age<=3.3+1e-8,'full cast exceeded 3.3s '+JSON.stringify({level,quantity,mode,pattern,age:f.age}));
   A.assert(f.comboHits===air&&f.move.dmg===original.damage&&f.move.quantityBonusAtCast===original.quantity,'budget fit mutated cast stats/count');
   const primary=r.ledger.filter(h=>h.primary),airHits=primary.filter(h=>h.phase==='combo');
   if(!approach)approach=primary[0].age-f.durations.windup;
   if(mode==='chase')A.assert(approach>=.3&&approach<.6,'moving-target fixture did not exercise a real long approach');
   if(mode==='approach-age-boundary')A.assert(approach>.58&&approach<.6,'boundary fixture did not consume late approach budget');
   A.assert(f.travel<=r.m.range+.001,'approach exceeded real movement range');
   A.assert(primary.length===air+2&&airHits.length===air&&r.side.every(e=>r.counts.get(e)===1)&&r.counts.get(r.outside)===0,'deadline discarded/duplicated hits or landing AOE');
   const base=f.move.dmg*f.attack*G.Types.mult(f.move.type,r.e.types)*G.Weather.mult(f.move.type);
   const expected=[base*.1,...Array.from({length:air},(_,n)=>base*.12*Math.pow(1.1,n+1)),base*.3];
   primary.forEach((hit,i)=>A.assert(Math.abs(hit.amount-expected[i])<1e-7,'deadline changed hit exponent '+i));
   airHits.forEach((hit,i)=>A.assert(hit.lift===60+8*(i+1),'compressed hit did not rise eight pixels'));
   A.assert(r.ledger.filter(h=>!h.primary).every(h=>Math.abs(h.amount-base*.35)<1e-7),'landing splash changed');
   A.assert(r.casts.length===1&&r.casts[0]==='naruto-reverse-lotus','basic or second main cast interrupted deadline');
   const factor=f.durations.combo/original.duration,intervals=f.comboDeadlines.map((d,i)=>d-(f.comboDeadlines[i-1]||0));
   A.assert(Math.abs(factor-Math.min(1,(3.3-approach-1.6)/1.65))<1e-9,'approach budget applied at more than the windup transition');
   A.assert(factor>0&&factor<=1&&intervals.every((d,i)=>d>0&&(!i||d<intervals[i-1])),'budget fitting destroyed accelerating schedule');
   f.comboDeadlines.forEach((d,i)=>A.assert(Math.abs(d-original.deadlines[i]*factor)<1e-10,'deadlines scaled inconsistently'));
   A.assert(!L.liftFor(r.e)&&!L.isInvulnerable(p),'completed deadline retained lift/immunity');
   out.push({level,quantity,air,mode,pattern,age:f.age,approach,combo:f.durations.combo,initialCombo:original.duration,factor,hits:primary.length,splash:r.side.map(e=>r.counts.get(e)),steps});
 }
 for(const mode of ['near','far','chase','approach-age-boundary'])for(const pattern of Object.keys(patterns)){
   const rows=out.filter(r=>r.mode===mode&&r.pattern===pattern);A.assert(rows[0].age>rows[1].age&&rows[1].age>rows[2].age,'higher counts did not finish faster');
 }
 // Forward Lotus retains its separate 1.66s presentation and two real hits.
 const front=[];
 for(const dt of [1/30,1/60,1/144,4]){const r=A.deadlineFixture(1,0,'near','naruto-lotus');A.resume();
   try{for(let n=0;n<600&&L.active;n++){G.Combat.tick(dt,p,0);G.Combat.updateFields(dt)}}finally{A.pause()}
   A.assert(!L.active&&r.f.age>=1.66&&r.f.age<1.75&&r.counts.get(r.e)===2,'reverse deadline changed normal Lotus');front.push({dt,age:r.f.age,hits:r.counts.get(r.e)});
 }
 return {cases:out,front};
}"""

def main():
    OUT.mkdir(parents=True,exist_ok=True);report={'errors':[],'failedRequests':[],'viewports':{}}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            for mobile in (False,True):
                label='mobile' if mobile else 'desktop';ctx=browser.new_context(locale='zh-TW',viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
                page=ctx.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.on('response',lambda r:report['failedRequests'].append(r.url) if r.status>=400 and '127.0.0.1' in r.url else None)
                page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY&&G.AnimationLab&&document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30006"]').click();page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
                page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(HELPERS);report['viewports'][label]=page.evaluate(MATRIX);ctx.close()
            browser.close()
        assert not report['errors'],report['errors'];assert not report['failedRequests'],report['failedRequests'];report['ok']=True
    except Exception as error:report['ok']=False;report['failure']=str(error);raise
    finally:(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'cases':120,'evidence':str(OUT)},ensure_ascii=False))

if __name__=='__main__':main()
