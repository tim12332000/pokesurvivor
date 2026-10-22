"""Learned roaming sand guard: native cards, projectiles, resolve and screenshots."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_gaara import SETUP, URL

OUT = Path(__file__).resolve().parents[1] / '.omx/state/gaara-sand-guard'

FIXTURE = r"""() => {
 const A=Acceptance,p=A.p();A.guardId='naruto-sand-shield';A.guard=()=>G.NarutoSandGuard.state(p);
 A.guardStep=(dt=.01)=>{A.resume();try{G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,0);p.anim.update(dt)}finally{A.pause()}};
 A.guardReset=()=>{A.gaaraArena();p.cdMul=1;p.quantityBonus=0;p.invuln=0;p.hurt(G.NarutoGaara.shieldState(p).amount,null,true);p.invuln=0;return A.guard()};
 A.nativeShot=(x=300,y=100,ax=-1,ay=0)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:17,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});G.EnemyMgr.add(e);e.shoot(ax,ay);return G.Projectiles.all().at(-1)};
 A.shot=(o={})=>G.Projectiles.spawn({friendly:false,x:180,y:0,vx:-90,vy:0,r:6,life:20,dmg:17,mtype:'fire',...o});
 A.untilGone=(shot,limit=3)=>{let n=0;while(G.Projectiles.all().includes(shot)&&n++<limit*100)A.guardStep();return n/100};
 A.isolate=()=>{const g=A.guardReset();g.guardians.forEach((s,i)=>{s.x=i? -300:100;s.y=i? -300:0;if(i){s.ready=false;s.charges=0}});return g.guardians[0]};
 A.spend=s=>{s.ready=false;s.charges=0;s.rechargeProgress=0;s.target=null};
 A.advanceGuard=(seconds)=>{for(let i=0;i<seconds*100;i++)A.guardStep()};
 A.snapshot=()=>{const g=A.guard();return {count:g.count,readyCount:g.readyCount,hp:p.hp,maxHp:p.maxHp,guardians:g.guardians.map(s=>({x:s.x,y:s.y,phase:s.phase,ready:s.ready,charges:s.charges,recharge:s.rechargeProgress,target:!!s.target,contact:!!s.contact}))}};
}"""

PROGRESSION = r"""() => {
 const A=Acceptance,p=A.p(),id=A.guardId,mon=p.mon,out={};p.level=1;
 A.assert(!p.hasMove(id)&&!A.guard(),'guard is innate before learning');
 A.assert(G.Moves.poolFor(mon).includes(id),'guard unavailable at character level one');
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
 A.assert(card&&card.apply(p)!==false,'actual level-one learn card unavailable');
 A.assert(p.hasMove(id)&&p.moves.find(m=>m.id===id).passive,'guard not learned passive');
 A.assert(p.slots.length===1&&!p.slots.some(g=>g.some(m=>m.id===id)),'passive consumed active slot');
 for(const dex of [30001,30002,30006,20001]){p.mon=G.DEX.find(m=>m.dex===dex)||{dex,gen:10,types:['normal']};A.assert(!G.Moves.poolFor(p.mon).includes(id),'guard leaked into '+dex)}p.mon=mon;
 out.learnedAtLevel=1;return out;
}"""

SPEED = r"""() => {
 const A=Acceptance,p=A.p(),g=A.guardReset(),first=g.guardians[0],out=[];
 const original={spdMul:p.spdMul,slowT:p.slowT,buff:{...p.buffs.spd}};
 A.spend(first);first.rechargeProgress=.4;
 try{
  for(const multiplier of [1,1.5,2]){
   p.spdMul=multiplier;p.slowT=0;p.buffs.spd.n=0;
   const current=A.guard(),expected=p.spd+200;
   A.assert(current===g&&current.guardians[0]===first&&!first.ready&&first.rechargeProgress===.4,'speed update reset guardians');
   A.assert(current.speed===expected&&current.guardians.every(c=>c.speed===expected),'speed did not follow player modifier');
   out.push({playerSpeed:p.spd,guardianSpeed:current.speed});
  }
  p.buffs.spd.n=1;p.buffs.spd.amount=.25;
  A.assert(A.guard().guardians.every(c=>c.speed===p.spd+200),'temporary speed buff ignored');
  p.slowT=2;
  A.assert(A.guard().guardians.every(c=>c.speed===p.spd+200),'player slow ignored');
 }finally{p.spdMul=original.spdMul;p.slowT=original.slowT;Object.assign(p.buffs.spd,original.buff);A.guardReset()}
 return out;
}"""

NATIVE = r"""() => {
 const A=Acceptance,p=A.p(),out={};let s=A.isolate(),shot=A.nativeShot(),hp=p.hp;
 A.assert(Math.abs(Math.hypot(shot.vx,shot.vy)-190)<.001&&shot.life===2.4,'fixture did not use native Enemy.shoot');
 const x=s.x,y=s.y;A.guardStep();A.assert(s.target===shot&&s.phase==='pursue','native off-axis shot ignored');
 A.assert(Math.hypot(s.x-x,s.y-y)>.1&&Math.hypot(s.x-x,s.y-y)<=s.speed*.01+.001&&G.Projectiles.all().includes(shot),'remote erase or excessive speed');
 for(let i=0;i<15;i++){p.y+=1;const x=s.x,y=s.y;A.guardStep();A.assert(Math.hypot(s.x-x,s.y-y)<=s.speed*.01+.001,'moving-owner cloud exceeded speed')}
 A.assert(s.target===shot,'moving owner stopped pursuit');out.movingOwner={phase:s.phase,nativeSpeed:190,nativeLife:2.4};
 s=A.isolate();s.x=-150;shot=A.nativeShot(120,0);hp=p.hp;A.guardStep();A.assert(s.target===shot&&s.x>-150,'impossible arrival suppressed pursuit');A.untilGone(shot,1);
 A.assert(p.hp<hp&&s.ready,'late cloud saved earlier impact');out.lateDamage=hp-p.hp;
 s=A.isolate();s.x=130;s.y=80;shot=A.nativeShot(200,80);hp=p.hp;const seconds=A.untilGone(shot,1);
 A.assert(!G.Projectiles.all().includes(shot)&&!s.ready&&p.hp===hp,'physical native contact failed');out.physicalEraseSeconds=seconds;
 // Two independent native shots, two independently assigned physical clouds.
 let g=A.guardReset();g.guardians.forEach((c,i)=>{c.x=130;c.y=(i-1)*100});
 const q1=A.nativeShot(260,-100),q2=A.nativeShot(260,100);A.guardStep(.01);
 const targets=g.guardians.filter(c=>c.target).map(c=>c.target);
 A.assert(targets.includes(q1)&&targets.includes(q2)&&new Set(targets).size===targets.length,'multiple clouds share target or fail parallel pursuit');
 A.assert(g.guardians[0].target===q1&&g.guardians[2].target===q2,'distant guardian stole a closer guardian target');
 A.assert(G.Projectiles.all().includes(q1)&&G.Projectiles.all().includes(q2),'parallel clouds erased remotely');
 for(let i=0;i<100&&(G.Projectiles.all().includes(q1)||G.Projectiles.all().includes(q2));i++)A.guardStep();
 A.assert(!G.Projectiles.all().includes(q1)&&!G.Projectiles.all().includes(q2)&&g.guardians.filter(c=>!c.ready).length===2,'parallel contacts did not consume exactly two clouds '+JSON.stringify({shots:[q1,q2].map(q=>({x:q.x,y:q.y,remaining:G.Projectiles.all().includes(q)})),clouds:g.guardians.map(c=>({x:c.x,y:c.y,target:c.target?.id,ready:c.ready,heading:c.heading}))}));
 const remaining=g.guardians.find(c=>c.ready);const q3=A.nativeShot(remaining.x+80,remaining.y);A.guardStep();A.assert(remaining.target===q3,'cooling clouds stalled remaining guardian');
 out.parallel=true;
 g=A.guardReset();g.guardians.forEach((c,i)=>{c.x=30+i*40;c.y=80});
 const cluster=[A.shot({x:220,y:80,vx:-30}),A.shot({x:230,y:85,vx:-30}),A.shot({x:240,y:90,vx:-30})];
 A.guardStep(.01);const assigned=g.guardians.map(c=>c.target);
 A.assert(assigned.every(q=>cluster.includes(q))&&new Set(assigned).size===3,'clustered shots left available guardians idle');
 return out;
}"""

COMBAT = r"""() => {
 const A=Acceptance,p=A.p(),out={};let s=A.isolate();
 const wall=G.World.isWall,block=G.World.projectileBlock;
 for(const [name,o] of Object.entries({friendly:{friendly:true},range:{x:600},unblockable:{unblockable:true},beam:{beam:true},ground:{ground:true}})){s=A.isolate();const q=A.shot(o);A.guardStep(.01);A.assert(s.target!==q&&s.ready,'invalid target '+name)}out.invalidTargets=true;
 for(const o of [{y:140,vx:0,vy:90},{vx:90}]){s=A.isolate();const q=A.shot(o);A.guardStep();A.assert(s.target===q&&G.Projectiles.all().includes(q),'nearby hostile ignored')}
 s=A.isolate();s.x=28;let terrainCalls=0;
 G.World.isWall=(x,y)=>{terrainCalls++;return x>65&&x<80};G.World.projectileBlock=(x,y)=>{terrainCalls++;return x>65&&x<80?'wall':false};
 try{const q=A.shot();A.guardStep();A.assert(s.target===q,'guardian failed to acquire across wall');out.wallAcquisition=true}finally{G.World.isWall=wall;G.World.projectileBlock=block}
 s=A.isolate();s.x=180;s.y=0;s.heading=Math.PI;A.spend(s);let steps=0,crossedWall=false;
 const corner=(x,y)=>x>=65&&x<=85&&y>=-45&&y<=45;
 G.World.isWall=(x,y)=>{terrainCalls++;return corner(x,y)};G.World.projectileBlock=(x,y)=>{terrainCalls++;return corner(x,y)?'wall':false};terrainCalls=0;
 try{for(;steps<800;steps++){const x=s.x,y=s.y;A.guardStep();A.assert(Math.hypot(s.x-x,s.y-y)<=s.speed*.01+.001,'return teleported or exceeded speed');crossedWall ||= corner(s.x,s.y);if(Math.hypot(s.x-p.x,s.y-p.y)>40)A.assert(!s.ready&&s.rechargeProgress===0,'reformed far from owner');if(s.rechargeProgress>0)break}A.assert(crossedWall&&steps<800,'guardian did not phase through wall on return');A.assert(terrainCalls===0,'guardian return queried terrain '+terrainCalls)}finally{G.World.isWall=wall;G.World.projectileBlock=block}out.wallPhasing={seconds:steps/100,crossedWall,terrainCalls};
 // Each cloud reforms independently; a second spent cloud starts later.
 let g=A.guardReset(),a=g.guardians[0],b=g.guardians[1];A.spend(a);a.x=a.y=0;A.advanceGuard(1);A.spend(b);b.x=b.y=0;A.advanceGuard(1.51);
 A.assert(a.ready&&!b.ready&&b.rechargeProgress>0,'clouds did not recharge independently');A.advanceGuard(1.01);A.assert(b.ready,'second cloud never reformed');out.independentRecharge=true;
 g=A.guardReset();a=g.guardians[0];A.spend(a);a.x=a.y=0;p.cdMul=.5;A.advanceGuard(1.24);A.assert(!a.ready,'cooldown recharge early');A.advanceGuard(.02);A.assert(a.ready,'cooldown card ignored');p.cdMul=1;
 s=A.isolate();s.x=-180;s.y=0;let q=A.shot({x:80,vx:-4000}),hp=p.hp;A.guardStep(.02);A.assert(p.hp<hp&&s.ready,'retroactive highspeed rescue');
 s=A.isolate();s.x=110;s.y=0;q=A.shot({x:200,vx:-2000});hp=p.hp;A.guardStep(.1);A.assert(!G.Projectiles.all().includes(q)&&!s.ready&&p.hp===hp,'swept physical contact failed');out.swept=true;
 g=A.guardReset();hp=p.hp;const hazard=G.Hazards.add({kind:'zone',x:0,y:0,r:40,delay:0,dmg:17,pure:true,color:'#fff'});A.resume();try{G.Hazards.update(.01)}finally{A.pause()}A.assert(hazard.hit&&p.hp<hp&&g.guardians.every(c=>c.ready),'ground hazard intercepted');G.Hazards.clear?.();out.hazards=true;return out;
}"""

TIERS = r"""() => {
 const A=Acceptance,p=A.p(),id=A.guardId,out=[];
 for(let tier=1;tier<=5;tier++){
  if(tier>1){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(card&&card.apply(p)!==false,'missing upgrade '+tier)}
  const g=A.guardReset(),expected=[2,2,3,3,4][tier-1]+1;A.assert(g.count===expected&&g.guardians.length===expected&&g.readyCount===expected,'wrong physical count '+tier);
  A.assert(g.guardians.every(c=>c.speed===p.spd+200&&c.range===400&&c.ready),'per-cloud fixed stats');
  for(let i=0;i<g.guardians.length;i++)for(let j=i+1;j<g.guardians.length;j++)A.assert(Math.hypot(g.guardians[i].x-g.guardians[j].x,g.guardians[i].y-g.guardians[j].y)>1,'clouds overlap spawn');out.push({tier,count:g.count});
 }
 for(const level of [1,7,20,36,37,38,40,100])for(let tier=1;tier<=5;tier++){p.level=level;p.moves.find(m=>m.id===id).lvl=tier;const g=A.guardReset();A.assert(g.count===Math.min(40,[2,2,3,3,4][tier-1]+level),'growth count')}
 p.level=1;p.moves.find(m=>m.id===id).lvl=1;let g=A.guardReset(),first=g.guardians[0];A.spend(first);first.rechargeProgress=.4;const old=g.guardians.slice();p.level=4;g=A.guard();A.assert(g.count===6&&old.every((c,i)=>g.guardians[i]===c)&&!first.ready&&first.rechargeProgress===.4,'growth reset existing clouds');p.level=100;g=A.guard();A.assert(g.count===40&&g.guardians.length===40&&!first.ready,'cap or spent state wrong');p.quantityBonus=20;A.assert(A.guard().count===40,'quantity exceeded cap');p.level=1;p.quantityBonus=2;A.assert(A.guard().count===5,'quantity did not add guardians');p.level=100;p.quantityBonus=0;g=A.guard();
 const index=p.activeSlot;p.setActive(0);A.assert(A.guard()===g&&!first.ready,'slot switch reset passive');p.setActive(index||0);p.moves.find(m=>m.id===id).lvl=5;
 A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='up:'+id),'tier six offered');
 p.level=15;for(const skill of ['naruto-sand-coffin','naruto-sand-tsunami','naruto-sand-prison','naruto-sand-armor']){const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+skill);A.assert(card&&card.apply(p)!==false,'full-slot fixture '+skill)}
 A.assert(p.slots.length===5,'full-slot fixture wrong');const moves=p.moves;p.moves=p.moves.filter(m=>m.id!==id);const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false&&p.slots.length===5&&p.hasMove(id),'full slots prevent passive learning');p.moves=moves;return out;
}"""

TURNING = r"""() => {
 const A=Acceptance,p=A.p(),tracks={};
 const angle=(a,b)=>Math.abs(Math.atan2(Math.sin(a-b),Math.cos(a-b)));
 const record=(name,s,steps,change=()=>{})=>{
  const track=tracks[name]=[{x:s.x,y:s.y,heading:s.heading}],dt=.01;
  let previous=null,maxTurn=0;
  for(let i=0;i<steps;i++){
   change(i);const x=s.x,y=s.y,heading=s.heading;A.guardStep(dt);
   const dx=s.x-x,dy=s.y-y,length=Math.hypot(dx,dy);
   A.assert(length<=s.speed*dt+1e-7,'turning exceeded speed '+name);
   A.assert(angle(heading,s.heading)<=3.6*dt+1e-7,'heading jumped '+name);
   if(length>1e-6){const next=Math.atan2(dy,dx);if(previous!==null){const turn=angle(next,previous);maxTurn=Math.max(maxTurn,turn);A.assert(turn<=3.6*dt+1e-6,'trajectory right angle '+name)}previous=next}else previous=null;
   track.push({x:s.x,y:s.y,heading:s.heading,phase:s.phase,ready:s.ready});
  }
  track.maxTurn=maxTurn;
 };
 let s=A.isolate();s.x=100;s.y=0;s.heading=0;
 let q=A.shot({x:260,y:0,vx:0,vy:0});
 record('retarget-90',s,70,i=>{if(i===15){q.x=s.x;q.y=s.y+160;q.px=q.x;q.py=q.y}});
 A.assert(tracks['retarget-90'].some(c=>c.y>5),'90 turn never curved');
 s=A.isolate();s.x=100;s.y=0;s.heading=0;q=A.shot({x:260,y:0,vx:0,vy:0});
 record('retarget-180',s,120,i=>{if(i===15){q.x=s.x-180;q.y=s.y;q.px=q.x;q.py=q.y}});
 A.assert(s.x<110,'180 turn never reversed');
 s=A.isolate();s.x=100;s.y=0;s.heading=0;
 // Idle nodes follow a shared physical flow aim; move its owner rather than
 // writing the retired per-cloud waypoint to exercise a genuine new aim.
 record('wander-waypoint',s,150,i=>{if(i===20)p.y+=150});
 A.assert(s.y>30,'wander turn never curved');
 const old=s.heading;G.Combat.resolve(.5,p,0);A.assert(s.heading===old,'pause rotated heading');
 const wall=G.World.isWall,block=G.World.projectileBlock;
 s=A.isolate();s.x=180;s.y=0;s.heading=0;A.spend(s);
 const corner=(x,y)=>x>=65&&x<=85&&y>=-45&&y<=45;
 G.World.isWall=corner;G.World.projectileBlock=(x,y)=>corner(x,y)?'wall':false;
 try{record('return-through-wall',s,1100);A.assert(tracks['return-through-wall'].some(c=>corner(c.x,c.y)),'curved guardian return did not pass through wall');A.assert(tracks['return-through-wall'].some(c=>c.phase==='recharge')&&s.ready,'curved return failed to recharge')}finally{G.World.isWall=wall;G.World.projectileBlock=block}
 return tracks;
}"""

CLEANUP = r"""() => {
 const A=Acceptance,p=A.p(),id=A.guardId,out=[];let s=A.guardReset();const snapshot=JSON.stringify(A.snapshot());
 G.Combat.resolve(.5,p,0);A.assert(JSON.stringify(A.snapshot())===snapshot,'pause advanced guard');out.push('pause');
 for(const reason of ['clear','death','world','owner','unlearn']){
  const previous=A.guardReset(),world=G.World,game=G.Game,moves=p.moves;
  if(reason==='clear')G.Combat.clearFields(p);if(reason==='death')p.dead=true;
  if(reason==='world')G.World={...world};if(reason==='owner')G.Game={...game,player:{...p}};
  if(reason==='unlearn')p.moves=p.moves.filter(m=>m.id!==id);
  try{const current=A.guard();A.assert(['clear','world'].includes(reason)?current!==previous:!current,'stale guard after '+reason)}finally{G.World=world;G.Game=game;p.moves=moves;p.dead=false}out.push(reason);
 }A.guardReset();G.Game.startRun();A.pause();A.assert(G.Game.player!==p&&!G.NarutoSandGuard.state(p)&&!G.NarutoSandGuard.state(G.Game.player),'new run leaked passive');out.push('new-run');return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'failedRequests': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in [False, True]:
                label = 'mobile' if mobile else 'desktop'
                context = browser.new_context(locale='zh-TW', viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('response', lambda r: report['failedRequests'].append(r.url) if r.status >= 400 and '127.0.0.1' in r.url else None)
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.NarutoSandGuard && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                for setup in [HARNESS, SETUP, FIXTURE]: page.evaluate(setup)
                result = report['viewports'][label] = {}
                for name, script in [('progression', PROGRESSION), ('speed', SPEED), ('native', NATIVE), ('combat', COMBAT), ('turning', TURNING), ('tiers', TIERS)]: result[name] = page.evaluate(script)
                tracks = result['turning']
                (OUT / f'{label}-turn-tracks.json').write_text(json.dumps(tracks, indent=2), 'utf-8')
                page.evaluate(r"""tracks=>{
                  const c=document.createElement('canvas');c.id='guard-turn-tracks';c.width=1000;c.height=1000;c.style='position:fixed;inset:0;z-index:99999;width:100vw;height:100vh;background:#17221c';document.body.append(c);
                  const ctx=c.getContext('2d');let panel=0;
                  for(const [name,points] of Object.entries(tracks)){
                    const ox=(panel%2)*500,oy=Math.floor(panel/2)*500;panel++;
                    ctx.fillStyle='#eee8d7';ctx.font='20px sans-serif';ctx.fillText(name,ox+20,oy+30);
                    const xs=points.map(p=>p.x),ys=points.map(p=>p.y),minX=Math.min(...xs)-20,minY=Math.min(...ys)-20;
                    const scale=Math.min(440/(Math.max(...xs)-minX+20),400/(Math.max(...ys)-minY+20));
                    ctx.strokeStyle='#d4cdbb';ctx.lineWidth=3;ctx.beginPath();points.forEach((p,i)=>{const x=ox+20+(p.x-minX)*scale,y=oy+60+(p.y-minY)*scale;i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke();
                    points.forEach((p,i)=>{if(i%10)return;ctx.fillStyle=i?'#aaa28e':'#fc8566';ctx.beginPath();ctx.arc(ox+20+(p.x-minX)*scale,oy+60+(p.y-minY)*scale,i?3:6,0,Math.PI*2);ctx.fill()});
                  }
                }""", tracks)
                page.locator('#guard-turn-tracks').screenshot(path=str(OUT / f'{label}-turn-tracks.png'))
                page.evaluate("document.getElementById('guard-turn-tracks').remove()")
                # Each guardian fixture depletes HP absorption while keeping the merged skill learned.
                for stage, script in [
                    ('three-clouds', "Acceptance.p().level=1;Acceptance.p().moves.find(m=>m.id===Acceptance.guardId).lvl=1;Acceptance.guardReset();Acceptance.advanceGuard(.7)"),
                    ('forty-clouds', "Acceptance.p().level=100;Acceptance.guardReset();Acceptance.advanceGuard(1)"),
                    ('parallel-pursuit', "Acceptance.p().level=1;Acceptance.guardReset();Acceptance.guard().guardians.forEach((c,i)=>{c.x=100;c.y=(i-1)*100;c.heading=0});window.guardShots=[Acceptance.nativeShot(260,-100),Acceptance.nativeShot(260,100)];Acceptance.guardStep(.12)"),
                    ('parallel-contact', "for(let n=0;n<100&&window.guardShots.some(q=>G.Projectiles.all().includes(q));n++)Acceptance.guardStep()"),
                    ('mixed-return-reform', "G.Projectiles.clear();const s=Acceptance.guard().guardians.find(c=>!c.ready);s.x=0;s.y=0;Acceptance.guardStep(.1)"),
                    ('native-late-impact', "const s=Acceptance.isolate();s.x=-150;s.y=0;const q=Acceptance.nativeShot(120,0);Acceptance.untilGone(q,1)"),
                ]:
                    page.evaluate(script)
                    state = page.evaluate('Acceptance.snapshot()')
                    if stage == 'three-clouds': assert state['count'] == 3
                    elif stage == 'forty-clouds': assert state['count'] == 40
                    elif stage == 'parallel-pursuit': assert sum(s['target'] for s in state['guardians']) == 2
                    elif stage == 'parallel-contact': assert sum(not s['ready'] for s in state['guardians']) == 2
                    elif stage == 'native-late-impact': assert state['hp'] < state['maxHp']
                    page.wait_for_timeout(70)
                    page.locator('#game').screenshot(path=str(OUT / f'{label}-{stage}.png'))
                    result.setdefault('visualStages', {})[stage] = state
                result['cleanup'] = page.evaluate(CLEANUP)
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        assert not report['failedRequests'], report['failedRequests']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))

if __name__ == '__main__': main()
