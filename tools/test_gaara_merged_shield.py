"""One learned Sand Shield card powers native HP defense and roaming interception."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS, SETUP
from test_gaara_passive_shield import PASSIVE, ARMOR
from test_gaara_sand_guard import FIXTURE

OUT = Path(__file__).resolve().parents[1] / '.omx/state/gaara-merged-shield'

MERGED = r"""()=>{
 const A=Acceptance,p=A.p(),id='naruto-sand-shield',legacy='naruto-sand-guard',N=G.NarutoGaara;
 const m=p.moves.find(m=>m.id===id);p.level=1;
 A.assert(m&&m.lvl===1&&m.name==='砂之盾','one canonical learned shield');
 A.assert(m.def.desc.includes('護衛')&&m.def.desc.includes('盾量')&&!m.def.desc.includes('???')&&m.def.ups.every(up=>up.t.includes('盾量')&&up.t.includes('護衛')),'merged descriptions or upgrades are unreadable');
 A.assert(!G.Moves.BY_ID[legacy]&&!G.Moves.poolFor(p.mon).includes(legacy),'legacy skill exposed in catalog');
 A.assert(!p.moves.some(m=>m.id===legacy)&&p.moves.filter(m=>m.passive).length===1,'duplicate passive');
 A.assert(!document.querySelector('#scr-naruto-skills').textContent.includes('游砂護衛'),'old separate guide name');
 const guide=[...document.querySelectorAll('#scr-naruto-skills h4')].map(h=>h.textContent);
 A.assert(guide.filter(s=>s.includes('砂之盾')).length===1,'merged guide must appear once');
 const tiers=[];
 for(let tier=1;tier<=5;tier++){
  if(tier>1){const cards=G.LevelUp.offer(p,100);A.assert(cards.filter(c=>c.key==='up:'+id).length===1&&!cards.some(c=>c.key.includes(legacy)),'one upgrade card');const card=cards.find(c=>c.key==='up:'+id);A.assert(card.apply(p)!==false,'upgrade failed')}
  A.gaaraArena();A.advance(.001);const shield=N.shieldState(p),g=A.guard();
  const expected=[45,60,75,90,110][tier-1]+tier,count=[2,2,3,3,4][tier-1]+1;
  A.assert(shield.capacity===expected&&g.count===count&&g.tier===tier&&g.move===m,'single level did not upgrade both mechanics');
  const hp=p.hp;p.invuln=0;A.resume();p.hurt(10,null,true);A.pause();
  A.assert(p.hp===hp&&N.shieldState(p).amount===expected-10,'merged native HP absorption failed');
  g.guardians.forEach((c,i)=>{c.x=130;c.y=(i-1)*100});
  const q1=A.nativeShot(260,-100),q2=A.nativeShot(260,100);A.guardStep();
  const targets=g.guardians.filter(c=>c.target).map(c=>c.target);
  A.assert(targets.includes(q1)&&targets.includes(q2)&&new Set(targets).size===targets.length,'merged independent tracking failed');
  for(let i=0;i<100&&(G.Projectiles.all().includes(q1)||G.Projectiles.all().includes(q2));i++)A.guardStep();
  A.assert(!G.Projectiles.all().includes(q1)&&!G.Projectiles.all().includes(q2)&&g.guardians.filter(c=>!c.ready).length===2,'merged physical interception failed');
  A.assert(p.hp===hp&&N.shieldState(p).amount===expected-10,'intercept used HP shield capacity');
  tiers.push({tier,capacity:expected,guardians:count});
 }
 A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='up:'+id||c.key.includes(legacy)),'extra upgrade above level five');
 return {tiers,oneLearnedPassive:true,oneUpgrade:true,nativeAbsorption:true,independentNativeInterception:true};
}"""

MIGRATION = r"""()=>{
 const A=Acceptance,p=A.p(),id='naruto-sand-shield',legacy='naruto-sand-guard',N=G.NarutoGaara;
 const original=p.moves.slice(),canonical=p.moves.find(m=>m.id===id),active=p.activeGroup()[0];
 const other=original.filter(m=>m!==canonical),near=(a,b)=>Math.abs(a-b)<1e-6;
 const alias=G.Moves.instance(legacy,3);A.assert(alias.id===id&&alias.lvl===3&&alias.passive,'direct legacy instance not canonical');
 const cases=[];
 for(const [shieldTier,guardTier] of [[0,3],[2,5],[5,2]]){
  const kept=shieldTier?G.Moves.instance(id,shieldTier):G.Moves.instance(id,guardTier);
  if(!shieldTier)kept.id=legacy;
  kept.t=3.25;kept.dealt=91;kept.since=7;
  p.moves=[...other,kept];p.arrange();A.gaaraArena();A.advance(.25);
  const gs=A.guard(),cloud=gs.guardians[0],ss=N.shieldState(p);cloud.ready=false;cloud.charges=0;cloud.rechargeProgress=.37;
  p.invuln=0;A.resume();p.hurt(5,null,true);A.pause();const damaged=N.shieldState(p),beforeAmount=damaged.amount,beforeCapacity=damaged.capacity,beforeProgress=damaged.progress;
  if(shieldTier){const old=G.Moves.instance(id,guardTier);old.id=legacy;p.moves.push(old);p.slots.unshift([old]);p.active++;p.bind[legacy]=0}
  else {kept.id=legacy;kept.passive=false;p.slots.unshift([kept]);p.active++;p.bind[legacy]=0}
  // Runtime access itself must repair an injected old instance, before a menu opens.
  const shieldFirst=shieldTier===0?N.shieldState(p):null,merged=A.guard(),after=N.shieldState(p),max=Math.max(shieldTier,guardTier);
  A.assert(shieldTier!==0||shieldFirst,'legacy guard-only failed native shield lookup');
  A.assert(p.moves.filter(m=>m.id===id).length===1&&!p.moves.some(m=>m.id===legacy),'old/both not collapsed');
  A.assert(p.moves.find(m=>m.id===id)===kept&&kept.lvl===max&&kept.t===3.25&&kept.dealt===91&&kept.since===7,'migration lost instance/tier/timers');
  A.assert(merged===gs&&merged.guardians[0]===cloud&&!cloud.ready&&cloud.rechargeProgress===.37,'migration reset guardian runtime');
  A.assert(near(after.progress,beforeProgress)&&near(after.amount,beforeAmount+after.capacity-beforeCapacity),'migration reset shield runtime');
  A.assert(p.activeGroup().includes(active)&&!p.slots.some(g=>g.some(m=>[id,legacy].includes(m.id)))&&p.bind[legacy]===undefined,'migration damaged active selection');
  const n=p.moves.length;A.assert(p.addMove(legacy)===false&&p.addMove(id)===false&&p.moves.length===n&&kept.lvl===max,'legacy add duplicated/downgraded');
  cases.push({shieldTier,guardTier,result:max,preservedRuntime:true});
 }
 p.moves=original;p.arrange();A.gaaraArena();return cases;
}"""

CAPTURE = r"""skill=>{
 const A=Acceptance,p=A.p(),id='naruto-sand-shield';p.level=100;A.gaaraArena();A.select(skill);A.spawn(100,0);
 if(skill==='naruto-sand-armor'){A.resume();G.Combat.tick(.001,p,0);A.pause()}
 else {A.actualCast(skill);A.advance(.3)}
 A.advanceGuard(.4);const g=A.guard();A.assert(g.count===40&&g.guardians.length===40,'forty guardian screenshot');
 p.invuln=0;A.resume();p.hurt(2,null,true,{fromX:100,fromY:0});A.pause();
 const canvas=document.getElementById('game'),ctx=canvas.getContext('2d'),texts=[],icons=[],fill=ctx.fillText,draw=G.Icons.draw;
 ctx.fillText=function(t,...args){texts.push(String(t));return fill.call(this,t,...args)};
 G.Icons.draw=function(c,key,...args){icons.push(key);return draw.call(this,c,key,...args)};
 try{G.HUD.draw(ctx,innerWidth,innerHeight,p,{time:30})}finally{ctx.fillText=fill;G.Icons.draw=draw}
 A.assert(icons.filter(s=>s==='move:'+id).length===1&&!icons.includes('move:naruto-sand-guard'),'HUD not one passive icon');
 A.assert(texts.some(s=>s.includes(String(g.readyCount)+'/'+g.count)),'HUD lacks guardian count');
 A.assert(texts.some(s=>s.includes('/'+G.NarutoGaara.shieldState(p).capacity)),'HUD lacks HP shield capacity');
 return {selected:skill,guardians:g.count,passiveIcons:1,hudTexts:texts};
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
                page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY && G.NarutoSandGuard && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click();page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                for script in [HARNESS,SETUP,FIXTURE]:page.evaluate(script)
                result=report['viewports'][label]={}
                for name,script in [('learnAndFullSlots',PASSIVE),('merged',MERGED),('migration',MIGRATION),('armor',ARMOR)]:result[name]=page.evaluate(script)
                for skill in ['naruto-sand-coffin','naruto-sand-armor']:
                    result[skill]=page.evaluate(CAPTURE,skill)
                    page.locator('#game').screenshot(path=str(OUT/f'{label}-{skill}.png'))
                context.close()
            browser.close()
        assert not report['errors'],report['errors'];report['ok']=True
    except Exception as e:
        report.update(ok=False,failure=str(e));raise
    finally:(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'ok':True,'evidence':str(OUT)}))


if __name__=='__main__':main()
