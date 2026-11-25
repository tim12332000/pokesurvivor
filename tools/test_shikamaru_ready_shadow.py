"""Persistent ready-shadow acceptance through the production game entry.

The mechanics arena and native scenes are controlled. Native captures use real
RAF and keyboard input; they do not stand in for natural growth or real phones.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from playwright.sync_api import sync_playwright
import test_shikamaru as base
import test_shikamaru_living_shadow as living

BASELINE = 'd25de4dd'
OUT = base.ROOT / '.omx/state/shikamaru-ready-shadow/qa'
RUNTIME = ['.omx/naruto-shikamaru.js', 'art-review/shikamaru/reference-shadow-geometry.js']
SOURCES = RUNTIME + ['.omx/digimon.html', '.omx/naruto-skills.js', '.omx/naruto.js']
base.URL = os.environ.get('SHIKAMARU_URL', 'http://127.0.0.1:8350/.omx/digimon.html?lang=zh-TW&layout=wide')


def manifest():
    return {name:hashlib.sha256((base.ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def routes(page, report):
    report['baselineRuntime'] = {}
    for name in RUNTIME:
        payload = subprocess.check_output(['git','show',BASELINE+':'+name],cwd=base.ROOT)
        report['baselineRuntime'][name] = hashlib.sha256(payload).hexdigest()
        def handler(data):
            return lambda route: route.fulfill(body=data,content_type='application/javascript')
        page.route('**/'+name+'*',handler(payload))


SETUP = r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry;
 A.readyBuild=()=>{const result=A.livingBuild(1);G.Spawner.update=()=>{};return result};
 A.readyPixels=(actor=p,fields=false)=>{const canvas=document.createElement('canvas');canvas.width=canvas.height=256;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.translate(128-actor.x,128-actor.y);const projection=S.projectionFor(actor);
  if(fields)G.Combat.drawGroundFields(ctx);else R.drawProjection(ctx,projection);
  const rgba=ctx.getImageData(0,0,256,256).data,mask=[];let count=0,left=256,top=256,right=-1,bottom=-1,hash=2166136261;
  for(let y=0;y<256;y++)for(let x=0;x<256;x++){const on=rgba[(y*256+x)*4+3]>127?1:0;mask.push(on);hash=Math.imul(hash^on,16777619)>>>0;if(on){count++;left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y)}}
  return {png:canvas.toDataURL(),mask,count,bounds:count?[left,top,right,bottom]:null,hash:hash.toString(16),kind:projection?.body.kind??projection?.kind,key:projection?.body.key,matrix:projection?.matrix,flow:projection?.flow??null,footInside:!!projection&&R.contains(projection,actor.x,actor.y)};
 };
 A.readyAssert=(actor=p)=>{const projection=S.projectionFor(actor);A.assert(projection?.body.kind==='ready-base'||projection?.kind==='ready-base','caster does not use the dedicated ready base');A.assert(projection.matrix.e===actor.x&&projection.matrix.f===actor.y,'ready base detached from foot anchor');A.assert(R.contains(projection,actor.x,actor.y),'caster foot is outside its ready base alpha');return projection};
 A.readySnapshot=()=>JSON.stringify({state:S.stateFor(p)?{clock:S.stateFor(p).clock,material:S.stateFor(p).material}:null,hp:p.hp,x:p.x,y:p.y,damage:p.dmgDealt,casts:S.casts.map(b=>({age:b.age,serial:b.serial,hits:b.hits})),leases:[...S.leases].map(([e,l])=>({id:e.id,until:l.until}))});
 A.readyTick=(dt=.01)=>{A.resume();try{G.Combat.tick(dt,p,0);G.Combat.updateFields(dt);p.anim.update(dt)}finally{A.pause()}};
}'''


CHECK = r'''baseline => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,R=G.ShikamaruReferenceGeometry,out={idle:[],cleanup:[]};
 A.readyBuild();A.assert(!S.stateFor(p),'cold fixture already has a cast state');const before=A.readySnapshot();out.cold=A.readyPixels(p,true);
 for(let i=0;i<20;i++){A.readyPixels(p,true);S.projectionFor(p)}A.assert(before===A.readySnapshot()&&!S.stateFor(p),'cold ready drawing created or advanced combat state');
 if(!baseline){A.readyAssert();A.assert(out.cold.count>300,'cold frame has no visible persistent base');}
 A.readyTick();const damage=p.dmgDealt||0,hp=p.hp;
 for(let i=0;i<3;i++){A.livingAdvance(.25);out.idle.push(A.readyPixels());if(!baseline)A.readyAssert()}
 A.assert(p.hp===hp&&(p.dmgDealt||0)===damage&&!S.casts.length&&!G.EnemyMgr.all().length,'idle ready base triggered combat');
 if(!baseline){A.assert(new Set(out.idle.map(x=>x.hash)).size===3,'standing ready base does not flow');const bounds=out.idle[1].bounds;A.assert(bounds[0]<112&&bounds[2]>144&&bounds[1]<118&&bounds[3]>138,'ready base is not a broad footprint surrounding the feet');
  const prior=A.readyPixels(),physical=R.bodyFor(p).key;p.anim.loop('Walk');p.anim.dir=4;p.aim=Math.PI;const movedPose=A.readyPixels();A.assert(prior.key===movedPose.key&&prior.hash===movedPose.hash,'ready base changed into the avatar pose');A.assert(R.bodyFor(p).key!==physical&&!R.bodyFor(p).kind,'physical body mask was replaced by ready shadow');p.anim.loop('Idle');p.anim.dir=2;
 }
 const pause=A.readySnapshot(),paused=A.readyPixels();S.update(2);A.assert(pause===A.readySnapshot()&&paused.hash===A.readyPixels().hash,'paused ready material advanced');
 const enemy=A.spawn(150,30),enemyBody=R.bodyFor(enemy),enemyProjection=S.projectionFor(enemy);A.assert(enemyProjection.body===enemyBody&&!enemyProjection.body.kind,'enemy foot projection was replaced with a caster ready base');
 const hits=A.watch(enemy),b=A.livingCast();A.livingWait(()=>S.held(enemy));if(!baseline)A.readyAssert();A.livingAdvance(.7);out.actualHits=hits.length;A.assert(hits.some(h=>h.loss>0),'ready source did not produce native kunai damage');
 for(let i=0;i<400&&(S.casts.includes(b)||S.stateFor(p)?.shadowReturns?.length);i++){A.livingStep();if(!baseline)A.readyAssert()}
 A.assert(!S.casts.includes(b)&&!S.stateFor(p)?.shadowReturns?.length,'cast and retraction did not close');out.afterReturn=A.readyPixels();out.cooldown=S.stateFor(p)?.cooldowns['naruto-shikamaru']||0;
 if(!baseline)A.assert(out.afterReturn.count>300&&out.cooldown>0,'ready base disappeared during cooldown');
 enemy.hp=0;enemy.dead=true;for(let i=0;i<160;i++)A.readyTick();out.afterCooldown=A.readyPixels();if(!baseline){A.readyAssert();A.assert((S.stateFor(p)?.cooldowns['naruto-shikamaru']||0)<1e-8,'cooldown did not tick while ready')}
 for(const reason of ['clear','unlearn','world','epoch','death']){A.readyBuild();const e=A.spawn(140,20),h=A.watch(e);A.livingCast();A.livingWait(()=>S.held(e));const world=G.World,count=h.length;
  if(reason==='clear')S.clear(p);if(reason==='unlearn')p.moves=[];if(reason==='world')G.World={...world};if(reason==='epoch')G.CombatPulse.beginRun();if(reason==='death')p.dead=true;
  try{A.livingAdvance(.6);A.assert(!S.held(e)&&!S.casts.some(c=>c.owner===p)&&h.length===count,'old ready action survived '+reason);if(!baseline){if(reason==='death')A.assert(A.readyPixels(p,true).count===0,'dead caster retained the ready base');else{A.readyAssert();A.assert(A.readyPixels(p,true).count>300,'living identity lost base after '+reason)}}}finally{p.dead=false;G.World=world}out.cleanup.push(reason);
 }
 A.readyBuild();const clone=G.SelfClones.summon(p);A.assert(clone,'clone fixture unavailable');clone.x=95;clone.y=0;const first=baseline?S.projectionFor(clone):A.readyAssert(clone);S.clear(p);if(!baseline){A.readyAssert();A.readyAssert(clone);A.assert(first.body.key===S.projectionFor(clone).body.key,'parent clear changed clone base')}
 clone.dead=true;A.livingAdvance(.01);out.cloneIsolation=true;out.readOnly=true;out.pause=true;
 return out;
}'''


NATIVE = r'''scene => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,built=A.readyBuild();
 const Q=window.ReadyShadow={scene,frames:[],samples:[],seen:new Set(),first:null,held:false,done:false,last:-1,ledger:built.ledger};
 if(scene==='cycle'){const e=A.spawn(150,30);e.hp=e.maxHp=Math.max(20,S.profile(p,p.moves[0]).damage*1.65);Q.enemy=e;Q.hits=A.watch(e);p.target=e;}
 const original=G.Combat.drawAirFields;
 G.Combat.drawAirFields=function(ctx){const result=original.call(this,ctx),s=S.stateFor(p),projection=S.projectionFor(p),pixels=A.readyPixels(),b=Q.first??=S.casts.find(c=>c.owner===p&&c.kind==='shadow'&&c.chain),keys=[],clock=s?.clock??G.Game.st.time;
  const base={clock,owner:{x:p.x,y:p.y,dir:p.anim.dir},kind:projection?.body.kind??projection?.kind,bodyKey:projection?.body.key,matrix:projection?.matrix,flow:projection?.flow??null,footInside:projection?G.ShikamaruReferenceGeometry.contains(projection,p.x,p.y):false,footHash:pixels.hash,footBounds:pixels.bounds,basePixels:pixels.count,cooldown:s?.cooldowns['naruto-shikamaru']||0,activeCasts:S.casts.filter(c=>c.owner===p).length,enemies:G.EnemyMgr.all().filter(e=>!e.dead).length};
  if(scene==='idle'){if(clock>.12&&!Q.seen.has('idle-1'))keys.push('idle-1');if(clock>.45&&!Q.seen.has('idle-2'))keys.push('idle-2');if(clock>.8&&!Q.seen.has('idle-3'))keys.push('idle-3');if(Math.hypot(p.x,p.y)>30)keys.push('moving');}
  else if(b){if(b.age<b.spec.release)keys.push('source');if(b.chain.segments.some(g=>!g.contact&&g.travelled/g.totalLength>.2&&g.travelled/g.totalLength<.8))keys.push('extend');if(Q.enemy&&S.held(Q.enemy)){Q.held=true;keys.push('held')}if(s?.shadowReturns?.length)keys.push('retract');if(Q.held&&!S.casts.includes(b)&&!s?.shadowReturns?.length){Q.done=true;keys.push('after-return');if(base.cooldown<=1e-8)keys.push('cooldown-ready')}}
  if(clock-Q.last>.08){Q.last=clock;Q.samples.push(base)}
  for(const key of keys)if(!Q.seen.has(key)){Q.seen.add(key);queueMicrotask(()=>Q.frames.push({...base,key,footPng:pixels.png,png:ctx.canvas.toDataURL()}))}
  return result;
 };A.resume();
}'''


def observe(page, report):
    page.on('pageerror',lambda e:report['errors'].append({'message':str(e),'stack':e.stack}))
    page.on('requestfailed',lambda r:report['failedRequests'].append({'url':r.url,'failure':r.failure}))


def boot(page, baseline, report, mobile=False):
    if baseline: routes(page,report)
    saved=base.URL
    if mobile: base.URL=saved.replace('&layout=wide','')
    try: base.boot(page)
    finally: base.URL=saved
    page.evaluate(living.SETUP);page.evaluate(SETUP)
    page.evaluate('window.ReadyWarm=Acceptance.spawn(1000,1000)')
    page.wait_for_function('!!G.ShikamaruReferenceGeometry.bodyFor(ReadyWarm)')


def png(path, data):
    path.write_bytes(base64.b64decode(data.split(',',1)[1]))


def save_pixels(folder, record):
    for name in ['cold','afterReturn','afterCooldown']:
        value=record[name];png(folder/(name+'.png'),value.pop('png'));value.pop('mask',None)
    for i,value in enumerate(record['idle'],1):
        png(folder/f'idle-{i}.png',value.pop('png'));value.pop('mask',None)


def native(browser, report, baseline, folder):
    for label,width,height in [('desktop',1100,850),('mobile390',390,844)]:
        for scene in ['idle','cycle']:
            target=folder/label/scene;target.mkdir(parents=True,exist_ok=True)
            context=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<600,has_touch=width<600,service_workers='block',record_video_dir=str(target/'raw'),record_video_size={'width':width,'height':height})
            context.set_default_timeout(60000);page=context.new_page();observe(page,report);boot(page,baseline,report,width<600);page.evaluate(NATIVE,scene)
            required=['idle-1','idle-2','idle-3','moving'] if scene=='idle' else ['source','extend','held','retract','after-return','cooldown-ready']
            started=time.monotonic();held=False
            while time.monotonic()-started<14:
                state=page.evaluate('({seen:[...ReadyShadow.seen],clock:G.NarutoShikamaru.stateFor(G.Game.player)?.clock||0})')
                if all(key in state['seen'] for key in required): break
                if scene=='idle' and state['clock']>1.1 and not held: page.keyboard.down('KeyD');held=True
                page.wait_for_timeout(70)
            if held: page.keyboard.up('KeyD')
            page.evaluate('Acceptance.pause()')
            data=page.evaluate('({frames:ReadyShadow.frames,samples:ReadyShadow.samples,seen:[...ReadyShadow.seen],hits:ReadyShadow.hits,ledger:ReadyShadow.ledger})')
            missing=[key for key in required if key not in data['seen']]
            assert not missing, {'viewport':label,'scene':scene,'missing':missing,'seen':data['seen']}
            if not baseline:
                assert all(s['kind']=='ready-base' and s['basePixels']>300 and s['footInside'] and s['matrix']['e']==s['owner']['x'] and s['matrix']['f']==s['owner']['y'] for s in data['samples']), f'{label}/{scene}: base disappeared or detached'
                if scene=='idle':
                    frames=[next(f for f in data['frames'] if f['key']==key) for key in ['idle-1','idle-2','idle-3']]
                    assert len({(f['owner']['x'],f['owner']['y']) for f in frames})==1
                    assert len({f['bodyKey'] for f in frames})==1 and len({f['footHash'] for f in frames})>1, 'idle ready base did not flow independently of pose'
                else:
                    assert data['hits'] and any(h['loss']>0 for h in data['hits']), 'ready base did not launch a real damaging attack'
                    assert next(f for f in data['frames'] if f['key']=='after-return')['enemies']==0, 'cycle fixture did not close on actual enemy defeat'
            for frame in data['frames']:
                png(target/(frame['key']+'.png'),frame.pop('png'));png(target/(frame['key']+'-foot.png'),frame.pop('footPng'))
            report.setdefault('native',{}).setdefault(label,{})[scene]=data
            video=page.video;context.close();video.save_as(str(target/'native-cycle.webm'));video.delete();print(label,scene,'native ready-base PASS',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',action='store_true');parser.add_argument('--checks-only',action='store_true');parser.add_argument('--capture-only',action='store_true');args=parser.parse_args()
    folder=OUT/('baseline' if args.baseline else 'current');folder.mkdir(parents=True,exist_ok=True)
    report={'baseline':args.baseline,'controlled':True,'url':base.URL,'sourceBefore':manifest(),'policy':'Normal entry then fixed-seed controlled arenas; native RAF/keyboard. No claim of natural growth or physical phones.','errors':[],'failedRequests':[]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
            if not args.capture_only:
                page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block');page.set_default_timeout(60000);observe(page,report);boot(page,args.baseline,report)
                report['checks']=page.evaluate(CHECK,args.baseline);save_pixels(folder,report['checks']);page.close();print('Cold fallback, persistence, physical mask, flow and lifecycle PASS',flush=True)
            if not args.checks_only: native(browser,report,args.baseline,folder)
            browser.close()
        assert not report['errors'] and not report['failedRequests'],{'errors':report['errors'],'failedRequests':report['failedRequests']};report['ok']=True
    except Exception as error:
        report['failure']=str(error);raise
    finally:
        report['sourceAfter']=manifest();report['sourceStable']=report['sourceBefore']==report['sourceAfter'];(folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')


if __name__=='__main__': main()
