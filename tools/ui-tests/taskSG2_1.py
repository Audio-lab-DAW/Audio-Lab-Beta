"""Task SG2-1 (lane R): the stem split's spectrogram columns, per chunk, and the quick split off the main thread (docs/stem-split-progress.md).
  python3 tools/ui-tests/taskSG2_1.py [index.html] [out dir] [old index.html: the quick split's stems must be bit-identical to it]
Checks: the quick split runs in a worker, posts one {t:'cols'} message per block, in order, the final columns cover the lane once,
and they match the spectrogram of the finished stems (sgColsOf on the stems); no main-thread task over 50 ms while it runs (long tasks
and a 10 ms heartbeat); stemSplit without onCols still works; the stems are bit-identical to the old main-thread split.
The neural worker (NEUW, run with a stand-in engine and model served by the test: same chunking, 7.8 s chunks, 25 % overlap) posts
one cols message per chunk, the draft stretch of chunk i is the overlap the next chunk cross-fades, the final columns match the final
stems' spectrogram, the first split shows the download, the second says cached; Stop ends a split and the next one works;
SG_HOOKS.onChunk sees every chunk of a split started from the clip menu's path (stemsFor). No console errors."""
import sys, os, json, time
from playwright.sync_api import sync_playwright
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
OLD = sys.argv[3] if len(sys.argv) > 3 else None
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('sg21')){sessionStorage.setItem('sg21','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1,wsShow:false}))}"
# a stand-in for onnxruntime-web: the same API the worker uses; the "model" splits the chunk into the input, a low band, a high band and silence
FAKE_ORT = r"""self.ort={env:{wasm:{}},Tensor:class{constructor(t,d,s){this.type=t;this.data=d;this.dims=s}},
 InferenceSession:{create:async m=>{const ns=m[0]||4;return{run:async f=>{const x=f.mix.data,N=x.length/2,o=new Float32Array(ns*2*N);
  for(let c=0;c<2;c++){let lp=0;for(let i=0;i<N;i++){const v=x[c*N+i];lp+=(v-lp)*.02;o[c*N+i]=v;if(ns>1)o[2*N+c*N+i]=lp;if(ns>2)o[4*N+c*N+i]=v-lp}}
  await new Promise(r=>setTimeout(r,150));return{stems:{data:o}}}}}}};"""
MODEL_N = 400000
SYN = r"""(sec=>{ensureCtx();const sr=44100,n=Math.round(sec*sr),b=ctx.createBuffer(2,n,sr),L=b.getChannelData(0),R=b.getChannelData(1);
 for(let i=0;i<n;i++){const t=i/sr,bt=t%0.5,k=Math.sin(2*Math.PI*(50+120*Math.exp(-bt*30))*bt)*Math.exp(-bt*9)*.6,bs=Math.sin(2*Math.PI*55*t)*.18*(t>12?1:0),
  v=Math.sin(2*Math.PI*(440+6*Math.sin(2*Math.PI*5*t))*t)*.12*((t%4)<3?1:0),h=Math.sin(2*Math.PI*9000*t)*.03*Math.exp(-((t+.25)%0.5)*40),p=Math.sin(2*Math.PI*330*t+Math.sin(t))*.05;
  L[i]=k+bs+v+h+p;R[i]=k+bs+v+h-p}return b})"""
def page(p, src):
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 1500, 'height': 950}); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.add_init_script(INIT)
    hits = {'model': 0, 'ort': 0}
    def model(r):
        hits['model'] += 1; ns = 6 if '6s' in r.request.url else 4
        r.fulfill(body=bytes([ns]) + bytes(MODEL_N - 1), headers={'content-length': str(MODEL_N), 'access-control-allow-origin': '*'}, content_type='application/octet-stream')
    def ort(r):
        hits['ort'] += 1; r.fulfill(body=FAKE_ORT, content_type='application/javascript', headers={'access-control-allow-origin': '*'})
    ctx.route('https://huggingface.co/**', model)
    ctx.route('https://cdn.jsdelivr.net/**', ort)
    ctx.route('https://app.test/**', lambda r: r.fulfill(body=src, content_type='text/html') if r.request.url.split('?')[0].endswith('/') else r.fulfill(status=404, body=''))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(2500)
    return b, pg, errs, hits
# the quick split's stems, hashed (to compare builds)
QHASH = r"""(async()=>{const b=(%s)(30);const out=await stemSplit(b,null,{bass:140,vlo:140,vhi:9000,focus:1.5,smooth:8});const h=[];for(const x of out)for(let c=0;c<2;c++){const d=await crypto.subtle.digest('SHA-256',x.getChannelData(c).slice().buffer);h.push([...new Uint8Array(d)].slice(0,8).map(v=>v.toString(16).padStart(2,'0')).join(''))}return JSON.stringify(h)})()""" % SYN
# rebuilds the full lanes from the messages and compares them with sgColsOf on the finished stems
CMP = r"""function sgT_full(msgs,ns,cw){const A=new Uint8Array(ns*96*cw),st=new Uint8Array(cw);for(const m of msgs){const n=m.prov[1]-m.fin[0];for(let j=0;j<ns;j++)for(let r=0;r<96;r++)for(let c=m.fin[0];c<m.prov[1];c++)A[(j*96+r)*cw+c]=m.cols[(j*96+r)*n+(c-m.fin[0])];for(let c=m.fin[0];c<m.fin[1];c++)st[c]=2}return{A,st}}
function sgT_cmp(A,bufs,cw){let mx=0,sum=0,cnt=0,big=0;bufs.forEach((b,j)=>{const L=b.getChannelData(0),R=b.getChannelData(1),o=new Uint8Array(96*cw);sgColsOf(q=>(L[q]+R[q])*.5,L.length,b.sampleRate,cw,0,cw,o,0,cw);
 for(let i=0;i<96*cw;i++){const d=Math.abs(o[i]-A[j*96*cw+i]);if(d>mx)mx=d;if(d>2)big++;sum+=d;cnt++}});return{mx,mean:sum/cnt,big:big/cnt}}"""
with sync_playwright() as p:
    old_hash = None
    if OLD:
        b0, pg0, e0, _ = page(p, open(OLD, encoding='utf-8').read())
        old_hash = json.loads(pg0.evaluate('c => AudioLab.run(c)', QHASH)); b0.close()
    b, pg, errs, hits = page(p, SRC)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    JA = lambda c: json.loads(R('(async()=>JSON.stringify(await ' + c + '))()'))
    ver = R('VERSION'); ok(tuple(map(int, ver.split('.'))) >= (0, 298), 'version 0.298 or later', ver)
    ok(J("typeof sgColsOf==='function'&&typeof SG_HOOKS==='object'&&typeof SG_HOOKS.onChunk==='function'&&stemSplit.length===4&&neuSeparate.length===5"), 'sgColsOf, SG_HOOKS.onChunk, stemSplit(buf,prog,P,onCols), neuSeparate(buf,kind,keep,prog,onCols)')
    R("(()=>{" + CMP.replace('\n', ' ') + ";window.sgT_full=sgT_full;window.sgT_cmp=sgT_cmp;return 1})()")
    # a full-scale sine reads 0 dB in its row, silence 0
    sine = J("(()=>{const sr=44100,n=sr*2,x=new Float32Array(n);for(let i=0;i<n;i++)x[i]=Math.sin(2*Math.PI*1000*i/sr);const o=new Uint8Array(96*4);sgColsOf(q=>x[q],n,sr,4,0,4,o,0,4);let mx=0,row=-1;for(let r=0;r<96;r++)if(o[r*4+1]>mx){mx=o[r*4+1];row=r}const z=new Uint8Array(96);sgColsOf(q=>0,n,sr,1,0,1,z,0,1);return{mx,row,f:32*Math.pow(500,(95-row+.5)/96),z:Math.max(...z)}})()")
    ok(sine['mx'] >= 250 and 900 < sine['f'] < 1100 and sine['z'] == 0, 'a full-scale 1 kHz sine reads 0 dB in the 1 kHz row (row 0 at the top), silence reads -84 dB', sine)

    print('Quick split (worker)')
    # the idle test page has its own long tasks now and then (software drawing): measure in Light mode once a 3 s window is quiet
    R('UI.lite=true;applyLite();0'); quiet = None
    for k in range(12):
        lt = JA("(async()=>{const LT=[];const po=new PerformanceObserver(l=>{for(const e of l.getEntries())LT.push(Math.round(e.duration))});po.observe({type:'longtask'});await new Promise(r=>setTimeout(r,3000));po.disconnect();return LT})()")
        if not lt: quiet = k; break
    ok(quiet is not None, 'the idle page is quiet (no long task in 3 s) before the measurement', quiet)
    q = JA(r"""(async()=>{const b=(%s)(40);const msgs=[],ps=[];const on=m=>msgs.push(m);on.cw=600;
      const LT=[];let po=null;try{po=new PerformanceObserver(l=>{for(const e of l.getEntries())LT.push(Math.round(e.duration))});po.observe({type:'longtask'})}catch(e){}
      let last=performance.now(),gap=0;const hb=setInterval(()=>{const n=performance.now();gap=Math.max(gap,n-last);last=n},10);
      const w=sgWorker(),f=w.onmessage,HT=[];w.onmessage=e=>{const t=performance.now();f(e);HT.push(performance.now()-t)};
      const t0=performance.now();const pr=stemSplit(b,p=>ps.push(+p.toFixed(3)),{},on),pre=performance.now()-t0;const out=await pr;const ms=performance.now()-t0;w.onmessage=f;
      const t1=performance.now();{const bb=ctx.createBuffer(2,b.length,44100);bb.copyToChannel(out[0].getChannelData(0),0);bb.copyToChannel(out[0].getChannelData(1),1)}const one=performance.now()-t1;
      await new Promise(r=>setTimeout(r,120));clearInterval(hb);if(po)po.disconnect();
      const F=sgT_full(msgs,4,600),C=sgT_cmp(F.A,out,600);let cont=true;for(let i=0;i<msgs.length;i++){if(msgs[i].i!==i||(i&&msgs[i].fin[0]!==msgs[i-1].fin[1])||msgs[i].s0!==(i?msgs[i-1].s1:0))cont=false}
      return{own:Math.round(Math.max(pre,one,...HT)),pre:Math.round(pre),one:Math.round(one),hmax:Math.round(Math.max(...HT)),n:msgs.length,nb:Math.ceil(b.length/(1<<18)),ps,ms:Math.round(ms),LT,gap:Math.round(gap),cont,allFin:F.st.every(v=>v===2),last:msgs.length&&msgs[msgs.length-1].fin[1],C,stems:out.length,len:out[0].length==b.length,wk:!!SG2.wk,shape:msgs[0]&&[msgs[0].rows,msgs[0].ns,msgs[0].cw,msgs[0].cols.length,msgs[0].cols.constructor.name]}})()""" % SYN)
    print('     quick split of 40 s:', q['ms'], 'ms;', q['n'], 'messages; long tasks', q['LT'], '; heartbeat gap', q['gap'], 'ms')
    ok(q['wk'] and q['stems'] == 4 and q['len'], 'the quick split ran in the worker and gave 4 stems of the clip\'s length')
    ok(q['n'] == q['nb'] and q['cont'], 'one cols message per block, in order, each starting where the last ended', (q['n'], q['nb'], q['cont']))
    ok(q['shape'] and q['shape'][0] == 96 and q['shape'][1] == 4 and q['shape'][2] == 600 and q['shape'][4] == 'Uint8Array', 'messages carry 96 rows, 4 stems, 600 columns, Uint8 dB', q['shape'])
    ok(q['allFin'] and q['last'] == 600, 'the final columns cover the whole lane once', q['last'])
    ok(q['C']['mx'] <= 1, 'the lanes are the spectrogram of the finished stems (largest difference in Uint8 dB steps)', q['C'])
    ok(len(q['ps']) == q['nb'] and q['ps'][-1] == 1, 'progress once per block, ending at 1', q['ps'])
    ok(q['own'] < 50, 'no main-thread pause over 50 ms from the quick split: the start, every message (columns and progress) and each stem made at the end, timed', {k: q[k] for k in ('pre', 'hmax', 'one')})
    print('     (for the record: long tasks of the whole page during the split', q['LT'], ', heartbeat gap', q['gap'], 'ms; the idle test page has some of its own)')
    q2 = JA(r"""(async()=>{const b=(%s)(8);const out=await stemSplit(b,null,{bass:140});return{n:out.length,l:out[0].length===b.length}})()""" % SYN)
    ok(q2['n'] == 4 and q2['l'], 'stemSplit without onCols still works', q2)
    if old_hash is not None:
        new_hash = json.loads(R(QHASH))
        ok(new_hash == old_hash, 'the quick split\'s stems are bit-identical to the old main-thread split', (new_hash[:2], old_hash[:2]))

    print('Neural worker (stand-in engine)')
    nr = JA(r"""(async()=>{const b=(%s)(30);const msgs=[],ph=[];const on=m=>msgs.push({...m,cols:m.cols.slice()});on.cw=500;
      const out=await neuSeparate(b,'n4',[true,true,true,false],(k,p,mb)=>ph.push(k),on);const keep=out.filter(Boolean);
      const F=sgT_full(msgs,3,500),C=sgT_cmp(F.A,keep,500);const N=343980,ST=N-Math.floor(N/4),tot=b.length,nc=Math.ceil(tot/ST);let draft=true,cont=true;
      for(let i=0;i<msgs.length;i++){const m=msgs[i],last=i===nc-1;if(m.i!==i||m.n!==nc||(i&&m.fin[0]!==msgs[i-1].fin[1]))cont=false;if(m.s1!==(last?tot:(i+1)*ST)||m.pe!==(last?tot:Math.min(tot,i*ST+N)))draft=false;if(!last&&!(m.prov[1]>m.prov[0]))draft=false}
      return{n:msgs.length,nc,cont,draft,C,dl:ph.includes('dl'),cached:ph.includes('cached'),runs:ph.filter(x=>x==='run').length,kept:keep.length,nulls:out.length-keep.length,ns:msgs[0]&&msgs[0].ns,allFin:F.st.every(v=>v===2)}})()""" % SYN)
    print('    ', {k: nr[k] for k in ('n', 'nc', 'C', 'runs')})
    ok(nr['n'] == nr['nc'] and nr['cont'], 'one cols message per chunk, in order, contiguous', (nr['n'], nr['nc']))
    ok(nr['draft'], 'chunk i is final up to (i+1) x 5.85 s; its draft stretch runs to the end of the chunk (the overlap the next chunk cross-fades)')
    ok(nr['ns'] == 3 and nr['kept'] == 3 and nr['nulls'] == 1, 'only the kept stems get columns (3 of 4)', (nr['ns'], nr['kept']))
    ok(nr['allFin'] and nr['C']['mx'] <= 2 and nr['C']['big'] == 0, 'the final columns match the spectrogram of the final stems', nr['C'])
    ok(nr['dl'] and hits['model'] == 1, 'the first split downloads the model (progress shown)', hits)
    nr2 = JA(r"""(async()=>{const b=(%s)(10);const ph=[];let n=0;const on=m=>n++;on.cw=200;await neuSeparate(b,'n4',[true,true,true,true],(k)=>ph.push(k),on);return{n,dl:ph.includes('dl'),init:ph.includes('init')}})()""" % SYN)
    ok(not nr2['dl'] and not nr2['init'] and nr2['n'] == 2 and hits['model'] == 1, 'the second split keeps the loaded model (no download, no load), columns still per chunk', (nr2, hits))
    st = JA(r"""(async()=>{const b=(%s)(30);let n=0,err='';const on=m=>{n++;if(n===1)sgStopNeural()};on.cw=200;try{await neuSeparate(b,'n4',[true,true,true,true],()=>{},on)}catch(e){err=e.message+(e.stopped?' (stopped)':'')}
      const b2=(%s)(6);let n2=0;const on2=m=>n2++;on2.cw=100;const ph=[];const o2=await neuSeparate(b2,'n4',[true,true,true,true],k=>ph.push(k),on2);return{err,n,n2,ok:o2.length===4,cached:ph.includes('cached'),dl:ph.includes('dl')}})()""" % (SYN, SYN))
    ok(st['err'] == 'stopped (stopped)' and st['n'] == 1 and st['ok'] and st['n2'] == 2, 'Stop ends a neural split at once; the next split works', st)
    ok(st['cached'] and not st['dl'] and hits['model'] == 1, 'after Stop the model is loaded again from the cache, not downloaded', (st, hits))
    sq = JA(r"""(async()=>{const b=(%s)(30);let n=0,err='';const on=m=>{n++;if(n===2)sgStopQuick()};on.cw=200;try{await stemSplit(b,null,{},on)}catch(e){err=e.message}const o2=await stemSplit((%s)(3),null,{});return{err,n,ok:o2.length===4}})()""" % (SYN, SYN))
    ok(sq['err'] == 'stopped' and sq['ok'], 'Stop ends a quick split; the next one works', sq)

    print('stemsFor passes every chunk to SG_HOOKS.onChunk')
    hk = JA(r"""(async()=>{const b=(%s)(12);const id=addBuf(b);const t=mkTrack('audio',null,'SG test');S.tracks.push(t);const c=mkClip({start:0,len:b.duration*S.bpm/60,name:'sgclip',buf:id,dur:b.duration,gain:0,fi:0,fo:0});t.clips.push(c);
      const seen=[];const h0=SG_HOOKS.onChunk;SG_HOOKS.onChunk=(j,m)=>seen.push([j.kind,j.name,m.i]);const n0=S.tracks.length;
      const pr=stemsFor(t,c);await new Promise(r=>setTimeout(r,300));const q=document.querySelector('#stq [name=steng][value=quick]');q.checked=true;q.dispatchEvent(new Event('change',{bubbles:true}));document.getElementById('stGo').click();let done=false;pr.then(()=>done=true);for(let k=0;k<300&&!done;k++){await new Promise(r=>setTimeout(r,100));const a=document.querySelector('[data-al="stem.add"]');if(a&&!a.disabled)a.click()}await pr;
      SG_HOOKS.onChunk=h0;return{seen,added:S.tracks.length-n0}})()""" % SYN)
    ok(len(hk['seen']) == 3 and hk['seen'][0][:2] == ['quick', 'sgclip'] and hk['added'] == 4, 'a quick split from stemsFor: every block reaches SG_HOOKS.onChunk with the job, 4 tracks added', hk)
    ok(not errs, 'no console errors', errs[:3])
    b.close()
print('%d/%d' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
