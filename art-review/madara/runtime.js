/* Original generated Madara sprites. Side views are mirrored, not eight authored directions. */
(() => {
  'use strict';
  const scriptURL = new URL(document.currentScript.src), base = new URL('./', scriptURL);
  let metadata, pending;
  const images = {}, whites = {};
  const api = {loaded:false, load, sample, draw, socketFor, avatarSample, avatarSocketFor, drawAvatar, drawElement,
    get metadata(){return metadata;}, get images(){return images;}};
  function load() {
    if (pending) return pending;
    pending = (async () => {
      const metadataURL = new URL('frames.json', base); metadataURL.search = scriptURL.search;
      const response = await fetch(metadataURL);
      if (!response.ok) throw Error('Madara animation metadata unavailable');
      metadata = await response.json();
      await Promise.all(Object.entries({common:metadata,...metadata.sheets}).map(async ([key,sheet]) => {
        const image = new Image(), url = new URL(sheet.source,base);url.searchParams.set('v',sheet.sha256);
        image.src=url.href;await image.decode();images[key]=image;
      }));
      api.loaded = true; return api;
    })().catch(error => { pending = null; throw error; });
    return pending;
  }
  function directionFor(dir=0,pose=null) {
    if(pose?.aim!=null){const x=Math.cos(pose.aim),y=Math.sin(pose.aim);return Math.abs(x)>=Math.abs(y)?x<0?'left':'right':y<0?'up':'down';}
    return typeof dir==='string'?dir:['down','right','right','right','up','left','left','left'][((dir||0)%8+8)%8];
  }
  function frameAt(sheet,index,mirror=false) {
    const data=sheet==='common'?metadata:metadata?.sheets?.[sheet], frame=data?.frames[index];
    return frame?{...frame,index,sheet,bodyHeight:data.bodyHeight,mirror,source:data.source}:null;
  }
  function sample(state='idle', time=0, dir=0, pose=null) {
    if (!metadata) return null;
    const age = Math.max(0, Number(time)||0);
    const direction=directionFor(dir,pose),mirror=direction==='left';
    if(pose?.kind==='basic'&&metadata.sheets?.taijutsu) {
      const contact=pose.contact||['palm','elbow','kick','landing'][(pose.index||0)%4],phase=pose.phase||'contact';
      if((direction==='up'||direction==='down')&&metadata.sheets.bodyDirections){
        const offset=direction==='up'?4:0;
        const index=phase==='windup'&&contact==='landing'?2:phase==='approach'||phase==='windup'||phase==='recover'?3:contact==='elbow'?1:contact==='kick'?2:contact==='landing'?3:0;
        return frameAt('bodyDirections',offset+index);
      }
      const index=phase==='approach'?0:phase==='windup'?({palm:0,elbow:2,kick:5,landing:4}[contact]??0):
        phase==='recover'?({palm:2,elbow:4,kick:7,landing:9}[contact]??9):({palm:1,elbow:3,kick:6,landing:8}[contact]??1);
      return frameAt('taijutsu',index,mirror);
    }
    if(!pose&&!['faint','death','hurt'].includes(state)&&(direction==='up'||direction==='down')){
      if((state==='walk'||state==='move')&&metadata.sheets?.walkDirections)
        return frameAt('walkDirections',(direction==='up'?4:0)+Math.floor(age*4.5)%4);
      if(metadata.sheets?.bodyDirections)return frameAt('bodyDirections',direction==='up'?7:3);
    }
    if(pose&&metadata.sheets?.castingDirections&&(direction==='up'||direction==='down')){
      const offset=direction==='up'?3:0,index=pose.phase==='recover'?2:pose.phase==='windup'||pose.phase==='charge'||pose.kind!=='fire'?0:1;
      return frameAt('castingDirections',offset+index);
    }
    let index = 0;
    if (state === 'faint' || state === 'death') index = age < .16 ? 14 : 15;
    else if (state === 'hurt') index = age < .12 ? 12 : 13;
    else if (pose || state === 'cast') {
      const kind = pose?.kind || 'basic', t = Math.max(0, pose?.age ?? age);
      if (kind === 'fire') index = t < .12 ? 4 : t < .25 ? 5 : t < .78 ? 6 : 7;
      else if (kind === 'meteor') index = t < .18 ? 4 : t < .42 ? 10 : t < 1.1 ? 10 : 11;
      else if (kind === 'clones') index = t < .14 ? 4 : t < .5 ? 5 : 7;
      else index = t < .10 ? 8 : t < .32 ? 9 : t < .48 ? 11 : 7;
    } else if (state === 'walk' || state === 'move') index = [1,0,2,0][Math.floor(age*9)%4];
    const result=frameAt('common',index,mirror);
    if(result&&!result.sockets){const [, ,w,h]=result.rect;result.sockets={mouth:[w*(index===6?.77:.72),h*(index===6?.27:.23)],palm:[w*.88,h*.45],elbow:[w*.68,h*.43],foot:[w*.82,h*.96]};}
    return result;
  }
  function paint(ctx,frame,{x=0,y=0,height=64,flash=false,alpha=1}={}) {
    if(!frame||!images[frame.sheet])return false;
    const [sx,sy,sw,sh]=frame.rect,k=height/frame.bodyHeight;
    ctx.save();ctx.translate(x,y);ctx.imageSmoothingEnabled=false;ctx.globalAlpha*=alpha;
    if(frame.mirror)ctx.scale(-1,1);
    if(flash&&!whites[frame.sheet]){
      const image=images[frame.sheet],white=document.createElement('canvas');white.width=image.width;white.height=image.height;
      const c=white.getContext('2d');c.drawImage(image,0,0);c.globalCompositeOperation='source-in';c.fillStyle='#fff';c.fillRect(0,0,white.width,white.height);
      whites[frame.sheet]=white;
    }
    ctx.drawImage(flash?whites[frame.sheet]:images[frame.sheet],sx,sy,sw,sh,-frame.anchor[0]*k,-frame.anchor[1]*k,sw*k,sh*k);
    ctx.restore();return true;
  }
  function draw(ctx, actor={}, options={}) {
    const {x=0,y=0,height=64,state='idle',time=0,dir=0,pose=null,flash=false,alpha=1} = options;
    return api.loaded&&paint(ctx,sample(state,time,dir,pose),{x,y,height,flash,alpha});
  }
  function pointFor(frame,name,x,y,height) {
    const socket=frame?.sockets?.[name];if(!socket)return null;
    const k=height/frame.bodyHeight,dx=(socket[0]-frame.anchor[0])*k*(frame.mirror?-1:1),dy=(socket[1]-frame.anchor[1])*k;
    return {x:x+dx,y:y+dy,height:-dy,space:'visual-world',sheet:frame.sheet,index:frame.index};
  }
  function socketFor(actor,name,options={}) {
    const {pose=null,dir=actor.anim?.dir||0,height=64,state=pose?'cast':'idle',time=pose?.age||0}=options;
    return pointFor(sample(state,time,dir,pose),name,options.x??actor.x??0,options.y??actor.y??0,height);
  }
  function avatarSample(form='rib',phase='manifest',age=0,aim=0,options={}) {
    const direction=directionFor(0,{aim}),directional=direction==='up'||direction==='down';
    if(form==='rib'&&direction==='down'&&(phase==='sweep'||phase==='contact')&&metadata?.sheets?.ribDown)
      return frameAt('ribDown',0);
    const key=directional?form+'Directions':form,sheet=metadata?.sheets?.[key];if(!sheet)return null;
    let index;
    if(directional)index=(direction==='up'?2:0)+(phase==='sweep'||phase==='contact'?1:0);
    else if(sheet.frames.length===4)index=phase==='manifest'?0:phase==='draw'?1:phase==='sweep'||phase==='contact'?((options.progress??0)<.5?2:3):age<.12?3:0;
    else index=phase==='manifest'?0:phase==='draw'?(age<.12?1:2):phase==='sweep'||phase==='contact'?((options.progress??0)<.5?3:4):5;
    return frameAt(key,index,direction==='left');
  }
  function avatarSocketFor(actor,name,options={}) {
    const {form='rib',phase='manifest',age=0,aim=0,height=200}=options;
    return pointFor(avatarSample(form,phase,age,aim,options),name,options.x??actor.x??0,options.y??actor.y??0,height);
  }
  function drawAvatar(ctx,options={}) {
    const {form='rib',phase='manifest',age=0,aim=0}=options;
    return api.loaded&&paint(ctx,avatarSample(form,phase,age,aim,options),options);
  }
  function drawElement(ctx,options={}) {
    const {kind,phase,x=0,y=0,alpha=1}=options;
    const sheet=kind==='wood'?'wood':'elements';if(!api.loaded||!metadata?.sheets?.[sheet])return false;
    const index=kind==='wood'?({root:0,separate:1,reveal:2,dismiss:3}[phase]??0):kind==='fire'?(phase==='tail'?2:phase==='wall'?1:0):kind==='meteor'?3:kind==='fracture'?4:5;
    const frame=frameAt(sheet,index),[sx,sy,sw,sh]=frame.rect;
    if(kind==='wood')return paint(ctx,frame,{x,y,height:options.height??64,alpha});
    ctx.save();ctx.translate(x,y);ctx.globalAlpha*=alpha;ctx.imageSmoothingEnabled=false;
    if(kind==='fire'){
      const width=options.width??150,depth=options.depth??72;
      if(phase==='wall'){
        // This source's broad axis is horizontal and its flame tips point up.
        ctx.rotate((options.aim||0)+Math.PI/2);
        ctx.drawImage(images.elements,sx,sy,sw,sh,-width*.5,-depth*.5,width,depth);
      }else{
        // Burst/tail tiles point right; distribute several undistorted tongues
        // across the same wall width instead of squeezing one long image.
        ctx.rotate(options.aim||0);const count=Math.max(1,Math.min(7,Math.ceil(width/70))),span=width/count;
        for(let i=0;i<count;i++)ctx.drawImage(images.elements,sx,sy,sw,sh,-depth*.5,-width*.5+i*span,depth,span);
      }
    }else{
      const radius=options.radius??80;
      ctx.drawImage(images.elements,sx,sy,sw,sh,-radius,-radius,radius*2,radius*2);
    }
    ctx.restore();return true;
  }
  Object.defineProperty(api,'ready',{get:load});
  G.MadaraArt = api;
})();
