"""Native desktop/mobile acceptance for uncapped, visible-area Universal Pull."""
import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-gravity-all'

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,moves=p.moves,out={};
 p.moves=moves.filter(m=>m.id==='naruto-pain-gravity');const m=p.moves[0];
 const start=()=>{A.ready('gravity');A.advance();const f=A.actions().find(f=>f.kind==='gravity');A.assert(f?.immediate&&f.phase==='push','600 trigger must directly push');return f};
 const hitsOnly=h=>h.filter(v=>v.id===m.id);
 try {
  A.assert(m.range===600&&m.triggerRadius===600&&m.radius===300&&m.cd===3,'gravity configuration');
  out.boundaries=[];
  for(const radius of [299,300,301,599,600,601]) {
   A.reset();const e=A.spawn(radius,0),hits=A.watch([e]);A.ready('gravity');A.advance();
   const action=A.actions().find(f=>f.kind==='gravity');
   A.assert(!!action===(radius<=600),'600 trigger boundary '+radius);
   if(action)A.assert(action.immediate&&action.phase==='push','trigger pulled instead of pushing');
   A.advance();const n=hitsOnly(hits).length;
   A.assert(n===(radius<=300?1:0),'300 damage boundary '+radius);
   A.assert(Math.abs(e.x-(radius+(radius<=300?80:0)))<1e-6,'300 push boundary '+radius);
   A.assert(radius<=600?m.t>2.9:m.t===0,'cooldown boundary '+radius);
   out.boundaries.push({radius,triggered:!!action,hits:n,x:e.x});
  }
  A.reset();const crowd=Array.from({length:32},(_,i)=>A.spawn(Math.cos(i*Math.PI/16)*280,Math.sin(i*Math.PI/16)*280)),outside=A.spawn(301,0),hs=A.watch([...crowd,outside]);
  start();A.advance();A.assert(hitsOnly(hs).length===32&&hitsOnly(hs).every(v=>v.owned),'uncapped owned group hit');
  A.assert(crowd.every(e=>Math.abs(Math.hypot(e.x,e.y)-360)<1e-6)&&outside.x===301,'uncapped group displacement');
  A.finish(.8);A.assert(hitsOnly(hs).length===32,'duplicate gravity damage');out.crowd=32;
  A.reset();const regular=A.spawn(200,0),boss=A.spawn(-200,0,true),fly=A.spawn(0,200),jump=A.spawn(0,-200);fly.flying=true;jump.jumpLift=18;jump.jumpT=.8;
  const airHits=A.watch([regular,boss,fly,jump]);start();A.advance();
  A.assert(hitsOnly(airHits).length===4,'airborne or boss omitted from damage');
  A.assert(Math.abs(regular.x-280)<1e-6&&Math.abs(boss.x+220)<1e-6&&fly.y===200&&jump.y===-200&&jump.jumpLift===18,'native displacement resistance');out.resistance=true;
  A.reset();const blocked=A.spawn(500,0),W=G.World,old=W.projectileBlock;
  W.projectileBlock=(x,y)=>x>=400&&x<=420?{destructible:false}:false;
  try{A.ready('gravity');A.advance();A.assert(!A.actions().length&&m.t===0,'blocked enemy triggered')}finally{W.projectileBlock=old}
  A.reset();const inner=A.spawn(250,0),block=W.projectileBlock;A.spawn(-500,0);const wallHits=A.watch([inner]);start();
  W.projectileBlock=(x,y)=>x>=100&&x<=120?{destructible:false}:false;
  try{A.advance();A.assert(!hitsOnly(wallHits).length&&inner.x===250,'push crossed wall')}finally{W.projectileBlock=block}out.wall=true;
  A.reset();A.spawn(600,0);const f=start(),age=f.age,t=m.t;
  G.Combat.tick(.5,p,0);G.Combat.updateFields(.5);A.assert(f.age===age&&m.t===t,'pause advanced push');
  p.frozen=true;try{A.advance(.5);A.assert(f.age===age&&m.t===t,'frozen push advanced')}finally{p.frozen=false}
  A.advance();A.assert(!A.actions().length,'push not completed');out.pauseFreeze=true;
  p.moves=[m,moves.find(v=>v.id==='naruto-pain-planet')];A.reset();A.spawn(200,0,true);A.ready('planet');A.advance();A.assert(P.snapshot(p).sharedRecovery===5,'planet did not create shared recovery');p.moves=[m];A.ready('gravity');A.advance();
  A.assert(!A.actions().some(f=>f.kind==='gravity'),'shared planet recovery bypassed');A.finish(4.9);A.assert(!A.actions().length,'shared recovery expired early');A.finish(.12);A.assert(P.snapshot(p).castCounts.gravity===1,'shared recovery did not resume');out.sharedRecovery=true;
  out.cleanup=[];
  for(const reason of ['clear','world','owner-death']) {
   A.reset();const e=A.spawn(200,0),h=A.watch([e]);start();const world=G.World,n=P.actorsFor(p).find(b=>b.path==='naraka');
   if(reason==='clear')G.Combat.clearFields();else if(reason==='world')G.World={...world};else{n.dead=true;p.dead=true}
   try{A.advance();A.assert(!A.actions().length&&!hitsOnly(h).length,'cancelled push damaged '+reason)}finally{G.World=world;p.dead=false}
   out.cleanup.push(reason);
  }
  A.reset();A.spawn(250,0);start();A.advance();const e=P.effects.find(f=>f.kind==='push');A.assert(e,'native push visual missing');
  const c=document.createElement('canvas'),ctx=c.getContext('2d'),arcs=[],arc=ctx.arc.bind(ctx);ctx.arc=(...args)=>{arcs.push(args[2]);return arc(...args)};
  G.Combat.drawAirFields(ctx);A.assert(arcs.includes(300),'push visual radius differs from actual 300');out.visualRadius=300;
  return out;
 } finally {p.moves=moves;A.reset()}
}"""

SCENE = r"""() => {
 const A=Acceptance;A.reset();for(const a of [0,.8,1.7,2.6,3.5,4.4,5.3])A.spawn(Math.cos(a)*260,Math.sin(a)*260);
 A.ready('gravity');A.finish(.16);
}"""

RENDER = r"""() => {
 const canvas=document.createElement('canvas');canvas.width=880;canvas.height=820;
 const ctx=canvas.getContext('2d');ctx.fillStyle='#23323d';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.translate(440,410);ctx.imageSmoothingEnabled=false;
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
            for phase in ['push', 'fade']:
                if phase == 'fade':
                    frame.evaluate('Acceptance.finish(.08)')
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
