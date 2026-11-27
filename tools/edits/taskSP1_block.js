/* --- v0.224 (task SP1): the splash pictures and the last stretch. The pictures themselves are drawn by SPLBG (right after the splash at the top of the body, so the first one is painted before this code is read). Here: every loading splash gets the picture (the atom is no longer drawn on it), and the timing. The splash stays for as long as the app is loading (bootRun, v0.195, unchanged: the bar follows the real steps). When loading is done the app behind is ready at once, the splash stays SP1.hold more milliseconds and then fades by itself; during that stretch a click or a key closes it at once, and a short line at the bottom says so. Before loading is done nothing closes it. --- */
const SP1={hold:1500,/* how long the splash stays after loading is done at the start of the app (between 1000 and 2000) */holdOpen:0,/* the same for the splash shown while a project is opened inside the running app: 0 = leaves right after loading, as before */busy:null,rdy:null,tm:0,h:0,t1:0,key:null,clk:null};
function sp1Ready(el){SP1.rdy=el;SP1.t1=performance.now();if(!(SP1.h>0)){sp1Close();return}
  el.classList.add('rdy');const p=el.querySelector(':scope>p');if(p)p.textContent='Click to continue';
  SP1.key=e=>{if(['Shift','Control','Alt','Meta','CapsLock','AltGraph'].includes(e.key))return;if(!e.ctrlKey&&!e.metaKey){e.preventDefault();e.stopPropagation()}sp1Close()};
  SP1.clk=e=>{if(el.contains(e.target)){e.preventDefault();e.stopPropagation()}sp1Close()};
  window.addEventListener('keydown',SP1.key,true);window.addEventListener('pointerdown',SP1.clk,true);SP1.tm=setTimeout(sp1Close,SP1.h)}
function sp1Close(){const el=SP1.rdy||SP1.busy;clearTimeout(SP1.tm);SP1.tm=0;if(SP1.key){window.removeEventListener('keydown',SP1.key,true);window.removeEventListener('pointerdown',SP1.clk,true);SP1.key=SP1.clk=null}SP1.busy=SP1.rdy=null;if(el&&SPL&&SPL.el===el)hideSplash()}
{const _ss=showSplash;showSplash=function(about){const had=SPL,r=_ss.apply(this,arguments),el=SPL&&SPL.el;
  if(!had&&el&&el.classList.contains('ld')&&window.SPLBG){el.classList.add('sp1');try{el.style.setProperty('--spz',String(ZOOM||1));SPLBG.attach(el)}catch(e){}
    if(about!=='pv'){SP1.busy=el;SP1.rdy=null;BOOTU.ms=-1}/* loading starts with the next task (bootRun): until it is done nothing closes the splash */
    else{el.classList.add('rdy');const p=el.querySelector(':scope>p'),m=el.querySelector('em');if(p)p.textContent='Click to close';if(m){m.style.width='';m.style.transition='none';m.style.transform='scaleX(1)'}}}
  return r}}
{const _hs=hideSplash;hideSplash=function(){const el=SPL&&SPL.el;
  if(el&&SP1.busy===el){if(SP1.rdy===el){sp1Close();return}if(BOOTU.ms<0)return;/* still loading: the splash stays */sp1Ready(el);return}
  if(el&&el.classList.contains('sp1')){try{SPLBG.stop()}catch(e){}setTimeout(()=>el.remove(),300)}
  return _hs.apply(this,arguments)}}
{const _br=bootRun;bootRun=async function(){const el=SPL&&SPL.el;if(!el||!el.classList.contains('sp1'))return _br.apply(this,arguments);
  SP1.h=BOOTU.first?SP1.hold:SP1.holdOpen;SP1.busy=el;SP1.rdy=null;BOOTU.ms=-1;
  try{await _br.apply(this,arguments)}catch(e){console.error('AudioLab splash',e)}
  if(SP1.busy===el&&SP1.rdy!==el){if(BOOTU.ms<0)BOOTU.ms=0;if(SPL&&SPL.el===el){try{bootClean()}catch(e){}sp1Ready(el)}else SP1.busy=null}}}
