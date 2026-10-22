"""Native repeatable Giant cards, authored sprite scaling and run reset."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/giant'
CHECK = r"""dex => {
 G.Naruto.choose(dex);G.Flow.play();Acceptance.pause();Acceptance.arena();
 const p=G.Game.player,near=(a,b)=>{if(Math.abs(a-b)>1e-7*Math.max(1,Math.abs(b)))throw Error(a+' != '+b)};
 const definition=G.LevelUp.STATS.find(c=>c.id==='giant');
 if(!definition||definition.max||definition.icon!=='giant')throw Error('repeatable card missing');
 const art=G.Icons.UI.giant;
 if(!art||art.rows.length!==12||art.rows.some(r=>r.length!==12))throw Error('invalid giant icon');
 for(const icon of ['heart','healthGrowth','lifesteal'])if(G.Icons.url(icon)===G.Icons.url('giant'))throw Error('duplicate giant icon');
 const base={hp:p.maxHp,spd:p.spd,cd:p.cdMul,r:p.r,h:p.bodyH,scale:p.anim.scale,atk:p.atk,slots:p.slots.length};
 const snapshot=()=>{
   const c=document.createElement('canvas');c.width=400;c.height=400;
   p.anim.draw(c.getContext('2d'),200,380);
   const pixels=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
   let left=400,right=0,top=400,bottom=0;
   for(let y=0;y<400;y++)for(let x=0;x<400;x++)if(pixels[(y*400+x)*4+3]){left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y)}
   return {canvas:c,width:right-left+1,height:bottom-top+1};
 };
 p.anim._start('Idle',false);const images=[snapshot()];
 for(let n=1;n<=6;n++){
   p.hp=p.maxHp/2;const previous=p.maxHp,hp=p.hp;
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:giant');
   if(!card||card.apply(p)===false)throw Error('card unavailable after pick '+n);
   near(p.maxHp,base.hp*1.25**n);near(p.hp,hp+previous*.25);
   near(p.spd,base.spd*.9**n);near(p.cdMul,base.cd/.9**n);
   near(p.r,base.r*1.25**n);near(p.bodyH,base.h*1.25**n);near(p.anim.scale,base.scale*1.25**n);
   near(p.atk,base.atk);near(G.Giant.interval(p),1/.9**n);
   if(p.statsTaken.giant!==n||p.slots.length!==base.slots)throw Error('card bookkeeping');
   if(n===1||n===6)images.push(snapshot());
 }
 const ratio=images[2].height/images[0].height;
 if(Math.abs(ratio-1.25**6)>.08)throw Error('authored sprite did not scale: '+ratio);
 if(!G.RunAttributes.rows(p).some(r=>r.id==='giant'))throw Error('run summary missing Giant');
 const max=p.maxHp,r=p.r;G.LevelUp.STATS.find(c=>c.id==='maxHealthPercent').apply(p);near(p.maxHp,max*1.1);near(p.r,r);
 const cd=p.cdMul,spd=p.spd;G.LevelUp.STATS.find(c=>c.id==='cd').apply(p);near(p.cdMul,cd*.92);
 G.LevelUp.STATS.find(c=>c.id==='spd').apply(p);near(p.spd,spd*1.07);
 let guardianInterval=null;
 if(dex===30007){
   p.addMove('naruto-sand-shield');const shield=G.NarutoGaara.shieldState(p).capacity;
   definition.apply(p);near(G.NarutoGaara.shieldState(p).capacity-shield,max*1.1*.25*2);
   G.Combat.clearFields();G.EnemyMgr.clear();
   const target=Acceptance.enemy(0,60),group=G.NarutoSandGuard.state(p),times=[];
   group.guardians.forEach((s,i)=>{s.x=target.x;s.y=target.y;s.ready=i===0;s.charges=i===0?1:0});
   let time=0,firstCooldown=null;const hurt=target.hurt;
   target.hurt=function(...args){times.push(time);return hurt.apply(this,args)};
   for(let i=0;i<500&&times.length<2;i++){
     time+=.01;Acceptance.resume();try{G.Combat.resolve(.01,p,0)}finally{Acceptance.pause()}
     if(times.length===1&&firstCooldown===null)firstCooldown=group.guardians[0].attackCooldown;
   }
   guardianInterval=times[1]-times[0];
   if(times.length!==2||Math.abs(firstCooldown-G.Giant.interval(p))>.02||guardianInterval<G.Giant.interval(p)-.02)throw Error('guardian ignored attack-speed penalty '+JSON.stringify({times,firstCooldown}));
 }
 const canvas=document.createElement('canvas');canvas.width=1200;canvas.height=450;const ctx=canvas.getContext('2d');
 ctx.fillStyle='#101820';ctx.fillRect(0,0,1200,450);ctx.imageSmoothingEnabled=false;
 for(let i=0;i<3;i++){ctx.drawImage(images[i].canvas,i*400,0);ctx.fillStyle='#cdd8ef';ctx.font='16px sans-serif';ctx.fillText(['0 cards','1 card','6 cards'][i],i*400+154,422);}
 G.Icons.draw(ctx,'giant',14,14,36);window.GiantEvidence=canvas.toDataURL();
 G.Game.startRun();Acceptance.pause();const fresh=G.Game.player;
 if(fresh===p||fresh.giantPicks||fresh.statsTaken.giant)throw Error('Giant leaked into new run');
 near(fresh.anim.scale,base.scale);near(fresh.r,base.r);near(fresh.bodyH,base.h);
 return {dex,picks:6,size:1.25**6,hp:base.hp*1.25**6,moveSpeed:.9**6,attackSpeed:.9**6,spriteHeightRatio:ratio,guardianInterval,reset:true};
}"""

def main():
    import base64
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in [False, True]:
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && G.Giant && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.evaluate(HARNESS)
            label = 'mobile' if mobile else 'desktop'
            report[label] = [page.evaluate(CHECK, dex) for dex in [30001, 30002, 30006, 30007]]
            (OUT / f'{label}.png').write_bytes(base64.b64decode(page.evaluate('window.GiantEvidence').split(',')[1]))
            assert not errors, errors
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, **report}))

if __name__ == '__main__':
    main()
