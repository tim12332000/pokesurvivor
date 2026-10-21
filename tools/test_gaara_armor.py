"""Native selected sand armor regression; HTTP server required on port 8004."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_gaara import SETUP, URL

OUT = Path(__file__).resolve().parents[1] / '.omx/state/gaara-armor'

SETUP_ARMOR = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,id='naruto-sand-armor';
 A.armorId=id;A.near=(a,b)=>Math.abs(a-b)<1e-5;
 A.startArmor=()=>{A.gaaraArena();A.select(id);A.spawn(80,0);p.target=null;
   A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()}
   A.assert(N.armorState(p),'native tick failed to start armor');return N.armorState(p)};
 A.realArmorHit=(amount=10,reset=true)=>{if(reset)p.invuln=0;A.resume();try{p.hurt(amount,null,true)}finally{A.pause()}};
}"""

PROGRESSION = r"""() => {
 const A=Acceptance,p=A.p(),id=A.armorId,out={},mon=p.mon;
 for(const level of [1,12,14,15]){
   p.level=level;const eligible=level>=15;
   A.assert(G.Moves.poolFor(p.mon).includes(id)===eligible,'armor level pool '+level);
   A.assert(G.LevelUp.offer(p,100).some(c=>c.key==='new:'+id)===eligible,'armor level card '+level);
 }
 for(const dex of [30001,30002,30006,20001]){
   p.mon=G.DEX.find(m=>m.dex===dex)||{dex,gen:10,types:['normal']};
   A.assert(!G.Moves.poolFor(p.mon).includes(id),'armor leaked '+dex);
 }p.mon=mon;p.level=15;
 // Shield is learned without consuming a slot; armor fills the fifth active slot.
 for(const skill of ['naruto-sand-coffin','naruto-sand-shield','naruto-sand-tsunami','naruto-sand-prison',id]){
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+skill);
   A.assert(card&&card.apply(p)!==false,'learn fixture '+skill);
 }
 A.assert(p.slots.length===5&&p.hasMove(id)&&p.hasMove('naruto-sand-shield'),'armor must fit beside passive shield');
 A.assert(!p.slots.some(g=>g.some(m=>m.id==='naruto-sand-shield')),'passive shield consumed slot');
 // Isolate existing armor mechanics; combination coverage lives in passive-shield suite.
 p.moves=p.moves.filter(m=>m.id!=='naruto-sand-shield');G.Combat.clearFields(p);
 out.fifthActive=true;
 return out;
}"""

COMBAT = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,id=A.armorId,m=p.moves.find(m=>m.id===id),out={};
 p.cdMul=1;
 for(const reason of ['empty','range','wall']){
   A.gaaraArena();A.select(id);if(reason!=='empty')A.spawn(reason==='range'?250:80,0);
   const wall=G.World.isWall;if(reason==='wall')G.World.isWall=(x,y)=>x>=35&&x<=40;
   try{A.resume();G.Combat.tick(.001,p,0);A.pause();A.assert(!N.armorState(p),'invalid armor target '+reason)}
   finally{A.pause();G.World.isWall=wall}
 }
 let s=A.startArmor();A.assert(s.duration===3&&A.near(m.t,10),'duration/cooldown contract');
 const hp=p.hp;A.realArmorHit(10);
 A.assert(A.near(hp-p.hp,7)&&N.armorState(p).hits===1,'30 percent reduction or accepted hit');
 const acceptedHp=p.hp;A.realArmorHit(10,false);
 A.assert(p.hp===acceptedHp&&N.armorState(p).hits===1,'invulnerable hit counted');
 A.realArmorHit(0);
 A.assert(p.hp===acceptedHp&&N.armorState(p).hits===1,'zero damage hit counted');
 A.realArmorHit();A.assert(N.armorState(p)?.hits===2,'second real hit missing');
 const target=G.EnemyMgr.all()[0];A.realArmorHit();
 A.assert(!N.armorState(p)&&target.hp<100000,'third hit failed to burst');
 const dealt=target.hp;A.advance(4);A.assert(target.hp===dealt,'burst duplicated after hit trigger');out.threeHits=true;
 A.startArmor();const e=G.EnemyMgr.all()[0];A.advance(2.99);
 A.assert(N.armorState(p)&&e.hp===100000,'armor expired early');A.advance(.01);
 A.assert(!N.armorState(p)&&e.hp<100000,'armor expiry did not burst');const expired=e.hp;
 A.advance(4);A.assert(e.hp===expired,'expiry burst duplicated');out.expiry=true;
 // Native owned damage, exact circle, line of sight, and boss knockback immunity.
 A.startArmor();G.EnemyMgr.clear();
 const es=[A.spawn(65,0),A.spawn(-65,0),A.spawn(0,65),A.spawn(125,0),A.spawn(60,-50),A.spawn(-50,-50,true)];
 const hits=es.map(()=>0),owned=es.map(()=>true);
 es.forEach((e,i)=>{const hurt=e.hurt;e.hurt=function(...args){hits[i]++;owned[i]&&=args[6]===p;return hurt.apply(this,args)}});
 const wall=G.World.isWall;G.World.isWall=(x,y)=>x>=28&&x<=32&&y< -15;
 try{A.advance(3)}finally{G.World.isWall=wall}
 A.assert(hits.slice(0,3).every(x=>x===1)&&hits[3]===0&&hits[4]===0&&hits[5]===1,'circle/LOS damage '+hits);
 A.assert(owned.every(Boolean),'burst lost player ownership');
 A.assert(es.slice(0,3).every(e=>Math.hypot(e.kx,e.ky)>0),'ordinary enemies not knocked back');
 A.assert(!es[5].kx&&!es[5].ky,'boss was knocked back');out.aoe={hits,damage:es.map(e=>100000-e.hp)};
 // Armor never monopolizes the action: constant native basic still casts.
 A.startArmor();const cast=p.cast,casts=[];
 p.cast=function(move,...args){casts.push(move.id);return cast.call(this,move,...args)};
 try{A.resume();G.Combat.tick(.61,p,0)}finally{p.cast=cast;A.pause()}
 A.assert(casts.includes('naruto-gaara')&&N.armorState(p),'armor suppressed basic');out.basic=true;
 return out;
}"""

STAGES = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,id=A.armorId,m=p.moves.find(m=>m.id===id),out=[];
 for(let stage=1;stage<=5;stage++){
   if(stage>1){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(card&&card.apply(p)!==false,'armor upgrade '+stage)}
   p.cdMul=1;p.quantityBonus=0;let s=A.startArmor();
   const damage=[70,85,85,105,130][stage-1],radius=[110,110,125,125,140][stage-1],reduction=[.3,.35,.35,.4,.45][stage-1];
   A.assert(m.lvl===stage&&A.near(s.damage,damage*p.atk)&&A.near(s.radius,radius)&&A.near(s.reduction,reduction)&&m.cd===10,'stage contract '+stage);
   const hp=p.hp;A.realArmorHit(10);A.assert(A.near(hp-p.hp,10*(1-reduction)),'stage damage reduction '+stage);
   out.push({stage,damage,radius,reduction});
 }
 p.cdMul=.92;p.quantityBonus=20;let s=A.startArmor();
 A.assert(A.near(m.t,9.2),'cooldown modifier ignored');const e=G.EnemyMgr.all()[0];let hits=0,raw=0;
 const hurt=e.hurt;e.hurt=function(...args){hits++;raw+=args[0];return hurt.apply(this,args)};
 A.advance(3);const expected=130*p.atk*G.Types.mult(m.type,e.types)*G.Weather.mult(m.type);
 A.assert(hits===1&&A.near(raw,expected),'quantity duplicated burst or attack modifier ignored');
 p.cdMul=1;p.quantityBonus=0;return out;
}"""

CLEANUP = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,id=A.armorId,m=p.moves.find(m=>m.id===id),out=[];
 A.startArmor();const e=G.EnemyMgr.all()[0],age=N.armorState(p).age,cd=m.t;
 G.Combat.updateFields(.5);A.assert(N.armorState(p).age===age&&m.t===cd,'pause advanced armor');out.push('pause');
 p.setActive(p.slots.findIndex(g=>g.some(m=>m.id==='naruto-gaara')));
 A.assert(!N.armorState(p)&&e.hp===100000&&m.t===cd,'switch burst or reset cooldown');
 p.setActive(p.slots.findIndex(g=>g.some(m=>m.id===id)));
 A.resume();try{G.Combat.tick(.01,p,0)}finally{A.pause()}
 A.assert(!N.armorState(p)&&m.t>9,'reselect bypassed cooldown');out.push('switch');
 for(const reason of ['clear','death','world','owner','unlearn']){
   A.startArmor();const e=G.EnemyMgr.all()[0],world=G.World,game=G.Game,moves=p.moves;
   if(reason==='clear')G.Combat.clearFields(p);if(reason==='death')p.dead=true;
   if(reason==='world')G.World={...world};if(reason==='owner')G.Game={...game,player:{...p}};
   if(reason==='unlearn')p.moves=p.moves.filter(x=>x!==m);
   try{G.Combat.updateFields(.01);A.assert(!N.armorState(p)&&e.hp===100000,'cleanup burst/leak '+reason)}
   finally{G.World=world;G.Game=game;p.dead=false;p.moves=moves}
   out.push(reason);
 }
 A.startArmor();const previous=p;G.Game.startRun();
 A.assert(G.Game.player!==previous&&!N.armorState(previous)&&!N.armorState(G.Game.player),'new run retained armor');A.pause();out.push('newgame');return out;
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
                page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                page.evaluate(HARNESS)
                page.evaluate(SETUP)
                page.evaluate(SETUP_ARMOR)
                result = {'progression': page.evaluate(PROGRESSION)}
                report['viewports'][label] = result
                result['combat'] = page.evaluate(COMBAT)
                result['stages'] = page.evaluate(STAGES)
                page.evaluate('Acceptance.p().cdMul=1;Acceptance.startArmor();Acceptance.advance(.5);Acceptance.p().flash=0')
                page.wait_for_timeout(70)
                page.locator('#game').screenshot(path=str(OUT / f'{label}-armor.png'))
                page.evaluate('Acceptance.realArmorHit();Acceptance.realArmorHit();Acceptance.p().flash=0')
                page.wait_for_timeout(70)
                page.locator('#game').screenshot(path=str(OUT / f'{label}-armor-cracked.png'))
                page.evaluate('Acceptance.realArmorHit();Acceptance.advance(.18);Acceptance.p().flash=0')
                page.wait_for_timeout(70)
                page.locator('#game').screenshot(path=str(OUT / f'{label}-burst.png'))
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


if __name__ == '__main__':
    main()
