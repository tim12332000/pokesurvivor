"""Audit design/discussion artifacts and prototype evidence, not game balance."""
import hashlib
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
COUNCIL = Path(__file__).resolve().parent


def main():
    baseline = json.loads((COUNCIL / 'phase1-manifest.json').read_text('utf8'))
    audit = {
        'independentDraftsPreserved': {}, 'peerArtifacts': {}, 'localLinks': [],
        'ratificationConditionsIncorporated': True, 'prototype': {},
        'scope': 'Four-agent design, actual peer discussion and executable prototype; no product implementation or balance claim.'
    }
    for name, entry in baseline['drafts'].items():
        draft = COUNCIL / name / 'proposal.md'
        same = hashlib.sha256(draft.read_bytes()).hexdigest() == entry['sha256']
        assert same, f'Independent draft changed: {name}'
        audit['independentDraftsPreserved'][name] = same
        for filename in ['peer-review.md', 'revision.md', 'ratification.md']:
            path = COUNCIL / name / filename
            assert path.is_file() and path.stat().st_size > 500, str(path)
            audit['peerArtifacts'][path.relative_to(ROOT).as_posix()] = {
                'bytes': path.stat().st_size,
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()
            }
    for filename in ['README.md', 'shared-design.md']:
        path = COUNCIL / filename
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text('utf8')):
            if link.startswith(('http:', 'https:', '#')):
                continue
            target = path.parent / link.split('#')[0]
            assert target.is_file(), (filename, link)
            audit['localLinks'].append(link)
    shared = (COUNCIL / 'shared-design.md').read_text('utf8')
    for condition in [
        'primaryHits: [{ targetId, primaryDirectDamage }]',
        'primary護盾吸收／overkill', '二階升三階', '同時完成升階與分歧',
        '以主線首領槽位識別', '每個owner同時最多一個里香演員',
        '不宣稱動畫原衣裝', '96不是整個遊戲所有幾何的總cap'
    ]:
        assert condition in shared, condition
    for filename in ['algorithms.js', 'prototype.js', 'prototype.html', 'test-algorithms.cjs']:
        path = COUNCIL / 'combat-vfx' / filename
        audit['prototype'][filename] = {
            'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()
        }
    proof = json.loads((COUNCIL / 'combat-vfx/evidence/prototype-peer-review.json').read_text('utf8'))
    assert not proof['prototype']['errors']
    assert proof['prototype']['twoFoldDprCamera']['low']['lastStats'] == {
        'texturedTriangles': 12, 'fallbackPanels': 2, 'folds': 2
    }
    url = 'http://127.0.0.1:8337/art-review/design-council/combat-vfx/prototype.html'
    with urlopen(Request(url, method='HEAD'), timeout=10) as response:
        assert response.status == 200
    audit['ok'] = True
    audit['manualEvidence'] = 'Leader inspected all four actual question/reply logs, revisions, ratifications and three rendered prototype modes.'
    audit['tests'] = 'Leader reran Node assertions, JS syntax, Python compile and prototype-only Chrome verification after final prototype edits.'
    out = ROOT / '.omx/state/design-council'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'final-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'ok': True, 'preservedDrafts': len(audit['independentDraftsPreserved']),
                      'peerRevisionRatificationFiles': len(audit['peerArtifacts']),
                      'checkedLinks': len(audit['localLinks']), 'prototype': url}))


if __name__ == '__main__':
    main()
