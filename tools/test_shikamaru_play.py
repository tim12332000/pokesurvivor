"""Unmodified level-one Shikamaru play: UI input and observational hooks only.

No XP/HP/clock/enemy/cast mutation; failed attempts remain in evidence.
"""
from __future__ import annotations
import hashlib
import json
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('SHIKAMARU_OUT', ROOT / 'art-review/shikamaru/qa/natural'))
URL = os.environ.get('SHIKAMARU_URL', 'http://127.0.0.1:8348/.omx/digimon.html?lang=zh-TW&layout=wide')
DEX = int(os.environ.get('SHIKAMARU_DEX', '30017'))
SECONDS = float(os.environ.get('SHIKAMARU_SECONDS', '480'))

OBSERVE = r"""() => {
 const R=window.ShikamaruQA={ledger:[],offers:[],hits:[],casts:[],samples:[],current:null};
 R.snapshot=()=>{const p=G.Game.player;return p?{time:G.Game.st.time,level:p.level,hp:p.hp,maxHp:p.maxHp,dead:!!p.dead,x:p.x,y:p.y,xp:p.xp,xpNext:p.xpNext,kills:p.kills,quantity:p.quantityPicks||0,moves:p.moves.map(m=>({id:m.id,rank:m.lvl,passive:!!m.passive})),module:G.NarutoShikamaru?.stats?.(p)||null}:null};
 const hurt=G.Enemy.prototype.hurt;G.Enemy.prototype.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);if(args[6]===G.Game.player)R.hits.push({t:G.Game.st.time,id:args[7],loss:hp-this.hp,x:this.x,y:this.y});return result};
 const cast=G.Player.prototype.cast;G.Player.prototype.cast=function(m,...args){if(this===G.Game.player)R.casts.push({t:G.Game.st.time,id:m.id,rank:m.lvl});return cast.call(this,m,...args)};
 const show=G.RunUI.showLevelUp;G.RunUI.showLevelUp=function(level,list,cb,...args){const offer={serial:R.offers.length,t:G.Game.st.time,level,options:list.map(c=>({key:c.key,type:c.type,title:c.title,desc:c.desc}))};R.offers.push(offer);R.current=offer;return show.call(this,level,list,card=>{const before=R.snapshot();cb(card);R.ledger.push({cost:R.ledger.length+1,key:card.key,offer:offer.serial,before,after:R.snapshot()});R.current=null},...args)};
 let last=-1;function sample(){if(G.Game.state==='playing'&&G.Game.st.time-last>.5){last=G.Game.st.time;R.samples.push(R.snapshot())}requestAnimationFrame(sample)}requestAnimationFrame(sample);
}"""

def priority(card):
    return {'new': 0, 'up': 1}.get(card['type'], {'stat:quantity': 2, 'stat:atk': 3, 'stat:cd': 4, 'stat:maxHealthPercent': 5, 'stat:heal': 6}.get(card['key'], 10))

def play(browser, attempt):
    folder=OUT / f'attempt-{attempt}'
    folder.mkdir(parents=True,exist_ok=True)
    context=browser.new_context(viewport={'width':1100,'height':850},service_workers='block',record_video_dir=str(folder/'raw'),record_video_size={'width':1100,'height':850})
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_function('window.PS_REDRAWN_READY&&window.G?.NarutoShikamaru&&document.getElementById("boot").classList.contains("hidden")')
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.locator(f'[data-quick-naruto="{DEX}"]').click()
    permanent=page.evaluate('G.DB.upgradesOf(G.DB.save.partner)')
    assert not any(permanent.values()),permanent
    page.evaluate(OBSERVE)
    page.locator('#scr-menu [data-go="play"]').click()
    page.wait_for_function(f'G.Game.player?.dex==={DEX}&&G.Game.state==="playing"')
    initial=page.evaluate('ShikamaruQA.snapshot()');assert initial['level']==1
    held=None;serial=None;started=time.monotonic();next_image=0;next_progress=30
    while time.monotonic()-started<max(300,SECONDS*2):
        s=page.evaluate('({state:G.Game.state,t:G.Game.st.time,dead:!!G.Game.player?.dead,offer:ShikamaruQA.current})')
        if s['dead'] or s['state']=='over' or s['t']>=SECONDS:break
        if s['state']=='levelup' and s['offer'] and s['offer']['serial']!=serial:
            if held:page.keyboard.up(held);held=None
            offer=s['offer'];chosen=min(range(len(offer['options'])),key=lambda i:(priority(offer['options'][i]),i))
            page.screenshot(path=str(folder/f'card-{offer["serial"]}.png'))
            page.locator('#cards .card').nth(chosen).click();serial=offer['serial']
        elif page.locator('#scr-item').is_visible():page.locator('#item-cards .card').first.click()
        elif page.locator('#scr-bond').is_visible():page.locator('#bond-cards .card').first.click()
        elif s['state']=='playing':
            key=['KeyD','KeyS','KeyA','KeyW'][int(s['t']//1.5)%4]
            if key!=held:
                if held:page.keyboard.up(held)
                page.keyboard.down(key);held=key
            if s['t']>=next_image:page.screenshot(path=str(folder/f'play-{s["t"]:.1f}.png'));next_image+=30
            if s['t']>=next_progress:
                progress=page.evaluate('ShikamaruQA.snapshot()');(folder/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2),encoding='utf8');print('natural',round(s['t']), 'Lv',progress['level'],'HP',round(progress['hp']),flush=True);next_progress+=30
        elif s['state']=='paused':page.locator('#btn-resume').click()
        page.wait_for_timeout(80)
    if held:page.keyboard.up(held)
    data=page.evaluate('({ledger:ShikamaruQA.ledger,offers:ShikamaruQA.offers,hits:ShikamaruQA.hits,casts:ShikamaruQA.casts,samples:ShikamaruQA.samples,final:ShikamaruQA.snapshot(),state:G.Game.state})')
    data.update(initial=initial,permanent=permanent,errors=errors,wallSeconds=time.monotonic()-started,policy='D/S/A/W square, 1.5 native seconds each; new > upgrade > quantity > attack > cooldown > health; native UI clicks; observational hooks only')
    page.screenshot(path=str(folder/'final.png'));video=page.video;context.close();video.save_as(str(folder/'native-play.webm'));video.delete()
    (folder/'run.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    return {'attempt':attempt,'level':data['final']['level'],'time':data['final']['time'],'dead':data['final']['dead'],'cards':len(data['ledger']),'moves':data['final']['moves'],'hitsBySkill':{id:sum(h['id']==id and h['loss']>0 for h in data['hits']) for id in set(h['id'] for h in data['hits'])},'errors':errors}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sources=['.omx/naruto-shikamaru.js','.omx/naruto.js','.omx/naruto-skills.js','.omx/naruto-training.js','art-review/shikamaru-art.js','art-review/shikamaru-frames.json','art-review/shikamaru/atlas-v1.png','js/entities/enemy.js','js/systems/combat.js','js/systems/self-clone.js','.omx/jujutsu-growth.js','.omx/digimon.html']
    hashes=lambda:{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources if (ROOT/s).exists()}
    report={'url':URL,'sourceBefore':hashes(),'runs':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME,headless=True)
        for attempt in range(1,int(os.environ.get('SHIKAMARU_ATTEMPTS','2'))+1):
            result=play(browser,attempt);report['runs'].append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
            (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
            if not result['dead'] and result['time']>=SECONDS:break
        browser.close()
    report['sourceAfter']=hashes();report['sourceStable']=report['sourceAfter']==report['sourceBefore']
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':main()
