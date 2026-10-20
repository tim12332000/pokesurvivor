"""Register original atlases without changing any source-image pixels.

Run from any directory with Python/Pillow. Alpha projections find the actual
gaps, since generated art is not registered to mathematically uniform cells.
All poses in an atlas use one body scale; crouching never enlarges the head.
"""
import json
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art-review'
OUT = ROOT / '.omx/state/redrawn-heroes'


def cuts(mask, count, vertical):
    length = mask.height if vertical else mask.width
    projection = [sum(mask.crop((0, p, mask.width, p + 1)).getdata())
                  if vertical else sum(mask.crop((p, 0, p + 1, mask.height)).getdata())
                  for p in range(length)]
    result = [0]
    for n in range(1, count):
        expected = length * n / count
        margin = length / count * .20
        candidates = range(max(result[-1] + 1, int(expected - margin)),
                           min(length, int(expected + margin)))
        # A clear run of pixels beats a single coincidental transparent pixel.
        result.append(min(candidates, key=lambda p: (
            sum(projection[max(0, p - 2):p + 3]), abs(p - expected))))
    return result + [length]


def atlas(name, rows):
    image = Image.open(ART / 'redrawn' / name).convert('RGBA')
    alpha = image.getchannel('A')
    mask = alpha.point(lambda a: 255 if a >= 24 else 0)
    ys = cuts(mask, rows, True)
    frames = []
    for row in range(rows):
        stripe = mask.crop((0, ys[row], image.width, ys[row + 1]))
        xs = cuts(stripe, 4, False)
        for col in range(4):
            cell = (xs[col], ys[row], xs[col + 1], ys[row + 1])
            box = mask.crop(cell).getbbox()
            if not box:
                raise ValueError(f'Empty {name} row {row} col {col}')
            left = max(cell[0], cell[0] + box[0] - 2)
            top = max(cell[1], cell[1] + box[1] - 2)
            right = min(cell[2], cell[0] + box[2] + 2)
            bottom = min(cell[3], cell[1] + box[3] + 2)
            crop = image.crop((left, top, right, bottom))
            solid = crop.getchannel('A').point(lambda a: 255 if a >= 180 else 0)
            solid_box = solid.getbbox()
            foot_y = solid_box[3] - 1
            feet = solid.crop((0, max(0, foot_y - 8), crop.width, foot_y + 1)).getbbox()
            anchor_x = (feet[0] + feet[2]) / 2
            frames.append({'rect': [left, top, right - left, bottom - top],
                           'anchor': [anchor_x, foot_y], 'atlasIndex': row * 4 + col})
    return {'source': 'redrawn/' + name, 'frames': frames}, image


def hair_width(image, frame):
    """Head-size reference excluding effects and the orange clothing palette."""
    x, y, w, h = frame['rect']
    crop = image.crop((x, y, x + w, y + h))
    points = [(px, py) for py in range(h) for px in range(w)
              if (lambda c: c[3] > 180 and c[0] > 180 and c[1] > 145
                  and c[2] < 110 and c[1] > c[0] * .75)(crop.getpixel((px, py)))]
    if not points:
        raise ValueError('Cannot establish Naruto hair reference')
    return max(p[0] for p in points) - min(p[0] for p in points) + 1


def sequence(source, indices, mirrors=()):
    frames = []
    for n, index in enumerate(indices):
        frame = dict(source['frames'][index])
        frame['bodyHeight'] = source['bodyHeight']
        if n in mirrors:
            frame['mirror'] = True
        frames.append(frame)
    return {'source': source['source'], 'bodyHeight': source['bodyHeight'],
            'safeFrames': list(range(len(frames))), 'frames': frames}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = {}
    images = {}
    for hero in ('naruto', 'sasuke'):
        for kind, rows in (('common', 8), ('skills', 4)):
            key = hero + '-' + kind
            version = 'v2' if kind == 'skills' else 'v1'
            sources[key], images[key] = atlas(key + '-' + version + '.png', rows)
    sources['one-tail'], images['one-tail'] = atlas('one-tail-v2.png', 6)
    # Standing reference is measured once, never independently per pose.
    for hero in ('naruto', 'sasuke'):
        common = sources[hero + '-common']
        common['bodyHeight'] = median(f['rect'][3] - 4 for f in common['frames'][:6])
    base = sources['naruto-common']
    base_head = median(hair_width(images['naruto-common'], f) for f in base['frames'][:2])
    # Standing skill poses must retain their physical body height. Head/body
    # proportions are an artwork QA concern, not a per-pose scale correction.
    sources['naruto-skills']['bodyHeight'] = median(
        f['rect'][3] - 4 for f in sources['naruto-skills']['frames'][:4])
    # Sasuke's upright recovery shares the common standing silhouette.
    sasuke_skills = sources['sasuke-skills']
    sasuke_skills['bodyHeight'] = median(sasuke_skills['frames'][i]['rect'][3] - 4
                                         for i in (3, 7, 11, 15))
    form_head = median(hair_width(images['one-tail'], f)
                       for f in sources['one-tail']['frames'][:4])
    sources['one-tail']['bodyHeight'] = round(base['bodyHeight'] * form_head / base_head, 2)
    assets = {}
    for hero in ('naruto', 'sasuke'):
        common = sources[hero + '-common']
        sets = {
            'movement': (list(range(8, 12)) + list(range(16, 20))
                         + list(range(12, 16)) * 2, range(8, 12)),
            'idle': ([0, 1, 0, 1, 2, 3, 2, 3] + [4, 5, 4, 5] * 2, range(8, 12)),
            'hurt': ([20, 21, 0, 1, 22, 23, 2, 3] + [6, 7, 4, 5] * 2, range(8, 12)),
            'death': (list(range(24, 28)), ()),
            'attack': (list(range(28, 32)), ()),
        }
        for kind, (indices, mirrors) in sets.items():
            entry = sequence(common, indices, mirrors)
            if kind in ('movement', 'idle', 'hurt'):
                entry['directions'] = {'down': 0, 'up': 1, 'left': 2, 'right': 3}
            assets[hero + '-' + kind] = entry
    for hero, kinds in (('naruto', ('clones', 'rasengan', 'throw', 'cloak')),
                        ('sasuke', ('chidori', 'fireball', 'throw', 'sword'))):
        for row, kind in enumerate(kinds):
            assets[hero + '-' + kind] = sequence(sources[hero + '-skills'], range(row * 4, row * 4 + 4))
    (ART / 'animation-assets.json').write_text(json.dumps(assets, indent=2) + '\n', encoding='utf-8')
    form = sources['one-tail']
    animations = {}
    for kind, indices, fps, loop in (
            ('idle', range(4), 7, True), ('walk', range(4, 8), 10, True),
            ('run', range(4, 8), 12, True), ('hurt', range(8, 12), 10, False),
            ('attack', range(12, 16), 12, False), ('throw', range(20, 24), 12, False),
            ('activation', range(4), 9, False), ('rasenganCharge', (16, 17), 9, False),
            ('rasenganDash', (18,), 12, True), ('rasenganRelease', (18,), 12, False),
            ('rasenganRecover', (19,), 10, False)):
        animations[kind] = {'frames': sequence(form, indices)['frames'], 'fps': fps, 'loop': loop}
    form_json = {'source': form['source'], 'bodyHeight': form['bodyHeight'],
                 'facing': 'right', 'animations': animations}
    (ART / 'kyuubi-frames.json').write_text(json.dumps(form_json, indent=2) + '\n', encoding='utf-8')
    (ART / 'redrawn/atlas-map.json').write_text(json.dumps(sources, indent=2) + '\n', encoding='utf-8')
    # Review every physical frame at the exact same world scale as the game.
    contact = Image.new('RGB', (1120, 2100), '#315f32')
    draw = ImageDraw.Draw(contact)
    top = 0
    for key, source in sources.items():
        draw.text((8, top + 5), f"{key} / fixed bodyHeight {source['bodyHeight']}", fill='white')
        top += 26
        for i, frame in enumerate(source['frames']):
            x, y, w, h = frame['rect']
            scale = 64 / source['bodyHeight']
            crop = images[key].crop((x, y, x + w, y + h))
            sprite = crop.resize((round(w * scale), round(h * scale)), Image.Resampling.NEAREST)
            px = 15 + (i % 8) * 138
            py = top + (i // 8) * 100
            draw.line((px, py + 76, px + 125, py + 76), fill='#6b9260')
            ax, ay = frame['anchor']
            contact.paste(sprite, (round(px + 58 - ax * scale), round(py + 76 - ay * scale)), sprite)
            draw.text((px, py + 81), str(i), fill='white')
        top += ((len(source['frames']) + 7) // 8) * 100 + 14
    contact.crop((0, 0, 1120, top)).save(OUT / 'contact.png')
    print(json.dumps({k: {'bodyHeight': v['bodyHeight'], 'frames': len(v['frames'])}
                      for k, v in sources.items()}, indent=2))


if __name__ == '__main__':
    main()
