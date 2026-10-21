"""Pause summary acceptance against real combat and the shipped sandbox entry."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/pause-summary'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=pause-summary'

CHECK = r"""() => {
 const A=Acceptance,p=A.p();A.arena();
 p.percentHealthDamage=0;p.lifestealRate=0;p.critChance=0;
 window.summaryClock=20;window.nativeTime=Object.getOwnPropertyDescriptor(G.Game.st,'time');
 Object.defineProperty(G.Game.st,'time',{configurable:true,get:()=>summaryClock});p.maxMoves=20;
 const m=p.moves[0];m.since=0;
 // Real projectile cast; changing the selected slot must not redirect its damage.
 const e=A.enemy(0,70);e.types=['normal'];e.shield=50;
 A.cast(m.id);
 p.addMove('naruto-sand-shield');const shield=p.moves.find(m=>m.id==='naruto-sand-shield');
 p.addMove('naruto-sand-coffin');const selected=p.moves.find(m=>m.id==='naruto-sand-coffin');
 const before=m.dealt;A.select(selected.id);
 for(let i=0;i<40&&!m.dealt;i++)A.step(.02);
 A.assert(m.dealt>before,'delayed projectile did not credit original move');
 A.assert(!selected.dealt,'projectile damage credited selected move');
 A.assert(shield.passive&&!p.slots.some(group=>group.includes(shield)),'shield must remain a learned passive');
 const afterProjectile=m.dealt;
 // Shared native hit path must include the flat max-HP proc exactly once.
 p.percentHealthDamage=.01;
 const old=m.dealt;e.hurt(10,'#fff',0,0,0,null,p,m.id);
 A.assert(m.dealt-old===1010,'percent-health proc was lost or counted twice');
 const expected=m.dealt;
 e.dead=true;e.hurt(90,'#fff',0,0,0,null,p,m.id);
 A.assert(m.dealt===expected,'dead enemy counted damage');e.dead=false;
 // Source snapshots retain credit after upgrade/fusion; unowned damage stays out.
 G.Moves.levelUp(m);const snapshot={...m};
 p.percentHealthDamage=0;e.hurt(20,'#fff',0,0,0,null,p,snapshot.id);
 e.hurt(5);A.assert(m.dealt===expected+20,'snapshot/unowned attribution failed');
 // A freshly learned move starts its own DPS denominator.
 p.addMove('tackle');const late=p.moves.find(m=>m.id==='tackle');
 A.assert(late.since===G.Game.st.time,'learn time missing '+late.since+' / '+G.Game.st.time);
 summaryClock=25;e.hurt(50,'#fff',0,0,0,null,p,late.id);
 // Include custom card effects and make the summary long enough to scroll.
 p.statsTaken={hp:2,atk:3,quantity:2,lifesteal:1,percentHealthDamage:1};
 p.quantityBonus=2;p.lifestealRate=.03;p.percentHealthDamage=.01;p.item='leftovers';
 G.RunUI.showPause();
 const row=document.querySelector(`[data-move-id="${m.id}"]`);
 const shieldRow=document.querySelector(`[data-move-id="${shield.id}"]`);
 A.assert(shieldRow&&Number(shieldRow.querySelector('[data-damage]').dataset.damage)===(shield.dealt||0),'passive shield summary missing or misattributed');
 A.assert(Number(row.querySelector('[data-damage]').dataset.damage)===m.dealt,'summary damage mismatch');
 A.assert(Number(row.querySelector('[data-dps]').dataset.dps)===m.dealt/25,'DPS must use simulation time');
 A.assert(document.querySelector('[data-move-id="tackle"] [data-dps]').dataset.dps==='10','late learned DPS wrong');
 const text=document.querySelector('#pause-sum').textContent;
 for(const label of ['招式傷害','目前屬性','攜帶道具與升級卡','吸血','生命剝奪'])A.assert(text.includes(label),'translation missing '+label);
 A.assert(!/NaN|Infinity|undefined/.test(text),'invalid summary numbers');
 window.summaryTime=G.Game.st.time;window.summaryHTML=document.querySelector('#pause-sum').innerHTML;
 return {projectileDamage:afterProjectile,damage:m.dealt,dps:m.dealt/25,lateMoveDps:10};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in (False, True):
                label = 'mobile' if mobile else 'desktop'
                context = browser.new_context(locale='zh-TW', viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900}, is_mobile=mobile, has_touch=mobile)
                page = context.new_page()
                page.on('pageerror', lambda err: report['errors'].append(str(err)))
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.querySelector('#boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                page.evaluate(HARNESS)
                report['viewports'][label] = page.evaluate(CHECK)
                page.wait_for_function('!document.querySelector("#ach-pop:not(.hidden)")', timeout=20000)
                page.wait_for_timeout(300)
                assert page.evaluate('G.Game.st.time===summaryTime'), 'pause advanced simulation'
                page.evaluate('G.RunUI.showPause()')
                assert page.evaluate('document.querySelector("#pause-sum").innerHTML===summaryHTML'), 'pause changed DPS'
                # Restore the native clock, then verify the actual game loop is paused.
                page.evaluate('Object.defineProperty(G.Game.st,"time",nativeTime);window.pausedNativeTime=G.Game.st.time')
                page.wait_for_timeout(250)
                assert page.evaluate('G.Game.st.time===pausedNativeTime'), 'native simulation advanced during pause'
                assert page.evaluate('''() => {
                  const box=document.querySelector('.pause-box').getBoundingClientRect();
                  const body=document.querySelector('#pause-sum');
                  return box.top>=0&&box.bottom<=innerHeight&&body.scrollWidth<=body.clientWidth+1;
                }'''), 'summary overflow'
                page.screenshot(path=str(OUT/f'{label}.png'), style='#ach-pop { visibility: hidden !important; }')
                page.locator('#pause-sum').evaluate('(el)=>el.scrollTop=el.scrollHeight')
                page.screenshot(path=str(OUT/f'{label}-stats.png'), style='#ach-pop { visibility: hidden !important; }')
                page.locator('#btn-resume').click()
                page.wait_for_function('G.Game.state==="playing" && !G.UI.isOpen("scr-pause")')
                page.evaluate('Object.defineProperty(G.Game.st,"time",nativeTime);G.Game.startRun();G.Game.togglePause()')
                assert page.evaluate('G.Game.player.moves.every(m=>m.dealt===0 && m.since===0)'), 'run did not reset summary'
                report['viewports'][label]['digimonEvolution'] = page.evaluate('''() => {
                  const actor=new G.Player(G.DEX_BY[20001]);actor.addMove(actor.mon.start);
                  const m=actor.moves[0],old=m.id;m.dealt=123;m.since=0;
                  if(!G.Digimon.evolve(actor,true))throw Error('evolution fixture rejected');
                  if(actor.moves[0]!==m||m.dealt!==123||m.since!==0)throw Error('evolution lost damage history');
                  const e=new G.Enemy({dex:19,hp:10000,spd:0,dmg:0,xp:0,behavior:'chase'},0,0,{hp:1,spd:1,dmg:1});
                  e.hurt(20,'#fff',0,0,0,null,actor,old);
                  if(m.dealt!==143)throw Error('pre-evolution projectile lost credit');
                  return {from:old,to:m.id,damage:m.dealt};
                }''')
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
