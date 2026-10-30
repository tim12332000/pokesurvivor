"""All five Gates speed tiers, real attack intervals, and retained excess HP."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

OUT = Path(__file__).resolve().parents[1] / '.omx/state/lee-gates-speed'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=lee&layout=wide&test=gates-speed'

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),g=G.NarutoGates,near=(a,b)=>Math.abs(a-b)<1e-7;
 A.leeArena();p.level=6;p.maxHp=1000;p.hp=1000;p.regenFlat=0;p.cdMul=.8;
 const base={spd:p.spd,max:p.maxHp,cd:p.cdMul,slots:p.slots.length},out={stages:[]};
 A.assert(g.attackSpeedMultiplier(p)===1,'unlearned Gates accelerated attacks');
 A.assert(p.addMove('naruto-gates'),'learning Gates failed');
 const gates=p.moves.find(m=>m.id==='naruto-gates');
 A.assert(gates.passive&&p.slots.length===base.slots,'automatic Gates consumed an active slot');
 const combatTick=()=>{A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()}};
 function nativeInterval(){
   const move=G.Moves.instance('tackle'),group=p.activeGroup,target=p.target;
   p.activeGroup=()=>[move];p.target=A.spawn(30,0);p.aim=0;move.t=0;
   try{combatTick()}finally{p.activeGroup=group;p.target=target}
   return {actual:move.t,base:move.cd};
 }
 for(let level=1;level<=5;level++){
   if(level>1){A.leeArena();A.assert(G.Moves.levelUp(gates),'upgrade failed '+level)}
   const factor=1+level*.1;
   A.assert(g.stage(p)===level&&g.performing(p),'tier did not open '+level);
   A.assert(near(p.spd,base.spd*factor),'movement speed wrong '+level);
   A.assert(near(g.attackSpeedMultiplier(p),factor),'attack speed wrong '+level);
   // Character levels do not add a hidden movement/attack speed percentage.
   p.level=30;A.assert(near(p.spd,base.spd*factor)&&near(g.attackSpeedMultiplier(p),factor),'character level changed speed tier');p.level=6;
   A.advance(5);A.assert(!g.performing(p)&&g.active(p),'opening did not end at five seconds');
   const native=nativeInterval();
   A.assert(near(native.actual,native.base*base.cd/factor),'native attack interval wrong '+level+' '+JSON.stringify(native));
   const whirlwind=A.select('naruto-lee');p.target=A.spawn(30,0);p.aim=0;combatTick();
   A.assert(near(whirlwind.t,Math.max(whirlwind.minCooldown||.05,whirlwind.cd*base.cd/factor)),'Lee whirlwind attack interval wrong '+level);
   A.assert(p.cdMul===base.cd,'Gates mutated cooldown cards '+level);
   const activeMax=p.maxHp;p.hp=activeMax;A.advance(10);
   A.assert(!g.active(p)&&near(p.maxHp,base.max),'capacity did not revert at fifteen seconds '+level);
   A.assert(p.hp===activeMax,'closing removed current HP '+level);
   A.assert(near(p.spd,base.spd)&&g.attackSpeedMultiplier(p)===1,'speed bonus survived closing '+level);
   p.heal(100);A.assert(p.hp===activeMax,'heal erased or increased retained HP');
   p.regenFlat=10;p.bellHeal=2;A.resume();try{p.update(.1)}finally{A.pause()}
   A.assert(p.hp===activeMax,'regeneration or shell bell changed retained HP');p.regenFlat=0;p.bellHeal=0;
   const specials=G.World.specialsNear;
   try{G.World.specialsNear=()=>[{type:'spring',x:p.x,y:p.y+8,charge:1}];G.Interact.update(.1,p)}
   finally{G.World.specialsNear=specials}
   A.assert(p.hp===activeMax,'spring changed retained HP');
   const normal=nativeInterval();A.assert(near(normal.actual,normal.base*base.cd),'attack speed survived closing');
   // Reopening restores capacity without farming more HP above that capacity.
   A.advance(15);A.assert(g.active(p)&&near(p.maxHp,activeMax)&&p.hp===activeMax,'repeat opening stacked maximum or current HP');
   p.invuln=0;p.hurt(1,null,true);A.assert(p.hp===activeMax,'opening refund lost retained HP');
   A.advance(15);A.assert(!g.active(p)&&near(p.maxHp,base.max)&&p.hp===activeMax,'repeat closing removed retained HP');
   out.stages.push({level,speedMultiplier:factor,nativeInterval:native.actual,whirlwindInterval:whirlwind.cd*base.cd/factor,activeMax,closedMax:p.maxHp,retainedHp:p.hp});
 }
 out.timing={opening:5,postOpening:10,cycle:30};out.cooldownCardsPreserved=true;out.overcapSources=['heal','regen','shellBell','spring'];
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in (False, True):
            label = 'mobile' if mobile else 'desktop'
            ctx = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900},
                                      is_mobile=mobile, has_touch=mobile, service_workers='block')
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
            report['viewports'][label] = page.evaluate(CHECK)
            ctx.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'viewports': list(report['viewports']), 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
