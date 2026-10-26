"""Capture native Front Lotus phases and verify its preview remains silent."""
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/lee-front-lotus'
URL = 'http://127.0.0.1:8004/art-review/lee-front-preview/'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
PHASES = {'windup': '踢前蓄勢', 'lift': '踢擊挑空', 'suspend': '背後抱住',
          'descent': '倒栽旋落', 'slam': '放手重摔', 'recovery': '收招'}


def check_completion(result):
    assert result['completion'], result
    assert result['skill']['cooldown'] == 10, result['skill']
    completion = result['completion']
    assert len(completion['group']) == 3, completion
    assert completion['group'][0]['hits'] == 2, completion
    assert all(target['hits'] == 1 and target['damage'] > 0 for target in completion['group'][1:]), completion
    assert completion['splash']['hits'] == 1 and completion['splash']['damage'] > 0, completion
    assert completion['outside'] == 0, completion
    for hit in result['ledger']:
        if not hit['primary']:
            assert hit['phase'] == 'slam', hit


def storyboard(paths):
    font = ImageFont.truetype(r'C:\Windows\Fonts\msjh.ttc', 21)
    board = Image.new('RGB', (1440, 780), '#101923')
    draw = ImageDraw.Draw(board)
    for index, (phase, title) in enumerate(PHASES.items()):
        x, y = index % 3 * 480, index // 3 * 390
        draw.text((x + 14, y + 6), title, fill='#eef5ef', font=font)
        shot = Image.open(paths[phase]).convert('RGB')
        shot.thumbnail((480, 356))
        board.paste(shot, (x + (480-shot.width)//2, y + 34))
    board.save(OUT / 'front-lotus-storyboard.png')


def pose_crop(path, target, state):
    shot = Image.open(path).convert('RGB')
    frame = state['framing']
    ratio = shot.width / frame['width']
    center_y = (frame['originY'] - state['visualLift'] - 14) * frame['scale'] * ratio
    left = max(0, int(shot.width / 2 - 200))
    top = max(0, min(shot.height - 420, int(center_y - 190)))
    shot.crop((left, top, min(shot.width, left + 400), min(shot.height, top + 420))).save(target)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {},
              'referenceScope': 'Previously extracted setup/kick reference is partial; this capture does not verify an entire original video.'}
    saved_audio = json.dumps({'music': .38, 'sfx': .41, 'muted': True})
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True,
                                     args=['--autoplay-policy=no-user-gesture-required'])
        for label, viewport, mobile in [('desktop', {'width': 1000, 'height': 1050}, False),
                                        ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile,
                service_workers='block', storage_state={'cookies': [], 'origins': [{
                    'origin': 'http://127.0.0.1:8004', 'localStorage': [{'name': 'ps.audio', 'value': saved_audio}]}]})
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(URL)
            page.wait_for_function('window.LeeFrontPreview?.ready || document.querySelector("#status").textContent.startsWith("預覽載入失敗")')
            assert page.evaluate('LeeFrontPreview.ready'), page.locator('#status').inner_text()
            assert not page.is_checked('#sound')
            silent = page.evaluate('''async () => {
              const A=document.querySelector('#game-source').contentWindow.G.Audio;
              A.unlock();const meter=A.debugMeter(350);A.music('battle');A.sfx('land');return await meter;
            }''')
            assert silent is not None and silent['peak'] == silent['rms'] == 0, silent
            page.evaluate('LeeFrontPreview.replay({manual:true})')
            frames, paths, phase_states, extra_states = [], {}, {}, {}
            for _ in range(360):
                page.evaluate('LeeFrontPreview.step(1/60)')
                state = page.evaluate('LeeFrontPreview.report()')
                if not mobile:
                    frames.append(Image.open(io.BytesIO(page.locator('#preview').screenshot())).convert('RGB'))
                phase = state.get('phase')
                if phase in PHASES and phase not in paths and state.get('phaseProgress', 0) >= .33:
                    path = OUT / f'{label}-front-{phase}.png'
                    page.locator('#preview').screenshot(path=str(path))
                    paths[phase] = path
                    phase_states[phase] = {key: state.get(key) for key in ('phase', 'phaseProgress', 'visualLift', 'actorPose', 'victimPose')}
                    if phase in ('suspend', 'descent'):
                        page.screenshot(path=str(OUT / f'{label}-front-{phase}-page.png'))
                for shot_label, shot_phase, threshold in [('reach', 'suspend', .10), ('clasp', 'suspend', .45),
                        ('inverted', 'suspend', .85), ('dive-early', 'descent', .15),
                        ('dive-mid', 'descent', .5), ('dive-late', 'descent', .85)]:
                    if phase == shot_phase and shot_label not in extra_states and state.get('phaseProgress', 0) >= threshold:
                        path = OUT / f'{label}-{shot_label}-stage.png'
                        page.locator('#preview').screenshot(path=str(path))
                        pose_crop(path, OUT / f'{label}-{shot_label}-closeup.png', state)
                        extra_states[shot_label] = {key: state.get(key) for key in ('phase', 'phaseProgress', 'visualLift', 'actorPose', 'victimPose')}
                if state['completion']:
                    break
            result = page.evaluate('LeeFrontPreview.report()')
            check_completion(result)
            assert set(paths) == set(PHASES), (label, paths.keys())
            assert len(extra_states) == 6, (label, extra_states.keys())
            assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'), label
            if not mobile:
                frames += [frames[-1]] * 12
                frames[0].save(OUT / 'front-lotus-redesign.gif', save_all=True, append_images=frames[1:], duration=17, loop=0)
                storyboard(paths)
            page.select_option('#level', '5')
            page.check('#gates')
            page.evaluate('LeeFrontPreview.replay({manual:true})')
            high_captured = set()
            for _ in range(360):
                page.evaluate('LeeFrontPreview.step(1/60)')
                state = page.evaluate('LeeFrontPreview.report()')
                phase = state.get('phase')
                if phase in ('suspend', 'descent') and phase not in high_captured and state.get('phaseProgress', 0) >= .4:
                    page.screenshot(path=str(OUT / f'{label}-level5-gates-{phase}.png'))
                    high_captured.add(phase)
                if state['completion']:
                    break
            upgraded = page.evaluate('LeeFrontPreview.report()')
            check_completion(upgraded)
            assert high_captured == {'suspend', 'descent'}, high_captured
            page.check('#sound')
            audible = page.evaluate('''async () => {
              const A=document.querySelector('#game-source').contentWindow.G.Audio;
              const meter=A.debugMeter(350);A.sfx('select');return await meter;
            }''')
            assert audible['peak'] > 0, audible
            page.uncheck('#sound')
            audit = page.evaluate('LeeFrontPreview.report().audio')
            assert audit['storedBefore'] == saved_audio == audit['storedAfter'], audit
            assert not audit['track'] and not audit['enabled'], audit
            report['viewports'][label] = {'normal': result, 'upgraded': upgraded,
                'phaseStates': phase_states, 'extraPoseStates': extra_states,
                'silentMeter': silent, 'enabledMeter': audible, 'audioAudit': audit}
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    (OUT / 'preview-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'url': URL, 'evidence': str(OUT),
        'results': {label: entry['normal']['completion'] for label, entry in report['viewports'].items()}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
