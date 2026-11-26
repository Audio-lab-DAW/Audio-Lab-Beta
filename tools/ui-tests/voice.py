"""Voice (v0.200, task Z): the voice changer with note editing, measured in the real app.
  python3 tools/ui-tests/voice.py [index.html] [out dir]
Makes sung notes with known pitches (one with vibrato, one glide) and a spoken-like phrase, puts them on an audio track with Voice,
finds the notes, moves them, corrects them, renders through the app's engine and measures the pitch with an FFT method that is
independent of the tracker. Also: live engine in exports (hard tune, choir), bit-identical renders, pop chain, the fake microphone
(Live and Record), screenshots of the device and the editor."""
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
from playwright.sync_api import sync_playwright
out = sys.argv[2] if len(sys.argv) > 2 else '.'
SR = 48000

class AL(AudioLab):
    """the same as AudioLab, with Chromium's fake microphone (a beep) so Live and Record can run headless"""
    def start(self):
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])
        self.page = self.browser.new_page(viewport={"width": self.size[0], "height": self.size[1]})
        self.errors = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)[:400]))
        src = open(self.index, encoding="utf-8").read()
        def handle(route):
            u = route.request.url
            if u.endswith("/") or u.endswith("index.html"): route.fulfill(body=src, content_type="text/html")
            else: route.fulfill(status=404, body="")
        self.page.route("https://app.test/**", handle)
        self.page.goto("https://app.test/")
        self.page.wait_for_function("() => window.AudioLab && window.AudioLab.version", timeout=60000)
        self.page.wait_for_timeout(2500)
        self.version = self.js("() => AudioLab.version")
        return self

def sing(mid, sec, form=((700, 90, 1), (1220, 110, .5), (2600, 160, .25))):
    """additive harmonics following a pitch curve (midi per sample), through three formant resonators"""
    N = int(sec * SR); t = np.arange(N) / SR; m = mid(t); on = m > 0
    f = np.where(on, 440 * 2 ** ((m - 69) / 12), 0); ph = np.cumsum(f / SR); raw = np.zeros(N)
    for k in range(1, 60):
        raw += np.where(on & (k * f < SR * .45), np.sin(2 * np.pi * k * ph) / k, 0)
    x = np.zeros(N)
    for fc, bw, g in form:
        r = np.exp(-np.pi * bw / SR); a1 = -2 * r * np.cos(2 * np.pi * fc / SR); a2 = r * r
        from scipy.signal import lfilter
        x += lfilter([(1 - r) * g], [1, a1, a2], raw)
    x *= .3 / np.max(np.abs(x)); x[~on] = 0
    # 5 ms fades at note edges
    edge = np.diff(on.astype(int), prepend=0, append=0); return x.astype(np.float32)

def meas(x, t, expM, win=.08):
    n = int(win * SR); s = int(t * SR - n / 2); seg = x[s:s + n] * np.hanning(n); Nf = 1 << 17
    S = np.log(np.abs(np.fft.rfft(seg, Nf)) + 1e-12); f = 440 * 2 ** ((expM - 69) / 12)
    k0, k1 = int(f * .94 * Nf / SR), int(f * 1.06 * Nf / SR); b = k0 + int(np.argmax(S[k0:k1 + 1]))
    a, c, d = S[b - 1], S[b], S[b + 1]; sh = .5 * (a - d) / (a - 2 * c + d); return (b + sh) * SR / Nf
def measc(x, a, b, m):
    """mean frequency of the first harmonic over a stretch: the power-weighted centre of its band (right for vibrato)"""
    s, e = int(a * SR), int(b * SR); seg = x[s:e] * np.hanning(e - s); Nf = 1 << 18; P = np.abs(np.fft.rfft(seg, Nf)) ** 2; f = 440 * 2 ** ((m - 69) / 12)
    k0, k1 = int(f * 2 ** (-2 / 12) * Nf / SR), int(f * 2 ** (2 / 12) * Nf / SR); k = np.arange(k0, k1); return float((k * P[k0:k1]).sum() / P[k0:k1].sum() * SR / Nf)
cents = lambda f, m: 1200 * np.log2(f / (440 * 2 ** ((m - 69) / 12)))

def envc(x, t, m):
    """centroid of the formant envelope (harmonic peaks, dB-interpolated) from 300 to 3200 Hz"""
    f0 = meas(x, t, m, .1); n = int(.1 * SR); s = int(t * SR - n / 2); Nf = 1 << 16; M = np.abs(np.fft.rfft(x[s:s + n] * np.hanning(n), Nf))
    H = []
    k = 1
    while k * f0 < 4000:
        b = int(round(k * f0 * Nf / SR)); H.append((k * f0, 20 * np.log10(M[b - 6:b + 7].max() + 1e-9))); k += 1
    H = np.array(H); fr = np.arange(300, 3200, 5); ev = 10 ** (np.interp(fr, H[:, 0], H[:, 1]) / 20); return float((fr * ev).sum() / ev.sum())

al = AL(sys.argv[1] if len(sys.argv) > 1 else 'index.html'); al.start()
print('version', al.version, 'page errors on load', al.errors)

# ---- material: sung notes (A3 30 cents sharp, C4 60 cents sharp, E4 20 cents flat with vibrato, D4 after a glide)
NOTES = [(.25, 1.05, 57.3), (1.2, 2.0, 60.6), (2.15, 3.05, 63.8), (3.2, 4.0, 62.0)]
def mid(t):
    m = np.zeros_like(t)
    for a, b, p in NOTES:
        sel = (t >= a) & (t < b); m[sel] = p
    v = (t >= 2.15) & (t < 3.05); m[v] += .6 * np.sin(2 * np.pi * 5.5 * t[v])
    g = (t >= 3.2) & (t < 3.35); m[g] = 59.5 + (62 - 59.5) * (t[g] - 3.2) / .15
    return m
x = sing(mid, 4.4)
# spoken-like: falling pitch 150 -> 100 Hz in three syllables with gaps
def spk(t):
    m = np.zeros_like(t)
    for a, b in ((.1, .45), (.55, .95), (1.05, 1.6)):
        sel = (t >= a) & (t < b); hz = 150 - 50 * (t[sel] - .1) / 1.5; m[sel] = 69 + 12 * np.log2(hz / 440)
    return m
xs = sing(spk, 1.8, ((500, 120, 1), (1500, 150, .4), (2500, 200, .2)))
bid = al.add_audio(x[None, :], SR); sid = al.add_audio(xs[None, :], SR)
spb = 60 / 120
al.build({'bpm': 120, 'tracks': [{'name': 'Vox', 'kind': 'audio', 'fx': [{'type': 'voice'}], 'clips': [{'start': 0, 'len': len(x) / SR / spb, 'buf': bid, 'dur': len(x) / SR, 'gain': 0, 'fi': 0, 'fo': 0, 'name': 'Sung'}]},
                    {'name': 'Talk', 'kind': 'audio', 'fx': [{'type': 'voice'}], 'clips': [{'start': 0, 'len': len(xs) / SR / spb, 'buf': sid, 'dur': len(xs) / SR, 'gain': 0, 'fi': 0, 'fo': 0, 'name': 'Spoken'}]}]})
al.run("selT=S.tracks[0].id;renderFx();1"); al.page.wait_for_timeout(800)
D = '.dev:has(canvas.viz[data-t="voice"])'

# ---- notes
t0 = time.time()
al.run("(async()=>{const t=S.tracks[0];await NACT.voice(t.fx[0],'notes',t);window._vn=1})();1")
al.page.wait_for_function("()=>window.AudioLab.run('window._vn===1')", timeout=20000)
print('notes found in %.2f s' % (time.time() - t0))
N = json.loads(al.run("JSON.stringify(S.tracks[0].clips[0].vx.notes)"))
print('sung notes (start, end, centre):', [(round(n['s'], 3), round(n['e'], 3), round(n['p0'], 2)) for n in N])
for (a, b, p), n in zip(NOTES, N):
    print('  expected %.2f..%.2f centre %.2f   found %.3f..%.3f centre %.2f   error %+.1f cents' % (a, b, p, n['s'], n['e'], n['p0'], (n['p0'] - p) * 100))
A = json.loads(al.run("(()=>{const A=vxA(S.tracks[0].clips[0].vx.buf);return JSON.stringify({hop:A.hop,f0:Array.from(A.f0)})})()"))
hop = A['hop'] / SR; f0 = np.array(A['f0']); tt = np.arange(len(f0)) * hop; truth = mid(tt)
ok = (truth > 0) & (f0 > 0); inner = np.zeros_like(ok)
for a, b, p in NOTES: inner |= (tt > a + .03) & (tt < b - .03)
err = np.abs(69 + 12 * np.log2(np.where(f0 > 0, f0, 1) / 440) - truth) * 100
for nm, msk in (('steady notes', inner & ok & ~((tt >= 2.15) & (tt < 3.05)) & ~((tt >= 3.2) & (tt < 3.35))), ('vibrato note', inner & ok & (tt >= 2.15) & (tt < 3.05)), ('glide', ok & (tt >= 3.2) & (tt < 3.35))):
    e = err[msk]; print('tracker %-13s median %.2f cents, 95 %% %.2f, frames %d' % (nm, np.median(e), np.percentile(e, 95), len(e)))
print('voiced frames missed inside notes', int((inner & (f0 == 0)).sum()), 'of', int(inner.sum()), '; unvoiced frames marked voiced', int(((truth == 0) & (f0 > 0)).sum()))
# spoken
al.run("(async()=>{const t=S.tracks[1];await NACT.voice(t.fx[0],'notes',t);window._vs=1})();1"); al.page.wait_for_function("()=>window.AudioLab.run('window._vs===1')", timeout=20000)
A2 = json.loads(al.run("(()=>{const A=vxA(S.tracks[1].clips[0].vx.buf);return JSON.stringify({f0:Array.from(A.f0),n:S.tracks[1].clips[0].vx.notes.length})})()"))
f2 = np.array(A2['f0']); tt2 = np.arange(len(f2)) * hop; tr2 = spk(tt2); m2 = (tr2 > 0) & (f2 > 0)
print('spoken phrase: notes', A2['n'], 'tracker median %.2f cents, 95 %% %.2f, voiced found %d of %d' % (np.median(np.abs(69 + 12 * np.log2(f2[m2] / 440) - tr2[m2]) * 100), np.percentile(np.abs(69 + 12 * np.log2(f2[m2] / 440) - tr2[m2]) * 100, 95), m2.sum(), (tr2 > 0).sum()))

def rend(name='Vox', b1=None):
    y, sr = al.render(b0=0, b1=b1 or (4.4 / spb), sr=SR, only=name, tail=.2); return y
def lat():
    return al.run("fxLat(S.tracks[0].fx[0],48000)")
L = lat()
y0 = rend(); y0b = rend()
print('render twice bit-identical (Natural preset):', bool(np.array_equal(y0, y0b)))
# where the clip lands in the render: cross-correlate
def off(y):
    c = [float(np.dot(y[0][d:d + SR * 2], x[:SR * 2])) for d in range(0, 4000)]; return int(np.argmax(c))
o0 = off(y0); print('Voice latency', L, 'samples (%.1f ms); the render is offset by %d samples' % (L / 48, o0))
def at(y, t): return y[0][o0:]

# ---- editor: open, select note 2, arrow up = +1 semitone
al.run("(()=>{const t=S.tracks[0];NACT.voice(t.fx[0],'edit',t)})();1"); al.page.wait_for_timeout(800)
al.page.screenshot(path=os.path.join(out, 'voice_editor.png'))
al.run("(()=>{const c=S.tracks[0].clips[0];VXSEL.cid=c.id;VXSEL.s=new Set([1]);vxWinPaint();1})()"); al.page.keyboard.press('ArrowUp'); al.page.wait_for_timeout(1500)
print('after ArrowUp on note 2: dp =', al.run("S.tracks[0].clips[0].vx.notes[1].dp"), 'clip plays a rendered copy:', al.run("S.tracks[0].clips[0].buf!==S.tracks[0].clips[0].vx.buf"))
y1 = rend()
for i, (a, b, p) in enumerate(NOTES[:3]):
    tm = (a + b) / 2 + (0 if i != 2 else .0); sh = 1 if i == 1 else 0
    fi = meas(x, tm, p); fo = meas(y1[0][o0:], tm, p + sh)
    print('  note %d moved %d st: measured %+.2f cents (want %d)' % (i + 1, sh, 1200 * np.log2(fo / fi), sh * 100))
# formant: note 1 (A3) moved up 5 semitones, with and without Keep formant (envelope centroid of the harmonic peaks)
for keep in (True, False):
    al.run("(()=>{const c=S.tracks[0].clips[0];pushUndo();c.vx.notes[0].dp=5;c.vx.keep=%s;vxCommit(c);1})()" % ('true' if keep else 'false')); al.page.wait_for_timeout(1500)
    yf = rend(); print('  note 1 up 5 st, Keep formant %s: pitch %+.1f cents, formant envelope %+.2f st' % ('on ' if keep else 'off', 1200 * np.log2(meas(yf[0][o0:], .65, 62.3) / meas(x, .65, 57.3)), 12 * np.log2(envc(yf[0][o0:], .65, 62.3) / envc(x, .65, 57.3))))
    al.run("undo();1"); al.page.wait_for_timeout(1200)
al.run("(()=>{const c=S.tracks[0].clips[0];pushUndo();c.vx.notes[0].fm=3;vxCommit(c);1})()"); al.page.wait_for_timeout(1500)
yf = rend(); print('  note 1 Formant +3 st: pitch %+.1f cents, formant envelope %+.2f st' % (1200 * np.log2(meas(yf[0][o0:], .65, 57.3) / meas(x, .65, 57.3)), 12 * np.log2(envc(yf[0][o0:], .65, 57.3) / envc(x, .65, 57.3))))
al.run("undo();1"); al.page.wait_for_timeout(1200)
# clicks: largest sample step against the input
st_in = np.max(np.abs(np.diff(x))); st_out = np.max(np.abs(np.diff(y1[0][o0:o0 + len(x)])))
print('largest sample step: input %.4f, after the move %.4f' % (st_in, st_out))
al.run("undo();1"); al.page.wait_for_timeout(1200); print('undo of the move: dp', al.run("S.tracks[0].clips[0].vx.notes[1].dp"), 'plays the recording:', al.run("S.tracks[0].clips[0].buf===S.tracks[0].clips[0].vx.buf"))
# a mouse drag in the device picture: note 1 up by about 2 semitones with Snap to semitones
al.page.click('#vxWin [data-vxw="close"]'); al.page.wait_for_timeout(300); print('editor closed:', al.run("document.getElementById('vxWin').hidden"))
g = json.loads(al.run("(()=>{drawViz();const cv=document.querySelector('canvas.viz[data-t=voice]'),r=cv.getBoundingClientRect(),G=cv._vx.G,n=S.tracks[0].clips[0].vx.notes[0],z=r.width/cv.clientWidth;return JSON.stringify({x:r.left+G.X((n.s+n.e)/2)*z,y:r.top+G.Y(n.p0+(n.dp||0))*z,rh:G.rh*z})})()"))
al.page.mouse.move(g['x'], g['y']); al.page.mouse.down(); al.page.mouse.move(g['x'], g['y'] - g['rh'] * 1.2, steps=4); al.page.mouse.move(g['x'], g['y'] - g['rh'] * 2.1, steps=4); al.page.mouse.up(); al.page.wait_for_timeout(1500)
n1 = json.loads(al.run("JSON.stringify(S.tracks[0].clips[0].vx.notes[0])")); print('mouse drag: note 1 centre %.2f + move %.2f = %.2f (snapped to a semitone)' % (n1['p0'], n1['dp'], n1['p0'] + n1['dp']))
al.page.screenshot(path=os.path.join(out, 'voice_device_notes.png'), clip=json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:Math.min(r.width,1600-r.left),height:r.height})})()" % D)))
al.run("undo();1"); al.page.wait_for_timeout(1200)
# double-click splits
al.run("drawViz();1"); g = json.loads(al.run("(()=>{const cv=document.querySelector('canvas.viz[data-t=voice]'),r=cv.getBoundingClientRect(),G=cv._vx.G,n=S.tracks[0].clips[0].vx.notes[0],z=r.width/cv.clientWidth;return JSON.stringify({x:r.left+G.X(n.s+(n.e-n.s)*.4)*z,y:r.top+G.Y(n.p0+(n.dp||0))*z})})()"))
nb = al.run("S.tracks[0].clips[0].vx.notes.length"); al.page.mouse.click(g['x'], g['y']); al.page.wait_for_timeout(120); al.page.mouse.click(g['x'], g['y']); al.page.wait_for_timeout(1200)
na = al.run("S.tracks[0].clips[0].vx.notes.length"); print('double-click split: notes', nb, '->', na)
ys = rend(); print('  after the split (nothing moved) the clip is the recording again:', al.run("S.tracks[0].clips[0].buf===S.tracks[0].clips[0].vx.buf"))
al.run("(()=>{const c=S.tracks[0].clips[0];pushUndo();vxJoin(c,[0,1]);vxCommit(c);changed(false);1})()"); al.page.wait_for_timeout(500); print('join: notes', al.run("S.tracks[0].clips[0].vx.notes.length")); al.run("undo();undo();1"); al.page.wait_for_timeout(1200); print('  two undos: notes', al.run("S.tracks[0].clips[0].vx.notes.length"), 'plays the recording:', al.run("S.tracks[0].clips[0].buf===S.tracks[0].clips[0].vx.buf"))

# ---- Correct pitch 100 % (centre and drift) in C major
al.run("(()=>{const t=S.tracks[0];NACT.voice(t.fx[0],'edit',t)})();1"); al.page.wait_for_timeout(500)
al.run("(()=>{const W=document.getElementById('vxWin');W.querySelector('[data-vxw=scaleN]').value='major';W.querySelector('[data-vxw=scaleN]').dispatchEvent(new Event('change',{bubbles:true}));W.querySelector('[data-vxw=cc]').value=100;W.querySelector('[data-vxw=cd]').value=100;VXSEL.s.clear();1})()")
al.page.click('#vxWin [data-vxw="correct"]'); al.page.wait_for_timeout(1800)
yc = rend()
for i, (a, b, p) in enumerate(NOTES):
    tg = [57, 60, 64, 62][i]; w = .545 if i == 2 else .1; f = meas(yc[0][o0:], (a + b) / 2, tg, w)
    if i == 2: print('  Correct pitch 100 %%: vibrato note %.2f -> %d: mean pitch %+.2f cents off (vibrato kept)' % (p, tg, cents(measc(yc[0][o0:], a + .1, b - .1, tg), tg)), '; the input reads %+.2f cents against %.2f' % (cents(measc(x, a + .1, b - .1, p), p), p))
    else: print('  Correct pitch 100 %%: note %.2f -> %d measured %+.2f cents off the scale note' % (p, tg, cents(f, tg)))
# vibrato note: drift 100 % removes slow wander, vibrato stays
al.page.screenshot(path=os.path.join(out, 'voice_editor_corrected.png'))
al.page.click('#vxWin [data-vxw="close"]')
al.run("undo();undo();1"); al.page.wait_for_timeout(1500); print('after two undos the clip plays the recording:', al.run("S.tracks[0].clips[0].buf===S.tracks[0].clips[0].vx.buf"))

# ---- live engine in exports: hard tune (Correct 100 %, Speed Hard) in C major
def setp(o):
    al.run("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,%s);changed(true);renderFx();1})()" % json.dumps(o)); al.page.wait_for_timeout(400)
setp({'corr': 100, 'spd': 0, 'scaleN': 'major', 'key': 0})
yh = rend(); yh2 = rend(); print('hard tune render twice bit-identical:', bool(np.array_equal(yh, yh2)))
for i, (a, b, p) in enumerate(NOTES[:2] + NOTES[3:]):
    tg = [57, 60, 62][i]; f = meas(yh[0][o0:], (a + b) / 2 + .1, tg, .1); print('  hard tune: %.2f -> %d measured %+.2f cents' % (p, tg, cents(f, tg)))
# choir: 2 voices, 40 ms spread, 30 cents, hard left and right
setp({'corr': 0, 'nv': 2, 'det': 30, 'spr': 40, 'wd': 100, 'scaleN': 'chrom'})
yv = rend()
for (a, b, p) in NOTES[:2]:
    tm = (a + b) / 2; print('  choir note %.2f: left %+.1f cents, right %+.1f cents (want -30 and +30, plus a slow drift of up to 9.5)' % (p, cents(meas(yv[0][o0:], tm, p), p), cents(meas(yv[1][o0:], tm, p), p)))
on = lambda c: int(np.argmax(np.abs(c) > .02))
print('  choir: first sound left at %d, right at %d samples: %.1f ms apart' % (on(yv[0]), on(yv[1]), (on(yv[1]) - on(yv[0])) / 48))
setp({'nv': 1, 'det': 0, 'spr': 0})
# Woman on the spoken phrase (100 to 150 Hz, 'You: Low voice'): an octave up and the formant up 2.7 st
al.run("(()=>{const f=S.tracks[1].fx[0];Object.assign(f.p,{ch:'woman',rg:'l'});f.p.clip=null;changed(true);1})()"); al.page.wait_for_timeout(300)
yw, _ = al.render(b0=0, b1=1.8 / spb, sr=SR, only='Talk', tail=.2); ow = int(np.argmax([float(np.dot(np.abs(yw[0][d:d + SR]), np.abs(xs[:SR]))) for d in range(0, 4000, 4)])) * 4
for tm in (.3, .75, 1.3):
    m = 69 + 12 * np.log2((150 - 50 * (tm - .1) / 1.5) / 440); print('  Woman from a low voice at %.2f s: pitch %+.0f cents (an octave is 1200)' % (tm, 1200 * np.log2(meas(yw[0][ow:], tm, m + 12, .06) / meas(xs, tm, m, .06))))
# cost: render time of 8 voices and the doubler, 4.4 s
setp({'nv': 8, 'det': 18, 'spr': 45, 'fsp': 1.2, 'dbl': 50, 'corr': 80, 'spd': 40})
t0 = time.time(); rend(); print('render of 4.4 s with 8 voices and the doubler: %.2f s (includes moving the samples to Python)' % (time.time() - t0))
al.page.screenshot(path=os.path.join(out, 'voice_device_choir.png'), clip=json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:Math.min(r.width,1600-r.left),height:r.height})})()" % D)))
setp({'nv': 1, 'det': 0, 'spr': 0, 'fsp': 0, 'dbl': 0, 'corr': 0})

# ---- pop chain preset
al.run("(()=>{const s=document.querySelector('%s select[data-x=pre]');s.value='poplead';s.dispatchEvent(new Event('change',{bubbles:true}))})()" % D); al.page.wait_for_timeout(800)
print('pop chain: track effects', al.run("JSON.stringify(S.tracks[0].fx.map(f=>f.type))"), 'returns', al.run("JSON.stringify(S.tracks.filter(t=>t.kind==='return').map(t=>t.name+':'+t.fx.map(f=>f.type)))"), 'sends', al.run("JSON.stringify(Object.values(S.tracks[0].sends||{}))"))
al.run("(()=>{const s=document.querySelector('%s select[data-x=pre]');s.value='pophard';s.dispatchEvent(new Event('change',{bubbles:true}))})()" % D); al.page.wait_for_timeout(800)
print('  again (Hard-tuned lead): effects', al.run("JSON.stringify(S.tracks[0].fx.map(f=>f.type))"), 'returns', al.run("S.tracks.filter(t=>t.kind==='return').length"))
al.run("undo();undo();1"); al.page.wait_for_timeout(500); print('  two undos: effects', al.run("JSON.stringify(S.tracks[0].fx.map(f=>f.type))"), 'returns', al.run("S.tracks.filter(t=>t.kind==='return').length"))

# ---- presets: every one renders, levels
pres = json.loads(al.run("JSON.stringify(Object.keys(FXPRE.voice))")); print('presets', len(pres))
lv = []
for k in pres:
    if k.startswith('pop'): continue
    al.run("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,JSON.parse(JSON.stringify(FXPRE.voice['%s'][1])));f.p.pre='%s';changed(true);1})()" % (k, k)); al.page.wait_for_timeout(150)
    y = rend(); r = 20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-12); pk = np.max(np.abs(y)); lv.append((k, round(float(r), 1), round(float(pk), 2), bool(np.isfinite(y).all())))
print('preset levels (rms dB, peak, finite):', lv, 'input rms %.1f dB' % (20 * np.log10(np.sqrt(np.mean(x ** 2)))))

# ---- the fake microphone: Live and Record
al.run("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,JSON.parse(JSON.stringify(FXPRE.voice.natural[1])));f.p.clip=null;changed(true);renderFx();1})()")
al.run("(async()=>{const t=S.tracks[0];await NACT.voice(t.fx[0],'live',t);window._lv=1})();1"); al.page.wait_for_function("()=>window.AudioLab.run('window._lv===1')", timeout=10000); al.page.wait_for_timeout(2500)
print('live: fake microphone, messages with a pitch', al.run("(vxXOf(S.tracks[0].fx[0])||{H:[]}).H.filter(q=>q.f>0).length"), 'loudest', al.run("Math.max(...(vxXOf(S.tracks[0].fx[0])||{H:[]}).H.map(q=>q.lv))"), 'pitches', al.run("JSON.stringify([...new Set((vxXOf(S.tracks[0].fx[0])||{H:[]}).H.filter(q=>q.f>0).map(q=>Math.round(q.f)))].slice(0,8))"))
print('live: on', al.run("vxIsLive(S.tracks[0].fx[0])"), 'pitch messages', al.run("(vxXOf(S.tracks[0].fx[0])||{H:[]}).H.length"), 'last', al.run("JSON.stringify((vxXOf(S.tracks[0].fx[0])||{H:[]}).H.slice(-1))"))
al.page.screenshot(path=os.path.join(out, 'voice_device_live.png'), clip=json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:Math.min(r.width,1600-r.left),height:r.height})})()" % D)))
nc = al.run("S.tracks[0].clips.length")
al.run("(async()=>{const t=S.tracks[0];pos=12;await NACT.voice(t.fx[0],'rec',t)})();1"); al.page.wait_for_timeout(3200); al.run("stop();1"); al.page.wait_for_timeout(2500)
print('recorded take: peak', al.run("(()=>{const c=S.tracks[0].clips[S.tracks[0].clips.length-1],d=BUFS.get(c.vx?c.vx.buf:c.buf).buf.getChannelData(0);let m=0;for(const v of d)m=Math.max(m,Math.abs(v));return m.toFixed(3)})()"))
print('record: clips', nc, '->', al.run("S.tracks[0].clips.length"), al.run("(()=>{const c=S.tracks[0].clips[S.tracks[0].clips.length-1];return JSON.stringify({start:+c.start.toFixed(3),dur:+c.dur.toFixed(2),notes:c.vx?c.vx.notes.length:null,shown:S.tracks[0].fx[0].p.clip===c.id})})()"))
al.run("(()=>{const t=S.tracks[0];NACT.voice(t.fx[0],'live',t)})();1"); al.page.wait_for_timeout(600)
al.page.screenshot(path=os.path.join(out, 'voice_device_recorded.png'), clip=json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:Math.min(r.width,1600-r.left),height:r.height})})()" % D)))

# ---- after a reload the rendered copy is made again from the recording and the notes (it is not kept in the browser storage)
al.run("(()=>{const c=S.tracks[0].clips[0];pushUndo();c.vx.notes[0].dp=2;vxCommit(c);changed(false);1})()"); al.page.wait_for_timeout(1500)
h1 = al.run("(()=>{const c=S.tracks[0].clips[0],d=BUFS.get(c.buf).buf.getChannelData(0);let h=0;for(let i=0;i<d.length;i+=7)h=(h*31+Math.round(d[i]*1e6))%1e9;window._rid=c.buf;BUFS.delete(c.buf);return h})()")
al.run("vxRestore();1"); al.page.wait_for_timeout(1500)
h2 = al.run("(()=>{const c=S.tracks[0].clips[0];if(!BUFS.has(c.buf))return -1;const d=BUFS.get(c.buf).buf.getChannelData(0);let h=0;for(let i=0;i<d.length;i+=7)h=(h*31+Math.round(d[i]*1e6))%1e9;return h})()")
print('rendered copy removed and made again: same samples', h1 == h2, '; project file keeps the recording:', al.run("(()=>{const ids=new Set();(function walk(o){if(!o||typeof o!=='object')return;if(Array.isArray(o)){for(const x of o)walk(x);return}for(const k in o){const v=o[k];if(k==='buf'&&typeof v==='string'&&BUFS.has(v))ids.add(v);else if(v&&typeof v==='object')walk(v)}})(S);const c=S.tracks[0].clips[0];return ids.has(c.vx.buf)&&ids.has(c.buf)})()"))
al.run("undo();1")
# ---- tooltips and dashes
al.page.mouse.move(5, 5); al.page.wait_for_timeout(200)
print('controls without a tooltip:', al.run("JSON.stringify([...document.querySelectorAll('%s [data-c],%s button,%s select,%s canvas')].filter(e=>e.getBoundingClientRect().width&&!(e.title||e.closest('[title]')||e.getAttribute('aria-label'))).map(e=>(e.textContent||e.dataset.c||e.tagName).trim().slice(0,14)))" % (D, D, D, D)))
print('editor controls without a tooltip:', al.run("JSON.stringify([...document.querySelectorAll('#vxWin button,#vxWin select,#vxWin input')].filter(e=>!(e.title||e.closest('[title]'))).map(e=>e.dataset.vxw))"))
print('dashes in texts:', al.run("(()=>{let s=document.querySelector('%s').textContent+document.getElementById('vxWin').textContent;for(const e of document.querySelectorAll('%s [title],#vxWin [title]'))s+=e.title;s+=JSON.stringify(FXPRE.voice)+FXDESC.voice+JSON.stringify(VXCH);return /\\u2014|\\u2013/.test(s)})()" % (D, D)))
print('effect browser group', al.run("JSON.stringify(FXCAT.find(g=>g[1].includes('voice'))[0])"))
print('errors', al.errors)
al.stop()
