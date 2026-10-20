"""Shared quantity cards add Reverse Lotus strikes; air damage grows geometrically."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.omx/state/lee-quantity-scaling'
URL='http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=lee-quantity-scaling'

HELPERS=r"""() => {
 const A=Acceptance,p=A.p();p.level=12;
 for(const id of ['naruto-reverse-lotus','naruto-gates']){const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'learn '+id)}
 A.quantityCard=id=>{let card;for(let n=0;n<150&&!card;n++)card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:'+id);A.assert(card,'real stat card missing '+id);A.assert(card.apply(p)!==false,'stat card rejected '+id);return card};
 A.quantityFixture=(quantity,splash=true,castNow=true)=>{
   A.leeArena();G.Weather.reset();p.statsTaken.quantity=0;p.maxHp=1000000;p.hp=10;
   for(let n=0;n<quantity;n++)A.quantityCard('quantity');
   A.quantityCard('percentHealthDamage');A.quantityCard('lifesteal');p.critChance=1;
   A.assert(p.quantityBonus===quantity&&p.percentHealthDamage===.01&&p.lifestealRate===.01,'real card effects incorrect');
   const m=A.select('naruto-reverse-lotus'),e=A.spawn(35,0),side=splash?A.spawn(35+m.radius*.7,0):null,ledger=[];
   for(const enemy of [e,side].filter(Boolean)){
     enemy.hp=enemy.maxHp=10000000;const hurt=enemy.hurt;
     enemy.hurt=function(...args){ledger.push({primary:this===e,amount:args[0],owner:args[6]===p,crit:args[5]==='crit'});return hurt.apply(this,args)};
   }
   p.target=e;p.aim=0;const before={hp:p.hp,damage:p.dmgDealt};
   if(castNow)A.actualCast(m.id);
   A.quantityRun={m,e,side,ledger,before,quantity};return A.quantityRun;
 };
 A.checkQuantityRun=(r,level,quantity,step=.005)=>{
   const f=G.NarutoLee.active,snapshot={damage:f.move.dmg,attack:f.attack,hits:f.comboHits,level:f.move.lvl,quantity:f.move.quantityBonusAtCast};
   const air=5+2*(level-1)+quantity,total=air+2;
   A.assert(f.comboHits===air,'quantity counted twice or omitted '+JSON.stringify(snapshot));
   for(let n=0;n<1000&&G.NarutoLee.active;n++)A.advance(step);
   A.assert(!G.NarutoLee.active,'quantity combo did not finish');
   const primary=r.ledger.filter(h=>h.primary),side=r.ledger.filter(h=>!h.primary);
   A.assert(primary.length===total&&side.length===(r.side?1:0),'wrong actual hit count '+primary.length+' expected '+total);
   A.assert(r.ledger.every(h=>h.owner&&h.crit),'critical ownership lost');
   const base=snapshot.damage*snapshot.attack*G.Types.mult(r.m.type,r.e.types)*G.Weather.mult(r.m.type)*1.5;
   const expected=[base*.1,...Array.from({length:air},(_,n)=>base*.12*Math.pow(1.1,n+1)),base*.3];
   const near=(a,b)=>Math.abs(a-b)<1e-8*Math.max(1,Math.abs(b));
   primary.forEach((h,i)=>A.assert(near(h.amount,expected[i]),'wrong geometric raw hit '+i+' '+h.amount+' vs '+expected[i]));
   if(r.side)A.assert(near(side[0].amount,base*.35),'landing splash inherited air exponent');
   const expectedCredit=r.ledger.reduce((sum,h)=>sum+h.amount+10000000*.01,0),actualCredit=p.dmgDealt-r.before.damage;
   A.assert(near(actualCredit,expectedCredit),'flat percent-HP component was exponentiated or credited twice');
   A.assert(near(p.hp-r.before.hp,expectedCredit*.01*G.NarutoGates.healingMultiplier(p)),'per-hit lifesteal/Gates healed twice');
   const actualLoss=10000000-r.e.hp,roundedLoss=expected.reduce((sum,d)=>sum+Math.round(d+10000000*.01),0);
   A.assert(actualLoss===roundedLoss,'enemy damage not one native hit per strike');
   return {level,quantity,airHits:air,totalPrimaryHits:total,splashHits:side.length,rawPrimary:primary.map(h=>h.amount),credit:actualCredit,healed:p.hp-r.before.hp,snapshot};
 };
}"""

MATRIX=r"""() => {
 const A=Acceptance,p=A.p(),out=[],move=p.moves.find(m=>m.id==='naruto-reverse-lotus');
 for(const level of [1,5]){
   while(move.lvl<level){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+move.id);A.assert(card&&card.apply(p)!==false,'real skill upgrade')}
   for(const quantity of [0,1,3,20]){const r=A.quantityFixture(quantity);out.push(A.checkQuantityRun(r,level,quantity));}
 }
 const r=A.quantityFixture(20);A.advance(4);
 A.assert(!G.NarutoLee.active&&r.ledger.filter(h=>h.primary).length===35&&r.ledger.filter(h=>!h.primary).length===1,'max quantity large dt lost/duplicated hits');
 const again=A.quantityFixture(0);const reset=A.checkQuantityRun(again,5,0);
 return {matrix:out,maxQuantityLargeDelta:35,newChainResetsExponent:reset.rawPrimary[1]};
}"""

SNAPSHOT=r"""() => {
 const A=Acceptance,p=A.p(),r=A.quantityFixture(1,false),f=G.NarutoLee.active;
 A.assert(r.m.lvl===1&&f.comboHits===6,'snapshot fixture must start Lv1/Q1');
 for(let n=0;n<200&&G.NarutoLee.active?.phase!=='combo';n++)A.advance(.005);
 A.assert(G.NarutoLee.active?.phase==='combo','snapshot combo phase missing');
 const upgrade=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+r.m.id);A.assert(upgrade&&upgrade.apply(p)!==false,'midair upgrade unavailable');A.quantityCard('quantity');
 A.assert(r.m.lvl===2&&p.quantityBonus===2&&f.comboHits===6&&f.move.lvl===1&&f.move.quantityBonusAtCast===1,'midair changes altered cast snapshot');
 const frozen=A.checkQuantityRun(r,1,1);
 const next=A.quantityFixture(2,false);const updated=A.checkQuantityRun(next,2,2);
 const pre=A.quantityFixture(3,false,false),snap=G.Quantity.snapshot(p,pre.m),twice=G.Quantity.snapshot(p,snap);
 A.assert(twice.count===snap.count&&twice.quantityBonusAtCast===3,'shared quantity snapshot not idempotent');
 A.resume();try{A.assert(G.NarutoLee.cast(p,twice),'pre-snapshot actual cast rejected')}finally{A.pause()}
 const preSnapshot=A.checkQuantityRun(pre,2,3);return {frozen,next:updated,preSnapshot};
}"""

DEAD_TARGET=r"""() => {
 const A=Acceptance,p=A.p(),r=A.quantityFixture(20,false);A.advance(.3);A.assert(G.NarutoLee.active?.phase==='lift','dead-target launch fixture');
 r.e.hp=0;r.e.dead=true;const hits=r.ledger.length,hp=p.hp,credit=p.dmgDealt;
 A.advance(1);A.assert(G.NarutoLee.active?.ticks>0,'planned swings did not continue after early KO');A.advance(4);
 A.assert(!G.NarutoLee.active&&r.ledger.length===hits&&p.hp===hp&&p.dmgDealt===credit,'dead target generated exponential hit/heal/credit');
 return {priorHits:hits,noAdditionalProcs:true};
}"""

def start(page):
    page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY&&G.AnimationLab&&document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.locator('[data-quick-naruto="30006"]').click();page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
    page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(HELPERS)

def main():
    OUT.mkdir(parents=True,exist_ok=True);report={'errors':[],'failedRequests':[],'viewports':{}}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            for mobile in (False,True):
                label='mobile' if mobile else 'desktop';ctx=browser.new_context(locale='zh-TW',viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
                page=ctx.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.on('response',lambda r:report['failedRequests'].append(r.url) if r.status>=400 and '127.0.0.1' in r.url else None)
                start(page);result={};report['viewports'][label]=result
                result['quantity']=page.evaluate(MATRIX);result['deadTarget']=page.evaluate(DEAD_TARGET)
                page.evaluate('G.Game.toUI();G.Flow.play();G.Game.togglePause()');page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(HELPERS)
                result['snapshots']=page.evaluate(SNAPSHOT)
                page.evaluate('G.Flow.goMenu()');page.locator('[data-quick-naruto="30002"]').click();page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30002&&G.Game.state==="playing"')
                page.evaluate(HARNESS);page.evaluate(SETUP)
                result['sasukeSharedQuantity']=page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p();A.leeArena();p.level=12;A.assert(p.addMove('naruto-shuriken'),'shared projectile fixture');
                  for(let n=0;n<3;n++){let card;for(let k=0;k<150&&!card;k++)card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');A.assert(card,'Sasuke shared quantity card missing');card.apply(p)}
                  const m=A.select('naruto-shuriken');p.target=A.spawn(100,0);const expected=G.Quantity.count(p,m.count);A.actualCast(m.id);A.advance(.5);
                  A.assert(p.quantityBonus===3&&G.Projectiles.all().filter(s=>s.friendly&&s.owner===p).length===expected,'Sasuke shared projectile quantity changed');return {bonus:p.quantityBonus,projectiles:expected};
                }""")
                ctx.close()
            browser.close()
        assert not report['errors'],report['errors'];assert not report['failedRequests'],report['failedRequests'];report['ok']=True
    except Exception as error:report['ok']=False;report['failure']=str(error);raise
    finally:(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'evidence':str(OUT)},ensure_ascii=False))

if __name__=='__main__':main()
