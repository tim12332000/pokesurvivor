from pathlib import Path
import json

root = Path(__file__).resolve().parent.parent
pixel = {}
for file in sorted((root / '.omx/digimon/pixel').glob('*.json')):
    metadata = json.loads(file.read_text(encoding='utf-8-sig'))
    if file.stem == 'greymon':
        # Visual review: source frames 0-2 face down-left, 3-5 face up-left,
        # 6-8 are front-facing idle/jump poses. Right views mirror the left art.
        rects = metadata.get('frame_rects', metadata.get('frames'))
        if rects is None:
            rects = metadata['alpha_bounds']
        normalized = []
        for box in rects:
            normalized.append([box['x'], box['y'], box['w'], box['h']] if isinstance(box, dict) else box)
        pixel[file.stem] = {'cell_width': 32, 'cell_height': 42, 'frame_count': 9,
            'frames_per_direction': 3, 'directions': ['down_left', 'down_right', 'up_left', 'up_right'],
            'scale': 1, 'anchor': [16, 41], 'frame_rects': normalized,
            'direction_frames': [[0,1,2],[0,1,2],[3,4,5],[3,4,5]], 'mirror_groups': [1,3], 'idle_frame': 6}
        continue
    assert metadata['frame_count'] == 12 and metadata['frames_per_direction'] == 3
    pixel[file.stem] = {key: metadata[key] for key in ['cell_width', 'cell_height', 'frame_count', 'frames_per_direction']}
    pixel[file.stem]['directions'] = metadata.get('directions', metadata.get('canonical_runtime_order', ['down_left', 'down_right', 'up_left', 'up_right']))
    pixel[file.stem]['scale'] = metadata.get('runtime_scale') or 1
    pixel[file.stem]['anchor'] = metadata.get('frame_anchor', [metadata['cell_width'] / 2, metadata['cell_height'] - 1])
assert len(pixel) == 33
(root / '.omx/digimon/pixel-data.js').write_text('window.PS_DIGIMON_PIXEL = ' + json.dumps(pixel) + ';\n', encoding='utf-8')
references = json.loads((root / '.omx/digimon/skills-reference.json').read_text(encoding='utf-8-sig'))
assert len(references['records']) == 33
(root / '.omx/digimon/skills-sources.js').write_text('window.PS_DIGIMON_SKILL_REFERENCES = ' + json.dumps(references) + ';\n', encoding='utf-8')
naruto = json.loads((root / '.omx/naruto/sprites.json').read_text(encoding='utf-8-sig'))
assert len(naruto) == 8
(root / '.omx/naruto/sprites-data.js').write_text('window.PS_NARUTO_SPRITES = ' + json.dumps(naruto) + ';\n', encoding='utf-8')
html = (root / 'dev.html').read_text(encoding='utf-8')
html = html.replace('</head>', '<link rel="stylesheet" href=".omx/mobile-portrait.css">\n</head>', 1)
html = html.replace('<head>', '<head>\n<base href="../">\n<script>window.PS_SANDBOX_KEY="ps.sandbox.digimon.v1";</script>', 1)
main = '<script defer src="js/main.js"></script>'
assert main in html
html = html.replace(main, '<script defer src=".omx/unlimited.js"></script>\n<script defer src=".omx/digimon/pixel-data.js"></script>\n<script defer src=".omx/digimon.js"></script>\n<script defer src=".omx/digimon/evolutions-data.js"></script>\n<script defer src=".omx/digimon-evolution.js"></script>\n<script defer src=".omx/digimon-size.js"></script>\n<script defer src=".omx/digimon/skills-sources.js"></script>\n<script defer src=".omx/digimon-skills.js"></script>\n<script defer src=".omx/digimon-skill-combat.js"></script>\n' + main, 1)
html = html.replace(main, '<script defer src=".omx/naruto-sand-vfx.js"></script>\n<script defer src=".omx/naruto/sprites-data.js"></script>\n<script defer src=".omx/naruto.js"></script>\n<script defer src=".omx/naruto-clones.js"></script>\n<script defer src=".omx/naruto-cloak-vfx.js"></script>\n<script defer src=".omx/naruto-support.js"></script>\n<script defer src=".omx/naruto-offense.js"></script>\n<script defer src=".omx/naruto-skills.js"></script>\n<script defer src=".omx/naruto-training.js"></script>\n<script defer src=".omx/quantity.js"></script>\n' + main, 1)
(root / '.omx/digimon.html').write_text(html, encoding='utf-8')
print('Created local Digimon edition entry')
