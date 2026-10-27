"""Native chase/flurry evidence and warmed, matched cooldown-gap sustain comparison."""
import io
import json
import argparse
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/lee-pursuit'
URL = 'http://127.0.0.1:8004/art-review/lee-pursuit-preview/'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'


def check_demo(result, trace):
    completion, skill = result['completion'], result['skill']
    assert completion and len(completion['front']) == 3, result
    expected_hits = 3 if skill['level'] == 1 else 5
    assert all(target['damage'] > 0 and target['hpChanges'] == expected_hits for target in completion['front']), completion
    assert completion['behind']['damage'] == completion['outside']['damage'] == 0, completion
    assert 20 < completion['travel'] < skill['range'], completion
    assert skill['passive'] and not any('naruto-lee-pursuit' in group for group in result['slots']), result['slots']
    assert {'rush', 'attack'} <= {state.get('phase') for state in trace}, trace
    assert any(state.get('guard') for state in trace if state.get('phase') == 'rush'), 'Native rush guard missing'
    assert not any(state.get('guard') for state in trace if state.get('phase') == 'attack' and state.get('attackAge', 0) > .1), 'Rush guard leaked through the flurry'


def capture(page, label, gif=False):
    page.evaluate('LeePursuitPreview.replay({manual:true})')
    paths, trace, frames = {}, [], []
    for _ in range(240):
        page.evaluate('LeePursuitPreview.step(1/120)')
        state = page.evaluate('LeePursuitPreview.report()')
        trace.append({key: state.get(key) for key in ('elapsed', 'phase', 'age', 'attackAge', 'hitIndex', 'hits', 'position', 'guard', 'animation')})
        if gif:
            frames.append(Image.open(io.BytesIO(page.locator('#preview').screenshot())).convert('RGB'))
        phase, pose = state.get('phase'), state.get('animation')
        if phase:
            key = ('lee-movement' if phase == 'rush' else 'lee-attack')
            if page.is_checked('#gates'):
                key = key.replace('lee-', 'lee-opened-')
            assert pose['key'] == key, state
        shot = 'rush' if phase == 'rush' and state.get('age', 0) >= .025 else f'attack-{pose["frame"]}' if phase == 'attack' else None
        if shot and shot not in paths:
            path = OUT / f'{label}-{shot}.png'
            page.locator('#preview').screenshot(path=str(path))
            paths[shot] = path
            if shot in ('rush', 'attack-2'):
                page.screenshot(path=str(OUT / f'{label}-{shot}-page.png'))
        if state['completion']:
            break
    result = page.evaluate('LeePursuitPreview.report()')
    check_demo(result, trace)
    finish = OUT / f'{label}-finish.png'
    page.locator('#preview').screenshot(path=str(finish));paths['finish'] = finish
    assert {'rush', 'attack-0', 'attack-1', 'attack-2', 'attack-3', 'finish'} <= set(paths), paths.keys()
    if gif:
        frames += [frames[-1]] * 15
        frames[0].save(OUT / 'pursuit-half-speed.gif', save_all=True, append_images=frames[1:], duration=17, loop=0)
        board = Image.new('RGB', (1440, 780), '#101923')
        draw = ImageDraw.Draw(board);font = ImageFont.truetype(r'C:\Windows\Fonts\msjh.ttc', 21)
        for index, (shot, title) in enumerate([('rush', '追近'), ('attack-0', '出拳'), ('attack-1', '連打'),
                ('attack-2', '連打'), ('attack-3', '末擊'), ('finish', '收勢')]):
            x, y = index % 3 * 480, index // 3 * 390
            draw.text((x + 14, y + 6), title, fill='#eef5ef', font=font)
            image = Image.open(paths[shot]).convert('RGB');image.thumbnail((480, 356));board.paste(image, (x + (480-image.width)//2, y + 34))
        board.save(OUT / 'pursuit-storyboard.png')
    return {'result': result, 'trace': trace, 'paths': {key: str(path) for key, path in paths.items()}}


def check_comparison(result):
    baseline, treatment = result['without'], result['withSkill']
    assert result['freshOwners'], result
    assert baseline['stats'] == treatment['stats'], (baseline['stats'], treatment['stats'])
    assert baseline['warmupDamage'] == treatment['warmupDamage'] > 0, result
    assert baseline['mainCooldown'] == treatment['mainCooldown'], result
    assert baseline['mainCooldownRemaining'] == treatment['mainCooldownRemaining'] > 900, result
    for condition in (baseline, treatment):
        assert condition['start'] == condition['end'], condition
        assert condition['start']['boss'] == {'x': 35, 'y': 0}, condition
        assert condition['measuredHpLoss'] > 0 and condition['seconds'] == 20, condition
        assert len(condition['points']) == 20, condition
    assert treatment['measuredHpLoss'] > baseline['measuredHpLoss'], result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reuse-sustain', action='store_true', help='Reuse the already-verified numeric benchmark when only visual code changed.')
    options = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    previous = json.loads((OUT / 'preview-report.json').read_text(encoding='utf-8')) if options.reuse_sustain else None
    report = {'errors': [], 'viewports': {}, 'gifPlaybackRate': .5, 'sustainReusedFromPriorVerifiedRun': options.reuse_sustain,
              'runtimeSha256': hashlib.sha256((ROOT / '.omx/naruto-lee-pursuit.js').read_bytes()).hexdigest()}
    saved_audio = json.dumps({'music': .38, 'sfx': .41, 'muted': True})
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True, args=['--autoplay-policy=no-user-gesture-required'])
        for label, viewport, mobile in [('desktop', {'width': 1000, 'height': 1050}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block',
                storage_state={'cookies': [], 'origins': [{'origin': 'http://127.0.0.1:8004', 'localStorage': [{'name': 'ps.audio', 'value': saved_audio}]}]})
            page = context.new_page();page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(URL)
            page.wait_for_function('window.LeePursuitPreview?.ready || document.querySelector("#status").textContent.startsWith("預覽載入失敗")')
            assert page.evaluate('LeePursuitPreview.ready'), page.locator('#status').inner_text()
            assert not page.is_checked('#sound')
            silent = page.evaluate('''async () => {const A=document.querySelector('#game-source').contentWindow.G.Audio;
              A.unlock();const meter=A.debugMeter(350);A.music('battle');A.sfx('land');return await meter;}''')
            assert silent is not None and silent['peak'] == silent['rms'] == 0, silent
            normal = capture(page, label, gif=not mobile)
            comparisons = {}
            if not mobile:
                if options.reuse_sustain:
                    comparisons = previous['viewports']['desktop']['sustainComparisons']
                    for comparison in comparisons.values():check_comparison(comparison)
                else:
                    for level in (1, 5):
                        page.select_option('#level', str(level))
                        comparison = page.evaluate('LeePursuitPreview.compare(20,true)')
                        check_comparison(comparison);comparisons[str(level)] = comparison
                    page.screenshot(path=str(OUT / 'desktop-sustain-comparison.png'))
            page.select_option('#level', '5');page.check('#gates')
            upgraded = capture(page, label + '-level5-gates')
            assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'), label
            page.check('#sound')
            audible = page.evaluate('''async () => {const A=document.querySelector('#game-source').contentWindow.G.Audio;
              const meter=A.debugMeter(350);A.sfx('select');return await meter;}''')
            assert audible['peak'] > 0, audible
            page.uncheck('#sound');audit = page.evaluate('LeePursuitPreview.report().audio')
            assert audit['storedBefore'] == saved_audio == audit['storedAfter'], audit
            assert not audit['track'] and not audit['enabled'], audit
            report['viewports'][label] = {'normal': normal, 'upgraded': upgraded, 'sustainComparisons': comparisons,
                'silentMeter': silent, 'enabledMeter': audible, 'audioAudit': audit}
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    (OUT / 'preview-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'url': URL, 'evidence': str(OUT), 'sustain': {level: {'without': data['without']['measuredHpLoss'],
        'with': data['withSkill']['measuredHpLoss'], 'ratio': data['ratio']} for level, data in report['viewports']['desktop']['sustainComparisons'].items()}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
