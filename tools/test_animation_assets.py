"""Validate original authored atlas registration and runtime rendering.

--write rebuilds crop metadata from the original generated atlases.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def verify(data):
    atlas_map = json.loads((ROOT/'art-review/redrawn/atlas-map.json').read_text())
    provenance = json.loads((ROOT/'art-review/redrawn/provenance.json').read_text())
    outputs = {item['file']: item for item in provenance['outputs']}
    expected = {hero+'-'+kind for hero in ('naruto','sasuke')
                for kind in ('movement','idle','hurt','death','attack')}
    expected.update('naruto-'+kind for kind in ('clones','rasengan','throw','cloak'))
    expected.update('sasuke-'+kind for kind in ('chidori','fireball','throw','sword'))
    assert set(data) == expected, set(data) ^ expected
    assert len(outputs) == len(atlas_map) == 5
    for source in atlas_map.values():
        path = ROOT/'art-review'/source['source']
        assert source['source'].startswith('redrawn/')
        assert outputs[source['source']]['kind'] == 'newly drawn bitmap'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == outputs[source['source']]['sha256']
    for key, spec in data.items():
        assert spec['source'] in outputs, key
        assert spec['source'].startswith('redrawn/'), key
        image = Image.open(ROOT/'art-review'/spec['source'])
        assert image.mode == 'RGBA' and image.getchannel('A').getextrema() == (0,255)
        assert spec['safeFrames'] == list(range(len(spec['frames']))), key
        assert len(spec['frames']) == (16 if key.endswith(('-movement','-idle','-hurt')) else 4)
        source = next(a for a in atlas_map.values() if a['source'] == spec['source'])
        assert spec['bodyHeight'] == source['bodyHeight'] > 0
        for index in spec['safeFrames']:
            frame = spec['frames'][index]
            assert frame['rect'] == source['frames'][frame['atlasIndex']]['rect'], (key,index)
            x,y,w,h = frame['rect']
            assert 0 <= x < x+w <= image.width and 0 <= y < y+h <= image.height
            crop = image.crop((x,y,x+w,y+h))
            assert crop.getchannel('A').point(lambda a:255 if a>=180 else 0).getbbox()
            ax,ay = frame['anchor']
            assert 0 <= ax <= w and 0 <= ay <= h
            assert frame['bodyHeight'] == spec['bodyHeight']
            assert isinstance(frame.get('mirror',False),bool)
        if 'directions' in spec:
            assert spec['directions'] == {'down':0,'up':1,'left':2,'right':3}
            assert [f.get('mirror',False) for f in spec['frames']] == [False]*8+[True]*4+[False]*4


def contact_sheet(data):
    sheet = Image.new('RGB', (16*112, len(data)*128), '#263b32')
    draw = ImageDraw.Draw(sheet)
    for row, (key, spec) in enumerate(data.items()):
        image = Image.open(ROOT/'art-review'/spec['source']).convert('RGBA')
        draw.text((3,row*128+2), key, fill='white')
        for index, frame in enumerate(spec['frames']):
            if not frame:
                continue
            x,y,w,h = frame['rect']
            scale = 64/spec['bodyHeight']
            crop = image.crop((x,y,x+w,y+h))
            crop = crop.resize((round(w*scale),round(h*scale)),Image.Resampling.NEAREST)
            footx, footy = index*112+56, row*128+110
            ax,ay = frame['anchor']
            sheet.paste(crop,(round(footx-ax*scale),round(footy-ay*scale)),crop)
            draw.line((footx-6,footy,footx+6,footy),fill='#ff80ff')
            draw.text((index*112+3,row*128+18),str(index),fill='white')
    target = ROOT/'.omx/state/animation-complete/assets-contact.png'
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target)
    print(target)


def browser_verify():
    from playwright.sync_api import sync_playwright
    import mimetypes
    from urllib.parse import urlsplit, unquote
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
        page = browser.new_page()
        def route(request):
            path = ROOT/unquote(urlsplit(request.request.url).path).lstrip('/')
            request.fulfill(status=200 if path.is_file() else 404,
                            body=path.read_bytes() if path.is_file() else b'',
                            content_type=mimetypes.guess_type(path)[0] or 'application/octet-stream')
        page.route('http://animation.test/**', route)
        page.goto('http://animation.test/art-review/animation-assets.json')
        page.add_script_tag(url='http://animation.test/art-review/animation-assets.js')
        report = page.evaluate('''async () => {
          const A = window.AnimationAssets;
          await A.load(); await A.load();
          if (!A.ready || A.keys.length !== 18) throw Error('incomplete image decoding');
          const canvas = document.createElement('canvas'); canvas.width=canvas.height=240;
          const ctx=canvas.getContext('2d',{willReadFrequently:true});
          let count=0;
          for(const key of A.keys) for(const i of A.get(key).safeFrames) {
            ctx.clearRect(0,0,240,240);
            if(!A.draw(ctx,key,i,120,120,{alpha:.5,flash:true,mirror:true,rotation:.1})) throw Error('missing crop');
            const pixels=ctx.getImageData(0,0,240,240).data;
            let visible=0;
            for(let p=0;p<pixels.length;p+=4) if(pixels[p+3]>20) {
              visible++;
              if(pixels[p]<250||pixels[p+1]<250||pixels[p+2]<250||pixels[p+3]>128) throw Error('flash/alpha failed');
            }
            if(visible<100) throw Error('empty actor');
            const transform=ctx.getTransform();
            if(transform.a!==1||transform.d!==1||transform.e!==0||ctx.globalAlpha!==1) throw Error('context state leaked');
            count++;
          }
          if(A.draw(ctx,'sasuke-chidori',4,120,120)) throw Error('out-of-range frame rendered');
          if(A.draw(ctx,'missing-atlas',0,120,120)) throw Error('missing atlas rendered');
          // Frame-level left mirroring and explicit mirroring compose by XOR.
          const original=ctx.drawImage.bind(ctx);let transform;
          ctx.drawImage=(...args)=>{transform=ctx.getTransform();return original(...args)};
          A.draw(ctx,'naruto-movement',8,120,120);
          if(transform.a>=0)throw Error('left frame mirror lost');
          A.draw(ctx,'naruto-movement',8,120,120,{mirror:true});
          if(transform.a<=0)throw Error('double mirror did not cancel');
          return {decoded:A.keys.length,drawn:count};
        }''')
        browser.close()
        print('Browser PASS:', report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--browser', action='store_true')
    args = parser.parse_args()
    target = ROOT/'art-review/animation-assets.json'
    if args.write:
        subprocess.run([sys.executable,str(ROOT/'tools/build_redrawn_atlases.py')],check=True)
    data = json.loads(target.read_text(encoding='utf-8'))
    verify(data)
    contact_sheet(data)
    if args.browser:
        browser_verify()
    print('PASS: 18 authored sequences, five provenance hashes, valid alpha/crops/scales/mirrors')
