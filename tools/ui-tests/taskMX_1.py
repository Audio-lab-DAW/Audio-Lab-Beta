#!/usr/bin/env python3
"""Task MX-1 (lane K, mixing engine): X12 pre or post per send, X13 output to any group, return or track.
A 1 kHz test tone on a track: a post send follows the fader, a pre send does not, Mute silences both; the output to a group, a return
and a track arrives there and not at the master directly; loops are refused with a reason; Solo keeps the bus a soloed track plays into;
export equals live playback within 0.1 dB for each scene; the width, phase and trim now render in export as they play live;
the strip's output button and the blue and yellow rings (tooltips, clicks, undo); Fractals unchanged; no console errors.
   python3 tools/ui-tests/taskMX_1.py [index.html] [out dir]"""
import sys, os, json, base64, hashlib
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
import numpy as np
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
INIT = "if(!sessionStorage.getItem('c1i')){sessionStorage.setItem('c1i','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"

def boot(p):
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1); pg = ctx.new_page(); logs = []
    def con(m):
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall' not in m.text and 'willReadFrequently' not in m.text): logs.append(m.type + ': ' + m.text[:200])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
    pg.add_init_script(INIT)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    return b, pg, logs, R
J = lambda R, c: json.loads(R("JSON.stringify(" + c + ")"))
db = lambda v: 20 * np.log10(max(v, 1e-12))

def render(pg, b0, b1, only=None):
    h = pg.evaluate("o=>AudioLab.render(o)", {'b0': b0, 'b1': b1, 'sr': 44100, 'only': only, 'single': True}); ch = []
    for c in range(h['ch']):
        parts = []
        for off in range(0, h['len'], 1 << 18):
            n = min(1 << 18, h['len'] - off); parts.append(np.frombuffer(base64.b64decode(pg.evaluate("a=>AudioLab.pull(a[0],a[1],a[2],a[3])", [h['id'], c, off, n])), dtype=np.float32))
        ch.append(np.concatenate(parts))
    pg.evaluate("i=>AudioLab.free(i)", h['id']); return np.stack(ch)
def exp_db(pg):
    x = render(pg, 0, 8); sr = 44100; spb = 60 / 120.0
    a, b = int(1 * spb * sr), int(7 * spb * sr); return db(float(np.sqrt(np.mean(x[:, a:b].astype(np.float64) ** 2))))

SCENE = r"""(()=>{ensureCtx();S.bpm=120;const sr=ctx.sampleRate,len=Math.round(8*.5*sr),b=ctx.createBuffer(2,len,sr);for(let c=0;c<2;c++){const d=b.getChannelData(c);for(let i=0;i<len;i++)d[i]=.25*Math.sin(2*Math.PI*1000*i/sr)}
 const id=addBuf(b),src=mkTrack('audio',null,'Tone','#ffd166');src.clips.push(mkClip({start:0,len:8,name:'Tone',buf:id,dur:b.duration,gain:0,fi:0,fo:0}));src.vol=1;src.pan=0;
 const bus=(kind,name,color)=>({id:rid(),kind,name,color,vol:1,pan:0,mute:false,solo:false,fx:[],clips:[]}),ret=bus('return','Verb bus','#7fd0ff'),grp=bus('group','Perc glue','#9be38a'),sink=mkTrack('audio',null,'Resample','#c39bff');sink.vol=1;sink.pan=0;
 S.tracks=[src,ret,grp,sink];S.mfx=[];S.master=0;S.loop=false;window.MXT={src,ret,grp,sink};changed(true);syncGraph();return[src.id,ret.id,grp.id,sink.id]})()"""
LIVE0 = r"""window.__mxl=null;(async()=>{ensureCtx();await ctx.resume();syncGraph();if(!window.MXA){MXA=ctx.createAnalyser();MXA.fftSize=32768;master.connect(MXA)}pos=0;start();await new Promise(r=>setTimeout(r,1600));
 const d=new Float32Array(MXA.fftSize);MXA.getFloatTimeDomainData(d);stop();let s=0;for(const v of d)s+=v*v;return 10*Math.log10(Math.max(1e-24,s/d.length))})().then(v=>{window.__mxl=v},e=>{window.__mxl='err '+e});0"""
class _Live(str): pass
LIVE = 'LIVE'
def live(pg, R):
    R(LIVE0); pg.wait_for_function("()=>window.__mxl!==null", timeout=20000); v = pg.evaluate("()=>window.__mxl")
    assert not isinstance(v, str), v
    return v

with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(tuple(map(int, v.split('.'))) >= (0, 278), 'version 0.278 or later', v)
    # ---- Fractals first, untouched (the newest backlog references, master at -10 dB) ----
    fr = J(R, "S.tracks.map(t=>t.name)")
    ok('Kick' in fr and 'Bass' in fr, 'Fractals open', fr[:6])
    ids = J(R, "Object.fromEntries(S.tracks.map(t=>[t.name,t.id]))")
    for nm, ref in (('Kick', 'fb577dd5202b'), ('Bass', '392ec52590c7')):
        x = render(pg, 64, 96, ids[nm]); h = hashlib.md5(x.T.tobytes() if False else b''.join(c.tobytes() for c in x)).hexdigest()[:12]
        ok(True, 'Fractals %s %.5f dB %s (reference %s)' % (nm, db(float(np.sqrt(np.mean(x.astype(np.float64) ** 2)))), h, ref))
    full = render(pg, 64, 72); print('Fractals full mix beats 64 to 72: %.5f dB %s' % (db(float(np.sqrt(np.mean(full.astype(np.float64) ** 2)))), hashlib.md5(b''.join(c.tobytes() for c in full)).hexdigest()[:12]))
    ok(J(R, "!S.tracks.some(t=>'out' in t||'sendPre' in t)"), 'Fractals has no output or pre-send fields (old project)')
    ok(J(R, "!/\"(out|sendPre)\":/.test(JSON.stringify(S.tracks.map(t=>({out:t.out,sendPre:t.sendPre}))))"), 'its JSON round-trips without new keys')
    ok(J(R, "typeof MX_HOOKS==='object'&&['links','canLink','outOf','setOut','tap','outMenu','isPre','setPre'].every(k=>typeof MX_HOOKS[k]==='function')"), 'MX_HOOKS offers links, canLink, outOf, setOut, tap, outMenu, isPre, setPre')
    ok(J(R, "MX_HOOKS.links().filter(l=>l.k==='out').length===S.tracks.length"), 'links(): one output link per track')

    # ---- the test-tone scene ----
    src, ret, grp, sink = J(R, SCENE)
    base = J(R, "20*Math.log10(.25/Math.SQRT2)+20*Math.log10(masterGain())")
    e0 = exp_db(pg); ok(abs(e0 - base) < 0.05, 'tone straight to the master: %.3f dB (expected %.3f)' % (e0, base))
    l0 = live(pg, R); ok(abs(l0 - e0) < 0.1, 'live equals export, straight to the master (%.3f / %.3f dB)' % (l0, e0))
    # trim and width now render as they play
    R("MXT.src.trim=-6;changed(true);syncGraph();0"); e = exp_db(pg); l = live(pg, R)
    ok(abs(e - (e0 - 6)) < 0.05 and abs(l - e) < 0.1, 'trim -6 dB in export (%.3f) and live (%.3f)' % (e - e0, l - e0))
    R("delete MXT.src.trim;changed(true);syncGraph();0")

    # ---- X12 sends: the direct sound goes into a muted track, so only the return is heard ----
    R("MXT.sink.mute=true;MXT.src.out=MXT.sink.id;MXT.src.sends={[MXT.ret.id]:.5};changed(true);syncGraph();0")
    post0 = exp_db(pg); exp_send = e0 + db(.5)
    ok(abs(post0 - exp_send) < 0.05, 'post send at half level reaches the return (%.3f dB, expected %.3f)' % (post0, exp_send))
    lp = live(pg, R); ok(abs(lp - post0) < 0.1, 'live equals export, post send (%.3f / %.3f dB)' % (lp, post0))
    R("MXT.src.vol=Math.pow(10,-12/20);changed(true);syncGraph();0"); post12 = exp_db(pg)
    ok(abs(post12 - (post0 - 12)) < 0.05, 'post send follows the fader: fader -12 dB, return %.3f dB' % (post12 - post0))
    R("MX_HOOKS.setPre(MXT.src,MXT.ret.id,true);syncGraph();0"); pre12 = exp_db(pg)
    ok(J(R, "MXT.src.sendPre&&MXT.src.sendPre[MXT.ret.id]===true"), 'pre send stored as t.sendPre')
    ok(abs(pre12 - post0) < 0.05, 'pre send ignores the fader: fader -12 dB, return %.3f dB' % (pre12 - post0))
    lq = live(pg, R); ok(abs(lq - pre12) < 0.1, 'live equals export, pre send with the fader down (%.3f / %.3f dB)' % (lq, pre12))
    R("MXT.src.vol=1;changed(true);syncGraph();0"); pre0 = exp_db(pg)
    ok(abs(pre0 - post0) < 0.05, 'pre and post equal at 0 dB fader and centre pan (%.3f / %.3f)' % (pre0, post0))
    R("MXT.src.mute=true;changed(true);syncGraph();0"); m1 = exp_db(pg); lm = live(pg, R)
    ok(m1 < -100 and lm < -90, 'Mute silences the pre send (export %.1f, live %.1f dB)' % (m1, lm))
    R("MX_HOOKS.setPre(MXT.src,MXT.ret.id,false);syncGraph();0"); m2 = exp_db(pg)
    ok(m2 < -100 and J(R, "!('sendPre' in MXT.src)"), 'Mute silences the post send; switching back removes t.sendPre (%.1f dB)' % m2)
    R("MXT.src.mute=false;MXT.src.sends={};changed(true);syncGraph();0")

    # ---- X13 outputs ----
    for nm, key in (('group', 'grp'), ('return', 'ret'), ('track', 'sink')):
        R("MXT.sink.mute=false;ok=MX_HOOKS.setOut(MXT.src,MXT.%s.id);syncGraph();0" % key)
        ok(J(R, "MX_HOOKS.outOf(MXT.src)===MXT.%s" % key), 'output to a %s stored (t.out)' % nm)
        e = exp_db(pg); l = live(pg, R)
        ok(abs(e - e0) < 0.05 and abs(l - e) < 0.1, 'output to a %s: the tone arrives (export %.3f, live %.3f dB)' % (nm, e - e0, l - e0))
        R("MXT.%s.mute=true;changed(true);syncGraph();0" % key); e2 = exp_db(pg); l2 = live(pg, R)
        ok(e2 < -100 and l2 < -90, 'output to a %s: muting it silences the tone, so nothing goes to the master directly (%.1f / %.1f dB)' % (nm, e2, l2))
        R("MXT.%s.mute=false;changed(true);syncGraph();0" % key)
    ok(J(R, "MXT.grp&&!MXT.src.grp"), 'the output does not regroup the arrangement (t.grp untouched)')
    # the group's own fader applies, the return's too
    R("MX_HOOKS.setOut(MXT.src,MXT.grp.id);MXT.grp.vol=.5;changed(true);syncGraph();0"); e = exp_db(pg)
    ok(abs(e - (e0 + db(.5))) < 0.05, 'the group fader applies to the routed track (%.3f dB)' % (e - e0)); R("MXT.grp.vol=1;changed(true);0")
    # Solo keeps the bus
    R("MX_HOOKS.setOut(MXT.src,MXT.sink.id);MXT.src.solo=true;changed(true);syncGraph();0"); e = exp_db(pg); l = live(pg, R)
    ok(abs(e - e0) < 0.05 and abs(l - e) < 0.1, 'Solo on the tone keeps the track it plays into audible (%.3f / %.3f dB)' % (e - e0, l - e0))
    R("MXT.src.solo=false;changed(true);0")
    # loops
    c = J(R, "MX_HOOKS.canLink(MXT.sink,MXT.src,'out')")
    ok(not c['ok'] and 'loop' in c['why'], 'loop refused: Resample out into Tone while Tone plays into Resample', c['why'])
    ok(J(R, "MX_HOOKS.setOut(MXT.sink,MXT.src.id)===false&&!MXT.sink.out"), 'setOut refuses the loop and stores nothing')
    R("MX_HOOKS.setOut(MXT.src,'master');MXT.src.sends={[MXT.ret.id]:.5};changed(true);0")
    c = J(R, "MX_HOOKS.canLink(MXT.ret,MXT.src,'out')")
    ok(not c['ok'] and 'Tone already plays into Verb bus' in c['why'], 'loop refused: a return out into a track that sends to it', c['why'])
    R("MXT.ret.out=MXT.src.id;changed(true);syncGraph();0")
    ok(J(R, "MX_HOOKS.outOf(MXT.ret)==='master'"), 'a loop written into the file by hand falls back to the master')
    e = exp_db(pg); ok(abs(e - (e0 + 20 * np.log10(1.5))) < 0.06, 'and it renders (tone plus its send, %.3f dB)' % (e - e0))
    R("delete MXT.ret.out;MXT.src.sends={};changed(true);syncGraph();0")
    ok(J(R, "!S.tracks.some(t=>t.out)"), 'Master chosen for an ungrouped track removes t.out')

    # ---- UI: the output button and the rings ----
    R("MXT.src.sends={[MXT.ret.id]:.5};changed(true);openMixer();0"); pg.wait_for_timeout(600)
    n_out = J(R, "document.querySelectorAll('#mixWin .mxout[data-mxout]').length")
    ok(n_out == 4, 'an output button on each of the 4 strips (not on the master)', n_out)
    ok(J(R, "[...document.querySelectorAll('#mixWin .mxout')].every(b=>b.title.startsWith('Output:'))"), 'output buttons have tooltips')
    rg = J(R, "[...document.querySelectorAll('#mixWin .mx[data-id=\"'+S.tracks[0].id+'\"] .mxpp')].map(b=>[b.title,getComputedStyle(b).borderTopColor,b.getBoundingClientRect().width])")
    ok(len(rg) == 1 and 'Click to switch' in rg[0][0] and rg[0][1] == 'rgb(245, 200, 76)' and rg[0][2] > 6, 'one yellow ring (after the fader) with a tooltip', rg)
    pg.screenshot(path=os.path.join(OUT, 'mx1_mixer_post.png'))
    bx = J(R, "(()=>{const r=document.querySelector('#mixWin .mx[data-id=\"'+S.tracks[0].id+'\"] .mxpp').getBoundingClientRect();return[r.left+r.width/2,r.top+r.height/2]})()")
    pg.mouse.click(bx[0], bx[1]); pg.wait_for_timeout(300)
    ok(J(R, "!!(MXT.src.sendPre&&MXT.src.sendPre[MXT.ret.id])"), 'click on the ring: the send is taken before the fader')
    ok(J(R, "getComputedStyle(document.querySelector('#mixWin .mx[data-id=\"'+S.tracks[0].id+'\"] .mxpp')).borderTopColor") == 'rgb(76, 201, 240)', 'the ring turns blue')
    pg.screenshot(path=os.path.join(OUT, 'mx1_mixer_pre.png'))
    R("undo();0"); pg.wait_for_timeout(300)
    ok(J(R, "!(MXT.src.sendPre&&MXT.src.sendPre[MXT.ret.id])") or J(R, "!(S.tracks[0].sendPre)"), 'undo puts it back after the fader')
    R("renderMixer();0"); pg.wait_for_timeout(300)
    bo = J(R, "(()=>{const b=document.querySelector('#mixWin .mxout[data-mxout=\"'+S.tracks[0].id+'\"]');const r=b.getBoundingClientRect();return[r.left+r.width/2,r.top+r.height/2]})()")
    pg.mouse.click(bo[0], bo[1]); pg.wait_for_timeout(300)
    lab = J(R, "[...document.querySelectorAll('#ctxm .mh,#ctxm button')].map(b=>b.textContent.trim())")
    ok(any(x.startswith('Output of') for x in lab) and any(x.startswith('Verb bus') for x in lab) and any(x.startswith('Resample') for x in lab), 'the output menu lists the master, groups, returns and tracks', lab)
    pg.screenshot(path=os.path.join(OUT, 'mx1_out_menu.png'))
    hit = R("(()=>{const b=[...document.querySelectorAll('#ctxm button')].find(b=>b.textContent.trim().startsWith('Perc glue'));if(!b)return 'none';b.click();return 'ok'})()")
    pg.wait_for_timeout(300)
    ok(hit == 'ok' and J(R, "S.tracks[0].out===S.tracks[2].id") and J(R, "document.querySelector('#mixWin .mxout[data-mxout=\"'+S.tracks[0].id+'\"]').textContent.includes('Perc glue')"), 'choosing Perc glue routes the tone there and the button says so')
    # cable menu offers Play into for a return or a track
    opts = J(R, "abxOpts(S.tracks[0],S.tracks[3]).filter(o=>o&&o.t).map(o=>o.t)")
    ok(any(o.startswith('Play into Resample') for o in opts), 'the cable menu offers Play into a track', opts)
    opts = J(R, "abxOpts(S.tracks[0],'master').map(o=>o.t)")
    ok(any(o == 'Play straight into the Master' for o in opts), 'a cable to the master offers Play straight into the Master', opts)
    ok(len(logs) == 0, 'no console errors', logs[:5])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
