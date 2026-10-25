"""Native support strikes/skills inherit lifesteal without sharing the heal."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-lifesteal'

SETUP = r"""() => {
 const A=Acceptance;
 A.lifeWatch=run=>{
   const p=A.p(),had=Object.hasOwn(p,'onDealt'),original=p.onDealt,credits=[];
   p.onDealt=function(amount,...rest){credits.push(amount);return original.call(this,amount,...rest)};
   try{return {result:run(credits),credits,total:credits.reduce((n,v)=>n+v,0)}}finally{if(had)p.onDealt=original;else delete p.onDealt}
 };
}"""

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,moves=p.moves,out={};
 const saved={maxHp:p.maxHp,hp:p.hp,baseAtk:p.baseAtk,atkMul:p.atkMul,atkBuff:p.buffs.atk.n,item:p.item,
   lifestealRate:p.lifestealRate,percentHealthDamage:p.percentHealthDamage,damageSplashPicks:p.damageSplashPicks};
 const bodies=()=>P.actorsFor(p),body=path=>bodies().find(b=>b.path===path);
 const close=(actual,expected,message)=>A.assert(Math.abs(actual-expected)<1e-6,message+' '+JSON.stringify({actual,expected}));
 function fresh(id='naruto-pain',rate=.1){
   p.dead=false;p.maxHp=1000;p.hp=500;p.moves=moves.filter(m=>m.id===id);A.reset();
   p.baseAtk=10;p.atkMul=1;p.buffs.atk.n=0;p.item=null;p.lifestealRate=rate;p.damageSplashPicks=0;p.percentHealthDamage=0;p.hp=500;
   for(const b of bodies()){b.hp=1000;b.cooldown=999}
 }
 function untouched(source,before){for(const b of bodies())if(b!==source)close(b.hp,before[b.path],'unrelated support healed '+b.path)}
 const capacities=()=>Object.fromEntries(bodies().map(b=>[b.path,b.hp]));
 function contact(path,options={}){
   fresh('naruto-pain',options.rate??.1);const b=body(path);b.x=250;b.y=0;b.cooldown=0;
   if(options.cardPicks){const card=G.LevelUp.STATS.find(c=>c.id==='lifesteal');A.assert(card,'native lifesteal card missing');for(let i=0;i<options.cardPicks;i++)card.apply(p)}
   if(options.ownerFull)p.hp=p.maxHp;if(options.bodyFull)b.hp=b.maxHp;
   p.percentHealthDamage=options.percent??0;p.damageSplashPicks=options.splash??0;
   const e=A.spawn(265,0),secondary=options.splash?A.spawn(310,0):null,hits=A.watch(secondary?[e,secondary]:[e]);
   const before=capacities(),ownerHp=p.hp,beforeSource=b.hp;
   const observed=A.lifeWatch(()=>A.advance());
   A.assert(hits.some(h=>h.owned&&h.id==='naruto-pain'),'native support contact did not damage target '+path);
   const heal=observed.total*p.lifestealRate;
   close(p.hp,Math.min(p.maxHp,ownerHp+heal),'Tendo did not receive its full independent heal');
   close(b.hp,Math.min(b.maxHp,beforeSource+heal),'attacking body did not receive its full independent heal '+path);
   untouched(b,before);
   return {path,rate:p.lifestealRate,damage:observed.total,credits:observed.credits,ownerHealed:p.hp-ownerHp,bodyHealed:b.hp-beforeSource,
     hits:hits.length,secondaryHp:secondary?.hp};
 }
 function skill(kind,path,invalid=null){
   fresh('naruto-pain-'+kind);const b=body(path);b.x=0;b.y=0;const target=A.spawn(140,0),hits=A.watch([target]),ownerHp=p.hp,before=capacities();
   A.ready(kind);let invalidated=false,steps=0;
   const observed=A.lifeWatch(credits=>{
     while(!credits.length&&steps++<600){
       A.advance();
       if(invalid&&!invalidated&&P.shots.some(s=>s.kind==='missile')){
         if(invalid==='dead'){b.invuln=0;b.hurt(b.maxHp+1,null,true);A.assert(b.dead,'native source death failed')}
         if(invalid==='unformed'){b.formed=false;b.placementRetry=999}
         if(invalid==='old-world')b.world={...G.World};
         if(invalid==='removed'){const list=P.stateFor(p).bodies;list[list.indexOf(b)]=Object.assign(Object.create(Object.getPrototypeOf(b)),b,{id:b.id+'-replacement'})}
         invalidated=true;
       }
     }
   });
   A.assert(observed.total>0&&hits.some(h=>h.owned&&h.id==='naruto-pain-'+kind),'native skill caused no credited hit '+kind+'/'+invalid);
   close(p.hp,Math.min(p.maxHp,ownerHp+observed.total*p.lifestealRate),'skill did not heal Tendo '+kind);
   close(b.hp,invalid==='dead'?0:Math.min(b.maxHp,before[path]+(invalid?0:observed.total*p.lifestealRate)),'skill healed wrong source body '+kind+'/'+invalid);
   untouched(b,before);if(invalid)A.assert(invalidated,'invalid source fixture never reached flight');
   return {kind,path,invalid,steps,damage:observed.total,ownerHealed:p.hp-ownerHp,bodyHealed:b.hp-(invalid==='dead'?0:before[path]),hits:hits.length};
 }
 try{
   out.contact=['asura','animal','human','preta','naraka'].map(path=>contact(path));
   out.ownerFull=contact('asura',{ownerFull:true});A.assert(out.ownerFull.bodyHealed>0&&out.ownerFull.ownerHealed===0,'full Tendo blocked body healing');
   out.bodyFull=contact('preta',{bodyFull:true});A.assert(out.bodyFull.ownerHealed>0&&out.bodyFull.bodyHealed===0,'full body blocked Tendo healing');
   out.zero=contact('naraka',{rate:0});A.assert(!out.zero.ownerHealed&&!out.zero.bodyHealed,'zero lifesteal healed allies');
   out.cards=contact('preta',{rate:0,cardPicks:3});close(out.cards.rate,.03,'three native cards did not stack');A.assert(out.cards.ownerHealed>0&&out.cards.bodyHealed>0,'native lifesteal cards were not inherited');
   out.percent=contact('human',{percent:.01});
   A.assert(out.percent.credits.length===2,'percent max-health bonus must be credited exactly once');
   close(out.percent.credits[0],1000,'percent max-health bonus changed');
   out.splash=contact('animal',{splash:10});A.assert(out.splash.hits===2&&out.splash.credits.length===1,'secondary splash generated lifesteal credit');
   out.skills=[skill('missiles','asura'),skill('summon','animal'),skill('soul','human')];
   out.invalid=['dead','unformed','old-world','removed'].map(reason=>skill('missiles','asura',reason));
   fresh();const b=body('preta');b.x=250;b.y=0;b.cooldown=0;A.spawn(265,0);p.invuln=0;p.hurt(p.maxHp+1,null,true);
   A.assert(p.dead&&p.hp===0&&P.canRevivePlayer(p),'native Tendo death did not leave rescuable family');
   const prior=b.hp,deadCredits=A.lifeWatch(()=>A.advance());
   A.assert(deadCredits.total>0,'support stopped attacking during Naraka rescue');close(b.hp,prior+deadCredits.total*p.lifestealRate,'rescue-time support failed to self heal');
   A.assert(p.dead&&p.hp===0,'support lifesteal revived or healed dead Tendo');out.deadTendo={damage:deadCredits.total,bodyHealed:b.hp-prior};
   fresh();const hpBefore=capacities(),enemy=A.spawn(150,0),rodHits=A.watch([enemy]),ownerHp=p.hp;
   const rods=A.lifeWatch(credits=>{for(let i=0;i<150&&!credits.length;i++)A.advance()});
   A.assert(rods.total>0&&rodHits.length>0,'native Tendo rods never landed');untouched(null,hpBefore);
   close(p.hp,Math.min(p.maxHp,ownerHp+rods.total*p.lifestealRate),'Tendo rod lifesteal changed');out.tendoOnly={damage:rods.total,hits:rodHits.length};
   return out;
 }finally{
   p.dead=false;p.moves=moves;Object.assign(p,{maxHp:saved.maxHp,hp:saved.hp,baseAtk:saved.baseAtk,atkMul:saved.atkMul,item:saved.item});p.buffs.atk.n=saved.atkBuff;A.reset();
   p.lifestealRate=saved.lifestealRate;p.percentHealthDamage=saved.percentHealthDamage;p.damageSplashPicks=saved.damageSplashPicks;
 }
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
                print(label, 'support lifesteal PASS', flush=True)
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
