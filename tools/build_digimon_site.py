"""Build only the public game files, excluding local state and the upstream domain."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'dist-digimon'
OUT.mkdir(exist_ok=True)
excluded = {'js/app.min.js', 'js/data/funding.js', 'js/ui/support-ui.js',
            'art-review/redrawn/temari-kamatari-v1.png', 'art-review/redrawn/temari-cyclone-wind-v1.png'}
# Remove obsolete files from an existing local artifact as well as fresh CI builds.
for name in excluded:
    stale=OUT/name
    assert stale.resolve().is_relative_to(OUT.resolve())
    stale.unlink(missing_ok=True)
tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
# New public runtime files must also be included in builds before a commit.
public_new = subprocess.check_output(
    ['git', 'ls-files', '--others', '--exclude-standard', '-z', '--', 'assets', 'css', 'js'],
    cwd=ROOT).decode().split('\0')
# Reviewed character runtime only; gallery controls and source references stay local.
review_runtime = ['art-review/' + name for name in [
    'cast-continuity.js', 'animation-assets.js', 'animation-runtime.js',
    'kyuubi-form.js', 'animation-assets.json', 'kyuubi-frames.json']]
metadata = json.loads((ROOT / 'art-review/animation-assets.json').read_text('utf-8'))
sources = {item['source'] for item in metadata.values()}
sources.add(json.loads((ROOT / 'art-review/kyuubi-frames.json').read_text('utf-8'))['source'])
for source in sorted(sources):
    path = Path('art-review') / source
    assert source.startswith('redrawn/') and path.suffix == '.png'
    assert (ROOT / path).resolve().is_relative_to((ROOT / 'art-review/redrawn').resolve())
    review_runtime.append(path.as_posix())
portraits = json.loads((ROOT / '.omx/naruto/sprites.json').read_text('utf-8'))
for hero in ('naruto', 'sasuke', 'rock-lee', 'gaara', 'tenten'):
    source = portraits[hero]['preview']['source']
    assert source.startswith('.omx/naruto/portraits/') and Path(source).suffix == '.png'
    assert (ROOT / source).resolve().is_relative_to((ROOT / '.omx/naruto/portraits').resolve())
    review_runtime.append(source)
review_runtime.extend(['.omx/naruto/portraits/pain.png', '.omx/naruto/portraits/temari.png'])
assert sources == {
    'redrawn/naruto-common-v1.png', 'redrawn/naruto-skills-v2.png',
    'redrawn/sasuke-common-v1.png', 'redrawn/sasuke-skills-v2.png',
    'redrawn/sasuke-chidori-charge-v3.png', 'redrawn/sasuke-chidori-walk-v1.png',
    'redrawn/one-tail-v2.png',
    'redrawn/lee-common-v1.png', 'redrawn/lee-skills-v1.png',
    'redrawn/lee-gates-common-v1.png', 'redrawn/lee-gates-skills-v1.png',
    'redrawn/gaara-common-v1.png', 'redrawn/gaara-skills-v1.png',
    'redrawn/tenten-common-v1.png', 'redrawn/tenten-skills-v1.png',
    'redrawn/tenten-twin-release-v1.png',
    'redrawn/lee-bandage-v1.png',
}, 'Unexpected reviewed hero atlas inventory'
pain = json.loads((ROOT / 'art-review/pain-frames.json').read_text('utf-8'))
assert set(pain['bodies']) == {'tendo','asura','animal','human','preta','naraka','rhino','king'}, 'Six distinct Pain bodies and both summons are required'
review_runtime.extend(['art-review/pain-art.js', 'art-review/pain-frames.json'])
for item in pain['bodies'].values():
    path = Path('art-review') / item['source']
    assert item['source'].startswith('redrawn/') and path.suffix == '.png'
    assert (ROOT / path).resolve().is_relative_to((ROOT / 'art-review/redrawn').resolve())
    review_runtime.append(path.as_posix())
review_runtime.extend(['art-review/temari-art.js', 'art-review/temari-frames.json'])
for source in ('temari-common-v1.png', 'temari-skills-v1.png', 'temari-kamatari-v2.png', 'temari-spin-v1.png'):
    review_runtime.append('art-review/redrawn/' + source)
for name in review_runtime + ['.omx/redrawn-init.js', '.omx/naruto-sand-guard.js', '.omx/damage-splash.js', '.omx/naruto-tenten.js', '.omx/naruto-pain.js', '.omx/naruto-temari.js', '.omx/naruto-temari-reflect.js', '.omx/temari-cyclone-vfx.js', '.omx/temari-coop.js', '.omx/naruto-pain-ui.js', '.omx/pain-beta.js', '.omx/menu-layout.css', '.omx/desktop-portrait.js', '.omx/portrait.html']:
    target = OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / name, target)
for name in filter(None, tracked + public_new):
    if name in excluded:
        continue
    path = Path(name)
    public = path.parts[0] in {'assets', 'css', 'js'}
    sandbox = name.startswith('.omx/') and (path.suffix in {'.js', '.css', '.html', '.png', '.json', '.md'})
    root_file = name in {'sw.js', 'manifest.webmanifest', 'version.json', 'LICENSE', 'LICENSE-NONCOMMERCIAL.md'}
    if not (public or sandbox or root_file):
        continue
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / path, target)

html_path = OUT / '.omx/digimon.html'
html = html_path.read_text(encoding='utf-8')
# Version the actual bytes, including local changes built before a commit.
def version_asset(match):
    source = match[2]
    digest = hashlib.sha256((OUT / source).read_bytes()).hexdigest()[:12]
    return match[1] + source + '?v=' + digest + match[3]

html = re.sub(r'(<script\b[^>]*\bsrc=")(?!https?://)([^"?]+)(?:\?[^"\s]*)?(")',
              version_asset, html)
html = re.sub(r'(<link\b(?=[^>]*\brel="stylesheet")[^>]*\bhref=")(?!https?://)([^"?]+)(?:\?[^"\s]*)?(")',
              version_asset, html)
html = re.sub(r'<!-- seo:begin -->.*?<!-- seo:end -->', '', html, flags=re.S)
html = re.sub(r'<title>.*?</title>', '<title>PokéSurvivor 寶可夢 × 數碼寶貝 × 火影忍者</title>', html, flags=re.S)
html = html.replace('<html lang="es">', '<html lang="zh-TW">')
html = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="免費遊玩、非營利、無廣告、無付費內容。原作由 JPTER78 開發，感謝原作者；本網站為非官方跨界修改版。">', html)
for source in re.findall(r'<(?:script|link)\b[^>]*(?:src|href)="([^"]+)"', html):
    if source.startswith(('js/', 'css/', '.omx/', 'art-review/')):
        assert (OUT / source.split('?', 1)[0]).is_file(), f'Missing runtime script: {source}'
html_path.write_text(html, encoding='utf-8')
(OUT / 'index.html').write_text('''<!doctype html>
<html lang="zh-TW"><meta charset="utf-8"><meta name="robots" content="noindex">
<script>
const target=new URL('.omx/digimon.html',location.href);
target.search=location.search;
if(!target.searchParams.has('lang'))target.searchParams.set('lang','zh-TW');
target.hash=location.hash;
location.replace(target.href);
</script>
<noscript><meta http-equiv="refresh" content="0;url=.omx/digimon.html?lang=zh-TW"></noscript>
<title>PokéSurvivor 跨界同人沙盒版</title>
<a href=".omx/digimon.html?lang=zh-TW">開啟寶可夢 × 數碼寶貝 × 火影忍者</a></html>
''', encoding='utf-8')
(OUT / '.nojekyll').touch()
assert not (OUT / 'CNAME').exists(), 'Never publish the upstream custom domain'
assert not (OUT / '.omx/github_publish.py').exists(), 'Never publish local tooling'
print(f'Built Digimon site: {OUT}')
