"""Front Lotus authored grip, inverted victim, real impact, and fixed camera."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

OUT = Path(__file__).resolve().parents[1] / '.omx/state/lee-front-lotus'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=lee&layout=wide'
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),L=G.NarutoLee,out=[];p.level=12;p.addMove('naruto-lotus');
 for(const [level,gates,boss,weak]of [[1,false,false,false],[5,true,false,false],[1,false,true,false],[1,false,false,true]]){
   A.leeArena();p.quantityPicks=p.quantityBonus=0;
   p.moves=p.moves.filter(m=>m.id!=='naruto-gates');if(gates)p.addMove('naruto-gates');
   const m=A.select('naruto-lotus');Object.assign(m,G.Moves.instance(m.id,level));
   const e=A.spawn(35,0,boss),side=[A.spawn(35,m.radius*.65),A.spawn(35,-m.radius*.65),A.spawn(35+m.radius*.65,0)],outside=A.spawn(35+m.radius+70,0);
   if(weak)e.hp=1;
   const ledger=[];for(const enemy of [e,...side,outside]){const hurt=enemy.hurt;enemy.hurt=function(...args){ledger.push({enemy,amount:args[0],phase:L.active?.phase});return hurt.apply(this,args)}}
   p.target=e;A.actualCast(m.id);const f=L.active,poses=new Set(),frames=new Set(),phases=new Set();let maxRotation=0,air=0,maxLift=0;
   A.assert(m.cd===10&&L.bindLimitOf(m,p)===3,'Front Lotus cooldown or pull count mismatch');
   for(let n=0;n<1500&&L.active;n++){
     G.Camera.follow(p.x,p.y,.005);A.advance(.005);G.FX.update(.005);if(!L.active)break;
     phases.add(f.phase);A.assert(!L.isInvulnerable(p),'Front Lotus gained reverse immunity');
     maxLift=Math.max(maxLift,f.visualLift);
     const pose=G.AnimationLab.stateFor(p.anim);poses.add(pose.key);
     if(['suspend','descent'].includes(f.phase)&&!boss){
       A.assert(pose.key===(gates?'lee-opened-lotus-hold':'lee-lotus-hold'),'authored grip atlas missing');frames.add(pose.frame);
       const asset=AnimationAssets.get(pose.key);A.assert(asset.image&&asset.frames[pose.frame].grip,'grip metadata not loaded');
       const target=L.victimPresentationFor(e);maxRotation=Math.max(maxRotation,target?.rotation||0);air++;
       A.assert(side.every(s=>!L.liftFor(s)),'Front Lotus lifted secondary targets');
       if(weak)A.assert(!e.dead&&L.pendingDefeat(e),'weak victim vanished before piledriver');
     }
     A.assert(side.every(s=>!ledger.some(h=>h.enemy===s&&h.phase!=='slam')),'splash hit before landing');
     if(boss)A.assert(!f.cameraLock,'ground boss incorrectly locked airborne camera');
     else if(!['approach','windup'].includes(f.phase))A.assert(f.cameraLock&&G.Camera.x===f.cameraLock.x&&G.Camera.y===f.cameraLock.y,'Front Lotus camera moved');
     const canvas=document.createElement('canvas');canvas.width=480;canvas.height=400;const ctx=canvas.getContext('2d');ctx.translate(220,260);
     G.Combat.drawGroundFields(ctx);[e,...side,outside].forEach(e=>e.draw(ctx));p.draw(ctx);G.Combat.drawAirFields(ctx);G.FX.draw(ctx);
     A.assert(ctx.globalAlpha===1&&ctx.getTransform().a===1,'piledriver drawing leaked transform');
   }
   const own=ledger.filter(h=>h.enemy===e),base=m.dmg*f.attack*G.Types.mult(m.type,e.types)*G.Weather.mult(m.type);
   A.assert(!L.active&&own.length===2,'Front Lotus changed hit count');
   A.assert(Math.abs(own[0].amount-base*.2)<1e-7&&own[0].phase==='lift','launch damage mismatch');
   A.assert(Math.abs(own[1].amount-base*.8)<1e-7&&own[1].phase==='slam','piledriver damage mismatch');
   A.assert(side.every(s=>ledger.filter(h=>h.enemy===s).length===1)&&!ledger.some(h=>h.enemy===outside),'landing AOE coverage changed');
   A.assert(!L.liftFor(e)&&!L.victimPresentationFor(e),'victim retained a piledriver pose');
   A.assert(f.age>=1.97&&f.age<2.7,'Front Lotus timing out of range');
   if(!boss){
     A.assert(frames.has(0)&&frames.has(1)&&frames.has(2)&&maxRotation>3,'grip-to-inverted pose sequence incomplete');
     A.assert(f.peakLift===240&&maxLift>140,'Front Lotus did not reach the higher apex');
   }
   if(weak)A.assert(e.dead&&!L.pendingDefeat(e),'weak victim not released at landing');
   out.push({level,gates,boss,weak,time:f.age,hits:own.length,poses:[...poses],frames:[...frames],maxRotation,maxLift,air});
 }
 A.leeArena();const e=A.spawn(35,0);e.hp=1;p.target=e;A.select('naruto-lotus');A.actualCast('naruto-lotus');A.advance(.9);L.clear(p);
 A.assert(!L.active&&!L.bound(e)&&!L.pendingDefeat(e)&&!L.liftFor(e),'cancel left a front hold behind');
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, mobile in [('desktop', False), ('mobile', True)]:
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1200, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(URL)
            page.wait_for_function("window.G?.NarutoLee&&document.querySelector('#boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
            page.evaluate('()=>G.Sprites.preload([19])')
            page.evaluate(HARNESS)
            page.evaluate(SETUP)
            report['viewports'][label] = page.evaluate(CHECK)
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    (OUT / 'regression.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, **report}))


if __name__ == '__main__':
    main()
