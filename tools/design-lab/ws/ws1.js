/* ===================== task WS-1 (lane Q): the start screen =====================
   The user's D6 answer (28 Nov): a fresh install opens with no song; a start screen in the splash's scientific style lists the
   recent projects and the ways to start (a new empty project, templates, open a file). Picks: W1 card over the drawing, T1 every
   start, D3 no demo songs in the app, P1 the splash grows into the start screen; round 2: the drawings S1 dipole, S2 moons and
   R4 interference, R5 phase portrait, R6 Lissajous, R7 TRAPPIST-1, R8 Fourier at random, the dipole's particles as field flow F1
   (Jupiter: out of the north half, along the line, in at the south and up through the ball), smaller and fewer; the hand-over M1,
   1000 ms, smooth. Plan and research: docs/start-screen.md. Pick pages: tools/design-lab/ws/.
   - Start-up: the stored tabs come back as they were (no Fractals song at every start, no demo songs added, no demo toast); with
     no stored project there is one empty project ("Untitled", one audio and one instrument track, 120 BPM) behind the start screen.
     A pulled-out project window (CHILD) starts as before. Under automation (navigator.webdriver, the UI tests and the release
     gate's engine tests) the start is the one before this step (task AI's Fractals song) unless localStorage 'audiolab-ws-test'
     is '1', so the 160 UI tests and export_same.py keep their song; the desktop smoke test opens Fractals by name anyway.
   - The splash (SPLBG, SP1) is read, never changed: its picture and rect are measured and the start screen grows out of it.
   - Nothing runs per frame while the start screen is closed. While it is open its drawing moves only at Motion Ambient, never
     in Light mode, with Reduce motion or while the window is hidden; otherwise it is one still picture.
   - Hooks: WS_HOOKS.open() for lane F's menus, WS_HOOKS.settingsRow() (lane B: the row 'Show the start screen at start-up' in the
     S4 table shape, its checkbox put after the splash's), WS_HOOKS.isOpen(). Motion: lane F's tokens (120 ms fades). */
/*@WSR2@*/
const WS={on:false,el:null,kind:null,sel:0,items:[],raf:0,hand:null,last:0,pend:false,auto:false,fresh:false,enter:false,still:true,dur:1000,F:null,d:{},t0:0,off:0,
  SET:['dipole','moons','interf','vdp','liss','trap','four'],
  BAND:{dipole:1,moons:.8,interf:.8,vdp:.58,liss:.56,trap:.78,four:.62},
  NAME:{dipole:'Dipole field',moons:'Moons in resonance',interf:'Wave interference',vdp:'Phase portrait',liss:'Lissajous figure',trap:'TRAPPIST-1',four:'Fourier series'}};
const WS_HOOKS=window.WS_HOOKS=window.WS_HOOKS||{};
WS.auto=(()=>{try{return navigator.webdriver===true&&localStorage.getItem('audiolab-ws-test')!=='1'}catch(e){return navigator.webdriver===true}})();
WS.pend=!CHILD&&!WS.auto&&UI.wsShow!==false;
WS.mac=/Mac|iPhone|iPad/.test(navigator.platform||navigator.userAgent||'');
/* the start of the app: no demo toast, the stored tabs as they were */
if(!CHILD&&!WS.auto){firstRun=false;{const _ip=initProjects;initProjects=function(){if(CHILD)return _ip.apply(this,arguments);try{wsInitProjects()}catch(e){console.error('AudioLab start screen',e);return _ip.apply(this,arguments)}}}}
function wsBlankS(){const keep=S,NS={bpm:120,loop:true,click:false,master:0,tracks:[],sections:[]};S=NS;try{NS.tracks.push(mkTrack('audio',null,'Audio 1',PAL[0]));NS.tracks.push(mkTrack('inst','saw',null,PAL[1%PAL.length]))}finally{S=keep}return NS}
function wsInitProjects(){let L=null;try{L=JSON.parse(localStorage.getItem('audiolab-projects'))}catch(e){L=null}
  let list=[];if(L&&Array.isArray(L.list))list=L.list.concat(Array.isArray(L.win)?L.win:[]).filter(q=>q&&q.id&&q.S&&Array.isArray(q.S.tracks)&&!q.frxHold);
  if(list.length){PJ={cur:L.cur,list,win:[]};const c=list.find(p=>p.id===PJ.cur)||list[0];PJ.cur=c.id;S=c.S}
  else{S=wsBlankS();PJ={cur:'p1',list:[{id:'p1',name:'Untitled',S,wsBlank:1}],win:[]};WS.fresh=true}
  /* the one-time kick fix of the old Psytrance demo tab (initProjects did it; kept for old profiles) */
  if(!UI.kickUp){for(const p of PJ.list)if(p.name==='Psytrance demo')for(const t of p.S.tracks)if(t.name==='Kick'&&t.inst&&t.inst.preset==='drums'){Object.assign(t.inst,{...PRESETS.kick,preset:'kick'});t.fx=t.fx.filter(f=>f.type!=='comp')}UI.kickUp=true}
  UI.psyAdded=true;UI.shrineAdded=true;UI.shrineBack=true;try{saveUI()}catch(e){}
  renderTabs();try{saveProjects()}catch(e){}}
/* when each project was last on screen (the tabs keep only how long they were open) */
function wsSeenAll(){try{return JSON.parse(localStorage.getItem('audiolab-ws-seen'))||{}}catch(e){return{}}}
function wsStamp(){try{const p=curP();if(!p||p.wsBlank)return;const m=wsSeenAll();m[p.name]=Date.now();const k=Object.keys(m);if(k.length>60){k.sort((a,b)=>m[a]-m[b]);for(const x of k.slice(0,k.length-60))delete m[x]}localStorage.setItem('audiolab-ws-seen',JSON.stringify(m))}catch(e){}}
function wsClips(s){let n=0;for(const t of s.tracks||[])n+=(t.clips||[]).length;return n}
function wsIsBlank(p){if(!p)return false;const s=p.id===PJ.cur?S:p.S;return!!p.wsBlank&&!p.dirty&&!p.file&&!!s&&!wsClips(s)}
function wsRecent(){const out=[],seen=new Set(),M=wsSeenAll();
  for(const p of PJ.list){const s=p.id===PJ.cur?S:p.S;if(!s||!Array.isArray(s.tracks)||wsIsBlank(p))continue;
    if(!p.dirty&&!p.file&&!wsClips(s)&&/^(Untitled|Project \d+)$/.test(p.name||''))continue;
    out.push({k:'tab',id:p.id,name:p.name||'Untitled',t:M[p.name]||+p.savedAt||+p.openedAt||0,S:s,file:p.file||'',cur:p.id===PJ.cur?1:0});seen.add(p.name)}
  savedList().forEach((q,i)=>{if(!q||!q.S||!Array.isArray(q.S.tracks)||seen.has(q.name))return;seen.add(q.name);out.push({k:'saved',i,name:q.name||'Untitled',t:Math.max(M[q.name]||0,+q.t||0),S:q.S,cur:0})});
  out.sort((a,b)=>(b.cur-a.cur)||(b.t-a.t));return out}
function wsWhen(t){if(!t)return'';const d=new Date(t),n=new Date(),day=864e5,hm=d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}),a=new Date(n.getFullYear(),n.getMonth(),n.getDate()).getTime();
  if(t>=a)return'Today '+hm;if(t>=a-day)return'Yesterday '+hm;return d.toLocaleDateString([],{day:'numeric',month:'short',year:d.getFullYear()===n.getFullYear()?undefined:'numeric'})}
function wsBars(s){let e=0;for(const t of s.tracks||[])for(const c of t.clips||[])e=Math.max(e,(+c.start||0)+(+c.len||0));return Math.ceil(e/4)}
/* a small map of the song: one row per track (up to 10) with its clips in the track's colour */
function wsMini(cv,s){const w=72,h=28,d=Math.min(2,devicePixelRatio||1);cv.width=w*d;cv.height=h*d;const g=cv.getContext('2d');g.setTransform(d,0,0,d,0,0);g.clearRect(0,0,w,h);
  const T=(s.tracks||[]).filter(t=>t.kind!=='group').slice(0,10),b=Math.max(16,wsBars(s)*4);g.fillStyle='rgba(255,255,255,.035)';g.fillRect(0,0,w,h);
  if(!T.length){g.strokeStyle='rgba(255,255,255,.14)';g.strokeRect(.5,.5,w-1,h-1);return}
  const rh=Math.max(1,Math.floor((h-4)/T.length)),y0=Math.round((h-rh*T.length)/2);
  T.forEach((t,i)=>{g.fillStyle=t.color||'#4c8dff';g.globalAlpha=.9;g.fillRect(0,y0+i*rh,2,Math.max(1,rh-1));g.globalAlpha=.62;for(const c of t.clips||[]){const x=4+(+c.start||0)/b*(w-6),cw=Math.max(1,(+c.len||0)/b*(w-6));g.fillRect(x,y0+i*rh,cw,Math.max(1,rh-1))}});g.globalAlpha=1}
/* ---- the drawing ---- */
function wsPal(k){return(window.SPLBG&&SPLBG.PAL[k])||WSR2.PAL[k]||SPLBG.PAL.dipole}
function wsFn(k){return k==='dipole'?WSR2.FN.dipF1:k==='moons'?SPLBG.FN.moons:WSR2.FN[k]}
function wsPick(){let f=null,last=null;try{f=localStorage.getItem('audiolab-ws-kind');last=localStorage.getItem('audiolab-ws-last')}catch(e){}
  if(WS.SET.includes(f))return f;const sk=window.SPLBG&&SPLBG.kind?SPLBG.kind():null;let k=sk==='dipole'||sk==='moons'?sk:null;
  if(!k){const L=WS.SET.filter(x=>x!==last);k=L[Math.floor(Math.random()*L.length)]}try{localStorage.setItem('audiolab-ws-last',k)}catch(e){}return k}
function wsReduce(){try{return matchMedia('(prefers-reduced-motion: reduce)').matches}catch(e){return false}}
function wsAmb(){try{return lkT().ambientOK()&&!wsReduce()}catch(e){return false}}
function wsBg(P,x,y){return`radial-gradient(ellipse 75% 75% at ${x.toFixed(1)}% ${y.toFixed(1)}%,${P.g},${P.bg} 70%,${P.e})`}
const wsLerp=(a,b,q)=>a+(b-a)*q;
function wsBez(x1,y1,x2,y2){return p=>{if(p<=0)return 0;if(p>=1)return 1;let lo=0,hi=1,t=p;for(let i=0;i<30;i++){t=(lo+hi)/2;const x=3*(1-t)*(1-t)*t*x1+3*(1-t)*t*t*x2+t*t*t;if(x<p)lo=t;else hi=t}return 3*(1-t)*(1-t)*t*y1+3*(1-t)*t*t*y2+t*t*t}}
WS.E=wsBez(.2,.7,.2,1);
function wsSeg(p,a,b){return WS.E(Math.max(0,Math.min(1,(p-a)/(b-a))))}
/* paints the drawing frame (577 x 427, the splash's own frame) at scale sc with its corner at (ox, oy), clipped to the rect R */
function wsPaint(ts,R,sc,ox,oy){const cv=WS.cv,c=WS.c;if(!cv||!c)return;const d=WS.dpr;c.setTransform(d,0,0,d,-WS.cx*d,-WS.cy*d);c.clearRect(WS.cx,WS.cy,WS.cw,WS.ch);
  c.save();c.beginPath();if(c.roundRect)c.roundRect(R.x,R.y,R.w,R.h,[R.r,R.r,R.rb,R.rb]);else c.rect(R.x,R.y,R.w,R.h);c.clip();c.translate(ox,oy);c.scale(sc,sc);
  const t=WS.still?40+WS.off:Math.max(0,(ts-WS.t0)/1000)+WS.off;try{wsFn(WS.kind)(c,577,427,t,wsPal(WS.kind),WS.d)}catch(e){}c.restore()}
function wsCanvasAt(x,y,w,h){const cv=WS.cv;WS.cx=x;WS.cy=y;WS.cw=w;WS.ch=h;const z=WS.z||1;WS.dpr=Math.min(2,(devicePixelRatio||1),Math.sqrt(2.4e6/Math.max(1,w*h)));
  Object.assign(cv.style,{left:x+'px',top:y+'px',width:w+'px',height:h+'px'});const pw=Math.round(w*WS.dpr),ph=Math.round(h*WS.dpr);if(cv.width!==pw||cv.height!==ph){cv.width=pw;cv.height=ph}void z}
/* ---- the screen ---- */
function wsBuild(){let el=document.getElementById('wsS');if(el)return el;el=document.createElement('div');el.id='wsS';el.className='ws';el.hidden=true;el.setAttribute('role','dialog');el.setAttribute('aria-modal','true');el.setAttribute('aria-label','Start screen');
  const K=WS.mac?'⌘':'Ctrl+';
  el.innerHTML=`<div class="wsBk"></div><div class="wsCard"></div><div class="wsGlow"></div><canvas class="wsCv" aria-hidden="true"></canvas>
<div class="wsCont"><div class="wsSp"></div><div class="wsBody">
 <section class="wsL"><div class="wsH wsRise"><span class="wsT">Recent projects</span><label class="wsQ" title="Type to search your projects and templates"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="4.6" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M10.4 10.4 14 14" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg><input id="wsQ" type="text" placeholder="Type to search" aria-label="Search projects and templates" spellcheck="false" autocomplete="off"></label></div><div class="wsList" id="wsList" role="listbox" aria-label="Recent projects"></div></section>
 <section class="wsR"><div class="wsT wsRise">Start something new</div>
  <button class="wsTile wsPri wsRise" data-a="new" data-k="empty" title="A new project with one audio and one instrument track at 120 BPM (${K}N)"><span class="wsTh"><b>New empty project</b><kbd>${K}N</kbd></span><small>One audio and one instrument track, 120 BPM.</small></button>
  <div class="wsG wsRise"><button class="wsTile" data-a="new" data-k="beat" title="A new project with a kick and a rolling bassline at 145 BPM"><b>Beat starter</b><small>A kick and a rolling bassline at 145 BPM, ready to build on.</small></button><button class="wsTile" data-a="new" data-k="audio" title="A new project with four audio tracks to drop recordings into"><b>Audio tracks</b><small>Vocals, guitar, bass and drums tracks to drop files into.</small></button></div>
  <div class="wsT2 wsRise">My templates</div><div class="wsG wsRise" id="wsMy"></div>
  <div class="wsG wsRise"><button class="wsTile" data-a="file" title="Open a .audiolab project from your computer (${K}O)"><span class="wsTh"><b>Open a file…</b><kbd>${K}O</kbd></span><small>A .audiolab project from your computer.</small></button><button class="wsTile" data-a="more" title="The New project window: name, tempo, track count, your templates"><b>More options…</b><small>Name, tempo and track count before you start.</small></button></div>
 </section>
 <div class="wsF wsRise"><div class="wsK" id="wsK"></div><button type="button" class="wsSw" id="wsSw" role="switch" aria-checked="true" title="Show this screen every time AudioLab starts. Also in Settings, General."><i></i>Show at start-up</button></div>
</div></div>
<div class="wsLogo" aria-hidden="true"><span class="wsA">Audio</span><span class="wsLb">Lab</span><span class="wsP">PRO</span></div><div class="wsVer"></div><div class="wsBar"><b></b></div>`;
  document.body.appendChild(el);WS.el=el;WS.cv=el.querySelector('.wsCv');WS.c=WS.cv.getContext('2d');WS.q=el.querySelector('#wsQ');
  WS.q.addEventListener('input',()=>{WS.sel=0;wsFill()});
  el.addEventListener('click',e=>{const b=e.target.closest('[data-a]');if(b&&el.contains(b)){e.preventDefault();wsAct(b);return}const sw=e.target.closest('#wsSw');if(sw){wsSetShow(UI.wsShow===false);return}});
  el.addEventListener('pointerdown',e=>{if(e.target.classList.contains('wsBk')&&!WS.hand){e.preventDefault();wsClose()}});
  el.addEventListener('pointermove',e=>{const b=e.target.closest('[data-a]');if(b){const i=WS.items.indexOf(b);if(i>=0&&i!==WS.sel){WS.sel=i;wsMark(false)}}});
  return el}
function wsSetShow(on){UI.wsShow=!!on;try{saveUI()}catch(e){}const sw=document.getElementById('wsSw');if(sw){sw.classList.toggle('on',!!on);sw.setAttribute('aria-checked',String(!!on))}const c=document.getElementById('wsSet');if(c)c.checked=!!on;
  if(WS.on)toast(on?'The start screen shows every time AudioLab starts.':'AudioLab starts with your last project. The start screen stays in the ＋ menu next to the tabs.')}
function wsFill(){const el=WS.el,q=(WS.q.value||'').trim().toLowerCase(),R=wsRecent(),list=el.querySelector('#wsList');WS.recent=R;
  const vis=R.map((r,i)=>[r,i]).filter(([r])=>!q||r.name.toLowerCase().includes(q));
  list.innerHTML=vis.length?vis.map(([r,i])=>{const bars=wsBars(r.S),n=r.S.tracks.length,src=r.k==='tab'?(r.file?r.file:'Not saved to a file'):'Saved project';
    return`<div class="wsRow wsRise" role="option" data-a="row" data-i="${i}" title="Open ${esc(r.name)}"><canvas class="wsMini" data-m="${i}"></canvas><span class="wsN"><b>${esc(r.name)}</b><small>${esc(src)}</small></span><span class="wsD">${esc(wsWhen(r.t)||(r.cur?'Open at quit':''))}</span><span class="wsM">${Math.round(+r.S.bpm||120)}<span class="wsU"> BPM</span>${bars?` · ${bars}<span class="wsU"> bars</span>`:''} · ${n}<span class="wsU"> ${n===1?'track':'tracks'}</span></span></div>`}).join('')
    :`<div class="wsNone wsRise">${R.length?'No project matches “'+esc(WS.q.value.trim())+'”.':'No projects yet. Start one on the right, or open a file.'}</div>`;
  for(const cv of list.querySelectorAll('canvas[data-m]')){const r=R[+cv.dataset.m];if(r)try{wsMini(cv,r.S)}catch(e){}}
  for(const b of el.querySelectorAll('.wsR [data-a]')){const tx=b.textContent.toLowerCase();b.hidden=!!q&&!tx.includes(q)}
  WS.items=[...el.querySelectorAll('[data-a]')].filter(b=>!b.hidden);if(WS.sel>=WS.items.length)WS.sel=0;wsMark(false)}
function wsMy(){const box=WS.el&&WS.el.querySelector('#wsMy');if(!box)return;tplAll().then(L=>{if(!WS.el)return;box.innerHTML=L.length?L.slice(0,6).map(r=>`<button class="wsTile" data-a="tpl" data-t="${esc(r.id)}" title="A new project from your template ${esc(r.name)}"><b>${esc(r.name)}</b><small>${r.st.tr} ${r.st.tr===1?'track':'tracks'} · ${Math.round(r.st.bpm)} BPM${r.kind==='all'?' · with clips':''}</small></button>`).join(''):'<small class="wsQuiet">None yet. In New project, save a project as a template and it shows here.</small>';
    if(WS.on){WS.items=[...WS.el.querySelectorAll('[data-a]')].filter(x=>!x.hidden);if(WS.sel>=WS.items.length)WS.sel=0;wsMark(false)}}).catch(()=>{})}
function wsMark(scroll){WS.items.forEach((b,i)=>b.classList.toggle('on',i===WS.sel));const b=WS.items[WS.sel];if(b&&scroll)b.scrollIntoView({block:'nearest'});
  const k=WS.el&&WS.el.querySelector('#wsK');if(!k)return;const K=WS.mac?'⌘':'Ctrl+',nm=b?(b.dataset.a==='row'?(WS.recent[+b.dataset.i]||{}).name:(b.querySelector('b')||b).textContent):'';
  k.innerHTML=`<span><b>↵</b> opens ${esc(nm||'the selection')}</span><span><b>↑ ↓</b> choose</span><span><b>type</b> to search</span><span><b>${K}N</b> empty project</span><span><b>${K}O</b> open a file</span><span><b>Esc</b> close</span>`}
function wsLayout(){const el=WS.el,W=el.clientWidth||innerWidth,H=el.clientHeight||innerHeight,w=Math.min(1020,W-48),h=Math.min(607,H-44),x=Math.round((W-w)/2),y=Math.round((H-h)/2),B=Math.max(120,Math.round(h*172/607)),bs=(WS.BAND[WS.kind]||.7)*w/1020;
  WS.F={x,y,w,h,B,bs,dx:x+w/2-288.5*bs,dy:y+B*(WS.BAND[WS.kind]<1?.5:.56)-147*bs};const ct=el.querySelector('.wsCont');Object.assign(ct.style,{left:x+'px',top:y+'px',width:w+'px',height:h+'px'});ct.querySelector('.wsSp').style.height=B+'px';
  const r=el.getBoundingClientRect();WS.z=el.clientWidth?r.width/el.clientWidth:1}
function wsFinal(){const F=WS.F,el=WS.el,P=wsPal(WS.kind);Object.assign(el.querySelector('.wsCard').style,{left:F.x+'px',top:F.y+'px',width:F.w+'px',height:F.h+'px',borderRadius:'12px',opacity:1});
  Object.assign(el.querySelector('.wsGlow').style,{left:F.x+'px',top:F.y+'px',width:F.w+'px',height:F.B+'px',borderRadius:'12px 12px 0 0',background:wsBg(P,50,(F.dy+147*F.bs-F.y)/F.B*100),opacity:1});
  el.querySelector('.wsBk').style.opacity=1;const lg=el.querySelector('.wsLogo');lg.style.transform=`translate(${F.x+28}px,${F.y+F.B-60}px)`;
  const v=el.querySelector('.wsVer');v.style.transform=`translate(${F.x+30}px,${F.y+F.B-24}px)`;v.style.opacity=1;
  Object.assign(el.querySelector('.wsBar').style,{left:F.x+'px',top:(F.y+F.B)+'px',width:F.w+'px',height:'1px',opacity:1});el.querySelector('.wsBar b').style.opacity=0;
  for(const r of el.querySelectorAll('.wsRise')){r.style.opacity='';r.style.transform=''}
  wsCanvasAt(F.x,F.y,F.w,F.B);WS.R={x:F.x,y:F.y,w:F.w,h:F.B,r:12,rb:0};wsPaint(performance.now(),WS.R,F.bs,F.dx,F.dy)}
function wsColours(){const P=wsPal(WS.kind),el=WS.el,st=el.style;st.setProperty('--wsink',P.ink);st.setProperty('--wsa',P.a);st.setProperty('--wsb',P.b);st.setProperty('--wsp',P.p);st.setProperty('--wsm',P.m);el.dataset.k=WS.kind}
/* opens the start screen; o.from: the splash element it grows out of (the start of the app) */
function wsOpen(o){o=o||{};if(CHILD)return;const el=wsBuild();if(WS.on&&!o.from){wsFill();return}
  WS.kind=wsPick();WS.d={};WS.off=Math.random()*60;WS.t0=performance.now();WS.still=!wsAmb();wsColours();
  el.querySelector('.wsVer').textContent='Digital audio workstation · v'+VERSION;WS.q.value='';WS.sel=0;
  const sw=el.querySelector('#wsSw');sw.classList.toggle('on',UI.wsShow!==false);sw.setAttribute('aria-checked',String(UI.wsShow!==false));
  el.hidden=false;el.classList.remove('out');WS.on=true;wsLayout();wsFill();wsMy();
  const anim=o.from&&o.from.isConnected&&!wsReduce()&&!UI.lite&&(()=>{try{return lkT().motion!=='signal'}catch(e){return true}})();
  if(anim){const z=WS.z||1,loc=r=>({x:r.left/z,y:r.top/z,w:r.width/z,h:r.height/z}),A=loc(o.from.getBoundingClientRect()),nb=o.from.querySelector('.spw>b'),bi=o.from.querySelector('.spw i');
    WS.hand={t0:performance.now(),A,N:nb?loc(nb.getBoundingClientRect()):null,I:bi?loc(bi.getBoundingClientRect()):null};const lg=el.querySelector('.wsLogo');lg.style.transform='none';WS.hand.L={w:lg.offsetWidth||200,h:lg.offsetHeight||34};
    wsCanvasAt(0,0,el.clientWidth,el.clientHeight);el.classList.add('hand');wsHandFrame(WS.hand.t0)}
  else{el.classList.add('fade');wsFinal();requestAnimationFrame(()=>requestAnimationFrame(()=>el.classList.remove('fade')))}
  try{WS.q.focus({preventScroll:true})}catch(e){}
  wsKick()}
function wsHandFrame(ts){const H=WS.hand,F=WS.F,el=WS.el,A=H.A,p=Math.min(1,Math.max(0,(ts-H.t0)/WS.dur)),g=wsSeg(p,0,1),P=wsPal(WS.kind);
  const card={x:wsLerp(A.x,F.x,g),y:wsLerp(A.y,F.y,g),w:wsLerp(A.w,F.w,g),h:wsLerp(A.h,F.h,g),r:wsLerp(A.w*.026,12,g)},gh=wsLerp(A.h,F.B,g),rb=g<.02?card.r:wsLerp(card.r,0,Math.min(1,g*3));
  Object.assign(el.querySelector('.wsCard').style,{left:card.x+'px',top:card.y+'px',width:card.w+'px',height:card.h+'px',borderRadius:card.r+'px',opacity:Math.min(1,g*2.5)});
  const sc=wsLerp(A.w/577,F.bs,g),ox=wsLerp(A.x,F.dx,g),oy=wsLerp(A.y,F.dy,g);
  Object.assign(el.querySelector('.wsGlow').style,{left:card.x+'px',top:card.y+'px',width:card.w+'px',height:gh+'px',borderRadius:`${card.r}px ${card.r}px ${rb}px ${rb}px`,background:wsBg(P,(ox+288.5*sc-card.x)/card.w*100,(oy+147*sc-card.y)/gh*100),opacity:1});
  el.querySelector('.wsBk').style.opacity=g;wsPaint(ts,{x:card.x,y:card.y,w:card.w,h:gh,r:card.r,rb},sc,ox,oy);
  const R=el.querySelectorAll('.wsRise'),n=R.length,stp=Math.min(.03,(1-.22-.5)/Math.max(1,n-1));R.forEach((r,j)=>{const q=wsSeg(p,.22+j*stp,.22+j*stp+.5);r.style.opacity=Math.max(0,Math.min(1,q*1.4));r.style.transform=`translateY(${((1-q)*120).toFixed(1)}px)`});
  const lg=el.querySelector('.wsLogo'),L=H.L,fx=F.x+28,fy=F.y+F.B-60;if(H.N){const s=wsLerp(H.N.h/L.h,1,g),sx=H.N.x+(H.N.w-L.w*H.N.h/L.h)/2;lg.style.transform=`translate(${wsLerp(sx,fx,g).toFixed(1)}px,${wsLerp(H.N.y,fy,g).toFixed(1)}px) scale(${s.toFixed(4)})`}else lg.style.transform=`translate(${fx}px,${fy}px)`;lg.style.opacity=H.N?1:g;
  const vq=wsSeg(p,.45,1),v=el.querySelector('.wsVer');v.style.transform=`translate(${F.x+30}px,${(F.y+F.B-24+(1-vq)*10).toFixed(1)}px)`;v.style.opacity=vq;
  const bq=wsSeg(p,0,.8),I=H.I||{x:A.x+A.w*.29,y:A.y+A.h*.85,w:A.w*.42,h:2},br=el.querySelector('.wsBar');Object.assign(br.style,{left:wsLerp(I.x,F.x,bq)+'px',top:wsLerp(I.y,F.y+F.B,bq)+'px',width:wsLerp(I.w,F.w,bq)+'px',height:(bq>.5?1:Math.max(1,I.h))+'px',opacity:1});br.firstChild.style.opacity=1-bq;
  if(p>=1){WS.hand=null;el.classList.remove('hand');wsFinal()}}
function wsTick(ts){WS.raf=0;if(!WS.on||document.hidden)return;
  if(WS.hand){wsHandFrame(ts);WS.raf=requestAnimationFrame(wsTick);return}
  const amb=wsAmb();if(!amb){if(!WS.still){WS.still=true;wsPaint(ts,WS.R,WS.F.bs,WS.F.dx,WS.F.dy)}return}
  if(WS.still){WS.still=false}if(ts-WS.last>=32){WS.last=ts;wsPaint(ts,WS.R,WS.F.bs,WS.F.dx,WS.F.dy)}WS.raf=requestAnimationFrame(wsTick)}
function wsKick(){if(WS.on&&!WS.raf&&!document.hidden)WS.raf=requestAnimationFrame(wsTick)}
function wsClose(){if(!WS.on)return;WS.on=false;WS.hand=null;if(WS.raf){cancelAnimationFrame(WS.raf);WS.raf=0}const el=WS.el;WS.d={};
  if(el){el.classList.add('out');setTimeout(()=>{if(!WS.on){el.hidden=true;el.classList.remove('out','hand','fade');if(WS.cv){WS.cv.width=1;WS.cv.height=1}}},130);if(el.contains(document.activeElement))try{document.activeElement.blur()}catch(e){}}}
/* what the rows and tiles do */
function wsDropBlank(keepId){const b=PJ.list.filter(p=>p.wsBlank&&p.id!==keepId&&wsIsBlank(p));if(!b.length)return;PJ.list=PJ.list.filter(p=>!b.includes(p));renderTabs();saveProjects()}
function wsMakeS(kind){const keep=S;let NS;try{if(kind==='beat'){demo();NS=S;NS.tracks=NS.tracks.slice(0,2);NS.tracks.forEach(t=>t.clips.forEach(c=>c.envShow=null));NS.sections=[];NS.loop=true}
  else{NS={bpm:120,loop:true,click:false,master:0,tracks:[],sections:[]};S=NS;if(kind==='audio')['Vocals','Guitar','Bass','Drums'].forEach((n,i)=>NS.tracks.push(mkTrack('audio',null,n,PAL[i%PAL.length])));else{NS.tracks.push(mkTrack('audio',null,'Audio 1',PAL[0]));NS.tracks.push(mkTrack('inst','saw',null,PAL[1%PAL.length]))}}}finally{S=keep}return NS}
function wsNewTab(name,NS){if(pFull())return false;const prev=PJ.cur,id='p'+rid();PJ.list.push({id,name,S:NS});saveProjects();switchProject(id);wsDropBlank(id);void prev;return true}
async function wsAct(b){if(!b)return;const a=b.dataset.a;
  if(a==='row'){const r=(WS.recent||[])[+b.dataset.i];if(!r)return;wsGo(r);return}
  if(a==='new'){const k=b.dataset.k;if(k==='empty'&&wsIsBlank(curP())){wsClose();return}const NS=wsMakeS(k);wsNewTab(k==='beat'?'Beat starter':k==='audio'?'Audio tracks':'Untitled',NS)&&toast(k==='empty'?'New empty project.':'New project from '+(k==='beat'?'Beat starter':'Audio tracks')+'.');return}
  if(a==='tpl'){const r=(await tplAll()).find(q=>q.id===b.dataset.t);if(!r){toast('That template is gone.');wsMy();return}const NS=JSON.parse(JSON.stringify(r.S));if(wsNewTab(r.name.slice(0,40),NS))toast(`New project from the template “${r.name}”.`);return}
  if(a==='file'){wsFile();return}
  if(a==='more'){wsClose();npOpen();return}}
function wsGo(r){if(r.k==='tab'){const p=PJ.list.find(q=>q.id===r.id);if(!p){wsFill();return}if(p.id===PJ.cur){wsClose();wsStamp()}else switchProject(p.id);wsDropBlank(p.id);return}
  const q=savedList()[r.i];if(!q){wsFill();return}const ex=PJ.list.find(p=>p.name===q.name);if(ex){switchProject(ex.id);wsDropBlank(ex.id);return}
  if(wsNewTab(q.name,JSON.parse(JSON.stringify(q.S))))toast('Opened '+q.name+'.')}
function wsFile(){try{const r=openProjectFile();if(r&&r.catch)r.catch(()=>{})}catch(e){}}
/* the keyboard while the start screen is open (and Enter during the splash: it opens the last project at once) */
function wsKey(e){if(!WS.on){if(WS.pend&&e.key==='Enter'&&!e.metaKey&&!e.ctrlKey&&!e.altKey&&document.getElementById('splash'))WS.enter=true;return}
  if(e.target&&e.target.closest&&e.target.closest('.modal:not([hidden]),#ctxm,#cdlg'))return;if(document.querySelector('#cdlg:not([hidden]),#ctxm:not([hidden])'))return;
  const k=e.key,mod=e.metaKey||e.ctrlKey,inQ=e.target===WS.q,stop=()=>{e.preventDefault();e.stopPropagation()};
  if(k==='Escape'){stop();if(inQ&&WS.q.value){WS.q.value='';WS.sel=0;wsFill()}else wsClose();return}
  if(k==='Enter'){stop();if(WS.hand){WS.hand.t0=-1e9}wsAct(WS.items[WS.sel]);return}
  if(k==='ArrowDown'||k==='ArrowUp'){stop();const n=WS.items.length;if(n){WS.sel=(WS.sel+(k==='ArrowDown'?1:n-1))%n;wsMark(true)}return}
  if(mod&&!e.altKey&&(k==='n'||k==='N')){stop();wsAct(WS.el.querySelector('[data-a="new"][data-k="empty"]'));return}
  if(mod&&!e.altKey&&(k==='o'||k==='O')){stop();wsFile();return}
  if(mod)return;
  if(inQ){e.stopPropagation();return}
  if(k.length===1&&!e.altKey){e.stopPropagation();try{WS.q.focus({preventScroll:true})}catch(x){}return}
  if(k==='Tab')return;e.stopPropagation()}
window.addEventListener('keydown',wsKey,true);
document.addEventListener('visibilitychange',()=>{if(document.hidden)wsStamp();else wsKick()});
window.addEventListener('resize',()=>{if(!WS.on)return;if(WS.hand){WS.hand=null;WS.el.classList.remove('hand')}wsLayout();wsFinal();wsKick()});
/* opening any project closes the start screen; the time it was on screen is remembered for the recent list */
{const _sp=switchProject;switchProject=function(id){const r=_sp.apply(this,arguments);try{if(WS.on)wsClose();wsStamp()}catch(e){}return r}}
/* the start of the app: the splash hands over to the start screen when it closes */
if(WS.pend&&typeof SP1==='object'){SP1.hold=Math.min(SP1.hold,400);
  {const _c=sp1Close;sp1Close=function(){const el=SP1.rdy||SP1.busy;if(WS.pend&&el&&el.id==='splash'){WS.pend=false;try{if(WS.enter){const r=wsRecent()[0];if(r)setTimeout(()=>wsGo(r),0);else setTimeout(()=>wsOpen({}),0)}else wsOpen({from:el})}catch(e){console.error('AudioLab start screen',e)}}return _c.apply(this,arguments)}}}
/* the splash may be off (Settings, General) or already gone: the start screen then fades in once the app is ready */
function wsBootOpen(n){try{if(!WS.pend||document.getElementById('splash'))return;if(typeof PJ!=='object'||!PJ){if((n||0)<50)setTimeout(()=>wsBootOpen((n||0)+1),100);return}WS.pend=false;wsOpen({})}catch(e){console.error('AudioLab start screen',e)}}
setTimeout(wsBootOpen,0);
/* D3: no demo songs in the app's menus and dialogs (the functions stay for the release gate and the tests) */
setTimeout(()=>{try{const pa=document.getElementById('pAdd');if(pa)pa.onclick=e=>{const r=e.currentTarget.getBoundingClientRect();openMenu(r.left,r.bottom+3,[{label:'New project…',sub:'Start from empty, a beat or a template',act:npOpen},{label:'Open project…',sub:'Choose an .audiolab file',key:'⌘O',act:()=>openProjectFile()},{label:'Start screen…',sub:'Recent projects, templates and a new empty project',act:()=>wsOpen({})}])}}catch(e){}
  try{WS_HOOKS.settingsRow()}catch(e){}},0);
Object.assign(WS_HOOKS,{
  open:()=>wsOpen({}),close:()=>wsClose(),isOpen:()=>WS.on,
  /* lane B: the Settings row in the S4 table's shape, and its checkbox right after the splash's on the General page */
  row:{id:'wsStart',l:'Show the start screen at start-up',pg:'general',b:'Help while you work',sc:'app',k:'UI.wsShow',c:'#wsSet',t:'check',d:true,h:'Every time AudioLab starts: your recent projects, a new empty project, templates and Open a file. Off: AudioLab opens your last project.',w:'start screen recent projects templates start up launch open last'},
  settingsRow(){const r=WS_HOOKS.row;try{if(typeof STX==='object'&&!STX.has(r.id)){STT.push(r);STX.set(r.id,r)}}catch(e){}
    if(document.getElementById('wsSet'))return;const sp=document.getElementById('setSplash'),lb=sp&&sp.closest('label');if(!lb)return;const n=document.createElement('label');n.className='chk';n.title='Show the start screen every time AudioLab starts';
    n.innerHTML='<input type="checkbox" id="wsSet"> Show the start screen at start-up';lb.after(n);const c=n.querySelector('input');c.checked=UI.wsShow!==false;c.onchange=()=>wsSetShow(c.checked)}});
/* ===================== end of task WS-1 (lane Q) ===================== */
