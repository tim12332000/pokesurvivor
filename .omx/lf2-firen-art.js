/* Firen uses the same original-LF2 frame, socket and effect renderer. */
(() => {
  'use strict';
  if (G.LF2FirenArt) return;
  const DEX=30021, art=G.LF2BossArt;
  if (!art?.register) throw Error('Classic LF2 art renderer must load before Firen');
  art.register(DEX,{slug:'firen',height:64,api:()=>G.LF2Firen});
  const load=()=>art.load(DEX),isReady=()=>art.isReady(DEX);
  G.LF2FirenArt={
    load,isReady,
    draw:(ctx,actor={},options={})=>art.draw(ctx,actor,{...options,dex:DEX}),
    pointFor:(actor,pose,name='release')=>art.pointFor(actor,pose,name),
    drawEffects:ctx=>art.drawEffects(ctx,DEX),
    playSound:(id,owner=G.Game.player)=>G.LF2Audio?.play(id,owner,art.metadataFor(DEX)),
    stopSounds:owner=>art.stopSounds(owner),
    frame:(key,id)=>art.frame(DEX,key,id),
    sequence:(key,start,age,loop=false)=>art.sequence(DEX,key,start,age,loop),
    sample:(state='idle',time=0,dir=0,pose=null)=>art.sample(DEX,state,time,dir,pose),
    get ready(){return load();},get loaded(){return isReady();},
    get metadata(){return art.metadataFor(DEX);},get images(){return art.images[DEX]||{};}
  };
})();
