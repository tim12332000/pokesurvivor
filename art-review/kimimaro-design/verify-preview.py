"""Browser evidence for the isolated Kimimaro design preview, not the game.

Starts its own localhost server so another worktree or an occupied review port
cannot accidentally provide the content under test. Requires existing Playwright
and Chrome; adds no dependencies and changes no game files.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import functools
import hashlib
import json
import math
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
from scipy.ndimage import label as connected_components


ROOT = Path(__file__).resolve().parents[2]
DESIGN = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / '.omx/state/kimimaro-final'
CHROME = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
SKILLS = ('willow', 'camellia', 'bullets', 'larch', 'vine', 'flower',
          'bracken', 'lily', 'combo', 'curse')
SHOT_TIMES = {'willow': .44, 'camellia': .57, 'bullets': .38, 'larch': .40,
              'vine': .54, 'flower': .58, 'bracken': .90, 'lily': .52,
              'combo': 1.12, 'curse': 1.10}
PHASE_TIMES = {'willow':(.08,.44,.63),'camellia':(.10,.57,.70),
               'bullets':(.10,.38,.55),'larch':(.10,.40,.66),
               'vine':(.16,.54,.68),'flower':(.20,.58,.78),
               'bracken':(.20,1.02,1.36),'lily':(.10,.52,.82),
               'combo':(.20,1.12,1.32),'curse':(.35,1.10,9.50)}
SOURCE_FILES = ('index.html','preview.css','preview-app.js','preview-scene.js','design-data.js','actors.json','effects.json','stage-assets.json')


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


@contextlib.contextmanager
def own_server():
    server = ThreadingHTTPServer(('127.0.0.1', 0),
        functools.partial(QuietHandler, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/art-review/kimimaro-design/'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def snapshot(page, skill=None, time=None, rank=1, quantity=0,
             form='normal', scenario='crowd'):
    return page.evaluate('''({skill,time,rank,quantity,form,scenario}) => {
      const p=window.KimimaroPreview, s=p.scene;
      p.pause();
      if(skill) p.selectSkill(skill);
      p.setRank(rank);p.setQuantity(quantity);p.setForm(form);p.setScenario(scenario);
      if(time!=null) p.setTime(time);
      s.draw();
      return s.getSnapshot();
    }''', dict(skill=skill, time=time, rank=rank, quantity=quantity,
               form=form, scenario=scenario))


def positive_hits(state):
    hits = state.get('hits')
    assert isinstance(hits, list), f'snapshot needs an actual hit ledger: {state}'
    return [hit for hit in hits if float(hit.get('damage', hit.get('amount', 0))) > 0]


def target_damage(state):
    targets = state.get('targets')
    assert isinstance(targets, list) and targets, f'missing target state: {state}'
    result = {}
    for target in targets:
        assert 'id' in target, target
        if 'hp' in target and 'maxHp' in target:
            result[str(target['id'])] = float(target['maxHp']) - float(target['hp'])
        elif 'damage' in target:
            result[str(target['id'])] = float(target['damage'])
        else:
            raise AssertionError(f'target needs verifiable HP or damage: {target}')
    return result


def hit_identity(hit):
    target = hit.get('targetId', hit.get('target'))
    if isinstance(target, dict):
        target = target.get('id')
    phase = hit.get('phase', hit.get('phaseId'))
    assert target is not None and phase is not None, f'hit missing target/phase: {hit}'
    return (str(phase), str(target))


def check_unique_hits(state):
    identities = [hit_identity(hit) for hit in positive_hits(state)]
    assert len(set(identities)) == len(identities), identities


def check_drill_contact(state, reach):
    """Compare actual draw geometry with the target, independently of HP hits."""
    weapon = state.get('weapon')
    assert weapon and weapon.get('kind') == 'bone-drill' and weapon.get('visible'), state
    base, tip = weapon['base'], weapon['tip']
    target = state['targets'][0]
    rendered = next((item for item in state.get('targetRenderSources',[]) if item['id']==target['id']), None)
    assert rendered and rendered.get('source') and rendered.get('visualBounds') and rendered.get('bodyCenter'), ('missing actual rendered target geometry',state)
    center = (rendered['bodyCenter']['x'],rendered['bodyCenter']['y'])
    bounds=rendered['visualBounds']
    vx,vy = tip['x']-base['x'],tip['y']-base['y']
    denominator = vx*vx+vy*vy
    assert denominator > 0, weapon
    projection = max(0,min(1,((center[0]-base['x'])*vx+(center[1]-base['y'])*vy)/denominator))
    nearest = (base['x']+projection*vx,base['y']+projection*vy)
    distance = math.hypot(center[0]-nearest[0],center[1]-nearest[1])
    # Use the sprite's actual alpha-bound body, not the old generic mannequin
    # chest offset or the larger gameplay collision radius.
    body_radius=min(bounds['right']-bounds['left'],bounds['bottom']-bounds['top'])/2
    assert distance <= body_radius+weapon['halfWidth'], (state['skill'],'solid drill does not touch visible sprite',distance,weapon,rendered)
    assert tip['x']-state['actor']['x'] >= reach*.85, (state['skill'],'visible drill is shorter than its attack reach',weapon,reach)
    return {'actual_sprite_body_center':center,'actual_sprite_bounds':bounds,
            'actual_sprite_source':rendered['source'],'distance_from_solid_drill':distance,'weapon':weapon,'expected_reach':reach}


def check_atlases():
    metadata = json.loads((DESIGN/'actors.json').read_text(encoding='utf8'))
    required = {'idle','run1','run2','run3','willow1','willow2','camellia1','camellia2',
                'bullets','larch','vine1','vine2','flower1','flower2','bracken','lily'}
    report = {}
    for form in ('normal','curse'):
        entry = metadata.get(form)
        assert entry and entry.get('image'), f'missing {form} atlas metadata'
        target = DESIGN/entry['image']
        with Image.open(target) as image:
            assert image.mode == 'RGBA', (target, image.mode)
            assert image.getchannel('A').getextrema() == (0,255), f'not genuine transparency: {target}'
            assert set(entry['frames']) == required, (form, entry['frames'].keys())
            # Check the original sheet, rather than labeling each crop: a small
            # tail/foot fragment inside one crop may belong to a large adjacent
            # pose. Its original connected component identifies that spill.
            alpha = np.asarray(image.getchannel('A')) > 40
            components, _ = connected_components(alpha, structure=np.ones((3,3), dtype=np.uint8))
            areas = np.bincount(components.ravel())
            major_threshold = alpha.size * .003
            major = [int(i) for i in np.flatnonzero(areas >= major_threshold) if i != 0]
            assert len(major) == len(required), (form, 'expected sixteen independent body poses', major)
            assigned = set()
            component_report = {}
            for name, frame in entry['frames'].items():
                x,y,w,h = frame['rect']
                ax,ay = frame['anchor']
                assert x>=0 and y>=0 and w>0 and h>0 and x+w<=image.width and y+h<=image.height, (name,frame)
                assert 0<=ax<=w and 0<=ay<=h, (name, frame)
                crop = components[y:y+h,x:x+w]
                raw_overlap = np.bincount(crop.ravel(), minlength=len(areas))
                runs = frame.get('clipRuns')
                assert isinstance(runs,list) and runs, (form,name,'missing component clip registration')
                mask = np.zeros((h,w),dtype=bool)
                for run in runs:
                    rx,ry,rw,rh = run
                    assert rx>=0 and ry>=0 and rw>0 and rh>0 and rx+rw<=w and ry+rh<=h, (form,name,run)
                    mask[ry:ry+rh,rx:rx+rw] = True
                assert int(mask.sum()) == frame['clipPixelCount'], (form,name,'incorrect clip pixel count')
                overlap = np.bincount(crop[mask], minlength=len(areas))
                bodies = sorted([(i,int(overlap[i]),int(areas[i])) for i in major if overlap[i] > 50],
                                key=lambda item: -item[1])
                assert len(bodies) == 1, (form,name,'clipped frame contains another major pose',bodies)
                component_id, contained, full_area = bodies[0]
                assert component_id not in assigned, (form,name,'one body reused by multiple frame crops')
                assert full_area-contained <= 50, (form,name,'frame clips its own body',contained,full_area)
                assigned.add(component_id)
                raw_foreign = {str(i):int(raw_overlap[i]) for i in major if i!=component_id and raw_overlap[i]>0}
                clipped_foreign = {str(i):int(overlap[i]) for i in major if i!=component_id and overlap[i]>0}
                assert not clipped_foreign, (form,name,'clip still includes a foreign major body',clipped_foreign)
                component_report[name] = {'component':component_id,'contained_pixels':contained,'full_pixels':full_area,
                    'raw_rectangle_foreign_pixels':raw_foreign,'clipped_foreign_pixels':clipped_foreign,
                    'clip_pixels':int(mask.sum()),'clip_runs':len(runs)}
            report[form] = {'image':entry['image'],'size':image.size,'frames':len(entry['frames']),
                            'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                            'major_component_threshold':major_threshold,'pose_components':component_report}
    return report


def check_effects():
    """Inspect the raster effect source, not only a renderer-ready boolean."""
    path = DESIGN/'effects.json'
    assert path.exists(), 'new bone VFX atlas metadata is not ready'
    entry = json.loads(path.read_text(encoding='utf8'))
    assert entry.get('image'), entry
    target = DESIGN/entry['image']
    assert target.exists(), target
    assert target.stat().st_size <= 256*1024, ('VFX atlas exceeds download budget',target.stat().st_size)
    required = {f'pillar{i}' for i in range(1,9)} | {'drill1','drill2','debris1','debris2'}
    assert required <= set(entry.get('frames',{})), entry.get('frames',{}).keys()
    crops = {}
    with Image.open(target) as image:
        assert image.mode == 'RGBA', (target,image.mode)
        assert image.width<=768 and image.height<=576, ('VFX atlas dimensions exceed budget',image.size)
        decoded_bytes=image.width*image.height*4
        assert decoded_bytes<=int(1.75*1024*1024), ('VFX decoded RGBA exceeds memory budget',decoded_bytes)
        alpha_extrema=image.getchannel('A').getextrema()
        assert alpha_extrema[0]==0 and alpha_extrema[1]>=240, (target,'requires clear transparent space and near-opaque bone',alpha_extrema)
        for name in sorted(required):
            frame=entry['frames'][name]
            x,y,w,h=frame['rect']
            ax,ay=frame['anchor']
            assert x>=0 and y>=0 and w>0 and h>0 and x+w<=image.width and y+h<=image.height, (name,frame)
            assert 0<=ax<=w and 0<=ay<=h, (name,frame)
            crop=image.crop((x,y,x+w,y+h))
            assert crop.getchannel('A').getbbox(), (name,'empty raster effect')
            crops[name]={'rect':frame['rect'],'anchor':frame['anchor'],
                         'pixel_sha256':hashlib.sha256(crop.tobytes()).hexdigest()}
    assert len({crops[f'pillar{i}']['pixel_sha256'] for i in range(1,9)})==8, 'pillar atlas repeats identical images'
    return {'image':entry['image'],'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'metadata_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':crops,
            'download_bytes':target.stat().st_size,'dimensions':image.size,'decoded_rgba_bytes':decoded_bytes,
            'alpha_extrema':alpha_extrema,
            'unloaded_original_candidates':[p.name for p in DESIGN.glob('effects*.png') if p.name!=target.name],
            'scope':'actual raster sources and registration; aesthetic quality requires screenshot review'}


def check_stage_assets():
    metadata=json.loads((DESIGN/'stage-assets.json').read_text(encoding='utf8'))
    assert metadata['pixelScale']==2 and set(metadata['normalIds'])=={'19','43'} and metadata['bossId']=='217', metadata
    assert {str(sprite['id']) for sprite in metadata['sprites']}=={'19','43','217'}, metadata
    images={};total=0
    for sprite in metadata['sprites']:
        for animation in ('idle','hurt'):
            frame=sprite[animation];path=DESIGN/frame['image'];source=ROOT/frame['source']
            assert path.is_file() and source.is_file(), (path,source)
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest==frame['sha256']==hashlib.sha256(source.read_bytes()).hexdigest(), ('stage sprite is not unchanged existing game art',frame)
            assert path.stat().st_size==frame['bytes'], frame
            with Image.open(path) as image:
                assert image.width>=frame['w']*frame['n'] and image.height>=frame['h']*frame['r'], (path,image.size,frame)
                alpha=image.convert('RGBA').getchannel('A')
                assert alpha.getextrema()[0]==0 and alpha.getextrema()[1]>240, path
                dimensions=image.size
            total+=frame['bytes']
            images[frame['image']]={'dex':str(sprite['id']),'animation':animation,'bytes':frame['bytes'],
                'sha256':digest,'size':dimensions,'source':frame['source']}
    assert len(images)==6, images
    props={}
    assert set(metadata.get('props',{}))=={'tree','rock','grass'}, metadata.get('props')
    for name,entry in metadata['props'].items():
        path=DESIGN/entry['image']
        assert path.is_file() and path.stat().st_size==entry['bytes'],entry
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],entry
        with Image.open(path) as image:
            assert image.size==(entry['width'],entry['height']),entry
            assert image.convert('RGBA').getchannel('A').getextrema()[0]==0,entry
        assert entry['source']==f'js/world/tiles.js::propSprite(0,{name},0)',entry
        total+=entry['bytes'];props[entry['image']]={**entry,'name':name}
    assert total==metadata['sourceTransferBytes'] and total<=24*1024, ('stage asset transfer budget',total)
    assert set(metadata['palette'])>={'floor','dirt','grass','rock'}, metadata
    return {'pixel_scale':2,'images':images,'props':props,'total_transfer_bytes':total,'palette':metadata['palette'],
            'scope':'six unchanged game sprite sheets and three existing game-code prop exports; cached procedural ground'}


def check_stage_prop_source(browser,stage):
    """Repaint original propSprite() in an isolated page and compare RGBA."""
    page=browser.new_page()
    try:
        page.set_content('<!doctype html><html><body></body></html>')
        page.evaluate('window.G={}')
        source_files=('js/core/util.js','js/world/tiles.js')
        for name in source_files:
            page.add_script_tag(content=(ROOT/name).read_text(encoding='utf8'))
        result={}
        for image,entry in stage['props'].items():
            raw=page.evaluate('''name=>{
              const c=G.Tiles.propSprite(0,name,0),ctx=c.getContext('2d');
              return {width:c.width,height:c.height,pixels:Array.from(ctx.getImageData(0,0,c.width,c.height).data)};
            }''',entry['name'])
            with Image.open(DESIGN/image) as png:
                rgba=png.convert('RGBA')
                assert rgba.size==(raw['width'],raw['height']),entry
                assert rgba.tobytes()==bytes(raw['pixels']),('prop PNG differs from actual game propSprite()',entry['name'])
            result[entry['name']]={'source':entry['source'],'rgba_sha256':hashlib.sha256(bytes(raw['pixels'])).hexdigest()}
        return {'props':result,'source_hashes':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_files}}
    finally:
        page.close()


def check_target_sprite_geometry(state):
    """Recompute rendered alpha bounds from the actual selected PNG frame."""
    assert state.get('stageAssetsLoaded') is True, state
    assert state.get('stagePixelScale')==2, state
    assert state.get('groundStyle')=='game-forest-pixel', state
    metadata=json.loads((DESIGN/'stage-assets.json').read_text(encoding='utf8'))
    expected_images={entry[animation]['image'] for entry in metadata['sprites'] for animation in ('idle','hurt')}
    expected_images.update(prop['image'] for prop in metadata['props'].values())
    sources=set(state.get('stageAssetSources',[]))
    assert len(sources)==len(expected_images), state.get('stageAssetSources')
    assert {Path(unquote(urlsplit(source).path)).name for source in sources}=={Path(image).name for image in expected_images}, sources
    definitions={str(sprite['id']):sprite for sprite in metadata['sprites']}
    rendered=state.get('targetRenderSources')
    assert rendered and len(rendered)==len(state['targets']), state
    result=[]
    for info in rendered:
        target=next(t for t in state['targets'] if t['id']==info['id'])
        assert info['source'] in state['stageAssetSources'] and info['dex'] in definitions, info
        frame=definitions[info['dex']][info['animation']]
        assert unquote(urlsplit(info['source']).path).endswith('/'+frame['image']), info
        assert 0<=info['frame']<frame['n'] and 0<=info['direction']<frame['r'], info
        with Image.open(DESIGN/frame['image']) as image:
            x=info['frame']*frame['w'];y=info['direction']*frame['h']
            alpha=np.asarray(image.convert('RGBA').getchannel('A').crop((x,y,x+frame['w'],y+frame['h'])))
            ys,xs=np.nonzero(alpha>=30)
            assert len(xs)>0, info
            scale=info['scale'];recoil=info['recoil']
            expected={'left':target['x']+recoil+(int(xs.min())-frame['ax'])*scale,
                      'right':target['x']+recoil+(int(xs.max())+1-frame['ax'])*scale,
                      'top':target['y']+(int(ys.min())-frame['ay'])*scale,
                      'bottom':target['y']+(int(ys.max())+1-frame['ay'])*scale}
        assert all(abs(info['visualBounds'][key]-value)<1e-6 for key,value in expected.items()), (info,expected)
        assert abs(info['bodyCenter']['x']-(expected['left']+expected['right'])/2)<1e-6, info
        assert abs(info['bodyCenter']['y']-(expected['top']+expected['bottom'])/2)<1e-6, info
        result.append({'target':info['id'],'dex':info['dex'],'animation':info['animation'],
                       'source':info['source'],'verified_alpha_bounds':expected})
    return result


def check_ground_palette(canvas_path, palette):
    """Confirm the actual rendered field contains the game's floor colors."""
    with Image.open(canvas_path) as image:
        pixels=np.asarray(image.convert('RGB'))
    colors=[tuple(bytes.fromhex(value.lstrip('#'))) for value in palette['floor']+palette['dirt']]
    matches=np.zeros(pixels.shape[:2],dtype=bool)
    coverage={}
    for color in colors:
        mask=np.all(pixels==np.array(color,dtype=np.uint8),axis=2)
        coverage['#'+bytes(color).hex()]=float(mask.mean())
        matches|=mask
    assert matches.mean()>=.10, ('game palette not visible in actual canvas',canvas_path,coverage)
    return {'exact_floor_palette_coverage':float(matches.mean()),'color_coverage':coverage,
            'mean_rgb':[float(n) for n in pixels.mean(axis=(0,1))],
            'scope':'actual canvas palette check, not a complete aesthetic verdict'}


def check_forest_layout(state, repeat):
    """Reject the former three equal-radius rings using independent geometry."""
    layout=state.get('forestLayout')
    assert isinstance(layout,list) and 32<=len(layout)<=36, ('forest must respect 32-36 pillar budget',layout)
    assert state.get('effectsLoaded') is True and state.get('effectSource'), state
    assert layout==repeat.get('forestLayout'), 'forest flickers or reseeds at the same scrub time'
    budget=state.get('vfxBudget')
    assert budget and budget['forestCount']==len(layout) and budget['maxForestColumns']==36, budget
    assert 0<=budget['activeParticleCount']<=20 and budget['maxSecondaryParticles']==20, budget
    center=state.get('forestCenter')
    radius=state.get('forestRadius')
    assert center and radius and radius>0, state
    radii=[];angles=[];heights=[];widths=[];leans=[]
    for column in layout:
        assert all(key in column for key in ('x','y','height','width','lean','wave','variant','start','grow','opacity','visible')), column
        radial=math.hypot(column['x']-center['x'],column['y']-center['y'])
        assert radial<=radius+1e-5, ('bone root outside actual attack circle',column,radial,radius)
        assert column['height']>0 and column['width']>0 and 0<=column['opacity']<=1 and 0<=column['grow']<=1, column
        radii.append(radial);angles.append(math.atan2(column['y']-center['y'],column['x']-center['x']))
        heights.append(column['height']);widths.append(column['width']);leans.append(column['lean'])
    assert len({round(v,1) for v in radii})>=20, ('still arranged in radius rings',radii)
    assert len({round(v,1) for v in heights})>=12 and max(heights)/min(heights)>1.8, heights
    assert len({round(v,1) for v in widths})>=8 and max(widths)/min(widths)>1.4, widths
    assert min(leans)<0<max(leans) and len({round(v,2) for v in leans})>=15, leans
    angles.sort()
    gaps=[b-a for a,b in zip(angles,angles[1:])]+[angles[0]+2*math.pi-angles[-1]]
    assert max(gaps)>min(gaps)*2 and np.std(gaps)>.01, ('equal angular spacing',gaps)
    assert len({column['variant'] for column in layout})>=6, 'not using varied bone silhouettes'
    assert len({column['wave'] for column in layout})==3, 'wave timing was discarded'
    return {'count':len(layout),'seed':state.get('forestSeed'),
            'distinct_radii_rounded_01':len({round(v,1) for v in radii}),
            'height_range':[min(heights),max(heights)],'width_range':[min(widths),max(widths)],
            'lean_range':[min(leans),max(leans)],'angular_gap_std':float(np.std(gaps)),
            'variants':sorted({column['variant'] for column in layout}),
            'vfx_budget':budget,
            'same_time_repeat':'identical','scope':'layout irregularity and real VFX source, not an aesthetic verdict'}


def dom_controls(page, report):
    """Exercise native visible controls; IDs are checked against the final UI."""
    report['controls'] = page.evaluate('''() => [...document.querySelectorAll('button,input,select')]
      .map(el=>({id:el.id,type:el.type,tag:el.tagName,text:el.textContent.trim().slice(0,50)}))''')
    assert page.get_by_role('button').count() >= 10, 'missing skill/playback controls'
    page.locator('#skill-nav button[data-skill="willow"]').click()
    page.evaluate('KimimaroPreview.pause();KimimaroPreview.setTime(0)')
    page.locator('#rank-select').select_option('5')
    assert page.locator('#rank-select').input_value() == '5'
    page.locator('#quantity-input').evaluate('''el => {
      el.value='1';el.dispatchEvent(new Event('input',{bubbles:true}));
    }''')
    assert page.locator('#quantity-value').inner_text().strip() == '1'
    page.locator('#form-options button[data-form="curse"]').click()
    assert page.locator('#form-options button[data-form="curse"]').get_attribute('aria-pressed') == 'true'
    page.locator('#scenario-options button[data-scenario="boss"]').click()
    assert page.locator('#scenario-options button[data-scenario="boss"]').get_attribute('aria-pressed') == 'true'
    page.locator('#speed-select').select_option('0.5')
    page.locator('#range-toggle').check()
    assert page.locator('#range-toggle').is_checked()
    page.locator('#sound-button').click()
    assert page.locator('#sound-button').get_attribute('aria-pressed') == 'true'
    page.wait_for_function('KimimaroPreview.audioContextState === "running"')
    report['audio'] = {'enabled_context': page.evaluate('KimimaroPreview.audioContextState'),
                       'scope': 'browser-generated design audio; not licensed game sound assets'}
    page.locator('#sound-button').click()
    assert page.locator('#sound-button').get_attribute('aria-pressed') == 'false'
    page.locator('#timeline').evaluate('''el => {
      el.value='.2';el.dispatchEvent(new Event('input',{bubbles:true}));
    }''')
    assert abs(page.evaluate('KimimaroPreview.scene.getSnapshot().time') - .2) < .002
    before = page.evaluate('KimimaroPreview.scene.getSnapshot().time')
    page.wait_for_timeout(180)
    after = page.evaluate('KimimaroPreview.scene.getSnapshot().time')
    assert before == after, (before, after)
    page.locator('#play-button').click()
    page.wait_for_timeout(180)
    advanced = page.evaluate('KimimaroPreview.scene.getSnapshot().time')
    page.locator('#play-button').click()
    assert advanced > after, (after, advanced)
    report['play_pause'] = {'paused_time': after, 'advanced_time': advanced}
    page.locator('#replay-button').click()
    page.evaluate('KimimaroPreview.pause()')
    assert page.evaluate('KimimaroPreview.scene.getSnapshot().time') < .2
    page.locator('#loop-toggle').uncheck()
    assert not page.locator('#loop-toggle').is_checked()
    page.locator('#loop-toggle').check()
    page.locator('#range-toggle').uncheck()
    page.locator('#rank-select').select_option('1')
    page.locator('#speed-select').select_option('1')
    page.locator('#form-options button[data-form="normal"]').click()
    page.locator('#scenario-options button[data-scenario="crowd"]').click()


def verify_viewport(browser, out, label, viewport, mobile):
    context = browser.new_context(viewport=viewport, is_mobile=mobile,
                                  has_touch=mobile, service_workers='block')
    page = context.new_page()
    report = {'page_errors': [], 'http_errors': [], 'request_failures': [], 'skills': {}, 'image_requests':[]}
    page.on('pageerror', lambda error: report['page_errors'].append(str(error)))
    page.on('response', lambda response: report['http_errors'].append(
        {'status': response.status, 'url': response.url}) if response.status >= 400 else None)
    page.on('requestfailed', lambda req: report['request_failures'].append(
        {'url': req.url, 'failure': req.failure}))
    page.on('request', lambda req: report['image_requests'].append(req.url)
        if req.url.split('?')[0].lower().endswith('.png') else None)
    with own_server() as url:
        page.goto(url, wait_until='networkidle')
        page.wait_for_function('window.KimimaroPreview?.ready === true', timeout=20000)
        page.evaluate('KimimaroPreview.pause()')
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), label
        report['loaded_assets'] = page.evaluate('''() => ({
          data:!!window.KIMIMARO_DESIGN,
          atlas:window.KimimaroPreview.scene.getSnapshot().assetStatus,
          actors:window.KimimaroPreview.scene.getSnapshot().actorsLoaded,
          effectsLoaded:window.KimimaroPreview.scene.getSnapshot().effectsLoaded,
          effectSource:window.KimimaroPreview.scene.getSnapshot().effectSource,
          stageAssetsLoaded:window.KimimaroPreview.scene.getSnapshot().stageAssetsLoaded,
          stageAssetSources:window.KimimaroPreview.scene.getSnapshot().stageAssetSources,
          images:[...document.images].map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0}))
        })''')
        assert report['loaded_assets']['data'], 'missing authoritative design data'
        assert report['loaded_assets']['atlas'] == 'loaded', report['loaded_assets']
        assert set(report['loaded_assets']['actors']) == {'normal', 'curse'}, report['loaded_assets']
        assert report['loaded_assets']['effectsLoaded'] is True and report['loaded_assets']['effectSource'], report['loaded_assets']
        assert report['loaded_assets']['stageAssetsLoaded'] is True and len(set(report['loaded_assets']['stageAssetSources']))==9, report['loaded_assets']
        effects=check_effects()
        requested={url.split('?')[0].rsplit('/',1)[-1] for url in report['image_requests']}
        assert effects['image'] in requested, ('registered optimized VFX atlas was not requested',requested)
        assert not requested.intersection(effects['unloaded_original_candidates']), ('unoptimized VFX original requested',requested)
        report['vfx_asset_budget']={'runtime_image':effects['image'],'download_bytes':effects['download_bytes'],
            'decoded_rgba_bytes':effects['decoded_rgba_bytes'],'originals_not_loaded':effects['unloaded_original_candidates']}
        stage=check_stage_assets()
        assert all(Path(name).name in requested for name in list(stage['images'])+list(stage['props'])), ('some registered game sprites/props were not actually requested',requested)
        report['stage_asset_budget']=stage
        dom_controls(page, report)
        report['default_camera']={}
        report['phase_screenshots']={}
        default_zoom=1.72 if page.locator('#preview-canvas').bounding_box()['width']<600 else 1.32

        for skill in SKILLS:
            initial = snapshot(page, skill, 0)
            assert not positive_hits(initial), (skill, 'damage before windup', initial)
            impact = snapshot(page, skill, SHOT_TIMES[skill])
            assert impact.get('clipApplied') is True, (skill,'registered source-body clip is not rendered',impact)
            budget=impact.get('vfxBudget')
            assert budget and 0<=budget['activeParticleCount']<=20, (skill,'secondary particle budget exceeded',budget)
            assert budget['forestCount']<=36, (skill,'forest column budget exceeded',budget)
            report.setdefault('actual_target_sprite_geometry',{})[skill]=check_target_sprite_geometry(impact)
            camera=page.evaluate('KimimaroPreview.scene.cameraFrame()')
            assert abs(camera['zoom']-default_zoom)<1e-9, (skill,'default study camera changed scale',camera,default_zoom)
            report['default_camera'][skill]=camera
            page.screenshot(path=str(out / f'{label}-{skill}.png'), full_page=True)
            phase_shots=[]
            for phase_name,time in zip(('preparation','execution','recovery'),PHASE_TIMES[skill]):
                phase_state=snapshot(page,skill,time)
                page_shot=out/f'{label}-{skill}-{phase_name}.png'
                canvas_shot=out/f'{label}-{skill}-{phase_name}-canvas.png'
                page.screenshot(path=str(page_shot),full_page=True)
                page.locator('#preview-canvas').screenshot(path=str(canvas_shot))
                if skill=='willow' and phase_name=='preparation':
                    report['actual_ground_palette']=check_ground_palette(canvas_shot,stage['palette'])
                phase_shots.append({'phase':phase_name,'time':time,'page':page_shot.name,'canvas':canvas_shot.name,
                    'actor_source':phase_state['actorSource'],'pose':phase_state['pose'],
                    'targets':check_target_sprite_geometry(phase_state)})
            report['phase_screenshots'][skill]=phase_shots
            complete = snapshot(page, skill, 12 if skill == 'curse' else 3)
            assert complete.get('skill') == skill, complete
            check_unique_hits(complete)
            if skill != 'curse':
                assert positive_hits(complete), (skill, 'no visible target damage', complete)
                assert sum(target_damage(complete).values()) > 0, complete
            report['skills'][skill] = {'initial': initial, 'impact': impact, 'complete': complete}

        for skill in ('willow', 'bullets'):
            base = snapshot(page, skill, 3, quantity=0)
            one = snapshot(page, skill, 3, quantity=1)
            high = snapshot(page, skill, 3, quantity=5)
            assert sum(target_damage(one).values()) > sum(target_damage(base).values()), skill
            assert sum(target_damage(high).values()) >= sum(target_damage(one).values()), skill
            report.setdefault('quantity', {})[skill] = {'q0': base, 'q1': one, 'q5': high}

        for skill in ('bracken', 'lily'):
            state = snapshot(page, skill, 3)
            damage = target_damage(state)
            assert len([n for n in damage.values() if n > 0]) >= 3, (skill, damage)
            assert any(n == 0 for n in damage.values()), (skill, 'outside target was hit', damage)
            assert all(damage[str(t['id'])] == 0 for t in state['targets'] if t['outside']), state
            assert all(damage[str(t['id'])] > 0 for t in state['targets'] if not t['outside']), state
            report.setdefault('aoe', {})[skill] = state

        boss = snapshot(page, 'bracken', 3, scenario='boss')
        boss_targets = [t for t in boss['targets'] if t.get('boss')]
        assert boss_targets, boss
        boss_damage = target_damage(boss)
        assert any(boss_damage[str(t['id'])] > 0 for t in boss_targets), boss
        assert any(t.get('flying') for t in boss_targets), 'does not cover the game boss flag'
        report['boss_bracken'] = boss
        report['boss_actual_sprite_geometry']=check_target_sprite_geometry(boss)
        snapshot(page,'bracken',1.02,rank=5)
        page.locator('#range-toggle').check()
        diagnostic_camera=page.evaluate('KimimaroPreview.scene.cameraFrame()')
        assert diagnostic_camera['zoom']<=default_zoom, ('diagnostic range zoom must not enlarge the field',diagnostic_camera)
        report['diagnostic_range_camera']=diagnostic_camera
        page.locator('#range-toggle').uncheck()

        forest = snapshot(page,'bracken',1.02,rank=5)
        repeated = snapshot(page,'bracken',1.02,rank=5)
        report['irregular_forest'] = check_forest_layout(forest,repeated)
        report['forest_visual_samples'] = {}
        for time in (.50,.70,1.02,1.16):
            sample=snapshot(page,'bracken',time,rank=5)
            assert sample.get('renderedForm')=='normal' and sample.get('clipApplied'), sample
            assert sample.get('effectsLoaded') is True, sample
            # Screenshots, rather than a self-reported visibility boolean, are
            # the authoritative evidence for hero readability and occlusion.
            shot=out/f'{label}-vfx-bracken-{time:.2f}.png'
            canvas_shot=out/f'{label}-vfx-bracken-{time:.2f}-canvas.png'
            page.screenshot(path=str(shot),full_page=True)
            page.locator('#preview-canvas').screenshot(path=str(canvas_shot))
            visible=[column for column in sample['forestLayout'] if column['visible']]
            report['forest_visual_samples'][str(time)]={'page':shot.name,'canvas':canvas_shot.name,
                'actual_actor_source':sample['actorSource'],'visible_columns':len(visible),
                'lower_opacity_columns':sum(column['opacity']<.5 for column in visible),
                'requires_manual_visual_verdict':True}
        samples=page.evaluate('''()=>{
          const p=KimimaroPreview;p.pause();p.selectSkill('bracken');p.setRank(5);p.pause();
          const samples=[];
          for(let i=0;i<=90;i++){
            const t=i/60;p.scene.setTime(t);p.scene.draw();
            const s=p.scene.getSnapshot();samples.push({time:t,budget:s.vfxBudget});
          }return samples;
        }''')
        assert all(s['budget'] and s['budget']['forestCount']<=36 and 0<=s['budget']['activeParticleCount']<=20 for s in samples), samples
        report['vfx_timeline_budget']={'samples':samples,
            'peak_secondary_particles':max(s['budget']['activeParticleCount'] for s in samples),
            'peak_forest_columns':max(s['budget']['forestCount'] for s in samples)}
        # Actual autoplay responsiveness, deliberately not presented as a game
        # FPS benchmark: verify time advances and browser RAF/control work.
        response=page.evaluate('''async()=>{
          const p=KimimaroPreview;p.selectSkill('bracken');p.setRank(5);p.setTime(0);p.play();
          const start=performance.now();let frames=0,last=start,maxGap=0;
          await new Promise(resolve=>{
            const tick=now=>{frames++;maxGap=Math.max(maxGap,now-last);last=now;
              if(now-start>=1000)resolve();else requestAnimationFrame(tick);};
            requestAnimationFrame(tick);
          });
          const advanced=p.scene.getSnapshot().time;p.pause();
          return {elapsed_ms:performance.now()-start,frames,max_raf_gap_ms:maxGap,advanced};
        }''')
        assert response['frames']>=2 and response['advanced']>.10, ('playback is unresponsive',response)
        report['vfx_playback_responsiveness']={**response,'scope':'headless preview responsiveness only; not actual-game FPS or device performance'}

        rank1 = snapshot(page, 'flower', 3, rank=1)
        rank5 = snapshot(page, 'flower', 3, rank=5)
        assert abs(sum(target_damage(rank5).values()) / sum(target_damage(rank1).values()) - 2) < 1e-6
        report['rank_scaling'] = {'rank1': rank1, 'rank5': rank5}

        report['cancellation'] = {}
        for skill, cancel_at in [('flower', .50), ('lily', .40), ('bullets', .25), ('bracken', .70)]:
            snapshot(page, skill, cancel_at)
            state = page.evaluate('''() => {
              const s=KimimaroPreview.scene;s.cancel();s.setTime(3);s.draw();return s.getSnapshot();
            }''')
            assert state.get('cancelled') is True, state
            hits = positive_hits(state)
            if skill == 'flower':
                assert not hits, state
            elif skill == 'lily':
                assert hits and {str(hit['phase']) for hit in hits} == {'0'}, state
            elif skill == 'bullets':
                releases = [e for e in state['events'] if e.get('type') == 'release']
                assert len(releases) == 2 and len(hits) == 2, state
                assert all(hit['time'] > cancel_at for hit in hits), state
            elif skill == 'bracken':
                assert hits and all(hit.get('wave', 0) <= 2 for hit in hits), state
                assert target_damage(state)['target-3'] == 0, state
            report['cancellation'][skill] = state

        curse_before = snapshot(page, 'curse', .45)
        curse_active = snapshot(page, 'curse', 1.10)
        curse_after = snapshot(page, 'curse', 9.10)
        assert curse_before['form'] == 'normal' and curse_active['form'] == 'curse' and curse_after['form'] == 'normal'
        assert curse_active['renderedForm'] == 'curse' and curse_active.get('actorSource'), curse_active
        report['transformation'] = {'before': curse_before, 'active': curse_active, 'after': curse_after}
        cursed_attack = snapshot(page, 'flower', .58, form='curse')
        assert cursed_attack['form'] == 'curse' and positive_hits(cursed_attack), cursed_attack
        assert cursed_attack['renderedForm'] == 'curse' and cursed_attack.get('actorSource'), cursed_attack
        assert cursed_attack.get('clipApplied') is True, cursed_attack
        assert cursed_attack['actorSource'] != rank1.get('actorSource'), 'curse form is not using a distinct atlas'
        page.screenshot(path=str(out / f'{label}-curse-flower.png'), full_page=True)
        report['cursed_attack'] = cursed_attack

        report['all_cursed_attacks'] = {}
        for skill in SKILLS[:8]:
            impact = snapshot(page, skill, SHOT_TIMES[skill], form='curse')
            assert impact['renderedForm'] == 'curse' and impact.get('clipApplied') is True, impact
            assert impact['actorSource'] != rank1.get('actorSource'), impact
            page.screenshot(path=str(out / f'{label}-curse-{skill}.png'), full_page=True)
            complete = snapshot(page, skill, 3, form='curse')
            assert positive_hits(complete), complete
            check_unique_hits(complete)
            report['all_cursed_attacks'][skill] = {'impact':impact,'complete':complete}

        report['solid_drill_contact'] = {}
        for skill,time in [('flower',.58),('combo',1.12)]:
            for form in ('normal','curse'):
                for scenario in ('crowd','boss'):
                    state = snapshot(page,skill,time,form=form,scenario=scenario)
                    report['solid_drill_contact'][f'{skill}-{form}-{scenario}'] = check_drill_contact(state,135)
                    check_target_sprite_geometry(state)

        for skill, hit_time in [('flower', .58), ('vine', .42), ('camellia', .30)]:
            before = snapshot(page, skill, hit_time-.001)
            after = snapshot(page, skill, hit_time+.001)
            assert sum(target_damage(after).values()) > sum(target_damage(before).values()), skill
            report.setdefault('contact_timing', {})[skill] = {'before': before, 'after': after}

        snapshot(page, 'combo', .9, rank=5, quantity=5, form='curse')
        snapshot(page, 'willow', 0, rank=1, quantity=0, form='normal')
        reset = page.evaluate('''() => {KimimaroPreview.scene.reset();return KimimaroPreview.scene.getSnapshot()}''')
        assert not positive_hits(reset), reset
        report['reset'] = reset
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), label
        assert not report['page_errors'], report['page_errors']
        assert not report['http_errors'], report['http_errors']
        assert not report['request_failures'], report['request_failures']
    context.close()
    return report


def record_reel(browser):
    """Capture the actual preview canvas with its own title and hit display.

    The reel is silent: synthetic design audio remains available in the page.
    No source video, game sound, generated-frame interpolation or other imagery
    is substituted for the rendered browser output.
    """
    context = browser.new_context(viewport={'width': 1440, 'height': 1050},
                                  service_workers='block')
    page = context.new_page()
    with own_server() as url:
        page.goto(url, wait_until='networkidle')
        page.wait_for_function('window.KimimaroPreview?.ready === true')
        captured = page.evaluate('''async () => {
          const p=KimimaroPreview;p.pause();
          const canvas=document.querySelector('#preview-canvas');
          const stream=canvas.captureStream(30);
          const mime=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm']
            .find(type=>MediaRecorder.isTypeSupported(type));
          if(!mime) throw new Error('No native WebM recorder is available');
          const chunks=[],recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:3500000});
          recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
          const stopped=new Promise(resolve=>recorder.onstop=resolve);
          recorder.start();
          const cases=[
            {id:'willow',rank:3,q:4},{id:'camellia',rank:3,q:0},
            {id:'bullets',rank:3,q:5},{id:'larch',rank:3,q:0},
            {id:'vine',rank:3,q:0},{id:'flower',rank:3,q:0},
            {id:'bracken',rank:3,q:0},{id:'lily',rank:3,q:0},
            {id:'curse',rank:3,q:0},{id:'combo',rank:3,q:0,form:'curse'}
          ];
          let elapsed=0;
          for(const entry of cases){
            p.selectSkill(entry.id);p.setRank(entry.rank);p.setQuantity(entry.q);
            p.setForm(entry.form||'normal');p.setScenario('crowd');p.setTime(0);
            const duration=entry.id==='curse'?9.5:Math.max(1.25,p.scene.duration+.50);
            entry.duration=duration;entry.start=elapsed;elapsed+=duration;
            const start=performance.now();
            await new Promise(resolve=>{
              const frame=()=>{
                const t=Math.min(duration,(performance.now()-start)/1000);
                p.setTime(t);p.scene.draw();
                if(t>=duration)resolve();else requestAnimationFrame(frame);
              };requestAnimationFrame(frame);
            });
          }
          recorder.stop();await stopped;stream.getTracks().forEach(track=>track.stop());
          const blob=new Blob(chunks,{type:mime}),bytes=new Uint8Array(await blob.arrayBuffer());
          let binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));
          return {mime,data:btoa(binary),bytes:bytes.length,duration:elapsed,cases,
            assets:p.scene.getSnapshot().actorsLoaded,scope:'silent recording of standalone design preview'};
        }''')
    context.close()
    evidence = DESIGN/'evidence'
    evidence.mkdir(exist_ok=True)
    target = evidence/'kimimaro-motion-reel.webm'
    target.write_bytes(base64.b64decode(captured.pop('data')))
    captured['file'] = str(target.relative_to(ROOT))
    captured['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    assert target.stat().st_size > 100000, 'recording is unexpectedly empty'
    (evidence/'motion-reel.json').write_text(json.dumps(captured,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return captured


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--record', action='store_true', help='also export a silent browser-canvas WebM reel')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'standalone animated design preview only; not game balance or integration',
              'viewports': {}, 'status': 'running'}
    try:
        assert (DESIGN / 'index.html').exists(), 'preview index.html is not ready'
        assert CHROME.exists(), f'existing Chrome missing: {CHROME}'
        report['atlas_validation'] = check_atlases()
        report['effects_validation'] = check_effects()
        report['stage_asset_validation'] = check_stage_assets()
        initial_hashes = {name:hashlib.sha256((DESIGN/name).read_bytes()).hexdigest() for name in SOURCE_FILES}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=str(CHROME), headless=True)
            report['original_stage_prop_pixels']=check_stage_prop_source(browser,report['stage_asset_validation'])
            for label, viewport, mobile in [
                ('desktop', {'width': 1440, 'height': 1050}, False),
                ('mobile', {'width': 390, 'height': 844}, True),
                ('mobile-landscape', {'width': 844, 'height': 390}, True),
            ]:
                report['viewports'][label] = verify_viewport(browser, args.out, label, viewport, mobile)
            if args.record:
                report['reel'] = record_reel(browser)
            browser.close()
        for name,digest in initial_hashes.items():
            assert hashlib.sha256((DESIGN/name).read_bytes()).hexdigest() == digest, ('preview source changed during capture',name)
        for atlas in report['atlas_validation'].values():
            assert hashlib.sha256((DESIGN/atlas['image']).read_bytes()).hexdigest() == atlas['sha256'], ('atlas changed during capture',atlas['image'])
        effect = report['effects_validation']
        assert hashlib.sha256((DESIGN/effect['image']).read_bytes()).hexdigest() == effect['sha256'], ('VFX atlas changed during capture',effect['image'])
        for name,sprite in report['stage_asset_validation']['images'].items():
            assert hashlib.sha256((DESIGN/name).read_bytes()).hexdigest()==sprite['sha256'], ('stage sprite changed during capture',name)
        for name,prop in report['stage_asset_validation']['props'].items():
            assert hashlib.sha256((DESIGN/name).read_bytes()).hexdigest()==prop['sha256'], ('stage prop changed during capture',name)
        for name,digest in report['original_stage_prop_pixels']['source_hashes'].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, ('original game prop code changed during capture',name)
        report['post_capture_source_hash_audit'] = 'pass: preview sources and atlas images did not change during verification'
        report['status'] = 'pass'
    except Exception as error:
        report['status'] = 'fail'
        report['error'] = repr(error)
        raise
    finally:
        report['file_hashes'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for name in SOURCE_FILES
            if (p := DESIGN/name).exists()}
        serialized = json.dumps(report, ensure_ascii=False, indent=2)+'\n'
        (args.out/'verification.json').write_text(serialized, encoding='utf8')
        if report['status'] == 'pass':
            (DESIGN/'evidence').mkdir(exist_ok=True)
            (DESIGN/'evidence/verification.json').write_text(serialized,encoding='utf8')
    print('PASS: desktop/mobile preview, eight attacks, combo, curse, quantity/rank, AOE bounds, boss flag and contact timing.')


if __name__ == '__main__':
    main()
