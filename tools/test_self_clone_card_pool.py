"""Verify repeatable clone-card eligibility and measure seeded three-card offers.

Requires the repository HTTP server on port 8004.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/self-clone/card-pool.json'
CHECK = r"""dex => {
 const assert=(ok,msg)=>{if(!ok)throw Error(msg)},key='stat:selfClone',random=Math.random;
 G.Naruto.choose(dex);G.Flow.play();Acceptance.pause();Acceptance.arena();
 const p=G.Game.player,S=G.SelfClones,C=G.NarutoSkillCatalog,report={dex,stages:{}};
 const def=G.LevelUp.STATS.find(s=>s.id==='selfClone');
 assert(def&&!def.max,'clone card has a selection cap');
 const eligible=()=>{const card=G.LevelUp.offer(p,1000).find(c=>c.key===key);assert(card,'clone excluded from eligible pool');return card;};
 const sample=label=>{
   // Consume real first-display milestone opportunities before measuring the
   // ordinary weighted pool. Merely previewing an offer must not consume them.
   while(G.LevelUp.offer(p,1000).some(card=>card.guaranteed)){
     G.RunUI.showLevelUp(p.level,G.LevelUp.offer(p,3),card=>card.apply(p));
     G.RunUI.closeLevelUp();
   }
   let seed=0x5eed,hits=0,longestGap=0,gap=0;
   Math.random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
   try{for(let i=0;i<1000;i++){
     const cards=G.LevelUp.offer(p,3);assert(cards.length===3,'offer lost choices');
     if(cards.some(c=>c.key===key)){hits++;gap=0;}else{gap++;longestGap=Math.max(longestGap,gap);}
   }}finally{Math.random=random;}
   const all=G.LevelUp.offer(p,1000),card=all.find(c=>c.key===key);assert(card&&hits>0,'clone vanished: '+label);
   report.stages[label]={offers:1000,hits,longestGap,eligible:all.length,weight:card.w};
 };
 try{
   sample('early');
   for(let i=0;i<200;i++){
     const before=p.statsTaken.selfClone||0,card=eligible();
     assert(card.apply(p)!==false,'repeat clone pick rejected '+i);
     assert(p.statsTaken.selfClone===before+1&&S.actors().length===1,'repeat pick did not summon exactly one clone');
     const actor=S.actors()[0];actor.dead=true;actor.hp=0;
     assert(S.actors().length===0,'dead clone remains active');S.clear();
   }
   assert(p.statsTaken.selfClone===200,'repeat pick count lost');sample('after200PicksAndDeaths');
   p.level=100;
   for(const definition of [C.byDex.get(dex),...(C.extraPools.get(dex)||[]).map(id=>G.Moves.BY_ID[id])]){
     if(!p.hasMove(definition.id))assert(p.addMove(definition.id),'late skill learn failed');
     const move=p.moves.find(m=>m.id===definition.id);while(G.Moves.nextUpText(move))G.Moves.levelUp(move);
   }
   p.maxMoves=p.slots.length;sample('lateFullSlots');
   p.banned=new Set(['selfClone',key,...G.Moves.poolFor(p.mon)]);
   eligible();sample('lateBans');
   for(const stat of G.LevelUp.STATS)if(stat.max)p.statsTaken[stat.id]=stat.max;
   sample('lateCappedStats');
   const evoInfo=G.Moves.evoInfo;
   G.Moves.evoInfo=move=>move===p.moves[0]?{ready:true,name:'fixture',text:'fixture'}:null;
   try{const offers=G.LevelUp.offer(p,3);assert(offers[0].type==='evo','evolution priority fixture failed');eligible();sample('evolutionPriority');}
   finally{G.Moves.evoInfo=evoInfo;}
   const count=p.statsTaken.selfClone,card=eligible();let applied=false;
   G.RunUI.showLevelUp(p.level,[card],picked=>{picked.apply(p);applied=true;});
   assert(G.RunUI.pickRandom()&&applied&&p.statsTaken.selfClone===count+1,'auto pick failed clone card');
   S.clear();G.Combat.clearFields();eligible();
   p.dead=true;p.hp=0;eligible();p.dead=false;p.hp=p.maxHp;
   G.Game.toUI();G.Naruto.choose(dex);G.Flow.play();Acceptance.pause();
   assert(!G.Game.player.statsTaken.selfClone,'new run retained clone selections');
   assert(G.LevelUp.offer(G.Game.player,1000).some(c=>c.key===key),'new run excluded clone');
   report.repeatPicks=201;report.lifecycle='clone death, clear, owner death, auto pick and new run retain eligibility';
   return report;
 }finally{Math.random=random;S.clear();}
}"""


def main():
    report = {'heroes': [], 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        context = browser.new_context(service_workers='block')
        page = context.new_page()
        page.on('pageerror', lambda error: report['errors'].append(str(error)))
        try:
            page.goto(URL)
            page.wait_for_function("G.SelfClones && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.evaluate(HARNESS)
            for dex in [30001, 30002, 30006, 30007]:
                report['heroes'].append(page.evaluate(CHECK, dex))
            assert not report['errors'], report['errors']
            report['ok'] = True
        finally:
            browser.close()
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
