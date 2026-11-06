"""Pure Love cannon: legal learning, real pulses and native automatic playback.

Controlled enemies isolate geometry/lifecycle; recordings are native RAF casts,
not evidence of natural levelling or subjective fun.
"""
from __future__ import annotations
import json
import os
import time
from playwright.sync_api import sync_playwright
import test_jujutsu as base

OUT = base.ROOT / '.omx/state/yuta-love'
CHECK = r"""() => {
 const A=JAcceptance,Y=G.JujutsuYuta,p=A.p(),assert=A.assert,id='jjk-yuta-love',out={};
 const nativePath=G.World.projectilePathClear;
 function setup(rank=1,q=0){A.reset();G.World.projectilePathClear=nativePath;const m=A.fixture(id,rank);
  p.quantityPicks=p.quantityBonus=q;p.invuln=999;return m;}
 function cast(m,owner=p){m.t=0;A.resume();try{assert(Y.cast(owner,m),'cannot cast love')}finally{A.pause()};return Y.stateFor(owner);}
 function wait(test,seconds=5){for(let t=0;t<seconds&&!test();t+=.01)A.advance(.01);assert(test(),'love phase timeout');}
 // Exercise the real learning and rank card pipeline, not only instances.
 A.reset();A.fixture('jjk-yuta');p.level=7;
 assert(!G.Moves.poolFor(p.mon).includes(id)&&!G.LevelUp.offer(p,1000).some(c=>c.key==='new:'+id)&&!p.addMove(id),'love learned before Lv8');
 p.level=8;const learn=G.LevelUp.offer(p,1000).find(c=>c.key==='new:'+id);
 assert(learn&&learn.apply(p)!==false&&p.hasMove(id),'Lv8 love learning card missing');
 assert(!p.addMove(id),'duplicate love learning');
 const mon=p.mon;p.mon=G.DEX_BY[30014];assert(!G.Moves.poolFor(p.mon).includes(id),'love leaked to Ryu');p.mon=mon;
 for(let rank=2;rank<=5;rank++){const card=G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+id);
  assert(card&&card.apply(p)!==false,'legal love rank card '+rank);assert(p.moves.find(m=>m.id===id).lvl===rank,'rank not applied');}
 assert(!G.LevelUp.offer(p,1000).some(c=>c.key==='up:'+id),'upgrade offered above cap');out.legalLearning={level:8,rank:5};

 for(const [rank,q,count] of [[1,0,3],[3,0,5],[5,0,7],[5,20,12]]){
  const m=setup(rank,q),targets=[A.spawn(250,0),A.spawn(400,0),A.spawn(520,0)],events=targets.map(e=>A.watch(e)),outside=A.spawn(1000,250),outsideHits=A.watch(outside);
  const s=cast(m),actor=s.companion;wait(()=>s.release?.phase==='charge');
  assert(!Y.manifested(p)&&s.release.requiresManifest===false,'love requires/creates manifestation');
  assert(s.release.count===count&&s.companion===actor&&!s.rika&&Y.drawables(null).length===1,'wrong pulse count or duplicate/missing Rika');
  const f=s.release;wait(()=>f.pulseIndex>=1);
  assert(f.sources.length===2&&new Set(f.sources.map(x=>x.castId)).size===2,'cannon lacks two distinct casts');
  const [hand,mouth]=f.sources;
  assert(Math.hypot(hand.anchorX-mouth.anchorX,hand.anchorY-mouth.anchorY)>10,'actor energy anchors collapsed');
  assert(hand.x===mouth.x&&hand.y===mouth.y&&hand.aim===mouth.aim,'love energy failed to converge into one cannon');
  assert(f.range===G.Jujutsu.power.yuta.releaseRanges[rank-1]&&f.radius===G.Jujutsu.power.yuta.releaseRadii[rank-1],'rank geometry differs');
  A.advance(3);
  assert(events.every(h=>h.filter(x=>x.id===id).length===count*2)&&!outsideHits.length,'real pulse/range damage differs '+JSON.stringify({rank,q,hits:events.map(h=>h.length)}));
  assert(!s.release&&!s.companion.visible&&!s.companion.full,'love-only Rika/pose persisted after recovery');
  out['rank'+rank+'q'+q]={count,hits:events.map(h=>h.length),outsideHits:outsideHits.length};
 }
 let m=setup(3),e=A.spawn(300,0),s=cast(m);wait(()=>s.release?.phase==='charge');
 const frozen=s.release,age=frozen.age;G.Combat.updateFields(.5);assert(frozen.age===age,'pause advanced cannon');
 p.frozen=true;A.advance(.4);assert(frozen.age===age,'frozen owner advanced cannon');p.frozen=false;A.advance(2);assert(!s.release,'unfrozen cannon failed to finish');out.pauseFrozen=true;

 // First quantity investment changes actual contacts, using the real card.
 m=setup(3);const before=G.Quantity.count(p,G.Jujutsu.power.yuta.loveBases[2]);
 const quantity=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');assert(quantity&&quantity.apply(p)!==false,'quantity card missing');
 e=A.spawn(300,0);const quantityHits=A.watch(e);s=cast(m);const after=s.release.count;A.advance(3);
 assert(after>before&&quantityHits.length===2*after,'first quantity card has no real contact benefit');out.firstQuantity={before,after,hits:quantityHits.length};

 // Old marks are frozen; future contacts originate from the moved actors.
 m=setup(5);e=A.spawn(400,0);s=cast(m);wait(()=>s.release?.pulseIndex===1);
 const f=s.release,marks=s.marks.filter(x=>x.kind==='release'),old=JSON.stringify(marks.map(x=>[x.x,x.y,x.aim])),firstX=f.sources[0].x;
 p.x+=35;A.advance(f.interval+.01);
 assert(f.pulseIndex>=2&&f.sources[0].x>firstX+20,'later pulse did not follow moving owner');
 assert(JSON.stringify(marks.map(x=>[x.x,x.y,x.aim]))===old,'old release marks followed owner');out.movingOrigins=true;

 for(const cancel of ['clear','unlearn','dead','wall']){
  m=setup();e=A.spawn(300,0);const events=A.watch(e);s=cast(m);wait(()=>s.release?.phase==='charge');
  if(cancel==='clear')G.Combat.clearFields(p);
  if(cancel==='unlearn')p.moves=[];
  if(cancel==='dead'){p.dead=true;p.hp=0;}
  if(cancel==='wall')G.World.projectilePathClear=(x,y,tx,ty)=>Math.max(x,tx)<200;
  A.advance(2);assert(!events.length,'cancelled/blocked cannon dealt damage '+cancel);out[cancel]=true;
 }
 // Both the next target in this pulse and every future pulse must stop.
 for(const cancel of ['clear','unlearn','dead','freeze','onDealt']){
  m=setup(5);const victims=[A.spawn(250,0),A.spawn(400,0)],events=victims.map(e=>A.watch(e));s=cast(m);
  const previous=p.onDealt;
  function stop(){if(cancel==='clear')G.Combat.clearFields(p);else if(cancel==='unlearn')p.moves=[];
   else if(cancel==='dead'){p.dead=true;p.hp=0;}else p.frozen=true;}
  if(cancel==='onDealt')p.onDealt=function(...args){stop();return previous.apply(this,args)};
  else for(const victim of victims){const hurt=victim.hurt;victim.hurt=function(...args){const result=hurt.apply(this,args);stop();return result;};}
  try{A.advance(3)}finally{p.onDealt=previous;}
  assert(events.reduce((sum,list)=>sum+list.length,0)===1,'callback retained next target/source/pulse '+cancel);
  out['callback-'+cancel]=events.map(h=>h.length);
 }
 // Each native clone owns its own actor, cast and cleanup scope.
 m=setup();e=A.spawn(300,0);const clone=G.SelfClones.summon(p);assert(clone,'native clone missing');
 const copied=clone.moves.find(move=>move.id===id);assert(copied,'clone omitted love');cast(m);cast(copied,clone);
 assert(Y.stateFor(p).companion!==Y.stateFor(clone).companion&&Y.stateFor(p).release.casts[0].ownerId!==Y.stateFor(clone).release.casts[0].ownerId,'clone shared cannon ownership');
 Y.clear(p);assert(!Y.stateFor(p)&&Y.stateFor(clone),'owner cleanup removed clone cannon');clone.dead=true;clone.hp=0;A.advance(.1);assert(!Y.stateFor(clone),'dead clone kept cannon');out.clones=true;
 G.World.projectilePathClear=nativePath;return out;
}"""

NATIVE = r"""mobile => {
 const A=JAcceptance,p=A.p();A.reset();A.fixture('jjk-yuta');p.level=8;
 const learn=G.LevelUp.offer(p,1000).find(c=>c.key==='new:jjk-yuta-love');A.assert(learn&&learn.apply(p)!==false,'native love learn');
 for(let i=1;i<5;i++){const card=G.LevelUp.offer(p,1000).find(c=>c.key==='up:jjk-yuta-love');A.assert(card&&card.apply(p)!==false,'native love upgrade');}
 for(let i=0;i<2;i++){const card=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');A.assert(card&&card.apply(p)!==false,'native quantity');}
 for(const m of p.moves)m.t=m.id==='jjk-yuta-love'?0:999;p.invuln=999;G.Spawner.update=()=>{};
 for(const [x,y] of (mobile?[[0,-160],[0,-260],[15,-340]]:[[220,0],[320,0],[430,0]])){const e=A.spawn(x,y);e.touchCd=999;}
 const label=document.createElement('div');label.id='love-evidence-label';label.style='position:fixed;top:90px;left:8px;right:8px;z-index:99999;background:#241d35e8;color:#fff;padding:8px;font:13px sans-serif;pointer-events:none';
 label.textContent='純愛砲｜Lv8・五階・2張數量卡｜受控敵人／原生自動戰鬥';document.body.append(label);
 window.LoveNative={started:G.Game.st.time};G.Game.debugSpeed(1);A.resume();return {level:8,rank:5,quantityCards:2,controlledEnemies:true};
}"""


def record_native(page, frame, label, mobile, page_started):
    native_started = time.monotonic() - page_started
    fixture = frame.evaluate(NATIVE, mobile)
    snapshots = {}
    for phase, condition in [
        ('charge', "s?.release?.phase==='charge'&&s.release.phaseAge>=.3"),
        ('first', "s?.release?.pulseIndex>=1&&s.release.pulseIndex<3"),
        ('last', "s?.release?.pulseIndex===s?.release?.count&&s.release.count>0"),
        ('recovery', "!s?.release&&s?.casts?.love>0"),
    ]:
        frame.wait_for_function("()=>{const s=G.JujutsuYuta.stateFor(JAcceptance.p());return " + condition + ";}", timeout=12000, polling=5)
        snapshots[phase] = frame.evaluate("""()=>{const s=G.JujutsuYuta.stateFor(JAcceptance.p()),f=s.release;return {time:G.Game.st.time,phase:f?.phase,pulse:f?.pulseIndex,count:f?.count,visible:s.companion.visible,casts:s.casts};}""")
        page.screenshot(path=str(OUT / f'{label}-love-{phase}.png'))
    result = frame.evaluate("""()=>{JAcceptance.pause();return {elapsed:G.Game.st.time-LoveNative.started};}""")
    # Playwright records the composited page, including the separate VFX canvas.
    # The caller closes the context and saves page.video after this returns.
    return {**fixture, **result, 'snapshots': snapshots, 'recording': 'composited full page; native RAF',
            'nativeStartSecondsFromPageCreation': native_started}


def check_selection(browser, width):
    context = browser.new_context(viewport={'width': width, 'height': 844}, is_mobile=True, has_touch=True, service_workers='block')
    page = context.new_page()
    page.goto(base.URL)
    frame = base.frame_for(page)
    frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if frame.locator('#tap-start').is_visible():
        frame.locator('#tap-start').click()
    frame.locator('[data-quick-naruto="30013"]').click()
    kit = frame.locator('.launch-kit')
    kit.scroll_into_view_if_needed()
    result = frame.evaluate("""()=>{
      const assert=(ok,msg)=>{if(!ok)throw Error(msg)},kit=document.querySelector('.launch-kit'),rect=kit.getBoundingClientRect();
      const cells=[...kit.children],style=getComputedStyle(kit),action=document.querySelector('.launch-action').getBoundingClientRect();
      assert(!kit.hidden&&style.display!=='none'&&style.visibility==='visible'&&cells.length===6,'six-cell kit not visible');
      assert(!kit.textContent.includes('undefined'),'undefined learning label');
      const love=cells.find(cell=>cell.textContent.includes('純愛砲'));assert(love&&/Lv\\.?\\s*8/.test(love.textContent),'love Lv8 label missing');
      const bounds=cells.map(cell=>{const r=cell.getBoundingClientRect(),s=getComputedStyle(cell);
        assert(s.display!=='none'&&s.visibility==='visible'&&r.width>0&&r.height>0,'hidden skill cell');
        assert(r.left>=-.5&&r.right<=innerWidth+.5&&r.top>=-.5&&r.bottom<=innerHeight+.5,'skill cell outside viewport');
        assert(r.bottom<=action.top+.5,'skill cell under fixed launch action');
        assert(cell.scrollWidth<=cell.clientWidth+1&&cell.scrollHeight<=cell.clientHeight+1,'skill cell text overflow');
        for(const text of cell.querySelectorAll('b,small')){const b=text.getBoundingClientRect();assert(b.left>=r.left-.5&&b.right<=r.right+.5,'skill label outside cell');}
        return {text:cell.textContent,x:r.x,y:r.y,width:r.width,height:r.height,scrollWidth:cell.scrollWidth,clientWidth:cell.clientWidth};});
      assert(document.documentElement.scrollWidth<=innerWidth,'selection horizontal overflow');
      return {viewport:{width:innerWidth,height:innerHeight},display:style.display,kit:{x:rect.x,y:rect.y,width:rect.width,height:rect.height},cells:bounds};
    }""")
    page.screenshot(path=str(OUT / f'mobile{width}-selection-six-skills.png'))
    context.close()
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base.OUT = OUT
    base.URL = os.environ.get('JUJUTSU_URL', 'http://127.0.0.1:8383/.omx/digimon.html?lang=zh-TW')
    report = {'url': base.URL, 'cases': {}, 'selection': {}, 'errors': [], 'missing': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        for width in [360, 390]:
            report['selection'][str(width)] = check_selection(browser, width)
        for mobile in [False, True]:
            label = 'mobile' if mobile else 'desktop'
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.on('response', lambda response: report['missing'].append(response.url) if response.status >= 400 else None)
            frame = base.boot(page, 30013, label)
            report['cases'][label] = frame.evaluate(CHECK)
            context.close()
            viewport = {'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}
            native_context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block',
                                                 record_video_dir=str(OUT / 'clips'), record_video_size=viewport)
            page_started = time.monotonic()
            native_page = native_context.new_page()
            native_page.on('pageerror', lambda error: report['errors'].append(str(error)))
            native_page.on('response', lambda response: report['missing'].append(response.url) if response.status >= 400 else None)
            frame = base.boot(native_page, 30013, label)
            video = native_page.video
            report['cases'][label]['native'] = record_native(native_page, frame, label, mobile, page_started)
            native_context.close()
            path = OUT / f'{label}-native-love.webm'
            video.save_as(str(path))
            report['cases'][label]['native']['clip'] = str(path)
        browser.close()
    assert not report['errors'], report['errors']
    assert not report['missing'], report['missing']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({'ok': True, 'views': list(report['cases']), 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
