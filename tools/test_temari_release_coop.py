"""Two independent clients exercise routed Temari release-origin commits.

Native protocol over the existing in-memory transport adapter; no Firebase,
WebRTC latency or internet lobby claim. Injected reorder/malformed cases are
explicit controlled protocol fixtures, not natural-growth evidence.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_temari import CHROME, URL, boot
from test_temari_coop import ADAPTER

OUT = Path(__file__).resolve().parents[1] / '.omx/state/temari-complete/release-coop'


def pump(pages, report):
    for _ in range(20):
        messages = [message for page in pages.values() for message in page.evaluate('CoopFixture.drain()')]
        if not messages:
            return
        for message in messages:
            for event in message['msg'].get('ev', []):
                if event[0] in ('tc', 'tw'):
                    report['wire'].append({'from': message['from'], 'to': message['to'], 'event': event})
            pages[message['to']].evaluate('(m)=>CoopFixture.receive(m.from,m.msg)', message)
    raise AssertionError('unbounded protocol relay')


def advance(pages, report, frames):
    for _ in range(frames):
        for page in pages.values():
            page.evaluate('CoopFixture.step(1)')
        pump(pages, report)


def reset(pages, report, quantity=0):
    for page in pages.values():
        page.evaluate('''q=>{const A=Acceptance,p=A.p();G.SelfClones.clear();G.Combat.clearFields();
          G.EnemyMgr.clear();G.Projectiles.clear();p.x=p.y=0;p.hp=p.maxHp;p.dead=false;
          p.quantityBonus=p.quantityPicks=q;p.target=null;for(const m of p.moves)m.t=999;}''', quantity)
    pump(pages, report)
    pages['host'].evaluate("window.WindEnemy=Acceptance.spawn(160,0,'boss');WindEnemy.hp=WindEnemy.maxHp=1e9;G.Coop.tick(.1)")
    pump(pages, report)
    for uid, page in pages.items():
        page.evaluate('''() => {const p=G.Game.player;p.target=G.EnemyMgr.all().find(e=>!e.dead);p.aim=0;
          G.EnemyMgr.rebuildGrid();}''')


LIFECYCLE = r"""() => {
 const A=Acceptance,T=G.NarutoTemari,N=G.TemariCoop,p=A.p(),out={};
 G.Combat.clearFields();G.EnemyMgr.clear();CoopFixture.drain();
 const receive=event=>N.receive('guest',event);
 const make=(actor,id=100000,template=WindBasicTemplate)=>({
   start:['tc',N.stamp(),'guest',{...template,actor,castId:id,needsRelease:true}],
   release:['tw',N.stamp(),'guest',{actor,castId:id,x:83,y:29,aim:0,age:.18}]
 });
 const find=actor=>T.casts.find(c=>c.ghost&&c.owner.cloneId===actor);
 // A real release may overtake start. It may not move the remote avatar.
 let pair=make('clone:reorder');receive(pair.release);A.assert(N.inspect().windPending===1,'release not pending');
 receive(pair.start);let b=find('clone:reorder');A.assert(b&&b.releaseOrigin&&b.x===83&&b.y===29,'reordered origin mismatch');
 A.assert(b.owner.x===pair.start[3].x&&b.owner.y===pair.start[3].y,'release teleported remote owner');
 const emitted=b.emitted;receive(pair.release);receive(pair.start);
 A.assert(find('clone:reorder')===b&&b.emitted===emitted,'duplicates restarted cast');
 receive(['tw',N.stamp(),'guest',{...pair.release[3],x:999}]);A.assert(b.x===83,'conflicting duplicate changed origin');
 out.reorderAndDuplicates=true;
 // New ghosts wait, legacy peers retain snapshot-origin fallback.
 pair=make('clone:waiting');receive(pair.start);CoopFixture.step(60);b=find('clone:waiting');
 A.assert(b&&b.emitted===0,'new ghost emitted before authoritative release');
 pair=make('clone:legacy');delete pair.start[3].needsRelease;receive(pair.start);CoopFixture.step(30);b=find('clone:legacy');
 A.assert(b&&b.emitted>0,'legacy fallback did not emit');out.legacy=true;
 // A pending release carries its elapsed age into a later start, with no new
 // full attack/control window. The target is a real ordinary enemy in the fan.
 const ordinary=A.spawn(110,29);pair=make('clone:delayed');receive(pair.release);CoopFixture.step(220);
 receive(pair.start);b=find('clone:delayed');A.assert(!b||b.age>=2.3,'pending release reset original timeline');
 CoopFixture.step(20);A.assert(!T.liftFor(ordinary)&&!T.pushFor(ordinary)&&!T.orbitFor(ordinary),'expired release replayed control');
 out.delayedNoReplay=true;
 // Waiting ghosts and release-before-start records both expire after 3 valid
 // playing seconds. Pause does not spend this budget.
 pair=make('clone:noRelease');receive(pair.start);CoopFixture.step(310);
 A.assert(!find('clone:noRelease'),'waiting ghost leaked beyond TTL');receive(pair.release);
 A.assert(!find('clone:noRelease')&&N.inspect().windPending===0,'late release resurrected expired start');
 pair=make('clone:noStart');receive(pair.release);const pending=N.inspect().windPending;
 // Native multiplayer does not pause from the pause button. Explicitly test
 // the paused engine-state branch, then restore the native fixture state.
 const gameState=Object.getOwnPropertyDescriptor(G.Game,'state');
 Object.defineProperty(G.Game,'state',{...gameState,get:()=> 'paused'});
 try{T.update(10);G.Projectiles.update(10,p,G.EnemyMgr.all());
   A.assert(N.inspect().windPending===pending,'paused engine state expired release');
 }finally{Object.defineProperty(G.Game,'state',gameState)}
 CoopFixture.step(310);receive(pair.start);
 A.assert(!find('clone:noStart')&&N.inspect().windPending===0,'expired pending release resurrected');out.ttl=true;
 for(let i=0;i<140;i++)receive(make('clone:cap',200000+i).release);
 A.assert(N.inspect().windPending===128,'pending release cap');CoopFixture.step(310);
 A.assert(N.inspect().windPending===0,'pending cap records did not expire');out.cap=128;
 // Malformed/spoofed/session/scene/retired/dead/disconnected owners cannot add
 // pending records or create a ghost. No replacement packet handler is used.
 const count=()=>T.casts.length;
 const unchanged=(event,label,from='guest')=>{const c=count(),n=N.inspect().windPending;N.receive(from,event);
   A.assert(count()===c&&N.inspect().windPending===n,label)};
 pair=make('clone:invalid');unchanged(['tw',['wrong',0],'guest',pair.release[3]],'stale session');
 unchanged(['tw',[N.stamp()[0],N.stamp()[1]-1],'guest',pair.release[3]],'stale scene');
 unchanged(['tw',N.stamp(),'host',pair.release[3]],'spoofed uid');
 unchanged(['tw',N.stamp(),'guest',{...pair.release[3],x:NaN}],'NaN origin');
 unchanged(['tw',N.stamp(),'guest',{...pair.release[3],castId:1.5}],'fractional id');
 unchanged(['tw',N.stamp(),'guest',{...pair.release[3],actor:'clone:bad:actor'}],'bad actor');
 receive(['tx',N.stamp(),'guest','clone:invalid']);unchanged(pair.release,'retired release');unchanged(pair.start,'retired start');
 const mate=G.Coop.mate('guest');mate.pl.dead=true;unchanged(make('clone:dead').release,'dead owner');mate.pl.dead=false;
 mate.connected=false;unchanged(make('clone:gone').release,'disconnected owner');mate.connected=true;
 pair=make('player',300000);receive(pair.release);G.Combat.clearFields(mate.pl);receive(pair.start);
 A.assert(!T.casts.some(c=>c.owner===mate.pl&&c.castId===300000),'owner clear resurrected pending release');
 pair=make('clone:scene');receive(pair.release);G.Combat.clearFields();receive(pair.start);receive(pair.release);
 A.assert(N.inspect().windPending===0&&!find('clone:scene'),'scene clear resurrected release');out.invalidAndTeardown=true;
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'coverage': 'Native two-context routed tc/tw; controlled reorder and lifecycle',
              'notCovered': ['Firebase', 'WebRTC', 'internet latency/lobby'], 'wire': [], 'cases': [], 'errors': [], 'ok': False}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            pages = {}
            for uid in ['host', 'guest']:
                context = browser.new_context(viewport={'width': 1000, 'height': 800}, service_workers='block')
                context.add_init_script('window.requestAnimationFrame=()=>0')
                page = context.new_page()
                page.on('pageerror', lambda error: report['errors'].append(str(error)))
                boot(page)
                page.evaluate(ADAPTER, uid)
                page.evaluate("if(!G.Game.player.hasMove('naruto-temari-typhoon'))G.Game.player.addMove('naruto-temari-typhoon')")
                pages[uid] = page
            for caster_uid in ['host', 'guest']:
                for quantity in [0, 5]:
                    for skill in ['naruto-temari', 'naruto-temari-great-scythe', 'naruto-temari-typhoon']:
                        reset(pages, report, quantity)
                        caster = pages[caster_uid]
                        viewer = pages['guest' if caster_uid == 'host' else 'host']
                        start = len(report['wire'])
                        caster.evaluate('(id)=>{Acceptance.castNative(id);window.WindCast=G.NarutoTemari.stateFor(G.Game.player).latest;}', skill)
                        pump(pages, report)
                        caster.evaluate('G.Game.player.x=37;G.Game.player.y=23')
                        advance(pages, report, 60)
                        local = caster.evaluate('({x:WindCast.x,y:WindCast.y,aim:WindCast.aim,origin:WindCast.releaseOrigin,id:WindCast.serial,emitted:WindCast.emitted,count:WindCast.count})')
                        remote = viewer.evaluate('(id)=>{const b=G.NarutoTemari.casts.find(c=>c.ghost&&c.castId===id);return b&&{x:b.x,y:b.y,aim:b.aim,origin:b.releaseOrigin,emitted:b.emitted,count:b.count};}', local['id'])
                        assert local['origin'] and local['x'] == 37 and local['y'] == 23, local
                        assert remote and remote['x'] == local['x'] and remote['y'] == local['y'] and remote['aim'] == local['aim'], (local, remote)
                        assert local['emitted'] == local['count'] and remote['emitted'] == remote['count'], (local, remote)
                        wire = report['wire'][start:]
                        starts = [w['event'][3] for w in wire if w['event'][0] == 'tc']
                        releases = [w['event'][3] for w in wire if w['event'][0] == 'tw']
                        assert len(starts) == len(releases) == 1 and starts[0]['needsRelease'], wire
                        if caster_uid == 'guest' and skill == 'naruto-temari':
                            pages['host'].evaluate('value=>window.WindBasicTemplate=value', starts[0])
                        report['cases'].append({'caster': caster_uid, 'quantity': quantity, 'skill': skill, 'local': local, 'remote': remote})
                        print(caster_uid, quantity, skill, 'origin PASS', flush=True)
            for caster_uid in ['host', 'guest']:
                reset(pages, report, 5)
                caster, viewer = pages[caster_uid], pages['guest' if caster_uid == 'host' else 'host']
                caster.evaluate('''() => {const p=G.Game.player,c=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');
                  Acceptance.assert(c&&c.apply(p)!==false,'clone card missing');window.WindClone=G.SelfClones.actors()[0];
                  WindClone.x=WindClone.y=0;WindClone.target=p.target;WindClone.aim=0;
                  Acceptance.castNative('naruto-temari-great-scythe',WindClone);window.WindCast=G.NarutoTemari.stateFor(WindClone).latest;}''')
                pump(pages, report)
                caster.evaluate('WindClone.x=46;WindClone.y=19')
                advance(pages, report, 55)
                local = caster.evaluate('({x:WindCast.x,y:WindCast.y,id:WindCast.serial})')
                remote = viewer.evaluate('(id)=>{const b=G.NarutoTemari.casts.find(c=>c.ghost&&c.castId===id&&c.owner.cloneId!=null);return b&&{x:b.x,y:b.y}}', local['id'])
                # Native clone AI keeps moving during windup; the authoritative
                # release position, rather than the injected initial position,
                # must agree exactly on both peers.
                assert remote and remote['x'] == local['x'] and remote['y'] == local['y'] and abs(local['x']) + abs(local['y']) > 1, (local, remote)
                report['cases'].append({'caster': caster_uid, 'clone': True, 'local': local, 'remote': remote})
            reset(pages, report)
            report['lifecycle'] = pages['host'].evaluate(LIFECYCLE)
            assert not report['errors'], report['errors']
            browser.close()
        report['ok'] = True
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': report['ok'], 'cases': len(report['cases']), 'lifecycle': report.get('lifecycle')}))


if __name__ == '__main__':
    main()
