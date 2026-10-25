"""Real entry screenshots and deterministic visual lifecycle for Planetary Devastation."""
import base64
import json
import io
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-planet-vfx'
SETUP = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;A.reset();
 p.moves=p.moves.filter(m=>m.id==='naruto-pain-planet');
 const es=[A.spawn(0,0,true),A.spawn(280,0),A.spawn(-250,80),A.spawn(0,300),A.spawn(0,961)];
 es.forEach(e=>e.flying=true);window.planetEnemies=es;window.planetHits=es.map(e=>A.watch([e]));
 A.ready('planet');A.advance();
}"""
CAPTURE = r"""() => {
 const P=G.NarutoPain,p=Acceptance.p(),f=P.actionsFor(p).find(f=>f.kind==='planet')||P.effects.find(f=>f.kind==='collapse');
 Acceptance.assert(f,'missing phase object');
 const canvas=document.createElement('canvas');canvas.width=canvas.height=1000;
 const ctx=canvas.getContext('2d');ctx.fillStyle='#253c28';ctx.fillRect(0,0,1000,1000);ctx.scale(.48,.48);ctx.translate(1042,1042);
 ctx.imageSmoothingEnabled=false;const before={alpha:ctx.globalAlpha,fill:ctx.fillStyle,transform:ctx.getTransform().toString()};
 const times=[];for(let i=0;i<20;i++){const start=performance.now();G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);times.push(performance.now()-start)}
 Acceptance.assert(ctx.globalAlpha===before.alpha&&ctx.fillStyle===before.fill&&ctx.getTransform().toString()===before.transform,'VFX leaked canvas state');
 const first=canvas.toDataURL();G.Combat.updateFields(.5);
 const age=f.age;const next=document.createElement('canvas');next.width=next.height=1000;
 const n=next.getContext('2d');n.fillStyle='#253c28';n.fillRect(0,0,1000,1000);n.scale(.48,.48);n.translate(1042,1042);
 for(let i=0;i<20;i++){G.Combat.drawGroundFields(n);G.Combat.drawAirFields(n)}
 Acceptance.assert(f.age===age&&first===next.toDataURL(),'pause/render changed animation');
 times.sort((a,b)=>a-b);
 return {visual:P.planetVisual(f),png:first,drawMedianMs:times[10],damage:planetEnemies.map(e=>100000-e.hp)};
}"""
LIFECYCLE = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,world=G.World,out=[];
 for(const phase of ['gather','wave'])for(const reason of ['clear','world','death','owner-down','unlearn']) {
  A.reset();A.spawn(0,0,true);const far=A.spawn(900,0);far.flying=true;A.ready('planet');A.advance();A.finish(phase==='gather'?.4:1.55);
  if(reason==='clear')G.Combat.clearFields();
  if(reason==='world')G.World={...world};
  if(reason==='death'){P.actorsFor(p).find(b=>b.path==='naraka').hurt(100000,null,true);p.dead=true;p.hp=0}
  if(reason==='owner-down'){p.dead=true;p.hp=0}
  const moves=p.moves;if(reason==='unlearn')p.moves=[];
  try{A.advance();A.assert(!P.actionsFor(p).some(f=>f.kind==='planet')&&!P.effects.some(f=>f.kind==='collapse'),'cancel left visual '+phase+':'+reason);A.finish(.7);A.assert(far.hp===100000,'cancelled wave damaged distant enemy')}
  finally{G.World=world;p.moves=moves;p.dead=false;p.hp=p.maxHp}
  out.push(phase+':'+reason);
 }
 return out;
}"""
SHOCKWAVE = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;A.reset();
 const center=A.spawn(0,0,true),distances=[120,320,680,920,960,961];
 const es=distances.map(d=>A.spawn(d,0));[center,...es].forEach(e=>e.flying=true);
 const hits=es.map(e=>A.watch([e]));A.ready('planet');A.advance();A.finish(1.5);
 const wave=P.effects.find(f=>f.kind==='collapse'),age=wave.age;
 G.Combat.updateFields(.3);A.assert(wave.age===age,'pause advanced shockwave');
 p.frozen=true;A.resume();try{G.Combat.updateFields(.3)}finally{p.frozen=false;A.pause()}
 A.assert(wave.age===age,'freeze advanced shockwave');
 const before=es.map(e=>e.hp),samples=[];
 function step(dt,expected) {
  for(let i=0;i<Math.round(dt*100);i++)A.advance(.01);const damaged=es.map((e,i)=>e.hp<before[i]);
  A.assert(JSON.stringify(damaged)===JSON.stringify(expected),'wavefront damage timing '+JSON.stringify({dt,damaged,expected}));
  samples.push(damaged);
 }
 step(.08,[true,false,false,false,false,false]);
 step(.14,[true,true,false,false,false,false]);
 step(.22,[true,true,true,false,false,false]);
 step(.14,[true,true,true,true,false,false]);
 step(.03,[true,true,true,true,true,false]);
 const counts=hits.map(h=>h.filter(v=>v.id==='naruto-pain-planet').length);
 A.assert(JSON.stringify(counts)===JSON.stringify([4,4,1,1,1,0]),'shockwave duplicate or outside hit '+counts);
 A.finish(.8);A.assert(hits.every((h,i)=>h.length===counts[i]),'expired wave repeated damage');
 // An occluder inserted after landing must also stop the final wave's native hit.
 A.reset();A.spawn(0,0,true).flying=true;const blocked=A.spawn(680,0);blocked.flying=true;
 A.ready('planet');A.advance();A.finish(1.5);const wall=G.World.isWall;
 G.World.isWall=(x,y)=>x>=400&&x<=420&&Math.abs(y)<10;
 try{A.finish(.7);A.assert(blocked.hp===100000,'shockwave damaged through solid wall')}
 finally{G.World.isWall=wall}
 A.reset();A.spawn(0,0,true).flying=true;const edge=A.spawn(960,0);edge.flying=true;
 const edgeHits=A.watch([edge]);A.ready('planet');A.advance();A.finish(1.5);A.advance(1);
 A.assert(edgeHits.length===1&&!P.effects.some(f=>f.kind==='collapse'),'large update skipped wave edge or retained wave');
 return {distances,counts,samples,wall:true,largeStep:true};
}"""


BALANCE = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,moves=p.moves,stats={baseAtk:p.baseAtk,atkMul:p.atkMul,buff:p.buffs.atk.n},out=[];
 try {
  p.baseAtk=1;p.atkMul=1;p.buffs.atk.n=0;
  for(let tier=1;tier<=5;tier++)for(const multiplier of [1,.5]) {
   p.moves=[G.Moves.instance('naruto-pain-planet',tier)];A.reset();p.cdMul=multiplier;
   const m=p.moves[0],ratio=[1,1.2,1.4,1.7,2][tier-1];
   A.assert(m.cd===18&&m.range===640&&m.radius===640&&m.impactRadius===960&&m.visualScale===1.5,'planet base configuration tier '+tier);
   A.assert(Math.abs(m.dmg-240*ratio)<1e-8,'planet doubled damage tier '+tier);
   const es=[A.spawn(0,0,true),A.spawn(200,0),A.spawn(-200,0),A.spawn(0,640),A.spawn(0,641),A.spawn(0,960),A.spawn(0,961)];
   es.forEach(e=>e.flying=true);const hs=es.map(e=>A.watch([e]));
   A.ready('planet');A.advance();
   A.assert(Math.abs(m.t-18*multiplier)<1e-8,'planet cooldown card scaling');
   A.finish(2.2);
   const counts=hs.map(h=>h.length),expected=[4,4,4,4,1,1,0];
   A.assert(JSON.stringify(counts)===JSON.stringify(expected),'planet 640/641 and 960/961 boundaries '+counts);
   const total=Math.round(m.dmg*.125)*3+Math.round(m.dmg);
   const ordinaryImpact=30000+p.atk,ordinaryTotal=Math.round(m.dmg*.125)*3+ordinaryImpact;
   A.assert(hs[0].reduce((n,v)=>n+v.damage,0)===total,'planet boss four-phase total tier '+tier);
   A.assert(hs.slice(1,4).every(h=>h.reduce((n,v)=>n+v.damage,0)===ordinaryTotal),'planet ordinary pulse plus fixed impact total tier '+tier+' '+JSON.stringify({ordinaryTotal,hits:hs.slice(1,4)}));
   A.assert(hs.slice(4,6).every(h=>h[0].damage===ordinaryImpact),'planet outer wave fixed impact tier '+tier);
   A.assert(total===Math.round(330*ratio),'planet base330 tier scale '+tier);
   out.push({tier,cdMultiplier:multiplier,bossDamage:total,ordinaryDamage:ordinaryTotal,ordinaryImpact,counts});
  }
 } finally {p.moves=moves;p.baseAtk=stats.baseAtk;p.atkMul=stats.atkMul;p.buffs.atk.n=stats.buff;A.reset()}
 return out;
}"""


FIXED_IMPACT = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,moves=p.moves;
 const previous={baseAtk:p.baseAtk,atkMul:p.atkMul,buff:p.buffs.atk.n,type:G.Types.mult,weather:G.Weather.mult};
 const out=[];
 try {
  for(const test of [
   {name:'normal-tier1',tier:1}, {name:'normal-tier5',tier:5},
   {name:'elite',tier:1,flag:'elite'},
   {name:'boss',tier:1,flag:'boss'}, {name:'legend',tier:1,flag:'legend'}, {name:'judge',tier:1,flag:'judge'},
   {name:'shield-partial',tier:1,shield:100}, {name:'shield-full',tier:1,shield:500},
   {name:'percent-card-additive',tier:1,percent:.02}, {name:'lethal',tier:1,hp:300}
  ]) {
   p.moves=[G.Moves.instance('naruto-pain-planet',test.tier)];A.reset();
   p.baseAtk=50;p.atkMul=1;p.buffs.atk.n=0;p.critChance=1;p.percentHealthDamage=test.percent||0;
   G.Types.mult=()=>2;G.Weather.mult=()=>1.5;
   const boss=!!test.flag&&test.flag!=='elite';
   const center=A.spawn(0,0,true);center.flying=true;center.hp=center.maxHp=1e7;
   const centerHits=A.watch([center]);
   const e=A.spawn(680,0);e.flying=true;e.maxHp=boss?100000:1000;e.hp=boss?100000:(test.hp||600);
   if(test.flag)e[test.flag]=true;
   e.shield=test.shield||0;
   const before={hp:e.hp,shield:e.shield},calls=[],native=e.hurt;
   e.hurt=function(...args){calls.push({amount:args[0],owner:args[6]===p,id:args[7]});return native.apply(this,args)};
   A.ready('planet');A.advance();
   const cast=P.actionsFor(p).find(f=>f.kind==='planet');
   A.assert(cast&&cast.attack===50,'planet cast attack snapshot fixture '+test.name);
   p.baseAtk=999; // Later attack growth must not change the launched wave.
   A.finish(2.2);
   const pulse=Math.round(p.moves[0].dmg*.125*50*2*1.5*1.5+center.maxHp*(test.percent||0)*.1);
   A.assert(centerHits.length===4&&centerHits.slice(0,3).every(h=>h.damage===pulse),'planet original three pulse multipliers '+test.name+' '+JSON.stringify(centerHits));
   const raw=boss?240*50*2*1.5*1.5:350;
   const bonus=test.percent?e.maxHp*test.percent:0;
   const expectedDamage=Math.round(raw+bonus),expectedHp=before.hp-Math.max(0,expectedDamage-before.shield);
   A.assert(calls.length===1&&calls[0].amount===raw&&calls[0].owner&&calls[0].id==='naruto-pain-planet','fixed impact native source/amount '+test.name+' '+JSON.stringify(calls));
   A.assert(e.hp===expectedHp,'fixed impact native HP '+test.name+' '+JSON.stringify({hp:e.hp,expectedHp}));
   A.assert(e.shield===Math.max(0,before.shield-expectedDamage),'fixed impact shield '+test.name);
   A.assert(e.dead===(expectedHp<=0),'fixed impact death lifecycle '+test.name);
   A.finish(.5);A.assert(calls.length===1,'fixed impact repeated after expiry '+test.name);
   out.push({name:test.name,raw,bonus,hp:e.hp,shield:e.shield,dead:e.dead});
  }
 } finally {
  G.Types.mult=previous.type;G.Weather.mult=previous.weather;
  p.moves=moves;p.baseAtk=previous.baseAtk;p.atkMul=previous.atkMul;p.buffs.atk.n=previous.buff;A.reset();
 }
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'viewports': {}, 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, viewport in [('desktop', {'width': 1200, 'height': 900}), ('mobile', {'width': 390, 'height': 844})]:
            page = browser.new_page(viewport=viewport, is_mobile=label == 'mobile', has_touch=label == 'mobile', service_workers='block')
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL)
            frame = game_frame(page)
            enter(frame)
            frame.evaluate(SETUP)
            phases = report['viewports'][label] = {}
            previous = 0
            for name, seconds in [('rise', .08), ('gather', .4), ('seal', 1.1), ('fall', 1.3), ('contact', 1.49), ('impact', 1.51), ('release', 1.9), ('wave-edge', 2.08)]:
                frame.evaluate('(dt)=>{for(let left=dt;left>1e-9;left-=.01)Acceptance.advance(Math.min(.01,left))}', seconds - previous)
                previous = seconds
                result = frame.evaluate(CAPTURE)
                (OUT / f'{label}-{name}.png').write_bytes(base64.b64decode(result.pop('png').split(',', 1)[1]))
                page.screenshot(path=str(OUT / f'{label}-{name}-game.png'))
                phases[name] = result
                if seconds < 1.5:
                    counts = frame.evaluate('planetHits.map(h=>h.filter(v=>v.id==="naruto-pain-planet").length)')
                    assert counts[0] <= 2 and counts[1] <= 2, 'impact damage before moon contact'
            assert phases['rise']['visual']['shell'] == 0
            assert phases['gather']['visual']['shell'] < phases['seal']['visual']['shell']
            assert abs(phases['seal']['visual']['shell'] - 320 * .29 * 1.5) < 1e-8
            assert phases['seal']['visual']['radius'] == 640
            assert phases['seal']['visual']['artRadius'] == 480
            assert phases['seal']['visual']['scale'] == 1.5
            assert phases['fall']['visual']['phase'] == 'fall'
            assert phases['seal']['visual']['height'] > phases['fall']['visual']['height'] > phases['contact']['visual']['height']
            assert phases['contact']['visual']['height'] >= phases['contact']['visual']['shell']
            assert phases['impact']['visual']['phase'] == 'impact'
            assert phases['impact']['visual']['waveRadius'] < phases['release']['visual']['waveRadius']
            frame.evaluate('Acceptance.finish(.25)')
            damage = frame.evaluate('planetHits.map(h=>h.filter(v=>v.id==="naruto-pain-planet").length)')
            assert damage == [4, 4, 4, 4, 0], damage
            phases['damagePhases'] = damage
            frame.evaluate('Acceptance.finish(.6);Acceptance.assert(!G.NarutoPain.effects.some(f=>f.kind==="collapse"),"release visual leaked")')
            phases['lifecycle'] = frame.evaluate(LIFECYCLE)
            phases['shockwave'] = frame.evaluate(SHOCKWAVE)
            phases['balance'] = frame.evaluate(BALANCE)
            phases['fixedImpact'] = frame.evaluate(FIXED_IMPACT)
            if label == 'desktop':
                frame.evaluate(SETUP)
                frames = frame.evaluate(r"""() => {
                 const canvas=document.createElement('canvas');canvas.width=600;canvas.height=700;
                 const ctx=canvas.getContext('2d'),frames=[];
                 for(let i=0;i<66;i++) {
                  ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle='#253c28';ctx.fillRect(0,0,600,700);
                  ctx.scale(.28,.28);ctx.translate(1071,1250);ctx.imageSmoothingEnabled=false;
                  G.Combat.drawGroundFields(ctx);G.Game.player.draw(ctx);
                  G.Combat.drawAirFields(ctx);frames.push(canvas.toDataURL());Acceptance.advance(1/30);
                 }
                 return frames;
                }""")
                images = [Image.open(io.BytesIO(base64.b64decode(data.split(',', 1)[1]))).convert('RGB') for data in frames]
                images[0].save(OUT / 'moon-impact-preview.gif', save_all=True, append_images=images[1:], duration=33, loop=0, disposal=2)
                frame.evaluate(SETUP)
                actual_frames = []
                for _ in range(23):
                    actual_frames.append(Image.open(io.BytesIO(page.screenshot())).convert('RGB'))
                    frame.evaluate('Acceptance.finish(.1)')
                actual_frames[0].save(OUT / 'moon-impact-game.gif', save_all=True, append_images=actual_frames[1:], duration=100, loop=0, disposal=2)
            print(label, 'visual phases, native damage, pause and lifecycle passed', flush=True)
            page.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
