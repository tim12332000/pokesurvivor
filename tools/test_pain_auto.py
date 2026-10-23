"""Native desktop/mobile acceptance for the movement-only Six Paths beta.

No selected skill, synthetic cast, replacement damage or replacement scheduler.
Only procedural terrain and enemy spawn positions are controlled in arenas.
"""
import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_gaara import CHROME, HARNESS
from test_pain import PASSIVES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/pain-auto'
URL = os.environ.get('PAIN_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=pain&painBeta=1')

SETUP = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;
 A.reset=()=>{A.arena();G.SelfClones.clear();G.Pickups.clear();p.xp=0;p.xpNext=1e9;
   p.target=null;p.quantityBonus=p.quantityPicks=0;p.percentHealthDamage=p.lifestealRate=p.critChance=0;p.cdMul=1;
   A.resume();G.Combat.updateFields(.001);A.pause();
   for(const b of P.actors())b.cooldown=999;
   for(const m of p.moves)m.t=999;
   A.finish(1.6); // Native protection expires before legacy combat fixtures.
 };
 A.spawn=(x,y,boss=false)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
   e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
 A.ready=(...kinds)=>{for(const k of kinds){const m=p.moves.find(m=>m.id==='naruto-pain-'+k);A.assert(m,'unlearned '+k);m.t=0}};
 A.advance=(dt=.01)=>{A.resume();try{G.Combat.tick(dt,p,0);G.Combat.updateFields(dt);p.anim.update(dt);
   G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,0)}finally{A.pause()}};
 A.finish=(seconds=1)=>{for(let i=0;i<Math.ceil(seconds*100);i++)A.advance(.01)};
 A.actions=()=>P.actionsFor(p);
 A.actors=()=>P.actors();
 A.watch=es=>{const hits=[];for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);
   if(this.hp<hp)hits.push({id:args[7],owned:args[6]===p,damage:hp-this.hp});return result}}return hits};
 A.reset();
}"""

BETA = r"""() => {
 const A=Acceptance,p=A.p();
 A.assert(p.level===15&&p.moves.length===8,'default beta must know all eight moves');
 A.assert(p.slots.length===0&&p.moves.every(m=>m.passive),'Pain must have zero selectable active slots');
 return {level:p.level,moves:p.moves.map(m=>({id:m.id,passive:m.passive})),slots:p.slots.length};
}"""

HUD = r"""() => {
 const A=Acceptance,p=A.p(),canvas=document.createElement('canvas');canvas.width=innerWidth;canvas.height=innerHeight;
 const buttons=[],handlers=[],texts=[],icons=[],add=G.Touch.addButton,draw=G.Icons.draw,ctx=canvas.getContext('2d'),fill=ctx.fillText.bind(ctx);
 const gravity=p.moves.find(move=>move.id==='naruto-pain-gravity'),previous=gravity.t;gravity.t=2.5;
 G.Touch.addButton=function(...args){buttons.push(args.slice(0,4));handlers.push(args[4]);return add.apply(this,args)};
 G.Icons.draw=function(ctx,name,...args){icons.push(name);return draw.call(this,ctx,name,...args)};
 ctx.fillText=function(text,...args){texts.push(text);return fill(text,...args)};
 try{G.HUD.draw(ctx,innerWidth,innerHeight,p,G.Game.st)}finally{G.Touch.addButton=add;G.Icons.draw=draw;gravity.t=previous}
 const bottom=buttons.map((rect,index)=>({rect,index})).filter(({rect})=>rect[1]>innerHeight*.65);
 A.assert(bottom.length===p.moves.length,'learned skills missing from bottom bar '+JSON.stringify(buttons));
 A.assert(p.moves.every(move=>icons.includes('move:'+move.id)),'skill icons missing '+JSON.stringify(icons));
 A.assert(texts.includes('2.5s'),'automatic skill cooldown not displayed '+JSON.stringify(texts));
 const selected=p.active;A.resume();try{handlers[bottom[0].index]()}finally{A.pause()}
 A.assert(p.slots.length===0&&p.active===selected,'inspecting a skill changed automatic casting');
 A.assert(texts.includes('六道自動作戰'),'movement-only heading missing '+JSON.stringify(texts));return {buttons,texts,icons};
}"""

CONCURRENT = r"""() => {
 const A=Acceptance,p=A.p(),out={};A.reset();
 const es=[A.spawn(70,0),A.spawn(85,18),A.spawn(85,-18),A.spawn(-500,400)],hits=es.map(e=>A.watch([e]));
 for(const b of G.NarutoPain.actors()){b.x=0;b.y=0}
 A.ready('gravity','missiles','summon','soul','planet');A.advance();
 const simultaneous=A.actions().map(f=>f.kind);
 A.assert(['gravity','missiles','summon','soul'].every(k=>simultaneous.includes(k)),'independent bodies must act concurrently '+simultaneous);
 A.assert(!simultaneous.includes('planet'),'Tendo cannot cast two abilities together');
 A.finish(4.5);
 for(const k of ['gravity','missiles','summon','soul'])A.assert(hits.slice(0,3).flat().some(h=>h.id==='naruto-pain-'+k),'automatic skill caused no native damage '+k);
 for(const k of ['gravity','missiles','summon'])A.assert(hits.slice(0,3).every(h=>h.some(v=>v.id==='naruto-pain-'+k)),'automatic AOE missed group '+k);
 A.assert(!hits[3].length,'automatic abilities damaged far control');
 A.assert(hits.flat().every(h=>h.owned&&h.damage>0),'damage must keep actual player ownership');
 out.concurrent={simultaneous,hits,damage:es.map(e=>100000-e.hp)};
 A.reset();A.ready('planet');const clustered=[A.spawn(160,0),A.spawn(175,18),A.spawn(175,-18)],planetHits=A.watch(clustered);
 A.advance();A.assert(A.actions().some(f=>f.kind==='planet'),'cluster did not trigger automatic planet');A.finish(3.5);
 A.assert(planetHits.filter(h=>h.id==='naruto-pain-planet').length===12,'planet must cause four phases on all three native enemies '+JSON.stringify(planetHits));
 out.planet={hits:planetHits,damage:clustered.map(e=>100000-e.hp)};
 return out;
}"""

DECISIONS = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out={};
 A.reset();A.ready('gravity','missiles','summon','soul','planet');A.finish(.5);
 A.assert(!A.actions().length,'no enemies must not start an action');
 A.assert(['gravity','missiles','summon','soul','planet'].every(k=>p.moves.find(m=>m.id==='naruto-pain-'+k).t<=0),'no target burned a cooldown');
 out.noEnemies=true;
 A.reset();A.ready('gravity','planet');const near=A.spawn(70,0);A.spawn(180,0);A.spawn(190,18);A.spawn(190,-18);A.advance();
 const gravity=A.actions().find(f=>f.kind==='gravity');
 A.assert(gravity?.immediate&&gravity.target===near,'close enemy must trigger emergency Tendo push');out.emergency=true;
 A.reset();A.ready('planet');A.spawn(160,0);A.advance();A.assert(!A.actions().some(f=>f.kind==='planet'),'planet wasted on isolated normal enemy');
 A.spawn(180,10,true);A.advance();A.assert(A.actions().some(f=>f.kind==='planet'),'special enemy did not qualify planet');out.planetSpecial=true;
 A.reset();A.ready('missiles');A.spawn(100,0);A.advance();const move=p.moves.find(m=>m.id==='naruto-pain-missiles'),cooldown=move.t;
 A.assert(cooldown>0,'automatic missiles did not start cooldown');
 const initial=P.snapshot(p).castCounts.missiles;A.finish(.9);
 A.assert(P.snapshot(p).castCounts.missiles===initial&&move.t>0&&move.t<cooldown,'cooldown allowed a duplicate cast');
 A.finish(cooldown+.5);const count=P.snapshot(p).castCounts.missiles-initial;
 A.assert(count===1,'ready cooldown did not resume automatic casts '+count);
 out.cooldown={initial:cooldown,repeat:count};
 return out;
}"""

BODIES = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out={};
 A.reset();const bodies=P.actors();A.assert(bodies.length===5&&new Set(bodies.map(b=>b.path)).size===5,'five unique support bodies required');
 p.quantityBonus=p.quantityPicks=20;const clone=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');A.assert(clone,'clone card missing');clone.apply(p);clone.apply(p);A.advance();
 A.assert(G.SelfClones.actors().length===2,'clone fixture missing');A.assert(P.actors().length===5&&P.actors().every(b=>bodies.includes(b)),'quantity or clones duplicated six paths');
 A.ready('missiles');A.spawn(100,0);A.advance();
 A.assert(A.actions().find(f=>f.kind==='missiles')?.count===30,'quantity multiplier must saturate missile count at30');
 A.assert(P.stateFor(p).actions.filter(f=>f.kind==='missiles').length===1,'clones scheduled duplicate Asura actions');
 G.SelfClones.clear();out.unique=true;
 A.reset();const asura=P.actors().find(b=>b.path==='asura');asura.hurt(asura.maxHp+1,null,true);
 A.ready('missiles','summon');A.spawn(100,0);A.advance();
 A.assert(!A.actions().some(f=>f.kind==='missiles')&&A.actions().some(f=>f.kind==='summon'),'dead Asura must suppress only missiles');
 A.finish(17.7);A.assert(!asura.dead,'support did not revive');
 A.ready('missiles');A.advance();A.assert(A.actions().some(f=>f.kind==='missiles'),'revived Asura did not resume missiles');out.revive=true;
 return out;
}"""

LIFECYCLE = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out=[];
 for(const reason of ['clear','owner-death','world']){
   A.reset();A.ready('missiles','summon');A.spawn(100,0);A.advance();A.assert(A.actions().length>=2,'lifecycle concurrent fixture absent');
   const world=G.World;
   if(reason==='clear')G.Combat.clearFields();if(reason==='owner-death'){
     const naraka=P.actorsFor(p).find(b=>b.path==='naraka');naraka.hurt(naraka.maxHp+1,null,true);
     p.invuln=0;p.hurt(p.maxHp+1,null,true);
   }if(reason==='world')G.World={...world};
   try{if(reason!=='clear'){A.resume();G.Combat.updateFields(.01);A.pause()}}finally{G.World=world;p.dead=false}
   A.assert(!P.actionsFor(p).length&&!P.shots.length,'concurrent actions leaked '+reason);out.push(reason);
 }
 A.reset();A.ready('missiles','summon');A.spawn(100,0);A.advance();const actions=A.actions(),ages=actions.map(a=>a.age),timers=p.moves.map(m=>m.t);
 G.Combat.tick(.5,p,0);G.Combat.updateFields(.5);
 A.assert(actions.every((a,i)=>a.age===ages[i])&&p.moves.every((m,i)=>m.t===timers[i]),'pause advanced action or ability cooldown');out.push('pause');
 A.reset();return out;
}"""

COLLISION = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out=[];
 for(const k of ['gravity','missiles','summon','soul','planet']){
   A.reset();const es=[A.spawn(160,0),A.spawn(175,18),A.spawn(175,-18)];
   P.actors().forEach((b,i)=>{b.x=-80;b.y=i*5});A.ready(k);
   const W=G.World,saved={isFree:W.isFree,projectileBlock:W.projectileBlock,isWall:W.isWall};
   Object.assign(W,{isFree:x=>x<50,projectileBlock:x=>x>=50&&x<=90?{destructible:false}:false,isWall:x=>x>=50&&x<=90});
   try{A.finish(3.5);A.assert(!A.actions().length&&es.every(e=>e.hp===100000),'automatic damage acquired through solid wall '+k);
     A.assert(P.actors().every(b=>b.x<50),'support crossed wall '+k)}finally{Object.assign(W,saved)}out.push(k);
 }
 A.reset();return out;
}"""

PROGRESSION = r"""() => {
 const A=Acceptance,p=A.p(),ids=['gravity','missiles','absorb','summon','soul','repair','planet'],levels=[3,6,6,9,12,12,15],out=[];
 A.assert(p.level===1&&p.moves.length===1&&p.moves[0].id==='naruto-pain','normal mode needs fresh level-one starter');
 A.spawn(70,0);A.finish(.5);A.assert(!A.actions().length,'unlearned abilities activated');A.reset();
 for(const level of [...new Set(levels)]){
   const group=ids.filter((_,i)=>levels[i]===level);p.level=level-1;
   for(const k of group)A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='new:naruto-pain-'+k),'premature skill '+k);
   p.level=level;
   for(const k of group){const c=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-pain-'+k);
     A.assert(c&&c.apply(p)!==false,'native upgrade cannot learn '+k);A.assert(p.slots.length===0&&p.moves.every(m=>m.passive),'learning added selectable slot '+k);out.push({level,kind:k});}
 }
 A.assert(p.moves.length===8,'normal progression cannot learn entire family');
 const original=p.mon;p.mon=G.DEX.find(m=>m.dex===30009);
 try{A.assert(!G.Moves.poolFor(p.mon).some(id=>id.startsWith('naruto-pain')),'Pain skill pool leaked into another hero')}finally{p.mon=original}
 return out;
}"""


def enter(page):
    page.wait_for_function("window.PS_REDRAWN_READY && G.NarutoPain && document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():
        page.locator('#tap-start').click()
    page.locator('#scr-menu [data-go="play"]').click()
    page.wait_for_function('G.Game.player?.dex===30010 && G.Game.state==="playing"')
    page.evaluate(HARNESS)
    page.evaluate(SETUP)


def game_frame(page):
    # Wait for the real public redirect before choosing the execution frame.
    if 'layout=' not in URL and page.viewport_size['width'] > 600:
        page.wait_for_url(re.compile(r'/portrait\.html\?'))
    page.wait_for_function("window.G?.NarutoPain || [...document.querySelectorAll('iframe#portrait-game')].some(f=>{try{return !!f.contentWindow?.G?.NarutoPain}catch{return false}})")
    return next(f for f in page.frames if f.evaluate('!!window.G?.NarutoPain'))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'failedRequests': [], 'requestFailures': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for label, viewport, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
                context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
                outer = context.new_page()
                outer.on('pageerror', lambda e: report['errors'].append({'message': str(e), 'stack': e.stack}))
                outer.on('response', lambda r: report['failedRequests'].append({'url': r.url, 'status': r.status}) if r.status >= 400 and '127.0.0.1' in r.url else None)
                outer.on('requestfailed', lambda r: report['requestFailures'].append({'url': r.url, 'failure': r.failure}))
                outer.goto(URL)
                page = game_frame(outer)
                enter(page)
                result = report['viewports'][label] = {}
                for name, check in [('beta', BETA), ('concurrent', CONCURRENT), ('decisions', DECISIONS), ('bodies', BODIES), ('passives', PASSIVES), ('collision', COLLISION), ('lifecycle', LIFECYCLE)]:
                    print(label, name, flush=True)
                    result[name] = page.evaluate(check)
                result['hud'] = page.evaluate(HUD)
                page.evaluate('Acceptance.reset();Acceptance.ready("gravity","missiles","summon","soul");Acceptance.spawn(100,0);Acceptance.spawn(110,18);Acceptance.spawn(110,-18);Acceptance.finish(.25)')
                outer.screenshot(path=str(OUT / f'{label}-automatic-combat.png'))
                outer.keyboard.down('KeyD')
                result['keyboardMovement'] = page.evaluate('''() => {const A=Acceptance,p=A.p(),x=p.x;A.resume();p.update(.08);A.pause();A.assert(p.x>x&&p.walking,'keyboard movement failed');return p.x-x}''')
                outer.keyboard.up('KeyD')
                if mobile:
                    page.evaluate('Acceptance.reset();Acceptance.resume()')
                    cdp = context.new_cdp_session(outer)
                    base = page.evaluate('G.Touch.stickBase()')
                    if page != outer.main_frame:
                        bounds = outer.locator('iframe').bounding_box()
                        native = page.evaluate('({w:innerWidth,h:innerHeight})')
                        base = {'x': bounds['x'] + base['x'] * bounds['width'] / native['w'], 'y': bounds['y'] + base['y'] * bounds['height'] / native['h']}
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': base['x'], 'y': base['y']}]})
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': base['x']+45, 'y': base['y']}]})
                    result['touchMovement'] = page.evaluate('''() => {const A=Acceptance,p=A.p(),x=p.x;A.assert(G.Touch.vector()?.[0]>0,'touch vector absent');p.update(.08);A.pause();A.assert(p.x>x,'touch movement failed');return p.x-x}''')
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                result['overflow'] = page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert result['overflow'], 'horizontal overflow'
                outer.goto(URL)
                page = game_frame(outer)
                page.wait_for_function("window.PS_REDRAWN_READY && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('#pain-beta-options summary').click()
                page.locator('[data-pain-mode="normal"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30010 && G.Game.state==="playing"')
                page.evaluate(HARNESS)
                page.evaluate(SETUP)
                result['progression'] = page.evaluate(PROGRESSION)
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
    print(json.dumps({'ok': report['ok'], 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
