"""Production-entry Perfect framing and native RAF recovery; controlled, not natural growth."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_madara_rework as acceptance

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('MADARA_FRAMING_OUT', ROOT / 'art-review/madara/rework-framing'))

EARN = r"""() => {
 const A=JAcceptance,p=A.p(),M=G.NarutoMadara;A.reset();
 const fire=A.fixture('naruto-madara-fire',1);
 A.assert(p.addMove('naruto-madara-susanoo'),'learn guardian');
 const guard=p.moves.find(m=>m.id==='naruto-madara-susanoo');
 Object.assign(guard,G.Moves.instance(guard.id,3));A.spawn(100,0);A.spawn(150,0);
 for(let i=0;i<3;i++){fire.t=0;A.resume();A.assert(M.cast(p,fire),'fire cast');A.pause();A.advance(.95);}
 A.assert(M.stateFor(p).impetus===3,'three true fire casts did not earn momentum');
 guard.t=0;A.resume();A.assert(M.cast(p,guard),'Perfect cast');A.pause();
 A.assert(M.guardianPose(p).perfect,'not Perfect');
 for(const m of p.moves)m.t=999;G.Spawner.update=()=>{};A.resume();
 return {form:M.guardianPose(p),perfectCount:M.stateFor(p).perfectCount};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    acceptance.OUT = OUT
    report = {'scope': 'normal entry, three controlled true fire casts earn Perfect; native RAF/camera thereafter; not natural growth',
              'views': {}, 'errors': [], 'failures': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=acceptance.base.CHROME, headless=True)
        for label, width, height, mobile in [('desktop',1280,900,False), ('mobile390',390,844,True), ('mobile360',360,800,True)]:
            context = browser.new_context(viewport={'width':width,'height':height}, is_mobile=mobile,
                                          has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            try:
                frame = acceptance.boot(page, label)
                start = frame.evaluate(EARN)
                page.wait_for_timeout(650)
                view = frame.evaluate(r"""() => {
                 const p=G.Game.player,c=G.Camera,s=G.MadaraFraming.inspect();
                 JAcceptance.assert(s?.active,'framing not active');
                 return {framing:s,top:(p.y-s.top-c.top())*c.scale,
                  bottom:(p.y+s.bottom-c.top())*c.scale,ownerScreenY:(p.y-c.top())*c.scale,
                  form:G.NarutoMadara.guardianPose(p)};
                }""")
                assert view['top'] >= min(112,height*.18)-12, (label,view)
                assert view['bottom'] <= height-min(112,height*.18)+12, (label,view)
                page.screenshot(path=str(OUT / f'{label}-perfect-framed.png'))
                before = frame.evaluate('JAcceptance.pause();JSON.stringify([G.Camera.x,G.Camera.y,G.Camera.scale,G.Camera.w,G.Camera.h])')
                page.wait_for_timeout(250)
                after = frame.evaluate('G.Camera.follow(100,100,.5);JSON.stringify([G.Camera.x,G.Camera.y,G.Camera.scale,G.Camera.w,G.Camera.h])')
                assert before == after, 'paused view drifted'
                frame.evaluate('JAcceptance.resume()')
                frame.wait_for_function('!G.NarutoMadara.guardianPose(G.Game.player)', timeout=12000)
                page.wait_for_timeout(700)
                end = frame.evaluate('({scale:G.Camera.scale,expected:G.Camera.viewportScale(innerWidth,innerHeight),cue:G.MadaraFraming.inspect()})')
                assert abs(end['scale']-end['expected']) < .001, (label,end)
                report['views'][label] = {'start':start,'active':view,'pauseFrozen':True,'end':end}
            except Exception as error:
                report['failures'].append(f'{label}: {error}')
                page.screenshot(path=str(OUT / f'{label}-failure.png'))
            finally:
                context.close()
        browser.close()
    report['ok'] = not (report['errors'] or report['failures'])
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'errors':report['errors'],'evidence':str(OUT)}))
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
