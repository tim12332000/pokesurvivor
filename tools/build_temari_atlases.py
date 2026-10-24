"""Register original Temari sheets; never rewrite or resample source pixels."""
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art-review'

# Anatomical standing height, excluding the fan. Keep this denominator for
# crouching/death poses so their shortened silhouettes stay shortened in game.
BODY_HEIGHTS = {'common': 235, 'skills': 275, 'kamatari': 155, 'spin': 325}
# Inspected sandal positions in source coordinates. The fan sometimes reaches
# below the feet, so alpha-bottom alone is unsuitable for the skills sheet.
SKILL_FEET = [(105, 329), (378, 329), (676, 329), (1004, 329),
              (100, 651), (381, 651), (680, 651), (1024, 651),
              (117, 973), (457, 973), (690, 973), (1040, 973),
              (106, 1297), (383, 1297), (704, 1297), (1062, 1297)]
KAMATARI_FEET = [(195, 400), (691, 391), (1116, 403), (1562, 380),
                 (219, 794), (643, 791), (1101, 792), (1545, 795)]
SPIN_FEET = [(164, 424), (600, 424), (1048, 424), (1538, 424),
             (305, 820), (715, 820), (1163, 820), (1615, 820)]


def cuts(mask, count, vertical):
    """Find low-alpha gutters, allowing wide fan poses to shift cell edges."""
    length = mask.height if vertical else mask.width
    projection = [sum(mask.crop((0, p, mask.width, p + 1)).getdata()) if vertical
                  else sum(mask.crop((p, 0, p + 1, mask.height)).getdata()) for p in range(length)]
    result = [0]
    for n in range(1, count):
        expected = length * n / count
        margin = length / count * .32
        candidates = range(max(result[-1] + 1, int(expected - margin)), min(length, int(expected + margin)))
        cut = min(candidates, key=lambda p: (sum(projection[max(0, p - 2):p + 3]), abs(p - expected)))
        if projection[cut]:
            raise ValueError(f'No transparent gutter near {expected}: would cut visible pixels')
        result.append(cut)
    return result + [length]


def register(name, rows):
    version = 2 if name == 'kamatari' else 1
    source = ART / 'redrawn' / f'temari-{name}-v{version}.png'
    image = Image.open(source).convert('RGBA')
    alpha = image.getchannel('A')
    if alpha.getextrema()[0] != 0 or alpha.getextrema()[1] < 180:
        raise ValueError(f'{source}: missing transparent background or solid body')
    # Very faint generation halos do not determine cell boundaries.
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
                raise ValueError(f'{name}: empty frame {row * 4 + col}')
            left, top = cell[0] + box[0], cell[1] + box[1]
            right, bottom = cell[0] + box[2], cell[1] + box[3]
            solid = alpha.crop((left, top, right, bottom)).point(lambda a: 255 if a >= 180 else 0)
            foot_y = solid.getbbox()[3] - 1
            feet = solid.crop((0, max(0, foot_y - 8), solid.width, foot_y + 1)).getbbox()
            anchor = [(feet[0] + feet[2]) / 2, foot_y]
            index = row * 4 + col
            if name == 'skills':
                anchor = [SKILL_FEET[index][0] - left, SKILL_FEET[index][1] - top]
            elif name == 'kamatari':
                # Blade wind arcs extend below paws in the spinning frames.
                anchor = [KAMATARI_FEET[index][0] - left, KAMATARI_FEET[index][1] - top]
            elif name == 'spin':
                # Center of the grounded sandal pair, not the fan silhouette.
                anchor = [SPIN_FEET[index][0] - left, SPIN_FEET[index][1] - top]
            elif name == 'common' and index >= 22:
                anchor[0] = (right - left) / 2
            if not (0 <= anchor[0] <= right - left and 0 <= anchor[1] <= bottom - top):
                raise ValueError(f'{name}/{index}: anchor outside crop: {anchor}')
            frames.append({'rect': [left, top, right - left, bottom - top], 'anchor': anchor})
    result = {'source': f'redrawn/{source.name}', 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'size': list(image.size), 'frames': frames}
    result['bodyHeight'] = BODY_HEIGHTS[name]
    return result


def main():
    sheets = {name: register(name, rows) for name, rows in
              [('common', 6), ('skills', 4), ('kamatari', 2), ('spin', 2)]}
    manifest = {'version': 3, 'physicalFrames': 56, 'characterFrames': 56, 'effectFrames': 0,
                'effectMethod': 'Procedural Canvas ribbons driven by combat time',
                'sheets': sheets, 'directionPolicy': {
        'common': 'Explicit front/back/side idle and run; mirror right-facing side for left; front/side hurt; side collapse.',
        'skills': 'Right-facing three-quarter actions; mirror horizontally for left; preserve fan and sandal anchor.',
        'kamatari': 'Right-facing ready/move and spinning slash poses; mirror travel for left.',
        'spin': 'Eight drawn turn poses in one 360-degree fan sweep; never rotate the character bitmap.'}}
    destination = ART / 'temari-frames.json'
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    provenance_path = ART / 'temari-provenance.json'
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    provenance['activeEffectMethod'] = 'Procedural Canvas; the old wind bitmap is archived, not loaded.'
    provenance['outputs'] = [{'source': sheet['source'], 'sha256': sheet['sha256'], 'size': sheet['size']}
                             for sheet in sheets.values()]
    provenance['outputs'].append({'source': destination.name,
                                  'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()})
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Registered 56 character frames; wind effects are procedural: {destination}')
    for name, sheet in sheets.items():
        print(name, sheet.get('bodyHeight', sheet.get('effectDiameter')), [frame['rect'] for frame in sheet['frames']])


if __name__ == '__main__':
    main()
