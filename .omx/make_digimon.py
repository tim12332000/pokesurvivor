from pathlib import Path
import json
import hashlib
import re

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
assert {'naruto', 'sakura', 'kakashi', 'hinata', 'rock-lee', 'gaara', 'sasuke', 'itachi', 'tenten', 'pain'} <= naruto.keys()
(root / '.omx/naruto/sprites-data.js').write_text('window.PS_NARUTO_SPRITES = ' + json.dumps(naruto) + ';\n', encoding='utf-8')
html = (root / 'dev.html').read_text(encoding='utf-8')
html = html.replace('</head>', '<link rel="stylesheet" href=".omx/mobile-portrait.css">\n<link rel="stylesheet" href=".omx/menu-layout.css">\n</head>', 1)
html = html.replace('<head>', '<head>\n<base href="../">\n<script>window.PS_SANDBOX_KEY="ps.sandbox.digimon.v1";</script>\n<script src=".omx/desktop-portrait.js"></script>', 1)
main = '<script defer src="js/main.js"></script>'
assert main in html
html = html.replace(main, '<script defer src=".omx/unlimited.js"></script>\n<script defer src=".omx/digimon/pixel-data.js"></script>\n<script defer src=".omx/digimon.js"></script>\n<script defer src=".omx/digimon/evolutions-data.js"></script>\n<script defer src=".omx/digimon-evolution.js"></script>\n<script defer src=".omx/digimon-size.js"></script>\n<script defer src=".omx/digimon/skills-sources.js"></script>\n<script defer src=".omx/digimon-skills.js"></script>\n<script defer src=".omx/digimon-skill-combat.js"></script>\n' + main, 1)
html = html.replace(main, '<script defer src=".omx/naruto-sand-vfx.js"></script>\n<script defer src=".omx/naruto/sprites-data.js"></script>\n<script defer src=".omx/naruto.js"></script>\n<script defer src=".omx/naruto-clones.js"></script>\n<script defer src=".omx/naruto-cloak-vfx.js"></script>\n<script defer src=".omx/naruto-support.js"></script>\n<script defer src=".omx/naruto-offense.js"></script>\n<script defer src=".omx/naruto-lee.js"></script>\n<script defer src=".omx/naruto-gates.js"></script>\n<script defer src=".omx/naruto-gaara.js"></script>\n<script defer src=".omx/naruto-sand-guard.js"></script>\n<script defer src=".omx/naruto-chidori.js"></script>\n<script defer src=".omx/naruto-fireball-cast.js"></script>\n<script defer src=".omx/naruto-fireball-aoe.js"></script>\n<script defer src=".omx/naruto-sharingan.js"></script>\n<script defer src=".omx/naruto-sharingan-powers.js"></script>\n<script defer src=".omx/naruto-kusanagi.js"></script>\n<script defer src=".omx/naruto-skills.js"></script>\n<script defer src=".omx/naruto-tenten.js"></script>\n<script defer src=".omx/naruto-training.js"></script>\n<script defer src=".omx/quantity.js"></script>\n<script defer src=".omx/lifesteal.js"></script>\n<script defer src=".omx/damage-splash.js"></script>\n<script defer src=".omx/percent-health-damage.js"></script>\n<script defer src=".omx/max-health-percent.js"></script>\n<script defer src="js/systems/giant.js"></script>\n<script defer src="js/systems/self-clone.js"></script>\n<script defer src=".omx/run-attributes.js"></script>\n<script defer src=".omx/starter-balance.js"></script>\n<script defer src=".omx/naruto-sharingan-icons.js"></script>\n<script defer src=".omx/dev-controls.js"></script>\n' + main, 1)
html = html.replace(main, '<script defer src="art-review/cast-continuity.js"></script>\n<script defer src="art-review/animation-assets.js"></script>\n<script defer src="art-review/animation-runtime.js"></script>\n<script defer src="art-review/kyuubi-form.js"></script>\n<script defer src=".omx/redrawn-init.js"></script>\n' + main, 1)
html = html.replace('window.PS_SANDBOX_KEY="ps.sandbox.digimon.v1";', 'window.PS_SANDBOX_KEY=new URLSearchParams(location.search).get("painBeta")==="1"?"ps.sandbox.pain-beta.v1":"ps.sandbox.digimon.v1";')
html = html.replace('<script defer src=".omx/naruto.js"></script>', '<script defer src="art-review/pain-art.js"></script>\n<script defer src="art-review/temari-art.js"></script>\n<script defer src=".omx/naruto.js"></script>', 1)
html = html.replace('<script defer src=".omx/naruto-tenten.js"></script>', '<script defer src=".omx/naruto-tenten.js"></script>\n<script defer src=".omx/naruto-pain.js"></script>\n<script defer src=".omx/temari-cyclone-vfx.js"></script>\n<script defer src=".omx/naruto-temari.js"></script>\n<script defer src=".omx/naruto-temari-reflect.js"></script>', 1)
pain_vfx = ''.join(f'<script defer src="js/systems/pain-vfx/{skill}.js"></script>\n' for skill in ['basic', 'gravity', 'missiles', 'summon', 'soul', 'absorb', 'repair', 'planet'])
html = html.replace('<script defer src=".omx/naruto-pain.js"></script>', pain_vfx + '<script defer src=".omx/naruto-pain.js"></script>', 1)
html = html.replace('<script defer src=".omx/quantity.js"></script>', '<script defer src=".omx/quantity.js"></script>\n<script defer src="js/systems/ninja-tool-bounce.js"></script>', 1)
html = html.replace('<script defer src="js/systems/self-clone.js"></script>', '<script defer src="js/systems/self-clone.js"></script>\n<script defer src=".omx/temari-coop.js"></script>', 1)
html = html.replace('<script defer src=".omx/naruto-sharingan-icons.js"></script>', '<script defer src=".omx/naruto-sharingan-icons.js"></script>\n<script defer src=".omx/naruto-pain-ui.js"></script>', 1)
html = html.replace(main, '<script defer src=".omx/pain-beta.js"></script>\n' + main, 1)
# Local previews need the same cache separation as deployed builds. A version
# on the page URL alone does not invalidate its independently cached scripts.
def version_asset(match):
    source = match[2]
    digest = hashlib.sha256((root / source).read_bytes()).hexdigest()[:12]
    return match[1] + source + '?v=' + digest + match[3]

html = re.sub(r'(<script\b[^>]*\bsrc=")(?!https?://)([^"?]+)(")', version_asset, html)
html = re.sub(r'(<link\b(?=[^>]*\brel="stylesheet")[^>]*\bhref=")(?!https?://)([^"?]+)(")', version_asset, html)
(root / '.omx/digimon.html').write_text(html, encoding='utf-8')
print('Created local Digimon edition entry')
