"""Compare native wind rendering with its stable-sort reference, without game hooks."""
import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_temari import CHROME

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/temari-front-selection'
REFERENCE = """const b=a.cast||{},fronts=[];
      for(const wave of group)for(const front of wave.fronts||[])if(!front.done&&front.reach>2)fronts.push({wave,front});
      fronts.sort((a,b)=>b.front.reach-a.front.reach);
      const selected=[];
      for(const f of fronts)if(selected.every(p=>Math.abs(p.front.reach-f.front.reach)>Math.max(34,(b.range||240)*.2))) {
        selected.push(f);if(selected.length===3)break;
      }
      """
CHECK = r"""({source,reference})=>{
 const start=source.indexOf('const b=a.cast||{}'),end=source.indexOf('for(let i=0;i<selected.length;i++) {',start);
 if(start<0||end<0)throw Error('selection block not found');
 const current=source.slice(start,end),oldSource=source.slice(0,start)+reference+source.slice(end);
 const expose=s=>s.replace('for(let i=0;i<selected.length;i++) {',
  '__selection.push(selected.map(f=>[f.wave.id,f.front.id])); for(let i=0;i<selected.length;i++) {');
 window.G={LIFT:6,Camera:{sees:(x,y,r)=>x+r>=0&&x-r<=900&&y+r>=0&&y-r<=700}};
 window.__selection=[];eval(expose(oldSource));const before=G.TemariCycloneVFX;
 eval(expose(source));const after=G.TemariCycloneVFX;
 let seed=24929;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
 const cases=[];let id=0;
 const wave=(reaches,extra={})=>({id:id++,x:430,y:350,aim:.1,cast:{range:240,arc:Math.PI},
  fronts:reaches.map((reach,id)=>({id,reach,done:false})),...extra});
 for(const reaches of [[],[0,2,2.00001],[190,190,140,140,90],
  [200,152,104,56],[200,152.00001,151.99999,104,55.99999],[2,3,4,5],
  [300,200,100,50],[120,168,216,72]])cases.push([wave(reaches)]);
 cases.push([wave([210,150]),wave([210,150,90])]);
 cases.push([wave([Infinity,Infinity,200,NaN,-Infinity,undefined,2])]);
 cases.push([wave([210],{dead:true}),wave([180],{x:-1000}),wave([140,90])]);
 cases.push([wave([210,160,110],{cast:{range:240,arc:2,kind:'heavy'}})]);
 cases.push([wave([210,160,110],{cast:{range:240,arc:2}}),wave([210,160,110],{owner:{},x:600})]);
 for(let i=0;i<450;i++){
  const range=[120,240,310,440][i%4],owner={};
  const group=Array.from({length:1+i%15},()=>wave(Array.from({length:i%31},()=>
   random()<.3?Math.floor(random()*8)*Math.max(34,range*.2):random()*range),
   {owner,cast:{range,arc:i%5===0?Math.PI:.7,kind:i%3?'basic':'heavy'}}));
  for(const w of group)for(const f of w.fronts)if(random()<.1)f.done=true;
  cases.push(group);
 }
 const c=document.createElement('canvas');c.width=900;c.height=700;document.body.append(c);
 const ctx=c.getContext('2d',{willReadFrequently:true}),commands=[];
 const tracked=new Proxy(ctx,{get(t,k){const v=t[k];return typeof v==='function'?(...args)=>{
  commands.push([k,...args]);return v.apply(t,args)}:v},set(t,k,v){commands.push(['set',k,v]);t[k]=v;return true}});
 const draw=(api,waves)=>{ctx.clearRect(0,0,900,700);commands.length=0;__selection=[];
  api.drawAir(tracked,{waves});return {commands:JSON.stringify(commands),selection:JSON.stringify(__selection)}};
 let commandCount=0,selectedCount=0;
 for(let i=0;i<cases.length;i++){
  const old=draw(before,cases[i]),pixels=c.toDataURL();commandCount+=commands.length;
  const next=draw(after,cases[i]);
  if(old.selection!==next.selection||old.commands!==next.commands||pixels!==c.toDataURL())
   throw Error('native Canvas mismatch case '+i+' '+old.selection+' / '+next.selection);
  selectedCount+=JSON.parse(next.selection).flat().length;
 }
 const representative=[wave([206,157,108,59]),wave([206,157,108,59])];
 draw(before,representative);const beforeImage=c.toDataURL();
 draw(after,representative);const afterImage=c.toDataURL();
 const select=s=>new Function('group',`const a=group[0]; ${s} return selected;`),oldSelect=select(reference),newSelect=select(current);
 const group=Array.from({length:45},()=>wave(Array.from({length:35},()=>random()*310)));
 let sink=0;const measure=fn=>{const samples=[];for(let n=0;n<9;n++){const t=performance.now();
  for(let j=0;j<600;j++)sink+=fn(group).length;samples.push((performance.now()-t)/600)}
  samples.sort((a,b)=>a-b);return samples[4]};
 for(let i=0;i<250;i++){oldSelect(group);newSelect(group)}
 return {cases:cases.length,selectedCount,commandCount,pixelEquivalent:true,
  beforeImage,afterImage,selectionMs:{reference:measure(oldSelect),current:measure(newSelect)},fronts:1575,sink};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = (ROOT / '.omx/temari-cyclone-vfx.js').read_text(encoding='utf-8')
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(viewport={'width': 900, 'height': 700})
        result = page.evaluate(CHECK, {'source': source, 'reference': REFERENCE})
        for name in ('before', 'after'):
            (OUT / f'{name}.png').write_bytes(base64.b64decode(result.pop(f'{name}Image').split(',')[1]))
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
