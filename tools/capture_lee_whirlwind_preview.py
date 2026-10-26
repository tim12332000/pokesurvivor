"""Capture native Leaf Whirlwind poses, cone hits and silent preview controls."""
import io
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/lee-whirlwind'
URL = 'http://127.0.0.1:8004/art-review/lee-whirlwind-preview/'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
POSES = ['踏入', '起跳', '展腿', '背身旋轉', '背身出腳', '旋踢命中', '落地', '收勢']


def check_completion(result, trace):
    assert result['completion'], result
    completion, skill = result['completion'], result['skill']
    assert len(completion['front']) == 3, completion
    assert all(target['hits'] == 1 and target['damage'] > 0 for target in completion['front']), completion
    assert completion['behind']['hits'] == completion['behind']['damage'] == 0, completion
    assert completion['outside']['hits'] == completion['outside']['damage'] == 0, completion
    assert 0 < completion['stepDistance'] <= 20.01, completion
    assert skill['mode'] == 'melee' and skill['arc'] == 3.9 and skill['knock'] == 95, skill
    expected = {'damage': 37, 'cooldown': 2, 'radius': 62} if skill['level'] == 1 else {'damage': 55.5, 'cooldown': 1.8, 'radius': 69.44}
    assert all(abs(skill[key] - value) < 1e-7 for key, value in expected.items()), skill
    assert not any(state['invulnerable'] for state in trace), 'Whirlwind gained invulnerability'
    assert max(state.get('visualLift') or 0 for state in trace) >= 30, 'Native aerial lift missing'
    assert all(.37 <= hit['time'] <= .40 for hit in result['ledger']), result['ledger']
    assert result['animation']['key'] not in ('lee-whirlwind', 'lee-opened-whirlwind'), result['animation']


def storyboard(paths):
    font = ImageFont.truetype(r'C:\Windows\Fonts\msjh.ttc', 21)
    board = Image.new('RGB', (1920, 780), '#101923')
    draw = ImageDraw.Draw(board)
    for frame, title in enumerate(POSES):
        x, y = frame % 4 * 480, frame // 4 * 390
        draw.text((x + 14, y + 6), title, fill='#eef5ef', font=font)
        shot = Image.open(paths[frame]).convert('RGB')
        shot.thumbnail((480, 356))
        board.paste(shot, (x + (480-shot.width)//2, y + 34))
    board.save(OUT / 'whirlwind-storyboard.png')


def capture(page, label, save_gif=False):
    page.evaluate('LeeWhirlwindPreview.replay({manual:true})')
    frames, paths, trace = [], {}, []
    for _ in range(180):
        page.evaluate('LeeWhirlwindPreview.step(1/120)')
        state = page.evaluate('LeeWhirlwindPreview.report()')
        trace.append({key: state.get(key) for key in ('elapsed', 'phase', 'frame', 'fieldTime', 'visualLift', 'position', 'invulnerable', 'camera', 'animation')})
        if save_gif:
            frames.append(Image.open(io.BytesIO(page.locator('#preview').screenshot())).convert('RGB'))
        frame = state.get('frame')
        if frame is not None and frame not in paths:
            assert isinstance(frame, int) and 0 <= frame < 8, state
            expected_key = 'lee-opened-whirlwind-air' if page.is_checked('#gates') else 'lee-whirlwind-air'
            assert state['animation']['key'] == expected_key and state['animation']['frame'] == frame, state
            path = OUT / f'{label}-pose-{frame}.png'
            page.locator('#preview').screenshot(path=str(path))
            paths[frame] = path
            if frame in (2, 4):
                page.screenshot(path=str(OUT / f'{label}-pose-{frame}-page.png'))
        if state['completion']:
            break
    result = page.evaluate('LeeWhirlwindPreview.report()')
    check_completion(result, trace)
    assert set(paths) == set(range(8)), (label, paths.keys())
    if save_gif:
        # Half-speed evidence makes the short native action easy to inspect.
        frames += [frames[-1]] * 20
        frames[0].save(OUT / 'whirlwind-half-speed.gif', save_all=True, append_images=frames[1:], duration=17, loop=0)
        storyboard(paths)
    return {'result': result, 'trace': trace, 'frames': [str(paths[index]) for index in range(8)]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}, 'gifPlaybackRate': .5,
              'reference': '.omx/state/lee-whirlwind-plan/user-reference-storyboard.jpg'}
    metadata = json.loads((ROOT / 'art-review/animation-assets.json').read_text(encoding='utf-8'))
    report['selectedArt'] = {key: {'source': metadata[key]['source'], 'bodyHeight': metadata[key]['bodyHeight'],
        'frames': len(metadata[key]['frames']),
        'sha256': hashlib.sha256((ROOT / 'art-review' / metadata[key]['source']).read_bytes()).hexdigest()}
        for key in ('lee-whirlwind-air', 'lee-opened-whirlwind-air')}
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
            page.wait_for_function('window.LeeWhirlwindPreview?.ready || document.querySelector("#status").textContent.startsWith("預覽載入失敗")')
            assert page.evaluate('LeeWhirlwindPreview.ready'), page.locator('#status').inner_text()
            assert not page.is_checked('#sound')
            silent = page.evaluate('''async () => {
              const A=document.querySelector('#game-source').contentWindow.G.Audio;
              A.unlock();const meter=A.debugMeter(350);A.music('battle');A.sfx('land');return await meter;
            }''')
            assert silent is not None and silent['peak'] == silent['rms'] == 0, silent
            normal = capture(page, label, save_gif=not mobile)
            page.select_option('#level', '5')
            page.check('#gates')
            upgraded = capture(page, label + '-level5-gates')
            assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'), label
            page.check('#sound')
            audible = page.evaluate('''async () => {
              const A=document.querySelector('#game-source').contentWindow.G.Audio;
              const meter=A.debugMeter(350);A.sfx('select');return await meter;
            }''')
            assert audible['peak'] > 0, audible
            page.uncheck('#sound')
            audit = page.evaluate('LeeWhirlwindPreview.report().audio')
            assert audit['storedBefore'] == saved_audio == audit['storedAfter'], audit
            assert not audit['track'] and not audit['enabled'], audit
            report['viewports'][label] = {'normal': normal, 'upgraded': upgraded,
                'silentMeter': silent, 'enabledMeter': audible, 'audioAudit': audit}
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    (OUT / 'preview-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'url': URL, 'evidence': str(OUT),
        'results': {label: entry['normal']['result']['completion'] for label, entry in report['viewports'].items()}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
