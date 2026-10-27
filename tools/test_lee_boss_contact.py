"""Real boss contact, movement, damage and retreat acceptance for Rock Lee."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

OUT = Path(__file__).resolve().parents[1] / '.omx/state/lee-boss-contact'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=lee&layout=wide'

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),L=G.NarutoLee,P=G.NarutoPursuit,assert=A.assert,ids=['naruto-lotus','naruto-reverse-lotus'];
 p.level=12;for(const id of [...ids,'naruto-lee-pursuit'])if(!p.hasMove(id))p.addMove(id);
 function fixture(id='naruto-lotus',x=160,radius=35,kind='boss'){
   A.leeArena();p.quantityPicks=p.quantityBonus=0;p.cdMul=1;
   const m=p.moves.find(m=>m.id===id);Object.assign(m,G.Moves.instance(id,1));m.t=0;
   for(const move of p.moves)if(move!==m)move.t=999;
   if(id!=='naruto-lee-pursuit')A.select(id);
   const e=A.spawn(x,0);e.r=radius;e[kind]=true;e.maxHp=e.hp=100000;e.kx=e.ky=0;
   const minion=A.spawn(25,0);p.target=minion;p.aim=0;G.EnemyMgr.rebuildGrid();
   const hits=[],hurt=e.hurt;e.hurt=function(...args){
     hits.push({damage:args[0],owner:args[6]===p,id:args[7],distance:Math.hypot(e.x-p.x,e.y-p.y),x:p.x,y:p.y});
     assert(Math.hypot(e.x-p.x,e.y-p.y)<=(p.r||12)+e.r+36+.001,'remote boss hit beyond physical contact');
     assert(!G.World.isWall((p.x+e.x)/2,(p.y+e.y)/2),'boss hit through wall');
     return hurt.apply(this,args);
   };return {m,e,minion,hits};
 }
 function step(dt=.005,speed=0,e=null){
   if(e){e.x+=speed*dt;G.EnemyMgr.rebuildGrid();}
   const x=p.x,y=p.y;A.advance(dt);
   assert(Math.hypot(p.x-x,p.y-y)<=1000*dt+.001,'contact chase teleported');
 }
 const cases=[],baselines={};
 for(const id of ids)for(const [kind,speed,radius,start] of [['boss',0,35,160],['boss',350,35,160],['legend',250,80,320],['judge',200,35,180]]){
   const q=fixture(id,start,radius,kind);A.actualCast(id);const f=L.activeFor(p);
   assert(f?.target===q.e&&!f.pullable,'near minion stole boss target or boss became pullable');
   let maxDistance=0,frames=0,groundFrames=0;
   while(L.activeFor(p)&&frames++<1000){
     const old=q.e.x;step(.005,speed,q.e);
     assert(q.e.x===old+speed*.005,'Lotus forcibly moved boss');
     assert(!L.liftFor(q.e)&&!q.e.jumpLift&&!f.visualLift,'boss was floated');
     assert(!f.cameraLock,'ground combo locked cinematic camera');
     if(L.activeFor(p)){
       const immune=id==='naruto-reverse-lotus'&&['lift','combo','descent'].includes(f.phase);
       assert(L.isInvulnerable(p)===immune,'boss contact changed immunity phases');
       maxDistance=Math.max(maxDistance,Math.hypot(q.e.x-p.x,q.e.y-p.y));
       if(f.phase!=='approach')groundFrames++;
     }
   }
   assert(frames<1000&&groundFrames>0,'boss combo did not complete '+JSON.stringify({id,kind,speed,frames,groundFrames,phase:f.phase,age:f.age,hits:q.hits.length}));
   const amounts=q.hits.map(h=>h.damage),expected=id==='naruto-lotus'?2:7;
   assert(amounts.length===expected&&q.hits.every(h=>h.owner&&h.id===id),'moving boss lost owned combo hits');
   if(!speed)baselines[id]=amounts;
   else assert(amounts.every((d,i)=>Math.abs(d-baselines[id][i])<1e-7),'moving boss damage differs from stationary');
   assert(q.m.cd===10&&q.m.t===10,'successful boss combo changed ten-second cooldown');
   cases.push({id,kind,speed,radius,hits:amounts.length,damage:amounts.reduce((a,b)=>a+b,0),maxDistance});
 }
 // Acquisition uses boss body edges; ordinary targets retain their original reach.
 for(const id of ids){
   let q=fixture(id,320,80);assert(L.canCast(p,q.m),'large boss body edge was not reachable');
   q=fixture(id,230,10);q.e.boss=false;q.minion.dead=true;G.EnemyMgr.rebuildGrid();
   assert(!L.canCast(p,q.m),'ordinary enemy acquired extended boss range');
   q=fixture(id);q.minion.dead=true;G.World.isWall=x=>x>=50&&x<=60;
   assert(!L.canCast(p,q.m),'boss acquired through wall');
   q=fixture(id);A.actualCast(id);G.World.isFree=x=>x<40;G.World.isWall=x=>x>=40&&x<=45;
   for(let i=0;i<150&&L.activeFor(p);i++)step();
   assert(p.x<40&&q.hits.length===0&&q.m.t<=.5,'blocked boss approach crossed wall, hit, or consumed full cooldown');
   q=fixture(id);A.actualCast(id);q.e.x=1400;G.EnemyMgr.rebuildGrid();
   for(let i=0;i<1000&&L.activeFor(p);i++)step();
   assert(!L.activeFor(p)&&q.hits.length===0&&q.m.t<=.5,'evasive boss received remote damage or no whiff retry');
 }
 // Passive pursuit also prioritizes and chases the moving boss without extra casts.
 const q=fixture('naruto-lee-pursuit',160,35);A.advance(.001);const action=P.activeFor(p);
 assert(action?.target===q.e,'pursuit preferred nearby minion over boss');
 let frames=0;while(P.activeFor(p)&&frames++<500)step(.005,300,q.e);
 assert(frames<500&&q.hits.length===3&&q.hits.every(h=>h.owner&&h.id==='naruto-lee-pursuit'),'moving boss lost pursuit punches');
 assert(q.hits.every(h=>h.distance>=(p.r||12)+q.e.r-4),'pursuit entered boss body');
 A.bossFixture=fixture;A.bossStep=step;
 return {cases,bodyEdge:true,priority:true,wall:true,evasion:true,pursuitHits:q.hits.length};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, mobile in [('desktop', False), ('mobile', True)]:
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1200, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(URL)
            page.wait_for_function("window.G?.NarutoPursuit&&document.querySelector('#boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
            page.evaluate('()=>G.Sprites.preload([19])')
            page.evaluate(HARNESS)
            page.evaluate(SETUP)
            report['viewports'][label] = page.evaluate(CHECK)
            page.evaluate("() => {const A=Acceptance,q=A.bossFixture();A.actualCast(q.m.id);A.bossStep(.005);window.bossRetreatCase=q;}")
            page.keyboard.down('a')
            try:
                report['viewports'][label]['retreat'] = page.evaluate('''() => {
                  const A=Acceptance,p=A.p(),q=window.bossRetreatCase,x=p.x;A.bossStep(.01);
                  A.assert(!G.NarutoLee.activeFor(p)&&p.x===x&&q.hits.length===0&&q.m.t<=.5,'retreat dragged player or consumed full cooldown');return true;
                }''')
            finally:
                page.keyboard.up('a')
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    (OUT / 'regression.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'viewports': list(report['viewports']), 'evidence': str(OUT / 'regression.json')}))


if __name__ == '__main__':
    main()
