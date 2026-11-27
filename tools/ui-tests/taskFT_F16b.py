#!/usr/bin/env python3
"""Task FT-F16b (volume shaper, part 2): the curve started by the notes of another track (sample exact, live and in an export, a muted ghost
track works) or by the hits of another track's sound (in the worklet and in an export with the trigger track muted), two or three bands
(only the lows follow the curve; the crossover adds up flat; every band shaped is the same as one band), the bar-line mode bit-identical
to v0.294, the second row of the device (tooltips, undo, Light), saved with the song.
   python3 tools/ui-tests/taskFT_F16b.py [index.html] [out dir] [old index.html for the bit-identical check]"""
import sys, os, json
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)[:300]) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)
# the fake MIDI system: FAKEMIDI.plug(name), .unplug(name), .msg(name,[bytes]); every byte AudioLab sends lands in FAKEMIDI.sent
FAKE = r"""(()=>{const F=window.FAKEMIDI={sent:[],asked:[],refuse:!!window.__refuseSysex,acc:null};
 const acc={inputs:new Map(),outputs:new Map(),onstatechange:null,sysexEnabled:false};F.acc=acc;
 const fire=p=>{if(acc.onstatechange)acc.onstatechange({port:p})};
 F.plug=(name,man,outName)=>{/* from v0.261 (task HF1) a control surface works only once the user turned it on in Controllers: these tests turn every fake device on */try{AudioLab.run('UI.ctlOn=Object.assign({},UI.ctlOn||{},{'+JSON.stringify(name)+':1})')}catch(e){}const id='in-'+name,oid='out-'+name;const i={id,name,manufacturer:man||'Fake',type:'input',state:'connected',onmidimessage:null};
   const o={id:oid,name:outName||name,manufacturer:man||'Fake',type:'output',state:'connected',send(d){F.sent.push({port:o.name,data:Array.from(d),t:performance.now()})}};
   acc.inputs.set(id,i);acc.outputs.set(oid,o);fire(i)};
 F.unplug=name=>{const i=acc.inputs.get('in-'+name),o=acc.outputs.get('out-'+name);if(i){i.state='disconnected';acc.inputs.delete(i.id)}if(o){o.state='disconnected';acc.outputs.delete(o.id)}fire(i)};
 F.msg=(name,b)=>{const i=acc.inputs.get('in-'+name);if(i&&i.onmidimessage)i.onmidimessage({data:new Uint8Array(b)})};
 Object.defineProperty(navigator,'requestMIDIAccess',{configurable:true,value:o=>{F.asked.push(!!(o&&o.sysex));if(o&&o.sysex&&F.refuse)return Promise.reject(new DOMException('SysEx refused','NotAllowedError'));acc.sysexEnabled=!!(o&&o.sysex);return Promise.resolve(acc)}})})()"""
INIT = "if(!sessionStorage.getItem('c1i')){sessionStorage.setItem('c1i','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"

def boot(p, refuse=False, dsf=1, src=None):
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=dsf); pg = ctx.new_page(); logs = []
    def con(m):
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall' not in m.text and 'willReadFrequently' not in m.text): logs.append(m.type + ': ' + m.text[:200])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=src or SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT + (';window.__refuseSysex=1;' if refuse else ';') + FAKE)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    return b, pg, logs, R
J = lambda R, c: json.loads(R("JSON.stringify(" + c + ")"))

import base64, hashlib
TR = []
def rhash(pg, b0, b1, tid):
    h = pg.evaluate("o=>AudioLab.render(o)", {'b0': b0, 'b1': b1, 'sr': 44100, 'only': tid}); m = hashlib.md5()
    for ch in range(h['ch']):
        for off in range(0, h['len'], 1 << 18):
            n = min(1 << 18, h['len'] - off); m.update(base64.b64decode(pg.evaluate("a=>AudioLab.pull(a[0],a[1],a[2],a[3])", [h['id'], ch, off, n])))
    pg.evaluate("i=>AudioLab.free(i)", h['id']); return m.hexdigest()[:12]
NOTES = "findClip(%s).c.notes.map(n=>[n.p,n.s,n.l,n.v,n.ch||1,n.ac||0,n.sl||0])"
def cell_xy(R, row, i, lane=None):
    return J(R, "(()=>{const f=ftSqClip(),st=f.c.steps,G=ftSqGeo(st),r=FTSQ.cv.getBoundingClientRect(),z=ZOOM||1;const y=%s;return[r.left+(FTSQ.LW+%d*G.cw+G.cw/2)*z,r.top+y*z]})()" % (("%d*FTSQ.RH+FTSQ.RH/2" % row) if lane is None else ("G.ly+%d*FTSQ.LH+(FTSQ.LH-5)/2" % lane), i))
def menu_labels(R): return J(R, "[...document.querySelectorAll('#ctxm button')].map(b=>b.textContent.trim())")
def menu_click(R, label):
    return R("(()=>{const b=[...document.querySelectorAll('#ctxm button')].find(b=>b.textContent.trim().startsWith(%s));if(!b)return 'none';b.click();return 'ok'})()" % json.dumps(label))


import struct
def floats(pg, h, ch, off, n):
    return struct.unpack('<%df' % n, base64.b64decode(pg.evaluate("a=>AudioLab.pull(a[0],a[1],a[2],a[3])", [h['id'], ch, off, n])))
# the worklet alone: a constant 1 through the shaper in an offline context, the song from beat 0
DIRECT = """async o=>{const c=new OfflineAudioContext(2,o.n,o.sr);const s=c.createConstantSource();s.offset.value=1;SIDE_B0=o.b0||0;const X=ftVsNode(c);X.set(o.p);s.connect(X.in);X.out.connect(c.destination);s.start(0);
 const b=await c.startRendering(),d=b.getChannelData(0);const out=[];for(const i of o.at)out.push(d[i]);let first=-1;for(let i=0;i<d.length;i++)if(d[i]>.5){first=i;break}SIDE_B0=0;return{at:out,first,peak:Math.max(...d)}}"""
def ARUN(R, pg, code):
    R('window.__P=(' + code + ');0'); return pg.evaluate('()=>window.__P')
OLD = sys.argv[3] if len(sys.argv) > 3 else None
import math
SR = 48000; BPM = 145
fr = lambda beat, sr=SR: int(-(-(beat * 60 / BPM * sr) // 1))
# offline worklet runs: a constant 1 into the shaper; optionally a burst train into its trigger input; optionally sines instead of the constant
DIRECT2 = """async o=>{const c=new OfflineAudioContext(2,o.n,o.sr);SIDE_B0=o.b0||0;const X=ftVsNode(c);X.set(o.p);
 if(o.sines){for(const[f,a] of o.sines){const s=c.createOscillator();s.frequency.value=f;const g=c.createGain();g.gain.value=a;s.connect(g);g.connect(X.in);s.start(0)}}
 else{const s=c.createConstantSource();s.offset.value=1;s.connect(X.in);s.start(0)}
 if(o.bursts){const B=c.createBuffer(1,o.n,o.sr),d=B.getChannelData(0);for(const[at,len,a] of o.bursts)for(let i=at;i<at+len&&i<o.n;i++)d[i]=a*(i%2?1:-1);const k=c.createBufferSource();k.buffer=B;k.connect(X.key);k.start(0)}
 X.out.connect(c.destination);const b=await c.startRendering(),d=b.getChannelData(0);SIDE_B0=0;window.__D=d;const out=[];for(const i of o.at||[])out.push(d[i]);
 const gz=[];for(const[f,i0,i1] of o.gz||[]){let re=0,im=0;for(let i=i0;i<i1;i++){const w=2*Math.PI*f*i/o.sr;re+=d[i]*Math.cos(w);im+=d[i]*Math.sin(w)}gz.push(2*Math.sqrt(re*re+im*im)/(i1-i0))}
 return{at:out,gz}}"""
def ARUN(R, pg, code):
    R('window.__P=(' + code + ');0'); return pg.evaluate('()=>window.__P')
def run(R, pg, o): return ARUN(R, pg, "(" + DIRECT2 + ")(" + json.dumps(o) + ")")
def song_hash(pg, R, preset_k4):
    R("AudioLab.build({bpm:145,tracks:[{name:'Bass',preset:'saw',clips:[{start:0,len:8,notes:[{p:45,s:0,l:4,v:.8},{p:52,s:4,l:4,v:.7}]}],fx:[{type:'ftvs',p:%s}]}]})" % json.dumps(preset_k4))
    pg.wait_for_timeout(400); return rhash(pg, 0, 8, J(R, "S.tracks[0].id"))
with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 294), 'version 0.294 or later', v)
    ok(J(R, "typeof ftVsTb==='function'&&!!NACT.ftvs.src&&FTVS_TG.note===1"), 'the F16b parts are in')
    ok(J(R, "S.tracks.every(t=>t.fx.every(f=>f.type!=='ftvs'))"), 'Fractals has no volume shaper (older songs untouched)')
    R("S.bpm=145;S.tempo=[];TMC=null")
    # --- 1. bar-line mode is unchanged: the F16a sample checks again, and an export hash equal to the build before this step
    roll = J(R, "Object.assign({},FXPRE.ftvs.kroll[1],{soft:0})")
    r = run(R, pg, {'n': SR, 'sr': SR, 'p': roll, 'at': [0, 4965, 4966, 19862, 19863, 24827, 24828]})
    ok(r['at'] == [0, 0, 1, 1, 0, 0, 1], 'bar lines (as before): the Psy roll gap’s point at 1/16 lands on frame 4966, the next gap on 19863 to 24828', r['at'])
    k4 = J(R, "FXPRE.ftvs.k4[1]")
    hnew = song_hash(pg, R, k4)
    if OLD:
        b2, pg2, logs2, R2 = boot(p, src=open(OLD, encoding='utf-8').read())
        R2("S.bpm=145;S.tempo=[];TMC=null"); hold = song_hash(pg2, R2, k4); b2.close()
        ok(hnew == hold, 'an export with a Volume Shaper on the bar lines is bit-identical to the build before this step (%s)' % hnew, (hnew, hold))
    # --- 2. notes of another track: a muted ghost kick with notes at beats 1, 2.5 and 3.25
    R("AudioLab.build({bpm:145,tracks:[{name:'Pad',preset:'saw',clips:[{start:0,len:8,notes:[{p:45,s:0,l:8,v:.8}]}],fx:[{type:'ftvs',p:%s}]},{name:'Ghost kick',preset:'saw',mute:true,clips:[{start:0,len:8,notes:[{p:36,s:1,l:.1,v:1},{p:36,s:2.5,l:.1,v:1},{p:38,s:3.25,l:.1,v:1}]}]}]})" % json.dumps(k4))
    pg.wait_for_timeout(400); PAD, GH = J(R, "[S.tracks[0].id,S.tracks[1].id]")
    pn = dict(J(R, "S.tracks[0].fx[0].p"), soft=0, trig='note', src=GH)
    ok(J(R, "ftVsTb(%s)" % json.dumps(pn)) == [1, 2.5, 3.25], 'the ghost track’s notes are the triggers, in song beats', J(R, "ftVsTb(%s)" % json.dumps(pn)))
    at = [0, fr(1) - 1, fr(1), fr(1.25), fr(1.5) + 1, fr(2.5) - 1, fr(2.5), fr(3.25), fr(3.25) + 5]
    r = run(R, pg, {'n': SR * 2, 'sr': SR, 'p': pn, 'at': at})
    g = r['at']
    ok(g[0] == 1 and g[1] == 1 and g[2] < 1e-3 and 0 < g[3] < 1 and g[4] == 1 and g[5] == 1 and g[6] < 1e-3 and g[7] < 1e-3, 'Start on notes: full before the first note, the curve starts on the note’s sample (frame %d at 145 BPM) and on every later note' % fr(1), g)
    pn1 = dict(pn, nf=36)
    g = run(R, pg, {'n': SR * 2, 'sr': SR, 'p': pn1, 'at': [fr(3.25), fr(3.25) + 5]})['at']
    ok(g[0] > .99 and g[1] > .99, 'Only one note (36): the note 38 at beat 3.25 does not start it', g)
    g = run(R, pg, {'n': SR, 'sr': SR, 'p': pn, 'at': [fr(1) - fr(.5), fr(1) - fr(.5) + 1, 0], 'b0': .5})['at']
    ok(g[0] == 1 and g[1] < 1e-3, 'a render that starts at beat 0.5 still starts the curve on the song’s beat 1', g)
    # an export: the pad equals the dry pad times the hook's gain, the ghost track muted
    R("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,{trig:'note',src:%s,soft:0});changed(false)})()" % json.dumps(GH))
    def render(o): return pg.evaluate("o=>AudioLab.render(o)", o)
    hw = render({'b0': 0, 'b1': 4, 'sr': SR, 'tracks': [PAD]}); R("S.tracks[0].fx[0].on=false;changed(false)"); hd = render({'b0': 0, 'b1': 4, 'sr': SR, 'tracks': [PAD]}); R("S.tracks[0].fx[0].on=true;changed(false)")
    n = min(hw['len'], hd['len'], fr(4))
    W = floats(pg, hw, 0, 0, n); D = floats(pg, hd, 0, 0, n)
    G = J(R, "(()=>{const p=S.tracks[0].fx[0].p,o=[];for(let i=0;i<%d;i+=5)o.push(FT_HOOKS.volumeShaper.gainAt(p,i/48000*145/60));return o})()" % n)
    errs = [abs(W[i] - D[i] * G[k]) for k, i in enumerate(range(0, n, 5)) if abs(D[i]) > .02]
    ok(len(errs) > 1000 and max(errs) < 1e-4, 'export: the pad is the dry pad times the curve started by each ghost note (%d samples, worst %.2e); the muted ghost track is silent' % (len(errs), max(errs) if errs else 9))
    ok(J(R, "S.tracks[1].mute===true"), 'the ghost track stays muted')
    R("AudioLab.free(%s);AudioLab.free(%s)" % (json.dumps(hw['id']), json.dumps(hd['id'])))
    # live: playing, the worklet gets the triggers and reports a trigger
    R("selectTrack(S.tracks[0].id);renderFx();pos=0;start()"); pg.wait_for_timeout(2600)
    X = J(R, "(()=>{const X=vizInst(S.tracks[0].fx[0]);return X?{node:!!X.node,tr:performance.now()-X.tr<2600,x:X.x,tbs:X.tbs}:null})()")
    ok(X and X['node'] and X['tr'] and X['tbs'].startswith('3:'), 'playing: the worklet has the 3 triggers and reports when one starts the curve', X)
    R("stop()"); pg.wait_for_timeout(300)
    # a note played live on the ghost track starts it at once
    R("(()=>{const X=vizInst(S.tracks[0].fx[0]);window.__S=[];const s0=X.send;X.send=m=>{window.__S.push(m);s0(m)};S.tracks[1].arm=true;noteOn(36,1,'t36');noteOff&&noteOff(36,'t36');S.tracks[1].arm=false;X.send=s0})()")
    ok(any('lt' in m for m in J(R, "window.__S")), 'a note played live on the ghost track starts the curve at once', J(R, "window.__S"))
    # --- 3. hits of another track's sound
    pa = dict(k4, soft=0, trig='audio', thr=-24)
    bur = [[12000, 200, .5], [12100, 200, .5], [30000, 50, .02], [36000, 300, .9]]
    g = run(R, pg, {'n': SR, 'sr': SR, 'p': pa, 'bursts': bur, 'at': [11999, 12000, 12000 + fr(.25), 12000 + fr(.5) + 2, 30010, 35999, 36000]})['at']
    ok(g[0] == 1 and g[1] == 0 and 0 < g[2] < 1 and g[3] == 1 and g[4] == 1 and g[5] == 1 and g[6] == 0, 'Start on hits: the curve starts on the sample a hit crosses -24 dB, a quiet hit (-34 dB) does not start it, the next loud hit does', g)
    # an export: a muted kick track starts the pad's curve
    R("AudioLab.build({bpm:145,tracks:[{name:'Pad',preset:'saw',clips:[{start:0,len:8,notes:[{p:45,s:0,l:8,v:.8}]}],fx:[{type:'ftvs',p:%s}]},{name:'Kick',preset:'saw',mute:true,clips:[{start:0,len:8,notes:[{p:36,s:1,l:.25,v:1},{p:36,s:2,l:.25,v:1},{p:36,s:3,l:.25,v:1}]}]}]})" % json.dumps(k4))
    pg.wait_for_timeout(400); PAD, KK = J(R, "[S.tracks[0].id,S.tracks[1].id]")
    R("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,{trig:'audio',src:%s,thr:-30,soft:0,pts:[{x:0,y:0,c:0},{x:.5,y:0,c:0},{x:.5,y:1,c:0},{x:1,y:1,c:0}]});changed(true)})()" % json.dumps(KK))
    ok(J(R, "abxKeys().has(%s)" % json.dumps(KK)), 'a render builds the muted kick track because it starts the curve')
    hw = render({'b0': 0, 'b1': 4, 'sr': SR, 'tracks': [PAD]}); R("S.tracks[0].fx[0].on=false;changed(false)"); hd = render({'b0': 0, 'b1': 4, 'sr': SR, 'tracks': [PAD]}); R("S.tracks[0].fx[0].on=true;changed(false)")
    n = min(hw['len'], hd['len']); W = floats(pg, hw, 0, 0, n); D = floats(pg, hd, 0, 0, n)
    def rms(A, a, b): return math.sqrt(sum(x * x for x in A[a:b]) / max(1, b - a))
    dips = [(rms(W, fr(k) + 2000, fr(k + .4)) / max(1e-9, rms(D, fr(k) + 2000, fr(k + .4))), rms(W, fr(k + .6), fr(k + .9)) / max(1e-9, rms(D, fr(k + .6), fr(k + .9)))) for k in (1, 2, 3)]
    pre = rms(W, fr(.3), fr(.8)) / max(1e-9, rms(D, fr(.3), fr(.8)))
    ok(all(a < .01 and abs(c - 1) < .01 for a, c in dips) and abs(pre - 1) < 1e-6, 'export: the pad is silent on each hit of the muted kick (a half-beat gate) and is back to full between them; untouched before the first hit', (dips, pre))
    R("AudioLab.free(%s);AudioLab.free(%s)" % (json.dumps(hw['id']), json.dumps(hd['id'])))
    R("selectTrack(S.tracks[0].id);renderFx()"); pg.wait_for_timeout(300)
    ok(J(R, "(()=>{const X=vizInst(S.tracks[0].fx[0]);const N=NODES.get(S.tracks[1].id);return !!X&&!!N&&X.ksrc===N.ut.out})()"), 'live: the kick’s sound after its effects and before its fader feeds the shaper’s trigger input')
    R("pos=0;start()"); pg.wait_for_timeout(2200); X = J(R, "(()=>{const X=vizInst(S.tracks[0].fx[0]);return{tr:performance.now()-X.tr<2200,kl:X.kl}})()")
    sh = os.path.join(OUT, 'f16b_audio.png'); el = pg.query_selector('.dev.nd[data-id]'); (el.screenshot(path=sh) if el else pg.screenshot(path=sh))
    R("stop()")
    ok(X['tr'], 'playing: the kick’s hits start the curve live', X)
    # a loop is refused: the kick cannot be started by a shaper on a track that plays into it
    ok(J(R, "(()=>{const me=S.tracks[0];return ftVsSrcOk(me,S.tracks[1])&&!ftVsSrcOk(me,me)})()"), 'a track cannot start its own curve')
    # --- 4. bands
    flat0 = dict(k4, pts=[{'x': 0, 'y': 0, 'c': 0}, {'x': 1, 'y': 0, 'c': 0}], depth=100, soft=0)
    GZ = [[60, 24000, 48000], [5000, 24000, 48000]]
    a = run(R, pg, {'n': SR, 'sr': SR, 'p': dict(flat0, bnd=2, x1=150, bs='100'), 'sines': [[60, .5], [5000, .5]], 'gz': GZ})['gz']
    ok(20 * math.log10(max(1e-9, a[0]) / .5) < -25 and abs(20 * math.log10(a[1] / .5)) < .05, 'two bands, Low shaped at 150 Hz: 60 Hz silenced (%.1f dB), 5 kHz passes (%.3f dB)' % (20 * math.log10(max(1e-9, a[0]) / .5), 20 * math.log10(a[1] / .5)), a)
    a = run(R, pg, {'n': SR, 'sr': SR, 'p': dict(flat0, bnd=3, x1=150, x2=2500, bs='010'), 'sines': [[60, .5], [700, .5], [8000, .5]], 'gz': [[60, 24000, 48000], [700, 24000, 48000], [8000, 24000, 48000]]})['gz']
    dd = [20 * math.log10(max(1e-9, x) / .5) for x in a]
    ok(dd[0] > -.5 and dd[1] < -30 and dd[2] > -.5, 'three bands, only Mid shaped: the mids go, lows and highs pass', dd)
    fl = []
    for f in [40, 150, 500, 2500, 6000, 12000]:
        a = run(R, pg, {'n': SR, 'sr': SR, 'p': dict(flat0, bnd=3, x1=150, x2=2500, bs='000'), 'sines': [[f, .5]], 'gz': [[f, 24000, 48000]]})['gz']; fl.append(round(20 * math.log10(a[0] / .5), 4))
    ok(all(abs(x) < .02 for x in fl), 'the crossover adds up flat with no band shaped (40 Hz to 12 kHz, worst %.4f dB)' % max(abs(x) for x in fl), fl)
    a1 = run(R, pg, {'n': 8000, 'sr': SR, 'p': dict(k4, bnd=1), 'sines': [[60, .5], [5000, .4]], 'at': list(range(0, 8000, 37))})['at']
    a3 = run(R, pg, {'n': 8000, 'sr': SR, 'p': dict(k4, bnd=3, bs='111'), 'sines': [[60, .5], [5000, .4]], 'at': list(range(0, 8000, 37))})['at']
    ok(a1 == a3, 'every band shaped is the same as the whole sound (sample for sample)')
    # --- 5. the device's second row
    R("AudioLab.build({bpm:145,tracks:[{name:'Bass',preset:'saw',clips:[{start:0,len:8,notes:[{p:45,s:0,l:8,v:.8}]}],fx:[{type:'ftvs'}]},{name:'Kick',preset:'saw',clips:[{start:0,len:8,notes:[{p:36,s:0,l:.25,v:1},{p:36,s:1,l:.25,v:1}]}]}]})")
    pg.wait_for_timeout(400); R("selectTrack(S.tracks[0].id);renderFx()"); pg.wait_for_timeout(300)
    row = J(R, "[...document.querySelectorAll('.dev.nd .ftvs2 label, .dev.nd .ftvs2 button')].map(e=>[e.textContent.trim().replace(/\\s+/g,' '),e.title||''])")
    ok(row and row[0][0].startswith('Start') and len(row) == 2, 'the device’s bar starts with Start (on the bar lines) and Bands', row)
    def setsel(k, v):
        pg.select_option('.dev.nd .ftvs2 select[data-x="%s"]' % k, str(v)); pg.wait_for_timeout(250)
    u0 = J(R, "UNDO.length"); setsel('trig', 'note')
    ok(J(R, "[S.tracks[0].fx[0].p.trig,S.tracks[0].fx[0].p.src===S.tracks[1].id]") == ['note', True] and J(R, "UNDO.length") == u0 + 1, 'Start on notes picks the Kick track by itself, one undo step')
    row = J(R, "[...document.querySelectorAll('.dev.nd .ftvs2 label, .dev.nd .ftvs2 button')].map(e=>[e.textContent.trim().replace(/\\s+/g,' '),e.title||''])")
    ok([x[0] for x in row][1:3] == ['Kick', 'Every note'], 'the row shows the track and Every note', row)
    pg.click('.dev.nd .ftvs2 [data-nact="nf"]'); pg.wait_for_timeout(200); ml = menu_labels(R)
    ok(any(x.startswith('Only') for x in ml), 'the notes menu lists the notes of the Kick track', ml); menu_click(R, 'Only'); pg.wait_for_timeout(200)
    ok(J(R, "S.tracks[0].fx[0].p.nf") == 36, 'Only one note chosen from the menu')
    pg.click('.dev.nd .ftvs2 [data-nact="src"]'); pg.wait_for_timeout(200); ml = menu_labels(R); R("closeMenu()")
    ok('Kick' in ' '.join(ml) and 'Bass' not in ' '.join(ml), 'the track menu offers the other tracks, not this one', ml)
    setsel('bnd', '3'); row = J(R, "[...document.querySelectorAll('.dev.nd .ftvs2 label, .dev.nd .ftvs2 button')].map(e=>[e.textContent.trim().replace(/\\s+/g,' '),e.title||''])")
    names = [x[0] for x in row]
    ok('Low' in names and 'Mid' in names and 'High' in names and any(x.startswith('Split') for x in names), 'three bands: Split, and, Low, Mid, High', names)
    u0 = J(R, "UNDO.length"); pg.click('.dev.nd .ftvs2 [data-nact="b1"]'); pg.wait_for_timeout(250)
    ok(J(R, "S.tracks[0].fx[0].p.bs") == '110' and J(R, "UNDO.length") == u0 + 1, 'Mid switched on: one undo step', J(R, "S.tracks[0].fx[0].p.bs"))
    row = J(R, "[...document.querySelectorAll('.dev.nd .ftvs2 label, .dev.nd .ftvs2 button')].map(e=>[e.textContent.trim(),(e.title||e.dataset.tip||'')])")
    ok(all(len(t[1]) > 15 for t in row), 'every new control has a tooltip', [t for t in row if len(t[1]) <= 15])
    txts = J(R, "[...Object.values(FTVS.TIP),...[...document.querySelectorAll('.dev.nd .ftvs2 *')].map(e=>e.textContent+(e.title||'')),ftVsCap(S.tracks[0].fx[0].p,'1/4 note')]")
    ok(all('—' not in x for x in txts), 'no em dash in the new text')
    ok('only below 150 Hz and 150 Hz to 2.5 kHz' in J(R, "ftVsCap(S.tracks[0].fx[0].p,'1/4 note')"), 'the display says what starts the curve and which bands follow it', J(R, "ftVsCap(S.tracks[0].fx[0].p,'1/4 note')"))
    setsel('trig', 'song')
    ok(J(R, "[S.tracks[0].fx[0].p.src,S.tracks[0].fx[0].p.src0===S.tracks[1].id]") == [None, True], 'back to the bar lines: the track is put aside (src0), so it is no longer kept playing')
    setsel('trig', 'audio')
    ok(J(R, "S.tracks[0].fx[0].p.src===S.tracks[1].id") and J(R, "!!document.querySelector('.dev.nd .ftvs2 select[data-x=\"thr\"]')"), 'Start on hits: the same track comes back, and a Level menu')
    R("pos=0;start()"); pg.wait_for_timeout(1500)
    el = pg.query_selector('.dev.nd[data-id]'); (el.screenshot(path=os.path.join(OUT, 'f16b_row.png')) if el else None)
    R("pmSetOn(true)"); pg.wait_for_timeout(700); el = pg.query_selector('.dev.nd[data-id]'); (el.screenshot(path=os.path.join(OUT, 'f16b_light.png')) if el else None); R("pmSetOn(false)"); R("stop()")
    j = J(R, "(()=>{const P=JSON.parse(JSON.stringify(S)).tracks[0].fx[0].p;return[P.trig,P.bnd,P.bs,!!P.src]})()")
    ok(j == ['audio', '3', '110', True], 'saved with the song', j)
    ok(not logs, 'no console errors', logs[:3])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL))); sys.exit(1 if FAIL else 0)
