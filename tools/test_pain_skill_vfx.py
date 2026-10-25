"""Per-skill native VFX acceptance and animated previews for the eight-agent delivery."""
import base64
import io
import json
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-skill-vfx'
SKILLS = ['basic', 'gravity', 'missiles', 'summon', 'soul', 'absorb', 'repair', 'planet']
SETUP = r"""(key) => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;
 if(!window.vfxMoves)window.vfxMoves=p.moves.slice();p.moves=vfxMoves.slice();A.reset();G.Hazards.clear();
 const id=key==='basic'?'naruto-pain':'naruto-pain-'+key;p.moves=p.moves.filter(m=>m.id===id);
 window.vfxEnemies=[];const spawn=(x,y,boss=false)=>{const e=A.spawn(x,y,boss);vfxEnemies.push(e);return e};
 const body=k=>P.actorsFor(p).find(b=>b.path===k);
 if(key==='basic')spawn(190,0);
 if(key==='gravity')spawn(220,0);
 if(key==='missiles'){body('asura').x=-60;body('asura').y=0;spawn(180,0);spawn(180,45)}
 if(key==='summon'){body('animal').x=-80;body('animal').y=0;spawn(180,0);spawn(180,30)}
 if(key==='soul'){body('human').x=-90;body('human').y=0;spawn(80,0)}
 if(key==='absorb'){
  P.actorsFor(p).forEach((b,i)=>{b.x=-150-i*25;b.y=-200});const b=body('preta');b.x=60;b.y=0;
  for(const [x,y]of [[85,0],[80,12],[40,-8]])G.Projectiles.spawn({friendly:false,x,y,px:x,py:y,r:3,dmg:7,painAbsorbable:true});
 }
 if(key==='repair'){
  const b=body('asura');b.x=70;b.y=0;b.hurt(b.maxHp+1,null,true);A.finish(9.95);
 }
 if(key==='planet')spawn(0,0,true).flying=true;
 if(!['basic','absorb','repair'].includes(key))A.ready(key);A.advance();
 window.vfxCounts={};window.vfxArt={};window.vfxOriginals=[];
 for(const [name,renderer]of Object.entries(G.PainSkillVFX))for(const [method,draw]of Object.entries(renderer)){
  vfxOriginals.push([renderer,method,draw]);renderer[method]=function(...args){const k=name+':'+method;vfxCounts[k]=(vfxCounts[k]||0)+1;return draw.apply(this,args)};
 }
 const draw=G.PainArt.draw;vfxOriginals.push([G.PainArt,'draw',draw]);G.PainArt.draw=function(ctx,opts,...args){vfxArt[opts.path]=(vfxArt[opts.path]||0)+1;return draw.call(this,ctx,opts,...args)};
}"""
CAPTURE = r"""(key) => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;
 const fingerprint=()=>JSON.stringify({state:P.snapshot(p),shots:P.shots.map(s=>[s.x,s.y,s.age,s.lift,s.phase]),effects:P.effects.map(e=>[e.kind,e.age]),hp:p.hp,damage:p.dmgDealt,moves:p.moves.map(m=>[m.id,m.t,m.dealt])});
 const before=fingerprint();
 function canvas(){const c=document.createElement('canvas');c.width=c.height=760;const ctx=c.getContext('2d');ctx.fillStyle='#253c28';ctx.fillRect(0,0,760,760);ctx.translate(380,400);ctx.scale(.7,.7);ctx.imageSmoothingEnabled=false;return [c,ctx]}
 function draw(){const [c,ctx]=canvas();G.Combat.drawGroundFields(ctx);for(const e of vfxEnemies)e.draw(ctx);p.draw(ctx);for(const b of P.actorsFor(p))b.draw(ctx);G.Combat.drawAirFields(ctx);return c}
 const first=draw(),again=draw();A.assert(first.toDataURL()===again.toDataURL(),'nondeterministic rendering '+key);
 A.assert(before===fingerprint(),'render mutated battle state '+key);
 return first.toDataURL();
}"""
MISSILES = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,moves=vfxMoves;p.moves=moves.slice();A.reset();p.moves=p.moves.filter(m=>m.id==='naruto-pain-missiles');
 const b=P.actors().find(b=>b.path==='asura');b.x=b.y=0;const e=A.spawn(180,0);A.ready('missiles');A.advance();A.finish(.13);
 const shot=P.shots.find(s=>s.kind==='missile');A.assert(shot?.phase==='rise','missile failed upward launch');
 const x=shot.x,y=shot.y,lift=shot.lift;A.finish(.06);
 A.assert(shot.x===x&&shot.y===y&&shot.lift>lift&&e.hp===100000,'rising missile moved on ground or hit early');
 const age=shot.age;G.Combat.updateFields(.3);A.assert(shot.age===age,'pause advanced missile');
 while(shot.phase==='rise')A.advance();A.assert(shot.phase==='orbit'&&shot.lift===shot.cruiseHeight&&shot.cruiseHeight>=48&&shot.cruiseHeight<=132&&!shot.target&&e.hp===100000,'missile did not enter unlocked horizontal orbit');
 e.dead=true;e.hp=0;G.EnemyMgr.rebuildGrid();const replacement=A.spawn(180,35);A.finish(.3);
 A.assert(shot.phase==='orbit'&&!shot.target&&replacement.hp===100000,'orbit selected or hit replacement before completion');
 while(shot.phase==='orbit')A.advance();A.finish(.03);
 A.assert(shot.phase==='seek'&&shot.target===replacement&&shot.distance>0&&shot.lift>0,'missile did not seek fresh replacement after orbit');
 A.finish(1.2);A.assert(replacement.hp<100000,'descending missile caused no actual damage');
 p.moves=moves.slice();A.reset();p.moves=p.moves.filter(m=>m.id==='naruto-pain-missiles');
 const asura=P.actors().find(b=>b.path==='asura');asura.x=asura.y=0;A.spawn(180,0);A.ready('missiles');A.advance();A.finish(1.05);
 const missile=P.shots.find(s=>s.kind==='missile'&&s.phase==='seek');A.assert(missile,'seeking fixture absent');
 const original=missile.target;original.dead=true;original.hp=0;G.EnemyMgr.rebuildGrid();const next=A.spawn(200,10);A.advance();
 A.assert(missile.target===next,'in-flight missile did not reacquire');
 G.Combat.clearFields();A.assert(!P.shots.length&&!P.effects.length,'scene cleanup retained new shots/effects');
 p.moves=moves.slice();A.reset();return {riseBeforeOrbit:true,orbitBeforeSeek:true,noEarlyHit:true,pause:true,reacquireAfterOrbit:true,reacquireInFlight:true,cleanup:true};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'errors': [], 'failedRequests': [], 'viewports': {}}
    durations = {'basic': 1, 'gravity': 1, 'missiles': 3.4, 'summon': 1, 'soul': .9, 'absorb': .65, 'repair': 1.4, 'planet': 2.2}
    captures = {'basic': .1, 'gravity': .16, 'missiles': .55, 'summon': .4, 'soul': .3, 'absorb': .1, 'repair': .45, 'planet': 1.3}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, viewport in [('desktop', {'width': 1200, 'height': 900}), ('mobile', {'width': 390, 'height': 844})]:
            page = browser.new_page(viewport=viewport, is_mobile=label == 'mobile', has_touch=label == 'mobile', service_workers='block')
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.on('response', lambda r: report['failedRequests'].append(r.url) if r.status >= 400 and '127.0.0.1' in r.url else None)
            page.goto(URL)
            frame = game_frame(page)
            enter(frame)
            assert sorted(frame.evaluate('Object.keys(G.PainSkillVFX)')) == sorted(SKILLS)
            results = report['viewports'][label] = {}
            for key in SKILLS:
                print(label, key, flush=True)
                frame.evaluate(SETUP, key)
                images = []
                snapped = False
                for i in range(round(durations[key] * 20)):
                    data = frame.evaluate(CAPTURE, key)
                    raw = base64.b64decode(data.split(',', 1)[1])
                    if label == 'desktop':
                        images.append(Image.open(io.BytesIO(raw)).convert('RGB'))
                    if not snapped and i / 20 >= captures[key]:
                        (OUT / f'{label}-{key}.png').write_bytes(raw)
                        page.screenshot(path=str(OUT / f'{label}-{key}-game.png'))
                        snapped = True
                    frame.evaluate('Acceptance.advance(.05)')
                result = frame.evaluate('''() => {for(const [obj,key,fn]of vfxOriginals)obj[key]=fn;return {hooks:vfxCounts,art:vfxArt,intercepted:G.NarutoPain.snapshot(Acceptance.p()).intercepted,revives:G.NarutoPain.snapshot(Acceptance.p()).revives}}''')
                assert any(k.startswith(key + ':') and n > 0 for k, n in result['hooks'].items()), key
                if key == 'summon':
                    assert result['art'].get('rhino', 0) > 0
                if key == 'repair':
                    assert result['art'].get('king', 0) > 0 and result['revives'] > 0
                if key == 'absorb':
                    assert result['intercepted'] == 3
                if images:
                    images[0].save(OUT / f'{key}.gif', save_all=True, append_images=images[1:], duration=50, loop=0, disposal=2)
                results[key] = result
            results['missileTrajectory'] = frame.evaluate(MISSILES)
            page.close()
        browser.close()
    assert not report['errors'], report['errors']
    assert not report['failedRequests'], report['failedRequests']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
