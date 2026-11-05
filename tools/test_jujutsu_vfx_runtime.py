"""Production JJK procedural rendering, real game hook, transforms and budgets."""
from __future__ import annotations
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.omx/state/jujutsu-vfx'
URL=os.environ.get('JUJUTSU_VFX_URL','http://127.0.0.1:8337/.omx/digimon.html?lang=zh-TW&layout=wide')

TRACE=r"""()=>{
 window.VFXTrace={phase:'init',captures:[],composites:[],proceduralFills:0};
 const liquid=G.World.drawLiquid,hazards=G.Hazards.draw,draw=CanvasRenderingContext2D.prototype.drawImage;
 const fill=CanvasRenderingContext2D.prototype.fill;
 const palette=new Set(['#319fc4','#55cfdf','#75c9db','#87d9e8','#d7f8ff']);
 CanvasRenderingContext2D.prototype.fill=function(...args){if(this.canvas===document.getElementById('game')&&palette.has(this.fillStyle))VFXTrace.proceduralFills++;return fill.apply(this,args)};
 G.World.drawLiquid=function(...args){const r=liquid.apply(this,args);VFXTrace.phase='background';return r};
 G.Hazards.draw=function(...args){VFXTrace.phase='hazards';return hazards.apply(this,args)};
 CanvasRenderingContext2D.prototype.drawImage=function(im,...args){
  let capture=null;
  if(im===document.getElementById('game')&&this.canvas.dataset?.source==='procedural-jjk-fold'){
   const inv=this.getTransform().inverse(),spots=[];
   for(const [u,v]of [[.25,.25],[.5,.5],[.75,.75],[.25,.75],[.75,.25]]){
    const x=Math.floor(this.canvas.width*u),y=Math.floor(this.canvas.height*v),p=inv.transformPoint({x:x+.5,y:y+.5});
    if(p.x>=0&&p.y>=0&&p.x<im.width&&p.y<im.height)spots.push({x,y,sx:p.x,sy:p.y,expected:[...im.getContext('2d').getImageData(Math.floor(p.x),Math.floor(p.y),1,1).data]});
   }
   capture={phase:VFXTrace.phase,size:[this.canvas.width,this.canvas.height],spots};VFXTrace.captures.push(capture);
  }
  if(im instanceof HTMLCanvasElement&&im.dataset?.source==='procedural-jjk-fold')
   VFXTrace.composites.push({phase:VFXTrace.phase,size:[im.width,im.height]});
  const result=draw.call(this,im,...args);
  if(capture)for(const p of capture.spots){p.actual=[...this.getImageData(p.x,p.y,1,1).data];p.error=Math.max(...p.actual.map((v,i)=>Math.abs(v-p.expected[i])))}
  return result;
 };
}"""

def boot(browser,dex,low=False,dpr=1):
 context=browser.new_context(viewport={'width':390,'height':844} if low else {'width':1280,'height':900},device_scale_factor=dpr,service_workers='block')
 page=context.new_page();page.goto(URL+'&hero='+str(dex));f=base.frame_for(page)
 f.wait_for_function("G.JujutsuVFX&&document.getElementById('boot').classList.contains('hidden')")
 if f.locator('#tap-start').is_visible():f.locator('#tap-start').click()
 f.locator('#scr-menu [data-go="play"]').click();f.wait_for_function("G.Game.state==='playing'")
 f.evaluate(base.SETUP);return context,page,f

def wait_render(page):page.wait_for_timeout(100)

def main():
 OUT.mkdir(parents=True,exist_ok=True);base.OUT=OUT
 report={'url':URL,'cases':{},'errors':[],'failures':[]}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
  for low,dpr in [(False,1),(True,2)]:
   label='low-dpr2' if low else 'high-dpr1';context,page,f=boot(browser,30015,low,dpr)
   page.on('pageerror',lambda e:report['errors'].append(str(e)))
   try:
    f.evaluate(TRACE)
    f.evaluate("""low=>{const A=JAcceptance;A.reset();G.JujutsuVFX.setQuality(low?'low':'high');A.fixture('jjk-uro-thin-ice');A.spawn(100,0);A.cast('jjk-uro-thin-ice');A.advance(.2);}""",low)
    wait_render(page);first=f.evaluate('G.JujutsuVFX.inspect()')
    page.screenshot(path=str(OUT/(label+'-sky-fold.png')))
    assert first['triangles']>0,('no actual texture triangles',first)
    assert first['triangles']<=(12 if low else 48),first
    assert first['snapshots']<=(1 if low else 2),first
    assert first['bufferBytes']<=(256*256*4 if low else 2*512*512*4),first
    f.evaluate('G.Camera.x+=37;G.Camera.y-=19');wait_render(page)
    moved=f.evaluate('G.JujutsuVFX.inspect()');assert first['capturesTotal']==moved['capturesTotal'],'camera/paused render recaptured terrain'
    trace=f.evaluate('VFXTrace')
    assert trace['captures'] and all(x['phase']=='background' for x in trace['captures']),'capture did not occur before hazards'
    assert trace['composites'] and all(x['phase']=='background' for x in trace['composites']),'composite did not occur before hazards'
    pixels=[spot for capture in trace['captures'] for spot in capture['spots']]
    assert pixels and max(p['error'] for p in pixels)<=3,('world/device transform copied wrong actual background pixels',pixels)
    f.evaluate("G.JujutsuVFX.enabled=false;VFXTrace.captures=[];VFXTrace.composites=[];VFXTrace.proceduralFills=0")
    f.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');wait_render(page)
    disabled=f.evaluate('({stats:G.JujutsuVFX.inspect(),trace:VFXTrace})');page.screenshot(path=str(OUT/(label+'-vfx-disabled.png')))
    assert not disabled['trace']['captures'] and not disabled['trace']['composites'] and not disabled['trace']['proceduralFills'],('disabled VFX still rendered native procedural pixels',disabled)
    assert disabled['stats']['snapshots']==0 and disabled['stats']['triangles']==0 and not disabled['stats']['draws'],disabled
    f.evaluate('G.JujutsuVFX.enabled=true')
    f.evaluate('G.Combat.clearFields()');wait_render(page)
    cleared=f.evaluate('G.JujutsuVFX.inspect()');assert cleared['snapshots']==0 and not cleared['folds'],cleared
    report['cases'][label]={'first':first,'moved':moved,'trace':trace,'disabled':disabled,'cleared':cleared}
   except Exception as e:
    report['failures'].append(label+': '+str(e));page.screenshot(path=str(OUT/(label+'-failure.png')))
   finally:context.close()
  for dex,skill,at,label in [(30014,'jjk-ryu-maximum',.78,'beam'),(30013,'jjk-yuta',.20,'katana'),(30013,'jjk-yuta-rika',.55,'rika')]:
   context,page,f=boot(browser,dex);page.on('pageerror',lambda e:report['errors'].append(str(e)))
   try:
    f.evaluate(TRACE)
    damage=f.evaluate("""({skill,at})=>{const A=JAcceptance;A.reset();A.fixture(skill);window.VFXTarget=A.spawn(100,0);A.cast(skill);A.advance(at);return VFXTarget.maxHp-VFXTarget.hp}""",{'skill':skill,'at':at})
    wait_render(page);data=f.evaluate('G.JujutsuVFX.inspect()');page.screenshot(path=str(OUT/(label+'-production.png')))
    kind='beam' if label=='beam' else 'arc-length-trail'
    assert any(x['kind']==kind for x in data['draws']),data
    without=f.evaluate("""({skill,at})=>{const A=JAcceptance;A.reset();G.JujutsuVFX.enabled=false;VFXTrace.captures=[];VFXTrace.composites=[];VFXTrace.proceduralFills=0;A.fixture(skill);const e=A.spawn(100,0);A.cast(skill);A.advance(at);return e.maxHp-e.hp}""",{'skill':skill,'at':at})
    f.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');wait_render(page)
    off=f.evaluate('({stats:G.JujutsuVFX.inspect(),trace:VFXTrace})')
    assert not off['stats']['draws'] and off['stats']['triangles']==0 and off['stats']['shards']==0 and off['stats']['beamProfiles']==0,off
    assert off['trace']['proceduralFills']==0 and not off['trace']['composites'] and not off['trace']['captures'],off
    f.evaluate('G.JujutsuVFX.enabled=true');data['disabledNativeRender']=off
    assert damage>0 and damage==without,('procedural VFX changed actual native damage',damage,without)
    data['damageWithVfx']=damage;data['damageWithoutVfx']=without
    report['cases'][label]=data
   except Exception as e:
    report['failures'].append(label+': '+str(e));page.screenshot(path=str(OUT/(label+'-failure.png')))
   finally:context.close()
  context,page,f=boot(browser,30015)
  try:
   f.evaluate("""()=>{const A=JAcceptance,p=A.p();A.reset();G.JujutsuVFX.setQuality('high');A.fixture('jjk-uro-thin-ice');A.spawn(100,0);
    const actors=[p,...Array.from({length:3},()=>G.SelfClones.summon(p))];A.assert(actors.every(Boolean),'native clones missing');
    A.resume();try{for(const actor of actors){const m=actor.moves.find(m=>m.id==='jjk-uro-thin-ice');m.t=0;A.assert(G.JjkUro.cast(actor,m),'native clone cast rejected')}}finally{A.pause()};A.advance(.2);}""")
   wait_render(page);high=f.evaluate('G.JujutsuVFX.inspect()');page.screenshot(path=str(OUT/'four-owners-high.png'))
   assert high['snapshots']==2 and high['triangles']==48 and high['fallbacks']>=2,high
   assert high['shards']<=24 and high['bufferBytes']<=2*512*512*4,high
   assert len({e['owner'] for e in high['folds']})==4,high
   f.evaluate("G.JujutsuVFX.setQuality('low')");wait_render(page)
   lowered=f.evaluate('G.JujutsuVFX.inspect()');page.screenshot(path=str(OUT/'four-owners-low.png'))
   assert lowered['snapshots']==1 and lowered['triangles']==12 and lowered['fallbacks']>=3,lowered
   assert lowered['bufferBytes']<=256*256*4,lowered
   f.evaluate('JAcceptance.advance(.2)');wait_render(page)
   contact=f.evaluate('G.JujutsuVFX.inspect()');assert contact['shards']==24,('four actual contact effects must share the24-shard budget',contact)
   f.evaluate('G.Game.player.dead=true');wait_render(page)
   dead=f.evaluate('G.JujutsuVFX.inspect()');assert dead['snapshots']==0 and not dead['folds'],dead
   changed=f.evaluate("""()=>{const old=G.Game.player,before=G.JujutsuVFX.inspect().epoch;G.Game.startRun();G.Combat.clearFields();JAcceptance.pause();return {before,after:G.JujutsuVFX.inspect().epoch,newOwner:G.Game.player!==old}}""")
   assert changed['newOwner'] and changed['after']>changed['before'],changed
   report['cases']['four-owner-budgets']={'high':high,'low':lowered,'contact':contact,'dead':dead,'restart':changed}
  except Exception as e:
   report['failures'].append('four-owner: '+str(e));page.screenshot(path=str(OUT/'four-owner-failure.png'))
  finally:context.close()
  browser.close()
 report['ok']=not(report['failures'] or report['errors'])
 (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'ok':report['ok'],'failures':report['failures'],'errors':report['errors'],'evidence':str(OUT)},ensure_ascii=True))
 if not report['ok']:raise SystemExit(1)

if __name__=='__main__':main()
