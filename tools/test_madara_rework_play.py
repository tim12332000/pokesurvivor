"""Natural level-one play observation, without combat/XP/spawner interventions.

The frozen local release snapshot is excluded from Git. Recreate it by copying
dist-digimon into art-review/madara/rework-play/baseline-site before running.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_jujutsu import CHROME

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('REWORK_PLAY_OUT', ROOT / 'art-review/madara/rework-play'))
SITE = Path(os.environ.get('REWORK_PLAY_SITE', OUT / 'baseline-site'))
URL = os.environ.get('REWORK_PLAY_URL', 'http://127.0.0.1:8347/art-review/madara/rework-play/baseline-site/.omx/digimon.html?lang=zh-TW&layout=wide')
SEED = 231106
TARGET = float(os.environ.get('REWORK_PLAY_SECONDS', '120'))

OBSERVE = r"""seed => {
 const R=window.Rework={seed,worldSeeds:[],casts:[],hits:[],pulses:[],samples:[],formationChanges:[],offers:[],ledger:[],items:[],errors:[],lastSample:-1};
 let randomState=seed>>>0;Math.random=()=>{randomState=(Math.imul(randomState,1664525)+1013904223)>>>0;return randomState/4294967296};
 const reset=G.World.reset;G.World.reset=function(requested){const used=R.worldSeeds.length?requested:seed;R.worldSeeds.push({requested,used});return reset.call(this,used)};
 const cast=G.Player.prototype.cast;G.Player.prototype.cast=function(m,...args){
  if(this===G.Game.player)R.casts.push({t:G.Game.st.time,id:m.id,x:this.x,y:this.y,rank:m.lvl});
  return cast.call(this,m,...args);
 };
 const hurt=G.Enemy.prototype.hurt;G.Enemy.prototype.hurt=function(...args){
  const before=this.hp,source=args[6],skill=args[7],result=hurt.apply(this,args);
  if(source===G.Game.player||source?.sourceOwner===G.Game.player)R.hits.push({t:G.Game.st.time,id:skill||null,raw:args[0],loss:before-this.hp,
   target:this.id,x:this.x,y:this.y,source:source===G.Game.player?'owner-player':'self-clone'});
  return result;
 };
 const brief=a=>a?{kind:a.kind,phase:a.phase,age:a.age,index:a.index,pulseIndex:a.pulseIndex,moveId:a.m?.id}:null;
 const snapshot=()=>{const p=G.Game.player;return p?{level:p.level,hp:p.hp,maxHp:p.maxHp,kills:p.kills,xp:p.xp,xpNext:p.xpNext,
  damage:p.dmgDealt,x:p.x,y:p.y,quantity:p.quantityPicks||0,statsTaken:{...p.statsTaken},moves:p.moves.map(m=>({id:m.id,rank:m.lvl,cd:m.t,passive:!!m.passive,auto:!!m.autoCast}))}:null};
 R.snapshot=snapshot;
 const oldPulse=G.CombatPulse.onPulse;G.CombatPulse.onPulse=info=>{
  if((info.owner===G.Game.player||info.owner?.sourceOwner===G.Game.player)&&(info.primaryHits||info.secondaryHits))R.pulses.push({t:G.Game.st.time,channel:info.channel,moveId:info.moveId,castId:info.castId,
   contactPulseIndex:info.contactPulseIndex,primaryHits:info.primaryHits,primaryDamage:info.primaryDamage,secondaryHits:info.secondaryHits,secondaryDamage:info.secondaryDamage,owner:info.owner===G.Game.player?'owner-player':'self-clone'});
  oldPulse?.(info);
 };
 const show=G.RunUI.showLevelUp;G.RunUI.showLevelUp=function(level,list,cb,...args){
  const offer={serial:R.offers.length,level,t:G.Game.st.time,wallSeconds:performance.now()/1000,options:list.map(c=>({key:c.key,type:c.type,title:c.title,desc:c.desc}))};
  R.offers.push(offer);R.currentOffer=offer;
  return show.call(this,level,list,function(card){const before=snapshot(),t=G.Game.st.time;cb(card);
   R.ledger.push({cost:R.ledger.length+1,t,wallSeconds:performance.now()/1000,key:card.key,type:card.type,title:card.title,description:card.desc,offer:offer.serial,before,after:snapshot()});
   if(R.currentOffer===offer)R.currentOffer=null;
  },...args);
 };
 function sample(){const p=G.Game.player,t=G.Game.st.time;
  if(p&&G.Game.state==='playing'&&t-R.lastSample>=.25){
   R.lastSample=t;const enemies=G.EnemyMgr.all().filter(e=>!e.dead&&e.hp>0),distance=enemies.length?Math.min(...enemies.map(e=>Math.hypot(e.x-p.x,e.y-p.y))):null;
   const ms=G.NarutoMadara?.stateFor?.(p),guardian=G.NarutoMadara?.guardianPose?.(p);
   if(ms&&(!R.lastFormation||ms.impetus!==R.lastFormation.impetus||ms.perfectCount!==R.lastFormation.perfectCount)){
    const change={t,wallSeconds:performance.now()/1000,impetus:ms.impetus,perfectCount:ms.perfectCount,army:ms.army?.length||0,body:G.NarutoMadara.pose(p),guardian:guardian?{form:guardian.form,phase:guardian.phase,remaining:guardian.remaining}:null};
    R.formationChanges.push(change);R.lastFormation=change;
   }
   R.samples.push({t,wallSeconds:performance.now()/1000,state:G.Game.state,...snapshot(),madaraPose:G.NarutoMadara?.pose?.(p)||null,leeAction:brief(G.NarutoLee?.activeFor?.(p)),
    madara:ms?{version:G.NarutoMadara.version||1,impetus:ms.impetus,perfectCount:ms.perfectCount,casts:{...ms.casts},
     guardian:guardian?{form:guardian.form,phase:guardian.phase,perfect:guardian.perfect,remaining:guardian.remaining}:null,
     army:(ms.army||ms.clones||[]).map(a=>({serial:a.serial,role:a.role,x:a.x,y:a.y,phase:a.phase})),
     meteors:(ms.meteors||[]).map(m=>({second:!!m.second,fragment:!!m.fragment,landed:!!m.landed,phase:m.phase,x:m.x,y:m.y})),fronts:ms.fires?.length}:null,
    enemies:enemies.length,nearestEnemy:distance,
    near150:enemies.filter(e=>Math.hypot(e.x-p.x,e.y-p.y)<=150).length,casts:R.casts.length,hits:R.hits.length});
  }requestAnimationFrame(sample);
 }requestAnimationFrame(sample);return {seed,permanent:G.DB.upgradesOf(G.DB.save.partner)};
}"""


def frame_for(page):
    for _ in range(300):
        for frame in page.frames:
            try:
                if frame.evaluate("typeof G==='object'&&!!G.Game&&!!G.Naruto"):
                    return frame
            except Exception:
                pass
        page.wait_for_timeout(100)
    raise RuntimeError('production entry did not load')


def card_priority(card):
    if card['type'] == 'new':
        return 0
    if card['type'] == 'up':
        return 1
    if card['key'] == 'stat:quantity':
        return 2
    return {'stat:atk': 3, 'stat:cd': 4, 'stat:maxHealthPercent': 5, 'stat:heal': 6}.get(card['key'], 10)


def analyze(run):
    samples, casts, hits = run['samples'], run['casts'], run['hits']
    bins = []
    for start in range(0, int(run['time']) + 1, 15):
        end = min(start + 15, run['time'])
        if end <= start:
            continue
        ss = [s for s in samples if start <= s['t'] < end]
        cs = [c for c in casts if start <= c['t'] < end]
        hs = [h for h in hits if start <= h['t'] < end]
        near = [s for s in ss if s['near150'] > 0]
        windows = [s for s in near if not any(s['t'] - .5 <= c['t'] <= s['t'] for c in casts)]
        no_contacts = [s for s in near if not any(s['t'] - .5 <= h['t'] <= s['t'] for h in hits)]
        bins.append({'from': start, 'to': end, 'casts': len(cs), 'hits': len(hs), 'hpLostByEnemies': sum(h['loss'] for h in hs),
                     'nearEnemySamples': len(near), 'nearEnemyNoCastWithinHalfSecondSamples': len(windows),
                     'nearEnemyNoHitWithinHalfSecondSamples': len(no_contacts),
                     'ending': ss[-1] if ss else None})
    counts = {}
    for c in casts:
        counts[c['id']] = counts.get(c['id'], 0) + 1
    madara = [s['madara'] for s in samples if s.get('madara')]
    formation = {'perfectObserved': any(s.get('guardian', {}).get('perfect') for s in madara if s.get('guardian')),
                 'armyObserved': any(s.get('army') for s in madara),
                 'firstMainImpactObserved': any(any(m['landed'] and not m['second'] and not m['fragment'] for m in s.get('meteors', [])) for s in madara),
                 'secondMainImpactObserved': any(any(m['landed'] and m['second'] for m in s.get('meteors', [])) for s in madara),
                 'moduleCasts': madara[-1].get('casts', {}) if madara else {},
                 'perfectCount': max((s.get('perfectCount') or 0 for s in madara), default=0)}
    formation['completeObserved'] = all(formation[k] for k in ['perfectObserved', 'armyObserved', 'firstMainImpactObserved', 'secondMainImpactObserved'])
    windows = {}
    for sample in samples:
        state = sample.get('madara')
        guardian = state.get('guardian') if state else None
        if guardian and guardian.get('perfect'):
            key = state.get('perfectCount')
            if key not in windows:
                windows[key] = {'perfectCount': key, 'from': sample['t'], 'to': sample['t'],
                                'wallFrom': sample.get('wallSeconds'), 'wallTo': sample.get('wallSeconds')}
            windows[key]['to'] = sample['t']
            windows[key]['wallTo'] = sample.get('wallSeconds')
    formation['perfectWindows'] = [{**w, 'observedDuration': w['to'] - w['from']} for w in windows.values()]
    formation['fullPerfectCyclesObserved'] = sum(w['observedDuration'] >= 5.2 for w in formation['perfectWindows'])
    army_learn = next((c['t'] for c in run['ledger'] if c['key'] == 'new:naruto-madara-clones'), None)
    guardian_rank = lambda sample: next((m['rank'] for m in sample.get('moves', []) if m['id'] == 'naruto-madara-susanoo'), 0)
    perfect_unlock = next(({'t': c['t'], 'cost': c['cost'], 'key': c['key']} for c in run['ledger'] if guardian_rank(c['after']) >= 3), None)
    formation['perfectUnlock'] = perfect_unlock
    formation['perfectSamplesWithArmy'] = sum(bool(s.get('madara', {}).get('army')) and bool(s.get('madara', {}).get('guardian', {}).get('perfect'))
                                               for s in samples if s.get('madara') and s['madara'].get('guardian'))
    army_comparison = None
    if army_learn is not None:
        army_comparison = {}
        for name, start, end in [('before', max(0, army_learn - 60), army_learn), ('after', army_learn, min(run['time'], army_learn + 60))]:
            selected = [s for s in samples if start <= s['t'] and (s['t'] <= end if name == 'after' else s['t'] < end) and s.get('madara')]
            channels = {}
            for pulse in run.get('pulses', []):
                if start <= pulse['t'] and (pulse['t'] <= end if name == 'after' else pulse['t'] < end):
                    channel = channels.setdefault(pulse['channel'], {'primaryHits': 0, 'primaryDamage': 0, 'secondaryHits': 0})
                    for key in channel:
                        channel[key] += pulse[key]
            first = selected[0]['madara'] if selected else {}
            last = selected[-1]['madara'] if selected else {}
            army_comparison[name] = {'from': start, 'to': end, 'seconds': end - start, 'channels': channels,
                                     'initialImpetus': first.get('impetus'), 'finalImpetus': last.get('impetus'),
                                     'initialPerfectCount': first.get('perfectCount'), 'finalPerfectCount': last.get('perfectCount'),
                                     'initialGuardianRank': guardian_rank(selected[0]) if selected else None,
                                     'finalGuardianRank': guardian_rank(selected[-1]) if selected else None,
                                     'perfectCountDelta': (last.get('perfectCount') or 0) - (first.get('perfectCount') or 0),
                                     'formationChanges': [c for c in run.get('formationChanges', []) if start <= c['t'] and (c['t'] <= end if name == 'after' else c['t'] < end)]}
    module_counts = run.get('finalMadara', {}).get('casts', {}) if run.get('finalMadara') else formation['moduleCasts']
    authoritative = module_counts if any(s.get('version') == 2 for s in madara) else counts
    return {'bins': bins, 'castsBySkill': authoritative, 'bodyCastEventsBySkill': counts,
            'binCastScope': 'Player.cast body event timestamps; autonomous guardian counter is reported in castsBySkill/moduleFormation',
            'moduleFormation': formation, 'armyBeforeAfter': army_comparison, 'totalHits': len(hits),
            'firstHitAt': hits[0]['t'] if hits else None,
            'firstLearnedNewSkill': next(({'at': c['t'], 'cost': c['cost'], 'key': c['key']} for c in run['ledger'] if c['type'] == 'new'), None)}


def play(browser, dex, slug, attempt, limit):
    folder = OUT / slug / f'attempt-{attempt}'
    folder.mkdir(parents=True, exist_ok=True)
    context = browser.new_context(viewport={'width': 1100, 'height': 850}, service_workers='block',
                                  record_video_dir=str(folder / 'raw-video'), record_video_size={'width': 1100, 'height': 850})
    page = context.new_page()
    errors, missing = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('response', lambda r: missing.append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
    page.goto(URL)
    frame = frame_for(page)
    frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if frame.locator('#tap-start').is_visible():
        frame.locator('#tap-start').click()
    frame.locator(f'[data-quick-naruto="{dex}"]').click()
    frame.wait_for_function(f'G.NarutoAssets.ready({dex})')
    permanent = frame.evaluate('G.DB.upgradesOf(G.DB.save.partner)')
    assert not any(permanent.values()), f'fresh context has permanent upgrades: {permanent}'
    frame.evaluate(OBSERVE, SEED)
    frame.locator('#scr-menu [data-go="play"]').click()
    frame.wait_for_function(f'G.Game.player?.dex==={dex}&&G.Game.state==="playing"')
    initial = frame.evaluate('Rework.snapshot()')
    assert initial['level'] == 1, initial
    screenshots, last_card_serial, held, next_image, next_progress = [], None, None, 0, 30
    wall_started = time.monotonic()
    wall_limit = float(os.environ.get('REWORK_PLAY_WALL_LIMIT', max(240, limit * 2)))
    while time.monotonic() - wall_started < wall_limit:
        state = frame.evaluate("({state:G.Game.state,time:G.Game.st.time,dead:!!G.Game.player?.dead,offer:Rework.currentOffer})")
        game_time = state['time']
        if game_time >= limit or state['state'] == 'over' or state['dead']:
            break
        if game_time >= next_progress:
            progress = frame.evaluate('({t:G.Game.st.time,...Rework.snapshot(),cards:Rework.ledger.length})')
            (folder / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
            print(slug, 'native seconds', round(game_time, 1), 'level', progress['level'], 'cards', progress['cards'], 'hp', progress['hp'], flush=True)
            next_progress += 30
        if state['state'] == 'levelup' and state['offer']:
            offer = state['offer']
            if offer['serial'] != last_card_serial:
                if held:
                    page.keyboard.up(held)
                    held = None
                chosen = min(range(len(offer['options'])), key=lambda i: (card_priority(offer['options'][i]), i))
                page.screenshot(path=str(folder / f'card-{offer["serial"]}-at-{game_time:.1f}.png'))
                frame.locator('#cards .card').nth(chosen).click()
                last_card_serial = offer['serial']
        elif frame.locator('#scr-item').is_visible():
            frame.locator('#item-cards .card').first.click()
        elif frame.locator('#scr-bond').is_visible():
            frame.locator('#bond-cards .card').first.click()
        elif state['state'] == 'playing':
            key = ['KeyD', 'KeyS', 'KeyA', 'KeyW'][int(game_time // 1.5) % 4]
            if key != held:
                if held:
                    page.keyboard.up(held)
                page.keyboard.down(key)
                held = key
            if game_time >= next_image:
                name = f'play-{game_time:.1f}.png'
                page.screenshot(path=str(folder / name))
                screenshots.append({'t': game_time, 'path': name})
                next_image += 15
        elif state['state'] == 'paused':
            frame.locator('#btn-resume').click()
        page.wait_for_timeout(80)
    if held:
        page.keyboard.up(held)
    data = frame.evaluate("(()=>({seed:Rework.seed,worldSeeds:Rework.worldSeeds,casts:Rework.casts,hits:Rework.hits,pulses:Rework.pulses,samples:Rework.samples,formationChanges:Rework.formationChanges,offers:Rework.offers,ledger:Rework.ledger,time:G.Game.st.time,state:G.Game.state,dead:!!G.Game.player?.dead,final:Rework.snapshot(),finalMadara:G.NarutoMadara?.stats?.(G.Game.player)||null}))()")
    page.screenshot(path=str(folder / 'final.png'))
    data.update({'dex': dex, 'hero': slug, 'attempt': attempt, 'initial': initial, 'permanent': permanent,
                 'wallSeconds': time.monotonic() - wall_started, 'errors': errors, 'missing': missing, 'screenshots': screenshots,
                 'stopReason': 'death' if data['dead'] else 'target-time' if data['time'] >= limit else 'native-over' if data['state'] == 'over' else 'wall-time-limit'})
    (folder / 'run.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    data['analysis'] = analyze(data)
    video = page.video
    context.close()
    video.save_as(str(folder / 'native-play.webm'))
    video.delete()
    (folder / 'run.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    return data


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    max_attempts = int(os.environ.get('REWORK_PLAY_ATTEMPTS', '6'))
    sources = ['.omx/naruto-madara.js', '.omx/naruto-madara-camera.js', '.omx/digimon-size.js', '.omx/naruto-lee.js',
               '.omx/naruto-skills.js', 'js/game.js', 'js/main.js', 'js/core/audio.js', '.omx/digimon.html',
               'art-review/madara/runtime.js', 'art-review/madara/frames.json']
    sources += [str(p.relative_to(SITE)).replace('\\', '/') for p in (SITE / 'art-review/madara').glob('*.png')]
    hashes = {name: hashlib.sha256((SITE / name).read_bytes()).hexdigest() for name in sources if (SITE / name).exists()}
    report = {'url': URL, 'seed': SEED, 'sourceHashes': hashes, 'targetNativeSecondsPerHero': TARGET, 'maxAttemptsPerHero': max_attempts,
              'policy': 'Clockwise square: D/S/A/W, one side per 1.5 native game seconds; new > upgrade > quantity > atk > cd > health > first; no rerolls; native UI clicks.',
              'videoTiming': 'wallSeconds fields use page navigation performance time; recording may have a small pre-navigation lead. Native HUD game time remains authoritative.',
              'constraints': ['Fresh isolated save and all permanent upgrades zero.', 'Native default speed 2 retained; no manual cast/time stepping/XP/level/invulnerability/spawner changes.',
                              'Same world seed and initial PRNG stream; native frames, combat and random consumption diverge, so encounters are not paired.',
                              f'Death is recorded; identical policy and seed restart until cumulative observed game time >= target, maximum {max_attempts} attempts.',
                              'Near-enemy 150px and half-second no-cast/no-enemy-hit counts are descriptive, not proof of idle bugs; range, cooldown, multi-hit actions and prop attacks differ.'], 'heroes': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        selected = os.environ.get('REWORK_PLAY_HEROES', 'madara,lee').split(',')
        for dex, slug in [(30016, 'madara'), (30006, 'lee')]:
            if slug not in selected:
                continue
            total, runs = 0, []
            for attempt in range(1, max_attempts + 1):
                print(slug, 'attempt', attempt, 'remaining', TARGET - total, flush=True)
                run = play(browser, dex, slug, attempt, TARGET - total)
                total += run['time']
                runs.append({'path': f'{slug}/attempt-{attempt}/run.json', 'time': run['time'], 'dead': run['dead'],
                             'level': run['final']['level'], 'cards': len(run['ledger']), 'kills': run['final']['kills'], 'analysis': run['analysis'],
                             'errors': run['errors'], 'missing': run['missing']})
                report['heroes'][slug] = {'totalObservedGameSeconds': total, 'attempts': runs}
                (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
                print(slug, 'observed', total, 'death', run['dead'], 'level', run['final']['level'], 'cards', len(run['ledger']), flush=True)
                if total >= TARGET or run['time'] < 1:
                    break
        browser.close()
    report['observationComplete'] = all(v['totalObservedGameSeconds'] >= TARGET for v in report['heroes'].values()) and len(report['heroes']) == len(selected)
    report['naturalFormationComplete'] = any(a['analysis'].get('moduleFormation', {}).get('completeObserved', False)
                                             for a in report['heroes'].get('madara', {}).get('attempts', []))
    report['sourceHashesAfter'] = {name: hashlib.sha256((SITE / name).read_bytes()).hexdigest() for name in hashes}
    report['sourceStable'] = report['sourceHashesAfter'] == report['sourceHashes']
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'complete': report['observationComplete'], 'naturalFormationComplete': report['naturalFormationComplete'],
                      'heroes': {k: v['totalObservedGameSeconds'] for k, v in report['heroes'].items()}}))


if __name__ == '__main__':
    main()
