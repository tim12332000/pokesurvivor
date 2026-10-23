"""Register inspected 4x4 Pain sheets without modifying source image pixels."""
import hashlib
import json
from pathlib import Path
from statistics import median

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art-review'
PATHS = ('tendo', 'asura', 'animal', 'human', 'preta', 'naraka')


def cuts(mask, count, vertical):
    length = mask.height if vertical else mask.width
    projection = [sum(mask.crop((0, p, mask.width, p + 1)).getdata())
                  if vertical else sum(mask.crop((p, 0, p + 1, mask.height)).getdata())
                  for p in range(length)]
    result = [0]
    for n in range(1, count):
        expected = length * n / count
        margin = length / count * .20
        candidates = range(max(result[-1] + 1, int(expected - margin)), min(length, int(expected + margin)))
        result.append(min(candidates, key=lambda p: (sum(projection[max(0, p - 2):p + 3]), abs(p - expected))))
    return result + [length]


def register(path, rows=4):
    file = ART / 'redrawn' / f'pain-{path}-v1.png'
    image = Image.open(file).convert('RGBA')
    mask = image.getchannel('A').point(lambda a: 255 if a >= 24 else 0)
    if image.getchannel('A').getextrema()[0] != 0:
        raise ValueError(f'{file}: missing transparency')
    ys = cuts(mask, rows, True)
    frames = []
    for row in range(rows):
        stripe = mask.crop((0, ys[row], image.width, ys[row + 1]))
        xs = cuts(stripe, 4, False)
        for col in range(4):
            cell = (xs[col], ys[row], xs[col + 1], ys[row + 1])
            box = mask.crop(cell).getbbox()
            if not box:
                raise ValueError(f'{path}: empty cell {row}/{col}')
            left, top = cell[0] + box[0], cell[1] + box[1]
            right, bottom = cell[0] + box[2], cell[1] + box[3]
            solid = image.crop((left, top, right, bottom)).getchannel('A').point(lambda a: 255 if a >= 180 else 0)
            solid_box = solid.getbbox()
            foot_y = solid_box[3] - 1
            feet = solid.crop((0, max(0, foot_y - 8), solid.width, foot_y + 1)).getbbox()
            anchor_x = (feet[0] + feet[2]) / 2
            # Prone pose anchors use body center, so a collapsed actor stays on its ground position.
            if row == 3 and col >= 2:
                anchor_x = (right - left) / 2
            frames.append({'rect': [left, top, right - left, bottom - top], 'anchor': [anchor_x, foot_y]})
    animations = {
        'idle': {'frames': [0, 1], 'fps': 2, 'loop': True},
        'move': {'frames': [2, 3, 4, 5, 6, 7], 'fps': 10, 'loop': True},
        'strike': {'frames': [8, 9, 9, 0], 'fps': 10, 'loop': False},
        'special': {'frames': [10, 11, 11, 0], 'fps': 8, 'loop': False},
        'hurt': {'frames': [12, 12, 0], 'fps': 9, 'loop': False},
        'death': {'frames': [12, 13, 14, 15], 'fps': 7, 'loop': False},
    }
    return {'source': f'redrawn/{file.name}', 'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
            'size': list(image.size), 'bodyHeight': median(f['rect'][3] for f in frames[:2]),
            'directionPolicy': 'right three-quarter; explicit horizontal mirror for left; same side pose for vertical travel',
            'frames': frames, 'animations': animations}


if __name__ == '__main__':
    manifest = {'version': 1, 'physicalFrames': 104, 'bodies': {path: register(path) for path in PATHS}}
    summons = register('summons', rows=2)
    for path, offset in [('rhino', 0), ('king', 4)]:
        frames = summons['frames'][offset:offset + 4]
        # Rhino's first ready pose has an unusually narrow source gutter.
        # Only play the three complete gallop poses rather than clip its horn.
        sequence = {'frames': [1, 2, 3, 2] if path == 'rhino' else [0, 1, 2, 3], 'fps': 8, 'loop': True}
        manifest['bodies'][path] = {**summons, 'frames': frames, 'bodyHeight': frames[0]['rect'][3],
                                   'animations': {state: sequence for state in ('idle', 'move', 'special', 'strike')}}
    destination = ART / 'pain-frames.json'
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Registered {len(manifest["bodies"])} bodies / {manifest["physicalFrames"]} physical frames: {destination}')
