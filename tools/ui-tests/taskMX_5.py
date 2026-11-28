#!/usr/bin/env python3
"""Task MX-5 (lane K, mixing engine): Dual Path Latency.
Off by default (nothing changes, a played track waits for its devices as before); turned on in Settings, Audio. Measured live with an impulse:
the same impulse goes straight into the master on the left and into a played (armed) instrument track on the right, delay compensation off
so only the track's own devices count. With a 5 ms Limiter and a Drive at 50 % Mix: off, the impulse arrives after both devices; on, the dry
part arrives at once (the Limiter's 1-sample stand-in) and Drive's wet part 192 samples later; a track you do not play stays exact. A Gate with
look-ahead and an oversampled Soft Clipper get their stand-ins too. f.p is never changed. Exports never see it: Fractals Kick and Bass at the
references with Dual Path Latency on and the Lead armed. Settings: the card, the tag "AudioLab Pro Technology" with the atom mark next to the
name, the switch's stable id, the row's stable name (XT_SET_NS, docs/settings-ids.md), the first-use card once, never the word "original";
the About section; the command (docs/commands.md); laid out in Dark and Light; no em dash; no work on clicks while it is off; no console errors.
   python3 tools/ui-tests/taskMX_5.py [index.html] [out dir]"""
# for: task MX-5 (lane K)
import sys, os, json, re
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
os.makedirs(OUT, exist_ok=True)
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)[:300]) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)
INIT = "if(!sessionStorage.getItem('c5i')){sessionStorage.setItem('c5i','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
REFS = {'Kick': -19.05560, 'Bass': -35.48685}

# the impulse scene: one armed instrument track; the result is [first arrival, largest peak] in samples after the left impulse, per impulse
SCENE = r"""(fx,arm)=>{ensureCtx();const k=Object.keys(PRESETS)[0],t=mkTrack('inst',k,'Played','#ffd166');t.vol=1;t.pan=0;t.arm=!!arm;t.clips=[];t.fx=fx.map(([ty,p])=>{const f=mkFx(ty);Object.assign(f.p,p);return f});
 S.tracks=[t];S.mfx=[];S.master=0;S.loop=false;S.pauto={};UI.pdc=false;UI.kbPiano=false;window.M5={t};changed(true);syncGraph();return ctx.sampleRate}"""
MEAS = r"""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));ensureCtx();await ctx.resume();syncGraph();await w(250);const sr=ctx.sampleRate,N=NODES.get(M5.t.id);
 const sp=ctx.createScriptProcessor(4096,2,2),L=[],R=[];sp.onaudioprocess=e=>{L.push(e.inputBuffer.getChannelData(0).slice());R.push(e.inputBuffer.getChannelData(1).slice())};master.connect(sp);sp.connect(ctx.destination);
 const mk=ch=>{const b=ctx.createBuffer(2,sr,sr);for(let k=0;k<3;k++)b.getChannelData(ch)[Math.round((.15+.25*k)*sr)]=.1;return b};
 const a=ctx.createBufferSource(),b=ctx.createBufferSource();a.buffer=mk(0);b.buffer=mk(1);a.connect(master);b.connect(N.in);await w(120);const t0=ctx.currentTime+.15;a.start(t0);b.start(t0);
 await w(1500);try{master.disconnect(sp)}catch(e){}sp.disconnect();a.disconnect();b.disconnect();
 const n=L.reduce((s,x)=>s+x.length,0),l=new Float32Array(n),r=new Float32Array(n);let o=0;for(let i=0;i<L.length;i++){l.set(L[i],o);r.set(R[i],o);o+=L[i].length}
 const out=[];for(let i=0;i<n;i++){if(Math.abs(l[i])>.05){let first=-1,best=-1,bv=0;for(let j=Math.max(0,i-4);j<Math.min(n,i+3000);j++){const v=Math.abs(r[j]);if(first<0&&v>.004)first=j-i;if(v>bv){bv=v;best=j-i}}out.push([first,best]);i+=2000}}
 return JSON.stringify({sr,out})})()"""

def boot(p):
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1); pg = ctx.new_page(); logs = []
    def con(m):
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall' not in m.text and 'willReadFrequently' not in m.text and 'ScriptProcessorNode' not in m.text): logs.append(m.text[:300])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    return b, pg, logs, R
J = lambda R, c: json.loads(R("JSON.stringify(" + c + ")"))

def meas(pg, R, fx, arm, on):
    R("(()=>{%s;return(%s)(%s,%s)})()" % ("UI.mxDpl=true" if on else "delete UI.mxDpl", SCENE, json.dumps(fx), 'true' if arm else 'false'))
    R("window.__m5=null;" + MEAS + ".then(v=>{window.__m5=v},e=>{window.__m5=JSON.stringify({err:String(e)})});0")
    pg.wait_for_function("()=>window.__m5!==null", timeout=30000)
    r = json.loads(pg.evaluate("()=>window.__m5")); assert 'err' not in r, r
    return r
near = lambda a, b, n: abs(a - b) <= n

with sync_playwright() as p:
    b, pg, logs, R = boot(p)
    v = R("VERSION"); ok(all(k in SRC for k in ('task MX-2 (lane K', 'task MX-3 (lane K', 'task MX-4 (lane K', 'task MX-5 (lane K')), 'MX-2, MX-3, MX-4 and MX-5 are in the file', v)
    # ---- off by default, the settings row ----
    ok(J(R, "UI.mxDpl!==true"), 'Dual Path Latency is off on a fresh start')
    ok(J(R, "STX.has('mxDpl')&&STX.get('mxDpl').t==='check'&&STX.get('mxDpl').c==='#mxDplChk'&&STX.get('mxDpl').d===false"), 'the Settings row exists (check box, off by default)')
    ok(J(R, "XT_SET_NS.mxDpl==='audio.dualPath'"), 'its stable name is audio.dualPath (XT_SET_NS)')
    ids_md = open(os.path.join(HERE, '..', '..', 'docs', 'settings-ids.md'), encoding='utf-8').read()
    cmd_md = open(os.path.join(HERE, '..', '..', 'docs', 'commands.md'), encoding='utf-8').read()
    ok('| `audio.dualPath` |' in ids_md, 'docs/settings-ids.md has the row audio.dualPath')
    ok(J(R, "SCM.has('mx.dualPath')") and '| `mx.dualPath` |' in cmd_md, 'the command mx.dualPath exists and has its line in docs/commands.md')
    # ---- Fractals with it on and the Lead armed: exports unchanged ----
    R("(()=>{UI.mxDpl=true;const l=S.tracks.find(t=>t.name==='Lead');if(l)l.arm=true;S.master=-10;changed(true);syncGraph();return 1})()")
    ids = J(R, "Object.fromEntries(S.tracks.map(t=>[t.name,t.id]))")
    for nm in ('Kick', 'Bass'):
        h = pg.evaluate("o=>AudioLab.render(o)", {'b0': 64, 'b1': 96, 'sr': 44100, 'only': ids[nm], 'single': True})
        import base64, numpy as np, hashlib
        ch = []
        for c in range(h['ch']):
            parts = []
            for off in range(0, h['len'], 1 << 18):
                n = min(1 << 18, h['len'] - off); parts.append(np.frombuffer(base64.b64decode(pg.evaluate("a=>AudioLab.pull(a[0],a[1],a[2],a[3])", [h['id'], c, off, n])), dtype=np.float32))
            ch.append(np.concatenate(parts))
        pg.evaluate("i=>AudioLab.free(i)", h['id']); x = np.stack(ch)
        lv = 20 * np.log10(max(float(np.sqrt(np.mean(x.astype(np.float64) ** 2))), 1e-12)); hs = hashlib.md5(b''.join(c.tobytes() for c in x)).hexdigest()[:12]
        ok(abs(lv - REFS[nm]) < .00001, 'export with Dual Path Latency on and the Lead armed: Fractals %s %.5f dB %s (reference %.5f)' % (nm, lv, hs, REFS[nm]))
    R("(()=>{delete UI.mxDpl;for(const t of S.tracks)t.arm=false;changed(true);syncGraph();return 1})()")

    # ---- live, with an impulse ----
    LIM_DRV = [['limit', {'look': 5}], ['drive', {'mix': 50}]]
    a = meas(pg, R, LIM_DRV, True, False); sr = a['sr']; L5 = max(1, int(5 * sr / 1000 + .5)); exp_off = L5 + 192  # as the worklet rounds (Math.round)
    print('live sample rate', sr, 'off:', a['out'])
    ok(len(a['out']) == 3 and all(exp_off - 40 <= o[0] <= exp_off and near(o[1], exp_off, 3) for o in a['out']), 'off (the default): the played track waits for its Limiter (5 ms, %d samples) and Drive (192): impulse after %d samples' % (L5, exp_off), a['out'])
    ok(J(R, "!NODES.get(M5.t.id).mxDS"), 'off: no extra nodes are built')
    c = meas(pg, R, LIM_DRV, True, True); print('on:', c['out'])
    ok(len(c['out']) == 3 and all(0 <= o[0] <= 2 for o in c['out']), 'on: the dry part arrives at once (%s samples: the Limiter\'s stand-in is 1 sample)' % [o[0] for o in c['out']], c['out'])
    ok(len(c['out']) == 3 and all(abs(o[1] - (o[0] + 192)) <= 3 or o[1] <= 2 for o in c['out']), 'on: the wet part of Drive joins 192 samples later (largest peaks %s)' % [o[1] for o in c['out']], c['out'])
    late = J(R, r"""(()=>{const w=[];const N=NODES.get(M5.t.id),D=N.mxDS&&N.mxDS.get(M5.t.fx[1].id);return D?[+D.dg.gain.value.toFixed(3),+D.wg.gain.value.toFixed(3)]:null})()""")
    ok(late == [0.5, 0.5], 'on: the two paths follow Mix 50 %% (dry %s, wet %s)' % tuple(late or [None, None]))
    R("(()=>{const f=M5.t.fx[1];f.p.mix=20;NODES.get(M5.t.id).fxm.get(f.id).set(f.p);return 1})()"); pg.wait_for_timeout(150)
    g2 = J(R, "(()=>{const D=NODES.get(M5.t.id).mxDS.get(M5.t.fx[1].id);return[+D.dg.gain.value.toFixed(2),+D.wg.gain.value.toFixed(2)]})()")
    ok(g2 == [0.8, 0.2], 'turning the Mix knob moves the two paths at once (Mix 20 %%: dry %s, wet %s)' % tuple(g2))
    ok(J(R, "M5.t.fx[0].p.look===5&&M5.t.fx[1].p.mix===20"), 'the devices\' own settings are never changed (Limiter look-ahead still 5 ms)')
    ok(J(R, "MX_HOOKS.dpl&&MX_HOOKS.dpl.on(M5.t)&&MX_HOOKS.dpl.lat(M5.t)===1"), 'MX_HOOKS.dpl: on for the played track, 1 sample while playing')
    d = meas(pg, R, LIM_DRV, False, True); print('on, not played:', d['out'])
    ok(len(d['out']) == 3 and all(exp_off - 40 <= o[0] <= exp_off and near(o[1], exp_off, 3) for o in d['out']), 'on, a track you do not play: the exact version (%d samples)' % exp_off, d['out'])
    GC = [['gate', {'look': 10, 'thr': -80, 'floor': 0}], ['clip', {}]]
    e = meas(pg, R, GC, True, False); f2 = meas(pg, R, GC, True, True); print('gate and clipper off', e['out'], 'on', f2['out'])
    G10 = int(10 * sr / 1000 + .5)
    ok(len(e['out']) == 3 and all(near(o[0], G10 + 192, 8) and near(o[1], G10 + 192, 3) for o in e['out']), 'off: a Gate with 10 ms look-ahead and an oversampled Soft Clipper delay by %d samples' % (G10 + 192), e['out'])
    ok(len(f2['out']) == 3 and all(0 <= o[0] <= 1 for o in f2['out']), 'on: both run their stand-ins, the sound arrives at once (%s)' % [o[0] for o in f2['out']], f2['out'])
    # ---- no work while it is off ----
    J(R, "(()=>{window.__sgN=0;const g=syncGraph;window.__sgO=g;syncGraph=function(){__sgN++;return g.apply(this,arguments)};delete UI.mxDpl;clearTimeout(mxDplEval.t);mxDplEval.t=undefined;mxDplEval();return 1})()")
    pg.wait_for_timeout(400)
    ok(J(R, "(()=>{const n=__sgN,t=mxDplEval.t;syncGraph=__sgO;return n===0&&t===undefined})()"), 'off: a click or a key does no work for it (no timer, no syncGraph)')
    # ---- Settings, Audio ----
    R("(()=>{delete UI.mxDpl;delete UI.mxDplSeen;S.tracks.forEach(t=>t.arm=false);openSettings('audio');return 1})()"); pg.wait_for_timeout(900)
    R("(()=>{try{ST5.show('audio')}catch(e){}return 1})()"); pg.wait_for_timeout(400)
    card = J(R, r"""(()=>{const c=document.getElementById('mxDplCard');if(!c)return null;const h=c.querySelector('h4'),t=c.querySelector('.mxtag'),k=document.getElementById('mxDplChk');
     const hr=h.getBoundingClientRect(),tr=t.getBoundingClientRect(),cr=c.getBoundingClientRect(),kr=k.closest('label').getBoundingClientRect();
     return{tag:t.textContent,atom:!!t.querySelector('svg.mxatom'),tip:t.title,h:h.textContent,al:k.dataset.al,ktip:k.closest('label').title,hidden:document.getElementById('mxDplFirst').hidden,
      inH:tr.top>=hr.top-1&&tr.bottom<=hr.bottom+1&&tr.left>=hr.left,inC:cr.width>200&&kr.right<=cr.right+1&&tr.right<=cr.right+1,vis:cr.height>20&&getComputedStyle(c).display!=='none',
      tcol:getComputedStyle(t).color,hcol:getComputedStyle(h).color,tq:[parseFloat(getComputedStyle(t).fontSize),parseFloat(getComputedStyle(h).fontSize),+getComputedStyle(t).opacity],page:c.closest('section')&&c.closest('section').dataset.page}})()""")
    print('card', card)
    ok(card is not None and card['vis'] and card['page'] == 'audio', 'Settings, Audio has the Dual Path Latency card')
    ok(card and card['tag'] == 'AudioLab Pro Technology' and card['atom'], 'the tag reads "AudioLab Pro Technology" with the atom mark', card and card['tag'])
    ok(card and card['inH'] and card['inC'], 'layout: the tag sits on the heading line next to the name, everything inside the card')
    ok(card and card['tq'][0] < card['tq'][1] and card['tq'][2] < 1, 'the tag is small and grey, quieter than the heading (%s px against %s px, opacity %s, colour %s)' % (card['tq'][0], card['tq'][1], card['tq'][2], card['tcol']))
    ok(card and card['tip'].startswith('AudioLab Pro Technology. Other DAWs turn slow devices off') and len(card['ktip']) > 40, 'tooltips on the tag and the switch')
    ok(card and card['al'] == 'settings.dualPath', 'the switch has a stable id (data-al settings.dualPath)')
    ok(card and card['hidden'], 'the first-use card is not shown before it is turned on')
    el = pg.query_selector('#mxDplCard')
    if el: el.screenshot(path=os.path.join(OUT, 'mx5_card_dark.png'))
    pg.click('#mxDplChk'); pg.wait_for_timeout(300)
    st = J(R, "[UI.mxDpl===true,!document.getElementById('mxDplFirst').hidden,UI.mxDplSeen===1,document.getElementById('mxDplLine').textContent]")
    ok(st[0] and st[1] and st[2], 'turning it on shows the first-use card once', st)
    fr = J(R, r"""(()=>{const f=document.getElementById('mxDplFirst'),c=document.getElementById('mxDplCard'),p=f.querySelector('svg.mxdplpic'),a=f.getBoundingClientRect(),b=c.getBoundingClientRect(),q=p.getBoundingClientRect();return{t:f.textContent,inC:a.left>=b.left&&a.right<=b.right+1,pic:q.width>100&&q.height>20&&q.right<=a.right+1}})()""")
    ok(fr['inC'] and fr['pic'], 'layout: the first-use card and its drawing fit inside the card', fr)
    ok('Other DAWs turn slow devices off to cut latency; Dual Path Latency keeps them and brings them back in sync.' in fr['t'], 'the first-use card says the user\'s line')
    if el: el.screenshot(path=os.path.join(OUT, 'mx5_card_first_dark.png'))
    # Dark (the plain level) and Light (the Light glass level, UI.fx): the tag keeps its place and stays readable
    R("(()=>{window.__fx0=UI.fx;UI.fx=fxPre('light');applyTrans();return 1})()"); pg.wait_for_timeout(700)
    if el: el.screenshot(path=os.path.join(OUT, 'mx5_card_first_light.png'))
    lt = J(R, r"""(()=>{const t=document.querySelector('#mxDplCard .mxtag'),h=document.querySelector('#mxDplCard h4'),tr=t.getBoundingClientRect(),hr=h.getBoundingClientRect(),s=getComputedStyle(t);return{col:s.color,op:+s.opacity,w:tr.width,inH:tr.top>=hr.top-1&&tr.bottom<=hr.bottom+1,lv:fxLevel()}})()""")
    ok(lt['inH'] and lt['w'] > 60 and 0.5 < lt['op'] < 1, 'Light level: the tag keeps its place on the heading line, grey and readable (%s, opacity %s, level %s)' % (lt['col'], lt['op'], lt['lv']))
    R("(()=>{UI.fx=window.__fx0;applyTrans();return 1})()"); pg.wait_for_timeout(300)
    pg.click('#mxDplOk'); pg.wait_for_timeout(150); pg.click('#mxDplChk'); pg.wait_for_timeout(150); pg.click('#mxDplChk'); pg.wait_for_timeout(200)
    ok(J(R, "UI.mxDpl===true&&document.getElementById('mxDplFirst').hidden"), 'Got it hides it, and it does not come back the next time')
    pg.click('#mxDplChk'); pg.wait_for_timeout(150)
    ok(J(R, "UI.mxDpl!==true"), 'the switch turns it off again')
    # ---- About ----
    ab = J(R, "ahfHtml()")
    ok('AudioLab Pro Technology' in ab and 'Dual Path Latency' in ab and 'Designed by Ilja V. Jakovliev' in ab and ab.index('mxAbout') < ab.index('Under the hood'), 'About: an "AudioLab Pro Technology" section lists Dual Path Latency, designed by Ilja V. Jakovliev')
    # ---- words ----
    blk = SRC[SRC.index('/* ===== task MX-5 (lane K'):SRC.index('/* ===== end of task MX-5 =====')]
    ui = ' '.join(re.findall(r"'([^'\\]*(?:\\.[^'\\]*)*)'", blk))
    ok('original' not in ui.lower(), 'never the word "original" in MX-5\'s text')
    ok('—' not in blk, 'no em dash in MX-5\'s text')
    ok(not logs, 'no console errors', logs[:5])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
for m in FAIL: print('  FAILED:', m)
sys.exit(1 if FAIL else 0)
