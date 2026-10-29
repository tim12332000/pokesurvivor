"""Pack approved merged forest groves as three contiguous strips per grove.

Horizontal strips preserve more source detail inside one effects atlas.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'art-review/redrawn/kimimaro-forest-groves-generated-v4.png'
TARGET=ROOT/'art-review/redrawn/kimimaro-effects-v5.png'
SOURCE_RECTS=[(27,24,481,705),(559,23,470,705),(1095,23,457,709),(1611,77,416,658)]
def build():
    im=Image.open(SOURCE).convert('RGBA')
    original=Image.open(ROOT/'art-review/redrawn/kimimaro-effects-v1.png').convert('RGBA')
    atlas=Image.new('RGBA',(640,768))
    atlas.paste(original.crop((0,0,640,240)),(0,0))
    atlas.paste(original.crop((0,380,640,480)),(0,668))
    def sprite(source,rect,height):
        x,y,w,h=rect
        cell=np.array(source.crop((x,y,x+w,y+h)))
        alpha=cell[:,:,3]
        mask=alpha>=128
        ys,xs=np.where(mask)
        cell[:,:,3]=np.where(mask,255,0).astype('uint8')
        cropped=Image.fromarray(cell).crop((int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1))
        width=round(cropped.width*height/cropped.height)
        return cropped.resize((width,height),Image.Resampling.LANCZOS)
    singles=Image.open(ROOT/'art-review/redrawn/kimimaro-bone-spikes-generated-v3.png').convert('RGBA')
    frames=[];cursor=0;row=244
    for i in range(4):
        image=sprite(singles,(i*512,0,512,768),204);width=image.width;segments=[]
        for offset in range(0,204,68):
            if cursor+width>640:cursor=0;row+=68
            assert row+68<=380
            atlas.alpha_composite(image.crop((0,offset,width,offset+68)),(cursor,row))
            segments.append({'rect':[cursor,row,width,68],'offsetY':offset});cursor+=width+1
        frames.append({'rect':segments[0]['rect'],'anchor':[width/2,67],
                       'sourceSize':[width,204],'segments':segments})
    grove_images=[sprite(im,rect,240) for rect in SOURCE_RECTS]
    grove_frames=[{'sourceSize':[image.width,240],'segments':[]} for image in grove_images]
    for offset in range(0,240,80):
        cursor=0;row=384+offset
        for image,frame in zip(grove_images,grove_frames):
            assert cursor+image.width<=640 and row+80<=668
            atlas.alpha_composite(image.crop((0,offset,image.width,offset+80)),(cursor,row))
            frame['segments'].append({'rect':[cursor,row,image.width,80],'offsetY':offset})
            cursor+=image.width+1
    for frame in grove_frames:
        frame.update(rect=frame['segments'][0]['rect'],anchor=[frame['sourceSize'][0]/2,79])
    frames.extend(grove_frames)
    atlas.save(TARGET,optimize=True)
    meta_path=ROOT/'art-review/kimimaro-frames.json'
    meta=json.loads(meta_path.read_text(encoding='utf8'))
    meta['budget']['maxForestColumns']=96
    meta['budget']['maxDecodedSheetBytes']=5*1024*1024
    effects=meta['sheets']['effects'];effects['source']='redrawn/kimimaro-effects-v5.png'
    effects['width'],effects['height']=atlas.size
    base_frames=json.loads((ROOT/'art-review/kimimaro-design/effects.json').read_text(encoding='utf8'))['frames']
    for key in ['drill1','drill2','debris1','debris2']:
        frame=json.loads(json.dumps(base_frames[key]));frame['rect'][1]+=288
        effects['frames'][key]=frame
    effects['sha256']=hashlib.sha256(TARGET.read_bytes()).hexdigest();effects['bytes']=TARGET.stat().st_size
    for i,frame in enumerate(frames):
        effects['frames']['pillar'+str(i+5)]=frame
    meta.setdefault('sources',{})['forestEffectProvenance']='redrawn/kimimaro-forest-mix-v5-provenance.json'
    decoded=sum(sheet['width']*sheet['height']*4 for sheet in meta['sheets'].values())
    meta['budget']['decodedSheetBytes']=decoded
    assert decoded<=meta['budget']['maxDecodedSheetBytes']
    meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    original=np.array(original)
    packed=np.array(atlas)
    assert np.array_equal(original[:240],packed[:240])
    assert np.array_equal(original[380:],packed[668:])
    assert TARGET.stat().st_size<=512*1024
    return effects

if __name__=='__main__':
    print(json.dumps(build(),ensure_ascii=True))
