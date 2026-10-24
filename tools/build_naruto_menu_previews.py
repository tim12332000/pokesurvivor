"""Build lightweight full-body menu previews from reviewed idle frames."""
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'art-review'
OUTPUT = ROOT / '.omx/naruto/portraits'


def main():
    temari = json.loads((REVIEW / 'temari-frames.json').read_text('utf-8'))['sheets']['common']
    pain = json.loads((REVIEW / 'pain-frames.json').read_text('utf-8'))['bodies']['tendo']
    report = {}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for hero, sheet in [('temari', temari), ('pain', pain)]:
        frame = sheet['frames'][0]
        x, y, w, h = frame['rect']
        ax, ay = frame['anchor']
        source = REVIEW / sheet['source']
        scale = min(88 / w, 106 / h)
        size = (max(1, round(w * scale)), max(1, round(h * scale)))
        with Image.open(source) as atlas:
            crop = atlas.convert('RGBA').crop((x, y, x + w, y + h))
            crop = crop.resize(size, Image.Resampling.NEAREST)
        preview = Image.new('RGBA', (96, 112))
        preview.alpha_composite(crop, (round(48 - ax * size[0] / w), round(110 - ay * size[1] / h)))
        target = OUTPUT / f'{hero}.png'
        preview.save(target, optimize=True)
        report[hero] = {
            'source': source.relative_to(ROOT).as_posix(), 'rect': frame['rect'],
            'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'preview': target.relative_to(ROOT).as_posix(), 'size': [96, 112],
            'anchor': [48, 110], 'bytes': target.stat().st_size,
            'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        }
    (REVIEW / 'naruto-menu-previews.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({hero: spec['bytes'] for hero, spec in report.items()}))


if __name__ == '__main__':
    main()
