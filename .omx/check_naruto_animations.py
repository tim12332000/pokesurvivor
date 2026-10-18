"""Source-facing and action-frame regression, with a visual contact sheet."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
import json
import mimetypes
import os

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=naruto-animation-fix'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(locale='zh-TW',viewport={'width':1440,'height':1150},service_workers='block')
    if os.environ.get('PAGES_LIVE')!='1':
        def proxy(route):
            name=unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            file=ROOT/name
            if file.is_file():route.fulfill(status=200,body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            else:route.fulfill(status=404,body='Not found')
        context.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(URL);page.wait_for_function('window.G?.Naruto&&[...G.Naruto.records.values()].every(r=>r.ready)')
    report=page.evaluate('''() => {
      const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
      const right=G.Sprites.dirFromAngle(0),left=G.Sprites.dirFromAngle(Math.PI);
      const sourceRows={naruto:[165,199],sakura:[161,194],kakashi:[176,218],hinata:[509,543],lee:[407,441],gaara:[159,193]};
      const summaries=[];
      for(const r of G.Naruto.records.values()) {
        const R=G.Naruto.frameFor(r,'Walk',right,0),L=G.Naruto.frameFor(r,'Walk',left,0);
        assert(R.direction==='right'&&L.direction==='left','Engine directions '+r.slug);
        if(['sasuke','itachi'].includes(r.slug))assert(!R.mirror&&L.mirror,'Right-facing source mirrored incorrectly '+r.slug);
        // These source rows were visually audited: the former left group faces right.
        if(sourceRows[r.slug])assert(R.rect[1]===sourceRows[r.slug][0]&&L.rect[1]===sourceRows[r.slug][1],'Source rows reversed '+r.slug);
        const pl=new G.Player(G.DEX_BY[r.dex],{});pl.cast(G.Moves.instance(r.start));
        const actual=pl.anim.cur;
        assert(G.Naruto.frameFor(r,actual,right,0).action,'Signature uses idle fallback '+r.slug);
        const tested=[];
        for(const [anim,action] of Object.entries(r.pixel.animations)) {
          const m=G.Sprites.animMeta(r.dex,anim);
          assert(m.n>=3&&m.d.length===m.n,'Action timing '+r.slug+' '+anim);
          for(const frames of Object.values(action.frames))for(const [x,y,w,h] of frames)
            assert(w>0&&h>0&&x>=0&&y>=0&&x+w<=r.image.width&&y+h<=r.image.height,'Invalid source crop');
          const a=new G.Sprites.Animator(r.dex);a.dir=right;a.play(anim,{hold:anim==='Faint'});
          const first=G.Naruto.frameFor(r,anim,right,a.frame).rect.join();
          a.update(m.d[0]/60+.001);
          assert(a.frame===1,'Action did not advance '+r.slug+' '+anim);
          assert(G.Naruto.frameFor(r,anim,right,a.frame).rect.join()!==first,'Action repeats same artwork '+r.slug+' '+anim);
          a.update(2);
          assert(anim==='Faint'?a.done&&a.frame===m.n-1:a.cur==='Idle','Action completion '+r.slug+' '+anim);
          tested.push(anim);
        }
        summaries.push({slug:r.slug,signature:actual,actions:tested});
      }
      const panel=document.createElement('section');panel.id='animation-review';
      panel.style.cssText='position:fixed;inset:0;z-index:20000;background:#09172c;color:white;padding:16px;font:14px sans-serif;overflow:auto';
      panel.innerHTML='<h2 style="margin:0 0 10px">原圖動作檢查：右行／左行／攻擊／施術／受傷／倒下</h2>';
      const variants=[['右行 →','Walk',right,1],['← 左行','Walk',left,1],['攻擊 1','Attack',right,0],['攻擊 2','Attack',right,1],['攻擊末格','Attack',right,99],['施術','Shoot',right,1],['蓄力','Charge',right,1],['受傷','Hurt',right,1],['倒下','Faint',right,99]];
      for(const r of G.Naruto.records.values()) {
        const row=document.createElement('div');row.style.cssText='display:flex;align-items:center;border-top:1px solid #496486;padding:4px 0';
        const label=document.createElement('b');label.textContent=r.chinese;label.style.cssText='width:116px;flex-shrink:0';row.append(label);
        for(const [label,anim,dir,index] of variants) {
          const box=document.createElement('div');box.style.cssText='width:138px;text-align:center';
          const caption=document.createElement('small');caption.textContent=label+(r.pixel.animations?.[anim]||anim==='Walk'?'':'（替代）');
          const canvas=document.createElement('canvas');canvas.width=132;canvas.height=100;canvas.style.cssText='display:block;background:#173564;margin:3px';
          const a=new G.Sprites.Animator(r.dex);a.cur=anim;a.dir=dir;a.frame=Math.min(index,G.Sprites.animMeta(r.dex,anim).n-1);
          a.draw(canvas.getContext('2d'),66,92);box.append(caption,canvas);row.append(box);
        }panel.append(row);
      }document.body.append(panel);
      return summaries;
    }''')
    page.screenshot(path=str(ROOT/'.omx/naruto-animation-review.png'),animations='disabled')
    assert not errors,errors
    print(json.dumps({'directions':'passed','source_actions':report,'errors':errors},ensure_ascii=True))
    browser.close()
