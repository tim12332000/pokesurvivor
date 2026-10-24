"""Native reflection authority and prediction over two-client JSON transport."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_temari import CHROME, URL, boot
from test_temari_coop import ADAPTER, pump, advance

OUT=Path(__file__).resolve().parents[1]/'.omx/state/temari-reflect'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    focused=os.environ.get('TEMARI_REFLECT_COOP_CHECKS')=='inside-beam'
    report={'bootPollingMs':20,'fixtureClock':'Manual RAF; native boot waits poll by timer because RAF polling cannot advance in this fixture','ok':False,'errors':[],'packets':0,'eventKinds':{},'scenarios':{},'coverage':'Two independent browser contexts with native Coop JSON transport, no WebRTC internet lobby'}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            pages={}
            for uid in ['host','guest']:
                context=browser.new_context(viewport={'width':1000,'height':800},service_workers='block')
                context.add_init_script('window.requestAnimationFrame=()=>0')
                page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
                report['bootStage']=uid+':native-ui-boot'
                try:
                    boot(page)
                except Exception:
                    report['bootDiagnostic']=page.evaluate("""() => ({url:location.href,state:G.Game.state,partner:G.DB.save.partner,player:G.Game.player?.dex,
                      hidden:document.hidden,visibility:document.visibilityState,art:G.TemariArt?.loaded,record:G.Naruto.records.get(30011)?.ready,assets:G.NarutoAssets?.ready(30011),
                      play:{disabled:document.querySelector('#scr-menu [data-go="play"]')?.disabled,text:document.querySelector('#scr-menu [data-go="play"]')?.textContent},
                      menuHidden:document.getElementById('scr-menu')?.classList.contains('hidden'),boot:document.getElementById('boot')?.outerHTML})""")
                    page.screenshot(path=str(OUT/('boot-failure-'+uid+'.png')))
                    raise
                report['bootStage']=uid+':native-coop-adapter'
                page.evaluate(ADAPTER,uid)
                page.evaluate("""() => {const A=Acceptance,p=A.p();p.level=30;
                  const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-temari-reflect');A.assert(card,'native reflect learning card absent');card.apply(p);
                  A.mastery(0);p.quantityBonus=p.quantityPicks=0;p.critChance=0;p.percentHealthDamage=0;p.lifestealRate=.1;p.item='shellbell';
                  const step=CoopFixture.step;CoopFixture.step=n=>{for(let i=0;i<n;i++){step(1);A.resume();try{G.Hazards.update(.01)}finally{A.pause()}}};
                }""")
                pages[uid]=page
            host,guest=pages['host'],pages['guest']
            if not focused:
                advance(pages,report,10.2)
                for uid,page in pages.items():
                    remote='guest' if uid=='host' else 'host'
                    idle=page.evaluate("uid=>{const p=G.Game.player,r=G.Coop.mate(uid).pl,T=G.NarutoTemariReflect;return {local:!!T.activeFor(p)?.permanent,remote:!!T.activeFor(r)?.permanent,casts:T.stateFor(p)?.casts,remoteGhost:T.activeFor(r)?.ghost}}",remote)
                    assert idle['local'] and idle['remote'] and idle['remoteGhost'] and idle['casts']==0,'idle permanent wall missing '+str(idle)
                    report['scenarios'][uid+':idleAfterTenSeconds']=idle
                before=host.evaluate("G.NarutoTemariReflect.activeFor(G.Coop.mate('guest').pl).castId")
                guest.evaluate("Acceptance.rank('naruto-temari-reflect',5);G.Game.player.quantityPicks=G.Game.player.quantityBonus=5")
                advance(pages,report,1.2)
                grown=host.evaluate("(()=>{const w=G.NarutoTemariReflect.activeFor(G.Coop.mate('guest').pl);return {castId:w.castId,radius:w.radius,copies:w.copies}})()")
                assert grown['castId']==before and grown['radius']==140 and grown['copies']==3,'remote permanent wall growth stale '+str(grown)
                guest.evaluate("Acceptance.rank('naruto-temari-reflect',1);G.Game.player.quantityPicks=G.Game.player.quantityBonus=0")
                advance(pages,report,1.2)
            for caster_uid in ([] if focused else ['host','guest']):
                for kind in ['projectile','beam','zone']:
                    print(caster_uid+':'+kind,flush=True)
                    for page in pages.values():
                        page.evaluate('G.Combat.clearFields();G.Projectiles.clear();G.Hazards.clear();G.Game.player.hp=G.Game.player.maxHp*.5')
                    host.evaluate("""() => {for(const e of [...G.EnemyMgr.all()]){e.dead=true;G.Coop.enemyGone(e,false)}
                      window.SourceEnemy=Acceptance.spawn(250,0,'boss');SourceEnemy.hp=SourceEnemy.maxHp=1e9;window.ReflectionHits=Acceptance.watch(SourceEnemy);G.Coop.tick(.2)}""")
                    pump(pages,report)
                    caster=pages[caster_uid]
                    for uid,page in pages.items():
                        page.evaluate('(active)=>{G.Game.player.x=active?0:1000;G.Game.player.y=0;G.Coop.tick(.2)}',uid==caster_uid)
                    pump(pages,report)
                    caster.evaluate("G.NarutoTemariReflect.sync(G.Game.player)")
                    pump(pages,report)
                    shot_id=host.evaluate("""kind=>{if(kind==='projectile'){
                      const p=G.Projectiles.spawn({x:200,y:0,vx:-400,vy:0,dmg:20,r:4,life:5,friendly:false,interceptable:false,bossSpecial:true});
                      G.Coop.enemyShot(p,'normal');return p.coopShotId;}
                      const h=G.Hazards.add({kind:kind==='beam'?'beam':'zone',x:kind==='beam'?250:0,y:0,
                        sourceX:250,sourceY:0,ranged:true,angle:Math.PI,len:500,w:14,r:40,delay:.2,dmg:20,type:'normal',color:'#fff'});
                      return h.coopShotId;
                    }""",kind)
                    assert shot_id,kind+': source missing network identity'
                    host.evaluate('G.Coop.tick(.2)');pump(pages,report)
                    hp_before=guest.evaluate('G.Game.player.hp')
                    if caster_uid=='guest':
                        guest.evaluate('CoopFixture.step(40)')
                        assert guest.evaluate('G.Game.player.hp')==hp_before,'predicted wall let guest take damage before authority ack'
                        if kind=='projectile':
                            assert guest.evaluate('G.Projectiles.all().some(p=>p.temariPending)'), 'projectile had no pending protection'
                        else:
                            assert guest.evaluate('G.TemariCoop.inspect().pendingHazards')==1,'hazard had no pending protection'
                    before=host.evaluate('SourceEnemy.hp')
                    advance(pages,report,1.5)
                    after=host.evaluate('({hp:SourceEnemy.hp,hits:ReflectionHits.length,shots:G.Projectiles.all().filter(p=>p.temariReflected).map(p=>({ghost:!!p.ghost}))})')
                    assert after['hits']==1 and after['hp']<before, 'host reflection missing or duplicated '+str(after)
                    live=guest.evaluate('G.Projectiles.all().filter(p=>p.temariReflected).map(p=>!!p.ghost)')
                    assert all(live),'guest spawned a damaging reflection'
                    if caster_uid=='guest':
                        heal=guest.evaluate('({hp:G.Game.player.hp,bell:G.Game.player.bellHeal})')
                        assert heal['hp']>hp_before and heal['bell']>0,'host reflection did not credit actual guest healing'
                    stable=after['hp'];advance(pages,report,.5)
                    assert host.evaluate('SourceEnemy.hp')==stable,'expired counter or ghost damaged again'
                    report['scenarios'][caster_uid+':'+kind]={'source':shot_id,'damage':before-after['hp'],'hits':after['hits'],'guestGhostFlags':live}
            print('guest:inside-origin-beam',flush=True)
            for uid,page in pages.items():
                page.evaluate("active=>{G.Combat.clearFields();G.Projectiles.clear();G.Hazards.clear();const p=G.Game.player;p.x=active?0:1000;p.y=0;p.hp=p.maxHp;p.item=null;p.lifestealRate=0;p.quantityPicks=p.quantityBonus=0;G.NarutoTemariReflect.sync(p);G.Coop.tick(.2)}",uid=='guest')
            pump(pages,report)
            host.evaluate("""() => {for(const e of [...G.EnemyMgr.all()]){e.dead=true;G.Coop.enemyGone(e,false)}
              window.SourceEnemy=Acceptance.spawn(250,0,'boss');SourceEnemy.hp=SourceEnemy.maxHp=1e9;
              window.ReflectionHits=Acceptance.watch(SourceEnemy);G.Coop.tick(.2)}""")
            pump(pages,report)
            shot_id=host.evaluate("""() => {const h=G.Hazards.add({kind:'beam',x:10,y:0,angle:Math.PI,len:200,w:24,
              ranged:true,delay:.2,dmg:20,type:'normal',color:'#fff'});G.Coop.tick(.2);return h.coopShotId}""")
            pump(pages,report)
            hp_before=guest.evaluate('G.Game.player.hp')
            guest.evaluate('CoopFixture.step(40)')
            assert guest.evaluate('G.Game.player.hp')==hp_before,'inside beam bypassed guest prediction before ack'
            host.evaluate('CoopFixture.step(25)')
            pump(pages,report)
            returned=guest.evaluate("id=>{const h=G.Hazards.all.find(h=>h.coopShotId===id);return h&&{hit:h.hit,len:h.len,returned:h.temariReturned}}",shot_id)
            assert returned and returned['hit'] and returned['len']==0 and returned['returned'],'guest zero-length beam remained live after tr '+str(returned)
            guest.evaluate('CoopFixture.step(5)')
            assert guest.evaluate('G.Game.player.hp')==hp_before,'received tr zero-length beam damaged guest during native Hazards.update'
            advance(pages,report,1.5)
            hit_count=host.evaluate('ReflectionHits.length')
            assert hit_count==1,'inside-origin beam host reflection missing or duplicated '+str(hit_count)
            assert guest.evaluate('G.Game.player.hp')==hp_before,'inside-origin beam changed guest hp after authority ack'
            report['scenarios']['guest:insideOriginBeam']={'source':shot_id,'receivedBeam':returned,'hostHits':hit_count,'guestHpBefore':hp_before,'guestHpAfter':guest.evaluate('G.Game.player.hp')}
            assert not report['errors'],report['errors']
            report['ok']=True;browser.close()
    except Exception as error:report['failure']=str(error)
    finally:(OUT/('reflection-coop-inside-beam-report.json' if focused else 'reflection-coop-report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':report['ok'],'failure':report.get('failure'),'packets':report['packets'],'eventKinds':report['eventKinds']}))
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':main()
