"""Extract classic LF2 2.0a Freeze data; never execute the installer.

The installer layout is documented by OpenLF2's MIT-licensed resource reader.
Only pinned original data is accepted. Runtime PNGs retain original pixels,
with LF2's pure-black colour key converted to alpha; no resampling/redrawing.
"""
import bz2
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'art-review/freeze/source'
OUT = ROOT / 'assets/lf2/freeze'
PIN = '540c485547e234b0d09595f54d067aafd7176092c308aca61868f3cbc03030e1'
URL = 'https://archive.org/download/little-fighter-2_202404/Little%20Fighter%202.rar/Little%20Fighter%202%2FLF2Setup.exe'


def extract_installer(blob):
    assert hashlib.sha256(blob).hexdigest() == PIN, 'Unrecognized installer'
    u16 = lambda p: struct.unpack_from('<H', blob, p)[0]
    u32 = lambda p: struct.unpack_from('<I', blob, p)[0]
    pe = u32(0x3c)
    sections = pe + 24 + u16(pe + 20)
    overlay = max(u32(p + 20) + u32(p + 16)
                  for p in range(sections, sections + u16(pe + 6) * 40, 40))
    assert blob[overlay:overlay + 6] == b'wwgT)H'
    cursor = overlay + 6
    table = None
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
    cursor = 4
    entries = {}
    for _ in range(struct.unpack_from('<I', table)[0]):
        size, kind = struct.unpack_from('<HH', table, cursor)
        rec = table[cursor:cursor + size]
        if kind == 0:
            path = rec[62:].split(b'\0')[0].decode('latin1').replace('\\', '/')
            off, compressed = struct.unpack_from('<II', rec, 6)
            rawsize = struct.unpack_from('<I', rec, 18)[0]
            if ('freeze' in path or path in ['data/weapon7.dat', 'sprite/sys/weapon7.bmp'] or re.fullmatch(r'data/\d+\.wav', path)):
                raw = decode(blob[payload + off], blob[payload + off + 1:payload + off + compressed])
                assert raw is not None and len(raw) == rawsize
                entries[path] = raw
        cursor += size
    return entries


def decrypt(data):
    key = b'SiuHungIsAGoodBearBecauseHeIsVeryGood'
    # LF2 advances the key by twelve positions before the first plaintext byte.
    return bytes((v - key[(i + 12) % len(key)]) % 256 for i, v in enumerate(data[123:])).decode('latin1')


def fields(text):
    return {k: float(v) if '.' in v else int(v) for k, v in re.findall(r'([\w_]+):\s*(-?\d+(?:\.\d+)?)', text)}


def bitmap(data):
    """Decode original BI_RLE8 including delta records (Pillow loses these)."""
    offset = struct.unpack_from('<I', data, 10)[0]
    width, height, _, bits, compression = struct.unpack_from('<iiHHI', data, 18)
    if bits != 8 or compression != 1:
        from io import BytesIO
        return Image.open(BytesIO(data)).convert('RGBA')
    palette = [tuple(data[54+i*4:57+i*4][::-1]) for i in range((offset-54)//4)]
    pixels = bytearray(width * height)
    cursor, x, y = offset, 0, 0
    while cursor + 1 < len(data):
        count, value = data[cursor:cursor+2]
        cursor += 2
        if count:
            for _ in range(count):
                if 0 <= x < width and 0 <= y < height:
                    pixels[(height-1-y)*width+x] = value
                x += 1
        elif value == 0:
            x, y = 0, y + 1
        elif value == 1:
            break
        elif value == 2:
            dx, dy = data[cursor:cursor+2]
            cursor += 2
            x, y = x + dx, y + dy
        else:
            for v in data[cursor:cursor+value]:
                if 0 <= x < width and 0 <= y < height:
                    pixels[(height-1-y)*width+x] = v
                x += 1
            cursor += value + value % 2
    img = Image.new('RGBA', (width, height))
    img.putdata([(*palette[index], 255) for index in pixels])
    return img


def parse_dat(name, text):
    sheets = []
    for start, end, path, w, h, row, col in re.findall(r'file\((\d+)-(\d+)\):\s*(\S+)\s+w:\s*(\d+)\s+h:\s*(\d+)\s+row:\s*(\d+)\s+col:\s*(\d+)', text):
        sheets.append(dict(start=int(start), end=int(end), image=Path(path.replace('\\', '/')).stem + '.png', w=int(w), h=int(h), columns=int(row), rows=int(col)))
    frames = {}
    for index, label, content in re.findall(r'<frame>\s*(\d+)\s+([^\r\n]*)[\r\n]+(.*?)<frame_end>', text, re.S):
        head = re.split(r'\b(?:bdy|itr|wpoint|opoint|cpoint|bpoint):', content)[0]
        frame = dict(name=label.strip(), **fields(head))
        for block in ['wpoint', 'opoint', 'cpoint', 'bpoint']:
            match = re.search(r'\b' + block + r':(.*?)' + block + r'_end:', content, re.S)
            if match:
                frame[block] = fields(match.group(1))
        for block in ['bdy', 'itr']:
            frame[block] = [fields(m) for m in re.findall(r'\b' + block + r':(.*?)' + block + r'_end:', content, re.S)]
        sound = re.search(r'sound:\s*(\S+)', content)
        if sound:
            frame['sound'] = sound.group(1).replace('\\', '/')
        frames[index] = frame
    return dict(sheets=sheets, frames=frames)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    entries = extract_installer((SOURCE / 'LF2Setup.exe').read_bytes())
    manifest = dict(game='Little Fighter 2 v2.0a (classic original)', installer_sha256=PIN, source_url=URL,
                    attribution='Little Fighter 2 artwork and data by Marti Wong and Starsky Wong. Not covered by this project code license.',
                    conversion='Original in-cell pixel values retained; RGB (0,0,0) and ignored 1px atlas divider rows/columns become transparent.', files=[])
    metadata = dict(version=1, fps=30, bodyHeight=65, objects={})
    sounds = {'005', '007', '008', '012', '015', '019', '020', '064', '072', '073', '074'}
    for path, data in entries.items():
        original = SOURCE / path
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(data)
        record = dict(path=path, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        if path.endswith('.bmp') and '_mirror' not in path:
            img = bitmap(data)
            pixels = list(img.getdata())
            img.putdata([(r,g,b,0 if (r,g,b)==(0,0,0) else a) for r,g,b,a in pixels])
            cells = {'freeze_0': (79,79), 'freeze_1': (79,79), 'freeze_2': (79,79),
                     'freeze_ball': (81,82), 'freeze_col': (109,109),
                     'freeze_ww': (159,159), 'weapon7': (69,69)}
            if original.stem in cells:
                w,h = cells[original.stem]
                # LF2 never displays the colourful 1px dividers. Removing them
                # also prevents neighbouring atlas colours bleeding at fractional
                # world zoom; all pixels inside each original cell stay intact.
                for x in range(w,img.width,w+1):
                    for y in range(img.height): img.putpixel((x,y),(0,0,0,0))
                for y in range(h,img.height,h+1):
                    for x in range(img.width): img.putpixel((x,y),(0,0,0,0))
            dest = OUT / (original.stem + '.png')
            img.save(dest, optimize=True)
            record.update(runtime=str(dest.relative_to(ROOT)).replace('\\','/'), runtime_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(), size=list(img.size))
        elif path.endswith('.dat'):
            text = decrypt(data)
            (SOURCE / (original.stem + '.txt')).write_text(text, encoding='utf8')
            metadata['objects'][original.stem] = parse_dat(original.stem, text)
        elif original.suffix == '.wav' and original.stem in sounds:
            dest = OUT / original.name
            dest.write_bytes(data)
            record.update(runtime=str(dest.relative_to(ROOT)).replace('\\','/'), runtime_sha256=hashlib.sha256(data).hexdigest())
        manifest['files'].append(record)
    # Keep the original cyan ice pixels, removing Freeze's own body so the
    # casing can visibly surround the actual target instead of substituting him.
    original = OUT / 'freeze_0.png'
    source = Image.open(original).convert('RGBA')
    casing = Image.new('RGBA', (160, 80))
    for index in range(2):
        cell = source.crop(((8+index)*80,0,(8+index)*80+79,79))
        cell.putdata([(r,g,b,a if b > r*1.25 and g > r*1.1 and g > 90 else 0)
                      for r,g,b,a in cell.getdata()])
        casing.paste(cell,(index*80,0))
    dest = OUT / 'freeze_ice.png'
    casing.save(dest, optimize=True)
    manifest['files'].append(dict(path='sprite/sys/freeze_0.bmp#pic8-9-cyan-overlay', runtime='assets/lf2/freeze/freeze_ice.png',
                                 runtime_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(), size=[160,80],
                                 conversion='Crop original pic8/9 and retain original cyan pixels only: b>r*1.25,g>r*1.1,g>90; no redrawing.'))
    metadata['source'] = manifest
    (OUT / 'manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    (SOURCE.parent / 'source-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'objects': list(metadata['objects']), 'files':len(entries), 'runtime':str(OUT)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
