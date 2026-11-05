"""Register the generated Madara sheet without resampling its source pixels."""
import hashlib
import json
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art-review' / 'madara'


def cuts(mask, count, vertical):
    length = mask.height if vertical else mask.width
    projection = [sum(mask.crop((0, p, mask.width, p + 1) if vertical else
                               (p, 0, p + 1, mask.height)).getdata()) for p in range(length)]
    result = [0]
    for n in range(1, count):
        center = length * n / count
        candidates = range(max(result[-1] + 1, int(center - length / count * .22)),
                           min(length, int(center + length / count * .22)))
        result.append(min(candidates, key=lambda p: (
            sum(projection[max(0, p - 3):p + 4]), abs(p - center))))
    return result + [length]


def main():
    source = ART / 'madara-actions-v1.png'
    image = Image.open(source).convert('RGBA')
    alpha = image.getchannel('A')
    assert alpha.getextrema() == (0, 255), 'Expected real transparency'
    mask = alpha.point(lambda value: 255 if value >= 24 else 0)
    ys = cuts(mask, 4, True)
    frames = []
    names = ['idle', 'step-left', 'step-right', 'ready', 'seal-start', 'seal-hold',
             'fire-breath', 'recover', 'arm-back', 'command', 'summon', 'finish',
             'flinch', 'hurt', 'fall', 'faint']
    for row in range(4):
        stripe = mask.crop((0, ys[row], image.width, ys[row + 1]))
        xs = cuts(stripe, 4, False)
        for column in range(4):
            cell = (xs[column], ys[row], xs[column + 1], ys[row + 1])
            bounds = mask.crop(cell).getbbox()
            assert bounds, f'Empty frame {row}, {column}'
            left, top = cell[0] + bounds[0], cell[1] + bounds[1]
            right, bottom = cell[0] + bounds[2], cell[1] + bounds[3]
            crop = image.crop((left, top, right, bottom))
            solid = crop.getchannel('A').point(lambda value: 255 if value >= 180 else 0)
            box = solid.getbbox()
            foot_y = box[3] - 1
            feet = solid.crop((0, max(0, foot_y - 7), crop.width, foot_y + 1)).getbbox()
            frames.append({'name': names[len(frames)], 'rect': [left, top, right-left, bottom-top],
                           'anchor': [(feet[0]+feet[2])/2, foot_y]})
    body_height = median(frame['rect'][3] for frame in frames[:3])
    metadata = {'source': source.name, 'bodyHeight': body_height, 'directions': 'right; left mirrored; side view for up/down',
                'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'frames': frames}
    (ART / 'frames.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    preview = Image.new('RGB', (640, 320), '#49713f')
    draw = ImageDraw.Draw(preview)
    for index, frame in enumerate(frames):
        x, y, w, h = frame['rect']
        scale = 64 / body_height
        sprite = image.crop((x, y, x+w, y+h)).resize((round(w*scale), round(h*scale)), Image.Resampling.NEAREST)
        column, row = index % 8, index // 8
        preview.paste(sprite, (column*80+40-round(frame['anchor'][0]*scale), row*160+105-round(frame['anchor'][1]*scale)), sprite)
        draw.text((column*80+2, row*160+120), frame['name'], fill='white')
    preview.save(ART / 'game-size-contact.png')
    print(json.dumps({'frames': len(frames), 'bodyHeight': body_height, 'sha256': metadata['sha256']}))


if __name__ == '__main__':
    main()
