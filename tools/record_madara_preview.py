"""Record a labeled, controlled build using the real game loop and input, not replayed images."""
import base64
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_madara_rework as acceptance

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art-review/madara/rework-showcase'
PUBLIC = ROOT / 'assets/previews'

SETUP = r"""() => {
 const A=JAcceptance,p=A.p();A.reset();p.level=30;p.moves=[];p.slots=[];p.bind={};p.statsTaken={};
 A.assert(p.addMove('naruto-madara'),'starter');const costs=[];
 const ids=G.NarutoMadara.kit[1].map(row=>row[0]);
 const choose=key=>{const card=G.LevelUp.offer(p,1000).find(c=>c.key===key);A.assert(card&&card.apply(p)!==false,'card '+key);costs.push({key,description:card.desc});};
 for(const id of ids.slice(1))choose('new:'+id);
 for(const id of ids)for(let rank=1;rank<3;rank++)choose('up:'+id);
 for(let i=0;i<3;i++)choose('stat:quantity');
 A.assert(costs.length===17&&p.moves.every(m=>m.lvl===3),'build cost');
 p.xpNext=1e12;G.Spawner.update=()=>{};
 for(const [x,y]of [[65,0],[110,40],[150,-35],[220,80],[290,-70],[-90,40],[-170,-80],[80,-130]]){const e=A.spawn(x,y);e.spd=8;e.dmg=0;}
 for(const m of p.moves)m.t=0;
 const canvas=document.getElementById('game'),stream=canvas.captureStream(30),audio=G.Audio.debugStream(true);
 if(audio)for(const track of audio.getAudioTracks())stream.addTrack(track);
 const chunks=[],type=MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus')?'video/webm;codecs=vp8,opus':'video/webm';
 const recorder=new MediaRecorder(stream,{mimeType:type,videoBitsPerSecond:1800000,audioBitsPerSecond:96000});
 recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
 const done=new Promise(resolve=>recorder.onstop=()=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}))});
 window.MadaraPreview={recorder,stream,done,costs,started:G.Game.st.time,startPosition:{x:p.x,y:p.y},audioTracks:stream.getAudioTracks().length};
 recorder.start();A.resume();return {cards:costs.length,moves:p.moves.map(m=>({id:m.id,rank:m.lvl})),quantity:p.quantityPicks,audioTracks:MadaraPreview.audioTracks};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    acceptance.OUT = OUT
    acceptance.URL = os.environ.get('MADARA_PREVIEW_URL', acceptance.URL)
    report = {'url':acceptance.URL,'scope':'controlled level30, five rank3 skills and three quantity cards, 17 actual card applications; moving high-HP targets; native RAF and real input; not natural progression',
              'views':{},'errors':[]}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=acceptance.base.CHROME, headless=True)
        for label, width, height, mobile in [('desktop',1100,850,False),('mobile390',390,844,True)]:
            context = browser.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile,service_workers='block')
            page = context.new_page()
            page.on('pageerror',lambda error:report['errors'].append(str(error)))
            frame = acceptance.boot(page,label)
            build = frame.evaluate(SETUP)
            for index, at in enumerate([3,7,11,17,23,30]):
                frame.wait_for_function('t=>G.Game.st.time-MadaraPreview.started>=t',arg=at,timeout=30000)
                if mobile:
                    client=context.new_cdp_session(page)
                    point=frame.evaluate('G.Touch.stickBase()')
                    client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]})
                    client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':point['x']+(25 if index%2==0 else -25),'y':point['y']}]})
                    page.wait_for_timeout(120)
                    client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                    client.detach()
                else:
                    key='KeyD'if index%2==0 else'KeyA'
                    page.keyboard.down(key);page.wait_for_timeout(120);page.keyboard.up(key)
                if at==11:
                    frame.locator('#game').screenshot(path=str(PUBLIC/f'madara-rework-{label}.png'))
            data=frame.evaluate(r"""async()=>{
             const p=G.Game.player,record=MadaraPreview;JAcceptance.pause();record.recorder.stop();
             const video=await record.done;for(const track of record.stream.getTracks())track.stop();
             const stats=G.NarutoMadara.stats(p);JAcceptance.assert(stats.perfectCount>0,'no earned Perfect window');
             JAcceptance.assert(['naruto-madara','naruto-madara-fire','naruto-madara-susanoo','naruto-madara-meteor','naruto-madara-clones'].every(id=>stats.casts[id]>0),'missing native skill');
             return {video,costs:record.costs,gameSeconds:G.Game.st.time-record.started,stats,position:{x:p.x,y:p.y}};
            }""")
            filename=f'madara-rework-{label}.webm'
            (PUBLIC/filename).write_bytes(base64.b64decode(data.pop('video').split(';base64,',1)[1]))
            report['views'][label]={'build':build,**data,'video':filename,'bytes':(PUBLIC/filename).stat().st_size}
            context.close()
        browser.close()
    report['ok']=not report['errors']
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'errors':report['errors'],'videos':{key:value['bytes']for key,value in report['views'].items()}}))
    if not report['ok']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
