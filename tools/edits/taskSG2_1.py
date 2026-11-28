"""Task SG2-1 (lane R, prefix sg): the stem split's workers post spectrogram columns per chunk; the quick split moves into a worker.
Inserts taskSG2_1_block.js (sgColsOf, sgColEnds, the quick worker SGW, sgMixCols, SG_HOOKS) before the neural splitter,
turns the old main-thread stemSplit into sgQuickCore (the same arithmetic, run in the worker) with a new stemSplit(buf,prog,P,onCols)
in front of it, and gives NEUW and neuSeparate the {t:'cols'} messages and onCols. stemsFor passes every chunk to SG_HOOKS.onChunk.
Bumps VERSION (highest on main + 0.001).
  python3 tools/edits/taskSG2_1.py [index.html]"""
import sys, os, re
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(P, encoding='utf-8').read()
blk = open(os.path.join(H, 'taskSG2_1_block.js'), encoding='utf-8').read()
assert 'task SG2-1' not in s, 'already applied'
for n in ('sgColsOf', 'sgColEnds', 'sgQuickCore', 'sgWSrc', 'sgWorker', 'sgStopQuick', 'sgStopNeural', 'sgReq', 'sgLR', 'sgMixCols', 'SG_HOOKS', 'SG2'):
    assert not re.search(r'(function|const|let|var)\s+' + n + r'\b', s), n + ' exists already'
def one(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:90]); s = s.replace(a, b)
# 1. the old quick split becomes the worker's core
A0 = "async function stemSplit(buf,prog,P){P=Object.assign({bass:140,vlo:140,vhi:9000,smooth:8,focus:1.5},P||{});STF.init();const N=STFT.n,H=STFT.hop,K=N/2+1,sr=buf.sampleRate,len=buf.length,L=buf.getChannelData(0),R=buf.numberOfChannels>1?buf.getChannelData(1):L;"
A1 = "    if(prog)prog(s1/len);await new Promise(r=>setTimeout(r,0))}\n  return out.map(([a,b])=>{const bb=ctx.createBuffer(2,len,sr);bb.copyToChannel(a,0);bb.copyToChannel(b,1);return bb})}\n"
assert s.count(A0) == 1 and s.count(A1) == 1 and s.index(A0) < s.index(A1)
i0 = s.index(A0); i1 = s.index(A1) + len(A1)
core = s[i0:i1]
assert 'await' not in core[len(A0):-len(A1)], 'the core has no other await'
core = ("/* the quick split's arithmetic (unchanged since v0.2xx), run in the worker SGW (task SG2-1): L and R in, 4 stems x [L,R] out; blk(s0,s1,out) after each block */\n"
        "function sgQuickCore(L,R,sr,P,blk){P=Object.assign({bass:140,vlo:140,vhi:9000,smooth:8,focus:1.5},P||{});STF.init();const N=STFT.n,H=STFT.hop,K=N/2+1,len=L.length;"
        + core[len(A0):-len(A1)] + "    if(blk)blk(s0,s1,out)}\n  return out}\n")
NEWQ = ("/* task SG2-1: the quick split runs in the worker SGW and never pauses the app; prog(p) once per block, onCols(msg) the lanes' columns */\n"
        "async function stemSplit(buf,prog,P,onCols){const len=buf.length,sr=buf.sampleRate,[L,R]=sgLR(buf),cw=onCols?(onCols.cw|0)||512:0,Q={};P=P||{};for(const k of['bass','vlo','vhi','smooth','focus'])if(P[k]!=null)Q[k]=+P[k];\n"
        "  const d=await sgReq({t:'quick',L,R,sr,P:Q,cw,ks:onCols&&onCols.ks||null},[L.buffer,R.buffer],m=>{if(m.t==='p'){if(prog)prog(m.p)}else if(m.t==='cols'&&onCols)onCols(m)});\n"
        "  ensureCtx();const bufs=[];for(const[a,b] of d.out){const bb=ctx.createBuffer(2,len,sr);bb.copyToChannel(a,0);bb.copyToChannel(b,1);bufs.push(bb);await new Promise(r=>setTimeout(r,0))}return bufs}\n")
s = s[:i0] + NEWQ + core + s[i1:]
# 2. the block, before the neural splitter
A = "/* ===================== neural stem separation: HTDemucs v4 (Meta, MIT weights) running in the browser ====================="
m = re.findall(r"const VERSION='(\d+)\.(\d+)'", s); assert len(m) == 1
v = '%s.%03d' % (m[0][0], int(m[0][1]) + 1)
one(A, blk.replace('v0.000', 'v' + v) + A)
# 3. the neural worker posts the columns of every chunk
one("const NEUW=`let ortm=null,sess=null,cur='';", "const NEUW=`${sgColsOf.toString()}\n${sgColEnds.toString()}\nlet ortm=null,sess=null,cur='';")
one(" const cb=new Float32Array(2*N);\n", " const cb=new Float32Array(2*N);let fc=0,fe0=0;const cw=d.cw|0,KS=keep.map((k,j)=>k?j:-1).filter(j=>j>=0);postMessage({t:'st',m:'run'});/* task SG2-1: the lanes' columns; 'run': the model is loaded, separating starts */\n")
one("  for(let s=0;s<cl;s++)wt[s0+s]+=win[s];postMessage({t:'p',p:(i+1)/nc})}",
    "  for(let s=0;s<cl;s++)wt[s0+s]+=win[s];\n"
    "  if(cw){const last=i===nc-1,fe=last?total:Math.min(total,(i+1)*ST),pe=last?total:Math.min(total,s0+N),E=sgColEnds(total,cw,fc,fe,pe),n=E[1]-fc,cols=new Uint8Array(KS.length*96*n);\n"
    "   KS.forEach((k,j)=>{const A=out[k][0],B=out[k][1];sgColsOf(q=>(A[q]+B[q])*.5/Math.max(wt[q],1e-8),total,44100,cw,fc,E[1],cols,j*96*n,n)});\n"
    "   postMessage({t:'cols',i,n:nc,s0:fe0,s1:fe,pe,fin:[fc,E[0]],prov:[E[0],E[1]],rows:96,ns:KS.length,cw,cols},[cols.buffer]);fc=E[0];fe0=fe}\n"
    "  postMessage({t:'p',p:(i+1)/nc})}")
# 4. neuSeparate: onCols, Stop, the stems made a few at a time
one("async function neuSeparate(buf,kind,keep,prog){const M=NEUM[kind],[L,R]=await neuTo44(buf),w=neuWorker();\n"
    "  return new Promise((res,rej)=>{w.onmessage=e=>{const d=e.data;if(d.t==='dl')prog('dl',d.p,d.mb);else if(d.t==='st')prog(d.m,0);else if(d.t==='p')prog('run',d.p);else if(d.t==='err'){rej(new Error(d.m))}else if(d.t==='done'){ensureCtx();res(d.out.map(O=>{if(!O)return null;const b=ctx.createBuffer(2,O[0].length,44100);b.copyToChannel(O[0],0);b.copyToChannel(O[1],1);return b}))}};\n"
    "    w.onerror=e=>rej(new Error(e.message||'the separation worker failed'));w.postMessage({base:NEUBASE,url:M.url,L,R,ns:M.stems.length,keep,cores:navigator.hardwareConcurrency||4},[L.buffer,R.buffer])})}",
    "async function neuSeparate(buf,kind,keep,prog,onCols){const M=NEUM[kind],[L,R]=await neuTo44(buf),w=neuWorker(),cw=onCols?(onCols.cw|0)||512:0;\n"
    "  const out=await new Promise((res,rej)=>{SG2.neuRej=rej;w.onmessage=e=>{const d=e.data;if(d.t==='dl')prog('dl',d.p,d.mb);else if(d.t==='st')prog(d.m,0);else if(d.t==='p')prog('run',d.p);else if(d.t==='cols'){if(onCols)onCols(d)}else if(d.t==='err'){SG2.neuRej=null;rej(new Error(d.m))}else if(d.t==='done'){SG2.neuRej=null;res(d.out)}};\n"
    "    w.onerror=e=>{SG2.neuRej=null;rej(new Error(e.message||'the separation worker failed'))};w.postMessage({base:NEUBASE,url:M.url,L,R,ns:M.stems.length,keep,cores:navigator.hardwareConcurrency||4,cw},[L.buffer,R.buffer])});\n"
    "  ensureCtx();const r=[];for(const O of out){if(!O){r.push(null);continue}const b=ctx.createBuffer(2,O[0].length,44100);b.copyToChannel(O[0],0);b.copyToChannel(O[1],1);r.push(b);await new Promise(q=>setTimeout(q,0))}return r}")
# 5. stemsFor: every chunk to SG_HOOKS.onChunk (the lanes come in SG2-2)
one("try{const all=await neuSeparate(src,PS.engine,PS.keep,(ph,p,mb)=>{if(ph==='dl')mdJob('stem',`Downloading the stem model, ${M.mb} MB (only the first time)`,p);else if(ph==='init')mdJob('stem','Loading the stem model',null);else if(ph==='run')mdJob('stem','Separating with HTDemucs',p)});",
    "try{const sgj={kind:PS.engine,name:c.name||t.name},sgc=d=>SG_HOOKS.onChunk(sgj,d);const all=await neuSeparate(src,PS.engine,PS.keep,(ph,p,mb)=>{if(ph==='dl')mdJob('stem',`Downloading the stem model, ${M.mb} MB (only the first time)`,p);else if(ph==='init')mdJob('stem','Loading the stem model',null);else if(ph==='run')mdJob('stem','Separating with HTDemucs',p)},sgc);")
one("mdJob('stem','Splitting into stems',0);try{const all=await stemSplit(src,p=>mdJob('stem','Splitting into stems',p),PS);",
    "mdJob('stem','Splitting into stems',0);try{const sgj={kind:'quick',name:c.name||t.name};const all=await stemSplit(src,p=>mdJob('stem','Splitting into stems',p),PS,d=>SG_HOOKS.onChunk(sgj,d));")
s = re.sub(r"const VERSION='\d+\.\d+'", "const VERSION='%s'" % v, s, count=1)
open(P, 'w', encoding='utf-8').write(s)
print(v)
