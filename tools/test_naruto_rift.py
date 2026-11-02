"""Exercise portal contact, arena travel and return with the Naruto-only picker."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME

URL = os.environ.get('NARUTO_RIFT_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW')
OUT = Path(__file__).resolve().parents[1] / '.omx/state/naruto-rift'

CHECK = '''() => {
  const assert=(ok,message)=>{if(!ok)throw Error(message)},p=G.Game.player;
  assert(p.dex===30001,'fixture must use Naruto');
  assert(G.DEX.every(mon=>mon.naruto),'picker must remain Naruto-only');
  G.Game.togglePause();G.UI.hide('scr-pause');
  const back={x:p.x,y:p.y,hp:p.hp},clone=G.SelfClones.summon(p),cloneHp=clone.hp;
  const enter=()=>{
    G.Rift.onEvent(['rift',p.x,p.y+10,45]);
    G.Rift.update(.01,p,G.Game.st.time);
    assert(G.Rift.inArena,'touching the portal did not enter');
    const arena=G.Rift.arena,boss=G.EnemyMgr.get(arena.bossId);
    assert(G.DEX_BY[arena.dex]?.leg && boss?.legend,'legendary opponent missing');
    assert(Math.hypot(p.x-arena.x,p.y-arena.y)<500,'player was not transported');
    assert(G.SelfClones.actors().includes(clone) && clone.hp===cloneHp,'permanent clone lost on travel');
    return boss;
  };
  const first=enter();
  G.Rift.onEvent(['al']);G.Rift.update(1.3,p,G.Game.st.time);
  assert(!G.Rift.inArena && p.x===back.x && p.y===back.y,'loss did not return to original map');
  assert(p.hp===back.hp && G.SelfClones.actors().includes(clone),'return changed living player or clone');
  const bonds=p.bonds,second=enter();
  // Native arena tick resolves the defeated opponent and its reward.
  second.hurt(second.hp*100,p);
  assert(second.dead,'legendary damage fixture did not defeat opponent');
  G.Rift.update(.01,p,G.Game.st.time);
  assert(G.Rift.arena.phase==='won' && p.bonds===bonds+1,'victory did not award bond');
  G.Rift.update(5.1,p,G.Game.st.time);
  assert(!G.Rift.inArena && p.x===back.x && p.y===back.y,'victory did not return to original map');
  assert(G.SelfClones.actors().includes(clone),'victory return lost permanent clone');
  // These progression systems must also use the complete encounter catalog.
  G.Events.reset();G.Events.debugStart('lost');
  assert(G.Events.current==='lost','lost-Pokemon event could not select a target');
  G.Events.reset();G.Judgment.debugStart();
  assert(G.Judgment.cinematic,'judgment could not select its legendary queue');
  return {dex:p.dex,firstLegend:first.dex,secondLegend:second.dex,lossReturn:true,victoryReturn:true,
    bondAwarded:true,clonePreserved:true,lostEvent:true,judgment:true};
}'''


if __name__ == '__main__':
    report = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in (False, True):
            context = browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},
                                          is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(URL + ('' if mobile else '&layout=wide'))
            page.wait_for_function("window.G?.NarutoAssets && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function("G.Game.state==='playing' && G.Game.player?.dex===30001", timeout=60000)
            result = page.evaluate(CHECK)
            assert not errors, errors
            report['mobile' if mobile else 'desktop'] = result
            print(json.dumps(result), flush=True)
            context.close()
        browser.close()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Naruto portal entry, loss/win return, clone continuity and progression passed on desktop/mobile.')
