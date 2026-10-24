"""Two-browser Temari Coop protocol test using the supported adapter boundary.

Python forwards JSON packets between independent browser contexts. Native Coop
serialization, enemy replication, guest hurt forwarding, ghost casts and shot
authority run unchanged. This does NOT cover Firebase login, signaling, real
WebRTC transport, packet loss or an internet lobby. No credentials are needed.
"""
import json
import os

from playwright.sync_api import sync_playwright
from test_temari import CHROME, OUT, URL, boot

ADAPTER = r"""async uid => {
 const listeners=new Set(),peers=new Set(),roomListeners=new Set(),out=[];
 const rooms={uid,me:{name:uid},room:null,started:false,start(){},stop(){},claimNick(){},createRoom(){},joinRoom(){},leaveRoom(){},
   setOpen(){},refreshMember(){},setPlaying(){},on:f=>roomListeners.add(f),off:f=>roomListeners.delete(f)};
 const transport={uid,hostUid:'host',isHost:uid==='host',open_:false,open(){this.open_=true},close(){this.open_=false},syncMembers(){},
   send(to,msg){out.push({from:uid,to,msg:JSON.parse(JSON.stringify(msg))})},peers:()=>[uid==='host'?'guest':'host'],mode:()=> 'connected',slow:()=>false,
   on:f=>listeners.add(f),off:f=>listeners.delete(f),onPeer:f=>peers.add(f),offPeer:f=>peers.delete(f)};
 await G.Multiplayer.configure({rooms,transport});transport.open();
 const A=Acceptance,p=A.p();A.learn();p.moves=p.moves.filter(m=>m.id!=='naruto-temari-blade-dance');A.reset();A.mastery(5);p.quantityBonus=p.quantityPicks=5;
 const cfg={host:'host',seed:123,members:[{uid:'host',name:'Host',dex:30011},{uid:'guest',name:'Guest',dex:30011}]};
 A.resume();G.Coop.begin(cfg,p,{team:()=>({time:0,level:30,xp:0,xpNext:1e12,kills:0,bosses:0,coins:0,t1:0,t10:0}),syncTeam(){},waiting(){},resume(){},levelStart(){},lost(){},over(){},shiny(){},item(){},summary(){return {}},mateLeft(){}});
 p.x=p.y=0;for(const m of p.moves)m.t=999;
 const step=()=>{A.resume();try{G.EnemyMgr.rebuildGrid();G.Projectiles.update(.01,p,G.EnemyMgr.all());G.Combat.resolve(.01,p,0);G.Combat.updateFields(.01);p.anim.update(.01);G.Coop.tick(.01)}finally{A.pause()}};
 window.CoopFixture={out,receive:(from,msg)=>{for(const f of listeners)f(from,msg)},disconnect:other=>{for(const f of peers)f(other,'closed')},
   step:n=>{for(let i=0;i<n;i++)step()},drain:()=>out.splice(0),
   effectCount:()=>[...G.NarutoTemari.blades,...G.NarutoTemari.waves,...G.NarutoTemari.summons].filter(a=>a.owner.remote).length};
 A.pause();return {uid,configured:G.Multiplayer.configured,host:G.Coop.isHost};
}"""


def pump(pages, report):
    """Deliver all queued messages without replacing any native packet handler."""
    for _ in range(20):
        messages = []
        for page in pages.values():
            messages.extend(page.evaluate('CoopFixture.drain()'))
        if not messages:
            return
        for message in messages:
            report['packets'] += 1
            for event in message['msg'].get('ev', []):
                report['eventKinds'][event[0]] = report['eventKinds'].get(event[0], 0)+1
                if event[0] == 'tc':
                    report['lastCastPacket'] = message
                if event[0] == 'tp':
                    report['lastPetPacket'] = message
            pages[message['to']].evaluate('(m)=>CoopFixture.receive(m.from,m.msg)', message)
    raise AssertionError('protocol produced an unbounded synchronous packet loop')


def advance(pages, report, seconds):
    for _ in range(round(seconds/.05)):
        for page in pages.values():
            page.evaluate('CoopFixture.step(5)')
        pump(pages, report)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'coverage': 'Native Coop over controlled in-memory JSON transport between two independent browser contexts',
              'notCovered': ['Firebase credentials/login', 'WebRTC signaling/transport', 'internet lobby', 'packet loss/reordering'],
              'packets': 0, 'eventKinds': {}, 'errors': [], 'scenarios': {}, 'requestedChecks':os.environ.get('TEMARI_COOP_CHECKS','all'), 'ok': False}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            contexts, pages = [], {}
            for uid in ['host', 'guest']:
                context = browser.new_context(viewport={'width': 1000, 'height': 800}, service_workers='block')
                # Keep time deterministic in both clients. DOM boot, real picker
                # and native game APIs still run; only the RAF clock is manual.
                context.add_init_script('window.requestAnimationFrame=()=>0')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                boot(page)
                report['scenarios'][uid+'Setup'] = page.evaluate(ADAPTER, uid)
                contexts.append(context)
                pages[uid] = page
            host, guest = pages['host'], pages['guest']
            host.evaluate("window.CoopEnemy=Acceptance.spawn(140,0,'boss');window.CoopHits=Acceptance.watch(CoopEnemy);G.Coop.tick(.1)")
            pump(pages, report)
            guest.wait_for_function('G.EnemyMgr.all().some(e=>e.remote)')
            guest.evaluate('window.CoopEnemy=G.EnemyMgr.all().find(e=>e.remote);G.EnemyMgr.rebuildGrid();G.Game.player.target=CoopEnemy;G.Game.player.aim=0')
            host.evaluate('G.Game.player.target=CoopEnemy;G.Game.player.aim=0')
            if os.environ.get('TEMARI_COOP_CHECKS') != 'interception':
                for caster_uid in ['host', 'guest']:
                    for skill in ['naruto-temari', 'naruto-temari-great-scythe']:
                        name = caster_uid+':'+skill
                        print(name, flush=True)
                        caster = pages[caster_uid]
                        before = host.evaluate('({hp:CoopEnemy.hp,hits:CoopHits.length})')
                        for page in pages.values():
                            page.evaluate('G.Combat.clearFields()')
                        caster.evaluate('(id)=>Acceptance.castNative(id)', skill)
                        pump(pages, report)
                        if caster_uid == 'host' and skill == 'naruto-temari':
                            packet = report['lastCastPacket']
                            receiver = pages[packet['to']]
                            before_duplicate = receiver.evaluate('G.NarutoTemari.casts.length')
                            receiver.evaluate('(m)=>CoopFixture.receive(m.from,m.msg)', packet)
                            assert receiver.evaluate('G.NarutoTemari.casts.length') == before_duplicate, 'duplicate cast packet created a second ghost'
                            report['scenarios']['duplicateCastIgnored'] = True
                        advance(pages, report, .7)
                        viewer = pages['guest' if caster_uid == 'host' else 'host']
                        ghost = viewer.evaluate('CoopFixture.effectCount()')
                        assert ghost > 0, name+': remote ghost effect missing'
                        viewer.screenshot(path=str(OUT / ('coop-'+caster_uid+'-'+skill+'.png')))
                        # Drawing the remote avatar must still use Temari's artwork.
                        art = viewer.evaluate('Acceptance.pose(G.Coop.puppets()[0]).sources')
                        assert art and all('temari' in source.lower() for source in art), art
                        advance(pages, report, 5)
                        outcome = host.evaluate('({hp:CoopEnemy.hp,hits:CoopHits.length})')
                        stats = caster.evaluate('''() => {const f=G.NarutoTemari.stateFor(G.Game.player).latest;
                          return {emitted:f.emitted,cuts:f.cuts,hits:f.hits,count:f.count,damage:f.damage,id:f.id}}''')
                        assert stats['hits'] > 0, name+': no authoritative local contact'
                        assert outcome['hits']-before['hits'] == stats['hits'], name+': ghost duplicated or forwarding lost hurt events'
                        assert outcome['hp'] < before['hp'], name+': host HP unchanged'
                        stable = outcome['hp']
                        advance(pages, report, .4)
                        assert host.evaluate('CoopEnemy.hp') == stable, name+': expired effects damaged again'
                        report['scenarios'][name] = {'ghostActorsAt700ms': ghost, 'hostDamage': before['hp']-outcome['hp'], **stats}
                        # The module keeps cast cooldowns independently of move.t.
                        # Advance native cooldowns without permitting another cast.
                        caster.evaluate('''() => {const p=G.Game.player,moves=p.moves;p.moves=[];Acceptance.resume();
                          try{G.Combat.tick(12,p,0)}finally{p.moves=moves;Acceptance.pause()}}''')
                # A learned passive companion remains visible without selecting a
                # move, wanders between fights, and attacks on only its owner's peer.
                host.evaluate('CoopEnemy.dead=true;G.Coop.enemyGone(CoopEnemy,false);G.Coop.tick(.1)')
                pump(pages, report)
                for caster_uid in ['host', 'guest']:
                    caster = pages[caster_uid]
                    viewer = pages['guest' if caster_uid == 'host' else 'host']
                    for page in pages.values():
                        page.evaluate("G.Game.player.moves=G.Game.player.moves.filter(m=>m.id!=='naruto-temari-blade-dance');G.Combat.clearFields()")
                    caster.evaluate("""() => {const A=Acceptance,p=A.p();p.quantityPicks=p.quantityBonus=0;p.cdMul=.12;A.mastery(0);
                      const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-temari-blade-dance');A.assert(card,'passive pet learn card missing');
                      const slots=p.slots.length;card.apply(p);A.assert(p.slots.length===slots,'passive pet added an active slot');
                      window.PetSlot=p.active;window.PetHitsBefore=G.NarutoTemari.stateFor(p)?.hitEvents||0;}""")
                    advance(pages, report, .3)
                    initial=caster.evaluate("G.NarutoTemari.summons.filter(a=>a.owner===G.Game.player).map(a=>({id:a.petId||a.id,x:a.x,y:a.y,phase:a.phase}))")
                    assert len(initial)==1, caster_uid+': passive pet did not appear while idle'
                    assert viewer.evaluate('G.NarutoTemari.summons.filter(a=>a.owner.remote).length')==1, 'idle remote pet invisible'
                    viewer.screenshot(path=str(OUT/('coop-'+caster_uid+'-permanent-pet-idle.png')))
                    caster.evaluate('G.Game.player.x=100')
                    advance(pages,report,.4)
                    followed=caster.evaluate('G.NarutoTemari.summons.find(a=>a.owner===G.Game.player).x')
                    assert abs(followed-initial[0]['x'])>5,'pet did not roam nearby'
                    caster.evaluate('G.Game.player.x=0')
                    host.evaluate("window.CoopEnemy=Acceptance.spawn(140,0,'boss');CoopEnemy.hp=CoopEnemy.maxHp=1e9;window.CoopHits=Acceptance.watch(CoopEnemy);G.Coop.tick(.1)")
                    pump(pages,report)
                    guest.evaluate('window.CoopEnemy=G.EnemyMgr.all().find(e=>e.remote&&!e.dead);G.EnemyMgr.rebuildGrid()')
                    phases={'wander'}
                    for _ in range(80):
                        advance(pages,report,.05)
                        phases.update(viewer.evaluate('G.NarutoTemari.summons.filter(a=>a.owner.remote).map(a=>a.phase)'))
                    assert {'wander','move','slash','return'}.issubset(phases),'remote pet lifecycle phases missing '+str(phases)
                    actual=host.evaluate('CoopHits.length')
                    owned=caster.evaluate('(G.NarutoTemari.stateFor(G.Game.player)?.hitEvents||0)-PetHitsBefore')
                    assert actual==owned and actual>=8,'passive owner damage missing/duplicated '+str((actual,owned))
                    assert caster.evaluate('G.Game.player.active===PetSlot'),'pet changed selected move'
                    host.evaluate('CoopEnemy.dead=true;G.Coop.enemyGone(CoopEnemy,false);G.Coop.tick(.1)')
                    pump(pages,report);advance(pages,report,1)
                    stable=caster.evaluate("G.NarutoTemari.summons.filter(a=>a.owner===G.Game.player).map(a=>a.petId||a.id)")
                    assert stable==[initial[0]['id']],'persistent companion was destroyed after attack'
                    caster.evaluate('G.Game.player.quantityPicks=G.Game.player.quantityBonus=5')
                    advance(pages,report,.3)
                    grown=caster.evaluate("G.NarutoTemari.summons.filter(a=>a.owner===G.Game.player).map(a=>a.petId||a.id)")
                    assert len(grown)==3 and initial[0]['id'] in grown,'quantity rebuilt or failed to grow pet roster'
                    assert viewer.evaluate('G.NarutoTemari.summons.filter(a=>a.owner.remote).length')==3,'quantity roster not synchronized'
                    report['scenarios'][caster_uid+':permanentPets']={'initial':initial,'followedX':followed,'hits':actual,'grownIds':grown,'remotePhases':sorted(phases)}
                # Clone pets have separate stable actor identity and clean up with the clone.
                # A remote clone keeps full quantity and its own identity, then an
                # explicit native expiry removes the remote ghost and pending cuts.
                guest.evaluate('''() => {const p=G.Game.player,c=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');c.apply(p);
                  const a=G.SelfClones.actors()[0];window.CoopClone=a;a.x=a.y=0;a.aim=0}''')
                pump(pages, report)
                advance(pages, report, .7)
                clones = host.evaluate('G.TemariCoop.remoteActors().map(a=>({actor:a.temariActorId||a.cloneId,dex:a.dex}))')
                assert clones, 'guest clone cast never produced a separate remote actor'
                tx_before = report['eventKinds'].get('tx', 0)
                guest.evaluate('G.SelfClones.clear(CoopClone)')
                pump(pages, report)
                assert host.evaluate('G.TemariCoop.remoteActors().length') == 0, 'expired guest clone ghost retained'
                assert report['eventKinds'].get('tx', 0) == tx_before+1, 'native clone expiry must send one removal event'
                guest.evaluate('G.TemariCoop.actorRemoved(CoopClone);G.TemariCoop.actorRemoved(CoopClone)')
                pump(pages, report)
                assert report['eventKinds'].get('tx', 0) == tx_before+1, 'repeat cleanup emitted duplicate clone expiry'
                report['scenarios']['cloneIdentityAndExpiry'] = clones
            for page in pages.values():
                page.evaluate("G.Game.player.moves=G.Game.player.moves.filter(m=>m.id!=='naruto-temari-blade-dance');G.Combat.clearFields()")
            host.evaluate("for(const e of G.EnemyMgr.all())if(!e.dead){e.dead=true;G.Coop.enemyGone(e,false)}window.CoopEnemy=Acceptance.spawn(140,0,'boss');G.Coop.tick(.1)")
            pump(pages,report)
            guest.evaluate('window.CoopEnemy=G.EnemyMgr.all().find(e=>e.remote&&!e.dead);G.Game.player.target=CoopEnemy;Acceptance.mastery(5);G.Game.player.cdMul=1;G.EnemyMgr.rebuildGrid()')
            # Host owns interception. Guest and host must remove the same ID,
            # while rear and explicitly special projectiles remain untouched.
            for page in pages.values():
                page.evaluate('G.Combat.clearFields();G.Projectiles.clear()')
            for _ in range(2):
                guest.evaluate("""() => {try{Acceptance.castNative('naruto-temari')}catch(error){const p=G.Game.player;
                  throw Error(error.message+' '+JSON.stringify({hp:p.hp,dead:p.dead,frozen:p.frozen,x:p.x,y:p.y,
                    target:CoopEnemy&&{x:CoopEnemy.x,y:CoopEnemy.y,hp:CoopEnemy.hp,dead:CoopEnemy.dead},
                    enemies:G.EnemyMgr.all().map(e=>({x:e.x,y:e.y,hp:e.hp,dead:e.dead})),state:{basicCooldown:G.NarutoTemari.stateFor(p)?.basicCooldown,basicRounds:G.NarutoTemari.stateFor(p)?.basicRounds}}))}}""")
                pump(pages, report)
                advance(pages, report, 2)
                guest.evaluate('''() => {const p=G.Game.player,moves=p.moves;p.moves=[];Acceptance.resume();try{G.Combat.tick(2,p,0)}finally{p.moves=moves;Acceptance.pause()}}''')
            shots = host.evaluate('''() => {window.AuthorityShots=[];for(const [name,x,flags] of [['front',50,{}],['rear',-50,{}],['special',45,{bossSpecial:true}],['unblockable',40,{unblockable:true}]]){
              const shot=G.Projectiles.spawn({x,y:0,vx:0,vy:0,dmg:7,r:3,life:20,friendly:false,interceptable:true,...flags});G.Coop.enemyShot(shot,'flying');AuthorityShots.push({name,id:shot.coopShotId})}return AuthorityShots}''')
            pump(pages, report)
            guest.evaluate("""() => {try{Acceptance.castNative('naruto-temari')}catch(error){const p=G.Game.player;
                  throw Error(error.message+' '+JSON.stringify({hp:p.hp,dead:p.dead,frozen:p.frozen,x:p.x,y:p.y,
                    target:CoopEnemy&&{x:CoopEnemy.x,y:CoopEnemy.y,hp:CoopEnemy.hp,dead:CoopEnemy.dead},
                    enemies:G.EnemyMgr.all().map(e=>({x:e.x,y:e.y,hp:e.hp,dead:e.dead})),state:{basicCooldown:G.NarutoTemari.stateFor(p)?.basicCooldown,basicRounds:G.NarutoTemari.stateFor(p)?.basicRounds}}))}}""")
            assert guest.evaluate('G.NarutoTemari.stateFor(G.Game.player).latest.empowered'), 'third-round authority fixture not empowered'
            pump(pages, report)
            advance(pages, report, .35)
            for uid, page in pages.items():
                live = page.evaluate('G.Projectiles.all().map(s=>s.coopShotId)')
                assert shots[0]['id'] not in live, uid+': authoritative front interception not reconciled'
                assert all(shot['id'] in live for shot in shots[1:]), uid+': excluded projectile incorrectly intercepted'
            assert report['eventKinds'].get('td', 0)>0, 'interception never emitted authoritative protocol event'
            report['scenarios']['interceptionAuthority'] = shots
            # Scene changes use the same public boundary as rift/reset.
            stale = report['lastCastPacket']
            for page in pages.values():
                page.evaluate('G.Combat.clearFields();G.Projectiles.clear()')
                assert page.evaluate('CoopFixture.effectCount()') == 0
            pages[stale['to']].evaluate('(m)=>CoopFixture.receive(m.from,m.msg)', stale)
            assert pages[stale['to']].evaluate('G.NarutoTemari.casts.length') == 0, 'stale previous-scene packet resurrected effects'
            guest.evaluate("""() => {const p=G.Game.player;p.quantityPicks=p.quantityBonus=0;
              const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-temari-blade-dance');Acceptance.assert(card,'lifecycle pet card missing');card.apply(p)}""")
            advance(pages,report,.3)
            assert host.evaluate('G.NarutoTemari.summons.filter(a=>a.owner.remote).length')==1,'disconnect fixture has no remote companion'
            host.evaluate("CoopFixture.disconnect('guest')")
            advance(pages, report, .2)
            assert host.evaluate('G.Coop.puppets().length') == 0, 'disconnected peer remains active'
            assert host.evaluate('CoopFixture.effectCount()') == 0, 'disconnected peer retained events'
            report['scenarios']['sceneAndDisconnectCleanup'] = True
            for page in pages.values():
                page.evaluate('G.Coop.end();G.Combat.clearFields()')
            for context in contexts:
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report['failure'] = str(error)
    finally:
        (OUT / ('coop-report-focused.json' if os.environ.get('TEMARI_COOP_CHECKS') else 'coop-report.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': report['ok'], 'failure': report.get('failure'), 'packets': report['packets'], 'evidence': str(OUT / ('coop-report-focused.json' if os.environ.get('TEMARI_COOP_CHECKS') else 'coop-report.json'))}))
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
