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
    for key, minimum in [('tenten-common', 32), ('tenten-skills', 16)]:
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
        assert len(set(crops)) >= minimum*.7, 'repeated static body posing as action atlas'
        for other in (ROOT / 'art-review/redrawn').glob('*.png'):
            if 'tenten' not in other.name:
                assert hashlib.sha256(other.read_bytes()).hexdigest() != digest, 'old hero copied '+str(other)
        report['atlases'][key] = {'source': atlas['source'], 'sha256': digest, 'frames': len(atlas['frames']), 'bodyHeight': atlas['bodyHeight'], 'uniqueCrops': len(set(crops))}
    for key, entry in metadata.items():
        if key.startswith('tenten-'):
            assert 'tenten-' in entry['source'], 'Tenten animation refers to another hero'
            report['keys'].append(key)
    assert len(report['keys']) >= 10, 'missing common/action registrations'
    report['ok'] = True
    (OUT / 'art.json').write_text(json.dumps(report, indent=2), 'utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
