"""Fresh Lv1 keyboard/card run through learning and using the stationary lure."""
import json
import time
from playwright.sync_api import sync_playwright
import test_shikamaru as base
from test_shikamaru_decoy import manifest

OUT = base.ROOT / 'art-review/shikamaru/qa/decoy/natural'
OBSERVE = r'''() => {
 const D=G.NarutoShikamaruDecoy,Q=window.DecoyNatural={offers:[],ledger:[],offer:null,inputs:[],samples:[],completed:false};
 Q.snapshot=()=>{const p=G.Game.player;return p?{time:G.Game.st.time,level:p.level,hp:p.hp,x:p.x,y:p.y,dead:p.dead,moves:p.moves.map(m=>({id:m.id,rank:m.lvl})),stats:D.stats(p),decoys:D.decoys().filter(d=>d.owner===p).map(d=>({id:d.id,x:d.x,y:d.y,age:d.age,life:d.life,enemies:d.enemies.size}))}:null};
 const show=G.RunUI.showLevelUp;
 G.RunUI.showLevelUp=function(level,list,cb,...args){const offer={serial:Q.offers.length+1,level,options:list.map(c=>({key:c.key,type:c.type,title:c.title}))};Q.offers.push(offer);Q.offer=offer;return show.call(this,level,list,c=>{cb(c);Q.ledger.push({level,key:c.key,snapshot:Q.snapshot()});Q.offer=null},...args)};
 let last=-1,first=null;
 function sample(){if(G.Game.state==='playing'){const s=Q.snapshot();if(s&&s.time-last>=.1){last=s.time;Q.samples.push(s);if(!first&&s.decoys.length)first=s.decoys[0];if(first&&!s.decoys.some(d=>d.id===first.id)&&(s.stats?.redirects||0)>0)Q.completed=true;}}requestAnimationFrame(sample)}requestAnimationFrame(sample);
}'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'sourceBefore': manifest(), 'policy': 'Fresh save, normal Lv1, real card clicks and keyboard only; native HP, XP, enemy AI and simulation clocks.'}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        context = browser.new_context(viewport={'width':1100,'height':850}, service_workers='block', record_video_dir=str(OUT/'raw'))
        page = context.new_page()
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        page.goto(base.URL)
        page.wait_for_function('window.PS_REDRAWN_READY&&G?.NarutoShikamaruDecoy&&document.getElementById("boot").classList.contains("hidden")')
        if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
        page.locator('[data-quick-naruto="30017"]').click()
        report['permanent'] = page.evaluate('G.DB.upgradesOf(G.DB.save.partner)')
        assert not any(report['permanent'].values())
        page.evaluate(OBSERVE)
        page.locator('#scr-menu [data-go="play"]').click()
        page.wait_for_function('G.Game.state==="playing"&&G.Game.player?.dex===30017')
        report['initial'] = page.evaluate('DecoyNatural.snapshot()')
        started = time.monotonic()
        held = None
        serial = None
        visible_saved = False
        while time.monotonic()-started < 150:
            data = page.evaluate('({state:G.Game.state,snapshot:DecoyNatural.snapshot(),offer:DecoyNatural.offer,completed:DecoyNatural.completed})')
            snap = data['snapshot']
            if data['completed'] or snap['dead'] or data['state']=='over': break
            if snap['decoys'] and not visible_saved:
                page.screenshot(path=str(OUT/'stationary-shadow.png'))
                visible_saved = True
            if data['state']=='levelup' and data['offer'] and serial!=data['offer']['serial']:
                if held: page.keyboard.up(held); held=None
                offer=data['offer']
                def priority(c):
                    if c['key']=='new:naruto-shikamaru-decoy': return 0
                    if c['key']=='stat:quantity': return 1
                    if c['key']=='up:naruto-shikamaru': return 2
                    return 8
                index=min(range(len(offer['options'])), key=lambda i:(priority(offer['options'][i]),i))
                page.screenshot(path=str(OUT/f'card-Lv{offer["level"]}.png'))
                page.locator('#cards .card').nth(index).click()
                serial=offer['serial']
            elif page.locator('#scr-item').is_visible(): page.locator('#item-cards .card').first.click()
            elif page.locator('#scr-bond').is_visible(): page.locator('#bond-cards .card').first.click()
            elif data['state']=='playing':
                key=['KeyD','KeyS','KeyA','KeyW'][int(snap['time']//1.5)%4]
                if key!=held:
                    if held: page.keyboard.up(held)
                    page.keyboard.down(key); held=key
                    page.evaluate('v=>DecoyNatural.inputs.push(v)', {'time':snap['time'],'key':key})
            page.wait_for_timeout(80)
        if held: page.keyboard.up(held)
        report.update(page.evaluate('({ledger:DecoyNatural.ledger,offers:DecoyNatural.offers,inputs:DecoyNatural.inputs,samples:DecoyNatural.samples,completed:DecoyNatural.completed,final:DecoyNatural.snapshot()})'))
        page.screenshot(path=str(OUT/'final.png'))
        video=page.video
        context.close(); video.save_as(str(OUT/'native-growth.webm')); video.delete(); browser.close()
    report['sourceAfter']=manifest()
    report['sourceStable']=report['sourceBefore']==report['sourceAfter']
    report['ok']=report['initial']['level']==1 and any(c['key']=='new:naruto-shikamaru-decoy' for c in report['ledger']) and report['completed'] and not report['errors'] and report['sourceStable']
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    assert report['ok'], {'final':report['final'],'ledger':report['ledger'],'errors':report['errors']}
    print('Fresh Lv1, true learn card, native lure redirects and expiry PASS')


if __name__=='__main__': main()
