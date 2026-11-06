"""Compare Temari quantity card previews with the real fan capability profile."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_temari as native

OUT = Path(__file__).resolve().parents[1] / '.omx/state/temari-complete/growth'
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,id='naruto-temari-great-scythe',out=[];
 A.learn();A.mastery(1);
 for(const rank of [1,3,5])for(const Q of [0,1,3,19]){
   A.reset();A.mastery(1);const move=A.rank(id,rank);p.quantityPicks=p.quantityBonus=Q;
   const before=T.heavyFor(p,move),benefit=G.JujutsuGrowth.quantityBenefit(p);
   const consumer=benefit.consumers.find(c=>c.id===id);
   A.assert(consumer,'heavy missing from real quantity preview');
   A.near(consumer.before['扇角'],Math.round(before.arc*180/Math.PI),'preview actual fan angle');
   A.near(consumer.before['射程'],before.range,'preview actual range');
   A.near(consumer.before['推退'],before.pushDistance,'preview actual push');
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');
   A.assert(card&&card.apply(p)!==false,'real quantity card unavailable');
   const after=T.heavyFor(p,move);
   A.near(consumer.after['扇角'],Math.round(after.arc*180/Math.PI),'next card fan angle');
   A.near(consumer.after['射程'],after.range,'next card range');
   A.near(consumer.after['推退'],after.pushDistance,'next card push');
   A.assert(after.arc>=before.arc&&after.arc<=Math.PI,'fan cap or regression');
   out.push({rank,Q,before:consumer.before,after:consumer.after});
 }
 p.quantityPicks=p.quantityBonus=20;
 A.assert(!G.JujutsuGrowth.quantityBenefit(p).eligible,'max quantity card still offered');
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
        page = browser.new_page()
        native.boot(page)
        result = page.evaluate(CHECK)
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'ok': True, 'cases': len(result), 'report': str(OUT / 'report.json')}))


if __name__ == '__main__':
    main()
