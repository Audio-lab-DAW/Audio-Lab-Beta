/* --- v0.229 (task AB2): the About card in the Settings menu (under Output and Export audio). The old nucleus (paintAtom on #navAtomC) and the blurred coloured balls behind it are gone.
   On the card now: the fine atom of the About window (FATOM, the same code) on #navAtomC, and behind it a small version of one of the splash drawings (SPLBG.FN, the same code) on one canvas (.nab).
   The drawing is chosen at random each time Settings opens, with the splash's weights and its never-twice-in-a-row rule (SPLBG.pick, with its own memory: localStorage audiolab-menu-last).
   The name and the version take the drawing's colours, as on the splash. Labels that ride on the moons and on H1 to H3 are dropped: at this size they would be 2 to 3 points high.
   Cost: at most 30 pictures a second, only while Settings is open, the card is in view and the window is in front (frames go through the app's frame gate, task AO). Light level and reduce motion: one still picture.
   Test hook: AB2.force('moons'|'harm'|'dipole'|'chart'|'spec'|null), or localStorage audiolab-menu-test. Counters: AB2.n. --- */
const AB2=(()=>{const LAST='audiolab-menu-last',TEST='audiolab-menu-test',
  /* how each drawing sits on the card: z = the drawing's width against the card's, s = scale of its lines (below 1 is finer than the splash), a = strength (moving / Light) */
  FIT={moons:{z:1.5,s:.8,a:.8},harm:{z:1.3,s:.8,a:.62},dipole:{z:1.4,s:.8,a:.78},chart:{z:1.45,s:.8,a:.8},spec:{a:.5}},
  n={bg:0,atom:0,opens:0,kinds:{moons:0,harm:0,dipole:0,chart:0,spec:0}};
  let S=null,forced=null,io=null,ro=null,vis=false,dirty=true,G=null;
  const card=()=>document.querySelector('#setNav .navAtom'),still=()=>{try{return!!(UI.lite||aoStill())}catch(e){return!!UI.lite}};
  /* the spectrogram draws into its own small picture (220 points wide); this stand-in takes the place of the canvas it would copy that picture to, and we draw it ourselves, fitted to the card */
  const shim=h=>({canvas:{height:h},globalCompositeOperation:'source-over',drawImage(){}});
  function setup(el){if(el.dataset.ab2)return;el.dataset.ab2=1;el.classList.add('ab2c');
    if(!el.querySelector('canvas.nab')){const c=document.createElement('canvas');c.className='nab';c.setAttribute('aria-hidden','true');el.insertBefore(c,el.firstChild)}
    try{io=new IntersectionObserver(es=>{for(const e of es)vis=e.isIntersecting;if(vis)dirty=true});io.observe(el)}catch(e){vis=true}
    try{ro=new ResizeObserver(()=>{dirty=true});ro.observe(el);const a=document.getElementById('navAtomC');if(a)ro.observe(a)}catch(e){}
    addEventListener('resize',()=>{dirty=true})}
  function pick(){let k=null;if(forced)k=forced;else{try{k=SPLBG.pick(LAST,TEST)}catch(e){k='chart'}}return SPLBG.KINDS.indexOf(k)>=0?k:'chart'}
  /* Settings opened (it was closed): a new drawing */
  function open(){const el=card();if(!el||!window.SPLBG||!window.FATOM)return;setup(el);const k=pick(),P=SPLBG.PAL[k],st=el.style;
    S={k,P,d:{},t0:performance.now(),off:k==='harm'||k==='spec'?0:Math.random()*60,last:-1e9,done:''};n.opens++;n.kinds[k]++;
    for(const v of['g','bg','e','ink','a','b','d','p','m','n'])st.setProperty('--sp'+v,P[v]);el.setAttribute('data-sp',k);dirty=true}
  /* sizes, read only when something changed (no layout reads per frame) */
  function measure(){const el=card(),bg=el&&el.querySelector('canvas.nab'),at=document.getElementById('navAtomC');if(!bg)return false;
    const w=el.clientWidth,h=el.clientHeight;if(!w||!h)return false;const z0=el.getBoundingClientRect().width/w,z=z0>.3&&z0<4?z0:1,sc=Math.min(3,(window.devicePixelRatio||1)*z),pw=Math.round(w*sc),ph=Math.round(h*sc);
    if(bg.width!==pw||bg.height!==ph){bg.width=pw;bg.height=ph}const as=at?at.clientWidth:0;
    G={el,bg,g:bg.getContext('2d'),at,w,h,sc,as,ax:at&&as?at.offsetLeft+as/2:w/2,ay:at&&as?at.offsetTop+at.clientHeight/2:h*.4,
      ty:(()=>{const b=el.querySelector('b');return b?b.offsetTop:h*.75})()};
    /* no text in the drawings: the labels that ride on the bodies would be 2 to 3 points high here */
    G.g.fillText=function(){};dirty=false;return true}
  function paintBg(t,li){const{g,w,h,sc,ax,ay,ty}=G,k=S.k,f=FIT[k],al=f.a*(li?.72:1);g.setTransform(1,0,0,1,0,0);g.clearRect(0,0,G.bg.width,G.bg.height);g.globalAlpha=al;
    if(k==='spec'){const bh=Math.max(60,Math.round(SPLBG.BW*h/w));SPLBG.FN.spec(shim(bh),w,h,t,S.P,S.d);if(S.d.b){g.imageSmoothingEnabled=true;g.setTransform(sc,0,0,sc,0,0);g.drawImage(S.d.b,0,0,w,ty*1.02)}}
    else{const s=f.s,vw=w*f.z/s,vh=vw*.74;g.setTransform(sc*s,0,0,sc*s,sc*(ax-s*vw/2),sc*(ay-s*vh*(k==='harm'?.34:.345)));g.lineWidth=1;SPLBG.FN[k](g,vw,vh,t,S.P,S.d)}
    /* the drawing fades out above the name, so the name and the version stay clear */
    g.globalAlpha=1;g.setTransform(sc,0,0,sc,0,0);g.globalCompositeOperation='destination-out';const y0=Math.max(ay,ty-h*.2),lg=g.createLinearGradient(0,y0,0,ty+2);lg.addColorStop(0,'rgba(0,0,0,0)');lg.addColorStop(1,'rgba(0,0,0,1)');g.fillStyle=lg;g.fillRect(0,y0,w,h-y0);
    g.globalCompositeOperation='source-over';n.bg++}
  function drawAtom2(t){const{at,as}=G;if(!at||as<8)return;FATOM.canvas(at,as,t,{scale:G.sc});n.atom++}
  /* one step, called from the Settings frame loop: at most 30 pictures a second; Light level and reduce motion: one still picture, again only when the size, the drawing or the level changes */
  function tick(now){if(!S||!vis||document.hidden)return;if(dirty&&!measure())return;const li=!!UI.lite,sl=still(),key=S.k+'|'+li+'|'+sl+'|'+G.w+'x'+G.h+'@'+G.sc+'|'+G.as;
    if(sl){if(S.done===key)return;S.done=key;paintBg(S.k==='harm'?8:40+S.off,li);drawAtom2(2);return}S.done='';
    if(now-S.last<32.5)return;S.last=now;const t=Math.max(0,(now-S.t0)/1000)+S.off;paintBg(t,li);drawAtom2(t)}
  function close(){if(S){S.d={};S=null}}
  return{open,close,tick,n,force(k){forced=SPLBG.KINDS.indexOf(k)>=0?k:null;if(S&&!$('#set').hidden)open();return forced},kind:()=>S?S.k:null,get vis(){return vis}}})();
/* the Settings frame loop: the old nucleus is no longer painted there; the card is drawn by AB2. Opening Settings (when it was closed) picks a new drawing. */
setLoop=function(now){if($('#set').hidden){SLP2.on=false;AB2.close();return}requestAnimationFrame(setLoop);try{if(!AB2.kind())AB2.open();AB2.tick(now)}catch(e){console.error('AudioLab menu card',e);AB2.close()}try{gpDraw(now)}catch(e){}};
{const _osA=openSettings;openSettings=function(){const was=$('#set').hidden;const x=_osA.apply(this,arguments);try{if(was){AB2.close();AB2.open()}else if(!AB2.kind())AB2.open()}catch(e){console.error('AudioLab menu card',e)}if(!SLP2.on){SLP2.on=true;requestAnimationFrame(setLoop)}return x}}
