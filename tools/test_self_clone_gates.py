"""Eight Gates inheritance on card clones, using native player and actor APIs.

Run with the repository HTTP server on port 8004.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/self-clone-gates'
CHECK = r"""() => {
 const A=Acceptance,assert=A.assert,near=(a,b,label)=>assert(Math.abs(a-b)<1e-6*Math.max(1,Math.abs(b)),label+': '+a+' != '+b);
 G.Naruto.choose(30006);G.Flow.play();A.pause();A.arena();
 const p=G.Game.player,S=G.SelfClones,K=G.NarutoGates;
 p.level=20;p.critChance=0;p.lifestealRate=0;p.percentHealthDamage=0;
 const step=(dt=.01)=>{A.resume();try{G.Combat.updateFields(dt)}finally{A.pause()}};
 const gateStep=()=>{A.resume();try{K.update(.001)}finally{A.pause()}};
 const summon=()=>{const a=S.summon(p);assert(a,'summon refused');return a};
 const plain=summon();assert(K.stage(plain)===0,'unlearned Gates active on clone');
 near(K.healingMultiplier(plain),1,'unlearned heal');near(K.inheritedRegen(plain),0,'unlearned innate regen');
 S.clear();assert(p.addMove('naruto-gates'),'learn Gates');
 const m=p.moves.find(m=>m.id==='naruto-gates'),a=summon(),b=summon(),spawnHp=a.maxHp,spawnHpB=b.maxHp;
 const rows=[];
 for(let stage=1;stage<=5;stage++){
   if(stage>1)assert(G.Moves.levelUp(m),'upgrade Gates');
   for(const n of p.moves)n.t=999;
   step(.001);
   for(const actor of [a,b]){
     const learned=actor.moves.find(n=>n.id==='naruto-gates');
     assert(learned&&learned!==m&&learned.passive&&learned.lvl===stage,'mirrored learned passive stage '+stage);
     assert(!actor.slots.some(g=>g.includes(learned)),'Gates took active slot');
     assert(K.stage(actor)===stage&&K.redSkin(actor)&&K.redForm(actor)===(stage>=3)&&K.intense(actor)===(stage>=3),'clone stage/VFX '+stage);
     near(actor.atk,p.atk/3,'single inherited atk '+stage);near(actor.spd,p.spd,'single inherited speed '+stage);
     near(K.bonusPercent(actor),10*stage+p.level,'clone tier bonus');
     near(K.healingMultiplier(actor),K.healingMultiplier(p),'healing tier');
     near(K.maxHealthBonus(actor),0,'no second Gates health bonus');
     const hp=actor.hp,max=actor.maxHp,source=p.hp;
     K.syncMaxHealth(actor);K.syncMaxHealth(actor);near(actor.maxHp,max,'sync changed snapshot');near(actor.hp,hp,'sync healed clone');near(p.hp,source,'sync changed player');
     near(actor.regen,p.regen/3,'single inherited regen '+stage);
     actor.hp=1;const ownerHp=p.hp,expected=1+2*K.healingMultiplier(actor);actor.heal(2);
     near(actor.hp,expected,'heal amplified once');near(p.hp,ownerHp,'clone heal changed player');
     actor.hp=1;const before=actor.hp,regen=actor.regen;step(.02);
     near(actor.hp-before,regen*.02,'regen tick once');
   }
   near(a.maxHp,spawnHp,'existing clone snapshot across upgrades');near(b.maxHp,spawnHpB,'second snapshot');
   K.clear();gateStep();p.x+=10;a.x+=20;b.x+=30;gateStep();
   for(const actor of [p,a,b]){
     const images=K.afterimagesFor(actor);assert(images.length>0,'missing individual trails');
     near(images.at(-1).x,actor.x,'actor trail origin');near(images.at(-1).scale,K.config.trails[stage-1].scale,'tier trail style');
   }
   const ownerImages=K.afterimages.length;K.clear(a);
   assert(!K.afterimagesFor(a).length&&K.afterimages.length===ownerImages&&K.afterimagesFor(b).length,'owner-scoped VFX clear');
   rows.push({stage,atk:a.atk,spd:a.spd,regen:a.regen,maxHp:a.maxHp,heal:K.healingMultiplier(a)});
 }
 const fresh=summon();near(fresh.maxHp,p.maxHp/3,'new clone upgraded source snapshot');assert(K.stage(fresh)===5,'new clone tier');
 const oldWorld=G.World;S.withSceneTransition(()=>{G.Combat.clearFields();G.World={...oldWorld}});step(.001);
 assert(S.isActor(b)&&K.stage(b)===5&&b.world===G.World,'scene retained clone/passive');near(b.maxHp,spawnHpB,'scene HP snapshot');
 K.clear(b);gateStep();b.x+=20;gateStep();assert(K.afterimagesFor(b).length,'scene VFX not recreated');
 const sourceHp=p.hp;a.invuln=0;A.resume();try{a.hurt(a.maxHp*100,null,true)}finally{A.pause()}
 assert(a.dead&&!S.actors().includes(a)&&K.stage(a)===0&&!K.redSkin(a)&&!K.afterimagesFor(a).length,'dead clone passive/VFX remains');
 near(K.inheritedRegen(a),0,'dead clone regen');near(p.hp,sourceHp,'clone death changed source');assert(K.stage(b)===5,'clone death cleared survivor');
 const survived=b;G.Game.quit();G.Flow.goMenu();G.Naruto.choose(30006);G.Flow.play();A.pause();A.arena();
 assert(!S.actors().length&&K.stage(survived)===0&&!K.afterimagesFor(survived).length,'new-run old actor state');
 assert(K.stage(G.Game.player)===0,'learned Gates leaked into new run');
 const noGates=S.summon(G.Game.player);assert(K.stage(noGates)===0,'old Gates leaked into new clone');
 return {stages:rows,inheritance:'learned-only, atk/spd/regen/heal once, immutable spawn HP',lifecycle:'independent trails, death, upgrade, scene and new-run cleanup'};
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report={'viewports':{},'errors':[]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            for mobile in [False,True]:
                context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
                page=context.new_page()
                page.on('pageerror',lambda e:report['errors'].append(str(e)))
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.SelfClones && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
                page.evaluate(HARNESS)
                report['viewports']['mobile' if mobile else 'desktop']=page.evaluate(CHECK)
                context.close()
            browser.close()
        assert not report['errors'],report['errors']
        report['ok']=True
    except Exception as error:
        report.update(ok=False,failure=str(error))
        raise
    finally:
        (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'stages':5}))

if __name__=='__main__':main()
