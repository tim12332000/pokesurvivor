"""Native chakra range rendering: radius, visibility, calm mode and desktop/mobile captures."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/chidori-chakra-range'
CHECK = r"""() => {
 G.Naruto.choose(30002);G.Flow.play();Acceptance.pause();Acceptance.arena();
 const p=G.Game.player,m=p.activeMove(),assert=Acceptance.assert,scale=G.Camera.scale||1;
 const wallNow=performance.now.bind(performance),NativePath=window.Path2D,hash=G.U.hash;
 let clock=1800,hashCalls=0,pathCreations=0;
 performance.now=()=>clock;G.U.hash=function(...args){hashCalls++;return hash.apply(this,args)};
 window.Path2D=class extends NativePath{
   constructor(){super();pathCreations++;this.points=[]}
   moveTo(x,y){this.points.push([x,y]);super.moveTo(x,y)}
   lineTo(x,y){this.points.push([x,y]);super.lineTo(x,y)}
 };
 const canvas=document.createElement('canvas');canvas.width=canvas.height=512;
 const ctx=canvas.getContext('2d');ctx.translate(256,256);
 let strokes=[];const stroke=ctx.stroke;
 ctx.stroke=function(path){strokes.push({path,alpha:this.globalAlpha,blur:this.shadowBlur,width:this.lineWidth,points:path.points||[]});return stroke.call(this,path)};
 const render=()=>{
   strokes=[];ctx.clearRect(-256,-256,512,512);G.Combat.drawGroundFields(ctx);
   assert(ctx.globalAlpha===1&&ctx.getLineDash().length===0&&ctx.getTransform().e===256&&ctx.shadowBlur===0&&ctx.lineWidth===1,'range leaked canvas state');
   return canvas.toDataURL();
 };
 const roots=()=>strokes.filter(s=>Math.abs(s.width-1.05/scale)<.001);
 const topology=()=>{
   const main=roots(),forks=strokes.filter(s=>Math.abs(s.width-.65/scale)<.001);
   const segments=strokes.reduce((n,s)=>n+Math.max(0,s.points.length-1),0);
   assert(main.length>=3&&main.length<=10,'cohorts lost their irregular multi-root topology');
   assert(segments<=480,'two-cohort segment budget exceeded');
   assert(strokes.every(s=>s.blur===0&&s.alpha<=.221),'unexpected glow or strong opacity');
   for(const s of strokes)assert(s.points.every(q=>Math.hypot(...q)<=m.range+.001),'geometry escaped actual range');
   for(const s of main)assert(Math.hypot(...s.points[0])<=11/scale,'root does not begin near feet');
   for(const s of forks){const first=s.points[0];assert(strokes.some(parent=>parent!==s&&parent.points.some(q=>q[0]===first[0]&&q[1]===first[1])),'fork is disconnected from its parent')}
   return {roots:main.length,forks:forks.length,segments};
 };
 const measure=()=>{
   render();const shape=topology(),pixels=ctx.getImageData(0,0,512,512).data;
   let inner=Infinity,outer=0,gold=0,maxAlpha=0;
   for(let y=0;y<512;y++)for(let x=0;x<512;x++){
     const i=(y*512+x)*4;if(!pixels[i+3])continue;
     maxAlpha=Math.max(maxAlpha,pixels[i+3]);const d=Math.hypot(x-256,y-256);inner=Math.min(inner,d);outer=Math.max(outer,d);
     if(pixels[i]>200&&pixels[i+1]>100&&pixels[i+2]<200)gold++;
   }
   assert(gold>100&&maxAlpha<=140,'helper missing or too bright');
   assert(inner<20/scale&&outer<=m.range+1.5,'rendered range incorrect');
   assert(roots().filter(s=>Math.abs(Math.hypot(...s.points.at(-1))-m.range)<.001).length>=2,'full cohort does not indicate actual range');
   return {radius:m.range,inner,outer,goldPixels:gold,maxAlpha,...shape};
 };
 let result;
 try{
   const initial=measure();for(let i=0;i<3;i++)G.Moves.levelUp(m);const upgraded=measure();
   assert(upgraded.outer>initial.outer+15,'range failed to follow upgrade');
   const cached=strokes.map(s=>s.path),beforePaths=pathCreations,beforeHash=hashCalls;
   clock=1850;render();assert(strokes.every((s,i)=>s.path===cached[i])&&pathCreations===beforePaths,'same-frame paths not reused');
   clock=1900;render();assert(hashCalls===beforeHash,'geometry rebuilt before cohort replacement');
   const reusedGeometry=true;
   G.Settings.set('calm',true);const calm=render();clock=4000;assert(render()===calm&&roots().length>=3,'calm pose changed or lost roots');
   G.Settings.set('calm',false);
   const shapes=new Set(),counts=new Set(),alphas=[],forkCounts=[],bounds=[];
   for(clock=0;clock<=12000;clock+=100){render();const t=topology();bounds.push(t.segments);counts.add(t.roots);forkCounts.push(t.forks);shapes.add(JSON.stringify(roots().map(s=>s.points.at(-1))));alphas.push(...roots().map(s=>s.alpha))}
   assert(counts.size>1&&shapes.size>10&&Math.max(...forkCounts)>2,'root counts, directions or stochastic forks remain fixed');
   assert(Math.max(...alphas)-Math.min(...alphas)>.15,'cohorts do not independently fade');
   clock=2500;render();const early=Math.max(...roots().filter(s=>s.alpha<.1).map(s=>Math.hypot(...s.points.at(-1))));
   clock=2800;render();assert(roots().some(s=>s.alpha<.1&&Math.hypot(...s.points.at(-1))>early+20),'outward reveal never advances');
   // Measure native CPU canvas command submission on this host, not phone hardware.
   ctx.stroke=stroke;window.Path2D=NativePath;G.U.hash=hash;
   const samples=[];for(let i=0;i<240;i++){clock=20000+i*100;const start=wallNow();ctx.clearRect(-256,-256,512,512);G.Combat.drawGroundFields(ctx);samples.push(wallNow()-start)}
   samples.sort((a,b)=>a-b);
   const timing={samples:samples.length,medianMs:samples[120],p95Ms:samples[228],maxMs:samples.at(-1),method:'headless same-host CPU canvas command submission; not a real phone benchmark'};
   ctx.stroke=function(path){strokes.push({path,points:path.points||[]});return stroke.call(this,path)};
   p.addMove('naruto-fireball');render();assert(!ctx.getImageData(0,0,512,512).data.some((n,i)=>i%4===3&&n),'range survived switching');
   p.setActive(p.slots.findIndex(g=>g.includes(m)));p.dead=true;render();assert(!ctx.getImageData(0,0,512,512).data.some((n,i)=>i%4===3&&n),'range survived death');
   p.dead=false;p.frozen=true;
   result={initial,upgraded,segmentCap:480,measuredMaxSegments:Math.max(...bounds),cachedPaths:true,reusedGeometry,calmStatic:true,stochasticCohorts:true,progressiveReveal:true,noGlow:true,switchHidden:true,deathHidden:true,timing};
 }finally{performance.now=wallNow;window.Path2D=NativePath;G.U.hash=hash;G.Settings.set('calm',false)}
 return result;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in [False, True]:
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.evaluate(HARNESS)
            label = 'mobile' if mobile else 'desktop'
            report[label] = page.evaluate(CHECK)
            page.evaluate('performance.now=()=>1200;Acceptance.resume()')
            page.wait_for_timeout(120)
            page.screenshot(path=str(OUT / f'{label}.png'))
            assert not errors, errors
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, **report}))

if __name__ == '__main__':
    main()
