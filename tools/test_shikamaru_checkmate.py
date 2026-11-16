"""Production-entry tests for Shikamaru's checkmate; controlled combat, not natural play."""
import base64
import hashlib
import json
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_shikamaru as base

OUT = base.ROOT / 'art-review/shikamaru/qa/checkmate'
SETUP = r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;
 A.checkmateBuild=(rank=1,q=0)=>{A.reset();p.statsTaken={};p.moves=[G.Moves.instance('naruto-shikamaru',1)];p.level=5;const ledger=[];
 for(const id of ['naruto-shikamaru','naruto-shikamaru','naruto-shikamaru-checkmate']){const key=(id.endsWith('checkmate')?'new:':'up:')+id,c=G.LevelUp.offer(p,1000).find(c=>c.key===key);A.assert(c&&c.apply(p)!==false,'actual card unavailable '+key);ledger.push(key)}
 for(let i=1;i<rank;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='up:naruto-shikamaru-checkmate');A.assert(c&&c.apply(p)!==false,'ultimate rank card missing');ledger.push(c.key)}
 for(let i=0;i<q;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');A.assert(c&&c.apply(p)!==false,'quantity card missing');ledger.push(c.key)}return ledger};
 A.checkmateArena=()=>{const ledger=A.checkmateBuild(),es=[[100,0],[130,90],[-100,80]].map(([x,y])=>A.spawn(x,y));p.target=es[0];return {ledger,es}};
 A.captureCheckmate=()=>{const b=S.casts.find(b=>b.kind==='shadow');A.assert(b,'shadow missing');for(let i=0;i<100&&!b.chain.ended;i++)A.step(.01);return b};
 A.checkmateManual=()=>{const fixture=A.checkmateArena();A.cast(p.moves[0]);A.captureCheckmate();const m=p.moves.find(m=>m.id.endsWith('checkmate'));A.cast(m);return {...fixture,b:S.casts.at(-1),m}};
}'''

CHECK = r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out={};
 A.reset();p.moves=[G.Moves.instance('naruto-shikamaru')];p.level=4;A.assert(!G.LevelUp.offer(p,1000).some(c=>c.key==='new:naruto-shikamaru-checkmate'),'early ultimate card');
 let {ledger,es,b,m}=A.checkmateManual();const hs=es.map(A.watch),far=A.spawn(800,800),fh=A.watch(far);A.assert(b.ultimate&&b.spec.pulses===3,'ultimate profile wrong');
 A.assert(!S.canCast(p,m),'cooldown missing');A.finish(b.duration+.1);const contacts=S.stats(p).contacts.filter(c=>c.moveId===m.id),direct=contacts.filter(c=>c.geometry?.kind==='xyz-tip-sweep'),blast=contacts.filter(c=>c.geometry?.kind==='planted-tag-blast');
 A.assert(direct.length===9,'three true rounds per three targets missing '+direct.length);A.assert(blast.length===3,'overlapping final blasts duplicated or missed '+blast.length);A.assert(hs.every(h=>h.filter(e=>e.id===m.id).length===4&&h.every(e=>e.owner)),'native hurt attribution mismatch');A.assert(!fh.length,'out-of-range target hit');out.combat={ledger,direct:direct.length,blast:blast.length,hits:hs.map(h=>h.filter(e=>e.id===m.id).length),damage:contacts.reduce((n,c)=>n+c.damage,0)};
 const growth=[];for(const [rank,q]of [[1,0],[1,1],[1,2],[3,0],[5,2]]){A.checkmateBuild(rank,q);const m=p.moves.find(m=>m.id.endsWith('checkmate')),spec=S.profile(p,m);growth.push({rank,q,pulses:spec.pulses,radius:spec.blastRadius});const cards=G.LevelUp.offer(p,1000);if(q===0)A.assert(cards.find(c=>c.key==='stat:quantity')?.desc.includes('詰將連刺輪次'),'quantity preview omits ultimate consumer')}
 A.assert(growth.map(g=>g.pulses).join(',')==='3,4,5,4,7','growth contract wrong');out.growth=growth;
 ({es,b}=A.checkmateManual());A.finish(.01);G.World.projectilePathClear=()=>false;const wallHits=es.map(A.watch);A.finish(3);A.assert(wallHits.every(h=>!h.length),'wall failed to block ultimate');out.wall=true;
 for(const reason of ['clear','death','world','unlearn','pause']){({es,b,m}=A.checkmateManual());A.finish(1.08);A.assert(b.sites.size,'lifecycle fixture has no planted sites '+reason+' '+JSON.stringify({age:b.age,emitted:b.emitted,cancelled:b.cancelled,arcs:b.arcs.map(a=>({blocked:a.blocked,hit:a.hit,progress:a.progress})),hp:es.map(e=>e.hp),held:es.map(e=>S.held(e)),moves:p.moves.map(m=>m.id)}));const hits=es.map(A.watch),world=G.World;
 if(reason==='clear')S.clear(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};if(reason==='unlearn')p.moves=p.moves.filter(x=>x.id!==m.id);
 try{if(reason==='pause')S.update(3);else A.finish(3);A.assert(hits.every(h=>!h.length),'pending blast leaked '+reason)}finally{p.dead=false;G.World=world}
 }out.lifecycle=true;
 for(const callback of ['hurt','onDealt']){({es,b,m}=A.checkmateManual());let count=0;const dealt=p.onDealt;for(const e of es){const h=e.hurt;e.hurt=function(...args){const result=h.apply(this,args);if(args[7]===m.id){count++;if(callback==='hurt')S.clear(p)}return result}}if(callback==='onDealt')p.onDealt=()=>{if(count)S.clear(p)};try{A.finish(3);A.assert(count===1,'same-wave cancellation leaked '+callback)}finally{p.onDealt=dealt}}out.callbacks=true;
 for(const callback of ['hurt','onDealt']){({es,b,m}=A.checkmateManual());A.finish(b.blastAt-.02);let count=0;const dealt=p.onDealt;
  for(const e of es){const hurt=e.hurt;e.hurt=function(...args){const result=hurt.apply(this,args);if(args[7]===m.id&&b.age+1e-8>=b.blastAt){count++;if(callback==='hurt')S.clear(p)}return result}}
  if(callback==='onDealt')p.onDealt=()=>{if(count)S.clear(p)};
  try{A.finish(1);A.assert(count===1,'terminal blast callback failed to cancel other targets/sites '+callback)}finally{p.onDealt=dealt}
 }out.blastCallbacks=true;
 ({es,b,m}=A.checkmateManual());A.finish(1.08);const sites=[...b.sites.values()].map(s=>({x:s.x,y:s.y}));A.assert(sites.length===3,'first contact did not plant all tags');for(const e of es){e.hp=0;e.dead=true}const newcomer=A.spawn(sites[0].x,sites[0].y),nh=A.watch(newcomer);A.finish(2);A.assert(nh.some(h=>h.id===m.id),'planted tag disappeared with dead target');A.assert([...b.sites.values()].every((s,i)=>s.x===sites[i].x&&s.y===sites[i].y),'planted tag moved');out.fixedTags=true;
 ({es,b}=A.checkmateManual());A.finish(.6);const canvas=document.createElement('canvas');canvas.width=canvas.height=500;const ctx=canvas.getContext('2d'),before=JSON.stringify({stats:S.stats(p),age:b.age,sites:[...b.sites]});for(let i=0;i<30;i++){G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx)}A.assert(before===JSON.stringify({stats:S.stats(p),age:b.age,sites:[...b.sites]}),'renderer mutated damage/clock');out.readOnly=true;
 A.checkmateBuild(5);p.quantityPicks=16;es=Array.from({length:16},(_,i)=>A.spawn(Math.cos(i*Math.PI/8)*180,Math.sin(i*Math.PI/8)*180));A.cast(p.moves[0]);A.captureCheckmate();m=p.moves.find(m=>m.id.endsWith('checkmate'));A.cast(m);b=S.casts.at(-1);A.finish(b.duration+.1);
 const maxContacts=S.stats(p).contacts.filter(c=>c.moveId===m.id);A.assert(b.arcs.length===112&&b.sites.size===16,'maximum capacity dropped arcs/sites');A.assert(b.arcs.every(a=>a.hit),'maximum capacity dropped real piercing hits');A.assert(b.blastSeen.size===16,'maximum capacity missed terminal targets');out.maximum={arcs:b.arcs.length,sites:b.sites.size,terminalTargets:b.blastSeen.size,ledgerCappedContacts:maxContacts.length};
 for(const dir of [0,2,4,6]){const frame=G.ShikamaruArt.sample('cast',.2,dir,{kind:'checkmate',phase:'checkmate',moving:true,phaseAge:.2,phaseDuration:2});A.assert(/run/i.test(frame.key),'moving checkmate uses stationary pose '+frame.key)}out.movingPose=true;
 return out;
}'''

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'controlled': True, 'errors': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            page = browser.new_page(viewport={'width':1100,'height':850}, service_workers='block')
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            base.boot(page)
            page.evaluate('window.WarmEnemy=Acceptance.spawn(100,0)')
            page.wait_for_function('!!G.ShikamaruReferenceGeometry.bodyFor(WarmEnemy)')
            page.evaluate(SETUP)
            report['checks'] = page.evaluate(CHECK)
            print('mechanics PASS', flush=True)
            for label,width,height in [('desktop',1100,850),('mobile360',360,780),('mobile390',390,844)]:
                page.set_viewport_size({'width':width,'height':height})
                page.evaluate(r'''() => {const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.checkmateArena();window.CheckmateFrames=[];window.CheckmateSeen=new Set();const draw=G.Combat.drawAirFields;G.Combat.drawAirFields=function(ctx){const result=draw.call(this,ctx),b=S.stateFor(p)?.ultimate;if(b){let key=b.age<b.spec.release?'prepare':b.age<b.blastAt?(b.sites.size?'tags':'arches'):b.age<b.blastAt+.17?'blast':'blast-middle';if(!CheckmateSeen.has(key)){CheckmateSeen.add(key);const state={key,age:b.age,phase:S.activeFor(p)?.phase,sites:[...b.sites.values()].map(s=>({...s})),contacts:S.stats(p).contacts};queueMicrotask(()=>CheckmateFrames.push({...state,png:ctx.canvas.toDataURL()}))}}return result};A.resume()}''')
                page.wait_for_function('CheckmateSeen.has("blast-middle")', timeout=15000)
                page.keyboard.down('d');page.wait_for_timeout(200);page.keyboard.up('d')
                page.evaluate('Acceptance.pause()')
                data=page.evaluate('({frames:CheckmateFrames,stats:G.NarutoShikamaru.stats(),x:Acceptance.p().x})')
                for frame in data['frames']:
                    png=frame.pop('png');name=label+'-'+frame['key']+'.png'
                    (OUT/name).write_bytes(base64.b64decode(png.split(',',1)[1]));frame['image']=name
                report['viewports'][label]=data
                print(label,'native auto-cast PASS',flush=True)
            browser.close()
        assert not report['errors'],report['errors']
        report['ok']=True
    finally:
        (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

def natural():
    """Fresh Lv1, native enemies/XP, actual UI cards and keyboard movement."""
    folder=OUT/'natural';folder.mkdir(parents=True,exist_ok=True)
    report={'errors':[],'configuration':'Fresh save; native HP/XP/AI/time; actual UI card choices and keyboard movement.'}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        context=browser.new_context(viewport={'width':1100,'height':850},service_workers='block',record_video_dir=str(folder/'video'))
        page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.goto(base.URL);page.wait_for_function('window.PS_REDRAWN_READY&&window.G?.NarutoShikamaru&&document.getElementById("boot").classList.contains("hidden")')
        if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
        page.locator('[data-quick-naruto="30017"]').click()
        page.evaluate(r'''() => {window.CMQA={ledger:[],offer:null,offers:0,blasts:0,ultimateHits:0};const show=G.RunUI.showLevelUp;G.RunUI.showLevelUp=function(level,list,cb,...args){CMQA.offer={serial:++CMQA.offers,level,options:list.map(c=>({key:c.key,type:c.type}))};return show.call(this,level,list,c=>{cb(c);CMQA.ledger.push({level,key:c.key});CMQA.offer=null},...args)};const hurt=G.Enemy.prototype.hurt;G.Enemy.prototype.hurt=function(...args){const result=hurt.apply(this,args);if(args[7]==='naruto-shikamaru-checkmate'){CMQA.ultimateHits++;const b=G.NarutoShikamaru.stateFor(G.Game.player)?.ultimate;if(b?.age>=b.blastAt)CMQA.blasts++}return result}}''')
        page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.state==="playing"&&G.Game.player?.dex===30017')
        report['initial']=page.evaluate('({level:G.Game.player.level,moves:G.Game.player.moves.map(m=>m.id)})')
        started=time.monotonic();held=None;last=-30;serial=None
        while time.monotonic()-started<300:
            data=page.evaluate('({state:G.Game.state,time:G.Game.st.time,level:G.Game.player.level,hp:G.Game.player.hp,dead:G.Game.player.dead,qa:CMQA})')
            if data['qa']['blasts'] or data['dead'] or data['state']=='over':break
            if data['time']-last>=30:print('natural',round(data['time']),'Lv',data['level'],'HP',round(data['hp']),'ultimate hits',data['qa']['ultimateHits'],flush=True);last=data['time']
            if data['state']=='levelup' and data['qa']['offer'] and data['qa']['offer']['serial']!=serial:
                if held:page.keyboard.up(held);held=None
                offer=data['qa']['offer'];priority=lambda c:0 if c['key']=='new:naruto-shikamaru-checkmate' else 1 if c['key']=='stat:quantity' else 2 if c['key']=='up:naruto-shikamaru' else 3 if c['type']=='new' else 5
                selected=min(range(len(offer['options'])),key=lambda i:priority(offer['options'][i]));page.locator('#cards .card').nth(selected).click();serial=offer['serial']
            elif page.locator('#scr-item').is_visible():page.locator('#item-cards .card').first.click()
            elif page.locator('#scr-bond').is_visible():page.locator('#bond-cards .card').first.click()
            elif data['state']=='playing':
                key=['KeyD','KeyS','KeyA','KeyW'][int(data['time']//1.5)%4]
                if key!=held:
                    if held:page.keyboard.up(held)
                    page.keyboard.down(key);held=key
            page.wait_for_timeout(65)
        if held:page.keyboard.up(held)
        page.screenshot(path=str(folder/'final.png'));report['final']=data
        video=page.video;context.close();video.save_as(str(folder/'native-growth.webm'));video.delete();browser.close()
    report['ok']=report['initial']['level']==1 and data['qa']['blasts']>0 and not report['errors']
    (folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    assert report['ok'],report['final']

def package():
    folder=OUT/'package';folder.mkdir(parents=True,exist_ok=True)
    report={'errors':[],'assets':{},'viewports':{}}
    for name in ['.omx/naruto-shikamaru.js','.omx/naruto-skills.js','.omx/naruto.js','.omx/jujutsu-growth.js','art-review/shikamaru-art.js']:
        content=(base.ROOT/name).read_bytes()
        assert content==(base.ROOT/'dist-digimon'/name).read_bytes(),name
        report['assets'][name]=hashlib.sha256(content).hexdigest()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        for label,width,height in [('desktop',1100,850),('mobile360',360,780),('mobile390',390,844)]:
            context=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<600,has_touch=width<600,service_workers='block')
            page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.goto('http://127.0.0.1:8348/dist-digimon/?lang=zh-TW&hero=shikamaru');game=page
            if width>600:
                page.wait_for_selector('#portrait-game')
                game=page.locator('#portrait-game').element_handle().content_frame()
            game.wait_for_function('window.PS_REDRAWN_READY&&window.G?.NarutoShikamaru&&document.getElementById("boot").classList.contains("hidden")')
            if game.locator('#tap-start').is_visible():game.locator('#tap-start').click()
            game.locator('[data-quick-naruto="30017"]').click()
            cell=game.locator('.launch-kit > span').filter(has=game.locator('b',has_text='詰將'))
            cell.wait_for(state='visible');bbox=cell.bounding_box()
            assert 0<=bbox['x'] and bbox['x']+bbox['width']<=width,bbox
            assert 'Lv.5' in cell.inner_text()
            page.screenshot(path=str(folder/(label+'-selection.png')))
            game.locator('#scr-menu [data-go="play"]').click()
            game.wait_for_function('G.Game.player?.dex===30017&&G.Game.state==="playing"')
            data=game.evaluate("({level:G.Game.player.level,starter:G.Game.player.moves.map(m=>m.id),registered:!!G.Moves.BY_ID['naruto-shikamaru-checkmate'],pool:G.NarutoSkillCatalog.extraPools.get(30017),version:G.NarutoShikamaru.version})")
            assert data['level']==1 and data['starter']==['naruto-shikamaru'] and data['registered'] and 'naruto-shikamaru-checkmate' in data['pool'],json.dumps(data)
            report['viewports'][label]={'cell':bbox,**data};context.close()
            print(label,'packaged menu and Lv1 PASS',flush=True)
        browser.close()
    assert not report['errors'],report['errors']
    report['ok']=True;(folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':
    if '--natural' in sys.argv:natural()
    elif '--package' in sys.argv:package()
    else:main()
