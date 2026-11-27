/* --- v0.228 (task GS3, glass step 3): frame time. Measured with tools/ui-tests/frametime.py (the user's window size, Fractals song open, one part switched off at a time).
   1. Things that drew the same picture again and again while nothing changed, each one a new frame for the whole window to be put together again:
      the master meter in the top bar (120 times a second, also in silence) draws only when what it shows changed; the logo in Settings draws at most
      60 pictures a second (it drew up to 160, about 1,500 canvas calls each).
   2. drawArr's last part asked the page where the "add track" row is and how tall the header column is on every full drawing (forced layouts);
      those answers are kept until the rows or the window change.
   3. The frame-rate read-out (Settings > Performance, "Frame-rate read-out on screen"): a small badge in the corner with the frames per second and
      the slowest frame of the last 5 seconds, updated twice a second. Saved in UI.fpsHud.
   Tried and left out (measured in the backlog log, task GS3): drawing a scrolled arrangement by shifting the old picture and drawing only strips. */
const ASC={gen:0};/* counts edits (changed()), so kept layout answers are asked again after one */
{const _ch=changed;changed=function(){ASC.gen++;return _ch.apply(this,arguments)}}
/* where the "add track" row sits inside the header column: kept until the rows change (it was a forced layout on every full drawing). The key is what the
   header column was last given (its row height and classes are set at the end of drawArr), so the drawing after a change asks again, as before. */
const ASCY={k:'',v:0,t:0,hk:'',hv:0};
function ascAddY(){const st=hdrin.style,k=[st.getPropertyValue('--th'),st.getPropertyValue('--lh'),st.getPropertyValue('--msh'),st.getPropertyValue('--mh'),hdrin.className,TOTH,S.tracks.length,hdrin.childElementCount,ASC.gen,UI.tracksRight?1:0,ZOOM].join('|'),n=performance.now();
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
