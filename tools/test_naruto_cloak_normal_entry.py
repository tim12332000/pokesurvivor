"""Controlled cloak combat and transition captures through the normal game entry."""
import hashlib
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME

ROOT = Path(__file__).resolve().parents[1]
LIVE = os.environ.get('CLOAK_LIVE') == '1'
OUT = ROOT / ('.omx/state/naruto-cloak-release/public-window' if LIVE else 'art-review/naruto-cloak-20261116')
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&layout=wide'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reports = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for width in (1100, 390):
            context = browser.new_context(viewport={'width': width, 'height': 850},
                                          is_mobile=width < 500, has_touch=width < 500,
                                          service_workers='block', record_video_dir=str(OUT / 'video'))

            def route(request):
                file = ROOT / unquote(urlsplit(request.request.url).path).removeprefix('/pokesurvivor/')
                request.fulfill(status=200 if file.is_file() else 404,
                                body=file.read_bytes() if file.is_file() else b'Not found',
                                content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')

            if not LIVE:
                context.route('https://tim12332000.github.io/pokesurvivor/**', route)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(URL.replace('digimon.html', 'portrait.html').replace('layout=wide', 'layout=portrait') if width < 500 else URL)
            view = page
            if width < 500:
                page.wait_for_selector('#portrait-game')
                view = page.locator('#portrait-game').element_handle().content_frame()
            view.wait_for_function('window.PS_REDRAWN_READY && document.getElementById("boot").classList.contains("hidden")')
            if view.locator('#tap-start').is_visible():
                view.locator('#tap-start').click()
            view.evaluate("""async()=>{await PS_REDRAWN_READY;G.Naruto.choose(30001);await G.Flow.play();
              if(G.Game.state==='playing')G.Game.togglePause();G.UI.hideAll();
              document.querySelectorAll('.toast,#ach-pop').forEach(e=>e.style.display='none');
            }""")
            report = view.evaluate("""() => {
              const p=G.Game.player,S=G.NarutoSupport,id='naruto-nine-tails-cloak';
              const assert=(v,m)=>{if(!v)throw Error(m)};
              G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();G.FX.clear();
              Object.assign(G.World,{isFree:()=>true,isWall:()=>false,isLiquid:()=>false,collide:()=>{},projectileBlock:()=>false});
              p.x=p.y=0;p.critChance=0;p.target=null;p.level=9;p.invuln=999;
              for(const m of p.moves)m.t=999;
              p.addMove(id);const m=p.moves.find(m=>m.id===id);m.t=0;
              const enemy=(x,y)=>{const e=new G.Enemy({dex:19,hp:1e7,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
                e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;};
              const near=enemy(80,0),outside=enemy(160,0),blocked=enemy(-80,0);p.target=near;p.aim=0;
              const atk=p.atk;
              p.setActive(p.slots.findIndex(group=>group.includes(m)));
              G.Combat.tick(.01,p,0);
              assert(S.effects.some(f=>f.owner===p&&f.mode==='nine-tails-cloak'),'normal selected cast failed');
              assert(Math.abs(p.atk/atk-1.5)<1e-6,'attack bonus is not single 50 percent multiplier');
              G.NarutoClones.cast(p,G.Moves.instance('naruto-shadow-clones',1));
              G.World.isWall=(x,y)=>x< -35&&x> -45&&Math.abs(y)<15;
              S.update(.66);
              const expected=Math.round(m.pulseDamage*p.atk*G.Types.mult(m.type,near.types)*G.Weather.mult(m.type));
              const actualPulse=1e7-near.hp;
              assert(Math.abs(1e7-near.hp-expected)<1e-6,'pulse damage mismatch: '+(1e7-near.hp)+' vs '+expected);
              assert(outside.hp===1e7&&blocked.hp===1e7,'pulse hit outside range or through wall');
              const upgrade=G.Moves.instance(id,5);
              assert(upgrade.pulseDamage>m.pulseDamage&&upgrade.radius>m.radius&&upgrade.pulseInterval<m.pulseInterval,'upgrades do not improve pulse');
              const tiers=[];
              for(let rank=1;rank<=5;rank++){
                const u=G.Moves.instance(id,rank),index=rank-1;
                const expected={radius:[96,96,108,108,120][index],pulseDamage:[18,22,22,26,32][index],
                  atkMul:[1.5,1.5,1.65,1.65,1.65][index],speedMul:[1.25,1.25,1.25,1.35,1.35][index],
                  fieldDuration:[8,9,9,9,10][index],cd:[14,14,14,14,11.9][index]};
                for(const [key,value] of Object.entries(expected))assert(Math.abs(u[key]-value)<1e-6,'tier '+rank+' '+key+' mismatch: '+u[key]);
                tiers.push({rank,...expected});
              }
              const sample=G.NarutoClones.actors[0];
              sample.x=near.x-20;sample.y=near.y;sample.cd=0;
              G.NarutoClones.update(.01);
              assert(G.KyuubiForm.poseFor(sample.anim)?.animation==='attack','basic shadow punch rendered as a throw');
              sample.dead=true;
              assert(!G.KyuubiForm.active(sample),'dead shadow retained cloak');
              sample.dead=false;
              const card=G.LevelUp.STATS.find(c=>c.id==='selfClone').apply(p);
              assert(card&&S.cast(card,G.Moves.instance(id,1)),'card clone could not own its cloak');
              G.NarutoClones.cast(card,G.Moves.instance('naruto-shadow-clones',1));
              const child=G.NarutoClones.actors.find(a=>a.owner===card);
              assert(child&&G.KyuubiForm.active(child),'card clone shadow did not inherit its own owner');
              S.clear(card);
              assert(!G.KyuubiForm.active(child)&&G.KyuubiForm.active(p),'card cleanup affected another owner');
              p.dead=true;
              assert(!G.KyuubiForm.active(sample),'dead owner left a transformed child');
              p.dead=false;G.SelfClones.clear();
              G.Combat.clearFields();G.EnemyMgr.clear();G.FX.clear();p.target=null;
              const danger=enemy(250,0);p.target=danger;assert(S.cast(p,m),'repeat cast failed');
              G.EnemyMgr.clear();p.target=null;
              G.NarutoClones.cast(p,G.Moves.instance('naruto-shadow-clones',1));
              G.Camera.x=p.x;G.Camera.y=p.y;
              window.cloakStep=dt=>{G.Game.togglePause();
                try{G.Combat.updateFields(dt);p.anim.update(dt)}finally{G.Game.togglePause()}
              };
              return {expectedPulse:expected,actualPulse,clones:8,tiers,upgrade:{damage:upgrade.pulseDamage,radius:upgrade.radius,interval:upgrade.pulseInterval},checks:['normal entry','single inherited attack bonus','one pulse despite eight clones','outside range','wall blocking','real basic punch pose','dead clone','dead owner','independent card-clone ownership','exact tier stats']};
            }""")
            previous = 0
            for age in (0, .15, .35, .7, 7.8, 8.05):
                view.evaluate('(dt)=>cloakStep(dt)', age - previous)
                previous = age
                page.wait_for_timeout(90)
                page.screenshot(path=str(OUT / f'normal-{width}-{age}.png'))
            view.evaluate("""()=>{const p=G.Game.player;
              if(G.KyuubiForm.poseFor(p.anim)||G.NarutoClones.actors.some(a=>G.KyuubiForm.active(a)))throw Error('expiry failed');
              G.Combat.clearFields();
            }""")
            # Advance the native game loop through a complete live window, rather than
            # treating the manually sampled phase captures as a natural-time recording.
            view.evaluate("""()=>{const p=G.Game.player;
              for(let i=0;i<12;i++){const a=i*Math.PI/6;
                G.EnemyMgr.add(new G.Enemy({dex:19,hp:2000,spd:40,dmg:0,xp:0,behavior:'chase'},
                  p.x+Math.cos(a)*180,p.y+Math.sin(a)*180,{hp:1,spd:1,dmg:1}));}
              G.EnemyMgr.rebuildGrid();
              const m=p.moves.find(m=>m.id==='naruto-nine-tails-cloak');m.t=999;
              if(!G.NarutoSupport.cast(p,m))throw Error('native window failed to start');
              G.Game.togglePause();
            }""")
            page.wait_for_timeout(8800)
            report['nativeWindow'] = view.evaluate("""()=>{
              const p=G.Game.player;
              if(G.Game.state!=='playing')throw Error('native loop stopped during cloak window');
              const active=G.KyuubiForm.active(p);G.Game.togglePause();
              if(active)throw Error('native cloak did not expire');
              return {expired:true,damage:p.dmgDealt,livingShadows:G.NarutoClones.actors.length};
            }""")
            assert not errors, errors
            report['errors'] = errors
            reports[str(width)] = report
            context.close()
        browser.close()
    reports['formSHA256'] = hashlib.sha256((ROOT / 'art-review/kyuubi-form.js').read_bytes()).hexdigest()
    (OUT / 'normal-report.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    print('PASS: normal desktop/mobile entries, pulse combat, upgrades, shadow lifecycle, transition captures')


if __name__ == '__main__':
    main()
