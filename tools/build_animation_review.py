"""Export the isolated art review website; never build or publish the game."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'art-review'
OUTPUT = ROOT / 'dist-animation-review'
manifest = json.loads((SOURCE / 'manifest.json').read_text(encoding='utf-8'))
files = {'index.html', 'gallery.js', 'style.css', 'manifest.json', 'README.md',
         'research.md', 'redrawn/provenance.json', 'redrawn/atlas-map.json'}
files.update(name for name in ['coverage.json','coverage.md','prompts-expansion.json','gameplay-contract.md'] if (SOURCE/name).is_file())
for item in manifest['items']:
    if item['status'] != 'candidate':
        continue
    files.add(item['image'])
    if item.get('beforeImage'):
        files.add(item['beforeImage'])
if OUTPUT.exists():
    if OUTPUT.resolve() != ROOT.resolve() / 'dist-animation-review':
        raise ValueError('Unexpected export directory')
    shutil.rmtree(OUTPUT)
for name in sorted(files):
    source = (SOURCE / name).resolve()
    if not source.is_relative_to(SOURCE.resolve()) or not source.is_file():
        raise ValueError(f'Invalid review asset: {name}')
    target = OUTPUT / 'art-review' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
OUTPUT.mkdir(exist_ok=True)
(OUTPUT / 'index.html').write_text('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=art-review/index.html"><title>動作演出審閱室</title><a href="art-review/index.html">開啟動作演出審閱室</a></html>', encoding='utf-8')
(OUTPUT / '.nojekyll').touch()
print(f'Built independent art review: {OUTPUT} ({len(files)} assets)')
