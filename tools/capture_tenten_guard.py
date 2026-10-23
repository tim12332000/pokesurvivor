"""Record actual guard gameplay frames and a desktop/mobile review page."""
import json
import os
from pathlib import Path
import subprocess

from playwright.sync_api import sync_playwright
from test_tenten_guard import CHROME, HARNESS, SETUP, AUDIT, SETUP_GUARD, PROGRESSION, URL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/tenten-guard'

PREPARE = r"""() => {
 const A=Acceptance,p=A.p();A.guardReset();p.aim=0;p.anim.dir=2;
 for(const [x,y] of [[60,0],[-45,40],[-30,-55],[180,70]])A.spawn(x,y);
 A.guardStep(.001);A.assert(A.guard()?.phase==='prepare','guard did not begin');
 G.UI.hide('ach-pop');document.querySelectorAll('.toast').forEach(el=>el.style.display='none');
 A.demoStep=()=>{A.resume();try{for(let i=0;i<5;i++){
   p.update(.01);G.Combat.updateFields(.01);G.Projectiles.update(.01,p,G.EnemyMgr.all());
   G.Combat.resolve(.01,p,0);
 }}finally{A.pause()}};
 return {moves:p.moves.map(m=>m.id),startX:p.x};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    ffmpeg = Path(os.environ.get('LOCALAPPDATA', '')) / 'ms-playwright/ffmpeg-1011/ffmpeg-win64.exe'
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, size, mobile in [('desktop', {'width': 1200, 'height': 900}, False),
                                    ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=size, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30009"]').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30009 && G.Game.state==="playing"')
            for setup in [HARNESS, SETUP, AUDIT, SETUP_GUARD, PROGRESSION]:
                page.evaluate(setup)
            result = report['viewports'][label] = page.evaluate(PREPARE)
            assert len(result['moves']) == 7, result['moves']
            frames, states, captured = [], [], set()
            try:
                for frame in range(34):
                    if frame == 10:
                        page.keyboard.down('KeyD')
                    if frame:
                        page.evaluate('Acceptance.demoStep()')
                    state = page.evaluate('''() => {const p=Acceptance.p(),g=Acceptance.guard();return {
                      phase:g.phase,age:g.age,boost:g.boostRemaining,x:p.x,walking:p.walking,
                      pose:G.AnimationLab.stateFor(p.anim).key,tools:g.tools}}''')
                    states.append(state)
                    # Native render loop paints the paused simulation's current state.
                    page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                    page.evaluate("document.querySelectorAll('#ach-pop,.toast').forEach(el=>el.style.setProperty('display','none','important'))")
                    frames.append(page.screenshot(type='jpeg', quality=92))
                    phase = state['phase']
                    if phase in {'prepare', 'sweep', 'escape'} and phase not in captured and (phase != 'sweep' or state['age'] >= .25):
                        page.screenshot(path=str(OUT / f'{label}-demo-{phase}.png'))
                        captured.add(phase)
            finally:
                page.keyboard.up('KeyD')
            assert captured == {'prepare', 'sweep', 'escape'}, captured
            assert all(s['tools'] == 8 for s in states), states
            assert states[-1]['x'] > states[10]['x'] and any(s['walking'] and s['boost'] > 0 for s in states), states
            assert states[0]['pose'] == 'tenten-mastery', states[0]
            result.update(frames=states, fps=20, duration=len(frames)/20, captured=sorted(captured))
            context.close()
            subprocess.run([str(ffmpeg), '-y', '-f', 'image2pipe', '-framerate', '20', '-c:v', 'mjpeg',
                            '-i', 'pipe:0', '-c:v', 'libvpx', '-b:v', '1800k', str(OUT / f'{label}-demo.webm')],
                           check=True, input=b''.join(frames), capture_output=True)
            print(label, 'guard gameplay video captured', flush=True)
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'capture-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    sections = []
    for label, title in [('desktop', '桌面'), ('mobile', '手機')]:
        shots = ''.join(f'<figure><img src="{label}-demo-{phase}.png" alt="{title} {caption}"><figcaption>{caption}</figcaption></figure>'
                        for phase, caption in [('prepare', '展卷準備'), ('sweep', '八枚忍具護身'), ('escape', '加速撤退')])
        sections.append(f'<section><h2>{title}</h2><video controls loop muted playsinline src="{label}-demo.webm"></video><div class="shots">{shots}</div></section>')
    html = '''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>天天・操具護身陣演出預覽</title><style>body{margin:24px auto;padding:0 20px;max-width:1280px;background:#151b25;color:#eee4c7;font-family:system-ui}a{color:#94e8dc}video{max-width:100%;max-height:75vh;background:#080c12}.shots{display:flex;gap:12px;flex-wrap:wrap}figure{margin:12px 0;flex:1;min-width:180px}img{width:100%;height:auto}figcaption{padding:6px}</style>
<h1>操具・護身陣</h1><p>實際遊戲逐格錄製，20 FPS、1.7 秒。先展卷，再擴散護身；後半段以原生鍵盤輸入移動，展示加速撤退。完整七招透過升級卡學習；測試場景固定地形與敵人位置。</p>
<p><a href="../../digimon.html?lang=zh-TW">開啟實際遊戲</a> · <a href="capture-report.json">錄製驗證資料</a></p>'''
    (OUT / 'preview.html').write_text(html + ''.join(sections) + '</html>', encoding='utf-8')


if __name__ == '__main__':
    main()
