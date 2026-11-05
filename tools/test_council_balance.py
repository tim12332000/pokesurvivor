"""Fixed-budget controlled comparison; no claim of human/full-run balance.

Uses legal native card recipes, seeded moving native enemies and the same
keyboard pursuit/orbit policy for all routes. Natural XP, spawning and loot are
excluded to keep the investment budget fixed. Results can reject a design; they
cannot establish universal win rates or real-device performance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_council_runtime import ROOT,HEROES,boot,runtime_hashes

ROUTES={30013:['blade','rika','balanced'],30014:['precision','spread','balanced'],30015:['control','counter','balanced']}
CASE=r"""({route,budget,threat,seed,seconds})=>{
 const A=JAcceptance,assert=A.assert;A.resume();G.Game.startRun();A.pause();const p=A.p(),baselineCd=p.cdMul,baselineCrit=p.critChance;
 A.reset();G.World.walkable=()=>true;G.Path.clear();p.cdMul=baselineCd;p.critChance=baselineCrit;p.statsTaken={};p.kills=0;p.dmgDealt=0;
 // Synthesized sound noise consumes Math.random after wall-clock throttling.
 // Exclude audio from the controlled RNG stream; restore the real API afterward.
 const nativeSfx=G.Audio.sfx;G.Audio.sfx=()=>{};
 let rng=seed>>>0;const random=Math.random;Math.random=()=>{rng=(Math.imul(1664525,rng)+1013904223)>>>0;return rng/4294967296};
 const held=new Set(),setKeys=desired=>{for(const k of held)if(!desired.has(k))window.dispatchEvent(new KeyboardEvent('keyup',{code:k}));for(const k of desired)if(!held.has(k))window.dispatchEvent(new KeyboardEvent('keydown',{code:k}));held.clear();for(const k of desired)held.add(k)};
 try{
  const records=G.TrialBuild.apply(p,route,budget);assert(records.length===budget,'recipe omitted investments');assert(p.level===budget+1,'recipe level/budget mismatch');
  assert(records.every((r,i)=>r.level===i+2),'non-native investment levels');
  const learned=records.filter(r=>r.key.startsWith('new:')).length;assert(learned===3,'missing or free learned skills in recipe '+learned);
  const loadout=p.moves.map(m=>({id:m.id,lvl:m.lvl,dmg:m.dmg,range:m.range,radius:m.radius,cd:m.cd}));
  const ignored=new Set(['id','name','desc','source_url','icon','type','kind','digiMode','learnLevel','lvl','dmg','cd','t','dealt','since','castAt','maxLvl']);
  const behavior=p.moves.map(m=>({id:m.id,fields:Object.fromEntries(Object.entries(m).filter(([k,v])=>!ignored.has(k)&&['number','boolean','string'].includes(typeof v)))}));
  // reset() deliberately disables existing moves for isolated geometry tests.
  // A route comparison must restore the starter as well as newly learned moves.
  // Otherwise the core beam never fires and maximum can never gain energy.
  for(const move of p.moves)move.t=0;
  const initialCooldowns=p.moves.map(m=>({id:m.id,t:m.t}));
  // Recipe sampling must not alter the paired encounter's formation/cooldowns.
  // A separate reset stream makes same seed/threat/budget actual same enemies.
  rng=seed>>>0;
  p.xp=0;p.xpNext=1e12;let taken=0;const hurt=p.hurt;p.hurt=function(...args){const hp=this.hp,r=hurt.apply(this,args);taken+=Math.max(0,hp-this.hp);return r};
  const enemies=[],factor=1+budget/10;
  function spawn(x,y,behavior,hp,spd,dmg,boss=false){const def={dex:boss?150:19,hp,spd,dmg,xp:0,behavior,shotDmg:dmg*.8,shotCd:1.4,range:225};
   const e=new G.Enemy(def,x,y,{hp:1,spd:1,dmg:1},boss);e.types=['normal'];G.EnemyMgr.add(e);enemies.push(e);return e;}
  if(threat==='boss')spawn(170,0,'charger',5500*(1+budget/20),38,24,true);
  else if(threat==='ranged')for(let i=0;i<10;i++){const a=i*Math.PI/5,r=190+Math.random()*40;spawn(Math.cos(a)*r,Math.sin(a)*r,i%3===0?'fan':'ranged',220*factor,25,10)}
  else if(threat==='support')for(let i=0;i<12;i++){const a=i*Math.PI/6,r=130+Math.random()*50;spawn(Math.cos(a)*r,Math.sin(a)*r,i<2?'healer':i===2?'shielder':'chase',190*factor,32,9)}
  else for(let i=0;i<12;i++){const a=i*Math.PI/6,r=85+Math.random()*55;spawn(Math.cos(a)*r,Math.sin(a)*r,'chase',170*factor,40,9)}
  const initialEnemies=enemies.map(e=>({x:e.x,y:e.y,hp:e.maxHp,spd:e.spd,dmg:e.dmg,behavior:e.behavior,shotCd:e.shotCd,skillCd:e.skillCd}));
  G.EnemyMgr.rebuildGrid();const initialHp=enemies.reduce((s,e)=>s+e.hp,0),dt=1/60,start=performance.now();let steps=0,distance=0,distSamples=0,firstHit=null,killTime=null;
  A.resume();
  for(let i=0;i<seconds*60&&!p.dead;i++){
   const t=i*dt;if(i%6===0){const x=Math.cos(t*.7)*60,y=Math.sin(t*.7)*60,dx=x-p.x,dy=y-p.y;setKeys(new Set([...(Math.abs(dx)>7?[dx>0?'KeyD':'KeyA']:[]),...(Math.abs(dy)>7?[dy>0?'KeyS':'KeyW']:[])]))}
   p.update(dt);G.Path.update(dt,[p]);G.EnemyMgr.update(dt,[p]);G.EnemyMgr.rebuildGrid();G.Combat.tick(dt,p,t);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,t);G.Combat.updateFields(dt);G.FX.update(dt);steps++;
   const alive=enemies.filter(e=>!e.dead);if(!alive.length){killTime=(i+1)*dt;break;}
   const d=Math.min(...alive.map(e=>Math.hypot(e.x-p.x,e.y-p.y)));distance+=d;distSamples++;
   if(firstHit===null&&enemies.some(e=>e.hp<e.maxHp))firstHit=t;
  }
  const api=p.dex===30013?G.JujutsuYuta:p.dex===30014?G.JjkRyu:G.JjkUro,s=api.stateFor(p);
  if(p.dex===30014)assert((s?.casts['jjk-ryu']||0)>0,'comparison disabled the core attack');
  const result={route,budget,threat,seed,seconds,baselineCd,records,loadout,behavior,initialEnemies,initialCooldowns,fixture:{flatWalkable:true,independentEncounterRng:true,allSkillsInitiallyReady:true,audioExcluded:true},stats:{...p.statsTaken},
   metrics:{alive:!p.dead,survivalSeconds:steps*dt,kills:enemies.filter(e=>e.dead).length,remainingEnemies:enemies.filter(e=>!e.dead).length,
    hp:p.hp,maxHp:p.maxHp,taken,enemyHpLoss:initialHp-enemies.reduce((sum,e)=>sum+Math.max(0,e.hp),0),killTime,firstHit,
    meanNearestDistance:distSamples?distance/distSamples:null,castCounts:s?{...(s.casts||s.castCounts||{})}:{},wallMs:performance.now()-start}};
  A.pause();return result;
 }finally{setKeys(new Set());Math.random=random;G.Audio.sfx=nativeSfx;A.pause();}
}"""

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--url',default=os.getenv('COUNCIL_URL','http://127.0.0.1:8337/.omx/digimon.html?lang=zh-TW'))
    ap.add_argument('--out',default=str(ROOT/'.omx/state/council-runtime/balance'));ap.add_argument('--seeds',default='17,73,131,197,251');ap.add_argument('--seconds',type=int,default=20);ap.add_argument('--heroes',default='yuta,ryu,uro');ap.add_argument('--budgets',default='10,19,35');ap.add_argument('--layout',choices=['wide','portrait','mobile'],default='wide');args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);seeds=[int(s) for s in args.seeds.split(',')];wanted=set(args.heroes.split(','))
    budgets=[int(n) for n in args.budgets.split(',')];url=args.url+('&layout=portrait' if args.layout=='portrait' else '')
    runner_hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['tools/test_council_balance.py','tools/test_council_runtime.py']}
    report={'scope':'Controlled fixed-card-budget scenarios, same seeded keyboard orbit controller; no natural XP/spawner/pickup progression, audio excluded from encounter RNG. Not human balance/real-device results.','methodVersion':'matched-encounter-v3-ready-skills-audio-isolation','runnerHashes':runner_hashes,'layout':args.layout,'sourceHashes':runtime_hashes(args.url),'seeds':seeds,'seconds':args.seconds,'cases':[],'reproducibility':{},'failures':[],'errors':[],'missing':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=__import__('test_jujutsu').CHROME,headless=True)
        for dex,slug in HEROES.items():
            if slug not in wanted:continue
            ctx=browser.new_context(viewport={'width':390,'height':844} if args.layout=='mobile' else {'width':1280,'height':900},device_scale_factor=2 if args.layout=='mobile' else 1,is_mobile=args.layout=='mobile',has_touch=args.layout=='mobile',service_workers='block');page,f,errors,missing=boot(ctx,dex,out,url)
            f.wait_for_function('G.TrialBuild&&G.JujutsuGrowth')
            f.evaluate('window.CouncilNativeSfx=G.Audio.sfx')
            for budget in budgets:
                for route in ROUTES[dex]:
                    for threat in ['close','ranged','support','boss']:
                        for seed in seeds:
                            try:report['cases'].append({'hero':slug,'viewport':f.evaluate('({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,worldRadius:G.Camera.outerRadius()})'),**f.evaluate(CASE,{'route':route,'budget':budget,'threat':threat,'seed':seed,'seconds':args.seconds})})
                            except Exception as e:
                                report['failures'].append(f'{slug}/{budget}/{route}/{threat}/{seed}: {e}')
                                page.screenshot(path=str(out/f'{slug}-failure.png'))
                        print(slug,budget,route,threat,'cases',len(report['cases']),flush=True)
                        (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            # Replaying the same investment/encounter after other routes must
            # reproduce combat, independent of audio throttle history or timing.
            probe=next(c for c in report['cases'] if c['hero']==slug and c['budget']==budgets[-1] and c['route']==('counter' if slug=='uro' else 'balanced') and c['threat']=='ranged' and c['seed']==seeds[0])
            metrics=lambda c:{k:v for k,v in c['metrics'].items() if k!='wallMs'}
            checks=[]
            for _ in range(2):
                f.evaluate(CASE,{'route':ROUTES[dex][0],'budget':budgets[0],'threat':'support','seed':seeds[-1],'seconds':args.seconds})
                repeated=f.evaluate(CASE,{k:probe[k] for k in ['route','budget','threat','seed','seconds']})
                checks.append(metrics(repeated)==metrics(probe))
            if not all(checks):report['failures'].append('non-reproducible paired encounter after interleaving: '+slug)
            if not f.evaluate('G.Audio.sfx===CouncilNativeSfx'):report['failures'].append('audio API not restored after comparison: '+slug)
            report['reproducibility'][slug]={'afterInterleavedCases':checks,'audioRestored':f.evaluate('G.Audio.sfx===CouncilNativeSfx')}
            report['errors'].extend(errors);report['missing'].extend(missing);ctx.close()
        browser.close()
    pairs={}
    for c in report['cases']:
        if not all(m['t']==0 for m in c['initialCooldowns']):report['failures'].append('disabled starting move in route comparison: '+c['hero']+'/'+c['route'])
        key=(c['hero'],c['budget'],c['threat'],c['seed']);formation=json.dumps(c['initialEnemies'],sort_keys=True)
        c['initialFormationHash']=hashlib.sha256(formation.encode()).hexdigest()
        if key in pairs and pairs[key]!=formation:report['failures'].append('unmatched initial enemies across routes: '+str(key))
        pairs[key]=formation
    report['pairedInitialFormationsVerified']=not any('unmatched initial enemies' in e for e in report['failures'])
    convergence=[]
    for slug in wanted:
        for budget in budgets:
            cases=[c for c in report['cases'] if c['hero']==slug and c['budget']==budget]
            sig={c['route']:json.dumps(c['behavior'],sort_keys=True) for c in cases}
            if len(sig)==3 and len(set(sig.values()))<3:convergence.append({'hero':slug,'budget':budget,'type':'behavior-fields-converge','routes':list(sig)})
    dominance=[]
    def vector(c):
        m=c['metrics']
        return [m['kills'],m['enemyHpLoss'],-m['taken'],int(m['alive']),-(m['killTime'] if m['killTime'] is not None else args.seconds+1)]
    for slug in wanted:
        for budget in [19,35]:
            cases=[c for c in report['cases'] if c['hero']==slug and c['budget']==budget]
            routes=sorted({c['route'] for c in cases})
            for better in routes:
                for worse in routes:
                    if better==worse:continue
                    pairs=[]
                    for threat in ['close','ranged','support','boss']:
                        for seed in seeds:
                            a=next((c for c in cases if c['route']==better and c['threat']==threat and c['seed']==seed),None)
                            b=next((c for c in cases if c['route']==worse and c['threat']==threat and c['seed']==seed),None)
                            if a and b:pairs.append((vector(a),vector(b)))
                    if len(pairs)==len(seeds)*4 and all(all(x>=y-1e-6 for x,y in zip(a,b)) for a,b in pairs) and any(any(x>y+1e-6 for x,y in zip(a,b)) for a,b in pairs):
                        dominance.append({'hero':slug,'budget':budget,'dominant':better,'dominated':worse,'scope':'all controlled threats and sampled seeds, not a universal balance claim'})
    report['softConvergence']=convergence
    report['controlledDominance']=dominance
    report['sourceHashesAfter']=runtime_hashes(args.url)
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime changed during controlled comparison; rerun after freeze')
    report['ok']=not(report['failures'] or report['errors'] or report['missing'])
    report['routeGatePassed']=report['ok'] and not convergence and not dominance
    report['routeGateScope']='Rejects structural convergence or sampled universal dominance only; it does not establish human/long-run balance.'
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'routeGatePassed':report['routeGatePassed'],'cases':len(report['cases']),'failures':report['failures'],'softConvergence':convergence,'controlledDominance':dominance},ensure_ascii=True))
    if not report['routeGatePassed']:raise SystemExit(1)

if __name__=='__main__':main()
