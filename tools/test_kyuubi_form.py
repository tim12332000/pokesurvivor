"""Real one-tail artwork acceptance. Run against the animation-lab server."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import BASE, CHROME, HARNESS, start, wait_ready

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / '.omx/state/kyuubi-form'

FORM_HARNESS = r"""() => {
  const A=Acceptance;
  A.formRender=()=>{
    const canvas=document.createElement('canvas');canvas.width=640;canvas.height=480;
    const ctx=canvas.getContext('2d',{willReadFrequently:true}),calls=[];
    const draw=ctx.drawImage.bind(ctx);
    ctx.drawImage=(img,...args)=>{calls.push({src:img.src||img.dataset?.source||'',formSource:img===G.KyuubiForm.image,args});return draw(img,...args)};
    const pose=G.KyuubiForm.poseFor(A.p().anim);
    A.p().anim.draw(ctx,320,390,{});
    const data=ctx.getImageData(0,0,640,480).data;
    let pixels=0,x0=640,y0=480,x1=-1,y1=-1;
    for(let y=0;y<480;y++)for(let x=0;x<640;x++)if(data[(y*640+x)*4+3]>20){
      pixels++;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);
    }
    A.assert(pixels>80,'empty actual form render');
    A.assert(x0>0&&x1<639&&y0>0&&y1<479,'form clipped');
    return {pose,calls,pixels,bounds:[x0,y0,x1,y1],png:canvas.toDataURL()};
  };
  A.activate=()=>{A.arena();const cast=A.cast('naruto-nine-tails-cloak');A.step(.6);
    A.assert(G.KyuubiForm.active(A.p()),'actual auto cast did not activate transformed form');return cast};
}"""


def save(name, result):
    (OUT / f'{name}.png').write_bytes(base64.b64decode(result.pop('png').split(',', 1)[1]))
    if result.get('pose'):
        assert result['pose']['key'] == 'naruto-one-tail', result
        assert any(c['formSource'] for c in result['calls']), result
        assert all(c['formSource'] for c in result['calls']), result
    return result


def observe(page, report):
    page.on('pageerror', lambda e: report['errors'].append(e.stack or str(e)))
    page.on('response', lambda r: report['failedRequests'].append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
    page.on('requestfailed', lambda r: report['failedRequests'].append({'url': r.url, 'failure': r.failure}))
    page.on('console', lambda m: report['consoleErrors'].append(m.text) if m.type == 'error' else None)


def ready(page, report):
    try:
        wait_ready(page, report)
    except Exception:
        report['bootFailure'] = page.evaluate('''() => {const f=document.querySelector('#game'),G=f.contentWindow.G;
          return {status:document.querySelector('#status').textContent,modules:Object.fromEntries(
            ['Naruto','DigimonSkills','NarutoSkillCatalog','Touch','AnimationLab','KyuubiForm','DB'].map(k=>[k,!!G?.[k]])),
            scripts:[...f.contentDocument.scripts].filter(s=>s.src).map(s=>s.src)}}''')
        (OUT / 'boot-failure.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=True))
        raise


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'failedRequests': [], 'consoleErrors': [], 'poses': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(viewport={'width': 1200, 'height': 900})
        observe(page, report)
        page.goto(BASE)
        ready(page, report)
        boot = page.frame_locator('#game').locator('#tap-start')
        if boot.is_visible():
            boot.click()
        frame = start(page, 30001)
        frame.wait_for_function('!!G.KyuubiForm')
        frame.evaluate(FORM_HARNESS)
        report['cast'] = frame.evaluate('Acceptance.activate()')
        report['poses']['idle'] = save('idle', frame.evaluate('Acceptance.formRender()'))
        idle_frames = frame.evaluate('''() => {const A=Acceptance,frames=[];
          for(let i=0;i<10;i++){A.step(.1);frames.push(G.KyuubiForm.poseFor(A.p().anim))}return frames}''')
        assert len({p['frame'] for p in idle_frames}) > 1, idle_frames
        report['idleFrames'] = idle_frames
        for key, direction in [('KeyD', 'right'), ('KeyA', 'left'), ('KeyW', 'up'), ('KeyS', 'down')]:
            page.locator('#game').focus()
            page.keyboard.down(key)
            result = frame.evaluate('''() => {const A=Acceptance,p=A.p(),x=p.x,y=p.y;
              A.resume();p.update(.08);A.pause();A.assert(p.walking&&Math.hypot(p.x-x,p.y-y)>0,'real movement missing');
              return A.formRender()}''')
            frames = frame.evaluate('''() => {const A=Acceptance,frames=[];for(let i=0;i<8;i++){
              A.resume();A.p().update(.08);A.pause();frames.push(G.KyuubiForm.poseFor(A.p().anim))}return frames}''')
            page.keyboard.up(key)
            assert len({p['frame'] for p in frames}) > 1, frames
            report['poses'][direction] = save(direction, result)
        report['pause'] = frame.evaluate('''() => {const A=Acceptance;A.pause();const before=G.KyuubiForm.poseFor(A.p().anim);
          A.p().anim.update(.8);return {before,after:G.KyuubiForm.poseFor(A.p().anim)}}''')
        assert report['pause']['before'] == report['pause']['after'], report['pause']
        report['poses']['hurt'] = save('hurt', frame.evaluate('''() => {const A=Acceptance,p=A.p();
          p.invuln=0;A.resume();p.hurt(11,null,true);A.pause();return A.formRender()}'''))
        assert 'hurt' in report['poses']['hurt']['pose']['animation'].lower(), report['poses']['hurt']
        for skill in ['naruto-naruto', 'naruto-kunai', 'naruto-rasenshuriken']:
            frame.evaluate('Acceptance.activate()')
            cast = frame.evaluate('(id)=>Acceptance.cast(id)', skill)
            phases = []
            for index in range(7):
                if index:
                    frame.evaluate('Acceptance.step(.06)')
                phases.append(save(f'{skill}-{index}', frame.evaluate('Acceptance.formRender()')))
            assert any('idle' not in p['pose']['animation'].lower() and 'run' not in p['pose']['animation'].lower() for p in phases), phases
            report[skill] = {'cast': cast, 'phases': phases}
        report['noExtraCloak'] = frame.evaluate('''() => {const A=Acceptance,canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');
          const f=G.NarutoSupport.effects.find(f=>f.owner===A.p()&&f.mode==='nine-tails-cloak');
          A.assert(f,'cloak effect missing');let calls=0;
          for(const name of ['fill','stroke','drawImage','fillRect']){const original=ctx[name].bind(ctx);ctx[name]=(...args)=>{calls++;return original(...args)}}
          G.NarutoCloakVFX.draw(ctx,f,100);A.assert(calls===0,'extra procedural cloak drawn over baked sprite');return true}''')
        page.screenshot(path=str(OUT / 'actual-gameplay.png'))
        page.locator('#candidate').uncheck()
        report['disabled'] = frame.evaluate('''() => {Acceptance.assert(!G.KyuubiForm.poseFor(Acceptance.p().anim),
          'disabled experiment retained transformed rendering');return true}''')
        page.locator('#candidate').check()
        assert frame.evaluate('!!G.KyuubiForm.poseFor(Acceptance.p().anim)'), 're-enabled experiment lost live buff'
        report['expiry'] = frame.evaluate('''() => {const A=Acceptance;A.activate();A.step(13);
          A.assert(!G.KyuubiForm.active(A.p()),'form survived expiry');A.assert(!G.KyuubiForm.poseFor(A.p().anim),'form pose survived expiry');
          return {active:false,regular:A.render().state}}''')
        report['cancel'] = frame.evaluate('''() => {const A=Acceptance;A.activate();G.Combat.clearFields();
          A.assert(!G.KyuubiForm.active(A.p()),'form survived clear');return true}''')
        report['death'] = frame.evaluate('''() => {const A=Acceptance;A.activate();const p=A.p();
          A.resume();p.invuln=0;p.hurt(p.maxHp*100,null,true);A.pause();
          A.assert(p.dead||p.hp<=0,'actual lethal damage did not kill');A.assert(!G.KyuubiForm.active(p),'dead owner retained form');return true}''')
        # Starting the other actual hero exercises owner/scene replacement.
        frame = start(page, 30002)
        report['scene'] = frame.evaluate('''() => {Acceptance.assert(!G.KyuubiForm.active(G.Game.player),'Sasuke inherited form');
          Acceptance.assert(!G.KyuubiForm.poseFor(G.Game.player.anim),'Sasuke inherited pose');return true}''')
        mobile = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True,
                                     has_touch=True, service_workers='block')
        phone = mobile.new_page()
        observe(phone, report)
        phone.goto(BASE)
        ready(phone, report)
        boot = phone.frame_locator('#game').locator('#tap-start')
        if boot.is_visible():
            boot.tap()
        frame = start(phone, 30001)
        frame.evaluate(FORM_HARNESS)
        mobile_report = report['mobile'] = {'cast': frame.evaluate('Acceptance.activate()')}
        # Begin between the real cloak's periodic attack pulses to observe run.
        frame.evaluate('Acceptance.step(.1);Acceptance.step(.1);Acceptance.step(.1)')
        bounds = phone.locator('#game').bounding_box()
        assert bounds['x'] >= 0 and bounds['x'] + bounds['width'] <= 390.5, bounds
        assert bounds['y'] >= 0 and bounds['y'] + bounds['height'] <= 844.5, bounds
        mobile_report['viewportBounds'] = bounds
        mobile_report['idle'] = save('mobile-idle', frame.evaluate('Acceptance.formRender()'))
        initial = frame.evaluate('({x:Acceptance.p().x,y:Acceptance.p().y})')
        frame.evaluate('Acceptance.p().invuln=99999;Acceptance.resume()')
        cdp = mobile.new_cdp_session(phone)
        x, y = bounds['x'] + 85, bounds['y'] + bounds['height'] * .6
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x+48, 'y': y}]})
        phone.wait_for_timeout(160)
        moved = frame.evaluate('''() => {Acceptance.pause();const p=Acceptance.p();
          return {x:p.x,y:p.y,walking:p.walking,pose:G.KyuubiForm.poseFor(p.anim)}}''')
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        assert moved['walking'] and moved['x'] > initial['x'], (initial, moved)
        assert moved['pose']['animation'] == 'run', moved
        mobile_report['touch'] = {'before': initial, 'after': moved}
        mobile_report['run'] = save('mobile-run', frame.evaluate('Acceptance.formRender()'))
        phone.screenshot(path=str(OUT / 'mobile-one-tail.png'))
        mobile_report['expiry'] = frame.evaluate('''() => {const A=Acceptance;A.step(13);
          A.assert(!G.KyuubiForm.active(A.p()),'mobile form survived expiry');
          A.assert(!G.KyuubiForm.poseFor(A.p().anim),'mobile form pose survived expiry');return true}''')
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        assert not report['errors'], report['errors']
        assert not report['failedRequests'], report['failedRequests']
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'passed': True, 'poses': len(report['poses']), 'errors': report['errors'], 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
