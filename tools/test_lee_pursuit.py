"""Native, slotless Rock Lee pursuit acceptance through the ordinary game entry.

Requires the local repository server on port 8004. Only isolated arena terrain is
controlled; real moves, upgrade cards, enemy HP, input and authored art are used.
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/lee-pursuit'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=lee&layout=wide'

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPursuit,id='naruto-lee-pursuit',assert=A.assert;
 const near=(a,b)=>Math.abs(a-b)<Math.max(1,Math.abs(b))*1e-8;
 assert(P&&typeof P.activeFor==='function'&&typeof P.clear==='function','native pursuit API missing');
 const progression=[];
 for(const level of [1,2,3]){
   p.level=level;const pool=G.Moves.poolFor(p.mon),cards=G.LevelUp.offer(p,100);
   assert(pool.includes(id)===(level>=2),'wrong pursuit pool milestone '+level);
   assert(cards.some(c=>c.key==='new:'+id)===(level>=2),'wrong pursuit offer milestone '+level);
   progression.push({level,eligible:pool.includes(id)});
 }
 p.level=2;assert(G.LevelUp.offer(p,3).some(c=>c.key==='new:'+id),'level two first offer omitted pursuit');
 const mon=p.mon;
 for(const dex of [30001,30002,30007,30011]){
   p.mon=G.DEX.find(m=>m.dex===dex);assert(!G.Moves.poolFor(p.mon).includes(id),'pursuit leaked into hero '+dex);
 }p.mon=mon;
 p.level=12;const initial=p.moves[0];p.moves=[initial];p.slots=[[initial]];p.active=0;
 for(const other of ['naruto-kunai','naruto-shuriken','tackle','scratch'])if(p.slots.length<p.maxMoves&&G.Moves.BY_ID[other])p.addMove(other);
 assert(p.slots.length===p.maxMoves,'full active slot fixture incomplete');
 const slots=p.slots.length,selected=p.activeGroup(),card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
 assert(card&&card.apply(p)!==false,'full loadout cannot learn pursuit');
 assert(p.hasMove(id)&&p.slots.length===slots&&p.activeGroup()===selected,'passive consumed or changed active slot');
 assert(!p.slots.flat().some(m=>m.id===id)&&!Object.hasOwn(p.bind||{},id),'passive received active binding');
 p.moves=p.moves.filter(m=>m.id===id||m===initial);p.slots=[[initial]];p.active=0;p.arrange();
 const levels=[1,2,3,4,5].map(level=>{
   const m=G.Moves.instance(id,level),i=level-1;
   assert(m.passive&&near(m.cd,[1.4,1.3,1.2,1.1,1][i])&&m.dmg===[18,22,22,28,34][i],'pursuit level balance mismatch '+level);
   assert(m.count===[3,3,4,4,5][i]&&near(m.radius,[85,90,95,100,110][i])&&m.range===[180,195,210,225,240][i]&&m.arc===2.8,'pursuit level geometry mismatch '+level);
   return {level,damage:m.dmg,cooldown:m.cd,count:m.count,radius:m.radius,range:m.range};
 });
 function advance(dt){A.resume();try{G.Combat.updateFields(dt);p.anim.update(dt)}finally{A.pause()}}
 function fixture(level=1,gates=false,quantity=0){
   A.leeArena();P.clear(p);p.quantityPicks=p.quantityBonus=quantity;p.cdMul=1;
   p.moves=p.moves.filter(m=>m.id!=='naruto-gates');if(gates)p.addMove('naruto-gates');
   const m=p.moves.find(m=>m.id===id);Object.assign(m,G.Moves.instance(id,level));m.t=0;
   for(const other of p.moves)if(other!==m&&!other.passive)other.t=999;
   p.aim=0;p.attackFace=0;p.walking=false;
   return m;
 }
 function ledger(enemies){const hits=[];for(const enemy of enemies){const hurt=enemy.hurt;enemy.hurt=function(...args){
   const pose=G.AnimationLab.stateFor(p.anim);hits.push({enemy,damage:args[0],knock:args[4],owned:args[6]===p,id:args[7],key:pose.key});
   return hurt.apply(this,args);
 };}return hits;}
 function finish(){let n=0;while(P.activeFor(p)&&n++<200)advance(.005);assert(n<200,'pursuit failed to finish');}
 const cases=[];
 for(const [level,gates,quantity] of [[1,false,0],[5,true,0],[1,false,4],[5,true,20]]){
   const m=fixture(level,gates,quantity),inside=[A.spawn(40,0),A.spawn(35,-25),A.spawn(35,25)],behind=A.spawn(-60,0),outside=A.spawn(350,0);
   p.target=inside[0];const hits=ledger([...inside,behind,outside]),credit=p.dmgDealt,stat=m.dealt||0;
   advance(.001);assert(P.activeFor(p),'native update did not start pursuit');
   const timer=m.t,position={x:p.x,y:p.y},pose=G.AnimationLab.stateFor(p.anim);
   G.Combat.updateFields(.2);assert(m.t===timer&&p.x===position.x&&p.y===position.y,'pause advanced pursuit');
   finish();const count=Math.min(12,Math.floor(m.count*1.25**quantity));
   assert(inside.every(e=>hits.filter(h=>h.enemy===e).length===count),'front cone missed or duplicated hits');
   assert(!hits.some(h=>h.enemy===behind||h.enemy===outside),'pursuit damaged behind or outside cone');
   const base=m.dmg*p.atk*G.Types.mult(m.type,inside[0].types)*G.Weather.mult(m.type);
   assert(hits.every(h=>h.owned&&h.id===id&&near(h.damage,base)),'pursuit ownership or per-hit damage mismatch');
   assert(inside.every(e=>100000-e.hp===Math.round(base)*count),'native HP loss mismatches strikes');
   assert(near(p.dmgDealt-credit,base*3*count)&&near((m.dealt||0)-stat,Math.round(base)*3*count),'damage credit or move statistics mismatch');
   assert(hits.filter(h=>h.enemy===inside[0]).every((h,i)=>h.knock===(i===count-1?55:8)),'finisher knockback mismatch');
   const expected=gates?'lee-opened-attack':'lee-attack';
   assert(hits.every(h=>h.key===expected),'strike did not use authored '+expected);
   assert(pose.key===expected,'pursuit start pose missing authored attack');
   const rendered=A.render();assert(rendered.pixels>80,'native actor artwork empty');
   cases.push({level,gates,quantity,hitsPerTarget:count,damagePerHit:base,nativeHP:100000-inside[0].hp,authoredPose:expected});
 }
 fixture();const distant=A.spawn(170,0),rushHits=ledger([distant]);p.target=distant;advance(.001);
 assert(P.activeFor(p),'rush did not start');advance(.03);
 assert(p.x>0&&p.x<170&&p.invuln>=.05,'bounded rush movement or protection missing');
 assert(G.AnimationLab.stateFor(p.anim).key==='lee-movement','rush did not use authored movement');finish();
 assert(rushHits.length===3,'rush did not arrive and punch');
 fixture();p.target=A.spawn(150,0);advance(.001);
 const fixed={x:G.Camera.x,y:G.Camera.y,scale:G.Camera.scale};G.Camera.kick(.4);G.Camera.follow(p.x+80,p.y+80,.1);
 assert(G.Camera.x===fixed.x&&G.Camera.y===fixed.y&&G.Camera.scale===fixed.scale&&G.Camera.shake===0,'pursuit moved or shook camera');P.clear(p);
 fixture();const wallEnemy=A.spawn(170,0);p.target=wallEnemy;
 G.World.isFree=x=>x<40;G.World.isWall=x=>x>=40;
 advance(.001);for(let i=0;i<100;i++)advance(.005);
 assert(p.x<40&&wallEnemy.hp===100000,'pursuit crossed or hit through wall');
 // A real main skill interrupts pending pursuit damage and owns the body pose.
 fixture();const victim=A.spawn(40,0),interruptHits=ledger([victim]);p.target=victim;advance(.001);
 const already=interruptHits.length;A.actualCast('naruto-lee');advance(.1);
 assert(!P.activeFor(p),'main whirlwind did not interrupt pursuit');
 assert(interruptHits.length===already,'interrupted pursuit delivered pending invisible hits');
 G.Combat.clearFields(p);
 if(!p.hasMove('naruto-lotus'))p.addMove('naruto-lotus');
 fixture();const lotusVictim=A.spawn(40,0),lotusHits=ledger([lotusVictim]);p.target=lotusVictim;advance(.001);
 A.actualCast('naruto-lotus');advance(.001);
 assert(!P.activeFor(p)&&G.NarutoLee.activeFor(p),'front Lotus did not take body ownership');
 assert(!lotusHits.some(h=>h.id===id),'Lotus interruption retained pursuit damage');G.Combat.clearFields(p);
 const cleanup=[];
 for(const reason of ['clear','death','world']){
   fixture();const enemy=A.spawn(150,0),hits=ledger([enemy]);p.target=enemy;advance(.001);assert(P.activeFor(p),'cleanup fixture missing');
   const original=G.World;
   if(reason==='clear')G.Combat.clearFields(p);
   if(reason==='death'){p.dead=true;p.hp=0;}
   if(reason==='world')G.World={...original};
   advance(.1);G.World=original;
   assert(!P.activeFor(p)&&hits.length===0,'pending damage retained after '+reason);cleanup.push(reason);
 }
 fixture();p.cdMul=.01;p.target=A.spawn(40,0);advance(.001);
 assert(near(p.moves.find(m=>m.id===id).t,.5),'pursuit cooldown floor missing');P.clear(p);
 const healingMove=fixture(),healingTarget=A.spawn(40,0);p.target=healingTarget;
 p.percentHealthDamage=.01;p.lifestealRate=.001;p.hp=p.maxHp/2;
 const hp=p.hp,credit=p.dmgDealt,base=healingMove.dmg*p.atk*G.Types.mult(healingMove.type,healingTarget.types)*G.Weather.mult(healingMove.type);
 advance(.001);finish();const total=(base+1000)*3;
 assert(near(p.dmgDealt-credit,total),'percentage-health damage lost or duplicated');
 assert(near(p.hp-hp,total*.001),'native lifesteal lost or duplicated');
 assert(near(100000-healingTarget.hp,Math.round(base+1000)*3),'percentage-health damage native HP mismatch');
 fixture();const doomed=A.spawn(40,0);doomed.hp=1;doomed.xp=7;p.target=doomed;
 const kills=p.kills,dropXp=G.Pickups.dropXp;let drops=0;
 G.Pickups.dropXp=function(...args){drops++;return dropXp.apply(this,args)};
 try{advance(.001);finish();G.EnemyMgr.update(.001,[p]);G.EnemyMgr.update(.001,[p]);}
 finally{G.Pickups.dropXp=dropXp;}
 assert(doomed.dead&&p.kills===kills+1&&drops===1,'native kill or reward credit duplicated');
 const mixedMove=fixture(),primary=A.spawn(40,0),survivor=A.spawn(45,20);primary.hp=1;primary.xp=7;p.target=primary;
 const mixedHits=ledger([primary,survivor]),mixedCredit=p.dmgDealt,mixedKills=p.kills;
 let mixedDrops=0;G.Pickups.dropXp=function(...args){mixedDrops++;return dropXp.apply(this,args)};
 try{
   advance(.001);const combo=P.activeFor(p);advance(.075);
   assert(primary.dead&&combo.hitIndex===1,'mixed-HP first strike did not kill primary');
   const cooldown=mixedMove.t,x=p.x,y=p.y;advance(.005);
   assert(P.activeFor(p)===combo&&combo.target===survivor&&combo.hitIndex===1&&combo.phase==='attack','target death restarted or cancelled combo');
   assert(p.x===x&&p.y===y&&near(mixedMove.t,cooldown-.005),'retarget rushed again or reset cooldown');
   finish();G.EnemyMgr.update(.001,[p]);G.EnemyMgr.update(.001,[p]);
 }finally{G.Pickups.dropXp=dropXp;}
 const mixedBase=mixedMove.dmg*p.atk*G.Types.mult(mixedMove.type,survivor.types)*G.Weather.mult(mixedMove.type);
 assert(mixedHits.filter(h=>h.enemy===primary).length===1&&mixedHits.filter(h=>h.enemy===survivor).length===3,'retarget lost or duplicated remaining strikes');
 assert(mixedHits.every(h=>h.owned&&h.id===id)&&near(p.dmgDealt-mixedCredit,mixedBase*4),'retarget lost native damage ownership');
 assert(100000-survivor.hp===Math.round(mixedBase)*3&&p.kills===mixedKills+1&&mixedDrops===1,'retarget native HP or kill reward mismatch');
 // Expose only fixture functions for a following real keyboard-input assertion.
 A.pursuitFixture=fixture;A.pursuitAdvance=advance;
 return {progression,fullSlots:slots,levels,cases,cleanup,pause:true,wall:true,interruption:true,percentageDamage:true,lifesteal:true,killReward:true,mixedHPRetarget:true};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, mobile in [('desktop', False), ('mobile', True)]:
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1200, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(URL)
            page.wait_for_function("window.G?.NarutoPursuit&&document.querySelector('#boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
            page.evaluate('()=>G.Sprites.preload([19])')
            page.evaluate(HARNESS)
            page.evaluate(SETUP)
            report['viewports'][label] = page.evaluate(CHECK)
            page.keyboard.down('d')
            try:
                report['viewports'][label]['manualMovement'] = page.evaluate('''() => {
                  const A=Acceptance,p=A.p();A.pursuitFixture();p.target=A.spawn(150,0);
                  A.assert(G.Input.axis()[0]!==0,'real keyboard input absent');
                  for(let i=0;i<50;i++)A.pursuitAdvance(.01);
                  A.assert(p.x===0&&p.y===0&&!G.NarutoPursuit.activeFor(p),'automatic dash dragged a moving player');
                  return true;
                }''')
            finally:
                page.keyboard.up('d')
            page.evaluate('''() => {const A=Acceptance;A.pursuitFixture();A.p().target=A.spawn(150,0);A.pursuitAdvance(.001);A.assert(G.NarutoPursuit.activeFor(A.p()),'mid-rush input fixture missing');}''')
            page.keyboard.down('d')
            try:
                report['viewports'][label]['midRushMovement'] = page.evaluate('''() => {
                  const A=Acceptance,p=A.p();p.x+=9;const x=p.x,y=p.y;A.pursuitAdvance(.03);
                  A.assert(p.x===x&&p.y===y&&!G.NarutoPursuit.activeFor(p),'rush pulled a manually moving player back');return true;
                }''')
            finally:
                page.keyboard.up('d')
            report['viewports'][label]['newRunClear'] = page.evaluate('''() => {
              const A=Acceptance,old=A.p();A.pursuitFixture();old.target=A.spawn(150,0);A.pursuitAdvance(.001);
              A.assert(G.NarutoPursuit.activeFor(old),'new-run fixture missing');
              G.Game.startRun();A.pause();
              A.assert(G.Game.player!==old&&!G.NarutoPursuit.activeFor(old)&&!G.NarutoPursuit.activeFor(G.Game.player),'new run retained pursuit');
              return true;
            }''')
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    (OUT / 'regression.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'viewports': list(report['viewports']), 'evidence': str(OUT / 'regression.json')}))


if __name__ == '__main__':
    main()
