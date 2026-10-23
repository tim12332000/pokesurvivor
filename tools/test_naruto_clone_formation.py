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
    import sys
    verify='--verify' in sys.argv
    out=ROOT/'.omx/state/naruto-clone-formation'
    out.mkdir(parents=True,exist_ok=True)
    page.evaluate("""async () => {
      G.Naruto.choose(30001);await G.Flow.play();if(G.Game.state==='playing')G.Game.togglePause();G.UI.hideAll();
      const p=G.Game.player;G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();
      Object.assign(G.World,{isFree:()=>true,collide:()=>{},projectileBlock:()=>false,isWall:()=>false,isLiquid:()=>false});
      p.x=p.y=0;p.hp=p.maxHp;p.dead=false;p.cdMul=1;p.quantityBonus=0;p.moves=[];p.slots=[];p.bind={};p.active=0;p.addMove('naruto-shadow-clones');
      G.Camera.x=G.Camera.y=0;G.Combat.tick(.01,p,0);G.Combat.updateFields(.42);
    }""")
    page.wait_for_timeout(120)
    page.screenshot(path=str(out/('after.png' if verify else 'before.png')))
    result=page.evaluate("""verify => {
      const p=G.Game.player,N=G.NarutoClones,id='naruto-shadow-clones',assert=(v,m)=>{if(!v)throw Error(m)};
      const positions=()=>N.actors.map(a=>({x:a.x-p.x,y:a.y-p.y}));
      const initial=positions();
      const balanced=spots=>Math.abs(spots.reduce((n,a)=>n+a.x,0))<1e-6&&Math.abs(spots.reduce((n,a)=>n+a.y,0))<1e-6;
      if(!verify)return {initial};
      assert(initial.length===2&&balanced(initial),'two summons not centered');
      assert(initial.every(a=>Math.abs(a.y)<1e-6)&&initial[0].x*initial[1].x<0,'two summons do not flank the owner');
      for(let i=0;i<100;i++)G.Combat.updateFields(.01);
      assert(positions().every((a,i)=>Math.hypot(a.x-initial[i].x,a.y-initial[i].y)<1e-6),'idle clones drift from summon formation');
      const counts=[];
      for(let rank=1;rank<=5;rank++)for(const quantity of [0,1,3]){
        N.clear();p.quantityBonus=quantity;const m=G.Moves.instance(id,rank);N.cast(p,m);
        assert(N.actors.length===N.limitOf(m,p),'missing ranks/quantity clones');
        assert(balanced(positions()),'unbalanced rank '+rank+' quantity '+quantity);
        for(const a of N.actors)for(const b of N.actors)if(a!==b)assert(Math.hypot(a.x-b.x,a.y-b.y)>=25,'overlapping clones');
        counts.push(N.actors.length);
      }
      N.clear();p.quantityBonus=0;const free=G.World.isFree;G.World.isFree=(x,y,r)=>Math.hypot(x-90,y)>23;
      assert(N.cast(p,G.Moves.instance(id,1))&&N.actors.length===2,'blocked spot fallback failed');
      assert(N.actors.every(a=>G.World.isFree(a.x,a.y,10)),'spawned inside obstacle');G.World.isFree=free;
      N.clear();return {initial,counts,checks:['centered','left and right positions','no idle drift','all ranks','quantity cards','spacing','obstacle fallback']};
    }""",verify)
    assert not errors,errors
    (out/('after.json' if verify else 'before.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result));browser.close()
