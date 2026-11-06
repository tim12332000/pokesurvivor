"""Register the generated Madara sheet without resampling its source pixels."""
import hashlib
import json
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art-review' / 'madara'


def cuts(mask, count, vertical):
    length = mask.height if vertical else mask.width
    projection = [sum(mask.crop((0, p, mask.width, p + 1) if vertical else
                               (p, 0, p + 1, mask.height)).getdata()) for p in range(length)]
    result = [0]
    for n in range(1, count):
        center = length * n / count
        candidates = range(max(result[-1] + 1, int(center - length / count * .22)),
                           min(length, int(center + length / count * .22)))
        result.append(min(candidates, key=lambda p: (
            sum(projection[max(0, p - 3):p + 4]), abs(p - center))))
    return result + [length]


def registered(source_name, rows, columns, body_height, target_height, names=None,
               socket_points=None, core_points=None, avatar=False):
    """Pack exact alpha crops at one sheet-wide scale, preserving every source rect."""
    source = ART / source_name
    image = Image.open(source).convert('RGBA')
    mask = image.getchannel('A').point(lambda value: 255 if value >= 24 else 0)
    ys, frames, crops = cuts(mask, rows, True), [], []
    scale = target_height / body_height
    for row in range(rows):
        xs = cuts(mask.crop((0, ys[row], image.width, ys[row + 1])), columns, False)
        for column in range(columns):
            cell = (xs[column], ys[row], xs[column + 1], ys[row + 1])
            box = mask.crop(cell).getbbox()
            assert box, (source_name, row, column)
            x, y = cell[0] + box[0], cell[1] + box[1]
            w, h = box[2] - box[0], box[3] - box[1]
            crop = image.crop((x, y, x + w, y + h))
            index = len(frames)
            solid = crop.getchannel('A').point(lambda value: 255 if value >= 180 else 0)
            solid_box = solid.getbbox() or (0, 0, w, h)
            foot_y = solid_box[3] - 1
            feet = solid.crop((0, max(0, foot_y - 7), w, foot_y + 1)).getbbox()
            anchor = [(feet[0] + feet[2])/2, foot_y] if feet else [w/2, foot_y]
            core = (core_points[index] if core_points else .5) * w
            sockets = {}
            measured = {}
            for key, value in (socket_points[index] if socket_points else {}).items():
                px, py = value[0]*w, value[1]*h
                # Nominal sites are hand measured against the source silhouette.
                # Snap only the final pixel registration, never extend a limb.
                limit = int(body_height*.09)
                candidates = [(ax,ay) for ay in range(max(0,int(py)-limit),min(h,int(py)+limit+1))
                              for ax in range(max(0,int(px)-limit),min(w,int(px)+limit+1))
                              if crop.getpixel((ax,ay))[3]>=180]
                if candidates:
                    ax,ay=min(candidates,key=lambda p:(p[0]-px)**2+(p[1]-py)**2)
                else: ax,ay=px,py
                measured[key] = {'nominal':[round(px,2),round(py,2)],'pixel':[ax,ay],
                                 'correction':round(((ax-px)**2+(ay-py)**2)**.5,2)}
                sockets[key]=[round(ax*scale,3),round(ay*scale,3)]
            if avatar:
                # All avatar points are explicit source-space values. The owner's
                # feet remain at the same world ground as the avatar base.
                anchor = [core, h - (body_height * .04 if 'rib' in source_name else 0)]
                sockets.update(groundAnchor=[round(v * scale, 3) for v in anchor],
                               ownerSocket=[round(core*scale, 3), round(anchor[1]*scale, 3)],
                               controlLinkSocket=[round(core*scale, 3), round((anchor[1]-body_height*.15)*scale, 3)])
            frames.append({'name': names[index] if names else str(index), 'sourceRect': [x, y, w, h],
                           'anchor': [round(v*scale, 3) for v in anchor], 'sockets': sockets,
                           'sourceSocketMeasurements':measured})
            crops.append(crop.resize((max(1, round(w*scale)), max(1, round(h*scale))), Image.Resampling.NEAREST))
    packed_columns = min(4, len(frames))
    cell_w, cell_h = max(c.width for c in crops)+4, max(c.height for c in crops)+4
    packed = Image.new('RGBA', (packed_columns*cell_w, ((len(frames)+packed_columns-1)//packed_columns)*cell_h))
    for index, (frame, crop) in enumerate(zip(frames, crops)):
        px, py = (index % packed_columns)*cell_w+2, (index//packed_columns)*cell_h+2
        packed.paste(crop, (px, py))
        frame['rect'] = [px, py, crop.width, crop.height]
    destination = ART / (source.stem+'-runtime.png')
    packed.save(destination, optimize=True)
    return {'source': destination.name, 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
            'originalSource': source.name, 'originalSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'bodyHeight': target_height, 'originalBodyHeight': body_height,
            'bytes': destination.stat().st_size, 'size': list(packed.size), 'frames': frames}


def avatar_geometry(sheet, anchors, points, form, canonical=None):
    """Source coordinates are actual foot/waist anchors, not the lowest sword pixel."""
    scale=sheet['bodyHeight']/sheet['originalBodyHeight']
    source=Image.open(ART/sheet['originalSource']).convert('RGBA')
    for index,frame in enumerate(sheet['frames']):
        x,y,_,_=frame['sourceRect'];ax,ay=anchors[index]
        frame['anchor']=[round((ax-x)*scale,3),round((ay-y)*scale,3)]
        frame['sockets']={}
        for key,p in points[index].items():
            px,py=p;candidate=(px,py)
            if not (0<=px<source.width and 0<=py<source.height and source.getpixel((px,py))[3]>=180):
                near=[(sx,sy) for sy in range(max(0,py-16),min(source.height,py+17))
                      for sx in range(max(0,px-16),min(source.width,px+17)) if source.getpixel((sx,sy))[3]>=180]
                if near:candidate=min(near,key=lambda q:(q[0]-px)**2+(q[1]-py)**2)
            frame['sockets'][key]=[round((candidate[0]-x)*scale,3),round((candidate[1]-y)*scale,3)]
            frame['sourceSocketMeasurements'][key]={'nominal':list(p),'pixel':list(candidate),
                'correction':round(((candidate[0]-px)**2+(candidate[1]-py)**2)**.5,2)}
        frame['sockets'].update(groundAnchor=list(frame['anchor']),ownerSocket=list(frame['anchor']))
        ratio={'rib':.2,'armored':.136,'perfect':.084}[form]
        frame['sockets']['ownerChest']=[frame['anchor'][0],round(frame['anchor'][1]-sheet['bodyHeight']*ratio,3)]
        frame['sockets']['controlLinkSocket']=[frame['anchor'][0],round(frame['anchor'][1]-sheet['bodyHeight']*.5,3)]
        if canonical and canonical[index]:
            cx,cy=canonical[index];frame['sockets']['canonicalSocket']=[round((cx-x)*scale,3),round((cy-y)*scale,3)]
        frame['groundPolicy']='measured virtual waist base' if form!='perfect' else 'measured foot floor, never blade tip'
    sheet['ownerPolicy']='ground feet; 64px actor is foreground projection, not the forehead occupant'
    return sheet


def extra_sheets():
    sheets = {}
    if (ART / 'madara-taijutsu-v2.png').exists():
        points = [
            {'mouth': [.77,.24], 'palm': [.91,.51], 'elbow': [.66,.49], 'foot': [.85,.97]},
            {'mouth': [.61,.25], 'palm': [.98,.25], 'elbow': [.70,.30], 'foot': [.75,.97]},
            {'mouth': [.76,.25], 'palm': [.93,.51], 'elbow': [.43,.34], 'foot': [.85,.97]},
            {'mouth': [.79,.24], 'palm': [.73,.36], 'elbow': [.98,.31], 'foot': [.85,.97]},
            {'mouth': [.73,.24], 'palm': [.96,.38], 'elbow': [.79,.39], 'foot': [.85,.97]},
            {'mouth': [.76,.25], 'palm': [.91,.34], 'elbow': [.41,.48], 'foot': [.74,.77]},
            {'mouth': [.51,.24], 'palm': [.67,.32], 'elbow': [.32,.41], 'foot': [.98,.36]},
            {'mouth': [.76,.24], 'palm': [.83,.42], 'elbow': [.66,.39], 'foot': [.98,.80]},
            {'mouth': [.75,.24], 'palm': [.97,.56], 'elbow': [.72,.55], 'foot': [.88,.97]},
            {'mouth': [.73,.24], 'palm': [.92,.62], 'elbow': [.70,.53], 'foot': [.86,.97]},
        ]
        sheets['taijutsu'] = registered('madara-taijutsu-v2.png', 2, 5, 345, 128,
            ['step','palm','elbow-windup','elbow','pivot','knee','kick','turn-kick','landing','recover'], points)
    if (ART / 'madara-body-directions-v2.png').exists():
        points = [
            {'mouth':[.58,.27],'palm':[.35,.70],'elbow':[.43,.49],'foot':[.88,.95]},
            {'mouth':[.67,.25],'palm':[.70,.43],'elbow':[.50,.42],'foot':[.87,.95]},
            {'mouth':[.68,.26],'palm':[.15,.55],'elbow':[.27,.47],'foot':[.48,.69]},
            {'mouth':[.57,.26],'palm':[.20,.65],'elbow':[.20,.53],'foot':[.84,.96]},
            {'mouth':[.65,.24],'palm':[.82,.08],'elbow':[.76,.34],'foot':[.85,.96]},
            {'mouth':[.63,.26],'palm':[.75,.24],'elbow':[.88,.19],'foot':[.85,.96]},
            {'mouth':[.55,.25],'palm':[.78,.48],'elbow':[.64,.45],'foot':[.92,.13]},
            {'mouth':[.56,.25],'palm':[.83,.67],'elbow':[.80,.53],'foot':[.84,.96]},
        ]
        sheets['bodyDirections'] = registered('madara-body-directions-v2.png',2,4,382,128,
            ['down-palm','down-elbow','down-kick','down-recover','up-palm','up-elbow','up-kick','up-recover'],points)
        # The rising kick is airborne; keep its virtual floor at the family baseline.
        frame = sheets['bodyDirections']['frames'][6]
        frame['anchor'][1] += 33*128/382
    if (ART / 'madara-elements-v2.png').exists():
        sheets['elements'] = registered('madara-elements-v2.png',2,3,571,256,
            ['fire-burst','fire-wall','fire-tail','rock','fracture','rubble'])
    if (ART / 'madara-wood-v3.png').exists():
        sheets['wood'] = registered('madara-wood-v3.png',2,2,480,128,
            ['root','separate','reveal','dismiss'])
    avatar_specs = [
        ('rib','madara-susanoo-rib-v3.png',2,3,400,256,
         [(288,400),(893,398),(1505,398),(215,820),(808,850),(1465,833)],
         [(178,151,102,362,102,362,145,384),(798,151,701,287,701,287,739,289),
          (1401,167,1368,55,1368,55,1419,22),(148,579,472,618,472,618,533,620),
          (761,607,1050,811,1050,811,1114,845),(1379,599,1652,704,1652,704,1707,710)]),
        ('armored','madara-susanoo-armored-v4.png',2,2,390,256,
         [(410,320),(1159,330),(355,800),(1080,820)],
         [(310,203,290,351,310,373,391,439),(1055,174,1036,97,1060,80,1216,25),
          (340,675,489,717,527,720,700,711),(1089,685,1226,850,1246,866,1370,928)]),
        ('perfect','madara-susanoo-perfect-v4.png',2,2,415,320,
         [(421,464),(1110,463),(344,945),(1059,942)],
         [(359,207,355,285,355,285,355,285),(1082,179,1058,128,1085,105,1234,57),
          (357,683,460,733,484,738,679,707),(1109,688,1138,805,1172,831,1334,938)]),
        ('ribDirections','madara-rib-directions-v2.png',2,2,400,256,
         [(424,422),(1157,416),(410,975),(1160,988)],
         [(326,193,265,65,265,65,329,28),(1038,211,990,376,990,376,999,490),
          (491,698,553,556,553,556,528,512),(1261,704,1292,551,1292,551,1327,507)]),
        ('armoredDirections','madara-armored-directions-v2.png',2,2,550,256,
         [(318,420),(915,420),(316,1120),(915,1120)],
         [(186,235,149,138,189,144,551,262),(797,242,884,375,890,410,894,630),
          (431,880,452,811,408,810,74,927),(970,861,942,785,937,758,927,659)]),
        ('perfectDirections','madara-perfect-directions-v2.png',2,2,555,320,
         [(326,574),(892,576),(320,1280),(881,1280)],
         [(218,235,213,138,258,123,553,95),(786,215,884,314,887,356,898,614),
          (451,880,437,811,400,795,93,727),(965,829,927,751,926,721,893,639)]),
    ]
    for key,name,rows,cols,body_h,target,anchors,coordinates in avatar_specs:
        if not (ART/name).exists():continue
        names=['guard','draw','sweep','followthrough'] if cols==2 else ['guard','draw','raised','sweep','followthrough','recover']
        if key.endswith('Directions'):names=['down-draw','down-sweep','up-draw','up-sweep']
        sheet=registered(name,rows,cols,body_h,target,names)
        points=[dict(zip(['shoulder','hand','bladeBase','bladeTip'],[(v[i],v[i+1]) for i in range(0,8,2)])) for v in coordinates]
        form=key.replace('Directions','')
        canonical={'perfect':[(448,118),(1184,156),(393,653),(1154,646)],
                   'perfectDirections':[(332,134),(893,133),None,None]}.get(key)
        sheets[key]=avatar_geometry(sheet,anchors,points,form,canonical)
    if (ART/'madara-rib-down-contact-v2.png').exists():
        sheet=registered('madara-rib-down-contact-v2.png',1,1,620,256,['down-contact'])
        points=[{'shoulder':(624,302),'hand':(765,727),'bladeBase':(765,727),'bladeTip':(770,1009)}]
        sheets['ribDown']=avatar_geometry(sheet,[(768,620)],points,'rib')
    if (ART/'madara-casting-directions-v2.png').exists():
        sheets['castingDirections']=registered('madara-casting-directions-v2.png',2,3,452,128,
            ['down-seal','down-breath','down-recover','up-seal','up-breath','up-recover'],
            [{'mouth':[.50,.30]},{'mouth':[205/345,158/420]},{'mouth':[.52,.30]},
             {'mouth':[.67,.24]},{'mouth':[224/337,70/454]},{'mouth':[.7,.24]}])
    if (ART/'madara-walk-directions-v3.png').exists():
        sheets['walkDirections']=registered('madara-walk-directions-v3.png',2,4,434,128,
            ['down-left','down-pass-left','down-right','down-pass-right',
             'up-left','up-pass-left','up-right','up-pass-right'])
    return sheets


def main():
    source = ART / 'madara-actions-v1.png'
    image = Image.open(source).convert('RGBA')
    alpha = image.getchannel('A')
    assert alpha.getextrema() == (0, 255), 'Expected real transparency'
    mask = alpha.point(lambda value: 255 if value >= 24 else 0)
    ys = cuts(mask, 4, True)
    frames = []
    names = ['idle', 'step-left', 'step-right', 'ready', 'seal-start', 'seal-hold',
             'fire-breath', 'recover', 'arm-back', 'command', 'summon', 'finish',
             'flinch', 'hurt', 'fall', 'faint']
    for row in range(4):
        stripe = mask.crop((0, ys[row], image.width, ys[row + 1]))
        xs = cuts(stripe, 4, False)
        for column in range(4):
            cell = (xs[column], ys[row], xs[column + 1], ys[row + 1])
            bounds = mask.crop(cell).getbbox()
            assert bounds, f'Empty frame {row}, {column}'
            left, top = cell[0] + bounds[0], cell[1] + bounds[1]
            right, bottom = cell[0] + bounds[2], cell[1] + bounds[3]
            crop = image.crop((left, top, right, bottom))
            solid = crop.getchannel('A').point(lambda value: 255 if value >= 180 else 0)
            box = solid.getbbox()
            foot_y = box[3] - 1
            feet = solid.crop((0, max(0, foot_y - 7), crop.width, foot_y + 1)).getbbox()
            frames.append({'name': names[len(frames)], 'rect': [left, top, right-left, bottom-top],
                           'anchor': [(feet[0]+feet[2])/2, foot_y]})
    body_height = median(frame['rect'][3] for frame in frames[:3])
    metadata = {'source': source.name, 'bodyHeight': body_height, 'directions': 'right; left mirrored; side view for up/down',
                'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'frames': frames}
    common_points=[{'mouth':[184/236 if i==6 else .72,74/255 if i==6 else .23],
                    'palm':[.88,.45],'elbow':[.68,.43],'foot':[.82,.96]} for i in range(16)]
    common=registered(source.name,4,4,body_height,128,names,common_points)
    metadata.update(common)
    metadata['directions']='left/right body plus authored front/back combat and casting supplements'
    metadata['sheets'] = extra_sheets()
    (ART / 'frames.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    preview = Image.new('RGB', (640, 320), '#49713f')
    draw = ImageDraw.Draw(preview)
    for index, frame in enumerate(frames):
        x, y, w, h = frame['rect']
        scale = 64 / body_height
        sprite = image.crop((x, y, x+w, y+h)).resize((round(w*scale), round(h*scale)), Image.Resampling.NEAREST)
        column, row = index % 8, index // 8
        preview.paste(sprite, (column*80+40-round(frame['anchor'][0]*scale), row*160+105-round(frame['anchor'][1]*scale)), sprite)
        draw.text((column*80+2, row*160+120), frame['name'], fill='white')
    preview.save(ART / 'game-size-contact.png')
    print(json.dumps({'frames': len(frames), 'bodyHeight': body_height, 'sha256': metadata['sha256']}))


if __name__ == '__main__':
    main()
