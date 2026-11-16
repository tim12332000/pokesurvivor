"""Controlled production-entry regression for parallel possession and physical kunai."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_shikamaru as base
OUT=Path(os.environ.get('SHIKAMARU_KUNAI_OUT',base.ROOT/'art-review/shikamaru/qa/parallel-kunai'))
CHECK=r'''() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,result={};
 const setup=(rank=3,q=0)=>{A.reset();const m=A.fixture('naruto-shikamaru',rank);p.quantityPicks=q;return m};
 let m=setup(),es=[A.spawn(160,0),A.spawn(0,160),A.spawn(-160,0)],hits=es.map(A.watch);A.cast(m);let b=S.casts.at(-1);
 A.assert(b.chain.segments.length===3&&b.chain.segments.every(s=>s.sourceActor===null&&s.origin.x===p.x&&s.origin.y===p.y),'parallel roots missing');
 A.assert(!hits.some(h=>h.length),'cast caused instant damage');
 for(let i=0;i<90&&!b.chain.segments.every(s=>s.contact);i++)A.step(.01);
 A.assert(b.chain.segments.every(s=>s.contact),'not all targets captured');
 A.assert(!hits.some(h=>h.length),'capture damaged before projectile flight');
 A.assert(b.kunai.length>0,'capture did not launch kunai');
 A.finish(1);A.assert(hits.every(h=>h.length===b.spec.kunaiRounds),'independent multi-hit rounds missing '+hits.map(h=>h.length));
 A.assert(S.stateFor(p).contacts.every(c=>c.geometry?.kind==='kunai-sweep'),'damage bypassed sweep');result.parallel={targets:3,rounds:b.spec.kunaiRounds,hits:hits.map(h=>h.length)};
 const body=G.ShikamaruReferenceGeometry.bodyFor(p);p.aim=0;const first=S.projectionFor(p);p.aim=2.7;const second=S.projectionFor(p);A.assert(JSON.stringify(first.matrix)===JSON.stringify(second.matrix),'aim rotated foot shadow');result.fixedDirection=true;
 m=setup();es=[A.spawn(160,0),A.spawn(0,160),A.spawn(-160,0)];hits=es.map(A.watch);A.cast(m);b=S.casts.at(-1);es[0].dead=true;es[0].hp=0;A.finish(1.7);A.assert(hits[1].length&&hits[2].length,'dead A stopped independent B/C');result.independent=true;
 m=setup();es=[A.spawn(160,0)];hits=es.map(A.watch);A.cast(m);b=S.casts.at(-1);while(!b.kunai.length)A.step(.01);es[0].x=800;es[0].y=800;A.finish(1);A.assert(hits[0].length===0,'projectile magically hit evaded target');result.evaded=true;
 m=setup();es=[A.spawn(160,0)];hits=es.map(A.watch);A.cast(m);b=S.casts.at(-1);while(!b.kunai.length)A.step(.01);G.World.projectilePathClear=()=>false;A.finish(1);A.assert(!hits[0].length,'kunai crossed wall');result.wall=true;
 for(const reason of ['clear','death','world','unlearn','pause']){
  m=setup();es=[A.spawn(160,0),A.spawn(0,160)];hits=es.map(A.watch);A.cast(m);b=S.casts.at(-1);while(!b.kunai.length)A.step(.01);
  const world=G.World;if(reason==='clear')S.clear(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};if(reason==='unlearn')p.moves=[];
  try{if(reason==='pause')S.update(2);else A.finish(1)}finally{p.dead=false;G.World=world}A.assert(!hits.some(h=>h.length),'lifecycle leaked '+reason);
 }result.lifecycle=true;
 m=setup();es=[A.spawn(160,0),A.spawn(0,160)];hits=es.map(A.watch);const hurt=es[0].hurt;es[0].hurt=function(...args){const r=hurt.apply(this,args);S.clear(p);return r};A.cast(m);A.finish(1.8);A.assert(hits[0].length===1&&!hits[1].length,'hurt callback failed to cancel other target');result.callback=true;
 for(const mode of ['hurt','onDealt']){
  m=setup();es=[A.spawn(160,0),A.spawn(0,160)];hits=es.map(A.watch);const dealt=p.onDealt;
  if(mode==='onDealt')p.onDealt=()=>S.clear(p);else{const h=es[0].hurt;es[0].hurt=function(...args){const r=h.apply(this,args);S.clear(p);return r}}
  try{A.cast(m);A.finish(1.8);A.assert(hits.reduce((n,h)=>n+h.length,0)===1,'callback leaked '+mode)}finally{p.onDealt=dealt}
 }
 m=setup(5,16);es=Array.from({length:16},(_,i)=>A.spawn(Math.cos(i*Math.PI/8)*180,Math.sin(i*Math.PI/8)*180));hits=es.map(A.watch);A.cast(m);b=S.casts.at(-1);A.finish(1.7);A.assert(hits.every(h=>h.length===5),'maximum target budget dropped hits '+hits.map(h=>h.length));result.maximum={targets:16,hits:hits.reduce((n,h)=>n+h.length,0)};
 const growth=[];for(const [rank,q]of [[1,0],[1,1],[3,0],[5,0],[5,16]]){m=setup(rank,q);const spec=S.profile(p,m);growth.push({rank,q,targets:spec.branches,rounds:spec.kunaiRounds})}A.assert(growth[1].targets===growth[0].targets+1&&growth[4].targets===16,'quantity contract mismatch');result.growth=growth;
 setup();return result;
}'''

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 report={'controlled':True,'checks':{},'errors':[]}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
  page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block');page.on('pageerror',lambda e:report['errors'].append(str(e)))
  base.boot(page);page.evaluate('window.WarmEnemy=Acceptance.spawn(160,0)');page.wait_for_function('!!G.ShikamaruReferenceGeometry.bodyFor(WarmEnemy)',timeout=60000);report['checks']=page.evaluate(CHECK)
  for name,width,height in [('desktop',1100,850),('mobile390',390,844)]:
   page.set_viewport_size({'width':width,'height':height})
   page.evaluate('''()=>{const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.reset();A.fixture('naruto-shikamaru',3);[A.spawn(160,0),A.spawn(0,160),A.spawn(-160,0)];A.cast(p.moves[0]);A.finish(.53)}''')
   page.screenshot(path=str(OUT/(name+'.png')))
  page.set_viewport_size({'width':1100,'height':850})
  page.evaluate("""()=>{const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.reset();A.fixture('naruto-shikamaru',3);window.NativeTargets=[A.spawn(160,0),A.spawn(0,160),A.spawn(-160,0)];window.NativeHits=NativeTargets.map(A.watch);Acceptance.resume()}""")
  page.wait_for_function('NativeHits.every(h=>h.length>=4)',timeout=12000)
  report['native']=page.evaluate("""()=>{const S=G.NarutoShikamaru,p=Acceptance.p();return {hits:NativeHits.map(h=>h.length),cycles:S.stateFor(p).cycles,clock:S.stateFor(p).clock}}""")
  page.keyboard.down('d');page.wait_for_timeout(500);page.keyboard.up('d')
  report['native']['moved']=page.evaluate('Math.abs(Acceptance.p().x)>10')
  assert report['native']['moved'],report['native']
  page.evaluate('Acceptance.pause()');page.screenshot(path=str(OUT/'native-moving.png'))
  browser.close()
 assert not report['errors'],report['errors']
 report['ok']=True;(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
