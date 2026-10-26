"""Native Leaf Whirlwind timing, quantity, movement, art and cleanup acceptance.

Requires the repository HTTP server on port 8004. Static enemy positions isolate
hit arithmetic; enemy hurt, player cast, collision checks and damage stay native.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/lee-whirlwind'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=lee&layout=wide'

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),D=G.DigimonSkills,assert=A.assert;
 const near=(a,b)=>Math.abs(a-b)<Math.max(1,Math.abs(b))*1e-8;
 const damage=[37,44.4,44.4,44.4,55.5],cooldown=[2,2,1.8,1.8,1.8];
 assert(typeof D.whirlwindFor==='function','native whirlwind API missing');
 p.level=12;p.addMove('naruto-lotus');
 const levels=damage.map((d,i)=>{
   const m=G.Moves.instance('naruto-lee',i+1);
   assert(near(m.dmg,d)&&near(m.cd,cooldown[i]),'existing whirlwind balance changed at level '+(i+1));
   assert(near(m.arc,3.9)&&m.knock===95,'existing arc or knock changed');
   return {level:i+1,damage:m.dmg,cooldown:m.cd,radius:m.radius};
 });
 function fixture(level=1,gates=false,quantity=0,cdMul=1){
   A.leeArena();p.quantityPicks=p.quantityBonus=quantity;p.cdMul=cdMul;
   p.moves=p.moves.filter(m=>m.id!=='naruto-gates');if(gates)p.addMove('naruto-gates');
   const m=A.select('naruto-lee');Object.assign(m,G.Moves.instance(m.id,level));
   const primary=A.spawn(70,0),inside=[primary,...[-1.05,1.05].map(a=>A.spawn(20+Math.cos(a)*48,Math.sin(a)*48))];
   const behind=A.spawn(-30,0),outside=A.spawn(20+m.radius+40,0),ledger=[];
   for(const enemy of [...inside,behind,outside]){
     const hurt=enemy.hurt;
     enemy.hurt=function(...args){const f=D.whirlwindFor(p),pose=G.AnimationLab.stateFor(p.anim);
       ledger.push({enemy,damage:args[0],knock:args[4],owned:args[6]===p,id:args[7],time:f?.t,frame:pose.frame,key:pose.key,x:p.x,y:p.y});
       return hurt.apply(this,args);
     };
   }
   p.target=primary;p.aim=0;return {m,primary,inside,behind,outside,ledger};
 }
 function advance(dt){A.resume();try{G.Combat.updateFields(dt);p.anim.update(dt);G.FX.update(dt)}finally{A.pause()}}
 const cases=[];
 for(const [level,gates,quantity,dt,cdMul]of [[1,false,0,1/120,1],[5,true,0,1/120,1],[1,false,4,1/60,1],[5,true,20,4,1],[1,false,0,1/120,.05]]){
   const r=fixture(level,gates,quantity,cdMul),credit=p.dmgDealt,atk=p.atk;
   A.actualCast('naruto-lee');const f=D.whirlwindFor(p),scale=G.Camera.scale,frames=new Set(),phases=new Set();
   assert(f,'native Combat.tick did not create whirlwind');
   assert(near(r.m.t,Math.max(.05,r.m.cd*cdMul)),'native cooldown changed');
   assert(f.life<=r.m.t&&f.life<=.72,'animation blocks the next ready cast');
   assert(f.nextHit===0&&r.ledger.length===0,'attack damaged before the kick');
   const count=Math.floor(1.25**quantity),expectedKey=gates?'lee-opened-whirlwind-air':'lee-whirlwind-air';
   const spec=AnimationAssets.get(expectedKey);
   assert(spec?.image&&spec.frames.length===8,'authored eight-frame atlas not loaded: '+expectedKey);
   const before=f.t;G.Combat.updateFields(.2);assert(f.t===before,'pause advanced whirlwind');
   let maxLift=0,steps=0;
   for(;steps<1000&&D.whirlwindFor(p);steps++){
     G.Camera.kick(.4);G.Camera.follow(p.x+80,p.y-80,dt);
     assert(G.Camera.x===f.camera.x&&G.Camera.y===f.camera.y&&G.Camera.scale===scale&&G.Camera.shake===0&&G.Camera._sx===0&&G.Camera._sy===0,'camera moved or shook during whirlwind');
     advance(dt);const current=D.whirlwindFor(p);if(!current)break;
     frames.add(current.frame);phases.add(current.phase);maxLift=Math.max(maxLift,current.visualLift);
     assert(p.invuln===0&&!G.NarutoLee.isInvulnerable(p),'whirlwind granted invulnerability');
     if(current.t<current.hitTimes[0]-1e-9)assert(r.ledger.length===0,'damage preceded heel contact');
     const pose=G.AnimationLab.stateFor(p.anim);assert(pose.key===expectedKey&&pose.frame===current.frame,'native action pose is out of sync');
     const canvas=document.createElement('canvas');canvas.width=400;canvas.height=300;
     const ctx=canvas.getContext('2d');ctx.translate(160,200);p.draw(ctx);G.Combat.drawAirFields(ctx);
     assert(ctx.globalAlpha===1&&ctx.getTransform().a===1,'whirlwind drawing leaked context state');
   }
   assert(!D.whirlwindFor(p)&&f.nextHit===count,'cast truncated or retained scheduled hits');
   assert(f.travelled>0&&f.travelled<=20.000001&&near(p.x,f.travelled)&&near(p.y,0),'advance was not a bounded forward step');
   assert(r.inside.every(e=>r.ledger.filter(h=>h.enemy===e).length===count),'front cone lost or duplicated hits');
   assert(!r.ledger.some(h=>h.enemy===r.behind||h.enemy===r.outside),'back gap or outer radius damaged');
   const base=r.m.dmg*atk*G.Types.mult(r.m.type,r.primary.types)*G.Weather.mult(r.m.type);
   assert(r.ledger.every(h=>h.owned&&h.id==='naruto-lee'&&h.knock===95&&near(h.damage,base)),'damage ownership, amount or knock changed');
   assert(r.ledger.every(h=>h.frame===5&&h.key===expectedKey),'true hit did not use authored contact frame');
   assert(r.ledger.every(h=>h.time>=.38*f.life/.72-1e-9&&h.time<=.46*f.life/.72+1e-9),'hit time left the strike phase');
   assert(near(p.dmgDealt-credit,base*3*count),'damage credit multiplied quantity incorrectly');
   assert(r.inside.every(e=>100000-e.hp===Math.round(base)*count),'native HP loss differs from displayed hits');
   if(dt<.01&&cdMul===1){assert(frames.size===8&&maxLift>31,'airborne sequence is missing authored frames or elevation')}
   const camera={x:G.Camera.x,y:G.Camera.y};G.Camera.follow(camera.x+80,camera.y+80,.1);
   assert(G.Camera.x>camera.x&&G.Camera.y>camera.y,'camera follow did not resume');
   cases.push({level,gates,quantity,dt,cdMul,life:f.life,hits:r.ledger.length,hitsPerTarget:count,travel:f.travelled,frames:[...frames],phases:[...phases],maxLift});
 }
 const wall=fixture();G.World.isFree=x=>x<8;G.World.isWall=x=>x>=8;
 A.actualCast('naruto-lee');advance(1);
 assert(p.x<8&&wall.ledger.length===0&&!D.whirlwindFor(p),'wall failed to stop swept advance or damage');
 const cancel=fixture();A.actualCast('naruto-lee');advance(.2);
 assert(D.whirlwindFor(p),'cancel fixture finished too early');
 A.select('naruto-lotus');advance(1);
 assert(!D.whirlwindFor(p)&&cancel.ledger.length===0,'switch retained the pending kick');
 const death=fixture();A.actualCast('naruto-lee');advance(.2);p.dead=true;p.hp=0;advance(1);
 assert(!D.whirlwindFor(p)&&death.ledger.length===0,'death retained the pending kick');
 const cleared=fixture();p.jumpLift=7;A.actualCast('naruto-lee');advance(.2);G.Combat.clearFields(p);
 assert(!D.whirlwindFor(p)&&cleared.ledger.length===0&&p.jumpLift===7,'clear retained an action or overwrote native jump height');
 const world=fixture();A.actualCast('naruto-lee');advance(.2);const originalWorld=G.World;
 G.World={...originalWorld};advance(1);G.World=originalWorld;
 assert(!D.whirlwindFor(p)&&world.ledger.length===0,'world change retained the pending kick');
 return {levels,cases,cleanup:{wall:true,switch:true,death:true,clear:true,world:true,nativeJumpPreserved:true}};
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
            page.wait_for_function("window.G?.DigimonSkills?.whirlwindFor&&document.querySelector('#boot').classList.contains('hidden')")
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
    print(json.dumps({'ok': True, 'viewports': list(report['viewports']), 'casesPerViewport': len(report['viewports']['desktop']['cases']), 'evidence': str(OUT / 'regression.json')}))


if __name__ == '__main__':
    main()
