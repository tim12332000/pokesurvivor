"""Temari's permanent summons pursue live targets without remote slashes."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_temari as native
import test_temari_passive as passive

OUT = Path(__file__).resolve().parents[1] / '.omx/state/temari-pursuit'
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out={};
 A.petReset();const e=A.spawn(140,0,'boss'),hits=A.watch(e);A.advance(.01);
 const pet=A.pets()[0];e.x=280;G.EnemyMgr.rebuildGrid();A.finish(3);
 A.assert(hits.length===4,'moving boss escaped initial pursuit: '+hits.length);
 A.assert(p.x===0&&p.y===0,'summon moved owner');out.movingHits=hits.length;
 // Keep moving during the real combination. Every hurt must remain in range.
 A.petReset();const runner=A.spawn(130,0,'boss'),moving=A.watch(runner);
 let remote=false;const hurt=runner.hurt;runner.hurt=function(...args){
   const a=A.pets()[0];remote ||= Math.hypot(this.x-a.x,this.y-a.y)>a.cast.radius+(this.r||0)+1e-6;
   return hurt.apply(this,args)};
 for(let i=0;i<170;i++){runner.x+=.9;G.EnemyMgr.rebuildGrid();A.advance(.01)}
 A.assert(moving.length===4&&!remote,'moving combo missed or dealt remote damage '+moving.length);
 out.comboHits=moving.length;
 // Target death and range escape end pursuit and leave the owner in control.
 for(const reason of ['dead','range']){
   A.petReset();const target=A.spawn(140,0,'boss'),h=A.watch(target);A.advance(.01);
   if(reason==='dead')target.dead=true;else target.x=2000;
   G.EnemyMgr.rebuildGrid();A.finish(2);
   A.assert(h.length===0&&A.pets()[0].phase!=='move','invalid target retained pursuit '+reason);
   out[reason]=true;
 }
 // A new obstruction cannot be crossed while refreshing the live destination.
 A.petReset();const blocked=A.spawn(140,0,'boss'),blockedHits=A.watch(blocked);A.advance(.01);
 const W=G.World,saved={projectileBlock:W.projectileBlock,isFree:W.isFree,isWall:W.isWall};
 Object.assign(W,{projectileBlock:(x,y)=>x>=60&&x<=100?{destructible:false}:false,
   isFree:x=>x<60||x>100,isWall:x=>x>=60&&x<=100});
 try{A.finish(2);A.assert(blockedHits.length===0,'pursuit crossed wall');}
 finally{Object.assign(W,saved)}out.wall=true;
 A.petReset();const paused=A.spawn(140,0,'boss');A.advance(.01);
 const resting=A.pets()[0],age=resting.age,px=resting.x;T.update(1);
 A.assert(resting.age===age&&resting.x===px,'paused summon pursued target');out.pause=true;
 A.petReset();const evasive=A.spawn(140,0,'boss');A.advance(.01);const chaser=A.pets()[0];
 for(let i=0;i<350;i++){evasive.x=0;evasive.y=i%2?300:-300;G.EnemyMgr.rebuildGrid();A.advance(.01)}
 A.assert(chaser.phase!=='move','unreachable moving target retained endless pursuit');out.bounded=true;
 // Growing C extends the finite combination; the approach budget must not
 // truncate legal later cuts while following a moving boss.
 out.growth=[];
 const growthCases=[];for(const L of [0,1,5])for(const Q of [0,1,5,20])growthCases.push([L,Q,300]);
 growthCases.push([1,20,400]);
 for(const [L,Q,speed] of growthCases){
   A.petReset();A.mastery(L);p.quantityPicks=p.quantityBonus=Q;T.syncPets(p);
   const target=A.spawn(130,0,'boss'),h=A.watch(target);target.r=4;
   // Isolate one real summon cycle while retaining the full quantity snapshot.
   for(const pet of A.pets().slice(1))pet.cooldown=999;
   let attack;
   for(let i=0;i<600;i++){
     const t=i*.01;target.x=130*Math.cos(t*speed/130);target.y=130*Math.sin(t*speed/130);
     G.EnemyMgr.rebuildGrid();A.advance(.01);const pet=A.pets()[0];
     if(!attack&&pet.phase==='move')attack=pet.cast;
   }
   A.assert(attack&&attack.cuts===attack.C&&h.length===attack.C,
     'moving growth truncated '+JSON.stringify({L,Q,speed,cuts:attack?.cuts,C:attack?.C,hits:h.length}));
   out.growth.push({L,Q,speed,cuts:attack.cuts,hits:h.length});
 }
 // Cancellation from either callback must stop this wave and every sibling pet.
 out.cancel={};
 for(const reason of ['hurtClear','onDealtClear','hurtDeath','onDealtDeath']){
   A.petReset();p.quantityPicks=p.quantityBonus=5;T.syncPets(p);
   const first=A.spawn(100,0,'boss'),second=A.spawn(105,0,'boss');
   const firstHits=A.watch(first),secondHits=A.watch(second),original=first.hurt,oldDealt=p.onDealt;
   const cancel=()=>{if(reason.endsWith('Clear')){
     p.moves=p.moves.filter(m=>m.digiMode!=='temari-blade-dance');G.Combat.clearFields(p);
   }else{p.hp=0;p.dead=true}};
   if(reason.startsWith('hurt'))first.hurt=function(...args){const result=original.apply(this,args);cancel();return result;};
   else p.onDealt=cancel;
   try{A.finish(3);A.assert(firstHits.length===1&&secondHits.length===0,'callback leaked summon damage '+reason);
     A.assert(!T.summons.length,'callback retained cancelled summon '+reason);
     out.cancel[reason]={first:firstHits.length,second:secondHits.length};
   }finally{p.onDealt=oldDealt;p.hp=p.maxHp;p.dead=false;}
 }
 // Clearing one owner must advance every interleaved surviving clone once.
 A.petReset();p.quantityPicks=p.quantityBonus=5;T.syncPets(p);
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');
 A.assert(card&&card.apply(p)!==false,'clone card missing');
 const clone=G.SelfClones.actors()[0];clone.x=clone.y=0;T.syncPets(clone);
 const owned=A.pets(),copied=A.pets(clone),mixed=[];
 for(let i=0;i<owned.length;i++){mixed.push(owned[i],copied[i]);copied[i].cooldown=999;}
 T.summons.splice(0,T.summons.length,...mixed);
 for(const pet of owned){pet.phase='slash';pet.nextCut=pet.age;pet.x=100;pet.y=0;}
 const target=A.spawn(100,0,'boss'),original=target.hurt;
 target.hurt=function(...args){const result=original.apply(this,args);
   p.moves=p.moves.filter(m=>m.digiMode!=='temari-blade-dance');T.clear(p);return result;};
 const before=copied.map(a=>a.age);A.advance(.01);
 copied.forEach((a,i)=>A.near(a.age-before[i],.01,'surviving clone advanced twice'));
 A.assert(!A.pets().length&&A.pets(clone).length===3,'owner clear removed clone pets');out.mixedOwner=true;
 return out;
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
        result = {}
        for label, viewport in [('desktop', {'width':1200,'height':900}), ('mobile', {'width':390,'height':844})]:
            page = browser.new_page(viewport=viewport, is_mobile=label=='mobile', has_touch=label=='mobile')
            native.boot(page)
            page.evaluate(passive.SETUP)
            result[label] = page.evaluate(CHECK)
            page.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(result, indent=2), 'utf-8')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
