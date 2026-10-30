"""Click native level-up cards and capture the packaged game's real renderer."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

OUT = Path(__file__).resolve().parents[1] / '.omx/state/lee-gates-live'
URL = 'http://127.0.0.1:8004/dist-digimon/.omx/digimon.html?lang=zh-TW&hero=lee&layout=wide'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in (False, True):
            label = 'mobile' if mobile else 'desktop'
            ctx = browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = ctx.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY&&G.NarutoGates&&document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30006"]').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
            page.evaluate(HARNESS)
            page.evaluate(SETUP)
            result = []
            for level in (1, 5):
                page.evaluate(r"""level => {
                  const A=Acceptance,p=A.p();A.leeArena();p.level=6;p.invuln=0;
                  if(level===5)p.moves.find(m=>m.id==='naruto-gates').lvl=4;
                  const key=(level===1?'new:':'up:')+'naruto-gates',offer=G.LevelUp.offer;
                  A.restoreOffer=()=>{G.LevelUp.offer=offer};
                  G.LevelUp.offer=(p)=>offer(p,100).filter(c=>c.key===key);
                  p.xpMul=0;A.resume();G.Game.debugLevelUp();
                  A.position=[p.x,p.y];
                }""", level)
                page.locator('#scr-levelup #cards .card').first.wait_for(state='visible')
                page.evaluate(r"""() => {
                  const stream=document.getElementById('game').captureStream(30),chunks=[];
                  Acceptance.recorder=new MediaRecorder(stream,{mimeType:'video/webm'});
                  Acceptance.recorded=new Promise(resolve=>{
                    Acceptance.recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
                    Acceptance.recorder.onstop=()=>{stream.getTracks().forEach(track=>track.stop());
                      const reader=new FileReader();reader.onload=()=>resolve(reader.result);
                      reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}));};
                  });
                  Acceptance.recorder.start();
                }""")
                page.locator('#scr-levelup #cards .card').first.click()
                page.evaluate('Acceptance.restoreOffer()')
                page.keyboard.down('KeyD')
                page.wait_for_function('G.NarutoGates.openingFor(G.Game.player)?.age>=2.2')
                charge = page.evaluate(r"""() => {
                  const p=G.Game.player,g=G.NarutoGates,f=g.openingFor(p);
                  Acceptance.assert(f.age<4&&g.charging(p),'native charge missing');
                  Acceptance.assert(p.x===Acceptance.position[0]&&p.y===Acceptance.position[1],'native charge allowed movement');
                  const pose=G.AnimationLab.stateFor(p.anim);
                  Acceptance.assert(pose.id==='naruto-gates'&&pose.key==='lee-opened-gates'&&pose.frame===1,'native charging pose mismatch');
                  return {stage:g.stage(p),age:f.age,color:g.config.trails[g.stage(p)-1].color};
                }""")
                page.screenshot(path=str(OUT / f'{label}-stage{level}-charge.png'))
                page.wait_for_function('G.NarutoGates.openingFor(G.Game.player)?.age>=3.4')
                page.evaluate("Acceptance.assert(G.AnimationLab.stateFor(G.Game.player.anim).phase==='intensify','native power peak pose mismatch')")
                page.screenshot(path=str(OUT / f'{label}-stage{level}-peak.png'))
                page.wait_for_function('G.NarutoGates.openingFor(G.Game.player)?.released')
                page.evaluate("Acceptance.assert(G.AnimationLab.stateFor(G.Game.player.anim).frame===2,'native explosion pose mismatch')")
                page.screenshot(path=str(OUT / f'{label}-stage{level}-burst.png'))
                page.wait_for_function('G.NarutoGates.openingFor(G.Game.player)?.age>=4.65')
                page.evaluate("Acceptance.assert(G.AnimationLab.stateFor(G.Game.player.anim).frame===3,'native recovery pose mismatch')")
                page.screenshot(path=str(OUT / f'{label}-stage{level}-recovery.png'))
                page.wait_for_function('!G.NarutoGates.openingFor(G.Game.player)')
                recording = page.evaluate('() => {Acceptance.recorder.stop();return Acceptance.recorded}')
                (OUT / f'{label}-stage{level}-opening.webm').write_bytes(base64.b64decode(recording.split(',')[1]))
                page.keyboard.up('KeyD')
                status = page.evaluate('G.NarutoGates.status(G.Game.player)')
                assert status['active'] and 9 < status['activeRemaining'] <= 10, status
                page.evaluate('Acceptance.advance(10.1)')
                status = page.evaluate('G.NarutoGates.status(G.Game.player)')
                assert not status['active'] and 0 < status['cooldownRemaining'] <= 15, status
                page.screenshot(path=str(OUT / f'{label}-stage{level}-cooldown.png'))
                charge['cooldownState'] = status
                result.append(charge)
                page.evaluate('Acceptance.pause()')
            report['viewports'][label] = result
            ctx.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), 'utf-8')
    previews = ''.join(f'<figure><figcaption>{label} / {stage}</figcaption><video controls loop playsinline preload="metadata" src="{label}-stage{stage}-opening.webm"></video></figure>'
                       for label in ('desktop', 'mobile') for stage in (1, 5))
    (OUT / 'index.html').write_text('<!doctype html><html lang="zh-TW"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>小李八門實機演出</title><style>body{background:#111a17;color:#e7f9ee;font:16px system-ui;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}figure{margin:0}video{width:100%;max-height:75vh;background:#000}figcaption{margin:12px 0}</style>'
        '<h1>小李八門實機演出</h1><p>實際點選卡片後錄製：蓄力 4 秒、爆發與收勢 1 秒；演出期間僅補回實際受傷扣血，結束後冷卻 25 秒，總週期 30 秒。第一階藍光、最高階紅光。</p><main>' + previews + '</main></html>', 'utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))

if __name__ == '__main__':
    main()
