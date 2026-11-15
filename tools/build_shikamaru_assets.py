"""Repack the generated Shikamaru poses; no artwork is synthesized by this tool."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,find_objects
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art-review/shikamaru'
KEYS='frontIdle backIdle idle frontRun1 frontRun2 backRun1 backRun2 run1 run2 frontPrepare frontSeal frontCrouch backPrepare backSeal backCrouch prepare seal crouch throwPrepare throwRelease throwRecover hurt exhausted faint'.split()
def main():
    source=OUT/'source-v1.png'; im=Image.open(source).convert('RGBA'); a=np.array(im)
    labels,_=label(a[:,:,3]>100); components=[]
    for i,b in enumerate(find_objects(labels),1):
        if b is not None and (labels[b]==i).sum()>1000: components.append((b[1].start,b[0].start,b[1].stop,b[0].stop,i))
    assert len(components)==24, 'Generated poses must be inspected before repacking'
    components.sort(key=lambda b:b[1])
    ordered=[]
    for r in range(4): ordered.extend(sorted(components[r*6:r*6+6],key=lambda b:b[0]))
    atlas=Image.new('RGBA',(768,520)); frames={}; scale=92/244
    for index,(key,(x0,y0,x1,y1,component)) in enumerate(zip(KEYS,ordered)):
        crop=a[y0:y1,x0:x1].copy()
        # Isolate the measured opaque pose, retaining original edge alpha within
        # its connected silhouette rather than importing transparent hidden RGB.
        crop[:,:,3]=np.where(labels[y0:y1,x0:x1]==component,crop[:,:,3],0)
        sprite=Image.fromarray(crop).resize((round((x1-x0)*scale),round((y1-y0)*scale)),Image.Resampling.NEAREST)
        x=(index%6)*128+(128-sprite.width)//2;y=(index//6)*104+100-sprite.height
        atlas.alpha_composite(sprite,(x,y))
        frames[key]={'rect':[index%6*128,index//6*104,128,104],'anchor':[64,100],'bodyHeight':92,'sourceRect':[x0,y0,x1-x0,y1-y0], 'visibleHeight':sprite.height}
    supplement=OUT/'source-v2-throw.png'; extra=np.array(Image.open(supplement).convert('RGBA'))
    extraLabels,_=label(extra[:,:,3]>100)
    bounds=[(b[1].start,b[0].start,b[1].stop,b[0].stop,i) for i,b in enumerate(find_objects(extraLabels),1) if b is not None and (extraLabels[b]==i).sum()>1000]
    assert len(bounds)==6
    bounds.sort(key=lambda b:(b[1]//512,b[0]))
    for index,(key,(x0,y0,x1,y1,component)) in enumerate(zip(['frontThrowPrepare','frontThrowRelease','frontThrowRecover','backThrowPrepare','backThrowRelease','backThrowRecover'],bounds)):
        crop=extra[y0:y1,x0:x1].copy();crop[:,:,3]=np.where(extraLabels[y0:y1,x0:x1]==component,crop[:,:,3],0)
        sprite=Image.fromarray(crop).resize((round((x1-x0)*92/466),round((y1-y0)*92/466)),Image.Resampling.NEAREST)
        x=index*128+(128-sprite.width)//2;y=416+100-sprite.height;atlas.alpha_composite(sprite,(x,y))
        frames[key]={'rect':[index*128,416,128,104],'anchor':[64,100],'bodyHeight':92,'sourceRect':[x0,y0,x1-x0,y1-y0], 'visibleHeight':sprite.height}
    target=OUT/'atlas-v1.png';atlas.save(target,optimize=True)
    meta={'version':2,'dex':30017,'provenance':'Original imagegen artwork; 30 measured pose silhouettes packed at one fixed scale. Authored front, back and side throw phases; left uses side mirror.','sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'supplementSha256':hashlib.sha256(supplement.read_bytes()).hexdigest(),'sheets':{'body':{'source':'shikamaru/atlas-v1.png','bodyHeight':92,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'frames':frames}}}
    (ROOT/'art-review/shikamaru-frames.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main()
