"""Native automatic Yuta decisions: near/remote teamwork and situational burst."""
from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('YUTA_IDENTITY_OUT', str(ROOT / '.omx/state/hero-identity/yuta')))
URL = os.environ.get('YUTA_IDENTITY_URL', os.environ.get(
    'JUJUTSU_URL', 'http://127.0.0.1:8337/.omx/digimon.html?lang=zh-TW'))

CHECK = r"""() => {
 const A=JAcceptance,Y=G.JujutsuYuta,p=A.p(),assert=A.assert,out={};
 const ids={blade:'jjk-yuta',rika:'jjk-yuta-rika',speech:'jjk-yuta-speech',manifest:'jjk-yuta-manifest'};
 function setup(names,ranks={}){
  A.reset();A.fixture(ids[names[0]],ranks[names[0]]||1);
  for(const name of names.slice(1))assert(p.addMove(ids[name]),'missing '+name);
  for(const m of p.moves){Object.assign(m,G.Moves.instance(m.id,ranks[Object.keys(ids).find(k=>ids[k]===m.id)]||1));m.t=999;}
  return Object.fromEntries(names.map(name=>[name,p.moves.find(m=>m.id===ids[name])]));
 }
 function tick(){A.step(.01,true);}
 function casts(kind){return Y.inspect(p)?.casts[kind]||0;}
 function crowd(){return [A.spawn(125,0),A.spawn(110,65),A.spawn(100,-65)];}

 let m=setup(['blade','rika']),near=A.spawn(70,0),far=A.spawn(360,0);
 const nearHits=A.watch(near),farHits=A.watch(far);m.blade.t=m.rika.t=0;tick();
 assert(Y.inspect(p).rika.tx>150,'Rika copied the blade nearest-target job');
 A.advance(.85,true);
 assert(nearHits.some(h=>h.id===ids.blade)&&!nearHits.some(h=>h.id===ids.rika),'near enemy was not left to the blade');
 assert(farHits.some(h=>h.id===ids.rika)&&!farHits.some(h=>h.id===ids.blade),'remote enemy was not struck by Rika');
 out.splitReach={near:nearHits.map(h=>h.id),far:farHits.map(h=>h.id)};

 m=setup(['blade','rika'],{blade:3});near=A.spawn(70,0);far=A.spawn(240,0);
 m.blade.t=0;tick();A.advance(.18,true);
 assert(Y.inspect(p).relay?.target===near,'rank3 native sword did not mark its victim');
 m.rika.t=0;tick();
 assert(Y.inspect(p).rika.tx<80,'rank3 relay did not override remote preference');
 out.relay={targetX:Y.inspect(p).rika.tx};

 m=setup(['rika']);near=A.spawn(70,0);m.rika.t=0;tick();
 assert(Y.inspect(p).rika.tx<80,'Rika failed nearby fallback without a distant enemy');
 out.nearFallback=true;

 m=setup(['speech']);near=A.spawn(130,0);m.speech.t=0;A.advance(.5,true);
 assert(casts('speech')===0&&m.speech.t===0,'speech wasted its cooldown on one distant enemy');
 assert(Y.statusFor(p,m.speech).state==='waiting'&&Y.statusFor(p,m.speech).reason==='pressure','speech HUD omitted waiting reason');
 near.x=70;G.EnemyMgr.rebuildGrid();tick();
 assert(casts('speech')===1,'speech did not respond to close pressure');
 A.advance(.25,true);assert(near.hp<near.maxHp&&Y.inspect(p).controls===1,'native speech did not hit/control');
 out.speechClose={casts:casts('speech'),controls:Y.inspect(p).controls};

 m=setup(['speech']);crowd();m.speech.t=0;tick();
 assert(casts('speech')===1,'speech ignored an enclosing group');out.speechCrowd=true;

 m=setup(['speech']);near=A.spawn(130,0);m.speech.t=0;A.resume();
 try{assert(Y.cast(p,m.speech),'explicit speech cast was incorrectly gated by automatic pressure policy');}finally{A.pause();}
 out.explicitSpeech=true;

 m=setup(['manifest']);near=A.spawn(130,0);m.manifest.t=0;A.advance(.5,true);
 assert(!Y.manifested(p)&&casts('manifest')===0&&m.manifest.t===0,'manifest wasted burst on lone trash');
 assert(Y.statusFor(p,m.manifest).state==='waiting'&&Y.statusFor(p,m.manifest).reason==='encounter','manifest HUD omitted encounter wait');
 near.boss=true;tick();assert(Y.manifested(p)&&casts('manifest')===1,'manifest ignored strong encounter');
 out.manifestBoss=true;

 m=setup(['manifest']);crowd();m.manifest.t=0;tick();
 assert(Y.manifested(p)&&casts('manifest')===1,'manifest ignored a crowd');out.manifestCrowd=true;

 m=setup(['rika','manifest']);near=A.spawn(210,0);near.boss=true;
 m.rika.t=4;m.manifest.t=0;tick();
 assert(Y.manifested(p)&&casts('rika')===1&&m.rika.t>0,'manifest did not refresh and dispatch Rika');
 const actor=Y.inspect(p).rika,afterCast=m.rika.t;A.advance(.3,true);
 assert(Y.inspect(p).rika===actor&&casts('rika')===1,'manifest created overlapping Rika actors');
 assert(m.rika.t>afterCast-.32&&m.rika.t<afterCast-.28,'Rika cooldown refreshed repeatedly inside manifestation');
 const frozen={age:actor.age,clock:Y.inspect(p).clock,t:m.rika.t};
 G.Combat.tick(1,p,0);G.Combat.updateFields(1);
 assert(actor.age===frozen.age&&Y.inspect(p).clock===frozen.clock&&m.rika.t===frozen.t,'pause advanced burst/companion');
 out.burst={rikaCasts:casts('rika'),singleActor:true,cooldown:afterCast,pause:true};

 m=setup(['rika','manifest']);near=A.spawn(210,0);m.rika.t=4;m.manifest.t=0;A.resume();
 try{assert(Y.cast(p,m.manifest),'explicit manifest was incorrectly gated by encounter policy');}finally{A.pause();}
 assert(Y.manifested(p)&&m.rika.t===0,'explicit manifest did not grant one companion refresh');out.explicitManifest=true;
 G.Combat.clearFields(p);assert(Y.inspect(p)===null&&Y.drawables().length===0,'owner clear retained burst actor');

 m=setup(['rika','manifest']);near=A.spawn(210,0);near.boss=true;m.manifest.t=0;tick();
 p.dead=true;p.hp=0;G.Combat.updateFields(.1);
 assert(Y.inspect(p)===null&&Y.drawables().length===0,'death retained burst actor');
 out.cleanup={owner:true,death:true};
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base.URL = URL
    base.OUT = OUT
    report = {'url': URL, 'viewports': {}, 'errors': [], 'missing': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        for label, viewport, mobile in [('desktop', {'width': 1280, 'height': 900}, False),
                                         ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=viewport, is_mobile=mobile,
                                          has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.on('response', lambda response: report['missing'].append(response.url)
                    if response.status >= 400 else None)
            frame = base.boot(page, 30013, label)
            report['viewports'][label] = frame.evaluate(CHECK)
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    assert not report['missing'], report['missing']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'viewports': list(report['viewports']), 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
