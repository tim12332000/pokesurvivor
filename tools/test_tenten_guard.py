"""Guard acceptance through native progression, actors, bullets and rendering.

Only arena terrain is controlled. Run against the repository server on 8004.
Evidence is kept outside authored assets in .omx/state/tenten-guard.
"""
import base64
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_tenten import CHROME, HARNESS, SETUP, AUDIT

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('TENTEN_GUARD_OUT', str(ROOT / '.omx/state/tenten-guard')))
URL = os.environ.get('TENTEN_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=tenten-guard')

SETUP_GUARD = r"""() => {
 const A=Acceptance,p=A.p();
 A.guardID='naruto-tenten-guard';
 A.guardReset=()=>{A.reset();p.spdMul=1;p.cdMul=1;p.buffs.spd={n:0,t:0,amount:0};};
 A.guardStep=(dt=.01)=>{A.resume();try{G.Combat.updateFields(dt);p.anim.update(dt)}finally{A.pause()}};
 A.guardFinish=seconds=>{for(let t=0;t<seconds-1e-7;t+=.01)A.guardStep(Math.min(.01,seconds-t))};
 A.guard=()=>G.NarutoTenten.guardFor(p);
 A.guardTrigger=()=>{A.spawn(60,0);A.guardStep(.001);for(let i=0;i<11&&A.guard()?.phase!=='prepare';i++)A.guardStep(.01);A.assert(A.guard()?.phase==='prepare','proximity did not prepare guard')};
 A.guardRank=rank=>{p.moves=p.moves.filter(m=>m.id!==A.guardID);p.moves.push(G.Moves.instance(A.guardID,rank));};
 A.guardReset();
}"""

PROGRESSION = r"""() => {
 const A=Acceptance,p=A.p(),id=A.guardID,out=[];
 p.level=3;A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='new:'+id),'guard before Lv4');
 p.level=4;p.maxMoves=0;const slots=p.slots.length,c=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
 A.assert(c&&c.apply(p)!==false,'guard cannot learn with full active slots');
 A.assert(p.hasMove(id)&&p.moves.find(m=>m.id===id).passive&&p.slots.length===slots,'guard used active slot');
 for(let rank=1;rank<=5;rank++){
   if(rank>1){const up=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(up&&up.apply(p)!==false,'full-slot guard upgrade '+rank)}
   A.assert(p.moves.find(m=>m.id===id).lvl===rank&&p.slots.length===slots,'guard rank/slot '+rank);out.push(rank);
 }
 A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='up:'+id),'guard exceeded max rank');p.maxMoves=6;
 p.level=12;for(const mid of ['naruto-tenten-bounce','naruto-tenten-fuma','naruto-tenten-mastery','naruto-tenten-tags','naruto-tenten-twin']){
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+mid);A.assert(card&&card.apply(p)!==false,'active fixture learn '+mid)}
 A.select('naruto-tenten-fuma');return {ranks:out,slots:p.slots.length};
}"""

RADIAL = r"""() => {
 const A=Acceptance,p=A.p(),out=[];
 for(let rank=1;rank<=5;rank++){
   A.guardReset();A.guardRank(rank);const radius=90+rank*10,knock=60+rank*10;
   const es=[A.spawn(60,0),A.spawn(0,60),A.spawn(-60,0),A.spawn(0,-radius-15),A.spawn(45,45,true),A.spawn(-40,-40)];
   const block=G.World.projectileBlock;G.World.projectileBlock=(x,y)=>x< -8&&y< -8?{destructible:false}:false;
   try{
     const before=es.map(e=>[e.x,e.y,e.hp]);A.guardStep(.001);const s=A.guard();
     A.assert(s?.phase==='prepare'&&s.tools===8,'guard prepare/tools');A.near(s.radius,radius,'rank radius');A.near(s.knock,knock,'rank knock');
     A.guardFinish(.10);A.assert(es.every((e,i)=>e.x===before[i][0]&&e.y===before[i][1]),'guard swept during preparation');
     A.guardFinish(.03);A.assert(A.guard()?.phase==='sweep','sweep phase absent');
     es.forEach((e,i)=>{const moved=Math.hypot(e.x-before[i][0],e.y-before[i][1]);
       A.assert(i<3?moved>knock-1e-6&&moved<=knock+1e-6:moved===0,'radial target membership '+rank+'/'+i+' distance '+moved);
       A.assert(e.hp===before[i][2],'guard dealt damage '+i)});
     const swept=es.map(e=>[e.x,e.y]);A.guardFinish(.3);A.assert(es.every((e,i)=>e.x===swept[i][0]&&e.y===swept[i][1]),'sweep repeated');
     out.push({rank,radius,knock,moved:es.map((e,i)=>Math.hypot(e.x-before[i][0],e.y-before[i][1]))});
   }finally{G.World.projectileBlock=block}
 }
 for(const key of ['elite','legend','judge']){A.guardReset();const e=A.spawn(60,0);e[key]=true;A.guardStep(.001);A.guardFinish(.13);A.assert(e.x===60&&e.y===0&&e.hp===100000,'immune '+key)}
 A.guardReset();A.spawn(81,0);A.guardStep(.01);A.assert(A.guard()?.ready,'trigger exceeded center radius80');
 A.guardReset();A.spawn(60,0);const block=G.World.projectileBlock;G.World.projectileBlock=()=>({destructible:false});
 try{A.guardStep(.01);A.assert(A.guard()?.ready,'guard triggered through wall')}finally{G.World.projectileBlock=block}
 A.guardReset();const same=A.spawn(0,0);A.guardStep(.001);A.guardFinish(.13);A.assert(Number.isFinite(same.x)&&Number.isFinite(same.y)&&Math.hypot(same.x,same.y)>0,'same-origin push invalid');
 A.guardReset();const e=A.spawn(60,0),free=G.World.isFree;let calls=0;
 G.World.isFree=(x,y)=>{calls++;return x<=80};
 try{A.guardStep(.001);A.guardFinish(.13);A.assert(calls>0&&e.x<=80,'push bypassed native terrain collision')}finally{G.World.isFree=free}
 return out;
}"""

SHOTS = r"""() => {
 const A=Acceptance,p=A.p();A.guardReset();const defs=[{}, {friendly:true},{orb:true},{special:true},{unblockable:true},{beam:true},{groundField:true},{bossSpecial:true},{x:250},{x:-50,y:-50},{interceptable:undefined}];
 const shots=defs.map(d=>G.Projectiles.spawn({x:50,y:25,life:50,vx:0,vy:0,friendly:false,interceptable:true,...d}));
 const ordinary=A.spawn(50,0),boss=A.spawn(50,0,true);ordinary.shoot(1,0);boss.ai={cast:{id:'nova'}};boss.shoot(1,0);
 const nativeShots=G.Projectiles.all().slice(-2);A.assert(nativeShots[0].interceptable===true&&nativeShots[1].interceptable===false,'native shot provenance missing');
 const block=G.World.projectileBlock;G.World.projectileBlock=(x,y)=>x< -8&&y< -8?{destructible:false}:false;
 try{A.guardTrigger();A.guardFinish(.13);const retained=shots.map(s=>G.Projectiles.all().includes(s));
   A.assert(retained.join(',')===[false,true,true,true,true,true,true,true,true,true,true].join(','),'ordinary/special bullet membership '+retained);
   A.assert(!G.Projectiles.all().includes(nativeShots[0])&&G.Projectiles.all().includes(nativeShots[1]),'native ordinary/boss special classification');return {retained,nativeOrdinary:true,bossSpecialRetained:true};
 }finally{G.World.projectileBlock=block}
}"""

TIMING = r"""() => {
 const A=Acceptance,p=A.p(),out=[];
 for(let rank=1;rank<=5;rank++){
   A.guardReset();A.guardRank(rank);p.spdMul=1.3;p.buffs.spd={n:2,t:9,amount:.1};const speed=p.spd,buff=JSON.stringify(p.buffs.spd);
   A.guardTrigger();A.near(p.spd,speed,'prepare granted early boost');A.guardFinish(.13);
   A.near(A.guard().speedBonus,[.15,.20,.25,.30,.35][rank-1],'rank boost');A.near(p.spd,speed*(1+[.15,.20,.25,.30,.35][rank-1]),'boost speed');
   A.guardFinish(1.45);A.assert(p.spd>speed,'boost ended early');A.guardFinish(.08);A.near(p.spd,speed,'boost did not expire');
   A.assert(p.spdMul===1.3&&JSON.stringify(p.buffs.spd)===buff,'guard modified existing speed buff/card');out.push({rank,speed});
 }
 for(const [mul,expected] of [[1,8],[.75,6],[.01,3]]){
   A.guardReset();p.cdMul=mul;A.guardTrigger();const remaining=A.guard().cooldownRemaining;
   A.assert(Math.abs(remaining-expected)<.03,'cooldown modifier/floor '+remaining+'/'+expected);
   A.guardFinish(expected-.05);A.assert(!A.guard().ready,'cooldown ready early');
   G.EnemyMgr.clear();A.guardFinish(.08);A.assert(A.guard().ready,'cooldown did not become ready');out.push({mul,remaining});
 }
 A.guardReset();A.guardTrigger();A.guardFinish(.13);const s=A.guard(),age=s.age,cd=s.cooldownRemaining,speed=p.spd;
 G.Combat.updateFields(.5);A.assert(A.guard().age===age&&A.guard().cooldownRemaining===cd&&p.spd===speed,'pause advanced guard');
 A.guardReset();const e=A.spawn(60,0);A.guardStep(.001);A.guardFinish(.05);const preparing=A.guard(),frozenAge=preparing.age,frozenCD=preparing.cooldownRemaining;
 p.frozen=true;A.guardStep(.5);const cv=document.createElement('canvas'),ctx=cv.getContext('2d');G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);
 A.near(A.guard().age,frozenAge,'frozen prepare age');A.near(A.guard().cooldownRemaining,frozenCD,'frozen cooldown');
 A.assert(e.x===60&&e.y===0&&A.guard().boostRemaining===0,'frozen prepare swept');p.frozen=false;A.guardFinish(.08);
 A.assert(e.x>60&&A.guard().pushed===1,'thawed prepare did not sweep exactly once');const sweptX=e.x;A.guardFinish(.2);A.assert(e.x===sweptX,'thawed guard repeated sweep');
 const beforeBoost=A.guard().boostRemaining,boostSpeed=p.spd;p.frozen=true;A.guardStep(.8);
 A.near(A.guard().boostRemaining,beforeBoost,'frozen boost expired');A.near(p.spd,boostSpeed,'frozen boost multiplier lost');
 p.frozen=false;A.guardFinish(beforeBoost+.03);A.assert(A.guard().boostRemaining===0&&G.NarutoTenten.speedMultiplier(p)===1,'thawed boost did not expire');
 out.push({freezePrepare:true,freezeBoost:true});return out;
}"""

INDEPENDENCE = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,out={};
 for(const quantity of [0,20]){A.guardReset();p.quantityPicks=p.quantityBonus=quantity;A.guardTrigger();A.guardFinish(.13);
   A.assert(A.guard().tools===8&&!T.weapons.length&&!G.Projectiles.all().length,'guard quantity generated projectiles');}
 A.guardReset();p.target=A.spawn(60,0);const twin=p.moves.find(m=>m.id==='naruto-tenten-twin');A.select(twin.id);
 T.cast(p,{...twin,quantityBonusAtCast:0,quantityMultiplierAtCast:1});const pose=T.activeFor(p);A.guardStep(.001);A.guardFinish(.13);
 A.assert(T.activeFor(p)===pose&&pose.emitted>0&&A.guard().phase==='sweep','guard replaced concurrent twin');out.concurrent=true;
 A.guardReset();p.spdMul=1.25;A.guardTrigger();A.guardFinish(.13);const boosted=p.spd;
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');A.assert(card,'clone card absent');card.apply(p);card.apply(p);
 const [a,b]=G.SelfClones.actors();A.assert(a&&b,'clone actors absent');a.x=1000;a.y=0;b.x=2000;b.y=0;
 A.near(a.spd,p.spd/(1+A.guard().speedBonus),'clone inherited temporary boost');A.near(a.spd,b.spd,'clone baseline differs');
 const baseline=a.spd;A.spawn(a.x+60,0);A.guardStep(.001);A.guardFinish(.13);
 A.near(a.spd,baseline*(1+T.guardFor(a).speedBonus),'clone boost double multiplier');A.near(b.spd,baseline,'sibling boost leaked');
 A.near(p.spd,boosted,'clone changed owner speed');G.Combat.clearFields(a);A.near(a.spd,baseline,'clone boost not cleared');A.assert(T.guardFor(b),'sibling state cleared');out.clones=true;
 for(const reason of ['clear','death','world','role']){
   A.guardReset();const original=p.spd;A.guardTrigger();A.guardFinish(.13);const world=G.World,dex=p.dex,mon=p.mon;
   if(reason==='clear')G.Combat.clearFields(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};
   if(reason==='role'){p.dex=30001;p.mon=G.DEX.find(m=>m.dex===30001)}
   try{A.guardStep(.01);A.near(p.spd,original,'cleanup boost leaked '+reason);const current=T.guardFor(p);
     A.assert(reason==='clear'?(!current||(current.ready&&current.boostRemaining===0&&current.activations===0)):!current,'guard state survived '+reason)}
   finally{p.dead=false;G.World=world;p.dex=dex;p.mon=mon}
 }
 A.guardReset();A.guardTrigger();A.guardFinish(.13);G.Combat.clearFields();A.assert(!T.guardFor(p),'scene clear kept guard');out.cleanup=true;return out;
}"""

PRESENT = r"""phase => {
 const A=Acceptance,p=A.p();A.guardReset();A.guardRank(3);p.aim=0;p.anim.dir=2;A.guardTrigger();
 if(phase==='sweep')A.guardFinish(.24);if(phase==='escape')A.guardFinish(.60);
 A.assert(A.guard().phase===phase,'capture phase '+phase+' actual '+A.guard().phase);
 G.UI.hide('ach-pop');document.querySelectorAll('.toast').forEach(el=>el.style.display='none');
 const cv=document.createElement('canvas');cv.width=innerWidth;cv.height=innerHeight;const ctx=cv.getContext('2d'),labels=[],fill=ctx.fillText.bind(ctx);
 ctx.fillText=(t,...args)=>{labels.push(String(t));return fill(t,...args)};G.HUD.draw(ctx,innerWidth,innerHeight,p,{time:20});
 const expected={prepare:'展卷',sweep:'護身',escape:'疾退 1.0s'}[phase];
 A.assert(labels.some(t=>phase==='escape'?t.startsWith('疾退 '):t===expected),'guard HUD phase label '+phase+' '+labels.join('|'));
 const pose=A.render();if(phase!=='escape')A.assert(pose.state.key==='tenten-mastery'&&pose.state.id===A.guardID,'guard authored scroll pose absent');
 return {phase,labels,actor:pose,tools:A.guard().tools};
}"""

HUD = r"""() => {
 const A=Acceptance,p=A.p();A.guardReset();A.guardStep(.001);
 const cv=document.createElement('canvas');cv.width=innerWidth;cv.height=innerHeight;const ctx=cv.getContext('2d'),labels=[],fill=ctx.fillText.bind(ctx);
 ctx.fillText=(t,...args)=>{labels.push(String(t));return fill(t,...args)};
 G.HUD.draw(ctx,innerWidth,innerHeight,p,{time:20});A.assert(labels.includes('就緒'),'ready HUD missing '+labels);
 labels.length=0;A.guardTrigger();A.guardFinish(2);G.HUD.draw(ctx,innerWidth,innerHeight,p,{time:20});
 A.assert(labels.some(t=>t.startsWith('冷卻 ')),'cooldown HUD missing '+labels);return {ready:true,cooldown:labels.filter(t=>t.startsWith('冷卻 '))};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'errors': [], 'failedRequests': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for label, size, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
                context = browser.new_context(viewport=size, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('response', lambda r: report['failedRequests'].append(r.url) if r.status >= 400 and '127.0.0.1' in r.url else None)
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30009"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30009 && G.Game.state==="playing"')
                for setup in [HARNESS, SETUP, AUDIT, SETUP_GUARD]:
                    page.evaluate(setup)
                result = report['viewports'][label] = {}
                for name, check in [('progression', PROGRESSION), ('radial', RADIAL), ('shots', SHOTS), ('timing', TIMING), ('independence', INDEPENDENCE), ('hud', HUD)]:
                    print(label, name, flush=True)
                    result[name] = page.evaluate(check)
                page.evaluate('Acceptance.guardReset();Acceptance.guardTrigger();Acceptance.guardFinish(.13)')
                page.keyboard.down('KeyD')
                try:
                    result['guardMovement'] = page.evaluate('''() => {const A=Acceptance,p=A.p(),x=p.x,speed=p.spd;A.resume();p.update(.08);A.pause();
                      A.assert(p.x>x&&p.walking&&A.guard()?.boostRemaining>0,'guard prevented native movement');return {distance:p.x-x,speed}}''')
                finally:
                    page.keyboard.up('KeyD')
                result['presentation'] = {}
                for phase in ['prepare', 'sweep', 'escape']:
                    print(label, 'capture', phase, flush=True)
                    capture = page.evaluate(PRESENT, phase)
                    actor = capture['actor']
                    assert actor['sources'] and all('tenten' in source for source in actor['sources']), actor
                    (OUT / f'{label}-{phase}-actor.png').write_bytes(base64.b64decode(actor.pop('png').split(',', 1)[1]))
                    result['presentation'][phase] = capture
                    page.screenshot(path=str(OUT / f'{label}-{phase}.png'))
                result['overflow'] = page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert result['overflow'], 'horizontal overflow'
                result['freshRun'] = page.evaluate('''() => {const A=Acceptance,old=A.p();G.Game.toUI();G.Naruto.choose(30009);G.Flow.play();A.pause();
                  A.assert(G.Game.player!==old&&!G.NarutoTenten.guardFor(old)&&!G.Game.player.hasMove(A.guardID),'guard leaked into fresh run');return true}''')
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        assert not report['failedRequests'], report['failedRequests']
        report['ok'] = True
    except Exception as error:
        report['ok'] = False
        report['failure'] = str(error)
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
