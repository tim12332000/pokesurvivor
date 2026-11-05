"""Native RAF combat with legal learning, real input and readable role evidence.

The moving, high-HP enemy fixture and periodic incoming shots keep every learned
role observable. This is a bounded presentation/input check, not a survival or
human enjoyment study. No direct skill casts or skill-clock advancement are used.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('HERO_PLAY_OUT', str(ROOT / '.omx/state/hero-identity/play')))

SETUP = r"""() => {
 const A=JAcceptance,p=A.p();A.reset();p.level=9;
 for(const id of G.Moves.poolFor(p.mon))if(!p.hasMove(id)){
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
   A.assert(card&&card.apply(p)!==false,'native learning failed '+id);
 }
 A.assert(p.moves.length===4&&p.moves.every(m=>m.lvl===1),'fixture granted ranks or omitted skill');
 for(const m of p.moves)m.t=0;
 p.xpNext=1e12;G.Spawner.update=()=>{};G.World.walkable=()=>true;G.Path.clear();
 const enemies=[];
 for(const [x,y] of [[70,0],[115,35],[145,-40],[240,0],[250,35],[245,-35],[160,140],[120,-145]]){
   const e=A.spawn(x,y);e.spd=8;e.dmg=0;enemies.push(e);
 }
 const events=[],cast=p.cast;p.cast=function(m,...args){events.push({time:G.Game.st.time,id:m.id,x:this.x,y:this.y});return cast.call(this,m,...args)};
 G.Game.debugSpeed(1);const started=G.Game.st.time;
 window.IdentityPlay={started,events,positions:[],lastShot:-2};
 function sample(){
   const run=window.IdentityPlay;if(!run)return;
   if(G.Game.state==='playing'){
     const t=G.Game.st.time-started;
     if(t-run.lastShot>=2){run.lastShot=t;G.Projectiles.spawn({x:p.x+180,y:p.y,vx:-180,vy:0,r:6,life:2,dmg:1,mtype:'psychic',friendly:false});}
     if(!run.positions.length||t-run.positions.at(-1).time>.5)run.positions.push({time:t,x:p.x,y:p.y});
   }
   requestAnimationFrame(sample);
 }
 requestAnimationFrame(sample);A.resume();
 return {level:p.level,skills:p.moves.map(m=>m.id),starting:{x:p.x,y:p.y}};
}"""


class Handler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def do_GET(self):
        try:
            super().do_GET()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass


class Server(ThreadingHTTPServer):
    request_queue_size = 128


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    server = None
    url = os.environ.get('JUJUTSU_URL')
    if not url:
        server = Server(('127.0.0.1', 0), partial(Handler, directory=str(ROOT)))
        Thread(target=server.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW'
    base.URL = url
    report = {'url': url, 'scope': '12 native game seconds, legal four rank1 skills, moving persistent enemy fixture, keyboard/touch input; no direct casts',
              'cases': {}, 'errors': [], 'missing': []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            for mobile in [False, True]:
                for dex, slug in base.HEROES.items():
                    key = ('mobile-' if mobile else 'desktop-') + slug
                    print(key, flush=True)
                    context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1100, 'height': 850},
                                                  is_mobile=mobile, has_touch=mobile, service_workers='block')
                    page = context.new_page()
                    page.on('pageerror', lambda e: report['errors'].append(str(e)))
                    page.on('response', lambda r: report['missing'].append(r.url) if r.status >= 400 else None)
                    frame = base.boot(page, dex, 'mobile' if mobile else 'desktop')
                    fixture = frame.evaluate(SETUP)
                    phase = {'yuta': "G.JujutsuYuta.inspect(G.Game.player)?.rika?.phase==='strike'",
                             'ryu': "G.JjkRyu.stateFor(G.Game.player)?.action?.mode==='jjk-ryu-maximum'&&G.JjkRyu.stateFor(G.Game.player)?.action?.released",
                             'uro': "G.JjkUro.stateFor(G.Game.player)?.screen&&G.JjkUro.stateFor(G.Game.player)?.pose?.mode!=='uro-screen'&&G.JjkUro.stateFor(G.Game.player)?.pose"}[slug]
                    frame.wait_for_function(phase, polling=10, timeout=25000)
                    frame.evaluate('JAcceptance.pause()')
                    page.wait_for_timeout(40)
                    page.screenshot(path=str(OUT / f'{key}-role-contact.png'))
                    frame.evaluate('JAcceptance.resume()')
                    snapshots = []
                    for index, at in enumerate([1, 3, 5, 8, 12]):
                        frame.wait_for_function('at=>G.Game.st.time-IdentityPlay.started>=at', arg=at, timeout=25000)
                        if mobile:
                            client = context.new_cdp_session(page)
                            box = frame.locator('#game').bounding_box()
                            x, y = box['x'] + 70, box['y'] + box['height'] - 120
                            client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
                            client.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x + (22 if index % 2 == 0 else -22), 'y': y}]})
                            page.wait_for_timeout(140)
                            client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                            client.detach()
                        else:
                            keycode = 'KeyD' if index % 2 == 0 else 'KeyA'
                            frame.evaluate('(code)=>window.dispatchEvent(new KeyboardEvent("keydown",{code}))', keycode)
                            page.wait_for_timeout(140)
                            frame.evaluate('(code)=>window.dispatchEvent(new KeyboardEvent("keyup",{code}))', keycode)
                        snapshots.append(frame.evaluate('''()=>({time:G.Game.st.time-IdentityPlay.started,positions:IdentityPlay.positions.length,
                          skills:G.Game.player.moves.map(m=>({id:m.id,label:G.RunInsights.skillState(G.Game.player,m).label})),
                          visualKinds:[...new Set((G.JujutsuVFX.inspect().frame?.draws||[]).map(d=>d.kind))]})'''))
                        page.screenshot(path=str(OUT / f'{key}-{at}s.png'))
                    frame.evaluate('JAcceptance.pause()')
                    result = frame.evaluate('''()=>{const run=IdentityPlay,p=G.Game.player,counts={};for(const e of run.events)counts[e.id]=(counts[e.id]||0)+1;
                      JAcceptance.assert(p.moves.every(m=>counts[m.id]>0),'learned role never automatically used '+JSON.stringify(counts));
                      JAcceptance.assert(run.positions.some(v=>Math.hypot(v.x,v.y)>3),'native input never moved player');
                      return {counts,events:run.events,positions:run.positions,damage:p.dmgDealt};}''')
                    report['cases'][key] = {'fixture': fixture, 'snapshots': snapshots, **result}
                    context.close()
                    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
            browser.close()
        assert not report['errors'], report['errors']
        assert not report['missing'], report['missing']
        report['ok'] = True
        (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
        print(json.dumps({'ok': True, 'cases': len(report['cases']), 'evidence': str(OUT)}))
    finally:
        if server:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
