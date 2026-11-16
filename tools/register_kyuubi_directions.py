"""Register generated front/back one-tail cels without altering source pixels."""
import hashlib
import json
from pathlib import Path
from statistics import median
from build_redrawn_atlases import atlas, hair_width, sequence

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art-review'


def register(form):
    source, image = atlas('one-tail-vertical-v1.png', 8)
    side, side_image = atlas(Path(form['source']).name, 6)
    side_head = median(hair_width(side_image, f) for f in side['frames'][:4])
    vertical_head = median(hair_width(image, f) for f in source['frames'][:8])
    source['bodyHeight'] = round(form['bodyHeight'] * vertical_head / side_head, 2)
    # Measured sphere centers in the unmodified generated sheet. Rear cels 28/31
    # hide the orb behind the torso, so they intentionally have no visible anchor.
    orbs = {24:(131,1487,14),25:(341,1481,16),26:(585,1478,17),27:(800,1492,14),
            29:(368,1677,10),30:(602,1652,16)}
    for index, (x, y, radius) in orbs.items():
        frame = source['frames'][index]
        frame['orb'] = [x-frame['rect'][0], y-frame['rect'][1], radius]
    directions = {}
    for direction, offset in (('down', 0), ('up', 4)):
        rows = {'idle': range(offset, offset + 4),
                'activation': range(offset, offset + 4),
                'walk': range(8 + offset, 12 + offset),
                'run': range(8 + offset, 12 + offset),
                'attack': range(16 + offset, 20 + offset),
                'hurt': (19 + offset,),
                'throw': range(16 + offset, 20 + offset),
                'rasenganCharge': (24 + offset, 25 + offset),
                'rasenganDash': (26 + offset,),
                'rasenganRelease': (26 + offset,),
                'rasenganRecover': (27 + offset,)}
        directions[direction] = {}
        for kind, indices in rows.items():
            original = form['animations'][kind]
            directions[direction][kind] = {
                'frames': sequence(source, indices)['frames'],
                'fps': original['fps'], 'loop': original['loop']}
    form['directional'] = {'source': source['source'], 'bodyHeight': source['bodyHeight'],
                           'animations': directions}
    return form


def main():
    path = ART / 'kyuubi-frames.json'
    form = register(json.loads(path.read_text(encoding='utf-8')))
    path.write_text(json.dumps(form, indent=2) + '\n', encoding='utf-8')
    record = json.loads((ART / 'naruto-cloak-directions-20261116/generation.json').read_text(encoding='utf-8'))
    record['sha256'] = hashlib.sha256((ART / form['directional']['source']).read_bytes()).hexdigest()
    record['raw_output_sha256'] = record['sha256']
    record['reference_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                  for name in record['references']}
    record['bodyHeight'] = form['directional']['bodyHeight']
    record['scaleRule'] = 'Median front/back hair width matched to existing side idle hair width; one shared scale across all poses.'
    (ART / 'redrawn/one-tail-vertical-v1.provenance.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'source': form['directional']['source'], 'bodyHeight': form['directional']['bodyHeight'], 'directions': list(form['directional']['animations'])}))


if __name__ == '__main__':
    main()
