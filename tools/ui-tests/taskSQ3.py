"""Task SQ3 (sound quality, lane N): resample once (Q11). With Hi-Fi on for the song, a buffer made at another rate is converted once
to the rate it plays at with a windowed-sinc resampler (worker; cached per rate); Hi-Fi off is today's linear path, bit for bit.
Checks, with the research doc's analyser (tools/engine-lab/ae1/anal.py alias_report, harmonics=1) at its test frequencies:
- a 44.1 kHz sine (amplitude 0.5) played in a 48 kHz render: images and aliases at 1, 5, 10 and 15 kHz, Hi-Fi off (today: -62.4,
  -33.9, -20.4, -11.1 dB in the research doc) against Hi-Fi on (under -100 dB at every frequency);
- 48 kHz to 96 kHz (an export at another rate) and 48 kHz to 44.1 kHz (bounces, the stem splitter's input): images under -100 dB;
- the level of the tone kept within 0.01 dB; DC through (a constant stays the constant); the length is the same duration;
- Hi-Fi off: an offline render with the hook is bit-identical to one with the hook turned off; Fractals' renderMix at 44.1 and 96 kHz
  bit-identical with and without the hook (the song is Classic), and nothing converted;
- the worker and the main thread give the same bits; a 4-minute stereo 44.1 kHz buffer converted in the worker (time reported);
- Hi-Fi on: renderMix at 96 kHz waits for the copies and uses them (counted), two renders give the same bits;
- live: turning Hi-Fi on makes copies of the loaded buffers for the engine's rate; a live source then gets the copy;
- no timers or jobs left while idle; the song's Hi-Fi row in Settings says it; dark and Light; no console errors.
  python3 tools/ui-tests/taskSQ3.py [repo dir] [out dir]"""

import sys,os,mimetypes,json,base64
import numpy as np
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else '.');OUT=sys.argv[2] if len(sys.argv)>2 else '.';os.makedirs(OUT,exist_ok=True)
sys.path.insert(0,os.path.join(ROOT,'tools','engine-lab','ae1'))
from anal import alias_report
N=[0,0];FAIL=[]
def ck(name,ok,info=''):
    N[0]+=1
    if ok:N[1]+=1
    else:FAIL.append(name);print('  FAIL',name,str(info)[:600])
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html';f=os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type='text/html' if f.endswith('.html') else (mimetypes.guess_type(f)[0] or 'application/octet-stream'))
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
J=lambda pg,c:json.loads(R(pg,"JSON.stringify("+c+")"))
AJ=lambda pg,c:json.loads(R(pg,"(async()=>JSON.stringify(await ("+c+")))()"))
def ctx(b,lite):
    c=b.new_context(viewport={'width':1600,'height':1000});pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and 'icons.json' not in m.text and errs.append('console '+m.text[:200]))
    pg.route('https://app.test/**',serve)
    u=dict(order=['arr','fx','tr','map'],splash=False,lat3=1,lite=lite,liteMan=lite)
    pg.add_init_script("if(!sessionStorage.getItem('q1')){sessionStorage.setItem('q1','1');localStorage.setItem('audiolab-ui',JSON.stringify(%s))}"%json.dumps(u))
    pg.goto('https://app.test/index.html')
    pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(2500)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
    return c,pg,errs
# a sine (or a constant) at rate a, played through an AudioBufferSourceNode in an offline render at rate b; Hi-Fi on: the copy is made
# by the worker first (as an export does); returns the output's middle second (base64 float32) and a checksum of the whole output
TONE0="""window.__tone=async([f,a,b,q,off,dc])=>{const n=a*2,src=new AudioBuffer({numberOfChannels:1,length:n,sampleRate:a}),d=src.getChannelData(0);
 for(let i=0;i<n;i++)d[i]=dc?0.5:0.5*Math.sin(2*Math.PI*f*i/a);const keep=S.sq;S.sq=q;SQRS.off=!!off;
 try{if(q==='clean'&&!off)await SQ_HOOKS.resample(src,b);const c=new OfflineAudioContext(1,b*2,b),s=c.createBufferSource();s.buffer=src;const used=s.buffer.sampleRate;
  s.connect(c.destination);s.start();const r=await c.startRendering(),o=r.getChannelData(0);let h=0;for(let i=0;i<o.length;i++){const u=new Uint32Array(new Float32Array([o[i]]).buffer)[0];h=(Math.imul(h,31)+u)|0}
  const m=o.slice(b/2,b/2+b),u8=new Uint8Array(m.buffer);let s2='';for(let i=0;i<u8.length;i+=32768)s2+=String.fromCharCode.apply(null,u8.subarray(i,i+32768));
  const cp=SQRS.cache.get(src),cl=cp&&cp.get(b);return{h,used,x:btoa(s2),len:cl&&cl.length?cl.length:0}}finally{S.sq=keep;SQRS.off=false}};1"""
TONE="a=>window.__tone(a)"
HASHB="b=>{let h=0;for(let c=0;c<b.numberOfChannels;c++){const o=b.getChannelData(c);for(let i=0;i<o.length;i++){const u=new Uint32Array(new Float32Array([o[i]]).buffer)[0];h=(Math.imul(h,31)+u)|0}}return h}"
def dec(x): return np.frombuffer(base64.b64decode(x),np.float32).astype(np.float64)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        c,pg,errs=ctx(b,lite)
        R(pg,TONE0)
        ck(f'{L}: version',float(R(pg,"VERSION"))>=0.294)
        ck(f'{L}: the hook is on the buffer setter',J(pg,"!!SQRS.desc&&Object.getOwnPropertyDescriptor(AudioBufferSourceNode.prototype,'buffer').set!==SQRS.desc.set"))
        ck(f'{L}: the open song is Hi-Fi off',R(pg,"sqProj()")=='classic')
        if not lite:
            print('  44.1 kHz sine (0.5) in a 48 kHz render, images and aliases (research doc: -62.4 / -33.9 / -20.4 / -11.1 dB today):')
            for f in (1000,5000,10000,15000):
                k=pg.evaluate(TONE,[f,44100,48000,'classic',False,False]);k0=pg.evaluate(TONE,[f,44100,48000,'classic',True,False]);cl=pg.evaluate(TONE,[f,44100,48000,'clean',False,False])
                rk=alias_report(dec(k['x']),48000,f,harmonics=1);rc=alias_report(dec(cl['x']),48000,f,harmonics=1)
                lk=20*np.log10(np.sqrt(2*np.mean(dec(k['x'])**2))/.5);lc=20*np.log10(np.sqrt(2*np.mean(dec(cl['x'])**2))/.5)
                print(f'   {f} Hz: Hi-Fi off {rk["alias_db"]:7.1f} dB, Hi-Fi on {rc["alias_db"]:7.1f} dB (worst {rc["worst_db"]:.1f} dB at {rc["worst_hz"]:.0f} Hz); level {lk:+.4f} / {lc:+.4f} dB')
                ck(f'Hi-Fi off at {f} Hz is today\'s linear path, bit for bit, and plays the 44.1 kHz buffer',k['h']==k0['h'] and k['used']==44100,(k['h'],k0['h'],k['used']))
                ck(f'Hi-Fi off at {f} Hz reads like the research doc (linear)',abs(rk['alias_db']-{1000:-62.4,5000:-33.9,10000:-20.4,15000:-11.1}[f])<1.5,rk['alias_db'])
                ck(f'Hi-Fi on at {f} Hz: images under -100 dB and the copy is played',rc['alias_db']<-100 and cl['used']==48000,(rc,cl['used']))
                ck(f'Hi-Fi on at {f} Hz: the level stays (within 0.01 dB of Hi-Fi off\'s ideal)',abs(lc)<0.01,lc)
            for (a,bb,f) in ((48000,96000,10000),(48000,96000,20000),(48000,44100,10000),(44100,96000,15000)):
                cl=pg.evaluate(TONE,[f,a,bb,'clean',False,False]);k=pg.evaluate(TONE,[f,a,bb,'classic',False,False])
                rc=alias_report(dec(cl['x']),bb,f,harmonics=1);rk=alias_report(dec(k['x']),bb,f,harmonics=1)
                print(f'   {a} -> {bb} Hz, {f} Hz tone: Hi-Fi off {rk["alias_db"]:.1f} dB, on {rc["alias_db"]:.1f} dB')
                ck(f'{a} to {bb} Hz at {f} Hz: images under -100 dB, the copy lasts as long',rc['alias_db']<-100 and abs(cl['len']/bb-2.0)<1.5/bb,(rc['alias_db'],cl['len']))
            d=pg.evaluate(TONE,[0,44100,48000,'clean',False,True]);x=dec(d['x'])
            ck('a constant stays the constant (DC passes exactly enough)',float(np.max(np.abs(x-.5)))<2e-6,float(np.max(np.abs(x-.5))))
            w=AJ(pg,"""(async()=>{const a=44100,n=a*240,mk=()=>{const b=new AudioBuffer({numberOfChannels:2,length:n,sampleRate:a});for(let c=0;c<2;c++){const d=b.getChannelData(c);let s=7+c;for(let i=0;i<n;i++){s=(Math.imul(s,1103515245)+12345)|0;d[i]=(s>>8)/16777216*.5+.3*Math.sin(i*.0123*(c+1))}}return b};
              const b1=mk(),b2=mk(),t0=performance.now();const o1=await SQ_HOOKS.resample(b1,48000);const tw=performance.now()-t0;const t1=performance.now(),o2=SQ_HOOKS.resampleNow(b2,48000),ts=performance.now()-t1;const H=%s;
              return{tw,ts,h1:H(o1),h2:H(o2),len:o1.length,sr:o1.sampleRate,same:SQRS.cache.get(b1).get(48000)===o1}})()"""%HASHB)
            print(f'  4-minute stereo 44.1 kHz buffer to 48 kHz: worker {w["tw"]/1000:.2f} s (the main thread stays free), on the spot {w["ts"]/1000:.2f} s')
            ck('the worker and the main thread give the same bits',w['h1']==w['h2'] and w['sr']==48000 and w['len']==240*48000,w)
            ck('the copy is cached per rate (converted once)',w['same'])
            ck('a 4-minute stereo buffer converts in the worker in under 20 s',w['tw']<20000,w['tw'])
            QUIET="(async()=>{const t0=Date.now();let q=0;while(Date.now()-t0<90000){if(!MAP.busy&&SQRS.exp===0){if(++q>10)break}else q=0;await new Promise(r=>setTimeout(r,100))}return Date.now()-t0})()"
            TR="(async()=>{const H=%s,T=S.tracks.filter(t=>%s.includes(t.name)),out={};for(const t of T){const one=async()=>H(await renderMix(%d,0,2,0.5,true,t.id));SQRS.off=true;const a=await one(),a2=await one();SQRS.off=false;const n0=SQRS.n.work+SQRS.n.sync,b=await one(),b2=await one();out[t.name]={a,a2,b,b2,made:SQRS.n.work+SQRS.n.sync-n0}}return out})()"
            NAMES=json.dumps(['Kick','Bass','Clap','Hat','Snare','Vocals (original)'])
            AJ(pg,QUIET)
            for sr in (44100,96000):
                r=AJ(pg,TR%(HASHB,NAMES,sr))
                rep=[k for k,v in r.items() if v['a']==v['a2']]
                print(f'  Fractals, Hi-Fi off, renderMix at {sr} Hz per track: repeatable {rep}; not repeatable (free-running randomness) {[k for k in r if k not in rep]}')
                ck(f'Fractals (Hi-Fi off) at {sr} Hz: Kick and Bass repeatable (the gate\'s reference lines)','Kick' in rep and 'Bass' in rep,r)
                ck(f'Fractals (Hi-Fi off) at {sr} Hz: every repeatable track bit-identical with the hook, nothing converted',all(r[k]['b']==r[k]['a'] and r[k]['b2']==r[k]['a'] for k in rep) and all(v['made']==0 for v in r.values()),r)
            nb=J(pg,"(()=>{const sr=ctx?ctx.sampleRate:0;return{sr,n:sqRsAll().length,other:sqRsAll().filter(b=>b.sampleRate!==sr).length,r96:sqRsAll().filter(b=>b.sampleRate!==96000).length}})()")
            print('  buffers loaded:',nb)
            ck('Fractals has buffers that play at another rate at 96 kHz (the test means something)',nb['r96']>0,nb)
            # Hi-Fi on: the export waits for the copies at 96 kHz and uses them; per track the same bits twice
            r=AJ(pg,"""(async()=>{sqUseAll('clean');const n0=Object.assign({},SQRS.n);const a=await renderMix(96000,0,1,0.2,true);const n1=Object.assign({},SQRS.n);
              const need=sqRsAll().filter(x=>x.sampleRate!==96000);return{made:n1.work+n1.sync-n0.work-n0.sync,hit:n1.hit-n0.hit,all:need.every(x=>!!sqRsHas(x,96000)),need:need.length}})()""")
            print('  Hi-Fi on, renderMix at 96 kHz:',r)
            ck('Hi-Fi on: the export at 96 kHz converts the buffers first and plays the copies',r['made']>0 and r['hit']>0 and r['all'],r)
            AJ(pg,QUIET)
            r=AJ(pg,TR%(HASHB,NAMES,96000))
            ck('Hi-Fi on at 96 kHz: each repeatable track gives the same bits twice and converts nothing again',all(v['b']==v['b2'] and v['made']==0 for k,v in r.items() if k in rep),r)
            ck('Hi-Fi on at 96 kHz: the sample tracks sound different from Hi-Fi off (the copies are used)',any(v['b']!=v['a'] for k,v in r.items() if k in rep),r)
            # live: copies for the engine's rate, then a live source gets the copy
            lv=AJ(pg,"""(async()=>{ensureCtx();const sr=ctx.sampleRate;await SQ_HOOKS.warm(sr);const L=sqRsAll().filter(b=>b.sampleRate!==sr);const b=new AudioBuffer({numberOfChannels:1,length:4410,sampleRate:sr===44100?48000:44100});
              await SQ_HOOKS.resample(b,sr);const s=ctx.createBufferSource();s.buffer=b;const s2=ctx.createBufferSource();S.sq='classic';s2.buffer=b;S.sq='clean';return{sr,n:L.length,all:L.every(x=>!!sqRsHas(x,sr)),got:s.buffer.sampleRate,classic:s2.buffer===b}})()""")
            ck('live, Hi-Fi on: every loaded buffer has its copy for the engine\'s rate; a source gets the copy; Hi-Fi off gets the original',lv['all'] and lv['got']==lv['sr'] and lv['classic'],lv)
            AJ(pg,QUIET)
            ck('nothing left running while idle (no batch timer, no job)',J(pg,"SQRS.tm===0&&SQRS.jobs.size===0&&SQRS.exp===0"))
            R(pg,"undo()");pg.wait_for_timeout(300)
            ck('one undo puts the song back to Hi-Fi off',R(pg,"sqProj()")=='classic')
        h=J(pg,"(()=>{const r=STX.get('songHiFi');return r?r.h:''})()")
        ck(f'{L}: the Hi-Fi row says samples are converted once, plain words, no em dash','converted once' in h and '—' not in h,h)
        pg.screenshot(path=os.path.join(OUT,f'sq3_{L}.png'))
        ck(f'{L}: no console errors',not errs,errs)
        c.close()
    b.close()
print(f'taskSQ3: {N[1]} of {N[0]} checks passed'+('' if not FAIL else ' -- FAILED: '+'; '.join(FAIL)))
sys.exit(1 if FAIL else 0)
