"""Native learned passive shield, migration, and armor composition acceptance."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS, SETUP, SHIELD
OUT=Path(__file__).resolve().parents[1]/'.omx/state/gaara-passive-shield'

PASSIVE=r"""()=>{
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,id='naruto-sand-shield';p.level=1;
 A.assert(!p.hasMove(id)&&!N.shieldState(p),'shield must be learned, not innate');
 const slots=p.slots.length,card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
 A.assert(card&&card.apply(p)!==false,'Lv1 native shield learn card');
 const m=p.moves.find(m=>m.id===id);A.assert(m.passive&&p.slots.length===slots&&!p.slots.some(g=>g.includes(m)),'passive consumed slot');
 A.advance(.001);const hp=p.hp;p.invuln=0;p.hurt(2,null,true);
 A.assert(p.hp===hp&&N.shieldState(p).amount===44,'learned Lv1 passive did not absorb');
 p.level=15;
 for(const id of ['naruto-sand-coffin','naruto-sand-tsunami','naruto-sand-prison','naruto-sand-armor']){
  const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'native active learn '+id);
 }
 A.assert(p.slots.length===5,'all active skills fit alongside shield');
 // A learned passive is still offered when five genuine active slots are occupied.
 p.moves=p.moves.filter(m=>m!==p.moves.find(m=>m.id==='naruto-sand-shield'));G.Combat.clearFields(p);
 const fullCard=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
 A.assert(fullCard&&fullCard.apply(p)!==false&&p.slots.length===5,'full active slots blocked shield learning');
 const shield=p.moves.find(m=>m.id===id);
 A.select('naruto-sand-coffin');shield.passive=false;p.slots.unshift([shield]);p.active++;p.bind[id]=0;p.arrange();
 A.assert(p.activeGroup().some(m=>m.id==='naruto-sand-coffin')&&!p.slots.some(g=>g.includes(shield))&&p.bind[id]===undefined,'migration lost selected nonshield or binding');
 shield.passive=false;p.slots.push([shield]);p.active=p.slots.length-1;p.bind[id]=4;p.arrange();
 A.assert(p.activeGroup().some(m=>!m.passive)&&!p.slots.some(g=>g.includes(shield))&&p.bind[id]===undefined,'selected old shield migration invalid');
 return {learnedAtLevel:1,slots:p.slots.length,migration:true,fullSlots:true};
}"""

LIFECYCLE=r"""()=>{
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,id='naruto-sand-shield',near=(a,b)=>Math.abs(a-b)<1e-6;
 A.gaaraArena();A.select('naruto-gaara');A.advance(1);
 let previous=N.shieldState(p);p.invuln=0;p.hurt(3,null,true);previous=N.shieldState(p);
 for(const id of ['naruto-sand-coffin','naruto-sand-tsunami','naruto-sand-prison','naruto-sand-armor','naruto-gaara']){
  A.select(id);const state=N.shieldState(p);A.assert(near(state.amount,previous.amount)&&near(state.progress,previous.progress),'switch reset shield '+id);
  const hp=p.hp;p.invuln=0;p.hurt(1,null,true);A.advance(.1);const after=N.shieldState(p);
  A.assert(p.hp===hp&&near(after.amount,previous.amount-1)&&near(after.progress,previous.progress+.1/(12*p.cdMul)),'passive failed with '+id);previous=after;
 }
 const before=N.shieldState(p);G.Combat.updateFields(1);A.assert(N.shieldState(p).progress===before.progress,'paused clock advanced');
 for(const reason of ['clear','death','world','owner','unlearn']){
  A.gaaraArena();A.advance(.01);const moves=p.moves,world=G.World,game=G.Game;
  if(reason==='clear')G.Combat.clearFields(p);if(reason==='death')p.dead=true;
  if(reason==='world')G.World={...world};if(reason==='owner')G.Game={...game,player:{...p}};
  if(reason==='unlearn')p.moves=p.moves.filter(m=>m.id!==id);
  if(reason!=='clear')G.Combat.updateFields(.01);
  const state=N.shieldState(p);A.assert(['clear','world'].includes(reason)?state&&state.world===G.World&&state.amount===state.capacity&&state.progress<.001:!state,'cleanup leaked shield '+reason);
  G.World=world;G.Game=game;p.moves=moves;p.dead=false;
 }
 A.gaaraArena();return {allSelections:true,pause:true,cleanup:true};
}"""

ARMOR=r"""()=>{
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,near=(a,b)=>Math.abs(a-b)<1e-6;
 A.gaaraArena();A.select('naruto-sand-armor');A.spawn(80,0);A.resume();G.Combat.tick(.001,p,0);A.pause();
 A.assert(N.armorState(p)?.reduction===.3,'armor fixture');
 const hit=n=>{p.invuln=0;A.resume();p.hurt(n,null,true);A.pause()};
 const hp=p.hp,initial=N.shieldState(p).amount;hit(10);
 A.assert(p.hp===hp&&near(N.shieldState(p).amount,initial-7)&&N.armorState(p).hits===0,'shield-only armor hit counted/reduction twice');
 let amount=N.shieldState(p).amount;hit((amount+.5)/.7);
 A.assert(near(p.hp,hp-.5)&&N.shieldState(p).amount===0&&N.armorState(p).hits===1,'fractional overflow or armor counter');
 const accepted=p.hp;A.resume();p.hurt(10,null,true);A.pause();A.assert(p.hp===accepted&&N.armorState(p).hits===1,'invulnerable hit counted');
 hit(0);A.assert(p.hp===accepted&&N.armorState(p).hits===1,'zero counted');
 hit(10);A.assert(N.armorState(p)?.hits===2,'second overflow absent');hit(10);
 A.assert(!N.armorState(p)&&G.EnemyMgr.all()[0].hp<100000,'third HP hit did not burst');
 A.gaaraArena();A.select('naruto-sand-armor');A.spawn(80,0);A.resume();G.Combat.tick(.001,p,0);A.pause();
 const typedAmount=N.shieldState(p).amount,type='fire',factor=G.Types.mult(type,p.mon.types)*G.Weather.mult(type);
 const close=p.activeGroup().some(m=>m.kind==='melee')?.75:1,expected=(10*.7*factor)*(1-p.reduction)*close;
 p.invuln=0;A.resume();p.hurt(10,type,false);A.pause();
 A.assert(near(N.shieldState(p).amount,typedAmount-Math.max(1,expected))&&N.armorState(p).hits===0,'native type/weather/reduction applied incorrectly');
 return {reductionOnce:true,shieldOnlyNotCounted:true,fractionalOverflow:true,thirdHpHitBursts:true,nativeTypedDamage:true};
}"""

CAPTURE=r"""id=>{
 const A=Acceptance,p=A.p();A.gaaraArena();A.select(id);A.spawn(100,0);
 if(id==='naruto-sand-armor'){A.resume();G.Combat.tick(.001,p,0);A.pause()}
 else {A.actualCast(id);A.advance(.3)}
 p.invuln=0;A.resume();p.hurt(2,null,true,{fromX:100,fromY:0});A.pause();
 A.assert(G.NarutoGaara.shieldState(p).flash>0,'passive visual missing');
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report={'errors':[], 'viewports':{}}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            for mobile in [False,True]:
                label='mobile' if mobile else 'desktop'
                context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
                page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
                page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click();page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(PASSIVE)
                active=page.evaluate('Acceptance.p().active')
                point=page.evaluate("""()=>{
                  const p=Acceptance.p(),index=p.slots.length,n=index+p.moves.filter(m=>m.passive&&!p.slots.some(s=>s.includes(m))).length;
                  if(innerWidth<500){const r=G.Touch.controlLayout(innerWidth,innerHeight,n).slots[index];return {x:r.x+r.w/2,y:r.y+r.h/2}}
                  return {x:(innerWidth-(n*54+(n-1)*9))/2+index*63+27,y:innerHeight-45};
                }""")
                page.evaluate('Acceptance.resume()')
                if mobile:page.touchscreen.tap(point['x'],point['y'])
                else:page.mouse.click(point['x'],point['y'])
                page.evaluate('Acceptance.pause()')
                assert page.evaluate('Acceptance.p().active')==active,'passive HUD selected active slot'
                result={'stages':page.evaluate(SHIELD),'lifecycle':page.evaluate(LIFECYCLE),'armorCombination':page.evaluate(ARMOR)};report['viewports'][label]=result
                for skill in ['naruto-sand-coffin','naruto-sand-armor']:
                    page.evaluate(CAPTURE,skill)
                    page.locator('#game').screenshot(path=str(OUT/f'{label}-passive-{skill}.png'))
                context.close()
            browser.close()
        assert not report['errors'],report['errors'];report['ok']=True
    except Exception as e:
        report['ok']=False;report['failure']=str(e);raise
    finally:(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'evidence':str(OUT)}))

if __name__=='__main__':main()
