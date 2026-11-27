#!/usr/bin/env python3
"""Task FT-F16a (volume shaper, part 1): the device and its presets, a point at 1/16 lands on the sample at 145 BPM in the worklet and in an export
(the export equals the dry track times the curve), tempo changes and loop jumps, the display with the signal of the last cycle, editing
the curve (snap, buttons, undo), saved with the song, nothing reported while silent, older songs untouched.
   python3 tools/ui-tests/taskFT_F16a.py [index.html] [out dir]"""
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

def boot(p, refuse=False, dsf=1):
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=dsf); pg = ctx.new_page(); logs = []
    def con(m):
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall' not in m.text and 'willReadFrequently' not in m.text): logs.append(m.type + ': ' + m.text[:200])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
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
with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 289), 'version 0.289 or later', v)
    ok(J(R, "!!FXDEF.ftvs&&FXDEF.ftvs.name==='Volume Shaper'&&FBG.some(g=>g[2].includes('ftvs'))"), 'the Volume Shaper is a device in the Modulation group of the browser')
    ok(J(R, "Object.keys(FXPRE.ftvs).length") >= 12, 'presets: Kickstart-style ducks, LFOTool-style gates, swells', J(R, "Object.values(FXPRE.ftvs).map(x=>x[0])"))
    ok(J(R, "S.tracks.every(t=>t.fx.every(f=>f.type!=='ftvs'))"), 'Fractals has no volume shaper (older songs untouched)')
    R("S.bpm=145;S.tempo=[];TMC=null")
    sr = 48000
    roll = J(R, "Object.assign({},FXPRE.ftvs.kroll[1],{soft:0})")
    res = ARUN(R, pg, "(" + DIRECT + ")(" + json.dumps({'n': sr, 'sr': sr, 'p': roll, 'at': [0, 4965, 4966, 19862, 19863, 24827, 24828]}) + ")")
    exp = int(-(-(.25 * 60 / 145 * sr) // 1))
    ok(res['first'] == exp == 4966, 'a point at 1/16 lands on the sample at 145 BPM (frame %d at 48 kHz)' % exp, res)
    ok(res['at'] == [0, 0, 1, 1, 0, 0, 1], 'silent before it, full after it; the next beat’s gap starts and ends on its sample too', res['at'])
    res = ARUN(R, pg, "(" + DIRECT + ")(" + json.dumps({'n': sr, 'sr': 44100, 'p': roll, 'at': [0], 'b0': 0}) + ")")
    ok(res['first'] == int(-(-(.25 * 60 / 145 * 44100) // 1)), 'and at 44.1 kHz', res['first'])
    r2 = ARUN(R, pg, "(" + DIRECT + ")(" + json.dumps({'n': sr, 'sr': sr, 'p': roll, 'at': [0], 'b0': .125}) + ")")
    ok(r2['first'] == int(-(-(.125 * 60 / 145 * sr) // 1)), 'a render that starts at another beat keeps the curve on the song’s grid', r2['first'])
    # tempo map: a jump to 120 BPM at beat 1: the step of beat 1 (at 1.25) lands where the map puts it
    want = int(-(-((.5 * 60 / 145 + .25 * 60 / 120) * sr) // 1))
    r3b = ARUN(R, pg, """(async()=>{S.tempo=[{b:1,bpm:120}];TMC=null;const c=new OfflineAudioContext(1,%d,%d),s=c.createConstantSource();SIDE_B0=.5;const X=ftVsNode(c);X.set(%s);s.connect(X.in);X.out.connect(c.destination);s.start(0);const d=(await c.startRendering()).getChannelData(0);SIDE_B0=0;S.tempo=[];TMC=null;let k=-1;for(let i=1;i<d.length;i++)if(d[i]>.5&&d[i-1]<.5&&i>100){k=i;break}return k})()""" % (sr, sr, json.dumps(roll)))
    ok(r3b == want, 'a tempo change: the step after it lands where the tempo map puts it', (r3b, want))
    # smoothing: no step, a short ramp starting on the same sample
    sm = J(R, "Object.assign({},FXPRE.ftvs.kroll[1],{soft:1})")
    r4 = ARUN(R, pg, "(" + DIRECT + ")(" + json.dumps({'n': sr, 'sr': sr, 'p': sm, 'at': [4965, 4966, 4967, 4966 + 48, 4966 + 300]}) + ")")
    ok(r4['at'][0] == 0 and 0 < r4['at'][1] < .1 and r4['at'][2] > r4['at'][1] and .55 < r4['at'][3] < .7 and r4['at'][4] > .99, 'Smooth 1 ms: the rise starts on the same sample and is 63 % there after 1 ms', r4['at'])
    # an export: the shaped track equals the dry track times the curve
    R("AudioLab.build({bpm:145,tracks:[{name:'Bass',preset:'saw',clips:[{start:0,len:8,notes:[{p:45,s:0,l:8,v:.8}]}],fx:[{type:'ftvs',p:%s}]}]})" % json.dumps(J(R, "Object.assign({},FXPRE.ftvs.k4[1])")))
    pg.wait_for_timeout(500); TID = J(R, "S.tracks[0].id")
    def render(b0, b1):
        h = pg.evaluate("o=>AudioLab.render(o)", {'b0': b0, 'b1': b1, 'sr': 48000, 'only': TID}); return h
    hw = render(0, 4); R("S.tracks[0].fx[0].on=false;changed(false)"); hd = render(0, 4); R("S.tracks[0].fx[0].on=true;changed(false)")
    n = min(hw['len'], hd['len'], 48000 * 2)
    W = floats(pg, hw, 0, 0, n); D = floats(pg, hd, 0, 0, n)
    pp = J(R, "S.tracks[0].fx[0].p")
    G = J(R, "(()=>{const p=S.tracks[0].fx[0].p,o=[];for(let i=0;i<%d;i+=7)o.push(FT_HOOKS.volumeShaper.gainAt(p,i/48000*145/60));return o})()" % n)
    errs = []; 
    import math
    ga = None
    for k, i in enumerate(range(0, n, 7)):
        if abs(D[i]) > .02: errs.append(abs(W[i] - D[i] * G[k]))
    worst = max(errs) if errs else 9
    ok(len(errs) > 500 and worst < 0.02, 'export: the shaped track is the dry track times the curve at the song’s beat (%d samples checked, worst %.4f)' % (len(errs), worst))
    # the dip on every beat in the export
    def rms(a, b): return math.sqrt(sum(x * x for x in W[a:b]) / max(1, b - a))
    spb = int(60 / 145 * 48000)
    ok(all(rms(k * spb, k * spb + 400) < .3 * rms(k * spb + spb // 2, k * spb + spb // 2 + 400) for k in range(3)), 'the export dips on every beat')
    R("AudioLab.free(%s);AudioLab.free(%s)" % (json.dumps(hw['id']), json.dumps(hd['id'])))
    # live: the display gets the last cycle while playing, nothing while silent
    R("selectTrack(S.tracks[0].id);renderFx()"); pg.wait_for_timeout(300)
    ok(J(R, "!!document.querySelector('.dev.nd[data-id]')"), 'the device shows in the devices panel')
    R("start()"); pg.wait_for_timeout(1600)
    X = J(R, "(()=>{const X=vizInst(S.tracks[0].fx[0]);return X?{node:!!X.node,bin:!!X.bin,n:X.bin?X.bin.length:0,fresh:performance.now()-X.tm<500}:null})()")
    ok(X and X['node'] and X['bin'] and X['n'] == 192 and X['fresh'], 'playing: the worklet runs and sends the last cycle’s levels', X)
    sh = os.path.join(OUT, 'f16a_play.png')
    el = pg.query_selector('.dev.nd[data-id]'); (el.screenshot(path=sh) if el else pg.screenshot(path=sh))
    R("stop()"); pg.wait_for_timeout(1500); t0 = J(R, "vizInst(S.tracks[0].fx[0]).tm"); pg.wait_for_timeout(800)
    ok(J(R, "vizInst(S.tracks[0].fx[0]).tm") == t0, 'stopped and silent: the worklet sends nothing')
    # loop jump: the anchor moves with it
    R("(()=>{const f=S.tracks[0].fx[0];f.p.cyc='2';ftVsApply(f);S.loop=true;S.loopRange={a:0,b:4};pos=0})()")
    la = J(R, "[loopA(),loopB()]")
    R("start()"); pg.wait_for_timeout(2400)
    lp = J(R, "(()=>{const X=vizInst(S.tracks[0].fx[0]);return[X.x,curDisp(),play.wrapped]})()"); R("stop();S.loop=false")
    ok(la == [0, 4] and lp[2] and abs(lp[0] - lp[1] / 8) < .04, 'a loop jump: the curve follows the song back to the loop start (phase %.3f, song beat %.2f of a 2-bar cycle)' % (lp[0], lp[1]), (la, lp))
    # editing: buttons with tooltips, undo
    tb = J(R, "[...document.querySelectorAll('.dev.nd .ndtb button, .dev.nd .ndtb label')].map(e=>[e.textContent.trim(),e.title||''])")
    ok(len(tb) >= 9 and all(len(t[1]) > 8 for t in tb), 'every button and menu of the device has a tooltip', tb)
    u0 = J(R, "UNDO.length"); n0 = J(R, "S.tracks[0].fx[0].p.pts.length")
    R("NACT.ftvs.add(S.tracks[0].fx[0],S.tracks[0])"); ok(J(R, "S.tracks[0].fx[0].p.pts.length") == n0 + 1 and J(R, "UNDO.length") == u0 + 1, 'Add point: one more point, one undo step')
    R("NACT.ftvs.flat(S.tracks[0].fx[0],S.tracks[0])"); ok(J(R, "S.tracks[0].fx[0].p.pts.every(q=>q.y===1)"), 'Flat: the sound passes unchanged')
    R("undo()"); ok(J(R, "S.tracks[0].fx[0].p.pts.length") == n0 + 1, 'undo')
    # snap: a dragged point lands on the song's 16ths
    hx = J(R, "(()=>{const f=S.tracks[0].fx[0];f.p.cyc='1';const H=HND.ftvs(f.p,560,200);const h=H.find(x=>x.l==='Point 2');h.drag(8+.33*544,100);return f.p.pts[1].x})()")
    ok(abs(hx / (1 / 16) - round(hx / (1 / 16))) < 1e-9, 'snap 1/16: a dragged point lands on a 16th of the bar', hx)
    # saved and loaded with the song
    j = J(R, "(()=>{const P=JSON.parse(JSON.stringify(S));return P.tracks[0].fx[0].type==='ftvs'&&Array.isArray(P.tracks[0].fx[0].p.pts)})()"); ok(j, 'saved with the song')
    # preset choice through the device's preset list
    ok(all('—' not in x for x in J(R, "[FXDESC.ftvs,vizHelp.ftvs,...Object.values(FXPRE.ftvs).map(x=>x[0]),...FXBTN.ftvs.map(b=>b[2]),FTVS.TIP.cyc,FTVS.TIP.snap]")), 'no em dash in the new text')
    R("pmSetOn(true)"); pg.wait_for_timeout(600); el = pg.query_selector('.dev.nd[data-id]'); (el.screenshot(path=os.path.join(OUT, 'f16a_light.png')) if el else None); R("pmSetOn(false)")
    ok(not logs, 'no console errors', logs[:3])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL))); sys.exit(1 if FAIL else 0)
