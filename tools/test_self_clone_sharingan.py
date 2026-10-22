"""All five Sharingan stages on independently controlled card-created actors."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/self-clone/sharingan.json'
CHECK = r"""() => {
 const assert=(ok,msg)=>{if(!ok)throw Error(msg)},near=(a,b,msg)=>assert(Math.abs(a-b)<1e-6*Math.max(1,Math.abs(b)),msg+': '+a+' != '+b);
 G.Naruto.choose(30002);G.Flow.play();Acceptance.pause();Acceptance.arena();
 const p=G.Game.player,S=G.SelfClones,E=G.NarutoSharingan,P=G.NarutoSharinganPowers,random=Math.random;
 p.level=30;p.critChance=0;p.percentHealthDamage=0;p.lifestealRate=0;p.quantityPicks=0;p.quantityBonus=0;
 assert(p.addMove('naruto-sharingan'),'learn eye');const eye=p.moves.find(m=>m.id==='naruto-sharingan');
 const a=S.summon(p),b=S.summon(p),step=dt=>{Acceptance.resume();try{G.Combat.updateFields(dt)}finally{Acceptance.pause()}};
 const enemy=(x,y,boss=false)=>{const e=new G.Enemy({dex:19,hp:900000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;};
 const out={stages:[],actors:2};
 try{
   step(.001);const magnet=p.magnet;
   for(let stage=1;stage<=5;stage++){
     if(stage>1)assert(G.Moves.levelUp(eye)!==false,'source eye upgrade failed');
     step(.001);
     for(const actor of [p,a,b])assert(E.stage(actor)===stage&&E.stateFor(actor)?.stage===stage,'existing clone missing stage '+stage);
     assert(a.moves.find(m=>m.id===eye.id)!==eye&&a.moves.find(m=>m.id===eye.id)!==b.moves.find(m=>m.id===eye.id),'shared passive move instance');
     near(p.magnet,magnet,'source magnet drift while syncing clones');
     const shot=G.Moves.instance('naruto-fireball');
     for(const actor of [p,a,b]){
       assert(E.projectileBonus(actor,shot)===(stage>=3?1:0),'ranged bonus wrong at stage '+stage);
       assert(G.Quantity.snapshot(actor,shot).count===(stage>=3?2:1),'actual ranged snapshot missing eye bonus');
       if(stage===3)assert(E.stateFor(actor).images.length>0,'stage-three actor afterimage missing');
     }
     if(stage<=2){
       Math.random=()=>.01;G.Projectiles.clear();const mainHp=p.hp,cloneHp=a.hp;a.invuln=0;a.hurt(5);
       near(a.hp,cloneHp,'clone dodge failed');near(p.hp,mainHp,'clone dodge touched owner');
       const shots=G.Projectiles.all();assert(shots.length===(stage===2?3:0)&&shots.every(shot=>shot.owner===a),'clone counter count/ownership');
       if(stage===2){
         const cloneDamage=shots[0].dmg;G.Projectiles.clear();p.invuln=0;p.hurt(5);
         const mainShots=G.Projectiles.all();assert(mainShots.length===3&&mainShots.every(shot=>shot.owner===p),'main counter overwritten by clone');
         near(cloneDamage,mainShots[0].dmg/3,'counter damage scaled twice or not scaled');
       }
       Math.random=()=>.99;a.invuln=0;const hp=a.hp;a.hurt(5);assert(a.hp<hp,'clone dodge always succeeds');
     }
     out.stages.push(stage);
   }
   Math.random=()=>.99;G.Projectiles.clear();
   a.invuln=0;a.hp=a.maxHp;const hp=a.hp;a.hurt(10);near(hp-a.hp,10*(1-a.reduction)*(a.activeGroup().some(m=>m.kind==='melee')?.75:1)*.7,'clone Susanoo mitigation');
   a.invuln=0;const pureHp=a.hp;a.hurt(10,null,true);near(pureHp-a.hp,10,'pure damage incorrectly mitigated');
   const aState=P.stateFor(a),mainState=P.stateFor(p),bState=P.stateFor(b);
   assert(aState&&mainState&&bState&&aState!==mainState&&aState!==bState,'powers singleton shared between owners');
   const ages=[mainState.age,aState.age,bState.age];step(.05);
   for(const [i,actor] of [p,a,b].entries())near(P.stateFor(actor).age-ages[i],.05,'global update double-ticked actor powers');
   // Separate positions isolate maximum-health fields and attack-scaled slashes.
   G.EnemyMgr.clear();P.clear();p.x=p.y=0;a.x=1000;a.y=0;b.x=2000;b.y=0;
   const mainTarget=enemy(200,0),cloneTarget=enemy(1200,0),bossTarget=enemy(1200,20,true);
   P.update(p,4,.001);P.update(a,4,.001);P.update(b,4,.001);
   assert(P.holes.some(h=>h.owner===p)&&P.holes.some(h=>h.owner===a),'independent automatic pulls missing');
   const mainHole=P.holes.find(h=>h.owner===p),cloneHole=P.holes.find(h=>h.owner===a);
   const bystander=enemy(1245,0),beforePull=bystander.x;
   P.update(a,4,.1);assert(bystander.x<beforePull,'clone pull does not move targets');near(mainHole.age,0,'clone pull aged main hole');
   P.update(p,4,1);P.update(a,4,.9);
   assert(P.fields.some(f=>f.owner===p)&&P.fields.some(f=>f.owner===a),'clone permanent flame missing');
   assert(!P.holes.includes(mainHole)&&!P.holes.includes(cloneHole),'pull did not collapse');
   const mainBefore=mainTarget.hp,cloneBefore=cloneTarget.hp,bossBefore=bossTarget.hp;
   P.update(p,4,.5);P.update(a,4,.5);
   near(mainBefore-mainTarget.hp,9000,'main maxHP flame');near(cloneBefore-cloneTarget.hp,3000,'clone maxHP flame one-third');
   near(bossBefore-bossTarget.hp,750,'clone boss maxHP flame one-third');
   // Repeated owner-scoped patches do not stack within an actor.
   const field=P.fields.find(f=>f.owner===a);P.fields.push({...field,x:field.x+1});
   const before=cloneTarget.hp;P.update(a,4,.5);near(before-cloneTarget.hp,3000,'clone overlapping flames stacked');
   G.EnemyMgr.clear();P.clear();
   const mainSlash=enemy(60,0),cloneSlash=enemy(1060,0),mainSlashHp=mainSlash.hp,cloneSlashHp=cloneSlash.hp;
   P.update(p,5,.001);P.update(a,5,.001);
   const mainDamage=mainSlashHp-mainSlash.hp,cloneDamage=cloneSlashHp-cloneSlash.hp;
   // Enemy display rounds health loss; credited raw damage is asserted separately.
   assert(Math.abs(cloneDamage-mainDamage/3)<=1,'clone slash damage ratio');
   near(a.atk,p.atk/3,'actor attack ratio');
   assert(P.slashes.some(s=>s.owner===p)&&P.slashes.some(s=>s.owner===a),'independent clone slash missing');
   const mainPower=P.stateFor(p),mainEye=E.stateFor(p),mainMagnet=p.magnet;
   a.invuln=0;a.hurt(a.maxHp*100,null,true);step(.001);
   assert(!S.actors().includes(a)&&!E.stateFor(a)&&!P.stateFor(a),'dead clone retained Sharingan powers');
   assert(E.stateFor(p)===mainEye&&P.stateFor(p)===mainPower&&E.stage(p)===5&&E.stage(b)===5,'clone death cleared other eyes');
   near(p.magnet,mainMagnet,'clone death removed main magnet');
   const fresh=S.summon(p);step(.001);assert(E.stage(fresh)===5&&P.stateFor(fresh)?.stage===5,'new clone missed current learned stage');
   G.Combat.clearFields();assert(!P.fields.length&&!P.holes.length&&!P.slashes.length&&!E.stateFor(p),'scene clear retained passive effects');
   out.scaling='counter, slash and maxHP black flames at one third; boss flames reduced';
   out.lifecycle='existing/new clone upgrades, per-owner clocks, clone death isolation and scene clear';
   return out;
 }finally{Math.random=random;S.clear();G.Combat.clearFields();}
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
                page.wait_for_function("G.SelfClones && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.evaluate(HARNESS)
                report['viewports']['mobile' if mobile else 'desktop'] = page.evaluate(CHECK)
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
