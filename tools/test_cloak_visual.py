"""Exercise the reference-based red one-tail cloak in the actual animation lab."""
from pathlib import Path
import base64
import json
from playwright.sync_api import sync_playwright
from test_animation_complete import BASE, CHROME, start

OUT=Path(__file__).resolve().parents[1]/'.omx/state/cloak-reference'

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=CHROME,headless=True)
    page=browser.new_page(viewport={'width':1200,'height':900},service_workers='block')
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE)
    page.wait_for_function('GameplayLab.ready')
    if page.frame_locator('#game').locator('#tap-start').is_visible():
        page.frame_locator('#game').locator('#tap-start').click()
    frame=start(page,30001)
    frame.evaluate("Acceptance.cast('naruto-nine-tails-cloak');Acceptance.step(.8)")
    frame.evaluate(r'''() => {
      window.captureCloak=()=>{
        const p=G.Game.player,f=G.NarutoSupport.effects.find(e=>e.mode==='nine-tails-cloak');
        const c=document.createElement('canvas');c.width=240;c.height=220;
        const ctx=c.getContext('2d');ctx.translate(120-p.x,170-p.y);
        const before=ctx.getTransform();
        G.NarutoCloakVFX.draw(ctx,f,true);p.anim.draw(ctx,p.x,p.y);G.NarutoCloakVFX.draw(ctx,f,false);
        const after=ctx.getTransform();
        if(before.a!==after.a||before.e!==after.e||before.f!==after.f||ctx.globalAlpha!==1)throw Error('Cloak leaked canvas state');
        return {image:c.toDataURL(),pose:G.KyuubiForm.poseFor(p.anim),age:f.age};
      };
    }''')
    OUT.mkdir(parents=True,exist_ok=True)
    report=[]
    for direction,index in [('down',0),('right',2),('up',4),('left',6)]:
        for walking in [False,True]:
            frame.evaluate('(a)=>{const p=G.Game.player;p.anim.dir=a.dir;p.walking=a.walk;p.anim.base=a.walk?"Walk":"Idle"}',{'dir':index,'walk':walking})
            result=frame.evaluate('captureCloak()')
            assert result['pose']['key']=='naruto-one-tail',result
            (OUT/f'cloak-{direction}-{walking}.png').write_bytes(base64.b64decode(result.pop('image').split(',')[1]))
            report.append(result)
    first=frame.evaluate('captureCloak()');page.wait_for_timeout(120);second=frame.evaluate('captureCloak()')
    assert first==second,'Paused cloak animation changed'
    frame.evaluate("G.Game.player.walking=false;G.Game.player.anim.base='Idle';Acceptance.cast('naruto-naruto');Acceptance.step(.04)")
    result=frame.evaluate('captureCloak()')
    assert result['pose']['animation'].startswith('rasengan'),'Cloak covered active attack pose'
    (OUT/'cloak-rasengan.png').write_bytes(base64.b64decode(result.pop('image').split(',')[1]))
    frame.evaluate('G.Camera.x=G.Game.player.x;G.Camera.y=G.Game.player.y')
    page.screenshot(path=str(OUT/'cloak-gameplay.png'))
    assert not errors,errors
    browser.close()
    (OUT/'browser-check.json').write_text(json.dumps({'directions':report,'attack':result,'pause':'stable','errors':errors},indent=2),encoding='utf-8')
    print('PASS: four directions, crouch/walk, casting, pause and canvas state')
