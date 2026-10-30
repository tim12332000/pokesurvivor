"""Real three-choice offers guarantee Gates at character levels 4, 8, and 16."""
from pathlib import Path
import test_lee_gates_speed as runner

runner.OUT = Path(__file__).resolve().parents[1] / '.omx/state/lee-gates-milestones'
runner.CHECK = r"""() => {
 const A=Acceptance,p=A.p();A.leeArena();const out=[];
 for(const id of ['naruto-lotus','naruto-reverse-lotus','tackle'])if(p.slots.length<p.maxMoves)p.addMove(id);
 A.assert(p.slots.length===p.maxMoves,'full active slot fixture missing');
 const gate=cards=>cards.find(c=>c.key.endsWith(':naruto-gates'));
 for(const chosen of [[4,8,16],[],[8,16],[4,16]]){
   G.Combat.clearFields(p);p.moves=p.moves.filter(m=>m.id!=='naruto-gates');
   p.narutoMilestonesShown=new Set();let tier=0;const shown=[];
   for(let level=1;level<=20;level++){
     p.level=level;
     if(![4,8,16].includes(level)){
       A.assert(!gate(G.LevelUp.offer(p,100)),'unscheduled or deferred Gates card '+level);continue;
     }
     for(let n=0;n<100;n++)A.assert(gate(G.LevelUp.offer(p,3))?.guaranteed,'not guaranteed '+level);
     const cards=G.LevelUp.offer(p,3),card=gate(cards);
     for(const c of cards)c.onShown?.(p);
     A.assert(!gate(G.LevelUp.offer(p,100)),'reroll repeated opportunity '+level);
     if(chosen.includes(level)){
       A.assert(card.apply(p)!==false,'milestone rejected');tier++;
       A.assert(p.moves.find(m=>m.id==='naruto-gates').lvl===tier,'skipped a gate');
     }
     shown.push({level,tier,chosen:chosen.includes(level)});
   }
   out.push({chosen,opportunities:shown,finalTier:tier});
 }
 p.level=40;A.assert(!gate(G.LevelUp.offer(p,100)),'fourth gate offered');
 return {scenarios:out,opportunitiesPerRun:3,noDeferredOffers:true};
}"""

if __name__ == '__main__':
    runner.main()
