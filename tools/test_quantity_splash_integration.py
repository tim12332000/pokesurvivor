"""Focused normal-entry check for quantity cards and four Naruto splash sources."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_gaara import URL


CHECK = r"""dex => {
 G.Naruto.choose(dex);G.Flow.play();Acceptance.pause();Acceptance.arena();
 const A=Acceptance,p=G.Game.player,Q=G.Quantity,S=G.DamageSplash;
 const eligible=G.LevelUp.STATS.filter(s=>!s.max||(p.statsTaken[s.id]||0)<s.max);
 const candidates=G.LevelUp.offer(p,100);
 A.assert(eligible.every(s=>candidates.some(c=>c.key==='stat:'+s.id)),'eligible growth card excluded before draw');
 p.percentHealthDamage=0;p.lifestealRate=0;p.quantityPicks=0;
 const quantity=G.LevelUp.STATS.find(c=>c.id==='quantity');
 for(let i=0;i<3;i++)quantity.apply(p);
 A.assert(Q.count(p,8)===15&&Q.multiplier(p)===1.25**3,'normal-entry quantity card');
 const card=G.LevelUp.STATS.find(c=>c.id==='damageSplash');
 card.apply(p);card.apply(p);A.assert(Math.abs(S.rate(p)-.2)<1e-9,'splash card stacking');
 const spawn=(x,y)=>{
  const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
  e.types=['normal'];e.logs=[];const hurt=e.hurt;
  e.hurt=function(...args){e.logs.push({damage:args[0],secondary:S.isSecondary()});return hurt.apply(this,args)};
  G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;
 };
 const primary=spawn(80,0),neighbor=spawn(110,30);p.target=primary;p.aim=0;
 const original=S.hit,calls=[];
 S.hit=function(...args){calls.push({primary:args[1]===primary,direct:args[2]});return original.apply(this,args)};
 A.resume();
 try{
  const move=p.moves[0],snapshot=Q.snapshot(p,move);
  if(dex===30001){
   G.NarutoClones.cast(p,snapshot);
   G.NarutoClones.actors.forEach((a,i)=>{a.dead=i>0;a.x=70;a.y=0;a.cd=0;a.age=.3});
   for(let i=0;i<100&&!calls.length;i++)G.NarutoClones.update(.01);
  }else if(dex===30002){
   A.assert(G.NarutoChidori.cast(p,snapshot),'chidori cast');
   for(let i=0;i<200&&!calls.length;i++)G.NarutoChidori.update(.01);
  }else if(dex===30006){
   const lotus=G.Moves.instance('naruto-reverse-lotus');
   A.assert(G.NarutoLee.cast(p,Q.snapshot(p,lotus)),'lotus cast');
   for(let i=0;i<300&&!calls.length;i++)G.Combat.updateFields(.01);
  }else{
   A.assert(G.NarutoGaara.cast(p,snapshot),'sand bullet cast');
   for(let i=0;i<200&&!calls.length;i++)G.NarutoGaara.update(.01);
  }
 }finally{A.pause();S.hit=original;}
 A.assert(calls.length&&calls[0].primary,'custom single-target source did not splash '+dex);
 const splash=neighbor.logs.find(l=>l.secondary);
 A.assert(splash&&Math.abs(splash.damage-calls[0].direct*.2)<1e-7,'incorrect splash damage '+dex);
 A.assert(!primary.logs.some(l=>l.secondary),'primary received its own splash '+dex);
 return {dex,direct:calls[0].direct,splash:splash.damage,quantityMultiplier:Q.multiplier(p)};
}"""

GUARD = r"""() => {
 const A=Acceptance,p=G.Game.player,S=G.DamageSplash;
 A.arena();p.quantityPicks=0;p.quantityBonus=0;p.damageSplashPicks=1;p.percentHealthDamage=.01;
 p.addMove('naruto-sand-shield');
 const spawn=(x,y)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
  e.types=['normal'];e.logs=[];const hurt=e.hurt;
  e.hurt=function(...args){e.logs.push({damage:args[0],secondary:S.isSecondary()});return hurt.apply(this,args)};
  G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;};
 const primary=spawn(110,0),neighbor=spawn(140,30),g=G.NarutoSandGuard.state(p);
 g.guardians.forEach((s,i)=>{s.x=100;s.y=0;s.heading=0;if(i){s.ready=false;s.charges=0}});
 A.resume();try{G.Combat.resolve(.01,p,0)}finally{A.pause()}
 const splash=neighbor.logs.find(l=>l.secondary),expected=10*p.atk*G.Types.mult('ground',primary.types)*G.Weather.mult('ground')*.1;
 A.assert(splash&&Math.abs(splash.damage-expected)<1e-7,'guardian splash copied intrinsic HP damage');
 A.assert(100000-neighbor.hp===Math.round(expected),'secondary procced common percent HP damage');
 p.quantityPicks=20;A.assert(G.NarutoSandGuard.state(p).count===100,'guardian cap changed');
 return {guardSplash:splash.damage,neighborHpLoss:100000-neighbor.hp,cap:100};
}"""


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(URL)
        page.wait_for_function("window.PS_REDRAWN_READY && G.DamageSplash && document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.evaluate(HARNESS)
        report = {'heroes': [page.evaluate(CHECK, dex) for dex in [30001, 30002, 30006, 30007]]}
        report['guardian'] = page.evaluate(GUARD)
        assert not errors, errors
        out = Path(__file__).resolve().parents[1] / '.omx/state/quantity-splash'
        out.mkdir(parents=True, exist_ok=True)
        (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'ok': True, **report}, ensure_ascii=False))
        browser.close()


if __name__ == '__main__':
    main()
