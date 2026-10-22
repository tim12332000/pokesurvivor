"""Exercise repeatable health growth through the normal entry and level-up UI."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/max-health-percent'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=max-health-percent'

CHECK = r"""() => {
 const p=G.Game.player,out={},near=(a,b)=>{if(Math.abs(a-b)>1e-8)throw Error(a+' != '+b)};
 const def=G.LevelUp.STATS.find(s=>s.id==='maxHealthPercent'),flat=G.LevelUp.STATS.find(s=>s.id==='hp');
 if(!def||def.max||G.MaxHealthPercent.perPick!==.1)throw Error('missing repeatable stat');
 const save=JSON.stringify(G.DB.save);
 p.maxHp=260;p.hp=130;p.level=6;p.addMove('naruto-gates');
 if(G.NarutoGates.healingMultiplier(p)!==1.16)throw Error('Gates fixture missing');
 const slots=p.slots.length;
 const findCard=(offer,owner)=>{for(let i=0;i<100;i++){
   const cards=offer(owner,100),card=cards.find(c=>c.key==='stat:maxHealthPercent');if(card)return {card,cards};
 }throw Error('real candidate unavailable after 100 offers')};
 let card=findCard(G.LevelUp.offer,p).card;
 if(!card)throw Error('real candidate unavailable');
 card.apply(p);near(p.maxHp,292.6);near(p.hp,162.6);
 if(p.statsTaken.maxHealthPercent!==1||p.slots.length!==slots)throw Error('card accounting/slots');
 out.first={max:p.maxHp,hp:p.hp};
 card.apply(p);near(p.maxHp,321.86);near(p.hp,191.86);
 flat.apply(p);near(p.maxHp,341.86);near(p.hp,211.86);
 card.apply(p);near(p.maxHp,376.046);near(p.hp,246.046);
 out.mixed={max:p.maxHp,hp:p.hp,count:p.statsTaken.maxHealthPercent};
 p.hp=p.maxHp;card.apply(p);near(p.hp,p.maxHp);
 p.regenFlat=0;
 const all=G.DEX.filter(mon=>mon.hp>0&&Number.isFinite(mon.hp));
 for(const mon of all){const actor=new G.Player(mon);actor.maxHp=260;actor.hp=130;
   def.apply(actor);near(actor.maxHp,286);near(actor.hp,156);
   if(actor.hp>actor.maxHp||actor.hp<=0)throw Error('invalid health '+mon.dex);
 }
 out.rosterCount=all.length;
 const row=G.RunAttributes.rows(p).find(r=>r.id==='maxHealthPercent');
 if(row?.text!=='生命成長 +10% ×4')throw Error('bad row '+JSON.stringify(row));
 if(JSON.stringify(G.DB.save)!==save)throw Error('stat persisted outside run');
 out.row=row.text;
 p.maxHp=260;p.hp=130;p.statsTaken={};p.level=5;p.invuln=999;
 G.EnemyMgr.clear();G.Projectiles.clear();G.NarutoLee.clear();
 const offer=G.LevelUp.offer;
 G.LevelUp.offer=(owner,n=3)=>{const {card:c,cards}=findCard(offer,owner),apply=c.apply;
   c.apply=actor=>{const result=apply(actor);window.HealthGrowthChoice={max:actor.maxHp,hp:actor.hp,count:actor.statsTaken.maxHealthPercent};return result};
   return [c,...cards.filter(x=>x!==c)].slice(0,n)};
 window.HealthGrowthOffer=offer;
 G.Game.debugLevelUp();G.Game.togglePause();
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'viewports': {}, 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in (False, True):
            label = 'mobile' if mobile else 'desktop'
            context = browser.new_context(locale='zh-TW', service_workers='block',
                viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900},
                is_mobile=mobile, has_touch=mobile)
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(URL)
            page.wait_for_function("window.G?.MaxHealthPercent && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30006"]').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
            page.evaluate('G.Game.togglePause();G.UI.hide("scr-pause")')
            result = page.evaluate(CHECK)
            page.wait_for_selector('#scr-levelup:not(.hidden) #cards .card')
            page.evaluate('() => {G.LevelUp.offer=HealthGrowthOffer}')
            page.evaluate('G.Game.player.maxHp=260;G.Game.player.hp=130')
            assert '生命成長 +10%' in page.locator('#cards .card').first.inner_text()
            page.wait_for_function("""() => {
              const card=document.querySelector('#scr-levelup:not(.hidden) #cards .card');
              if(!card)return false;
              const style=getComputedStyle(card);
              return Number(style.opacity)>.99&&!card.getAnimations().some(a=>a.playState==='running');
            }""")
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUT / f'{label}-choice.png'))
            page.locator('#cards .card').first.click()
            result['ui'] = page.evaluate("""() => {
              const p=G.Game.player,result=HealthGrowthChoice;
              if(Math.abs(result.max-286)>1e-8||Math.abs(result.hp-156)>1e-8||result.count!==1)throw Error('actual choice delta '+JSON.stringify(result));
              if(G.Game.state==='playing')G.Game.togglePause();G.UI.hide('scr-pause');
              return {...result,row:G.RunAttributes.rows(p).find(r=>r.id==='maxHealthPercent').text};
            }""")
            page.screenshot(path=str(OUT / f'{label}-row.png'))
            result['reset'] = page.evaluate("""() => {
              const old=G.Game.player;G.Game.toUI();G.Flow.play();G.Game.togglePause();G.UI.hide('scr-pause');
              const p=G.Game.player;
              if(p===old||p.statsTaken.maxHealthPercent||G.RunAttributes.rows(p).some(r=>r.id==='maxHealthPercent'))throw Error('new run leaked growth');
              return {max:p.maxHp,hp:p.hp};
            }""")
            report['viewports'][label] = result
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
