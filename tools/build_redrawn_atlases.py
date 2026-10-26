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


def atlas(name, rows, columns=4):
    image = Image.open(ART / 'redrawn' / name).convert('RGBA')
    alpha = image.getchannel('A')
    mask = alpha.point(lambda a: 255 if a >= 24 else 0)
    ys = cuts(mask, rows, True)
    frames = []
    for row in range(rows):
        stripe = mask.crop((0, ys[row], image.width, ys[row + 1]))
        xs = cuts(stripe, columns, False)
        for col in range(columns):
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
                           'anchor': [anchor_x, foot_y], 'atlasIndex': row * columns + col})
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


def lee_lotus_hold():
    """Authored grip/inverted hold poses; never scale each crouched crop to standing."""
    source, image = atlas('lee-front-lotus-hold-v1.png', 2)
    # Hair-band widths: new 112px, existing Lotus 84px at a 248px body scale.
    source['bodyHeight'] = 330.67
    points = ((403, 220), (769, 251), (1177, 257), (1674, 206),
              (403, 653), (768, 681), (1175, 687), (1674, 639))
    for frame, point in zip(source['frames'], points):
        frame['grip'] = [point[0] - frame['rect'][0], point[1] - frame['rect'][1]]
        frame['hand'] = list(frame['grip'])
    assets = {'lee-lotus-hold': sequence(source, range(4)),
              'lee-opened-lotus-hold': sequence(source, range(4, 8))}
    return source, image, assets


def lee_whirlwind_air():
    """Eight authored aerial-kick poses per form, sharing a fixed body scale."""
    source, image = atlas('lee-whirlwind-air-v1.png', 4)
    # Hair-band widths: new 87px, existing Whirlwind 82px at 248px body scale.
    source['bodyHeight'] = 263.12
    feet = ((253, 325), (527, 266), (917, 296), (1125, 318),
            (310, 502), (625, 512), (891, 613), (1181, 616),
            (253, 910), (527, 853), (920, 879), (1124, 903),
            (309, 1067), (630, 1088), (891, 1187), (1181, 1187))
    for frame, point in zip(source['frames'], feet):
        frame['foot'] = [point[0] - frame['rect'][0], point[1] - frame['rect'][1]]
    assets = {'lee-whirlwind-air': sequence(source, range(8)),
              'lee-opened-whirlwind-air': sequence(source, range(8, 16))}
    return source, image, assets


def lee_neck_to_feet(image, frame):
    """Raised hair adds height after opening the gates, not a smaller body."""
    x, y, w, h = frame['rect']
    crop = image.crop((x, y, x + w, y + h))
    green_rows = [py for py in range(h) for px in range(w)
                  if (lambda c: c[3] > 180 and c[1] > 45
                      and c[1] > c[0] * 1.3 and c[1] > c[2] * 1.15)(
                          crop.getpixel((px, py)))]
    if not green_rows:
        raise ValueError('Cannot establish Lee green jumpsuit reference')
    return frame['anchor'][1] - min(green_rows)



def write_registered_entries(path, entries):
    """Retain untouched/custom registrations and their numeric/key formatting."""
    previous = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    for key, value in entries.items():
        if key not in previous or previous[key] != value:
            previous[key] = value
    path.write_text(json.dumps(previous, indent=2) + '\n', encoding='utf-8')


def register_menu_portraits(assets, images):
    """Small exact-pixel crops keep the roster independent of gameplay atlases."""
    path = ROOT / '.omx/naruto/sprites.json'
    metadata = json.loads(path.read_text('utf-8'))
    folder = ROOT / '.omx/naruto/portraits'
    folder.mkdir(parents=True, exist_ok=True)
    for slug, hero in [('naruto','naruto'),('sasuke','sasuke'),('rock-lee','lee'),('gaara','gaara'),('tenten','tenten')]:
        frame = assets[hero+'-idle']['frames'][0]
        x, y, w, h = frame['rect']
        name = hero+'.png'
        images[hero+'-common'].crop((x,y,x+w,y+h)).save(folder/name, optimize=True)
        metadata[slug]['preview'] = {'source':'.omx/naruto/portraits/'+name,
                                     'w':w,'h':h,'ax':frame['anchor'][0],'ay':frame['anchor'][1]}
    path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (path.parent/'sprites-data.js').write_text('window.PS_NARUTO_SPRITES = '+json.dumps(metadata,ensure_ascii=False)+';\n',encoding='utf-8')


def register_tenten_fallback(common):
    """Keep the genuine new art available to portraits and the source renderer."""
    path = ROOT / '.omx/naruto/sprites.json'
    metadata = json.loads(path.read_text(encoding='utf-8'))
    rects = lambda indices: [common['frames'][i]['rect'] for i in indices]
    sides = lambda indices: {'default': rects(indices), 'right': rects(indices),
                             'left': rects(indices)}
    metadata['tenten'] = {
        'file': 'tenten-common-v1.png',
        'source': 'art-review/' + common['source'],
        'bodyHeight': common['bodyHeight'],
        'frames': {'down': rects((0, 1)), 'up': rects((2, 3)),
                   'right': rects((4, 5)), 'left': rects((4, 5))},
        'mirror': ['left'],
        'directionNote': 'Genuine front/back idle, walk and hurt views; left is mirrored from right. Side-only throws and death explicitly reuse right-facing poses for up/down.',
        'animations': {
            'Idle': {'frames': {'down': rects((0, 1)), 'up': rects((2, 3)),
                               'right': rects((4, 5)), 'left': rects((4, 5))}, 'mirror': ['left'], 'durations': [12, 12]},
            'Walk': {'frames': {'down': rects(range(8, 12)), 'up': rects(range(16, 20)),
                               'right': rects(range(12, 16)), 'left': rects(range(12, 16))}, 'mirror': ['left'], 'durations': [6] * 4},
            'Hurt': {'frames': {'down': rects((20, 21)), 'up': rects((22, 23)),
                               'right': rects((6, 7)), 'left': rects((6, 7))}, 'mirror': ['left']},
            **{name: {'frames': sides(range(28, 32)), 'mirror': ['left'], 'durations': [5] * 4,
                       'directionFallback': {'up': 'right', 'down': 'right'}}
               for name in ('Attack', 'Shoot', 'Charge')},
            'Faint': {'frames': sides(range(24, 28)), 'mirror': ['left'], 'durations': [10] * 4,
                      'directionFallback': {'up': 'right', 'down': 'right'}}
        }
    }
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (path.parent / 'sprites-data.js').write_text('window.PS_NARUTO_SPRITES = ' +
        json.dumps(metadata, ensure_ascii=False) + ';\n', encoding='utf-8')


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
    for kind, rows in (('common', 8), ('skills', 4)):
        key = 'lee-' + kind
        sources[key], images[key] = atlas(key + '-v1.png', rows)
        opened_key = 'lee-opened-' + kind
        sources[opened_key], images[opened_key] = atlas('lee-gates-' + kind + '-v1.png', rows)
    for hero in ('gaara', 'tenten'):
        for kind, rows in (('common', 8), ('skills', 4)):
            key = hero + '-' + kind
            sources[key], images[key] = atlas(key + '-v1.png', rows)
    sources['lee-bandage'], images['lee-bandage'] = atlas('lee-bandage-v1.png', 2)
    release, images['tenten-twin-release'] = atlas('tenten-twin-release-v1.png', 2, columns=2)
    sources['tenten-twin-release'] = release
    # One standing reference for the complete toss/rise/apex/landing sequence.
    release['bodyHeight'] = release['frames'][0]['rect'][3] - 4
    for frame, left, right in zip(release['frames'],
                                  ((200,342),(792,192),(156,861),(785,955)),
                                  ((562,323),(1110,260),(558,901),(1138,1045))):
        frame['scrollLeft'] = [left[0]-frame['rect'][0], left[1]-frame['rect'][1]]
        frame['scrollRight'] = [right[0]-frame['rect'][0], right[1]-frame['rect'][1]]
        frame['hand'] = list(frame['scrollRight'])
    # Measured cloth exit at the wrist/leading fist in each genuine pose.
    for frame, point in zip(sources['lee-bandage']['frames'],
                            ((294,266),(838,230),(1170,248),(1635,244),
                             (295,700),(838,660),(1170,677),(1637,678))):
        frame['hand'] = [point[0]-frame['rect'][0], point[1]-frame['rect'][1]]
    # Measured points in the original atlases, never an assumed global actor.
    for frame, point in zip(sources['tenten-common']['frames'][28:32],
                            ((171,1668),(398,1663),(633,1654),(795,1667))):
        frame['hand'] = [point[0]-frame['rect'][0], point[1]-frame['rect'][1]]
    for frame, point in zip(sources['tenten-skills']['frames'],
                            ((207,192),(617,146),(833,200),(1139,183),
                             (247,470),(616,453),(881,579),(1145,496),
                             (263,778),(594,758),(929,780),(1175,829),
                             (232,1067),(519,1106),(835,1110),(1158,1123))):
        frame['hand'] = [point[0]-frame['rect'][0], point[1]-frame['rect'][1]]
    for frame, left, right in zip(sources['tenten-skills']['frames'][8:12],
                                  ((53,735),(382,708),(696,742),(1084,800)),
                                  ((263,751),(594,728),(929,750),(1175,815))):
        frame['scrollLeft'] = [left[0]-frame['rect'][0], left[1]-frame['rect'][1]]
        frame['scrollRight'] = [right[0]-frame['rect'][0], right[1]-frame['rect'][1]]
    # Standing reference is measured once, never independently per pose.
    for hero in ('naruto', 'sasuke', 'lee', 'lee-opened', 'gaara', 'tenten'):
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
    # Whirlwind and gates finish upright. Both lotus rows finish in a low
    # landing, so those poses cannot define the fixed standing body scale.
    for hero in ('lee', 'lee-opened'):
        lee_skills = sources[hero + '-skills']
        lee_skills['bodyHeight'] = median(lee_skills['frames'][i]['rect'][3] - 4
                                        for i in (3, 11))
    # All four sand gestures recover upright. Effects must remain detached
    # from the actor's head-to-feet scale reference.
    sources['gaara-skills']['bodyHeight'] = median(
        sources['gaara-skills']['frames'][i]['rect'][3] - 4 for i in (3, 7, 11, 15))
    sources['tenten-skills']['bodyHeight'] = median(
        sources['tenten-skills']['frames'][i]['rect'][3] - 4 for i in (3, 7, 15))
    # Preserve the original body's scale beneath the added hair spikes. Use
    # just the same upright references in each atlas, never individual poses.
    for kind, indices in (('common', (0, 1)), ('skills', (3, 11))):
        base_lee = sources['lee-' + kind]
        opened_lee = sources['lee-opened-' + kind]
        base_body = median(lee_neck_to_feet(images['lee-' + kind], base_lee['frames'][i])
                           for i in indices)
        opened_body = median(lee_neck_to_feet(images['lee-opened-' + kind], opened_lee['frames'][i])
                             for i in indices)
        opened_lee['bodyHeight'] = round(base_lee['bodyHeight'] * opened_body / base_body, 2)
    form_head = median(hair_width(images['one-tail'], f)
                       for f in sources['one-tail']['frames'][:4])
    sources['one-tail']['bodyHeight'] = round(base['bodyHeight'] * form_head / base_head, 2)
    assets = {}
    for hero in ('naruto', 'sasuke', 'lee', 'lee-opened', 'gaara', 'tenten'):
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
                        ('sasuke', ('chidori', 'fireball', 'throw', 'sword')),
                        ('lee', ('whirlwind', 'lotus', 'gates', 'reverse')),
                        ('lee-opened', ('whirlwind', 'lotus', 'gates', 'reverse')),
                        ('gaara', ('sand-burst', 'coffin', 'shield', 'tsunami')),
                        ('tenten', ('fuma', 'tags', 'twin', 'mastery'))):
        for row, kind in enumerate(kinds):
            assets[hero + '-' + kind] = sequence(sources[hero + '-skills'], range(row * 4, row * 4 + 4))
    for hero, indices in (('lee', range(4)), ('lee-opened', range(4, 8))):
        bandage = sources['lee-bandage']
        base_common = sources[hero + '-common']
        neck = lee_neck_to_feet(images['lee-bandage'], bandage['frames'][indices[-1]])
        base_neck = median(lee_neck_to_feet(images[hero + '-common'], f) for f in base_common['frames'][4:6])
        bandage['bodyHeight'] = round(base_common['bodyHeight'] * neck / base_neck, 2)
        assets[hero + '-bandage'] = sequence(bandage, indices)
    # The atlas has one common body scale; the alternate head adds height.
    sources['lee-bandage']['bodyHeight'] = assets['lee-bandage']['bodyHeight']
    hold, hold_image, hold_assets = lee_lotus_hold()
    sources['lee-front-lotus-hold'] = hold
    images['lee-front-lotus-hold'] = hold_image
    assets.update(hold_assets)
    whirlwind, whirlwind_image, whirlwind_assets = lee_whirlwind_air()
    sources['lee-whirlwind-air'] = whirlwind
    images['lee-whirlwind-air'] = whirlwind_image
    assets.update(whirlwind_assets)
    assets['gaara-throw'] = sequence(sources['gaara-common'], range(28, 32))
    assets['tenten-throw'] = sequence(sources['tenten-common'], range(28, 32))
    assets['tenten-twin-release'] = sequence(release, range(4))
    for key, entry in assets.items():
        if key.startswith('tenten-') and 'directions' not in entry:
            entry.update(facing='right', directionFallback={'up': 'right', 'down': 'right'},
                         mirrorDirections=['left'])
    register_tenten_fallback(sources['tenten-common'])
    register_menu_portraits(assets, images)
    write_registered_entries(ART / 'animation-assets.json', assets)
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
    write_registered_entries(ART / 'redrawn/atlas-map.json', sources)
    # Review every physical frame at the exact same world scale as the game.
    contact_height = sum(40 + ((len(source['frames']) + 7) // 8) * 100
                         for source in sources.values())
    contact = Image.new('RGB', (1120, contact_height), '#315f32')
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
