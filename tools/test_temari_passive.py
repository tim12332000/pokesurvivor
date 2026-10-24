"""Native permanent Kamatari acceptance, through the normal picker and cards.

Controlled open terrain makes hit counts reproducible. Pet movement, acquisition,
cooldowns, damage, progression, clones, migration and cleanup remain production.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_temari import CHROME, OUT, URL, boot

SETUP = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;
 A.pets=(owner=p)=>T.summons.filter(a=>a.owner===owner&&a.permanent&&!a.dead);
 A.petReset=()=>{A.reset();p.maxMoves=5;A.petEnabled=true;A.learn();A.mastery(0);A.rank('naruto-temari-blade-dance',1);T.syncPets(p);};
 A.until=(fn,seconds=15)=>{for(let t=0;t<seconds;t+=.01){if(fn())return;A.advance(.01);}A.assert(fn(),'pet state timed out');};
}"""

PROGRESSION = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,id='naruto-temari-blade-dance';
 A.assert(!p.hasMove(id),'starter already learned pet');p.level=8;
 A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='new:'+id),'pet unlocked before Lv9');
 p.addMove('naruto-temari-great-scythe');p.maxMoves=p.slots.length;
 const slots=p.slots.slice(),selected=p.activeGroup();p.level=9;
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card?.guaranteed,'Lv9 milestone absent at full slots');
 A.assert(card.apply(p)!==false,'full active slots prevented passive learn');
 const move=p.moves.find(m=>m.id===id),pets=A.pets();
 A.assert(move.passive&&!p.bind[id]&&p.slots.length===slots.length,'pet occupied/bound active slot');
 A.assert(p.activeGroup()===selected&&p.slots.every((g,i)=>g===slots[i]),'learning replaced active group references');
 A.assert(pets.length===1&&pets[0].phase==='wander','learn did not immediately create permanent pet');
 A.assert(!T.canCast(p,move),'passive still accepts active casting');
 A.petEnabled=true;const pet=pets[0];A.finish(25);
 A.assert(A.pets()[0]===pet&&pet.age>=25&&pet.cooldown===0,'idle pet expired or spent cooldown without enemies');
 return {level:p.level,slots:p.slots.length,id:pet.petId,age:pet.age,cooldown:pet.cooldown};
}"""

CYCLES = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.petReset();p.item='lifeorb';p.hp=p.maxHp/2;
 const hp=p.hp,e=A.spawn(140,0,'boss'),hits=A.watch(e),pet=A.pets()[0],events=[],old=p.cast;let ownerCasts=0;
 p.cast=function(...args){ownerCasts++;return old.apply(this,args)};
 try{for(let cycle=0;cycle<2;cycle++){
   A.until(()=>pet.phase==='move');const attack=pet.cast;
   A.assert(!T.activeFor(p),'autonomous attack replayed owner cast pose');
   A.until(()=>pet.phase==='slash');A.until(()=>pet.phase==='return');
   A.assert(attack.cuts===4&&pet.cuts===4,'pet cut cycle truncated '+attack.cuts);
   A.until(()=>pet.phase==='wander');events.push({cycle,serial:attack.serial,cuts:attack.cuts,cooldown:pet.cooldown});
   A.assert(A.pets()[0]===pet,'attack/return replaced pet');
 }}finally{p.cast=old}
 A.assert(events[0].serial!==events[1].serial&&hits.length===8,'two autonomous cycles did not produce eight actual hits');
 A.assert(hits.every(h=>h.owner&&h.id==='naruto-temari-blade-dance'&&h.damage>0),'pet damage attribution');
 A.assert(ownerCasts===0&&p.hp===hp,'autonomous pet paid cast recoil or called Player.cast');
 A.assert(A.pets().length===1,'second cycle spawned disposable replacement actors');
 return {events,hits:hits.length,ownerCasts,lifeorbLoss:hp-p.hp,pet:pet.petId};
}"""

QUANTITY = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];A.petReset();
 for(const Q of [0,5,10,20]){
   const before=A.pets().slice(),saved=before.map(a=>({a,cooldown:a.cooldown,age:a.age,x:a.x,y:a.y,cast:a.cast}));
   p.quantityBonus=p.quantityPicks=Q;T.syncPets(p);const now=A.pets();
   A.assert(now.length===Math.floor(1.25**Q),'quantity actor count capped '+Q+' '+now.length);
   A.assert(saved.every(v=>now.includes(v.a)&&v.a.cast===v.cast&&v.a.age===v.age&&v.a.x===v.x&&v.a.y===v.y&&v.a.cooldown===v.cooldown),'quantity reset existing pet state '+Q);
   A.assert(new Set(now.map(a=>a.petId)).size===now.length,'duplicate pet IDs');A.finish(.2);
   out.push({Q,count:now.length,retained:before.length});
 }
 // A new quantity card during an ongoing attack must keep the old attack timer.
 A.petReset();A.spawn(100,0,'boss');A.advance(.01);const pet=A.pets()[0],cast=pet.cast,cd=pet.cooldown,age=pet.age;
 p.quantityBonus=p.quantityPicks=5;T.syncPets(p);
 A.assert(A.pets().length===3&&A.pets().includes(pet)&&pet.cast===cast&&pet.cooldown===cd&&pet.age===age,'midattack quantity reset actor');
 return out;
}"""

RANKS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(const rank of [1,2,3,4,5])for(const L of [0,1,5]){
   A.petReset();A.rank('naruto-temari-blade-dance',rank);A.mastery(L);p.quantityBonus=p.quantityPicks=5;p.cdMul=.92;
   const e=A.spawn(100,0,'boss');e.r=300;const hits=A.watch(e);G.EnemyMgr.rebuildGrid();T.syncPets(p);A.advance(.001);
   const actors=A.pets().slice(),C=[4,4,5,5,6][rank-1]+(L?L+5:0),raw=[32,39,47,57,69][rank-1]*p.atk;
   A.assert(actors.length===3,'rank/mastery changed count');
   A.assert(actors.every(a=>a.cast.C===C&&Math.abs(a.cast.damage-raw)<1e-8),'rank/mastery snapshot '+JSON.stringify({rank,L,C,raw,actors:actors.map(a=>({C:a.cast.C,damage:a.cast.damage,phase:a.phase}))}));
   A.assert(actors.every(a=>Math.abs(a.cooldown-9.2)<1e-6),'cooldown cards did not scale pet cycles');
   A.finish(5);A.assert(hits.length===3*C,'native pet cut hit count '+rank+'/'+L+' '+hits.length+'/'+3*C);
   A.assert(hits.every(h=>Math.abs(h.raw-raw)<1e-5&&h.owner),'full per-cut rank damage');
   A.assert(actors.every(a=>A.pets().includes(a)&&a.phase==='wander'),'rank pet did not return');out.push({rank,L,C,count:actors.length,hits:hits.length,raw});
 }
 return out;
}"""

CLONES = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.petReset();A.mastery(5);p.quantityBonus=p.quantityPicks=5;
 const e=A.spawn(100,0,'boss'),hits=A.watch(e),card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');
 A.assert(card&&card.apply(p)!==false,'clone card missing');const clone=G.SelfClones.actors()[0];clone.x=clone.y=0;clone.target=e;
 T.syncPets(p);T.syncPets(clone);A.advance(.001);
 const owner=A.pets(),pets=A.pets(clone);A.assert(owner.length===3&&pets.length===3,'clone reduced permanent pet count');
 A.assert(pets.every(a=>owner.every(b=>a!==b&&a.petId!==b.petId)),'clone shares pet actors/IDs');
 A.finish(5);const own=hits.filter(h=>h.owner&&h.id==='naruto-temari-blade-dance'),copied=hits.filter(h=>h.clone&&h.id==='naruto-temari-blade-dance');A.assert(own.length===42&&copied.length===42,'clone pet real hit count '+own.length+'/'+copied.length);
 copied.forEach(h=>A.near(h.raw*3,own[0].raw,'clone pet damage one third exactly once'));
 G.SelfClones.clear();A.advance();A.assert(!A.pets(clone).length&&!T.stateFor(clone),'removed clone retained pet');
 return {ownerHits:own.length,cloneHits:copied.length,ratio:copied[0].raw/own[0].raw};
}"""

MIGRATION = r"""() => {
 const A=Acceptance,p=A.p();A.petReset();p.level=30;p.addMove('naruto-temari-typhoon');
 const pet=p.moves.find(m=>m.id==='naruto-temari-blade-dance'),heavy=p.moves.find(m=>m.id==='naruto-temari-great-scythe'),typhoon=p.moves.find(m=>m.id==='naruto-temari-typhoon');
 pet.passive=false;p.bind[pet.id]=3;const fused=[heavy,pet],selected=[typhoon];p.slots=[[pet],fused,selected];p.active=2;
 const moves=p.moves.slice();G.Moves.poolFor(p.mon);
 A.assert(p.slots.length===2&&p.slots[0]===fused&&p.slots[1]===selected&&p.activeGroup()===selected,'migration replaced/reselected existing groups');
 A.assert(fused.length===1&&fused[0]===heavy&&p.moves.every((m,i)=>m===moves[i]),'migration replaced/deleted learned moves');
 A.assert(pet.passive&&!Object.hasOwn(p.bind,pet.id)&&p.active===1,'migration passive/binding/index');
 p.slots=[fused,[pet]];p.active=1;G.Moves.poolFor(p.mon);
 A.assert(p.active===0&&p.activeGroup()===fused,'removed selected passive left invalid active index');
 const remaining=p.slots.map(g=>g.map(m=>m.id));p.slots.push(selected);return {groupIdentity:true,moveIdentity:true,selectedIdentity:true,remaining};
}"""

LIFECYCLE = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(const reason of ['pause','switch','death','world','clear']){
   A.petReset();const pet=A.pets()[0];A.spawn(140,0,'boss');A.finish(.3);const age=pet.age,cd=pet.cooldown,x=pet.x,y=pet.y,cast=pet.cast,world=G.World;
   if(reason==='pause'){G.Combat.updateFields(5);A.assert(pet.age===age&&pet.cooldown===cd&&pet.x===x&&pet.y===y&&pet.cast===cast,'paused pet advanced');}
   if(reason==='switch'){p.level=30;if(!p.hasMove('naruto-temari-typhoon'))p.addMove('naruto-temari-typhoon');A.select('naruto-temari-typhoon');A.finish(3);A.assert(A.pets().includes(pet)&&pet.phase==='wander','active switch removed pet');}
   if(reason==='death'){p.dead=true;A.advance();A.assert(!A.pets().length&&!T.stateFor(p),'dead owner retained pet');p.dead=false;}
   if(reason==='world'){G.World={...world};try{A.advance();A.assert(!A.pets().includes(pet),'old-world pet survived');}finally{G.World=world}}
   if(reason==='clear'){G.Combat.clearFields();A.assert(!A.pets().length&&!T.stateFor(p),'clear retained pet');}
   out.push(reason);
 }
 // Owner movement uses bounded roaming recovery rather than teleporting companions.
 A.petReset();A.finish(1);const pet=A.pets()[0],x=pet.x,y=pet.y;p.x+=500;A.advance(.01);
 A.assert(Math.hypot(pet.x-x,pet.y-y)<10&&Math.hypot(pet.x-p.x,pet.y-p.y)>400,'pet teleported with owner');
 return {reasons:out,followStep:Math.hypot(pet.x-x,pet.y-y)};
}"""


OBSTACLE_HOME = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.petReset();
 const e=A.spawn(140,100,'boss'),hits=A.watch(e),pet=A.pets()[0];A.until(()=>pet.phase==='slash');
 const W=G.World,saved={isFree:W.isFree,isWall:W.isWall,projectileBlock:W.projectileBlock};
 const blocked=(x,y,r=0)=>Math.hypot(x-36,y)<14+r;
 Object.assign(W,{isFree:(x,y,r=0)=>!blocked(x,y,r),isWall:(x,y)=>blocked(x,y),projectileBlock:(x,y,r=0)=>blocked(x,y,r)?{destructible:false}:false});
 const phases=[];
 try{
   A.until(()=>pet.phase==='return');phases.push(pet.phase);A.until(()=>pet.phase==='wander',6);phases.push(pet.phase);
   A.assert(!blocked(pet.x,pet.y,9),'pet returned inside wall/tree');
   A.until(()=>pet.phase==='move',15);phases.push(pet.phase);A.until(()=>pet.phase==='return');A.until(()=>pet.phase==='wander',6);
   A.assert(A.pets()[0]===pet&&hits.length===8,'blocked home starved second attack or replaced pet '+hits.length);
 }finally{Object.assign(W,saved)}
 return {phases,hits:hits.length,pet:pet.petId,position:[pet.x,pet.y]};
}"""


ROAM_REACH = r"""() => {
 const A=Acceptance,p=A.p();A.petReset();const pet=A.pets()[0];pet.x=-140;pet.y=0;
 const enemy=A.spawn(330,0,'boss'),hits=A.watch(enemy);A.until(()=>pet.phase==='move');
 A.until(()=>pet.phase==='return');A.assert(hits.length===4,'roaming offset shortened owner acquisition reach '+hits.length);
 A.until(()=>pet.phase==='wander');return {hits:hits.length,ownerRange:360,petStart:-140,target:330};
}"""


WANDER = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.petReset();const pet=A.pets()[0],id=pet.petId;
 let travel=0,moving=0,resting=0,near=0,samples=0,peak=0,maxStep=0;const destinations=new Set();
 for(let i=0;i<1800;i++){
   const x=pet.x,y=pet.y;A.advance(.01);const distance=Math.hypot(pet.x-p.x,pet.y-p.y),step=Math.hypot(pet.x-x,pet.y-y);
   travel+=step;peak=Math.max(peak,distance);maxStep=Math.max(maxStep,step);
   if(pet.roamTarget)destinations.add(Math.round(pet.roamTarget.x)+','+Math.round(pet.roamTarget.y));
   if(i>200){samples++;if(distance<45)near++;if(pet.moving)moving++;else resting++;}
   A.assert(pet.phase==='wander'&&distance<=176,'idle pet left nearby roaming region');
 }
 A.assert(travel>450&&destinations.size>=4&&moving>100&&resting>50,'idle pet did not independently walk and rest '+JSON.stringify({travel,destinations:destinations.size,moving,resting}));
 A.assert(near/samples<.25,'idle pet spent most time clinging to owner '+near+'/'+samples);
 const stationary={travel,destinations:destinations.size,moving,resting,nearRatio:near/samples,peak};
 // A walking owner changes the region only when needed. Pet positions remain
 // continuous and catch up under the leash instead of following every step.
 for(let i=0;i<900;i++){
   const x=pet.x,y=pet.y;p.x+=.8;A.advance(.01);const step=Math.hypot(pet.x-x,pet.y-y);
   maxStep=Math.max(maxStep,step);A.assert(step<6,'roaming pet teleported while owner walked');
   A.assert(Math.hypot(pet.x-p.x,pet.y-p.y)<231,'roaming leash let pet fall too far behind');
 }
 A.finish(3);A.assert(Math.hypot(pet.x-p.x,pet.y-p.y)<176&&A.pets()[0]===pet&&pet.petId===id,'moving owner lost roaming pet');
 // Place terrain on an actual chosen roaming destination. The pet must select
 // a reachable alternative while swept movement stays outside the obstacle.
 A.petReset();const obstaclePet=A.pets()[0];A.advance(.01);const point={...obstaclePet.roamTarget},W=G.World;
 const saved={isFree:W.isFree,isWall:W.isWall,projectileBlock:W.projectileBlock};
 const blocked=(x,y,r=0)=>Math.hypot(x-point.x,y-point.y)<14+r;
 Object.assign(W,{isFree:(x,y,r=0)=>!blocked(x,y,r),isWall:(x,y)=>blocked(x,y),projectileBlock:(x,y,r=0)=>blocked(x,y,r)?{destructible:false}:false});
 let alternate=false;
 try{for(let i=0;i<600;i++){
   A.advance(.01);A.assert(!blocked(obstaclePet.x,obstaclePet.y,9),'roaming pet walked inside terrain');
   if(obstaclePet.roamTarget&&Math.hypot(obstaclePet.roamTarget.x-point.x,obstaclePet.roamTarget.y-point.y)>24)alternate=true;
 }}finally{Object.assign(W,saved)}
 A.assert(alternate,'blocked roaming destination was never replaced');
 return {stationary,maxStep,ownerPosition:[p.x,p.y],blockedDestination:point,alternate};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'errors': [], 'failures': [], 'viewports': {}, 'ok': False}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, viewport, mobile in [('desktop', {'width':1200,'height':900}, False), ('mobile', {'width':390,'height':844}, True)]:
            if os.environ.get('TEMARI_VIEWPORTS') and label not in os.environ['TEMARI_VIEWPORTS'].split(','):
                continue
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            boot(page);page.evaluate(SETUP)
            result = report['viewports'][label] = {}
            for name, check in [('progression',PROGRESSION),('cycles',CYCLES),('quantity',QUANTITY),('ranks',RANKS),('clones',CLONES),('migration',MIGRATION),('lifecycle',LIFECYCLE),('obstacleHome',OBSTACLE_HOME),('wander',WANDER),('roamReach',ROAM_REACH)]:
                if os.environ.get('TEMARI_PASSIVE_CHECKS') and name not in os.environ['TEMARI_PASSIVE_CHECKS'].split(','):
                    continue
                print(label, name, flush=True)
                try:
                    result[name] = page.evaluate(check)
                except Exception as error:
                    result[name] = {'failure': str(error)}
                    report['failures'].append(label+':'+name+': '+str(error))
                    print(report['failures'][-1],flush=True)
            try:
                page.evaluate('Acceptance.petReset();Acceptance.finish(1)')
                page.screenshot(path=str(OUT / (label+'-permanent-idle.png')))
                page.evaluate('Acceptance.p().x+=120;Acceptance.advance(.1)')
                page.screenshot(path=str(OUT / (label+'-permanent-follow.png')))
                page.evaluate('Acceptance.spawn(Acceptance.p().x+140,Acceptance.p().y,"boss");Acceptance.until(()=>Acceptance.pets()[0].phase==="slash")')
                page.screenshot(path=str(OUT / (label+'-permanent-slash.png')))
                page.evaluate('Acceptance.until(()=>Acceptance.pets()[0].phase==="return")')
                page.screenshot(path=str(OUT / (label+'-permanent-return.png')))
                result['screenshots'] = [label+'-permanent-'+phase+'.png' for phase in ['idle','follow','slash','return']]
            except Exception as error:
                report['failures'].append(label+':screenshots: '+str(error))
            context.close()
        browser.close()
    report['ok'] = not (report['failures'] or report['errors'])
    target = OUT / ('report-permanent-pets-focused.json' if os.environ.get('TEMARI_PASSIVE_CHECKS') else 'report-permanent-pets.json')
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':report['ok'],'report':str(target),'failures':report['failures']}))
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
