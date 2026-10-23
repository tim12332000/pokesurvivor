"""Browser checks for shadow clone actors, training choices and lifecycle."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
import json
import mimetypes
import os

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=naruto-shadow-clones'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(locale='zh-TW',viewport={'width':1280,'height':820},service_workers='block')
    if os.environ.get('PAGES_LIVE')!='1':
        def proxy(route):
            file=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            if file.is_file():route.fulfill(status=200,body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            else:route.fulfill(status=404,body='Not found')
        context.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    page=context.new_page();errors=[];missing=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:missing.append(r.url) if r.status>=400 else None)
    page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY && G.SelfClones && document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    out=ROOT/'.omx/state/naruto-rasengan'
    out.mkdir(parents=True,exist_ok=True)
    page.evaluate("""async () => {G.Naruto.choose(30001);await G.Flow.play();if(G.Game.state==='playing')G.Game.togglePause();G.UI.hideAll();}""")
    result=page.evaluate("""() => {
      const assert=(v,m)=>{if(!v)throw Error(m)},p=G.Game.player,D=G.DigimonSkills,id='naruto-naruto';
      const reset=()=>{G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();G.FX.clear();p.flash=0;p.x=p.y=0;p.hp=p.maxHp;p.dead=false;p.invuln=0;p.cdMul=1;p.quantityBonus=0;p.critChance=0;p.percentHealthDamage=0;p.lifestealRate=0;p.moves=[];p.slots=[];p.bind={};p.active=0;p.addMove(id);p.aim=0;G.Camera.x=G.Camera.y=0;Object.assign(G.World,{isFree:()=>true,collide:()=>{},projectileBlock:()=>false,isWall:()=>false,isLiquid:()=>false});return p.moves[0]};
      const enemy=(x,y,boss=false)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:5,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
      const step=t=>{for(let a=0;a<t-1e-9;){const d=Math.min(.01,t-a);G.Combat.updateFields(d);a+=d}};
      let m=reset();
      assert(m.charge===.6,'extended charge');assert(m.cd===2&&G.Moves.instance(id,3).cd===1.8,'Rasengan cooldown progression');
      const main=enemy(80,0),sides=[enemy(125,65),enemy(170,-40),enemy(100,-65)],outside=enemy(125,165),boss=enemy(125,60,true);
      const before=main.hp,sideHP=sides.map(e=>e.hp),hp=p.hp;
      assert(D.cast(p,m),'cast failed');assert(D.rasenganFor(p).phase==='charge'&&p.x===0,'windup missing');
      step(.4);assert(p.x===0&&D.rasenganFor(p).phase==='charge','charge did not last 0.6 seconds');
      const input=G.Input.axis;G.Input.axis=()=>[1,0];try{p.update(.01)}finally{G.Input.axis=input;}assert(p.x===0&&p.y===0,'charge moved with input');
      step(.21);assert(p.x>0&&p.x<125,'no continuous travel');
      p.hurt(10);assert(p.hp===hp,'dash hurt protection missing');
      step(.16);assert(D.rasenganFor(p).phase==='impact','impact missing');
      assert(main.hp<before,'no primary damage');const damage=before-main.hp;
      assert(sides.every((e,i)=>e.hp===sideHP[i]),'shockwave duplicated damage');
      assert(sides.every(e=>(e.x-p.x)*e.kx+(e.y-p.y)*e.ky>0),'three surrounding enemies not pushed outward');
      assert(outside.kx===0&&outside.ky===0,'outside enemy pushed');
      for(const e of sides){const d=Math.hypot(e.x-p.x,e.y-p.y);e.update(.1,p);assert(Math.hypot(e.x-p.x,e.y-p.y)>d+10,'nearby enemy did not actually move away');}
      assert(boss.kx===0&&boss.ky===0,'boss launched');
      const endX=p.x;p.hurt(10);assert(p.hp===hp&&p.invuln>=.49,'arrival protection missing');
      step(.4);assert(!D.rasenganFor(p)&&main.hp===before-damage,'repeated damage or stuck recovery');
      for(let i=0;i<60;i++)p.update(.01);p.hurt(10);assert(p.hp<hp,'protection never expired');
      m=reset();G.World.isFree=(x,y,r)=>x+r<60;D.cast(p,m);step(.85);assert(p.x+p.r<60,'crossed wall');
      m=reset();const blocked=enemy(125,65);G.World.isFree=(x,y,r)=>!(x>100&&y>25);D.cast(p,m);step(.8);assert(blocked.kx===0&&blocked.ky===0,'shock crossed wall');
      m=reset();D.cast(p,m);step(.06);p.addMove('naruto-rasenshuriken');step(.4);assert(!D.rasenganFor(p)&&p.x===0,'switch did not cancel charge');
      m=reset();D.cast(p,m);step(.62);const deathX=p.x;p.dead=true;step(.5);assert(!D.rasenganFor(p)&&p.x===deathX,'death retained dash');
      m=reset();D.cast(p,m);G.Combat.clearFields();step(.5);assert(!D.rasenganFor(p)&&p.x===0,'clear retained dash');
      m=reset();p.target=enemy(80,0);p.moves[0].t=0;G.Combat.tick(.01,p,0);assert(D.rasenganFor(p)&&m.t>1,'native automatic cast failed');step(.1);const state=D.rasenganFor(p);assert(state.phaseAge<.11&&p.x===0,'charge moved prematurely');
      window.rasenganStep=step;
      return {damage,endX,checks:['charge','continuous dash','single path hit','three nearby enemies pushed','outside unaffected','boss resistance','dash immunity','arrival protection','protection expires','wall collision','shock line of sight','switch cancel','death','clear']};
    }""")
    for phase,dt in [('charge',0),('charge-ready',.35),('dash',.2),('impact',.18)]:
        if dt:page.evaluate('t=>rasenganStep(t)',dt)
        page.wait_for_timeout(100)
        page.screenshot(path=str(out/(phase+'.png')))
    page.set_viewport_size({'width':390,'height':844})
    page.evaluate("""() => {G.Combat.clearFields();G.FX.clear();G.EnemyMgr.clear();const p=G.Game.player;p.x=p.y=0;p.flash=p.invuln=0;p.aim=0;G.DigimonSkills.cast(p,p.moves[0]);rasenganStep(.68);}""")
    page.wait_for_timeout(120)
    page.screenshot(path=str(out/'mobile-dash.png'))
    assert not errors,errors
    (out/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result));browser.close()
