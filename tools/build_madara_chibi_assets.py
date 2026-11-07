"""Pack the reviewed chibi body sheets without changing Madara's other actors.

The source sheet grid is only a crop hint. Alpha gutters determine each crop;
one standing-height scale per family keeps crouches and fallen poses small.
Socket sites below are measured against each cropped source silhouette.
"""
from __future__ import annotations

import json

from build_madara_assets import ART, registered
from PIL import Image, ImageDraw


BODY_KEYS = ('taijutsu', 'bodyDirections', 'castingDirections', 'walkDirections')


def sites(mouth, palm, elbow, foot):
    return dict(mouth=mouth, palm=palm, elbow=elbow, foot=foot)


# All pairs are fractions of that frame's alpha crop, not of its grid cell.
COMMON = [
    sites((.81,.44),(.36,.73),(.32,.65),(.80,.96)),
    sites((.80,.44),(.88,.65),(.66,.64),(.82,.96)),
    sites((.80,.44),(.87,.65),(.67,.64),(.83,.96)),
    sites((.80,.43),(.88,.68),(.70,.63),(.75,.95)),
    sites((.81,.44),(.63,.61),(.42,.64),(.79,.96)),
    sites((.80,.44),(.80,.60),(.53,.63),(.80,.96)),
    sites((.77,.53),(.91,.49),(.72,.61),(.82,.96)),
    sites((.80,.44),(.34,.73),(.30,.65),(.80,.96)),
    sites((.70,.46),(.90,.66),(.70,.65),(.81,.96)),
    sites((.65,.46),(.95,.48),(.73,.57),(.75,.96)),
    sites((.62,.35),(.92,.40),(.76,.49),(.81,.96)),
    sites((.80,.45),(.90,.72),(.70,.64),(.82,.96)),
    sites((.64,.36),(.92,.56),(.74,.62),(.75,.96)),
    sites((.76,.51),(.72,.80),(.57,.75),(.78,.96)),
    sites((.53,.54),(.88,.61),(.73,.64),(.91,.84)),
    sites((.80,.85),(.94,.86),(.73,.81),(.10,.86)),
]

TAIJUTSU = [
    sites((.74,.48),(.87,.65),(.60,.64),(.84,.96)),
    # Leading palm surface at source (706,224), not glove interior (690,224).
    sites((.61,.48),(308/311,183/382),(.70,.55),(.72,.96)),
    sites((.76,.48),(.89,.64),(.33,.47),(.82,.96)),
    sites((.77,.48),(.69,.56),(.93,.54),(.83,.96)),
    sites((.76,.48),(.94,.59),(.72,.58),(.84,.96)),
    sites((.73,.48),(.89,.52),(.42,.59),(.73,.85)),
    sites((.60,.48),(.73,.52),(.38,.59),(.95,.58)),
    sites((.75,.48),(.87,.58),(.64,.55),(.94,.88)),
    sites((.75,.52),(.94,.69),(.71,.72),(.84,.96)),
    sites((.75,.48),(.88,.72),(.72,.65),(.83,.96)),
]

BODY_DIRECTIONS = [
    sites((.58,.46),(.33,.67),(.34,.62),(.84,.96)),
    sites((.61,.46),(.73,.57),(.35,.55),(.84,.96)),
    sites((.59,.46),(.12,.62),(.27,.55),(.37,.81)),
    sites((.60,.46),(.21,.72),(.23,.62),(.84,.96)),
    sites((.69,.39),(.89,.23),(.79,.40),(.84,.96)),
    sites((.66,.40),(.80,.33),(.92,.27),(.84,.96)),
    sites((.58,.42),(.72,.51),(.58,.44),(.91,.27)),
    sites((.61,.43),(.85,.67),(.81,.60),(.83,.96)),
]

CASTING_DIRECTIONS = [
    sites((.59,.43),(.56,.56),(.82,.58),(.83,.96)),
    sites((.56,.49),(.44,.54),(.85,.60),(.83,.96)),
    sites((.59,.43),(.90,.71),(.80,.63),(.83,.96)),
    sites((.76,.30),(.88,.39),(.86,.48),(.83,.96)),
    sites((.71,.24),(.78,.25),(.91,.41),(.83,.96)),
    sites((.67,.42),(.87,.68),(.82,.59),(.83,.96)),
]

WALK_DIRECTIONS = [
    sites((.55,.43),(.76,.68),(.79,.59),(.59,.96)),
    sites((.55,.43),(.30,.65),(.21,.59),(.42,.96)),
    sites((.55,.43),(.79,.68),(.79,.59),(.47,.96)),
    sites((.55,.43),(.29,.65),(.22,.59),(.66,.96)),
    sites((.67,.37),(.17,.70),(.18,.61),(.58,.96)),
    sites((.67,.37),(.13,.68),(.16,.59),(.59,.85)),
    sites((.67,.37),(.16,.70),(.19,.61),(.59,.96)),
    sites((.67,.37),(.13,.68),(.17,.59),(.59,.85)),
]

# Standing source silhouette heights, never per-frame height normalization.
FAMILIES = [
    ('taijutsu', 'madara-taijutsu-chibi-v1.png', 2, 5, 377, TAIJUTSU),
    ('bodyDirections', 'madara-body-directions-chibi-v1.png', 2, 4, 373, BODY_DIRECTIONS),
    ('castingDirections', 'madara-casting-directions-chibi-v1.png', 2, 3, 439, CASTING_DIRECTIONS),
    ('walkDirections', 'madara-walk-directions-chibi-v1.png', 2, 4, 418, WALK_DIRECTIONS),
]


def main():
    path = ART / 'frames.json'
    metadata = json.loads(path.read_text('utf-8'))
    untouched = {key: value for key, value in metadata['sheets'].items() if key not in BODY_KEYS}
    common = registered('madara-actions-chibi-v1.png', 4, 4, 261, 128,
                        [frame['name'] for frame in metadata['frames']], COMMON)
    metadata.update(common)
    metadata['directions'] = 'left/right chibi body; authored front/back combat, casting and walking'
    metadata['bodyStyle'] = 'large-head compact chibi, matched to current Naruto sprites'
    for key, source, rows, columns, height, points in FAMILIES:
        names = [frame['name'] for frame in metadata['sheets'][key]['frames']]
        metadata['sheets'][key] = registered(source, rows, columns, height, 128, names, points)
    # Rear rising kick is airborne. Its virtual floor stays below the lower
    # sole, matching the existing jump pose rather than pinning the foot down.
    metadata['sheets']['bodyDirections']['frames'][6]['anchor'][1] += round(32 * 128 / 373, 3)
    # Never invoke the legacy full-actor builder: Susanoo, fire, rock and wood
    # sheets remain byte-for-byte intact.
    assert {key: metadata['sheets'][key] for key in untouched} == untouched
    path.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    image = Image.open(ART / metadata['source']).convert('RGBA')
    preview = Image.new('RGB', (640, 320), '#49713f')
    draw = ImageDraw.Draw(preview)
    for index, frame in enumerate(metadata['frames']):
        x, y, w, h = frame['rect']
        sprite = image.crop((x, y, x + w, y + h)).resize((round(w / 2), round(h / 2)), Image.Resampling.NEAREST)
        column, row = index % 8, index // 8
        preview.paste(sprite, (column * 80 + 40 - round(frame['anchor'][0] / 2),
                               row * 160 + 105 - round(frame['anchor'][1] / 2)), sprite)
        draw.text((column * 80 + 2, row * 160 + 120), frame['name'], fill='white')
    preview.save(ART / 'game-size-contact.png')
    print(json.dumps({'bodySources': [metadata['source']] +
                     [metadata['sheets'][key]['source'] for key in BODY_KEYS],
                     'unchangedOtherSheets': sorted(untouched)}, indent=2))


if __name__ == '__main__':
    main()
