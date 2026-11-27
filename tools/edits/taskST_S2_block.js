/* v0.231 (task ST-S2): the export options and the piano roll options are remembered.
   Export: format, sample rate, bit depth, MP3 bitrate, FLAC compression, dither, normalize, range, tail, limiter and folder in UI.exOpt (this computer, last used);
   the file name in the project (S.exName), so each song keeps its own; an empty name means the default "AudioLab mix".
   Piano roll: tool, snap, chord, ghost on or off and the bottom lane in UI.prMem (last used); scale and root in the project (S.prKey), default A minor as before.
   PR keeps its fields: they become getters and setters, so every place that sets them (menus, keys, tools) is remembered without a second copy. */
const STS2=(()=>{
  const EXK=['exBit','exKbps','exFlacC','exDit','exNorm','exRange','exTail'],q=id=>document.getElementById(id),DEFN='AudioLab mix';
  const has=(sel,v)=>!!sel&&[...sel.options].some(o=>o.value===String(v));
  let exReady=false;
  function exSave(){if(!exReady)return;const o={fmt:EX.fmt};for(const id of EXK.concat('exSr')){const e=q(id);if(e)o[id]=e.value}
    o.exLim=!!(q('exLim')&&q('exLim').checked);o.exFolder=!!(q('exFolder')&&q('exFolder').checked);
    if(JSON.stringify(o)!==JSON.stringify(UI.exOpt||null)){UI.exOpt=o;saveUI()}}
  function exLoad(){const o=UI.exOpt;try{if(o&&typeof o==='object'){
      if(o.fmt==='wav'||o.fmt==='flac'||o.fmt==='mp3')EX.fmt=o.fmt;
      for(const id of EXK){const e=q(id);if(e&&o[id]!=null&&has(e,o[id]))e.value=String(o[id])}
      if(typeof o.exLim==='boolean'&&q('exLim'))q('exLim').checked=o.exLim;if(typeof o.exFolder==='boolean'&&q('exFolder'))q('exFolder').checked=o.exFolder;
      exUI();const sr=q('exSr');if(sr&&o.exSr!=null&&has(sr,o.exSr)){sr.value=String(o.exSr);exUI()}}
    else exUI()}catch(e){}exReady=true}
  function nameSync(){const n=q('exName');if(!n||document.activeElement===n)return;const v=typeof S.exName==='string'&&S.exName.trim()?S.exName:DEFN;if(n.value!==v)n.value=v}
  function exWire(){const sec=document.querySelector('#setBody section[data-page="export"]');if(!sec||sec.dataset.sts2)return;sec.dataset.sts2=1;
    sec.addEventListener('change',e=>{if(e.target&&e.target.id!=='exName'&&e.target.id!=='exSeedV')exSave()});
    q('exFmt').addEventListener('click',()=>setTimeout(exSave,0));
    const n=q('exName');if(n){n.title='The name of the exported file. Each project keeps its own name.';
      n.addEventListener('input',()=>{const v=n.value.trim();S.exName=v&&v!==DEFN?n.value:''});
      n.addEventListener('change',()=>{try{changed(false)}catch(e){}})}
    const h=sec.querySelector('h4');if(h&&!q('exMem'))h.insertAdjacentHTML('afterend','<p class="hint" id="exMem">AudioLab remembers these choices for the next export. The file name is kept with each project.</p>');
    {const _u=exUI;exUI=function(){nameSync();return _u.apply(this,arguments)}}
    exLoad();nameSync()}
  /* piano roll */
  const TOOLS=()=>[...document.querySelectorAll('#prTools [data-tool]')].map(b=>b.dataset.tool);
  const okPR={tool:v=>TOOLS().includes(v),snap:v=>SNAPS.some(s=>s[1]===v),chord:v=>Object.prototype.hasOwnProperty.call(CHORDS,v),ghost:v=>typeof v==='boolean',lane:v=>v==='vel'||(typeof v==='string'&&CCK.some(c=>c[0]===v))};
  const okKey={root:v=>Number.isInteger(v)&&v>=0&&v<12,scale:v=>Object.prototype.hasOwnProperty.call(SCALES,v)},DK={root:9,scale:'minor'};
  function prWire(){if(PR.__sts2)return;const mem=UI.prMem&&typeof UI.prMem==='object'?UI.prMem:{};
    for(const k of Object.keys(okPR)){let v=PR[k];if(mem[k]!==undefined&&okPR[k](mem[k]))v=mem[k];
      Object.defineProperty(PR,k,{configurable:true,enumerable:true,get(){return v},set(x){v=x;if(okPR[k](x)){const m=UI.prMem&&typeof UI.prMem==='object'?UI.prMem:(UI.prMem={});if(m[k]!==x){m[k]=x;saveUI()}}}})}
    for(const k of Object.keys(okKey)){delete PR[k];Object.defineProperty(PR,k,{configurable:true,enumerable:true,
      get(){const K=S&&S.prKey;return K&&okKey[k](K[k])?K[k]:DK[k]},
      set(x){if(!S||!okKey[k](x))return;if(this[k]===x&&S.prKey)return;S.prKey=Object.assign({root:this.root,scale:this.scale},S.prKey||{},{[k]:x})}})}
    Object.defineProperty(PR,'__sts2',{value:1});
    if(PR.snap)PR.len=PR.snap;
    for(const id of['prRoot','prScale'])q(id).addEventListener('change',()=>{try{changed(false)}catch(e){}});
    prSync();
    const _o=openPR;openPR=function(){const r=_o.apply(this,arguments);prSync();return r}}
  function prSync(){try{q('prSnap').value=String(PR.snap);q('prChord').value=PR.chord;q('prRoot').value=String(PR.root);q('prScale').value=PR.scale;prSelState();
    for(const b of q('prTools').children)b.classList.toggle('on',b.dataset.tool===PR.tool);const l=q('prLane');if(l&&l.value!==PR.lane)l.value=PR.lane}catch(e){}}
  try{exWire()}catch(e){console.warn('ST-S2 export',e)}
  try{prWire()}catch(e){console.warn('ST-S2 piano roll',e)}
  {const _sp=switchProject;switchProject=function(){const r=_sp.apply(this,arguments);try{nameSync();prSync()}catch(e){}return r}}
  return{exSave,exLoad,nameSync,prSync}})();
