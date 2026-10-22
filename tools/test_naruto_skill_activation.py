"""Audit all 18 playable ninja skills: selection, passive slots, upgrades and legacy runs."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/naruto-skill-activation'
CHECK = r"""dex => {
 G.Naruto.choose(dex);G.Flow.play();Acceptance.pause();Acceptance.arena();
 const p=G.Game.player,C=G.NarutoSkillCatalog,assert=(v,m)=>{if(!v)throw Error(m)};
 const definitions=[C.byDex.get(dex),...(C.extraPools.get(dex)||[]).map(id=>G.Moves.BY_ID[id])];
 p.level=30;
 for(const def of definitions.filter(d=>!d.passive))if(!p.hasMove(def.id))assert(p.addMove(def.id),'cannot learn '+def.id);
 const selected=p.activeGroup();p.maxMoves=p.slots.length;
 for(const def of definitions.filter(d=>d.passive)){
   const slots=p.slots.slice(),ids=p.moves.map(m=>m.id);
   if(!p.hasMove(def.id)){
     const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+def.id);
     assert(card&&card.apply(p)!==false,'passive unavailable at full slots: '+def.id);
     assert(ids.every(id=>p.hasMove(id)),'passive replaced a learned move');
   }
   assert(p.slots.length===slots.length&&p.activeGroup()===selected,'passive changed active slots');
 }
 const learned=definitions.map(d=>p.moves.find(m=>m.id===d.id));
 for(const m of learned){
   while(m.lvl<5){
     const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+m.id);
     assert(card&&card.apply(p)!==false,'upgrade missing: '+m.id);
   }
   assert(p.slots.filter(g=>g.includes(m)).length===(m.passive?0:1),'wrong slot category: '+m.id);
 }
 // Old runs: passives may already occupy a numbered slot or leave a stale binding.
 for(const m of learned.filter(m=>m.passive)){
   const group=p.activeGroup();m.dealt=91;m.passive=false;p.slots.unshift([m]);p.active++;
   p.bind[m.id]=0;p.arrange();
   Acceptance.resume();try{G.Combat.updateFields(.001)}finally{Acceptance.pause()}
   assert(m.passive&&m.lvl===5&&m.dealt===91&&p.moves.includes(m),'legacy passive lost learned state');
   assert(!p.slots.some(g=>g.includes(m))&&p.bind[m.id]===undefined,'legacy passive still selectable');
   assert(p.activeGroup()===group,'legacy passive changed selected active');
   p.bind[m.id]=0;Acceptance.resume();try{G.Combat.updateFields(.001)}finally{Acceptance.pause()}
   assert(p.bind[m.id]===undefined,'slotless passive kept stale binding');
 }
 const tick=()=>{Acceptance.resume();try{G.Combat.tick(.01,p,0);G.Combat.updateFields(.01)}finally{Acceptance.pause()}};
 const prepare=()=>{G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();p.x=p.y=0;p.hp=p.maxHp;p.dead=false;p.frozen=false;p.target=Acceptance.enemy(0,50);p.aim=0;for(const m of p.moves)m.t=999};
 const inventory=[];
 for(const m of learned.filter(m=>!m.passive)){
   prepare();p.setActive(p.slots.findIndex(g=>g.includes(m)));m.t=0;
   let casts=[];const cast=p.cast;p.cast=function(move,...args){casts.push(move.id);return cast.call(this,move,...args)};
   try{tick();
     if(m.id==='naruto-sand-prison'){
       assert(G.NarutoGaara.prisonCooldownState(p),'selected prison did not start');
       Acceptance.resume();try{G.Combat.updateFields(6*p.cdMul)}finally{Acceptance.pause()}
       assert(G.NarutoGaara.sandPrisonState(p),'selected prison never generated a field');
     }else assert(casts.includes(m.id),'selected skill did not cast: '+m.id);
     const other=p.slots.findIndex(g=>!g.includes(m));
     if(m.id==='naruto-shadow-clones'){
       Acceptance.resume();try{G.Combat.updateFields(.5)}finally{Acceptance.pause()}
       const actors=G.NarutoClones.actors.filter(a=>a.owner===p&&!a.dead);
       assert(actors.length>0,'selected summon did not create clones');p.setActive(other);
       Acceptance.resume();try{G.Combat.updateFields(.01)}finally{Acceptance.pause()}
       assert(actors.some(a=>!a.dead&&G.NarutoClones.actors.includes(a)),'switch removed finite clones');
       Acceptance.resume();try{G.Combat.updateFields(m.cloneDuration+1)}finally{Acceptance.pause()}
       assert(!G.NarutoClones.actors.some(a=>a.owner===p&&!a.dead),'clones became a permanent passive');
     }
     if(m.id==='naruto-nine-tails-cloak'){
       const effect=G.NarutoSupport.effects.find(f=>f.owner===p&&f.mode==='nine-tails-cloak');
       assert(effect,'selected cloak did not activate');p.setActive(other);
       Acceptance.resume();try{G.Combat.updateFields(.01)}finally{Acceptance.pause()}
       assert(G.NarutoSupport.effects.includes(effect),'switch removed finite cloak');
       Acceptance.resume();try{G.Combat.updateFields(effect.ttl+1)}finally{Acceptance.pause()}
       assert(!G.NarutoSupport.effects.includes(effect),'cloak became a permanent passive');
     }
     if(m.id==='naruto-kusanagi'){
       assert(G.NarutoKusanagi.active(p),'selected sword did not activate');p.setActive(other);
       assert(!G.NarutoKusanagi.active(p)&&!G.NarutoKusanagi.states.has(p),'sword survived switching');
     }
     if(m.id==='naruto-sand-prison'){
       p.setActive(other);assert(!G.NarutoGaara.sandPrisonState(p),'prison survived switching');
     }
     prepare();p.setActive(other);for(const n of p.moves)n.t=999;m.t=0;casts=[];
     tick();assert(!casts.includes(m.id),'unselected skill cast itself: '+m.id);
   }finally{p.cast=cast}
   inventory.push({id:m.id,name:m.def.name,category:'active',level:m.lvl,selectedCast:true,inactiveBlocked:true});
 }
 prepare();
 for(const m of learned.filter(m=>m.passive)){
   assert(!p.activeGroup().includes(m),'passive selected');
   if(m.id==='naruto-sharingan')assert(G.NarutoSharingan.sync(p)===5,'Sharingan requires selection');
   if(m.id==='naruto-gates')assert(G.NarutoGates.stage(p)===5&&p.regen>0,'Gates requires selection');
   if(m.id==='naruto-sand-shield')assert(G.NarutoGaara.shieldState(p)&&G.NarutoSandGuard.state(p).count>0,'Shield requires selection');
   if(m.id==='naruto-gaara'){
     const old=p.active;p.active=-1;Acceptance.resume();try{G.Combat.tick(.61,p,0)}finally{Acceptance.pause()}
     assert(G.NarutoGaara.active(p)?.kind==='gaara-sand-burst','basic requires selection');p.active=old;
   }
   inventory.push({id:m.id,name:m.def.name,category:m.id==='naruto-gaara'?'automatic-basic':'passive',level:m.lvl,slotless:true});
 }
 G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();p.frozen=true;p.active=0;
 const guide=[...document.querySelectorAll('.naruto-skill-entry')][[30001,30002,30006,30007].indexOf(dex)];
 const labels=[...guide.querySelectorAll('small')].map(el=>el.textContent);
 assert(labels.length===definitions.length,'guide skill count wrong');
 definitions.forEach((d,i)=>assert(labels[i].includes(d.passive?'常駐':'主動'),'guide activation wrong: '+d.id));
 return {dex,inventory,labels,activeSlots:p.slots.length,passives:learned.filter(m=>m.passive).length};
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in [False, True]:
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.evaluate(HARNESS)
            label = 'mobile' if mobile else 'desktop'
            report[label] = []
            for dex in [30001, 30002, 30006, 30007]:
                report[label].append(page.evaluate(CHECK, dex))
                page.evaluate('Acceptance.resume()')
                page.wait_for_timeout(100)
                page.screenshot(path=str(OUT / f'{label}-{dex}.png'))
            assert not errors, errors
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'heroes': 4, 'skills': sum(len(r['inventory']) for r in report['desktop']), 'viewports': list(report)}))

if __name__ == '__main__':
    main()
