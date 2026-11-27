/* EXPERIMENT, NOT IN THE APP (task GS3): drawing a scrolled arrangement by shifting the old picture and drawing only strips.
   It needed two hooks in drawArr (const ASB=ascBegin(g,w,h) after clampV, ascEnd(g,ASB) after thUnder, and `const ASCRAW=drawArr` after the function).
   This is the first version (one clip made of several rectangles, and a copy of the canvas onto itself). Measured on the cloud machine's software renderer it was no faster
   than a full drawing (backlog log, task GS3), so it was left out; the later version drew each strip as its own pass through a second canvas, also no faster there.
   Kept for a test on a real graphics card. */
/* --- v0.228 (task GS3, glass step 3): frame time. Measured with tools/ui-tests/frametime.py (the user's window size, Fractals song open, one part switched off at a time).
   1. Scrolling the arrangement moves pixels instead of drawing them again (ascBegin / ascEnd, called from drawArr):
      when the only thing that changed since the last full drawing is where the view is (sideways, or up and down by whole screen pixels), the canvas is
      shifted onto itself by that many screen pixels and only these strips are drawn again: the edge that came into view, the part next to the track
      headers where names stay put while their clip slides under them (clip names, section names, the loop label, the hint in an empty track), the
      ruler's top band and the master lane (it shows the level while playing). Clips that lie wholly outside those strips are not drawn at all.
      Anything else that changed (an edit, the selection, hovering a clip, a drag, recording, the overview, the theme) makes the next drawing a full one,
      and so do these safety nets: a full drawing after 48 shifted ones (a fifth of a second at 240 Hz) or a second, whichever comes first, and one 6 frames after the view stops.
      Sideways the view is put on the screen's pixel grid (at most half a screen pixel), so the shifted picture is the same as a new drawing.
   2. Things that drew the same picture again and again while nothing changed: the master meter in the top bar (120 times a second, also in silence)
      draws only when what it shows changed; the logo in Settings draws at most 60 pictures a second (it drew up to 160).
   3. drawArr's last part asked the page where the "add track" row is on every full drawing (a forced layout); that answer is kept until the rows change.
   4. The frame-rate read-out (Settings > Performance, "Frame-rate read-out on screen"): a small badge in the corner with the frames per second and
      the slowest frame of the last 5 seconds, updated twice a second. Saved in UI.fpsHud. */
const ASC={on:true,sub:null,zall:null,b:null,bg:null,gen:0,sig:null,vx:0,vy:0,W:0,H:0,full:0,force:0,fc:0,pend:0,quiet:0,z:null,cur:null,n:{full:0,fast:0,skip:0,why:{}}};
function ascSig(w,h){const s=S.sections||[];let sh=s.length;for(const c of s)sh=(sh*31+c.start*64+c.len*8+(c.name||'').length+(c.color||'').length)%1e9;
  return[arr.width,arr.height,DPX,X0,TY,BY,AY,HDRW,V.ppb,V.th,TOTH,S.tracks.length,selT,selC,SELCS.size,hovC,ASC.gen,gleSig(),sh,loopA(),loopB(),S.loopRange?S.loopRange.a+'-'+S.loopRange.b:'',
    TMPH(),UI.gridB??50,UI.subTicks!==false,UI.bars4!==false,UI.tracksRight?1:0,UI.lite?1:0,TH.bg,TH.ruler,TH.under||'',TH.secBg||'',MAP.d?MAP.d.N:0].join('|')}
/* may this drawing only shift the picture and draw strips? (why not: counted in ASC.n.why, for the test) */
function ascWhy(){if(!ASC.on)return'off';if(REC.on)return'rec';if(ad||md||SELR||FDRAG||CAPDRAG)return'drag';if(OVW.on||OVW.a)return'overview';if(PREVMAP)return'preview';if(BOOTF!=null)return'boot';if(ASC.force)return'forced';
  if(ASC.fc>=48||performance.now()-ASC.full>1000)return'age';return''}
function ascBegin(g,w,h){
  if(ASC.sub){/* one strip of a shifted drawing: a plain rectangle clip, so the browser draws only inside it */const r=ASC.sub,d=DPX;g.save();g.setTransform(1,0,0,1,0,0);g.beginPath();g.rect(Math.floor(r[0]*d),Math.floor(r[1]*d),Math.ceil(r[2]*d)+2,Math.ceil(r[3]*d)+2);g.clip();g.setTransform(d,0,0,d,0,0);ASC.z=[r];return 2}
  ASC.z=null;layoutRows();const sig=ascSig(w,h);ASC.cur=sig;let why=ascWhy();
  if(!why&&(sig!==ASC.sig||arr.width!==ASC.W||arr.height!==ASC.H))why='changed';
  let dx=0,dy=0;
  if(!why){const d=DPX,dxd=(ASC.vx-V.x)*V.ppb*d,dyd=(ASC.vy-V.y)*d;dx=Math.round(dxd);dy=Math.round(dyd);
    if(Math.abs(dyd-dy)>1e-3)why='y-grid';
    else{if(Math.abs(dxd-dx)>1e-6){const vx=ASC.vx-dx/(V.ppb*d);V.x=vx;clampV();if(Math.abs(V.x-vx)>1e-9)why='edge'}
      if(!why&&!dx&&!dy)why='still';if(!why&&(Math.abs(dx)>arr.width*.6||Math.abs(dy)>arr.height*.6))why='far'}}
  if(why){ASC.n.why[why]=(ASC.n.why[why]||0)+1;return 0}
  /* the shift: the rows, sideways and up or down, read from the canvas as it was (the band above them is drawn again, it is short).
     Through a second canvas: drawing a canvas onto itself makes the browser copy it first, which measured 4 to 5 times slower. */
  const W=arr.width,H=arr.height,d=DPX,ay=Math.round(AY*d);
  const B=ASC.b||(ASC.b=document.createElement('canvas'));if(B.width!==W||B.height!==H-ay){B.width=W;B.height=H-ay;ASC.bg=B.getContext('2d',{alpha:false})}
  ASC.bg.drawImage(arr,0,ay,W,H-ay,0,0,W,H-ay);g.save();g.setTransform(1,0,0,1,0,0);g.beginPath();g.rect(0,ay,W,H-ay);g.clip();g.drawImage(B,dx,ay+dy);g.restore();
  /* the strips that are drawn again, in CSS pixels; each one is a pass of its own with a plain rectangle clip (one clip made of several rectangles
     measured no cheaper than the whole drawing: the browser then works through the whole canvas for every shape) */
  const Z=[],add=(x,y,ww,hh)=>{x=Math.max(0,x);y=Math.max(0,y);ww=Math.min(w-x,ww);hh=Math.min(h-y,hh);if(ww>0&&hh>0)Z.push([x,y,ww,hh])},SW=460,cx=dx/d,cy=dy/d;
  add(0,0,w,AY);                                                   /* everything above the rows: the ruler and sections band is short, and some of it stays put */
  if(UI.tracksRight){add(0,AY,Math.max(SW,cx+2),h-AY);const rx=Math.min(w-HDRW-2,cx<0?w+cx-2:w);add(rx,AY,w-rx,h-AY)}
  else{add(0,AY,Math.max(X0+SW,cx+2),h-AY);/* the right edge (thin scroll marks there stay put) and what came into view there */const rx=Math.min(w-14,cx<0?w+cx-2:w);add(rx,AY,w-rx,h-AY)}
  if(cy<0)add(0,h+cy-2,w,-cy+2);else if(cy>0)add(0,AY,w,cy+2);
  {const y=AY+TOTH+MSY0-V.y,mh=mshOf();if(y<h&&y+mh>AY)add(0,y-2,w,mh+4)}
  if(TH.under&&BY>0)add(0,h-BY,w,BY);
  for(let i=1;i<Z.length;i++){ASC.sub=Z[i];try{ASCRAW(false)}finally{ASC.sub=null}}
  {const r=Z[0];g.save();g.setTransform(1,0,0,1,0,0);g.beginPath();g.rect(Math.floor(r[0]*d),Math.floor(r[1]*d),Math.ceil(r[2]*d)+2,Math.ceil(r[3]*d)+2);g.clip();g.setTransform(d,0,0,d,0,0)}
  ASC.z=[Z[0]];ASC.zall=Z;ASC.n.fast++;ASC.n.strips=(ASC.n.strips||0)+Z.length;return 1}
function ascEnd(g,mode){if(mode===2){g.restore();ASC.z=null;return}
  if(mode===1){g.restore();ASC.z=null;ASC.fc++;ASC.pend=1;ASC.quiet=0}
  else{ASC.full=performance.now();ASC.force=0;ASC.fc=0;ASC.pend=0;ASC.n.full++}
  ASC.sig=ASC.cur;ASC.vx=V.x;ASC.vy=V.y;ASC.W=arr.width;ASC.H=arr.height}
/* the safety net after scrolling: once 6 frames went by without a shifted drawing, one full drawing */
{const _f0=frame0;frame0=function(now){const r=_f0.apply(this,arguments);if(ASC.pend&&++ASC.quiet>=6){ASC.pend=0;ASC.force=1;dirty=true}return r}}
function ascHit(x,y,w,h){const Z=ASC.z;if(!Z)return true;for(const r of Z)if(x<r[0]+r[2]&&x+w>r[0]&&y<r[1]+r[3]&&y+h>r[1])return true;ASC.n.skip++;return false}
{const _dc=drawClipC;drawClipC=function(g,t,c,G,w){if(ASC.z&&!ascHit(G.x-6,G.y-6,G.w+12,G.h+12))return;return _dc.apply(this,arguments)}}
{const _ch=changed;changed=function(){ASC.gen++;return _ch.apply(this,arguments)}}
/* a waveform is drawn one screen column at a time: inside a strip only the columns of that strip are drawn (a long audio clip across the screen
   is otherwise thousands of columns for a strip of a few pixels). Only on the arrangement canvas itself, never into a clip's cached picture. */
{const _mw=miniWave;miniWave=function(g,c,x,y,w,h,col,xmin,xmax,PP){const Z=ASC.z;if(Z&&g&&g.canvas===arr){const r=Z[0];xmin=Math.max(xmin,r[0]-2);xmax=Math.min(xmax,r[0]+r[2]+2);if(xmax<=xmin)return}return _mw.call(this,g,c,x,y,w,h,col,xmin,xmax,PP)}}
/* where the "add track" row sits inside the header column: kept until the rows change (it was a forced layout on every full drawing) */
const ASCY={k:'',v:0,t:0,hk:'',hv:0};
function ascAddY(){const k=[TOTH,V.th,S.tracks.length,hdrin.childElementCount,ASC.gen,UI.tracksRight?1:0,mshOf(),ZOOM].join('|'),n=performance.now();
  if(k!==ASCY.k||n-ASCY.t>2000){ASCY.k=k;ASCY.t=n;const ab=hdrin.querySelector('.addrow button'),ar=ab&&ab.closest('.addrow');ASCY.v=ab&&ar?ar.offsetTop+ab.offsetTop+ab.offsetHeight/2:TOTH+34}return ASCY.v}
function ascHcH(hc,h){const k=arr.height+'|'+innerHeight+'|'+ZOOM+'|'+BY+'|'+TY,n=performance.now();if(k!==ASCY.hk||n-ASCY.ht>2000){ASCY.hk=k;ASCY.ht=n;ASCY.hv=hc.clientHeight}return ASCY.hv||h}

/* ---- the frame-rate read-out ---- */
const FHUD={el:null,iv:new Float64Array(4096),at:new Float64Array(4096),i:0,n:0,t:0,last:0};
{const _ft=fpsTrack;fpsTrack=function(now){if(FHUD.last&&UI.fpsHud){const d=now-FHUD.last;if(d>0&&d<1000){const i=FHUD.i;FHUD.iv[i]=d;FHUD.at[i]=now;FHUD.i=(i+1)&4095;FHUD.n=Math.min(4096,FHUD.n+1)}}FHUD.last=now;
  const r=_ft.apply(this,arguments);if(UI.fpsHud&&now-FHUD.t>=500){FHUD.t=now;try{fhudPaint(now)}catch(e){}}return r}}
function fhudWorst(now,ms){let w=0,k=FHUD.i;for(let j=0;j<FHUD.n;j++){k=(k-1)&4095;if(now-FHUD.at[k]>ms)break;if(FHUD.iv[k]>w)w=FHUD.iv[k]}return w}
function fhudPaint(now){let el=FHUD.el;if(!el){el=FHUD.el=document.createElement('div');el.id='fpsHud';el.setAttribute('role','status');el.setAttribute('aria-live','off');el.innerHTML='<b></b><span></span>';document.body.appendChild(el)}
  const hz=FPS.hz||0,f=Math.min(FPS.fps,hz||FPS.fps),w=fhudWorst(now,5000),t1=f+' fps',t2='slowest '+(w?w.toFixed(1):'–')+' ms',c=!hz||f>=hz*.95?'ok':f>=hz*.7?'mid':'low';
  const b=el.firstChild,s=el.lastChild;if(b.textContent!==t1)b.textContent=t1;if(s.textContent!==t2)s.textContent=t2;if(el.dataset.c!==c)el.dataset.c=c;
  el.title='Frames per second now'+(hz?' (your screen: '+hz+' Hz)':'')+', and the slowest single frame of the last 5 seconds. Settings > Performance turns this off.'}
function fhudSet(on){UI.fpsHud=!!on;saveUI();FHUD.n=0;FHUD.i=0;FHUD.last=0;if(!on&&FHUD.el){FHUD.el.remove();FHUD.el=null}if(on)fhudPaint(performance.now());const c=document.getElementById('fpsHudChk');if(c)c.checked=!!on}
function fhudUi(){const sec=document.querySelector('#setBody section[data-page=perf]');if(!sec||sec.querySelector('#fpsHudRow'))return;const lim=sec.querySelector('#pmLim');if(!lim)return;
  const r=document.createElement('div');r.className='pmhud';r.id='fpsHudRow';r.title='Shows the frames per second and the slowest frame of the last 5 seconds in the bottom right corner, on top of everything, so you can check the frame rate while you work.';
  r.innerHTML='<span>Frame-rate read-out on screen</span><label class="bpsw"><input type="checkbox" id="fpsHudChk" aria-label="Frame-rate read-out on screen"><i></i></label>';lim.after(r);
  const c=r.querySelector('input');c.checked=!!UI.fpsHud;c.onchange=()=>fhudSet(c.checked)}
{const _pb=pmBuild;pmBuild=function(){const r=_pb.apply(this,arguments);try{fhudUi()}catch(e){console.error('AudioLab frame-rate read-out',e)}return r}}
if(UI.fpsHud)setTimeout(()=>{try{fhudPaint(performance.now())}catch(e){}},1500);
/* saved choices of the settings removed by glass step 3 are dropped once */
{let ch=false;for(const k of['glPlay','glBack','blur'])if(k in UI){delete UI[k];ch=true}if(ch)saveUI()}
