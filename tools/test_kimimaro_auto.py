"""Native-game regression for learned, slotless Kimimaro support techniques."""
from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_kimimaro as native

OUT = native.ROOT / '.omx/state/kimimaro-auto'

HELPERS = r"""() => {
 const A=KAcceptance,p=A.p(),K=A.K,id=key=>key==='willow'?'naruto-kimimaro':'naruto-kimimaro-'+key;
 function prepare(keys,selected=null,rank=1){
   A.reset();p.level=30;p.moves=[];p.slots=[];p.bind={};p.active=0;p.maxMoves=4;
   for(const key of keys){A.assert(p.addMove(id(key)),'learn '+key);const m=p.moves.find(m=>m.id===id(key));Object.assign(m,G.Moves.instance(m.id,rank));m.t=999;}
   p.arrange();if(selected)p.setActive(p.slots.findIndex(g=>g.some(m=>m.id===id(selected))));
   A.advance(.11);return p.moves;
 }
 const move=key=>p.moves.find(m=>m.id===id(key));
 function begin(key,distance,selected='camellia',rank=1){
   prepare([key,selected],selected,rank);move(key).t=0;move(selected).t=999;
   const e=A.spawn(distance,0),hits=A.watch(e);p.target=e;p.aim=0;A.step(.001,true);
   A.assert(A.action()?.baseKind===key||A.action()?.kind===key,'auto '+key+' did not start');return {e,hits,m:move(key)};
 }
 window.KAuto={...A,p,K,id,prepare,move,begin};
}"""

PROGRESSION = r"""() => {
 const A=KAuto,p=A.p,out={gates:[],flags:[],ranks:[]};
 A.assert(p.level===1&&p.moves.length===1&&p.moves[0].id===A.id('willow')&&!p.slots.length,'native fresh starter must only learn Willow');
 const gates={camellia:3,bullets:3,boomerang:2,larch:6,vine:6,'bone-guard':6,flower:9,lily:9,bracken:12,curse:15};
 for(const level of [1,2,3,5,6,8,9,11,12,14,15]){
   p.level=level;const pool=G.Moves.poolFor(p.mon),cards=G.LevelUp.offer(p,100);
   for(const [key,gate] of Object.entries(gates)){
     A.assert(pool.includes(A.id(key))===(level>=gate),'pool gate '+key+' '+level);
     A.assert(cards.some(c=>c.key==='new:'+A.id(key))===(level>=gate),'learn card gate '+key+' '+level);
   }out.gates.push({level,pool});
 }
 for(const key of ['willow',...Object.keys(gates)]){
   const passive=true,def=G.Moves.instance(A.id(key));
   A.assert(!!def.passive===passive,'passive flag '+key);out.flags.push({key,passive});
 }
 const stats={willow:[30,.9],camellia:[120,5],bullets:[45,2.4],boomerang:[64,1],larch:[96,6],vine:[48,8],flower:[192,8],lily:[100,6],bracken:[600,17]};
 for(const [key,[damage,cd]] of Object.entries(stats))for(let rank=1;rank<=5;rank++){
   const m=G.Moves.instance(A.id(key),rank);A.near(m.dmg,damage*[1,1.2,1.4,1.7,2][rank-1],'rank damage '+key);A.near(m.cd,cd,'fixed cooldown '+key);out.ranks.push({key,rank,dmg:m.dmg,cd:m.cd});
 }
 // Rebuild exactly the pre-conversion screenshot save: four formerly active skills.
 A.prepare(['willow','bullets','larch','vine','lily'],'lily');p.level=12;p.maxMoves=4;
 const passive=p.moves.filter(m=>['bullets','larch','vine','lily'].some(k=>m.id===A.id(k)));
 passive.forEach((m,i)=>{m.passive=false;m.lvl=2;m.t=2+i});const before=passive.map(m=>({m,lvl:m.lvl,t:m.t}));p.slots=passive.map(m=>[m]);p.active=3;
 p.bind=Object.fromEntries(p.slots.flatMap((g,i)=>g.map(m=>[m.id,i])));
 const cards=G.LevelUp.offer(p,3);p.arrange();
 A.assert(p.slots.length===0&&p.activeGroup().length===0,'migration retained an active Kimimaro group');
 A.assert(before.every(v=>p.moves.includes(v.m)&&v.m.lvl===v.lvl&&v.m.t===v.t),'migration reset move identity/rank/cooldown');
 A.assert(passive.every(m=>m.passive&&!Object.hasOwn(p.bind,m.id)),'passive binding retained');
 A.assert(p.moves.length===5&&new Set(p.moves.map(m=>m.id)).size===5,'migration duplicated learned techniques');
 const index=cards.findIndex(c=>c.key==='new:'+A.id('bracken'));
 A.assert(cards.length===3&&index>=0,'Lv12 first native three-card offer omitted Bracken');
 window.KAutoOffer={cards,index};G.RunUI.showLevelUp(12,cards,card=>{A.assert(card.apply(p)!==false,'native card apply failed')});
 out.offer=cards.map(c=>c.key);out.index=index;out.migratedSlots=p.slots.map(g=>g.map(m=>m.id));return out;
}"""

PICK = r"""() => {const A=KAuto,p=A.p;
 A.assert(p.hasMove(A.id('bracken'))&&p.slots.length===0,'native pick did not learn slotless Bracken without fusion');
 A.assert(p.moves.length===6,'native pick learned unrelated skill');return {moves:p.moves.map(m=>m.id),slots:p.slots.map(g=>g.map(m=>m.id))};}"""

AUTO = r"""() => {
 const A=KAuto,p=A.p,out={};
 for(const key of ['bullets','larch','vine'])for(const rank of [1,5]){
   const distance={bullets:190,larch:55,vine:155}[key],f=A.begin(key,distance,'camellia',rank);
   A.assert(!p.activeGroup().includes(f.m)&&f.m.t>0,'auto consumed selection or missed own cooldown '+key);
   A.advance(key==='vine'?.55:1.4);const expected=key==='bullets'?5*A.expected(f.m,.2,f.e):key==='larch'?2*A.expected(f.m,.5,f.e):A.expected(f.m,1,f.e);
   A.assert(f.e.maxHp-f.e.hp===expected,'auto native HP loss '+key+' '+rank+' '+JSON.stringify(f.hits));
   A.assert(f.hits.every(h=>h.owner&&h.id===f.m.id),'auto ownership '+key);
   if(key==='vine')A.assert(f.e.x<distance&&f.e.x>=p.r+f.e.r+7.9,'safe standalone auto pull');
   out[key+rank]={hpLoss:f.e.maxHp-f.e.hp,expected,cooldown:f.m.t,hits:f.hits,slots:p.slots.length,log:A.K.stateFor(p).castLog};
 }
 for(const q of [1,5]){
   // Snapshot quantity must be set before the actual cast.
   A.prepare(['bullets','camellia'],'camellia');p.quantityPicks=p.quantityBonus=q;A.move('bullets').t=0;
   const e=A.spawn(190,0),hits=A.watch(e);p.target=e;A.step(.001,true);A.advance(1.4);
   const count=Math.min(15,Math.floor(5*1.25**q));A.assert(hits.length===count,'auto quantity '+q);
   A.assert(e.maxHp-e.hp===count*A.expected(A.move('bullets'),.2,e),'quantity damage duplicated');out['quantity'+q]={count,hpLoss:e.maxHp-e.hp};
 }
 const guard=A.begin('larch',55);A.assert(p.addMove(A.id('willow')),'Larch fixture retains starter Willow');A.move('willow').t=999;A.advance(.3);const before=p.hp;p.invuln=0;
 A.resume();try{p.hurt(20,null,false)}finally{A.pause()}
 const expectedGuard=20*(1-p.reduction)*.75*.8;A.near(before-p.hp,expectedGuard,'unselected learned Larch guard');out.guard={loss:before-p.hp,expected:expectedGuard};
 A.prepare(['willow','camellia'],'camellia');A.move('willow').t=0;const close=A.spawn(50,0),hits=A.watch(close);p.target=close;A.advance(.7,true);
 A.assert(hits.length===4,'automatic Willow stopped near selected cooldown skill');out.willow=hits;
 return out;
}"""

COMBO = r"""() => {
 const A=KAuto,p=A.p;A.prepare(['vine','flower'],'flower');const vine=A.move('vine'),flower=A.move('flower');vine.t=flower.t=0;
 const e=A.spawn(155,0),hits=A.watch(e);p.target=e;A.step(.001,true);
 A.assert(A.action()?.kind==='combo'&&!p.slots.length,'passive Vine plus learned Flower did not link');
 A.advance(.53);A.assert(!A.K.stateFor(p).castCounts.flower&&flower.t===0,'Flower cooldown charged early');
 A.advance(.02);A.assert(A.K.stateFor(p).castCounts.flower===1,'Flower did not start at .54');A.assert(Math.abs(flower.t-8)<.011,'independent Flower cooldown');
 A.advance(.9);A.assert(hits.length===2&&e.maxHp-e.hp===A.expected(vine,1,e)+A.expected(flower,1,e),'combo duplicated damage');
 const log=A.K.stateFor(p).castLog;A.assert(Math.abs(log[1].time-log[0].time-.54)<1e-7,'combo start timing');
 A.prepare(['camellia','flower','lily','bracken']);for(const m of p.moves)m.t=0;p.target=A.spawn(55,0);A.advance(6,true);
 const counts=A.K.stateFor(p).castCounts;A.assert(['camellia','flower','lily','bracken'].every(k=>counts[k]>=1),'learned technique did not cast without selection '+JSON.stringify(counts));
 A.prepare(['willow','bullets','larch','vine','camellia'],'camellia');for(const m of p.moves)m.t=0;p.target=A.spawn(55,0);A.advance(3,true);
 const fair=A.K.stateFor(p).castLog;A.assert(fair.some(c=>c.kind==='camellia')&&fair.some(c=>c.kind==='larch')&&fair.some(c=>c.kind==='willow'),'body scheduler starved ready technique');
 for(let i=1;i<fair.length;i++)A.assert(fair[i].time-fair[i-1].time>=.59,'overlapping independent body actions');
 return {comboLog:log,hits,selectedCounts:counts,fairLog:fair};
}"""

# The real starter always learns Willow. Keep that defensive baseline while
# reusing native clone ownership, cooldown, guard and curse regression checks.
CLONES = native.CLONES.replace(
    "const enemy=A.spawn(clone.x+32,clone.y)",
    "A.assert(!clone.slots.some(g=>g.some(m=>m.passive)),'clone copied passive into active slots');const enemy=A.spawn(clone.x+32,clone.y)",
    1,
)


def hud_controls(page, frame, label, mobile):
    frame.evaluate(r"""() => {
      const A=KAuto,p=A.p;A.prepare(['willow','bullets','larch','vine','curse','camellia','flower','lily','bracken','bone-guard','boomerang']);
      A.assert(p.slots.length===0&&p.moves.filter(m=>m.passive).length===11,'fully learned slot counts');
      p.frozen=true;window.KHUDButtons=[];window.KHUDOriginal={add:G.Touch.addButton,clear:G.Touch.clearButtons};
      G.Touch.clearButtons=function(...args){KHUDButtons=[];return KHUDOriginal.clear.apply(this,args)};
      G.Touch.addButton=function(x,y,w,h,cb,...args){KHUDButtons.push({x,y,w,h});return KHUDOriginal.add.call(this,x,y,w,h,cb,...args)};
      A.resume();
    }""")
    page.wait_for_timeout(150)
    geometry = frame.evaluate(r"""() => {
      const A=KAuto;let all;
      if(G.Touch.active)all=G.Touch.controlLayout(innerWidth,innerHeight,11).slots;
      else{const size=54,gap=9,start=(innerWidth-(11*size+10*gap))/2;all=Array.from({length:11},(_,i)=>({x:start+i*(size+gap),y:innerHeight-size-18,w:size,h:size}));}
      A.assert(all.length===11&&all.every(b=>b.x>=0&&b.x+b.w<=innerWidth&&b.y>=0&&b.y+b.h<=innerHeight),'standard eleven-skill row overflow');
      A.assert(!KHUDButtons.some(b=>b.w===24&&b.h===24),'unexpected custom automatic badge panel');
      return {passive:all,slots:[],all,active:G.Game.player.active,touch:G.Touch.active};
    }""")
    offset = {'x': 0, 'y': 0}
    if frame != page.main_frame:
        box = page.locator('iframe').first.bounding_box()
        offset = {'x': box['x'], 'y': box['y']}
    click = page.touchscreen.tap if mobile else page.mouse.click
    before = frame.evaluate('G.Game.player.active')
    for slot in geometry['passive']:
        click(slot['x'] + slot['w']/2 + offset['x'], slot['y'] + slot['h']/2 + offset['y'])
        assert frame.evaluate('G.Game.player.active') == before, 'passive badge changed selected active'
    # Several learned-skill achievements can queue 2.8-second native toasts.
    frame.locator('#ach-pop').wait_for(state='hidden', timeout=20000)
    page.screenshot(path=str(OUT / f'{label}-all-eleven-skills-hud.png'))
    frame.evaluate('G.Touch.addButton=KHUDOriginal.add;G.Touch.clearButtons=KHUDOriginal.clear;KAuto.p.frozen=false;KAuto.pause()')
    return {'activeCount': 0, 'passiveCount': 11, 'clickedAllPassiveSkills': True, 'passiveKeptSelection': True, 'geometry': geometry}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    native.OUT = OUT
    report = {'sourceHashes': native.runtime_hashes(), 'viewports': {}, 'errors': [], 'failedRequests': [], 'failures': []}
    selected = set(os.environ.get('KIMIMARO_AUTO_CHECKS', '').split(',')) - {''}
    checks = [('progression', PROGRESSION), ('auto', AUTO), ('combo', COMBO),
              ('lifecycle', native.LIFECYCLE), ('curse', native.CURSE),
              ('clones', CLONES), ('restart', native.RESTART), ('terminal', native.TERMINAL)]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
        for label, viewport, mobile in [('desktop', {'width': 1280, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(e.stack or str(e)))
            page.on('response', lambda r: report['failedRequests'].append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
            result = report['viewports'][label] = {}
            try:
                frame = native.boot(page, label)
                frame.evaluate(HELPERS)
                for name, check in checks:
                    if selected and name not in selected:
                        continue
                    print(label, name, flush=True)
                    try:
                        result[name] = frame.evaluate(check)
                        if name == 'progression':
                            frame.locator('#scr-levelup').wait_for(state='visible')
                            # Let the native modal transition finish before recording it.
                            page.wait_for_timeout(300)
                            frame.locator('#ach-pop').wait_for(state='hidden', timeout=20000)
                            page.screenshot(path=str(OUT / f'{label}-lv12-bracken-offer.png'))
                            frame.locator('#cards .card').nth(result[name]['index']).click()
                            result['nativePick'] = frame.evaluate(PICK)
                    except Exception as error:
                        report['failures'].append(f'{label}:{name}: {error}')
                    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
                if not selected or 'hud' in selected:
                    try:
                        frame.evaluate(HELPERS)
                        result['hud'] = hud_controls(page, frame, label, mobile)
                    except Exception as error:
                        report['failures'].append(f'{label}:hud: {error}')
                assert not frame.evaluate('document.documentElement.scrollWidth>innerWidth'), 'horizontal overflow'
            except Exception as error:
                report['failures'].append(f'{label}:boot: {error}')
            finally:
                context.close()
        browser.close()
    report['sourceHashesAfter'] = native.runtime_hashes()
    if report['sourceHashesAfter'] != report['sourceHashes']:
        report['failures'].append('Runtime sources changed during verification; rerun frozen sources')
    report['ok'] = not any(report[k] for k in ['errors', 'failedRequests', 'failures'])
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'ok': report['ok'], 'failures': report['failures'], 'evidence': str(OUT)}, ensure_ascii=True))
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
