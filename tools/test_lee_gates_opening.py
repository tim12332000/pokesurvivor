"""Real learning/upgrade charge, AOE damage and cancellation."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

OUT = Path(__file__).resolve().parents[1] / '.omx/state/lee-gates-opening'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=lee&layout=wide&test=gates-opening'
TEST = r"""() => {
 const A=Acceptance,p=A.p(),g=G.NarutoGates;A.leeArena();p.level=4;
 const learn=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-gates');
 A.assert(learn&&learn.apply(p)!==false,'learning card missing');
 const out={stages:[]};p.addMove('naruto-lee-pursuit');
 A.openingCapture=()=>{const c=document.createElement('canvas');c.width=520;c.height=620;
   const ctx=c.getContext('2d');ctx.fillStyle='#17251d';ctx.fillRect(0,0,520,620);ctx.translate(260-p.x,420-p.y);
   G.Combat.drawGroundFields(ctx);p.draw(ctx);G.Combat.drawAirFields(ctx);return c.toDataURL()};
 for(let level=1;level<=3;level++){
   A.assert(g.stage(p)===level&&g.charging(p),'charge missing at stage '+level);
   const foes=[[65,0],[-80,0],[0,1000],[1001,0]].map(([x,y])=>A.spawn(x,y));
   foes.push(A.spawn(0,-90,true),A.spawn(-100,-50),A.spawn(100,-50));foes[1].elite=true;
   foes[5].legend=true;foes[6].judge=true;
   foes.forEach(e=>e.hp=e.maxHp*.8);
   p.percentHealthDamage=.25;p.critChance=1;
   const hp=foes.map(e=>e.hp),pos=[p.x,p.y],damage=p.dmgDealt;
   const tick=dt=>{A.resume();try{p.update(dt);G.Combat.tick(dt,p,0);G.Combat.updateFields(dt)}finally{A.pause()}};
   tick(.3);
   A.assert(G.AnimationLab.stateFor(p.anim).frame===0,'opening skipped preparation pose');
   tick(.7);
   A.assert(g.openingFor(p).age===1,'charge timer mismatch');
   const pose=()=>G.AnimationLab.stateFor(p.anim);
   A.assert(pose().id==='naruto-gates'&&pose().key===(level===3?'lee-death-gates':'lee-opened-gates')&&pose().frame===1,'charge pose did not stay synchronized');
   const pausedAge=g.openingFor(p).age;G.Combat.updateFields(1);
   A.assert(g.openingFor(p).age===pausedAge,'pause advanced charge');
   A.assert(p.addMove('naruto-gates')===false&&g.openingFor(p).age===pausedAge,'duplicate retriggered opening');
   tick(2.99);
   A.assert(p.x===pos[0]&&p.y===pos[1]&&!p.walking,'charge allowed movement');
   A.assert(foes.every((e,i)=>e.hp===hp[i])&&p.dmgDealt===damage,'damage before four seconds');
   const charging=A.openingCapture();tick(.01);
   A.assert(!g.charging(p),'charge did not end at four seconds');
   A.assert(pose().id==='naruto-gates'&&pose().frame===2,'burst did not use shouting pose');
   const groundCanvas=document.createElement('canvas'),groundCtx=groundCanvas.getContext('2d'),rings=[];
   const ellipse=groundCtx.ellipse.bind(groundCtx),arc=groundCtx.arc.bind(groundCtx);
   groundCtx.ellipse=(x,y,rx,ry,...args)=>{if(rx>30)rings.push({x,y,rx,ry});return ellipse(x,y,rx,ry,...args)};
   groundCtx.arc=(x,y,r,...args)=>{A.assert(r<=30,'burst used a face-on circle');return arc(x,y,r,...args)};
   G.Combat.drawGroundFields(groundCtx);
   A.assert(rings.length===3&&rings.every(r=>r.x===pos[0]&&r.y===pos[1]&&r.ry/r.rx<=.5),'shockwave did not use foot-centered ground perspective');
   A.assert(foes.every((e,i)=>e.hp===hp[i]),'AOE hit before performance ended');
   const burst=A.openingCapture();
   A.advance(.02);A.assert(foes.every((e,i)=>e.hp===hp[i]),'AOE hit during performance');
   A.resume();p.update(.02);A.pause();
   A.assert(p.x===pos[0]&&p.y===pos[1],'burst pose slid during the performance');
   A.advance(.58);A.assert(pose().id==='naruto-gates'&&pose().frame===3,'recovery pose did not follow burst');
   A.advance(.39);A.assert(g.openingFor(p),'burst ended before five seconds');
   A.assert(foes.every((e,i)=>e.hp===hp[i]),'AOE hit before five seconds');
   A.advance(.02);A.assert(!g.openingFor(p),'opening survived five seconds');
   const after=foes.map(e=>e.hp);
   A.assert(foes.slice(0,3).every((e,i)=>hp[i]-e.hp===Math.round(e.maxHp*.3)),'normal/elite damage was not exactly 30% maximum HP');
   A.assert(foes[3].hp===hp[3],'AOE exceeded radius');
   A.assert(foes.slice(4).every((e,i)=>hp[i+4]-e.hp===Math.round(e.maxHp*.1)),'boss/legend/judge damage was not exactly 10% maximum HP');
   A.advance(.02);
   A.assert(foes.every((e,i)=>e.hp===after[i]),'performance allowed extra attacks or repeated burst damage');
   A.assert(pose().id!=='naruto-gates','opening pose leaked after five seconds');
   A.resume();p.update(.02);A.pause();A.assert(p.x>pos[0],'movement did not resume');
   out.stages.push({level,before:hp,after,charging,burst});A.leeArena();
   if(level<3){p.level=[4,8,16][level];const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:naruto-gates');
     A.assert(card&&card.apply(p)!==false,'upgrade card missing');}
 }
 for(const reason of ['clear','death','world']){
   A.leeArena();const move=p.moves.find(m=>m.id==='naruto-gates');move.lvl=1;G.Moves.levelUp(move);
   A.assert(g.charging(p),'cancel fixture missing');const e=A.spawn(50,0),hp=e.hp;
   if(reason==='clear')G.Combat.clearFields(p);
   if(reason==='death')p.dead=true;
   const world=G.World;if(reason==='world')G.World={...world};
   A.assert(!g.charging(p),'cancel retained lock '+reason);
   A.advance(6);G.World=world;p.dead=false;
   A.assert(e.hp===hp&&!g.openingFor(p),'canceled burst survived '+reason);
 }
 return out;
}"""

HEAL = r"""() => {
 const A=Acceptance,p=A.p(),g=G.NarutoGates,near=(a,b)=>Math.abs(a-b)<1e-7;
 const start=()=>{A.leeArena();const m=p.moves.find(m=>m.id==='naruto-gates');m.lvl=1;G.Moves.levelUp(m);
   p.maxHp=20000;p.hp=100;A.assert(g.healingMultiplier(p)>1,'healing multiplier fixture missing')};
 // Missing HP from before the opening is never repaid by the opening refund.
 start();A.advance(.25);A.assert(near(p.hp,100),'uninjured opening granted free HP');
 const hit=(amount,pure=false)=>{p.invuln=0;p.hurt(amount,null,pure)};
 hit(40,true);A.assert(near(p.hp,100),'actual damage was not refunded exactly');
 hit(70);A.assert(near(p.hp,100),'mitigated damage refund amplified healing');
 p.invuln=1;const before=p.hp;p.hurt(90,null,true);
 A.assert(p.hp===before,'blocked hit created extra HP');
 const paused=p.hp;G.Combat.updateFields(1);A.assert(p.hp===paused,'paused opening healed');
 A.resume();for(const dt of [0,-1,Infinity,NaN])g.update(dt);A.pause();
 A.assert(p.hp===paused,'invalid delta healed');
 A.advance(3.75);hit(30,true);A.assert(near(p.hp,100),'burst interval failed exact refund');
 A.advance(.99);hit(20,true);A.assert(near(p.hp,100),'last opening interval failed refund');
 A.advance(.01);A.assert(!g.openingFor(p),'opening survived five seconds');
 hit(20,true);A.assert(near(p.hp,80),'damage after five seconds was refunded');
 A.advance(1);A.assert(near(p.hp,80),'opening healing leaked after five seconds');
 start();A.advance(19);A.assert(near(p.hp,100),'large delta granted free healing');
 start();p.hp=p.maxHp-10;hit(50,true);A.assert(near(p.hp,p.maxHp-10),'refund filled preexisting missing HP');
 start();hit(200,true);A.assert(p.dead&&p.hp===0,'refund resurrected a lethal hit');p.dead=false;
 for(const reason of ['clear','death','world']){
   start();const hp=p.hp,world=G.World;
   if(reason==='clear')G.Combat.clearFields(p);
   if(reason==='death')p.dead=true;
   if(reason==='world')G.World={...world};
   A.advance(2);G.World=world;p.dead=false;
   A.assert(p.hp===hp&&!g.openingFor(p),'opening heal survived '+reason);
 }
 A.leeArena();return {actualDamageRefund:true,noFreeHealing:true,seconds:5,pause:true,cap:true,cancellation:true};
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in (False, True):
            label = 'mobile' if mobile else 'desktop'
            ctx = browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = ctx.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY&&G.NarutoGates&&document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30006"]').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
            page.evaluate(HARNESS)
            page.evaluate(SETUP)
            page.keyboard.down('KeyD')
            result = page.evaluate(TEST)
            result['healing'] = page.evaluate(HEAL)
            page.keyboard.up('KeyD')
            for stage in result['stages']:
                for phase in ('charging', 'burst'):
                    (OUT / f'{label}-stage{stage["level"]}-{phase}.png').write_bytes(base64.b64decode(stage.pop(phase).split(',')[1]))
            report['viewports'][label] = result
            ctx.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'viewports': list(report['viewports']), 'evidence': str(OUT)}))

if __name__ == '__main__':
    main()
