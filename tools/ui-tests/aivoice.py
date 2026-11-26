"""AI voices for Voice (v0.206, task Z2), measured in the real page with the real model.
  python3 tools/ui-tests/aivoice.py [index.html] [out dir] [model dir] [test audio dir]
The desktop bridge is replaced by tools/ui-tests/aivoice_server.js, which runs desktop/voice-ai-worker.js (the same code as the app's
utility process) on the downloaded OpenVoice V2 ONNX model. Needs node with onnxruntime-node on NODE_PATH, and test audio you may use:
  sung.wav   one person singing (here: VocalSet f1 arpeggios, CC BY 4.0)      talk.wav  one person talking (LibriSpeech 1272, CC BY 4.0)
  refA.wav   a second voice for the sung phrase (LibriSpeech 1272, other utterances)  refB.wav  a second voice for the talking (VocalSet f2 spoken)
Measures: speaker similarity before and after (WavLM-base-plus-sv cosine, see /tmp sim helper), pitch on held notes against the edited
pitch line (a synthetic sung phrase with known notes, measured by FFT), clicks, time, memory, the original clip unchanged, page errors,
screenshots of the AI window in the web, old-app and ready states."""
import sys, os, json, time, subprocess, hashlib, base64, urllib.request
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
idx = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
out = sys.argv[2] if len(sys.argv) > 2 else '.'
mdir = sys.argv[3] if len(sys.argv) > 3 else '/tmp/claude-0/ov/fp16'
adir = sys.argv[4] if len(sys.argv) > 4 else '/tmp/claude-0/testaudio'
SR = 48000; PORT = 8765
here = os.path.dirname(os.path.abspath(__file__))
srv = subprocess.Popen(['node', os.path.join(here, 'aivoice_server.js'), mdir, str(PORT)], stdout=subprocess.PIPE, env=dict(os.environ))
assert srv.stdout.readline().decode().startswith('ready')

class AL(AudioLab):
    def start(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start(); self.browser = self._pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        self.page = self.browser.new_page(viewport={"width": self.size[0], "height": self.size[1]}); self.errors = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)[:400]))
        src = open(self.index, encoding="utf-8").read()
        def handle(route):
            u = route.request.url
            if '/vai/' in u:
                r = urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:%d/%s' % (PORT, u.split('/vai/')[1]), data=(route.request.post_data or '').encode(), method='POST'), timeout=600)
                route.fulfill(body=r.read(), content_type='application/json'); return
            if u.endswith("/") or u.endswith("index.html"): route.fulfill(body=src, content_type="text/html")
            else: route.fulfill(status=404, body="")
        self.page.route("https://app.test/**", handle); self.page.goto("https://app.test/")
        self.page.wait_for_function("() => window.AudioLab && window.AudioLab.version", timeout=60000); self.page.wait_for_timeout(2500)
        self.version = self.js("() => AudioLab.version"); return self

BRIDGE = """(full)=>{const P=x=>Promise.resolve(x),call=(n,b)=>fetch('https://app.test/vai/'+n,{method:'POST',body:JSON.stringify(b||{})}).then(r=>r.json()).then(r=>{if(r&&r.err)throw new Error(r.err);return r});
 const b64=a=>{const u=new Uint8Array(Float32Array.from(a).buffer);let s='';for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));return btoa(s)};
 const f32=s=>{const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return new Float32Array(u.buffer)};
 const D={isDesktop:true,platform:'test',version:()=>P('0.201.0'),programVersion:()=>P('0.201'),updateCheck:()=>P({}),updateStatus:()=>P({}),updateApp:()=>P('page'),checkForUpdates:()=>P(),applyUpdate:()=>P(),isFullScreen:()=>P(false),displayHz:()=>P(60),onDock(){},onFromChild(){},onDockHover(){},dac:null};
 if(full)D.voiceAI={status:()=>call('status'),download:()=>call('download'),embed:(x,ep,sh)=>call('embed',{x:b64(x),ep,sh:sh?{st:sh.st,f0:b64(sh.f0)}:null}).then(r=>({se:f32(r.se)})),
  convert:m=>call('convert',{x:b64(m.x),src:Array.from(m.src),tgt:Array.from(m.tgt),ep:m.ep}).then(r=>({y:f32(r.y),ms:r.ms})),voices:()=>call('voices'),
  saveVoice:v=>call('saveVoice',{name:v.name,from:v.from,x:b64(v.x),se:v.se,hz:v.hz}),getVoice:id=>call('getVoice',{id}).then(v=>Object.assign(v,{x:f32(v.x)})),
  setVoice:(id,p)=>call('setVoice',{id,p}),delVoice:id=>call('delVoice',{id}),free:()=>P(true),onProgress:cb=>{window._vaiCb=cb;return()=>{}}};
 window.audiolabDesktop=D;VAI.voices=null;VAI.off=null;return 1}"""

def load(name, sr=SR):
    import soxr
    x, s = sf.read(os.path.join(adir, name), dtype='float32', always_2d=True); return soxr.resample(x.mean(1), s, sr).astype(np.float32)
def sing(mid, sec, form=((700, 90, 1), (1220, 110, .5), (2600, 160, .25))):
    from scipy.signal import lfilter
    N = int(sec * SR); t = np.arange(N) / SR; m = mid(t); on = m > 0; f = np.where(on, 440 * 2 ** ((m - 69) / 12), 0); ph = np.cumsum(f / SR); raw = np.zeros(N)
    for k in range(1, 60): raw += np.where(on & (k * f < SR * .45), np.sin(2 * np.pi * k * ph) / k, 0)
    x = np.zeros(N)
    for fc, bw, g in form:
        r = np.exp(-np.pi * bw / SR); x += lfilter([(1 - r) * g], [1, -2 * r * np.cos(2 * np.pi * fc / SR), r * r], raw)
    x *= .3 / np.max(np.abs(x)); x[~on] = 0; return x.astype(np.float32)
def meas(x, t, expM, win=.1):
    n = int(win * SR); s = int(t * SR - n / 2); seg = x[s:s + n] * np.hanning(n); Nf = 1 << 17
    S = np.log(np.abs(np.fft.rfft(seg, Nf)) + 1e-12); f = 440 * 2 ** ((expM - 69) / 12)
    k0, k1 = int(f * .94 * Nf / SR), int(f * 1.06 * Nf / SR); b = k0 + int(np.argmax(S[k0:k1 + 1])); a, c, d = S[b - 1], S[b], S[b + 1]; return (b + .5 * (a - d) / (a - 2 * c + d)) * SR / Nf
cents = lambda f, m: 1200 * np.log2(f / (440 * 2 ** ((m - 69) / 12)))

al = AL(idx); al.start(); print('version', al.version, 'page errors on load', al.errors)
NOTES = [(.3, 1.3, 64.0), (1.45, 2.45, 67.0), (2.6, 3.6, 62.0)]   # held notes (E4, G4, D4), exactly in tune
def mid(t):
    m = np.zeros_like(t)
    for a, b, p in NOTES: m[(t >= a) & (t < b)] = p
    return m
syn = sing(mid, 3.9)
sung, talk, refA, refB = load('sung.wav'), load('talk.wav'), load('refA.wav')[:SR * 40], load('refB.wav')
ids = [al.add_audio(a[None, :], SR) for a in (syn, sung, talk, refA, refB)]
spb = .5; mk = lambda nm, i, a: {'name': nm, 'kind': 'audio', 'fx': [{'type': 'voice'}], 'clips': [{'start': 0, 'len': len(a) / SR / spb, 'buf': ids[i], 'dur': len(a) / SR, 'gain': 0, 'fi': 0, 'fo': 0, 'name': nm + ' clip'}]}
al.build({'bpm': 120, 'tracks': [mk('Synth', 0, syn), mk('Sung', 1, sung), mk('Talk', 2, talk), mk('Voice A', 3, refA), mk('Voice B', 4, refB)]})
T = lambda n: "S.tracks.find(t=>t.name==='%s')" % n
def wait(cond, ms=600000): al.page.wait_for_function("()=>window.AudioLab.run(%s)" % json.dumps(cond), timeout=ms)
def act(track, a):
    al.run("window._d=0;(async()=>{const t=%s;await NACT.voice(t.fx[0],'%s',t);window._d=1})();1" % (T(track), a)); wait('window._d===1')
def shot(name): al.page.screenshot(path=os.path.join(out, name)); print('screenshot', name)
def rend(name, sec): y, _ = al.render(b0=0, b1=sec / spb, sr=SR, only=name, tail=.3); return y
md5 = lambda tr: al.run("(()=>{const c=%s.clips[0],b=BUFS.get(c.vx?c.vx.buf:c.buf).buf;let h=0;const d=b.getChannelData(0);for(let i=0;i<d.length;i++)h=(h*31+Math.round(d[i]*1e6))|0;return h})()" % T(tr))

# ---- 1. web version: the window says what it can and cannot do
al.run("selT=%s.id;renderFx();1" % T('Sung')); al.page.wait_for_timeout(500)
act('Sung', 'ai'); print('web:', al.run("document.querySelector('#vaiWin .vainfo').textContent")[:120]); shot('ai_web.png')
# ---- 2. an older desktop app: asks for an update
al.run('(' + BRIDGE + ')(false)'); act('Sung', 'ai'); print('old app:', al.run("document.querySelector('#vaiWin .vainfo').textContent")[:80]); shot('ai_oldapp.png')
# ---- 3. the new desktop app
al.run('(' + BRIDGE + ')(true)'); act('Sung', 'ai'); print('desktop:', al.run("document.querySelector('#vaiWin .vainfo').textContent")[:80])
print('voices listed:', al.run("JSON.stringify(VAI.voices.map(v=>v.name))"))
tips = al.run("(()=>{const W=document.getElementById('vaiWin');const L=[...W.querySelectorAll('button,select,input')].filter(e=>!(e.title||(e.closest('label')&&e.closest('label').title)||(e.closest('[title]')&&e.closest('[title]')!==W)));return L.length})()")
print('controls without a tooltip:', tips)
h0 = {n: md5(n) for n in ('Synth', 'Sung', 'Talk')}

# make two voices from clips in the project
def make(track, name):
    i = al.run("vaiClips().findIndex(o=>o.t.name==='%s')" % track)
    al.run("(()=>{const W=document.getElementById('vaiWin');W.querySelector('[data-va=src]').value='%d';W.querySelector('[data-va=name]').value=%s;W.querySelector('[data-va=make]').click();1})()" % (i, json.dumps(name)))
    al.page.wait_for_timeout(300); wait('!VAI.busy'); print('made voice', name, '->', al.run("VAI.msg"))
t0 = time.time(); make('Voice A', 'Speaker A (talking)'); print('  in %.1f s' % (time.time() - t0))
make('Voice B', 'Singer B (talking)')
vid = json.loads(al.run("JSON.stringify(Object.fromEntries(VAI.voices.map(v=>[v.name,v.id])))"))

def convert(track, voice, extra=None):
    o = {'aiV': vid[voice], 'aiAmt': 100, 'aiRng': 0, 'aiFm': 0, 'aiBr': 50, 'aiLay': []}; o.update(extra or {})
    al.run("(()=>{const f=%s.fx[0];Object.assign(f.p,%s);1})()" % (T(track), json.dumps(o)))
    al.run("window._d=0;(async()=>{const t=%s;if(!vxClip(t.fx[0]))await vxNotes(t.fx[0],t);await vaiConvert(t.fx[0],t);window._d=1})();1" % T(track)); wait('window._d===1')
    r = json.loads(al.run("JSON.stringify(%s.clips[0].vx.ai||null)" % T(track))); print('converted', track, '->', voice, ':', al.run("VAI.msg"), 'pitch fit (cents left after each try):', r and r.get('cal')); return r

# ---- 4. speaker similarity: the sung phrase into Speaker A, the talking into Singer B
ySung0 = rend('Sung', len(sung) / SR); yTalk0 = rend('Talk', len(talk) / SR)
st = json.loads(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:%d/stats' % PORT, data=b'{}')).read())
a1 = convert('Sung', 'Speaker A (talking)'); a2 = convert('Talk', 'Singer B (talking)')
st2 = json.loads(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:%d/stats' % PORT, data=b'{}')).read())
ySung = rend('Sung', len(sung) / SR); yTalk = rend('Talk', len(talk) / SR)
convert('Sung', 'Speaker A (talking)', {'aiFit': 'oct'}); ySungO = rend('Sung', len(sung) / SR)
convert('Talk', 'Singer B (talking)', {'aiFit': 'own'}); yTalkO = rend('Talk', len(talk) / SR)
convert('Sung', 'Speaker A (talking)')
for n, y in (('sung_before', ySung0), ('sung_ai', ySung), ('sung_ai_octave', ySungO), ('talk_before', yTalk0), ('talk_ai', yTalk), ('talk_ai_ownrange', yTalkO)): sf.write(os.path.join(out, 'ai_%s.wav' % n), y.T, SR)
sf.write(os.path.join(out, 'ai_refA.wav'), refA, SR); sf.write(os.path.join(out, 'ai_refB.wav'), refB, SR)
conv_s = st2['convert'] - st['convert']; aud = st2['convertAudio'] - st['convertAudio']
print('model time: %.1f s for %.1f s of audio, real-time factor %.3f (this machine: %d cores)' % (conv_s / 1000, aud, conv_s / 1000 / aud, os.cpu_count()))
print('whole conversion in the page (Sung %.1f s of audio): %.1f s; (Talk %.1f s): %.1f s' % (len(sung) / SR, a1['ms'] / 1000, len(talk) / SR, a2['ms'] / 1000))
print('model process memory: %d MB' % st2['rssMB'])

# ---- 5. held notes follow the pitch line, also after a note edit
a3 = convert('Synth', 'Speaker A (talking)')
y = rend('Synth', 3.9); al.run("(()=>{const c=%s.clips[0];pushUndo();c.vx.notes[1].dp=2;vxCommit(c);1})()" % T('Synth')); al.page.wait_for_timeout(500); wait("!!%s.clips[0].vx._k&&BUFS.has(%s.clips[0].buf)" % (T('Synth'), T('Synth')))
al.page.wait_for_timeout(2500); ye = rend('Synth', 3.9)
L = al.run("fxLat(%s.fx[0],48000)" % T('Synth')); o = int(L)
import librosa
def yinm(yy, a, b):
    f = librosa.yin(yy[int(a * SR):int(b * SR)], fmin=120, fmax=900, sr=SR, frame_length=4096, hop_length=480); return 69 + 12 * np.log2(f / 440)
for lab, yy, edit in (('converted', y, 0), ('converted, note 2 moved +2 st', ye, 2)):
    res = []
    for i, (a, b, p) in enumerate(NOTES):
        tgt = p + (edit if i == 1 else 0); m = (yinm(yy[0][o:], a + .1, b - .1) - tgt) * 100
        f = [cents(meas(yy[0][o:], t, tgt), tgt) for t in np.linspace(a + .15, b - .15, 5)]
        res.append('YIN median %+.1f (10..90 %% %+.1f..%+.1f), FFT median %+.1f' % (np.median(m), np.percentile(m, 10), np.percentile(m, 90), np.median(f)))
    print('held notes %s, cents off the line:\n   %s' % (lab, '\n   '.join(res)))
# the real sung phrase: does the converted voice keep the notes that were sung? (frame by frame, voiced in both)
fs_ = librosa.yin(sung, fmin=150, fmax=900, sr=SR, frame_length=4096, hop_length=480); fa = librosa.yin(ySung[0][o:o + len(sung)], fmin=150, fmax=900, sr=SR, frame_length=4096, hop_length=480)
_, vs_, _ = librosa.pyin(sung[::2], fmin=150, fmax=900, sr=SR // 2, frame_length=2048, hop_length=240); n = min(len(fs_), len(fa), len(vs_))
d = 1200 * np.log2(fa[:n] / fs_[:n]); d = d[vs_[:n]]; d = d - 1200 * np.round(d / 1200)
print('real sung phrase converted: pitch against the sung pitch, median %+.1f cents, median abs %.1f, 90 %% within %.1f cents (%d voiced frames)' % (np.median(d), np.median(np.abs(d)), np.percentile(np.abs(d), 90), len(d)))
# ---- 6. clicks: the largest jump between samples, against the 99.9th percentile of the jumps (a click stands out)
for n, yy in (('sung (input)', sung), ('sung', ySung[0]), ('talk (input)', talk), ('talk', yTalk[0]), ('synth (input)', syn), ('synth', ye[0])):
    d = np.abs(np.diff(yy)); print('clicks %s: largest step %.4f, 99.9 %% step %.4f, ratio %.1f' % (n, d.max(), np.percentile(d, 99.9), d.max() / max(np.percentile(d, 99.9), 1e-9)))
# ---- 7. formant and breath change at once (no AI needed), Back to the recording, the original is unchanged
al.run("(()=>{const W=document.getElementById('vaiWin');const s=W.querySelector('[data-va=aiFm]');s.value='2';s.dispatchEvent(new Event('change',{bubbles:true}));1})()"); al.page.wait_for_timeout(2500)
print('formant +2 applied to the clip:', al.run("%s.clips[0].vx.ai.fm" % T('Sung')))
print('originals unchanged:', {n: md5(n) == h0[n] for n in h0})
# ---- 8. choir: two saved voices and a built-in one at once
a4 = convert('Talk', 'Singer B (talking)', {'aiLay': [vid['Speaker A (talking)'], 'b:high']})
yc = rend('Talk', len(talk) / SR); print('choir: layers', len(a4['lay']), 'channels', yc.shape[0], 'left/right difference %.1f dB' % (20 * np.log10(np.sqrt(np.mean((yc[0] - yc[1]) ** 2)) / np.sqrt(np.mean(yc[0] ** 2)))))
sf.write(os.path.join(out, 'ai_talk_choir.wav'), yc.T, SR)
# built-in voice alone
for b in ('b:low', 'b:high'):
    vid[b] = b; convert('Talk', b); sf.write(os.path.join(out, 'ai_talk_%s.wav' % b[2:]), rend('Talk', len(talk) / SR).T, SR)
# ---- 9. undo back to the recording, reload survival of the rendered copy
al.run("(()=>{const c=%s.clips[0];c.buf='gone';vxRestore();1})()" % T('Sung')); al.page.wait_for_timeout(4000)
print('rendered AI copy made again after a reload (restore):', al.run("BUFS.has(%s.clips[0].buf)&&%s.clips[0].buf!==%s.clips[0].vx.buf" % (T('Sung'), T('Sung'), T('Sung'))))
act('Sung', 'ai'); al.page.wait_for_timeout(500); shot('ai_ready.png')
W = json.loads(al.run("(()=>{const r=document.getElementById('vaiWin').getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:r.width,height:r.height})})()"))
al.page.screenshot(path=os.path.join(out, 'ai_window.png'), clip=W)
al.page.set_viewport_size({'width': 640, 'height': 900}); al.page.wait_for_timeout(400); shot('ai_narrow.png'); al.page.set_viewport_size({'width': 1600, 'height': 1000})
print('page errors', al.errors)
try:   # speaker similarity: WavLM-base-plus-sv (Microsoft) cosine between x-vectors; 0.86 is the model card's same-speaker threshold
    import torch, soxr
    from transformers import AutoFeatureExtractor, WavLMForXVector
    fe = AutoFeatureExtractor.from_pretrained("microsoft/wavlm-base-plus-sv"); mm = WavLMForXVector.from_pretrained("microsoft/wavlm-base-plus-sv").eval()
    def xv(y):
        y = np.asarray(y, np.float32); y = y.mean(0) if y.ndim > 1 else y; y = soxr.resample(y, SR, 16000)[:16000 * 20]
        with torch.no_grad(): e = mm(**fe(y, sampling_rate=16000, return_tensors='pt')).embeddings[0]
        return torch.nn.functional.normalize(e, dim=-1).numpy()
    eA, eB = xv(refA), xv(refB)
    for lab, e, ys in (('sung phrase vs Speaker A', eA, (('before', ySung0), ('AI, keep my notes', ySung), ('AI, nearest octave', ySungO))), ('talking vs Singer B', eB, (('before', yTalk0), ('AI, keep my notes', yTalk), ("AI, the voice's own range", yTalkO)))):
        print('speaker similarity %s: %s' % (lab, ', '.join('%s %.3f' % (n, float(np.dot(xv(y), e))) for n, y in ys)))
except ImportError as e: print('speaker similarity skipped:', e)
al.stop(); srv.terminate()
