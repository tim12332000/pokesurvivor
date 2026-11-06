"""Native Canvas regression for event-owned Temari cyclone tail cuts.

The render fixtures use the production VFX entry point and immutable contact
snapshots. They do not run combat or claim natural-growth validation.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_temari as native
import test_temari_typhoon as typhoon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/temari-tail-vfx'

CHECK = r"""() => {
 const T=G.TemariCycloneVFX,canvas=document.createElement('canvas');
 canvas.width=700;canvas.height=520;
 const ctx=canvas.getContext('2d',{willReadFrequently:true});
 const enemy={x:100,y:30,hp:100,r:8},mark={x:100,y:30,age:1.6,angle:.3};
 const contact={started:.4,cuts:3,lastHit:mark};
 const storm={x:0,y:0,age:1.64,aim:0,angle:Math.PI*2,sweepDuration:1.2,lifetime:2.4,
   cast:{radius:240,kind:'typhoon',ghost:false},contacts:new Map([[enemy,contact]]),propContacts:new Map()};
 const save=()=>JSON.stringify({storm:{...storm,contacts:[...storm.contacts],propContacts:[...storm.propContacts]},enemy});
 const capture=(storms=[storm])=>{
   ctx.clearRect(0,0,700,520);ctx.save();ctx.translate(350,260);
   const before=save();T.drawAir(ctx,{storms});ctx.restore();
   if(before!==save())throw Error('tail render mutated contact, actor or clock');
   const rgba=ctx.getImageData(0,0,700,520).data;let pixels=0,x0=700,y0=520,x1=-1,y1=-1;
   for(let y=0;y<520;y++)for(let x=0;x<700;x++)if(rgba[(y*700+x)*4+3]>8){pixels++;x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y)}
   return {pixels,bounds:[x0,y0,x1,y1],png:canvas.toDataURL()};
 };
 const out={tail:capture()};
 enemy.x=250;enemy.y=-140;out.moved=capture();
 if(out.tail.png!==out.moved.png)throw Error('old tail mark followed the moving target');
 storm.age=1.75;out.expired=capture();storm.age=1.64;
 delete contact.lastHit;out.noHit=capture();contact.lastHit=mark;
 storm.cast.ghost=true;out.ghostWithoutVisual=capture();
 contact.visualHit={...mark,visualOnly:true};out.ghost=capture();
 delete contact.visualHit;storm.cast.ghost=false;
 out.coincident=capture(Array.from({length:120},()=>({...storm})));
 storm.age=.5;out.sweep=capture();storm.age=1.64;
 out.renderPure=true;return out;
}"""

NATIVE_SETUP = r"""({quantity,quality}) => {
 const A=Acceptance,p=A.p();A.tyLearn();A.reset();A.mastery(0);A.rank(A.ty,1);p.level=12;
 G.Settings.set('quality',quality);p.quantityPicks=p.quantityBonus=quantity;
 p.moves=p.moves.filter(m=>m.id===A.ty);p.xpNext=1e12;
 const positions=[[100,0],[-115,0],[105,-35],[500,0]],enemies=positions.map(([x,y])=>A.spawn(x,y,'elite'));
 window.TailEvidence={hits:[],stages:[],expectedHits:9*Math.floor(1.25**quantity)};
 for(const [index,e] of enemies.entries()){
   e.r=4;e.hp=e.maxHp=1e9;const hurt=e.hurt;
   e.hurt=function(...args){const result=hurt.apply(this,args);
     TailEvidence.hits.push({index,clock:G.Game.st.time,x:this.x,y:this.y,damage:args[0]});return result;};
 }
 G.EnemyMgr.rebuildGrid();p.target=enemies[0];A.castNative(A.ty);p.frozen=true;
 TailEvidence.cast=G.NarutoTemari.stateFor(p).latest;
 TailEvidence.seek=stage=>{
   TailEvidence.reached=false;
   const watch=()=>{
     const storms=G.NarutoTemari.storms,first=storms[0],marks=storms.flatMap(a=>[...a.contacts.values()].map(c=>c.lastHit).filter(Boolean));
     const age=first?.age||0;
     const ready=stage==='first'?age>=.2:stage==='middle'?age>=.8:stage==='late'?marks.some(m=>m.age>=1.3&&age-m.age<.04):
       stage==='last'?TailEvidence.hits.length===TailEvidence.expectedHits&&marks.some(m=>m.age>=2.1&&age-m.age<.04):!storms.length;
     if(ready){
       A.pause();TailEvidence.reached=true;
       TailEvidence.stages.push({stage,age,hits:TailEvidence.hits.length,marks,casts:TailEvidence.cast.cuts});
     }else requestAnimationFrame(watch);
   };
   A.resume();requestAnimationFrame(watch);
 };
 return {quantity,quality,rank:1,mastery:0,level:p.level,expectedStreams:Math.floor(1.25**quantity)};
}"""


def capture_native(browser):
    report = {'scope': 'Normal entry then explicitly controlled Lv12/rank1 cyclone arena. Native RAF clock; phase pauses capture existing state, no manual field advancement.',
              'sources': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
                          ['.omx/naruto-temari.js', '.omx/temari-cyclone-vfx.js']}, 'cases': {}}
    cases = [('desktop', 1200, 900, False, 0, 'high'), ('mobile390', 390, 844, True, 0, 'high'),
             ('mobile360-low-q5', 360, 800, True, 5, 'low')]
    for name, width, height, mobile, quantity, quality in cases:
        folder = OUT / name
        folder.mkdir(exist_ok=True)
        context = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=mobile,
                                      has_touch=mobile, service_workers='block', record_video_dir=str(folder / 'video'))
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        url = native.URL + ('&layout=wide' if not mobile else '')
        page.goto(url)
        page.wait_for_function("window.PS_REDRAWN_READY && window.G?.NarutoTemari && document.getElementById('boot').classList.contains('hidden')", polling=20)
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.locator('[data-quick-naruto="30011"]').click()
        page.wait_for_function('G.NarutoAssets.ready(30011)', polling=20)
        page.screenshot(path=str(folder / 'normal-selection.png'))
        page.locator('#scr-menu [data-go="play"]').click()
        page.wait_for_function('G.Game.player?.dex===30011 && G.Game.state==="playing"', polling=20)
        initial = page.evaluate('({level:G.Game.player.level,dex:G.Game.player.dex})')
        assert initial['level'] == 1, initial
        page.screenshot(path=str(folder / 'normal-lv1.png'))
        page.evaluate(native.HARNESS)
        page.evaluate(native.SETUP)
        page.evaluate(typhoon.SETUP)
        fixture = page.evaluate(NATIVE_SETUP, {'quantity': quantity, 'quality': quality})
        for stage in ['first', 'middle', 'late', 'last', 'recovery']:
            page.evaluate('TailEvidence.seek', stage)
            page.wait_for_function('TailEvidence.reached', polling=10)
            page.wait_for_timeout(100)
            page.screenshot(path=str(folder / f'{stage}.png'))
            layer = page.evaluate('''() => {
              const c=document.createElement('canvas');c.width=700;c.height=520;
              const ctx=c.getContext('2d');ctx.translate(350,260);
              G.Combat.drawAirFields(ctx);return c.toDataURL();
            }''')
            (folder / f'{stage}-air.png').write_bytes(base64.b64decode(layer.split(',', 1)[1]))
        result = page.evaluate('({hits:TailEvidence.hits,stages:TailEvidence.stages,cuts:TailEvidence.cast.cuts,streams:TailEvidence.cast.count})')
        assert not any(hit['index'] == 3 for hit in result['hits']), 'out-of-range target received a cut'
        assert len(result['hits']) == 9 * fixture['expectedStreams'], result
        assert not errors, errors
        report['cases'][name] = {'initial': initial, 'fixture': fixture, **result, 'errors': errors}
        video = page.video
        context.close()
        video.save_as(str(folder / 'native-phases.webm'))
        print(name, 'native first/middle/late/last/recovery pass', flush=True)
    (OUT / 'native-report.json').write_text(json.dumps(report, indent=2), encoding='utf8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, help='Optional saved production VFX source for baseline proof')
    parser.add_argument('--label', default='candidate')
    parser.add_argument('--native', action='store_true', help='Also record normal entry and controlled native phase windows in three viewports')
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
        page.close()
        if args.native:
            capture_native(browser)
        browser.close()
    for key, value in report.items():
        if isinstance(value, dict) and 'png' in value:
            (OUT / f'{args.label}-{key}.png').write_bytes(base64.b64decode(value.pop('png').split(',', 1)[1]))
    (OUT / f'{args.label}.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    assert report['tail']['pixels'] > 20, 'real tail cut has no visible mark after the sweep'
    assert report['tail'] == report['moved'], 'fixed hit-position snapshot changed after target movement'
    assert report['expired']['pixels'] == report['noHit']['pixels'] == report['ghostWithoutVisual']['pixels'] == 0
    assert report['ghost']['pixels'] > 20, 'explicit ghost visual contact is missing'
    assert report['coincident']['pixels'] == report['tail']['pixels'], 'coincident quantity visuals stacked'
    assert report['sweep']['pixels'] > report['tail']['pixels'], 'large first sweep was lost'
    print(json.dumps({'ok': True, 'renderPure': report['renderPure'], 'tailPixels': report['tail']['pixels'], 'out': str(OUT)}))


if __name__ == '__main__':
    main()
