"""v2 design arithmetic only; no combat simulation or gameplay claims."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
scales = [1, 1.2, 1.4, 1.7, 2]
skills = [('柳',30,.9,.64,1),('椿',120,5,.74,3),('唐松',96,6,.70,3),
          ('鐵線花',240,8,1.40,1.8),('早蕨',300,12,1.48,3)]
result = {'scope':'paper arithmetic, one active, no switching or bond queue', 'skills':[], 'quantity':[]}
for name, base, cd, duration, triple in skills:
    result['skills'].append({'name':name,'rank_damage':[base*s for s in scales],
        'single_dps':[round(base*s/cd,6) for s in scales],
        'three_enemy_dps':[round(base*s*triple/cd,6) for s in scales],
        'interval_10_cdr_cards':max(cd*.92**10,duration)})
for q in [0,1,2,3,4,5,10,20]:
    n=min(8,int(4*1.25**q));d=30*n/4
    result['quantity'].append({'cards':q,'hits':n,'rank1_damage':d,'dps':d/.9,
        'dps_10_cdr_cards':d/max(.9*.92**10,.64),
        'hit_times':[round(.12+i*.48/(n-1),6) for i in range(n)],
        'willow_clematis_continuous_dps_at_1_32':(240/8+(1-1.4/8)*d/.9)*1.32})
result['curse_average_bonus_percent']=[100*b*8/30 for b in [.1,.125,.15,.175,.2]]
result['guard']={'uptime_no_cards':.7/6,'uptime_10_cdr_cards':.7/(6*.92**10),
                 'received_with_melee_discount':.75*.8}
assert [r['hits'] for r in result['quantity'][:5]]==[4,5,6,7,8]
assert abs(result['quantity'][1]['willow_clematis_continuous_dps_at_1_32']-84.975)<1e-9
assert abs(sum([.25,.25,.5])-1)<1e-9
assert abs(sum([.2,.8])-1)<1e-9
(root/'calculation-results-v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS: v2 five ranks, quantity q0-20, CDR animation limits, combo estimates, guard and curse arithmetic.')
