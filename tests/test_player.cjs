const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const source = fs.readFileSync('web/player.js','utf8');

function environment(native) {
  let now=0, timers=[], intervals=[];
  const events={};
  const video={currentTime:0,src:'',buffered:{length:0},
    canPlayType:()=>native?'maybe':'',play:()=>Promise.resolve(),pause:()=>{},load:()=>{},
    removeAttribute:()=>{},addEventListener:(name,callback)=>events[name]=callback};
  const elements={tv:video,tunein:{value:'Play'},status:{style:{}},fslink:{},tvwrap:{}};
  class Hls {
    static instances=[];
    static Events={MANIFEST_PARSED:'manifest',ERROR:'error'};
    static ErrorTypes={MEDIA_ERROR:'media',NETWORK_ERROR:'network'};
    static isSupported(){return true;}
    constructor(){this.events={};this.destroyed=false;Hls.instances.push(this);}
    on(name,callback){this.events[name]=callback;}
    loadSource(){} attachMedia(){} destroy(){this.destroyed=true;} recoverMediaError(){this.recovered=true;}
  }
  const window={Hls,addEventListener:(name,callback)=>events['window-'+name]=callback};
  const context={window,Hls,document:{hidden:false,getElementById:id=>elements[id]},
    Date:{now:()=>now},setInterval:callback=>intervals.push(callback),
    setTimeout:(callback,delay)=>{let timer={callback,at:now+delay};timers.push(timer);return timer;},
    clearTimeout:timer=>{timers=timers.filter(item=>item!==timer);}};
  vm.runInNewContext(source,context);
  const advance=milliseconds=>{
    now+=milliseconds;
    for(const timer of [...timers])if(timer.at<=now){timers=timers.filter(item=>item!==timer);timer.callback();}
    for(const callback of intervals)callback();
  };
  return {video,elements,events,Hls,advance,get timers(){return timers;}};
}

for(const native of [true,false]){
  const e=environment(native);e.elements.tunein.onclick();
  assert.equal(e.elements.status.textContent,'connecting');
  e.video.currentTime=1;e.events.timeupdate();
  assert.equal(e.elements.status.textContent,'live');
  e.events.error();assert.equal(e.elements.status.textContent,'reconnecting');
  e.events.error();assert.equal(e.timers.length,1,'Only one reconnect timer');
  e.advance(2000);assert.equal(e.elements.status.textContent,'connecting');
  e.video.currentTime=2;e.events.timeupdate();
  assert.equal(e.elements.status.textContent,'live');
  e.advance(13000);assert.equal(e.elements.status.textContent,'reconnecting','Silent stall must reconnect');
  e.elements.tunein.onclick();assert.equal(e.elements.status.textContent,'offline');
  e.advance(30000);assert.equal(e.elements.status.textContent,'offline','Stopped player must not restart');
  if(!native)assert(e.Hls.instances.every(instance=>instance.destroyed));
}

const e=environment(false);e.elements.tunein.onclick();
let hls=e.Hls.instances[0];
hls.events.error(null,{fatal:true,type:'media'});assert(hls.recovered);
hls.events.error(null,{fatal:true,type:'media'});assert(hls.destroyed);
assert.equal(e.elements.status.textContent,'reconnecting');
e.events['window-pagehide']();assert.equal(e.timers.length,0);
console.log('Player recovery checks passed for native HLS and hls.js.');
