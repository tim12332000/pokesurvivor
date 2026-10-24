"""Native regression for Temari's advancing whole-fan wind-wave basic.

Run against the normal local game on port 8004. Enemy hurt, mastery,
quantity, clone ownership and field timing use the production pipeline.
"""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_temari import CHROME, boot

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/temari-windwave'

SETUP = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;
 A.fanReset=(L=0,Q=0,rank=1)=>{A.reset();A.mastery(L);A.rank('naruto-temari',rank);
   p.quantityBonus=p.quantityPicks=Q;p.x=p.y=0;p.aim=0;};
 A.fanEnemy=(x,y,r=4)=>{const e=A.spawn(x,y,'boss');e.r=r;e.hp=e.maxHp=1e10;
   G.EnemyMgr.rebuildGrid();return e;};
 A.fanPolar=(radius,angle)=>A.fanEnemy(radius*Math.cos(angle),radius*Math.sin(angle));
 A.fanCast=target=>{p.target=target;A.castNative('naruto-temari');return T.stateFor(p).latest;};
 A.fanVisualStart=(rank=1)=>{A.fanReset(0,0,rank);G.Settings.set('dmgNumbers',true);
   const angles=rank===5?Array.from({length:8},(_,i)=>i*Math.PI/4):[-Math.PI/8,-Math.PI/16,0,Math.PI/16,Math.PI/8];
   const es=angles.map(a=>A.fanPolar(150,a));A.fanVisualHits=es.map(A.watch);
   A.fanCast(es[rank===5?0:2]);A.fanVisualAge=0;};
 A.fanVisualAdvance=to=>{while(A.fanVisualAge<to-1e-8){const dt=Math.min(.005,to-A.fanVisualAge);
   A.advance(dt);A.resume();try{G.FX.update(dt)}finally{A.pause()}A.fanVisualAge+=dt;}
   return {age:A.fanVisualAge,hits:A.fanVisualHits.map(h=>h.length),waves:T.waves.map(b=>({reach:b.reach,aim:b.aim})),blades:T.blades.length,
     fx:G.FX.count,damageNumbers:G.Settings.get('dmgNumbers')};};
 A.fanVisualSnapshot=()=>{const s=T.stateFor(p);return JSON.stringify({
   owner:{x:p.x,y:p.y,hp:p.hp,damage:p.dmgDealt},enemies:G.EnemyMgr.all().map(e=>({x:e.x,y:e.y,hp:e.hp})),
   state:s&&{clock:s.clock,basicCooldown:s.basicCooldown,totalCuts:s.totalCuts,hitEvents:s.hitEvents},
   casts:T.casts.map(c=>({age:c.age,cuts:c.cuts,hits:c.hits,emitted:c.emitted})),
   waves:T.waves.map(w=>({x:w.x,y:w.y,age:w.age,reach:w.reach,cuts:w.cuts,
     fronts:w.fronts.map(f=>({reach:f.reach,started:f.started,hits:f.hits.size,props:f.props.size,done:f.done}))})),fx:G.FX.count});};
 A.fanVisualRenderCheck=()=>{const before=A.fanVisualSnapshot(),canvas=document.createElement('canvas');
   canvas.width=900;canvas.height=700;const ctx=canvas.getContext('2d');ctx.translate(450,350);
   G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);G.FX.draw(ctx);
   A.assert(before===A.fanVisualSnapshot(),'synchronous native field render mutated combat or FX');return true;};
}"""

GEOMETRY = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out={};A.fanReset();
 const spread=[-Math.PI/8,-Math.PI/16,0,Math.PI/16,Math.PI/8].map(a=>A.fanPolar(150,a));
 const rejected=[A.fanPolar(150,Math.PI*.45),A.fanEnemy(-100,0),A.fanEnemy(500,0)];
 const enemies=[...spread,...rejected],hits=enemies.map(A.watch),f=A.fanCast(spread[2]);
 A.finish(2);A.assert(hits.slice(0,5).every(h=>h.length===3),'whole fan missed off-axis or spread targets '+hits.map(h=>h.length));
 A.assert(hits.slice(5).every(h=>h.length===0),'fan hit outside/behind/out-of-range target '+hits.map(h=>h.length));
 A.assert(hits.flat().every(h=>h.knock===0),'basic inherited heavy knockback');
 A.assert(hits.flat().every(h=>h.id==='naruto-temari'&&h.owner&&h.raw>0),'fan bypassed owned native hurt');
 out.spread={angles:[-22.5,-11.25,0,11.25,22.5],hits:hits.map(h=>h.length),count:f.count};
 A.fanReset(5);const first=A.fanEnemy(85,0),second=A.fanEnemy(180,0),pair=[first,second].map(A.watch);
 const piercing=A.fanCast(first);A.finish(3);
 A.assert(pair.every(h=>h.length===18),'first contact stopped wave or duplicate recuts '+pair.map(h=>h.length));
 out.piercing={hits:pair.map(h=>h.length),R:piercing.R,cuts:piercing.cuts};
 // The original target moves before any release; the cast direction stays fixed.
 A.fanReset();const aimTarget=A.fanEnemy(150,0),fixed=A.fanEnemy(210,0),fixedHits=A.watch(fixed);
 A.fanCast(aimTarget);aimTarget.x=-200;aimTarget.y=200;p.target=aimTarget;G.EnemyMgr.rebuildGrid();A.finish(.32);
 const angles=T.waves.map(b=>b.aim);
 A.assert(!T.blades.length,'basic still emitted individual projectiles');
 A.assert(angles.length===3,'did not release three whole-fan waves '+angles);
 angles.forEach((a,i)=>A.near(a,0,'fixed wind-wave aim '+i));
 T.waves.forEach(w=>A.near(w.cast.arc,Math.PI/4,'whole fan width'));
 A.finish(2);A.assert(fixedHits.length===3,'basic retargeted after cast');out.fixedAim=angles;
 // One large production frame must still contact an enemy between endpoints.
 A.fanReset();const swept=A.fanEnemy(100,0),sweptHits=A.watch(swept);A.fanCast(swept);
 A.finish(.17);A.advance(.4);A.finish(2);A.assert(sweptHits.length===3,'large frame tunneled past target');out.swept=sweptHits.length;
 return out;
}"""

FRONTS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out={};A.fanReset(5);
 const escape=A.fanEnemy(150,0),hits=A.watch(escape);A.fanCast(escape);
 for(let i=0;i<200&&!hits.length;i++)A.advance(.005);
 A.assert(hits.length===1,'first contact fixture failed '+hits.length);
 escape.x=-800;escape.y=700;G.EnemyMgr.rebuildGrid();A.finish(3);
 A.assert(hits.length===1,'later wave fronts followed escaped target '+hits.length);out.escape=hits.length;
 A.fanReset(5);const blocked=A.fanEnemy(180,0,55),blockedHits=A.watch(blocked);A.fanCast(blocked);
 const W=G.World,saved={isFree:W.isFree,isWall:W.isWall,projectileBlock:W.projectileBlock};
 Object.assign(W,{isFree:x=>x<70,isWall:x=>x>=70&&x<=100,
   projectileBlock:x=>x>=70&&x<=100?{destructible:false}:false});
 try{A.finish(3);A.assert(blockedHits.length===0,'wave front or enemy body leaked through wall '+blockedHits.length)}
 finally{Object.assign(W,saved)}out.wall=blockedHits.length;
 // A wall introduced after the first front blocks every later advancing front.
 A.fanReset(5);const recut=A.fanEnemy(150,0),recutHits=A.watch(recut);A.fanCast(recut);
 for(let i=0;i<200&&!recutHits.length;i++)A.advance(.005);
 A.assert(recutHits.length===1,'wall recut fixture failed');
 const wall={destructible:false};W.projectileBlock=(x,y)=>x>recut.x-25&&x<recut.x-15?wall:false;
 try{A.finish(3);A.assert(recutHits.length===1,'later fronts crossed newly inserted wall '+recutHits.length)}
 finally{Object.assign(W,saved)}out.pendingWall=recutHits.length;return out;
}"""

RANK_GEOMETRY = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[],degrees=[45,75,105,135,180];
 for(let rank=1;rank<=5;rank++){
   A.fanReset(0,0,rank);const arc=degrees[rank-1]*Math.PI/180,margin=5*Math.PI/180;
   const center=A.fanEnemy(150,0),inside=[A.fanPolar(150,-arc/2+margin),A.fanPolar(150,arc/2-margin)];
   const outside=[A.fanPolar(150,-arc/2-margin),A.fanPolar(150,arc/2+margin)];
   const rear=A.fanEnemy(-150,0),range=T.snapshot(p,p.moves.find(m=>m.id==='naruto-temari')).range;
   const distant=A.fanEnemy(range+80,0),enemies=[center,...inside,...outside,rear,distant],hits=enemies.map(A.watch);
   const f=A.fanCast(center);A.near(f.arc,arc,'rank fan angle '+rank);A.finish(3);
   A.assert(hits.slice(0,3).every(h=>h.length===3),'rank fan missed inner angular edge '+rank+' '+hits.map(h=>h.length));
   A.assert(hits.slice(3,3+outside.length).every(h=>h.length===0),'rank fan exceeded angular edge '+rank+' '+hits.map(h=>h.length));
   A.assert(hits.at(-2).length===0,'rear hit outside forward fan '+rank+' '+hits.at(-2).length);
   A.assert(hits.at(-1).length===0,'rank full radius exceeded range '+rank);
   out.push({rank,degrees:degrees[rank-1],range,hits:hits.map(h=>h.length)});
 }
 A.fanReset(0,0,5);const surround=Array.from({length:8},(_,i)=>A.fanPolar(150,i*Math.PI/4));
 const hits=surround.map(A.watch);A.fanCast(surround[0]);A.finish(3);
 const expected=[3,3,3,0,0,0,3,3];
 A.assert(hits.every((h,i)=>h.length===expected[i]),'rank 5 exceeded or missed forward semicircle '+hits.map(h=>h.length));
 A.assert(!T.blades.length,'rank 5 restored single-target projectiles');out.push({fanDegrees:180,probeDirections:8,hits:hits.map(h=>h.length),expected});
 return out;
}"""

GROWTH = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(const Q of [0,5,10,20])for(const L of [0,1,5]){
   A.fanReset(L,Q,5);const e=A.fanEnemy(100,0,300),hits=A.watch(e),f=A.fanCast(e);
   const N=Math.floor(3*1.25**Q),R=L?1+L+Q:1;A.finish(5);
   A.assert(f.count===N&&f.emitted===N,'quantity changed/capped fan '+Q+' '+L);
   A.assert(f.R===R&&f.cuts===N*R&&hits.length===N*R,'wave count/front mastery changed '+Q+' '+L+' '+hits.length+'/'+N*R);
   A.assert(hits.every(h=>Math.abs(h.raw-18*p.atk*G.Types.mult('flying',e.types)*G.Weather.mult('flying'))<1e-6),'rank 5 damage changed');
   out.push({Q,L,N,R,hits:hits.length});
 }
 for(let rank=1;rank<=5;rank++){
   A.fanReset(0,0,rank);const e=A.fanEnemy(150,0),hits=A.watch(e),f=A.fanCast(e);A.finish(3);
   A.assert(hits.length===3,'rank altered whole-fan wave count '+rank+' '+hits.length);
   A.near(f.damage,[8,9.6,11.52,14.4,18][rank-1]*p.atk,'rank damage '+rank);
   out.push({rank,damage:f.damage,range:f.range});
 }
 return out;
}"""

OWNERSHIP = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out={};A.fanReset(5,5);
 const e=A.fanEnemy(100,0,300),hits=A.watch(e),ownerCast=A.fanCast(e);A.finish(5);
 const baseline=hits[0].raw;G.Combat.clearFields();e.hp=e.maxHp;hits.length=0;
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');A.assert(card,'native clone card unavailable');card.apply(p);
 const clone=G.SelfClones.actors()[0];clone.x=clone.y=0;clone.target=e;clone.aim=0;clone.critChance=0;
 A.castNative('naruto-temari',clone);const f=T.stateFor(clone).latest;
 for(const m of clone.moves)m.t=999;const savedMoves=p.moves;p.moves=p.moves.filter(m=>m.digiMode==='temari-mastery');
 try{A.finish(5)}finally{p.moves=savedMoves}
 const actual=hits.filter(h=>h.clone&&h.id==='naruto-temari');A.assert(actual.length===ownerCast.count*ownerCast.R,'clone fan count/mastery reduced '+actual.length+'/'+ownerCast.count*ownerCast.R);
 actual.forEach(h=>A.near(h.raw*3,baseline,'clone damage scaled more than once'));
 out.clone={hits:actual.length,count:f.count,R:f.R,ratio:actual[0].raw/baseline};
 A.fanReset(5,5);const remoteTarget=A.fanEnemy(100,0,300),remoteHits=A.watch(remoteTarget);
 const move=p.moves.find(m=>m.id==='naruto-temari'),packet=T.snapshot(p,move),remote={x:0,y:0,hp:100,dead:false,aim:0};
 A.assert(T.ghost(remote,{...packet,x:0,y:0,aim:0,targetPositions:[{x:100,y:0}]}),'remote cast rejected');
 A.finish(.32);A.assert(T.waves.some(b=>b.owner===remote)&&!T.blades.length,'remote wind wave absent or still individual shots');A.finish(5);
 A.assert(remoteHits.length===0,'remote visual fan dealt local damage');out.remoteDamage=remoteHits.length;return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'viewports': {}, 'errors': [], 'failures': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, viewport, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
            if os.environ.get('TEMARI_VIEWPORTS') and label not in os.environ['TEMARI_VIEWPORTS'].split(','):
                continue
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            try:
                boot(page)
                page.evaluate(SETUP)
                result = report['viewports'][label] = {}
                for name, check in [('geometry', GEOMETRY), ('rankGeometry', RANK_GEOMETRY), ('fronts', FRONTS), ('growth', GROWTH), ('ownership', OWNERSHIP)]:
                    print(label, name, flush=True)
                    try:
                        result[name] = page.evaluate(check)
                    except Exception as error:
                        result[name] = {'failure': str(error)}
                        report['failures'].append(label+':'+name+': '+str(error))
                    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
                result['visual'] = capture_visual(page, label)
                result['rank5Visual'] = capture_visual(page, label, 5)
            except Exception as error:
                report['failures'].append(label+':boot: '+str(error))
            finally:
                context.close()
        browser.close()
    report['ok'] = not (report['errors'] or report['failures'])
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': report['ok'], 'failures': report['failures'], 'report': str(OUT / 'report.json')}))
    if not report['ok']:
        raise SystemExit(1)


def capture_visual(page, label, rank=1):
    page.evaluate('(rank)=>Acceptance.fanVisualStart(rank)', rank)
    frames = []
    for at in ([.50, .65] if rank == 5 else [.30, .50, .65]):
        frame = page.evaluate('(at)=>Acceptance.fanVisualAdvance(at)', at)
        frame['rank'] = rank
        frames.append(frame)
        frame['renderPure'] = page.evaluate('Acceptance.fanVisualRenderCheck()')
        # The normal RAF draws the paused production scene without advancing
        # the controlled native combat fixture.
        page.wait_for_timeout(60)
        suffix = '-rank5' if rank == 5 else ''
        page.screenshot(path=str(OUT / f'{label}-fan{suffix}-{at:.2f}.png'))
    return frames


if __name__ == '__main__':
    main()
