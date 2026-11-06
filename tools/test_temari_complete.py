"""Real Temari pipeline regressions for release, weaving and contact aftermath."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_temari as native
import test_temari_typhoon as typhoon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/temari-complete/mechanics'

SETUP = r"""() => {
 const A=Acceptance,p=A.p();A.tyLearn();
 A.completeReset=()=>{A.reset();A.mastery(0);p.hp=p.maxHp;p.dead=false;p.frozen=false;};
 A.completeTick=dt=>{A.resume();try{G.Combat.tick(dt,p,0)}finally{A.pause()}};
 A.completeSelect=id=>p.setActive(p.slots.findIndex(g=>g.some(m=>m.id===id)));
}"""

ORIGINS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(const id of ['naruto-temari','naruto-temari-great-scythe','naruto-temari-typhoon']){
   A.completeReset();p.quantityBonus=p.quantityPicks=5;p.target=A.spawn(150,0,'boss');
   A.castNative(id);const b=T.stateFor(p).latest,aim=b.aim;A.finish(b.release-.01);
   p.x=45;p.y=25;A.advance(.01);const committed={x:b.x,y:b.y};
   A.near(b.x,45,'release x '+id);A.near(b.y,25,'release y '+id);A.near(b.aim,aim,'locked aim');
   p.x=90;p.y=-25;A.finish(.2);
   const actors=[...T.waves,...T.storms].filter(a=>a.cast===b);
   A.assert(actors.length===b.count,'copy emission '+id);
   A.assert(actors.every(a=>a.x===committed.x&&a.y===committed.y),'quantity origins split or dragged');
   out.push({id,count:b.count,origin:committed});
 }
 for(const reason of ['clear','death','world','unlearn']){
   A.completeReset();p.target=A.spawn(150,0,'boss');A.castNative('naruto-temari');
   const b=T.stateFor(p).latest,world=G.World,moves=p.moves;
   try{
     if(reason==='clear')T.clear(p);else if(reason==='death'){p.hp=0;p.dead=true;}
     else if(reason==='world')G.World=Object.create(world);else p.moves=p.moves.filter(m=>m.id!==b.id);
     A.finish(.5);A.assert(b.emitted===0&&!T.waves.some(a=>a.cast===b),'invalid prerelease emitted '+reason);
   }finally{G.World=world;p.moves=moves;p.hp=p.maxHp;p.dead=false;T.clear();}
 }
 return out;
}"""

COOLDOWNS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(const [id,other,cd] of [['naruto-temari-great-scythe',A.ty,5],[A.ty,'naruto-temari-great-scythe',8]]){
   A.completeReset();p.target=A.spawn(150,0,'boss');A.castNative(id);A.completeSelect(other);
   const otherMove=p.moves.find(m=>m.id===other);otherMove.t=999;
   for(let i=0;i<20;i++)A.completeTick(.1);
   A.near(T.stateFor(p).cooldowns[id],cd-2,'offslot recovery');
   const move=p.moves.find(m=>m.id===id);A.near(move.t,cd-2,'offslot HUD');
   A.completeSelect(id);A.near(move.t,cd-2,'switch shortened HUD');
   A.assert(!T.canCast(p,move),'switch bypassed cooldown');
   p.frozen=true;A.completeTick(.5);p.frozen=false;A.near(T.stateFor(p).cooldowns[id],cd-2,'freeze recovered');
   A.completeSelect(other);otherMove.t=999;for(let i=0;i<(cd-2)*10;i++)A.completeTick(.1);
   A.near(T.stateFor(p).cooldowns[id],0,'offslot expiry');
   const count=T.stateFor(p).castCounts[move.digiMode];A.completeSelect(id);A.completeTick(.01);
   A.assert(T.stateFor(p).castCounts[move.digiMode]===count+1,'reselect failed to cast once');
   A.near(T.stateFor(p).cooldowns[id],cd,'new recovery shortened');out.push({id,cd});
 }
 return out;
}"""

CANCELLATION = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(const id of ['naruto-temari','naruto-temari-great-scythe',A.ty])
 for(const phase of ['hurt','onDealt'])for(const reason of ['clear','death','world']){
   A.completeReset();const first=A.spawn(100,0),second=A.spawn(100,2),one=A.watch(first),two=A.watch(second);
   const original=first.hurt,oldDealt=p.onDealt,world=G.World;
   const cancel=()=>{if(reason==='clear')T.clear(p);else if(reason==='death'){p.hp=0;p.dead=true;}else G.World=Object.create(world);};
   if(phase==='hurt')first.hurt=function(...args){const r=original.apply(this,args);cancel();return r;};else p.onDealt=cancel;
   try{p.target=first;A.castNative(id);for(let i=0;i<200&&!one.length;i++)A.advance(.005);
     A.assert(one.length===1&&two.length===0,'same-wave cancellation damage '+id+'/'+phase+'/'+reason);
     A.assert(!T.liftForState(first)&&!T.liftForState(second)&&!T.pushFor(first)&&!T.pushFor(second)&&!T.orbitFor(first)&&!T.orbitFor(second),'cancelled control lease '+id+'/'+phase+'/'+reason);
     if(reason==='clear')A.assert(!T.stateFor(p),'cancelled state recreated '+id);
     A.advance(.05);A.assert(two.length===0,'future cancelled damage');
     out.push({id,phase,reason});
   }finally{G.World=world;p.onDealt=oldDealt;p.hp=p.maxHp;p.dead=false;T.clear();}
 }
 return out;
}"""

CONTACTS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.completeReset();
 const e=A.spawn(0,-140,'boss'),h=A.watch(e);p.target=A.spawn(140,0,'boss');A.castNative(A.ty);
 A.finish(2.2);const storm=T.storms[0],contact=storm?.contacts.get(e);
 A.assert(contact?.lastHit&&contact.lastHit.age>1.2,'late actual contact lacks tail metadata');
 const mark={...contact.lastHit};A.assert(h.length>0,'tail mark without actual damage');
 e.x=1000;G.EnemyMgr.rebuildGrid();A.advance(.005);
 A.assert(contact.lastHit.x===mark.x&&contact.lastHit.y===mark.y,'historical mark followed enemy');
 T.clear();A.completeReset();const target=A.spawn(140,0,'boss'),visual=A.spawn(0,-140,'boss'),hp=target.hp,visualHp=visual.hp;
 const move=p.moves.find(m=>m.id===A.ty),packet=T.snapshot(p,move),remote={x:0,y:0,hp:100,dead:false,aim:0};
 packet.aim=0;packet.castId=771;packet.needsRelease=true;packet.targetPositions=[{x:140,y:0}];
 A.assert(T.ghost(remote,packet),'ghost rejected');A.finish(.6);A.assert(!T.storms.length,'ghost emitted without commit');
 A.assert(T.applyWindRelease(remote,{castId:771,x:0,y:0,aim:0}),'ghost release rejected');
 A.assert(T.applyWindRelease(remote,{castId:771,x:0,y:0,aim:0}),'duplicate release not idempotent');
 A.assert(!T.applyWindRelease(remote,{castId:771,x:90,y:0,aim:0}),'conflicting release accepted');
 A.finish(.2);const ghostStorm=T.storms[0];
 A.assert(ghostStorm?.age>=.4,'delayed release restarted original clock');
 A.assert(target.hp===hp,'visual ghost damaged target');
 A.finish(1.4);const remoteContact=ghostStorm.contacts.get(visual),ghost=ghostStorm.cast;
 A.assert(remoteContact?.visualHit?.visualOnly===true&&!remoteContact.lastHit,'ghost omitted separate visual tail');
 A.assert(visual.hp===visualHp&&ghost.hits===0&&ghost.cuts===0&&!T.orbitFor(visual),'ghost visual changed damage/control/counters');
 A.assert(remoteContact.visualHit.age>1.2,'ghost tail did not extend to actual later contact');
 T.clear();A.completeReset();packet.castId=772;T.ghost(remote,packet);A.finish(3.1);
 A.assert(!T.casts.some(b=>b.owner===remote)&&!T.applyWindRelease(remote,{castId:772,x:0,y:0,aim:0}),'expired ghost resurrected');
 return {actual:mark,ghostNoDamage:true,expiry:true};
}"""

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source', type=Path)
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--checks', default='origins,cooldowns,cancellation,contacts')
    args=parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report={'source':str(args.source or '.omx/naruto-temari.js'),'results':{},'failures':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=native.CHROME,headless=True)
        for label, viewport in [('desktop',{'width':1200,'height':900}),('mobile',{'width':390,'height':844})]:
            page=browser.new_page(viewport=viewport,is_mobile=label=='mobile',has_touch=label=='mobile')
            if args.source:
                page.route('**/.omx/naruto-temari.js*',lambda route:route.fulfill(path=str(args.source.resolve()),content_type='application/javascript'))
            native.boot(page);page.evaluate(typhoon.SETUP);page.evaluate(SETUP)
            report['results'][label]={}
            for name,check in [('origins',ORIGINS),('cooldowns',COOLDOWNS),('cancellation',CANCELLATION),('contacts',CONTACTS)]:
                if name not in args.checks.split(','):continue
                try:
                    report['results'][label][name]=page.evaluate(check)
                except Exception as error:
                    report['failures'].append(label+':'+name+': '+str(error))
                print(label,name,'done',flush=True)
            page.close()
        browser.close()
    report['ok']=not report['failures']
    path=OUT/('baseline.json' if args.baseline else 'report.json')
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'report':str(path)}))
    if not report['ok']:raise SystemExit(1)

if __name__=='__main__':main()
