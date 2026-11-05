"""Yuta moving-body contact and bounded same-target Rika pursuit.

--baseline records the old behavior without expecting the fixes. Controlled
positions isolate contact geometry; this is not a subjective enjoyment score.
"""
import argparse
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('YUTA_FEEL_OUT', str(ROOT / '.omx/state/feel-v4/yuta')))

CHECK = r"""baseline => {
 const A=JAcceptance,Y=G.JujutsuYuta,p=A.p(),out={};
 function setup(id){A.reset();return A.fixture(id);}
 function cast(m){A.resume();try{A.assert(Y.cast(p,m),'cast failed '+m.id)}finally{A.pause()}}
 for(const [kind,id,release] of [['blade','jjk-yuta',.14],['speech','jjk-yuta-speech',.24]]){
   const m=setup(id),old=A.spawn(100,0),fresh=A.spawn(400,0),behind=A.spawn(210,0);
   cast(m);const aim=Y.stateFor(p).action.aim;
   A.advance(.05);p.x=300;p.aim=Math.PI;G.EnemyMgr.rebuildGrid();
   A.advance(release-.05+.01);
   const f=Y.stateFor(p).action,mark=Y.stateFor(p).marks.at(-1);
   const result={oldLoss:old.maxHp-old.hp,newLoss:fresh.maxHp-fresh.hp,behindLoss:behind.maxHp-behind.hp,
     x:f.x,y:f.y,aim:f.aim,markX:mark.x,cd:m.t,range:f.range,radius:f.radius};
   if(!baseline){A.assert(result.oldLoss===0&&result.newLoss>0,kind+' hit cast origin instead of release origin');
     A.assert(f.aim===aim&&f.x===300&&f.y===0,kind+' lost locked aim or release body origin');
     if(kind==='blade')A.assert(result.behindLoss===0,'blade became all-direction auto aim');
     p.x=500;A.advance(.05);A.assert(mark.x===300&&f.x===300,'released contact moved with player');
   }
   out[kind]=result;
 }
 // A moving strong target keeps its identity until Rika starts winding up.
 let m=setup('jjk-yuta-rika'),boss=A.spawn(230,0,'boss');boss.r=14;cast(m);
 const r=Y.stateFor(p).rika,steps=[];
 for(let i=0;i<60&&r.phase==='travel';i++){
   boss.y+=3;G.EnemyMgr.rebuildGrid();A.advance(.01);
   steps.push({time:r.age,x:r.x,y:r.y,tx:r.tx,ty:r.ty,targetY:boss.y,phase:r.phase,aim:r.aim});
 }
 const locked={x:r.x,y:r.y,tx:r.tx,ty:r.ty,aim:r.aim,phase:r.phase};
 if(!baseline){A.assert(r.phase==='strike'&&r.y>20,'Rika did not pursue the moving strong target');
   A.assert(r.travelDistance<=r.travelBudget+.001&&r.age<=1.41,'Rika exceeded pursuit budget');}
 boss.x+=50;boss.y+=30;G.EnemyMgr.rebuildGrid();A.advance(.23);
 if(!baseline){A.assert(r.x===locked.x&&r.y===locked.y&&r.aim===locked.aim,'Rika homed after punch windup');
   A.assert(boss.hp<boss.maxHp,'bounded pursuit missed the controlled moving boss');}
 out.movingBoss={steps,locked,loss:boss.maxHp-boss.hp};
 if(baseline)return out;

 // The new multi-beat excursion can also approach the same ordinary enemy.
 m=setup('jjk-yuta-rika');let e=A.spawn(230,0);cast(m);let actor=Y.stateFor(p).rika;
 e.y=150;G.EnemyMgr.rebuildGrid();A.advance(.12);
 A.assert(actor.pursuitTarget===e&&actor.y>0,'ordinary combo failed its bounded same-target approach');out.ordinaryPursuit=true;

 // A blocked/dead target cannot be replaced by another target or hit through a wall.
 for(const mode of ['wall','dead','budget']){
   m=setup('jjk-yuta-rika');e=A.spawn(230,0,'boss');e.r=14;const spare=A.spawn(240,100,'boss');cast(m);actor=Y.stateFor(p).rika;
   if(mode==='wall'){G.World.projectileBlock=(x,y)=>x>=80&&x<=110?{hp:100}:false;G.World.isWall=(x,y)=>x>=80&&x<=110;}
   if(mode==='dead'){e.dead=true;e.hp=0;}
   let maximumDistance=0;
   for(let i=0;i<180&&Y.stateFor(p).rika;i++){
     if(mode==='budget'){e.x+=7;G.EnemyMgr.rebuildGrid();}
     A.advance(.01);maximumDistance=Math.max(maximumDistance,actor.travelDistance||0);
   }
   A.assert(spare.hp===spare.maxHp,'invalid pursuit changed target '+mode);
   if(mode==='wall')A.assert(e.hp===e.maxHp&&actor.x<80,'Rika crossed wall or hit through it');
   if(mode==='budget')A.assert(e.hp===e.maxHp&&maximumDistance<=actor.travelBudget+.001,'Rika chased outside budget');
   out[mode]={maximumDistance,budget:actor.travelBudget,phase:actor.phase};
 }

 m=setup('jjk-yuta-rika');e=A.spawn(230,0,'boss');cast(m);actor=Y.stateFor(p).rika;A.advance(.1);
 const frozen={age:actor.age,x:actor.x,y:actor.y,clock:Y.stateFor(p).clock};
 G.Combat.updateFields(.5);A.assert(actor.age===frozen.age&&actor.x===frozen.x&&Y.stateFor(p).clock===frozen.clock,'pause moved pursuit');
 G.Combat.clearFields(p);A.assert(!Y.stateFor(p)&&Y.drawables().length===0,'clear retained pursuit');
 m=setup('jjk-yuta-rika');e=A.spawn(230,0,'boss');cast(m);p.dead=true;p.hp=0;G.Combat.updateFields(.1);
 A.assert(!Y.stateFor(p)&&Y.drawables().length===0,'dead owner retained pursuit');out.lifecycle={pause:true,clear:true,death:true};
 return out;
}"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    out = OUT / ('before' if args.baseline else 'after')
    out.mkdir(parents=True, exist_ok=True)
    base.URL = os.environ.get('JUJUTSU_URL', 'http://127.0.0.1:8341/.omx/digimon.html?lang=zh-TW')
    base.OUT = out
    report = {'url': base.URL, 'baseline': args.baseline, 'cases': {}, 'errors': [], 'missing': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        for label, viewport, mobile in [('desktop', {'width': 1280, 'height': 900}, False),
                                         ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.on('response', lambda response: report['missing'].append(response.url) if response.status >= 400 else None)
            frame = base.boot(page, 30013, label)
            report['cases'][label] = frame.evaluate(CHECK, args.baseline)
            frame.evaluate('''() => {
              const A=JAcceptance,p=A.p();A.reset();const m=A.fixture('jjk-yuta');p.invuln=100;
              A.spawn(100,0);A.spawn(180,15);A.resume();
              try{A.assert(G.JujutsuYuta.cast(p,m),'visual blade cast')}finally{A.pause()}
              A.advance(.06);p.x=80;G.EnemyMgr.rebuildGrid();A.advance(.01);
            }''')
            for phase, advance in [('windup', 0), ('contact', .08), ('recovery', .12)]:
                if advance:
                    frame.evaluate('dt=>JAcceptance.advance(dt)', advance)
                page.wait_for_timeout(50)
                page.screenshot(path=str(out / f'{label}-moving-blade-{phase}.png'))
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    assert not report['missing'], report['missing']
    report['ok'] = True
    (out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'baseline': args.baseline, 'evidence': str(out)}))


if __name__ == '__main__':
    main()
