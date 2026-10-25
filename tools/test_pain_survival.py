"""Native Six Paths survival regressions; no replacement AI or damage handlers."""
import json
from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-survival'

NARAKA_HP = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out={};
 const saved={maxHp:p.maxHp,hp:p.hp,moves:p.moves};
 const bodies=()=>P.actorsFor(p);
 const snapshot=()=>bodies().map(b=>({path:b.path,maxHp:b.maxHp,hp:b.hp,dead:b.dead}));
 try{
   p.maxHp=p.hp=200;A.reset();const bs=bodies();
   A.assert(bs.length===5&&new Set(bs.map(b=>b.path)).size===5,'all five support paths must exist');
   A.assert(bs.every(b=>b.maxHp===400&&b.hp===400),'every support must spawn at twice owner maximum HP');
   out.spawn=snapshot();
   bs.forEach(b=>b.hurt(60,null,true));A.assert(bs.every(b=>b.hp===340),'native support damage fixture failed');
   p.addMaxHp(20);A.advance();
   A.assert(p.maxHp===220&&bs.every(b=>b.maxHp===440&&b.hp===380),'native max HP growth failed to preserve support missing health');
   out.growth={owner:p.maxHp,actors:snapshot()};
   A.finish(.25);A.assert(bs.every(b=>b.hp===380),'repeated capacity sync duplicated max HP healing');
   p.maxHp=100;A.advance();A.assert(bs.every(b=>b.maxHp===200&&b.hp===140),'support shrink failed to preserve missing health');
   p.maxHp=20;A.advance();A.assert(bs.every(b=>b.maxHp===40&&b.hp===1),'support shrink did not clamp a living body to one HP');
   out.shrink={owner:p.maxHp,actors:snapshot()};
   p.moves=p.moves.filter(m=>m.id!=='naruto-pain-repair');
   A.finish(.5); // Let native damage invulnerability expire before the lethal hit.
   bs.forEach(b=>b.hurt(b.maxHp+1,null,true));A.assert(bs.every(b=>b.dead),'native support death fixture failed');
   p.maxHp=p.hp=240;A.advance();
   A.assert(bs.every(b=>b.dead&&b.maxHp===480),'dead support capacity did not track current owner maximum HP');
   A.finish(16.4);
   A.assert(bs.every(b=>!b.dead&&b.maxHp===480&&b.hp===480),'every support must revive full at the current double HP ratio');
   out.revive={owner:p.maxHp,actors:snapshot()};
   return out;
 }finally{p.maxHp=saved.maxHp;p.hp=saved.hp;p.moves=saved.moves;A.reset()}
}"""

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out={};
 const bodies=()=>P.actorsFor(p), body=k=>bodies().find(b=>b.path===k);
 // Real native Enemy.update, projectile flight/collision and telegraphed hazards.
 function step(seconds){A.resume();try{for(let i=0;i<Math.ceil(seconds*100);i++){
   for(const e of G.EnemyMgr.all())e.update(.01,p);
   G.EnemyMgr.rebuildGrid();G.Combat.tick(.01,p,0);G.Combat.updateFields(.01);
   G.Projectiles.update(.01,p,G.EnemyMgr.all());G.Hazards.update(.01);G.Combat.resolve(.01,p,0);
 }}finally{A.pause()}}
 function fresh(){A.reset();G.Hazards.clear();G.Combat.clearFields();A.resume();G.Combat.updateFields(.001);A.pause();return bodies()}
 function zone(b,dmg=5){return G.Hazards.add({kind:'zone',x:b.x,y:b.y,r:16,delay:.01,dmg,type:'normal',pure:true,color:'#f80'})}
 let bs=fresh();A.assert(bs.length===5,'initial family must keep five records');
 const initial=bs.map(b=>({path:b.path,hp:b.hp,maxHp:b.maxHp,formed:b.formed,protection:b.protectionRemaining}));
 A.assert(bs.every(b=>b.formed&&b.protectionRemaining>1.4),'initial safe spawn protection missing');
 A.assert(bs.every(b=>b.maxHp===p.maxHp*2),'all support capacities must be twice Tendo maximum HP');
 A.spawn(145,0);A.ready('missiles','summon','soul');
 bs.forEach(b=>{zone(b,1000);b.hurt(1000,null,true)});step(.15);
 A.assert(bs.every(b=>b.hp===b.maxHp&&!b.dead&&b.protectionRemaining>1.2),'spawn wiped or hazard erased protection');
 A.assert(!P.actionsFor(p).some(a=>a.body),'protected bodies attacked');
 G.Hazards.clear();step(1.5);const h=body('human');const hp=h.hp;zone(h,5);step(.03);
 A.assert(h.hp<hp&&!h.dead,'unprotected body must take native ground damage');
 step(.5);h.hurt(h.maxHp+1,null,true);A.assert(h.dead,'supports became immortal after protection');out.spawn={initial,hazardDamage:hp-(hp-5),killable:h.dead};

 A.reset();G.Hazards.clear();p.aim=0;const enemy=A.spawn(145,0);step(1);
 const rear=bodies().filter(b=>['asura','animal','naraka'].includes(b.path));
 A.assert(rear.every(b=>b.x<p.x+10&&Math.hypot(b.x-enemy.x,b.y-enemy.y)>70),'rear supports pursued melee enemy');
 const rearSeparation=Math.min(...rear.flatMap((b,i)=>rear.slice(i+1).map(other=>Math.hypot(b.x-other.x,b.y-other.y))));
 A.assert(rearSeparation>28,'settled rear supports overlap instead of spreading '+rearSeparation);
 A.assert(Math.hypot(body('preta').x-p.x,body('preta').y-p.y)<85,'Preta left close guard');
 A.assert(!P.actionsFor(p).some(a=>a.kind==='soul'),'unready Human pursued soul');
 out.formation=rear.map(b=>({path:b.path,x:b.x,y:b.y}));
 const human=body('human');human.x=65;human.y=0;A.ready('soul');step(2.5);
 A.assert(enemy.hp<100000,'ready Human never completed native soul damage');
 A.assert(!P.actionsFor(p).some(a=>a.kind==='soul')&&human.x<65,'Human failed to withdraw after soul');
 human.x=90;human.y=0;human.hurt(human.maxHp*.7,null,true);A.ready('soul');const prior=Math.hypot(human.x-p.x,human.y-p.y);step(.6);
 A.assert(human.retreating&&Math.hypot(human.x-p.x,human.y-p.y)<prior,'low HP Human pursued instead of retreating');
 A.assert(!P.actionsFor(p).some(a=>a.body===human),'low HP Human started attack');
 const damaged=human.hp;step(.5);A.assert(human.hp===damaged&&human.retreating,'retreat healed or oscillated without recovery');out.retreat={hp:damaged,distance:Math.hypot(human.x-p.x,human.y-p.y)};
 // Recovery requires a genuinely safe regroup; proximity, warning and recent damage each block it.
 enemy.x=human.x+30;enemy.y=human.y;G.EnemyMgr.rebuildGrid();step(3.5);
 A.assert(human.hp===damaged,'nearby enemy did not block recovery');G.EnemyMgr.clear();
 const warning=G.Hazards.add({kind:'zone',x:0,y:0,r:300,delay:20,dmg:99,color:'#f00'});step(.4);
 A.assert(human.hp===damaged,'telegraphed hazard allowed regroup healing');G.Hazards.clear();
 human.x=20;human.y=0;step(6);
 A.assert(!human.retreating&&human.hp>=human.maxHp*.5,'safe regroup did not restore Human combat availability');
 const healed=human.hp;step(1);A.assert(human.hp===healed,'safe recovery exceeded retreat threshold');out.recovery={before:damaged,after:healed};
 const max=p.maxHp,cap=human.maxHp,current=human.hp;p.maxHp+=20;step(.01);
 A.assert(Math.abs(human.hp-current-(human.maxHp-cap))<1e-6,'max HP card did not preserve missing-health delta');p.maxHp=max;step(.01);
 const evader=body('animal');const hazard=G.Hazards.add({kind:'zone',x:evader.x,y:evader.y,r:85,delay:3,dmg:80,color:'#f00'});
 step(1.5);A.assert(!G.Hazards.inside(hazard,evader.x,evader.y,evader.r),'rear support failed to leave native warning');out.evasion=true;G.Hazards.clear();

 // Rear weapons originate at their body: owner visibility/range cannot substitute.
 out.bodyOrigin=[];
 for(const [kind,path,range] of [['missiles','asura',320],['summon','animal',300]]){
   A.reset();G.Hazards.clear();let caster=body(path);caster.x=-100;caster.y=0;
   A.spawn(range-50,0);A.ready(kind);A.advance();
   A.assert(!P.actionsFor(p).some(a=>a.kind===kind),'owner range incorrectly enabled rear weapon '+kind);
   A.assert(p.moves.find(m=>m.id==='naruto-pain-'+kind).t<=0,'out-of-body-range burned cooldown '+kind);
   A.reset();G.Hazards.clear();caster=body(path);caster.x=-100;caster.y=0;
   A.spawn(-range-50,0);A.ready(kind);A.advance();
   A.assert(P.actionsFor(p).some(a=>a.kind===kind),'body range incorrectly limited by owner '+kind);
   A.reset();G.Hazards.clear();caster=body(path);caster.x=-100;caster.y=0;A.spawn(100,0);
   const W=G.World,saved={isFree:W.isFree,isWall:W.isWall,projectileBlock:W.projectileBlock};
   Object.assign(W,{isFree:x=>x<-55||x>-45,isWall:x=>x>=-55&&x<=-45,projectileBlock:x=>x>=-55&&x<=-45?{destructible:false}:false});
   try{A.ready(kind);A.advance();A.assert(!P.actionsFor(p).some(a=>a.kind===kind),'owner LOS bypassed body wall '+kind)}finally{Object.assign(W,saved)}
   A.reset();G.Hazards.clear();caster=body(path);caster.x=100;caster.y=0;A.spawn(150,0);
   Object.assign(W,{isFree:x=>x<45||x>55,isWall:x=>x>=45&&x<=55,projectileBlock:x=>x>=45&&x<=55?{destructible:false}:false});
   try{A.ready(kind);A.advance();A.assert(P.actionsFor(p).some(a=>a.kind===kind),'owner wall blocked clear body LOS '+kind)}finally{Object.assign(W,saved)}
   out.bodyOrigin.push(kind);
 }
 A.reset();G.Hazards.clear();let walker=body('human');walker.x=0;walker.y=0;let victim=A.spawn(140,0);
 G.Hazards.add({kind:'zone',x:victim.x,y:victim.y,r:30,delay:3,dmg:80,color:'#f00'});A.ready('soul');A.advance();
 A.assert(!P.actionsFor(p).some(a=>a.kind==='soul'),'Human approached a target inside ground warning');
 A.assert(p.moves.find(m=>m.id==='naruto-pain-soul').t<=0,'unsafe soul target consumed cooldown');
 A.reset();G.Hazards.clear();walker=body('human');walker.x=0;walker.y=0;victim=A.spawn(140,0);A.ready('soul');A.advance();
 A.assert(P.actionsFor(p).some(a=>a.kind==='soul'&&a.phase==='grasp')&&Math.hypot(walker.x-victim.x,walker.y-victim.y)<=36,'soul teleport cancellation fixture absent');
 G.Hazards.add({kind:'zone',x:victim.x,y:victim.y,r:30,delay:3,dmg:80,color:'#f00'});A.advance();
 A.assert(!P.actionsFor(p).some(a=>a.kind==='soul'),'Human continued into newly warned destination');
 A.assert(victim.hp===100000&&p.moves.find(m=>m.id==='naruto-pain-soul').t>4,'unsafe grasp dealt damage or reset its started cooldown');out.soulWarning=true;

 A.reset();G.Hazards.clear();const original=p.moves;p.moves=original.filter(m=>m.id!=='naruto-pain-repair');
 const dead=body('asura');dead.hurt(dead.maxHp+1,null,true);const serial=dead.deathSerial;
 const W=G.World,free=W.isFree;W.isFree=()=>false;
 try{step(16.3);A.assert(dead.dead&&dead.reviveRemaining===0&&dead.deathSerial===serial,'unsafe resurrection must defer');
   A.assert(bodies().length===5&&new Set(bodies().map(b=>b.id)).size===5,'defer duplicated bodies');
 }finally{W.isFree=free;p.moves=original}
 G.EnemyMgr.clear();G.Hazards.clear();step(.4);
 A.assert(!dead.dead&&dead.hp===dead.maxHp&&dead.protectionRemaining>1,'safe retry failed protected resurrection');
 const remaining=dead.protectionRemaining;G.Combat.updateFields(.8);A.assert(dead.protectionRemaining===remaining,'pause advanced protection');out.revive={serial,protection:remaining};

 // A wall, telegraphed ground zone and actual nearby enemies each forbid initial placement.
 for(const reason of ['wall','hazard','enemy']){
   A.reset();G.Hazards.clear();G.Combat.clearFields();const saved=W.isFree;
   if(reason==='wall')W.isFree=()=>false;
   if(reason==='hazard')G.Hazards.add({kind:'zone',x:0,y:0,r:1000,delay:10,dmg:99,color:'#f00'});
   if(reason==='enemy'){for(let x=-200;x<=200;x+=30)for(let y=-200;y<=200;y+=30)A.spawn(x,y)}
   A.resume();G.Combat.updateFields(.01);A.pause();
   try{A.assert(bodies().length===5&&bodies().every(b=>!b.formed),'unsafe initial placement accepted '+reason)}
   finally{W.isFree=saved;G.Hazards.clear();G.EnemyMgr.clear()}
   step(.4);A.assert(bodies().every(b=>b.formed&&b.protectionRemaining>1),'safe initial retry failed '+reason);
 }out.safePlacement=['wall','hazard','enemy'];

 // Dense 12-second native pressure combines actual pursuit, flight/collision and
 // ground damage. Require continued team presence plus measurable incoming damage.
 A.reset();G.Hazards.clear();p.hp=p.maxHp;const counts={enemyUpdates:0,shots:0,hazards:0};
 for(let i=0;i<12;i++){const angle=(i/12)*Math.PI*2,e=A.spawn(Math.cos(angle)*210,Math.sin(angle)*210);e.spd=10;e.dmg=2;e.atkType='fire';e.def={...e.def,dmg:2,shotDmg:2};e.survivalStart={x:e.x,y:e.y};}
 for(let tick=0;tick<24;tick++){
   for(const e of G.EnemyMgr.all()){const target=bodies().find(b=>!b.dead)||p;e.shoot(target.x-e.x,target.y-e.y);counts.shots++;}
   const target=body('human');zone(target,2);counts.hazards++;step(.5);counts.enemyUpdates+=G.EnemyMgr.all().length*50;
 }
 const alive=bodies().filter(b=>!b.dead),lost=bodies().reduce((n,b)=>n+b.maxHp-b.hp,0);
 const moved=G.EnemyMgr.all().map(e=>Math.hypot(e.x-e.survivalStart.x,e.y-e.survivalStart.y));
 A.assert(moved.every(distance=>distance>20),'native dense enemies did not actually pursue');
 A.assert(counts.enemyUpdates>=10000&&counts.shots===288&&counts.hazards===24,'stress pressure fixtures did not run');
 A.assert(alive.length>=3&&lost>0,'dense pressure wiped support team or caused no native damage');
 out.stress={...counts,alive:alive.length,lost,enemyDisplacement:moved,actors:bodies().map(b=>({path:b.path,hp:b.hp,maxHp:b.maxHp,dead:b.dead}))};
 A.reset();G.Hazards.clear();out.reset=bodies().length;return out;
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'viewports': {}, 'errors': [], 'failedRequests': []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for label, viewport, mobile in [('desktop', {'width':1200,'height':900}, False), ('mobile', {'width':390,'height':844}, True)]:
                context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
                outer = context.new_page()
                outer.on('pageerror', lambda error: report['errors'].append({'message':str(error),'stack':error.stack}))
                outer.on('requestfailed', lambda request: report['failedRequests'].append({'url':request.url,'failure':request.failure}))
                outer.goto(URL)
                page = game_frame(outer)
                enter(page)
                print(label, 'survival', flush=True)
                report['viewports'][label] = {'narakaHp': page.evaluate(NARAKA_HP), 'survival': page.evaluate(CHECK)}
                outer.screenshot(path=str(OUT / f'{label}-survival.png'))
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
