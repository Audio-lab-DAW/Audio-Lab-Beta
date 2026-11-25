"""Preset switch while playing (v0.184): how long is the old preset still heard, is there a click, does a long note carry on, does a fast pattern keep its notes?

The track's own output is recorded in the page together with a marker that jumps at the moment of the switch, so times are exact to the sample.
The switch goes through the preset menu of the device (the select in the title row gets a change event), as a click on the menu or on the arrows does.

  python3 tools/engine-tests/preset_switch.py [index.html] [old|new|pattern|start|fx|all]

 old      from the moment of the switch no new note is handed to the audio engine (the test swallows them), so everything heard after it was
          started before the switch: how long does it last?
 new      a real switch: level 20 to 50 ms after it (the long note must sound again), biggest sample step around the switch
 pattern  sixteenth notes: the notes handed to the engine after the switch are counted against the grid (no double, no missing)
 start    press Play inside a long note: does it sound?
 fx       preset change on effects with memory: how long is the old tail heard?
"""
import sys, os, json, base64
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab

INDEX = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith('.html') else 'index.html'
MODE = [a for a in sys.argv[1:] if not a.endswith('.html')] or ['all']
MODE = MODE[0]

# name, preset, inst overrides, UI.poly, pitch
ENG = [
    ('Saw lead (voice engine)', 'saw', {}, True, 60), ('Soft pad (voice engine)', 'pad', {}, True, 60), ('Strings (voice engine)', 'strings', {}, True, 60),
    ('Plant (voice engine)', 'plant', {}, True, 60), ('Acid (voice engine)', 'acid', {}, True, 48), ('Wavetable (voice engine)', 'wtab', {}, True, 60),
    ('Sampler, grains (al-grain)', 'sampler', {'mode': 'grain'}, True, 60), ('Sampler, plain', 'sampler', {}, True, 60),
    ('Emit', 'emit', {}, True, 60), ('Vector Grain', 'vgrain', {}, True, 60), ('Vector FM', 'vfm', {}, True, 60), ('Orbit', 'orb', {}, True, 60),
    ('Venom', 'venom', {}, True, 60), ('Growl', 'growl', {}, True, 40), ('Grid', 'grid', {}, True, 60), ('SFX', 'sfx', {}, True, 60),
    ('Perc', 'perc', {}, True, 60), ('Drum kit', 'drums', {}, True, 36), ('Snare (drum instrument)', 'zsnare', {}, True, 60), ('Hat (drum instrument)', 'zhat', {}, True, 60),
    ('Soft pad (per-note nodes)', 'pad', {}, False, 60), ('Plant (per-note nodes)', 'plant', {}, False, 60), ('Wavetable (per-note nodes)', 'wtab', {}, False, 60),
]
FX = [('delay', 'Echo delay'), ('tdelay', 'Timeless delay'), ('reverb', 'Reverb'), ('blur', 'Blur'), ('conv', 'Space reverb'), ('vdelay', 'Vector Delay'), ('bdelay', 'Bounce Delay'), ('reson', 'Resonator'), ('chorus', 'Chorus'), ('phaser', 'Phaser')]

JS_HELP = r"""(async()=>{
ensureCtx();if(!ctx.__trec){ctx.__trec=1;await ctx.audioWorklet.addModule(URL.createObjectURL(new Blob([`class TR extends AudioWorkletProcessor{constructor(){super();this.x=new Float32Array(4096);this.m=new Float32Array(4096);this.n=0;this.end=0;this.port.onmessage=()=>{this.end=1}}
 flush(){if(this.n)this.port.postMessage({x:this.x.slice(0,this.n),m:this.m.slice(0,this.n)});this.n=0}
 process(ins){const a=ins[0];if(this.end){if(this.end===1){this.flush();this.port.postMessage({done:1});this.end=2}return true}const L=a&&a[0],M=a&&a[1],N=L?L.length:128;for(let i=0;i<N;i++){this.x[this.n]=L?L[i]:0;this.m[this.n]=M?M[i]:0;if(++this.n===4096)this.flush()}return true}}
registerProcessor('t-rec',TR)`],{type:'text/javascript'})))}
window.__recs={};
window.__rec=function(t){ensureCtx();if(!NODES.get(t.id))syncGraph();const N=NODES.get(t.id);const mono=ctx.createGain();mono.channelCount=1;mono.channelCountMode='explicit';N.pan.connect(mono);
  const mk=ctx.createConstantSource(),mg=ctx.createGain();mg.gain.value=0;mk.connect(mg);mk.start();const mer=ctx.createChannelMerger(2);mono.connect(mer,0,0);mg.connect(mer,0,1);
  /* recorded on the audio thread (a ScriptProcessor loses blocks while the page is busy, and the page is busy exactly at a switch) */
  const sp=new AudioWorkletNode(ctx,'t-rec',{numberOfInputs:1,numberOfOutputs:1,channelCount:2,channelCountMode:'explicit',channelInterpretation:'discrete',outputChannelCount:[1]}),R={x:[],m:[],on:1,mg,sp,mono,mer,mk};sp.port.onmessage=e=>{if(e.data.done){R.fin&&R.fin();return}R.x.push(e.data.x);R.m.push(e.data.m)};
  mer.connect(sp);sp.connect(ctx.destination);window.__recs[t.id]=R;return R};
window.__mark=function(t){const R=window.__recs[t.id];R.mg.gain.setValueAtTime(1,ctx.currentTime)};
window.__pull=async function(id){const R=window.__recs[id];await new Promise(r=>{R.fin=r;R.sp.port.postMessage('end');setTimeout(r,1500)});try{R.sp.disconnect();R.mer.disconnect();R.mono.disconnect();R.mk.stop()}catch(e){}let n=0;for(const a of R.x)n+=a.length;const x=new Float32Array(n),m=new Float32Array(n);let o=0;R.x.forEach((a,i)=>{x.set(a,o);m.set(R.m[i],o);o+=a.length});
  const b64=a=>{const u=new Uint8Array(a.buffer);let s='';for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));return btoa(s)};delete window.__recs[id];return JSON.stringify({sr:ctx.sampleRate,x:b64(x),m:b64(m)})};
/* the preset menu of the selected track's instrument, as a click would use it */
window.__ipre=function(t,k,mark){selT=t.id;renderFx();const s=fxin.querySelector('select[data-s=ipre]')||fxin.querySelector('select[data-vnp]');if(!s)return 'no menu';s.value=k;if(mark)window.__mark(t);s.dispatchEvent(new Event('change',{bubbles:true}));return t.inst.ipk};
window.__fpre=function(t,f,k,mark){selT=t.id;renderFx();const d=[...fxin.querySelectorAll('.dev[data-d=fx]')].find(d=>d.dataset.id===f.id),s=d&&d.querySelector('select[data-x=pre]');if(!s)return 'no menu';s.value=k;if(mark)window.__mark(t);s.dispatchEvent(new Event('change',{bubbles:true}));return f.p.pre};
return 1})()"""


def pull(al, tid):
    d = json.loads(al.run("window.__pull(%s)" % json.dumps(tid)))
    x = np.frombuffer(base64.b64decode(d['x']), dtype=np.float32)
    m = np.frombuffer(base64.b64decode(d['m']), dtype=np.float32)
    i = np.argmax(m > .5) if (m > .5).any() else -1
    return x, int(i), d['sr']


def db(v):
    return 20 * np.log10(max(float(v), 1e-9))


def gone_ms(x, i, sr, pre):
    """ms after the switch until the sound stays under -60 dB of what it was (and under -80 dBFS)"""
    thr = max(pre * 1e-3, 1e-4)
    a = np.abs(x[i:])
    k = np.nonzero(a > thr)[0]
    return 0.0 if not len(k) else (k[-1] + 1) / sr * 1000


def build(al, group, notes_of, poly=True, fx=None):
    tr = []
    for (name, pre, ov, _p, pitch) in group:
        t = {'name': name, 'preset': pre, 'clips': [{'start': 0, 'len': 64, 'notes': notes_of(pitch)}]}
        if ov:
            t['inst'] = ov
        if fx:
            t['fx'] = fx
        tr.append(t)
    al.build({'bpm': 120, 'tracks': tr})
    al.run("UI.poly=%s;UI.countIn=false;S.loop=false;S.click=false;1" % ('true' if poly else 'false'))
    al.run(JS_HELP)


def groups(L, n):
    for i in range(0, len(L), n):
        yield L[i:i + n]


LONG = lambda p: [{'p': p, 's': 0, 'l': 60, 'v': .8}]
FAST = lambda p: [{'p': p, 's': i * .25, 'l': .2, 'v': .8} for i in range(240)]
SHORT = lambda p: [{'p': p, 's': 0, 'l': 1.9, 'v': .8}]   # ends at 0.95 s: the switch at 1.05 s lands in its release


def run_switch(al, group, notes_of, silent, at=1500, after=2600, poly=True):
    """returns per track: (x, i, sr, key before, key after)"""
    build(al, group, notes_of, poly)
    W = al.page.wait_for_timeout
    al.run("(()=>{for(const t of S.tracks)window.__rec(t);pos=0;start();return 1})()")
    W(at)
    keys = json.loads(al.run("""(()=>{const out=[];for(const t of S.tracks){const I=t.inst,P=IPRE[I.preset];if(!P){out.push([null,'no menu']);continue}const ks=Object.keys(P[0]),k0=I.ipk||ks[0],k1=ks[(Math.max(0,ks.indexOf(k0))+1)%%ks.length];
      if(%s&&!window.__sb1){window.__sb1=synthB;window.__sy1=synth;synthB=function(){};synth=function(){}}
      const r=window.__ipre(t,k1,1);out.push([k0,r])}return JSON.stringify(out)})()""" % ('true' if silent else 'false')))
    W(after)
    al.run("(()=>{stop();if(window.__sb1){synthB=window.__sb1;synth=window.__sy1;window.__sb1=null}return 1})()")
    out = []
    for (g, kk) in zip(group, keys):
        x, i, sr = pull(al, al.tracks[g[0]])
        out.append((g, x, i, sr, kk))
    return out


def test_old(al):
    print('\n== How long the old preset is still heard after a switch (no new notes from the switch on) ==')
    print('%-30s | %-22s | long note held | in the release | sixteenth notes' % ('instrument', 'switch'))
    res = {}
    for poly in (True, False):
        L = [e for e in ENG if e[3] == poly]
        for case, notes_of, at in (('long', LONG, 1500), ('rel', SHORT, 1050), ('fast', FAST, 1500)):
            for g in groups(L, 6):
                for (e, x, i, sr, kk) in run_switch(al, g, notes_of, True, at=at, poly=poly):
                    if i < 0 or kk[1] == 'no menu':
                        res.setdefault(e[0], {})[case] = None
                        continue
                    pre = float(np.max(np.abs(x[max(0, i - int(.4 * sr)):i]))) if i > 0 else 0
                    ms = gone_ms(x, i, sr, pre)
                    cap = (len(x) - i) / sr * 1000
                    res.setdefault(e[0], {})[case] = (ms, cap, pre)
                    res[e[0]]['sw'] = '%s > %s' % (kk[0], kk[1])
    worst = 0
    for e in ENG:
        r = res.get(e[0], {})

        def f(c):
            v = r.get(c)
            if v is None:
                return 'no menu'
            ms, cap, pre = v
            if pre < 2e-4:
                return 'silent before'
            return ('over %d ms' % int(cap - 60)) if ms > cap - 60 else '%.0f ms' % ms
        for c in ('long', 'rel', 'fast'):
            v = r.get(c)
            if v and v[2] >= 2e-4:
                worst = max(worst, v[0])
        print('%-30s | %-22s | %-14s | %-14s | %s' % (e[0], r.get('sw', '')[:22], f('long'), f('rel'), f('fast')))
    print('longest: %.0f ms' % worst)
    return worst


def test_new(al):
    print('\n== A real switch inside a long note: is it heard again, is there a click ==')
    print('%-30s | %-22s | level before | 20 to 50 ms after | 100 to 300 ms after | biggest step at the switch / in the sound before / after (per cent of full scale)' % ('instrument', 'switch'))
    bad = []
    for poly in (True, False):
        L = [e for e in ENG if e[3] == poly]
        for g in groups(L, 1):
            for (e, x, i, sr, kk) in run_switch(al, g, LONG, False, at=1600, after=900, poly=poly):
                if i < 0 or kk[1] == 'no menu':
                    print('%-30s | no menu' % e[0])
                    continue
                rms = lambda a: db(np.sqrt(np.mean(a * a))) if len(a) else -180
                st = lambda a: float(np.max(np.abs(np.diff(a)))) * 100 if len(a) > 1 else 0
                b = x[i - int(.3 * sr):i]
                a1 = x[i + int(.02 * sr):i + int(.05 * sr)]
                a2 = x[i + int(.1 * sr):i + int(.3 * sr)]
                s0, s1, s2 = st(x[i - int(.002 * sr):i + int(.03 * sr)]), st(b), st(x[i + int(.05 * sr):i + int(.4 * sr)])
                was = rms(b) > -60
                heard = rms(a1) > -60 or not was
                click = s0 > max(s1, s2) * 2 + 1.0
                if not heard or click:
                    bad.append((e[0], 'not heard' if not heard else 'step'))
                print('%-30s | %-22s | %6.1f dB | %6.1f dB %s | %6.1f dB | %.2f / %.2f / %.2f%s' % (e[0], ('%s > %s' % tuple(kk))[:22], rms(b), rms(a1), ('yes' if heard else 'NO ') if was else 'n/a', rms(a2), s0, s1, s2, '  STEP' if click else ''))
    print('problems:', bad)
    return bad


def test_pattern(al):
    print('\n== Sixteenth notes across a switch: notes handed to the engine, counted against the grid ==')
    bad = []
    for poly in (True, False):
        L = [e for e in ENG if e[3] == poly]
        for g in groups(L, 6):
            build(al, g, FAST, poly)
            W = al.page.wait_for_timeout
            al.run("""(()=>{window.__nl=[];window.__cut={};if(typeof chsTrack==='function'&&!window.__ct0){window.__ct0=chsTrack;chsTrack=function(t){window.__cut[t.name]=(window.__cut[t.name]||0)+1;return window.__ct0.apply(this,arguments)}}const _sb=synthB;window.__sb0=_sb;synthB=function(c,I,dest,p,w,dur,v,clip,ns,spb){if(c===ctx&&clip){const t=ITRK.get(I);window.__nl.push([t?t.name:'?',+ns.toFixed(4),+w.toFixed(5),+dur.toFixed(4),+ctx.currentTime.toFixed(5),t?(window.__cut[t.name]||0):0])}return _sb.apply(this,arguments)};pos=0;start();return 1})()""")
            W(1500)
            ts = json.loads(al.run("""(()=>{const o={};for(const t of S.tracks){const I=t.inst,P=IPRE[I.preset];if(!P)continue;const ks=Object.keys(P[0]),k1=ks[(Math.max(0,ks.indexOf(I.ipk))+1)%ks.length];o[t.name]=[ctx.currentTime,play.t0];window.__ipre(t,k1)}return JSON.stringify(o)})()"""))
            W(2000)
            nl = json.loads(al.run("(()=>{const n=window.__nl;const e=[ctx.currentTime,play.t0,play.sched];stop();synthB=window.__sb0;return JSON.stringify([n,e])})()"))
            notes, (tend, t0, sched) = nl
            for e in g:
                if e[0] not in ts:
                    print('%-30s | no menu' % e[0])
                    continue
                tsw = ts[e[0]][0]
                mine = [n for n in notes if n[0] == e[0]]
                # the sound of a note: what was handed over last for that note start (a switch plays the notes of the look-ahead again; the old ones are cut)
                want = [round(k * .25, 4) for k in range(240) if k * .125 + t0 < tend - .4 and k * .25 < sched]
                after = [n for n in mine if n[2] >= tsw - .001]
                before = [n for n in mine if n[2] < tsw - .001]
                # notes that sound after the switch: every grid note whose time is after the switch must have been handed over after the switch exactly once (or, before the fix, once in all)
                late = [s for s in want if s * .5 + t0 > tsw + .012]
                cnt = {s: 0 for s in late}
                for n in mine:
                    if n[1] in cnt:
                        cnt[n[1]] += 1
                miss = [s for s in late if cnt[s] == 0]
                # a cut silences everything handed over before it, so the copies that sound are the ones handed over after the track's last cut
                last = max([n[5] for n in mine] or [0])
                live = lambda s_: sum(1 for n in mine if n[1] == s_ and (n[5] == last or n[2] < tsw))
                dbl_same = [s for s in late if sum(1 for n in mine if n[1] == s and n[5] == last) > 1]
                if last:
                    miss += [s for s in late if sum(1 for n in mine if n[1] == s and n[5] == last) == 0]
                off = [n for n in mine if n[1] in cnt and abs(n[2] - (n[1] * .5 + t0)) > .002]
                ok = not miss and not dbl_same and not off
                if not ok:
                    bad.append(e[0])
                print('%-30s | notes due after the switch %3d | missing or still with the old sound %d | sounding twice %d | off the grid by more than 2 ms %d | %s' % (e[0], len(late), len(miss), len(dbl_same), len(off), ('ok' if ok else 'PROBLEM') + (', cut %d times' % last if last != 1 else '')))
    print('problems:', bad)
    return bad


def test_start(al):
    print('\n== Press Play inside a long note (at beat 3 of a note from 0 to 60), against what playing from the start gives at that spot ==')
    bad = []
    for poly in (True, False):
        L = [e for e in ENG if e[3] == poly]
        for g in groups(L, 6):
            build(al, g, LONG, poly)
            W = al.page.wait_for_timeout
            lv = {}
            for pos in (0, 3):
                al.run("(()=>{for(const t of S.tracks)window.__rec(t);pos=%d;start();const T=play.t0+%f;for(const t of S.tracks){const R=window.__recs[t.id];R.mg.gain.setValueAtTime(1,T)}return 1})()" % (pos, 1.5 if pos == 0 else 0))
                W(2600 if pos == 0 else 1100)
                al.run("stop();1")
                W(500)
                for e in g:
                    x, i, sr = pull(al, al.tracks[e[0]])
                    a = x[i + int(.02 * sr):i + int(.05 * sr)] if i >= 0 else x[:0]
                    a2 = x[i + int(.1 * sr):i + int(.5 * sr)] if i >= 0 else x[:0]
                    lv[(e[0], pos)] = (db(np.sqrt(np.mean(a * a))) if len(a) else -180, db(np.sqrt(np.mean(a2 * a2))) if len(a2) else -180)
            for e in g:
                r, c = lv[(e[0], 0)], lv[(e[0], 3)]
                ok = c[1] > -60 or r[1] < -60
                if not ok:
                    bad.append(e[0])
                print('%-30s | playing from the start, at that spot %6.1f dB | Play pressed there: 20 to 50 ms after %6.1f dB, 100 to 500 ms after %6.1f dB | %s' % (e[0], r[1], c[0], c[1], ('sounds' if c[1] > -60 else 'nothing to pick up') if ok else 'SILENT'))
    print('silent:', bad)
    return bad


def test_fx(al):
    print('\n== Preset change on an effect: how long is the old tail heard (a short note, then silence, then the switch) ==')
    worst = 0
    for (ty, name) in FX:
        al.build({'bpm': 120, 'tracks': [{'name': 'T', 'preset': 'pluck', 'fx': [{'type': ty}], 'clips': [{'start': 0, 'len': 64, 'notes': [{'p': 60, 's': 0, 'l': .5, 'v': .9}, {'p': 67, 's': .5, 'l': .5, 'v': .9}, {'p': 72, 's': 1, 'l': .5, 'v': .9}]}]}]})
        al.run("UI.poly=true;UI.countIn=false;S.loop=false;S.click=false;1")
        al.run(JS_HELP)
        W = al.page.wait_for_timeout
        # the longest preset first, so there is a tail to measure
        k0 = al.run("""(()=>{const t=S.tracks[0],f=t.fx[0],P=FXPRE[f.type];if(!P)return null;const ks=Object.keys(P);let best=ks[0],bv=-1;for(const k of ks){const p=P[k][1],v=(+p.fb||0)+(+p.feedback||0)+(+p.fbk||0)+(+p.regen||0)+(+p.decay||0)*20+(+p.size||0)+(+p.mix||0)/100;if(v>bv){bv=v;best=k}}Object.assign(f.p,P[best][1]);f.p.pre=best;if(f.p.mix!=null)f.p.mix=Math.max(f.p.mix,50);changed(true);renderFx();window.__rec(t);pos=0;start();return best})()""")
        if k0 is None:
            print('%-16s | no presets' % name)
            continue
        W(1500)
        k1 = al.run("""(()=>{const t=S.tracks[0],f=t.fx[0],ks=Object.keys(FXPRE[f.type]),k=ks[(ks.indexOf(f.p.pre)+1)%ks.length];return window.__fpre(t,f,k,1)})()""")
        W(2600)
        al.run("stop();1")
        x, i, sr = pull(al, al.tracks['T'])
        pre = float(np.max(np.abs(x[max(0, i - int(.2 * sr)):i]))) if i > 0 else 0
        ms = gone_ms(x, i, sr, pre)
        cap = (len(x) - i) / sr * 1000
        st = lambda a: float(np.max(np.abs(np.diff(a)))) * 100 if len(a) > 1 else 0
        s0, s1 = st(x[i - int(.002 * sr):i + int(.03 * sr)]), st(x[i - int(.2 * sr):i])
        txt = 'silent before' if pre < 2e-4 else (('over %d ms' % int(cap - 60)) if ms > cap - 60 else '%.0f ms' % ms)
        if pre >= 2e-4:
            worst = max(worst, ms)
        ms2 = al.run("+(CHS&&CHS.fxms||0).toFixed(2)")
        print('%-16s | %-12s > %-12s | tail before the switch %6.1f dB | old tail heard for %-12s | biggest step at the switch %.2f, before %.2f | the fresh effect took %s ms to build' % (name, str(k0)[:12], str(k1)[:12], db(pre), txt, s0, s1, ms2))
    print('longest: %.0f ms' % worst)
    return worst


if __name__ == '__main__':
    al = AudioLab(INDEX)
    al.start()
    print('AudioLab', al.version)
    R = {}
    for name, fn in (('old', test_old), ('new', test_new), ('pattern', test_pattern), ('start', test_start), ('fx', test_fx)):
        if MODE in ('all', name):
            R[name] = fn(al)
    print('\npage errors:', al.errors)
    al.stop()
