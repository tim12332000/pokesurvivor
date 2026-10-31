"""Check design artifact links, provenance and arithmetic, without running game code."""
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent
data = json.loads((root / 'provenance.json').read_text(encoding='utf-8'))
assert set(data['prompts']) == {'concept', 'transformation'}
for output in data['outputs']:
    assert hashlib.sha256((root / output['file']).read_bytes()).hexdigest() == output['sha256']
for doc in root.glob('*.md'):
    for link in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
        if '://' not in link and not link.startswith('#'):
            assert (doc.parent / link.split('#')[0]).exists(), (doc.name, link)
rows = []
for name, base, cd, triple, duration in [
    ('柳', 30, .9, 1, .44), ('椿', 120, 5, 3, .74),
    ('唐松', 96, 6, 3, .70), ('鐵線花', 240, 8, 1.8, 1.40),
    ('早蕨', 300, 12, 3, 1.48),
]:
    damage = [base * scale for scale in (1, 1.2, 1.4, 1.7, 2)]
    rows.append({'skill': name, 'damage': damage,
                 'single_dps': [round(d / cd, 6) for d in damage],
                 'three_enemy_dps': [round(d * triple / cd, 6) for d in damage],
                 'interval_with_10_cdr_cards': max(cd * .92 ** 10, duration)})
combo = (240 / 8 + (1 - 1.4 / 8) * 30 / .9) * 1.32
assert abs(combo - 75.9) < 1e-9
result = {'scope': 'design artifacts only; no gameplay validation', 'rows': rows,
          'willow_clematis_combo_at_attack_1_32': combo,
          'curse_rank5_ideal_average': 1 + .25 * 8 / 30,
          'willow_target_caps_q0_to_q5': [min(3, int(1.25 ** q)) for q in range(6)],
          'local_links': 'pass', 'image_hashes': 'pass', 'prompt_records': 'pass'}
(root / 'calculation-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PASS: local document links, two image hashes, two prompts, five-rank DPS and combo arithmetic.')
