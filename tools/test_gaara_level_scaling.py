"""Native browser regression for character-level Gaara scaling and multi-target coffin."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS, SETUP, PROGRESSION, UPGRADES

OUT = Path(__file__).resolve().parents[1] / '.omx/state/gaara-level-scaling'

SCALING = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,out={counts:[],damage:[],lifecycle:[]};
 const coffin=p.moves.find(m=>m.id==='naruto-sand-coffin'),shower=p.moves.find(m=>m.id==='naruto-gaara');
 const original={level:p.level,atk:p.atk,quantity:p.quantityBonus},wall=G.World.isWall;
 const observe=e=>{const state={hits:0,raw:0},hurt=e.hurt;e.hurt=function(amount,...args){state.hits++;state.raw+=amount;return hurt.call(this,amount,...args)};return state};
 try{
 for(const level of [1,9,25,100])for(const bonus of [0,20,80]){
   A.gaaraArena();p.level=level;p.quantityBonus=bonus;
   const targets=Array.from({length:31},(_,i)=>A.spawn(50+i*3,Math.sin(i)*25));targets[30].elite=true;
   const outside=A.spawn(400,0),hidden=A.spawn(210,0);G.World.isWall=(x,y)=>x>=180&&x<=184;
   const hits=targets.map(observe);const m=A.actualCast(coffin.id),f=N.active(p),count=Math.min(1+level,10)+Math.min(20,bonus);
   A.assert(f.count===count&&f.targets.length===count&&f.target===targets[30],'coffin count/priority '+level+'/'+bonus);
   const chosen=f.targets.slice();A.advance(.22+1.09);
   A.assert(hits.every(s=>s.hits===0),'coffin hit before full bind');
   A.advance(.011);A.assert(chosen.every(e=>e.hp<100000),'coffin omitted selected target');A.finish();A.advance(1);
   A.assert(targets.every((e,i)=>hits[i].hits===(chosen.includes(e)?1:0))&&outside.hp===100000&&hidden.hp===100000,'coffin outside/cap/duplicate '+level+'/'+bonus);
   A.assert(targets.every(e=>e.slow===0),'coffin leaked control after finish');
   out.counts.push({level,bonus,count,hits:hits.reduce((n,s)=>n+s.hits,0)});G.World.isWall=wall;
 }
 for(let tier=1;tier<=5;tier++){
   if(tier>1)for(const id of [coffin.id,shower.id]){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(card&&card.apply(p)!==false,'missing real scaling upgrade '+id+'/'+tier)}
   for(const id of [coffin.id,shower.id])for(const level of [1,9,25]){
     A.gaaraArena();p.level=level;p.atk=2.3;const e=A.spawn(180,0),s=observe(e);p.target=e;
     const m=A.actualCast(id),f=N.active(p),expected=(m.dmg+level)*p.atk*G.Types.mult(m.type,e.types)*G.Weather.mult(m.type);
     A.assert(f.move.dmg===m.dmg+level,'character damage snapshot missing');
     p.level=level+7;A.finish();A.advance(2);
     A.assert(Math.abs(s.raw-expected)<1e-5,'damage scaling doubled or changed midcast '+id+'/'+tier+'/'+level+' '+s.raw+'/'+expected);
     A.assert(s.hits===(id===coffin.id?1:m.count),'per-target hit count wrong');
     A.gaaraArena();p.target=A.spawn(180,0);A.actualCast(id);A.assert(N.active(p).move.dmg===m.dmg+level+7,'next cast omitted new level');A.finish();
     out.damage.push({id,tier,level,raw:s.raw});
   }
 }
 for(const reason of ['dead-primary','wall-primary','switch','clear','owner-death','world','owner','pause']){
   A.gaaraArena();p.level=9;p.atk=1;
   const primary=A.spawn(80,0),survivor=A.spawn(0,100);primary.elite=true;survivor.applySlow(.2,5);
   const sp=observe(primary),ss=observe(survivor);A.actualCast(coffin.id);A.advance(.3);const f=N.active(p),age=f.age;
   const late=A.spawn(20,80),world=G.World,game=G.Game;
   if(reason==='dead-primary')primary.dead=true;
   if(reason==='wall-primary')G.World.isWall=(x,y)=>x>=40&&x<=44&&Math.abs(y)<5;
   if(reason==='switch')A.select(shower.id);
   if(reason==='clear')G.Combat.clearFields(p);
   if(reason==='owner-death')p.dead=true;
   if(reason==='world')G.World={...world};
   if(reason==='owner')G.Game={...game,get state(){return game.state},player:{...p}};
   try{
     if(reason==='pause'){G.Combat.updateFields(1);A.assert(f.age===age&&sp.hits===0&&ss.hits===0,'pause advanced multi coffin');A.select(shower.id)}
     else A.advance(.01);
     if(reason==='dead-primary'||reason==='wall-primary'){
       A.assert(N.active(p)?.targets.length===1&&primary.slow===0,'removed primary retained control or cancelled survivor');A.finish();
       A.assert(ss.hits===1&&sp.hits===0&&late.hp===100000,'survivor missing or target list expanded');
     }else {A.assert(!N.active(p)&&primary.slow===0&&Math.abs(survivor.slow-.2)<1e-6,'multi cleanup lost controls '+reason);A.advance(3);A.assert(ss.hits===0&&sp.hits===0,'cleanup delayed damage '+reason)}
     A.assert(Math.abs(survivor.slow-.2)<1e-6,'survivor baseline slow lost '+reason);out.lifecycle.push(reason);
   }finally{G.World=world;G.Game=game;G.World.isWall=wall;p.dead=false}
 }
 }finally{p.level=original.level;p.atk=original.atk;p.quantityBonus=original.quantity;G.World.isWall=wall;A.gaaraArena()}
 return out;
}"""

PRISON_DURATION = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,id='naruto-sand-prison';p.level=12;
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'prison learn');
 A.gaaraArena();p.cdMul=1;p.quantityBonus=20;const e=A.spawn(170,0);let hits=0;const hurt=e.hurt;e.hurt=function(...args){hits++;return hurt.apply(this,args)};
 A.select(id);A.advance(6);A.advance(4);A.assert(N.sandPrisonState(p)?.age===4&&hits===8&&N.rooted(e),'prison not active at four seconds');
 A.advance(.999);A.assert(N.sandPrisonState(p)&&hits===9,'prison expired before five seconds');
 A.advance(.001);A.assert(!N.sandPrisonState(p)&&hits===10&&!N.rooted(e),'five-second final tick/release');
 A.advance(.99);A.assert(!N.sandPrisonState(p)&&hits===10,'prison extra late tick or changed six-second period');
 A.advance(.01);A.assert(N.sandPrisonState(p)?.age===0&&hits===10,'prison next field must begin at six seconds');
 return {duration:5,ticks:hits,period:6,quantityDoesNotMultiply:true};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report={'errors':[], 'viewports':{}}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            for mobile in [False,True]:
                label='mobile' if mobile else 'desktop'
                context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
                page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
                page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click();page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(PROGRESSION)
                result={'scaling':page.evaluate(SCALING),'prison':page.evaluate(PRISON_DURATION)};report['viewports'][label]=result
                result['coffinCapture']=page.evaluate("""()=>{const A=Acceptance,p=A.p();A.gaaraArena();p.level=9;[[65,-60],[115,0],[65,60]].forEach(([x,y])=>A.spawn(x,y));A.actualCast('naruto-sand-coffin');A.advance(.7);return {targets:G.NarutoGaara.active(p).targets.length,phase:G.NarutoGaara.active(p).phase}}""")
                page.locator('#game').screenshot(path=str(OUT/f'{label}-multi-coffin.png'))
                result['prisonCapture']=page.evaluate("""()=>{const A=Acceptance,p=A.p();A.gaaraArena();p.cdMul=1;A.select('naruto-sand-prison');A.spawn(120,0);A.advance(10);return {age:G.NarutoGaara.sandPrisonState(p).age}}""")
                page.locator('#game').screenshot(path=str(OUT/f'{label}-prison-four-seconds.png'));context.close()
            browser.close()
        assert not report['errors'],report['errors'];report['ok']=True
    except Exception as e:
        report['ok']=False;report['failure']=str(e);raise
    finally:(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'evidence':str(OUT)}))

if __name__=='__main__':main()
