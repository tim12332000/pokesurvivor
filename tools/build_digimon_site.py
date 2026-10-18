"""Build only the public game files, excluding local state and the upstream domain."""
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'dist-digimon'
OUT.mkdir(exist_ok=True)
tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
for name in filter(None, tracked):
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
html = re.sub(r'<!-- seo:begin -->.*?<!-- seo:end -->', '', html, flags=re.S)
html = re.sub(r'<title>.*?</title>', '<title>PokéSurvivor 數碼寶貝同人沙盒版</title>', html, flags=re.S)
html = html.replace('<html lang="es">', '<html lang="zh-TW">')
html = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="非官方數碼寶貝同人沙盒版，免費遊玩，存檔保存在此瀏覽器。">', html)
html_path.write_text(html, encoding='utf-8')
(OUT / 'index.html').write_text('''<!doctype html>
<html lang="zh-TW"><meta charset="utf-8"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0;url=.omx/digimon.html?lang=zh-TW">
<title>PokéSurvivor 數碼寶貝同人沙盒版</title>
<a href=".omx/digimon.html?lang=zh-TW">開啟數碼寶貝同人沙盒版</a></html>
''', encoding='utf-8')
(OUT / '.nojekyll').touch()
assert not (OUT / 'CNAME').exists(), 'Never publish the upstream custom domain'
assert not (OUT / '.omx/github_publish.py').exists(), 'Never publish local tooling'
print(f'Built Digimon site: {OUT}')
