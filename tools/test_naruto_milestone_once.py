"""Native milestone cards: first real display once per skill and run, then weighted."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/naruto-milestone-once/report.json'
CHECK = r"""dex => {
 const assert=(ok,msg)=>{if(!ok)throw Error(msg)},C=G.NarutoSkillCatalog,random=Math.random,out={dex,skills:[]};
 const ids=C.extraPools.get(dex),milestones=ids.map((id,i)=>({id,level:G.Moves.BY_ID[id].learnLevel||(i===0?3:6)}));
 const fresh=()=>{
   G.RunUI.closeLevelUp();G.Game.toUI();G.Naruto.choose(dex);G.Flow.play();Acceptance.pause();Acceptance.arena();
   const p=G.Game.player;p.moves=p.moves.filter(m=>!ids.includes(m.id));
   p.slots=p.slots.map(group=>group.filter(m=>!ids.includes(m.id))).filter(group=>group.length);p.active=0;
   p.bind={};p.banned=new Set();p.rerolls=0;p.maxMoves=6;p.level=1;delete p.narutoMilestonesShown;
   return p;
 };
 const show=(p,cards=G.LevelUp.offer(p,3))=>{assert(cards.length===3,'native offer lost choices');
   G.RunUI.showLevelUp(p.level,cards,c=>c.apply(p));assert(document.querySelectorAll('#cards .card').length===3,'native cards not rendered');return cards;};
 const ordinary=(p,id)=>{
   const c=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);assert(c&&!c.guaranteed&&!c.tag.includes('首次解鎖'),'declined card lost random eligibility or stayed guaranteed');
   Math.random=()=>.999999999;
   try{assert(!G.LevelUp.offer(p,3).some(c=>c.key==='new:'+id),'declined card still forced despite stat-only random choice');}
   finally{Math.random=random;}
 };
 try{
   for(const milestone of milestones){
     const {id,level}=milestone;let p=fresh();p.banned=new Set(ids.filter(other=>other!==id));p.level=level-1;
     assert(!G.LevelUp.offer(p,100).some(c=>c.key==='new:'+id),'skill offered before level '+id);
     p.level=level;
     for(let i=0;i<20;i++)assert(G.LevelUp.offer(p,3).some(c=>c.key==='new:'+id&&c.guaranteed),'first eligible offer not guaranteed '+id);
     assert(!p.narutoMilestonesShown,'preview consumed first display');
     const first=show(p);assert(first.some(c=>c.key==='new:'+id&&c.tag.includes('首次解鎖')),'unlock tag missing');
     assert(p.narutoMilestonesShown?.has(id),'native display did not consume milestone');
     const other=first.findIndex(c=>c.key!=='new:'+id);assert(other>=0,'no alternative card');G.RunUI.pick(other);
     assert(!p.hasMove(id),'choosing another card learned declined skill');ordinary(p,id);
     p=fresh();p.banned=new Set(ids.filter(other=>other!==id));p.level=level;
     show(p);G.RunUI.reroll();assert(p.rerolls===1,'native reroll did not execute');ordinary(p,id);G.RunUI.closeLevelUp();
     p=fresh();p.banned=new Set(ids.filter(other=>other!==id));p.level=level;
     show(p);G.RunUI.closeLevelUp();ordinary(p,id);
     p=fresh();p.banned=new Set(ids.filter(other=>other!==id));p.level=level;
     assert(p.addMove(id),'learn-before-display fixture failed');assert(!G.LevelUp.offer(p,100).some(c=>c.key==='new:'+id),'already learned skill offered as new');
     p=fresh();p.banned=new Set(ids);p.level=level;
     assert(!G.LevelUp.offer(p,100).some(c=>c.key==='new:'+id),'banned milestone forced');
     // Auto-pick uses the real card callback and keeps the prior attack selection.
     p=fresh();p.banned=new Set(ids.filter(other=>other!==id));p.level=level;
     const active=p.activeGroup().map(m=>m.id).join('|'),cards=show(p),index=cards.findIndex(c=>c.key==='new:'+id);
     Math.random=()=> (index+.1)/cards.length;
     try{assert(G.RunUI.pickRandom(),'auto pick failed');}finally{Math.random=random;}
     assert(p.hasMove(id)&&p.narutoMilestonesShown.has(id),'auto pick missed milestone');
     assert(p.activeGroup().map(m=>m.id).join('|')===active||!active,'auto-pick changed prior attack selection');
     out.skills.push({id,level,checks:'preview, first display, choose-other, reroll, close, ban, learned-before, auto-pick'});
   }
   let p=fresh();p.level=99;
   const first=show(p),firstIds=first.filter(c=>c.guaranteed).map(c=>c.key.slice(4));
   assert(firstIds.length===Math.min(3,ids.length),'simultaneous pending skills not reserved');
   const pending=ids.filter(id=>!firstIds.includes(id));G.RunUI.closeLevelUp();
   const next=G.LevelUp.offer(p,3);
   for(const id of pending)assert(next.some(c=>c.key==='new:'+id&&c.guaranteed),'overflow milestone lost first opportunity');
   assert(next.every(c=>!firstIds.includes(c.key.slice(4))||!c.guaranteed),'already displayed pending skill forced again');
   out.pending={first:firstIds.length,next:pending.length};
   p=fresh();p.level=99;const evoInfo=G.Moves.evoInfo;
   G.Moves.evoInfo=move=>move===p.moves[0]?{ready:true,name:'fixture',text:'fixture'}:null;
   try{
     const cards=show(p);assert(cards[0].type==='evo'&&cards.filter(c=>c.guaranteed).length===2,'evolution priority displaced or overflowed milestone choices');
     G.RunUI.closeLevelUp();assert(ids.some(id=>!p.narutoMilestonesShown.has(id)),'undisplayed milestones consumed behind evolution');
   }finally{G.Moves.evoInfo=evoInfo;}
   const passive=milestones.find(m=>G.Moves.BY_ID[m.id].passive);
   if(passive){
     p=fresh();p.level=passive.level;p.banned=new Set(ids.filter(id=>id!==passive.id));
     assert(p.addMove('naruto-kunai'),'full-slot fixture failed');p.maxMoves=p.slots.length;
     const active=p.activeGroup().map(m=>m.id).join('|'),count=p.slots.length,choices=show(p);
     const index=choices.findIndex(c=>c.key==='new:'+passive.id);assert(index>=0,'full slots hid passive milestone');G.RunUI.pick(index);
     assert(p.hasMove(passive.id)&&p.slots.length===count&&p.activeGroup().map(m=>m.id).join('|')===active,'passive milestone consumed/replaced active slot');
     out.fullSlotPassive=passive.id;
   }
   // Fresh Player instances reset run metadata without touching the previous player.
   p=fresh();const future=milestones.find(m=>m.level>1);p.level=future.level;
   p.banned=new Set(ids.filter(id=>id!==future.id));show(p);const previous=p;
   G.RunUI.closeLevelUp();G.Game.toUI();G.Naruto.choose(dex);G.Flow.play();Acceptance.pause();
   p=G.Game.player;assert(p!==previous&&!p.narutoMilestonesShown?.has(future.id),'new run retained shown milestone');
   if(!p.hasMove(future.id)){p.level=future.level;p.banned=new Set(ids.filter(id=>id!==future.id));assert(G.LevelUp.offer(p,3).some(c=>c.key==='new:'+future.id&&c.guaranteed),'new run lost unlock opportunity');}
   out.reset=true;return out;
 }finally{Math.random=random;G.RunUI.closeLevelUp();}
}"""


def main():
    report = {'viewports': {}, 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        try:
            for mobile in [False, True]:
                context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda error: report['errors'].append(str(error)))
                page.goto(URL)
                page.wait_for_function("G.NarutoSkillCatalog && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.evaluate(HARNESS)
                report['viewports']['mobile' if mobile else 'desktop'] = [page.evaluate(CHECK, dex) for dex in [30001, 30002, 30006, 30007]]
                context.close()
            assert not report['errors'], report['errors']
            report['ok'] = True
        finally:
            browser.close()
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
