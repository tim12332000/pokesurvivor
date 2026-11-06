"""Committed-result wind-chain protocol over two native independent clients.

The sender hook boundary receives controlled committed-result packets. Core
mechanic tests independently prove real attacks produce those results. These
tests prove routing/identity, remote-only visuals, bounded replay and teardown;
they do not claim Firebase/WebRTC or natural gameplay coverage.
"""
import json
import hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_temari import CHROME, URL, boot
from test_temari_coop import ADAPTER

OUT = Path(__file__).resolve().parents[1] / '.omx/state/temari-fun/chain-coop'


def pump(pages, report):
    for _ in range(20):
        messages = [message for page in pages.values() for message in page.evaluate('CoopFixture.drain()')]
        if not messages:
            return
        for message in messages:
            for event in message['msg'].get('ev', []):
                if event[0] in ('tk', 'tg'):
                    report['wire'].append({'from': message['from'], 'to': message['to'], 'event': event})
            pages[message['to']].evaluate('(m)=>CoopFixture.receive(m.from,m.msg)', message)
    raise AssertionError('unbounded chain protocol relay')


def unlearn_cases(browser, report):
    """Real producer resources disappear remotely before their normal TTL."""
    results = []
    for caster_uid in ['host', 'guest']:
        for resource in ['knot', 'burst']:
            pages, contexts = {}, []
            try:
                for uid in ['host', 'guest']:
                    context = browser.new_context(viewport={'width': 1000, 'height': 800}, service_workers='block')
                    contexts.append(context)
                    context.add_init_script('window.requestAnimationFrame=()=>0')
                    page = context.new_page()
                    page.on('pageerror', lambda error: report['errors'].append(str(error)))
                    boot(page)
                    page.evaluate(ADAPTER, uid)
                    page.evaluate('Acceptance.mastery(1);G.Game.player.quantityBonus=G.Game.player.quantityPicks=0;CoopFixture.drain()')
                    pages[uid] = page
                pages['host'].evaluate("window.ChainEnemy=Acceptance.spawn(140,0,'boss');ChainEnemy.hp=ChainEnemy.maxHp=1e9;G.Coop.tick(.1)")
                pump(pages, report)
                caster, viewer = pages[caster_uid], pages['guest' if caster_uid == 'host' else 'host']
                caster.evaluate('G.Game.player.target=G.EnemyMgr.all().find(e=>!e.dead);G.Game.player.aim=0')
                wire_start = len(report['wire'])
                for _ in range(140):
                    caster.evaluate('''()=>{Acceptance.resume();for(let i=0;i<5;i++){
                      G.Combat.tick(.01,G.Game.player,0);CoopFixture.step(1)}}''')
                    viewer.evaluate('CoopFixture.step(5)')
                    pump(pages, report)
                    if caster.evaluate('G.NarutoTemari.windKnots.length>0'):
                        break
                else:
                    raise AssertionError('unlearn fixture native knot missing')
                if resource == 'burst':
                    caster.evaluate("Acceptance.castNative('naruto-temari-great-scythe')")
                    for _ in range(100):
                        caster.evaluate('CoopFixture.step(1)')
                        viewer.evaluate('CoopFixture.step(1)')
                        pump(pages, report)
                        if caster.evaluate('G.NarutoTemari.windBursts.length>0'):
                            break
                    else:
                        raise AssertionError('unlearn fixture native burst missing')
                before = viewer.evaluate('({knots:G.NarutoTemari.windKnots.length,bursts:G.NarutoTemari.windBursts.length})')
                assert before['knots' if resource == 'knot' else 'bursts'] > 0, before
                caster.evaluate("G.Game.player.moves=G.Game.player.moves.filter(m=>m.digiMode!=='temari-great-scythe');CoopFixture.step(1)")
                pump(pages, report)
                viewer.evaluate('CoopFixture.step(1)')
                local = caster.evaluate('({knots:G.NarutoTemari.windKnots.length,bursts:G.NarutoTemari.windBursts.length,alive:!G.Game.player.dead&&G.Game.player.hp>0})')
                remote = viewer.evaluate('({knots:G.NarutoTemari.windKnots.length,bursts:G.NarutoTemari.windBursts.length})')
                assert local == {'knots': 0, 'bursts': 0, 'alive': True} and remote == {'knots': 0, 'bursts': 0}, (caster_uid, resource, local, remote)
                events = [item['event'] for item in report['wire'][wire_start:]]
                removals = [event for event in events if event[0] == 'tg' and event[3].get('removed')]
                assert len(removals) == 1, events
                for event in events:
                    viewer.evaluate('(m)=>G.TemariCoop.receive(m.from,m.event)', {'from': caster_uid, 'event': event})
                assert viewer.evaluate('G.NarutoTemari.windKnots.length+G.NarutoTemari.windBursts.length') == 0, 'late result resurrected removed resources'
                results.append({'caster': caster_uid, 'resource': resource, 'before': before, 'localAfter': local,
                                'remoteAfter': remote, 'removal': removals[0][3], 'lateReplayRejected': True})
                print(caster_uid, resource, 'native unlearn cleanup PASS', flush=True)
            finally:
                for context in contexts:
                    context.close()
    return results


LIFECYCLE = r"""() => {
 const A=Acceptance,T=G.NarutoTemari,N=G.TemariCoop,out={};
 const receive=event=>N.receive('guest',event),owner=()=>G.Coop.mate('guest').pl;
 const knot=(id,x=120,age=0,actor='player')=>['tk',N.stamp(),'guest',{
   actor,seedId:id,sourceCastId:10,x,y:0,age,ttl:6}];
 const chain=(id,seeds,age=0,actor='player')=>['tg',N.stamp(),'guest',{
   actor,heavyCastId:20,activationId:id,consumedIds:seeds,
   bursts:seeds.map((seed,i)=>({id:10000+id*8+i,x:120+i*50,y:0,age,radius:202,cuts:3,interval:.1,travel:.08,damageType:'flying'}))}];
 const knots=()=>T.windKnots.filter(a=>a.owner===owner());
 const bursts=()=>T.windBursts.filter(a=>a.owner===owner());
 const reset=()=>{G.Combat.clearFields();G.EnemyMgr.clear();CoopFixture.drain()};
 const step=seconds=>CoopFixture.step(Math.ceil(seconds/.01));
 reset();
 // Self-contained seeds do not require any cast body. Arrival order must not
 // turn an older seed into the newest knot at the eight-node replacement cap.
 for(let id=10;id>=1;id--)receive(knot(id,id*60));
 A.assert(knots().length===8&&knots().every(a=>a.seedId>=3),'reorder replaced newer knot at cap');
 const avatar={x:owner().x,y:owner().y};receive(knot(11,999));
 A.assert(owner().x===avatar.x&&owner().y===avatar.y,'seed teleported existing avatar');out.reorderCap=true;
 reset();receive(chain(1,[20]));const count=bursts().length;receive(knot(20));receive(chain(1,[20]));
 A.assert(count===1&&bursts().length===1&&knots().length===0,'activation-before-seed or duplicate resurrected');
 step(1);receive(chain(1,[20]));A.assert(!bursts().length,'duplicate replayed completed burst');
 step(6);receive(chain(1,[20]));receive(knot(20));
 A.assert(!bursts().length&&!knots().length,'expired protection forgot retired sequence');out.activationOrdering=true;
 reset();receive(knot(30));receive(chain(2,[30],2));
 A.assert(!knots().length&&!bursts().length,'expired incoming burst replayed fresh phase');out.expiredFront=true;
 reset();receive(knot(1));step(6.91);receive(knot(1));
 A.assert(!knots().length&&N.inspect().chainProtection===0,'old age-zero seed replayed after retirement');out.ttl=true;
 // Whole presentation rejection at 32 preserves all consumed-ID protection.
 reset();for(let i=0;i<4;i++)receive(chain(10+i,Array.from({length:8},(_,j)=>100+i*8+j)));
 A.assert(bursts().length===32,'remote burst ceiling fixture');receive(knot(500));
 receive(chain(14,[500,501]));A.assert(bursts().length===32&&!knots().length,'overflow partially presented or missed consumption');
 step(1);receive(chain(14,[500,501]));receive(knot(501));
 A.assert(!bursts().length&&!knots().length,'overflow activation replayed after capacity freed');out.presentationCap=true;
 // Admission at 1023/1024 is all-or-nothing; no live record may be evicted.
 reset();for(let id=1;id<=1023;id++)receive(knot(id,id*60));
 A.assert(N.inspect().chainProtection===1023,'protection fixture size');const before=knots().map(a=>a.seedId).join(',');
 receive(chain(1,[2000]));A.assert(N.inspect().chainProtection===1023&&!bursts().length&&knots().map(a=>a.seedId).join(',')===before,'protection overflow partially admitted');
 receive(chain(2,[1023]));A.assert(N.inspect().chainProtection===1024&&bursts().length===1,'exact protection capacity rejected');
 receive(knot(2001));A.assert(N.inspect().chainProtection===1024&&!knots().some(a=>a.seedId===2001),'evicted live replay protection');out.protectionCap=true;
 reset();const unchanged=(event,label,from='guest')=>{const n=knots().length,b=bursts().length,c=N.inspect().chainProtection;
   N.receive(from,event);A.assert(knots().length===n&&bursts().length===b&&N.inspect().chainProtection===c,label)};
 let event=knot(1);unchanged(['tk',['wrong',0],'guest',event[3]],'stale stamp');
 unchanged(['tk',N.stamp(),'host',event[3]],'spoofed uid');
 unchanged(['tk',N.stamp(),'guest',{...event[3],x:NaN}],'NaN seed');
 unchanged(['tk',N.stamp(),'guest',{...event[3],seedId:1.2}],'fractional seed id');
 event=chain(1,[1]);unchanged(['tg',N.stamp(),'guest',{...event[3],consumedIds:[1,1]}],'duplicate consumed id');
 unchanged(['tg',N.stamp(),'guest',{...event[3],bursts:[{...event[3].bursts[0],cuts:999}]}],'cuts cap');
 unchanged(['tg',N.stamp(),'guest',{...event[3],bursts:[{...event[3].bursts[0],radius:441}]}],'radius cap');
 const mate=G.Coop.mate('guest');mate.pl.dead=true;unchanged(knot(2),'dead owner');mate.pl.dead=false;
 mate.connected=false;unchanged(knot(2),'disconnected owner');mate.connected=true;
 receive(['tx',N.stamp(),'guest','clone:retired']);unchanged(knot(2,120,0,'clone:retired'),'retired clone');
 receive(knot(3));G.Combat.clearFields(mate.pl);receive(knot(3));A.assert(!knots().length,'owner clear replayed seed');
 event=knot(4);G.Combat.clearFields();unchanged(event,'scene teardown');out.guards=true;
 reset();receive(knot(10));receive(chain(10,[11]));receive(knot(30,240));receive(chain(30,[31]));
 const removal=['tg',N.stamp(),'guest',{actor:'player',removed:true,seedThrough:20,activationThrough:20}];
 receive(removal);
 A.assert(knots().length===1&&knots()[0].seedId===30&&bursts().length===1&&bursts()[0].activationId===30,'old removal cleared newer results');
 receive(knot(10));receive(chain(10,[11]));receive(removal);
 A.assert(knots().length===1&&bursts().length===1,'removed sequence replay or duplicate cleanup');
 receive(['tg',N.stamp(),'guest',{...removal[3],seedThrough:25,activationThrough:15}]);
 A.assert(knots().length===1&&bursts().length===1,'nonuniform removal floors moved backwards');
 unchanged(['tg',N.stamp(),'guest',{...removal[3],seedThrough:NaN}],'invalid removal floor');
 unchanged(['tg',N.stamp(),'guest',{...removal[3],bursts:[]}],'mixed removal payload');out.selectiveRemoval=true;
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'coverage': 'Native two-context committed-result hooks and controlled protocol lifecycle',
              'notCovered': ['Core attack eligibility (separate mechanic suite)', 'Firebase', 'WebRTC', 'natural play'],
              'wire': [], 'cases': [], 'errors': [], 'ok': False}
    root = Path(__file__).resolve().parents[1]
    report['sourceHashes'] = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
                             ['.omx/naruto-temari.js', '.omx/temari-coop.js', 'js/net/coop.js', 'tools/test_temari_wind_chain_coop.py']}
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
                page.evaluate("Acceptance.assert(G.NarutoTemari.applyWindKnot&&G.NarutoTemari.applyWindChain,'wind-chain APIs missing')")
                pages[uid] = page
            for caster_uid in ['host', 'guest']:
                for clone in [False, True]:
                    for page in pages.values():
                        page.evaluate('G.SelfClones.clear();G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();CoopFixture.drain()')
                    pump(pages, report)
                    caster, viewer = pages[caster_uid], pages['guest' if caster_uid == 'host' else 'host']
                    packets = caster.evaluate('''clone=>{const A=Acceptance,p=A.p(),T=G.NarutoTemari;let owner=p;
                      if(clone){const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');A.assert(card&&card.apply(p)!==false,'clone card');owner=G.SelfClones.actors()[0];}
                      const seed={seedId:100,sourceCastId:10,x:180,y:37,age:0,ttl:6};
                      const profile=T.windChainProfile(p,p.moves.find(m=>m.digiMode==='temari-great-scythe'));
                      const activation={heavyCastId:20,activationId:200,consumedIds:[100],bursts:[{id:300,x:180,y:37,age:0,radius:profile.radius,cuts:profile.cuts,interval:.1,travel:.08,damageType:'flying'}]};
                      window.ChainActor=owner;window.ChainActivation=activation;T.onWindKnot(owner,seed);
                      return {seed,activation};}''', clone)
                    pump(pages, report)
                    remote = viewer.evaluate('G.NarutoTemari.windKnots.map(a=>({x:a.x,y:a.y,seedId:a.seedId}))')
                    assert remote == [{'x': 180, 'y': 37, 'seedId': 100}], remote
                    caster.evaluate('G.NarutoTemari.onWindChain(ChainActor,ChainActivation)')
                    pump(pages, report)
                    outcome = viewer.evaluate('''()=>{const T=G.NarutoTemari,A=Acceptance,e=A.spawn(180,37),hits=A.watch(e),hp=e.hp;
                      const before=T.windBursts.map(a=>({x:a.x,y:a.y,cuts:a.cuts,radius:a.radius}));
                      A.resume();try{for(let i=0;i<60;i++)T.update(.01)}finally{A.pause()}
                      return {before,remainingKnots:T.windKnots.length,hits:hits.length,hpUnchanged:e.hp===hp};}''')
                    assert outcome['before'] == [{'x': 180, 'y': 37, 'cuts': packets['activation']['bursts'][0]['cuts'], 'radius': packets['activation']['bursts'][0]['radius']}], outcome
                    assert outcome['remainingKnots'] == 0 and outcome['hits'] == 0 and outcome['hpUnchanged'], outcome
                    report['cases'].append({'caster': caster_uid, 'clone': clone, 'outcome': outcome})
                    print(caster_uid, 'clone' if clone else 'player', 'routed chain PASS', flush=True)
            # Fresh scene: actual native basic producer -> actual heavy front.
            # Earlier hook-boundary packets used synthetic IDs deliberately;
            # they must not affect this independent native integration proof.
            for page in pages.values():
                page.evaluate('''()=>{const p=G.Game.player;G.SelfClones.clear();G.Combat.clearFields();G.EnemyMgr.clear();
                  G.Projectiles.clear();CoopFixture.drain();p.x=p.y=0;p.target=null;p.cdMul=1;p.quantityBonus=p.quantityPicks=0;
                  Acceptance.mastery(1);for(const m of p.moves)m.t=999;}''')
            host, guest = pages['host'], pages['guest']
            host.evaluate("window.ChainEnemy=Acceptance.spawn(140,0,'boss');ChainEnemy.hp=ChainEnemy.maxHp=1e9;window.ChainHits=Acceptance.watch(ChainEnemy);G.Coop.tick(.1);G.Game.player.target=ChainEnemy;G.Game.player.aim=0")
            pump(pages, report)
            guest.evaluate('''()=>{window.ChainGhostHurt=0;const enemy=G.EnemyMgr.all().find(e=>e.remote);Acceptance.assert(enemy,'replicated native target missing');
              const hurt=enemy.hurt;enemy.hurt=function(...args){ChainGhostHurt++;return hurt.apply(this,args)}}''')
            wire_start = len(report['wire'])
            for _ in range(140):
                host.evaluate('''()=>{Acceptance.resume();for(let i=0;i<5;i++){
                  G.Combat.tick(.01,G.Game.player,0);CoopFixture.step(1)}Acceptance.pause()}''')
                guest.evaluate('CoopFixture.step(5)')
                pump(pages, report)
                if host.evaluate('G.NarutoTemari.windKnots.some(a=>a.owner===G.Game.player)'):
                    break
            else:
                raise AssertionError('actual empowered native basics did not create knot')
            local_seed = host.evaluate('G.NarutoTemari.windKnots.filter(a=>a.owner===G.Game.player).map(a=>({seedId:a.seedId,x:a.x,y:a.y}))')
            remote_seed = guest.evaluate('G.NarutoTemari.windKnots.map(a=>({seedId:a.seedId,x:a.x,y:a.y}))')
            assert local_seed == remote_seed and local_seed, (local_seed, remote_seed)
            host.evaluate("Acceptance.castNative('naruto-temari-great-scythe')")
            remote_bursts = []
            for _ in range(28):
                host.evaluate('CoopFixture.step(5)')
                guest.evaluate('CoopFixture.step(5)')
                pump(pages, report)
                if not remote_bursts:
                    remote_bursts = guest.evaluate('G.NarutoTemari.windBursts.map(a=>({x:a.x,y:a.y,cuts:a.cuts,radius:a.radius}))')
            derived = host.evaluate("ChainHits.filter(h=>h.id==='naruto-temari-wind-chain').length")
            native_wire = report['wire'][wire_start:]
            seeds = [item['event'][3] for item in native_wire if item['event'][0] == 'tk']
            activations = [item['event'][3] for item in native_wire if item['event'][0] == 'tg']
            assert seeds and len(activations) == 1, native_wire
            expected = [{key: burst[key] for key in ['x', 'y', 'cuts', 'radius']} for burst in activations[0]['bursts']]
            assert remote_bursts == expected and derived == 3 and guest.evaluate('ChainGhostHurt') == 0, (remote_bursts, expected, derived)
            report['nativeProducer'] = {'seeds': local_seed, 'activation': activations[0], 'remoteBursts': remote_bursts,
                                        'actualDerivedHits': derived, 'receiverHurtCalls': guest.evaluate('ChainGhostHurt')}
            print('actual native empowered basic -> heavy -> 3 hits routed PASS', flush=True)
            report['lifecycle'] = pages['host'].evaluate(LIFECYCLE)
            report['nativeUnlearn'] = unlearn_cases(browser, report)
            assert not report['errors'], report['errors']
            browser.close()
        report['ok'] = True
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': report['ok'], 'cases': len(report['cases']), 'lifecycle': report.get('lifecycle')}))


if __name__ == '__main__':
    main()
