"""Lee's cooldown melee uses real Combat.tick without changing the selected skill."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP
from test_redrawn_heroes import AUDIT

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.omx/state/lee-basic-attack'
URL='http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=lee-basic-attack'

HELPERS=r"""() => {
 const A=Acceptance,p=A.p();p.level=12;
 for(const id of ['naruto-lotus','naruto-reverse-lotus']){
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'real learn card missing '+id);
 }
 A.basicCasts=[];const cast=p.cast;
 p.cast=function(m,...args){A.basicCasts.push({id:m.id,name:m.name,type:m.type,damage:m.dmg,cd:m.cd,radius:m.radius,time:A.basicTime||0});return cast.call(this,m,...args)};
 A.basicTick=dt=>{A.resume();try{G.Combat.tick(dt,p,A.basicTime||0)}finally{A.pause()}A.basicTime=(A.basicTime||0)+dt};
 A.basicStep=dt=>{A.basicTick(dt);A.advance(dt)};
 A.basicFixture=id=>{A.leeArena();const m=A.select(id);m.t=10;A.basicTick(.6);A.basicCasts=[];A.basicTime=0;return m};
 A.assertLoadout=(slots,moves,active,groupFn)=>{
   A.assert(p.slots.length===slots.length&&p.slots.every((s,i)=>s===slots[i]),'hidden basic changed real slots');
   A.assert(p.moves.length===moves.length&&p.moves.every((m,i)=>m===moves[i]),'hidden basic became a learned move');
   A.assert(p.active===active&&p.activeGroup===groupFn,'temporary group was not restored');
 };
}"""

COMBAT=r"""() => {
 const A=Acceptance,p=A.p(),out={},near=(a,b)=>Math.abs(a-b)<1e-6;
 const ids=['naruto-lotus','naruto-reverse-lotus'];
 A.assert(!p.hasMove('tackle')&&!G.Moves.poolFor(p.mon).includes('tackle'),'basic leaked into learned pool');
 for(const id of ids){
   const m=A.basicFixture(id),e=A.spawn(35,0),far=A.spawn(300,0);p.target=far;
   const slots=p.slots.slice(),moves=p.moves.slice(),active=p.active,fn=p.activeGroup,t=m.t;
   const expected=G.Moves.BY_ID.tackle.dmg*p.atk*G.Types.mult('fighting',e.types)*G.Weather.mult('fighting'),damage=p.dmgDealt;
   A.basicTick(.01);
   A.assert(A.basicCasts.length===1&&A.basicCasts[0].id==='tackle'&&A.basicCasts[0].type==='fighting','cooldown did not invoke real fighting melee '+id);
   A.assert(A.basicCasts[0].damage===G.Moves.BY_ID.tackle.dmg&&A.basicCasts[0].cd===G.Moves.BY_ID.tackle.cd&&A.basicCasts[0].radius===G.Moves.BY_ID.tackle.radius,'basic bypassed shared melee definition');
   A.assert(near(100000-e.hp,Math.round(expected))&&near(p.dmgDealt-damage,expected),'basic real damage incorrect '+id+' '+JSON.stringify({enemy:100000-e.hp,credit:p.dmgDealt-damage,expected,casts:A.basicCasts}));
   A.assert(far.hp===100000&&p.target===far,'basic changed selected far target or hit outside range');
   A.assert(near(m.t,t-.01),'selected cooldown decremented twice');A.assertLoadout(slots,moves,active,fn);
   out[id]={cooldownHit:100000-e.hp,selectedCooldown:m.t,casts:A.basicCasts.slice()};
   // Main technique is ready while the private basic has cooldown: Lotus wins.
   A.basicCasts=[];m.t=0;p.target=e;A.basicTick(.001);
   A.assert(A.basicCasts.length===1&&A.basicCasts[0].id===id&&G.NarutoLee.active?.move.id===id,'ready main technique lost priority');
   A.assertLoadout(slots,moves,active,fn);
   let hits=0;const hurt=e.hurt;e.hurt=function(...args){hits++;return hurt.apply(this,args)};
   // The final recovery boundary is advanced without another attack tick.
   for(let n=0;n<500&&G.NarutoLee.active;n++){
     const before=A.basicCasts.length;A.basicTick(.01);
     A.assert(A.basicCasts.length===before,'basic overlapped active Lotus '+id);A.advance(.01);
   }
   A.assert(!G.NarutoLee.active&&hits===(id==='naruto-lotus'?2:7),'combo gained/lost hits '+id+' '+hits);
   out[id].pureComboHits=hits;A.assertLoadout(slots,moves,active,fn);
 }
 // A 240 Hz tick stream must retain the half-second native melee cadence.
 let m=A.basicFixture('naruto-lotus'),e=A.spawn(35,0);p.target=e;m.t=10;
 for(let n=0;n<240;n++)A.basicTick(1/240);
 const period=G.Moves.BY_ID.tackle.cd*p.cdMul;
 A.assert(A.basicCasts.length===Math.ceil(1/period),'high frame rate basic spam '+A.basicCasts.length+' period '+period);
 A.assert(A.basicCasts.every((c,i,all)=>!i||c.time-all[i-1].time>=period-1e-6),'basic ignored cooldown');
 A.assert(near(m.t,9),'one-second simulation changed selected cooldown twice');out.cadence={period,casts:A.basicCasts.slice(),selectedCooldown:m.t};
 // No cast animation is spent without a valid close, clear target.
 out.blocked=[];
 for(const reason of ['no-target','range','wall','projectile-block','dead-target','dead-owner']){
   m=A.basicFixture('naruto-reverse-lotus');e=reason==='no-target'?null:A.spawn(reason==='range'?100:35,0);p.target=e;
   if(reason==='dead-target')e.dead=true;
   if(reason==='dead-owner')p.dead=true;
   if(reason==='wall')G.World.isWall=()=>true;
   if(reason==='projectile-block')G.World.projectileBlock=()=>true;
   A.basicTick(.2);A.assert(A.basicCasts.length===0,'basic cast without valid contact '+reason);
   if(e)A.assert(e.hp===100000,'blocked enemy hurt '+reason);out.blocked.push(reason);
 }
 // Switching between the two techniques cannot reset their shared basic timer.
 m=A.basicFixture('naruto-lotus');e=A.spawn(35,0);p.target=e;A.basicTick(.01);
 A.assert(A.basicCasts.length===1,'switch fixture did not punch');const selected=A.select('naruto-reverse-lotus');selected.t=10;A.basicCasts=[];
 A.basicTick(.01);A.assert(!A.basicCasts.length,'switching Lotus skills reset hidden basic cooldown');out.switchPreservesCadence=true;
 A.assert(G.Moves.BY_ID.tackle.type==='normal','hidden fighting basic mutated shared move definition');
 // Selecting the ordinary whirlwind must not add a second, hidden basic stream.
 A.leeArena();A.basicCasts=[];m=A.select('naruto-lee');m.t=10;e=A.spawn(35,0);p.target=e;
 for(let n=0;n<20;n++)A.basicTick(.02);
 A.assert(!A.basicCasts.length&&e.hp===100000,'basic ran while non-Lotus skill selected');
 // Two bound Lotus skills retain their group identity and share one fallback.
 m=A.basicFixture('naruto-lotus');const other=p.moves.find(m=>m.id==='naruto-reverse-lotus');
 const groups=p.slots,active=p.active;const bound=[m,other];p.slots=[bound];p.active=0;m.t=other.t=10;
 e=A.spawn(35,0);p.target=e;const fn=p.activeGroup;A.basicCasts=[];A.basicTick(.01);
 A.assert(A.basicCasts.length===1&&A.basicCasts[0].id==='tackle'&&p.slots[0]===bound&&p.activeGroup===fn,'bound group duplicated fallback or changed identity');
 A.assert(near(m.t,9.99)&&near(other.t,9.99),'bound cooldown double tick');
 G.Combat.clearFields(p);other.t=0;A.basicCasts=[];A.basicTick(.01);
 A.assert(A.basicCasts.length===1&&A.basicCasts[0].id===other.id&&G.NarutoLee.active?.move.id===other.id,'bound ready technique did not take priority');
 G.Combat.clearFields(p);p.slots=groups;p.active=active;
 // Passive Gates, criticals, percent-HP and lifesteal use the normal owned-hit path once.
 p.level=12;const learn=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-gates');A.assert(learn&&learn.apply(p)!==false,'learn passive gates');
 m=A.basicFixture('naruto-lotus');e=A.spawn(35,0);p.target=e;p.percentHealthDamage=.01;p.critChance=1;p.lifestealRate=.001;p.hp=10;
 const beforeHp=p.hp,beforeDamage=p.dmgDealt,factor=G.NarutoGates.healingMultiplier(p);
 const expected=G.Moves.BY_ID.tackle.dmg*p.atk*G.Types.mult('fighting',e.types)*G.Weather.mult('fighting')*1.5+e.maxHp*.01;
 A.basicTick(.01);
 A.assert(near(100000-e.hp,Math.round(expected))&&near(p.dmgDealt-beforeDamage,expected),'basic percent/critical ownership duplicated');
 A.assert(near(p.hp-beforeHp,expected*.001*factor),'basic lifesteal/Gates healing formula incorrect');
 out.ownedDamage={damage:expected,healed:p.hp-beforeHp,healingFactor:factor};
 p.percentHealthDamage=p.critChance=p.lifestealRate=0;return out;
}"""

ART=r"""() => {
 const A=Acceptance,p=A.p(),out={};
 for(const id of ['naruto-lotus','naruto-reverse-lotus']){
   A.basicFixture(id);p.target=A.spawn(35,0);A.basicTick(.01);
   const sample=A.render();A.assert(sample.state.key==='lee-opened-attack','cooldown punch used wrong animation '+id+' '+sample.state.key);
   A.assert(sample.sources.every(s=>s.includes('/lee-gates-common-v1.png')),'cooldown punch borrowed a different skill/hero atlas');out[id]=sample;
 }return out;
}"""


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'errors':[],'failedRequests':[],'viewports':{}}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            for mobile in (False,True):
                label='mobile' if mobile else 'desktop'
                ctx=browser.new_context(locale='zh-TW',viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
                page=ctx.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
                page.on('response',lambda r:report['failedRequests'].append(r.url) if r.status>=400 and '127.0.0.1' in r.url else None)
                page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY&&G.AnimationLab&&document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30006"]').click();page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
                page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(HELPERS)
                result={'combat':page.evaluate(COMBAT)};report['viewports'][label]=result
                page.evaluate(AUDIT);result['art']=page.evaluate(ART)
                for name,pose in result['art'].items():
                    (OUT/f'{label}-{name}.png').write_bytes(base64.b64decode(pose.pop('png').split(',',1)[1]))
                result['worldReset']=page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p(),m=A.basicFixture('naruto-lotus');p.target=A.spawn(35,0);A.basicTick(.01);A.assert(A.basicCasts.length===1,'reset fixture');
                  const original=G.World;try{G.World={...original};A.basicCasts=[];A.basicTick(.01);A.assert(A.basicCasts.length===1,'private basic timer leaked across worlds')}finally{G.World=original}
                  G.Game.toUI();G.Flow.play();G.Game.togglePause();const next=G.Game.player;
                  A.assert(next!==p&&!next.hasMove('tackle')&&next.moves.length===1,'new run retained hidden learned basic');return true;
                }""")
                ctx.close()
            browser.close()
        assert not report['errors'],report['errors']
        assert not report['failedRequests'],report['failedRequests']
        report['ok']=True
    except Exception as error:
        report['ok']=False;report['failure']=str(error);raise
    finally:
        (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'evidence':str(OUT)},ensure_ascii=False))

if __name__=='__main__':main()
