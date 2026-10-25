"""Eight Gates maximum HP is exactly current character level times skill level."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.omx/state/lee-gates-health'
URL='http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&layout=wide&test=lee-gates-health'

HELPERS=r"""() => {
 const A=Acceptance,p=A.p();A.leeArena();p.level=6;p.xp=0;p.xpNext=G.Player.xpFor(6);p.maxHp=260;p.hp=260;
 A.healthNear=(a,b,message)=>A.assert(Math.abs(a-b)<1e-8,(message||'health mismatch')+' '+a+' vs '+b);
 A.healthCard=key=>{let card;for(let n=0;n<150&&!card;n++)card=G.LevelUp.offer(p,100).find(c=>c.key===key);A.assert(card,'real card missing '+key);A.assert(card.apply(p)!==false,'real card rejected '+key);return card};
 A.nextHealthLevel=()=>{const level=p.level,needed=p.xpNext-p.xp;const got=p.gainXp((needed+.0001)/p.xpMul);A.assert(p.level===level+1&&got===1,'actual single XP level failed');return got};
}"""

EXACT=r"""() => {
 const A=Acceptance,p=A.p(),g=G.NarutoGates,N=A.healthNear,out=[];
 A.assert(g.maxHealthBonus(p)===0,'unlearned HP capacity bonus');
 const descriptor=Object.getOwnPropertyDescriptor(p,'maxHp');A.assert(descriptor?.writable&&!descriptor.get&&!descriptor.set,'maximum HP stopped being a plain writable field');
 A.healthCard('new:naruto-gates');N(p.maxHp,266);N(p.hp,266);A.assert(g.maxHealthBonus(p)===6,'Lv6 N1 bonus not exactly 6');out.push({level:6,skill:1,max:p.maxHp,hp:p.hp});
 A.nextHealthLevel();N(p.maxHp,267);N(p.hp,267);out.push({level:7,skill:1,max:p.maxHp,hp:p.hp});
 A.healthCard('up:naruto-gates');N(p.maxHp,274);N(p.hp,274);out.push({level:7,skill:2,max:p.maxHp,hp:p.hp});
 for(let level=3;level<=5;level++)A.healthCard('up:naruto-gates');N(p.maxHp,295);N(p.hp,295);
 p.xp=0;p.xpNext=G.Player.xpFor(7);let needed=0;for(let level=7;level<30;level++)needed+=G.Player.xpFor(level);
 const levels=p.gainXp((needed+.0001)/p.xpMul);A.assert(levels===23&&p.level===30,'actual multi-level XP gain failed');
 N(p.maxHp,410);N(p.hp,410);A.assert(g.maxHealthBonus(p)===150,'Lv30 N5 bonus not exactly 150');out.push({level:30,skill:5,max:p.maxHp,hp:p.hp,levelsAtOnce:levels});
 A.healthCard('stat:maxHealthPercent');N(p.maxHp,451);N(p.hp,451);out.push({growth:1,max:p.maxHp,hp:p.hp});
 A.nextHealthLevel();N(p.maxHp,456);N(p.hp,456);A.assert(g.maxHealthBonus(p)===155,'Lv31 N5 bonus incorrect');out.push({level:31,skill:5,max:p.maxHp,hp:p.hp});
 // Neither repeated explicit synchronization nor ordinary field updates refill missing HP.
 p.hp=70;for(let n=0;n<10000;n++){g.syncMaxHealth(p);G.Combat.updateFields(0)}N(p.maxHp,456);N(p.hp,70);
 A.assert(!p.addMove('naruto-gates'),'duplicate learned gates accepted');N(p.maxHp,456);N(p.hp,70);
 const world=G.World;G.Combat.clearFields(p);G.Combat.updateFields(0);G.World={...world};G.Combat.updateFields(0);G.World=world;G.Combat.updateFields(0);
 N(p.maxHp,456);N(p.hp,70);out.push({syncs:10000,max:p.maxHp,hp:p.hp,worldAndClearStable:true});
 p.dead=true;p.hp=0;g.syncMaxHealth(p);N(p.maxHp,456);N(p.hp,0);A.assert(g.stage(p)===0&&g.maxHealthBonus(p)===155,'death removed learned capacity or retained active buffs');
 p.level=32;g.syncMaxHealth(p);N(p.maxHp,461);N(p.hp,0);for(let n=0;n<100;n++)g.syncMaxHealth(p);N(p.hp,0);
 p.revive(.5);N(p.maxHp,461);N(p.hp,230.5);g.syncMaxHealth(p);N(p.hp,230.5);out.push({deadLevel:32,max:p.maxHp,revived:p.hp});
 return out;
}"""

MIXED=r"""() => {
 const A=Acceptance,p=A.p(),N=A.healthNear,g=G.NarutoGates;p.hp=100;
 A.healthCard('new:naruto-gates');N(p.maxHp,266);N(p.hp,106);
 A.healthCard('stat:maxHealthPercent');N(p.maxHp,292.6);N(p.hp,132.6);
 // Flat health grants still compose with Gates; the old Vigor selection card is retired.
 p.addMaxHp(20);N(p.maxHp,312.6);N(p.hp,152.6);
 A.healthCard('up:naruto-gates');N(p.maxHp,318.6);N(p.hp,158.6);
 A.nextHealthLevel();N(p.maxHp,320.6);N(p.hp,160.6);
 A.healthCard('stat:maxHealthPercent');N(p.maxHp,352.66);N(p.hp,192.66);
 A.healthCard('up:naruto-gates');N(p.maxHp,359.66);N(p.hp,199.66);A.assert(g.maxHealthBonus(p)===21,'mixed cards changed the exact additive Gates component');
 const move=p.moves.find(m=>m.id==='naruto-gates');p.hp=100;move.lvl=4;G.Combat.updateFields(0);
 N(p.maxHp,366.66);N(p.hp,107);p.level=8;G.Combat.updateFields(0);N(p.maxHp,370.66);N(p.hp,111);
 for(let n=0;n<10000;n++)g.syncMaxHealth(p);N(p.maxHp,370.66);N(p.hp,111);
 return {max:p.maxHp,hp:p.hp,level:p.level,skill:move.lvl,gateBonus:g.maxHealthBonus(p),flatGrants:1,growthCards:p.statsTaken.maxHealthPercent};
}"""

def main():
    OUT.mkdir(parents=True,exist_ok=True);report={'errors':[],'failedRequests':[],'viewports':{}}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            for mobile in (False,True):
                label='mobile' if mobile else 'desktop';ctx=browser.new_context(locale='zh-TW',viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
                page=ctx.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.on('response',lambda r:report['failedRequests'].append(r.url) if r.status>=400 and '127.0.0.1' in r.url else None)
                page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY&&G.NarutoGates?.syncMaxHealth&&document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30006"]').click();page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
                page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(HELPERS)
                result={'exact':page.evaluate(EXACT)};report['viewports'][label]=result
                result['newOwner']=page.evaluate(r"""() => {
                  const A=Acceptance,old=A.p(),oldMax=old.maxHp;G.Game.toUI();G.Flow.play();G.Game.togglePause();const p=G.Game.player;
                  A.assert(p!==old&&!p.hasMove('naruto-gates')&&G.NarutoGates.maxHealthBonus(p)===0,'new owner inherited Gates capacity');A.assert(old.maxHp===oldMax,'new owner rewrote prior owner capacity');return {max:p.maxHp,hp:p.hp};
                }""")
                page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(HELPERS);result['mixed']=page.evaluate(MIXED)
                page.evaluate('G.Flow.goMenu()');page.locator('[data-quick-naruto="30002"]').click();page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30002&&G.Game.state==="playing"')
                page.evaluate(HARNESS);page.evaluate(SETUP)
                result['sasuke']=page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p();A.leeArena();p.maxHp=260;p.hp=130;p.level=30;p.xp=0;p.xpNext=G.Player.xpFor(30);
                  G.NarutoGates.syncMaxHealth(p);p.gainXp((p.xpNext+.0001)/p.xpMul);A.assert(p.maxHp===260&&p.hp===130&&G.NarutoGates.maxHealthBonus(p)===0,'Gates capacity leaked to Sasuke');
                  let card;for(let n=0;n<150&&!card;n++)card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:maxHealthPercent');A.assert(card,'shared health growth missing');card.apply(p);
                  A.assert(Math.abs(p.maxHp-286)<1e-8&&Math.abs(p.hp-156)<1e-8,'shared growth changed on non-Lee');return {max:p.maxHp,hp:p.hp};
                }""")
                ctx.close()
            browser.close()
        assert not report['errors'],report['errors'];assert not report['failedRequests'],report['failedRequests'];report['ok']=True
    except Exception as error:report['ok']=False;report['failure']=str(error);raise
    finally:(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'evidence':str(OUT)},ensure_ascii=False))

if __name__=='__main__':main()
