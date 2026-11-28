"""Task SG2-3 (lane R): S1, the stem split's card with a strip per stem, and SG_HOOKS.card / pill (docs/stem-split-progress.md).
  python3 tools/ui-tests/taskSG2_3.py [index.html] [out dir]
Checks (neural worker on a stand-in engine): Keep working sends the split to a card in the job pill's place (no pill for it at the
same time) with the orbit and the real progress, the clip name, one strip per stem filled chunk by chunk (one putImageData per strip
per chunk), the time left, Open and Stop; Open brings the sheet back with every lane drawn so far; the end says how many stems were
added below which track and offers Undo, which takes them out; Stop from the card changes nothing; SG_HOOKS.card(job) gives the
strips for lane F, SG_HOOKS.pill('stem') a strip for lane G's pill while a split runs on (null otherwise); every control has an id
and a tooltip; solid, no backdrop-filter. No console errors."""
import sys, os, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('sg23')){sessionStorage.setItem('sg23','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1,wsShow:false,lite:false,liteMan:false}))}"
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
    cx.route('https://app.test/**', alsong(lambda r: r.fulfill(body=src, content_type='text/html') if r.request.url.split('?')[0].endswith('/') else r.fulfill(status=404, body='')))
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
    ver = R('VERSION'); ok(tuple(map(int, ver.split('.'))) >= (0, 300), 'version 0.300 or later', ver)
    css = SRC[SRC.index('/* task SG2-3 (lane R)'):SRC.index('.a2dbar{height:6px;')]
    ok('backdrop-filter:' not in css, 'the card is solid: no backdrop-filter')
    R(CLIP + '(30)')
    R("(()=>{UI.lite=false;applyLite();const B=document.body,k=()=>B.classList.remove('lite','fxstill','lkm1');k();new MutationObserver(k).observe(B,{attributes:true,attributeFilter:['class']});return 1})()")
    R("""(()=>{window.sgPI=0;const f=CanvasRenderingContext2D.prototype.putImageData;CanvasRenderingContext2D.prototype.putImageData=function(){if(this.canvas.closest&&this.canvas.closest('#sgCard'))sgPI++;return f.apply(this,arguments)};return 1})()""")
    n0 = J('S.tracks.length'); u0 = J('UNDO.length')
    R("(" + START + ")('n4')"); wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.done>=1})()")
    ok(J("SG_HOOKS.pill('stem')") is None, 'no pill strip while the split shows in its sheet')
    pg.click('#sgKeep'); pg.wait_for_timeout(250)
    cd = J("""(()=>{const c=document.getElementById('sgCard'),j=[...SG2.jobs][0];return c&&{strips:c.querySelectorAll('.sgSs canvas').length,orb:!!c.querySelector('.mdorb'),t:c.querySelector('b').textContent,ro:c.querySelector('.sgCr').innerText,btn:[...c.querySelectorAll('button')].filter(e=>!e.hidden).map(e=>e.textContent),pill:!!(document.getElementById('mdJob')&&!document.getElementById('mdJob').hidden&&document.getElementById('mdJob').dataset.k==='stem'),sheet:!!document.getElementById('stq'),done:j.done,pi:sgPI,
      noid:[...c.querySelectorAll('button')].filter(e=>!e.dataset.al).length,notip:[...c.querySelectorAll('button')].filter(e=>!e.title&&!e.dataset.tip).length}})()""")
    print('    ', cd)
    ok(cd and not cd['sheet'] and cd['strips'] == 4 and cd['orb'] and cd['t'] == 'Splitting “Loop”', 'Keep working: the sheet closes and the card shows the orbit, the clip name and a strip per stem (4)', cd)
    ok(cd and not cd['pill'], 'no job pill for the split while the card shows it')
    ok(cd and 'left' in cd['ro'].lower() and 'chunks' in cd['ro'].lower() and cd['btn'] == ['✕', 'Open', 'Stop'], 'the card reads chunks and time left, with Open and Stop', (cd['ro'], cd['btn']))
    ok(cd and cd['noid'] == 0 and cd['notip'] == 0, 'every control of the card has an id (data-al) and a tooltip')
    pl = J("(()=>{const e=SG_HOOKS.pill('stem');return e&&{cv:e.querySelectorAll('canvas').length,w:e.className}})()")
    ok(pl and pl['cv'] == 4, 'SG_HOOKS.pill(\'stem\') gives lane G a strip of the running split', pl)
    hk = J("(()=>{const j=[...SG2.jobs][0],e=SG_HOOKS.card(j),cv=e.querySelectorAll('canvas'),d=cv[0].getContext('2d').getImageData(0,0,cv[0].width,96).data;let a=0;for(let i=3;i<d.length;i+=4)a+=d[i]>0;sgDrop(j,e);return{n:cv.length,painted:a>0}})()")
    ok(hk['n'] == 4 and hk['painted'], 'SG_HOOKS.card(job) gives lane F the strips, drawn up to where the split is', hk)
    p1 = J("(()=>({done:[...SG2.jobs][0].done,pi:sgPI}))()")
    p2 = wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.done>=%d?{done:j.done,pi:sgPI}:null})()" % (p1['done'] + 1))
    ok(p2['pi'] - p1['pi'] == 4 * (p2['done'] - p1['done']), 'one putImageData per strip per chunk', (p1, p2))
    pg.screenshot(path=os.path.join(OUT, 'sg23_card.png'))
    pg.click('#sgCard [data-sg=open]'); pg.wait_for_timeout(200)
    op = J("""(()=>{const m=document.getElementById('stq'),j=[...SG2.jobs][0],cv=m&&m.querySelectorAll('.sgLn[data-s] canvas')[0];if(!cv)return null;const d=cv.getContext('2d').getImageData(0,0,cv.width,96).data;let a=0;for(let c=0;c<cv.width;c++){let x=0;for(let r=0;r<96;r++)x=Math.max(x,d[(r*cv.width+c)*4+3]);if(x>0)a++}return{card:!!document.getElementById('sgCard'),cols:a,st:j.st.reduce((s,v)=>s+(v>0),0),bg:j.bg}})()""")
    ok(op and not op['card'] and not op['bg'] and abs(op['cols'] - op['st']) <= 1, 'Open brings the sheet back with every lane drawn so far, the card goes', op)
    pg.click('#sgKeep'); pg.wait_for_timeout(100)
    wait(pg, J, "(()=>{const c=document.getElementById('sgCard');return c&&!c.querySelector('[data-sg=undo]').hidden})()", 60000)
    en = J("(()=>{const c=document.getElementById('sgCard');return{t:c.querySelector('b').textContent,ro:c.querySelector('.sgCr').innerText,btn:[...c.querySelectorAll('button')].filter(e=>!e.hidden).map(e=>e.textContent),n:S.tracks.length}})()")
    ok(en['t'] == '3 stems added below “Loop”' and en['btn'] == ['✕', 'Undo'] and en['n'] == n0 + 3, 'at the end the card says what was added and offers Undo', en)
    pg.screenshot(path=os.path.join(OUT, 'sg23_card_done.png'))
    pg.click('#sgCard [data-sg=undo]'); pg.wait_for_timeout(200)
    ok(J('S.tracks.length') == n0 and J('UNDO.length') == u0 and not J("!!document.getElementById('sgCard')"), 'Undo on the card takes the stem tracks out again and closes it')
    R("(()=>{sgT.t=S.tracks.find(t=>t.name==='Loop');sgT.c=sgT.t.clips[0];return 1})()"); R('sgT.pr')
    R("(" + START + ")('n4')"); wait(pg, J, "(()=>{const j=[...SG2.jobs][0];return j&&j.done>=1})()")
    pg.click('#sgKeep'); pg.wait_for_timeout(100); pg.click('#sgCard [data-sg=stop]'); R('sgT.pr'); pg.wait_for_timeout(200)
    ok(J('S.tracks.length') == n0 and not J("!!document.getElementById('sgCard')") and J('SG2.jobs.size') == 0 and J("SG_HOOKS.pill('stem')") is None, 'Stop on the card: the card goes, nothing is changed, no pill strip')
    ok(not errs, 'no console errors', errs[:3])
    b.close()
print('%d/%d' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
