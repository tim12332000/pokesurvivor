"""Extract pinned classic LF2 Firzen/Julian assets without running the installer."""
import bz2
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib
from PIL import Image

from build_freeze_assets import bitmap, decrypt, parse_dat, PIN, URL

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'art-review/lf2-bosses/source'
INSTALLER = ROOT / 'art-review/freeze/source/LF2Setup.exe'


def extract(blob, select):
    assert hashlib.sha256(blob).hexdigest() == PIN, 'Unrecognized classic installer'
    u16 = lambda p: struct.unpack_from('<H', blob, p)[0]
    u32 = lambda p: struct.unpack_from('<I', blob, p)[0]
    pe = u32(0x3c)
    sections = pe + 24 + u16(pe + 20)
    overlay = max(u32(p + 20) + u32(p + 16)
                  for p in range(sections, sections + u16(pe + 6) * 40, 40))
    assert blob[overlay:overlay + 6] == b'wwgT)H'
    cursor, table = overlay + 6, None
    decode = lambda method, data: data if method == 0 else zlib.decompress(data) if method == 1 else bz2.decompress(data) if method == 2 else None
    while cursor < len(blob):
        tag, flags, size = struct.unpack_from('<HHI', blob, cursor)
        body = cursor + 8
        if tag == 0x7f7f:
            assert flags == 0 and u32(body) == size
            payload = body + 4
            break
        if tag == 0x143a:
            table = decode(blob[body + 4], blob[body + 5:body + size])
            assert len(table) == u32(body)
        cursor = body + size
    assert table
    cursor, entries = 4, {}
    for _ in range(struct.unpack_from('<I', table)[0]):
        size, kind = struct.unpack_from('<HH', table, cursor)
        rec = table[cursor:cursor + size]
        if kind == 0:
            path = rec[62:].split(b'\0')[0].decode('latin1').replace('\\', '/')
            if select(path):
                offset, compressed = struct.unpack_from('<II', rec, 6)
                rawsize = struct.unpack_from('<I', rec, 18)[0]
                raw = decode(blob[payload + offset], blob[payload + offset + 1:payload + offset + compressed])
                assert raw is not None and len(raw) == rawsize
                entries[path] = raw
        cursor += size
    return entries


def main():
    SOURCE.mkdir(parents=True, exist_ok=True)
    blob = INSTALLER.read_bytes()
    data = extract(blob, lambda p: p.endswith('.dat') or p == 'data/data.txt')
    index = {int(oid): path.replace('\\', '/') for oid, path in
             re.findall(r'id:\s*(\d+)\s+type:\s*\d+\s+file:\s*(\S+)', data['data/data.txt'].decode('latin1'))}
    texts = {path: decrypt(raw) for path, raw in data.items() if path.endswith('.dat')}
    for hero in ('firzen', 'julian'):
        out = ROOT / 'assets/lf2' / hero
        out.mkdir(parents=True, exist_ok=True)
        # Some classic object behaviours create sibling objects in the engine
        # (e.g. Firzen's ice chase); they are not all explicit opoint records.
        wanted, pending = set(), [p for p in texts if Path(p).stem.startswith(hero)]
        while pending:
            path = pending.pop()
            if path in wanted or path not in texts:
                continue
            wanted.add(path)
            text = texts[path]
            for block in re.findall(r'\bopoint:(.*?)opoint_end:', text, re.S):
                for oid in re.findall(r'\boid:\s*(\d+)', block):
                    dependency = index.get(int(oid))
                    if dependency and dependency not in wanted:
                        pending.append(dependency)
        metadata = dict(version=1, fps=30, bodyHeight=65 if hero == 'firzen' else 86, objects={})
        images, cells, sounds = set(), {}, set()
        for path in sorted(wanted):
            text = texts[path]
            key = Path(path).stem
            obj = parse_dat(key, text)
            obj['id'] = next((oid for oid, filename in index.items() if filename == path), None)
            metadata['objects'][key] = obj
            for _, _, image, w, h, _, _ in re.findall(r'file\((\d+)-(\d+)\):\s*(\S+)\s+w:\s*(\d+)\s+h:\s*(\d+)\s+row:\s*(\d+)\s+col:\s*(\d+)', text):
                image = image.replace('\\', '/')
                images.add(image)
                cells[image] = (int(w), int(h))
            for sound in re.findall(r'\b(?:sound|weapon_hit_sound|weapon_drop_sound|weapon_broken_sound):\s*(\S+\.wav)', text):
                sounds.add(sound.replace('\\', '/'))
        # Shared original close hit/guard samples, not substitute generated audio.
        sounds.update({'data/001.wav', 'data/007.wav', 'data/012.wav'})
        selected = wanted | images | sounds | {'data/data.txt', 'readme.txt'}
        if hero == 'firzen':
            selected.add('sprite/sys/freeze_0.bmp')
        entries = extract(blob, lambda p: p in selected)
        manifest = dict(game='Little Fighter 2 v2.0a (classic original)', installer_sha256=PIN,
            source_url=URL, attribution='Original LF2 artwork/data/audio by Marti Wong and Starsky Wong; not covered by project code license.',
            conversion='Original in-cell pixel values retained; RGB (0,0,0) and ignored 1px atlas divider rows/columns become transparent.', files=[])
        for path, raw in sorted(entries.items()):
            local = SOURCE / path
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(raw)
            record = dict(path=path, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            if hero == 'firzen' and path == 'sprite/sys/freeze_0.bmp':
                original = bitmap(raw)
                casing = Image.new('RGBA', (160, 80))
                for cell_index in range(2):
                    cell = original.crop(((8 + cell_index) * 80, 0, (8 + cell_index) * 80 + 79, 79))
                    cell.putdata([(r,g,b,a if b > r * 1.25 and g > r * 1.1 and g > 90 else 0)
                                  for r,g,b,a in cell.getdata()])
                    casing.paste(cell, (cell_index * 80, 0))
                dest = out / 'freeze_ice.png'
                casing.save(dest, optimize=True)
                record.update(runtime=dest.relative_to(ROOT).as_posix(), runtime_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
                              size=[160,80], conversion='Original pic8/9 cyan-only ice casing; no redrawing.')
            elif path in images:
                img = bitmap(raw)
                img.putdata([(r, g, b, 0 if (r, g, b) == (0, 0, 0) else a) for r, g, b, a in img.getdata()])
                w, h = cells[path]
                for x in range(w, img.width, w + 1):
                    for y in range(img.height): img.putpixel((x, y), (0, 0, 0, 0))
                for y in range(h, img.height, h + 1):
                    for x in range(img.width): img.putpixel((x, y), (0, 0, 0, 0))
                dest = out / (Path(path).stem + '.png')
                img.save(dest, optimize=True)
                # Original LF2 loads every physical cell even when the declared
                # file range is too short (Julian's skull uses pics8-11 after
                # declaring 0-7). Retain both facts for honest rendering.
                for obj in metadata['objects'].values():
                    for sheet in obj['sheets']:
                        if sheet['image'] == dest.name:
                            sheet['declaredEnd'] = sheet['end']
                            count = (img.width // (sheet['w'] + 1)) * (img.height // (sheet['h'] + 1))
                            sheet['end'] = sheet['start'] + count - 1
                record.update(runtime=dest.relative_to(ROOT).as_posix(), runtime_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(), size=list(img.size))
            elif path in sounds:
                dest = out / Path(path).name
                dest.write_bytes(raw)
                record.update(runtime=dest.relative_to(ROOT).as_posix(), runtime_sha256=hashlib.sha256(raw).hexdigest())
            elif path in texts:
                local.with_suffix('.txt').write_text(texts[path], encoding='utf-8')
            manifest['files'].append(record)
        for obj in metadata['objects'].values():
            for pos, sheet in enumerate(obj['sheets']):
                sheet['physicalEnd'] = sheet['end']
                if pos + 1 < len(obj['sheets']):
                    # Physical unused cells cannot steal the next declared
                    # sheet's numbers (Firzen's emitter art begins at pic8).
                    sheet['end'] = min(sheet['end'], obj['sheets'][pos + 1]['start'] - 1)
        metadata['source'] = manifest
        (out / 'manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (SOURCE.parent / (hero + '-source-manifest.json')).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'hero':hero, 'objects':list(metadata['objects']), 'images':len(images), 'sounds':len(sounds)}))


if __name__ == '__main__':
    main()
