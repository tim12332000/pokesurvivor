"""Paper balance for eight Kimimaro candidates; does not import game code."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCALES = [1, 1.2, 1.4, 1.7, 2]
SKILLS = [
    ('柳', 30, .9, .64, 1),
    ('椿', 120, 5, .74, 3),
    ('十指穿彈', 45, 2.4, .60, 1),
    ('唐松', 96, 6, .70, 3),
    ('鐵線花・蔓', 48, 8, .70, 1),
    ('鐵線花・花', 192, 8, .86, 2),
    ('早蕨', 300, 12, 1.48, 3),
    ('鬼百合', 100, 6, .90, 3),
]
data = {'scope': 'paper arithmetic; full hits, A=1, no switching, no four-move queue simulation',
        'attack_multiplier': 1.32, 'skills': [], 'quantity': [], 'clematis_combo': []}
for name, base, cd, duration, crowd in SKILLS:
    data['skills'].append({'name': name, 'rank_base_damage': [base*s for s in SCALES],
        'single_dps': [round(base*s/cd, 6) for s in SCALES],
        'three_enemy_total_dps': [round(base*s*crowd/cd, 6) for s in SCALES],
        'cast_duration': duration, 'base_cd': cd,
        'interval_10_cdr_cards': max(cd*.92**10, duration)})
for q in [0, 1, 2, 3, 4, 5, 10, 20]:
    willow_n = min(8, math.floor(4*1.25**q))
    bullets_n = min(15, math.floor(5*1.25**q))
    three_shares = [bullets_n//3 + (i < bullets_n % 3) for i in range(3)]
    assert sum(three_shares) == bullets_n
    data['quantity'].append({'cards': q, 'willow_hits': willow_n,
        'willow_rank1_dps': willow_n*7.5/.9,
        'bullet_count': bullets_n, 'bullet_rank1_damage': bullets_n*9,
        'bullets_rank1_dps': bullets_n*9/2.4,
        'bullets_rank1_dps_10_cdr_cards': bullets_n*9/max(2.4*.92**10, .60),
        'three_target_round_robin_shot_counts': three_shares,
        'three_target_rank1_damage_each': [n*9 for n in three_shares]})
for scale in SCALES:
    vine, flower = 48*scale, 192*scale
    assert abs(vine + flower - 240*scale) < 1e-9
    assert abs(vine + flower + 2*flower*.5 - 432*scale) < 1e-9
    interval = max(8 + .54, 1.4)
    data['clematis_combo'].append({'scale': scale, 'main_damage': vine+flower,
        'three_enemy_total_damage': vine+flower+2*flower*.5,
        'steady_interval': interval, 'single_dps': (vine+flower)/interval,
        'three_enemy_total_dps': (vine+flower+2*flower*.5)/interval,
        'normal_duration':1.4, 'standalone_duration_sum':.70+.86,
        'vine_cd_start':0, 'flower_cd_start':.54,
        'with_willow_rank1_q0_continuous_dps_at_scale': (vine+flower)/interval+(1-1.4/interval)*(30*scale/.9)})
data['curse_average_bonus_percent'] = [100*b*8/30 for b in [.10,.125,.15,.175,.20]]
data['combo_reservation_policy'] = 'same group by skill IDs, bounded wait <=.54 seconds, no older eligible queued action, no filler animation crossing reservation'

data['combo_start_schedule'] = [{'vine': round(i*8.54, 6), 'flower': round(i*8.54+.54, 6)} for i in range(4)]
data['combo_interval_10_cdr_cards_both_ready_reservation'] = max(8*.92**10+.54, 1.4)
for previous, current in zip(data['combo_start_schedule'], data['combo_start_schedule'][1:]):
    assert current['vine'] >= previous['flower'] + 8 - 1e-9
    assert current['flower'] >= previous['flower'] + 8 - 1e-9
data['willow_accelerating_hit_times'] = {}
for n in range(4,9):
    gaps=[.85**i for i in range(n-1)]
    times=[.12]
    for gap in gaps:
        times.append(times[-1]+.48*gap/sum(gaps))
    assert abs(times[-1]-.60)<1e-9
    data['willow_accelerating_hit_times'][str(n)]=times

data['guard'] = {'uptime_no_cards': .7/6, 'uptime_10_cdr_cards':.7/(6*.92**10),
                 'damage_received_with_melee_discount': .75*.8}
assert [r['bullet_count'] for r in data['quantity'][:6]] == [5,6,7,9,12,15]
assert [r['willow_hits'] for r in data['quantity'][:5]] == [4,5,6,7,8]
assert abs(data['clematis_combo'][0]['single_dps']-240/8.54)<1e-9
(ROOT/'calculation-results-v3.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print('PASS: eight candidates/five ranks, quantity caps, bounded volley split, split-clematis budget and CDR intervals.')
