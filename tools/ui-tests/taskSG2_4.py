"""Task SG2-4 (lane R): Audio to MIDI's "Split into stems first" shows the lanes instead of its bar; done, each lane is in its listen row.
  python3 tools/ui-tests/taskSG2_4.py [index.html] [out dir]
Checks (the quick split, and the neural split on a stand-in engine): after Split the pop-up shows the lanes (mix and one lane per
stem) where the 4 px bar was (the bar hidden), the lanes fill chunk by chunk and survive the pop-up redrawing its body; done, every
listen row (▶, Convert, mode) holds its stem's spectrogram, painted to the end, in the stem's order; ▶ and Convert still work;
Cancel changes nothing; no console errors."""
import sys, os, json
from playwright.sync_api import sync_playwright
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
INIT = "if(!sessionStorage.getItem('sg24')){sessionStorage.setItem('sg24','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1,wsShow:false,lite:false,liteMan:false}))}"
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
A2M = r"""(()=>{const b=(%s)(14);const id=addBuf(b);const t=mkTrack('inst','keys',null);t.name='Keys';S.tracks.push(t);const c=mkClip({start:0,len:b.duration*S.bpm/60,name:'Loop',buf:id,dur:b.duration,gain:0,fi:0,fo:0});t.clips.push(c);pushUndo();window.sgA={n:S.tracks.length,u:UNDO.length};a2dCommit([{c,t,ti:S.tracks.indexOf(t)}]);return 1})()""" % SYN
def a2m_run(pg, R, J, eng, tag):
    R(A2M); pg.wait_for_timeout(400)
    pg.click('#a2d [data-card=stems]'); pg.click('#a2dGo'); pg.wait_for_timeout(200)
    R("(()=>{const r=document.querySelector('#a2d [name=a2deng][value=%s]');r.checked=true;r.dispatchEvent(new Event('change',{bubbles:true}));return 1})()" % eng)
    pg.click('#a2dGo')
    ln = wait(pg, J, "(()=>{const m=document.getElementById('a2d'),l=m&&m.querySelector('.sgA2h .sgL');return l?{lanes:[...l.querySelectorAll('.sgLn')].map(e=>e.classList.contains('mix')?'MIX':e.querySelector('.sgNm').textContent),bar:m.querySelector('.a2dbar').hidden}:null})()")
    return ln
with sync_playwright() as p:
    b, pg, errs, R, J, JA = page(p, SRC, delay=60)
    ver = R('VERSION'); ok(tuple(map(int, ver.split('.'))) >= (0, 301), 'version 0.301 or later', ver)
    R("(()=>{UI.lite=false;applyLite();return 1})()")
    for eng, names in (('n4', ['Drums', 'Bass', 'Other', 'Vocals']), ('quick', ['Drums', 'Bass', 'Vocals', 'Other'])):
        print('Audio to MIDI,', eng)
        ln = a2m_run(pg, R, J, eng, eng)
        ok(ln and ln['lanes'] == ['MIX'] + names and ln['bar'], eng + ': the lanes (mix and one per stem) replace the bar while it splits', ln)
        if eng == 'n4':
            wait(pg, J, "(()=>{const j=[...SG2.jobs].find(x=>x.a2m);return j&&j.done>=1})()")
            R("(()=>{const e=document.getElementById('a2dTidy');e.click();e.click();return 1})()")
            pg.screenshot(path=os.path.join(OUT, 'sg24_running.png'))
            # the pop-up redraws its body: the lanes come back with what is drawn so far
            R("(()=>{const b=document.getElementById('a2dBody');b.querySelectorAll('.sgA2h').forEach(x=>x.remove());b.querySelector('.a2dbar').hidden=false;b.innerHTML=b.innerHTML;return 1})()"); pg.wait_for_timeout(100)
            rb = J("(()=>{const m=document.getElementById('a2d'),j=[...SG2.jobs].find(x=>x.a2m),cv=m.querySelector('.sgA2h .sgLn[data-s] canvas');if(!cv)return null;const d=cv.getContext('2d').getImageData(0,0,cv.width,96).data;let a=0;for(let c=0;c<cv.width;c++){let x=0;for(let r=0;r<96;r++)x=Math.max(x,d[(r*cv.width+c)*4+3]);if(x>0)a++}return{a,st:j.st.reduce((s,v)=>s+(v>0),0),n:m.querySelectorAll('.sgA2h .sgL').length}})()")
            ok(rb and rb['n'] == 1 and abs(rb['a'] - rb['st']) <= 1, 'after the pop-up redraws its body the lanes are back, drawn so far', rb)
        rows = wait(pg, J, "(()=>{const r=[...document.querySelectorAll('#a2d .a2sr')];const j=SG2.a2mLast,AS=sgAlpha()[0];return r.length&&r.every(x=>x.querySelector('.sgA2l'))?r.map((x,i)=>{const cv=x.querySelector('.sgA2l canvas'),d=cv.getContext('2d').getImageData(0,0,cv.width,96).data;let a=0;for(let c=0;c<cv.width;c++){let e=0;for(let q=0;q<96;q++)e=Math.max(e,Math.abs(d[(q*cv.width+c)*4+3]-AS[j.cols[(i*96+q)*j.cw+c]]));if(e===0&&j.st[c]===2)a++}return{n:x.querySelector('b').textContent,full:a/cv.width,play:!!x.querySelector('[data-play]'),conv:!!x.querySelector('[data-pick]'),mode:!!x.querySelector('[data-smode]')}}):null})()", 60000)
        ok(rows and [r['n'] for r in rows] == names and all(r['full'] == 1 for r in rows), eng + ': done, every listen row holds its stem\'s spectrogram, painted to the end, in order', rows and [(r['n'], round(r['full'], 3)) for r in rows])
        ok(rows and all(r['play'] and r['conv'] and r['mode'] for r in rows), eng + ': the rows keep ▶, Convert and the mode')
        ok(not J("!!document.querySelector('#a2d .sgA2h')"), eng + ': the lanes above are gone once the rows show')
        if eng == 'n4': pg.screenshot(path=os.path.join(OUT, 'sg24_rows.png'))
        R("(()=>{const b=document.querySelector('#a2d .a2sr [data-pick]');b.click();return 1})()"); pg.wait_for_timeout(100)
        ok(J("document.querySelectorAll('#a2d .a2sr .sgA2l').length") == len(names), eng + ': ticking Convert redraws the rows with their spectrograms')
        pg.click('#a2dNo'); pg.wait_for_timeout(300)
        ok(J("!document.getElementById('a2d')&&S.tracks.length===sgA.n&&UNDO.length===sgA.u-1"), eng + ': Cancel changes nothing', J("[S.tracks.length,sgA.n,UNDO.length,sgA.u]"))
        R("(()=>{undo();return 1})()")
        ok(J("[...SG2.jobs].filter(x=>x.a2m).length") == 0, eng + ': no job left behind')
    ok(not errs, 'no console errors', errs[:3])
    b.close()
print('%d/%d' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
