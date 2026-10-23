"""Complete native Tenten presentation proof, shared desktop/mobile review page."""
import json
import os
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_tenten import CHROME, HARNESS, SETUP, PROGRESSION

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('TENTEN_COMPLETE_OUT', str(ROOT / '.omx/state/tenten-complete')))
URL = os.environ.get('TENTEN_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=tenten-complete')

HELPERS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten;
 window.Proof={
  reset(){A.reset();G.Settings.set('calm',false);p.aim=0;p.anim.dir=2;
    const b=p.moves.find(m=>m.id==='naruto-tenten-bounce');if(b)p.moves.splice(p.moves.indexOf(b),1);},
  cast(id,x=190,y=0){this.reset();p.target=A.spawn(x,y);return A.castNative(id)},
  audit(){const cv=document.createElement('canvas');cv.width=1200;cv.height=900;const c=cv.getContext('2d'),paper=[],sources=[],strokes=[];
    const rect=c.fillRect.bind(c),stroke=c.stroke.bind(c),draw=c.drawImage.bind(c);
    c.fillRect=function(...args){if(this.fillStyle==='#efd8a4'||this.fillStyle==='#f0dcab')paper.push(this.fillStyle);return rect(...args)};
    c.stroke=function(...args){strokes.push(this.strokeStyle);if(this.strokeStyle==='#f0dcab')paper.push(this.strokeStyle);return stroke(...args)};
    c.drawImage=function(image,...args){const source=image.dataset?.source||image.src;if(source)sources.push(source);return draw(image,...args)};
    G.Combat.drawAirFields(c);p.anim.draw(c,600,450);return {paper,sources,strokes};},
  bounce(calm,id='naruto-tenten'){this.reset();G.Settings.set('calm',calm);
    const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-tenten-bounce');A.assert(card,'bounce learning absent');card.apply(p);
    p.moves.find(m=>m.id==='naruto-tenten-bounce').lvl=5;
    const m=p.moves.find(m=>m.id===id),saved=m.count;m.count=1;
    for(const [x,y] of [[100,0],[150,-40],[210,-10],[240,55],[170,75],[110,65],[65,95]])A.spawn(x,y);
    p.target=G.EnemyMgr.all()[0];A.castNative(id);m.count=saved;return T.weapons[0];}
 };return true;
}"""

CATCH_DIRECTIONS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,scale=p.anim.scale,out=[];
 try{for(const [direction,aim,dir] of [['right',0,2],['left',Math.PI,6],['down',Math.PI/2,0],['up',-Math.PI/2,4]])for(const growth of [1,1.25]){
  Proof.reset();p.anim.scale=scale*growth;p.aim=aim;p.anim.dir=dir;p.target=A.spawn(Math.cos(aim)*170,Math.sin(aim)*170);A.castNative('naruto-tenten-fuma');
  const w=T.weapons[0];A.assert(w,'missing Fuma');let steps=0;
  while(!w.dead&&steps++<300)A.advance(.005);
  const hand=G.AnimationLab.handForTenten(p,0,{key:'tenten-fuma',frame:2,mirror:Math.cos(w.angle)<0});
  A.assert(w.dead&&Math.hypot(w.x-hand.x,w.y-hand.y)<.01,'catch missed real authored hand '+direction+' '+growth);
  A.assert(T.activeFor(p)?.phase==='catch','no final catch pose');
  A.assert(Proof.audit().paper.length===0,'Fuma catch emitted paper');
  out.push({direction,growth,endpoint:[w.x,w.y],hand:[hand.x,hand.y],steps});
 }}finally{p.anim.scale=scale;Proof.reset()}return out;
}"""

CLEANUP = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,out=[];
 for(const reason of ['pause','clear','death','world']){
  Proof.cast('naruto-tenten-tags',110);let limit=0;while(!T.blasts.length&&limit++<250)A.advance(.01);
  p.target=A.spawn(170,0);A.castNative('naruto-tenten-twin');A.advance(.13);
  p.target=A.spawn(50,0);A.castNative('naruto-tenten');limit=0;while(!T.impacts.some(i=>i.kind==='metal')&&limit++<30)A.advance(.005);
  A.assert(T.weapons.length&&T.activeFor(p)&&T.blasts.length&&T.impacts.length,'cleanup fixture must exercise weapons,pose,blast,impact');
  if(reason==='pause'){const before=JSON.stringify({w:T.weapons.map(w=>[w.x,w.y,w.age]),i:T.impacts.map(i=>i.age),b:T.blasts.map(b=>b.age),age:T.activeFor(p).age});
   G.Combat.updateFields(.5);A.assert(before===JSON.stringify({w:T.weapons.map(w=>[w.x,w.y,w.age]),i:T.impacts.map(i=>i.age),b:T.blasts.map(b=>b.age),age:T.activeFor(p).age}),'paused suite advanced');}
  else{const world=G.World;if(reason==='clear')G.Combat.clearFields(p);else if(reason==='death')p.dead=true;else G.World={...world};
   try{if(reason!=='clear')A.advance(.01);A.assert(!T.weapons.some(w=>w.owner===p)&&!T.blasts.some(w=>w.owner===p)&&!T.impacts.some(w=>w.owner===p)&&!T.activeFor(p),'owner cleanup leaked '+reason);}
   finally{p.dead=false;G.World=world}}
  out.push(reason);
 }
 Proof.reset();A.select('naruto-tenten-twin');const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');
 // Use the actual offered clone card, preserving its native actor lifecycle.
 const cloneCard=card||G.LevelUp.offer(p,100).find(c=>c.name?.includes('分身')||c.key?.includes('clone'));
 A.assert(cloneCard,'clone card absent');cloneCard.apply(p);cloneCard.apply(p);
 const clones=G.SelfClones.actors();A.assert(clones.length>=2,'clone actors absent');
 const enemy=A.spawn(160,0);p.target=enemy;
 for(const [i,a] of clones.entries()){a.x=i*25;a.y=30;a.target=enemy;for(const m of a.moves)m.t=999;const m=a.moves.find(m=>m.id==='naruto-tenten-twin');m.t=0;}
 A.advance(.2);A.assert(clones.every(a=>T.weapons.some(w=>w.owner===a)),'clone emissions absent');
 const [a,b]=clones,remaining=T.weapons.filter(w=>w.owner===b).length;G.Combat.clearFields(a);
 A.assert(!T.weapons.some(w=>w.owner===a)&&T.weapons.filter(w=>w.owner===b).length===remaining,'clone cleanup affected sibling');
 window.proofSurvivingClone=b;out.push('clones-owned-clear');return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, size, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=size, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30009"]').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30009 && G.Game.state==="playing"')
            page.evaluate(HARNESS)
            page.evaluate(SETUP)
            page.evaluate(PROGRESSION)
            page.evaluate(HELPERS)
            result = {'stills': [], 'phases': {}, 'catchDirections': page.evaluate(CATCH_DIRECTIONS)}
            report['viewports'][label] = result
            frames = []

            def capture(name=None):
                page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                if name:
                    file = f'{label}-{name}.png'
                    page.screenshot(path=str(OUT / file))
                    result['stills'].append(file)
                frames.append(page.screenshot(type='jpeg', quality=90))

            def advance(dt=.05, name=None):
                page.evaluate('(dt)=>Acceptance.advance(dt)', dt)
                capture(name)

            result['phases']['mastery'] = capture_mastery(page, capture)
            page.evaluate("Proof.cast('naruto-tenten');window.basicEnemy=G.Game.player.target")
            capture('basic-release')
            advance(.08, 'basic-flight')
            hit = False
            for i in range(15):
                advance(.025)
                if page.evaluate("G.NarutoTenten.impacts.some(i=>i.kind==='metal')"):
                    capture('basic-impact')
                    hit = True
                    break
            assert hit and page.evaluate('basicEnemy.hp<100000'), 'basic actual metal impact missing'
            result['phases']['basic'] = ['release', 'flight', 'real-hit-impact']

            page.evaluate("Proof.cast('naruto-tenten-fuma');window.fuma=G.NarutoTenten.weapons[0]")
            capture('fuma-outbound')
            for i in range(9):
                advance(.05, 'fuma-flight' if i == 2 else None)
                assert not page.evaluate('Proof.audit().paper'), 'Fuma outbound produced scrolls'
                if page.evaluate('fuma.back'):
                    capture('fuma-turn')
                    break
            assert page.evaluate('fuma.back')
            advance(.10, 'fuma-return')
            while not page.evaluate('fuma.dead'):
                advance(.015)
            capture('fuma-catch')
            assert page.evaluate("G.NarutoTenten.activeFor(G.Game.player)?.phase==='catch'")
            advance(.24, 'fuma-ready-steel')
            assert page.evaluate('G.NarutoTenten.stateFor(G.Game.player).chargeRemaining>0')
            assert not page.evaluate('Proof.audit().paper'), 'recovery produced paper'
            page.evaluate("G.Game.player.target=Acceptance.spawn(190,0);Acceptance.castNative('naruto-tenten-fuma')")
            advance(.06, 'fuma-empowered')
            assert page.evaluate('G.NarutoTenten.weapons.some(w=>w.volley.power>1)')
            assert not page.evaluate('Proof.audit().paper'), 'empowered Fuma produced paper'
            result['phases']['fuma'] = ['outbound', 'turn', 'return', 'catch', 'steel-ready', 'empowered-no-paper']

            page.evaluate("Proof.reset();window.tm=G.Game.player.moves.find(m=>m.id==='naruto-tenten-twin');for(let i=0;i<4;i++)G.LevelUp.STATS.find(c=>c.id==='quantity').apply(G.Game.player);G.Game.player.target=Acceptance.spawn(240,0);Acceptance.castNative(tm.id);window.twinPose=G.NarutoTenten.activeFor(G.Game.player);window.appearances=[]")
            total = page.evaluate('twinPose.count')
            assert total == page.evaluate('G.Quantity.count(G.Game.player,tm.count)'), 'showcase must use attainable quantity cards'
            batches = [(total*n+3)//4 for n in range(1,5)]
            capture('twin-launch')
            assert page.evaluate('twinPose.emitted===0'), 'twin must launch before weapons'
            coils = []
            for i in range(21):
                advance(.05)
                sample = page.evaluate('''() => {const T=G.NarutoTenten,p=G.Game.player;
                  for(const w of T.weapons)if(w.appearance&&!appearances.some(a=>a.kind===w.appearance.kind))appearances.push({...w.appearance});
                  const s=T.scrollFor(p,1),births=T.weapons.filter(w=>w.age<=.050001).map(w=>{const h=T.scrollFor(p,w.side).head;return Math.hypot(w.sx-h.x,w.sy-h.y)});
                  return {age:twinPose.age,emitted:twinPose.emitted,head:s?.head,height:s?.height,births,source:G.AnimationLab.stateFor(p.anim).key,audit:Proof.audit()}}''')
                if sample['head']:
                    coils.append(sample)
                if i in [2, 6, 10, 14]:
                    capture(f'twin-batch-{[2,6,10,14].index(i)+1}')
                    assert sample['emitted'] == batches[[2, 6, 10, 14].index(i)], sample
                    assert sample['source'] == 'tenten-twin-release', sample
                    assert sample['births'] and max(sample['births']) < .001, 'weapons detached from moving scroll heads'
                    assert any('tenten-twin-release-v1.png' in s for s in sample['audit']['sources']), 'new empty-hand actor was not actually drawn'
                if i == 19:
                    capture('twin-landing')
            kinds = page.evaluate('appearances')
            assert len(kinds) == 8 and len({a['scale'] for a in kinds}) >= 3 and len({a['palette'] for a in kinds}) >= 3, kinds
            assert coils[-2]['height'] > coils[0]['height']+30, 'scroll heads did not ascend'
            xs = [c['head']['x'] for c in coils]
            assert max(xs)-min(xs)>45, 'scroll heads did not orbit'
            assert any(len(set(c['audit']['sources'])) >= 4 for c in coils), 'diverse weapons were not actually drawn'
            drawn_tools = {s.split('tenten-tool-')[1].split(':')[0] for c in coils for s in c['audit']['sources'] if s.startswith('tenten-tool-')}
            assert len(drawn_tools) == 8, drawn_tools
            result['phases']['twin'] = {'quantityCards': 4, 'count': total, 'batches': batches, 'appearances': kinds, 'coilSamples': coils}

            page.evaluate("Proof.reset();window.tagMove=G.Game.player.moves.find(m=>m.id==='naruto-tenten-tags');window.tagCount=tagMove.count;tagMove.count=1;G.Game.player.target=Acceptance.spawn(150,0);Acceptance.castNative(tagMove.id);tagMove.count=tagCount;window.tag=G.NarutoTenten.weapons[0]")
            advance(.07, 'tag-flight')
            while not page.evaluate('tag.landed'):
                advance(.025)
            capture('tag-land')
            advance(.12, 'tag-fuse')
            page.evaluate('''() => {G.Game.player.target.dead=true;G.EnemyMgr.rebuildGrid();const witness=Acceptance.spawn(tag.x,tag.y+38),hurt=witness.hurt;window.tagHits=0;
              witness.hurt=function(...args){if(args[7]==='naruto-tenten-tags')tagHits++;return hurt.apply(this,args)};
              G.Game.player.target=Acceptance.spawn(220,0);Acceptance.castNative('naruto-tenten')}''')
            ignition = blast = False
            for i in range(55):
                advance(.025)
                phase = page.evaluate('({triggered:tag.triggered,dead:tag.dead,hits:tagHits,blasts:G.NarutoTenten.blasts.length})')
                if phase['triggered'] and not phase['dead']:
                    assert phase['hits'] == 0, 'damage during ignition'
                    if not ignition:
                        capture('tag-ignition')
                        ignition = True
                if phase['blasts'] and not blast:
                    capture('tag-blast')
                    blast = True
            capture('tag-decay')
            assert ignition and blast and page.evaluate('tagHits===1&&!G.NarutoTenten.blasts.length'), 'tag phase/exactly-once failure'
            result['phases']['tags'] = ['flight', 'land', 'fuse', 'ignition-no-damage', 'blast-once', 'decay']

            routes = []
            for calm in [False, True]:
                page.evaluate('(calm)=>{window.bw=Proof.bounce(calm)}', calm)
                seen = False
                for i in range(30):
                    advance(.035)
                    route = page.evaluate("({hops:bw.bounced,chaining:bw.chaining,stroke:Proof.audit().strokes.includes('#83f5cb')})")
                    if route['hops'] and route['chaining'] and route['stroke']:
                        if not seen:
                            capture('bounce-calm-route' if calm else 'bounce-route')
                        seen = True
                assert seen, 'actual bounce trail invisible, calm='+str(calm)
                routes.append({'calm': calm, 'hops': page.evaluate('bw.bounced'), 'routeDrawn': seen})
            result['phases']['bounce'] = routes
            result['allToolsBounce'] = page.evaluate('''() => {const out=[];for(const id of ['naruto-tenten','naruto-tenten-fuma','naruto-tenten-tags','naruto-tenten-twin']){
              Proof.bounce(false,id);if(id.endsWith('twin'))Acceptance.advance(.13);const w=G.NarutoTenten.weapons[0];Acceptance.assert(w,'missing bounce tool '+id);Acceptance.finish(4);
              Acceptance.assert(w.bounced>0,'tool failed to ricochet '+id);out.push({id,bounced:w.bounced});}return out}''')
            for direction, aim, animdir in [('left', 3.141592653589793, 6), ('right', 0, 2), ('up', -1.5707963267948966, 4), ('down', 1.5707963267948966, 0)]:
                page.evaluate('''([aim,dir])=>{Proof.reset();const p=G.Game.player;p.aim=aim;p.anim.dir=dir;p.target=Acceptance.spawn(Math.cos(aim)*170,Math.sin(aim)*170);Acceptance.castNative('naruto-tenten-twin')}''', [aim, animdir])
                advance(.43, 'direction-'+direction)
            result['cleanup'] = page.evaluate(CLEANUP)
            capture('clone-owned-fields')
            page.evaluate("G.SelfClones.withSceneTransition(()=>G.Combat.clearFields());Acceptance.assert(G.SelfClones.actors().includes(proofSurvivingClone)&&!G.NarutoTenten.weapons.length&&!G.NarutoTenten.impacts.length&&!G.NarutoTenten.blasts.length,'scene cleanup leaked fields or lost actor')")
            capture('clone-scene-cleanup')
            result['quantity20TwoCloneStress'] = page.evaluate('''() => {
              const A=Acceptance,p=A.p(),T=G.NarutoTenten;G.SelfClones.summon(p);
              const actors=[p,...G.SelfClones.actors()];A.assert(actors.length===3,'stress requires two native clones');
              for(const a of actors){a.quantityPicks=20;a.quantityBonus=20;a.target=A.spawn(190,0);for(const m of a.moves)m.t=999;const m=a.moves.find(m=>m.id==='naruto-tenten-twin');m.t=0;}
              A.castNative('naruto-tenten-twin');const cv=document.createElement('canvas');cv.width=1200;cv.height=900;const c=cv.getContext('2d'),samples=[];let peakWeapons=0;
              for(let i=0;i<16;i++){const start=performance.now();A.advance(.05);G.Combat.drawGroundFields(c);G.Combat.drawAirFields(c);for(const a of actors)a.anim.draw(c,600,450);samples.push(performance.now()-start);peakWeapons=Math.max(peakWeapons,T.weapons.length);}
              const emitted=actors.map(a=>({quantityPicks:a.quantityPicks,totalEmitted:T.stateFor(a)?.totalEmitted||0}));A.assert(emitted.every(a=>a.totalEmitted>0),'native stress actors did not emit');
              const out={host:'same desktop Chromium host; not physical-phone FPS',steps:samples.length,stepSimulationSeconds:.05,quantityPicks:20,nativeClones:2,peakWeapons,emitted,elapsedMs:samples.reduce((a,b)=>a+b,0),perStepMs:samples};A.reset();return out;
            }''')
            context.close()
            ffmpeg = Path(os.environ.get('LOCALAPPDATA', '')) / 'ms-playwright/ffmpeg-1011/ffmpeg-win64.exe'
            subprocess.run([str(ffmpeg), '-y', '-f', 'image2pipe', '-framerate', '12', '-c:v', 'mjpeg', '-i', 'pipe:0', '-c:v', 'libvpx', '-b:v', '1800k', str(OUT / f'{label}-complete.webm')], input=b''.join(frames), capture_output=True, check=True)
            print(label, 'complete suite PASS', flush=True)
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    write_preview(report)


def capture_mastery(page, capture):
    page.evaluate('Proof.reset()')
    poses = []
    for i, dt in enumerate([.05, .1, .1, .1]):
        page.evaluate('(dt)=>Acceptance.advance(dt)', dt)
        pose = page.evaluate('G.AnimationLab.stateFor(G.Game.player.anim)')
        assert pose['key'] == 'tenten-mastery' and pose['frame'] == i, pose
        assert page.evaluate("!G.NarutoTenten.activeFor(G.Game.player) && !G.Game.player.slots.flat().some(m=>m.id==='naruto-tenten-mastery')"), 'mastery must stay passive'
        capture(f'mastery-{i+1}')
        poses.append({'key': pose['key'], 'frame': pose['frame']})
    return poses


def write_preview(report):
    captions = {
        'mastery-1':'忍具精通・檢視', 'mastery-2':'忍具精通・整備',
        'mastery-3':'忍具精通・收卷', 'mastery-4':'忍具精通・就緒',
        'basic-release':'普攻・出手', 'basic-flight':'普攻・飛行', 'basic-impact':'普攻・命中',
        'fuma-outbound':'迴刃・出程', 'fuma-flight':'迴刃・飛行', 'fuma-turn':'迴刃・折返',
        'fuma-return':'迴刃・回程', 'fuma-catch':'迴刃・接刃', 'fuma-ready-steel':'迴刃・金屬蓄勢',
        'fuma-empowered':'迴刃・強化施放', 'twin-launch':'雙昇龍・放卷',
        'twin-batch-1':'雙昇龍・第一批', 'twin-batch-2':'雙昇龍・第二批',
        'twin-batch-3':'雙昇龍・第三批', 'twin-batch-4':'雙昇龍・第四批',
        'twin-landing':'雙昇龍・落地', 'tag-flight':'爆符・飛行', 'tag-land':'爆符・落地',
        'tag-fuse':'爆符・引信', 'tag-ignition':'爆符・點燃', 'tag-blast':'爆符・爆破',
        'tag-decay':'爆符・消散', 'bounce-route':'連彈・轉向', 'bounce-calm-route':'連彈・低動態',
        'direction-left':'左向演出', 'direction-right':'右向演出', 'direction-up':'上向演出',
        'direction-down':'下向演出', 'clone-owned-fields':'分身・獨立演出',
        'clone-scene-cleanup':'分身・換場清理'
    }
    cards = ''
    for label, data in report['viewports'].items():
        gallery = ''.join(f'<figure><a href="{name}"><img loading="lazy" src="{name}"></a><figcaption>{captions.get(name.removeprefix(label+"-").removesuffix(".png"), name)}</figcaption></figure>' for name in data['stills'])
        title = '桌機' if label == 'desktop' else '手機尺寸'
        cards += f'<section><h2>{title}</h2><video controls loop muted playsinline poster="{label}-twin-batch-4.png" src="{label}-complete.webm"></video><div class="gallery">{gallery}</div></section>'
    (OUT / 'preview.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>天天完整演出</title><style>body{font:16px/1.7 system-ui;background:#14251f;color:#eee;margin:24px}main{max-width:1200px;margin:auto}video{max-width:100%;max-height:80vh}.gallery{display:flex;gap:16px;overflow:auto}figure{margin:8px 0;flex:none}img{height:240px}a{color:#9ed}section{margin:32px 0}</style><main><h1>天天完整演出</h1><p>普攻 → 風魔去回與接刃 → 雙卷螺旋升空與八種忍具 → 爆符飛行、落地與引爆 → 全忍具連彈。影片為正常遊戲逐幀慢放；風魔不顯示卷軸。雙昇龍示範採用四張數量卡的可達配置。</p><p><a href="../../digimon.html?lang=zh-TW">進入遊戲</a> · <a href="report.json">驗證紀錄</a></p>'+cards+'</main>', 'utf-8')


if __name__ == '__main__':
    main()
