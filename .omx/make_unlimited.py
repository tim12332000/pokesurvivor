from pathlib import Path

root = Path(__file__).resolve().parent.parent
html = (root / 'dev.html').read_text(encoding='utf-8')
html = html.replace('<head>', '<head>\n<base href="../">', 1)
main = '<script defer src="js/main.js"></script>'
assert main in html
html = html.replace(main, '<script defer src=".omx/unlimited.js"></script>\n' + main, 1)
(root / '.omx/unlimited.html').write_text(html, encoding='utf-8')
print('Created local unlimited-coins entry')
