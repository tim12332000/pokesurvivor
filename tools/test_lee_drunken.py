"""Drunken Fist: native attacks, probability boundaries, counter geometry and lifecycle."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

OUT = Path(__file__).resolve().parents[1] / '.omx/state/lee-drunken'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=lee&layout=wide&test=lee-drunken'
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),D=G.NarutoDrunkenFist,id='naruto-lee-drunken',out={levels:[],native:[],cleanup:[]};
 const near=(a,b)=>Math.abs(a-b)<1e-6;
 p.level=3;A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='new:'+id),'Drunken Fist learned before Lv4');
 p.level=4;A.assert(G.LevelUp.offer(p,100).some(c=>c.key==='new:'+id),'Lv4 Drunken Fist card missing');
 p.level=12;
 for(const m of ['naruto-lotus','naruto-reverse-lotus','naruto-kunai','naruto-shuriken'])p.addMove(m);
 const slots=p.slots.length;A.assert(slots===p.maxMoves,'full-loadout fixture missing');
 A.assert(p.addMove(id)&&p.slots.length===slots&&!p.slots.some(g=>g.some(m=>m.id===id)),'passive consumed/replaced active slot');
 const learned=p.moves.find(m=>m.id===id);A.assert(!p.addMove(id),'duplicate learned Drunken Fist');
 const mon=p.mon;
 for(const dex of [30001,30002,30007,30011]){p.mon=G.DEX.find(m=>m.dex===dex);
   A.assert(!D.stage(p)&&!G.Moves.poolFor(p.mon).includes(id),'Drunken Fist leaked into another hero');}
 p.mon=mon;
 function fixture(level=1){A.leeArena();G.Weather.reset();p.invuln=0;p.flash=0;p.frozen=false;p.critChance=0;p.item=null;
   Object.assign(learned,G.Moves.instance(id,level));p.percentHealthDamage=0;p.lifestealRate=0;return learned;}
 function forced(value,fn){const rng=Math.random;Math.random=()=>value;A.resume();try{return fn()}finally{Math.random=rng;A.pause()}}
 function hit(value,context,pure=false){return forced(value,()=>p.hurt(20,'normal',pure,context))}
 const context=e=>({fromX:e.x,fromY:e.y});
 const ledger=e=>{const hits=[],hurt=e.hurt;e.hurt=function(...args){hits.push(args);return hurt.apply(this,args)};return hits};
 for(let level=1;level<=5;level++){
   const move=fixture(level),e=A.spawn(45,0),hits=ledger(e),hp=p.hp,credit=p.dmgDealt;
   A.assert(near(move.dodgeChance,[.1,.15,.2,.25,.3][level-1]),'tier dodge chance mismatch');
   hit(move.dodgeChance-.0001,context(e));
   A.assert(p.hp===hp&&near(p.invuln,.25),'successful dodge lost HP or wrong immunity');
   A.assert(D.activeFor(p)&&D.presentationFor(p).phase==='dodge','dodge presentation missing');
   const cast=p.cast;let casts=0;p.cast=function(...args){casts++;return cast.apply(this,args)};
   A.resume();try{G.Combat.tick(.01,p,0)}finally{A.pause();p.cast=cast}
   A.assert(!casts,'selected primary attack started during reaction');
   A.assert(!hits.length,'counter hit before dodge motion');
   hit(0,context(e));A.assert(!hits.length,'invulnerable hit duplicated counter');
   A.advance(.099);A.assert(!hits.length,'counter hit too early');
   forced(.999,()=>G.Combat.updateFields(.001));
   const damage=move.dmg*p.atk*G.Types.mult(move.type,e.types)*G.Weather.mult(move.type);
   A.assert(hits.length===1&&near(hits[0][0],damage)&&hits[0][6]===p&&hits[0][7]===id,'counter damage/ownership mismatch');
   A.assert(near(p.dmgDealt-credit,damage),'counter credited wrong damage');
   A.assert(G.AnimationLab.stateFor(p.anim).id===id,'real renderer did not select counter body');
   A.advance(1);A.assert(hits.length===1&&!D.activeFor(p),'counter repeated or pose did not expire');
   p.invuln=0;const before=p.hp;hit(move.dodgeChance,context(e));
   A.assert(p.hp<before&&!D.activeFor(p),'exact probability boundary must fail');
   out.levels.push({level,chance:move.dodgeChance,damage,nativeHP:100000-e.hp});
 }
 // A real contact context should target its attacker over a nearer bystander.
 fixture();const close=A.spawn(5,0),attacker=A.spawn(-15,0),contactHits=ledger(attacker),bystanderHits=ledger(close);
 close.touchCd=99;attacker.touchCd=0;attacker.dmg=17;attacker.atkType='normal';
 const hp=p.hp;forced(0,()=>G.Combat.resolve(.01,p,0));
 A.assert(attacker.touchCd>0&&p.hp===hp,'native contact did not dodge');
 A.advance(.1);A.assert(contactHits.length===1&&!bystanderHits.length,'counter did not prioritize actual contact attacker');out.native.push('contact');
 // Native enemy projectile is consumed and can only counter a reachable nearby enemy.
 fixture();const local=A.spawn(60,0),localHits=ledger(local),shot=G.Projectiles.spawn({friendly:false,x:p.x,y:p.y,dmg:17,mtype:'fire',vx:0,vy:0});
 const projectileHp=p.hp;forced(0,()=>G.Combat.resolve(.01,p,0));
 A.assert(p.hp===projectileHp&&!G.Projectiles.all().includes(shot),'native projectile did not dodge/consume');
 A.advance(.1);A.assert(localHits.length===1,'projectile dodge did not counter nearest enemy');out.native.push('projectile');
 for(const reason of ['pure','environment','frozen','invuln','gates','lotus']){
   fixture();const e=A.spawn(45,0);
   if(reason==='frozen')p.frozen=true;
   if(reason==='invuln')p.invuln=1;
   if(reason==='gates'){p.addMove('naruto-gates');A.assert(G.NarutoGates.performing(p),'gate fixture missing');}
   if(reason==='lotus'){A.leeArena();p.target=A.spawn(35,0);A.actualCast('naruto-reverse-lotus');
     for(let n=0;n<500&&!G.NarutoLee.isInvulnerable(p);n++)A.advance(.005);
     A.assert(G.NarutoLee.isInvulnerable(p),'lotus immunity fixture missing');p.invuln=0;}
   const rng=Math.random;Math.random=()=>0;const before=p.hp;A.resume();
   try{p.hurt(20,'normal',reason==='pure',reason==='environment'?undefined:context(e))}finally{Math.random=rng;A.pause()}
   A.assert(!D.activeFor(p),'bypass triggered dodge '+reason);
   // Other native systems may roll for incidental effects; Drunken Fist must not start a counter.
   if(['pure','environment','frozen'].includes(reason))A.assert(p.hp<before,'bypass swallowed native damage '+reason);
   if(reason==='gates')A.assert(p.hp===before,'gate performance must retain its existing damage refund');
   out.native.push(reason);
 }
 p.frozen=false;
 for(const reason of ['wall','range','empty','dead-target','target-moved','heavy-start']){
   fixture();const e=reason==='empty'?null:A.spawn(reason==='range'?121:60,0),hits=e?ledger(e):[];
   if(reason==='wall')G.World.isWall=x=>x>=25;
   hit(0,e?context(e):{fromX:500,fromY:0,vx:-1,vy:0});
   if(reason==='dead-target')e.dead=true;
   if(reason==='target-moved'){e.x=200;G.EnemyMgr.rebuildGrid();}
   if(reason==='heavy-start'){p.target=A.spawn(35,0);const m=A.select('naruto-lotus');A.assert(G.NarutoLee.cast(p,m),'forced heavy action fixture missing');}
   const before=p.dmgDealt;A.advance(.1);
   A.assert(!hits.length&&p.dmgDealt===before,'invalid counter dealt damage '+reason);out.native.push(reason);
 }
 // Critical damage and native lifesteal use the normal owned-hit path exactly once.
 const move=fixture(5),victim=A.spawn(45,0),hits=ledger(victim);p.critChance=1;p.lifestealRate=.1;p.hp=10;
 const before=p.hp,credit=p.dmgDealt;hit(0,context(victim));forced(0,()=>G.Combat.updateFields(.1));
 const critical=move.dmg*p.atk*G.Types.mult(move.type,victim.types)*G.Weather.mult(move.type)*1.5;
 A.assert(hits.length===1&&hits[0][5]==='crit'&&near(p.dmgDealt-credit,critical),'critical path failed');
 A.assert(near(p.hp-before,critical*.1*G.NarutoGates.healingMultiplier(p)),'native lifesteal path failed');
 for(const reason of ['clear','death','world','owner']){
   fixture();const e=A.spawn(45,0),hits=ledger(e);hit(0,context(e));
   const state=D.activeFor(p),world=G.World;A.assert(state,'cleanup fixture missing');
   G.Combat.updateFields(1);A.assert(D.activeFor(p)?.age===0,'pause advanced dodge');
   if(reason==='clear')G.Combat.clearFields(p);
   if(reason==='death')p.dead=true;
   if(reason==='world')G.World={...world};
   if(reason==='owner'){G.Game.toUI();G.Flow.play();}
   A.resume();try{D.update(1)}finally{if(reason!=='owner')G.World=world;p.dead=false;A.pause()}
   A.assert(!hits.length&&!D.activeFor(p),'counter survived '+reason);out.cleanup.push(reason);
 }
 return out;
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in (False, True):
                label = 'mobile' if mobile else 'desktop'
                ctx = browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = ctx.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY&&G.NarutoDrunkenFist&&document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30006"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
                page.evaluate(HARNESS)
                page.evaluate(SETUP)
                report['viewports'][label] = page.evaluate(CHECK)
                ctx.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report['ok'] = False
        report['failure'] = str(error)
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'viewports': list(report['viewports']), 'evidence': str(OUT)}))

if __name__ == '__main__':
    main()
