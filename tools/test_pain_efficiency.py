"""Native acceptance for the requested Six Paths balance update."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-efficiency'
CHECK = r"""(scenario) => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out={};
 A.reset();const moves=p.moves;
 const only=(...ids)=>{p.moves=moves.filter(m=>ids.includes(m.id))};
 try {
  if(scenario==='gravity') {
   only('naruto-pain-gravity');const m=p.moves[0];A.assert(m.cd===3,'gravity base CD');
   p.cdMul=.5;A.spawn(120,0);A.ready('gravity');A.advance();
   A.assert(Math.abs(m.t-1.5)<1e-8,'gravity cooldown multiplier');
   A.finish(1.7);A.assert(P.snapshot(p).castCounts.gravity===2,'gravity repeat cadence');
   return {base:m.cd,effective:1.5,casts:P.snapshot(p).castCounts.gravity};
  }
  if(scenario==='absorb') {
   only('naruto-pain-absorb');p.cdMul=.5;
   const preta=P.actors().find(b=>b.path==='preta');
   const guard=()=>{P.actors().forEach((b,i)=>{b.x=-150-i*25;b.y=-200});preta.x=60;preta.y=0};guard();
   const make=(opts={})=>G.Projectiles.spawn({friendly:false,x:80,y:0,px:80,py:0,r:3,dmg:7,painAbsorbable:true,...opts});
   const eligible=[make(),make({y:12,py:12}),make({x:40,px:40})];
   const controls=[make({physical:true,y:20,py:20}),make({beam:true,y:20,py:20}),make({ground:true,y:20,py:20}),make({painAbsorbable:false,y:20,py:20}),make({friendly:true}),make({y:50,py:50})];
   A.resume();G.Combat.resolve(.01,p,0);A.pause();
   A.assert(eligible.every(s=>!G.Projectiles.all().includes(s)),'batch left eligible shots');
   A.assert(controls.every(s=>G.Projectiles.all().includes(s)),'batch swallowed ineligible/outside shot');
   A.assert(P.snapshot(p).intercepted===3&&P.snapshot(p).absorbCooldown===1.25,'batch cooldown/count');
   const late=make();A.resume();G.Combat.resolve(.01,p,0);A.pause();
   A.assert(G.Projectiles.all().includes(late),'cooldown swallowed late shot');
   G.Projectiles.clear();A.finish(1.26);guard();const next=[make(),make({y:12,py:12})];
   A.resume();G.Combat.resolve(.01,p,0);A.pause();
   A.assert(next.every(s=>!G.Projectiles.all().includes(s))&&P.snapshot(p).intercepted===5,'next batch failed');
   G.Projectiles.clear();A.finish(1.26);guard();const wallShot=make({x:25,px:25});
   const block=G.World.projectileBlock;G.World.projectileBlock=x=>x>=40&&x<=45?{destructible:false}:false;
   try{A.resume();G.Combat.resolve(.01,p,0);A.pause();A.assert(G.Projectiles.all().includes(wallShot),'absorption crossed wall')}
   finally{G.World.projectileBlock=block}
   return {firstBatch:3,secondBatch:2,controls:controls.length,cooldown:1.25,wall:true};
  }
  if(scenario==='soul') {
   only('naruto-pain-soul');out.cases=[];
   for(const cancel of [null,'distance','wall','body-death','clear','unlearn','pause','freeze','world']) {
    A.reset();const human=P.actors().find(b=>b.path==='human');human.x=human.y=0;
    const e=A.spawn(140,0),hits=A.watch([e]);A.ready('soul');A.advance();
    const f=A.actions().find(f=>f.kind==='soul');
    A.assert(f?.phase==='grasp'&&human.x>100&&Math.hypot(human.x-e.x,human.y-e.y)<=36,'soul did not teleport into grasp');
    A.assert(e.hp===100000&&p.moves[0].t===5,'teleport damage/cooldown timing');
    const block=G.World.projectileBlock,world=G.World;
    if(cancel==='distance')e.x+=100;
    if(cancel==='wall')G.World.projectileBlock=()=>({destructible:false});
    if(cancel==='body-death')human.hurt(human.maxHp+1,null,true);
    if(cancel==='clear')G.Combat.clearFields();
    if(cancel==='unlearn')p.moves=[];
    if(cancel==='freeze')p.frozen=true;
    if(cancel==='world')G.World={...world};
    try {
     if(cancel==='pause'||cancel==='freeze') {
      const age=f.age;G.Combat.updateFields(.7);A.assert(f.age===age&&e.hp===100000,'pause/freeze advanced grasp');
     } else if(!cancel) {
      A.finish(.59);A.assert(e.hp===100000,'soul hit before .6 seconds');A.finish(.03);
      A.assert(hits.filter(h=>h.id==='naruto-pain-soul').length===1,'soul missing/duplicate native hit');
     } else {A.finish(.7);A.assert(!hits.some(h=>h.id==='naruto-pain-soul'),'cancelled soul dealt damage')}
    } finally {G.World=world;G.World.projectileBlock=block;p.frozen=false;only('naruto-pain-soul')}
    out.cases.push(cancel||'hit');
   }
   return out;
  }
  if(scenario==='soul-safety') {
   only('naruto-pain-soul');out.rejected=[];
   for(const reason of ['wall','landing','hazard','owner-range','body-range']) {
    A.reset();const b=P.actors().find(b=>b.path==='human');b.x=b.y=0;
    const e=A.spawn(140,0),W=G.World,saved={isFree:W.isFree,isWall:W.isWall,projectileBlock:W.projectileBlock};
    if(reason==='wall')W.isWall=x=>x>=60&&x<=90;
    if(reason==='landing')W.isFree=(x,y)=>Math.hypot(x-e.x,y-e.y)>45;
    if(reason==='hazard')G.Hazards.add({kind:'zone',x:e.x,y:e.y,r:60,delay:3,dmg:80});
    if(reason==='owner-range'){b.x=250;e.x=350;G.EnemyMgr.rebuildGrid()}
    if(reason==='body-range'){e.x=250;G.EnemyMgr.rebuildGrid()}
    try{A.ready('soul');A.advance();A.assert(!A.actions().some(f=>f.kind==='soul')&&p.moves[0].t===0,'unsafe teleport '+reason)}
    finally{Object.assign(W,saved);G.Hazards.clear()}
    out.rejected.push(reason);
   }
   return out;
  }
  if(scenario==='planet') {
   only('naruto-pain-planet');const seed=A.spawn(0,0,true);
   const es=[seed,A.spawn(280,0),A.spawn(-250,80),A.spawn(0,300),A.spawn(0,550)];
   es.forEach(e=>e.flying=true);const hits=es.map(e=>A.watch([e]));
   A.ready('planet');A.advance();const f=A.actions().find(f=>f.kind==='planet');
   A.assert(f?.m.radius===320,'planet radius config');
   A.finish(.75);
   function render(radius) {
    const old=f.m.radius;f.m.radius=radius;
    const canvas=document.createElement('canvas');canvas.width=canvas.height=800;
    const ctx=canvas.getContext('2d');ctx.fillStyle='#253c28';ctx.fillRect(0,0,800,800);ctx.translate(400,430);
    const arcs=[],arc=ctx.arc.bind(ctx);ctx.arc=(...args)=>{arcs.push(args[2]);return arc(...args)};
    try{G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);return {png:canvas.toDataURL(),arcs}}
    finally{f.m.radius=old}
   }
   const reference=render(160),updated=render(320);
   A.assert(updated.arcs.includes(320)&&P.planetVisual(f).shell>45,'planet range/aggregated shell too small');
   A.finish(.76);
   const collapse=P.effects.find(e=>e.kind==='collapse');A.assert(collapse?.m.impactRadius===480,'impact radius lost');
   A.finish(.1);const arcs=[],canvas=document.createElement('canvas'),ctx=canvas.getContext('2d'),arc=ctx.arc.bind(ctx);
   ctx.arc=(...args)=>{arcs.push(args[2]);return arc(...args)};G.Combat.drawAirFields(ctx);
   A.assert(arcs.some(r=>Math.abs(r-480*collapse.age/collapse.life)<1e-8),'shockwave visual radius');
   A.finish(.6);
   A.assert(hits.slice(0,4).every(h=>h.filter(v=>v.id==='naruto-pain-planet').length===4),'planet missed enlarged-area four phases');
   A.assert(es[4].hp===100000,'planet damaged beyond shockwave radius');
   A.assert(P.snapshot(p).sharedRecovery>2,'planet shared recovery lost');
   return {damage:es.map(e=>100000-e.hp),phases:hits.map(h=>h.filter(v=>v.id==='naruto-pain-planet').length),reference,updated};
  }
  if(scenario==='planet-pull') {
   only('naruto-pain-planet');A.spawn(0,0,true);
   const inside=A.spawn(280,0),outside=A.spawn(350,0);A.ready('planet');A.advance();A.finish(.25);
   A.assert(inside.x<260&&outside.x===350,'enlarged planet pull boundary');
   return {insidePull:280-inside.x,outsidePull:350-outside.x};
  }
  if(scenario==='quantity') {
   out.tiers=[];
   for(const id of ['naruto-pain','naruto-pain-missiles'])for(let tier=1;tier<=5;tier++) {
    p.moves=moves;
    if(tier>1){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(card&&card.apply(p)!==false,'missing actual tier upgrade')}
    for(const picks of [0,4,20]) {
     A.reset();p.quantityPicks=p.quantityBonus=picks;only(id);const m=p.moves[0];
     if(id.endsWith('missiles')){const b=P.actors().find(b=>b.path==='asura');b.x=b.y=0;A.ready('missiles')}
     A.spawn(180,0);A.advance();const expected=Math.min(id==='naruto-pain'?40:30,Math.floor([5,5,6,7,8][tier-1]*Math.pow(1.25,picks)));
     A.assert(P.snapshot(p).count===expected,'native cast quantity '+id+' tier '+tier+' picks '+picks+' got '+P.snapshot(p).count);
     out.tiers.push({id,tier,picks,count:expected});
    }
   }
   return out;
  }
 } finally {p.moves=moves;G.Hazards.clear();A.reset()}
}"""


def main():
    report = {'url': URL, 'viewports': {}, 'errors': []}
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, viewport in [('desktop', {'width': 1200, 'height': 900}), ('mobile', {'width': 390, 'height': 844})]:
            page = browser.new_page(viewport=viewport, is_mobile=label == 'mobile', has_touch=label == 'mobile', service_workers='block')
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL)
            frame = game_frame(page)
            enter(frame)
            results = report['viewports'][label] = {}
            for scenario in ['gravity', 'absorb', 'soul', 'soul-safety', 'planet', 'planet-pull', 'quantity']:
                print(label, scenario, flush=True)
                result = frame.evaluate(CHECK, scenario)
                if scenario == 'planet':
                    for key in ['reference', 'updated']:
                        data = result[key].pop('png').split(',', 1)[1]
                        (OUT / f'{label}-planet-{key}.png').write_bytes(base64.b64decode(data))
                results[scenario] = result
            frame.evaluate('''() => {const A=Acceptance,p=A.p();A.reset();p.moves=p.moves.filter(m=>m.id==='naruto-pain-planet');A.spawn(0,0,true);A.ready('planet');A.advance();A.finish(.75)}''')
            page.screenshot(path=str(OUT / f'{label}-planet-game.png'))
            page.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
