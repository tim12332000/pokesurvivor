"""Learned, slotless Rasengan/Rasenshuriken: scheduling, migration, clones and HUD."""
import hashlib
import json
import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/naruto-automatic-attacks'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&layout=wide'

CHECK = r"""() => {
 const p=G.Game.player,R='naruto-naruto',S='naruto-rasenshuriken',assert=(v,m)=>{if(!v)throw Error(m)};
 const equal=(a,b,m)=>assert(Math.abs(a-b)<1e-6,m+': '+a+' != '+b);
 Object.assign(G.World,{isFree:()=>true,isWall:()=>false,isLiquid:()=>false,collide:()=>{},projectileBlock:()=>false,propsInCircle:()=>[]});
 G.Camera.sees=()=>true;
 let time=0,calls=[];
 const nativeCast=p.cast;p.cast=function(m){if(m.autoCast)calls.push({id:m.id,t:time});return nativeCast.call(this,m)};
 function reset(){
  G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();
  p.x=p.y=0;p.aim=0;p.level=30;p.hp=p.maxHp;p.dead=false;p.flash=p.invuln=0;p.cdMul=1;p.quantityBonus=p.quantityPicks=0;p.critChance=0;p.percentHealthDamage=p.lifestealRate=0;
  p.moves=[];p.slots=[];p.bind={};p.active=0;p.maxMoves=4;time=0;calls=[];p.target=null;G.Camera.x=G.Camera.y=0;
 }
 const enemy=(x=80,y=0)=>{const e=new G.Enemy({dex:19,hp:1e9,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];e.touchCd=999;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
 function advance(seconds,owner=p,followTarget=true){
  for(let t=0;t<seconds-1e-8;){const dt=Math.min(.01,seconds-t);
   if(followTarget&&owner.target){owner.target.x=owner.x+80;owner.target.y=owner.y;G.EnemyMgr.rebuildGrid()}
   G.Combat.tick(dt,owner,time);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,time);G.Combat.updateFields(dt);G.FX.update(dt);owner.anim.update(dt);time+=dt;t+=dt;
  }
 }
 reset();p.target=enemy();advance(1);assert(!calls.length,'unlearned attacks fired');
 // Preserve the established learning milestones and Naruto-only pools.
 for(const [level,rasengan,shuriken] of [[1,false,false],[3,true,false],[6,true,true]]){
  p.level=level;const pool=G.Moves.poolFor(p.mon);assert(pool.includes(R)===rasengan&&pool.includes(S)===shuriken,'learning level '+level);
 }
 assert(!G.Moves.poolFor(G.DEX_BY[30002]).includes(R)&&!G.Moves.poolFor(G.DEX_BY[30002]).includes(S),'skills leaked to another ninja');
 reset();p.maxMoves=1;assert(p.addMove('naruto-kunai'),'tool learn');const selected=p.activeGroup();
 for(const id of [R,S]){
  const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);assert(card&&card.apply(p)!==false,'full slots hid learned automatic '+id);
  assert(p.slots.length===1&&p.activeGroup()===selected,'passive learning replaced selection');
 }
 assert(p.moves.filter(m=>m.autoCast).length===2&&!p.slots.some(g=>g.some(m=>m.autoCast)),'automatic attacks occupy slots');
 assert(!p.addMove(R)&&!p.addMove(S),'duplicate learning accepted');
 assert(G.LevelUp.offer(p,100).some(c=>c.key==='up:'+R),'automatic skill cannot upgrade');
 const r=p.moves.find(m=>m.id===R),s=p.moves.find(m=>m.id===S);equal(r.cd,5,'Rasengan base CD');equal(s.cd,6,'Rasenshuriken base CD');
 p.target=enemy();r.t=s.t=0;advance(.01);assert(calls.length===1&&calls[0].id===R,'ready attacks must queue without interrupting charge');
 const live=G.DigimonSkills.rasenganFor(p);assert(live,'passive Rasengan missing');advance(.3);assert(G.DigimonSkills.rasenganFor(p)===live,'unselected Rasengan cancelled');
 advance(1);assert(calls.some(c=>c.id===S),'queued Rasenshuriken never released');
 advance(12);const ordinary=calls.slice();
 for(const [id,cd] of [[R,5],[S,6]]){
  const events=calls.filter(c=>c.id===id);assert(events.length>=2,'automatic repeat missing '+id);
  for(let i=1;i<events.length;i++)assert(events[i].t-events[i-1].t>=cd-.015,'cooldown shortened '+id);
 }
 // The two skills continue with no selectable moves at all, including cooldown reduction.
 reset();p.addMove(R);p.addMove(S);assert(!p.slots.length,'zero-slot fixture');p.cdMul=.5;p.target=enemy();advance(7);
 const reduced=calls.slice();for(const [id,minimum] of [[R,2.5],[S,3]]){
  const es=calls.filter(c=>c.id===id);assert(es.length>=2,'reduced repeat missing '+id);
  assert(es[1].t-es[0].t<minimum+.1,'cooldown reduction ignored '+id);
  assert(es[1].t-es[0].t>=minimum-.015,'cooldown reduction double-applied '+id);
 }
 const timers=p.moves.map(m=>m.t),count=calls.length;G.Combat.tick(0,p,time);assert(calls.length===count&&p.moves.every((m,i)=>m.t===timers[i]),'zero dt advanced automatic attacks');
 reset();p.addMove(R);p.addMove(S);advance(.2);assert(!calls.length&&p.moves.every(m=>m.t<=.05),'no-target cast consumed cooldown');
 p.target=enemy(1000,0);advance(.1,p,false);assert(!calls.length,'out-of-range target triggered');
 p.dead=true;p.target.x=80;advance(.1,p,false);assert(!calls.length,'dead actor cast');
 reset();p.addMove(R);const distant=enemy(300,0);enemy(0,80);p.target=distant;p.aim=0;G.Combat.tick(.01,p,time);
 const closeCast=G.DigimonSkills.rasenganFor(p);assert(closeCast,'selected weapon target prevented in-range automatic attack');
 equal(closeCast.aim,Math.PI/2,'independent automatic aim');assert(p.target===distant&&p.aim===0,'automatic targeting replaced selected weapon aim');
 // Migrate live legacy/fused slots without changing objects, upgrades, selection or cooldown fraction.
 reset();const tool=G.Moves.instance('naruto-kunai'),oldR=G.Moves.instance(R,3),oldS=G.Moves.instance(S,3);
 Object.assign(oldR,{autoCast:false,passive:false,cd:1.8,t:.9,dmg:77});Object.assign(oldS,{autoCast:false,passive:false,cd:2.25,t:1.125});
 delete oldR.cloneDashRange;oldR.range=125;
 const fused=[oldR,tool];p.moves=[oldR,tool,oldS];p.slots=[fused,[oldS]];p.active=0;p.bind={[R]:0,[S]:1,'naruto-kunai':3};p.arrange();
 assert(p.moves[0]===oldR&&oldR.dmg===77&&p.activeGroup()===fused&&fused.length===1&&fused[0]===tool,'legacy object or fused selection lost');
 equal(oldR.cd,4.5,'upgraded Rasengan CD');equal(oldS.cd,5.4,'upgraded shuriken CD');equal(oldR.t,2.25,'legacy R cooldown fraction');equal(oldS.t,2.7,'legacy S cooldown fraction');
 equal(oldR.range,80,'legacy contact reach');equal(oldR.cloneDashRange,125,'legacy clone dash reach');
 equal(G.Moves.instance(R,4).range,89.6,'contact range upgrade');equal(G.Moves.instance(R,4).cloneDashRange,140,'clone dash range upgrade');
 assert(p.bind[R]==null&&p.bind[S]==null&&p.bind['naruto-kunai']===3,'legacy bindings not repaired');
 G.NarutoSkillCatalog.migrateNarutoAutomatic(p);equal(oldR.t,2.25,'migration reset timer');
 // Real shadow actors independently use BOTH learned attacks without selection.
 reset();p.addMove(R);p.addMove(S);p.addMove('naruto-kunai');
 for(let i=0;i<8;i++){const a=i*Math.PI/4;enemy(Math.cos(a)*125,Math.sin(a)*125)}
 assert(G.NarutoClones.cast(p,G.Moves.instance('naruto-shadow-clones')),'clone summon failed');
 for(let t=0;t<2;t+=.01)G.Combat.updateFields(.01);
 const clones=G.NarutoClones.actors;assert(clones.length===8&&clones.every(a=>a.cooldowns.get(R)>0&&a.cooldowns.get(S)>0),'shadow actors did not cast both learned attacks');
 const cloneCooldowns=clones.map(a=>({rasengan:a.cooldowns.get(R),rasenshuriken:a.cooldowns.get(S)}));
 // A permanent card clone inherits automatic skills, including the zero-slot case.
 reset();p.addMove(R);p.addMove(S);const card=G.LevelUp.STATS.find(c=>c.id==='selfClone').apply(p);assert(card&&!card.slots.length,'card clone inherited phantom slots');
 const castCard=card.cast,cardEvents=[];card.cast=function(m){if(m.autoCast)cardEvents.push(m.id);return castCard.call(this,m)};card.target=enemy(card.x+80,card.y);card.aim=0;advance(1.3,card);
 assert(cardEvents.includes(R)&&cardEvents.includes(S),'card clone automatic attacks missing');
 G.Combat.clearFields(card);assert(!G.DigimonSkills.rasenganFor(card),'card clear retained cast');
 // Leave the ordinary tool selected while both learned automatic attacks appear on the real HUD.
 reset();p.addMove('naruto-kunai');p.addMove(R);p.addMove(S);p.target=enemy();advance(.35);
 const canvas=document.getElementById('game'),ctx=canvas.getContext('2d'),fillText=ctx.fillText,labels=[];
 ctx.fillText=function(text,...args){labels.push(String(text));return fillText.call(this,text,...args)};
 window.autoAttackHUD={labels,restore(){ctx.fillText=fillText}};
 p.cast=nativeCast;
 return {baseCooldowns:{rasengan:5,rasenshuriken:6},ordinary,reduced,cloneCooldowns,cardEvents,
  checks:['learned only','levels 3/6','Naruto-only pool','full-slot learning','no active slots','selection preserved','upgrades','queued release','repeat','cooldown reduction','zero dt','no target','out of range','independent automatic targeting','death','legacy fused-slot migration','legacy timer preservation','both techniques on eight shadow actors','permanent card clone','card clear']};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reports = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for locale,mobile in (('zh-TW',False),('zh-TW',True),('en',False)):
            context = browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1100,'height':850},
                                          is_mobile=mobile, has_touch=mobile, locale=locale, service_workers='block')

            def route(request):
                file = ROOT / unquote(urlsplit(request.request.url).path).removeprefix('/pokesurvivor/')
                request.fulfill(status=200 if file.is_file() else 404, body=file.read_bytes() if file.is_file() else b'Not found',
                                content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')

            context.route('https://tim12332000.github.io/pokesurvivor/**', route)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            target=URL.replace('lang=zh-TW','lang='+locale)
            page.goto(target.replace('digimon.html','portrait.html').replace('layout=wide','layout=portrait') if mobile else target)
            view = page
            if mobile:
                page.wait_for_selector('#portrait-game')
                view = page.locator('#portrait-game').element_handle().content_frame()
            view.wait_for_function('window.PS_REDRAWN_READY && G.Flow && document.getElementById("boot").classList.contains("hidden")')
            if view.locator('#tap-start').is_visible():
                view.locator('#tap-start').click()
            view.evaluate("""async()=>{await PS_REDRAWN_READY;G.Naruto.choose(30001);await G.Flow.play();if(G.Game.state==='playing')G.Game.togglePause();G.UI.hideAll();document.getElementById('tap-start').style.display='none';document.querySelectorAll('.toast,#ach-pop').forEach(e=>e.style.display='none')}""")
            report = view.evaluate(CHECK)
            page.wait_for_timeout(120)
            hud = view.evaluate("""()=>{const a=autoAttackHUD;const labels=a.labels.slice();a.restore();return labels}""")
            automatic='AUTO' if locale=='en' else '自動'
            assert hud.count(automatic) >= 2, hud
            if locale=='en':
                descriptions=view.evaluate("[G.Moves.BY_ID['naruto-naruto'].desc,G.Moves.BY_ID['naruto-rasenshuriken'].desc]")
                assert all(text.startswith('Automatically casts once learned') for text in descriptions), descriptions
            assert any(label.endswith('s') for label in hud), hud
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'Viewport overflow'
            key = ('mobile' if mobile else 'desktop')+('-en' if locale=='en' else '')
            page.screenshot(path=str(OUT/(key+'.png')))
            assert not errors, errors
            report['errors'] = errors
            report['hudAutomaticLabels'] = hud.count(automatic)
            reports[key] = report
            context.close()
        browser.close()
    reports['combatSHA256'] = hashlib.sha256((ROOT/'.omx/digimon-skill-combat.js').read_bytes()).hexdigest()
    (OUT/'report.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'cases':[key for key in reports if key!='combatSHA256'],'baseCooldowns':reports['desktop']['baseCooldowns']}))


if __name__ == '__main__':
    main()
