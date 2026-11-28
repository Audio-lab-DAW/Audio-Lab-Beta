"""Task SG2-2 (lane R): G1 lanes under the mix in the Split sheet, P1 draft stretch, F1 scan (docs/stem-split-progress.md).
  python3 tools/ui-tests/taskSG2_2.py [index.html] [out dir]
Checks, with the neural worker on a stand-in engine served by the test (the app's own chunking) and the real quick split:
the Split sheet stays open after Split and becomes the lanes (mix on top, one lane per kept stem); during the model download the
lanes are empty, the mix is drawn and the read-out says MB of MB; the lanes fill at the true position chunk by chunk (one
putImageData per lane per chunk, nothing per frame, no requestAnimationFrame from the splitter); the amber edge sits at the last
final sample with a 120 ms transition (0 with Reduce motion); the draft stretch is drawn at half strength and repainted when final
(not in Light mode); the chunk at work has the soft scan (a still hatch with Reduce motion); the read-out (L2 units) counts chunks,
time and time left; at the end every lane matches the final stem's spectrogram, shows its level and a tick (the silent stem
unticked) and Add 3 tracks adds them (one undo step, the clip muted); Stop changes nothing; Keep working closes the sheet and the
split goes on; several clips read "clip 2 of 3"; the quick split fills its 4 lanes block by block without a main-thread pause over
50 ms; a neural split that cannot run falls back to the quick split in the same sheet; every control has an id (data-al).
Screenshots dark, Light mode and Reduce motion. No console errors."""
import sys, os, json
from playwright.sync_api import sync_playwright
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('sg22')){sessionStorage.setItem('sg22','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1,wsShow:false,lite:false,liteMan:false}))}"
FAKE_ORT = r"""self.ort={env:{wasm:{}},Tensor:class{constructor(t,d,s){this.type=t;this.data=d;this.dims=s}},
 InferenceSession:{create:async m=>{const ns=m[0]||4,dl=(m[1]||40)*10;return{run:async f=>{const x=f.mix.data,N=x.length/2,o=new Float32Array(ns*2*N);
  for(let c=0;c<2;c++){let lp=0;for(let i=0;i<N;i++){const v=x[c*N+i];lp+=(v-lp)*.02;o[c*N+i]=v-lp;if(ns>1)o[2*N+c*N+i]=lp;if(ns>2)o[4*N+c*N+i]=v*.5}}
  await new Promise(r=>setTimeout(r,dl));return{stems:{data:o}}}}}}};"""
SYN = r"""(sec=>{ensureCtx();const sr=44100,n=Math.round(sec*sr),b=ctx.createBuffer(2,n,sr),L=b.getChannelData(0),R=b.getChannelData(1);
 for(let i=0;i<n;i++){const t=i/sr,bt=t%0.5,k=Math.sin(2*Math.PI*(50+120*Math.exp(-bt*30))*bt)*Math.exp(-bt*9)*.6,bs=Math.sin(2*Math.PI*55*t)*.18*(t>12?1:0),
  v=Math.sin(2*Math.PI*(440+6*Math.sin(2*Math.PI*5*t))*t)*.12*((t%4)<3?1:0),h=Math.sin(2*Math.PI*9000*t)*.03*Math.exp(-((t+.25)%0.5)*40),p=Math.sin(2*Math.PI*330*t+Math.sin(t))*.05;
  L[i]=k+bs+v+h+p;R[i]=k+bs+v+h-p}return b})"""
CLIP = r"""(sec=>{const b=(%s)(sec);const id=addBuf(b);const t=mkTrack('audio',null,'Loop');S.tracks.push(t);const c=mkClip({start:0,len:b.duration*S.bpm/60,name:'Loop',buf:id,dur:b.duration,gain:0,fi:0,fo:0});t.clips.push(c);changed(true);window.sgT={t,c};return 1})""" % SYN
# a split started as the clip menu does: stemsFor, pick the engine, Split
START = r"""(eng=>{window.sgT.pr=stemsFor(sgT.t,sgT.c);return new Promise(r=>setTimeout(()=>{const q=document.querySelector('#stq [name=steng][value='+eng+']');q.checked=true;q.dispatchEvent(new Event('change',{bubbles:true}));
  if(eng==='n4'){const c=document.querySelector('#stq [data-s="2"]');if(c)c.checked=true}document.getElementById('stGo').click();r(1)},250))})"""
JOB = "(()=>{const j=[...SG2.jobs][0];return j?{ph:j.phase,done:j.done,n:j.n,fin:j.fin,total:j.total,ns:j.ns,cw:j.cw,st1:j.st?j.st.reduce((a,v)=>a+(v===1),0):0,st2:j.st?j.st.reduce((a,v)=>a+(v===2),0):0,mix:!!j.mix}:null})()"
def page(p, src, reduced=False, ort_ok=True, delay=40):
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    cx = b.new_context(viewport={'width': 1400, 'height': 900}, reduced_motion='reduce' if reduced else 'no-preference'); pg = cx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.add_init_script(INIT)
    def model(r):
        ns = 6 if '6s' in r.request.url else 4; n = 3000000
        r.fulfill(body=bytes([ns, delay]) + bytes(n - 2), headers={'content-length': str(n), 'access-control-allow-origin': '*'}, content_type='application/octet-stream')
    cx.route('https://huggingface.co/**', model)
    cx.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(body=FAKE_ORT, content_type='application/javascript', headers={'access-control-allow-origin': '*'}) if ort_ok else r.fulfill(status=404, body=''))
    cx.route('https://app.test/**', lambda r: r.fulfill(body=src, content_type='text/html') if r.request.url.split('?')[0].endswith('/') else r.fulfill(status=404, body=''))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(2500)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    JA = lambda c: json.loads(R('(async()=>JSON.stringify(await ' + c + '))()'))
    return b, pg, errs, R, J, JA
def wait(pg, J, cond, ms=20000):
    for k in range(ms // 50):
        v = J(cond)
        if v: return v
        pg.wait_for_timeout(50)
    return None
SHEET = "document.querySelector('#stq .sgSh')"
with sync_playwright() as p:
    b, pg, errs, R, J, JA = page(p, SRC, delay=60)
    ver = R('VERSION'); ok(tuple(map(int, ver.split('.'))) >= (0, 299), 'version 0.299 or later', ver)
    blk = SRC[SRC.index('stem split lanes, step 2'):SRC.index('/* ===================== neural stem separation')]
    ok('requestAnimationFrame' not in blk and 'setInterval(' in blk and blk.count('setInterval(') == 1, 'the lanes code asks for no animation frames; its only timer is the read-out once a second')
    ok('backdrop-filter' not in SRC[SRC.index('/* task SG2-2 (lane R)'):SRC.index('.a2dbar{height:6px;')].replace('no backdrop-filter */',''), 'no backdrop-filter in the lanes\' CSS')
    R(CLIP + '(30)')
    # this test machine is slow, so AudioLab may turn Light mode or still effects on by itself: keep them off here (a fast computer)
    R("(()=>{UI.lite=false;applyLite();const B=document.body,k=()=>B.classList.remove('lite','fxstill','lkm1');k();new MutationObserver(k).observe(B,{attributes:true,attributeFilter:['class']});return 1})()"); pg.wait_for_timeout(200)
    print('     body:', J('document.body.className'))
    # count putImageData on the lanes' canvases and requestAnimationFrame callbacks that come from the splitter
    R("""(()=>{window.sgPI=0;const f=CanvasRenderingContext2D.prototype.putImageData;CanvasRenderingContext2D.prototype.putImageData=function(){if(this.canvas.closest&&this.canvas.closest('.sgL'))sgPI++;return f.apply(this,arguments)};
      window.sgRAF=0;const r=window.requestAnimationFrame;window.requestAnimationFrame=function(cb){if(/\\bsg[A-Z]/.test(String(cb)))sgRAF++;return r.call(window,cb)};return 1})()""")
    print('Neural split, first time (stand-in engine)')
    R("(" + START + ")('n4')")
    ph = wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&(j.phase==='dl'||j.phase==='init'||j.phase==='run')?j.phase:null})()")
    ok(J("!!" + SHEET + "&&!!document.querySelector('#stq .sgL')"), 'the Split sheet stays open after Split and shows the lanes')
    lanes = J("[...document.querySelectorAll('#stq .sgLn')].map(e=>e.classList.contains('mix')?'MIX':e.querySelector('.sgNm').textContent)")
    ok(lanes == ['MIX', 'Drums', 'Bass', 'Other', 'Vocals'], 'the mix on top, then one lane per kept stem in the model\'s order', lanes)
    # the download: empty lanes, the read-out in MB (driven on a job of its own, the stand-in model arrives too fast to see it)
    dl = JA(r"""(async()=>{const j=sgJob({kind:'n4',name:'dl',len:44100*30,sr:44100,stems:NEUM.n4.stems.map((n,i)=>({name:n,col:NEUM.n4.cols[i],k:i}))});const h=document.createElement('div');h.style.cssText='position:fixed;left:20px;top:20px;width:560px;background:#101116;padding:10px;z-index:99999999';h.id='sgDlT';document.body.appendChild(h);
      sgLanes(h,j);j.mix=await sgMixCols((%s)(30),j.cw);sgDrop(j);for(const v of j.views)if(v.si<0)sgPaint(j,v,0,j.cw);sgPhase(j,'dl',{p:.31,mb:51.4});const cv=[...h.querySelectorAll('canvas')].map(c=>{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let a=0;for(let i=3;i<d.length;i+=4)a+=d[i]>0;return a});
      const t=h.querySelector('.sgRo').innerText;await new Promise(r=>setTimeout(r,60));return{t,cv,edge:h.querySelector('.sgEdge').hidden,j}})()""" % SYN)
    pg.screenshot(path=os.path.join(OUT, 'sg22_download.png'), clip={'x': 0, 'y': 0, 'width': 620, 'height': 330})
    ok('Downloading the model' in dl['t'] and '51 / 166' in dl['t'] and 'MB' in dl['t'].upper(), 'during the first download the read-out says MB of MB', dl['t'])
    ok(dl['cv'][0] > 1000 and all(v == 0 for v in dl['cv'][1:]) and dl['edge'], 'during the download the mix is drawn and the stem lanes are empty, no edge yet', dl['cv'])
    R("(()=>{const h=document.getElementById('sgDlT');const j=[...SG2.jobs].find(x=>x.name==='dl');sgDrop(j,h);SG2.jobs.delete(j);h.remove();return 1})()")
    # the first chunk
    j1 = wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.done>=1&&j.done<j.n?{done:j.done}:null})()")
    pg.wait_for_timeout(220)
    st = J(r"""(()=>{const j=[...SG2.jobs][0],m=document.getElementById('stq'),ed=m.querySelector('.sgEdge'),wk=m.querySelector('.sgWork'),ov=m.querySelector('.sgOv').getBoundingClientRect(),er=ed.getBoundingClientRect(),cs=getComputedStyle(ed),ws=getComputedStyle(wk,'::after');
      const cv=m.querySelectorAll('.sgLn[data-s] canvas')[0],d=cv.getContext('2d').getImageData(0,0,cv.width,96).data,AS=sgAlpha()[0],a=c=>{if(c<0)return -1;const k=j.st[c];let e=0;for(let r=0;r<96;r++){const v=j.cols[r*j.cw+c],x=k===2?AS[v]:k===1?AS[v]>>1:0;e=Math.max(e,Math.abs(d[(r*cv.width+c)*4+3]-x))}return{k,e}};
      const f1=j.st.indexOf(1),f2=j.st.indexOf(2),last2=j.st.lastIndexOf(2),e0=j.st.indexOf(0);
      return{done:j.done,n:j.n,fin:j.fin,total:j.total,edgeX:(er.left-ov.left)/ov.width,edgeHid:ed.hidden,tr:cs.transitionDuration,trp:cs.transitionProperty,work:!wk.hidden,wl:(wk.getBoundingClientRect().left-ov.left)/ov.width,anim:ws.animationName,
       aFin:a(Math.max(0,last2-1)),aDraft:a(f1>=0?f1+1:-1),aEmpty:a(e0>=0?Math.min(cv.width-1,e0+2):-1),ro:m.querySelector('.sgRo').innerText,units:[...m.querySelectorAll('.sgRo .lku')].map(e=>e.textContent),ucol:getComputedStyle(m.querySelector('.sgRo .lku')).color,pi:sgPI}})()""")
    print('    ', {k: st[k] for k in ('done', 'n', 'edgeX', 'tr', 'anim', 'aFin', 'aDraft', 'aEmpty', 'ro')})
    ok(abs(st['edgeX'] - st['fin'] / st['total']) < 0.01 and not st['edgeHid'], 'the amber edge sits at the last final sample', (round(st['edgeX'], 4), round(st['fin'] / st['total'], 4)))
    ok(st['tr'] == '0.12s' and 'left' in st['trp'], 'the edge moves by a 120 ms transition', (st['tr'], st['trp']))
    ok(st['work'] and abs(st['wl'] - st['fin'] / st['total']) < 0.01 and st['anim'] == 'sgScan', 'the chunk at work has the soft scan (F1), starting at the edge', (st['wl'], st['anim']))
    ok(st['aFin']['k'] == 2 and st['aFin']['e'] == 0 and st['aDraft']['k'] == 1 and st['aDraft']['e'] == 0 and st['aEmpty']['k'] == 0 and st['aEmpty']['e'] == 0, 'final columns at full strength, the draft stretch at half strength (P1), the rest empty (every pixel as its level says)', (st['aFin'], st['aDraft'], st['aEmpty']))
    ok(('%d / %d' % (st['done'], st['n'])) in st['ro'] and 'left' in st['ro'].lower() and set(u.lower() for u in st['units']) >= {'chunks', 's', 'left'}, 'the read-out counts chunks, time and time left, units in their own spans', (st['ro'], st['units']))
    ok(st['ucol'] in ('rgb(255, 181, 71)',), 'units in amber (--unit)', st['ucol'])
    pg.screenshot(path=os.path.join(OUT, 'sg22_dark_running.png'))
    pi1 = st['pi']
    j2 = wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.done>=%d?{done:j.done,pi:sgPI}:null})()" % (st['done'] + 1))
    pi2 = j2['pi']
    ok(pi2 - pi1 == 4 * (j2['done'] - st['done']), 'one putImageData per lane per chunk (4 lanes)', (pi1, pi2, j2))
    # idle between chunks: the read-out only, once a second
    R("(()=>{const j=[...SG2.jobs][0];window.sgUC=[0,0];window.sgD0=j.done;for(const f of[...j.ui]){j.ui.delete(f);const g=x=>{sgUC[x?1:0]++;return f(x)};j.ui.add(g)}return 1})()")
    pg.wait_for_timeout(2100); uc = J('[sgUC,[...SG2.jobs][0].done-sgD0,[...SG2.jobs][0].ui.size]')
    ok(uc[0][1] <= 3 * uc[2] and uc[0][0] <= 2 * (uc[1] + 1) * uc[2], 'nothing per frame: over 2 s, an update per chunk and the read-out ticking once a second (a frame loop would be about 120)', uc)
    done = wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.phase==='done'})()", 60000)
    pg.wait_for_timeout(100)
    en = J(r"""(()=>{const j=[...SG2.jobs][0],m=document.getElementById('stq');let mx=0,big=0;j.bufs.forEach((b,s)=>{const L=b.getChannelData(0),R=b.getChannelData(1),o=new Uint8Array(96*j.cw);sgColsOf(q=>(L[q]+R[q])*.5,L.length,44100,j.cw,0,j.cw,o,0,j.cw);for(let i=0;i<o.length;i++){const d=Math.abs(o[i]-j.cols[s*96*j.cw+i]);if(d>mx)mx=d;if(d>2)big++}});
      const cv=m.querySelectorAll('.sgLn[data-s] canvas')[1],c=Math.floor(j.cw/2),L=INS.cmap('viridis');let r=0;for(let k=0;k<96;k++)if(j.cols[1*96*j.cw+k*j.cw+c]>j.cols[1*96*j.cw+r*j.cw+c])r=k;const px=cv.getContext('2d').getImageData(c,r,1,1).data,v=j.cols[1*96*j.cw+r*j.cw+c];
      return{mx,big,st:j.st.every(v=>v===2),px:[...px].slice(0,4),lut:[L[v*3],L[v*3+1],L[v*3+2],sgAlpha()[0][v]],lv:[...m.querySelectorAll('.sgLv')].map(e=>e.hidden?null:e.textContent),ck:[...m.querySelectorAll('.sgCk')].map(e=>e.checked),add:m.querySelector('#sgAdd').textContent,addDis:m.querySelector('#sgAdd').disabled,
       stop:m.querySelector('#sgStop').hidden,keep:m.querySelector('#sgKeep').hidden,edge:m.querySelector('.sgEdge').hidden,work:m.querySelector('.sgWork').hidden,ro:m.querySelector('.sgRo').innerText,raf:sgRAF,rate:UI.sgRate&&UI.sgRate.n4}})()""")
    print('    ', {k: en[k] for k in ('mx', 'big', 'lv', 'ck', 'add', 'ro', 'rate')})
    ok(en['st'] and en['mx'] <= 2 and en['big'] == 0, 'at the end every lane is the spectrogram of its final stem', (en['mx'], en['big']))
    ok(en['px'] == en['lut'], 'the lanes are drawn in viridis from INS.cmap (lane E)', (en['px'], en['lut']))
    ok(all(en['lv']) and en['lv'][3] == 'silent' and en['ck'] == [True, True, True, False], 'each lane shows its level and a tick, the silent stem unticked', (en['lv'], en['ck']))
    ok(en['add'] == 'Add 3 tracks' and not en['addDis'] and en['stop'] and en['keep'] and en['edge'] and en['work'], 'Add 3 tracks, no Stop or Keep working, no edge or scan once done', en['add'])
    ok(en['raf'] == 0, 'no requestAnimationFrame from the splitter during the whole split', en['raf'])
    ok(en['rate'] and en['rate'] > 0, 'this computer\'s speed for the model is kept (UI.sgRate) for the next estimate', en['rate'])
    pg.screenshot(path=os.path.join(OUT, 'sg22_dark_done.png'))
    n0 = J('S.tracks.length'); u0 = J('UNDO.length')
    pg.click('#sgAdd'); R('sgT.pr'); pg.wait_for_timeout(300)
    ad = J("(()=>({n:S.tracks.length,names:S.tracks.slice(-3).map(t=>t.name),cols:S.tracks.slice(-3).map(t=>t.color),mute:!!sgT.c.mute,u:UNDO.length,sheet:!!document.getElementById('stq'),jobs:SG2.jobs.size}))()")
    ok(ad['n'] == n0 + 3 and ad['names'] == ['Loop · Drums', 'Loop · Bass', 'Loop · Other'] and ad['mute'] and ad['u'] == u0 + 1 and not ad['sheet'] and ad['jobs'] == 0, 'Add 3 tracks: three stem tracks below the clip in the stems\' colours, the clip muted, one undo step, the sheet closed', ad)
    R('undo()'); pg.wait_for_timeout(200)
    ok(J('S.tracks.length') == n0 and not J('S.tracks.find(t=>t.id===sgT.t.id).clips[0].mute'), 'Undo brings the song back as it was')
    R("(()=>{sgT.t=S.tracks.find(t=>t.name==='Loop');sgT.c=sgT.t.clips[0];return 1})()")

    print('Stop and Keep working')
    n0 = J('S.tracks.length'); u0 = J('UNDO.length')
    R("(" + START + ")('n4')"); wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.done>=1})()")
    pg.click('#sgStop'); R('sgT.pr'); pg.wait_for_timeout(200)
    ok(J('S.tracks.length') == n0 and J('UNDO.length') == u0 and not J("!!document.getElementById('stq')") and J('SG2.jobs.size') == 0, 'Stop: the sheet closes and nothing is changed')
    R("(" + START + ")('n4')"); wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.done>=1})()")
    pg.click('#sgKeep'); pg.wait_for_timeout(150)
    kw = J("(()=>({sheet:!!document.getElementById('stq'),bg:[...SG2.jobs][0].bg}))()")
    ok(not kw['sheet'] and kw['bg'], 'Keep working closes the sheet and the split goes on', kw)
    R('sgT.pr'); pg.wait_for_timeout(300)
    ok(J('S.tracks.length') == n0 + 3, 'a split sent on with Keep working adds the ticked stems when it ends', J('S.tracks.length') - n0)
    R('undo()'); R("(()=>{sgT.t=S.tracks.find(t=>t.name==='Loop');sgT.c=sgT.t.clips[0];return 1})()")

    print('Several clips, ids')
    R("(()=>{SG2.batch={n:3,k:1};IMPCH={all:true};return 1})()"); R("(" + START + ")('n4')"); wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.done>=1})()")
    ro = J("document.querySelector('#stq .sgRo').innerText")
    ok('clip 2 of 3' in ro, 'several clips: the read-out says clip 2 of 3', ro)
    un = J("[...document.querySelectorAll('#stq button,#stq input,#stq select')].filter(e=>!e.dataset.al).map(e=>e.outerHTML.slice(0,60))")
    ok(not un, 'every control of the sheet has an id (data-al)', un)
    tt = J("[...document.querySelectorAll('#stq button')].filter(e=>!e.title&&!e.dataset.tip).map(e=>e.id)")
    ok(not tt, 'every button has a tooltip', tt)
    pg.click('#sgStop'); R('sgT.pr'); R("(()=>{SG2.batch=null;IMPCH=null;return 1})()")

    print('Quick split in the sheet')
    R("""(()=>{window.sgHT=[];const w=sgWorker(),f=w.onmessage;w.onmessage=e=>{const t=performance.now();f(e);sgHT.push(performance.now()-t)};return 1})()""")
    n0 = J('S.tracks.length'); R("(" + START + ")('quick')")
    wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.phase==='done'})()", 60000)
    qk = J("(()=>{const j=[...SG2.jobs][0];return{n:j.n,done:j.done,ns:j.ns,lanes:document.querySelectorAll('#stq .sgLn[data-s]').length,draft:j.st.some(v=>v===1),ht:Math.round(Math.max(...sgHT)),add:document.getElementById('sgAdd').textContent}})()")
    ok(qk['ns'] == 4 and qk['lanes'] == 4 and qk['done'] == qk['n'] == 6, 'the quick split fills its 4 lanes block by block (6 blocks)', qk)
    pg.click('#sgAdd'); R('sgT.pr'); pg.wait_for_timeout(200)
    ok(J('S.tracks.length') == n0 + int(qk['add'].split()[1]), 'the quick split adds its ticked stems', qk['add'])
    hts = [qk['ht']]
    for k in range(2):
        if hts[-1] < 50: break
        R("(()=>{sgHT.length=0;return 1})()"); R("(" + START + ")('quick')"); wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.phase==='done'})()", 60000)
        hts.append(J('Math.round(Math.max(...sgHT))')); pg.click('#sgDiscard'); R('sgT.pr')
    ok(hts[-1] < 50, 'no main-thread pause over 50 ms from a block of the quick split (columns copied and painted; repeated once or twice when a garbage collection lands in one)', hts)
    ok(not errs, 'no console errors', errs[:3])
    b.close()

    print('Light mode and Reduce motion')
    for tag, red, lite in (('lite', False, True), ('reduced', True, False)):
        b, pg, errs, R, J, JA = page(p, SRC, reduced=red, delay=60)
        R(CLIP + '(30)')
        if lite: R('UI.lite=true;applyLite();0')
        R("(" + START + ")('n4')"); wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.done>=1&&j.done<j.n})()")
        pg.wait_for_timeout(60)
        lm = J(r"""(()=>{const j=[...SG2.jobs][0],m=document.getElementById('stq'),ed=m.querySelector('.sgEdge'),wk=m.querySelector('.sgWork'),cv=m.querySelectorAll('.sgLn[data-s] canvas')[0],d=cv.getContext('2d').getImageData(0,0,cv.width,96).data,f1=j.st.indexOf(1);let a=0;if(f1>=0)for(let r=0;r<96;r++)a+=d[(r*cv.width+f1+1)*4+3];
          return{still:m.querySelector('.sgL').classList.contains('still'),tr:getComputedStyle(ed).transitionDuration,anim:getComputedStyle(wk,'::after').animationName,disp:getComputedStyle(wk,'::after').display,bg:getComputedStyle(wk).backgroundImage.slice(0,25),draftA:f1>=0?Math.round(a/96):-1,anims:document.getAnimations().filter(x=>x.animationName==='sgScan').length}})()""")
        ok(lm['still'] and lm['tr'] in ('0s', '1e-05s') and (lm['disp'] == 'none' or lm['anim'] == 'none') and 'repeating-linear' in lm['bg'] and lm['anims'] == 0, tag + ': no scan (a still hatch) and no transition on the edge; the lanes still fill', lm)
        if lite: ok(lm['draftA'] == 0, 'Light mode: no draft stretch drawn', lm['draftA'])
        pg.screenshot(path=os.path.join(OUT, 'sg22_%s.png' % tag))
        pg.click('#sgStop'); R('sgT.pr')
        ok(not errs, tag + ': no console errors', errs[:3])
        b.close()

    print('The neural split cannot run: the quick split in the same sheet')
    b, pg, errs, R, J, JA = page(p, SRC, ort_ok=False)
    R(CLIP + '(12)'); R("(" + START + ")('n4')")
    ask = wait(pg, J, "(()=>{const b=[...document.querySelectorAll('button')].find(e=>e.textContent==='Quick split'&&e.offsetParent);return b?1:0})()", 30000)
    ok(ask and J("!!document.querySelector('#stq .sgL')"), 'a neural split that cannot run asks, the sheet stays open')
    R("[...document.querySelectorAll('button')].find(e=>e.textContent==='Quick split'&&e.offsetParent).click()")
    wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.kind==='quick'&&j.phase==='done'})()", 30000)
    fb = J("(()=>({lanes:[...document.querySelectorAll('#stq .sgLn[data-s] .sgNm')].map(e=>e.textContent),en:document.querySelector('#stq .sgEn').textContent}))()")
    ok(fb['lanes'] == ['Drums', 'Bass', 'Vocals', 'Other'] and 'Quick' in fb['en'], 'the same sheet shows the quick split\'s lanes', fb)
    pg.click('#sgDiscard'); R('sgT.pr')
    ok(not J("!!document.getElementById('stq')"), 'Discard closes the sheet')
    errs2 = [e for e in errs if 'ort.min.js' not in e and 'importScripts' not in e and 'NetworkError' not in e]
    ok(not errs2, 'no console errors', errs2[:3])
    b.close()
print('%d/%d' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
