"""Both Lotus techniques own a sustained, distinct aerial performance and stronger impact."""
import base64
import json
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP
from test_redrawn_heroes import AUDIT

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.omx/state/lee-lotus-presentation'
URL='http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=lee-lotus-presentation'

HELPERS=r"""() => {
 const A=Acceptance,p=A.p();p.level=12;
 for(const id of ['naruto-lotus','naruto-reverse-lotus','naruto-gates']){const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'learn '+id)}
 A.presentationTick=dt=>{A.resume();try{G.Combat.tick(dt,p,0);G.Combat.updateFields(dt);p.anim.update(dt);G.FX.update(dt)}finally{A.pause()}};
 A.presentationFixture=id=>{
   A.leeArena();const m=A.select(id),e=A.spawn(35,0),side=[0,2*Math.PI/3,4*Math.PI/3].map(a=>A.spawn(35+Math.cos(a)*m.radius*.65,Math.sin(a)*m.radius*.65));
   const outside=A.spawn(35+m.radius+30,40),ledger=[],counts=new Map();
   for(const enemy of [e,...side,outside]){counts.set(enemy,0);const hurt=enemy.hurt;enemy.hurt=function(...args){counts.set(this,counts.get(this)+1);ledger.push({primary:this===e,amount:args[0]});return hurt.apply(this,args)}}
   p.target=e;p.aim=0;A.actualCast(id);A.presentation={id,m,e,side,outside,ledger,counts};return A.presentation;
 };
 A.presentationScene=()=>{
   const r=A.presentation,canvas=document.createElement('canvas');canvas.width=480;canvas.height=360;const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.fillStyle='#17422b';ctx.fillRect(0,0,480,360);
   ctx.save();ctx.translate(240-r.e.x,220-r.e.y);G.Combat.drawGroundFields(ctx);for(const e of [...r.side,r.outside,r.e])e.draw(ctx);p.draw(ctx);G.Combat.drawAirFields(ctx);G.FX.draw(ctx);ctx.restore();
   const pose=A.render();delete pose.png;return {pose,phase:G.NarutoLee.active?.phase||'basic',lift:G.NarutoLee.active?.visualLift||0,png:canvas.toDataURL()};
 };
}"""

PRESENTATION=r"""id => {
 const A=Acceptance,p=A.p(),reverse=id==='naruto-reverse-lotus';
 // Capture a real native melee punch before contrasting its action atlas.
 A.leeArena();let m=A.select(id);m.t=10;const basicEnemy=A.spawn(35,0);p.target=basicEnemy;A.presentation={id,m,e:basicEnemy,side:[],outside:basicEnemy};
 A.resume();try{G.Combat.tick(.6,p,0)}finally{A.pause()}const basic=A.presentationScene();A.assert(basic.pose.state.key==='lee-opened-attack','basic reference did not use shared punch');
 const r=A.presentationFixture(id),expectedBase=reverse?210:110,expectedKey=reverse?'lee-opened-reverse':'lee-opened-lotus',frames={},phases=[],descent=[];
 A.assert(r.m.dmg===expectedBase&&r.m.cd===(reverse?5:3),'main damage/cooldown not updated');
 const cast=p.cast,casts=[];p.cast=function(m,...args){casts.push(m.id);return cast.call(this,m,...args)};
 let elapsed=0,maxLift=0,airTime=0;
 try{for(let n=0;n<1000&&G.NarutoLee.active;n++){
   const f=G.NarutoLee.active;phases.push(f.phase);if(!['slam','recovery'].includes(f.phase))A.assert(r.side.every(e=>r.counts.get(e)===0),'impact happened before landing');
   A.presentationTick(.005);elapsed+=.005;const current=G.NarutoLee.active;if(!current)break;
   maxLift=Math.max(maxLift,current.visualLift);if(current.visualLift>1)airTime+=.005;
   if(!reverse)A.assert(!G.NarutoLee.isInvulnerable(p),'normal Lotus gained aerial immunity');
   const phase=current.phase,label=phase==='suspend'||phase==='combo'?'air':phase==='slam'?'landing':phase;
   if(phase==='descent')descent.push(current.visualLift);
   const ready=phase==='windup'?current.phaseAge>.08:phase==='lift'?current.visualLift>(reverse?30:20):phase==='combo'?current.phaseAge>.4:phase==='suspend'?current.phaseAge>.1:phase==='descent'?current.phaseAge>.12:phase==='slam';
   if(ready&&!frames[label])frames[label]=A.presentationScene();
 }}finally{p.cast=cast}
 A.assert(!G.NarutoLee.active&&elapsed>=(reverse?3.25:1.66),'main action still too short '+elapsed);
 A.assert(maxLift===(reverse?60:40)&&airTime>(reverse?2:.8),'main action did not visibly stay airborne');
 A.assert(['windup','lift',reverse?'combo':'suspend','descent','slam','recovery'].every(phase=>phases.includes(phase)),'missing presentation phase');
 A.assert(descent.length>20&&descent.every((h,i)=>!i||h<=descent[i-1]+.001)&&descent.at(-1)<2,'descent did not smoothly reach ground');
 A.assert(!casts.includes('tackle'),'cooldown basic interrupted Lotus presentation');
 A.assert(Object.values(frames).every(frame=>frame.pose.state.key===expectedKey&&frame.pose.sources.every(s=>s.includes('lee-gates-skills-v1.png'))),'main action reused shared basic art');
 const primary=r.ledger.filter(h=>h.primary),expectedHits=reverse?7:2,base=r.m.dmg*p.atk*G.Types.mult(r.m.type,r.e.types)*G.Weather.mult(r.m.type);
 const ratios=reverse?[.1,...Array.from({length:5},(_,n)=>.12*Math.pow(1.1,n+1)),.3]:[.2,.8];
 A.assert(primary.length===expectedHits,'presentation changed real primary hit count');
 primary.forEach((hit,i)=>A.assert(Math.abs(hit.amount-base*ratios[i])<1e-6,'boosted main hit amount incorrect'));
 A.assert(r.side.every(e=>r.counts.get(e)===1)&&r.counts.get(r.outside)===0,'landing AOE lost inside/outside coverage');
 A.assert(r.ledger.filter(h=>!h.primary).every(h=>Math.abs(h.amount-base*.35)<1e-6),'boosted splash incorrect');
 const expectedLoss=ratios.reduce((sum,ratio)=>sum+Math.round(base*ratio),0);A.assert(100000-r.e.hp===expectedLoss,'boosted native HP damage mismatch');
 return {id,baseDamage:r.m.dmg,cooldown:r.m.cd,elapsed,maxLift,airTime,phases:[...new Set(phases)],primaryHits:primary.length,damage:expectedLoss,basic,frames};
}"""

DEAD_TARGET=r"""() => {
 const A=Acceptance,p=A.p(),out=[];
 for(const id of ['naruto-lotus','naruto-reverse-lotus']){
   const r=A.presentationFixture(id);for(let n=0;n<300&&G.NarutoLee.active?.phase!=='lift';n++)A.advance(.005);
   A.assert(G.NarutoLee.active?.phase==='lift','committed launch fixture');const hits=r.counts.get(r.e),credit=p.dmgDealt;r.e.hp=0;r.e.dead=true;
   A.advance(4);A.assert(!G.NarutoLee.active&&r.counts.get(r.e)===hits&&r.e.hp===0,'dead primary received extra damage');
   A.assert(r.side.every(e=>r.counts.get(e)===1),'committed technique did not finish landing AOE after early KO');
   const expected=r.side.length*r.m.dmg*.35*p.atk*G.Types.mult(r.m.type,r.side[0].types)*G.Weather.mult(r.m.type);
   A.assert(Math.abs(p.dmgDealt-credit-expected)<1e-6,'dead primary generated fake damage credit');out.push(id);
 }
 for(const phase of ['lift','suspend','descent']){
   A.presentationFixture('naruto-lotus');for(let n=0;n<500&&G.NarutoLee.active?.phase!==phase;n++)A.advance(.005);
   A.assert(G.NarutoLee.active?.phase===phase,'normal aerial vulnerability fixture '+phase);p.invuln=0;const hp=p.hp;p.hurt(5,null,true);
   A.assert(p.hp===hp-5,'normal Lotus not damageable '+phase);
 }return {committedOnEarlyKO:out,normalAirDamageable:true};
}"""

def strip(paths,target):
    width=480;header=26;images=[Image.open(p).convert('RGB') for _,p in paths]
    board=Image.new('RGB',(width*len(images),360+header),'#0f291d');draw=ImageDraw.Draw(board)
    for i,((label,_),im) in enumerate(zip(paths,images)):
        draw.text((i*width+8,7),label,fill='white');board.paste(im,(i*width,header))
    board.save(target)

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
                page.evaluate('()=>G.Sprites.preload([19])');page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(AUDIT);page.evaluate(HELPERS)
                result={'techniques':[]};report['viewports'][label]=result
                for id in ('naruto-lotus','naruto-reverse-lotus'):
                    evidence=page.evaluate(PRESENTATION,id);paths=[]
                    for phase,frame in [('basic',evidence['basic']),*evidence['frames'].items()]:
                        path=OUT/f'{label}-{id}-{phase}.png';path.write_bytes(base64.b64decode(frame.pop('png').split(',',1)[1]));paths.append((phase,path))
                    strip(paths,OUT/f'{label}-{id}-strip.png');result['techniques'].append(evidence)
                result['regressions']=page.evaluate(DEAD_TARGET);ctx.close()
            browser.close()
        assert not report['errors'],report['errors'];assert not report['failedRequests'],report['failedRequests'];report['ok']=True
    except Exception as error:report['ok']=False;report['failure']=str(error);raise
    finally:(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'evidence':str(OUT)},ensure_ascii=False))

if __name__=='__main__':main()
