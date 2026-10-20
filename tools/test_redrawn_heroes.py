"""Source-audited browser evidence for the authored, unified hero atlases.

Uses actual game casts and actor renderers; no substituted art or simulation.
Run with the lab server on 8318. Evidence remains outside reviewed assets.
"""
import base64
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
import test_animation_complete as acceptance

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / '.omx/state/redrawn-heroes'

AUDIT = r"""() => {
  const original=CanvasRenderingContext2D.prototype.drawImage, origins=new WeakMap();
  const sourceOf=image=>image.src?[image.src]:image.dataset?.source?
    [new URL(image.dataset.source,parent.location.href).href]:origins.get(image)||[];
  CanvasRenderingContext2D.prototype.drawImage=function(image,...args){
    const sources=sourceOf(image);
    const previous=origins.get(this.canvas)||[];
    origins.set(this.canvas,[...new Set([...previous,...sources])]);
    return original.call(this,image,...args);
  };
  const render=Acceptance.render;
  Acceptance.render=function(anim=Acceptance.p().anim,opts={}){
    const sources=[],saved=CanvasRenderingContext2D.prototype.drawImage;
    CanvasRenderingContext2D.prototype.drawImage=function(image,...args){
      sources.push(...sourceOf(image));
      return saved.call(this,image,...args);
    };
    let result;try{result=render(anim,opts)}finally{CanvasRenderingContext2D.prototype.drawImage=saved}
    result.sources=[...new Set(sources)];
    result.form=G.KyuubiForm?.poseFor(anim)||null;
    result.options={flash:!!opts.flash,alpha:opts.alpha??1};
    Acceptance.assert(result.sources.length,'no traceable actor image');
    Acceptance.assert(result.sources.every(s=>new URL(s).pathname.includes('/art-review/redrawn/')),
      'legacy actor image rendered: '+result.sources.join(','));
    return result;
  };
}"""


def save(name, result, report):
    data = base64.b64decode(result.pop('png').split(',', 1)[1])
    path = OUT / f'{name}.png'
    path.write_bytes(data)
    report['poses'][name] = result
    return result


def static_checks():
    metadata = json.loads((ROOT / 'art-review/animation-assets.json').read_text('utf-8'))
    sources = {item['source'] for item in metadata.values()}
    sources.add(json.loads((ROOT / 'art-review/kyuubi-frames.json').read_text('utf-8'))['source'])
    assert all('redrawn/' in source for source in sources), sources
    generated = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (ROOT / 'art-review/redrawn').glob('*.png')}
    assert len(set(generated.values())) == len(generated), 'duplicate atlas bytes'
    # A new filename must never conceal a byte-for-byte original sprite sheet.
    legacy = {hashlib.sha256(p.read_bytes()).hexdigest(): str(p.relative_to(ROOT))
              for folder in ['assets', '.omx/naruto', 'art-review/candidates',
                             'art-review/reference', 'art-review/references']
              for p in (ROOT / folder).rglob('*.png') if (ROOT / folder).exists()}
    assert not (set(generated.values()) & set(legacy)), 'copied reference bytes'
    provenance_path = ROOT / 'art-review/redrawn/provenance.json'
    assert provenance_path.exists(), 'authorship/provenance record missing'
    provenance = json.loads(provenance_path.read_text('utf-8'))
    assert provenance, 'empty provenance record'
    provenance_text = json.dumps(provenance)
    for source in sources:
        digest = generated[Path(source).name]
        assert digest in provenance_text, f'provenance hash does not match {source}'
    return {'metadataSources': sorted(sources), 'sha256': generated, 'provenance': provenance}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'poses': {}, 'errors': [], 'failedRequests': [], 'static': static_checks()}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=acceptance.CHROME, headless=True)
        for mobile in [False, True]:
            label = 'mobile' if mobile else 'desktop'
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else
                                          {'width': 1200, 'height': 900}, is_mobile=mobile,
                                          has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.on('response', lambda r: report['failedRequests'].append(r.url)
                    if r.status >= 400 else None)
            page.goto(acceptance.BASE)
            acceptance.wait_ready(page, report)
            boot = page.frame_locator('#game').locator('#tap-start')
            if boot.is_visible():
                boot.click()
            for dex, hero in [(30001, 'naruto'), (30002, 'sasuke')]:
                frame = acceptance.start(page, dex)
                frame.evaluate(AUDIT)
                frame.evaluate('Acceptance.arena()')
                if dex == 30001:
                    # Explicit same-frame controls prove the atlas scale/palette
                    # is identical on both viewports. Live animation ages below
                    # may legitimately differ by one browser presentation tick.
                    references = frame.evaluate('''() => parent.AnimationAssets.keys.map(key=>{
                      const assets=parent.AnimationAssets,asset=assets.get(key);
                      const cv=document.createElement('canvas');cv.width=240;cv.height=200;
                      const ctx=cv.getContext('2d',{willReadFrequently:true});
                      Acceptance.assert(assets.draw(ctx,key,0,120,150,{scale:1}),key);
                      return {key,pose:{state:{key,frame:0},sources:[asset.image.src],
                        fixedReference:true,png:cv.toDataURL()}};
                    })''')
                    for reference in references:
                        save(f'{label}-fixed-{reference["key"]}', reference['pose'], report)
                # Use the actual menu sprite constructor and the returned preview
                # animator, rather than re-labelling the player's body a preview.
                save(f'{label}-{hero}-preview', frame.evaluate('''() => {
                  const cv=document.createElement('canvas');cv.width=240;cv.height=200;
                  document.body.append(cv);const preview=G.UI.sprite(cv,Acceptance.p().dex,{shadow:false});
                  const result=Acceptance.render(preview.a);cv.remove();return result;}'''), report)
                for direction, key in [('right', 'KeyD'), ('down', 'KeyS'), ('left', 'KeyA'), ('up', 'KeyW')]:
                    page.locator('#game').focus()
                    page.keyboard.down(key)
                    pose = frame.evaluate('''() => {Acceptance.resume();Acceptance.p().update(.08);
                      Acceptance.pause();Acceptance.assert(Acceptance.p().walking,'keyboard movement missing');
                      return Acceptance.render()}''')
                    page.keyboard.up(key)
                    assert pose['state']['direction'] == direction, pose
                    save(f'{label}-{hero}-move-{direction}', pose, report)
                    frame.evaluate('Acceptance.resume();Acceptance.p().update(.08);Acceptance.pause()')
                    save(f'{label}-{hero}-idle-{direction}', frame.evaluate('Acceptance.render()'), report)
                frame.evaluate('Acceptance.arena();Acceptance.resume();Acceptance.p().hurt(5,null,true);Acceptance.pause()')
                for name, options in [('hurt', '{}'), ('flash', '{flash:true,alpha:.5}')]:
                    save(f'{label}-{hero}-{name}', frame.evaluate(f'Acceptance.render(Acceptance.p().anim,{options})'), report)
                primary = frame.evaluate('G.NarutoSkillCatalog.byDex.get(G.Game.player.dex).id')
                ids = ([primary, 'naruto-naruto', 'naruto-rasenshuriken', 'naruto-nine-tails-cloak']
                       if dex == 30001 else [primary, 'naruto-fireball', 'naruto-fuma-shuriken',
                                             'naruto-kusanagi', 'naruto-sharingan'])
                ids += ['naruto-kunai', 'naruto-shuriken']
                for skill in ids:
                    frame.evaluate('Acceptance.arena()')
                    frame.evaluate('(id)=>Acceptance.cast(id)', skill)
                    previous = 0
                    phases = []
                    for age in [0, .06, .14, .28, .46, .8]:
                        frame.evaluate('(dt)=>Acceptance.step(dt)', age - previous)
                        previous = age
                        pose = frame.evaluate('Acceptance.render()')
                        phases.append(pose)
                        save(f'{label}-{hero}-{skill}-{age}', pose, report)
                    assert any(pose['state'].get('id') == skill for pose in phases), (skill, phases)
                    if skill == primary and dex == 30001:
                        clones = frame.evaluate('''() => {Acceptance.assert(G.NarutoClones.actors.length,'no actual clones');
                          return G.NarutoClones.actors.map(a=>Acceptance.render(a.anim))}''')
                        for i, clone in enumerate(clones):
                            save(f'{label}-clone-{i}', clone, report)
                    if skill == 'naruto-nine-tails-cloak':
                        assert all(pose['form'] for pose in phases), 'cloak never switched complete form'
                        assert all('one-tail' in source for pose in phases for source in pose['sources']), phases
                        page.screenshot(path=str(OUT / f'{label}-cloak-gameplay.png'))
                        # Full form movement/hurt use the same actual actor update
                        # APIs while the live buff is still active.
                        frame.evaluate('Acceptance.p().walking=true;Acceptance.p().anim.base="Walk"')
                        save(f'{label}-cloak-move', frame.evaluate('Acceptance.render()'), report)
                        frame.evaluate('Acceptance.resume();Acceptance.p().hurt(5,null,true);Acceptance.pause()')
                        save(f'{label}-cloak-hurt', frame.evaluate('Acceptance.render()'), report)
                frame.evaluate('Acceptance.arena()')
                page.screenshot(path=str(OUT / f'{label}-{hero}-gameplay.png'))
                frame.evaluate('Acceptance.resume();Acceptance.p().hurt(Acceptance.p().maxHp*10,null,true);Acceptance.pause();Acceptance.step(2)')
                save(f'{label}-{hero}-death', frame.evaluate('Acceptance.render()'), report)
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    assert not report['failedRequests'], report['failedRequests']
    report['metrics'] = contact_and_metrics(report)
    (OUT / 'acceptance.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), 'utf-8')
    print(json.dumps({'passed': True, 'poses': len(report['poses']), 'evidence': str(OUT)}))


def contact_and_metrics(report):
    samples = list(report['poses'])
    sheet = Image.new('RGB', (240 * 6, 225 * ((len(samples) + 5) // 6)), '#172137')
    draw = ImageDraw.Draw(sheet)
    metrics = {}
    for i, name in enumerate(samples):
        image = Image.open(OUT / f'{name}.png').convert('RGBA')
        x, y = i % 6 * 240, i // 6 * 225
        sheet.paste(image, (x, y + 25), image)
        draw.text((x + 3, y + 3), name[:37], fill='white')
        bounds = image.getbbox()
        pixels = [pixel for pixel in image.getdata() if pixel[3] > 20]
        metrics[name] = {'width': bounds[2] - bounds[0], 'height': bounds[3] - bounds[1],
                         'visiblePixels': len(pixels), 'colors': len(set(p[:3] for p in pixels)),
                         'darkOutlineFraction': sum(max(p[:3]) < 95 for p in pixels) / len(pixels),
                         'rgbaSha256': hashlib.sha256(image.tobytes()).hexdigest()}
    sheet.save(OUT / 'runtime-contact.png')
    # Exactly equal evidence scale on both devices; common actors should remain
    # approximately 64px high without a huge change on hero selection.
    heights = [metrics[f'desktop-{hero}-idle-right']['height'] for hero in ['naruto', 'sasuke']]
    assert max(heights) / min(heights) < 1.35, heights
    comparisons = {'fixedFrames': 0, 'matchingLiveFrames': 0, 'differentLiveFrames': []}
    for name in samples:
        # Clone spawn positions and their target-facing directions are random.
        # Their source is audited, while viewport comparisons use player poses.
        if name.startswith('desktop-') and '-clone-' not in name and name.replace('desktop-', 'mobile-', 1) in metrics:
            other = name.replace('desktop-', 'mobile-', 1)
            left, right = report['poses'][name], report['poses'][other]
            # Animated poses are comparable only when their actual frame and
            # all renderer inputs match, including form/flash/adapter timing.
            fields = ['state', 'form', 'options', 'sources']
            same_frame = all(left.get(field) == right.get(field) for field in fields)
            if left.get('fixedReference') or same_frame:
                assert metrics[name] == metrics[other], (name, left, right)
                comparisons['fixedFrames' if left.get('fixedReference') else 'matchingLiveFrames'] += 1
            else:
                comparisons['differentLiveFrames'].append(name)
    expected = sum(report['poses'][name].get('fixedReference', False)
                   for name in samples if name.startswith('desktop-'))
    assert expected >= 18 and comparisons['fixedFrames'] == expected, comparisons
    report['viewportComparisons'] = comparisons
    return metrics


if __name__ == '__main__':
    main()
