"""Eight Gates learned passive: real main entry, upgrade cards, stats and source art."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_redrawn_heroes import AUDIT
from test_rock_lee import SETUP

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/lee-gates'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=lee-gates'

HUD = r"""() => {
 const A=Acceptance;
 A.inspectHud=(id='naruto-gates')=>{
   const p=A.p(),m=p.moves.find(m=>m.id===id),canvas=document.createElement('canvas');
   canvas.width=innerWidth;canvas.height=innerHeight;const ctx=canvas.getContext('2d'),icons=[],rects=[],texts=[],buttons=[];
   const icon=G.Icons.draw,add=G.Touch.addButton,fill=ctx.fillRect.bind(ctx),text=ctx.fillText.bind(ctx);
   G.Icons.draw=function(c,key,x,y,size,...args){icons.push({key,x,y,size});return icon.call(this,c,key,x,y,size,...args)};
   G.Touch.addButton=function(x,y,w,h,...args){buttons.push({x,y,w,h});return add.call(this,x,y,w,h,...args)};
   ctx.fillRect=function(x,y,w,h){rects.push({x,y,w,h,color:ctx.fillStyle});return fill(x,y,w,h)};
   ctx.fillText=function(value,x,y,...args){texts.push({value:String(value),x,y});return text(value,x,y,...args)};
   try{G.HUD.draw(ctx,canvas.width,canvas.height,p,{time:30})}finally{G.Icons.draw=icon;G.Touch.addButton=add}
   const key=G.SharinganIcons?.forMove(m)||'move:'+id,matches=icons.filter(i=>i.key===key);
   A.assert(matches.length===1,'learned passive icon missing or duplicated '+id+' '+matches.length);
   const i=matches[0],button=buttons.find(b=>i.x+i.size/2>b.x&&i.x+i.size/2<b.x+b.w&&i.y+i.size/2>b.y&&i.y+i.size/2<b.y+b.h);
   A.assert(button,'HUD icon did not register actual input target '+id);
   const inside=r=>r.x>=button.x&&r.x<=button.x+button.w&&r.y>=button.y&&r.y<=button.y+button.h;
   const dots=rects.filter(r=>r.w===4&&r.h===3&&inside(r));ctx.fillStyle=G.U.TYPE_COLOR[m.type];const col=ctx.fillStyle;
   A.assert(dots.length===m.def.maxLvl&&dots.filter(d=>d.color===col).length===m.lvl,'HUD stage dots not current '+id+' Lv'+m.lvl);
   if(id==='naruto-gates')A.assert(texts.some(t=>t.value==='\u221e'&&inside(t)),'slotless passive badge missing');
   return {icon:key,count:matches.length,level:m.lvl,dots:dots.length,filled:dots.filter(d=>d.color===col).length,
     target:{x:button.x+button.w/2,y:button.y+button.h/2},active:p.active,selected:p.activeGroup().map(m=>m.id)};
 };
}"""

PASSIVE = r"""() => {
 const A=Acceptance,p=A.p(),g=G.NarutoGates,out={stages:[]},near=(a,b)=>Math.abs(a-b)<1e-7;
 A.assert(g&&g.stage(p)===0,'new Lee already owns gates');
 const baseAtk=p.atk,baseSpd=p.spd;
 p.level=5;A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='new:naruto-gates'),'gate learned before Lv6');
 // Fill every active slot first: learning must neither replace a weapon nor fail.
 for(const id of ['naruto-lotus','naruto-reverse-lotus','tackle'])if(p.slots.length<p.maxMoves)A.assert(p.addMove(id),'fixture '+id);
 A.assert(p.slots.length===p.maxMoves,'full-slot fixture missing');
 const slots=p.slots.map(s=>s.map(m=>m.id)),selected=p.activeGroup().map(m=>m.id);
 p.level=6;const learn=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-gates');
 A.assert(learn&&learn.apply(p)!==false,'full slots prevented passive learning');
 const move=p.moves.find(m=>m.id==='naruto-gates');
 A.assert(move?.passive&&move.digiMode==='gates-passive','not a learned passive');
 A.assert(JSON.stringify(p.slots.map(s=>s.map(m=>m.id)))===JSON.stringify(slots),'learning consumed/replaced active slot');
 A.assert(JSON.stringify(p.activeGroup().map(m=>m.id))===JSON.stringify(selected),'learning changed selected weapon');
 A.assert(!p.addMove('naruto-gates')&&p.moves.filter(m=>m.id==='naruto-gates').length===1,'duplicate learned gates');
 let gatesCasts=0;const cast=p.cast;p.cast=function(m,...args){if(m.id==='naruto-gates')gatesCasts++;return cast.call(this,m,...args)};
 try{A.resume();G.Combat.tick(.1,p,0)}finally{p.cast=cast;A.pause()}
 A.assert(gatesCasts===0&&move.t===0,'passive entered automatic cast/cooldown');
 for(let level=1;level<=5;level++){
   if(level>1){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:naruto-gates');A.assert(card&&card.apply(p)!==false,'missing real stage card '+level)}
   A.advance(.01);A.assert(move.lvl===level&&g.stage(p)===level,'wrong learned stage '+level);
   const atk=baseAtk*[1.3,1.35,1.4,1.45,1.5][level-1],spd=baseSpd*(1+(10*level+p.level)/100);
   A.assert(near(p.atk,atk)&&near(p.spd,spd),'wrong stage stats '+level);
   for(let n=0;n<150;n++)A.advance(.1);
   A.assert(near(p.atk,atk)&&near(p.spd,spd),'stacked or expired stage '+level);
   A.assert(p.slots.length===slots.length&&!p.slots.some(s=>s.includes(move)),'upgrade gained a slot');
   A.assert(g.active(p)&&g.redSkin(p)&&g.redForm(p)===(level>=3),'form stage API mismatch '+level);
   const factor=1+(10*level+p.level)/100;
   A.assert(g.bonusPercent(p)===10*level+p.level&&near(g.healingMultiplier(p),factor),'wrong healing API formula');
   p.hp=10;p.heal(10);A.assert(near(p.hp-10,10*factor),'direct healing not scaled exactly once');
   p.hp=10;p.regenFlat=4;A.resume();p.update(.25);A.pause();
   A.assert(near(p.hp-10,factor),'regeneration did not use healing formula');p.regenFlat=0;
   p.hp=10;p.bellHeal=2;A.resume();p.update(.25);A.pause();
   A.assert(near(p.hp-10,factor)&&near(p.bellHeal,1),'shell bell did not scale once');p.bellHeal=0;
   p.hp=10;p.lifestealRate=.1;p.onDealt(100);p.lifestealRate=0;
   A.assert(near(p.hp-10,10*factor),'lifesteal did not scale once');
   const specials=G.World.specialsNear;
   try{G.World.specialsNear=()=>[{type:'spring',x:p.x,y:p.y+8,charge:1}];p.hp=10;G.Interact.update(.1,p);
     A.assert(near(p.hp-10,p.maxHp*.014*factor),'spring did not scale once');
   }finally{G.World.specialsNear=specials}
   p.hp=p.maxHp;
   out.stages.push({hud:A.inspectHud(),level,playerLevel:p.level,name:move.name,attack:p.atk,speed:p.spd,healingFactor:factor,slots:p.slots.length});
 }
 A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='up:naruto-gates'),'sixth gates stage offered');
 p.level=29;p.xp=0;p.xpNext=G.Player.xpFor(p.level);p.gainXp((p.xpNext+.001)/p.xpMul);
 A.assert(p.level===30&&g.bonusPercent(p)===80&&near(g.healingMultiplier(p),1.8)&&near(p.spd,baseSpd*1.8),'N5 LV30 did not update immediately');
 p.hp=10;p.heal(10);A.assert(near(p.hp,28),'N5 LV30 healing should be +80%');
 out.dynamicLevel={skillLevel:5,playerLevel:30,bonusPercent:g.bonusPercent(p),speed:p.spd,healingFactor:g.healingMultiplier(p)};
 for(const id of ['naruto-lee','naruto-lotus','naruto-reverse-lotus']){A.select(id);A.advance(.01);A.assert(g.stage(p)===5&&near(p.atk,baseAtk*1.5),'weapon switch lost passive')}
 const atk=p.atk,spd=p.spd;
 G.Combat.clearFields(p);A.advance(.01);A.assert(near(p.atk,atk)&&near(p.spd,spd),'field clear disabled passive');
 // Permanent stat cards must compose with, and survive, the passive multiplier.
 for(const id of ['atk','spd']){let card;for(let n=0;n<100&&!card;n++)card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:'+id);A.assert(card,'stat card missing '+id);card.apply(p)}
 A.assert(near(p.atk,atk*1.1)&&near(p.spd,spd*1.07),'stat card composed incorrectly');
 // An old active-gates save migrates without retaining a slot or support timers.
 p.slots.push([move]);p.active=p.slots.length-1;move.passive=false;move.fieldDuration=5;move.fatigueDuration=2;
 A.advance(.01);A.assert(move.passive&&!p.slots.some(s=>s.includes(move))&&!('fatigueDuration' in move)&&!('fieldDuration' in move),'legacy active gate did not migrate');
 A.assert(p.activeGroup().some(m=>!m.passive),'legacy migration stranded active slot');
 const boostedAtk=p.atk,boostedSpd=p.spd;
 p.dead=true;A.advance(.01);A.assert(g.stage(p)===0&&!g.active(p)&&!g.redSkin(p),'dead owner retained passive');
 A.assert(near(p.atk,boostedAtk/1.5)&&near(p.spd,boostedSpd/1.8),'dead owner retained stat factors');
 p.dead=false;p.hp=p.maxHp;A.advance(.01);out.slotCount=p.slots.length;return out;
}"""

ART = r"""() => {
 const A=Acceptance,p=A.p(),out={};A.leeArena();
 for(const [name,anim,walking] of [['idle','Idle',false],['run','Walk',true]]){
   p.walking=walking;p.anim.dir=2;p.anim.play(anim);out[name]=A.render();
 }
 p.walking=false;p.hurt(10,null,true);out.hurt=A.render();
 A.leeArena();p.target=A.spawn(35,0);A.actualCast('tackle');out.punch=A.render();
 A.assert(out.punch.state.key==='lee-opened-attack','punch did not use the actual attack pose');
 for(const id of ['naruto-lee','naruto-lotus','naruto-reverse-lotus']){
   A.leeArena();p.target=A.spawn(35,0);A.actualCast(id);A.advance(.3);out[id]=A.render();
 }
 for(const [name,sample] of Object.entries(out)){
   A.assert(sample.sources.length&&sample.sources.every(src=>/lee-gates-(common|skills)-v1\.png/.test(src)),'normal/non-red gates art '+name+' '+sample.sources);
 }
 A.leeArena();return out;
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'failedRequests': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in (False, True):
                label = 'mobile' if mobile else 'desktop'
                ctx = browser.new_context(locale='zh-TW', viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = ctx.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('response', lambda r: report['failedRequests'].append(r.url) if r.status>=400 and '127.0.0.1' in r.url else None)
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && G.NarutoGates && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30006"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
                page.evaluate(HARNESS)
                page.evaluate(SETUP)
                page.evaluate(HUD)
                result = {'passive':page.evaluate(PASSIVE)}
                page.evaluate(r"""() => {const A=Acceptance,p=A.p();A.leeArena();p.regenFlat=0;p.hp=1;G.Pickups.clear();
                  A.expectedBerry=1+p.maxHp*.3*G.NarutoGates.healingMultiplier(p);G.Pickups.drop('heal',p.x,p.y);A.resume();
                }""")
                page.wait_for_function('G.Pickups.count===0&&G.Game.player.hp>1')
                result['pickup']=page.evaluate(r"""() => {const A=Acceptance,p=A.p();A.pause();A.assert(Math.abs(p.hp-A.expectedBerry)<1e-7,'real berry healing scaled incorrectly');return {hp:p.hp,expected:A.expectedBerry}}""")
                report['viewports'][label] = result
                target=page.evaluate('Acceptance.inspectHud().target')
                before=page.evaluate('({active:G.Game.player.active,ids:G.Game.player.activeGroup().map(m=>m.id)})')
                page.evaluate('Acceptance.resume()')
                if mobile:page.touchscreen.tap(target['x'],target['y'])
                else:page.mouse.click(target['x'],target['y'])
                result['hudClick']=page.evaluate(r"""before => {
                  const A=Acceptance,p=A.p();A.pause();A.assert(p.active===before.active&&JSON.stringify(p.activeGroup().map(m=>m.id))===JSON.stringify(before.ids),'passive click changed weapon');
                  const toast=document.querySelector('.toast');A.assert(toast&&toast.textContent.includes(p.moves.find(m=>m.id==='naruto-gates').name)&&toast.textContent.includes('Lv.5'),'passive click did not explain learned level');
                  return {active:p.active,toast:toast.textContent,hud:A.inspectHud()};
                }""",before)
                page.evaluate('Acceptance.resume()')
                page.wait_for_function("!document.querySelector('.toast')||document.querySelector('.toast').style.display==='none'")
                page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                result['hudScreenshotState']=page.evaluate('({game:G.Game.state,body:document.body.dataset.gameState})')
                page.screenshot(path=str(OUT/f'hud-{label}.png'))
                page.evaluate('Acceptance.pause()')
                page.evaluate(AUDIT)
                result['art'] = page.evaluate(ART)
                for name, pose in result['art'].items():
                    (OUT/f'{label}-{name}.png').write_bytes(base64.b64decode(pose.pop('png').split(',',1)[1]))
                result['newOwner'] = page.evaluate(r"""() => {
                  const A=Acceptance,old=A.p();G.Game.toUI();G.Flow.play();G.Game.togglePause();
                  const p=G.Game.player;A.assert(p!==old&&p.dex===30006,'restart owner unchanged');
                  A.assert(!p.hasMove('naruto-gates')&&G.NarutoGates.stage(p)===0&&!G.NarutoGates.active(old),'gates leaked into new run');
                  return true;
                }""")
                page.screenshot(path=str(OUT/f'{label}.png'))
                page.evaluate('G.Flow.goMenu()')
                page.locator('[data-quick-naruto="30002"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30002&&G.Game.state==="playing"')
                page.evaluate(HARNESS)
                page.evaluate(HUD)
                result['sharinganNoDuplicate']=page.evaluate(r"""() => {const A=Acceptance,p=A.p();A.pause();A.assert(p.addMove('naruto-sharingan'),'learn sharingan fixture');return A.inspectHud('naruto-sharingan')}""")
                ctx.close()
            browser.close()
        assert not report['errors'], report['errors']
        assert not report['failedRequests'], report['failedRequests']
        report['ok'] = True
    except Exception as error:
        report['ok'] = False
        report['failure'] = str(error)
        raise
    finally:
        (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'poses':sum(len(v['art']) for v in report['viewports'].values()),'evidence':str(OUT)},ensure_ascii=False))

if __name__ == '__main__':
    main()
