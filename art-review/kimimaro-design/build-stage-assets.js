/* Reuse existing project sprites for a representative game-context preview. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=__dirname,repo=path.resolve(root,'../..'),target=path.join(root,'stage');
fs.mkdirSync(target,{recursive:true});
const context={G:{}};vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(repo,'js/data/sprites-meta.js'),'utf8'),context);
const sprites=[];
for(const id of ['19','43','217']){
  const source=context.G.SPRITE_META[id];
  if(!source)throw new Error('Missing existing sprite metadata '+id);
  const def={id,shadow:source.s};
  for(const [key,anim] of [['idle','Idle'],['hurt','Hurt']]){
    const from=path.join(repo,'assets/pokemon',id,anim+'.png');
    const filename=id+'-'+key+'.png',to=path.join(target,filename);
    fs.copyFileSync(from,to);
    def[key]={...source.a[anim],image:'stage/'+filename,
      source:'assets/pokemon/'+id+'/'+anim+'.png',bytes:fs.statSync(to).size,
      sha256:crypto.createHash('sha256').update(fs.readFileSync(to)).digest('hex')};
  }
  sprites.push(def);
}
const props={};
for(const [type,w,h] of [['tree',30,40],['rock',22,17],['grass',20,17]]){
  const filename='stage/'+type+'.png',file=path.join(root,filename);
  if(fs.existsSync(file))props[type]={image:filename,width:w,height:h,
    source:'js/world/tiles.js::propSprite(0,'+type+',0)',
    bytes:fs.statSync(file).size,sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')};
}
const data={scope:'existing game sprites reused only in independent art preview',
  source:'js/data/sprites-meta.js and assets/pokemon; code-painted tile props reused',pixelScale:2,normalIds:['19','43'],bossId:'217',sprites,props,
  sourceTransferBytes:sprites.reduce((sum,s)=>sum+s.idle.bytes+s.hurt.bytes,0)+Object.values(props).reduce((sum,p)=>sum+p.bytes,0),
  palette:{floor:['#3e7a39','#44813d','#397134'],dirt:['#7d6742','#735e3b','#86704a'],
    speck:'#2f5f2b',light:'#5f9d50',grass:['#2f6b2c','#4c9a3f','#7cc45a'],
    rock:['#5e6670','#7f8893','#a1aab4']}};
fs.writeFileSync(path.join(root,'stage-assets.json'),JSON.stringify(data,null,2)+'\n');
console.log(JSON.stringify({sprites:sprites.length,sheets:6,bytes:data.sourceTransferBytes,metadata:sprites.map(s=>({id:s.id,idle:s.idle}))}));
