"""Verify signature-only learning without removing internal counter projectiles."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import mimetypes
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    context = browser.new_context(locale='zh-TW', service_workers='block')
    def proxy(route):
        file = ROOT / unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
        route.fulfill(status=200 if file.is_file() else 404, body=file.read_bytes() if file.is_file() else b'', content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
    context.route('https://tim12332000.github.io/pokesurvivor/**', proxy)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    try:
        page.goto(URL)
        page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
        result = page.evaluate(r'''() => {
          const assert=(ok,msg)=>{if(!ok)throw Error(msg)},retired=['naruto-kunai','naruto-shuriken'];
          const checks=[];
          for(const dex of [30006,30001,30002]){
            G.Game.toUI();G.Naruto.choose(dex);G.Flow.play();G.Game.togglePause();
            const pl=G.Game.player,main=G.NarutoSkillCatalog.byDex.get(dex).id;
            assert(pl.moves.length===(dex===30002?2:1)&&pl.hasMove(main),'Wrong initial signature '+dex);
            const milestones=G.NarutoSkillCatalog.extraPools.get(dex);
            for(const level of [1,3,6,9,12]){
              pl.level=level;
              const pool=G.Moves.poolFor(pl.mon);
              assert(retired.every(id=>!pool.includes(id)),'Retired tool in pool');
              for(const [index,id] of milestones.entries()){
                const gate=G.Moves.BY_ID[id].learnLevel||(index===0?3:6);
                assert(pool.includes(id)===(level>=gate),'Gate changed '+id+' at '+level);
              }
              for(let i=0;i<40;i++){
                const cards=G.LevelUp.offer(pl,3);
                assert(cards.length===3,'Fewer than three cards');
                assert(cards.every(c=>!retired.some(id=>c.key.endsWith(':'+id))),'Retired learn/upgrade card');
              }
            }
            for(const id of retired)assert(pl.addMove(id),'Internal definition removed '+id);
            for(let i=0;i<40;i++){
              const cards=G.LevelUp.offer(pl,3);
              assert(cards.length===3&&cards.every(c=>!retired.some(id=>c.key.endsWith(':'+id))),'Legacy tool upgrade offered');
            }
            checks.push({dex,initial:main,gates:[3,6,9],offers:200});
          }
          const pl=G.Game.player;
          G.Projectiles.clear();pl.invuln=0;pl.dead=false;pl.hp=pl.maxHp;pl.frozen=0;pl.quantityBonus=0;
          assert(pl.addMove('naruto-sharingan'),'Could not learn passive fixture');
          Object.assign(pl.moves.find(m=>m.id==='naruto-sharingan'),G.Moves.instance('naruto-sharingan',2));
          G.NarutoSharingan.sync(pl);
          const random=Math.random;Math.random=()=>.01;
          try{pl.hurt(10);}finally{Math.random=random;}
          assert(G.Projectiles.count===3,'Sharingan internal counter broken');
          assert(G.Projectiles.all().every(p=>p.owner===pl),'Counter ownership lost');
          const guide=document.getElementById('scr-naruto-skills').textContent;
          assert(!guide.includes(G.Moves.BY_ID[retired[0]].name)&&!guide.includes(G.Moves.BY_ID[retired[1]].name),'Guide advertises retired tools');
          G.Game.toUI();return {characters:checks,counter:'three owned shuriken preserved',guide:'signature only'};
        }''')
        assert not errors, errors
        print(json.dumps({'ok':True,'checks':result,'pageErrors':errors},ensure_ascii=False))
    finally:
        browser.close()
