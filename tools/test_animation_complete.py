"""Real-art browser acceptance for the complete local animation lab.

Requires the lab server on localhost:8318 and existing Playwright/Chrome.
No synthetic art, external routing, or replacement combat implementations.
Controlled arenas remove terrain only where explicitly stated; actual casts,
projectiles, actor damage, keyboard/touch input and upgrade cards are exercised.
Evidence is generated under .omx/state/animation-complete, never previews/.
"""
from pathlib import Path
import base64
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / '.omx/state/animation-complete'
BASE = 'http://127.0.0.1:8318/art-review/playtest.html'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

HARNESS = r"""() => {
  const assert=(value,message)=>{if(!value)throw Error(message)};
  const p=()=>G.Game.player;
  function pause(){if(G.Game.state==='playing')G.Game.togglePause();G.UI.hide('scr-pause')}
  function resume(){if(G.Game.state==='paused')G.Game.togglePause();assert(G.Game.state==='playing','cannot resume '+G.Game.state)}
  function arena(){
    G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();
    G.NarutoClones.clear();G.AnimationLab.clear();
    // Deliberately open arena: equal enabled/disabled outcomes below include
    // real combat collision with enemies but omit procedural map obstacles.
    G.World.collide=()=>{};G.World.isLiquid=()=>false;G.World.isFree=()=>true;
    G.World.isWall=()=>false;G.World.projectileBlock=()=>false;
    const a=p();a.x=a.y=0;a.hp=a.maxHp;a.dead=false;a.frozen=false;
    a.flash=0;a.invuln=0;a.attackFace=0;a.walking=false;a.quantityBonus=0;
    a.anim.once=false;a.anim.done=false;a.critChance=0;
    G.Camera.x=G.Camera.y=0;pause();
  }
  function enemy(angle=0,distance=85){
    const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},
      Math.cos(angle)*distance,Math.sin(angle)*distance,{hp:1,spd:1,dmg:1});
    G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();p().target=e;p().aim=angle;return e;
  }
  function step(dt=.02){
    Acceptance.resume();
    G.Combat.updateFields(dt);p().anim.update(dt);
    G.Projectiles.update(dt,p(),G.EnemyMgr.all());
    pause();
  }
  function render(anim=p().anim,opts={}){
    const canvas=document.createElement('canvas');canvas.width=240;canvas.height=200;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});let old=0,calls=0;
    const original=ctx.drawImage.bind(ctx),source=G.Naruto.records.get(anim.dex||p().dex)?.image;
    ctx.drawImage=(image,...args)=>{calls++;if(image===source)old++;return original(image,...args)};
    const sourceBefore=G.AnimationLab.counters.source,candidateBefore=G.AnimationLab.counters.candidate;
    anim.draw(ctx,120,150,opts);
    assert(G.AnimationLab.counters.source===sourceBefore,'renderer fell back to source image');
    assert(G.AnimationLab.counters.candidate===candidateBefore+1,'candidate actor draw missing');
    const data=ctx.getImageData(0,0,240,200).data;
    let x0=240,y0=200,x1=-1,y1=-1,count=0;
    for(let y=0;y<200;y++)for(let x=0;x<240;x++)if(data[(y*240+x)*4+3]>20){
      count++;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);
    }
    assert(count>80,'empty candidate '+JSON.stringify(G.AnimationLab.stateFor(anim)));
    assert(old===0,'original actor image rendered '+JSON.stringify(G.AnimationLab.stateFor(anim)));
    assert(x0>0&&x1<239&&y0>0&&y1<199,'actor clipped at evidence canvas edges');
    return {state:G.AnimationLab.stateFor(anim),bounds:[x0,y0,x1,y1],pixels:count,calls,sourceCalls:old,png:canvas.toDataURL()};
  }
  function select(id){
    const a=p(),index=a.slots.findIndex(group=>group.some(m=>m.id===id));
    assert(index>=0,'unlearned skill '+id);a.setActive(index);
    const m=a.moves.find(m=>m.id===id);m.t=0;return m;
  }
  function cast(id,angle=0){
    const m=select(id);enemy(angle);let calls=0;
    const original=p().cast;p().cast=function(...args){calls++;return original.apply(this,args)};
    try{Acceptance.resume();p().update(0);G.Combat.tick(.001,p(),0)}finally{p().cast=original;pause()}
    // Sharingan is a learned passive; it never enters automatic Combat.tick.
    if(m.passive){Acceptance.resume();G.NarutoSharingan.sync(p());G.Combat.updateFields(.001);pause()}
    else assert(calls===1,'automatic combat rejected '+id+' calls='+calls);
    return {id,entry:m.passive?'original learned passive sync':'Combat.tick',cooldown:m.t};
  }
  window.Acceptance={assert,p,pause,resume,arena,enemy,step,render,select,cast};pause();
}"""


def start(page, dex):
    page.locator(f'[data-hero="{dex}"]').click()
    page.wait_for_function(f"document.querySelector('#game').contentWindow.G.Game.player?.dex==={dex}")
    frame = next(f for f in page.frames if '/.omx/digimon.html' in f.url)
    page.locator('#training').click()
    frame.evaluate(HARNESS)
    frame.evaluate('Acceptance.arena()')
    return frame


def wait_ready(page, report):
    try:
        page.wait_for_function('GameplayLab.ready && !!document.querySelector("#game").contentWindow.G.AnimationLab')
    except Exception:
        print('BOOT FAILURE', page.locator('#status').inner_text(), report['errors'], report['failedRequests'])
        print(json.dumps(page.evaluate('''() => {const f=document.querySelector('#game'),G=f.contentWindow.G;
          return {assets:window.AnimationAssets?.keys,game:!!G?.Game,db:!!G?.DB?.save,boot:f.contentDocument.querySelector('#boot')?.className,
          body:f.contentDocument.body.innerText.slice(0,300),scripts:[...f.contentDocument.scripts].filter(s=>s.src).map(s=>s.src).slice(-8)}}'''), ensure_ascii=True))
        raise


def save_pose(name, result):
    png = result.pop('png')
    (OUT / f'{name}.png').write_bytes(base64.b64decode(png.split(',', 1)[1]))
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'common': {}, 'skills': {}, 'errors': [], 'failedRequests': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        context = browser.new_context(viewport={'width': 1200, 'height': 900}, service_workers='block')
        page = context.new_page()
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        page.on('response', lambda r: report['failedRequests'].append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
        page.goto(BASE)
        wait_ready(page, report)
        boot = page.frame_locator('#game').locator('#tap-start')
        if boot.is_visible():
            boot.click()
        assert page.locator('#candidate').is_checked(), 'fresh default mode is disabled'
        for dex, hero in [(30001, 'naruto'), (30002, 'sasuke')]:
            frame = start(page, dex)
            report['common'][hero] = common = {}
            # Keyboard events genuinely reach Input; Player.update drives movement.
            for direction, key in [('right', 'KeyD'), ('down', 'KeyS'), ('left', 'KeyA'), ('up', 'KeyW')]:
                frame.evaluate('Acceptance.arena()')
                page.locator('#game').focus()
                page.keyboard.down(key)
                result = frame.evaluate('''() => {const A=Acceptance,p=A.p(),x=p.x,y=p.y;
                  Acceptance.resume();p.update(.08);A.pause();
                  A.assert(p.walking&&Math.hypot(p.x-x,p.y-y)>0,'real keyboard did not move actor');
                  return A.render();}''')
                page.keyboard.up(key)
                assert result['state']['direction'] == direction, result
                common[f'walk-{direction}'] = save_pose(f'{hero}-walk-{direction}', result)
                result = frame.evaluate('''() => {Acceptance.resume();Acceptance.p().update(.08);Acceptance.pause();return Acceptance.render()}''')
                assert result['state']['state'] == 'idle', result
                common[f'idle-{direction}'] = save_pose(f'{hero}-idle-{direction}', result)
            # Stationary loops retain their feet; natural crouching can reduce height.
            feet = [v['bounds'][3] for k, v in common.items() if k.startswith('idle')]
            assert max(feet)-min(feet) <= 4, feet
            hurt = frame.evaluate('''() => {const A=Acceptance,p=A.p();A.arena();const hp=p.hp;
              Acceptance.resume();p.hurt(11,null,true);A.pause();A.assert(p.hp<hp&&p.flash>0,'damage/flash lost');
              return {normal:A.render(),flash:A.render(p.anim,{flash:true,softFlash:true,alpha:.5})};}''')
            assert hurt['normal']['state']['state'] == 'hurt', hurt['normal']['state']
            assert hurt['normal']['png'] != hurt['flash']['png'], 'flash/alpha has no visible effect'
            common['hurt'] = save_pose(f'{hero}-hurt', hurt['normal'])
            common['flash'] = save_pose(f'{hero}-flash', hurt['flash'])
            frame.evaluate('Acceptance.step(.5)')
            # Paused calls must not change presentation age or selected frame.
            paused = frame.evaluate('''() => {const A=Acceptance;A.pause();const before=A.render().state;
              A.p().anim.update(.4);return {before,after:A.render().state}}''')
            assert paused['before'] == paused['after'], paused
            common['pauseStable'] = True

            outcomes = []
            for enabled in [False, True]:
                page.locator('#candidate').set_checked(enabled)
                # Snapshot the same original hit and projectile systems with a
                # deterministic dt. Presentation must not alter either result.
                outcomes.append(frame.evaluate('''() => {const A=Acceptance,results={};
                  for(const id of ['naruto-kunai',G.NarutoSkillCatalog.byDex.get(A.p().dex).id]){
                    A.arena();const p=A.p(),damage=p.dmgDealt;A.cast(id);
                    const shots=G.Projectiles.all().map(s=>({x:s.x,y:s.y,vx:s.vx,vy:s.vy,dmg:s.dmg,r:s.r}));
                    for(let i=0;i<35;i++)A.step(.02);
                    results[id]={shots,damage:p.dmgDealt-damage,x:p.x,y:p.y,cooldown:p.moves.find(m=>m.id===id).t};
                  }return results}'''))
            page.locator('#candidate').check()
            assert outcomes[0] == outcomes[1], outcomes
            common['enabledDisabledCombat'] = outcomes

            ids = (['naruto-clones', 'naruto-naruto', 'naruto-rasenshuriken', 'naruto-nine-tails-cloak']
                   if dex == 30001 else ['naruto-sasuke', 'naruto-fireball', 'naruto-fuma-shuriken', 'naruto-kusanagi', 'naruto-sharingan'])
            # Catalog's primary IDs are authoritative (clone/Chidori differ by build).
            ids[0] = frame.evaluate('G.NarutoSkillCatalog.byDex.get(G.Game.player.dex).id')
            ids += ['naruto-kunai', 'naruto-shuriken']
            for skill in ids:
                phases = []
                frame.evaluate('Acceptance.arena()')
                cast = frame.evaluate('(id)=>Acceptance.cast(id)', skill)
                for age in [0, .04, .12, .26, .45, .8]:
                    if phases:
                        frame.evaluate('(dt)=>Acceptance.step(dt)', age - phases[-1]['age'])
                    pose = frame.evaluate('Acceptance.render()')
                    phases.append({'age': age, **save_pose(f'{hero}-{skill}-{age}', pose)})
                    if age in [0, .26, .45]:
                        page.screenshot(path=str(OUT / f'gameplay-{hero}-{skill}-{age}.png'))
                assert any(p['state'].get('id') == skill for p in phases), (skill, phases)
                assert all(p['state'].get('id') == skill for p in phases if p['state']['state'] == 'skill'), (skill, phases)
                report['skills'][f'{hero}:{skill}'] = {'cast': cast, 'phases': phases}
                # Original skill APIs accept target/aim in all cardinal directions.
                # Side-view skill boards mirror left/right; vertical direction is
                # still tested without claiming newly authored back-view artwork.
                if skill != 'naruto-sharingan':
                    aims = []
                    for angle in [0, 1.5707963267948966, 3.141592653589793, -1.5707963267948966]:
                        frame.evaluate('Acceptance.arena()')
                        frame.evaluate('([id,a])=>Acceptance.cast(id,a)', [skill, angle])
                        aimed = frame.evaluate('Acceptance.render()')
                        aimed.pop('png')
                        aims.append(aimed)
                    report['skills'][f'{hero}:{skill}']['cardinalAims'] = aims
                if dex == 30001 and skill == ids[0]:
                    # The aim matrix leaves the last cast at windup; complete its
                    # genuine summon delay before inspecting clone actors.
                    frame.evaluate('Acceptance.step(.5)')
                    clones = frame.evaluate('''() => {const A=Acceptance,actors=G.NarutoClones.actors;
                      A.assert(actors.length>0,'accepted clone cast created no actors');
                      return actors.map(a=>({id:a.id,ttl:a.ttl,pose:A.render(a.anim)}))}''')
                    for i, clone in enumerate(clones):
                        clone['pose'] = save_pose(f'clone-{i}', clone['pose'])
                    report['clones'] = clones
                    frame.evaluate('Acceptance.resume();G.NarutoClones.update(30);Acceptance.pause();Acceptance.assert(!G.NarutoClones.actors.length,"clones did not expire")')
            if dex == 30001:
                common['cloakExpiry'] = frame.evaluate('''() => {
                  const A=Acceptance;A.arena();A.cast('naruto-nine-tails-cloak');A.step(.02);
                  A.assert(G.NarutoSupport.effects.some(f=>f.mode==='nine-tails-cloak'),'cloak buff never activated');
                  const duration=A.p().moves.find(m=>m.id==='naruto-nine-tails-cloak').fieldDuration;
                  A.step(duration+.1);A.assert(!G.NarutoSupport.effects.some(f=>f.mode==='nine-tails-cloak'),'cloak buff survived expiry');
                  return {duration,expired:true};}''')
            else:
                common['switchCleanup'] = frame.evaluate('''() => {
                  const A=Acceptance;A.arena();A.cast('naruto-fuma-shuriken');A.step(.1);A.select('naruto-kunai');A.step(.15);
                  A.assert(!G.Projectiles.all().length,'switch before Fuma release spawned a projectile');
                  A.assert(A.render().state.id!=='naruto-fuma-shuriken','cancelled Fuma pose persisted');
                  A.arena();A.cast('naruto-fuma-shuriken');A.step(.21);const shot=G.Projectiles.all()[0];
                  A.assert(shot,'Fuma failed to release');A.select('naruto-kunai');A.step(.01);
                  A.assert(G.Projectiles.all().includes(shot),'switch removed already released Fuma');
                  A.arena();A.cast('naruto-kusanagi');A.step(.01);
                  A.assert(G.NarutoKusanagi.active(A.p()),'Kusanagi failed to equip');A.select('naruto-kunai');
                  A.assert(!G.NarutoKusanagi.active(A.p()),'Kusanagi survived switch away');
                  return {fumaCancel:true,releasedFumaRetained:true,kusanagiRemoved:true};}''')
                tiers = []
                for level in range(1, 6):
                    pose = frame.evaluate('''(level) => {const A=Acceptance;A.arena();
                      A.p().moves.find(m=>m.id==='naruto-sharingan').lvl=level;
                      A.resume();G.NarutoSharingan.sync(A.p());G.Combat.updateFields(.001);A.pause();
                      A.assert(G.NarutoSharingan.stage(A.p())===level,'Sharingan tier mismatch');return A.render();}''', level)
                    tiers.append(pose['png'])
                    common[f'sharingan-tier-{level}'] = save_pose(f'sharingan-tier-{level}', pose)
                assert len(set(tiers)) == 5, 'Sharingan tier presentation not distinguishable'
                frame.evaluate('G.Game.player.moves.find(m=>m.id==="naruto-sharingan").lvl=1;G.NarutoSharingan.sync()')
            # Actual lethal damage initiates Faint; presentation holds final pose.
            death = frame.evaluate('''() => {const A=Acceptance;A.arena();const p=A.p();Acceptance.resume();
              p.hurt(p.maxHp*10,null,true);A.pause();A.assert(p.dead,'lethal hit did not kill');
              const first=A.render();A.step(2);const end=A.render();A.step(1);const hold=A.render();return {first,end,hold};}''')
            assert death['end']['state']['state'] == 'death', death['end']['state']
            assert death['end']['png'] == death['hold']['png'], 'death final frame not held'
            common['death'] = {k: save_pose(f'{hero}-death-{k}', v) for k, v in death.items()}
            page.screenshot(path=str(OUT / f'{hero}-desktop.png'))

        # Restart must clear dead actors, clones and stale candidate action state.
        frame = start(page, 30001)
        report['restart'] = frame.evaluate('''() => ({dead:G.Game.player.dead,clones:G.NarutoClones.actors.length,state:Acceptance.render().state})''')
        assert not report['restart']['dead'] and report['restart']['clones'] == 0
        frame.evaluate('Acceptance.resume();G.Game.player.invuln=99999')
        report['desktopLevelups'] = levelups(page, frame)
        page.screenshot(path=str(OUT / 'desktop-controls.png'))
        mobile = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, service_workers='block')
        phone = mobile.new_page()
        phone.on('pageerror', lambda e: report['errors'].append(str(e)))
        phone.goto(BASE)
        wait_ready(phone, report)
        boot = phone.frame_locator('#game').locator('#tap-start')
        if boot.is_visible():
            boot.tap()
        frame = start(phone, 30002)
        frame.evaluate('Acceptance.resume();G.Game.player.invuln=99999')
        report['mobileLevelups'] = levelups(phone, frame)
        bounds = phone.locator('#game').bounding_box()
        assert bounds['y'] + bounds['height'] <= 844.5, bounds
        # CDP generates genuine touch input through the iframe canvas listeners.
        frame.evaluate('Acceptance.arena();Acceptance.resume();G.Game.player.invuln=99999')
        initial = frame.evaluate('({x:G.Game.player.x,y:G.Game.player.y})')
        cdp = mobile.new_cdp_session(phone)
        x, y = bounds['x'] + 85, bounds['y'] + bounds['height'] * .6
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x+48, 'y': y}]})
        phone.wait_for_timeout(140)
        moved = frame.evaluate('({x:G.Game.player.x,y:G.Game.player.y,walking:G.Game.player.walking})')
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        assert moved['walking'] and moved['x'] > initial['x'], (initial, moved)
        report['mobileTouch'] = {'before': initial, 'after': moved}
        phone.screenshot(path=str(OUT / 'mobile-controls.png'))
        assert not report['errors'], report['errors']
        assert not report['failedRequests'], report['failedRequests']
        browser.close()
    (OUT / 'browser-acceptance.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    contact_sheets(report)
    print(json.dumps({'passed': True, 'heroes': len(report['common']), 'skillRows': len(report['skills']), 'evidence': str(OUT)}, ensure_ascii=False))


def levelups(page, frame):
    game = page.frame_locator('#game')
    for _ in range(2):
        button = game.locator('#dev-level-up')
        button.wait_for(state='visible')
        before = frame.evaluate('G.Game.player.level')
        button.click()
        game.locator('#scr-levelup').wait_for(state='visible')
        assert frame.evaluate('G.Game.player.level') == before + 1
        game.locator('#cards .card').first.click()
    return 2


def contact_sheets(report):
    from PIL import Image, ImageDraw
    width, height = 210, 165
    sheet = Image.new('RGB', (width*6, (height+30)*len(report['skills'])), '#132037')
    draw = ImageDraw.Draw(sheet)
    for row, (key, item) in enumerate(report['skills'].items()):
        hero, skill = key.split(':')
        draw.text((5, row*(height+30)+3), key, fill='white')
        for col, pose in enumerate(item['phases']):
            image = Image.open(OUT / f'{hero}-{skill}-{pose["age"]}.png').convert('RGBA')
            image.thumbnail((width, height))
            px, py = col*width, row*(height+30)+23
            sheet.paste(image, (px, py), image)
            draw.text((px+5, py+height-18), f'{pose["age"]:.2f}s {pose["state"]["phase"]}', fill='white')
    sheet.save(OUT / 'runtime-contact.png')
    samples = []
    for hero, poses in report['common'].items():
        for name in ['idle-down', 'walk-right', 'hurt', 'flash']:
            samples.append((f'{hero}-{name}', OUT / f'{hero}-{name}.png'))
        samples.append((f'{hero}-death', OUT / f'{hero}-death-end.png'))
    samples.append(('actual clone actor', OUT / 'clone-0.png'))
    sheet = Image.new('RGB', (240*4, 225*((len(samples)+3)//4)), '#132037')
    draw = ImageDraw.Draw(sheet)
    for i, (label, path) in enumerate(samples):
        image = Image.open(path).convert('RGBA')
        x,y=(i%4)*240,(i//4)*225
        sheet.paste(image,(x,y+20),image);draw.text((x+5,y+4),label,fill='white')
    sheet.save(OUT / 'common-contact.png')


if __name__ == '__main__':
    main()
