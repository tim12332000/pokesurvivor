"""Audit the complete design delivery against current authoritative artifacts."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
report = json.loads((ROOT/'evidence/verification.json').read_text(encoding='utf8'))
assert report['status']=='pass'
assert set(report['viewports'])=={'desktop','mobile','mobile-landscape'}
for path,digest in report['file_hashes'].items():
    assert sha(ROOT/path)==digest,('source changed after browser verification',path)
assert sha(ROOT/'evidence/kimimaro-motion-reel.webm')==report['reel']['sha256']
assert report['reel']['duration']>=22
assert len(report['reel']['cases'])==10
for viewport,result in report['viewports'].items():
    assert not result['page_errors'] and not result['http_errors'] and not result['request_failures'],viewport
    assert len(result['skills'])==10,viewport
data = json.loads(subprocess.run(['node','-e',
    "process.stdout.write(JSON.stringify(require('./design-data.js')))"],
    cwd=ROOT,capture_output=True,text=True,encoding='utf8',check=True).stdout)
assert len(data['skills'])==8
expected={'willow','camellia','bullets','larch','vine','flower','bracken','lily'}
assert {s['id'] for s in data['skills']}==expected
calculations=json.loads((ROOT/'calculation-results-v3.json').read_text(encoding='utf8'))
for skill in data['skills']:
    assert len(skill['damage'])==5 and skill['duration']>0 and skill['cd']>0
    row=next(row for row in calculations['skills'] if row['name'] in skill['name'])
    assert all(abs(a-b)<1e-8 for a,b in zip(row['rank_base_damage'],skill['damage'])),skill['id']
actors=json.loads((ROOT/'actors.json').read_text(encoding='utf8'))
for form in ('normal','curse'):
    assert len(actors[form]['frames'])==16
    assert sha(ROOT/actors[form]['image'])==actors[form]['sha256']
    assert all(f['clipRuns'] for f in actors[form]['frames'].values())
provenance=json.loads((ROOT/'provenance-final.json').read_text(encoding='utf8'))
for key in ('normal','curseDraft','curse','curseSpacing'):
    assert len(provenance[key]['prompt'])>500
    assert sha(ROOT/provenance[key]['output'])==provenance[key]['outputSha256']
assert sha(ROOT/'actors.json')==provenance['indexing']['sha256']
required=['final-spec.md','asset-production-spec.md','README.md','presentation-v3.md','balance-v3.md',
    'research-assets.md','research-video.md','research-mobile-games.md','research-console-games.md',
    'research-community-games.md','research-gacha-games.md','research-official-motion-samples.md',
    'game-fit-review.md','evidence/overview.png','evidence/mobile-preview.png','visual-review-final.json']
assert all((ROOT/p).is_file() for p in required)
visual=json.loads((ROOT/'evidence/art-verdict.json').read_text(encoding='utf8'))
assert visual['verdict']=='pass' and not visual['blocking_issues']
assert set(visual['criteria'])=={'consistency','readability','peak_hit'}
assert all(c['verdict']=='pass' and c['evidence'] for c in visual['criteria'].values())
assert all((ROOT/p).is_file() for p in ['evidence/game-reference.png','evidence/art-phases.png','evidence/art-after.png'])
effects=json.loads((ROOT/'effects.json').read_text(encoding='utf8'))
effect_path=ROOT/effects['image']
assert sha(effect_path)==effects['sha256']
assert len(effects['frames'])==12 and effects['width']<=768 and effects['height']<=576
assert effect_path.stat().st_size<=256*1024
assert effects['width']*effects['height']*4<=int(1.75*1024*1024)
assert effects['budget']['maxPillars']==36 and effects['budget']['maxTransientParticles']==20
assert (ROOT/'visual-review-vfx-after.json').is_file()
stage=json.loads((ROOT/'stage-assets.json').read_text(encoding='utf8'))
assert stage['pixelScale']==2 and stage['sourceTransferBytes']<=24*1024
for sprite in stage['sprites']:
    for key in ('idle','hurt'):
        assert sha(ROOT/sprite[key]['image'])==sprite[key]['sha256']
for prop in stage['props'].values():
    assert sha(ROOT/prop['image'])==prop['sha256']
result={'status':'pass','scope':'complete design package and isolated preview, not game integration',
    'requirements':{
        'eight_attacks_and_curse':{'status':'pass','evidence':['final-spec.md','design-data.js']},
        'five_rank_numbers_and_quantity':{'status':'pass','evidence':['calculation-results-v3.json']},
        'materials_and_game_video_research':{'status':'pass','evidence':required[5:13]},
        'game_fit':{'status':'pass','evidence':['game-fit-review.md','final-spec.md']},
        'images_and_two_forms':{'status':'pass','physical_key_poses':32,'evidence':['actors.json','provenance-final.json']},
        'animated_performance_and_controls':{'status':'pass','evidence':['evidence/verification.json','evidence/kimimaro-motion-reel.webm']},
        'desktop_and_mobile':{'status':'pass','viewports':list(report['viewports'])},
        'visual_review':{'status':'pass','criteria':list(visual['criteria']),'evidence':['evidence/art-verdict.json','evidence/art-phases.png','evidence/game-reference.png']},
        'source_evidence_still_current':{'status':'pass','files':report['file_hashes']},
        'bounded_bone_effect_revision':{'status':'pass','evidence':['vfx-revision.md','effects.json','visual-review-vfx-after.json'],
            'runtimeBytes':effect_path.stat().st_size,'decodedRgbaBytes':effects['width']*effects['height']*4,
            'maxPillars':36,'maxSecondaryParticles':20},
        'coherent_game_art_context':{'status':'pass','evidence':['art-direction.md','stage-assets.json'],
            'existingStageBytes':stage['sourceTransferBytes'],'pixelScale':stage['pixelScale']}},
    'limits':['Preview enemies are demonstration targets, not actual game AI.',
              'Actual play balance, complete directional frame animation and game integration are future implementation work.',
              'Sound is procedural preview audio; exported reel is silent.']}
(ROOT/'evidence/completion-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS: full design requirement audit, current-source hashes, 32 poses, eight rank tables and three-viewport browser evidence.')
