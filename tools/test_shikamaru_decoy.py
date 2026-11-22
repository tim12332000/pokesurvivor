"""Focused stationary shadow-lure acceptance through the production entry.

Mechanics use a controlled open arena. Native RAF/keyboard recordings are also
controlled examples, not a claim of natural progression or mobile hardware QA.
"""
from __future__ import annotations

import hashlib
import json
from playwright.sync_api import sync_playwright
import test_shikamaru as base

OUT = base.ROOT / 'art-review/shikamaru/qa/decoy'
SOURCES = ['.omx/naruto-shikamaru-decoy.js', '.omx/naruto-skills.js',
           '.omx/jujutsu-growth.js', '.omx/menu-layout.css',
           'js/entities/enemy.js', '.omx/digimon.html']


def manifest():
    return {name: hashlib.sha256((base.ROOT / name).read_bytes()).hexdigest()
            for name in SOURCES}


def observe(page, report):
    page.on('pageerror', lambda e: report['errors'].append({'message': str(e), 'stack': e.stack}))
    page.on('requestfailed', lambda r: report.setdefault('failedRequests', []).append({'url': r.url, 'error': r.failure}))
    page.on('response', lambda r: report.setdefault('badResponses', []).append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)


SETUP = r'''() => {
 const A=Acceptance,p=A.p(),D=G.NarutoShikamaruDecoy,ID='naruto-shikamaru-decoy';
 A.assert(D,'missing production stationary shadow module');
 A.decoyReset=()=>{A.reset();D.clear();p.level=2;p.moves=[G.Moves.instance(ID)];p.moves[0].t=0;};
 A.decoyStep=(dt=.01)=>{A.resume();try{D.update(dt)}finally{A.pause()}};
 A.decoyAdvance=seconds=>{for(let i=0;i<Math.ceil(seconds/.01);i++)A.decoyStep(.01)};
 A.decoyMine=owner=>D.decoys().filter(d=>d.owner===(owner||p));
 A.decoyCast=owner=>{owner??=p;const m=owner.moves.find(m=>m.id===ID);A.resume();try{A.assert(D.cast(owner,m),'stationary shadow cast rejected')}finally{A.pause()}return m};
 A.decoyStart=()=>{A.decoyReset();const e=A.spawn(100,0);A.decoyCast();A.decoyAdvance(.1);A.assert(A.decoyMine().length,'no fixed shadow actor');return e};
 A.decoyEnemyUpdate=(e,dt=.01)=>{A.resume();try{e.update(dt,p)}finally{A.pause()}};
 A.decoyProjectiles=seconds=>{for(let i=0;i<Math.ceil(seconds/.01);i++){A.resume();try{G.Projectiles.update(.01,p,G.EnemyMgr.all());G.Combat.resolve(.01,p,0);D.update(.01)}finally{A.pause()}}};
 A.decoyRanged=e=>{e.behavior='ranged';e.spd=0;e.dmg=25;e.def={...e.def,dmg:25,shotDmg:25,range:500,shotCd:10};e.shotCd=0;e.touchCd=99;return e};
}'''

PROGRESSION = r'''() => {
 const A=Acceptance,p=A.p(),D=G.NarutoShikamaruDecoy,ID='naruto-shikamaru-decoy';
 A.reset();p.level=1;p.moves=[G.Moves.instance('naruto-shikamaru')];
 A.assert(!G.LevelUp.offer(p,1000).some(c=>c.key==='new:'+ID),'lure appeared before Lv2');
 p.level=2;const learn=G.LevelUp.offer(p,1000).find(c=>c.key==='new:'+ID);
 A.assert(learn&&learn.apply(p)!==false,'actual Lv2 learn card missing');
 const m=p.moves.find(m=>m.id===ID),first=D.profile(p,m);
 A.assert(first.count===1&&first.life===3&&first.range===280&&m.dmg===0,'base lure contract');
 const quantity=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');
 A.assert(quantity&&quantity.apply(p)!==false,'first true quantity card absent');
 const quantityProfile=D.profile(p,m);A.assert(quantityProfile.count===2,'first quantity has no real actor consumer');
 A.spawn(100,0);A.decoyCast();A.decoyAdvance(.1);A.assert(A.decoyMine().length===2,'quantity did not create two real aim actors');
 D.clear(p);p.quantityPicks=p.quantityBonus=0;
 const preview=G.JujutsuGrowth.preview(p,G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+ID));A.assert(preview.desc.includes('留影秒數')&&preview.desc.includes('誘敵半徑')&&!preview.desc.includes('傷害'),'preview hid utility growth or advertised fake damage');
 for(let i=0;i<2;i++){const up=G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+ID);A.assert(up&&up.apply(p)!==false,'actual rank card missing')}
 const ranked=D.profile(p,m);A.assert(m.lvl===3&&ranked.count===2&&ranked.life>first.life&&ranked.range>first.range,'rank growth did not change lure behavior');
 p.quantityPicks=p.quantityBonus=99;A.assert(D.profile(p,m).count===6,'actor cap missing');
 const mon=p.mon;p.mon=G.DEX.find(m=>m.dex===30006);try{A.assert(!G.Moves.poolFor(p.mon).includes(ID),'lure leaked into Lee pool')}finally{p.mon=mon}
 return {first,quantityProfile,ranked,learned:m.id,rank:m.lvl,upgradePreview:preview.desc};
}'''

UTILITY = r'''() => {
 const A=Acceptance,p=A.p(),D=G.NarutoShikamaruDecoy,out={};
 let e=A.decoyStart(),d=A.decoyMine()[0],origin=[d.x,d.y];p.x=150;p.y=0;e.x=d.x+70;e.y=d.y+50;e.spd=60;e.flying=true;
 const distance=Math.hypot(e.x-d.x,e.y-d.y);A.decoyEnemyUpdate(e,.1);
 A.assert(e._shikamaruDecoyTarget===d&&Math.hypot(e.x-d.x,e.y-d.y)<distance,'native chase ignored stationary shadow');
 A.decoyAdvance(.2);A.assert(d.x===origin[0]&&d.y===origin[1],'shadow followed real owner');
 A.assert(p.x===150&&p.y===0,'lure moved owner');out.chase={origin,owner:[p.x,p.y],enemy:[e.x,e.y],redirects:D.stats(p).redirects};
 e=A.decoyStart();d=A.decoyMine()[0];p.x=150;e.x=60;e.y=80;A.decoyRanged(e);A.decoyEnemyUpdate(e);
 const shot=G.Projectiles.all().find(b=>!b.friendly);A.assert(shot&&e._shikamaruDecoyTarget===d,'native ranged AI did not shoot at lure');
 const aim=Math.atan2(shot.vy,shot.vx),desired=Math.atan2(d.y-e.y,d.x-e.x),real=Math.atan2(p.y-e.y,p.x-e.x);
 A.assert(Math.abs(Math.atan2(Math.sin(aim-desired),Math.cos(aim-desired)))<.001&&Math.abs(aim-real)>.1,'native shot aimed at player rather than shadow');
 const hp=p.hp,dhp=d.hp;A.decoyProjectiles(.55);A.assert(G.Projectiles.all().includes(shot)&&d.hp===dhp,'intangible shadow consumed projectile');A.decoyProjectiles(.85);A.assert(p.hp===hp,'redirected shot hit displaced real owner');
 A.decoyReset();p.moves=[];p.x=150;e=A.spawn(60,80);A.decoyRanged(e);const baseHP=p.hp;A.decoyEnemyUpdate(e);A.decoyProjectiles(1.4);A.assert(p.hp<baseHP,'same encounter without lure failed to threaten player');
 out.ranged={aim,realAim:real,withLureLoss:0,withoutLureLoss:baseHP-p.hp,projectilePassed:true};
 e=A.decoyStart();d=A.decoyMine()[0];p.x=d.x-30;e.x=d.x+50;e.y=d.y;A.decoyRanged(e);const behind=p.hp;A.decoyEnemyUpdate(e);A.decoyProjectiles(.8);A.assert(p.hp<behind,'shadow shielded real player standing behind it');out.noShield={loss:behind-p.hp};
 e=A.decoyStart();d=A.decoyMine()[0];p.x=150;e.x=60;e.y=80;A.decoyEnemyUpdate(e);A.assert(e._shikamaruDecoyTarget===d,'expiry fixture never redirected');A.decoyAdvance(3.1);A.decoyEnemyUpdate(e);A.assert(!A.decoyMine().length&&!e._shikamaruDecoyTarget,'expired lure retained native target');out.expiry=true;
 e=A.decoyStart();d=A.decoyMine()[0];p.x=150;e.x=80;e.y=0;const path=G.World.projectilePathClear;G.World.projectilePathClear=()=>false;try{A.decoyEnemyUpdate(e);A.assert(!e._shikamaruDecoyTarget,'lure worked through blocking path')}finally{G.World.projectilePathClear=path}out.wall=true;
 for(const kind of ['remote','thief','friendly']){e=A.decoyStart();d=A.decoyMine()[0];p.x=150;e.x=80;e.y=20;if(kind==='thief')e.behavior='thief';else e[kind]=true;A.assert(D.targetForEnemies(e,p)===p,'excluded enemy was lured '+kind)}out.exclusions=['remote','thief','friendly'];
 e=A.decoyStart();d=A.decoyMine()[0];p.x=150;const julian=G.SelfClones.summon(p),F=G.LF2Julian;julian.mon=G.DEX.find(m=>m.dex===30020);julian.x=julian.y=100;julian.moves=[G.Moves.instance('lf2-julian-mirror')];julian.moves[0].t=0;
 A.resume();try{A.assert(F.cast(julian,julian.moves[0]),'mixed-hero mirror fixture rejected');F.update(.1)}finally{A.pause()}
 const other=F.decoys().find(d=>d.owner===julian);A.assert(other,'mixed-hero mirror fixture absent');e.x=other.x+15;e.y=other.y+10;A.decoyEnemyUpdate(e);A.assert(e._lf2MirrorTarget===other&&!e._shikamaruDecoyTarget,'farther shadow replaced nearer Julian phantom');
 e.x=d.x+20;e.y=d.y+20;A.decoyEnemyUpdate(e);A.assert(e._shikamaruDecoyTarget===d&&!e._lf2MirrorTarget,'nearer shadow lost to farther Julian phantom');out.mixedPhantoms=true;
 e=A.decoyStart();e.x=p.x;e.y=p.y;e.dmg=25;e.touchCd=0;p.invuln=0;G.EnemyMgr.rebuildGrid();const contactHP=p.hp;A.resume();try{G.Combat.resolve(.01,p,0)}finally{A.pause()}A.assert(p.hp<contactHP,'stationary lure granted contact invulnerability');out.noInvulnerability=true;
 return out;
}'''

LIFECYCLE = r'''() => {
 const A=Acceptance,p=A.p(),D=G.NarutoShikamaruDecoy,out=[];
 const sample=()=>JSON.stringify({stats:D.stats(p),decoys:A.decoyMine().map(d=>({id:d.id,x:d.x,y:d.y,age:d.age,hp:d.hp})),hp:p.hp});
 A.decoyStart();const before=sample(),canvas=document.createElement('canvas');canvas.width=canvas.height=500;const ctx=canvas.getContext('2d');ctx.translate(250,300);
 for(let i=0;i<80;i++){G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx)}A.assert(sample()===before,'render advanced lure state');D.update(8);A.assert(sample()===before,'pause advanced lure state');out.push('readOnly','pause');
 for(const reason of ['clear','death','unlearn','world','epoch','terminal']){A.decoyStart();const world=G.World,game=G.Game;
  if(reason==='clear')G.Combat.clearFields(p);if(reason==='death')p.dead=true;if(reason==='unlearn')p.moves=[];if(reason==='world')G.World={...world};if(reason==='epoch')G.CombatPulse.beginRun();
  if(reason==='terminal'){G.Game={...game,state:'over'};D.update(.01)}else A.decoyStep(.01);
  A.assert(!D.decoys().length,'invalid state retained active lure '+reason);G.World=world;G.Game=game;p.dead=false;out.push(reason);
 }
 A.decoyReset();A.spawn(100,0);const clone=G.SelfClones.summon(p);A.assert(clone,'clone unavailable');clone.x=clone.y=0;A.decoyCast(p);A.decoyCast(clone);A.decoyAdvance(.1);D.clear(p);
 A.assert(!A.decoyMine(p).length&&A.decoyMine(clone).length,'owner clear crossed clone scope');clone.dead=true;A.decoyStep(.01);A.assert(!D.decoys().length,'dead clone left active lure');out.push('cloneIsolation');return out;
}'''


def native(pw, report):
    browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
    for label, width, height in [('desktop', 1100, 850), ('mobile360', 360, 780), ('mobile390', 390, 844)]:
        folder = OUT / label
        folder.mkdir(parents=True, exist_ok=True)
        context = browser.new_context(viewport={'width': width, 'height': height},
                                      is_mobile=width < 600, has_touch=width < 600,
                                      service_workers='block', record_video_dir=str(folder / 'raw'),
                                      record_video_size={'width': width, 'height': height})
        page = context.new_page()
        observe(page, report)
        saved_url = base.URL
        if width < 600:
            base.URL = base.URL.replace('&layout=wide', '')
        try:
            page.goto(base.URL)
            page.wait_for_function('window.PS_REDRAWN_READY&&window.G?.NarutoShikamaruDecoy&&document.getElementById("boot").classList.contains("hidden")')
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30017"]').click()
            cell = page.locator('.launch-kit span').filter(has_text='留影誘敵')
            cell.scroll_into_view_if_needed()
            menu = cell.evaluate('e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {text:e.innerText,title:e.title,icon:!!e.querySelector("canvas,svg,img"),visible:s.display!=="none"&&s.visibility!=="hidden",bounds:{x:r.x,y:r.y,width:r.width,height:r.height},viewport:{width:innerWidth,height:innerHeight},overflow:e.scrollWidth>e.clientWidth+1}}')
            page.screenshot(path=str(folder / 'selection-skill.png'))
            assert menu['visible'] and menu['icon'] and 'Lv.2' in menu['text'], menu
            assert menu['bounds']['x'] >= 0 and menu['bounds']['x'] + menu['bounds']['width'] <= width + 1 and menu['bounds']['y'] + menu['bounds']['height'] <= height + 1 and not menu['overflow'], menu
            report.setdefault('menu', {})[label] = menu
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30017&&G.Game.state==="playing"')
            page.evaluate(base.HARNESS)
            page.evaluate(base.SETUP)
        finally:
            base.URL = saved_url
        page.evaluate(SETUP)
        page.evaluate(r'''() => {
         const A=Acceptance,p=A.p();A.decoyReset();const e=A.spawn(80,60);e.spd=35;e.flying=true;
         A.decoyCast();window.DecoyNative={origin:{x:p.x,y:p.y},samples:[],started:performance.now()};
         const step=()=>{const d=G.NarutoShikamaruDecoy.decoys().filter(d=>d.owner===p);DecoyNative.samples.push({elapsed:(performance.now()-DecoyNative.started)/1000,owner:{x:p.x,y:p.y},decoys:d.map(d=>({id:d.id,x:d.x,y:d.y,age:d.age})),target:e._shikamaruDecoyTarget?.id||null});if(d.length&&performance.now()-DecoyNative.started<9000)requestAnimationFrame(step)};requestAnimationFrame(step);A.resume();
        }''')
        page.wait_for_timeout(200)
        overlap = page.evaluate('()=>{const p=G.Game.player,d=G.NarutoShikamaruDecoy.decoys().find(d=>d.owner===p);return {owner:{x:p.x,y:p.y},decoy:d?{x:d.x,y:d.y,age:d.age}:null}}')
        assert overlap['decoy'] and overlap['owner']['x'] == overlap['decoy']['x'] and overlap['owner']['y'] == overlap['decoy']['y'], f'{label}: standing overlap fixture missing'
        page.screenshot(path=str(folder / 'standing-overlap.png'))
        page.keyboard.down('KeyD')
        page.wait_for_timeout(550)
        page.keyboard.up('KeyD')
        page.screenshot(path=str(folder / 'stationary-shadow.png'))
        page.keyboard.down('KeyS')
        page.wait_for_timeout(350)
        page.keyboard.up('KeyS')
        page.wait_for_function('DecoyNative.samples.length>2&&!DecoyNative.samples.at(-1).decoys.length', timeout=8000)
        page.screenshot(path=str(folder / 'expired-shadow.png'))
        data = page.evaluate('({samples:DecoyNative.samples,stats:G.NarutoShikamaruDecoy.stats(G.Game.player),origin:DecoyNative.origin})')
        data['overlap'] = overlap
        active = [s for s in data['samples'] if s['decoys']]
        assert active and any(s['target'] for s in active), f'{label}: no native redirected target'
        assert any(abs(s['owner']['x'] - data['origin']['x']) > 30 for s in active), f'{label}: no keyboard separation'
        first = active[0]['decoys'][0]
        assert all(d['x'] == first['x'] and d['y'] == first['y']
                   for s in active for d in s['decoys'] if d['id'] == first['id']), f'{label}: native shadow moved'
        assert not data['samples'][-1]['decoys'], f'{label}: no native expiry'
        report['native'][label] = data
        video = page.video
        context.close()
        video.save_as(str(folder / 'stationary-shadow.webm'))
        video.delete()
    browser.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'controlled': True, 'url': base.URL,
              'policy': 'Production entry; controlled open arena and true learn/upgrade cards. Native RAF keyboard examples, not natural progression or mobile hardware.',
              'sourceBefore': manifest(), 'checks': {}, 'native': {}, 'errors': []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            page = browser.new_page(viewport={'width': 1100, 'height': 850}, service_workers='block')
            observe(page, report)
            base.boot(page)
            page.evaluate(SETUP)
            for name, check in [('progression', PROGRESSION), ('utility', UTILITY), ('lifecycle', LIFECYCLE)]:
                report['checks'][name] = page.evaluate(check)
                print(name, 'PASS', flush=True)
            browser.close()
            native(pw, report)
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report['failure'] = str(error)
        raise
    finally:
        report['sourceAfter'] = manifest()
        report['sourceStable'] = report['sourceBefore'] == report['sourceAfter']
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')


if __name__ == '__main__':
    main()
