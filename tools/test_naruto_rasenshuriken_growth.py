"""Normal-entry projectile growth, light outer spread and long orange-cloak contracts."""
import base64
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
LIVE = os.environ.get('CLOAK_LIVE') == '1'
OUT = ROOT / ('.omx/state/naruto-rasenshuriken-growth-public' if LIVE else 'art-review/naruto-rasenshuriken-growth-20261116')
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&layout=wide'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

CHECK = r"""() => {
 const p=G.Game.player,V=G.NarutoRasenshurikenVFX,S=G.NarutoSupport,id='naruto-rasenshuriken',cloakId='naruto-nine-tails-cloak';
 const assert=(v,m)=>{if(!v)throw Error(m)},near=(a,b,m)=>assert(Math.abs(a-b)<1e-6,m+': '+a+' != '+b);
 const sizes=[12,15,18,21,24],blasts=[100,110,120,130,140],durations=[24,27,27,27,30],cooldowns=[42,42,42,42,35.7];
 Object.assign(G.World,{isWall:()=>false,isFree:()=>true,collide:()=>{},propsInCircle:()=>[],projectileBlock:()=>false,isLiquid:()=>false});
 G.Camera.sees=()=>true;
 function enemy(x,y){const e=new G.Enemy({dex:19,hp:1e7,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
   e.types=['normal'];e.touchCd=999;G.EnemyMgr.add(e);return e;}
 function reset(rank=1){
   G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();G.NarutoClones.clear();G.SelfClones.clear();
   G.World.isWall=()=>false;G.World.projectileBlock=()=>false;
   p.x=p.y=0;p.aim=0;p.hp=p.maxHp;p.dead=false;p.frozen=false;p.flash=p.invuln=0;
   p.critChance=0;p.percentHealthDamage=p.lifestealRate=0;p.quantityBonus=p.quantityPicks=0;p.cdMul=1;
   p.level=30;p.moves=[];p.slots=[];p.bind={};p.active=0;p.target=null;
   assert(p.addMove(id),'learn Rasenshuriken');const m=p.moves.find(m=>m.id===id);
   for(let n=1;n<rank;n++)assert(G.Moves.levelUp(m),'incremental level-up failed');
   G.Camera.x=G.Camera.y=0;return m;
 }
 function activate(owner=p,rank=1){
   enemy(owner.x+200,owner.y);G.EnemyMgr.rebuildGrid();
   assert(S.cast(owner,G.Moves.instance(cloakId,rank)),'cloak cast failed');
   const f=S.effects.find(f=>f.owner===owner&&f.mode==='nine-tails-cloak');assert(f,'missing cloak effect');return f;
 }
 function launch(m){assert(G.DigimonSkills.cast(p,m),'Rasenshuriken cast failed');const shot=G.Projectiles.all().at(-1);assert(shot?.mid===id,'missing projectile');return shot;}
 function render(shot){
   const canvas=document.createElement('canvas');canvas.width=360;canvas.height=240;
   const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.translate(180-shot.x,145-shot.y+G.LIFT);
   const before=JSON.stringify({x:shot.x,y:shot.y,r:shot.r,dmg:shot.dmg,t:shot.t,cloak:shot.narutoCloak});
   assert(V.drawProjectile(ctx,shot),'renderer rejected projectile');
   assert(before===JSON.stringify({x:shot.x,y:shot.y,r:shot.r,dmg:shot.dmg,t:shot.t,cloak:shot.narutoCloak}),'render changed simulation');
   const rgba=ctx.getImageData(0,0,360,240).data;let left=360,top=240,right=-1,bottom=-1,blue=0,orange=0;
   for(let y=0;y<240;y++)for(let x=0;x<360;x++){const i=(y*360+x)*4;if(rgba[i+3]<40)continue;
     left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x);bottom=Math.max(bottom,y);
     if(rgba[i+2]>rgba[i]*1.15&&rgba[i+2]>60)blue++;
     if(rgba[i]>rgba[i+2]*1.5&&rgba[i]>100&&rgba[i+1]>40)orange++;
   }
   assert(left>0&&top>0&&right<359&&bottom<239,'projectile evidence clipped');
   return {width:right-left+1,height:bottom-top+1,blue,orange,image:canvas.toDataURL()};
 }
 const tiers=[],frames=[];
 for(let rank=1;rank<=5;rank++){
   const m=reset(rank),single=G.Moves.instance(id,rank);
   near(m.size,sizes[rank-1],'incremental size rank '+rank);near(single.size,m.size,'instance vs levelUp size');
   near(m.blastRadius,blasts[rank-1],'blast rank '+rank);near(single.blastRadius,m.blastRadius,'instance vs levelUp blast');
   near(m.spreadRadiusMul,1.25,'light spread radius multiplier');near(m.spreadDamageRatio,.15,'light spread damage ratio');
   let shot=launch(m);shot.t=.11;near(shot.r,m.size,'physical projectile radius');
   assert(!shot.narutoCloak&&shot.vis.pal==='naruto-blue','normal projectile is not blue');
   const blue=render(shot);assert(blue.blue>10&&blue.orange===0,'normal projectile palette is not blue');
   frames.push({rank,cloak:false,...blue});
   G.Projectiles.clear();activate();shot=launch(m);shot.t=.11;
   assert(shot.narutoCloak&&shot.vis.pal==='naruto-cloak-orange','cloak projectile/trail marker missing');
   const orange=render(shot);assert(orange.orange>10&&orange.blue===0,'cloak projectile palette is not orange');
   frames.push({rank,cloak:true,...orange});
   near(orange.width,blue.width,'palette changed projectile width');near(orange.height,blue.height,'palette changed projectile height');
   if(rank>1){assert(blue.width>tiers.at(-1).width&&blue.height>tiers.at(-1).height,'each rank must visibly grow');}
   tiers.push({rank,size:m.size,blast:m.blastRadius,width:blue.width,height:blue.height});
   S.update(durations[0]+.1);assert(!S.effects.some(f=>f.owner===p),'cloak failed to expire');
   assert(shot.narutoCloak&&render(shot).orange>10,'in-flight cast color changed after cloak expiry');
 }
 // Same-cost actual impact: core and outer annulus are exclusive and walls occlude spread.
 function impactCase(rank=1,cloneScale=1){
   const m=reset(rank),core=enemy(50,0),edge=enemy(0,m.blastRadius+16),outside=enemy(0,m.blastRadius*1.25+30),blocked=enemy(-m.blastRadius-16,0);
   edge.y=m.blastRadius+edge.r+4;outside.y=m.blastRadius*1.25+outside.r+8;blocked.x=-m.blastRadius-blocked.r-4;
   const all=[core,edge,outside,blocked],calls=all.map(()=>[]);
   all.forEach((e,i)=>{const hurt=e.hurt;e.hurt=function(amount,...args){calls[i].push(amount);return hurt.call(this,amount,...args)};});
   G.EnemyMgr.rebuildGrid();G.World.isWall=G.World.projectileBlock=(x,y)=>x< -45&&x> -55&&Math.abs(y)<20;
   const shot=cloneScale===1?launch(m):G.DigimonSkills.fireFrom(p,m,0,0,0,cloneScale)[0];
   shot.x=shot.y=0;shot.hits.add(core.id);G.Combat.resolve(0,p,0);
   assert(calls[0].length===1&&calls[1].length===1,'core/outer target did not receive one exclusive impact');
   const base=m.dmg*p.atk*G.Types.mult(m.type,core.types)*G.Weather.mult(m.type)*cloneScale;
   near(calls[0][0],base*.8,'core impact damage');near(calls[1][0],base*.15,'light outer damage');
   assert(!calls[2].length&&!calls[3].length,'spread escaped radius or wall');
   const after=all.map(e=>e.hp);G.Combat.resolve(0,p,0);assert(all.every((e,i)=>e.hp===after[i]),'spread repeated damage');
   assert(!G.Projectiles.all().includes(shot),'impact did not remove projectile');
   return {rank,cloneScale,core:calls[0][0],outer:calls[1][0],outside:calls[2].length,wall:calls[3].length};
 }
 const impacts=[impactCase(1),impactCase(5),impactCase(1,.3)];
 // Solid breakables must not block their own damage ray, while a separate wall still does.
 let propImpact;
 {
   const m=reset(),saved={propsInCircle:G.World.propsInCircle,projectileBlock:G.World.projectileBlock,damageProp:G.World.damageProp};
   const props=[{name:'core',x:55,y:0,r:8},{name:'outer',x:0,y:m.blastRadius+16,r:8},
     {name:'outside',x:0,y:m.blastRadius*1.25+24,r:8},{name:'wall',x:-70,y:0,r:8}]
     .map(prop=>({...prop,solid:true,destructible:true,hp:1e7}));
   const calls=Object.fromEntries(props.map(prop=>[prop.name,[]]));
   try{
     G.World.propsInCircle=(x,y,r)=>props.filter(prop=>Math.hypot(prop.x-x,prop.y-y)<=r+prop.r);
     G.World.projectileBlock=(x,y,r=1)=>{
       if(x< -25&&x> -35&&Math.abs(y)<10)return 'wall';
       return props.find(prop=>Math.hypot(prop.x-x,prop.y-y)<prop.r+r)||null;
     };
     G.World.damageProp=(prop,amount)=>{calls[prop.name].push(amount);return true;};
     const shot=launch(m);shot.x=shot.y=0;shot.hits.add(-1);G.Combat.resolve(0,p,0);
     assert(calls.core.length===1&&calls.outer.length===1,'solid prop blocked its own blast ray');
     near(calls.core[0],m.dmg*p.atk*.8,'solid core prop damage');
     near(calls.outer[0],m.dmg*p.atk*.15,'solid outer prop damage');
     assert(!calls.outside.length&&!calls.wall.length,'prop spread escaped range or separate wall');
     G.Combat.resolve(0,p,0);assert(calls.core.length===1&&calls.outer.length===1,'prop blast repeated after removal');
     propImpact=calls;
   }finally{Object.assign(G.World,saved);}
 }
 // The actual orange collision passes its launch tint and complete spread radius to VFX.
 let burst;
 {
   const m=reset(5);activate();const victim=enemy(50,0);G.EnemyMgr.rebuildGrid();
   const shot=launch(m);shot.x=shot.y=0;shot.hits.add(victim.id);G.Combat.resolve(0,p,0);
   const f=V.activeBursts.at(-1);assert(f?.cloak,'actual impact did not preserve orange launch color');
   near(f.radius,m.blastRadius*m.spreadRadiusMul,'impact does not show full spread radius');
   const canvas=document.createElement('canvas');canvas.width=420;canvas.height=360;
   const ctx=canvas.getContext('2d');V.drawBurst(ctx,210,180,.22,f.radius,{cloak:f.cloak});
   const data=ctx.getImageData(0,0,420,360).data;let orange=0,blue=0;
   for(let i=0;i<data.length;i+=4)if(data[i+3]>40){
     if(data[i]>data[i+2]*1.5&&data[i]>100&&data[i+1]>40)orange++;
     if(data[i+2]>data[i]*1.15&&data[i+2]>60)blue++;
   }
   assert(orange>10&&blue===0,'orange collision burst retained blue pixels');
   burst={radius:f.radius,orange,blue,image:canvas.toDataURL()};
 }
 // A hurt callback can clear the entire cast; same-wave targets must then stop.
 {
   const m=reset(),first=enemy(50,0),second=enemy(50,0);let firstCalls=0,secondCalls=0;
   const hurt=first.hurt;first.hurt=function(...args){firstCalls++;hurt.apply(this,args);G.Combat.clearFields(p)};
   second.hurt=()=>{secondCalls++};G.EnemyMgr.rebuildGrid();const shot=launch(m);shot.x=shot.y=0;shot.hits.add(first.id);
   G.Combat.resolve(0,p,0);assert(firstCalls===1&&secondCalls===0,'clear from first callback failed to cancel subsequent targets');
   G.Combat.resolve(0,p,0);assert(secondCalls===0,'cancelled impact resumed');
 }
 // Native autonomous shadows inherit the orange launch snapshot from their owner.
 {
   const m=reset();activate();G.EnemyMgr.clear();enemy(200,0);G.EnemyMgr.rebuildGrid();
   assert(G.NarutoClones.cast(p,G.Moves.instance('naruto-shadow-clones',1)),'shadow summon failed');
   for(const a of G.NarutoClones.actors)a.cooldowns.set(id,0);
   G.NarutoClones.update(.01);const shots=G.Projectiles.all().filter(s=>s.mid===id&&s.narutoClone);
   assert(shots.length&&shots.every(s=>s.owner===p&&s.narutoCloak&&s.vis.pal==='naruto-cloak-orange'),'native shadow color/owner mismatch');
 }
 // Card clones own their own cloak; their tint must not leak to an ordinary owner.
 {
   const m=reset(),card=G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);
   assert(card&&G.SelfClones.isControlled(card),'missing card clone');activate(card);
   const shot=G.DigimonSkills.fireFrom(card,card.moves.find(m=>m.id===id),card.x,card.y,0)[0];
   assert(shot?.owner===card&&shot.narutoCloak,'card cloak snapshot missing');
   const ordinary=launch(m);assert(!ordinary.narutoCloak,'card cloak leaked to ordinary owner');
 }
 const cloakTiers=[];
 for(let rank=1;rank<=5;rank++){
   reset();const m=G.Moves.instance(cloakId,rank),incremental=G.Moves.instance(cloakId,1);
   for(let n=1;n<rank;n++)G.Moves.levelUp(incremental);
   near(m.cd,cooldowns[rank-1],'cloak cooldown rank '+rank);near(m.fieldDuration,durations[rank-1],'cloak duration rank '+rank);
   near(incremental.cd,m.cd,'incremental cloak cooldown');near(incremental.fieldDuration,m.fieldDuration,'incremental cloak duration');
   const f=activate(p,rank);near(f.ttl,m.fieldDuration,'runtime cloak duration clamp');
   S.update(13);assert(S.effects.includes(f),'long cloak still capped at old 12 seconds');
   S.update(m.fieldDuration-13-.01);assert(S.effects.includes(f),'cloak expired early');
   S.update(.02);assert(!S.effects.includes(f),'cloak survived intended expiry');
   cloakTiers.push({rank,cd:m.cd,duration:m.fieldDuration});
 }
 reset();const finalMove=p.moves.find(m=>m.id===id);activate();
 G.Game.togglePause();S.update(.7);p.anim.update(.7);G.Game.togglePause();G.UI.hide('scr-pause');
 p.target=enemy(180,-70);G.EnemyMgr.rebuildGrid();p.aim=-.35;
 launch(finalMove);G.Projectiles.update(.18,p,G.EnemyMgr.all());
 window.rasenGrowth={frames,tiers,impacts,cloakTiers};
 return {tiers,impacts,propImpact,cloakTiers,frames,burst,checks:['normal entry','instance and real incremental upgrades','all five blue/orange render sizes','cast tint snapshot','native shadow tint','independent card clone tint','orange collision burst and complete spread radius','core and outer damage exclusive','outside and wall blocked','solid breakables exempt their own path but not separate walls','no repeat damage','callback cancellation','tripled cloak runtime and cooldown']};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reports = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for width in (1100, 390):
            context = browser.new_context(viewport={'width': width, 'height': 850}, is_mobile=width < 500,
                                          has_touch=width < 500, locale='zh-TW', service_workers='block')

            def route(request):
                file = ROOT / unquote(urlsplit(request.request.url).path).removeprefix('/pokesurvivor/')
                request.fulfill(status=200 if file.is_file() else 404, body=file.read_bytes() if file.is_file() else b'Not found',
                                content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')

            if not LIVE:
                context.route('https://tim12332000.github.io/pokesurvivor/**', route)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(URL.replace('digimon.html', 'portrait.html').replace('layout=wide', 'layout=portrait') if width < 500 else URL)
            view = page
            if width < 500:
                page.wait_for_selector('#portrait-game')
                view = page.locator('#portrait-game').element_handle().content_frame()
            view.wait_for_function('window.PS_REDRAWN_READY && G.NarutoRasenshurikenVFX && document.getElementById("boot").classList.contains("hidden")')
            if view.locator('#tap-start').is_visible():
                view.locator('#tap-start').click()
            view.evaluate("""async()=>{await PS_REDRAWN_READY;G.Naruto.choose(30001);await G.Flow.play();
              if(G.Game.state==='playing')G.Game.togglePause();G.UI.hideAll();
              document.querySelectorAll('.toast,#ach-pop').forEach(e=>e.style.display='none');}""")
            report = view.evaluate(CHECK)
            for frame in report.pop('frames'):
                image = frame.pop('image')
                (OUT / f'{width}-rank-{frame["rank"]}-{"orange" if frame["cloak"] else "blue"}.png').write_bytes(base64.b64decode(image.split(',', 1)[1]))
            burst = report['burst']
            (OUT / f'{width}-orange-impact.png').write_bytes(base64.b64decode(burst.pop('image').split(',', 1)[1]))
            page.wait_for_timeout(80)
            view.evaluate("G.UI.hide('scr-pause')")
            page.screenshot(path=str(OUT / f'{width}-orange-gameplay.png'))
            assert not errors, errors
            report['errors'] = errors
            reports[str(width)] = report
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(reports, indent=2) + '\n', encoding='utf-8')
    print('PASS: five-tier growth, blue/orange body and clone projectiles, exclusive spread, callbacks, tripled cloak, desktop/mobile')


if __name__ == '__main__':
    main()
