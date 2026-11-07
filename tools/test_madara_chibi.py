"""Scoped Madara body-art QA through the production entry and renderer.

The contact sheets are deterministic render probes, not gameplay evidence.
Normal-entry screenshots and native keyboard/touch movement are recorded separately.
"""
import argparse
import base64
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright
import test_madara_rework as acceptance

ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass


class Server(ThreadingHTTPServer):
    request_queue_size = 128


SHEETS = r"""() => {
 const art=G.MadaraArt,root=art.metadata,keys=['common','taijutsu','bodyDirections','castingDirections','walkDirections'];
 const result={};
 for(const key of keys){
  const sheet=key==='common'?root:root.sheets[key];
  JAcceptance.assert(sheet&&art.images[key],'missing body sheet '+key);
  const columns=4,cellW=160,cellH=132,rows=Math.ceil(sheet.frames.length/columns);
  const canvas=document.createElement('canvas');canvas.width=columns*cellW;canvas.height=rows*cellH;
  const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.imageSmoothingEnabled=false;
  ctx.fillStyle='#49713f';ctx.fillRect(0,0,canvas.width,canvas.height);
  const records=[];
  for(let index=0;index<sheet.frames.length;index++){
   const f=sheet.frames[index],x=(index%columns)*cellW+80,y=Math.floor(index/columns)*cellH+92;
   const [sx,sy,w,h]=f.rect,k=64/sheet.bodyHeight;
   const a=f.anchor;
   ctx.drawImage(art.images[key],sx,sy,w,h,x-a[0]*k,y-a[1]*k,w*k,h*k);
   ctx.fillStyle='#fff';ctx.font='11px monospace';ctx.fillText(index+': '+f.name,(index%columns)*cellW+4,y+20);
   ctx.fillStyle='#101d12';ctx.fillRect((index%columns)*cellW,y+29,cellW-2,1);
   records.push({index,name:f.name,rect:f.rect,anchor:f.anchor,sockets:f.sockets,
    renderedWidth:w*k,renderedHeight:h*k});
  }
  const clean=canvas.toDataURL();
  for(let index=0;index<sheet.frames.length;index++){
   const f=sheet.frames[index],x=(index%columns)*cellW+80,y=Math.floor(index/columns)*cellH+92,k=64/sheet.bodyHeight;
   ctx.strokeStyle='#fff';ctx.beginPath();ctx.moveTo(x-4,y);ctx.lineTo(x+4,y);ctx.moveTo(x,y-4);ctx.lineTo(x,y+4);ctx.stroke();
   for(const [name,color] of Object.entries({mouth:'#ffcb00',palm:'#00ffff',elbow:'#ff55ff',foot:'#ff6540'})){
    const p=f.sockets?.[name];if(!p)continue;
    const px=x+(p[0]-f.anchor[0])*k,py=y+(p[1]-f.anchor[1])*k;
    ctx.fillStyle=color;ctx.beginPath();ctx.arc(px,py,2,0,Math.PI*2);ctx.fill();
   }
  }
  result[key]={source:sheet.source,sha256:sheet.sha256,bodyHeight:sheet.bodyHeight,frames:records,
   clean,overlay:canvas.toDataURL()};
 }
 return result;
}"""

REFERENCE = r"""async () => {
 await AnimationAssets.loadHero(30001);
 const c=document.createElement('canvas');c.width=640;c.height=290;
 const ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;
 ctx.fillStyle='#49713f';ctx.fillRect(0,0,c.width,c.height);
 ctx.fillStyle='#fff';ctx.font='13px monospace';
 ctx.fillText('Production renderers, 64px standing height',10,20);
 ctx.fillText('Naruto',10,112);ctx.fillText('Madara chibi',10,242);
 const directions=[['front',0,0],['side',2,12],['back',4,4]],details=[];
 for(let i=0;i<directions.length;i++){
  const [label,dir,index]=directions[i],x=220+i*150;
  AnimationAssets.draw(ctx,'naruto-idle',index,x,110,{scale:1});
  G.MadaraArt.draw(ctx,{}, {x,y:240,height:64,state:'idle',time:0,dir});
  ctx.fillStyle='#fff';ctx.fillText(label,x-20,270);
  const s=G.MadaraArt.sample('idle',0,dir),asset=AnimationAssets.get('naruto-idle');
  details.push({direction:label,naruto:{source:asset.source,bodyHeight:asset.bodyHeight,index,frame:asset.frames[index]},
   madara:{sheet:s.sheet,index:s.index,bodyHeight:s.bodyHeight,frame:s}});
 }
 return {png:c.toDataURL(),details,scope:'same 64px standing height, actual production asset draw functions, no post-render resizing'};
}"""


def save_png(path, data):
    path.write_bytes(base64.b64decode(data.split(';base64,', 1)[1]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', default='candidate')
    parser.add_argument('--url')
    parser.add_argument('--out', type=Path, default=ROOT / 'art-review/madara-chibi-20261107/qa')
    args = parser.parse_args()
    out = args.out / args.label
    out.mkdir(parents=True, exist_ok=True)
    server = None
    url = args.url
    if not url:
        server = Server(('127.0.0.1', 0), partial(Handler, directory=str(ROOT)))
        Thread(target=server.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW'
    acceptance.URL = url
    acceptance.OUT = out
    report = {'url': url, 'label': args.label, 'scope': 'body-art contact sheets at 64px; actual normal entry and input separately',
              'views': {}, 'errors': [], 'missing': [], 'failures': []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=acceptance.base.CHROME, headless=True)
            for label, width, height, mobile in [('desktop',1280,900,False),('mobile390',390,844,True),('mobile360',360,800,True)]:
                context = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=mobile,
                                              has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('response', lambda r: report['missing'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
                try:
                    frame = acceptance.boot(page, label)
                    result = report['views'][label] = {}
                    result['inputAndBody'] = acceptance.input_and_body(page, frame, context, mobile, label)
                    if label == 'desktop':
                        sheets = frame.evaluate(SHEETS)
                        for key, sheet in sheets.items():
                            save_png(out / f'{key}-64px.png', sheet.pop('clean'))
                            save_png(out / f'{key}-64px-sockets.png', sheet.pop('overlay'))
                        result['bodySheets'] = sheets
                        reference = frame.evaluate(REFERENCE)
                        save_png(out / 'naruto-madara-same-size.png', reference.pop('png'))
                        result['sameSizeReference'] = reference
                    page.screenshot(path=str(out / f'{label}-after-input.png'))
                except Exception as error:
                    report['failures'].append(f'{label}: {error}')
                    page.screenshot(path=str(out / f'{label}-failure.png'))
                finally:
                    context.close()
            browser.close()
    finally:
        if server:
            server.shutdown()
            server.server_close()
    report['ok'] = not (report['errors'] or report['missing'] or report['failures'])
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'ok':report['ok'],'evidence':str(out),'errors':report['errors'],'failures':report['failures']}))
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
