"""Native desktop/mobile acceptance for uncapped, visible-area Universal Pull."""
import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-gravity-all'

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out={};
 const d=e=>Math.hypot(e.x-p.x,e.y-p.y);
 const start=()=>{A.ready('gravity');A.advance(.001);const f=A.actions().find(f=>f.kind==='gravity');A.assert(f,'no native gravity action');return f};
 A.reset();const group=[A.spawn(200,0),A.spawn(-200,0),A.spawn(0,200),A.spawn(0,-200),A.spawn(240,0)],far=A.spawn(241,0);
 const hits=A.watch(group),initial=group.map(d),f=start();A.finish(.15);
 A.assert(f.pulls.length===5,'pull snapshot must contain all five in-range targets');
 A.assert(group.every((e,i)=>d(e)<initial[i])&&d(far)===241,'all in-range targets must move; outside must stay');
 A.assert(!hits.filter(h=>h.id==='naruto-pain-gravity').length,'pull must precede damage');out.dispersed={initial,mid:group.map(d),outside:d(far)};
 A.finish(.21);const pushHits=hits.filter(h=>h.id==='naruto-pain-gravity');A.assert(pushHits.length===5&&pushHits.every(h=>h.owned),'single owned push per target '+JSON.stringify(hits));
 const m=p.moves.find(m=>m.id==='naruto-pain-gravity');A.assert(m.cd===3&&m.t>2.6&&m.t<3,'three-second cooldown changed '+m.t);
 A.finish(.5);A.assert(hits.filter(h=>h.id==='naruto-pain-gravity').length===5,'duplicate push damage');out.hits=hits;
 A.reset();const many=Array.from({length:32},(_,i)=>A.spawn(Math.cos(i*Math.PI/16)*220,Math.sin(i*Math.PI/16)*220)),mf=start();A.finish(.30);
 A.assert(mf.pulls.length===32&&many.every(e=>d(e)<220),'uncapped crowd not pulled');
 A.assert(mf.pulls.every(e=>e.distance<=110+1e-6),'per-target pull exceeded 110');out.crowd={count:mf.pulls.length,distances:mf.pulls.map(e=>e.distance)};
 A.reset();const regular=A.spawn(230,0),boss=A.spawn(-230,0,true);start();A.finish(.15);
 const normalMove=230-d(regular),bossMove=230-d(boss);A.assert(Math.abs(normalMove/4-bossMove)<1e-5,'boss displacement must be quarter speed');out.boss={normalMove,bossMove};
 A.reset();const ground=A.spawn(210,0),fly=A.spawn(-210,0),jump=A.spawn(0,210);fly.flying=true;jump.jumpLift=18;jump.jumpT=.8;start();A.finish(.15);
 A.assert(d(ground)<210&&d(fly)===210&&d(jump)===210&&jump.jumpLift===18&&jump.jumpT===.8,'airborne state moved or mutated');out.grounded=true;
 A.reset();const blocked=A.spawn(200,0),open=A.spawn(-200,0),W=G.World,old=W.projectileBlock;
 W.projectileBlock=(x,y)=>x>90&&x<120?{destructible:false}:false;
 try{start();A.finish(.15);A.assert(d(blocked)===200&&d(open)<200,'line-of-sight pull failed')}finally{W.projectileBlock=old}out.wall=true;
 A.reset();const exit=A.spawn(210,0),hidden=A.spawn(0,210),ongoing=A.spawn(-210,0);start();A.finish(.08);
 exit.x=241;const beforeHidden={x:hidden.x,y:hidden.y},beforeOngoing=d(ongoing),blocker=W.projectileBlock;
 W.projectileBlock=(x,y)=>y>80?{destructible:false}:false;
 try{A.finish(.08);A.assert(exit.x===241&&hidden.x===beforeHidden.x&&hidden.y===beforeHidden.y&&d(ongoing)<beforeOngoing,'per-target range/LOS revalidation failed')}finally{W.projectileBlock=blocker}out.midPullRevalidation=true;
 A.reset();const dying=A.spawn(210,0),survivor=A.spawn(-210,0);start();dying.dead=true;A.finish(.15);
 A.assert(d(dying)===210&&d(survivor)<210,'one dead target cancelled surviving target');out.deathIsolation=true;
 A.reset();const cap=A.spawn(240,0),cf=start();A.finish(.348);A.assert(cf.pulls[0].distance<=110+1e-6&&cf.pulls[0].distance>109,'110 cap changed');out.cap=cf.pulls[0].distance;
 A.reset();A.spawn(200,0);const paused=start(),age=paused.age,t=m.t;G.Combat.tick(.5,p,0);G.Combat.updateFields(.5);
 A.assert(paused.age===age&&m.t===t,'paused pull advanced');out.pause=true;
 A.reset();const close=A.spawn(70,0),other=A.spawn(-120,0),emergency=A.watch([close,other]);A.ready('gravity');A.advance(.01);
 A.assert(A.actions().some(f=>f.kind==='gravity'&&f.immediate&&f.phase==='push'),'emergency must skip pull');A.advance(.001);
 const gravityHits=emergency.filter(h=>h.id==='naruto-pain-gravity');A.assert(gravityHits.length===2&&gravityHits.every(h=>h.owned),'emergency push delayed '+JSON.stringify({emergency,actions:A.actions().map(f=>({kind:f.kind,age:f.age,phase:f.phase,immediate:f.immediate})),snapshot:P.snapshot(p)}));out.emergency=true;
 out.cleanup=[];
 for(const reason of ['clear','world','owner-death']){
   A.reset();A.spawn(200,0);start();const world=G.World;
   if(reason==='clear')G.Combat.clearFields();else if(reason==='world')G.World={...world};else p.dead=true;
   try{A.resume();G.Combat.updateFields(.01);A.pause();A.assert(!P.actionsFor(p).length,'pull leaked '+reason)}finally{G.World=world;p.dead=false}
   out.cleanup.push(reason);
 }
 A.reset();return out;
}"""

SCENE = r"""() => {
 const A=Acceptance;A.reset();for(const a of [0,.8,1.7,2.6,3.5,4.4,5.3])A.spawn(Math.cos(a)*210,Math.sin(a)*210);
 A.ready('gravity');A.finish(.16);
}"""

RENDER = r"""() => {
 const canvas=document.createElement('canvas');canvas.width=720;canvas.height=600;
 const ctx=canvas.getContext('2d');ctx.fillStyle='#23323d';ctx.fillRect(0,0,720,600);ctx.translate(360,300);ctx.imageSmoothingEnabled=false;
 G.Combat.drawGroundFields(ctx);
 const entities=[Acceptance.p(),...G.EnemyMgr.all(),...G.NarutoPain.actors()];entities.sort((a,b)=>a.y-b.y).forEach(e=>e.draw(ctx));
 G.Combat.drawAirFields(ctx);G.FX.draw(ctx);return canvas.toDataURL();
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, viewport, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
            outer = context.new_page()
            outer.on('pageerror', lambda error: report['errors'].append(str(error)))
            outer.goto(URL)
            frame = game_frame(outer)
            enter(frame)
            report['viewports'][label] = frame.evaluate(CHECK)
            frame.evaluate(SCENE)
            frame.evaluate(RENDER)  # Request the actual sprite assets before recording evidence.
            outer.wait_for_timeout(300)
            for phase in ['pull', 'push']:
                if phase == 'push':
                    frame.evaluate('Acceptance.finish(.20)')
                png = frame.evaluate(RENDER).split(',', 1)[1]
                (OUT / f'{label}-{phase}-combat.png').write_bytes(base64.b64decode(png))
                outer.screenshot(path=str(OUT / f'{label}-{phase}-game.png'), animations='disabled')
            print(label, 'all-target gravity PASS', flush=True)
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Native all-target gravity PASS', flush=True)


if __name__ == '__main__':
    main()
