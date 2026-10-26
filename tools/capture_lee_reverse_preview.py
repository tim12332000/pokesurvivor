"""Capture native Reverse Lotus preview frames; never modifies sprite art."""
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/lee-reverse-preview'
URL = 'http://127.0.0.1:8004/art-review/lee-reverse-preview/'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True, args=['--autoplay-policy=no-user-gesture-required'])
        saved_audio = json.dumps({'music': .38, 'sfx': .41, 'muted': False})
        context = browser.new_context(viewport={'width': 1000, 'height': 1100}, device_scale_factor=1,
                                      storage_state={'cookies': [], 'origins': [{'origin': 'http://127.0.0.1:8004',
                                          'localStorage': [{'name': 'ps.audio', 'value': saved_audio}]}]})
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(URL)
        page.wait_for_function('window.LeeReversePreview?.ready')
        assert not page.is_checked('#sound'), 'Preview should start silent'
        silent_meter = page.evaluate('''async () => {
          const A=document.querySelector('#game-source').contentWindow.G.Audio;
          A.unlock();const meter=A.debugMeter(400);A.music('battle');A.sfx('land');return await meter;
        }''')
        assert silent_meter is not None and silent_meter['peak'] == 0, silent_meter
        page.evaluate('LeeReversePreview.replay({manual:true})')
        frames = []
        captured = set()
        for _ in range(90):
            page.evaluate('LeeReversePreview.step(1/24)')
            frames.append(Image.open(io.BytesIO(page.locator('#preview').screenshot())).convert('RGB'))
            state = page.evaluate('LeeReversePreview.report()')
            for label, ready in [('combo', state.get('phase') == 'combo' and state.get('ticks', 0) >= 2),
                                 ('landing', state.get('phase') == 'slam')]:
                if ready and label not in captured:
                    page.screenshot(path=str(OUT / f'preview-{label}-group.png'))
                    page.locator('#preview').screenshot(path=str(OUT / f'arena-{label}-group.png'))
                    captured.add(label)
        report = page.evaluate('LeeReversePreview.report()')
        assert report['completion'], report
        assert report['completion']['hits'] == 7, report
        assert len(report['completion']['group']) == 5, report
        assert all(member['hits'] == 7 and member['damage'] > 0 for member in report['completion']['group']), report
        assert report['completion']['splash']['hits'] == 1 and report['completion']['splash']['damage'] > 0, report
        assert report['completion']['outside'] == 0, report
        assert captured == {'combo', 'landing'}, captured
        assert not errors, errors
        frames[0].save(OUT / 'reverse-lotus-group.gif', save_all=True, append_images=frames[1:], duration=42, loop=0)
        page.screenshot(path=str(OUT / 'preview-desktop-group.png'))
        page.evaluate('LeeReversePreview.replay({manual:true})')
        contacts = []
        for hit in range(1, 5):
            state = page.evaluate('''hit => {
              for(let n=0;n<1200;n++){
                LeeReversePreview.step(1/240);
                const s=LeeReversePreview.report();
                if(s.phase==='combo'&&s.ticks>=hit)return s;
              }
              throw Error('Missing native contact '+hit);
            }''', hit)
            path = OUT / f'contact-{hit}-group.png'
            page.locator('#preview').screenshot(path=str(path))
            follow_path = OUT / f'followthrough-{hit}-group.png'
            page.evaluate('LeeReversePreview.step(.1)')
            page.locator('#preview').screenshot(path=str(follow_path))
            contacts.append({'hit': hit, 'actorPose': state['actorPose'], 'victimPose': state['victimPose'],
                             'framing': state['framing'], 'path': str(path), 'followPath': str(follow_path)})
        assert max(c['actorPose']['offsetY'] for c in contacts) - min(c['actorPose']['offsetY'] for c in contacts) > 40, contacts
        span = lambda rows, key: max(c[key]['offsetX'] for c in rows) - min(c[key]['offsetX'] for c in rows)
        scale, width = contacts[0]['framing']['scale'], contacts[0]['framing']['width']
        coverage = {'actorWorldSpan': span(contacts, 'actorPose'), 'victimWorldSpan': span(contacts, 'victimPose'),
                    'actorWidthFraction': span(contacts, 'actorPose') * scale / width,
                    'victimWidthFraction': span(contacts, 'victimPose') * scale / width}
        previous = json.loads((OUT / 'report-multidirection.json').read_text(encoding='utf-8'))['contacts']
        coverage['previousActorWidthFraction'] = span(previous, 'actorPose') * 2 / width
        coverage['previousVictimWidthFraction'] = span(previous, 'victimPose') * 2 / width
        assert coverage['actorWidthFraction'] > .55, coverage
        assert coverage['victimWorldSpan'] > 300, coverage
        font = ImageFont.truetype(r'C:\Windows\Fonts\msjh.ttc', 21)
        board = Image.new('RGB', (1120, 960), '#101923')
        draw = ImageDraw.Draw(board)
        for index, contact in enumerate(contacts):
            x, y = index % 2 * 560, index // 2 * 480
            label = ['左下追擊', '右上追擊', '左上追擊', '右下追擊'][index]
            draw.text((x + 14, y + 6), f'第 {index+1} 擊 · {label}', fill='#eef5ef', font=font)
            shot = Image.open(contact['path']).convert('RGB')
            shot.thumbnail((560, 446))
            board.paste(shot, (x + (560-shot.width)//2, y + 34))
        board.save(OUT / 'group-storyboard.png')
        follow = Image.new('RGB', (1120, 960), '#101923')
        follow_draw = ImageDraw.Draw(follow)
        for index, contact in enumerate(contacts):
            x, y = index % 2 * 560, index // 2 * 480
            follow_draw.text((x + 14, y + 6), f'第 {index+1} 擊後 · 群體追擊', fill='#eef5ef', font=font)
            shot = Image.open(contact['followPath']).convert('RGB')
            shot.thumbnail((560, 446))
            follow.paste(shot, (x + (560-shot.width)//2, y + 34))
        follow.save(OUT / 'group-followthrough-storyboard.png')
        page.set_viewport_size({'width': 390, 'height': 844})
        page.evaluate('LeeReversePreview.replay({manual:true})')
        for _ in range(80):
            page.evaluate('LeeReversePreview.step(1/24)')
            if page.evaluate("LeeReversePreview.report().phase==='slam'"):
                break
        page.screenshot(path=str(OUT / 'preview-mobile-group.png'))
        page.select_option('#level', '5')
        page.evaluate('LeeReversePreview.replay({manual:true})')
        for _ in range(90):
            page.evaluate('LeeReversePreview.step(1/24)')
            if page.evaluate("LeeReversePreview.report().phase==='combo'&&LeeReversePreview.report().ticks>=11"):
                page.screenshot(path=str(OUT / 'preview-mobile-level5-normal-group.png'))
                break
        page.check('#gates')
        page.evaluate('LeeReversePreview.replay({manual:true})')
        high_captured = False
        for _ in range(90):
            page.evaluate('LeeReversePreview.step(1/24)')
            if not high_captured and page.evaluate("LeeReversePreview.report().phase==='combo'&&LeeReversePreview.report().ticks>=11"):
                page.screenshot(path=str(OUT / 'preview-mobile-level5-gates-group.png'))
                high_captured = True
        upgraded = page.evaluate('LeeReversePreview.report()')
        assert upgraded['completion']['hits'] == 15, upgraded
        assert all(member['hits'] == 15 for member in upgraded['completion']['group']), upgraded
        assert upgraded['completion']['outside'] == 0, upgraded
        assert high_captured, 'High-level aerial sample missing'
        page.check('#sound')
        enabled_meter = page.evaluate('''async () => {
          const A=document.querySelector('#game-source').contentWindow.G.Audio;
          const meter=A.debugMeter(400);A.sfx('select');return await meter;
        }''')
        assert enabled_meter['peak'] > 0, enabled_meter
        page.uncheck('#sound')
        audio = page.evaluate('LeeReversePreview.report().audio')
        assert audio['storedBefore'] == saved_audio == audio['storedAfter'], audio
        assert not audio['track'] and not audio['enabled'], audio
        muted_saved = json.dumps({'music': .38, 'sfx': .41, 'muted': True})
        muted_context = browser.new_context(storage_state={'cookies': [], 'origins': [{'origin': 'http://127.0.0.1:8004',
            'localStorage': [{'name': 'ps.audio', 'value': muted_saved}]}]})
        muted_page = muted_context.new_page()
        muted_page.on('pageerror', lambda error: errors.append(str(error)))
        muted_page.goto(URL)
        muted_page.wait_for_function('window.LeeReversePreview?.ready')
        muted_default_meter = muted_page.evaluate('document.querySelector("#game-source").contentWindow.G.Audio.debugMeter(300)')
        assert muted_default_meter['peak'] == 0, muted_default_meter
        muted_page.check('#sound')
        muted_enabled_meter = muted_page.evaluate('''async () => {
          const A=document.querySelector('#game-source').contentWindow.G.Audio;
          const meter=A.debugMeter(300);A.sfx('select');return await meter;
        }''')
        assert muted_enabled_meter['peak'] > 0, muted_enabled_meter
        muted_audit = muted_page.evaluate('LeeReversePreview.report().audio')
        assert muted_audit['storedBefore'] == muted_saved == muted_audit['storedAfter'], muted_audit
        muted_context.close()
        assert not errors, errors
        browser.close()
    (OUT / 'report-group.json').write_text(json.dumps({'errors': errors, 'contacts': contacts, 'coverage': coverage,
        'level5Gates': upgraded, 'silentMeter': silent_meter, 'enabledMeter': enabled_meter, 'audioAudit': audio,
        'savedMutedDefaultMeter': muted_default_meter, 'savedMutedEnabledMeter': muted_enabled_meter,
        'savedMutedAudit': muted_audit, **report}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'url': URL, 'evidence': str(OUT), 'completion': report['completion']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
