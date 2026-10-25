"""Pain level durability through native XP, cards and incoming damage."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-durability'

SETUP = r"""() => {
 Acceptance.durabilityStep=dt=>{
   Acceptance.resume();try{G.Combat.updateFields(dt)}finally{Acceptance.pause()}
 };
}"""

CHECK = r"""() => {
 const A=Acceptance,P=G.NarutoPain,original=A.p(),mon=G.DEX.find(m=>m.dex===30010),out={};
 const keys=['mon','dex','level','maxHp','hp','painHealthBonus','moves','slots','xp','xpNext','xpMul','dmgReduce','regenFlat','lifestealRate','item','dead','r','bodyH','spdMul','cdMul','giantPicks'];
 const saved=Object.fromEntries(keys.map(key=>[key,original[key]])),savedBuffs=structuredClone(original.buffs),savedScale=original.anim.scale;
 const close=(actual,expected,message)=>A.assert(Math.abs(actual-expected)<1e-6,message+' '+JSON.stringify({actual,expected}));
 const stat=id=>{const card=G.LevelUp.STATS.find(c=>c.id===id);A.assert(card,'missing native card '+id);return card};
 function fresh(level=1,hp=200){
   G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();
   const p=original;Object.assign(p,{mon,dex:mon.dex,level,maxHp:200,hp,painHealthBonus:0,dead:false,dmgReduce:.16,giantPicks:0,r:saved.r,bodyH:saved.bodyH,spdMul:saved.spdMul,cdMul:saved.cdMul});p.anim.scale=savedScale;p.moves=[];p.slots=[];
   p.buffs.def={n:0,t:0,amount:0};p.invuln=0;p.frozen=false;
   p.xp=0;p.xpNext=G.Player.xpFor(level);p.xpMul=1;p.regenFlat=0;p.lifestealRate=0;p.item=null;
   P.syncDurability(p);return p;
 }
 function nativeHit(p,raw,type=null){const before=p.hp;p.invuln=0;p.hurt(raw,type);return before-p.hp}
 try{
   A.assert(mon.hp===120,'normal Pain base HP fixture changed');
   A.assert(typeof P.syncDurability==='function'&&typeof P.damageReductionBonus==='function'&&typeof P.durabilityState==='function','durability APIs missing');
   out.levels=[];
   for(const [level,hp,reduction] of [[1,200,.16],[15,284,.30],[21,320,.36],[25,344,.36],[34,398,.36],[35,400,.36],[203,400,.36]]){
     const p=fresh(level);close(p.maxHp,hp,'level maximum HP '+level);close(p.hp,hp,'new level capacity did not heal added capacity only '+level);
     close(p.reduction,reduction,'effective innate reduction '+level);close(p.dmgReduce,.16,'innate armor mutated card armor');
     const rows=G.RunAttributes.rows(p);A.assert(rows.some(r=>r.id==='painHealthGrowth')===(level>1),'growth HUD row level '+level);if(level>1)A.assert(rows.find(r=>r.id==='painDefenseGrowth').text.includes(Math.round(p.reduction*100)+'%'),'growth HUD effective armor');out.levels.push({level,maxHp:p.maxHp,reduction:p.reduction,state:P.durabilityState(p),rows});
   }
   let p=fresh(1,150);const one=p.gainXp(p.xpNext);
   A.assert(one===1&&p.level===2,'native XP did not gain exactly one level');close(p.maxHp,206,'single native XP level max HP');close(p.hp,156,'single XP level fully healed missing health');
   const once=p.hp;p.gainXp(0);P.syncDurability(p);close(p.hp,once,'zero XP or repeat sync granted another heal');
   out.singleXp={level:p.level,maxHp:p.maxHp,hp:p.hp};
   p=fresh(34,150);p.gainXp(p.xpNext);close(p.level,35,'native cap-crossing level');close(p.maxHp,400,'health growth must stop exactly at 200');close(p.hp,350,'last growth step must add only two HP');
   const capHp=p.hp;p.gainXp(p.xpNext);close(p.maxHp,400,'post-cap XP increased maximum health');close(p.hp,capHp,'post-cap XP healed missing health');
   close(p.painHealthBonus,200,'tracked growth cap');close(P.damageReductionBonus(p),.2,'reduction growth cap');
   stat('maxHealthPercent').apply(p);close(p.maxHp,440,'growth cap blocked health card');stat('giant').apply(p);close(p.maxHp,550,'growth cap blocked giant card');
   const cappedCardHp=p.hp;p.gainXp(p.xpNext);close(p.maxHp,550,'post-card capped XP changed capacity');close(p.hp,cappedCardHp,'post-card capped XP healed');
   out.growthCap={level:p.level,maxHp:p.maxHp,hp:p.hp,trackedBonus:p.painHealthBonus};
   p=fresh(1,150);const xp=Array.from({length:14},(_,i)=>G.Player.xpFor(i+1)).reduce((a,b)=>a+b,0),levels=p.gainXp(xp);
   A.assert(levels===14&&p.level===15,'native multi-level XP did not reach level 15');close(p.maxHp,284,'multi-level XP max HP');close(p.hp,234,'multi-level XP did not preserve missing health');
   out.multiXp={levels,xp,maxHp:p.maxHp,hp:p.hp,missing:p.maxHp-p.hp};
   p=fresh(1,150);p.level=15;p.update(0);close(p.maxHp,284,'native update did not synchronize practice-style level assignment');close(p.hp,234,'update sync healed beyond added capacity');
   const before={maxHp:p.maxHp,hp:p.hp},world=G.World;
   for(let i=0;i<5;i++){P.syncDurability(p);G.Combat.clearFields();A.durabilityStep(.01)}
   G.World={...world};try{A.durabilityStep(.01);P.syncDurability(p)}finally{G.World=world}
   close(p.maxHp,before.maxHp,'clear/world cycles farmed capacity');close(p.hp,before.hp,'clear/world cycles farmed healing');out.noFarming={maxHp:p.maxHp,hp:p.hp};
   G.Combat.clearFields();A.durabilityStep(.01);A.durabilityStep(1.6);const bodies=P.actorsFor(p);A.assert(bodies.length===5,'five support capacity fixtures missing');
   for(const b of bodies){close(b.maxHp,568,'support did not inherit twice grown Tendo maximum');close(P.damageReductionBonus(b),0,'support inherited its own Tendo armor');const hp=b.hp;b.hurt(100,null,false);close(hp-b.hp,84,'support inherited Tendo innate armor '+b.path)}
   out.supports=bodies.map(b=>({path:b.path,maxHp:b.maxHp,damageTaken:568-b.hp,innateArmor:P.damageReductionBonus(b)}));
   p=fresh(15,150);const missing=p.maxHp-p.hp;stat('maxHealthPercent').apply(p);close(p.maxHp,312.4,'native health growth card max HP');
   const grown=p.maxHp;P.syncDurability(p);close(p.maxHp,grown,'growth card caused innate bonus duplication');
   stat('giant').apply(p);close(p.maxHp,390.5,'native giant health multiplier');close(p.maxHp-p.hp,missing,'health cards did not preserve missing HP');
   p.gainXp(p.xpNext);close(p.level,16,'post-card native XP level');close(p.maxHp,396.5,'new level multiplied its flat HP bonus through prior cards');close(p.maxHp-p.hp,missing,'post-card XP healed existing missing HP');
   out.cards={level:p.level,maxHp:p.maxHp,hp:p.hp,missing,trackedBonus:p.painHealthBonus};
   p=fresh(15);stat('def').apply(p);stat('def').apply(p);close(p.dmgReduce,.28,'native defense card state changed');close(p.reduction,.42,'native defense cards did not stack with innate armor');
   p.buffs.def.n=2;p.buffs.def.amount=.1;close(p.reduction,.62,'temporary defense did not stack');p.dmgReduce=.7;close(p.reduction,.8,'global 80 percent armor cap changed');out.armorCap=p.reduction;
   p=fresh(15);p.invuln=0;p.hurt(p.maxHp+1,null,true);A.assert(p.dead&&p.hp===0,'native lethal fixture failed');
   p.level=16;P.syncDurability(p);close(p.maxHp,290,'dead owner capacity did not grow');A.assert(p.dead&&p.hp===0,'direct sync resurrected dead Tendo');
   p.xpNext=G.Player.xpFor(16);p.gainXp(p.xpNext);close(p.maxHp,296,'dead native XP capacity did not grow');A.assert(p.dead&&p.hp===0,'native XP resurrected dead Tendo');out.deadGrowth={level:p.level,maxHp:p.maxHp,hp:p.hp,dead:p.dead};
   p=fresh(15,150);const other=G.DEX.find(m=>m.dex===30009);p.mon=other;p.dex=other.dex;P.syncDurability(p);
   close(p.maxHp,200,'hero change retained innate health');close(p.hp,150,'hero change altered pre-growth missing HP');close(P.damageReductionBonus(p),0,'hero change retained innate armor');out.heroChange={maxHp:p.maxHp,hp:p.hp,bonus:P.damageReductionBonus(p)};
   const another=new G.Player(mon,{hp:80,dmgReduce:.16});another.level=25;P.syncDurability(another);close(another.maxHp,200,'non-main Pain received innate health');close(P.damageReductionBonus(another),0,'non-main Pain received innate armor');
   const newRun=new G.Player(mon,{hp:80,dmgReduce:.16});close(newRun.level,1,'new run inherited previous level');close(newRun.maxHp,200,'new run inherited previous level health');close(newRun.painHealthBonus||0,0,'new run inherited tracked health bonus');out.freshRun=true;
   out.incoming=[];
   for(const [seconds,expectedRaw] of [[300,57.6],[480,113.14285714285714],[600,163.2]]){
     const def=G.Enemies.bagAt(seconds).filter(d=>d.behavior!=='tank').sort((a,b)=>b.dmg-a.dmg)[0];A.assert(def,'native enemy bag had no ordinary mob');
     const enemy=new G.Enemy(def,500,0,G.Enemies.scale(seconds)),raw=enemy.dmg*2.4;close(raw,expectedRaw,'native spawn damage curve '+seconds);
     for(const level of [1,15])for(const type of [null,'dark']){
       p=fresh(level);const factor=type?G.Types.mult(type,p.mon.types)*G.Weather.mult(type):1,before=p.hp,expected=Math.min(before,raw*factor*(1-p.reduction));
       const damage=nativeHit(p,raw,type);close(damage,expected,'native incoming damage '+JSON.stringify({seconds,level,type}));
       out.incoming.push({seconds,level,type,raw,maxHp:p.maxHp,reduction:p.reduction,resolvedDamage:raw*factor*(1-p.reduction),damage,hp:p.hp,dead:p.dead});
     }
   }
   p=fresh(15);const weak=G.Types.mult('dark',p.mon.types)*G.Weather.mult('dark');close(weak,1.6,'native dark weakness fixture changed');
   const sequence=[];for(let i=0;i<2;i++){sequence.push(nativeHit(p,163.2,'dark'));if(i<1)A.assert(!p.dead&&p.hp>0,'grown Tendo died before second 10-minute weakness hit')}
   A.assert(p.dead&&p.hp===0,'second native 10-minute weakness hit should still be lethal');out.tenMinuteWeakness={sequence,dead:p.dead};
   return out;
 }finally{G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();Object.assign(original,saved);original.buffs=savedBuffs;original.anim.scale=savedScale;original.anim._start(original.dead?'Faint':'Idle',false);A.reset()}
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'errors': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for label, viewport, mobile in [('desktop', {'width':1200,'height':900}, False), ('mobile', {'width':390,'height':844}, True)]:
                context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
                outer = context.new_page()
                outer.on('pageerror', lambda error: report['errors'].append(str(error)))
                outer.goto(URL)
                frame = game_frame(outer)
                enter(frame)
                frame.evaluate(SETUP)
                report['viewports'][label] = frame.evaluate(CHECK)
                outer.wait_for_timeout(100)
                outer.screenshot(path=str(OUT / f'{label}-growth-hud.png'))
                print(label, 'Pain durability PASS', flush=True)
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
