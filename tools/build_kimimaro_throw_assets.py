"""Pack authored throwing poses into the existing Kimimaro atlas dimensions."""
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art-review'
SOURCE = ART / 'redrawn/kimimaro-throw-generated-v1.png'
KEYS = ['throwWindup', 'throwRelease', 'throwRecover']
HANDS = [[(136, 327), (473, 313), (360, 424)],
         [(153, 266), (493, 258), (385, 397)]]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    meta_path = ART / 'kimimaro-frames.json'
    meta = json.loads(meta_path.read_text(encoding='utf8'))
    generated = Image.open(SOURCE).convert('RGBA')
    assert generated.size == (1536, 1024)
    outputs = {}
    for row, form in enumerate(['normal', 'curse']):
        sheet = meta['sheets'][form]
        # Always rebuild from the original frames, preserving their pixels and anchors.
        original = Image.open(ART / f'redrawn/kimimaro-{form}-v1.png').convert('RGBA')
        current = Image.open(ART / sheet['source']).convert('RGBA')
        sprites = []
        for key, frame in sheet['frames'].items():
            if key in KEYS:
                continue
            x, y, w, h = frame['rect']
            sprites.append((key, current.crop((x, y, x+w, y+h)), dict(frame)))
        for col, key in enumerate(KEYS):
            cell = generated.crop((col*512, row*512, (col+1)*512, (row+1)*512))
            alpha = cell.getchannel('A').point(lambda value: 255 if value >= 128 else 0)
            cell.putalpha(alpha)
            box = cell.getbbox()
            assert box
            sprite = cell.crop(box)
            scale = 84 / sprite.height
            size = (round(sprite.width*scale), 84)
            sprite = sprite.resize(size, Image.Resampling.NEAREST)
            hx, hy = HANDS[row][col]
            frame = {'rect': [0, 0, *size],
                     'anchor': [round((256-box[0])*scale), 84],
                     'hand': [round((hx-box[0])*scale), round((hy-box[1])*scale)],
                     'bodyHeight': 92, 'originalBodyHeight': 300}
            sprites.append((key, sprite, frame))
        atlas = Image.new('RGBA', original.size)
        x, y, row_height = 2, 2, 0
        frames = {}
        for key, sprite, frame in sprites:
            if x + sprite.width + 2 > atlas.width:
                x, y, row_height = 2, y + row_height + 2, 0
            assert y + sprite.height + 2 <= atlas.height, (form, key, 'atlas overflow')
            atlas.alpha_composite(sprite, (x, y))
            frame['rect'] = [x, y, *sprite.size]
            frames[key] = frame
            x += sprite.width + 2
            row_height = max(row_height, sprite.height)
        target = ART / f'redrawn/kimimaro-{form}-throw-v2.png'
        atlas.save(target, optimize=True)
        sheet.update(source='redrawn/' + target.name, frames=frames,
                     sha256=digest(target), bytes=target.stat().st_size)
        outputs[form] = {'source': sheet['source'], 'sha256': sheet['sha256']}
    provenance = ART / 'redrawn/kimimaro-throw-provenance.json'
    provenance.write_text(json.dumps({
        'generator': 'image_gen', 'source': SOURCE.name, 'sha256': digest(SOURCE),
        'references': [{'source': f'kimimaro-{form}-v1.png',
                        'sha256': digest(ART / f'redrawn/kimimaro-{form}-v1.png')}
                       for form in ['normal', 'curse']],
        'prompt': 'Six transparent full-body Kimimaro poses in a 3x2 grid: normal and curse forms, facing right; side windup with throwing arm pulled back, open-hand release, and follow-through recovery. Match existing reference proportions, identity, clothes, outline and style. Empty hands, no weapons, no trails, no labels. 1536x1024.',
        'packing': 'Crop authored cells, threshold alpha, nearest-neighbor normalize to 84px, repack original unchanged frames within existing 560x660 atlases.',
        'outputs': outputs
    }, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    meta.setdefault('sources', {})['throwProvenance'] = 'redrawn/' + provenance.name
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    return outputs


if __name__ == '__main__':
    print(json.dumps(build()))
