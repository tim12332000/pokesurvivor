"""Capture a contact sheet from the verified browser renderer (not new art)."""
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'evidence'
OUT.mkdir(exist_ok=True)
CASES = [('willow',.467,'normal'),('camellia',.57,'normal'),
         ('bullets',.42,'normal'),('larch',.40,'normal'),
         ('vine',.54,'normal'),('flower',.58,'normal'),
         ('bracken',1.00,'normal'),('lily',.52,'normal'),
         ('combo',1.12,'curse'),('curse',1.10,'normal')]
font = ImageFont.truetype(r'C:\Windows\Fonts\msjh.ttc',22)
board = Image.new('RGB',(1200,2050),'#111721')
draw = ImageDraw.Draw(board)
proof = []
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1365,'height':1000})
    page.goto('http://127.0.0.1:8327/art-review/kimimaro-design/')
    page.wait_for_function('KimimaroPreview.ready')
    for i,(skill,t,form) in enumerate(CASES):
        snapshot=page.evaluate('''({skill,t,form})=>{
          const p=KimimaroPreview;p.pause();p.setRank(3);p.setQuantity(skill==='bullets'?5:skill==='willow'?4:0);
          p.setForm(form);p.selectSkill(skill);p.pause();p.setTime(t);
          return p.scene.getSnapshot();
        }''',{'skill':skill,'t':t,'form':form})
        assert snapshot['assetStatus']=='loaded' and snapshot['clipApplied']
        frame=Image.open(io.BytesIO(page.locator('#preview-canvas').screenshot())).convert('RGB')
        frame.thumbnail((580,360))
        x=(i%2)*600;y=(i//2)*410
        title=page.locator('#skill-name').inner_text()
        draw.text((x+16,y+10),f'{i+1:02d}  {title}',font=font,fill='#f0e7d5')
        board.paste(frame,(x+(600-frame.width)//2,y+42))
        proof.append({'skill':skill,'time':t,'form':snapshot['renderedForm'],'source':snapshot['actorSource'],'pose':snapshot['pose']})
    page.set_viewport_size({'width':390,'height':844})
    page.evaluate("KimimaroPreview.setForm('curse');KimimaroPreview.selectSkill('combo');KimimaroPreview.setTime(1.12)")
    page.screenshot(path=str(OUT/'mobile-preview.png'),full_page=True)
    browser.close()
board.save(OUT/'overview.png')
(OUT/'overview.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Captured ten actual renderer frames and final mobile preview.')
