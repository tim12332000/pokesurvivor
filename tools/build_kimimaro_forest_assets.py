"""Pack generated forest needles into the existing effect-atlas budget."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'art-review/redrawn/kimimaro-bone-spikes-generated-v2.png'
TARGET=ROOT/'art-review/redrawn/kimimaro-effects-v2.png'
def build():
    im=Image.open(SOURCE).convert('RGBA')
    atlas=Image.open(ROOT/'art-review/redrawn/kimimaro-effects-v1.png').convert('RGBA')
    atlas.paste((0,0,0,0),(0,240,640,380))
    rects=[]
    for i,height in enumerate([132,120,104,128]):
        cell=np.array(im.crop((i*512,0,(i+1)*512,768)))
        alpha=cell[:,:,3]
        mask=alpha>=128
        ys,xs=np.where(mask)
        cell[:,:,3]=np.where(mask,255,0).astype('uint8')
        sprite=Image.fromarray(cell).crop((int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1))
        width=round(height/9)
        sprite=sprite.resize((width,height),Image.Resampling.NEAREST)
        x=i*160+(160-width)//2;y=376-height
        atlas.alpha_composite(sprite,(x,y))
        rects.append([x,y,width,height])
    atlas.save(TARGET,optimize=True)
    meta_path=ROOT/'art-review/kimimaro-frames.json'
    meta=json.loads(meta_path.read_text(encoding='utf8'))
    effects=meta['sheets']['effects'];effects['source']='redrawn/kimimaro-effects-v2.png'
    effects['sha256']=hashlib.sha256(TARGET.read_bytes()).hexdigest();effects['bytes']=TARGET.stat().st_size
    for i,rect in enumerate(rects):
        effects['frames']['pillar'+str(i+5)]={'rect':rect,'anchor':[rect[2]/2,rect[3]-1]}
    meta.setdefault('sources',{})['forestEffectProvenance']='redrawn/kimimaro-bone-spikes-v2-provenance.json'
    meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    original=np.array(Image.open(ROOT/'art-review/redrawn/kimimaro-effects-v1.png').convert('RGBA'))
    packed=np.array(atlas)
    assert np.array_equal(original[:240],packed[:240])
    assert np.array_equal(original[380:],packed[380:])
    assert TARGET.stat().st_size<=256*1024
    return effects

if __name__=='__main__':
    print(json.dumps(build(),ensure_ascii=True))
