"""Verify the charging walk cycle follows collision-resolved movement distance."""
import base64
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import HARNESS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/chidori-live'
URL = os.environ.get('CHIDORI_TEST_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=sasuke&layout=wide')

CHECK = r"""() => {
  const assert=(ok,msg)=>{if(!ok)throw Error(msg)},p=G.Game.player;
  const move=p.moves.find(m=>m.digiMode==='chidori-chain');
  const axis=G.Input.axis,spd=p.spdMul;
  function setup(multiplier){
    Acceptance.arena();p.spdMul=spd*multiplier;
    const normalSpeed=p.spd;
    Acceptance.enemy(0,85);assert(G.NarutoChidori.cast(p,move),'cast');
    assert(Math.abs(p.spd/normalSpeed-.8)<1e-6,'charge speed must be 80%');
  }
  function walk(dt,input=[0,1]){
    G.Input.axis=()=>input;Acceptance.resume();
    try{p.update(dt)}finally{Acceptance.pause();G.Input.axis=axis}
    return {distance:G.NarutoChidori.activeFor(p).chargeDistance,pose:G.AnimationLab.stateFor(p.anim)};
  }
  try{
    setup(1);let normal=walk(.2);
    assert(normal.distance>0&&normal.pose.key==='sasuke-chidori-charge-walk','moving pose');
    assert(normal.pose.frame===Math.floor(normal.distance/10)%4,'distance frame');
    const stopped=walk(.2,[0,0]);
    assert(stopped.distance===normal.distance&&stopped.pose.key==='sasuke-chidori-charge','stop');
    setup(.5);const slow=walk(.2);
    assert(Math.abs(slow.distance*2-normal.distance)<1e-6,'speed scales stride');
    const equal=walk(.2);
    assert(Math.abs(equal.distance-normal.distance)<1e-6&&equal.pose.frame===normal.pose.frame,'equal distance gives equal foot pose');
    const x=p.x,y=p.y,before=equal.distance;
    G.World.collide=owner=>{owner.x=x;owner.y=y};const blocked=walk(.2);
    assert(blocked.distance===before&&blocked.pose.key==='sasuke-chidori-charge','wall must not advance feet');
    setup(1);const parts=[];
    for(let i=0;i<4;i++)parts.push(walk(.05));
    assert(Math.abs(parts[3].distance-normal.distance)<1e-6&&parts[3].pose.frame===normal.pose.frame,'frame partition invariant');
    assert(move.charge===.3,'charge timing changed');
    Acceptance.step(.29);assert(G.NarutoChidori.active.phase==='charge','early dash');
    Acceptance.step(.011);assert(G.NarutoChidori.active.phase==='dash','late dash');
    setup(1);walk(.15);
    return {normal,slow,equal,blocked,partitioned:parts[3],chargeSeconds:move.charge};
  }finally{p.spdMul=spd;G.Input.axis=axis}
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
        page = browser.new_page(viewport={'width':1280,'height':900})
        errors=[]
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(URL)
        page.wait_for_function("window.PS_REDRAWN_READY&&document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.locator('[data-quick-naruto="30002"]').click()
        page.locator('#scr-menu [data-go="play"]').click()
        page.wait_for_function('G.Game.player?.dex===30002&&G.Game.state==="playing"')
        page.evaluate(HARNESS)
        report=page.evaluate(CHECK)
        render=page.evaluate('Acceptance.render()')
        (OUT/'distance-walk.png').write_bytes(base64.b64decode(render['png'].split(',')[1]))
        assert not errors,errors
        (OUT/'stride-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        browser.close()
    print('PASS: stride follows distance, scales with speed, stops at rest/walls; charge is 0.3s')


if __name__ == '__main__':
    main()
