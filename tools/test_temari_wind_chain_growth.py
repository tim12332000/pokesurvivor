"""Use real quantity offers to compare wind-chain previews and damage credit."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_temari as native

OUT = Path(__file__).resolve().parents[1] / '.omx/state/temari-fun/growth'
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,id='naruto-temari-great-scythe',derived='naruto-temari-wind-chain',out=[];
 A.assert(typeof T.windChainProfile==='function','wind chain capability absent');
 A.learn();
 for(const H of [1,3,5])for(const L of [0,1,5])for(const Q of [0,1,3,5,19]){
   A.reset();A.mastery(L);const move=A.rank(id,H);p.quantityPicks=p.quantityBonus=Q;
   (p.statsTaken??={}).quantity=Q;
   const before=T.windChainProfile(p,move),consumer=G.JujutsuGrowth.quantityBenefit(p).consumers.find(c=>c.id===id);
   A.assert(before.enabled&&consumer,'learned heavy has no chain benefit');
   for(const [label,key] of [['引爆風結','triggerLimit'],['風爆連切','cuts'],['風爆半徑','radius']])
     A.near(consumer.before[label],before[key],'before preview '+label);
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');
   A.assert(card&&card.apply(p)!==false,'real quantity offer missing '+JSON.stringify({H,L,Q}));
   const after=T.windChainProfile(p,move);
   for(const [label,key] of [['引爆風結','triggerLimit'],['風爆連切','cuts'],['風爆半徑','radius']])
     A.near(consumer.after[label],after[key],'after preview '+label);
   if(H===1&&L===1&&Q===0){
     A.assert(before.cuts===3&&after.cuts===4,'first card has no real extra cut');
     A.assert(before.triggerLimit===2&&after.triggerLimit===3,'first card trigger benefit');
     A.assert(before.radius===202&&after.radius===214,'first card actual coverage');
   }
   out.push({H,L,Q,before:consumer.before,after:consumer.after});
 }
 A.reset();A.mastery(1);const upgrading=A.rank(id,2);p.quantityPicks=p.quantityBonus=0;(p.statsTaken??={}).quantity=0;
 const rankBefore=T.windChainProfile(p,upgrading),upgrade=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);
 A.assert(upgrade?.desc.includes('風爆連切')&&upgrade.desc.includes(`${rankBefore.cuts}→${rankBefore.cuts+1}`),'rank card hides actual extra cut');
 A.assert(upgrade.apply(p)!==false&&T.windChainProfile(p,upgrading).cuts===rankBefore.cuts+1,'rank card preview is not consumed');
 A.reset();const heavy=A.rank(id,1);A.mastery(1);
 A.assert(heavy.damageIds?.includes(derived),'derived damage lost native learned-move credit');
 const enemy=A.spawn(100,0,'boss'),before=heavy.dealt||0;
 enemy.hurt(7,'#fff',0,0,0,null,p,derived);
 A.near((heavy.dealt||0)-before,7,'native heavy damage alias credit');
 A.assert(!G.Moves.poolFor(p.mon).includes(derived),'derived reaction entered learnable pool');
 A.assert(!p.moves.some(m=>m.id===derived),'derived reaction added a slot/move');
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
        page = browser.new_page()
        native.boot(page)
        result = page.evaluate(CHECK)
        native.URL = native.URL.replace('lang=zh-TW', 'lang=en')
        english = browser.new_page()
        native.boot(english)
        english.evaluate("""() => {
          const A=Acceptance,p=A.p();A.learn();A.mastery(1);const move=A.rank('naruto-temari-great-scythe',2);
          const benefit=G.JujutsuGrowth.quantityBenefit(p).consumers.find(c=>c.id===move.id);
          A.assert(benefit.before['Gust cuts']===G.NarutoTemari.windChainProfile(p,move).cuts,'English chain preview label');
          const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+move.id);
          A.assert(card.desc.includes('Gust cuts'),'English rank card hides chain growth');
        }""")
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'ok': True, 'cases': len(result), 'nativeDamageCredit': True, 'englishPreview': True}))


if __name__ == '__main__':
    main()
