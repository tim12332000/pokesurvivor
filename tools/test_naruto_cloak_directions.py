"""Verify genuine front/back cloak frames through normal desktop/mobile entries.

Movement uses real keyboard/touch input. Pose captures use the actual Animator
renderer in a controlled open arena, with no replacement artwork or renderer.
"""
import base64
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME

ROOT = Path(__file__).resolve().parents[1]
LIVE = os.environ.get('CLOAK_LIVE') == '1'
OUT = ROOT / ('.omx/state/naruto-cloak-release/public-directions' if LIVE else 'art-review/naruto-cloak-directions-20261116')
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&layout=wide'

HARNESS = r"""() => {
 const p=G.Game.player,S=G.NarutoSupport,F=G.KyuubiForm;
 const assert=(v,m)=>{if(!v)throw Error(m)};
 G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();G.FX.clear();
 Object.assign(G.World,{isFree:()=>true,isWall:()=>false,isLiquid:()=>false,collide:()=>{},projectileBlock:()=>false});
 p.x=p.y=0;p.level=9;p.invuln=0;p.critChance=0;p.target=null;p.aim=0;
 for(const m of p.moves)m.t=999;
 const enemy=(x,y)=>{const e=new G.Enemy({dex:19,hp:1e7,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
   G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;};
 enemy(250,0);assert(S.cast(p,G.Moves.instance('naruto-nine-tails-cloak',1)),'cloak activation failed');
 G.EnemyMgr.clear();
 G.NarutoClones.cast(p,G.Moves.instance('naruto-shadow-clones',1));
 G.Game.togglePause();S.update(1);p.anim.update(1);G.Game.togglePause();G.UI.hide('scr-pause');
 const clone=G.NarutoClones.actors[0];
 assert(clone&&F.active(clone),'shadow did not inherit cloak');
 const dirs={down:0,right:2,up:4,left:6};
 function rest(a,dir){a.target=null;a.walking=false;a.comboT=0;a.mimickedId=null;
   a.anim.once=false;a.anim.done=false;a.anim.base='Idle';a.anim.cur='Idle';a.anim.dir=dirs[dir];}
 function render(a){
   const pose=F.poseFor(a.anim);assert(pose,'missing form pose');
   const canvas=document.createElement('canvas');canvas.width=220;canvas.height=160;
   const ctx=canvas.getContext('2d',{willReadFrequently:true}),calls=[],draw=ctx.drawImage.bind(ctx);
   ctx.drawImage=(img,...args)=>{calls.push({source:img.dataset?.source||img.src||'',rect:args.slice(0,4)});return draw(img,...args)};
   a.anim.draw(ctx,110,125);
   const expected=['up','down'].includes(pose.direction)?'one-tail-vertical-v1.png':'one-tail-v2.png';
   assert(calls.length&&calls.every(c=>c.source.includes(expected)),'wrong actual source: '+JSON.stringify({pose,calls}));
   assert(calls.every(c=>JSON.stringify(c.rect)===JSON.stringify(pose.rect)),'draw rectangle differs from selected pose');
   if(['up','down'].includes(pose.direction))assert(pose.mirror===false,'vertical pose was mirrored');
   const pixels=ctx.getImageData(0,0,220,160).data;let x0=220,y0=160,x1=-1,y1=-1;
   for(let y=0;y<160;y++)for(let x=0;x<220;x++)if(pixels[(y*220+x)*4+3]>20){x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}
   assert(x1-x0>20&&y1-y0>25,'empty or undersized body');
   assert(x0>0&&y0>0&&x1<219&&y1<159,'body clipped');
   return {pose,calls,bounds:[x0,y0,x1,y1],image:canvas.toDataURL()};
 }
 function betweenPulses(){G.Game.togglePause();
   for(let n=0;n<40;n++){const f=S.effects.find(f=>f.owner===p&&f.mode==='nine-tails-cloak');
     if(!f.pulseFlash&&f.tick<.3)break;S.update(.02)}G.Game.togglePause();G.UI.hide('scr-pause');}
 window.DirectionCheck={p,clone,assert,rest,render,enemy,betweenPulses,
  move(){betweenPulses();const before={x:p.x,y:p.y};G.Game.togglePause();p.update(.08);G.Game.togglePause();G.UI.hide('scr-pause');
    assert(p.walking&&Math.hypot(p.x-before.x,p.y-before.y)>0,'real input did not move actor');return {before,after:{x:p.x,y:p.y},render:render(p)};},
  punch(dir){G.EnemyMgr.clear();rest(clone,dir);clone.x=clone.y=0;clone.cd=0;
    const e=enemy(0,dir==='up'?-25:25),hp=e.hp;G.NarutoClones.update(.01);
    assert(e.hp<hp,'basic shadow punch did not hit');const result=render(clone);
    assert(result.pose.animation==='attack'&&result.pose.direction===dir,'punch changed facing');return result;},
  pulse(dir){rest(p,dir);S.update(.65);const result=render(p);
    assert(result.pose.animation==='attack'&&result.pose.direction===dir,'pulse changed facing');return result;},
  dispatch(dir){rest(p,dir);const original=G.AnimationLab.stateFor,results={};
    // Controlled action fixtures exercise the production pose selector and real
    // draw source; actual movement, punches and counter pulses are checked separately.
    const cases=[['hurt',{state:'hurt'}],['throw',{state:'skill',id:'naruto-kunai',phase:'release'}],
      ['activation',{state:'skill',id:'naruto-shadow-clones',phase:'seal'}],
      ['rasenganCharge',{state:'skill',id:'naruto-naruto',phase:'charge',frame:0}],
      ['rasenganDash',{state:'skill',id:'naruto-naruto',phase:'strike',frame:2}],
      ['rasenganRecover',{state:'skill',id:'naruto-naruto',phase:'recovery',frame:3}]];
    try{for(const [name,action] of cases){
      G.AnimationLab.stateFor=anim=>anim===p.anim?{...original(anim),...action,direction:dir,age:.1}:original(anim);
      const result=render(p);assert(result.pose.animation===name,'wrong action dispatch '+name);results[name]=result;
    }}finally{G.AnimationLab.stateFor=original}return results;},
  startRasengan(dir){
    G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();G.FX.clear();rest(p,dir);
    p.x=p.y=0;p.aim=dir==='up'?-Math.PI/2:Math.PI/2;
    p.target=enemy(0,dir==='up'?-65:65);
    assert(S.cast(p,G.Moves.instance('naruto-nine-tails-cloak',1)),'live Rasengan cloak failed');
    G.Game.togglePause();S.update(1);p.anim.update(1);G.Game.togglePause();G.UI.hide('scr-pause');
    if(!p.hasMove('naruto-naruto'))assert(p.addMove('naruto-naruto'),'Rasengan learning failed');
    for(const m of p.moves)m.t=999;
    const move=p.moves.find(m=>m.id==='naruto-naruto');
    assert(G.DigimonSkills.cast(p,move),'native Rasengan cast failed');
    assert(G.DigimonSkills.rasenganFor(p)?.phase==='charge','native field absent');
    G.Camera.x=G.Camera.y=0;
  },
  rasenganStep(dt,expectedPhase){
    G.Game.togglePause();G.Combat.updateFields(dt);p.anim.update(dt);G.Game.togglePause();G.UI.hide('scr-pause');
    const field=G.DigimonSkills.rasenganFor(p),pose=F.poseFor(p.anim),ordinary=G.AnimationLab.stateFor(p.anim);
    assert(field&&field.phase===expectedPhase,'live field phase differs: '+field?.phase);
    const point=G.NarutoRasenganVFX.point(p.anim,ordinary,p.x,p.y);
    const canvas=document.createElement('canvas');canvas.width=220;canvas.height=160;
    const ctx=canvas.getContext('2d'),effects=[],drawVFX=G.VFX.draw;
    let expected=null;
    if(pose.orb){const [x,y,r]=pose.orb,k=55/pose.bodyHeight*(p.anim.scale||1);
      expected={x:p.x+(x-pose.anchor[0])*k,y:p.y+(y-pose.anchor[1])*k,r:r*k};
      assert(point&&Math.abs(point.x-expected.x)<1e-6&&Math.abs(point.y-expected.y)<1e-6&&Math.abs(point.r-expected.r)<1e-6,'live orb anchor differs from actual frame');
    }else assert(point===null,'occluded back-facing orb leaked a side-hand anchor');
    G.VFX.draw=(context,name,pal,x,y,options)=>{effects.push({name,x,y});return drawVFX(context,name,pal,x,y,options)};
    try{G.NarutoRasenganVFX.drawOrb(ctx,p.anim,ordinary,p.x,p.y)}finally{G.VFX.draw=drawVFX}
    if(point)assert(effects.length===2&&effects.every(e=>Math.abs(e.x-point.x)<1e-6&&Math.abs(e.y-point.y)<1e-6),'VFX did not use measured vertical orb center');
    else assert(effects.length===0,'hidden orb drew side-facing VFX');
    let airCalls=0;const fill=ctx.fillRect.bind(ctx);ctx.fillRect=(...args)=>{airCalls++;return fill(...args)};
    G.NarutoRasenganVFX.drawAir(ctx,field);
    assert(point?airCalls>0:airCalls===0,'live air effects disagree with vertical visibility');
    return {phase:field.phase,phaseAge:field.phaseAge,point,expected,effects,airCalls,render:render(p)};
  }
 };
 G.Camera.x=G.Camera.y=0;
 return {verticalSource:F.metadata.directional?.source,clones:G.NarutoClones.actors.length};
}"""


def save(name, capture):
    (OUT / f'{name}.png').write_bytes(base64.b64decode(capture.pop('image').split(',', 1)[1]))
    return capture


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reports = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for width in (1100, 390):
            context = browser.new_context(viewport={'width': width, 'height': 850},
                                          is_mobile=width < 500, has_touch=width < 500,
                                          service_workers='block')

            def route(request):
                file = ROOT / unquote(urlsplit(request.request.url).path).removeprefix('/pokesurvivor/')
                request.fulfill(status=200 if file.is_file() else 404,
                                body=file.read_bytes() if file.is_file() else b'Not found',
                                content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')

            if not LIVE:
                context.route('https://tim12332000.github.io/pokesurvivor/**', route)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(URL.replace('digimon.html', 'portrait.html').replace('layout=wide', 'layout=portrait') if width < 500 else URL)
            view = page
            if width < 500:
                page.wait_for_selector('#portrait-game')
                view = page.locator('#portrait-game').element_handle().content_frame()
            view.wait_for_function('window.PS_REDRAWN_READY && document.getElementById("boot").classList.contains("hidden")')
            if view.locator('#tap-start').is_visible():
                view.locator('#tap-start').click()
            view.evaluate("""async()=>{await PS_REDRAWN_READY;G.Naruto.choose(30001);await G.Flow.play();
              if(G.Game.state==='playing')G.Game.togglePause();G.UI.hideAll();
              document.querySelectorAll('.toast,#ach-pop').forEach(e=>e.style.display='none');}""")
            report = {'setup': view.evaluate(HARNESS), 'poses': {}, 'movement': {}}
            for direction, key in [('up', 'KeyW'), ('down', 'KeyS'), ('left', 'KeyA'), ('right', 'KeyD')]:
                for actor in ('p', 'clone'):
                    capture = view.evaluate("""([actor,dir])=>{const A=DirectionCheck;A.betweenPulses();A.rest(A[actor],dir);return A.render(A[actor]);}""", [actor, direction])
                    assert capture['pose']['direction'] == direction, capture
                    assert capture['pose']['animation'] == 'idle', capture
                    report['poses'][f'{actor}-{direction}'] = save(f'{width}-{actor}-{direction}-idle', capture)
                if width < 500:
                    before = view.evaluate('''()=>{const A=DirectionCheck;A.betweenPulses();const p=A.p;
                      const before={x:p.x,y:p.y};G.Game.togglePause();return before;}''')
                    bounds = page.locator('#portrait-game').bounding_box()
                    x, y = bounds['x'] + 80, bounds['y'] + bounds['height'] * .65
                    dx, dy = {'up': (0, -45), 'down': (0, 45), 'left': (-45, 0), 'right': (45, 0)}[direction]
                    cdp = context.new_cdp_session(page)
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x + dx, 'y': y + dy}]})
                    page.wait_for_timeout(90)
                    moved = view.evaluate('''()=>{G.Game.togglePause();G.UI.hide('scr-pause');const A=DirectionCheck,p=A.p;
                      A.assert(p.walking,'real touch input did not move actor');return {after:{x:p.x,y:p.y},render:A.render(p)};}''')
                    moved['before'] = before
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                    cdp.detach()
                else:
                    page.keyboard.down(key)
                    moved = view.evaluate('DirectionCheck.move()')
                    page.keyboard.up(key)
                assert moved['render']['pose']['direction'] == direction, moved
                assert moved['render']['pose']['animation'] == 'run', moved
                moved['render'] = save(f'{width}-{direction}-run', moved['render'])
                report['movement'][direction] = moved
                page.wait_for_timeout(60)
                page.screenshot(path=str(OUT / f'{width}-{direction}-gameplay.png'))
            for direction in ('up', 'down'):
                report['poses'][f'clone-{direction}-punch'] = save(f'{width}-{direction}-punch', view.evaluate('(dir)=>DirectionCheck.punch(dir)', direction))
                report['poses'][f'p-{direction}-pulse'] = save(f'{width}-{direction}-pulse', view.evaluate('(dir)=>DirectionCheck.pulse(dir)', direction))
                actions = view.evaluate('(dir)=>DirectionCheck.dispatch(dir)', direction)
                report['poses'][f'p-{direction}-dispatch'] = {
                    name: save(f'{width}-{direction}-{name}', capture) for name, capture in actions.items()
                }
            report['liveRasengan'] = {}
            for direction in ('up', 'down'):
                view.evaluate('(dir)=>DirectionCheck.startRasengan(dir)', direction)
                phases = {}
                for name, dt, phase in [('charge-early', .1, 'charge'), ('charge-late', .25, 'charge'), ('strike', .27, 'strike')]:
                    capture = view.evaluate('([dt,phase])=>DirectionCheck.rasenganStep(dt,phase)', [dt, phase])
                    assert capture['render']['pose']['direction'] == direction, capture
                    capture['render'] = save(f'{width}-{direction}-live-rasengan-{name}', capture['render'])
                    phases[name] = capture
                    page.wait_for_timeout(60)
                    page.screenshot(path=str(OUT / f'{width}-{direction}-live-rasengan-{name}-gameplay.png'))
                report['liveRasengan'][direction] = phases
            report['expiry'] = view.evaluate("""()=>{G.NarutoSupport.update(20);const A=DirectionCheck;
              A.assert(!G.KyuubiForm.poseFor(A.p.anim)&&!G.KyuubiForm.poseFor(A.clone.anim),'form survived expiry');return true;}""")
            assert not errors, errors
            report['errors'] = errors
            reports[str(width)] = report
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    print('PASS: front/back sources, keyboard/touch, shadow punches/pulses, live Rasengan fields/anchors, expiry, desktop/mobile')


if __name__ == '__main__':
    main()
