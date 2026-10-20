"""Reverse Lotus rises eight world pixels per kick and accelerates its hit schedule."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP
from test_redrawn_heroes import AUDIT

# Source-audited actor evidence needs enough space for the genuine high-altitude pose.
# This changes only the test canvas, never the actor's actual visualLift.
TALL_HARNESS=(HARNESS.replace('canvas.width=240;canvas.height=200','canvas.width=240;canvas.height=620')
    .replace('anim.draw(ctx,120,150,opts)','anim.draw(ctx,120,550,opts)')
    .replace('0,0,240,200','0,0,240,620').replace('y0=200','y0=620')
    .replace('y<200','y<620').replace('y1<199','y1<619'))

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.omx/state/lee-rising-combo'
URL='http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=lee-rising-combo'

HELPERS=r"""() => {
 const A=Acceptance,p=A.p();p.level=12;
 for(const id of ['naruto-reverse-lotus','naruto-gates']){const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'learn '+id)}
 A.risingFixture=(level,quantity)=>{
   A.leeArena();G.Weather.reset();p.statsTaken.quantity=0;const m=A.select('naruto-reverse-lotus');
   while(m.lvl<level){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+m.id);A.assert(card&&card.apply(p)!==false,'upgrade rising skill')}
   for(let n=0;n<quantity;n++){let card;for(let k=0;k<150&&!card;k++)card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');A.assert(card,'real quantity card missing');card.apply(p)}
   const e=A.spawn(35,0);e.maxHp=e.hp=10000000;p.target=e;p.aim=0;const ledger=[],effects=[];
   const hurt=e.hurt;e.hurt=function(...args){const f=G.NarutoLee.active;
     ledger.push({phase:f?.phase,n:f?.ticks,phaseAge:f?.phaseAge,lift:f?.visualLift,targetLift:G.NarutoLee.liftFor(this),amount:args[0],x:this.x,y:this.y});return hurt.apply(this,args)};
   for(const kind of ['dmgText','spark','burst']){const original=G.FX[kind];G.FX[kind]=function(x,y,...args){const f=G.NarutoLee.active;
     if(f?.phase==='combo'&&x===e.x)effects.push({kind,n:f.ticks,y,lift:G.NarutoLee.liftFor(e),native:e.jumpLift||0});return original.call(this,x,y,...args)};}
   A.actualCast(m.id);A.rising={m,e,ledger,effects,level,quantity};return A.rising;
 };
 A.viewportBounds=()=>{
   const p=A.p(),canvas=document.createElement('canvas');canvas.width=innerWidth;canvas.height=innerHeight;
   const ctx=canvas.getContext('2d');ctx.scale(G.Camera.scale,G.Camera.scale);G.Camera.apply(ctx);p.anim.draw(ctx,p.x,p.y);
   const data=ctx.getImageData(0,0,canvas.width,canvas.height).data;let x0=canvas.width,y0=canvas.height,x1=-1,y1=-1,pixels=0;
   for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++)if(data[(y*canvas.width+x)*4+3]>20){pixels++;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}
   A.assert(pixels>80&&x0>0&&y0>0&&x1<canvas.width-1&&y1<canvas.height-1,'actual viewport camera clipped airborne actor');
   const groundY=(p.y-G.Camera.top())*G.Camera.scale;
   A.assert(groundY>y1+G.NarutoLee.active.visualLift*G.Camera.scale*.8,'ground shadow did not remain far below aerial body');
   return {bounds:[x0,y0,x1,y1],pixels,groundY,cameraY:G.Camera.y,scale:G.Camera.scale,width:canvas.width,height:canvas.height};
 };
}"""

RISE=r"""params => {
 const A=Acceptance,p=A.p(),L=G.NarutoLee,r=A.risingFixture(params.level,params.quantity),f=L.active,dt=.0001;
 const planned=f.comboDeadlines,intervals=planned.map((t,i)=>t-(planned[i-1]||0));
 A.assert(f.comboHits===params.count&&planned.length===params.count,'wrong planned kick count');
 A.assert(intervals.every((d,i)=>d>0&&(!i||d<intervals[i-1])),'planned kicks do not strictly accelerate');
 const duration=1.65/(1+.025*(params.count-5));A.assert(Math.abs(f.durations.combo-duration)<1e-10&&Math.abs(planned.at(-1)-duration)<1e-10,'wrong normalized combo duration');
 const ground={x:p.x,y:p.y,targetX:r.e.x,targetY:r.e.y};A.resume();
 try{for(let n=0;n<60000&&L.active?.phase!=='descent';n++){G.Camera.follow(p.x,p.y,dt);L.update(dt);G.FX.update(dt)}}finally{A.pause()}
 A.assert(L.active?.phase==='descent','high precision simulation did not finish the kick schedule');
 const air=r.ledger.filter(h=>h.phase==='combo');A.assert(air.length===params.count,'actual kick count differs from planned schedule');
 air.forEach((hit,i)=>{
   const lift=60+8*(i+1);A.assert(Math.abs(hit.lift-lift)<1e-8&&Math.abs(hit.targetLift-lift)<1e-8,'hit height was not raised before damage '+(i+1));
   A.assert(Math.abs(hit.phaseAge-planned[i])<dt+1e-8,'actual high precision hit missed its deadline');
 });
 const actualIntervals=air.map((h,i)=>h.phaseAge-(air[i-1]?.phaseAge||0));A.assert(actualIntervals.every((d,i)=>!i||d<actualIntervals[i-1]),'actual kick intervals failed to speed up');
 for(const effect of r.effects){const expected=effect.kind==='dmgText'?r.e.y-r.e.bodyH-4-effect.lift:effect.kind==='spark'?r.e.y-r.e.bodyH*.5-effect.lift:r.e.y-effect.native-effect.lift;
   A.assert(Math.abs(effect.y-expected)<1e-8,'hit effect remained at ground instead of air body '+effect.kind);
 }
 A.assert(r.effects.filter(e=>e.kind==='dmgText').length===params.count&&r.effects.filter(e=>e.kind==='spark').length===params.count,'native damage number/spark path missing');
 A.assert(f.visualLift===60+8*params.count&&f.peakLift===f.visualLift,'peak height did not follow number of kicks');
 A.assert(p.x===ground.x&&p.y===ground.y&&r.e.x===ground.targetX&&r.e.y===ground.targetY,'visual rise moved ground collision coordinates');
 A.assert(L.isInvulnerable(p),'high descent lost reverse immunity');
 const pose=A.render();A.assert(pose.state.key==='lee-opened-reverse'&&pose.sources.every(s=>s.includes('lee-gates-skills-v1.png')),'rising combo lost actual redform source');
 const viewport=A.viewportBounds();const age=f.age,peak=f.visualLift;G.Combat.updateFields(.3);
 A.assert(f.age===age&&f.visualLift===peak,'paused high combo advanced');
 return {count:params.count,peak:f.peakLift,duration,planned,intervals,actualIntervals,hits:air,effects:r.effects,viewport,source:pose.sources,phase:f.phase};
}"""

DESCENT=r"""() => {
 const A=Acceptance,p=A.p(),L=G.NarutoLee,f=L.active,r=A.rising,peak=f.peakLift,values=[];
 A.resume();try{for(let n=0;n<100&&L.active?.phase==='descent';n++){G.Camera.follow(p.x,p.y,.005);L.update(.005);if(L.active?.phase==='descent')values.push(L.active.visualLift)}}finally{A.pause()}
 A.assert(values.length>20&&values[0]>peak*.95&&values.at(-1)<peak*.03&&values.every((h,i)=>!i||h<values[i-1]),'descent did not smoothly start at actual rising peak');
 A.assert(L.active?.phase==='slam'&&!L.isInvulnerable(p)&&L.active.visualLift===0&&!L.liftFor(r.e),'landing did not remove high-altitude lift/immunity');
 A.assert(Math.abs(G.Camera.y-p.y)<.001,'camera retained its forced aerial offset after landing');
 A.advance(1);A.assert(!L.active&&r.ledger.length===f.comboHits+2,'high combo landing lost/duplicated final hit');
 return {peak,values,cameraY:G.Camera.y,totalHits:r.ledger.length};
}"""

CLEANUP=r"""() => {
 const A=Acceptance,p=A.p(),L=G.NarutoLee,out={};
 A.risingFixture(5,20);A.resume();try{for(let n=0;n<3000&&L.active?.phase!=='descent';n++){G.Camera.follow(p.x,p.y,.001);L.update(.001)}}finally{A.pause()}
 A.assert(L.active?.visualLift>=320,'cleanup fixture never reached max height');G.Combat.clearFields(p);
 A.assert(!L.active&&!L.liftFor(A.rising.e)&&Math.abs(G.Camera.y-p.y)<.001,'clear retained elevated camera or actor height');out.clear=true;
 A.risingFixture(5,0);const e=A.rising.e;e.startJump(p);e.updateJump(.55);const native=e.jumpLift;
 A.advance(1.2);A.assert(e.jumpLift===native&&L.liftFor(e)>60,'rising combo overwrote native jump height');G.Combat.clearFields(p);A.assert(e.jumpLift===native&&!L.liftFor(e),'cleanup destroyed original enemy jump');out.nativeJump=true;
 A.risingFixture(5,20);A.advance(1.8);const world=G.World;G.World={...world};G.Camera.y=12345;A.advance(.001);
 A.assert(!L.active&&G.Camera.y===12345,'old-world clear overwrote new-world camera');G.World=world;G.Camera.y=p.y;out.worldCameraIsolation=true;
 A.risingFixture(5,0);const shielded=A.rising.e;shielded.shield=1000000000;const hp=shielded.hp;A.advance(4);
 const numbers=A.rising.effects.filter(effect=>effect.kind==='dmgText');
 A.assert(shielded.hp===hp&&numbers.length===13&&numbers.every(effect=>Math.abs(effect.y-(shielded.y-shielded.bodyH-4-effect.lift))<1e-8),'shield absorption numbers did not follow per-hit aerial height');out.shieldTextHeight=true;
 return out;
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
                page.evaluate('()=>G.Sprites.preload([19])');page.evaluate(TALL_HARNESS);page.evaluate(SETUP);page.evaluate(AUDIT);page.evaluate(HELPERS)
                result={'counts':[]};report['viewports'][label]=result
                for level,quantity,count in [(1,0,5),(5,2,15),(5,20,33)]:
                    case=page.evaluate(RISE,{'level':level,'quantity':quantity,'count':count})
                    result['counts'].append(case)
                    page.wait_for_function("!document.getElementById('ach-pop')||document.getElementById('ach-pop').classList.contains('hidden')")
                    page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                    page.screenshot(path=str(OUT/f'{label}-air{count}-peak.png'))
                    if mobile and count==33:
                        previous_camera=page.evaluate('({x:G.Camera.x,y:G.Camera.y})')
                        page.set_viewport_size({'width':844,'height':390})
                        page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                        case['landscapeViewport']=page.evaluate('() => {Acceptance.resume();G.Camera.follow(G.Game.player.x,G.Game.player.y,.0001);G.NarutoLee.update(.0001);Acceptance.pause();return Acceptance.viewportBounds()}')
                        assert case['landscapeViewport']['bounds'][1]>70,case['landscapeViewport']
                        page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                        page.screenshot(path=str(OUT/'mobile-landscape-air33-peak.png'))
                        page.set_viewport_size({'width':390,'height':844})
                        page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                        page.evaluate('camera=>{G.Camera.x=camera.x;G.Camera.y=camera.y}',previous_camera)
                    case['descent']=page.evaluate(DESCENT)
                    page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                    page.screenshot(path=str(OUT/f'{label}-air{count}-landed.png'))
                result['cleanup']=page.evaluate(CLEANUP)
                duration=[r['duration'] for r in result['counts']]
                assert duration[0]>duration[1]>duration[2],duration
                ctx.close()
            browser.close()
        assert not report['errors'],report['errors'];assert not report['failedRequests'],report['failedRequests'];report['ok']=True
    except Exception as error:report['ok']=False;report['failure']=str(error);raise
    finally:(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'evidence':str(OUT)},ensure_ascii=False))

if __name__=='__main__':main()
