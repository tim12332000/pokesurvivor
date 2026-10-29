"""Verify proportional forest packing and the optional full-skill game entry."""
import json
import os
from pathlib import Path

os.environ.setdefault('KIMIMARO_OUT', str(Path(__file__).resolve().parents[1]/'.omx/state/kimimaro-practice'))
import test_kimimaro as game
from PIL import Image
from playwright.sync_api import sync_playwright
from build_kimimaro_forest_assets import SOURCE_RECTS


def main():
    game.OUT.mkdir(parents=True, exist_ok=True)
    inventory = game.asset_inventory()
    meta = json.loads((game.ROOT/'art-review/kimimaro-frames.json').read_text())
    sources=[('kimimaro-bone-spikes-generated-v3.png',(i*512,0,512,768),i+5) for i in range(4)]
    sources.extend(('kimimaro-forest-groves-generated-v4.png',rect,i+9) for i,rect in enumerate(SOURCE_RECTS))
    for filename,(x,y,w,h),key in sources:
        source = Image.open(game.ROOT/'art-review/redrawn'/filename).convert('RGBA')
        cell = source.crop((x,y,x+w,y+h))
        bounds = cell.getchannel('A').point(lambda a: 255 if a >= 128 else 0).getbbox()
        width, height = bounds[2]-bounds[0], bounds[3]-bounds[1]
        frame_meta = meta['sheets']['effects']['frames'][f'pillar{key}']
        packed_width, packed_height = frame_meta['sourceSize']
        assert packed_width == round(width*packed_height/height)
        atlas = Image.open(game.ROOT/'art-review'/meta['sheets']['effects']['source']).convert('RGBA')
        restored = Image.new('RGBA', (packed_width, packed_height))
        for segment in frame_meta['segments']:
            x,y,w,h = segment['rect']
            restored.paste(atlas.crop((x,y,x+w,y+h)), (0,segment['offsetY']))
        crop = cell.crop(bounds)
        crop.putalpha(crop.getchannel('A').point(lambda a: 255 if a >= 128 else 0))
        expected = Image.new('RGBA', (packed_width, packed_height))
        expected.alpha_composite(crop.resize((packed_width,packed_height),Image.Resampling.LANCZOS))
        assert restored.tobytes() == expected.tobytes()
    report = {'inventory': inventory, 'entries': {}, 'errors': []}
    entry_url=game.URL.split('?',1)[0]+'?lang=zh-TW&hero=kimimaro'
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=game.CHROME, headless=True)
        for label, viewport in [('desktop', {'width':1280, 'height':900}), ('mobile', {'width':390, 'height':844})]:
            context = browser.new_context(viewport=viewport, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            for practice in (False, True):
                game.URL = entry_url + ('&kimimaroPractice=1' if practice else '')
                frame = game.boot(page, label)
                state = frame.evaluate("""() => {
                  const p=G.Game.player,ids=['naruto-kimimaro',...G.NarutoSkillCatalog.extraPools.get(30012)];
                  return {level:p.level,moves:p.moves.map(m=>({id:m.id,rank:m.lvl})),expected:ids};
                }""")
                if practice:
                    assert state['level'] == 30, state
                    assert set(state['expected']) <= {m['id'] for m in state['moves']}, state
                    assert all(m['rank'] == 5 for m in state['moves'] if m['id'] in state['expected']), state
                    frame.evaluate("""() => {
                      KAcceptance.fixture('naruto-kimimaro-bracken',5);
                      KAcceptance.p().target=KAcceptance.spawn(80,0);
                      KAcceptance.cast('naruto-kimimaro-bracken');KAcceptance.advance(2.6,true);
                    }""")
                    page.screenshot(path=str(game.OUT/f'{label}-forest-proportional.png'))
                    frame.evaluate("""() => {
                      KAcceptance.fixture('naruto-kimimaro-bracken',1);
                      KAcceptance.p().target=KAcceptance.spawn(80,0);
                      KAcceptance.cast('naruto-kimimaro-bracken');
                    }""")
                    elapsed = 0
                    for age in (.50,.82,1.14,1.46,1.78,2.10):
                        frame.evaluate('(dt)=>KAcceptance.advance(dt,true)', age-elapsed)
                        page.screenshot(path=str(game.OUT/f'{label}-radial-{age:.2f}.png'))
                        elapsed = age
                else:
                    assert state['level'] == 1 and len(state['moves']) == 1, state
                report['entries'][f'{label}-practice-{practice}'] = state
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    (game.OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'ok': True, 'entries': len(report['entries']), 'proportionalSprites': len(sources)}))


if __name__ == '__main__':
    main()
