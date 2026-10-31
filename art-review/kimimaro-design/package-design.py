"""Create a portable design package; never edits or publishes the game."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parent
output = root.parents[1] / 'output'
output.mkdir(exist_ok=True)
target = output / 'kimimaro-design-complete.zip'
paths = sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts
               and p.suffix.lower() in {'.md','.js','.json','.html','.css','.png','.webm','.py'})
manifest = {'scope':'complete design and independent preview; not game integration',
            'files':{str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
start = '''# 開啟君麻呂設計預覽

此壓縮包包含八招、蔓花連動、咒印、普通與二階關鍵姿勢、獨立預覽、無聲影片和研究規格。

解壓後，在此資料夾啟動：

    python -m http.server 8327 --bind 127.0.0.1 --directory kimimaro-design

再開啟 http://127.0.0.1:8327/ 。或直接觀看 kimimaro-design/evidence/kimimaro-motion-reel.webm。

角色設計以 final-spec.md 和 design-data.js 為準；README 中的工作區網址適用原專案目錄。
所有生成、研究和驗證界線保留於文件。這不是正式遊戲安裝包。
'''
with ZipFile(target,'w',compression=ZIP_DEFLATED,compresslevel=6) as archive:
    for p in paths:
        archive.write(p, 'kimimaro-design/'+p.relative_to(root).as_posix())
    archive.writestr('START-HERE.md',start)
    archive.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
with ZipFile(target) as archive:
    assert archive.testzip() is None
    stored = json.loads(archive.read('manifest.json'))
    for name, digest in stored['files'].items():
        assert hashlib.sha256(archive.read('kimimaro-design/'+name)).hexdigest()==digest,name
print(json.dumps({'file':str(target),'bytes':target.stat().st_size,'files':len(paths),
                  'sha256':hashlib.sha256(target.read_bytes()).hexdigest()},ensure_ascii=True))
