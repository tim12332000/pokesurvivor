"""Register aligned imagegen hair edits using the existing authored pose anchors."""
import copy
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art-review'
SOURCES = {
    'lee-gates-common-v1.png': 'lee-death-common-v3.png',
    'lee-gates-skills-v1.png': 'lee-death-skills-v3.png',
    'lee-bandage-v1.png': 'lee-death-bandage-v3.png',
    'lee-front-lotus-hold-v1.png': 'lee-death-front-lotus-hold-v3.png',
    'lee-whirlwind-air-v1.png': 'lee-death-whirlwind-air-v3.png',
}


def main():
    from build_redrawn_atlases import atlas
    crops, scales = {}, {}
    for old, new in SOURCES.items():
        with Image.open(ART / 'redrawn' / old) as original, Image.open(ART / 'redrawn' / new) as edited:
            assert max(abs(a - b) for a, b in zip(original.size, edited.size)) <= 2, f'Unaligned Death Gate atlas: {new}'
            scales[new] = (edited.width / original.width, edited.height / original.height)
            assert edited.mode == 'RGBA' and edited.getextrema()[3][0] == 0, f'Missing transparency: {new}'
        rows = 8 if 'common' in old else 4 if 'skills' in old or 'whirlwind' in old else 2
        crops[new], _ = atlas(new, rows)
    path = ART / 'animation-assets.json'
    data = json.loads(path.read_text('utf-8'))
    for key, entry in list(data.items()):
        if not key.startswith('lee-opened-'):
            continue
        clone = copy.deepcopy(entry)
        clone['source'] = 'redrawn/' + SOURCES[Path(entry['source']).name]
        for frame in clone['frames']:
            fresh = crops[Path(clone['source']).name]['frames'][frame['atlasIndex']]
            sx, sy = scales[Path(clone['source']).name]
            shift_x = fresh['rect'][0] + fresh['anchor'][0] - (frame['rect'][0] + frame['anchor'][0]) * sx
            shift_y = fresh['rect'][1] + fresh['anchor'][1] - (frame['rect'][1] + frame['anchor'][1]) * sy
            for point in ('anchor', 'hand', 'grip', 'foot'):
                if point in frame:
                    frame[point] = [(frame[point][0] + frame['rect'][0]) * sx + shift_x - fresh['rect'][0],
                                    (frame[point][1] + frame['rect'][1]) * sy + shift_y - fresh['rect'][1]]
            frame['rect'] = fresh['rect']
        data[key.replace('lee-opened-', 'lee-death-', 1)] = clone
    path.write_text(json.dumps(data, indent=2) + '\n', 'utf-8')
    atlas_path = ART / 'redrawn/atlas-map.json'
    registered = json.loads(atlas_path.read_text('utf-8'))
    for name, source in crops.items():
        source['bodyHeight'] = next(item['bodyHeight'] for item in data.values()
                                    if item['source'] == 'redrawn/' + name)
        registered[name.removesuffix('-v3.png')] = source
    atlas_path.write_text(json.dumps(registered, indent=2) + '\n', 'utf-8')
    manifest_path = ART / 'manifest.json'
    manifest = json.loads(manifest_path.read_text('utf-8'))
    items = {item['id']: item for item in manifest['items']}
    for name, source in crops.items():
        identity = name.removesuffix('.png')
        sequences = [{'name': key, 'indices': [frame['atlasIndex'] for frame in entry['frames']], 'loop': False}
                     for key, entry in data.items() if key.startswith('lee-death-') and entry['source'] == source['source']]
        items[identity] = {'id': identity, 'title': '小李・死門：' + identity.removeprefix('lee-death-'),
                           'character': '小李', 'category': 'common' if 'common' in name else 'skill',
                           'kind': '原創重繪・AI 輔助製作', 'image': source['source'],
                           'status': 'candidate', 'runtimePreview': True,
                           'summary': '死門期間使用赤紅上揚火焰髮；關門直接恢復普通小李。',
                           'references': [{'title': '官方八門遁甲', 'url': 'https://naruto-official.com/en/anime/naruto2/list/01_864'}],
                           'animation': {'fps': 8, 'bodyHeight': source['bodyHeight'], 'frames': source['frames'], 'sequences': sequences}}
    for identity in ('lee-gates-common-v1', 'lee-gates-skills-v1'):
        if identity in items:
            items[identity]['summary'] = '杜門與景門期間使用紅膚黑髮動作；死門切換專用紅髮圖集，關門直接恢復普通小李。'
    manifest['items'] = list(items.values())
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print('Registered 12 Death Gate animation sequences across five aligned atlases')


if __name__ == '__main__':
    main()
