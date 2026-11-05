"""Moving-body shatters and one genuine, source-aware Uro counter.

--baseline records the old-origin defect before runtime edits. No claim about
human enjoyment follows from these deterministic native combat fixtures.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('URO_FEEL_OUT', str(ROOT / '.omx/state/feel-v4/uro')))

MOVEMENT = r"""baseline => {
 const A=JAcceptance,p=A.p(),U=G.JjkUro,out={};
 for(const [id,release,offset] of [['jjk-uro',.18,200],['jjk-uro-thin-ice',.34,400]]){
  A.reset();const m=A.fixture(id),old=A.spawn(70,0);A.cast(id);
  const action=U.activeFor(p),aim=action.aim;p.y=offset;
  const victims=[A.spawn(70,offset),A.spawn(80,offset+15),A.spawn(85,offset-15)],outside=A.spawn(-80,offset);
  A.advance(release-.02);const before={origin:[action.x,action.y],hp:victims.map(e=>e.hp)};
  A.assert(victims.every(e=>e.hp===e.maxHp),'body hit before contact');
  A.advance(.03);const at={origin:[action.x,action.y],old:old.maxHp-old.hp,inside:victims.map(e=>e.maxHp-e.hp),outside:outside.maxHp-outside.hp,aim:action.aim};
  if(!baseline){
   A.assert(at.old===0&&at.inside.every(n=>n>0)&&at.outside===0,'moving body left damage at old origin '+id+' '+JSON.stringify(at));
   A.assert(action.aim===aim,'body silently retargeted while moving');
   const origin=[action.x,action.y];p.y+=100;A.advance(.08);
   A.assert(action.x===origin[0]&&action.y===origin[1],'released shatter followed owner during recovery');
  }
  out[id]={before,at};
 }
 A.reset();const m=A.fixture('jjk-uro-collapse'),e=A.spawn(200,0);A.cast(m.id);
 const action=U.activeFor(p),locked=[action.tx,action.ty];p.y=400;A.advance(.56);
 A.assert(action.tx===locked[0]&&action.ty===locked[1]&&e.hp<e.maxHp,'remote collapse moved with caster');
 out.collapse={locked,damage:e.maxHp-e.hp};
 return out;
}"""

COUNTER = r"""() => {
 const A=JAcceptance,p=A.p(),U=G.JjkUro,assert=A.assert,out={};
 const incoming=(extra={})=>G.Projectiles.spawn({x:0,y:70,px:0,py:120,vx:0,vy:-200,r:6,life:2,dmg:7,mtype:'psychic',friendly:false,...extra});
 function setup(){
  A.reset();const shield=A.fixture('jjk-uro-screen',3);assert(p.addMove('jjk-uro-thin-ice'),'learn thin');
  const thin=p.moves.find(m=>m.id==='jjk-uro-thin-ice'),near=A.spawn(70,0),shooter=A.spawn(0,200);
  incoming({x:0,y:170});A.cast(shield.id);G.Projectiles.clear();thin.t=4;
  return {shield,thin,near,shooter,s:U.stateFor(p)};
 }
 function reflect(extra){const shot=incoming(extra);A.resume();try{U.intercept()}finally{A.pause()};assert(!G.Projectiles.all().includes(shot),'no real reflection');}
 function castThin(r){A.advance(.43);A.resume();try{assert(U.cast(p,r.thin),'counter did not cast')}finally{A.pause()};return U.activeFor(p);}
 let r=setup();reflect({sourceEnemy:r.shooter});const deadline=r.s.counterUntil;
 assert(r.s.counterTarget===r.shooter&&r.thin.t===0,'known source was not retained');
 const reply=castThin(r);assert(Math.abs(reply.aim-Math.PI/2)<1e-8&&reply.riposte,'counter ignored actual shooter');
 assert(r.s.counterTarget===null&&r.s.counterUntil===0,'counter target not consumed');A.advance(.35);
 assert(r.shooter.hp<r.shooter.maxHp&&r.near.hp===r.near.maxHp,'counter hit nearest decoy rather than source');
 r.thin.t=2;reflect({sourceEnemy:r.near});assert(r.thin.t===2&&r.s.counterUntil===0,'same pane armed another counter');
 out.knownSource={aim:reply.aim,sourceDamage:r.shooter.maxHp-r.shooter.hp,decoyDamage:r.near.maxHp-r.near.hp,deadline};
 for(const invalid of ['unknown','dead','range','wall','removed']){
  r=setup();reflect(invalid==='unknown'?{}:{sourceEnemy:r.shooter});
  if(invalid==='dead'){r.shooter.dead=true;r.shooter.hp=0}
  if(invalid==='range')r.shooter.y=600;
  if(invalid==='wall')G.World.projectilePathClear=(x,y,tx,ty)=>ty<100;
  if(invalid==='removed'){G.EnemyMgr.clear();G.EnemyMgr.add(r.near);G.EnemyMgr.rebuildGrid()}
  const f=castThin(r);assert(Math.abs(f.aim)<1e-8&&f.riposte,'invalid source did not fall back '+invalid);
  out[invalid]={aim:f.aim,fallback:true};
 }
 r=setup();reflect({sourceEnemy:r.shooter});const age=r.s.clock,expiry=r.s.counterUntil;U.update(4);
 assert(r.s.clock===age&&r.s.counterUntil===expiry&&r.s.counterTarget===r.shooter,'pause spent source counter');
 A.advance(3.01);assert(r.s.counterTarget===null&&r.s.counterUntil===0,'expired counter retained source');out.expiry=true;
 r=setup();reflect({sourceEnemy:r.shooter});G.Combat.clearFields(p);assert(!U.stateFor(p),'owner clear retained counter');out.clear=true;
 // Enemy.shoot is the production source producer; do not rely only on fixture fields.
 r=setup();G.Projectiles.clear();r.shooter.shoot(0,-1);
 assert(G.Projectiles.all().some(shot=>shot.sourceEnemy===r.shooter),'native enemy shot omitted sourceEnemy');out.nativeSource=true;
 return out;
}"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    out = OUT / ('before' if args.baseline else 'after')
    out.mkdir(parents=True, exist_ok=True)
    base.OUT = out
    base.URL = os.environ.get('JUJUTSU_URL', 'http://127.0.0.1:8341/.omx/digimon.html?lang=zh-TW')
    report = {'baseline': args.baseline, 'cases': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        for mobile in [False, True]:
            label = 'mobile' if mobile else 'desktop'
            context = browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1100,'height':850}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            frame = base.boot(page, 30015, label)
            result = {'movement': frame.evaluate(MOVEMENT, args.baseline)}
            if not args.baseline:
                result['counter'] = frame.evaluate(COUNTER)
            assert not errors, errors
            page.screenshot(path=str(out / f'{label}-contact.png'))
            report['cases'][label] = result
            context.close()
        browser.close()
    (out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({'ok': True, 'baseline': args.baseline, 'evidence': str(out)}))


if __name__ == '__main__':
    main()
