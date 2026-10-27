"""Pack original Kimimaro design art into bounded, isolated gameplay atlases.

Only alpha extraction, proportional sampling and palette encoding are performed.
The generated source artwork and its prompts remain in kimimaro-design/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops
from scipy.ndimage import find_objects, label

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT/'art-review/kimimaro-design'
OUT = ROOT/'art-review/redrawn'
BODY, CW, CH = 92, 140, 110
KEYS = ['idle','run1','run2','run3','willow1','willow2','camellia1','camellia2',
        'bullets','larch','vine1','vine2','flower1','flower2','bracken','lily']
COMMON = ['frontIdle','backIdle','frontRun','backRun','hurt1','hurt2','death1','death2']
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def source_pose(image, frame):
    x,y,w,h=frame['rect']
    sprite=image.crop((x,y,x+w,y+h)).convert('RGBA')
    if frame.get('clipRuns'):
        mask=Image.new('L',(w,h))
        from PIL import ImageDraw
        draw=ImageDraw.Draw(mask)
        for rx,ry,rw,rh in frame['clipRuns']:
            draw.rectangle((rx,ry,rx+rw-1,ry+rh-1),fill=255)
        sprite.putalpha(ImageChops.multiply(sprite.getchannel('A'),mask))
    return sprite,frame['anchor']


def supplement(path):
    image=Image.open(path).convert('RGBA');alpha=np.array(image)[:,:,3]
    connected,_=label(alpha>40)
    components=[]
    for i,bounds in enumerate(find_objects(connected),1):
        if bounds is None:continue
        if (connected[bounds]==i).sum()<image.width*image.height*.002:continue
        sy,sx=bounds;components.append((sx.start,sy.start,sx.stop,sy.stop,i))
    assert len(components)==16,('Supplement needs actual pose inspection',len(components))
    components.sort(key=lambda r:(r[1]+r[3])/2)
    ordered=[]
    for row in range(4):ordered.extend(sorted(components[row*4:row*4+4],key=lambda r:(r[0]+r[2])/2))
    result={}
    for form,start in [('normal',0),('curse',8)]:
        entries={};body=ordered[start][3]-ordered[start][1]
        for name,(x0,y0,x1,y1,i) in zip(COMMON,ordered[start:start+8]):
            margin=2;x=max(0,x0-margin);y=max(0,y0-margin)
            right=min(image.width,x1+margin);bottom=min(image.height,y1+margin)
            sprite=image.crop((x,y,right,bottom))
            own=(connected[y:bottom,x:right]==i).astype(np.uint8)*255
            sprite.putalpha(ImageChops.multiply(sprite.getchannel('A'),Image.fromarray(own)))
            band=connected[max(y0,y1-50):y1,x0:x1]==i
            xs=np.nonzero(band)[1]
            anchor=[x0+(float(xs.min())+float(xs.max()))/2-x,y1-y]
            entries[name]=(sprite,anchor,body)
        result[form]=entries
    return result


def pack(form,metadata,common):
    original=Image.open(DESIGN/metadata['image']).convert('RGBA')
    canvas=Image.new('RGBA',(CW*4,CH*6));frames={}
    entries=[]
    for key in KEYS:
        image,anchor=source_pose(original,metadata['frames'][key])
        entries.append((key,image,anchor,metadata['bodyHeight']))
    entries.extend((name,*common[name]) for name in COMMON)
    for i,(name,image,anchor,source_body) in enumerate(entries):
        scale=BODY/source_body
        w,h=round(image.width*scale),round(image.height*scale)
        image=image.resize((w,h),Image.Resampling.LANCZOS)
        ox=(i%4)*CW+64;oy=(i//4)*CH+104
        left=round(ox-anchor[0]*scale);top=round(oy-anchor[1]*scale)
        assert left>=(i%4)*CW and left+w<=(i%4+1)*CW,(form,name,left,w)
        assert top>=(i//4)*CH and top+h<=(i//4+1)*CH,(form,name,top,h)
        canvas.alpha_composite(image,(left,top))
        frames[name]={'rect':[left,top,w,h],'anchor':[ox-left,oy-top],
                      'bodyHeight':BODY,'originalBodyHeight':source_body}
    canvas=canvas.quantize(colors=128,method=Image.Quantize.FASTOCTREE).convert('RGBA')
    filename=f'kimimaro-{form}-v1.png';path=OUT/filename
    canvas.save(path,optimize=True,compress_level=9)
    return {'source':'redrawn/'+filename,'width':canvas.width,'height':canvas.height,
            'bodyHeight':BODY,'frames':frames,'sha256':sha(path),'bytes':path.stat().st_size}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--supplement',type=Path,
        default=DESIGN/'actors-game-supplement-v1.png');args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    original=json.loads((DESIGN/'actors.json').read_text(encoding='utf8'))
    shared=supplement(args.supplement)
    sheets={form:pack(form,original[form],shared[form]) for form in ['normal','curse']}
    fx=json.loads((DESIGN/'effects.json').read_text(encoding='utf8'))
    effect=OUT/'kimimaro-effects-v1.png';effect.write_bytes((DESIGN/fx['image']).read_bytes())
    sheets['effects']={'source':'redrawn/'+effect.name,'width':fx['width'],'height':fx['height'],
        'frames':fx['frames'],'sha256':sha(effect),'bytes':effect.stat().st_size}
    decoded=sum(s['width']*s['height']*4 for s in sheets.values())
    assert decoded<=4*1024*1024,decoded
    assert sheets['effects']['bytes']<=256*1024
    result={'version':1,'scope':'playable Kimimaro original art; up/down common poses, side attacks with explicit left mirror',
        'bodyHeight':BODY,'sheets':sheets,'budget':{'decodedSheetBytes':decoded,'maxDecodedSheetBytes':4*1024*1024,
        'maxForestColumns':72,'maxSecondaryParticles':20},
        'sources':{'actorMetadata':'kimimaro-design/actors.json','supplement':str(args.supplement.relative_to(ROOT)),
                   'supplementSha256':sha(args.supplement),'originalActorProvenance':'kimimaro-design/provenance-final.json',
                   'supplementProvenance':'kimimaro-design/game-supplement-provenance.json',
                   'effectProvenance':'kimimaro-design/provenance-art-v2.json'}}
    (ROOT/'art-review/kimimaro-frames.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # Selection cards use the same full-body composition as the other ninjas.
    image=Image.open(OUT/'kimimaro-normal-v1.png');f=sheets['normal']['frames']['frontIdle']
    x,y,w,h=f['rect'];pose=image.crop((x,y,x+w,y+h))
    bounds=pose.getbbox()
    assert bounds is not None,'Kimimaro selection pose is empty'
    pose=pose.crop(bounds)
    scale=min(84/pose.width,104/pose.height)
    pose=pose.resize((round(pose.width*scale),round(pose.height*scale)),Image.Resampling.NEAREST)
    portrait=Image.new('RGBA',(96,112))
    portrait.alpha_composite(pose,((96-pose.width)//2,110-pose.height))
    target=ROOT/'.omx/naruto/portraits/kimimaro.png';target.parent.mkdir(parents=True,exist_ok=True)
    portrait.save(target,optimize=True)
    print(json.dumps({'sheets':{key:{'source':s['source'],'bytes':s['bytes']} for key,s in sheets.items()},
        'frames':sum(len(s['frames']) for key,s in sheets.items() if key!='effects'),'decodedBytes':decoded},ensure_ascii=True))


if __name__=='__main__':main()
