/* Practice controls must share the local-only boundary of dev-controls.js. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../.omx/trial-build.js'),'utf8');

function load(host,query='?startLevel=20&hero=jjk-yuta'){
  const created=[],inserted=[],location=new URL('http://'+host+'/.omx/digimon.html'+query);
  const nativeOpen=()=> 'native-menu';
  const G={MenuUI:{open:nativeOpen},DB:{save:{partner:30013}},Naruto:{records:new Map([[30013,{slug:'jjk-yuta'}]])}};
  const document={
    createElement(tag){
      const element={tag,style:{},children:[],attributes:{},append(...nodes){this.children.push(...nodes);},
        replaceChildren(...nodes){this.children=nodes;},setAttribute(key,value){this.attributes[key]=value;}};
      created.push(element);return element;
    },
    querySelector(selector){assert.equal(selector,'.launch-action');return {before(element){inserted.push(element);}};}
  };
  vm.runInNewContext(source,{G,location,document,URL,URLSearchParams,history:{replaceState(_state,_title,url){location.href=url.href;}}});
  return {G,created,inserted,nativeOpen,location};
}

for(const host of ['tim12332000.github.io','example.com','localhost.example.com']){
  const result=load(host);
  assert.equal(typeof result.G.TrialBuild.apply,'function','public runtime lost recipe API');
  assert.equal(result.G.TrialBuild.routes[30013].join(','),'blade,rika');
  assert.equal(result.created.length,0,'public query created local-only practice controls');
  assert.equal(result.inserted.length,0);
  assert.equal(result.G.MenuUI.open,result.nativeOpen,'public query wrapped the normal menu flow');
}
for(const host of ['localhost','127.0.0.1','[::1]']){
  const result=load(host);
  assert.notEqual(result.G.MenuUI.open,result.nativeOpen,'local trial query did not install controls');
  assert.equal(result.inserted.length,1);
  assert.equal(result.inserted[0].id,'trial-build-options');
  assert.equal(result.G.MenuUI.open(),'native-menu','local wrapper changed native return value');
  assert.equal(result.inserted[0].hidden,false);
  assert.equal(result.inserted[0].children[1].children.length,4,'local recipe choices missing');
}
const normal=load('localhost','?hero=jjk-yuta');
assert.equal(normal.created.length,0,'normal local menu unexpectedly shows practice controls');
assert.equal(normal.G.MenuUI.open,normal.nativeOpen);
console.log('PASS: public practice queries preserve recipe API and menu flow; local hosts alone receive trial controls.');
