"""Reverse Lotus prolonged airborne combo and level-scaled landing AOE."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP
from test_redrawn_heroes import AUDIT

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.omx/state/lee-reverse-aoe'
URL='http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=lee-reverse-aoe'

HELPERS=r"""() => {
 const A=Acceptance,p=A.p();p.level=12;
 for(const id of ['naruto-reverse-lotus','naruto-gates']){const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'learn card '+id)}
 A.rings=[];const ring=G.FX.ring;G.FX.ring=function(...args){A.rings.push(args);return ring.apply(this,args)};
 A.reverseStep=dt=>{A.advance(dt);G.FX.update(dt)};
 A.reverseFixture=()=>{
   A.leeArena();A.rings=[];const m=A.select('naruto-reverse-lotus'),primary=A.spawn(35,0),side=[];
   for(const angle of [0,2*Math.PI/3,4*Math.PI/3])side.push(A.spawn(primary.x+Math.cos(angle)*m.radius*.7,primary.y+Math.sin(angle)*m.radius*.7));
   const farther=A.spawn(primary.x,primary.y-(100+primary.r+15));
   const outside=A.spawn(primary.x,primary.y+m.radius+primary.r+35);
   const counts=new Map();for(const e of [primary,...side,farther,outside]){counts.set(e,0);const hurt=e.hurt;e.hurt=function(...args){counts.set(e,counts.get(e)+1);return hurt.apply(this,args)}}
   p.target=primary;p.aim=0;A.actualCast(m.id);
   A.reverse={m,primary,side,farther,outside,counts};return {level:m.lvl,radius:m.radius};
 };
 A.reverseScene=()=>{
   const p=A.p(),r=A.reverse,canvas=document.createElement('canvas');canvas.width=640;canvas.height=600;
   const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.fillStyle='#17422b';ctx.fillRect(0,0,640,600);
   ctx.save();ctx.translate(320-r.primary.x,300-r.primary.y);G.Combat.drawGroundFields(ctx);
   for(const e of [...r.side,r.farther,r.outside,r.primary])e.draw(ctx);p.draw(ctx);G.Combat.drawAirFields(ctx);G.FX.draw(ctx);ctx.restore();
   const pose=A.render();delete pose.png;
   A.assert(pose.state.key==='lee-opened-reverse'&&pose.sources.every(s=>s.includes('lee-gates-skills-v1.png')),'reverse lost its actual redform action artwork');
   return {pose,visualLift:G.NarutoLee.active?.visualLift||0,targetLift:G.NarutoLee.liftFor(r.primary),phase:G.NarutoLee.active?.phase||null,png:canvas.toDataURL()};
 };
}"""

LEVEL=r"""level => {
 const A=Acceptance,p=A.p(),m=p.moves.find(m=>m.id==='naruto-reverse-lotus'),out={level};
 if(level>1){const before=m.radius,card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+m.id);
   A.assert(card,'missing upgrade card Lv'+level);out.card={title:card.title,desc:card.desc};
   A.assert(card.desc.includes(String(100+(level-1)*20)),'upgrade preview omits next real radius');
   A.assert(card.apply(p)!==false&&m.radius>before,'actual card did not enlarge landing AOE');}
 A.assert(m.lvl===level&&m.radius===100+(level-1)*20,'wrong radius Lv'+level+' '+m.radius);
 A.reverseFixture();const r=A.reverse;let airborne=0,elapsed=0,descending=[],air=null,landing=null;
 for(let n=0;n<350&&G.NarutoLee.active;n++){
   const f=G.NarutoLee.active,phase=f.phase;
   if(phase!=='slam'&&phase!=='recovery')A.assert(r.side.every(e=>r.counts.get(e)===0)&&r.counts.get(r.outside)===0&&r.counts.get(r.farther)===0,'AOE occurred before landing');
   A.reverseStep(.01);elapsed+=.01;
   const next=G.NarutoLee.active;if(next?.visualLift>1)airborne+=.01;
   if(next?.phase==='combo'&&next.phaseAge>.4&&!air)air=A.reverseScene();
   if(next?.phase==='descent')descending.push(next.visualLift);
   if(next?.phase==='slam'&&!landing){
     A.assert(next.visualLift===0&&G.NarutoLee.liftFor(r.primary)===0,'impact occurred while floating');landing=A.reverseScene();
   }
 }
 A.assert(!G.NarutoLee.active&&elapsed>=2.1&&airborne>1.2,'airborne combo did not stay up longer '+elapsed+' air '+airborne);
 A.assert(air&&air.visualLift>=51&&air.targetLift>=51,'airborne height did not reach 52px');
 A.assert(descending.length>10&&descending.every((h,i)=>i===0||h<=descending[i-1]+.001)&&descending[0]>40&&descending.at(-1)<5,'descent did not visibly lower toward ground');
 A.assert(landing&&r.counts.get(r.primary)===5+2*(level-1)+2,'primary combo hit count did not scale with skill level');
 A.assert(r.side.every(e=>r.counts.get(e)===1),'landing did not hit 3 separated inside enemies exactly once');
 A.assert(r.counts.get(r.outside)===0&&r.outside.hp===100000,'outside boundary damaged');
 if(level===1)A.assert(r.counts.get(r.farther)===0,'Lv1 unexpectedly hit beyond small boundary');
 if(level===5)A.assert(r.counts.get(r.farther)===1,'Lv5 did not hit enemy beyond old boundary');
 A.assert(A.rings.some(args=>Math.abs(args[3]-m.radius)<.001),'visible impact ring did not match real AOE radius');
 out.radius=m.radius;out.elapsed=elapsed;out.airborne=airborne;out.descentSamples=descending;out.primaryHits=r.counts.get(r.primary);out.splashHits=r.side.map(e=>r.counts.get(e));out.expandedTargetHits=r.counts.get(r.farther);
 return {...out,air,landing};
}"""

REGRESSIONS=r"""() => {
 const A=Acceptance,p=A.p(),out={};
 // A large simulation delta preserves the current-level primary hit count and one landing splash.
 A.reverseFixture();let r=A.reverse;const expectedHits=7+2*(r.m.lvl-1);A.reverseStep(3);
 A.assert(!G.NarutoLee.active&&r.counts.get(r.primary)===expectedHits&&r.side.every(e=>r.counts.get(e)===1),'large dt lost or duplicated combo/AOE hits');out.largeDt=true;
 // Long airborne ownership suppresses cooldown punches until recovery completes.
 A.reverseFixture();r=A.reverse;const casts=[],cast=p.cast;
 p.cast=function(m,...args){casts.push(m.id);return cast.call(this,m,...args)};
 try{for(let n=0;n<350&&G.NarutoLee.active;n++){A.resume();G.Combat.tick(.01,p,0);A.pause();A.reverseStep(.01)}}finally{p.cast=cast}
 A.assert(!casts.includes('tackle')&&r.counts.get(r.primary)===expectedHits,'basic punched into long airborne chain');out.noBasicOverlap=true;
 // Bosses retain their native ground position throughout the longer sequence.
 A.leeArena();const boss=A.spawn(35,0,true);p.target=boss;A.actualCast('naruto-reverse-lotus');
 for(let n=0;n<300&&G.NarutoLee.active;n++){A.reverseStep(.01);A.assert(!G.NarutoLee.active?.visualLift&&!G.NarutoLee.liftFor(boss)&&!boss.jumpLift,'boss lifted')};out.bossGrounded=true;
 A.reverseFixture();r=A.reverse;for(let n=0;n<200&&G.NarutoLee.active?.phase!=='combo';n++)A.reverseStep(.01);
 A.assert(G.NarutoLee.active?.phase==='combo','combo phase fixture never reached');
 const before={age:G.NarutoLee.active.age,lift:G.NarutoLee.liftFor(r.primary),phase:G.NarutoLee.active.phase};G.Combat.updateFields(.5);
 A.assert(G.NarutoLee.active.age===before.age&&G.NarutoLee.liftFor(r.primary)===before.lift,'pause advanced long airborne combo');
 G.Combat.clearFields(p);A.assert(!G.NarutoLee.active&&!G.NarutoLee.liftFor(r.primary),'clear left airborne height');out.pauseClear=true;
 for(const phase of ['lift','combo']){
   A.reverseFixture();r=A.reverse;
   for(let n=0;n<200&&G.NarutoLee.active?.phase!==phase;n++)A.reverseStep(.01);
   A.assert(G.NarutoLee.active?.phase===phase,'dead-target fixture missing '+phase);
   const priorHits=r.counts.get(r.primary),credit=p.dmgDealt;r.primary.hp=0;r.primary.dead=true;
   for(let n=0;n<350&&G.NarutoLee.active;n++)A.reverseStep(.01);
   A.assert(!G.NarutoLee.active&&r.side.every(e=>r.counts.get(e)===1),'dead primary cancelled promised landing AOE '+phase);
   A.assert(r.counts.get(r.primary)===priorHits&&r.primary.hp===0&&r.primary.dead,'dead primary received extra hit or revived');
   const live=[...r.side,r.farther].filter(e=>r.counts.get(e)===1),expected=live.reduce((sum,e)=>sum+r.m.dmg*.35*p.atk*G.Types.mult(r.m.type,e.types)*G.Weather.mult(r.m.type),0);
   A.assert(Math.abs((p.dmgDealt-credit)-expected)<1e-6,'dead-primary landing granted extra damage credit');
 }out.deadPrimaryStillLands=true;
 for(const reason of ['owner-death','world']){
   A.reverseFixture();r=A.reverse;A.reverseStep(.8);A.assert(G.NarutoLee.active?.phase==='combo','abort fixture missing long combo');const world=G.World;
   if(reason==='owner-death')p.dead=true;else G.World={...world};A.reverseStep(.01);
   A.assert(!G.NarutoLee.active&&!G.NarutoLee.liftFor(r.primary)&&r.side.every(e=>r.counts.get(e)===0),'invalid-owner/world chain still landed '+reason);
   G.World=world;p.dead=false;p.hp=p.maxHp;
 }out.ownerWorldAbort=true;
 A.leeArena();const e=A.spawn(35,0);e.startJump(p);e.updateJump(.55);p.target=e;A.actualCast('naruto-reverse-lotus');
 for(let n=0;n<200&&G.NarutoLee.active?.phase!=='combo';n++)A.reverseStep(.01);
 A.assert(G.NarutoLee.active?.phase==='combo','combo phase fixture never reached');
 const native=e.jumpLift;A.assert(native>0&&G.NarutoLee.liftFor(e)>0,'native jump coexistence fixture missing');
 A.reverseStep(.05);A.assert(e.jumpLift===native,'reverse overwrote native jump');G.Combat.clearFields(p);
 A.assert(e.jumpLift===native&&!G.NarutoLee.liftFor(e),'cancel destroyed native jump');out.nativeJump=true;
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
                page.evaluate('() => G.Sprites.preload([19])')
                page.evaluate("() => {if(!G.Sprites.sheet(19,'Idle').ready)throw Error('real enemy artwork did not load')}")
                page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(AUDIT);page.evaluate(HELPERS)
                result={'levels':[]};report['viewports'][label]=result
                for level in range(1,6):
                    evidence=page.evaluate(LEVEL,level)
                    for phase in ('air','landing'):
                        (OUT/f'{label}-lv{level}-{phase}.png').write_bytes(base64.b64decode(evidence[phase].pop('png').split(',',1)[1]))
                    result['levels'].append(evidence)
                result['regressions']=page.evaluate(REGRESSIONS);ctx.close()
            browser.close()
        assert not report['errors'],report['errors'];assert not report['failedRequests'],report['failedRequests'];report['ok']=True
    except Exception as error:report['ok']=False;report['failure']=str(error);raise
    finally:(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'poses':20,'evidence':str(OUT)},ensure_ascii=False))

if __name__=='__main__':main()
