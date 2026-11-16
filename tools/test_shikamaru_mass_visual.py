"""Record the mass shadow's normal-entry RAF animation; fixtures are explicitly controlled."""
import base64
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_shikamaru as base

OUT=base.ROOT/'art-review/shikamaru/qa/mass/self-native'
SETUP=r'''() => {
 const A=Acceptance,p=A.p(),M=G.NarutoShikamaruMass;
 A.massScene=()=>{A.reset();p.statsTaken={};p.level=6;p.moves=[G.Moves.instance('naruto-shikamaru')];const card=G.LevelUp.offer(p,1000).find(c=>c.key==='new:naruto-shikamaru-mass');A.assert(card&&card.apply(p)!==false,'Lv6 actual mass card unavailable');
 const es=Array.from({length:18},(_,i)=>A.spawn(Math.cos(i*2.4)*(55+i*7),Math.sin(i*2.4)*(55+i*7),i===0));p.target=es[0];return es};
 window.MassFrames=[];window.MassSeen=new Set();window.MassTimeline=[];let last=-1;
 const draw=G.Combat.drawAirFields;G.Combat.drawAirFields=function(ctx){const result=draw.call(this,ctx),b=M.stateFor(p)?.cast;if(!b)return result;
 const key=b.age<b.spec.prepare?'seal':b.age<b.full?'stabbing':b.age<b.throwAt?'bind':b.age<b.landAt?'bomb-flight':b.age<b.blastAt?'fuse':b.age<b.blastAt+.12?'blast':b.age<b.blastAt+.4?'blast-middle':b.age<b.releaseAt?'hold-after-blast':'release';
 const sample=()=>({key,age:b.age,radius:b.radius,rays:[...b.rays.values()].map(r=>({targetId:r.target.id,source:{...r.source},tip:{...r.current},hit:r.hit,contact:r.contact,boundAt:r.boundAt})),bound:b.bound.size,center:{...b.center},origin:{...b.origin},bomb:b.bomb?JSON.parse(JSON.stringify(b.bomb)):null,exploded:b.exploded,contacts:M.stateFor(p).contacts.slice(),pose:G.NarutoShikamaru.activeFor(p)});
 if(b.age-last>.08){MassTimeline.push(sample());last=b.age;}
 const delayed=(key==='stabbing'&&b.age<b.spec.prepare+.1)||(key==='bomb-flight'&&b.age<b.throwAt+.2)||(key==='release'&&b.age<b.releaseAt+.15);
 if(!delayed&&!MassSeen.has(key)){MassSeen.add(key);const state=sample();queueMicrotask(()=>MassFrames.push({...state,png:ctx.canvas.toDataURL()}))}return result;};
}'''

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'configuration':'Actual Lv6 new-skill card; native RAF auto-casts. Controlled 18 native enemies, open geometry and fixed stats; not natural growth.','errors':[],'viewports':{},'sha256':hashlib.sha256((base.ROOT/'.omx/naruto-shikamaru-mass.js').read_bytes()).hexdigest()}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        for label,width,height in [('desktop',1100,850),('mobile360',360,780),('mobile390',390,844)]:
            folder=OUT/label;folder.mkdir(parents=True,exist_ok=True)
            context=browser.new_context(viewport={'width':width,'height':height},is_mobile=width<600,has_touch=width<600,service_workers='block',record_video_dir=str(folder/'video'))
            page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
            saved=base.URL
            if width<600:base.URL=saved.replace('&layout=wide','')
            try:base.boot(page)
            finally:base.URL=saved
            page.evaluate(SETUP);page.evaluate('Acceptance.massScene();Acceptance.resume()')
            page.wait_for_function('MassSeen.has("release")',timeout=20000)
            page.evaluate('Acceptance.pause()');data=page.evaluate('({frames:MassFrames,timeline:MassTimeline,stats:{casts:G.NarutoShikamaruMass.stateFor(Acceptance.p()).casts,hits:G.NarutoShikamaruMass.stateFor(Acceptance.p()).hits}})')
            for frame in data['frames']:
                png=frame.pop('png');name=frame['key']+'.png';(folder/name).write_bytes(base64.b64decode(png.split(',',1)[1]));frame['image']=name
            report['viewports'][label]=data
            video=page.video;context.close();video.save_as(str(folder/'native-cycle.webm'));video.delete()
            print(label,'mass full native cycle PASS',flush=True)
        browser.close()
    assert not report['errors'],report['errors']
    report['ok']=True;(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':main()
