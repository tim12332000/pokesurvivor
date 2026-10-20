"""Learned Gates add maximum-HP regeneration, composed with existing healing once."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.omx/state/lee-gates-regeneration'
URL='http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=lee-gates-regeneration'

STAGES=r"""() => {
 const A=Acceptance,p=A.p(),out={stages:[]},near=(a,b)=>Math.abs(a-b)<1e-7;
 A.leeArena();p.maxHp=1000;p.hp=100;p.regenFlat=0;p.buffs.regen.n=0;
 A.regenUpdate=dt=>{A.resume();try{p.update(dt)}finally{A.pause()}};
 A.regenUpdate(1);A.assert(p.hp===100&&p.regen===0,'unlearned Gates supplied regeneration');
 p.regenFlat=4;A.regenUpdate(1);A.assert(near(p.hp,104),'unlearned existing regeneration changed');out.unlearnedExisting=4;
 p.level=6;const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-gates');A.assert(card&&card.apply(p)!==false,'real Gates learn card');
 const move=p.moves.find(m=>m.id==='naruto-gates');
 for(let level=1;level<=5;level++){
   if(level>1){const up=G.LevelUp.offer(p,100).find(c=>c.key==='up:naruto-gates');A.assert(up&&up.apply(p)!==false,'real Gates upgrade '+level)}
   for(const existing of [0,4]){
     p.regenFlat=existing;const factor=1+(10*level+p.level)/100,expected=(existing+p.maxHp*level*.01)*factor;
     A.assert(near(p.regen,expected),'wrong combined innate regeneration getter');const results=[];
     for(const steps of [1,4,60]){
       p.hp=100;for(let i=0;i<steps;i++)A.regenUpdate(1/steps);
       A.assert(near(p.hp-100,expected),'frame-rate dependent regeneration Lv'+level+' '+steps+' steps');results.push({steps,healed:p.hp-100});
     }
     A.assert(p.regenFlat===existing&&p.buffs.regen.n===0,'getter mutated existing regeneration state');
     out.stages.push({skillLevel:level,playerLevel:p.level,existing,basePercent:level,healingFactor:factor,perSecond:expected,results});
   }
 }
 // A real XP level increase changes the preexisting healing bonus immediately.
 p.level=29;p.xp=0;p.xpNext=G.Player.xpFor(29);p.gainXp((p.xpNext+.001)/p.xpMul);
 A.assert(p.level===30&&near(p.regen,(4+1000*.05)*1.8),'player level did not update regeneration bonus immediately');
 p.regenFlat=0;p.hp=100;A.regenUpdate(1);A.assert(near(p.hp,190),'N5 LV30 should regenerate 9% max HP per second');out.level30Innate=90;
 p.regenFlat=4;let hpCard;for(let n=0;n<150&&!hpCard;n++)hpCard=G.LevelUp.offer(p,100).find(c=>c.key==='stat:hp');
 A.assert(hpCard,'max HP stat card missing');p.hp=100;hpCard.apply(p);
 A.assert(p.maxHp===1020&&p.hp===120,'maximum HP card was incorrectly healing-multiplied');
 const afterHp=(4+1020*.05)*1.8;A.assert(near(p.regen,afterHp),'max HP card did not change innate regeneration immediately');
 A.regenUpdate(1);A.assert(near(p.hp,120+afterHp),'max HP scaling did not use actual new maximum');out.maxHpCard={maxHp:p.maxHp,perSecond:afterHp};
 p.addBuff('regen',2,100,1);p.hp=100;const buffed=(6+1020*.05)*1.8;A.regenUpdate(1);
 A.assert(near(p.hp-100,buffed)&&p.buffs.regen.n===1,'existing regeneration buff did not compose once');p.buffs.regen.n=0;out.buffPerSecond=buffed;
 p.hp=p.maxHp-1;A.regenUpdate(1);A.assert(p.hp===p.maxHp,'innate regeneration exceeded maximum HP');out.cap=true;
 G.Combat.clearFields(p);p.hp=100;A.regenUpdate(1);A.assert(near(p.hp-100,afterHp),'clearFields disabled learned regeneration');out.clearSafe=true;
 // Direct heals and lifesteal remain instant single multiplications, without an extra regeneration tick.
 p.hp=100;p.heal(10);A.assert(near(p.hp,118),'direct heal included an extra regeneration tick');
 p.lifestealRate=.01;p.onDealt(100);A.assert(near(p.hp,119.8),'lifesteal included an extra regeneration tick');p.lifestealRate=0;
 p.dead=true;p.hp=100;A.assert(p.regen===4,'dead owner retained innate regeneration or its multiplier');A.regenUpdate(1);
 A.assert(p.hp===100,'dead player regenerated');p.dead=false;p.hp=100;out.deathSafe=true;
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
                page.evaluate(HARNESS);page.evaluate(SETUP)
                result={'regeneration':page.evaluate(STAGES)};report['viewports'][label]=result
                before=page.evaluate('G.Game.player.hp')
                page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(resolve))))')
                result['pausedNoUpdate']=page.evaluate('before=>{Acceptance.assert(G.Game.state==="paused"&&G.Game.player.hp===before,"paused production frames regenerated HP");return true}',before)
                result['newOwner']=page.evaluate(r"""() => {
                  const A=Acceptance,old=A.p();G.Game.toUI();G.Flow.play();G.Game.togglePause();const p=G.Game.player;
                  A.assert(p!==old&&!p.hasMove('naruto-gates')&&G.NarutoGates.stage(p)===0,'new run retained learned Gates');
                  A.assert(p.regen===p.regenFlat+p.buffs.regen.n*p.buffs.regen.amount,'new owner received innate regeneration');
                  A.assert(old.regen===4,'old owner retained innate regeneration');return true;
                }""")
                page.evaluate('G.Flow.goMenu()');page.locator('[data-quick-naruto="30002"]').click();page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30002&&G.Game.state==="playing"')
                page.evaluate(HARNESS);page.evaluate(SETUP)
                result['sasuke']=page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p();A.leeArena();p.level=30;p.maxHp=1000;p.hp=100;p.regenFlat=4;p.buffs.regen.n=0;
                  A.resume();p.update(1);A.pause();A.assert(p.regen===4&&p.hp===104,'Gates innate regeneration leaked to Sasuke');return {regen:p.regen,healed:p.hp-100};
                }""")
                ctx.close()
            browser.close()
        assert not report['errors'],report['errors'];assert not report['failedRequests'],report['failedRequests'];report['ok']=True
    except Exception as error:report['ok']=False;report['failure']=str(error);raise
    finally:(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'evidence':str(OUT)},ensure_ascii=False))

if __name__=='__main__':main()
