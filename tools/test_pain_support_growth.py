"""Support-only growth beta; native XP, incoming damage and body revival."""
import os,json
from pathlib import Path
os.environ.setdefault('PAIN_URL','http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=pain&painBeta=1&painSupportGrowth=1')
from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME,URL,enter,game_frame
CHECK=r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out=[];
 const close=(v,e,m)=>A.assert(Math.abs(v-e)<1e-6,m+JSON.stringify({v,e}));
 for(const [level,bonus,armor] of [[1,0,0],[15,84,.14],[21,120,.2],[34,198,.2],[35,200,.2],[203,200,.2]]){
  A.reset();Object.assign(p,{level,maxHp:200,hp:150,painHealthBonus:0,dmgReduce:.16,dead:false,regenFlat:0});p.buffs.def={n:0,t:0,amount:0};P.syncDurability(p);
  A.advance();A.finish(1.6);const bodies=P.actorsFor(p);A.assert(bodies.length===5,'five bodies missing');
  close(p.maxHp,200,'Tendo received health growth');close(p.hp,150,'Tendo received growth healing');close(P.damageReductionBonus(p),0,'Tendo received armor growth');close(p.reduction,.16,'Tendo effective armor');
  for(const b of bodies){close(b.maxHp,400+bonus,'body capacity');close(P.damageReductionBonus(b),armor,'body armor');b.hp=b.maxHp;b.invuln=0;b.hurt(100,null,false);close(b.maxHp-b.hp,100*(1-.16-armor),'body actual damage');b.invuln=0;const hp=b.hp;P.syncDurability(p);A.advance();close(b.hp,hp,'repeat sync healed body');}
  const rows=G.RunAttributes.rows(p);if(bonus)A.assert(rows.find(r=>r.id==='painHealthGrowth').text.includes('\u4e94\u9053'),'HUD attributes assigned to Tendo');
  out.push({level,bonus,armor,tendoHp:p.maxHp,bodies:bodies.map(b=>({path:b.path,maxHp:b.maxHp}))});
 }
 A.reset();Object.assign(p,{level:34,maxHp:200,hp:150,painHealthBonus:0,xp:0,xpNext:G.Player.xpFor(34),xpMul:1,dmgReduce:.16,dead:false,regenFlat:0});P.syncDurability(p);A.advance();A.finish(1.6);
 const bodies=P.actorsFor(p);for(const b of bodies)b.hp=b.maxHp-50;
 const dead=bodies.find(b=>b.path==='asura');dead.invuln=0;dead.hurt(dead.maxHp+1,null,true);A.assert(dead.dead,'native support death');
 p.gainXp(p.xpNext);close(p.level,35,'native cap XP');close(p.maxHp,200,'XP grew Tendo');close(p.hp,150,'XP healed Tendo');
 for(const b of bodies){close(b.maxHp,600,'cap capacity');if(b!==dead)close(b.hp,550,'cap should add only two HP');else close(b.hp,0,'growth revived dead body');}
 p.gainXp(p.xpNext);for(const b of bodies)if(b!==dead)close(b.hp,550,'postcap XP healed');
 p.moves=p.moves.filter(m=>m.id!=='naruto-pain-repair');A.finish(16.1);A.assert(!dead.dead,'natural support revival failed');close(dead.maxHp,600,'revival lost growth');close(dead.hp,600,'revival not full');
 const card=G.LevelUp.STATS.find(c=>c.id==='maxHealthPercent');card.apply(p);A.advance();close(p.maxHp,220,'health card failed');for(const b of P.actorsFor(p))close(b.maxHp,640,'health card doubled growth bonus');
 const naraka=P.actorsFor(p).find(b=>b.path==='naraka'),asura=P.actorsFor(p).find(b=>b.path==='asura');
 p.invuln=0;p.hurt(p.maxHp+1,null,true);A.assert(p.dead,'Tendo death fixture');close(P.damageReductionBonus(naraka),.4,'Naraka lacks extra armor while Tendo dead');close(P.damageReductionBonus(asura),.2,'other path received rescue armor');
 naraka.hp=naraka.maxHp;naraka.invuln=0;let hp=naraka.hp;naraka.hurt(100,null,false);close(hp-naraka.hp,44,'Naraka rescue armor actual damage');
 p.dmgReduce=.7;naraka.invuln=0;hp=naraka.hp;naraka.hurt(100,null,false);close(hp-naraka.hp,20,'rescue armor exceeded total cap');naraka.invuln=0;hp=naraka.hp;naraka.hurt(100,null,true);close(hp-naraka.hp,100,'rescue armor reduced pure damage');p.dmgReduce=.16;
 p.revive(1);close(P.damageReductionBonus(naraka),.2,'rescue armor remained after revival');naraka.invuln=0;hp=naraka.hp;naraka.hurt(100,null,false);close(hp-naraka.hp,64,'restored normal armor damage');
 const texts=[],canvas=document.createElement('canvas');canvas.width=innerWidth;canvas.height=innerHeight;const ctx=canvas.getContext('2d'),fill=ctx.fillText.bind(ctx);ctx.fillText=(text,...args)=>{texts.push(String(text));return fill(text,...args)};
 for(const rank of [1,5]){const rod=G.Moves.instance('naruto-pain',rank),missile=G.Moves.instance('naruto-pain-missiles',rank);for(const q of [0,5,100]){p.quantityPicks=q;p.moves=[rod,missile];G.HUD.draw(ctx,innerWidth,innerHeight,p,G.Game.st);for(const m of p.moves)A.assert(texts.includes(P.projectileCount(p,m)+'\u0020\u767c'),'HUD omitted projectile count');}}
 return {levels:out,nativeXp:true,cap:true,deadGrowth:true,naturalRevival:true,cards:true,narakaRescueArmor:true,projectileHud:true};
}"""
def main():
 out=Path('.omx/state/pain-support-growth');out.mkdir(parents=True,exist_ok=True)
 report={'url':URL,'errors':[],'viewports':{}}
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=CHROME,headless=True)
   for name,size in [('desktop',{'width':1200,'height':900}),('mobile',{'width':390,'height':844})]:
    page=browser.new_page(viewport=size,is_mobile=name=='mobile',has_touch=name=='mobile',service_workers='block');page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(URL);frame=game_frame(page);enter(frame)
    report['viewports'][name]=frame.evaluate(CHECK);page.screenshot(path=str(out/(name+'.png')));page.close();print(name,'support growth PASS',flush=True)
   browser.close()
  assert not report['errors'];report['ok']=True
 finally:(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
