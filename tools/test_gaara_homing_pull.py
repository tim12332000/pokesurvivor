"""Native acceptance for curved sand rain and grounded inward quicksand."""
import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_gaara import SETUP, URL

OUT = Path(__file__).resolve().parents[1] / '.omx/state/gaara-homing-pull'

FIXTURE = r"""() => {
 const A=Acceptance,p=A.p();p.level=12;p.cdMul=1;
 const c=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-sand-prison');
 A.assert(c&&c.apply(p)!==false,'native prison learn card missing');
 A.distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
 A.angle=(a,b)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
 A.prison=()=>{A.gaaraArena();A.select('naruto-sand-prison');A.spawn(180,0);A.advance(6);return G.NarutoGaara.sandPrisonState(p)};
 A.frame=()=>{const c=document.createElement('canvas');c.width=640;c.height=440;
 const x=c.getContext('2d');x.fillStyle='#374b38';x.fillRect(0,0,c.width,c.height);x.translate(220,220);
 G.Combat.drawGroundFields(x);for(const e of G.EnemyMgr.all())e.anim?.draw(x,e.x,e.y,{scale:1});
 p.anim.draw(x,p.x,p.y,{scale:1});G.Combat.drawAirFields(x);return c.toDataURL()};
}"""

HOMING = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,out={};
 A.gaaraArena();let target=A.spawn(210,0);p.target=target;A.actualCast('naruto-gaara');A.advance(.13);
 const first=N.bullets[0];A.assert(first&&target.hp===100000,'rain hit remotely at launch');
 target.x=170;target.y=80;G.EnemyMgr.rebuildGrid();
 let maxTurn=0,travel=0;const path=[[first.x,first.y]];
 for(let i=0;i<65&&N.bullets.includes(first);i++){
   const {x,y,aim,distance}=first;A.advance(.01);const turn=Math.abs(A.angle(first.aim,aim));
   A.assert(turn<=3.6*.01+1e-7,'rain turned sharper than smooth 3.6 rad/s');
   A.assert(Math.hypot(first.x-x,first.y-y)<=4.2+1e-6,'rain exceeded speed 420');
   A.assert(first.distance-distance<=4.2+1e-6,'rain travelled beyond frame budget');
   maxTurn=Math.max(maxTurn,turn);travel=first.distance;path.push([first.x,first.y]);
   if(i===17)out.frame=A.frame();
 }
 A.assert(maxTurn>.001&&path.some(q=>q[1]>5),'rain stayed straight instead of homing');
 A.assert(target.hp<100000,'moving target never received real sand contact');
 A.assert(travel<=first.range+1e-5,'homing extended original travel range');
 out.movingTarget={maxTurn,travel,damage:100000-target.hp,path};
 // Dead targets must relinquish steering and allow another living enemy.
 A.gaaraArena();target=A.spawn(200,0);p.target=target;A.actualCast('naruto-gaara');A.advance(.13);
 const bullet=N.bullets[0];target.dead=true;target.hp=0;const replacement=A.spawn(160,55);
 for(let i=0;i<80&&replacement.hp===100000;i++)A.advance(.01);
 A.assert(replacement.hp<100000,'dead target prevented retargeting');out.retarget=true;
 // With no surviving target, bullets expire using distance rather than orbiting forever.
 A.gaaraArena();target=A.spawn(200,0);p.target=target;A.actualCast('naruto-gaara');A.advance(.13);
 const lost=N.bullets[0];target.dead=true;target.hp=0;A.advance(2);
 A.assert(!N.bullets.length&&lost.distance<=lost.range+1e-5,'lost target prolonged range');out.lostTarget=true;
 // A wall occupying the actual impact area must win over enemy contact, at both dt sizes.
 for(const dt of [.01,2]){
   A.gaaraArena();target=A.spawn(210,0);p.target=target;A.actualCast('naruto-gaara');
   const w=G.World.isWall;G.World.isWall=(x,y)=>x>=85&&x<=94;
   try{for(let i=0;i<Math.ceil(2/dt);i++)A.advance(dt)}finally{G.World.isWall=w}
   A.assert(target.hp===100000&&!N.bullets.length,'homing crossed wall dt='+dt);
 }
 out.wallFirst=true;return out;
}"""

PULL = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,out={};let field=A.prison();
 const regular=A.spawn(field.x+65,field.y),elite=A.spawn(field.x,field.y+65);elite.elite=true;
 const fly=A.spawn(field.x-55,field.y),jump=A.spawn(field.x,field.y-55),outside=A.spawn(field.x+100,field.y);
 fly.flying=true;jump.jump={sx:jump.x,sy:jump.y,tx:jump.x,ty:jump.y,t:0,dur:1};
 const initial=[regular,elite,fly,jump,outside].map(e=>({x:e.x,y:e.y,d:A.distance(e,field)}));
 out.startFrame=A.frame();
 A.advance(.1);const normalPull=initial[0].d-A.distance(regular,field),elitePull=initial[1].d-A.distance(elite,field);
 A.assert(normalPull>0&&normalPull<20,'ordinary enemy failed gradual inward movement');
 A.assert(Math.abs(elitePull/normalPull-.35)<1e-5,'elite pull is not 35 percent normal strength');
 [fly,jump,outside].forEach((e,i)=>A.assert(e.x===initial[i+2].x&&e.y===initial[i+2].y,'airborne/outside victim pulled'));
 const before={x:regular.x,y:regular.y};G.Combat.updateFields(.5);
 A.assert(regular.x===before.x&&regular.y===before.y,'paused prison pulled');
 p.frozen=true;A.advance(.5);p.frozen=false;
 A.assert(regular.x===before.x&&regular.y===before.y,'frozen owner prison pulled');
 A.advance(.9);out.middleFrame=A.frame();
 A.assert(A.distance(regular,field)<initial[0].d-normalPull,'pull failed to continue');
 const wallVictim=A.spawn(field.x+60,field.y+20),wallPosition={x:wallVictim.x,y:wallVictim.y};
 const w=G.World.isWall;G.World.isWall=(x,y)=>x>=field.x+20&&x<=field.x+24;
 try{A.advance(.3)}finally{G.World.isWall=w}
 A.assert(wallVictim.x===wallPosition.x&&wallVictim.y===wallPosition.y,'prison pulled through intervening wall');
 const pos={x:regular.x,y:regular.y};A.select('naruto-gaara');A.advance(.3);
 A.assert(!N.sandPrisonState(p)&&regular.x===pos.x&&regular.y===pos.y&&!N.rooted(regular),'cancelled prison retained pull');
 out.pull={normalPull,elitePull,ratio:elitePull/normalPull};out.immune=true;out.pauseFreeze=true;out.wall=true;out.cancel=true;
 // Damage cadence and duration remain the original ten half-second contacts.
 field=A.prison();const victim=G.EnemyMgr.all()[0];let hits=0;const hurt=victim.hurt;
 victim.hurt=function(...args){hits++;return hurt.apply(this,args)};
 A.advance(4.99);A.assert(hits===9&&N.sandPrisonState(p),'prison duration/ticks ended early');
 A.advance(.01);A.assert(hits===10&&!N.sandPrisonState(p),'prison is not exactly five seconds / ten hits');
 out.ticks=hits;return out;
}"""

RENDER = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara;A.gaaraArena();const e=A.spawn(220,0);p.target=e;
 A.actualCast('naruto-gaara');A.advance(.2);e.y=55;G.EnemyMgr.rebuildGrid();A.advance(.04);
 const bullets=N.bullets,before=JSON.stringify(bullets.map(b=>({x:b.x,y:b.y,aim:b.aim,distance:b.distance,trail:b.trail})));
 let paints=0,queries=0;const c=document.createElement('canvas'),ctx=c.getContext('2d');
 for(const key of ['fill','stroke','fillRect','drawImage']){const fn=ctx[key].bind(ctx);ctx[key]=(...args)=>{paints++;return fn(...args)}}
 const q=G.EnemyMgr.queryCircle,w=G.World.isWall,block=G.World.projectileBlock;
 G.EnemyMgr.queryCircle=()=>{queries++;return []};G.World.isWall=()=>{queries++;return false};G.World.projectileBlock=()=>{queries++;return false};
 try{for(const b of bullets)G.NarutoSandVFX.drawBullet(ctx,b)}finally{G.EnemyMgr.queryCircle=q;G.World.isWall=w;G.World.projectileBlock=block}
 A.assert(queries===0,'rain renderer queries combat/terrain');
 A.assert(before===JSON.stringify(bullets.map(b=>({x:b.x,y:b.y,aim:b.aim,distance:b.distance,trail:b.trail}))),'rain renderer mutated physics');
 A.assert(paints>0&&paints<=50*bullets.length,'rain visual per-bullet paint budget exceeded');
 return {bullets:bullets.length,paints,queries};
}"""

RESOURCE = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,out={};
 A.gaaraArena();const e=A.spawn(250,0);p.target=e;A.actualCast('naruto-gaara');A.advance(.13);
 const count=N.bullets.length;let queries=0,walls=0;
 const q=G.EnemyMgr.queryCircle,w=G.World.isWall,block=G.World.projectileBlock;
 G.EnemyMgr.queryCircle=function(...args){queries++;return q.apply(this,args)};
 G.World.isWall=function(...args){walls++;return w.apply(this,args)};
 G.World.projectileBlock=function(...args){walls++;return block.apply(this,args)};
 try{A.advance(.01)}finally{G.EnemyMgr.queryCircle=q;G.World.isWall=w;G.World.projectileBlock=block}
 A.assert(queries<=count,'steady homing performs redundant enemy queries');
 A.assert(walls<=count*6,'steady homing added target LOS scans to physical 2px wall samples');
 out.steadyTarget={bullets:count,queries,wallSamples:walls};
 A.gaaraArena();p.quantityBonus=20;const target=A.spawn(230,0);p.target=target;
 let hits=0,raw=0;const hurt=target.hurt;target.hurt=function(amount,...args){hits++;raw+=amount;return hurt.call(this,amount,...args)};
 const move=A.actualCast('naruto-gaara');A.advance(2);
 const expected=(move.dmg+p.level)*p.atk*G.Types.mult(move.type,target.types)*G.Weather.mult(move.type)/3*23;
 A.assert(hits===23&&Math.abs(raw-expected)<1e-5,'quantity card changed per-bullet divisor or lost emissions '+JSON.stringify({hits,raw,expected}));
 out.quantity={hits,raw,expected};p.quantityBonus=0;
 const positions=[];
 for(const dt of [.01,.5]){
   const field=A.prison(),victim=A.spawn(field.x+65,field.y);
   for(let i=0;i<Math.round(.5/dt);i++)A.advance(dt);
   positions.push(A.distance(victim,field));
 }
 A.assert(Math.abs(positions[0]-positions[1])<1,'large-dt pull diverged materially from short frames');
 out.pullDeltaDistances=positions;return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in (False, True):
                label = 'mobile' if mobile else 'desktop'
                context = browser.new_context(locale='zh-TW', viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile)
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.NarutoGaara && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                for fixture in (HARNESS, SETUP, FIXTURE):
                    page.evaluate(fixture)
                result = report['viewports'][label] = {}
                for name, fixture in [('homing', HOMING), ('pull', PULL), ('render', RENDER), ('resource', RESOURCE)]:
                    result[name] = page.evaluate(fixture)
                    for key in list(result[name]):
                        if key.lower().endswith('frame'):
                            data = result[name].pop(key)
                            (OUT / f'{label}-{name}-{key}.png').write_bytes(base64.b64decode(data.split(',', 1)[1]))
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
