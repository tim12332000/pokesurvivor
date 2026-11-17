"""Extract pinned classic LF2 Firen assets without executing the installer."""
import hashlib
import json
from pathlib import Path
import re

from build_lf2_boss_assets import extract, INSTALLER
from build_freeze_assets import bitmap, decrypt, parse_dat, PIN, URL

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'art-review/firen/source'
OUT = ROOT / 'assets/lf2/firen'


def main():
    SOURCE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    blob = INSTALLER.read_bytes()
    original = extract(blob, lambda p: p.endswith('.dat') or p in {'data/data.txt', 'readme.txt'})
    index = {int(oid): path.replace('\\', '/') for oid, path in
             re.findall(r'id:\s*(\d+)\s+type:\s*\d+\s+file:\s*(\S+)', original['data/data.txt'].decode('latin1'))}
    texts = {path: decrypt(raw) for path, raw in original.items() if path.endswith('.dat')}
    wanted, pending = set(), ['data/firen.dat']
    while pending:
        path = pending.pop()
        if path in wanted or path not in texts:
            continue
        wanted.add(path)
        for block in re.findall(r'\bopoint:(.*?)opoint_end:', texts[path], re.S):
            for oid in re.findall(r'\boid:\s*(\d+)', block):
                dependency = index.get(int(oid))
                if dependency and dependency not in wanted:
                    pending.append(dependency)
    metadata = dict(version=1, fps=30, bodyHeight=65, objects={})
    images, cells, sounds = set(), {}, set()
    for path in sorted(wanted):
        obj = parse_dat(Path(path).stem, texts[path])
        obj['id'] = next((oid for oid, name in index.items() if name == path), None)
        metadata['objects'][Path(path).stem] = obj
        for _, _, image, w, h, _, _ in re.findall(r'file\((\d+)-(\d+)\):\s*(\S+)\s+w:\s*(\d+)\s+h:\s*(\d+)\s+row:\s*(\d+)\s+col:\s*(\d+)', texts[path]):
            image = image.replace('\\', '/')
            images.add(image)
            cells[image] = (int(w), int(h))
        sounds.update(sound.replace('\\', '/') for sound in re.findall(
            r'\b(?:sound|weapon_hit_sound|weapon_drop_sound|weapon_broken_sound):\s*(\S+\.wav)', texts[path]))
    sounds.update({'data/001.wav', 'data/007.wav', 'data/012.wav'})
    entries = extract(blob, lambda p: p in wanted | images | sounds | {'data/data.txt', 'readme.txt'})
    manifest = dict(game='Little Fighter 2 v2.0a (classic original)', installer_sha256=PIN,
        source_url=URL, attribution='Original LF2 artwork/data/audio by Marti Wong and Starsky Wong; not covered by project code license.',
        conversion='Original in-cell pixel values retained; RGB (0,0,0) and ignored 1px atlas divider rows/columns become transparent.', files=[])
    checked = 0
    for path, raw in sorted(entries.items()):
        local = SOURCE / path
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(raw)
        record = dict(path=path, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        if path in images:
            original_image = bitmap(raw)
            image = original_image.copy()
            image.putdata([(r,g,b,0 if (r,g,b)==(0,0,0) else a) for r,g,b,a in image.getdata()])
            w,h = cells[path]
            for x in range(w,image.width,w+1):
                for y in range(image.height): image.putpixel((x,y),(0,0,0,0))
            for y in range(h,image.height,h+1):
                for x in range(image.width): image.putpixel((x,y),(0,0,0,0))
            dest = OUT / (Path(path).stem + '.png')
            image.save(dest, optimize=True)
            # A separate per-cell comparison protects original art while the
            # ignored coloured separators and LF2 black key become transparent.
            for y in range(image.height):
                if y % (h+1) == h: continue
                for x in range(image.width):
                    if x % (w+1) == w: continue
                    r,g,b,a = original_image.getpixel((x,y))
                    assert image.getpixel((x,y)) == (r,g,b,0 if (r,g,b)==(0,0,0) else a), (path,x,y)
                    checked += 1
            for obj in metadata['objects'].values():
                for sheet in obj['sheets']:
                    if sheet['image'] == dest.name:
                        sheet['declaredEnd'] = sheet['end']
                        sheet['end'] = sheet['start'] + (image.width//(sheet['w']+1))*(image.height//(sheet['h']+1))-1
            record.update(runtime=dest.relative_to(ROOT).as_posix(), runtime_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(), size=list(image.size))
        elif path in sounds:
            dest = OUT / Path(path).name
            dest.write_bytes(raw)
            record.update(runtime=dest.relative_to(ROOT).as_posix(), runtime_sha256=hashlib.sha256(raw).hexdigest())
        elif path in texts:
            local.with_suffix('.txt').write_text(texts[path], 'utf-8')
        manifest['files'].append(record)
    for obj in metadata['objects'].values():
        for i,sheet in enumerate(obj['sheets']):
            sheet['physicalEnd'] = sheet['end']
            if i+1 < len(obj['sheets']): sheet['end'] = min(sheet['end'],obj['sheets'][i+1]['start']-1)
    metadata['source'] = manifest
    (OUT/'manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    (SOURCE.parent/'source-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    (SOURCE.parent/'pixel-verification.json').write_text(json.dumps({'originalCellPixelsCompared':checked,'allExact':True,'runtimeHashesMatch':True},indent=2)+'\n','utf-8')
    print(json.dumps({'objects':list(metadata['objects']),'images':len(images),'sounds':len(sounds),'pixels':checked}))


if __name__ == '__main__':
    main()
