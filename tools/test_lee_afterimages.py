"""Real Eight Gates afterimages: input, historical sprites, pixels and lifecycle."""
import base64
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/lee-afterimages'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=lee-afterimages'

HELPERS = r"""() => {
 const A=Acceptance,origins=new WeakMap(),draw=CanvasRenderingContext2D.prototype.drawImage;
 const sourceOf=image=>image.src?[image.src]:(origins.get(image)||[]);
 CanvasRenderingContext2D.prototype.drawImage=function(image,...args){
   origins.set(this.canvas,[...new Set([...(origins.get(this.canvas)||[]),...sourceOf(image)])]);
   return draw.call(this,image,...args);
 };
 A.trailStep=(dt=.02)=>{const p=A.p();A.resume();try{p.update(dt);G.Combat.updateFields(dt)}finally{A.pause()}};
 A.trailState=()=>G.NarutoGates.afterimages.map(s=>({x:s.x,y:s.y,life:s.life,ttl:s.ttl,scale:s.scale}));
 A.trailCapture=()=>{
   const p=A.p(),canvas=document.createElement('canvas');canvas.width=600;canvas.height=260;
   const ctx=canvas.getContext('2d',{willReadFrequently:true}),calls=[],original=ctx.drawImage.bind(ctx);
   ctx.drawImage=function(image,...args){calls.push({sources:sourceOf(image),width:image.width,height:image.height,args});return original(image,...args)};
   ctx.save();ctx.translate(460-p.x,205-p.y);G.Combat.drawGroundFields(ctx);ctx.restore();
   const pixels=ctx.getImageData(0,0,600,260).data;let count=0,x0=600,x1=-1,y0=260,y1=-1,maxAlpha=0,checksum=0;
   for(let y=0;y<260;y++)for(let x=0;x<600;x++){const k=(y*600+x)*4,r=pixels[k],g=pixels[k+1],b=pixels[k+2],a=pixels[k+3];
     if(a>8&&r>80&&r>g*1.5&&r>b*1.3){count++;maxAlpha=Math.max(maxAlpha,a);checksum=(checksum+((k+1)*a))%2147483647;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}}
   A.assert(count>50&&calls.length>0,'no real red historical sprites rendered');
   A.assert(calls.some(c=>c.sources.some(src=>/lee-gates-(common|skills)-v1\.png/.test(src))),'afterimage silhouette not derived from actual Lee artwork');
   A.assert(maxAlpha<255,'red afterimages became opaque');
   const footprint={width:x1-x0+1,height:y1-y0+1,pixels:count,maxAlpha,checksum,bounds:[x0,y0,x1,y1]};
   A.assert(x0>0&&y0>0&&x1<599&&y1<259,'afterimage evidence clipped');
   // Compose exactly as the game: historical ground sprites, current player, air aura.
   ctx.save();ctx.translate(460-p.x,205-p.y);p.draw(ctx);G.Combat.drawAirFields(ctx);ctx.restore();
   const preview=document.createElement('canvas');preview.width=canvas.width;preview.height=canvas.height;
   const background=preview.getContext('2d');background.fillStyle='#17422b';background.fillRect(0,0,preview.width,preview.height);background.drawImage(canvas,0,0);
   return {footprint,calls,snapshots:A.trailState(),png:preview.toDataURL()};
 };
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report={'errors':[],'failedRequests':[],'viewports':{}}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            for mobile in (False, True):
                label='mobile' if mobile else 'desktop'
                ctx=browser.new_context(locale='zh-TW',viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
                page=ctx.new_page()
                page.on('pageerror',lambda e:report['errors'].append(str(e)))
                page.on('response',lambda r:report['failedRequests'].append(r.url) if r.status>=400 and '127.0.0.1' in r.url else None)
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY&&G.AnimationLab&&G.NarutoGates?.afterimages&&document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30006"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
                page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(HELPERS)
                page.evaluate("() => {const p=Acceptance.p();p.level=6;const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-gates');Acceptance.assert(card&&card.apply(p)!==false,'learn gates');}")
                result={'stages':{}}
                report['viewports'][label]=result
                for level in (1,5):
                    page.evaluate(r"""level=>{const A=Acceptance,p=A.p();A.leeArena();
                      const m=p.moves.find(m=>m.id==='naruto-gates');while(m.lvl<level){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:naruto-gates');A.assert(card&&card.apply(p)!==false,'upgrade trail stage')}
                      A.advance(.6);A.trailBaseline={hp:p.hp,atk:p.atk,spd:p.spd,damage:p.dmgDealt};
                    }""",level)
                    if mobile:
                        page.evaluate('Acceptance.resume()')
                        client=ctx.new_cdp_session(page)
                        base=page.evaluate('G.Touch.stickBase()')
                        client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':base['x'],'y':base['y']}]})
                        client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':base['x']+45,'y':base['y']}]})
                    else:page.keyboard.down('KeyD')
                    stage=page.evaluate(r"""() => {const A=Acceptance,p=A.p(),x=p.x;A.assert(G.Input.axis()[0]>0,'actual movement input missing');
                      for(let n=0;n<40;n++)A.trailStep(.02);
                      A.assert(p.x>x+10,'actual Player.update did not move');
                      const shots=A.trailState();A.assert(shots.length>0,'moving gates emitted no afterimages');
                      A.assert(shots.every(s=>s.x<p.x+.001)&&shots.some(s=>s.x<p.x-2),'afterimages did not trail real historical positions');
                      A.assert(p.hp===A.trailBaseline.hp&&p.atk===A.trailBaseline.atk&&p.spd===A.trailBaseline.spd&&p.dmgDealt===A.trailBaseline.damage,'visual trail altered gameplay stats/damage');
                      const shot=A.trailCapture(),dir=p.anim.dir,cur=p.anim.cur;
                      p.anim.dir=6;p.anim.play('Attack');const turned=A.trailCapture();
                      A.assert(turned.footprint.checksum===shot.footprint.checksum,'turn redrew historical sprite poses');p.anim.dir=dir;p.anim.play(cur);
                      shot.frozenHistoricalPoses=true;
                      const before=JSON.stringify(A.trailState());G.Combat.updateFields(.5);
                      A.assert(JSON.stringify(A.trailState())===before,'paused simulation expired trails');shot.pausePreserves=true;return shot;
                    }""")
                    if mobile:
                        client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});client.detach()
                    else:page.keyboard.up('KeyD')
                    (OUT/f'{label}-stage{level}.png').write_bytes(base64.b64decode(stage.pop('png').split(',',1)[1]))
                    result['stages'][str(level)]=stage
                    stage['fade']=page.evaluate("() => {for(let n=0;n<30;n++)Acceptance.trailStep(.02);Acceptance.assert(!G.NarutoGates.afterimages.length,'stationary trails did not fade');return true}")
                result['stageGrowth']=page.evaluate(r"""stages=>{const A=Acceptance,small=stages['1'].footprint,big=stages['5'].footprint;
                  A.assert(big.height>small.height*1.15,'higher gate did not enlarge actual silhouette height');
                  A.assert(big.pixels>small.pixels,'higher gate did not increase red footprint');return {small,big};
                }""",result['stages'])
                # Refill real moving history for each lifecycle boundary.
                page.keyboard.down('KeyD')
                result['cleanup']=page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p(),g=G.NarutoGates,out=[];
                  const refill=()=>{A.leeArena();A.advance(.6);for(let n=0;n<20;n++)A.trailStep(.02);A.assert(g.afterimages.length,'cleanup fixture did not emit')};
                  for(const reason of ['clear','death','world']){
                    refill();const world=G.World;
                    if(reason==='clear')G.Combat.clearFields(p);
                    if(reason==='death'){p.dead=true;A.trailStep(.01)}
                    if(reason==='world'){G.World={...world};A.trailStep(.01)}
                    A.assert(!g.afterimages.length,'trail leaked through '+reason);out.push(reason);G.World=world;p.dead=false;p.hp=p.maxHp;
                  }
                  for(const method of ['clearFields','direct-clear'])for(const mode of ['playing','paused']){
                    refill();if(mode==='playing')A.resume();else A.pause();
                    if(method==='clearFields')G.Combat.clearFields(p);else g.clear(p);
                    // Deliberately draw immediately: no update may recreate state first.
                    const canvas=document.createElement('canvas');canvas.width=600;canvas.height=260;
                    const context=canvas.getContext('2d');context.translate(460-p.x,205-p.y);
                    G.Combat.drawGroundFields(context);G.Combat.drawAirFields(context);
                    A.assert(!g.afterimages.length,'immediate clear retained snapshots '+method+' '+mode);
                    const data=context.getImageData(0,0,600,260).data;let red=0;
                    for(let k=0;k<data.length;k+=4)if(data[k+3]>8&&data[k]>80&&data[k]>data[k+1]*1.5&&data[k]>data[k+2]*1.3)red++;
                    A.assert(red===0,'immediate '+method+' draw retained red pixels '+mode);out.push(method+'-immediate-draw-'+mode);A.pause();
                  }
                  refill();G.Game.toUI();G.Flow.play();G.Game.togglePause();
                  A.assert(G.Game.player!==p&&!g.afterimages.length,'old-owner trail leaked into new run');out.push('new-owner');return out;
                }""")
                page.keyboard.up('KeyD')
                ctx.close()
            browser.close()
        assert not report['errors'],report['errors']
        assert not report['failedRequests'],report['failedRequests']
        report['ok']=True
    except Exception as error:
        report['ok']=False;report['failure']=str(error);raise
    finally:
        (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'evidence':str(OUT)},ensure_ascii=False))

if __name__=='__main__':main()
