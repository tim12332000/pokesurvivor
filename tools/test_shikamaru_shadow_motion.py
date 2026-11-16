"""A moving source must deform the whole shadow, not stretch one edge into an elbow."""
import json
import subprocess
import sys
from playwright.sync_api import sync_playwright
import test_shikamaru as base

OUT=base.ROOT/'art-review/shikamaru/qa/shadow-motion'
CHECK=r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,M=G.NarutoShikamaruMass,out={};
 const inspect=seg=>{const points=seg.grownPoints,steps=points.slice(1).map((v,i)=>Math.hypot(v.x-points[i].x,v.y-points[i].y)).filter(d=>d>1e-5),mean=steps.reduce((a,b)=>a+b,0)/steps.length;
  A.assert(Math.hypot(points[0].x-p.x,points[0].y-p.y)<1e-6,'root detached from live feet');
  A.assert(Math.max(...steps)<Math.max(12,mean*2.5),'single long edge forms an elbow '+JSON.stringify({max:Math.max(...steps),mean}));
  let angle=0;for(let i=1;i<points.length-1;i++){const a=points[i-1],b=points[i],c=points[i+1],ux=b.x-a.x,uy=b.y-a.y,vx=c.x-b.x,vy=c.y-b.y,d=Math.hypot(ux,uy)*Math.hypot(vx,vy);if(d>1e-5)angle=Math.max(angle,Math.acos(Math.max(-1,Math.min(1,(ux*vx+uy*vy)/d))))}
  A.assert(angle<1.1,'sharp local tangent turn '+angle);return {points:points.length,maxStep:Math.max(...steps),mean,maxTurn:angle,linked:seg.linked};};
 const setup=()=>{A.reset();const m=A.fixture('naruto-shikamaru'),e=A.spawn(190,0);A.cast(m);return {e,b:S.casts.at(-1)}};
 let {e,b}=setup();A.finish(.29);let seg=b.chain.segments[0],tip={...seg.grownPoints.at(-1)};p.x=-90;p.y=110;S.update(0);A.step(.00001);seg=b.chain.segments[0];out.flight=inspect(seg);A.assert(Math.hypot(seg.grownPoints.at(-1).x-tip.x,seg.grownPoints.at(-1).y-tip.y)<.02,'moving source teleported unreleased front to target');
 ({e,b}=setup());A.finish(.6);seg=b.chain.segments[0];A.assert(seg.contact,'fixture failed to bind');p.x=-90;p.y=110;A.step(.01);out.bound=inspect(seg);A.assert(S.held(e),'source movement released clear connected target');
 const orbit=[];for(let i=0;i<48;i++){const t=i*Math.PI*2/48;p.x=e.x+150*Math.cos(t);p.y=e.y+150*Math.sin(t);A.step(.002);orbit.push(inspect(seg))}out.orbit={frames:orbit.length,maxTurn:Math.max(...orbit.map(v=>v.maxTurn))};
 p.x=e.x+seg.contactOffset.x-.25;p.y=e.y+seg.contactOffset.y;A.step(.002);A.assert(seg.grownPoints.every(v=>Number.isFinite(v.x)&&Number.isFinite(v.y)),'near-zero link produced invalid geometry');A.assert(seg.grownPoints.every(v=>Math.hypot(v.x-p.x,v.y-p.y)<1),'near-zero link retained a large loop');out.collapsed=true;
 ({e,b}=setup());A.finish(.6);seg=b.chain.segments[0];e.x+=65;e.y+=70;G.EnemyMgr.rebuildGrid();A.step(.002);out.targetMotion=inspect(seg);A.assert(Math.hypot(seg.grownPoints.at(-1).x-e.x-seg.contactOffset.x,seg.grownPoints.at(-1).y-e.y-seg.contactOffset.y)<1e-6,'tip detached from moved target');
 p.x=-70;p.y=100;G.World.projectilePathClear=()=>false;A.step(.01);A.assert(!seg.linked&&!S.held(e),'new smooth connection crossed a wall');out.wall=true;
 A.reset();p.moves=[G.Moves.instance('naruto-shikamaru-mass')];const m=p.moves[0];A.spawn(200,0);A.resume();try{A.assert(M.cast(p,m,{x:200,y:0}),'mass fixture rejected')}finally{A.pause()}b=M.casts.at(-1);const origin={...b.origin},center={...b.center};A.finish(b.full+.02);p.x=-90;p.y=110;A.step(.01);
 A.assert(b.rays.size&&[...b.rays.values()].every(r=>Math.hypot(r.source.x-p.x,r.source.y-p.y)<1e-6),'mass straight rays not at live feet');A.assert(JSON.stringify(b.origin)===JSON.stringify(origin)&&JSON.stringify(b.center)===JSON.stringify(center),'live tether dragged fixed field');out.mass={sources:[...b.rays.values()].map(r=>r.source),center:b.center};
 const canvas=document.createElement('canvas');canvas.width=canvas.height=500;const ctx=canvas.getContext('2d'),before=JSON.stringify([...b.rays.values()].map(r=>({source:r.source,current:r.current})));for(let i=0;i<10;i++)G.Combat.drawGroundFields(ctx);A.assert(before===JSON.stringify([...b.rays.values()].map(r=>({source:r.source,current:r.current}))),'render mutated tether');out.readOnly=true;
 return out;
}'''

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'checks':{},'errors':[]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
            page=browser.new_page(service_workers='block',viewport={'width':1100,'height':850})
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            base.boot(page);page.evaluate('window.WarmEnemy=Acceptance.spawn(190,0)')
            page.wait_for_function('!!G.ShikamaruReferenceGeometry.bodyFor(WarmEnemy)')
            report['checks']=page.evaluate(CHECK);browser.close()
        assert not report['errors'],report['errors']
        report['ok']=True;print('Moving source, orbit, target motion, wall and mass tether PASS')
    finally:
        (OUT/'mechanics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

def native(baseline=False):
    folder=OUT/('before' if baseline else 'native');folder.mkdir(parents=True,exist_ok=True)
    report={'controlled':True,'errors':[],'viewports':{}}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        for label,width,height in [('desktop',1100,850),('mobile390',390,844)]:
            context=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<600,has_touch=width<600,service_workers='block',record_video_dir=str(folder/label/'video'))
            page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
            if baseline:
                old=subprocess.check_output(['git','show','HEAD:.omx/naruto-shikamaru.js'],cwd=base.ROOT)
                page.route('**/.omx/naruto-shikamaru.js*',lambda route:route.fulfill(body=old,content_type='application/javascript'))
            saved=base.URL
            if width<600:base.URL=saved.replace('&layout=wide','')
            try:base.boot(page)
            finally:base.URL=saved
            data={}
            for mode in (['shadow'] if baseline else ['shadow','mass']):
                page.evaluate(r'''mode=>{const A=Acceptance,p=A.p();A.reset();p.level=6;p.moves=[G.Moves.instance('naruto-shikamaru',3)];if(mode==='mass')p.moves.push(G.Moves.instance('naruto-shikamaru-mass'));for(const [x,y]of [[150,0],[145,85],[140,-85]])A.spawn(x,y);window.MotionFrames=[];const draw=G.Combat.drawAirFields;G.Combat.drawAirFields=function(ctx){const result=draw.call(this,ctx),s=G.NarutoShikamaru.stateFor(p),b=G.NarutoShikamaruMass.stateFor(p)?.cast;MotionFrames.push({time:G.Game.st.time,x:p.x,y:p.y,segments:s?.lastChain?.chain.segments.map(seg=>({points:seg.grownPoints.map(v=>({...v})),contact:seg.contact,linked:seg.linked})),rays:b?[...b.rays.values()].map(r=>({source:{...r.source},tip:{...r.current}})):null,center:b?{...b.center}:null});return result};A.resume()}''',mode)
                if mode=='shadow':page.wait_for_function('G.NarutoShikamaru.stateFor(Acceptance.p())?.lastChain?.chain.segments.some(s=>s.contact)')
                else:page.wait_for_function('(()=>{const b=G.NarutoShikamaruMass.stateFor(Acceptance.p())?.cast;return b&&b.age>b.full})()')
                for key in ['s','a','w','d']:
                    page.keyboard.down(key);page.wait_for_timeout(180);page.keyboard.up(key)
                    page.screenshot(path=str(folder/label/(mode+'-'+key+'.png')))
                page.evaluate('Acceptance.pause()');data[mode]=page.evaluate('MotionFrames')
            report['viewports'][label]=data
            video=page.video;context.close();video.save_as(str(folder/label/'moving-shadows.webm'));video.delete()
            print(label,'real keyboard shadow movement recorded',flush=True)
        browser.close()
    assert not report['errors'],report['errors']
    report['ok']=True;(folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':
    if '--before' in sys.argv:native(True)
    elif '--native' in sys.argv:native()
    else:main()
