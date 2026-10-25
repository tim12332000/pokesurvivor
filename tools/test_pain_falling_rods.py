"""Falling black receivers: timed ground impacts, distribution and lifecycle."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame
from test_ninja_tool_bounce import SETUP, PAIN

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-falling-rods'
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out={};
 function fresh(count=1){A.bounceReset();const m=G.Moves.instance('naruto-pain',1);m.cd=999;m.quantityBaseCount=count;p.moves=[m];return m}
 fresh();let e=A.spawn(180,0),hp=e.hp;A.advance();let shot=P.shots.find(s=>s.kind==='rod');
 A.assert(shot?.phase==='fall'&&shot.x===e.x&&shot.y===e.y&&shot.lift>170,'rod did not originate above fixed landing point');
 const lift=shot.lift;A.finish(.15);A.assert(shot.x===180&&shot.y===0&&shot.lift<lift&&shot.lift>0&&e.hp===hp,'rod moved on ground or hit while airborne');
 const age=shot.age;G.Combat.updateFields(1);A.assert(shot.age===age,'pause advanced falling rod');
 A.finish(.22);A.assert(e.hp<hp&&P.shots.length===0,'impact failed to cause a single real hit');
 const after=e.hp;A.finish(.4);A.assert(e.hp===after,'planted rod dealt damage repeatedly');out.timedSingleImpact=true;out.pause=true;
 fresh();e=A.spawn(180,0);A.advance();e.x=230;G.EnemyMgr.rebuildGrid();A.finish(.5);
 A.assert(e.hp===100000,'fixed landing point followed dodging enemy');out.dodge=true;
 fresh();e=A.spawn(180,0);const dead=e;A.advance();e.dead=true;e.hp=0;G.EnemyMgr.rebuildGrid();A.finish(.5);
 A.assert(dead.hp===0&&!P.shots.length,'dead target was hit or leaked');out.deadTarget=true;
 fresh(5);const inside=[A.spawn(-180,0),A.spawn(0,180),A.spawn(180,0)],outside=A.spawn(281,0),hits=A.watchBounce([...inside,outside]);
 A.advance();A.finish(.8);const counts=hits.map(h=>h.length);
 A.assert(JSON.stringify(counts.slice(0,3).sort())===JSON.stringify([1,2,2])&&counts[3]===0,'volley did not distribute over range '+counts);out.distribution=counts;
 fresh();e=A.spawn(180,0);const block=G.World.projectileBlock;G.World.projectileBlock=x=>x>=80&&x<=90?{destructible:false}:false;
 try{A.advance();A.finish(.5);A.assert(!P.shots.length&&e.hp===100000,'selected target through solid cover')}finally{G.World.projectileBlock=block}out.cover=true;
 fresh();e=A.spawn(180,0);A.advance();const wall=G.World.isWall;G.World.isWall=x=>x===180;
 try{A.finish(.5);A.assert(e.hp===100000&&!P.shots.length,'landed inside new wall')}finally{G.World.isWall=wall}out.newWall=true;
 for(const reason of ['clear','death','world']){
  fresh();e=A.spawn(180,0);A.advance();const world=G.World;
  try{if(reason==='clear')G.Combat.clearFields();else {if(reason==='death'){p.dead=true;p.hp=0}else G.World={...world};A.resume();G.Combat.updateFields(.01);A.pause()}
   A.assert(!P.shots.length&&!P.effects.length,'falling rods survived '+reason);A.assert(e.hp===100000,'cancelled impact caused damage '+reason);
  }finally{G.World=world;p.dead=false;p.hp=p.maxHp}
 }out.cleanup=true;
 out.counts=[];
 for(let lvl=1;lvl<=5;lvl++){
  A.bounceReset();const m=G.Moves.instance('naruto-pain',lvl);m.cd=999;p.moves=[m];e=A.spawn(180,0);const hs=A.watchBounce([e]);A.advance();A.finish(.8);
  A.assert(hs[0].length===[5,5,6,7,8][lvl-1],'rank count changed '+lvl);out.counts.push(hs[0].length);
 }
 A.bounceReset();const capped=G.Moves.instance('naruto-pain',5);capped.cd=999;p.moves=[capped];p.quantityPicks=p.quantityBonus=15;
 e=A.spawn(180,0);const cappedHits=A.watchBounce([e]);A.advance();A.finish(.8);
 A.assert(cappedHits[0].length===40,'quantity cap or damage-bearing rod count changed');out.quantityCap=40;
 A.bounceReset();return out;
}"""
VISUAL = r"""() => {
 const A=Acceptance,p=A.p();A.bounceReset();const m=G.Moves.instance('naruto-pain',1);m.cd=999;p.moves=[m];
 window.fallEnemies=[A.spawn(-125,65),A.spawn(30,115),A.spawn(170,30)];A.advance();A.finish(.22);
}"""
CAPTURE = r"""() => {
 const c=document.createElement('canvas');c.width=800;c.height=620;const ctx=c.getContext('2d');
 ctx.fillStyle='#253c28';ctx.fillRect(0,0,c.width,c.height);ctx.translate(360,330);ctx.imageSmoothingEnabled=false;
 const before=JSON.stringify(G.NarutoPain.shots.map(p=>[p.x,p.y,p.age,p.lift]));
 G.Combat.drawGroundFields(ctx);for(const e of fallEnemies)e.draw(ctx);Acceptance.p().draw(ctx);
 for(const b of G.NarutoPain.actorsFor(Acceptance.p()))b.draw(ctx);G.Combat.drawAirFields(ctx);
 Acceptance.assert(before===JSON.stringify(G.NarutoPain.shots.map(p=>[p.x,p.y,p.age,p.lift])),'drawing mutated falling shots');return c.toDataURL();
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'viewports': {}, 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, vp in [('desktop', {'width': 1200, 'height': 900}), ('mobile', {'width': 390, 'height': 844})]:
            page = browser.new_page(viewport=vp, is_mobile=label == 'mobile', has_touch=label == 'mobile', service_workers='block')
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL)
            frame = game_frame(page)
            frame.wait_for_function("window.PS_REDRAWN_READY&&G.NarutoPain&&document.getElementById('boot').classList.contains('hidden')")
            if frame.locator('#tap-start').is_visible():
                frame.locator('#tap-start').click()
            frame.locator('[data-quick-naruto="30010"]').click()
            enter(frame)
            frame.evaluate(SETUP)
            result = report['viewports'][label] = {'falling': frame.evaluate(CHECK), 'bounce': frame.evaluate(PAIN)}
            frame.evaluate(VISUAL)
            for phase, advance in [('fall', 0), ('impact', .16), ('settled', .25)]:
                if advance:
                    frame.evaluate('(dt)=>Acceptance.finish(dt)', advance)
                image = frame.evaluate(CAPTURE)
                (OUT / f'{label}-{phase}.png').write_bytes(base64.b64decode(image.split(',', 1)[1]))
                if phase == 'fall':
                    page.screenshot(path=str(OUT / f'{label}-game.png'))
            page.close()
            print(label + ' falling rods and additive ricochets PASS', flush=True)
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), 'utf-8')
    print('Falling rods PASS')


if __name__ == '__main__':
    main()
