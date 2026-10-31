"""Record design-only generated illustrations; never updates game asset manifests."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
repo = root.parent.parent
prompts = json.loads((root / 'prompts.json').read_text(encoding='utf-8'))
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
outputs = []
for name, key, reference in [
    ('concept-five-dances-v1.png', 'concept', 'art-review/redrawn/gaara-common-v1.png'),
    ('concept-transformation-storyboard-v1.png', 'transformation', 'art-review/kimimaro-design/concept-five-dances-v1.png'),
]:
    outputs.append({'file': name, 'sha256': digest(root / name), 'promptKey': key,
                    'referenceImages': [{'file': reference, 'sha256': digest(repo / reference)}],
                    'kind': 'AI generated design illustration; not production atlas or official art'})
data = {'date': '2026-10-27', 'tool': 'image_gen.imagegen (built-in)', 'scope': 'design-only',
        'transparent_background': False, 'prompts': prompts, 'outputs': outputs,
        'notes': ['Commercial reference sheets were inspected for research, not copied into project.',
                  'No runtime asset registration. Static storyboard is not an animation.',
                  'Smooth concept illustrations require pixel-art production redraw.',
                  'Curse stage 2 concept tail is over-exposed bone; final design needs gray-brown flesh with bone detailing.',
                  'Storyboard camera placement is illustrative; final implementation must keep fixed camera and common ground anchors.']}
(root / 'provenance.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Recorded two image hashes, two reference hashes and full prompts.')
