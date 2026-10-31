"""Real Eight Gates afterimages: input, historical sprites, pixels and lifecycle."""
import base64
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/lee-gate-trail-colors'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=lee-afterimages&hero=lee&layout=wide'

HELPERS = r"""() => {
 const A=Acceptance,origins=new WeakMap(),draw=CanvasRenderingContext2D.prototype.drawImage;
 const sourceOf=image=>image.src?[image.src]:(origins.get(image)||[]);
 CanvasRenderingContext2D.prototype.drawImage=function(image,...args){
   origins.set(this.canvas,[...new Set([...(origins.get(this.canvas)||[]),...sourceOf(image)])]);
   return draw.call(this,image,...args);
 };
 A.trailStep=(dt=.02)=>{const p=A.p();A.resume();try{p.update(dt);G.Combat.updateFields(dt)}finally{A.pause()}};
 A.trailState=()=>G.NarutoGates.afterimagesFor(A.p());
 A.readyGates=()=>{const g=G.NarutoGates,p=A.p();
   g.update(0);
   if(!g.active(p))A.advance(g.status(p).cooldownRemaining||g.config.cooldown);
   if(g.performing(p))A.advance(g.config.openingDuration+g.config.openingBurstDuration+.1);
 };
 A.trailPixels=canvas=>{
   const data=canvas.getContext('2d',{willReadFrequently:true}).getImageData(0,0,canvas.width,canvas.height).data;
   let green=0,red=0,x0=canvas.width,x1=-1,y0=canvas.height,y1=-1,maxAlpha=0,checksum=0;
   for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++){
     const k=(y*canvas.width+x)*4,r=data[k],g=data[k+1],b=data[k+2],a=data[k+3];
     const isGreen=a>8&&g>100&&g>r*1.3&&g>b*1.12,isRed=a>8&&r>100&&r>g*1.5&&r>b*1.3;
     if(isGreen)green++;if(isRed)red++;
     if(isGreen||isRed){maxAlpha=Math.max(maxAlpha,a);checksum=(checksum+(k+1)*a)%2147483647;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}
   }
   return {green,red,pixels:green+red,width:x1-x0+1,height:y1-y0+1,maxAlpha,checksum,bounds:[x0,y0,x1,y1]};
 };
 A.trailCapture=()=>{
   const p=A.p(),level=G.NarutoGates.stage(p),style=G.NarutoGates.config.trails[level-1];
   const canvas=document.createElement('canvas');canvas.width=900;canvas.height=340;
   const ctx=canvas.getContext('2d',{willReadFrequently:true}),calls=[],original=ctx.drawImage.bind(ctx);
   ctx.drawImage=function(image,...args){calls.push({sources:sourceOf(image),width:image.width,height:image.height,args});return original(image,...args)};
   ctx.save();ctx.translate(760-p.x,250-p.y);G.Combat.drawGroundFields(ctx);ctx.restore();
   const air=document.createElement('canvas');air.width=900;air.height=340;
   const airCtx=air.getContext('2d');airCtx.translate(760-p.x,250-p.y);G.Combat.drawAirFields(airCtx);
   const particles=A.trailPixels(air),expectedColor=level<5?'green':'red',otherColor=level<5?'red':'green';
   A.assert(particles[expectedColor]>0&&particles[otherColor]===0,'air aura RGB did not match stage '+level);
   const footprint=A.trailPixels(canvas),expected=level<5?'green':'red',opposite=level<5?'red':'green';
   A.assert(footprint[expected]>500&&footprint[opposite]===0,'native trail RGB did not match stage '+level+' '+JSON.stringify(footprint));
   A.assert(calls.some(c=>c.sources.some(src=>/lee-gates-(common|skills)-v1[.]png/.test(src))),'historical sprite did not originate in native Lee Gates art');
   A.assert(footprint.maxAlpha<255&&footprint.maxAlpha>=style.opacity*255*.75,'trail alpha is opaque or too faint');
   const [x0,y0,x1,y1]=footprint.bounds;A.assert(x0>0&&y0>0&&x1<899&&y1<339,'trail evidence clipped');
   const snapshots=A.trailState(),distances=snapshots.map(s=>Math.hypot(p.x-s.x,p.y-s.y));
   const history={maxDistance:Math.max(...distances),span:Math.max(...snapshots.map(s=>s.x))-Math.min(...snapshots.map(s=>s.x)),speed:p.spd};
   A.assert(history.maxDistance>p.spd*(level===5?.50:.32),'native history did not extend the tail range');
   A.assert(G.NarutoGates.redSkin(p),'Gates body skin unexpectedly lost its existing red form');
   ctx.save();ctx.translate(760-p.x,250-p.y);p.draw(ctx);G.Combat.drawAirFields(ctx);ctx.restore();
   const preview=document.createElement('canvas');preview.width=canvas.width;preview.height=canvas.height;
   const background=preview.getContext('2d');background.save();background.translate(760-p.x,250-p.y);
   G.World.drawGround(background,{left:()=>p.x-760,top:()=>p.y-250,w:900,h:340});background.restore();background.drawImage(canvas,0,0);
   return {footprint,history,calls,snapshots,style,png:preview.toDataURL()};
 };
 A.trailEmptyDraw=()=>{
   const canvas=document.createElement('canvas');canvas.width=900;canvas.height=340;
   const ctx=canvas.getContext('2d');ctx.translate(760-A.p().x,250-A.p().y);
   G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);return A.trailPixels(canvas);
 };
}"""


def comparison(stages, label):
    # A common crop preserves the true relative tail lengths and actor scale.
    left = max(0, min(stage['footprint']['bounds'][0] for stage in stages.values()) - 24)
    top = max(0, min(stage['footprint']['bounds'][1] for stage in stages.values()) - 20)
    box = (left, top, 866, 284)
    width, height = box[2] - box[0], box[3] - box[1]
    board = Image.new('RGB', (width * 5, height + 44), '#101923')
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype(r'C:\Windows\Fonts\msjh.ttc', 21)
    for index, name in enumerate(['開門', '休門', '生門', '傷門', '杜門']):
        level = index + 1
        color = '綠色' if level < 5 else '紅色'
        draw.text((index * width + 12, 8), f'{name} · {color}', font=font, fill='#edf4ee')
        shot = Image.open(OUT / f'{label}-stage{level}.png').convert('RGB').crop(box)
        board.paste(shot, (index * width, 44))
    board.save(OUT / f'{label}-five-stages.png')


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
                for level in range(1,6):
                    page.evaluate(r"""level=>{const A=Acceptance,p=A.p();A.leeArena();
                      const m=p.moves.find(m=>m.id==='naruto-gates');while(m.lvl<level){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:naruto-gates');A.assert(card&&card.apply(p)!==false,'upgrade trail stage')}
                      A.readyGates();A.trailBaseline={hp:p.hp,atk:p.atk,spd:p.spd,damage:p.dmgDealt};
                    }""",level)
                    if mobile:
                        page.evaluate('Acceptance.resume()')
                        client=ctx.new_cdp_session(page)
                        base=page.evaluate('G.Touch.stickBase()')
                        client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':base['x'],'y':base['y']}]})
                        client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':base['x']+45,'y':base['y']}]})
                    else:page.keyboard.down('KeyD')
                    stage=page.evaluate(r"""() => {const A=Acceptance,p=A.p(),x=p.x;A.assert(G.Input.axis()[0]>0,'actual movement input missing');
                      for(let n=0;n<80;n++){A.trailStep(.02);A.assert(A.trailState().length<=G.NarutoGates.config.trails[G.NarutoGates.stage(p)-1].count,'history count exceeded stage cap');}
                      A.assert(p.x>x+10,'actual Player.update did not move');
                      const shots=A.trailState();A.assert(shots.length>0,'moving gates emitted no afterimages');
                      const level=G.NarutoGates.stage(p),style=G.NarutoGates.config.trails[level-1],expected=level<5?'#70f5aa':'#ff315b';
                      A.assert(style.color===expected&&style.count===level+5,'stage color/count spec mismatch');
                      A.assert(shots.every(s=>s.color===expected&&s.opacity===style.opacity&&s.life===style.life&&s.scale===style.scale),'snapshots lost their own color/opacity/lifetime');
                      A.assert(shots.every(s=>s.x<p.x+.001)&&shots.some(s=>s.x<p.x-2),'afterimages did not trail real historical positions');
                      A.assert(p.hp===A.trailBaseline.hp&&p.atk===A.trailBaseline.atk&&p.spd===A.trailBaseline.spd&&p.dmgDealt===A.trailBaseline.damage,'visual trail altered gameplay stats/damage');
                      const shot=A.trailCapture(),dir=p.anim.dir,cur=p.anim.cur;
                      p.anim.dir=6;p.anim.play('Attack');const turned=A.trailCapture();
                      A.assert(turned.footprint.checksum===shot.footprint.checksum,'turn redrew historical sprite poses');p.anim.dir=dir;p.anim.play(cur);
                      shot.frozenHistoricalPoses=true;
                      const saved=JSON.stringify(A.trailState()),copies=G.NarutoGates.afterimagesFor(p);copies[0].x+=999;copies[0].color='#000000';copies[0].opacity=0;
                      A.assert(JSON.stringify(A.trailState())===saved,'public snapshot copies mutated live history');shot.snapshotCopiesReadOnly=true;
                      const before=JSON.stringify(A.trailState());G.Combat.updateFields(.5);
                      A.assert(JSON.stringify(A.trailState())===before,'paused simulation expired trails');shot.pausePreserves=true;return shot;
                    }""")
                    if mobile:
                        client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});client.detach()
                    else:page.keyboard.up('KeyD')
                    (OUT/f'{label}-stage{level}.png').write_bytes(base64.b64decode(stage.pop('png').split(',',1)[1]))
                    result['stages'][str(level)]=stage
                    if level==5:
                        page.evaluate('G.Camera.x=G.Game.player.x;G.Camera.y=G.Game.player.y')
                        page.wait_for_timeout(80)
                        page.screenshot(path=str(OUT/f'{label}-stage5-game.png'))
                    stage['fade']=page.evaluate("() => {for(let n=0;n<60;n++)Acceptance.trailStep(.02);Acceptance.assert(!G.NarutoGates.afterimages.length,'stationary trails did not fade');return true}")
                result['stageGrowth']=page.evaluate(r"""stages=>{const A=Acceptance,small=stages['1'].footprint,big=stages['5'].footprint;
                  A.assert(big.height>small.height*1.15,'higher gate did not enlarge actual silhouette height');
                  A.assert(big.width>small.width*1.15,'higher gate did not widen native trail pixel bounds');
                  A.assert(stages['5'].history.maxDistance>stages['1'].history.maxDistance*1.2,'higher gate did not extend real historical positions');
                  A.assert(big.pixels>small.pixels,'higher gate did not increase colored footprint');return {small,big};
                }""",result['stages'])
                comparison(result['stages'],label)
                # A paused stage change must hide old green history before any tick.
                page.keyboard.down('KeyD')
                page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p();A.leeArena();
                  Object.assign(p.moves.find(m=>m.id==='naruto-gates'),G.Moves.instance('naruto-gates',4));
                  A.readyGates();for(let n=0;n<40;n++)A.trailStep(.02);
                  A.assert(A.trailState().length&&A.trailState().every(s=>s.color==='#70f5aa'),'green transition fixture missing');
                }""")
                page.keyboard.up('KeyD')
                result['pausedStageChange']=page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p(),position=[p.x,p.y];A.pause();
                  const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:naruto-gates');
                  A.assert(card&&card.apply(p)!==false,'native stage-five upgrade card missing');
                  A.assert(!G.NarutoGates.afterimagesFor(p).length,'paused upgrade exposed old green snapshots');
                  A.assert(A.trailEmptyDraw().green===0,'paused upgrade rendered old green snapshots');
                  A.trailStep(.02);
                  A.assert(p.x===position[0]&&p.y===position[1]&&!A.trailState().length,'stationary upgrade emitted a phantom snapshot');
                  return {immediateHidden:true,stationaryNoPhantom:true};
                }""")
                # Refill real moving history for each lifecycle boundary.
                page.keyboard.down('KeyD')
                result['cleanup']=page.evaluate(r"""async () => {
                  const A=Acceptance,p=A.p(),g=G.NarutoGates,out=[];
                  const refill=()=>{A.leeArena();A.readyGates();for(let n=0;n<20;n++)A.trailStep(.02);A.assert(g.afterimages.length,'cleanup fixture did not emit')};
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
                    const canvas=document.createElement('canvas');canvas.width=900;canvas.height=340;
                    const context=canvas.getContext('2d');context.translate(760-p.x,250-p.y);
                    G.Combat.drawGroundFields(context);G.Combat.drawAirFields(context);
                    A.assert(!g.afterimages.length,'immediate clear retained snapshots '+method+' '+mode);
                    const colored=A.trailPixels(canvas).pixels;
                    A.assert(colored===0,'immediate '+method+' draw retained colored pixels '+mode);out.push(method+'-immediate-draw-'+mode);A.pause();
                  }
                  refill();G.Game.toUI();await G.Flow.play();if(G.Game.state==='playing')G.Game.togglePause();
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
