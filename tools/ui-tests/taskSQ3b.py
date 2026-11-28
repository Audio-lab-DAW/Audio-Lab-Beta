"""Task SQ3b part a (sound quality, lane N): the pitched read (Q12). With Hi-Fi on for the device, a Sampler note (Classic and One shot
modes) or a key-tracked drum designer note at another pitch plays a copy of its sample read at that pitch with a windowed sinc (made once
per pitch, in a worker live, on the spot in renders that make files); Hi-Fi off is today's path (Chromium's linear playbackRate).
Checks, with the research doc's analyser (tools/engine-lab/ae1/anal.py alias_report, harmonics=1) and its case (measure_app.py: a sine
at 48 kHz played at playbackRate 2^(7/12) in a 48 kHz render, the middle second):
- +7 semitones at 1, 5 and 10 kHz: Hi-Fi off reads like the research doc (-63.9 / -35.5 / -22.2 dB), Hi-Fi on under -100 dB;
- -12, +12 and +19 semitones, and a 44.1 kHz sample at +7 semitones in a 48 kHz render (pitch and rate in one step): under -100 dB;
- the level is kept (within 0.05 dB of the ideal), a constant stays the constant, the copy lasts length / ratio;
- Hi-Fi off: the source path is bit-identical with the hook and without it (SQP.off);
- the worker and the main thread give the same bits;
- the Sampler end to end (sampPlay, Classic with its loop, and One shot), a key-tracked Tom designer (pzPlay): Hi-Fi on uses the copy,
  the note's level stays within 1 dB of Hi-Fi off, it starts and stops at the same samples, no NaN; two renders give the same bits;
  Hi-Fi off (and a device following a Hi-Fi off song) is bit-identical with the hook and without it;
- live: a Hi-Fi Sampler note the first time plays as before and asks the worker; once the copy is there the next note plays it;
  the song's notes are converted ahead when the song starts;
- the Sampler shows its Hi-Fi switch with its line and tooltip; no timers or jobs left while idle; dark and Light; no console errors.
  python3 tools/ui-tests/taskSQ3b.py [repo dir] [out dir]"""

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
# a sine (or a constant) at rate a, played at playbackRate rate in an offline render at rate b, through the hook as a Hi-Fi note
# (mode 'on'), as a Hi-Fi off note ('off': straight), or with the hook turned off ('raw'); the middle second and a checksum
TONE0="""window.__pt=async([f,a,b,rate,mode,dc,worker])=>{const n=Math.ceil(a*3*Math.max(1,rate*a/b)),src=new AudioBuffer({numberOfChannels:1,length:n,sampleRate:a}),d=src.getChannelData(0);
 for(let i=0;i<n;i++)d[i]=dc?0.5:0.5*Math.sin(2*Math.PI*f*i/a);SQP.off=mode==='raw';const h0={...SQP.n};
 try{if(worker)await SQ_HOOKS.pitched(src,b,Math.fround(rate));
  const c=new OfflineAudioContext(1,b*2,b),go=c=>{const s=c.createBufferSource();s.buffer=src;s.playbackRate.value=rate;s.connect(c.destination);s.start()};
  if(mode==='on'){SQP.exp++;try{sqPrCall(go,null,[c],c)}finally{SQP.exp--}}else go(c);
  const r=await c.startRendering(),o=r.getChannelData(0);let h=0;for(let i=0;i<o.length;i++){const u=new Uint32Array(new Float32Array([o[i]]).buffer)[0];h=(Math.imul(h,31)+u)|0}
  const m=o.slice(b/2,b/2+b),u8=new Uint8Array(m.buffer);let s2='';for(let i=0;i<u8.length;i+=32768)s2+=String.fromCharCode.apply(null,u8.subarray(i,i+32768));
  const cp=sqPrHas(src,b,Math.fround(rate));return{h,x:btoa(s2),len:cp?cp.length:0,hit:SQP.n.hit-h0.hit,sync:SQP.n.sync-h0.sync}}finally{SQP.off=false}};
window.__wk=async([n,rate])=>{const a=48000,src=new AudioBuffer({numberOfChannels:2,length:n,sampleRate:a});for(let c=0;c<2;c++){const d=src.getChannelData(c);let x=1;for(let i=0;i<n;i++){x=(x*16807)%2147483647;d[i]=(x/2147483647-.5)*.8}}
 const r=Math.fround(rate),t0=performance.now(),w=await SQ_HOOKS.pitched(src,a,r),tw=performance.now()-t0;const k=SQP.cache.get(src);k.delete(sqPrKey(a,r));const t1=performance.now(),m=SQ_HOOKS.pitchedNow(src,a,r),tm=performance.now()-t1;
 let same=w.length===m.length;for(let c=0;c<2&&same;c++){const x=w.getChannelData(c),y=m.getChannelData(c);for(let i=0;i<x.length;i++)if(x[i]!==y[i]){same=false;break}}return{same,tw,tm,len:w.length,used:!!SQP.w}};
/* a note of the device I through play(c,I,dest,p,w,dur,v) in a 48 kHz render: level, first and last sample over -80 dB, checksum */
window.__note=async([kind,q,songq,p,mode,raw])=>{const keep=S.sq;S.sq=songq;SQP.off=!!raw;const h0={...SQP.n};
 try{const sr=48000,c=new OfflineAudioContext(2,sr*3,sr);let I;
  if(kind==='sampler'){I={preset:'sampler',...sampParams('choir'),mode,gain:.6};if(mode==='classic')I.loop=true}else{I={...PRESETS.ztom,preset:'ztom',kt:1,gain:.9};delete I.name;delete I.cat;delete I.desc}
  if(q)I.quality=q;SQP.exp++;try{if(kind==='sampler')sampPlay(c,I,c.destination,p,.1,1.2,.8);else pzPlay(c,I,c.destination,p,.1,.8)}finally{SQP.exp--}
  const r=await c.startRendering();let h=0,e=0,f=-1,l=-1,nan=0;for(let ch=0;ch<2;ch++){const o=r.getChannelData(ch);for(let i=0;i<o.length;i++){const v=o[i];if(v!==v)nan++;e+=v*v;if(Math.abs(v)>1e-4){if(f<0||i<f)f=i;if(i>l)l=i}const u=new Uint32Array(new Float32Array([v]).buffer)[0];h=(Math.imul(h,31)+u)|0}}
  return{h,db:10*Math.log10(e/(2*r.length)+1e-30),f,l,nan,hit:SQP.n.hit-h0.hit,sync:SQP.n.sync-h0.sync}}finally{S.sq=keep;SQP.off=false}};1"""
def dec(x): return np.frombuffer(base64.b64decode(x),np.float32).astype(np.float64)
ST=2**(1/12)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        c,pg,errs=ctx(b,lite)
        R(pg,TONE0)
        ck(f'{L}: version',float(R(pg,"VERSION"))>=0.314)
        ck(f'{L}: the pitched read is in (sampPlay and pzPlay wrapped)',J(pg,"typeof SQP==='object'&&typeof sqPrRun==='function'&&!!SQ.DEV['inst:sampler']&&!!SQ.DEV['inst:ztom']"))
        if not lite:
            print('  48 kHz sine (0.5) at +7 semitones in a 48 kHz render (research doc, today: -63.9 / -35.5 / -22.2 dB):')
            for f in (1000,5000,10000):
                r7=ST**7;fo=f*r7
                k=pg.evaluate("a=>window.__pt(a)",[f,48000,48000,r7,'off',False,False]);k0=pg.evaluate("a=>window.__pt(a)",[f,48000,48000,r7,'raw',False,False]);cl=pg.evaluate("a=>window.__pt(a)",[f,48000,48000,r7,'on',False,False])
                rk=alias_report(dec(k['x']),48000,fo,harmonics=1);rc=alias_report(dec(cl['x']),48000,fo,harmonics=1)
                lc=20*np.log10(np.sqrt(2*np.mean(dec(cl['x'])**2))/.5);lk=20*np.log10(np.sqrt(2*np.mean(dec(k['x'])**2))/.5)
                print(f'   {f} Hz -> {fo:.0f} Hz: Hi-Fi off {rk["alias_db"]:7.1f} dB, Hi-Fi on {rc["alias_db"]:7.1f} dB (worst {rc["worst_db"]:.1f} dB at {rc["worst_hz"]:.0f} Hz); level {lk:+.4f} / {lc:+.4f} dB')
                ck(f'Hi-Fi off at {f} Hz is bit for bit the path without the hook',k['h']==k0['h'],(k['h'],k0['h']))
                ck(f'Hi-Fi off at {f} Hz reads like the research doc (linear)',abs(rk['alias_db']-{1000:-63.9,5000:-35.5,10000:-22.2}[f])<1.5,rk['alias_db'])
                ck(f'Hi-Fi on at {f} Hz: images under -100 dB, the copy is played (made on the spot)',rc['alias_db']<-100 and cl['hit']==1 and cl['sync']==1,(rc,cl['hit'],cl['sync']))
                ck(f'Hi-Fi on at {f} Hz: the level stays',abs(lc)<0.05,lc)
                ck(f'Hi-Fi on at {f} Hz: the copy lasts the length divided by the ratio',abs(cl['len']-np.ceil(np.ceil(48000*3*r7)/np.float32(r7)))<=1,cl['len'])
            for (st,f,a) in ((-12,1000,48000),(-12,8000,48000),(12,5000,48000),(12,9000,48000),(19,3000,48000),(7,10000,44100),(-5,15000,44100)):
                r=ST**st;fo=f*r
                cl=pg.evaluate("a=>window.__pt(a)",[f,a,48000,r,'on',False,False]);k=pg.evaluate("a=>window.__pt(a)",[f,a,48000,r,'off',False,False])
                rc=alias_report(dec(cl['x']),48000,fo,harmonics=1);rk=alias_report(dec(k['x']),48000,fo,harmonics=1);lc=20*np.log10(np.sqrt(2*np.mean(dec(cl['x'])**2))/.5)
                print(f'   {st:+d} st, {f} Hz at {a} Hz -> {fo:.0f} Hz: Hi-Fi off {rk["alias_db"]:.1f} dB, on {rc["alias_db"]:.1f} dB, level {lc:+.4f} dB')
                ck(f'{st:+d} semitones, {f} Hz sample at {a} Hz: images under -100 dB, level kept',rc['alias_db']<-100 and abs(lc)<0.05,(rc['alias_db'],lc))
            d=pg.evaluate("a=>window.__pt(a)",[0,48000,48000,ST**7,'on',True,False]);x=dec(d['x'])
            ck('a constant stays the constant (within 1e-6)',np.max(np.abs(x-.5))<1e-6,np.max(np.abs(x-.5)))
            w=pg.evaluate("a=>window.__wk(a)",[48000*20,ST**5])
            print(f"   worker: 20 s stereo at +5 semitones in {w['tw']:.0f} ms (worker {w['used']}), on the spot {w['tm']:.0f} ms")
            ck('the worker and the main thread give the same bits',w['same'] and w['used'],w)
            # the devices end to end
            print('  Sampler and Tom designer notes in a 48 kHz render (level, first and last sample over -80 dB):')
            for (kind,mode,pp) in (('sampler','classic',79),('sampler','oneshot',72),('sampler','classic',48),('tom','',67)):
                on=pg.evaluate("a=>window.__note(a)",[kind,'clean','classic',pp,mode,False]);on2=pg.evaluate("a=>window.__note(a)",[kind,'clean','classic',pp,mode,False])
                of=pg.evaluate("a=>window.__note(a)",[kind,'classic','classic',pp,mode,False]);of0=pg.evaluate("a=>window.__note(a)",[kind,'classic','classic',pp,mode,True])
                fo=pg.evaluate("a=>window.__note(a)",[kind,None,'classic',pp,mode,False]);fo0=pg.evaluate("a=>window.__note(a)",[kind,None,'classic',pp,mode,True])
                tag=f'{kind} {mode} note {pp}'
                print(f"   {tag}: Hi-Fi off {of['db']:.3f} dB ({of['f']} to {of['l']}), on {on['db']:.3f} dB ({on['f']} to {on['l']}), copies played {on['hit']}")
                ck(f'{tag}: Hi-Fi on plays the copy, no NaN',on['hit']>=1 and on['nan']==0,on)
                ck(f'{tag}: Hi-Fi on, two renders give the same bits',on['h']==on2['h'],(on['h'],on2['h']))
                ck(f'{tag}: level within 1 dB of Hi-Fi off',abs(on['db']-of['db'])<1,(on['db'],of['db']))
                ck(f'{tag}: starts at the same sample and ends within 5 ms (the release tail crosses -80 dB a little earlier or later)',on['f']==of['f'] and abs(on['l']-of['l'])<240,(on['f'],of['f'],on['l'],of['l']))
                ck(f'{tag}: Hi-Fi off and a device following a Hi-Fi off song are bit-identical with and without the hook',of['h']==of0['h'] and fo['h']==fo0['h'] and of['hit']==0 and fo['hit']==0,(of,of0,fo,fo0))
            rt=pg.evaluate("a=>window.__note(a)",['sampler','clean','classic',60,'classic',False])
            ck('the root note of a 44.1 kHz sample in a Hi-Fi device: only the rate change (SQ3\'s copy)',rt['hit']==1 and rt['sync']==0,rt)
        # live
        lv=J(pg,"(()=>{const t=mkTrack('inst','sampler');Object.assign(t.inst,sampParams('glasskeys'),{preset:'sampler'});pushUndo();S.tracks.push(t);selT=t.id;changed(true);sqScan();return{id:t.id,q:t.inst.quality}})()")
        ck(f'{L}: a new Sampler starts with Hi-Fi on',lv['q']=='clean',lv)
        R(pg,"ensureCtx();ctx.resume();1");pg.wait_for_timeout(400)
        a=J(pg,"(()=>{const t=S.tracks.find(t=>t.id===%s),h0={...SQP.n};sampPlay(ctx,t.inst,ctx.destination,74,ctx.currentTime+.05,.2,.5);return{miss:SQP.n.miss-h0.miss,hit:SQP.n.hit-h0.hit}})()"%json.dumps(lv['id']))
        pg.wait_for_timeout(1500)
        b2=J(pg,"(()=>{const t=S.tracks.find(t=>t.id===%s),h0={...SQP.n};sampPlay(ctx,t.inst,ctx.destination,74,ctx.currentTime+.05,.2,.5);return{miss:SQP.n.miss-h0.miss,hit:SQP.n.hit-h0.hit,work:SQP.n.work}})()"%json.dumps(lv['id']))
        ck(f'{L}: live, the first note plays as before and asks the worker; the next one plays the copy',a['miss']==1 and a['hit']==0 and b2['hit']==1 and b2['work']>=1,(a,b2))
        wm=J(pg,"(()=>{const t=S.tracks.find(t=>t.id===%s);t.clips.push({id:rid(),name:'n',start:0,len:4,off:0,notes:[{p:62,s:0,l:1,v:.8},{p:65,s:1,l:1,v:.8},{p:69,s:2,l:1,v:.8}]});return 1})()"%json.dumps(lv['id']))
        R(pg,"(window.__wm=SQ_HOOKS.warmPitched(ctx.sampleRate).then(n=>window.__wmn=n),1)");pg.wait_for_timeout(2500)
        ck(f'{L}: the song\'s Hi-Fi Sampler notes are converted ahead',J(pg,"window.__wmn")==3,J(pg,"window.__wmn"))
        R(pg,"try{stop()}catch(e){};1");pg.wait_for_timeout(600)
        ck(f'{L}: nothing left running while idle (no jobs)',J(pg,"SQP.jobs.size")==0)
        # the switch on the Sampler
        R(pg,"renderFx();1");pg.wait_for_timeout(600)
        sw=J(pg,"(()=>{const D=document.querySelector('#fxin .dev[data-d=\"inst\"]');const r=D&&D.querySelector('.sqrow,.sqchip');const ch=D&&D.querySelector('.sqchip');return{has:!!r,text:r?r.textContent:'',tip:ch?ch.title:''}})()")
        ck(f'{L}: the Sampler shows its Hi-Fi switch with its line and a tooltip that says what it changes',sw['has'] and 'Hi-Fi' in sw['text'] and 'pitch' in sw['tip'],sw)
        pg.screenshot(path=os.path.join(OUT,f'sq3b_sampler_{L}.png'))
        ck(f'{L}: no console errors',not errs,errs)
        c.close()
    b.close()
print(f'taskSQ3b: {N[1]}/{N[0]} passed'+('' if not FAIL else '; failed: '+'; '.join(FAIL)))
sys.exit(0 if not FAIL else 1)
