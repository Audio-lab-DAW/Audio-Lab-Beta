#!/usr/bin/env python3
"""Task DS-B1a (lane A, design round 2, B3 with the details BR2 and BP1): the Instrument and Effects browsers as a
catalogue with a measured preview.
   python3 tools/design-lab/ds/ds_b1a.py index.html
Behind the same entry points (openBrowser, openFxBrowser, Change instrument, Change effect): a top bar with the title,
a search field (focused on open) and a Cards switch; categories with counts on the left; one row per device (logo,
name, what it is for, up to three tag colours from what its presets are made for, kind); on the right the preview: name,
kind and preset, the preview phrase's waveform with a time scale and a scrub line (rendered once offline per sound,
phrase and tempo and cached; the scrub line moves only while the preview plays), key, tempo, length and peak, the
presets (left and right arrows step and play), "In tempo, next bar" and the one live device, scaled to fit.
Up and down arrows choose and play, Enter adds (or uses, or keeps), Escape in the search field clears it first.
Today's plane of large live cards is one click away (Cards, and List to come back; remembered in UI.ibView).
The catalogue keeps the id #ibPlane and the .ibc[data-k] rows, so the Change code, double-click and Enter work as they
did; the preview's live box comes first in the DOM, so it is the tile ibLiveRender finds. Only the AudioLab look (dsAC3);
the other looks keep today's browser. The audio path is untouched: the preview plays through the existing preview path
(ibPlayPhrase, prevIn); "In tempo" only moves its start to the next bar while the song plays. Every anchor is asserted.
Re-run on a fresh file after a rebase."""
import sys
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
assert 'task DS-B1a (lane A' not in s, 'already applied'
assert 'function dsAC3()' in s, 'needs task DS-A3'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:120])
    s = s.replace(old, new)

JS = r"""/* task DS-B1a (lane A, design round 2, B3 with BR2 and BP1): the Instrument and Effects browsers as a catalogue with a
   measured preview, behind the same entry points. Only the AudioLab look; UI.ibView==='cards' keeps today's plane.
   The catalogue is #ibPlane with .ibc[data-k] rows (the Change code, double-click and Enter work as before); the
   preview's live box (.dsblv) comes first in the DOM, so ibLiveRender finds it. The waveform is rendered once offline
   per sound, phrase and tempo (DSB.wv), drawn on change; the scrub line moves only while the preview plays. */
const DSB={q:'',cat:-1,wv:new Map(),hay:new Map(),cur:null,job:0,ph:null,raf:0,pv:'',wt:0,bc:null,k:1};
function dsB1Cat(){return dsAC3()&&UI.ibView!=='cards'}
const DSB_TAG={lead:['Lead','#ff9a3c'],bass:['Bass','#3ecf8e'],pad:['Pad','#4cc9f0'],pluck:['Pluck','#f5c84c'],keys:['Keys','#cfd3db'],drums:['Drums','#ff6b6b'],fx:['Effects and risers','#b583ff'],vocal:['Vocal','#ff7ac8']};
const DSB_ROLE={lead:'lead',saw:'lead',square:'lead',bass:'bass',pad:'pad',pluck:'pluck',keys:'keys',drums:'drums',kick:'drums',fx:'fx',vocal:'vocal'};
const DSB_CAT={Leads:'lead',Bass:'bass',Pads:'pad','Keys & plucks':'pluck',Drums:'drums'};
const dsB1Fx=()=>ib&&ib.mode==='fx';
/* BR2: up to three tags, from the instrument's own kind and what its presets are made for */
function dsB1Tags(k){if(dsB1Fx()){const g=dsB1Grp(k);return g[0]?[[g[0],g[1]]]:[]}const n={},P=PRESETS[k]||{},c=DSB_CAT[P.cat];if(c)n[c]=1e3;const M=PSMETA[k];if(M)for(const q in M){const r=DSB_ROLE[M[q].r];if(r)n[r]=(n[r]||0)+1}
  return Object.keys(n).sort((a,b)=>n[b]-n[a]).slice(0,3).map(r=>DSB_TAG[r])}
function dsB1Kind(k,g){if(dsB1Fx())return g;const P=PRESETS[k]||{};return P.cat||g}
function dsB1Items(){const out=[],fx=dsB1Fx();IBGR().forEach(([g,col,keys],gi)=>{for(const k of keys)if(fx?FXDEF[k]:PRESETS[k])out.push({k,gi,g,col})});return out}
function dsB1Grp(k){return IBGR().find(g=>g[2].includes(k))||['','#8b8b97',[]]}
/* presets: [key, name, group] */
function dsB1PreList(k){if(!k)return[];if(dsB1Fx()){const T=FXPRE[k];return T?Object.entries(T).map(([q,v])=>{const n=String(v[0]),i=n.indexOf('|');return i<0?[q,n,'']:[q,n.slice(i+1),n.slice(0,i)]}):[]}
  const P=IPRE[k];if(!P)return[];const M=PSMETA[k]||{};return Object.entries(P[0]).map(([q,v])=>[q,String(v.n||q).replace(/^[^·]*· /,''),(M[q]||{}).g||''])}
function dsB1PreCur(){const k=ib.sel;if(!k||!ib.t)return'';if(dsB1Fx()){const f=ib.t.fx&&ib.t.fx[0];return f&&f.type===k?(f.p.pre||''):''}return ib.t.inst&&ib.t.inst.preset===k?(ib.t.inst.ipk||(PRESETS[k]||{}).ipk||''):''}
function dsB1Hay(it){const key=ib.mode+':'+it.k;let h=DSB.hay.get(key);if(h==null){h=[ibName(it.k),ibDesc(it.k),dsB1Kind(it.k,it.g),it.g,...dsB1Tags(it.k).map(t=>t[0]),...dsB1PreList(it.k).map(p=>p[1])].join(' ').toLowerCase();DSB.hay.set(key,h)}return h}
const dsB1Words=()=>DSB.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
function dsB1Hit(it){const W=dsB1Words();if(!W.length)return true;const h=dsB1Hay(it);return W.every(w=>h.includes(w))}
function dsB1PreHit(it){const W=dsB1Words();if(!W.length)return'';const nm=(ibName(it.k)+' '+ibDesc(it.k)+' '+it.g).toLowerCase();if(W.every(w=>nm.includes(w)))return'';const p=dsB1PreList(it.k).find(p=>W.every(w=>p[1].toLowerCase().includes(w)));return p?p[1]:''}
function dsB1Render(){IBLAY=null;const v=$('#ibList'),fx=dsB1Fx(),what=fx?'effects':'instruments';v.dataset.k='';for(const k of[...CT.keys()])if(k.startsWith('ibt:'))CT.delete(k);DSB.pv='';
  v.innerHTML=`<div class="ibplane dsbcat" id="ibPlane"><section class="dsbpv" id="dsbPv" aria-label="Preview"></section><nav class="dsbside" id="dsbSide" aria-label="Categories"></nav><div class="dsbmain"><div class="dsbhd"><span>Name</span><span>Tags</span><span>Kind</span></div><div class="dsbrows" id="dsbRows" role="listbox" aria-label="${what}"></div></div></div>`
   +`<div class="ibnav dsbnav"><b class="ibttl">${esc($('#ibT').textContent)}</b><label class="dsbq" title="Type to find ${fx?'an effect':'a sound'} by name, kind, tag or preset. Up and down arrows choose and play, Enter ${esc($('#ibAdd').textContent.toLowerCase())}s it."><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5"/><path d="M12.2 12.2 17 17"/></svg><input id="dsbQ" type="search" placeholder="Search ${what}" aria-label="Search ${what}" autocomplete="off" spellcheck="false" value="${esc(DSB.q)}"></label>`
   +`<span class="dsbkeys">↑ ↓ choose and play · ← → presets · Enter ${esc($('#ibAdd').textContent.toLowerCase())}</span><span class="ibsp"></span><button id="dsbView" title="Show every ${fx?'effect':'instrument'} as a large live card instead of this list">Cards</button><button class="ibx2" aria-label="Close" title="Close">✕</button></div>`;
  dsB1List();dsB1PvSync(true);setTimeout(()=>{const q=$('#dsbQ');if(q&&!$('#ib').hidden&&document.activeElement!==q)try{q.focus({preventScroll:true})}catch(e){}},0)}
function dsB1List(){const R=$('#dsbRows'),Sd=$('#dsbSide');if(!R||!Sd)return;const fx=dsB1Fx(),all=dsB1Items(),hit=all.filter(dsB1Hit),G=IBGR(),cnt=G.map(()=>0);for(const it of hit)cnt[it.gi]++;
  Sd.innerHTML=[[-1,'All',hit.length,''],...G.map((g,i)=>[i,g[0],cnt[i],g[1]])].map(([i,n,c,col])=>`<button data-dsc="${i}" class="${i===DSB.cat?'on':''}${c?'':' none'}" style="--gc:${col||'#8b8b97'}" title="${i<0?'Every '+(fx?'effect':'instrument'):'Only '+esc(n)}${DSB.q?' that matches the search':''}"><i></i><span>${esc(n)}</span><small>${c}</small></button>`).join('');
  const rows=hit.filter(it=>DSB.cat<0||it.gi===DSB.cat),was=typeof chgOn==='function'&&chgOn()&&CHG?CHG.key:'';
  R.innerHTML=rows.length?rows.map(it=>{const k=it.k,tg=dsB1Tags(k),ph=dsB1PreHit(it),on=k===ib.sel;return`<div class="ibc dsbr${on?' on':''}" data-k="${k}" role="option" aria-selected="${on}" tabindex="-1" style="--gc:${it.col}">${logoSvg(k,18)}<b>${esc(ibName(k))}</b><small>${k===was?'<em>On the track before</em> ':''}${esc(ph?'Preset: '+ph:ibDesc(k))}</small><span class="dsbtg">${tg.map(t=>`<i style="--tc:${t[1]}" title="${esc(t[0])}"></i>`).join('')}</span><span class="dsbk">${esc(dsB1Kind(k,it.g))}</span></div>`}).join('')
   :`<p class="dsbnone">Nothing found for “${esc(DSB.q.trim())}”${DSB.cat>=0?' in '+esc(G[DSB.cat][0]):''}.</p>`}
/* the preview side follows ib.sel; called at the start of renderIBTry, before ibLiveRender looks for the live box */
function dsB1PvSync(force){const P=$('#dsbPv');if(!P||!dsB1Cat())return;const k=ib.sel||'',fx=dsB1Fx();
  for(const r of document.querySelectorAll('#dsbRows .dsbr')){const on=r.dataset.k===k;r.classList.toggle('on',on);r.setAttribute('aria-selected',on)}
  if(!force&&DSB.pv===k)return;DSB.pv=k;DSB.cur=null;DSB.bc=null;DSB.ph=null;DSB.job++;
  if(!k){P.innerHTML=`<div class="dsbemp"><b>Choose ${fx?'an effect':'a sound'} on the left</b><span>${fx?'It plays a test sound through the effect':'It plays at once'}, in the song's tempo. Up and down arrows step through the list.</span></div>`;return}
  P.innerHTML=`<div class="dsbph">${logoSvg(k,22)}<b>${esc(ibName(k))}</b></div><small class="dsbsub" id="dsbSub">${esc(dsB1Kind(k,dsB1Grp(k)[0]))}</small>`
   +`<div class="dsbwv"><canvas id="dsbWv" title="The preview as it sounds, worked out once: the scale is in seconds, the blue line shows where it is playing"></canvas></div><div class="dsbinfo" id="dsbInfo"></div>`
   +`<div class="dsbprh"><b>Presets</b><small>← → play the next one</small></div><div class="dsbpre" id="dsbPre" role="listbox" aria-label="Presets"></div>`
   +`<div class="dsbtl"><label class="tgl" title="While the song plays, the preview starts on the next bar so it lands in time with the song. Stopped, it starts at once."><input type="checkbox" id="dsbTempo"${UI.dsbTempo!==false?' checked':''}><i></i>In tempo, next bar</label><span class="ibsp"></span><button id="dsbPlay" title="Play the preview again" aria-label="Play the preview again">▶</button></div>`
   +`<div class="ibc dsblv on" data-k="${k}" title=""><div class="ibdv" data-k="${k}"></div></div>`;
  dsB1Pre();dsB1Info();dsB1WaveDraw();dsB1WaveSoon()}
function dsB1Pre(){const el=$('#dsbPre');if(!el)return;const L=dsB1PreList(ib.sel),cur=dsB1PreCur();if(!L.length){el.innerHTML='<p class="dsbnp">No presets: the sound is set on the device below.</p>';return}
  let g0=null,h='';const grp=L.some(p=>p[2]);for(const[k,n,g] of L){if(grp&&g!==g0){g0=g;h+=`<h5>${esc(g||'Other')}</h5>`}h+=`<button data-dsp="${esc(k)}" role="option" class="${k===cur?'on':''}" title="${esc((typeof psTip==='function'&&!dsB1Fx()&&psTip(ib.sel,k))||'Play this preset')}">${esc(n)}</button>`}el.innerHTML=h}
function dsB1PreMark(){const el=$('#dsbPre'),cur=dsB1PreCur();if(el)for(const b of el.querySelectorAll('[data-dsp]'))b.classList.toggle('on',b.dataset.dsp===cur);
  const sb=$('#dsbSub');if(sb&&ib.sel){const p=dsB1PreList(ib.sel).find(p=>p[0]===cur),t=dsB1Kind(ib.sel,dsB1Grp(ib.sel)[0])+(p?' · '+p[1]:'');if(sb.textContent!==t)sb.textContent=t}}
function dsB1PreSet(pk){const k=ib.sel;if(!k)return;
  if(dsB1Fx()){const f=ib.t&&ib.t.fx&&ib.t.fx[0],T=f&&FXPRE[f.type];if(!T||!T[pk])return;Object.assign(f.p,JSON.parse(JSON.stringify(T[pk][1])));f.p.pre=pk;ibFxApply()}
  else{const I=ibInst(),P=IPRE[k];if(!I||!P||!P[0][pk])return;Object.assign(I,JSON.parse(JSON.stringify(P[1](pk))),{ipk:pk});if(typeof chgOn==='function'&&chgOn()&&CHG)try{chgRevoice(CHG.t)}catch(e){}}
  ibLiveRender();dsB1PreMark();ibPlayPhrase();dsB1WaveSoon();const b=$('#dsbPre [data-dsp].on');if(b)b.scrollIntoView({block:'nearest'})}
function dsB1PreStep(d){const L=dsB1PreList(ib.sel);if(!L.length)return;const i=L.findIndex(p=>p[0]===dsB1PreCur());dsB1PreSet(L[i<0?(d>0?0:L.length-1):(i+d+L.length)%L.length][0])}
function dsB1Step(d){const R=[...document.querySelectorAll('#dsbRows .dsbr')];if(!R.length)return;const i=R.findIndex(r=>r.dataset.k===ib.sel),n=R[i<0?(d>0?0:R.length-1):clamp(i+d,0,R.length-1)];if(!n||n.dataset.k===ib.sel)return;n.click();n.scrollIntoView({block:'nearest'})}
function dsB1Fit(box){if(!box||!box.closest||!box.closest('.dsblv'))return;dsB1PreMark();const inn=box.firstChild;if(!inn)return;inn.style.transform='translate(-50%,-50%)';
  requestAnimationFrame(()=>{if(!inn.isConnected)return;const W=box.clientWidth-14,H=box.clientHeight-14,sc=Math.min(1,W/Math.max(1,inn.scrollWidth),H/Math.max(1,inn.scrollHeight));inn.style.transform=`translate(-50%,-50%) scale(${Math.max(.2,sc).toFixed(3)})`})}
/* the phrase ibPlayPhrase plays: [beat, length, pitch, velocity] and its key */
function dsB1PhName(){const fx=dsB1Fx(),src=UI.ibPhrase||'auto';if(src.startsWith('clip:'))return src;return fx?(UI.ibFxSrc==='drums'?'beat':src==='auto'?({bass:'bass',pluck:'arp',pad:'chords'}[UI.ibFxSrc]||'melody'):src):src==='auto'?(PHAUTO[ib.sel]||'chords'):src}
function dsB1Notes(){const n=dsB1PhName();let notes=[];if(n.startsWith('clip:')){const id=n.slice(5);for(const t of S.tracks)for(const c of t.clips)if(c.id===id&&c.notes)notes=c.notes.filter(q=>!q.m&&q.s>=c.off&&q.s<c.off+8).map(q=>[q.s-c.off,q.l,q.p,q.v])}
  else{const P=PHR[n];if(P)notes=P.notes.map(([s,l,p])=>[s,l,P.root+p,.8])}return notes.filter(q=>q[0]<8)}
function dsB1T0(){const n=ctx.currentTime+.05;if(!dsB1Cat()||UI.dsbTempo===false||!play.on)return n;try{const bp=barPos(curBeat()),t=play.t0+secOf(bp.start+bp.len)-secOf(play.b0);return isFinite(t)&&t>n?t:n}catch(e){return n}}
const dsB1Dur=()=>8*60/S.bpm;
function dsB1Stop(){try{DSB.ph=null}catch(e){}}
function dsB1Info(){const el=$('#dsbInfo');if(!el)return;const C=DSB.cur,n=dsB1PhName(),four=(S.sigN||4)===4&&(S.sigD||4)===4,
  p=[n==='beat'||n.startsWith('clip:')?'':'Key A minor',(Math.round(S.bpm*100)/100)+' BPM',four?'2 bars':'8 beats',dsB1Dur().toFixed(3)+' s'];
  if(C&&C.pk)p.push(C.peak>1e-5?'peak '+(20*Math.log10(C.peak)).toFixed(1).replace('-','−')+' dBFS':'silent');const t=p.filter(Boolean).join(' · ');if(el.textContent!==t)el.textContent=t}
function dsB1WaveSoon(){clearTimeout(DSB.wt);DSB.wt=setTimeout(dsB1Wave,250)}
async function dsB1Wave(){const cv=$('#dsbWv');if(!cv||$('#ib').hidden||!ib||!ib.sel||!dsB1Cat())return;const job=++DSB.job,fx=dsB1Fx(),sel=ib.sel;
  const I=fx?ibTestInst():ibInst(),f=fx&&ib.t&&ib.t.fx&&ib.t.fx[0];if(!I||(fx&&(!f||f.type!==sel))){DSB.cur=null;dsB1WaveDraw();return}
  const notes=dsB1Notes(),spb=60/S.bpm,dur=dsB1Dur();let key='';try{key=[ib.mode,sel,S.bpm,dsB1PhName(),fx?UI.ibFxSrc||'keys':'',JSON.stringify(fx?f.p:I),JSON.stringify(notes)].join('|')}catch(e){}
  const hit=key&&DSB.wv.get(key);if(hit){DSB.cur=hit;dsB1WaveDraw();dsB1Info();return}
  DSB.cur={wait:1};dsB1WaveDraw();
  try{const sr=44100,len=Math.ceil(dur*sr),oc=new OfflineAudioContext(2,len+Math.ceil(.05*sr),sr);await wlLoad(oc);if(job!==DSB.job)return;
    let dest=oc.destination;if(fx){const n=mkFxNode(oc,f.type);n.out.connect(oc.destination);try{n.set(f.p)}catch(e){}dest=n.in}
    const g=oc.createGain();g.connect(dest);for(const[s0,l,p,v] of notes)synth(oc,I,g,p,.02+s0*spb,Math.max(.05,l*spb),v||.8);
    const b=await oc.startRendering();if(job!==DSB.job||ib.sel!==sel)return;
    const N=720,L=b.getChannelData(0),R=b.numberOfChannels>1?b.getChannelData(1):L,n=Math.min(L.length,len),pk=new Float32Array(N);let mx=0;
    for(let i=0;i<N;i++){const a=Math.floor(i*n/N),z=Math.floor((i+1)*n/N);let m=0;for(let j=a;j<z;j++){const x=Math.abs(L[j]),y=Math.abs(R[j]);if(x>m)m=x;if(y>m)m=y}pk[i]=m;if(m>mx)mx=m}
    const res={pk,peak:mx};if(key){DSB.wv.set(key,res);if(DSB.wv.size>32)DSB.wv.delete(DSB.wv.keys().next().value)}DSB.cur=res}
  catch(e){if(job!==DSB.job)return;DSB.cur={err:1}}
  dsB1WaveDraw();dsB1Info()}
/* BP1: the waveform on a dark well, a time scale under it (a tick per beat, longer per bar, seconds at each bar); drawn on change only */
function dsB1WaveDraw(){const cv=$('#dsbWv');if(!cv||!cv.isConnected)return;const r=fitRect(cv);if(r.width<2)return;const{g,w,h}=fit(cv),C=DSB.cur,spb=60/S.bpm,dur=dsB1Dur(),ih=h-17,m=Math.round(ih/2)+2,amp=ih/2-4;
  g.fillStyle='#0b0c10';g.fillRect(0,0,w,h);g.fillStyle='rgba(255,255,255,.12)';g.fillRect(6,m,w-12,1);
  const X=t=>6+(w-12)*t/dur;g.font='500 9.5px Inter,system-ui,sans-serif';g.textBaseline='alphabetic';
  for(let b=0;b<=8;b++){const x=Math.round(X(b*spb))+.5,bar=b%4===0;g.fillStyle=bar?'rgba(255,255,255,.38)':'rgba(255,255,255,.2)';g.fillRect(x-.5,ih+2,1,bar?6:3);
    if(bar){const tx=(b*spb).toFixed(2)+' s';g.fillStyle='rgba(139,139,151,.95)';g.textAlign=b===8?'right':b===0?'left':'center';g.fillText(tx,b===8?w-6:b===0?6:x,h-2)}}
  g.textAlign='left';
  if(C&&C.pk){const P=C.pk,N=P.length;g.beginPath();g.moveTo(6,m);for(let x=0;x<=w-12;x++){const v=P[Math.min(N-1,Math.floor(x/(w-12)*N))];g.lineTo(6+x,m-Math.min(1,v)*amp)}for(let x=w-12;x>=0;x--){const v=P[Math.min(N-1,Math.floor(x/(w-12)*N))];g.lineTo(6+x,m+1+Math.min(1,v)*amp)}g.closePath();g.fillStyle='rgba(236,236,241,.55)';g.fill()}
  else{g.fillStyle='rgba(139,139,151,.9)';g.font='500 11px Inter,system-ui,sans-serif';g.fillText(!C?'':C.err?'No picture for this sound':'Measuring the sound…',12,16)}
  DSB.k=cv.width/w;DSB.w=w;DSB.h=h;let bc=DSB.bc;if(!bc)bc=DSB.bc=document.createElement('canvas');bc.width=cv.width;bc.height=cv.height;bc.getContext('2d').drawImage(cv,0,0);
  if(DSB.ph&&!DSB.raf)DSB.raf=requestAnimationFrame(dsB1Tick)}
/* the scrub line: only while the preview plays */
function dsB1Scrub(t0){if(!dsB1Cat()||!$('#dsbWv'))return;DSB.ph={t0,dur:dsB1Dur()};if(!DSB.raf)DSB.raf=requestAnimationFrame(dsB1Tick)}
function dsB1Tick(){DSB.raf=0;const cv=$('#dsbWv'),P=DSB.ph,bc=DSB.bc;if(!cv||!bc||!ctx||$('#ib').hidden||bc.width!==cv.width)return;const g=cv.getContext('2d');g.setTransform(1,0,0,1,0,0);g.drawImage(bc,0,0);
  if(!P)return;const t=ctx.currentTime-P.t0;if(t>P.dur){DSB.ph=null;return}g.setTransform(DSB.k,0,0,DSB.k,0,0);g.font='500 9.5px Inter,system-ui,sans-serif';
  if(t<0){g.fillStyle='rgba(139,139,151,.95)';g.fillText('starts on the next bar',10,14)}
  else{const x=Math.round(6+(DSB.w-12)*t/P.dur)+.5;g.fillStyle='#4c8dff';g.fillRect(x-.5,2,1,DSB.h-19);const tx=t.toFixed(3)+' s',tw=g.measureText(tx).width;g.fillText(tx,x+4+tw>DSB.w-4?x-4-tw:x+4,11)}
  DSB.raf=requestAnimationFrame(dsB1Tick)}
document.addEventListener('input',e=>{if(e.target.id!=='dsbQ')return;DSB.q=e.target.value;dsB1List()});
document.addEventListener('change',e=>{const id=e.target.id;if(id==='dsbTempo'){UI.dsbTempo=e.target.checked;saveUI();return}if((id==='ibPh'||id==='ibSrc'||id==='ibAutoOn')&&dsB1Cat()){dsB1Info();dsB1WaveSoon()}
  if(e.target.closest&&e.target.closest('.dsblv'))dsB1WaveSoon()});
document.addEventListener('pointerup',e=>{if(e.target.closest&&e.target.closest('.dsblv'))setTimeout(dsB1WaveSoon,150)});
document.addEventListener('click',e=>{if(!e.target.closest||$('#ib').hidden)return;const c=e.target.closest('[data-dsc]');if(c){DSB.cat=+c.dataset.dsc;dsB1List();return}
  const p=e.target.closest('[data-dsp]');if(p){dsB1PreSet(p.dataset.dsp);return}
  if(e.target.closest('#dsbPlay')){const a=UI.ibAuto;UI.ibAuto=true;try{ibPlayPhrase()}finally{UI.ibAuto=a}return}
  if(e.target.closest('#dsbView')){UI.ibView=dsB1Cat()?'cards':'list';saveUI();IBLAY=null;const v=$('#ibList');v.dataset.k='';v.dataset.k2='';renderIB();if(!dsB1Cat()){const b=$('#ibAdd');if(b)b.focus()}}});
/* keys: up and down choose and play, left and right step the presets, Enter in the search field adds; before the browser's own keys */
addEventListener('keydown',e=>{if(!ib||$('#ib').hidden||!dsB1Cat()||!$('#dsbRows')||e.metaKey||e.ctrlKey||e.altKey)return;const g=e.target,inQ=!!(g&&g.id==='dsbQ'),k=e.key;
  if(!inQ&&g&&g.closest&&g.closest('input,select,textarea,.dsblv [data-c],#ibTry'))return;
  if(k==='ArrowUp'||k==='ArrowDown'){e.preventDefault();e.stopImmediatePropagation();dsB1Step(k==='ArrowDown'?1:-1);return}
  if((k==='ArrowLeft'||k==='ArrowRight')&&!(inQ&&g.value)){e.preventDefault();e.stopImmediatePropagation();dsB1PreStep(k==='ArrowRight'?1:-1);return}
  if(k==='Enter'&&inQ&&!e.repeat){e.preventDefault();e.stopImmediatePropagation();if(ib.sel)chooseIB();else dsB1Step(1);return}
  if(k==='Escape'&&inQ&&g.value){e.preventDefault();e.stopImmediatePropagation();g.value='';DSB.q='';dsB1List()}},true);
new MutationObserver(()=>{if($('#ib').hidden){DSB.q='';DSB.cat=-1;DSB.ph=null;DSB.job++;clearTimeout(DSB.wt)}}).observe($('#ib'),{attributes:true,attributeFilter:['hidden']});
"""

CSS = r"""/* task DS-B1a (lane A, design round 2, B3, BR2, BP1): the catalogue browser */
#ibPlane.dsbcat{position:absolute;left:0;right:0;top:40px;bottom:0;width:auto;transform:none!important;display:grid;grid-template-columns:190px minmax(0,1fr) minmax(380px,36%);grid-template-areas:"side main pv";cursor:default;contain:none}
#ibPlane.dsbcat>.dsbside{grid-area:side;overflow-y:auto;padding:10px 8px;border-right:1px solid rgba(255,255,255,.07);display:flex;flex-direction:column;gap:2px;scrollbar-width:thin}
.dsbside button{display:grid!important;grid-template-columns:7px minmax(0,1fr) auto;align-items:center;gap:8px;min-height:26px;padding:0 8px;border-radius:5px;background:none;border:0;box-shadow:none;color:#c9c9d2;font-size:var(--fs2);text-align:left;flex:none}
.dsbside button i{width:7px;height:7px;border-radius:50%;background:var(--gc)}.dsbside button span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dsbside button small{color:var(--mut);font-size:var(--fs1);font-variant-numeric:tabular-nums}.dsbside button:hover{background:rgba(255,255,255,.05)}
.dsbside button.on{background:rgba(76,141,255,.22);color:var(--ink);font-weight:var(--fw6)}.dsbside button.none{opacity:.45}
#ibPlane.dsbcat>.dsbmain{grid-area:main;display:flex;flex-direction:column;min-width:0;min-height:0;border-right:1px solid rgba(255,255,255,.07)}
.dsbhd{display:grid;grid-template-columns:minmax(0,1fr) 52px 118px;gap:10px;padding:8px 20px 6px 46px;font-size:var(--fs1);color:var(--mut);border-bottom:1px solid rgba(255,255,255,.07);flex:none}.dsbhd span:nth-child(n+2){text-align:right}
.dsbrows{flex:1;min-height:0;overflow-y:auto;padding:4px 8px 10px;scrollbar-width:thin}
#ibPlane .ibc.dsbr{display:grid!important;grid-template-columns:18px max-content minmax(0,1fr) 52px 118px;align-items:center;gap:0 10px!important;height:30px;min-height:30px;padding:0 10px!important;margin:0;border-radius:5px;background:none;border:1px solid transparent;box-shadow:none;cursor:pointer;contain:none;transform:none}
#ibPlane .dsbr .plogo{border-radius:4px;display:block}.dsbr b{font-size:var(--fs2);font-weight:var(--fw5);color:var(--ink);white-space:nowrap}
.dsbr small{font-size:var(--fs1);color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.dsbr small em{font-style:normal;color:#e6e8ee;background:rgba(255,255,255,.12);border-radius:7px;padding:1px 6px;margin-right:4px}
#ibPlane .dsbr .dsbtg{display:flex;flex-direction:row;gap:5px;justify-content:flex-end;align-items:center}.dsbtg i{width:7px;height:7px;border-radius:50%;background:var(--tc);flex:none}
#ibPlane .dsbr .dsbk{display:block;text-align:right;font-size:var(--fs1);color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#ibPlane .ibc.dsbr:hover{background:rgba(255,255,255,.04)}#ibPlane .ibc.dsbr.on{background:rgba(76,141,255,.20);border-color:rgba(140,180,255,.45)}.dsbr.on b{font-weight:var(--fw6)}
.dsbnone{padding:18px 12px;color:var(--mut);font-size:var(--fs2);margin:0}
#ibPlane.dsbcat>.dsbpv{grid-area:pv;display:flex;flex-direction:column;gap:8px;padding:12px 14px;min-width:0;min-height:0;overflow:hidden}
.dsbph{display:flex;align-items:center;gap:8px;flex:none}.dsbph .plogo{border-radius:5px}.dsbph b{font-size:var(--fs3);color:var(--ink)}
.dsbsub{color:var(--mut);font-size:var(--fs1);margin-top:-4px;flex:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dsbwv{height:104px;flex:none;border-radius:6px;background:#0b0c10;border:1px solid rgba(255,255,255,.08);overflow:hidden}.dsbwv canvas{display:block;width:100%;height:100%}
.dsbinfo{font-size:var(--fs1);color:#c9c9d2;font-variant-numeric:tabular-nums;flex:none;min-height:15px}
.dsbprh{display:flex;align-items:baseline;justify-content:space-between;flex:none;margin-top:2px}.dsbprh b{font-size:var(--fs1);color:var(--mut);font-weight:var(--fw6)}.dsbprh small{font-size:var(--fs1);color:var(--mut)}
.dsbpre{max-height:156px;overflow-y:auto;display:flex;flex-direction:column;gap:1px;flex:none;scrollbar-width:thin}
.dsbpre button{min-height:22px;padding:0 8px;text-align:left;border:0;border-radius:4px;background:none;box-shadow:none;font-size:var(--fs2);color:var(--ink);flex:none;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dsbpre button:hover{background:rgba(255,255,255,.05)}.dsbpre button.on{background:rgba(76,141,255,.2)}.dsbpre h5{margin:6px 8px 2px;font-size:var(--fs1);color:var(--mut);font-weight:var(--fw6)}.dsbpre h5:first-child{margin-top:0}
.dsbnp{margin:0;padding:2px 8px;color:var(--mut);font-size:var(--fs1)}
.dsbtl{display:flex;align-items:center;gap:8px;font-size:var(--fs1);flex:none}.dsbtl .ibsp{flex:1}.dsbtl button{min-height:24px;min-width:28px;padding:0}
#ibPlane .ibc.dsblv{display:block!important;position:relative;flex:1 1 auto;min-height:150px;padding:0!important;margin:0;border-radius:8px;background:rgba(10,11,15,.7);border:1px solid rgba(255,255,255,.08);box-shadow:none;cursor:default;overflow:hidden;transform:none}
#ibPlane .dsblv>.ibdv{position:absolute;inset:0;pointer-events:auto}
.dsbemp{margin:auto;text-align:center;display:flex;flex-direction:column;gap:6px;color:var(--mut);font-size:var(--fs2);max-width:290px}.dsbemp b{color:var(--ink);font-size:var(--fs3)}
.dsbnav .dsbq{display:flex;align-items:center;gap:6px;height:26px;padding:0 8px;border-radius:6px;background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.10);width:280px;flex:none;cursor:text}
.dsbq svg{width:14px;height:14px;fill:none;stroke:var(--mut);stroke-width:1.6;stroke-linecap:round;flex:none}
.dsbq input{flex:1;min-width:0;border:0;background:none;outline:0;color:var(--ink);font-size:var(--fs2);padding:0;min-height:0;height:22px;box-shadow:none}.dsbq:focus-within{border-color:rgba(140,180,255,.6)}
.dsbkeys{font-size:var(--fs1);color:var(--mut);white-space:nowrap;margin-left:10px;flex:none}#dsbView{flex:none;min-height:26px;padding:0 10px}
"""

rep("function askChoice(title,text,btns,icon){", JS + "function askChoice(title,text,btns,icon){")
rep("\n.dacv{display:flex;", "\n" + CSS + ".dacv{display:flex;")
# the browser's own functions: the catalogue first, the plane's layout and zoom stay off it
rep("function renderPlaneInst(){const on=UI.ibGroups!==false,", "function renderPlaneInst(){if(dsB1Cat())return dsB1Render();const on=UI.ibGroups!==false,")
rep("function renderIBTry(){const fx=ib.mode==='fx',k=ib.sel,", "function renderIBTry(){dsB1PvSync();const fx=ib.mode==='fx',k=ib.sel,")
rep("const tile=ib.sel&&document.querySelector(`#ibPlane .ibc[data-k=\"${ib.sel}\"]`);if(!tile||!ib.t){IBL=null;return}",
    "const tile=ib.sel&&document.querySelector(`#ibPlane .ibc[data-k=\"${ib.sel}\"]`);if(!tile||!ib.t||!tile.querySelector('.ibdv')){IBL=null;return}")
rep("if(pw&&(Math.abs(inn.offsetWidth-pw)>2||Math.abs(inn.offsetHeight-ph)>2))ibLayout()}",
    "if(pw&&(Math.abs(inn.offsetWidth-pw)>2||Math.abs(inn.offsetHeight-ph)>2))ibLayout();dsB1Fit(box)}")
rep("function ibLayout(){const P=$('#ibPlane');if(!P)return;", "function ibLayout(){const P=$('#ibPlane');if(!P||P.classList.contains('dsbcat'))return;")
rep("IBAR=0;const p=$('#ibPlane');if(!p)return;", "IBAR=0;const p=$('#ibPlane');if(!p||p.classList.contains('dsbcat'))return;")
rep("v.addEventListener('wheel',e=>{e.preventDefault();const r=v.getBoundingClientRect()",
    "v.addEventListener('wheel',e=>{if(e.target.closest&&e.target.closest('.dsbcat'))return;e.preventDefault();const r=v.getBoundingClientRect()")
rep("v.addEventListener('pointerdown',e=>{if(e.target.closest('.ibc,.ibzoom,.ibnav'))return;pan=",
    "v.addEventListener('pointerdown',e=>{if(e.target.closest('.ibc,.ibzoom,.ibnav,.dsbcat'))return;pan=")
rep("v.addEventListener('dblclick',e=>{if(!e.target.closest('.ibc,.ibnav')){", "v.addEventListener('dblclick',e=>{if(!e.target.closest('.ibc,.ibnav,.dsbcat')){")
rep("if(IBLAY)ibPianoPlace()},250)}).observe(sh);", "if(IBLAY)ibPianoPlace();if(dsB1Cat()){const b=$('#ibLive');if(b)dsB1Fit(b);dsB1WaveDraw()}},250)}).observe(sh);")
# the cards view gets a List button back to the catalogue (AudioLab look only)
rep('<span class="ibsp"></span><button class="ibx2" aria-label="Close">✕</button></div>`;',
    '<span class="ibsp"></span>${dsAC3()?\'<button id="dsbView" title="Show the list with one preview instead of the cards">List</button>\':\'\'}<button class="ibx2" aria-label="Close">✕</button></div>`;')
# the preview: in tempo from the next bar (catalogue only), the scrub line, the effect loop waits for the late start
rep("function ibStopPhrase(){clearTimeout(IBLOOP);", "function ibStopPhrase(){clearTimeout(IBLOOP);dsB1Stop();")
rep("const src=UI.ibPhrase||'auto',spb=60/S.bpm,t0=ctx.currentTime+.05;let notes=[];", "const src=UI.ibPhrase||'auto',spb=60/S.bpm,t0=dsB1T0();let notes=[];")
rep("v||.8);if(fx)IBLOOP=setTimeout(", "v||.8);dsB1Scrub(t0);if(fx)IBLOOP=setTimeout(")
rep("ibPlayPhrase()},8*spb*1000)}", "ibPlayPhrase()},(Math.max(0,t0-ctx.currentTime-.05)+8*spb)*1000)}")
open(F, 'w', encoding='utf-8').write(s)
print('DS-B1a applied to', F)
