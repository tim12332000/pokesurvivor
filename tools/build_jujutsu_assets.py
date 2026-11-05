"""Register inspected transparent generation cells without redrawing source artwork."""
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art-review'

def tight(image, cell):
    x0,y0,x1,y1 = map(int,cell)
    alpha=image.getchannel('A').crop((x0,y0,x1,y1))
    box=alpha.point(lambda a:255 if a>=24 else 0).getbbox()
    if not box: raise ValueError(('Empty pose',cell))
    left,top,right,bottom=box
    return [x0+left,y0+top,right-left,bottom-top]

def build():
    sheets={}
    sources={}
    for slug in ['yuta','ryu','uro','rika']:
        source=ART/'jjk-art'/f'{slug}-source-v1.png'
        target=ART/'redrawn'/f'jjk-{slug}-v1.png'
        shutil.copyfile(source,target)
        im=Image.open(source).convert('RGBA');w,h=im.size
        if im.getchannel('A').getextrema()!=(0,255):raise ValueError('Expected authored transparency')
        cells=[]
        rows=2 if slug=='rika' else 4
        for row in range(rows):
            for col in range(4):cells.append((round(w*col/4),round(h*row/rows),round(w*(col+1)/4),round(h*(row+1)/rows)))
        if slug=='uro':
            # The inspected source has three broad bottom-row poses, not four.
            physical=cells[:12]+[(0,round(h*.75),round(w*.25),h),(round(w*.25),round(h*.75),round(w*.5),h),(round(w*.5),round(h*.75),w,h)]
            mapping=[0,1,2,3,4,5,6,7,7,8,9,10,11,12,13,14]
            cells=[physical[i] for i in mapping]
        rects=[tight(im,cell) for cell in cells]
        body=rects[0][3]
        frames=[]
        for i,rect in enumerate(rects):
            x,y,fw,fh=rect
            # In a fallen pose anchor the body at ground instead of stretching it.
            # All poses retain the same standing-height denominator.
            anchor_x=fw/2
            if slug!='rika' and i!=15:
                # A katana or stretched sky cloth widens the crop without
                # moving the body. Locate solid shoe pixels at ground height.
                solid=im.getchannel('A').crop((x,y,x+fw,y+fh)).point(lambda a:255 if a>=180 else 0)
                feet=solid.crop((0,max(0,fh-12),fw,fh)).getbbox()
                if feet:anchor_x=(feet[0]+feet[2])/2
            frames.append({'rect':rect,'anchor':[anchor_x,fh-1]})
        sheets[slug]={'source':f'redrawn/jjk-{slug}-v1.png','bodyHeight':body,'frames':frames}
        sources[slug]={'source':str(source.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'runtimeSha256':hashlib.sha256(target.read_bytes()).hexdigest(),'physicalFrames':15 if slug=='uro' else len(frames),'registeredFrames':len(frames)}
        if slug!='rika':
            x,y,fw,fh=rects[0]
            portrait=im.crop((x,y,x+fw,y+fh))
            portrait.save(ROOT/'.omx/naruto/portraits'/f'jjk-{slug}.png')
    metadata={'version':1,'sheets':sheets,'limitations':['Left-facing side animation mirrors right-facing authored poses.','Uro has a single authored side walking pose; its two walk slots intentionally share that frame.','Only front/back/right directions are separately drawn.']}
    (ART/'jjk-frames.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    (ART/'jjk-art/provenance-v1.json').write_text(json.dumps({'generator':'built-in image_gen','reference':'art-review/redrawn/gaara-common-v1.png','prompts':'art-review/jjk-art/prompts-v1.json','sources':sources,'processing':'Copy original transparent atlas unchanged; inspected cells registered and portrait crops extracted.'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'sheets':len(sheets),'registeredFrames':sum(len(s['frames']) for s in sheets.values()),'physicalFrames':55,'transparent':True}))

if __name__=='__main__':build()
