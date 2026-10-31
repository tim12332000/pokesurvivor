"""Bounded runtime packaging of generated VFX: resize/encode/index, no repaint.

The full original is retained for provenance and never loaded by the preview.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
source=ROOT/'effects-bones-art-v2.png'
runtime=ROOT/'effects-bones-runtime.png'
original=Image.open(source).convert('RGBA')
scale=640/original.width
small=original.resize((round(original.width*scale),round(original.height*scale)),Image.Resampling.LANCZOS)
# A bounded palette reduces transfer size while retaining actual alpha. Convert
# back to RGBA so existing atlas inspection and browsers use one format.
small=small.quantize(colors=96,method=Image.Quantize.FASTOCTREE).convert('RGBA')
small.save(runtime,optimize=True,compress_level=9)
assert runtime.stat().st_size<=256*1024
assert small.width*small.height*4<=int(1.75*1024*1024)
alpha=np.array(small)[:,:,3]
frames={}
regions=[]
for row,(y0,y1) in enumerate([(0,550),(550,865),(865,1086)]):
    columns=[0,362,760,1125,1448] if row<2 else [0,400,880,1125,1448]
    for col in range(4):
        name=f'pillar{row*4+col+1}' if row<2 else ['drill1','drill2','debris1','debris2'][col]
        regions.append((name,columns[col],y0,columns[col+1],y1))
for name,x0,y0,x1,y1 in regions:
    x0,y0,x1,y1=[round(v*scale) for v in (x0,y0,x1,y1)]
    points=np.argwhere(alpha[y0:y1,x0:x1]>30)
    assert len(points)>40,name
    top,left=points.min(axis=0);bottom,right=points.max(axis=0)+1
    left=max(0,x0+int(left)-1);right=min(small.width,x0+int(right)+1)
    top=max(0,y0+int(top)-1);bottom=min(small.height,y0+int(bottom)+1)
    w,h=right-left,bottom-top
    band=alpha[max(top,bottom-15):bottom,left:right]>30
    xs=np.nonzero(band)[1]
    anchor=[round((float(xs.min())+float(xs.max()))/2,2),h-1]
    frame={'rect':[left,top,w,h],'anchor':anchor}
    if name.startswith('drill'):
        local=alpha[top:bottom,left:right]>30
        tip_rows=np.nonzero(local[:,max(0,w-8):])[0]
        axis=float(np.median(tip_rows)) if len(tip_rows) else h/2
        frame.update(origin=[2,round(axis,2)],tip=[w-2,round(axis,2)])
    frames[name]=frame
data={'image':runtime.name,'width':small.width,'height':small.height,'frames':frames,
      'sha256':hashlib.sha256(runtime.read_bytes()).hexdigest(),
      'source':source.name,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'budget':{'maxPillars':36,'maxTransientParticles':20,'maxTransferBytes':256*1024,
                'maxDecodedBytes':int(1.75*1024*1024),'actualTransferBytes':runtime.stat().st_size,
                'actualDecodedBytes':small.width*small.height*4},
      'scope':'shared physical-bone VFX atlas, generated original retained, runtime only loads this reduced atlas'}
(ROOT/'effects.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'image':runtime.name,'size':small.size,'bytes':runtime.stat().st_size,
                  'decodedBytes':small.width*small.height*4,'frames':len(frames)}))
