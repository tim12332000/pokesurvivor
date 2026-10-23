"""Check real Tenten atlas geometry, authored frames and build registration."""
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/tenten'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mapping = json.loads((ROOT / 'art-review/redrawn/atlas-map.json').read_text('utf-8'))
    metadata = json.loads((ROOT / 'art-review/animation-assets.json').read_text('utf-8'))
    provenance = '\n'.join(path.read_text('utf-8') for path in [ROOT / 'art-review/redrawn/provenance.json', ROOT / 'art-review/tenten-production-provenance.json'] if path.exists())
    report = {'atlases': {}, 'keys': []}
    for key, minimum in [('tenten-common', 32), ('tenten-skills', 16), ('tenten-twin-release', 4)]:
        atlas = mapping[key]
        path = ROOT / 'art-review' / atlas['source']
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest in provenance, 'missing current authored source provenance '+key
        image = Image.open(path).convert('RGBA')
        assert len(atlas['frames']) >= minimum, key
        assert atlas['bodyHeight'] > 0, key
        crops = []
        for index, frame in enumerate(atlas['frames']):
            x, y, w, h = frame['rect']
            ax, ay = frame['anchor']
            assert 0 <= x < x+w <= image.width and 0 <= y < y+h <= image.height, (key, index, frame)
            assert w > 5 and h > 15 and 0 <= ax <= w and 0 <= ay <= h+5, (key, index, frame)
            crop = image.crop((x, y, x+w, y+h))
            assert crop.getchannel('A').getextrema()[1] == 255, 'empty authored pose'
            assert sum(1 for p in crop.getdata() if p[3] > 32) > 80, 'near-empty authored pose'
            crops.append(hashlib.sha256(crop.tobytes()).hexdigest())
            if key == 'tenten-twin-release':
                assert len(atlas['frames']) == 4, 'release must contain four genuine poses'
                for point in ('hand', 'scrollLeft', 'scrollRight'):
                    hx, hy = frame[point]
                    assert 0 <= hx < w and 0 <= hy < h, (key, index, point)
                    assert crop.getpixel((hx, hy))[3] > 180, 'palm anchor misses opaque hand'
        assert len(set(crops)) >= minimum*.7, 'repeated static body posing as action atlas'
        if key == 'tenten-twin-release':
            assert len(set(crops)) == 4, 'release requires four distinct full-body poses'
        for other in (ROOT / 'art-review/redrawn').glob('*.png'):
            if 'tenten' not in other.name:
                assert hashlib.sha256(other.read_bytes()).hexdigest() != digest, 'old hero copied '+str(other)
        report['atlases'][key] = {'source': atlas['source'], 'sha256': digest, 'frames': len(atlas['frames']), 'bodyHeight': atlas['bodyHeight'], 'uniqueCrops': len(set(crops))}
    for key, entry in metadata.items():
        if key.startswith('tenten-'):
            assert 'tenten-' in entry['source'], 'Tenten animation refers to another hero'
            report['keys'].append(key)
    assert len(report['keys']) >= 10, 'missing common/action registrations'
    release = metadata['tenten-twin-release']
    source = mapping['tenten-twin-release']
    assert release['frames'] == [dict(f, bodyHeight=source['bodyHeight']) for f in source['frames']]
    assert release['bodyHeight'] == source['bodyHeight'] == source['frames'][0]['rect'][3]-4
    assert release['safeFrames'] == [0, 1, 2, 3]
    production = json.loads((ROOT / 'art-review/tenten-production-provenance.json').read_text('utf-8'))
    record = next(o for o in production['outputs'] if o['file'].endswith('tenten-twin-release-v1.png'))
    assert record['generator'] == 'built-in image_gen' and record['transparent_background'] is True
    assert record['prompt'].startswith('Use case: identity-preserve / precise-object-edit.')
    assert record['references'][0]['sha256'] == hashlib.sha256((ROOT / record['references'][0]['path']).read_bytes()).hexdigest()
    report['ok'] = True
    (OUT / 'art.json').write_text(json.dumps(report, indent=2), 'utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
