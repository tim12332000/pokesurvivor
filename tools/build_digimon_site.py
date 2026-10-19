"""Build only the public game files, excluding local state and the upstream domain."""
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'dist-digimon'
OUT.mkdir(exist_ok=True)
tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
# New public runtime files must also be included in builds before a commit.
public_new = subprocess.check_output(
    ['git', 'ls-files', '--others', '--exclude-standard', '-z', '--', 'assets', 'css', 'js'],
    cwd=ROOT).decode().split('\0')
for name in filter(None, tracked + public_new):
    path = Path(name)
    public = path.parts[0] in {'assets', 'css', 'js'}
    sandbox = name.startswith('.omx/') and (path.suffix in {'.js', '.html', '.png', '.json', '.md'})
    root_file = name in {'sw.js', 'manifest.webmanifest', 'version.json', 'LICENSE', 'LICENSE-NONCOMMERCIAL.md'}
    if not (public or sandbox or root_file):
        continue
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / path, target)

html_path = OUT / '.omx/digimon.html'
html = html_path.read_text(encoding='utf-8')
build_id = subprocess.check_output(['git','rev-parse','--short','HEAD'],cwd=ROOT).decode().strip()
# Every deployment must fetch its matching scripts, including changed skill data.
html = re.sub(r'(<script\b[^>]*\bsrc=")(?!https?://)([^"?]+)(")',
              lambda match: match[1]+match[2]+'?v='+build_id+match[3], html)
html = re.sub(r'<!-- seo:begin -->.*?<!-- seo:end -->', '', html, flags=re.S)
html = re.sub(r'<title>.*?</title>', '<title>PokéSurvivor 寶可夢 × 數碼寶貝 × 火影忍者</title>', html, flags=re.S)
html = html.replace('<html lang="es">', '<html lang="zh-TW">')
html = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="寶可夢、數碼寶貝與火影忍者的非官方跨界沙盒版，免費遊玩，存檔保存在此瀏覽器。">', html)
for source in re.findall(r'<script[^>]*src="([^"]+)"', html):
    if source.startswith(('js/', '.omx/')):
        assert (OUT / source.split('?', 1)[0]).is_file(), f'Missing runtime script: {source}'
html_path.write_text(html, encoding='utf-8')
(OUT / 'index.html').write_text('''<!doctype html>
<html lang="zh-TW"><meta charset="utf-8"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0;url=.omx/digimon.html?lang=zh-TW">
<title>PokéSurvivor 跨界同人沙盒版</title>
<a href=".omx/digimon.html?lang=zh-TW">開啟寶可夢 × 數碼寶貝 × 火影忍者</a></html>
''', encoding='utf-8')
(OUT / '.nojekyll').touch()
assert not (OUT / 'CNAME').exists(), 'Never publish the upstream custom domain'
assert not (OUT / '.omx/github_publish.py').exists(), 'Never publish local tooling'
print(f'Built Digimon site: {OUT}')
