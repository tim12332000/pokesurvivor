"""Native Naruto effects owned by card clones: temporary children and cloak."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/self-clone-naruto-effects'
CHECK = r"""() => {
 const A=Acceptance,assert=A.assert,near=(a,b,label)=>assert(Math.abs(a-b)<1e-6,label+': '+a+' != '+b);
 G.Naruto.choose(30001);G.Flow.play();A.pause();A.arena();
 const p=G.Game.player,S=G.SelfClones,N=G.NarutoClones;
 p.level=30;p.critChance=0;p.percentHealthDamage=0;p.lifestealRate=0;
 for(const id of ['naruto-naruto','naruto-rasenshuriken','naruto-nine-tails-cloak'])if(!p.hasMove(id))assert(p.addMove(id),'learn '+id);
 assert(p.moves.length===4&&p.moves.every(m=>!m.passive),'Naruto finite techniques were classified as learned passives');
 A.select('naruto-shadow-clones');const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');
 assert(card&&card.apply(p)!==false,'real clone card missing');const actor=S.actors()[0];actor.x=actor.y=0;
 near(actor.maxHp,p.maxHp/3,'clone max HP');near(actor.atk,p.atk/3,'clone base attack');
 const target=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},100,0,{hp:1,spd:1,dmg:1});
 target.types=['normal'];target.touchCd=999;G.EnemyMgr.add(target);G.EnemyMgr.rebuildGrid();p.target=actor.target=target;
 const hits=[],hurt=target.hurt;target.hurt=function(...args){hits.push({amount:args[0],owner:args[6],id:args[7]});return hurt.apply(this,args)};
 const step=dt=>{A.resume();try{G.Combat.updateFields(dt);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,0)}finally{A.pause()}};
 const living=owner=>N.actors.filter(a=>a.owner===owner&&!a.dead);
 // One actual automatic cast on the player supplies an equivalent native
 // punch baseline; global updates cast the generic clone's selected technique.
 for(const m of p.moves)m.t=m.id==='naruto-shadow-clones'?0:999;
 A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()}
 for(let n=0;n<160&&(!living(p).length||!living(actor).length);n++)step(.01);
 assert(living(actor).length===N.config.counts[0]&&living(p).length===N.config.counts[0],'independently owned temporary shadow clones missing');
 const children=living(actor).slice(),ownerChildren=living(p).slice();
 for(const m of [...p.moves,...actor.moves])m.t=999;
 for(let n=0;n<160&&!(hits.some(h=>h.owner===p)&&hits.some(h=>h.owner===actor));n++)step(.01);
 const ownerHit=hits.find(h=>h.owner===p&&h.id==='naruto-shadow-clones'),cloneHit=hits.find(h=>h.owner===actor&&h.id==='naruto-shadow-clones');
 assert(ownerHit&&cloneHit,'native temporary-clone punch baseline missing');near(cloneHit.amount*3,ownerHit.amount,'temporary punch one-third damage');
 const mimic=[];
 for(const id of ['naruto-naruto','naruto-rasenshuriken']){
   A.select(id);for(const m of p.moves)m.t=999;
   const move=actor.moves.find(m=>m.id===id);move.t=0;const before=hits.length;
   for(let n=0;n<90;n++)step(.01);
   assert(S.actors().length===1&&S.actors()[0]===actor,'native technique recursively created card clones');
   assert(children.some(c=>!c.dead&&N.actors.includes(c)),'slot switch removed finite shadow clones');
   assert(children.filter(c=>!c.dead).every(c=>c.mimickedId===id),'temporary child did not mirror generic actor selected technique '+id);
   assert(children.some(c=>c.cooldowns.get(id)>0),'temporary mimic never attacked '+id);
   assert(hits.slice(before).some(h=>h.owner===actor&&h.id===id),'mimicked technique damage missing '+id);
   assert(actor.activeGroup().some(m=>m.id===id),'generic actor selection lost '+id);
   mimic.push(id);
 }
 const playerHp=p.hp;actor.invuln=0;A.resume();try{actor.hurt(7,null,true)}finally{A.pause()}
 near(p.hp,playerHp,'generic actor damage changed player HP');near(actor.hp,actor.maxHp-7,'independent actor HP');
 A.select('naruto-nine-tails-cloak');for(const m of p.moves)m.t=999;
 const baseAtk=actor.atk,baseSpd=actor.spd,cloakMove=actor.moves.find(m=>m.id==='naruto-nine-tails-cloak');cloakMove.t=0;step(.01);cloakMove.t=999;
 const effect=G.NarutoSupport.effects.find(f=>f.owner===actor&&f.mode==='nine-tails-cloak');
 assert(effect&&!G.NarutoSupport.effects.some(f=>f.owner===p&&f.mode==='nine-tails-cloak'),'clone-only cloak not independently owned');
 assert(actor.atk>baseAtk&&actor.spd>baseSpd,'clone cloak failed effective stat bonuses');
 A.select('naruto-naruto');for(const m of p.moves)m.t=999;step(.01);
 assert(G.NarutoSupport.effects.includes(effect),'switch removed finite cloak');
 for(const m of actor.moves)m.t=999;
 for(let t=0;t<effect.ttl+.2;t+=.05)step(.05);
 assert(!G.NarutoSupport.effects.includes(effect),'cloak did not expire');near(actor.atk,baseAtk,'cloak attack expiry');near(actor.spd,baseSpd,'cloak speed expiry');
 assert(!children.some(c=>!c.dead&&N.actors.includes(c))&&!ownerChildren.some(c=>!c.dead&&N.actors.includes(c)),'temporary shadow clones never expired');
 assert(S.actors().length===1&&S.actors()[0]===actor,'generic permanent clone expired with finite children');
 // Native child actors are never eligible to summon another skill-card actor.
 assert(S.summon(children[0])===null&&S.summon(actor)===null,'recursive card summon accepted a summoned actor');
 actor.invuln=0;A.resume();try{actor.hurt(actor.maxHp*10,null,true)}finally{A.pause()}step(.01);
 assert(actor.dead&&!S.actors().includes(actor)&&!N.actors.some(a=>a.owner===actor&&!a.dead),'dead generic actor retained its children');
 return {skills:4,truePassives:0,temporaryChildren:children.length,mimic,damageRatio:cloneHit.amount/ownerHit.amount,
   finiteEffectsSurviveSwitch:true,finiteEffectsExpire:true,genericActorPersists:true,recursiveSummonBlocked:true,independentHp:true};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'viewports': {}, 'errors': []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in [False, True]:
                context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900},
                                              is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.SelfClones && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.evaluate(HARNESS)
                report['viewports']['mobile' if mobile else 'desktop'] = page.evaluate(CHECK)
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'viewports': list(report['viewports']), 'skills': 4}))


if __name__ == '__main__':
    main()
