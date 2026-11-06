"""Temari wind-chain rendering follows immutable knot/front/contact state."""
import argparse
import base64
import hashlib
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_temari as native
import test_temari_typhoon as typhoon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/temari-wind-chain-vfx'

CHECK = r"""() => {
 const api=G.TemariCycloneVFX,c=document.createElement('canvas');c.width=700;c.height=520;
 const ctx=c.getContext('2d',{willReadFrequently:true}),owner={id:'player'};
 const knot={seedId:1,sourceCastId:1,owner,x:60,y:20,age:1,ttl:6,r:10,created:0,ghost:false,consumed:false};
 const burst={id:1,activationId:1,owner,x:40,y:0,age:.04,radius:160,cuts:3,interval:.1,travel:.08,fade:.12,
   fronts:[{index:0,started:0,reach:80,done:false,hits:new Set(),props:new Set()}],lastHits:[],ghost:false,cast:{}};
 const snapshot=()=>JSON.stringify({knot,burst},(k,v)=>v instanceof Set?[...v]:v);
 const draw=(windKnots=[],windBursts=[])=>{
   ctx.clearRect(0,0,700,520);ctx.save();ctx.translate(350,260);
   const before=snapshot();api.drawGround(ctx,{windKnots});api.drawAir(ctx,{windKnots,windBursts});ctx.restore();
   if(before!==snapshot())throw Error('wind-chain render mutated simulation');
   const rgba=ctx.getImageData(0,0,700,520).data;let pixels=0,alphaSum=0,opaqueCenter=0,maxRadius=0;
   for(let y=0;y<520;y++)for(let x=0;x<700;x++){
     const alpha=rgba[(y*700+x)*4+3];if(alpha<=8)continue;pixels++;alphaSum+=alpha;
     const d=Math.hypot(x-(350+burst.x),y-(260+burst.y-(G.LIFT||0)));
     maxRadius=Math.max(maxRadius,d);if(d<30&&alpha>220)opaqueCenter++;
   }
   return {pixels,alphaSum,opaqueCenter,maxRadius,png:c.toDataURL()};
 };
 const out={knot:draw([knot]),front:draw([],[burst])};
 knot.ghost=true;out.ghostKnot=draw([knot]);knot.ghost=false;
 knot.consumed=true;out.consumed=draw([knot]);knot.consumed=false;
 knot.age=6.1;out.expiredKnot=draw([knot]);knot.age=1;
 burst.age=.25;burst.fronts[0].done=true;burst.fronts[0].reach=160;out.expiredFront=draw([],[burst]);
 burst.age=.04;burst.fronts[0].done=false;burst.fronts[0].reach=80;
 out.coincident=draw([],Array.from({length:120},()=>({...burst})));
 burst.fronts=[];burst.age=.2;burst.lastHits=[{x:100,y:30,age:.18,angle:.3,pulse:1}];
 out.hit=draw([],[burst]);const mark=burst.lastHits[0];
 burst.target={x:300,y:300};out.fixedHit=draw([],[burst]);
 burst.ghost=true;out.unidentifiedGhost=draw([],[burst]);mark.visualOnly=true;out.ghostHit=draw([],[burst]);
 out.renderPure=true;return out;
}"""

SMOKE = r"""high => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;
 A.reset();A.learn();A.mastery(1);A.rank('naruto-temari',1);A.rank('naruto-temari-great-scythe',1);p.level=6;
 p.moves=p.moves.filter(m=>['temari-wind','temari-mastery','temari-great-scythe'].includes(m.digiMode));
 for(const m of p.moves)m.t=999;
 const es=[A.spawn(100,0),A.spawn(170,20)],hits=es.map(A.watch);es.forEach(e=>e.hp=e.maxHp=1e9);
 p.target=es[0];G.EnemyMgr.rebuildGrid();
 for(let i=0;i<500&&T.windKnots.length<2;i++){
   A.resume();try{G.Combat.tick(.01,p,i*.01)}finally{A.pause()}A.advance(.01);
 }
 A.assert(T.windKnots.length===2,'real empowered basic failed to create two knots');
 if(high){A.mastery(5);A.rank('naruto-temari-great-scythe',5);p.quantityPicks=p.quantityBonus=20;}
 const move=p.moves.find(m=>m.digiMode==='temari-great-scythe');p.setActive(p.slots.findIndex(g=>g.includes(move)));move.t=0;
 A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()}
 p.frozen=true;
 for(let i=0;i<200&&!T.windBursts.some(a=>a.fronts.some(f=>f.reach>=a.radius*.4&&!f.done));i++)A.advance(.005);
 const burst=T.windBursts.find(a=>a.fronts.some(f=>f.reach>=a.radius*.4&&!f.done));
 A.assert(burst,'actual heavy front failed to activate a growing burst');
 const c=document.createElement('canvas');c.width=1200;c.height=1000;
 const ctx=c.getContext('2d',{willReadFrequently:true});ctx.translate(600,500);
 const state=()=>JSON.stringify({knots:T.windKnots.map(a=>({x:a.x,y:a.y,age:a.age,consumed:a.consumed})),
   bursts:T.windBursts.map(a=>({x:a.x,y:a.y,age:a.age,radius:a.radius,fronts:a.fronts.map(f=>({reach:f.reach,done:f.done})),hits:a.lastHits})),hp:es.map(e=>e.hp)});
 const before=state();
 G.TemariCycloneVFX.drawGround(ctx,{windKnots:T.windKnots});
 G.TemariCycloneVFX.drawAir(ctx,{windKnots:T.windKnots,windBursts:T.windBursts});
 A.assert(before===state(),'actual wind-chain layer render mutated combat');
 const pixels=ctx.getImageData(0,0,1200,1000).data;let visible=0,centerOpaque=0;
 for(let y=0;y<1000;y++)for(let x=0;x<1200;x++)if(pixels[(y*1200+x)*4+3]>8){
   visible++;if(Math.hypot(x-600-burst.x,y-500-burst.y+(G.LIFT||0))<30&&pixels[(y*1200+x)*4+3]>220)centerOpaque++;
 }
 return {radius:burst.radius,cuts:burst.cuts,fronts:burst.fronts.map(f=>({index:f.index,reach:f.reach,done:f.done})),
   visible,centerOpaque,renderPure:true,knots:T.windKnots.length,bursts:T.windBursts.length,png:c.toDataURL()};
}"""

NATIVE_SETUP = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;
 A.tyLearn();A.reset();A.mastery(1);A.rank('naruto-temari',1);A.rank('naruto-temari-great-scythe',1);p.level=12;
 p.moves=p.moves.filter(m=>['temari-wind','temari-mastery','temari-great-scythe','temari-typhoon'].includes(m.digiMode));
 p.setActive(p.slots.findIndex(g=>g.some(m=>m.digiMode==='temari-typhoon')));
 for(const m of p.moves)m.t=999;
 const es=[A.spawn(100,0),A.spawn(170,20)];
 const basic=p.moves.find(m=>m.digiMode==='temari-wind');
 const base=basic.dmg*p.atk*G.Types.mult('flying',es[0].types)*G.Weather.mult('flying');
 // Declared controlled HP: survive two six-hit rounds, fall to the empowered
 // third round. The real successful hit leaves a clearly visible corpse knot.
 es.forEach(e=>{e.hp=e.maxHp=base*12.5;e.r=4});
 p.target=es[0];p.xpNext=1e12;G.EnemyMgr.rebuildGrid();
 const R=window.WindArt={stages:[],hits:[],activations:[],retired:[],tracked:[],expectedKnots:2,burst:null};
 const oldHit=T.onWindChainHit,oldChain=T.onWindChain;
 T.onWindChainHit=event=>{
   if(event.owner===p&&!event.ghost&&!event.visualOnly)R.hits.push({burstId:event.burstId,pulse:event.pulse,
     time:G.Game.st.time,x:event.x,y:event.y,damage:event.damage,hpDamage:event.hpDamage});
   oldHit?.(event);
 };
 T.onWindChain=(owner,packet)=>{
   if(owner===p&&packet.removed)R.retired.push({seedThrough:packet.seedThrough,activationThrough:packet.activationThrough});
   else if(owner===p){
     R.activations.push(...packet.bursts.map(a=>({id:a.id,cuts:a.cuts,radius:a.radius})));
     R.tracked.push(...packet.bursts.map(a=>T.windBursts.find(b=>b.owner===p&&b.id===a.id)));
   }
   oldChain?.(owner,packet);
 };
 R.seek=(stage,index=0)=>{
   R.reached=false;
   const watch=()=>{
     const knots=T.windKnots.filter(a=>a.owner===p),bursts=T.windBursts.filter(a=>a.owner===p);
     const windup=T.casts.some(a=>a.owner===p&&a.kind==='heavy'&&a.age<a.release);
     if(!R.burst&&bursts.length)R.burst=bursts[0];
     const front=R.burst?.fronts.find(f=>f.index===index);
     const allFinal=R.activations.length===R.expectedKnots&&R.activations.every(a=>R.hits.some(h=>h.burstId===a.id&&h.pulse===a.cuts-1));
     const terminal=R.tracked.length===R.expectedKnots&&R.tracked.every(a=>a.fronts.some(f=>f.index===a.cuts-1&&f.done));
     const fading=terminal&&R.tracked.every(a=>a.age>=(a.cuts-1)*a.interval+a.travel+a.fade*.4);
     const ready=stage==='knots'?knots.length===R.expectedKnots:
       stage==='idle'?knots.length===R.expectedKnots&&knots.every(a=>a.age>=.7):stage==='windup'?windup:
       stage==='cross'?!!R.burst&&R.burst.fronts.some(f=>f.index===0&&f.reach>0):
       stage==='pulse'?!!front&&front.reach>0&&!front.done:
       stage==='last'?allFinal&&terminal:stage==='terminal'?terminal:stage==='fade'?fading:
       !bursts.length&&R.activations.length===R.expectedKnots;
     if(stage==='last'&&!bursts.length&&R.activations.length===R.expectedKnots&&!ready){
       R.failure={stage,allFinal,terminal,hp:p.hp,dead:p.dead,retired:R.retired,hits:R.hits,
         targets:(R.targets||[]).map(e=>({x:e.x,y:e.y,hp:e.hp,dead:e.dead})),
         tracked:R.tracked.map(a=>({id:a.id,age:a.age,cuts:a.cuts,dead:a.dead,
           fronts:a.fronts.map(f=>({index:f.index,reach:f.reach,done:f.done}))}))};
       A.pause();R.reached=true;return;
     }
     if(ready){
       A.pause();R.reached=true;
       R.stages.push({stage,index,time:G.Game.st.time,hits:R.hits.length,
         knots:knots.map(a=>({id:a.seedId,x:a.x,y:a.y,age:a.age})),
         bursts:bursts.map(a=>({id:a.id,x:a.x,y:a.y,age:a.age,radius:a.radius,cuts:a.cuts,
           fronts:a.fronts.map(f=>({index:f.index,reach:f.reach,done:f.done})),lastHits:a.lastHits}))});
     }else requestAnimationFrame(watch);
   };
   A.resume();requestAnimationFrame(watch);
 };
 return {heavySlot:p.slots.findIndex(g=>g.some(m=>m.digiMode==='temari-great-scythe'))};
}"""


def capture_native(browser, only=None):
    report = {'scope': 'Normal Lv1 entry, then controlled Lv12 ordinary targets with calibrated third-round corpse HP and fresh high-HP receivers. Real basic seeding, native manual heavy selection and native RAF; phase pauses only. High fixture uses declared direct profile setup, not natural growth.',
              'sources': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
                          ['.omx/naruto-temari.js', '.omx/temari-cyclone-vfx.js', '.omx/jujutsu-growth.js',
                           '.omx/naruto-skills.js', '.omx/naruto-skills-en.js', '.omx/temari-coop.js',
                           'js/net/coop.js', 'art-review/temari-art.js']}, 'cases': {}}
    cases = [('desktop-q0', 1200, 900, False, 0, False), ('mobile390-q1', 390, 844, True, 1, False),
             ('mobile360-low-high', 360, 800, True, 20, True)]
    for name, width, height, mobile, quantity, high in cases:
        if only and only != name:
            continue
        folder = OUT / name
        folder.mkdir(exist_ok=True)
        context = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=mobile,
                                      has_touch=mobile, service_workers='block', record_video_dir=str(folder / 'video'))
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(native.URL + ('&layout=wide' if not mobile else ''))
        page.wait_for_function("window.PS_REDRAWN_READY && window.G?.NarutoTemari && document.getElementById('boot').classList.contains('hidden')", polling=20)
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.locator('[data-quick-naruto="30011"]').click()
        page.wait_for_function('G.NarutoAssets.ready(30011)', polling=20)
        page.screenshot(path=str(folder / 'normal-selection.png'))
        page.locator('#scr-menu [data-go="play"]').click()
        page.wait_for_function('G.Game.player?.dex===30011 && G.Game.state==="playing"', polling=20)
        assert page.evaluate('G.Game.player.level') == 1
        page.screenshot(path=str(folder / 'normal-lv1.png'))
        page.evaluate(native.HARNESS)
        page.evaluate(native.SETUP)
        page.evaluate(typhoon.SETUP)
        cards = None
        if width == 390:
            heavy_index = page.evaluate('''() => {
              const p=Acceptance.p();p.level=3;
              G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-temari-three-stars').apply(p);
              p.level=6;const cards=G.LevelUp.offer(p,3);
              G.RunUI.showLevelUp(6,cards,c=>c.apply(p));
              return cards.findIndex(c=>c.key==='new:naruto-temari-great-scythe');
            }''')
            assert heavy_index >= 0
            heavy_card = page.locator('#cards .card').nth(heavy_index)
            heavy_card.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            page.screenshot(path=str(folder / 'heavy-first-learn-card.png'))
            cards = {'heavy': heavy_card.locator('.ds').evaluate('''el=>({text:el.textContent,
              clientHeight:el.clientHeight,scrollHeight:el.scrollHeight,overflow:getComputedStyle(el).overflowY,
              rect:{left:el.getBoundingClientRect().left,right:el.getBoundingClientRect().right}})''')}
            heavy_card.click()
            quantity_index = page.evaluate('''() => {
              const p=Acceptance.p();let cards,index;
              for(let i=0;i<100;i++){cards=G.LevelUp.offer(p,3);index=cards.findIndex(c=>c.key==='stat:quantity');if(index>=0)break;}
              G.RunUI.showLevelUp(p.level,cards,c=>c.apply(p));return index;
            }''')
            assert quantity_index >= 0
            quantity_card = page.locator('#cards .card').nth(quantity_index)
            quantity_card.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            page.screenshot(path=str(folder / 'quantity-preview-card.png'))
            cards['quantity'] = quantity_card.locator('.ds').evaluate('''el=>({text:el.textContent,
              clientHeight:el.clientHeight,scrollHeight:el.scrollHeight,overflow:getComputedStyle(el).overflowY,
              rect:{left:el.getBoundingClientRect().left,right:el.getBoundingClientRect().right}})''')
            page.evaluate('G.RunUI.closeLevelUp()')
        setup = page.evaluate(NATIVE_SETUP)

        def capture(stage, index=0):
            page.evaluate('([stage,index])=>WindArt.seek(stage,index)', [stage, index])
            page.wait_for_function('WindArt.reached', polling=10)
            failure = page.evaluate('WindArt.failure||null')
            if failure:
                (folder / 'failure.json').write_text(json.dumps(failure, indent=2), encoding='utf8')
                raise AssertionError(failure)
            page.wait_for_timeout(70)
            suffix = f'{stage}-{index}' if stage == 'pulse' else stage
            page.screenshot(path=str(folder / f'{suffix}.png'))
            layer = page.evaluate('''() => {
              const c=document.createElement('canvas');c.width=1200;c.height=1000;
              const ctx=c.getContext('2d');ctx.translate(600,500);
              const T=G.NarutoTemari;
              G.TemariCycloneVFX.drawGround(ctx,{windKnots:T.windKnots});
              G.TemariCycloneVFX.drawAir(ctx,{windKnots:T.windKnots,windBursts:T.windBursts});
              return c.toDataURL();
            }''')
            (folder / f'{suffix}-chain.png').write_bytes(base64.b64decode(layer.split(',', 1)[1]))

        capture('knots')
        capture('idle')
        page.evaluate('''() => {
          const A=Acceptance,p=A.p();const targets=[A.spawn(130,0),A.spawn(200,20)];
          targets.forEach(e=>{e.hp=e.maxHp=1e9;e.r=4});WindArt.targets=targets;
          p.target=targets[0];G.EnemyMgr.rebuildGrid();
        }''')
        profile = page.evaluate('''({quantity,high}) => {
          const A=Acceptance,p=A.p();p.quantityPicks=p.quantityBonus=quantity;
          if(high){A.mastery(5);A.rank('naruto-temari-great-scythe',5);p.level=40;}
          G.Settings.set('quality',high?'low':'high');return G.NarutoTemari.windChainProfile(p);
        }''', {'quantity': quantity, 'high': high})
        page.evaluate('Acceptance.resume()')
        if mobile:
            rect = page.evaluate('''index=>{
              const p=G.Game.player,n=p.slots.length+p.moves.filter(m=>m.passive&&!p.slots.some(g=>g.includes(m))).length;
              return G.Touch.controlLayout(innerWidth,innerHeight,n).slots[index];
            }''', setup['heavySlot'])
            page.touchscreen.tap(rect['x'] + rect['w'] / 2, rect['y'] + rect['h'] / 2)
        else:
            page.keyboard.press(f'Digit{setup["heavySlot"] + 1}')
        page.wait_for_function('(index)=>G.Game.player.active===index', arg=setup['heavySlot'], polling=20)
        capture('windup')
        page.evaluate('G.Game.player.frozen=true')
        capture('cross')
        for index in range(1, profile['cuts']):
            capture('pulse', index)
        capture('last')
        capture('terminal')
        capture('fade')
        capture('recovery')
        result = page.evaluate('({stages:WindArt.stages,hits:WindArt.hits,activations:WindArt.activations,retired:WindArt.retired})')
        assert all(any(hit['burstId'] == a['id'] and hit['pulse'] == pulse and hit['hpDamage'] > 0 for hit in result['hits'])
                   for a in result['activations'] for pulse in range(a['cuts'])), result
        assert not errors, errors
        report['cases'][name] = {'quantity': quantity, 'high': high, 'profile': profile, 'cards': cards, **result, 'errors': errors}
        report_name = 'native-report.json' if not only else f'native-report-{only}.json'
        (OUT / report_name).write_text(json.dumps(report, indent=2), encoding='utf8')
        video = page.video
        context.close()
        video.save_as(str(folder / 'native-chain.webm'))
        print(name, 'native seed/cross/everypulse/finalhit/recovery pass', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path)
    parser.add_argument('--label', default='candidate')
    parser.add_argument('--smoke', action='store_true', help='Probe actual empowered-basic to heavy activation at early and high profiles')
    parser.add_argument('--native', action='store_true', help='Capture actual native seeding/manual selection/every pulse in three viewports')
    parser.add_argument('--native-case', choices=['desktop-q0', 'mobile390-q1', 'mobile360-low-high'])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
        page = browser.new_page(viewport={'width': 1200, 'height': 900})
        if args.source:
            source = args.source.read_text(encoding='utf8')
            page.route('**/.omx/temari-cyclone-vfx.js*', lambda route: route.fulfill(body=source, content_type='text/javascript'))
        native.boot(page)
        report = page.evaluate(CHECK)
        if args.smoke:
            smoke = {}
            for name, high in [('early', False), ('high', True)]:
                result = page.evaluate(SMOKE, high)
                (OUT / f'smoke-{name}.png').write_bytes(base64.b64decode(result.pop('png').split(',', 1)[1]))
                assert result['visible'] > 100 and result['centerOpaque'] < 20, result
                smoke[name] = result
            (OUT / 'smoke.json').write_text(json.dumps(smoke, indent=2), encoding='utf8')
        page.close()
        if args.native:
            capture_native(browser, args.native_case)
        browser.close()
    for name, value in report.items():
        if isinstance(value, dict) and 'png' in value:
            (OUT / f'{args.label}-{name}.png').write_bytes(base64.b64decode(value.pop('png').split(',', 1)[1]))
    (OUT / f'{args.label}.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    assert report['knot']['pixels'] > 40, 'charged knot is not visible'
    assert 0 < report['ghostKnot']['alphaSum'] < report['knot']['alphaSum'], 'ally knot is visually indistinct from the local resource'
    assert report['front']['pixels'] > 100, 'real burst front is not visible'
    assert report['front']['maxRadius'] <= 88, 'visual front exceeds actual reach'
    assert report['front']['opaqueCenter'] < 20, 'burst fills the player route with opaque light'
    assert report['consumed']['pixels'] == report['expiredKnot']['pixels'] == report['expiredFront']['pixels'] == 0
    assert report['coincident'] == report['front'], 'coincident burst decoration stacks'
    assert report['hit'] == report['fixedHit'], 'immutable hit mark follows another object'
    assert report['hit']['pixels'] > 20 and report['ghostHit']['pixels'] > 20
    assert report['unidentifiedGhost']['pixels'] == 0
    print(json.dumps({'ok': True, 'knotPixels': report['knot']['pixels'], 'frontPixels': report['front']['pixels'], 'renderPure': True}))


if __name__ == '__main__':
    main()
