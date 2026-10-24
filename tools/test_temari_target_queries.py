"""Compare native pet acquisition with the uncached runtime, including live mutations."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_temari as native
import test_temari_passive as pets
import test_temari_fan as fan

ROOT = Path(__file__).resolve().parents[1]
CHECK = r"""kind => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,W=G.World,M=G.EnemyMgr;
 A.petReset();p.quantityPicks=p.quantityBonus=10;T.syncPets(p);
 const first=A.spawn(100,0,'boss'),other=A.spawn(kind==='move'?600:180,0,'boss');
 for(const a of A.pets())Object.assign(a,{phase:'wander',cooldown:0,restUntil:9999,
   roamTarget:{x:100,y:0,arrived:true}});
 const originalQuery=M.queryCircle,originalHook=T.onPetAttack,originalBlock=W.projectileBlock;
 const events=[];let queries=0,blocked=false;
 M.queryCircle=function(...args){queries++;return originalQuery.apply(this,args)};
 W.projectileBlock=(x,y,r)=>blocked&&x>20&&x<80?'wall':false;
 T.onPetAttack=(owner,a)=>{
   events.push({index:a.index,x:a.tx,y:a.ty});
   if(events.length!==1)return;
   if(kind==='death'){first.hp=0;first.dead=true;}
   if(kind==='move'){other.x=80;M.rebuildGrid();}
   if(kind==='replace'){
     const replacement=A.spawn(70,0,'boss'),list=M.all();
     list.splice(list.indexOf(other),1);M.rebuildGrid();
     A.assert(list.includes(replacement),'replacement fixture missing');
   }
   if(kind==='wall')blocked=true;
 };
 try{A.resume();T.update(1/60)}finally{
   A.pause();M.queryCircle=originalQuery;T.onPetAttack=originalHook;W.projectileBlock=originalBlock;
 }
 A.assert(events.length===(kind==='wall'?1:9),'pet acquisition changed '+kind);
 A.assert(new Set(A.pets().map(a=>a.index)).size===9,'duplicate roster index');
 return {events,queries};
}"""

WAVE_CHECK = r"""kind => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,W=G.World;
 A.fanReset(3,5,5);
 const first=A.fanEnemy(100,0,10),other=A.fanEnemy(130,25,8),events=[];
 const block=W.projectileBlock,props=W.propsInCircle,damageProp=W.damageProp;
 const rock={x:75,y:0,r:4,hp:1,destructible:true,dead:false};
 let mutated=false,opened=false;
 W.projectileBlock=(x,y)=>kind==='prop'&&!opened&&x>65&&x<85&&Math.abs(y)<8?rock:false;
 W.propsInCircle=()=>kind==='prop'?[rock]:[];
 W.damageProp=(target,damage)=>{target.hp-=damage;if(target.hp<=0){target.dead=true;opened=true;}return opened;};
 for(const [index,e] of [first,other].entries()){
   const hurt=e.hurt;e.hurt=function(...args){
     events.push({index,x:this.x,y:this.y,r:this.r,raw:args[0]});
     const result=hurt.apply(this,args);
     if(!mutated){mutated=true;
       if(kind==='move'){other.x=220;other.y=80;}
       if(kind==='radius')other.r=75;
       G.EnemyMgr.rebuildGrid();
     }
     return result;
   };
 }
 try{A.fanCast(other);A.finish(4)}finally{
   W.projectileBlock=block;W.propsInCircle=props;W.damageProp=damageProp;
 }
 A.assert(events.length>0,'wave fixture missed all targets');
 if(kind==='prop')A.assert(opened&&events.some(e=>e.index===0),'broken blocker hid later front');
 return {events,cuts:T.stateFor(p).totalCuts};
}"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path,
                        help='Optional saved pre-optimization naruto-temari.js for exact comparison.')
    args = parser.parse_args()
    report = {'errors': [], 'cases': {}, 'ok': False}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
        for variant in (['before', 'after'] if args.baseline else ['after']):
            context = browser.new_context(viewport={'width': 1200, 'height': 900}, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            if variant == 'before':
                body = args.baseline.read_bytes()
                page.route('**/.omx/naruto-temari.js*',
                           lambda route: route.fulfill(body=body, content_type='text/javascript'))
            native.boot(page)
            page.evaluate(pets.SETUP)
            report['cases'][variant] = {kind: page.evaluate(CHECK, kind)
                                        for kind in ['stable', 'death', 'move', 'replace', 'wall']}
            page.evaluate(fan.SETUP)
            report['cases'][variant]['waves'] = {
                kind: page.evaluate(WAVE_CHECK, kind) for kind in ['move', 'radius', 'prop']}
            context.close()
        browser.close()
    after = report['cases']['after']
    assert after['stable']['queries'] == 1, after['stable']
    assert after['wall']['queries'] == 1, after['wall']
    if args.baseline:
        before = report['cases']['before']
        for kind in after:
            if kind == 'waves':
                assert before[kind] == after[kind], kind
            else:
                assert before[kind]['events'] == after[kind]['events'], kind
        assert before['stable']['queries'] == 9, before['stable']
    assert not report['errors'], report['errors']
    report['ok'] = True
    output = ROOT / '.omx/state/temari-performance/target-queries.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'stableQueries': after['stable']['queries'], 'report': str(output)}))


if __name__ == '__main__':
    main()
