"""Task NI-5b (lane D): I12 masking cables, part 2: the fixes.
Edit script with unique asserted anchors (needs NI-5a in the file), so a rebase can re-run it on a fresh index.html.
  python3 tools/feature-lab/ni/ni_5b.py [index.html]
Adds:
  - the Ducker (task AB's 'duck', worklet al-abxduck) learns an opt-in mode p.bd "duck only the focus band": the duck gain is applied to a
    band of the ducked sound around the focus frequency (p.ff, width p.bq as Q) instead of to all of it: out = x - (1 - gain) * band(x), with a
    zero-phase state-variable band-pass, so at the centre the band is ducked by the full amount and away from it nothing changes. Without
    p.bd the per-sample code is the one it was (bit-identical); abxSp passes bd and bq along
  - in the Ducker window, with Listen to "Band" (or the mode on): a button "Only this band" (NI_HOOKS.duckBandRow(el, t, f) for a lane that
    rebuilds that window)
  - two fixes in the clash card (through NI_HOOKS.clashPop), each one undo step:
      Duck <covered> under <louder> in this band: a Ducker on the covered track, triggered by the louder one, listening to that band, ducking
      only that band (amount 50%, about 6 dB at the centre; the ducked band twice as wide as the clash range, so its edges are ducked too; trigger level 9 dB under the louder track's band level)
      Notch <covered> by 2 dB at <f>: a -2 dB bell on the covered track's first Pro EQ (an unused bell band nearest in frequency, or a new
      Pro EQ), Q from the band's width
  - a clash already handled by such a band Ducker is drawn dimmed and dashed, labelled "Bass ducks under Kick, ...", and not counted in the
    legend (the per-track measure does not hear ducking, so it says so instead of hiding the cable); the card then offers to open the Ducker
"""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(P, encoding='utf-8').read()
MARK = '/* ===== lane D (task NI-5b)'
if MARK in s:
    print('NI-5b already applied'); sys.exit(0)
assert '/* ===== end of lane D NI-5a ===== */' in s, 'NI-5a must be in the file first'

def rep(s, old, new):
    n = s.count(old)
    assert n == 1, (old[:70], n)
    return s.replace(old, new)

# 1. the Ducker worklet: the band mode (only when p.bd; the old per-sample path is untouched)
s = rep(s, "this.pkR=Math.exp(-1/(.01*sr))}",
        "this.pkR=Math.exp(-1/(.01*sr));/* NI-5b: duck only a band */this.bd=P.bd?1:0;this.bg=Math.tan(Math.PI*f/sr);this.bk=1/Math.max(.3,nz(P.bq,4.3));if(!this.bs)this.bs=new Float64Array(4)}")
s = rep(s, "for(let i=0;i<n;i++){let v=0,ax=0;",
        "const bd=this.bd,bs=this.bs,bG=this.bg,bK=this.bk,bA1=1/(1+bG*(bG+bK)),bA2=bG*bA1,bA3=bG*bA2;\n   for(let i=0;i<n;i++){let v=0,ax=0;")
s = rep(s, "if(ls){oL[i]=v;oR[i]=v}else{oL[i]=bL[r]*gn;oR[i]=bR[r]*gn}",
        "if(ls){oL[i]=v;oR[i]=v}else if(bd){const xl=bL[r],xr=bR[r],u=1-gn;let w3=xl-bs[1],w1=bA1*bs[0]+bA2*w3,w2=bs[1]+bA2*bs[0]+bA3*w3;bs[0]=2*w1-bs[0];bs[1]=2*w2-bs[1];oL[i]=xl-u*bK*w1;w3=xr-bs[3];w1=bA1*bs[2]+bA2*w3;w2=bs[3]+bA2*bs[2]+bA3*w3;bs[2]=2*w1-bs[2];bs[3]=2*w2-bs[3];oR[i]=xr-u*bK*w1}else{oL[i]=bL[r]*gn;oR[i]=bR[r]*gn}")

# 2. NI-5a's drawing learns handled clashes (lane D's own code)
s = rep(s, "const key=C.list.map(c=>c.a.id+c.b.id+c.m0+'-'+c.m1+':'+Math.round(c.s)).join('|')",
        "const key=C.list.map(c=>c.a.id+c.b.id+c.m0+'-'+c.m1+':'+Math.round(c.s)+(c.duck?'d':'')).join('|')")
s = rep(s, "front+=`<path class=\"nicc\" data-n=\"${i}\" d=\"${d}\" stroke-width=\"${wd}\"/>`;",
        "front+=`<path class=\"nicc${c.duck?' nidk':''}\" data-n=\"${i}\" d=\"${d}\" stroke-width=\"${wd}\"/>`;")
s = rep(s, "const tx=`${c.a.name} vs ${c.b.name}, ${c.range}`,tw=cs2Tw(tx)",
        "const tx=c.duck?`${c.b.name} ducks under ${c.a.name}, ${c.range}`:`${c.a.name} vs ${c.b.name}, ${c.range}`,tw=cs2Tw(tx)")
s = rep(s, "cnt=on?(C.meas&&!C.list.length?'…':String(C.list.length)):''",
        "cnt=on?(C.meas&&!C.list.length?'…':String(C.list.filter(c=>!c.duck).length)):''")

# 3. CSS
CSS = r"""/* lane D (task NI-5b): handled clashes, the fixes in the clash card, the band button in the Ducker window */
#mixWin svg.cabs .nicc.nidk{stroke-dasharray:3 5;opacity:.45}
#niClashPop .nicpf{display:flex;flex-direction:column;gap:5px;margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,.1)}
#niClashPop .nicpf button{display:flex;flex-direction:column;align-items:flex-start;gap:1px;height:auto;min-height:28px;padding:4px 9px;text-align:left}
#niClashPop .nicpf button small{color:var(--mut);font-size:var(--fs1);font-weight:var(--fw4)}
#niClashPop .nicpf p{margin:0;font-size:var(--fs1)}
.abxfo button.nibd,.agfo button.nibd{margin-left:6px;min-height:20px;padding:0 8px;font-size:var(--fs1)}.abxfo button.nibd.on,.agfo button.nibd.on{background:linear-gradient(#e86bff,#b148d0);color:#16061b;border-color:#5c1f6b}
"""
s = rep(s, ".dacv{display:flex;", CSS + ".dacv{display:flex;")

# 4. JS after NI-5a
JS = r"""
/* ===== lane D (task NI-5b): I12 masking cables, part 2: the fixes =====
   Two fixes from the clash card, each one undo step: duck the covered track under the louder one in that band only (the Ducker's new band
   mode), or a 2 dB bell cut on the covered track's Pro EQ. A clash already handled by a band Ducker is drawn dimmed: the per-track measure
   (NI-3) renders one track at a time and so does not hear ducking. */
{const _s=abxSp;abxSp=function(p){const o=_s.apply(this,arguments);o.bd=p&&p.bd?1:0;o.bq=+(p&&p.bq)||4.3;return o}}
/* centre and Q of a clash's band range */
function NI_clBand(c){const a=NI_clEdges(c.m0)[0],b=NI_clEdges(c.m1)[1],fc=Math.sqrt(a*b),n=Math.pow(2,Math.log2(b/a));return{fa:a,fb:b,fc,q:Math.sqrt(n)/(n-1)}}
/* a band Ducker on the covered track that this clash's louder track triggers, around this band */
function NI_clDuckOf(c){const B=NI_clBand(c);for(const[t,s] of[[c.b,c.a],[c.a,c.b]])for(const f of t.fx||[])if(f.type==='duck'&&f.on&&f.p&&f.p.bd&&f.p.src===s.id&&f.p.ff>=B.fa*.8&&f.p.ff<=B.fb*1.25)return{t,f};return null}
{const _at=NI_clashAt;NI_clashAt=function(){const R=_at.apply(this,arguments);for(const c of R.list){const d=NI_clDuckOf(c);c.duck=!!d;c.duckFx=d&&d.f.id}return R};NI.clash.at=NI_clashAt}
const NI_fmtHz=f=>f>=1000?(Math.round(f/100)/10)+' kHz':Math.round(f)+' Hz';
/* fix 1: duck the covered track under the louder one, in this band only */
function NI_clFixDuck(c){const B=NI_clBand(c),a=c.a,b=c.b;if(!trkById(a.id)||!trkById(b.id))return null;pushUndo();const f=mkFx('duck');
  Object.assign(f.p,{src:a.id,fo:'band',ff:Math.round(clamp(B.fc,30,8000)),bd:1,bq:+clamp(B.q/2,.5,6).toFixed(2),amt:50,th:Math.round(clamp(c.la-9,-60,-6))});b.fx.push(f);changed(true);
  try{renderFx()}catch(e){}try{renderMixer()}catch(e){}try{cabSoon()}catch(e){}toast(`${b.name} now ducks under ${a.name} at ${c.range} only, about 6 dB while ${a.name} plays there.`);return f}
/* fix 2: a 2 dB bell cut on the covered track's Pro EQ */
function NI_clFixNotch(c){const B=NI_clBand(c),b=c.b;if(!trkById(b.id))return null;pushUndo();let f=(b.fx||[]).find(x=>x.type==='eq'&&x.on&&x.p&&Array.isArray(x.p.bands));
  const lf=v=>Math.log2(Math.max(10,v)),free=f?f.p.bands.map((x,i)=>[x,i]).filter(([x])=>x.t==='peaking'&&(!x.on||eqIdle(x))):[];
  if(!f||!free.length){f=mkFx('eq');b.fx.push(f);free.length=0;f.p.bands.forEach((x,i)=>{if(x.t==='peaking'&&(!x.on||eqIdle(x)))free.push([x,i])})}
  free.sort((p,q)=>Math.abs(lf(p[0].f)-lf(B.fc))-Math.abs(lf(q[0].f)-lf(B.fc)));const[bd,bi]=free[0];Object.assign(bd,{t:'peaking',f:Math.round(B.fc),g:-2,q:+clamp(B.q,.3,12).toFixed(2),on:true});
  changed(true);try{renderFx()}catch(e){}toast(`${b.name}: 2 dB less at ${NI_fmtHz(B.fc)} on its Pro EQ (band ${bi+1}).`);return{f,band:bi}}
/* the fixes in the clash card */
NI_HOOKS.clashPop=function(c,p){const B=NI_clBand(c),bx=p.querySelector('.nicpb'),box=document.createElement('div');box.className='nicpf';
  if(c.duck){box.innerHTML=`<p>${esc(c.b.name)} already ducks under ${esc(c.a.name)} in this band. Measuring one track at a time cannot hear ducking, so this cable stays, dimmed.</p><button type="button" data-nf="open" title="Open the Ducker that handles this clash">Open the Ducker<small>Change how much and how fast ${esc(c.b.name)} ducks</small></button>`}
  else box.innerHTML=`<button type="button" data-nf="duck" title="Add a Ducker to ${esc(c.b.name)} that lowers only ${esc(c.range)}, and only while ${esc(c.a.name)} plays there (about 6 dB). One undo step.">Duck ${esc(c.b.name)} under ${esc(c.a.name)} in this band<small>Only ${esc(c.range)}, only while ${esc(c.a.name)} plays</small></button>
    <button type="button" data-nf="notch" title="Cut ${esc(c.b.name)} by 2 dB around ${NI_fmtHz(B.fc)} with a bell on its Pro EQ (a new Pro EQ if it has none). One undo step.">Notch ${esc(c.b.name)} by 2 dB at ${NI_fmtHz(B.fc)}<small>Always on, a small bell cut on its Pro EQ</small></button>`;
  p.insertBefore(box,bx);box.addEventListener('click',e=>{const b=e.target.closest('[data-nf]');if(!b)return;e.stopPropagation();const k=b.dataset.nf;NI_clPopClose();
    if(k==='duck')NI_clFixDuck(c);else if(k==='notch')NI_clFixNotch(c);else if(k==='open'&&c.duckFx)abxOpen(c.duckFx);
    NI.clash.drawn='';setTimeout(()=>{try{NI_clTick(true)}catch(_){}},0)});
  const r=p.getBoundingClientRect();if(r.bottom>innerHeight-4)p.style.top=Math.max(4,innerHeight-r.height-4)+'px'};
/* the Ducker window: "Only this band" next to Listen to (Band) */
NI_HOOKS.duckBandRow=function(el,t,f){const fo=el&&el.querySelector('.agfo,.abxfo');if(!fo)return;let b=fo.querySelector('.nibd');const show=(f.p.fo||'all')==='band'||!!f.p.bd;
  if(!show){if(b)b.remove();return}if(!b){b=document.createElement('button');b.type='button';b.className='nibd';fo.appendChild(b)}
  b.classList.toggle('on',!!f.p.bd);b.setAttribute('aria-pressed',String(!!f.p.bd));b.textContent='Only this band';
  b.title=f.p.bd?`On: only the band around the focus frequency of ${t.name} is ducked, the rest stays. Click to duck all of it.`:`Off: all of ${t.name} is ducked. Click to duck only the band around the focus frequency.`;
  b.onclick=e=>{e.stopPropagation();pushUndo();f.p.bd=!f.p.bd;if(!f.p.bq)f.p.bq=4.3;abxSet(t,f);changed(true);const W=ABXW.get(f.id);if(W)abxBuild(W);else NI_HOOKS.duckBandRow(el,t,f)}};
/* the Ducker window's builder: today agBuild (which calls itself by name), before it abxBuild; both get the row */
{const wrap=_b=>function(W){const r=_b.apply(this,arguments);try{const F=abxFind(W.fid);if(F)NI_HOOKS.duckBandRow(W.el,F.t,F.f)}catch(e){console.warn('NI duck band',e)}return r};
 if(typeof agBuild==='function'){const same=abxBuild===agBuild;agBuild=wrap(agBuild);if(same)abxBuild=agBuild;else abxBuild=wrap(abxBuild)}else abxBuild=wrap(abxBuild)}
NI.clash.fixDuck=NI_clFixDuck;NI.clash.fixNotch=NI_clFixNotch;NI.clash.band=NI_clBand;
/* ===== end of lane D NI-5b ===== */"""
s = rep(s, "/* ===== end of lane D NI-5a ===== */", "/* ===== end of lane D NI-5a ===== */" + JS)
open(P, 'w', encoding='utf-8').write(s)
print('NI-5b applied')
