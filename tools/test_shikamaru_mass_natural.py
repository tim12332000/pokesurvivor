"""Fresh Lv1 production play through the mass shadow field's complete native window.

Only keyboard and visible card/item UI inputs change the run. Observers capture
cards, main-player casts/hurt events and the eventual field release; no HP, XP,
enemy AI, clocks or permanent upgrades are modified.
"""
import base64
import hashlib
import json
import time
from playwright.sync_api import sync_playwright
import test_shikamaru as base

OUT = base.ROOT / 'art-review/shikamaru/qa/mass/natural'
SOURCE = '.omx/naruto-shikamaru-mass.js'

OBSERVE = r'''() => {
 const M=G.NarutoShikamaruMass,Q=window.MassNatural={ledger:[],offers:[],offer:null,inputs:[],mainHits:[],casts:[],frames:[],samples:[],completed:false,completeCast:null};
 let lastSample=-1;const seen=new Set();
 Q.snapshot=()=>{const p=G.Game.player,s=p&&M.stateFor(p),b=s?.cast;return p?{time:G.Game.st.time,level:p.level,hp:p.hp,maxHp:p.maxHp,dead:!!p.dead,x:p.x,y:p.y,moves:p.moves.map(m=>({id:m.id,rank:m.lvl})),mass:s?{casts:s.casts,captured:s.captured,hits:s.hits,damage:s.damage,cooldown:s.cooldown,age:b?.age,active:!!b&&M.casts.includes(b),bound:b?.bound.size||0,exploded:!!b?.exploded,releaseAt:b?.releaseAt,duration:b?.duration}:null}:null};
 const show=G.RunUI.showLevelUp;
 G.RunUI.showLevelUp=function(level,list,cb,...args){const offer={serial:Q.offers.length+1,time:G.Game.st.time,level,options:list.map(c=>({key:c.key,type:c.type,title:c.title,desc:c.desc}))};Q.offers.push(offer);Q.offer=offer;return show.call(this,level,list,c=>{const before=Q.snapshot();cb(c);Q.ledger.push({time:G.Game.st.time,level,key:c.key,before,after:Q.snapshot()});Q.offer=null},...args)};
 const hurt=G.Enemy.prototype.hurt;
 G.Enemy.prototype.hurt=function(...args){const hp=this.hp,p=G.Game.player,b=M.stateFor(p)?.cast,result=hurt.apply(this,args);if(args[6]===p&&args[7]==='naruto-shikamaru-mass'&&this.hp<hp)Q.mainHits.push({time:G.Game.st.time,targetId:this.id,hpBefore:hp,hpAfter:this.hp,loss:hp-this.hp,raw:args[0],cast:M.stateFor(p)?.casts,castAge:b?.age,blastAt:b?.blastAt,center:b?{...b.center}:null});return result};
 const draw=G.Combat.drawAirFields;
 G.Combat.drawAirFields=function(ctx){const result=draw.call(this,ctx),p=G.Game.player,s=p&&M.stateFor(p),b=s?.cast;if(!b)return result;
  if(!Q.casts.some(c=>c.serial===s.casts))Q.casts.push({serial:s.casts,time:G.Game.st.time,level:p.level,center:{...b.center},origin:{...b.origin},profile:{...b.spec},releaseAt:b.releaseAt,duration:b.duration,blastAt:b.blastAt});
  if(b){const active=M.casts.includes(b),keys=[];if(b.age<b.arrive)keys.push('shadow-flight');if(b.age>=b.full&&b.age<b.throwAt)keys.push('full-circle');if(b.age>=b.throwAt+.15&&b.age<b.landAt)keys.push('bomb-flight');if(b.age>=b.blastAt+.1&&b.age<b.blastAt+.4)keys.push('blast');if(!active&&b.age>=b.duration&&Q.mainHits.some(h=>h.cast===s.casts)){keys.push('full-release');Q.completed=true;Q.completeCast={serial:s.casts,age:b.age,duration:b.duration,releaseAt:b.releaseAt,remainingBound:b.bound.size,active};}
   for(const key of keys)if(!seen.has(s.casts+'-'+key)){seen.add(s.casts+'-'+key);const state={key,serial:s.casts,snapshot:Q.snapshot(),castAge:b.age,center:{...b.center},radius:b.radius,bound:b.bound.size,bomb:b.bomb?{source:{...b.bomb.source},aim:b.bomb.aim}:null,exploded:b.exploded};queueMicrotask(()=>Q.frames.push({...state,png:ctx.canvas.toDataURL()}))}
  }
  return result;
 };
 function sample(){if(G.Game.state==='playing'){const s=Q.snapshot();if(s&&s.time-lastSample>=.25){lastSample=s.time;Q.samples.push(s)}}requestAnimationFrame(sample)}requestAnimationFrame(sample);
}'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    digest = lambda: hashlib.sha256((base.ROOT/SOURCE).read_bytes()).hexdigest()
    report = {'errors': [], 'sourceBefore': digest(),
              'policy': 'Fresh context/save, native HP/XP/AI/time, no permanent upgrades. Visible cards/items and keyboard D/S/A/W square only. Damage events count only main-player mass skill.'}
    data = None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            context = browser.new_context(viewport={'width':1100,'height':850}, service_workers='block', record_video_dir=str(OUT/'raw'), record_video_size={'width':1100,'height':850})
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append({'message':str(error),'stack':error.stack}))
            page.goto(base.URL)
            page.wait_for_function('window.PS_REDRAWN_READY&&window.G?.NarutoShikamaruMass&&document.getElementById("boot").classList.contains("hidden")')
            if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30017"]').click()
            report['permanent'] = page.evaluate('G.DB.upgradesOf(G.DB.save.partner)')
            assert not any(report['permanent'].values())
            page.evaluate(OBSERVE)
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.state==="playing"&&G.Game.player?.dex===30017')
            report['initial'] = page.evaluate('MassNatural.snapshot()')
            assert report['initial']['level'] == 1
            started = time.monotonic();held = None;last = -30;serial = None
            while time.monotonic()-started < 300:
                data = page.evaluate('({state:G.Game.state,snapshot:MassNatural.snapshot(),offer:MassNatural.offer,hits:MassNatural.mainHits.length,casts:MassNatural.casts.length,completed:MassNatural.completed})')
                snap = data['snapshot'];now = snap['time']
                if data['completed'] and data['hits'] > 0: break
                if snap['dead'] or data['state'] == 'over': break
                if now-last >= 30:
                    print('mass natural',round(now),'Lv',snap['level'],'HP',round(snap['hp']),'main hits',data['hits'],'casts',data['casts'],flush=True);last = now
                if data['state'] == 'levelup' and data['offer'] and data['offer']['serial'] != serial:
                    if held: page.keyboard.up(held);held = None
                    offer = data['offer']
                    def priority(card):
                        key = card['key']
                        if key == 'new:naruto-shikamaru-mass': return 0
                        if key == 'stat:quantity': return 1
                        if key == 'up:naruto-shikamaru': return 2
                        if key == 'new:naruto-shikamaru-sewing': return 3
                        if key == 'new:naruto-shikamaru-trap': return 4
                        if key == 'new:naruto-shikamaru-tactics': return 5
                        if key == 'new:naruto-shikamaru-checkmate': return 20
                        if card['type'] == 'up': return 6
                        return 9
                    selected = min(range(len(offer['options'])), key=lambda i: (priority(offer['options'][i]), i))
                    page.screenshot(path=str(OUT/f'card-{offer["serial"]}-Lv{offer["level"]}.png'))
                    page.locator('#cards .card').nth(selected).click();serial = offer['serial']
                elif page.locator('#scr-item').is_visible(): page.locator('#item-cards .card').first.click()
                elif page.locator('#scr-bond').is_visible(): page.locator('#bond-cards .card').first.click()
                elif data['state'] == 'paused': page.locator('#btn-resume').click()
                elif data['state'] == 'playing':
                    key = ['KeyD','KeyS','KeyA','KeyW'][int(now//1.5)%4]
                    if key != held:
                        if held: page.keyboard.up(held)
                        page.keyboard.down(key);held = key
                        page.evaluate('event=>MassNatural.inputs.push(event)', {'time':now,'key':key})
                page.wait_for_timeout(65)
            if held: page.keyboard.up(held)
            page.screenshot(path=str(OUT/'final.png'))
            report.update(page.evaluate('({ledger:MassNatural.ledger,offers:MassNatural.offers,inputs:MassNatural.inputs,mainHits:MassNatural.mainHits,casts:MassNatural.casts,samples:MassNatural.samples,completed:MassNatural.completed,completeCast:MassNatural.completeCast,final:MassNatural.snapshot(),state:G.Game.state})'))
            report['frames'] = []
            for frame in page.evaluate('MassNatural.frames'):
                png = frame.pop('png');name = 'cast-'+str(frame['serial'])+'-'+frame['key']+'.png'
                (OUT/name).write_bytes(base64.b64decode(png.split(',',1)[1]));report['frames'].append({'image':name,**frame})
            video = page.video;context.close();video.save_as(str(OUT/'native-growth.webm'));video.delete();browser.close()
        report['ok'] = (report['initial']['level'] == 1 and
                        any(c['key']=='new:naruto-shikamaru-mass' and c['level']>=6 for c in report['ledger']) and
                        len(report['mainHits'])>0 and report['completed'] and
                        report['completeCast']['remainingBound']==0 and not report['errors'])
        assert report['ok'], {'final':report['final'],'ledger':report['ledger'],'mainHits':len(report['mainHits']),'complete':report['completed']}
        print('Fresh Lv1 mass learn, main-player blast and full native release PASS',flush=True)
    except Exception as error:
        report['failure'] = str(error)
        raise
    finally:
        report['sourceAfter'] = digest();report['sourceStable'] = report['sourceBefore']==report['sourceAfter']
        (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')


if __name__ == '__main__':
    main()
