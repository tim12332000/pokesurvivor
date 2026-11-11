"""Native Lee skill snapshots, controlled combat invariance and lifecycle checks.

The baseline routes only committed naruto-gates.js into the same current game.
No combat, artwork or damage implementation is substituted. Controlled arenas
and fixed timesteps are labelled separately from native visual play evidence.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art-review/lee-skill-afterimages-20261112/qa'
URL = os.environ.get('LEE_AFTERIMAGES_URL', 'http://127.0.0.1:8347/.omx/digimon.html?lang=zh-TW&layout=wide')
SKILLS = ['naruto-lee-pursuit', 'naruto-lee', 'naruto-lotus', 'naruto-reverse-lotus', 'naruto-lee-drunken']

HELPERS = r'''() => {
 const A=Acceptance,p=A.p(),Gates=G.NarutoGates,assert=A.assert;
 const phase=()=>G.AnimationLab.stateFor(p.anim),shots=()=>Gates.afterimagesFor(p);
 function fixture(id){A.leeArena();p.moves=[];p.slots=[];p.active=0;p.bind={};p.level=30;p.maxMoves=5;p.item=null;p.cdMul=1;p.quantityPicks=p.quantityBonus=0;p.percentHealthDamage=p.lifestealRate=0;p.frozen=false;p.critChance=0;p.anim.play('Idle');
  assert(p.addMove('naruto-lee'),'learn primary');if(id!=='naruto-lee')assert(p.addMove(id),'learn '+id);p.arrange();for(const m of p.moves)m.t=999;
  const e=A.spawn(id==='naruto-lee-pursuit'?160:40,0),hits=[],hurt=e.hurt;e.hurt=function(...args){hits.push({damage:args[0],id:args[7],owned:args[6]===p});return hurt.apply(this,args)};p.target=e;p.aim=0;return {id,e,hits};
 }
 function active(id){return id==='naruto-lee-pursuit'?G.NarutoPursuit.activeFor(p):id==='naruto-lee'?G.DigimonSkills.whirlwindFor(p):id==='naruto-lee-drunken'?G.NarutoDrunkenFist.activeFor(p):G.NarutoLee.activeFor(p)}
 function begin(id){const f=fixture(id);if(id==='naruto-lee-pursuit'){p.moves.find(m=>m.id===id).t=0;A.advance(.001)}else if(id==='naruto-lee-drunken'){const rng=Math.random;Math.random=()=>0;A.resume();try{p.hurt(20,'normal',false,{fromX:f.e.x,fromY:f.e.y})}finally{Math.random=rng;A.pause()}}else A.actualCast(id);assert(active(id),'skill did not start '+id);return f;}
 // Alpha plus opaque RGB avoids GPU premultiplication rounding of translucent
 // edge colors when PNG evidence forces a later readback of the same canvas.
 function pixels(image){const data=image.getContext('2d',{willReadFrequently:true}).getImageData(0,0,image.width,image.height).data,colors=new Set();let count=0,x0=image.width,y0=image.height,x1=-1,y1=-1,hash=2166136261;
  for(let y=0;y<image.height;y++)for(let x=0;x<image.width;x++){const k=(y*image.width+x)*4,a=data[k+3];if(a>8){count++;x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);colors.add((data[k]<<16)|(data[k+1]<<8)|data[k+2]);}hash=Math.imul(hash^a,16777619)>>>0;if(a===255)for(let c=0;c<3;c++)hash=Math.imul(hash^data[k+c],16777619)>>>0;}return {pixels:count,colors:colors.size,bounds:[x0,y0,x1,y1],hash};}
 const records=[],checked=new Set();let record=false;
 function step(dt=.005){const draw=p.anim.draw;p.anim.draw=function(ctx,x,y,opts){const pose={...phase()},result=draw.call(this,ctx,x,y,opts);if(record&&ctx.canvas instanceof HTMLCanvasElement){const entry={canvas:ctx.canvas,pose,x,y,ownerX:p.x,ownerY:p.y};records.push(entry);if(!checked.has(pose.id+':'+pose.phase)){checked.add(pose.id+':'+pose.phase);entry.first=true;entry.before=pixels(ctx.canvas);const native=document.createElement('canvas');native.width=ctx.canvas.width;native.height=ctx.canvas.height;draw.call(this,native.getContext('2d'),x,y,opts);entry.native=pixels(native);}}return result};A.resume();try{G.Combat.updateFields(dt);p.anim.update(dt)}finally{A.pause();p.anim.draw=draw}}
 function drawHistory(low=false){const canvas=document.createElement('canvas');canvas.width=canvas.height=1024;const ctx=canvas.getContext('2d'),calls=[],draw=ctx.drawImage.bind(ctx),quality=G.Settings.get('quality');G.Settings.set('quality',low?'low':'high');ctx.translate(512-p.x,800-p.y);ctx.drawImage=function(image,...args){if(image instanceof HTMLCanvasElement)calls.push({image,args});return draw(image,...args)};const before=JSON.stringify(shots()),damage=p.dmgDealt,hp=p.hp,rng=Math.random;let randomCalls=0;Math.random=()=>{randomCalls++;return .999};try{G.Combat.drawGroundFields(ctx)}finally{Math.random=rng;G.Settings.set('quality',quality)}assert(JSON.stringify(shots())===before&&p.dmgDealt===damage&&p.hp===hp&&randomCalls===0,'drawing changed history/gameplay/RNG');return {calls,canvas};}
 window.LeeAfter={A,p,Gates,assert,phase,shots,fixture,active,begin,pixels,step,drawHistory,records,checked,set recording(v){record=v}};
}'''

SCENE = r'''opts => {
 const T=LeeAfter,{A,p,Gates,assert}=T;T.records.length=0;T.checked.clear();T.recording=opts.candidate;const f=T.begin(opts.id),damage=p.dmgDealt,positions=[],emitted=new Set(),metadata=[],phasePixels=[],snapshotSeen=new Set();let maxCount=0,ended=false,peak=null,recordCursor=0;
 for(let i=0;i<1800;i++){
  const a=T.active(opts.id),pose=T.phase();positions.push([p.x,p.y,a?.phase||null]);if(!a){ended=true;break;}T.step();const shots=T.shots();maxCount=Math.max(maxCount,shots.length);
  if(opts.candidate){assert(!Gates.learnedStage(p)&&!Gates.stage(p),'skill fixture learned Gates');assert(shots.length<=6,'normal trail exceeded six');assert(shots.every(s=>s.natural&&s.color===null&&s.life<=.220001),'normal trail was tinted or long-lived');
   for(const s of shots){const key=[s.x,s.y,s.ttl,s.phase].join(':');if(!snapshotSeen.has(key)){snapshotSeen.add(key);metadata.push(s)}emitted.add(s.phase);}
   for(const r of T.records.slice(recordCursor)){if(!r.first)continue;assert(r.before.pixels>80&&r.before.colors>4,'normal snapshot lost natural colors');assert(r.before.hash===r.native.hash,'snapshot differs from actual authored draw');const [x0,y0,x1,y1]=r.before.bounds;assert(x0>0&&y0>0&&x1<r.canvas.width-1&&y1<r.canvas.height-1,'snapshot clipped '+r.pose.id+'/'+r.pose.phase);phasePixels.push({pose:r.pose,bounds:r.before.bounds,colors:r.before.colors,hash:r.before.hash,snapshotAnchor:[r.x,r.y],owner:[r.ownerX,r.ownerY],png:r.canvas.toDataURL()});}
   if(T.records.length>recordCursor){const r=T.records.at(-1),s=shots.at(-1),pose=r.pose;assert(s&&s.skillId===pose.id&&s.poseKey===pose.key&&s.phase===pose.phase,'history metadata differs from frozen authored pose');assert(Math.abs(s.x-(r.ownerX+(pose.offsetX||0)))<1e-7&&Math.abs(s.y-(r.ownerY+(pose.offsetY||0)-(pose.visualLift||0)))<1e-7,'history did not use actual airborne/offset position');assert(s.visualLift===(pose.visualLift||0)&&s.rotation===(pose.rotation||0),'history dropped lift/rotation');assert(Math.abs(r.y+(pose.offsetY||0)-(pose.visualLift||0)-s.anchorY)<1e-7,'snapshot did not normalize authored height into frozen anchor');}
   recordCursor=T.records.length;
   if(shots.length>=3&&!peak){const high=T.drawHistory(),low=T.drawHistory(true);assert(high.calls.length===shots.length,'normal history not all drawn');assert(low.calls.length===Math.ceil(shots.length/2),'low-quality history not newest alternating subset');const newest=high.calls.at(-1).image;assert(low.calls.at(-1).image===newest,'low quality omitted newest snapshot');peak={high:high.calls.length,low:low.calls.length};}
  }
 }
 assert(ended,'skill did not finish');for(const m of p.moves)m.t=999;
 if(opts.candidate){assert(maxCount>0,'skill emitted no snapshot '+opts.id);const required=opts.id==='naruto-lee-pursuit'?['rush','attack']:opts.id==='naruto-lotus'?['lift','suspend','descent']:opts.id==='naruto-reverse-lotus'?['lift','combo','descent']:opts.id==='naruto-lee-drunken'?['dodge','counter']:['rise','turn','strike'];assert(required.every(x=>emitted.has(x)),'missing skill snapshots '+opts.id+' '+[...emitted]);
  for(const r of T.records.filter(x=>x.first)){assert(T.pixels(r.canvas).hash===r.before.hash,'snapshot bitmap mutated after later poses '+JSON.stringify({pose:r.pose,before:r.before,after:T.pixels(r.canvas)}));}
  const history=JSON.stringify(T.shots());G.Combat.updateFields(.1);assert(JSON.stringify(T.shots())===history,'paused normal history aged');const copies=T.shots();if(copies.length){copies[0].x+=999;assert(JSON.stringify(T.shots())===history,'metadata exposed mutable live history');}
  for(let i=0;i<55;i++)T.step();assert(T.shots().length===0,'finished skill left ghosts after lifetime');assert(T.drawHistory().calls.length===0,'finished skill retained rendered ghosts');
 }
 T.recording=false;return {id:opts.id,positions,hits:f.hits,loss:100000-f.e.hp,damage:p.dmgDealt-damage,ended,maxCount,emitted:[...emitted],metadata,phasePixels,peak};
}'''

LIFECYCLE = r'''() => {
 const T=LeeAfter,{A,p,Gates,assert}=T,out=[];
 for(const reason of ['clear','death','world','unlearn']){const f=T.begin('naruto-reverse-lotus');for(let i=0;i<500&&!T.shots().some(s=>s.phase==='combo');i++)T.step();assert(T.shots().length,'lifecycle fixture missing');const world=G.World;
  if(reason==='clear')G.Combat.clearFields(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};if(reason==='unlearn'){p.moves=p.moves.filter(m=>m.id!==f.id);p.slots=p.slots.filter(g=>!g.some(m=>m.id===f.id));}
  assert(!T.shots().length,'stale snapshots visible before update '+reason);assert(!T.drawHistory().calls.length,'stale snapshots drawn '+reason);T.step();assert(!T.shots().length,'stale snapshots retained '+reason);G.World=world;p.dead=false;p.hp=p.maxHp;out.push(reason);
 }return out;
}'''

GATES = r'''() => {
 const T=LeeAfter,{A,p,Gates,assert}=T,out=[];
 for(const level of [1,2,3]){T.fixture('naruto-lee');G.EnemyMgr.clear();assert(p.addMove('naruto-gates'),'learn Gates');Object.assign(p.moves.find(m=>m.id==='naruto-gates'),G.Moves.instance('naruto-gates',level));for(let i=0;i<100;i++)T.step();assert(Gates.performing(p),'opening fixture missing');assert(!T.shots().some(s=>s.natural),'opening spawned ordinary skill history');A.advance(4.6);assert(Gates.stage(p)===level&&!Gates.performing(p),'Gates not ready');const x=p.x,damage=p.dmgDealt,hp=p.hp;
  for(let i=0;i<70;i++){A.resume();try{p.update(.02);G.Combat.updateFields(.02)}finally{A.pause()}}
  const shots=T.shots(),style=Gates.config.trails[level-1];assert(p.x>x+10,'native walking input missing');assert(shots.length>0&&shots.length<=style.count,'colored trails missing/cap changed');assert(shots.every(s=>!s.natural&&s.color===style.color&&s.life===style.life),'Gates walking trails changed');assert(p.dmgDealt===damage&&p.hp===hp,'walking afterimages changed gameplay');out.push({level,style,count:shots.length,dx:p.x-x});
 }return out;
}'''


def boot(browser, baseline=None):
    context = browser.new_context(viewport={'width': 1280, 'height': 900}, service_workers='block')
    if baseline is not None:
        context.route('**/.omx/naruto-gates.js*', lambda route: route.fulfill(status=200, body=baseline, content_type='application/javascript'))
    page = context.new_page()
    page.goto(URL)
    page.wait_for_function("window.PS_REDRAWN_READY&&G.AnimationLab&&G.NarutoGates&&document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():
        page.locator('#tap-start').click()
    page.locator('[data-quick-naruto="30006"]').click()
    page.locator('#scr-menu [data-go="play"]').click()
    page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
    page.evaluate(HARNESS)
    page.evaluate(SETUP)
    page.evaluate(HELPERS)
    return context, page


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    baseline = subprocess.check_output(['git', 'show', '8edbb632:.omx/naruto-gates.js'], cwd=ROOT)
    report = {'scope': 'controlled actual normal-menu runtime, fixed step; no natural-growth claim', 'sourceSha256': hashlib.sha256((ROOT / '.omx/naruto-gates.js').read_bytes()).hexdigest(), 'baselineSha256': hashlib.sha256(baseline).hexdigest(), 'cases': {}, 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        _, before_page = boot(browser, baseline)
        context, page = boot(browser)
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        for skill in SKILLS:
            name = skill.replace('naruto-', '')
            try:
                before = before_page.evaluate(SCENE, {'id': skill, 'candidate': False})
                after = page.evaluate(SCENE, {'id': skill, 'candidate': True})
                comparable = ['positions', 'hits', 'loss', 'damage', 'ended']
                assert all(before[k] == after[k] for k in comparable), 'snapshot changed combat: ' + str({k: [before[k], after[k]] for k in comparable if before[k] != after[k]})
                for evidence in after['phasePixels']:
                    image = evidence.pop('png')
                    path = OUT / f'{name}-{evidence["pose"]["phase"]}.png'
                    path.write_bytes(base64.b64decode(image.split(',', 1)[1]))
                    evidence['path'] = str(path.relative_to(ROOT)).replace('\\', '/')
                report['cases'][skill] = {'ok': True, 'combatIdentical': comparable, 'candidate': after}
                print(skill, 'PASS', flush=True)
            except Exception as exc:
                report['cases'][skill] = {'ok': False, 'error': str(exc)}
                print(skill, 'FAIL', str(exc).splitlines()[0], flush=True)
        for name, script in [('lifecycle', LIFECYCLE), ('gates_walking', GATES)]:
            try:
                if name == 'gates_walking':
                    page.keyboard.down('KeyD')
                report['cases'][name] = {'ok': True, 'result': page.evaluate(script)}
                print(name, 'PASS', flush=True)
            except Exception as exc:
                report['cases'][name] = {'ok': False, 'error': str(exc)}
                print(name, 'FAIL', str(exc).splitlines()[0], flush=True)
            finally:
                page.keyboard.up('KeyD')
        browser.close()
    report['ok'] = all(c['ok'] for c in report['cases'].values()) and not report['errors']
    (OUT / 'mechanics.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
