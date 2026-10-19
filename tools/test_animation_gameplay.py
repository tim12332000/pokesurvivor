"""Exercise the actual iframe game; synthetic opaque test cells are not art candidates."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json, mimetypes
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = 'http://127.0.0.1:8318/'

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    context = browser.new_context(viewport={'width':1200,'height':900}, service_workers='block')
    errors=[];synthetic=True
    def route(request):
        path=unquote(urlsplit(request.request.url).path).lstrip('/')
        if synthetic and path=='art-review/playtest-config.json':
            return request.fulfill(json={'sprites':{'30002':{'image':'test-cells.svg','columns':4,'rows':4,'directions':{'down':0,'up':1,'left':2,'right':3}}}})
        if path=='art-review/test-cells.svg':
            cells=''.join(f'<rect x="{col*40+13}" y="{row*40+4}" width="14" height="34" fill="{color}"/>' for row,color in enumerate(['red','blue','green','yellow']) for col in range(4))
            return request.fulfill(content_type='image/svg+xml',body=f'<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160">{cells}</svg>')
        file=ROOT/path
        request.fulfill(status=200 if file.is_file() else 404,body=file.read_bytes() if file.is_file() else b'',content_type=mimetypes.guess_type(file)[0] or 'application/octet-stream')
    context.route(BASE+'**',route)
    page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'art-review/playtest.html')
    try:
        page.wait_for_function('GameplayLab.ready && GameplayLab.assets.has(30002)')
    except Exception:
        print('BOOT DIAGNOSTICS',page.evaluate('({ready:GameplayLab.ready,assets:[...GameplayLab.assets.keys()],frames:[...document.querySelectorAll("iframe")].map(f=>({url:f.src,boot:f.contentDocument.querySelector("#boot")?.className,G:!!f.contentWindow.G,db:!!f.contentWindow.G?.DB?.save,text:f.contentDocument.body.innerText.slice(0,200)}))})'),errors)
        raise
    frame=page.frame_locator('#game')
    if frame.locator('#tap-start').is_visible():frame.locator('#tap-start').click()
    page.locator('[data-hero="30002"]').click()
    page.wait_for_function('GameplayLab.attached?.player.dex===30002')
    iframe=next(f for f in page.frames if '/.omx/digimon.html' in f.url)
    iframe.evaluate('G.Game.togglePause()')
    page.locator('#training').click()
    report=iframe.evaluate('''() => {
      const p=G.Game.player;G.Combat.clearFields();G.EnemyMgr.clear();
      G.World.collide=()=>{};G.World.isLiquid=()=>false;
      p.x=p.y=0;p.hp=p.maxHp;p.dead=false;p.frozen=false;
      p.setActive(p.slots.findIndex(g=>g.some(m=>m.id==='naruto-fuma-shuriken')));
      const enemy=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},100,0,{hp:1,spd:1,dmg:1});G.EnemyMgr.add(enemy);
      return {skills:p.moves.length,damage:p.activeMove().dmg};
    }''')
    assert report['skills']>=5,report
    # Real keyboard state flows through G.Input.axis and Player.update, with deterministic dt.
    distances=[]
    for candidate in (False,True):
        page.locator('#candidate').set_checked(candidate)
        page.locator('#game').focus();page.keyboard.down('KeyD')
        distances.append(iframe.evaluate('''() => {const p=G.Game.player,x=p.x;p.update(.1);return p.x-x;}'''))
        page.keyboard.up('KeyD')
    assert distances[0]>0 and abs(distances[0]-distances[1])<1e-8,distances
    report.update(iframe.evaluate('''() => {
      const p=G.Game.player,L=parent.GameplayLab;
      const assert=(x,msg)=>{if(!x)throw Error(msg)};
      p.update(.01);assert(p.target===G.EnemyMgr.all()[0],'automatic target lost');
      const m=p.activeMove(),damage=m.dmg;m.t=0;
      let cast=0;const original=p.cast;p.cast=function(...a){cast++;return original.apply(this,a)};
      G.Combat.tick(.1,p,0);p.cast=original;
      assert(cast===1,'selected skill no longer autocasts');assert(m.dmg===damage,'render toggle changed damage');
      G.Combat.clearFields();p.anim.once=false;p.anim.done=false;p.walking=true;p.moveAngle=-Math.PI/2;p.attackFace=0;
      const ctx=document.createElement('canvas').getContext('2d');let imageCall;
      const draw=ctx.drawImage.bind(ctx);ctx.drawImage=(...a)=>{imageCall=a;return draw(...a)};
      const before=L.counters.candidate;p.anim.draw(ctx,80,80);
      assert(L.counters.candidate===before+1,'walking candidate not shown');assert(imageCall[2]>=40&&imageCall[2]<80,'up direction row incorrect');
      p.moveAngle=Math.PI/2;p.anim.draw(ctx,80,80);assert(imageCall[2]<40,'down direction row incorrect');
      p.anim.play('Shoot');const fallback=L.counters.source;p.anim.draw(ctx,80,80);assert(L.counters.source===fallback+1,'cast pose overwritten');
      const old=p.anim.draw;p.setActive(p.slots.findIndex(g=>g.some(m=>m.id==='naruto-kusanagi')));
      p.anim.once=false;p.frozen=false;p.update(.01);assert(!p.frozen,'switch froze player');
      assert(p.anim.draw===old,'switch replaced renderer');
      const clone=new G.Sprites.Animator(p.dex,1);assert(!Object.hasOwn(clone,'draw'),'other animator patched');
      return {autocasts:cast,damage,upDownRowsCorrect:true,castPosePreserved:true,isolatedRenderer:true};
    }'''))
    report['continuityAudit']=iframe.evaluate('''() => {
      const p=G.Game.player,A=G.CastContinuityLab,assert=(v,m)=>{if(!v)throw Error(m)};
      const block=G.World.projectileBlock;G.World.projectileBlock=()=>false;
      const start=(id,aim=0)=>{G.Combat.clearFields();G.Projectiles.clear();A.clear();p.aim=aim;
        p.setActive(p.slots.findIndex(s=>s.some(m=>m.id===id)));p.activeMove().t=0;G.Combat.tick(.001,p,0);};
      try{
        start('naruto-fireball');G.Combat.updateFields(.239);assert(!A.events.length,'fire released before seal');
        G.Combat.updateFields(.002);const fire=A.events[0];assert(fire&&fire.originError<.001&&fire.phase==='breath','mouth/release timeline mismatch '+JSON.stringify({fire,active:G.NarutoFireball.active?.phase,shots:G.Projectiles.all().map(p=>({x:p.x,y:p.y,shape:p.vis?.proj}))}));
        start('naruto-fuma-shuriken');G.Combat.updateFields(.199);assert(!A.events.length,'weapon released before charge');
        G.Combat.updateFields(.002);const fuma=A.events[0];assert(fuma&&fuma.originError>15,'existing center-origin gap was not detected');
        assert(fuma.actorAnimation!=='Attack','expected to audit current generic cast');
        parent.document.getElementById('continuity').checked=true;
        const other=new G.Player(G.DEX_BY[30002],{});parent.document.getElementById('continuity').checked=false;
        other.cast(G.Moves.instance('naruto-fuma-shuriken'));const otherBaseline=other.anim.cur;
        parent.document.getElementById('continuity').checked=true;other.cast(G.Moves.instance('naruto-fuma-shuriken'));
        assert(other.anim.cur===otherBaseline,'prototype changed another player casting');
        start('naruto-fuma-shuriken');p.x+=12;p.y+=5;G.Combat.updateFields(.199);
        assert(!A.events.length,'prototype projectile precedes release');
        assert(p.anim.cur==='Attack','throw falls back to generic jutsu on recovery');
        const airContext=document.createElement('canvas').getContext('2d');let ornaments=0;
        airContext.drawImage=()=>ornaments++;G.Combat.drawAirFields(airContext);
        assert(ornaments===0,'generic center charge ornament duplicates held weapon');
        const ctx=document.createElement('canvas').getContext('2d'),draw=ctx.drawImage;let source;
        ctx.drawImage=function(image,...args){if(image===G.Naruto.records.get(30002).image)source=args.slice(0,4);return draw.call(this,image,...args)};
        p.anim.draw(ctx,100,100);assert(source?.join()==='196,107,50,40','throw windup uses generic jutsu');
        G.Combat.updateFields(.002);const release=A.events[0],shot=G.Projectiles.all()[0];
        assert(release?.mode==='prototype'&&release.originError<.001,'hand-release anchor mismatch');
        assert(release.sourceFrame.join()==='252,108,48,39','release frame mismatch');
        assert(shot.fumaCurve.sx===release.expected.x&&shot.fumaCurve.sy===release.expected.y,'curve teleported away from release hand');
        assert(shot.dmg===p.activeMove().dmg*p.atk&&Math.hypot(shot.vx,shot.vy)===460,'prototype changed power/speed');
        p.setActive(p.slots.findIndex(s=>s.some(m=>m.id==='naruto-kusanagi')));G.Combat.updateFields(.01);
        assert(G.Projectiles.all().includes(shot),'switch removed an already thrown weapon');
        start('naruto-fuma-shuriken');G.Combat.updateFields(.1);p.setActive(p.slots.findIndex(s=>s.some(m=>m.id==='naruto-kusanagi')));G.Combat.updateFields(.101);
        assert(!G.Projectiles.all().length&&A.events[0]?.reason==='switched-before-release','pre-release cancellation failed');
        start('naruto-fuma-shuriken');G.World.projectileBlock=()=>true;G.Combat.updateFields(.201);
        assert(!G.Projectiles.all().length&&A.events[0]?.reason==='blocked-hand-origin','hand origin crossed a wall');
        G.World.projectileBlock=()=>false;start('naruto-fuma-shuriken',Math.PI);G.Combat.updateFields(.201);
        assert(A.events[0].expected.x<p.x&&A.events[0].originError<.001,'left mirrored hand mismatch');
        p.quantityBonus=2;start('naruto-fuma-shuriken');G.Combat.updateFields(.201);
        assert(A.events.length===3&&A.events.every(e=>e.originError<.001),'quantity release duplicated or detached');
        return {fireball:{age:fire.castAge,originError:fire.originError},baselineFuma:{originError:fuma.originError,actorAnimation:fuma.actorAnimation},prototypeFuma:{originError:release.originError,releaseFrame:release.sourceFrame,movementAnchor:true,cancellation:'before release only',curveOrigin:'matches hand',powerAndSpeed:'unchanged',walls:'blocked',mirror:'left passed',quantity:'three shots from same hand'}};
      }finally{p.quantityBonus=0;parent.document.getElementById('continuity').checked=false;G.World.projectileBlock=block;G.Combat.clearFields();G.Projectiles.clear();}
    }''')
    old_wrapper=iframe.evaluate('window.oldPlayer=G.Game.player;window.oldOriginal=parent.GameplayLab.attached.original;true')
    page.locator('[data-hero="30001"]').click()
    page.wait_for_function('GameplayLab.attached?.player.dex===30001')
    assert iframe.evaluate('oldPlayer.anim.draw===oldOriginal'),'old player renderer not restored'
    synthetic=False
    page.evaluate('GameplayLab.reloadConfig()')
    assert page.evaluate('GameplayLab.assets.size')==2,'actual curated movement sheets missing'
    for dex,name in [(30001,'naruto'),(30002,'sasuke')]:
        page.locator(f'[data-hero="{dex}"]').click()
        page.wait_for_function(f'GameplayLab.attached?.player.dex==={dex}')
        iframe.evaluate('G.Game.togglePause();G.Combat.clearFields();G.EnemyMgr.clear();G.Game.player.walking=true;G.Game.player.moveAngle=Math.PI/2;G.Game.player.anim.once=false')
        page.locator('#candidate').set_checked(True)
        page.screenshot(path=str(ROOT/'art-review'/'previews'/f'{name}-actual-game-walk.png'))
        iframe.evaluate("G.Game.player.anim.play('Shoot')")
        page.screenshot(path=str(ROOT/'art-review'/'previews'/f'{name}-actual-game-cast.png'))
    page.locator('#continuity').set_checked(True)
    iframe.evaluate('''()=>{
      const p=G.Game.player;if(G.Game.state==='playing')G.Game.togglePause();G.UI.hide('scr-pause');
      G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();p.x=p.y=0;p.aim=0;p.walking=false;p.flash=0;
      if(!p.hasMove('naruto-fuma-shuriken'))p.addMove('naruto-fuma-shuriken');
      p.setActive(p.slots.findIndex(s=>s.some(m=>m.id==='naruto-fuma-shuriken')));
      const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},180,0,{hp:1,spd:1,dmg:1});G.EnemyMgr.add(e);p.target=e;
      p.activeMove().t=0;G.Combat.tick(.001,p,0);G.Combat.updateFields(.199);G.Camera.x=G.Camera.y=0;
    }''')
    page.screenshot(path=str(ROOT/'art-review/previews/fuma-continuity-windup.png'))
    iframe.evaluate('G.Combat.updateFields(.002)')
    page.screenshot(path=str(ROOT/'art-review/previews/fuma-continuity-release.png'))
    mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,service_workers='block')
    mobile.route(BASE+'**',route)
    phone=mobile.new_page();phone.on('pageerror',lambda e:errors.append(str(e)));phone.goto(BASE+'art-review/playtest.html')
    phone.wait_for_function('GameplayLab.ready && GameplayLab.assets.has(30002)')
    if phone.frame_locator('#game').locator('#tap-start').is_visible():phone.frame_locator('#game').locator('#tap-start').tap()
    phone.locator('[data-hero="30002"]').tap();phone.wait_for_function('GameplayLab.attached?.player.dex===30002')
    phone.locator('#candidate').set_checked(True)
    gameframe=next(f for f in phone.frames if '/.omx/digimon.html' in f.url)
    gameframe.evaluate("if(G.Game.state==='playing')G.Game.togglePause();G.UI.hide('scr-pause');G.Game.player.walking=true;G.Game.player.anim.once=false;G.Game.player.moveAngle=-Math.PI/2")
    bounds=phone.locator('#game').bounding_box();assert bounds['y']+bounds['height']<=844.5
    assert gameframe.evaluate('G.Touch.active&&G.Touch.controlLayout(innerWidth,innerHeight,2).slots.every(s=>s.y+s.h<=innerHeight)')
    phone.screenshot(path=str(ROOT/'art-review/previews/playtest-mobile.png'))
    assert not errors,errors
    report['movementDistances']=distances;report['oldPlayerRestored']=True
    print(json.dumps(report,ensure_ascii=False))
    browser.close()
