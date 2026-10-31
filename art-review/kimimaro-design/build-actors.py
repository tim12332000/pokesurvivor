"""Index generated transparent key poses for the standalone preview only.

Reads alpha and records original-image rectangles; does not repaint, resize or
alter the generated bitmap, and never updates a game asset manifest.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, find_objects, label

ROOT = Path(__file__).resolve().parent
NAMES = ['idle', 'run1', 'run2', 'run3', 'willow1', 'willow2',
         'camellia1', 'camellia2', 'bullets', 'larch', 'vine1', 'vine2',
         'flower1', 'flower2', 'bracken', 'lily']


def index_atlas(filename):
    path = ROOT / filename
    im = Image.open(path).convert('RGBA')
    alpha = np.array(im)[:, :, 3]
    labels, _ = label(alpha > 40)
    components = []
    for component_id, bounds in enumerate(find_objects(labels), 1):
        if bounds is None:
            continue
        area = int((labels[bounds] == component_id).sum())
        if area < im.width * im.height * .003:
            continue
        sy, sx = bounds
        components.append((sx.start, sy.start, sx.stop, sy.stop, component_id))
    assert len(components) == 16, (filename, 'needs manual pose boundary review', len(components))
    # Rows can have figures extending beyond the equal-cell baseline. Group by
    # visual center, then sort actual actor silhouettes horizontally.
    components.sort(key=lambda r: (r[1]+r[3])/2)
    ordered = []
    for row in range(4):
        ordered += sorted(components[row*4:row*4+4], key=lambda r: (r[0]+r[2])/2)
    frames = {}
    for name, (x0, y0, x1, y1, component_id) in zip(NAMES, ordered):
        # Foot anchor derives from the lowest opaque body pixels, not the
        # weapon's width. All frames share the idle source-pixel scale.
        foot_band = (labels[max(y0,y1-50):y1, x0:x1] == component_id)
        xs = np.nonzero(foot_band)[1]
        # Include both feet, even when one shoe's sole sits a few pixels higher.
        # A median of only the bottommost scanlines snaps to the leading foot.
        anchor_x = x0 + (float(xs.min()) + float(xs.max())) / 2
        left, top = max(0,x0-2), max(0,y0-2)
        right, bottom = min(im.width,x1+2), min(im.height,y1+2)
        frames[name] = {'rect':[left,top,right-left,bottom-top],
                        'anchor':[round(anchor_x-left,2),y1-top],
                        'sourceBodyBounds':[x0,y0,x1-x0,y1-y0]}
        # A curled tail can wrap around transparent space whose rectangle also
        # includes another pose. Record the selected connected alpha silhouette
        # as render clipping metadata; the original PNG remains untouched.
        component = labels[top:bottom,left:right] == component_id
        clip = binary_dilation(component, iterations=1)
        foreign = (labels[top:bottom,left:right] != 0) & ~component
        clip &= ~foreign
        runs = []
        for yy, row_pixels in enumerate(clip):
            changes = np.diff(np.pad(row_pixels.astype(np.int8),(1,1)))
            for start, end in zip(np.where(changes==1)[0],np.where(changes==-1)[0]):
                runs.append([int(start),int(yy),int(end-start),1])
        frames[name]['clipRuns'] = runs
        frames[name]['clipPixelCount'] = int(clip.sum())
    return {'image':filename,'width':im.width,'height':im.height,'columns':4,'rows':4,
            'bodyHeight':ordered[0][3]-ordered[0][1], 'frames':frames,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'scope':'original generated key poses; side view and mirror only'}


normal = index_atlas('actors-normal-v1.png')
result = {'version':1,'scope':'standalone design preview; not game atlas registration',
          'image':normal['image'],'bodyHeight':normal['bodyHeight'],'frames':normal['frames'],
          'normal':normal}
curse_filename = 'actors-curse-v2.png' if (ROOT/'actors-curse-v2.png').exists() else 'actors-curse-v1.png'
if (ROOT/curse_filename).exists():
    result['curse'] = index_atlas(curse_filename)
(ROOT/'actors.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Indexed alpha bounds and foot anchors:', ', '.join(k for k in ('normal','curse') if k in result))
