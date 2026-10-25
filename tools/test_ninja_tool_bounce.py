"""Native additive ninja-tool card tests across the three projectile pipelines."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlencode
from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame
from test_animation_complete import HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/ninja-tool-bounce'
SETUP = r"""() => {
 const A=Acceptance,p=A.p();window.bounceMoves=p.moves.slice();
 A.bounceReset=()=>{p.moves=bounceMoves.slice();p.ninjaToolBouncePicks=0;p.statsTaken={};p.quantityPicks=p.quantityBonus=0;
  A.arena();G.SelfClones.clear();G.Pickups.clear();p.xpNext=1e9;p.critChance=p.percentHealthDamage=p.lifestealRate=p.damageSplashPicks=0;
  for(const m of p.moves)m.t=999;A.resume();G.Combat.updateFields(.001);A.pause();A.finish(1.6);
  for(const b of G.NarutoPain.actorsFor(p))b.cooldown=999;
 };
 A.bounceCard=(n=1)=>{for(let i=0;i<n;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:ninjaToolBounce');A.assert(c,'card not offered for tool owner');c.apply(p)}};
 A.watchBounce=es=>{const records=es.map(()=>[]);es.forEach((e,i)=>{const hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);if(hp>this.hp)records[i].push({damage:hp-this.hp,owner:args[6],id:args[7]});return result}});return records};
}"""
PAIN = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out=[];
 const m=bounceMoves.find(m=>m.id==='naruto-pain'),original={count:m.count,cd:m.cd};
 try {
  m.cd=999;
  for(const picks of [0,1,2]) {
   A.bounceReset();p.moves=[m];A.bounceCard(picks);
   const es=[A.spawn(80,0),A.spawn(80,80),A.spawn(160,80),A.spawn(400,0)],hits=A.watchBounce(es);
   A.advance();A.finish(1.3);const counts=hits.map(h=>h.length);
   A.assert(counts.slice(0,3).reduce((a,b)=>a+b,0)===5*(picks+1)&&counts.slice(0,3).every(n=>n<=5)&&counts[3]===0,'falling rod bounce additive '+picks+' '+counts);
   A.assert(hits.flat().every(h=>h.id==='naruto-pain'&&h.owner===p),'rod ownership changed');
   A.assert(hits.flat().every(h=>Math.abs(h.damage-hits[0][0].damage)<1e-6),'rod bounce damage scaled twice');
   out.push({picks,counts,damage:hits[0][0].damage});
  }
  A.bounceReset();p.moves=[m];A.bounceCard(2);const lone=A.spawn(80,0),h=A.watchBounce([lone]);A.advance();A.finish(.8);
  A.assert(h[0].length===5,'card bounced back into same lone victim');
  A.bounceReset();p.moves=[m];const es=[A.spawn(80,0),A.spawn(80,80)],snapshot=A.watchBounce(es);A.advance();A.bounceCard();A.finish(.8);
  A.assert(snapshot[0].length===3&&snapshot[1].length===2,'card retroactively changed an existing falling rod');
 } finally {Object.assign(m,original);p.moves=bounceMoves.slice();A.bounceReset()}
 return {cases:out,noSelfRepeat:true,castSnapshot:true};
}"""
GENERIC = r"""() => {
 const A=Acceptance,p=A.p(),out={};
 function fire(picks,pierce=0) {
  A.bounceReset();const m=G.Moves.instance('naruto-kunai',1);m.count=1;m.pierce=pierce;p.moves=[m];A.bounceCard(picks);
  const es=[A.spawn(60,0),A.spawn(60,80),A.spawn(140,80),A.spawn(400,0)],hits=A.watchBounce(es);
  const shots=G.DigimonSkills.fireFrom(p,m,0,0,0);A.assert(shots.length===1,'native kunai spawn');p.moves=[];
  A.finish(.9);return {es,hits,shots};
 }
 for(const n of [0,1,2]) {
  const {hits}=fire(n),counts=hits.map(h=>h.length);
  A.assert(JSON.stringify(counts)===JSON.stringify([1,n>=1?1:0,n>=2?1:0,0]),'generic additive hops '+n+' '+counts);
  A.assert(hits.flat().every(h=>Math.abs(h.damage-hits[0][0].damage)<1e-6&&h.owner===p),'generic double-scaled damage');out[n]=counts;
 }
 A.bounceReset();let m=G.Moves.instance('naruto-kunai',1);m.count=1;m.pierce=1;p.moves=[m];A.bounceCard();
 let es=[A.spawn(50,0),A.spawn(100,0),A.spawn(150,0),A.spawn(240,0)],hits=A.watchBounce(es);
 G.DigimonSkills.fireFrom(p,m,0,0,0);p.moves=[];A.finish(.9);
 A.assert(JSON.stringify(hits.map(h=>h.length))===JSON.stringify([1,1,1,0]),'card consumed existing pierce budget');out.pierce=true;
 A.bounceReset();m=G.Moves.instance('naruto-kunai',1);m.count=1;p.moves=[m];A.bounceCard();
 es=[A.spawn(60,0),A.spawn(60,80)];hits=A.watchBounce(es);G.DigimonSkills.fireFrom(p,m,0,0,0);p.moves=[];A.finish(.7);
 A.assert(hits.every(h=>h.length===1),'default piercing kunai did not redirect on its first hit');out.immediateWithPierce=true;
 A.bounceReset();m=G.Moves.instance('naruto-kunai',1);m.count=1;m.pierce=0;p.moves=[m];A.bounceCard();
 es=[A.spawn(60,0),A.spawn(60,170)];hits=A.watchBounce(es);G.DigimonSkills.fireFrom(p,m,0,0,0);p.moves=[];A.finish(.9);
 A.assert(hits[0].length===1&&hits[1].length===0,'bounce exceeded160 radius');out.range=true;
 A.bounceReset();m=G.Moves.instance('naruto-kunai',1);m.count=1;m.pierce=0;p.moves=[m];A.bounceCard();
 es=[A.spawn(60,0),A.spawn(130,80)];hits=A.watchBounce(es);const block=G.World.projectileBlock;
 G.World.projectileBlock=x=>x>=85&&x<=95?'wall':false;
 try{G.DigimonSkills.fireFrom(p,m,0,0,0);p.moves=[];A.finish(.9);A.assert(hits[0].length===1&&hits[1].length===0,'bounce crossed wall')}
 finally{G.World.projectileBlock=block}out.wall=true;
 A.bounceReset();p.ninjaToolBouncePicks=5;
 for(const id of ['naruto-pain-missiles','naruto-fireball','naruto-rasenshuriken','naruto-tenten-tags','water-gun'])A.assert(G.NinjaToolBounce.create(p,id)===null,'AoE/non-tool got card '+id);
 out.exclusions=true;
 A.bounceReset();m=G.Moves.instance('naruto-kunai',1);m.count=1;m.pierce=0;p.moves=[m];A.bounceCard();
 es=[A.spawn(60,0),A.spawn(60,80),A.spawn(150,80)];hits=A.watchBounce(es);
 G.DigimonSkills.fireFrom(p,m,0,0,0);p.moves=[];A.finish(.15);es[1].dead=true;es[1].hp=0;G.EnemyMgr.rebuildGrid();A.finish(.7);
 A.assert(hits[0].length===1&&hits[1].length===0&&hits[2].length===1,'dead ricochet target was not replaced within paid hop');out.deadTarget=true;
 A.bounceReset();m=G.Moves.instance('naruto-kunai',1);m.count=1;m.pierce=0;p.moves=[m];A.bounceCard();A.spawn(120,0);
 const pending=G.DigimonSkills.fireFrom(p,m,0,0,0)[0],world=G.World;G.World={...world};
 try{A.advance();A.assert(!G.Projectiles.all().includes(pending),'scene change retained ricochet projectile')}
 finally{G.World=world}out.worldCleanup=true;
 p.moves=bounceMoves.slice();A.bounceReset();return out;
}"""
FUMA_CLONE_EVO = r"""() => {
 const A=Acceptance,p=A.p(),out={};A.bounceReset();const m=G.Moves.instance('naruto-fuma-shuriken',1);p.moves=[m];A.bounceCard();
 const first=A.spawn(60,0),next=A.spawn(60,60),hits=A.watchBounce([first,next]);
 const shot=G.Projectiles.spawn({owner:p,mid:m.id,friendly:true,x:45,y:0,px:45,py:0,vx:160,vy:0,dmg:10,r:4,life:4,hits:new Set(),pierce:0,
  fumaReturn:true,boom:.4,back:true,returnAt:.65,t:.7,bsp:160,fumaPierce:0});
 A.resume();G.Combat.resolve(.01,p,0);A.pause();A.assert(shot.toolBounce?.chaining,'return-leg Fuma failed to bounce');p.moves=[];
 for(let i=0;i<100&&shot.toolBounce.chaining;i++)A.advance();
 A.assert(!shot.toolBounce.chaining&&shot.back&&shot.t>=shot.returnAt,'Fuma return clock regressed');
 A.assert(hits[0].length===1&&hits[1].length===1,'Fuma missing/duplicate card hit');A.finish(2);
 A.assert(!G.Projectiles.all().includes(shot),'returning Fuma failed to expire/catch');out.fumaReturn=true;
 A.bounceReset();const kunai=G.Moves.instance('naruto-kunai',1);kunai.count=1;kunai.pierce=0;p.moves=[kunai];A.bounceCard();
 const cloneCard=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:selfClone');A.assert(cloneCard,'clone card absent');cloneCard.apply(p);
 const clone=G.SelfClones.actors()[0];A.assert(clone.ninjaToolBouncePicks===1,'clone missed card inheritance');
 clone.moves.forEach(m=>m.t=999);const es=[A.spawn(60,0),A.spawn(60,80)],records=A.watchBounce(es);
 G.DigimonSkills.fireFrom(clone,kunai,0,0,0);A.finish(.8);
 A.assert(records.every(h=>h.length===1&&h[0].owner===clone),'clone duplicate or wrong hit ownership');
 const expected=Math.max(1,Math.round(kunai.dmg*clone.atk*G.Weather.mult('steel')));
 A.assert(records.flat().every(h=>Math.abs(h.damage-expected)<1e-6),'clone damage scaled more than once');out.clone=true;
 A.bounceReset();p.moves=[G.Moves.instance('naruto-pain-gravity',1)];
 A.assert(!G.LevelUp.offer(p,1000).some(c=>c.key==='stat:ninjaToolBounce'),'card offered without any physical tools');out.eligibility=true;
 out.evolutions=[];
 for(const [id,needs,legacy]of [['tackle','maxHealthPercent','hp'],['fire-spin','lifesteal','rgn']]) {
  const move=G.Moves.instance(id,G.Moves.BY_ID[id].maxLvl),before=G.Moves.evoInfo(move,{}),after=G.Moves.evoInfo(move,{[needs]:1}),old=G.Moves.evoInfo(move,{[legacy]:1});
  A.assert(before.needs===needs&&!before.ready&&after.ready&&old.ready,'evolution prerequisite compatibility '+id);
  const pokemon=new G.Player(G.DEX_BY[1],{});pokemon.moves=[move];
  const prerequisite=G.LevelUp.offer(pokemon,1000).find(c=>c.key==='stat:'+needs);A.assert(prerequisite,'replacement prerequisite not offered');prerequisite.apply(pokemon);
  A.assert(G.LevelUp.offer(pokemon,1000).some(c=>c.key==='evo:'+id),'replacement card did not unlock actual evolution offer');
  out.evolutions.push({id,needs,actualOffer:true});
 }
 p.moves=bounceMoves.slice();A.bounceReset();return out;
}"""
TENTEN = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,out={};
 function fresh() {A.arena();G.SelfClones.clear();p.ninjaToolBouncePicks=0;p.statsTaken={};p.quantityPicks=p.quantityBonus=0;p.critChance=p.percentHealthDamage=p.lifestealRate=p.damageSplashPicks=0;p.level=15;
  p.moves=[G.Moves.instance('naruto-tenten',1)];p.moves[0].count=1;p.moves[0].pierce=0;}
 function card(n) {for(let i=0;i<n;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:ninjaToolBounce');A.assert(c,'Tenten card absent');c.apply(p)}}
 function finish(seconds) {for(let i=0;i<Math.round(seconds*100);i++){A.resume();G.Combat.updateFields(.01);G.Projectiles.update(.01,p,G.EnemyMgr.all());G.Combat.resolve(.01,p,0);A.pause()}}
 for(const native of [0,3]) {
  fresh();if(native){const skill=G.LevelUp.offer(p,1000).find(c=>c.key==='new:naruto-tenten-bounce');A.assert(skill,'native Tenten bounce missing');skill.apply(p);
   for(let i=1;i<native;i++){const up=G.LevelUp.offer(p,1000).find(c=>c.key==='up:naruto-tenten-bounce');A.assert(up,'native upgrade missing');up.apply(p)}}
  A.assert(T.bounceCount(p)===native,'wrong native bounce baseline');card(1);A.assert(T.bounceCount(p)===native+1,'card replaced native bounce count');
  const es=[A.spawn(80,0),A.spawn(80,70),A.spawn(150,70),A.spawn(150,140),A.spawn(220,140),A.spawn(600,0)],hits=A.watchBounce(es);
  p.target=es[0];A.assert(T.cast(p,p.moves[0]),'actual Tenten cast rejected');finish(1.5);
  const counts=hits.map(h=>h.length),expected=native===0?[1,1,0,0,0,0]:[1,1,1,1,1,0];
  A.assert(JSON.stringify(counts)===JSON.stringify(expected),'Tenten additive actual hits '+native+' '+counts);out[native]={counts,total:T.bounceCount(p)};
 }
 fresh();card(2);A.assert(T.bounceCount(p)===2,'repeated Tenten card did not stack');p.quantityPicks=p.quantityBonus=2;
 const skill=G.LevelUp.offer(p,1000).find(c=>c.key==='new:naruto-tenten-bounce');skill.apply(p);
 A.assert(T.bounceCount(p)===5,'native+quantity+card not additive');out.quantityNativeCard=5;
 fresh();card(1);p.moves[0].pierce=2;const pierceEnemies=[A.spawn(80,0),A.spawn(80,40),A.spawn(100,80),A.spawn(120,120)],pierceHits=A.watchBounce(pierceEnemies);
 p.target=pierceEnemies[0];A.assert(T.cast(p,p.moves[0]),'piercing Tenten cast');finish(.8);
 A.assert(pierceHits.every(h=>h.length===1),'Tenten card discarded existing piercing hits');out.piercePreserved=true;
 fresh();card(2);const tags=G.LevelUp.offer(p,1000).find(c=>c.key==='new:naruto-tenten-tags');A.assert(tags,'tag skill absent');tags.apply(p);A.select('naruto-tenten-tags');p.target=A.spawn(150,0);
 A.assert(T.cast(p,p.moves.find(m=>m.id==='naruto-tenten-tags')),'tags cast');const tagsInFlight=T.weapons.filter(w=>w.owner===p&&w.mode==='tenten-tags');
 A.assert(tagsInFlight.length>0&&tagsInFlight.every(w=>w.cardBounces===0),'explosive tag consumed card budget');out.tagsExcluded=true;
 G.Combat.clearFields();A.assert(!T.weapons.length,'cleanup leaked ricochet weapons');return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'viewports': {}, 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, viewport in [('desktop', {'width': 1200, 'height': 900}), ('mobile', {'width': 390, 'height': 844})]:
            page = browser.new_page(viewport=viewport, is_mobile=label == 'mobile', has_touch=label == 'mobile', service_workers='block')
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL)
            frame = game_frame(page)
            enter(frame)
            frame.evaluate(SETUP)
            result = report['viewports'][label] = {}
            for name, check in [('pain', PAIN), ('generic', GENERIC), ('fumaCloneEvo', FUMA_CLONE_EVO)]:
                print(label, name, flush=True)
                result[name] = frame.evaluate(check)
            frame.evaluate('''() => {const p=Acceptance.p(),cards=G.LevelUp.offer(p,1000);G.RunUI.showLevelUp(p.level,['ninjaToolBounce','heal','giant'].map(id=>cards.find(c=>c.key==='stat:'+id)),c=>c.apply(p))}''')
            assert frame.locator('#cards .card').count() == 3
            assert frame.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(OUT / f'{label}-card-selection.png'), animations='disabled')
            frame.locator('#cards .card').first.click()
            result['selection'] = frame.evaluate('''() => {const p=Acceptance.p();Acceptance.assert(p.ninjaToolBouncePicks===1&&p.statsTaken.ninjaToolBounce===1,'actual bounce card click');Acceptance.assert(G.RunAttributes.rows(p).some(r=>r.id==='ninjaToolBounce'&&r.text.includes('+1')),'bounce HUD missing');G.RunUI.closeLevelUp();return true}''')
            print(label, 'tenten', flush=True)
            frame.evaluate('G.Game.toUI();G.MenuUI.open();G.UI.show("scr-menu")')
            frame.locator('[data-quick-naruto="30009"]').click()
            frame.locator('#scr-menu [data-go="play"]').click()
            frame.wait_for_function('G.Game.player?.dex===30009&&G.Game.state==="playing"')
            frame.evaluate(HARNESS)
            # Reuse controlled enemy creation and observation; the Tenten fixture owns stepping.
            frame.evaluate('''() => {const A=Acceptance;A.spawn=(x,y,boss=false)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};A.watchBounce=es=>{const hs=es.map(()=>[]);es.forEach((e,i)=>{const h=e.hurt;e.hurt=function(...args){const before=this.hp,r=h.apply(this,args);if(this.hp<before)hs[i].push(before-this.hp);return r}});return hs}}''')
            result['tenten'] = frame.evaluate(TENTEN)
            page.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
