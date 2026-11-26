"""AI voices in the real desktop app (Electron, main.js + preload.js + voice-ai.js in a utility process), driven over the DevTools port.
Start the app first:  xvfb-run electron --no-sandbox --remote-debugging-port=9333 desktop   (with desktop/app/index.html synced)
  python3 tools/ui-tests/aivoice_electron.py [out dir] [test audio dir]
Checks: no page errors after a reload, the bridge is there, the model downloads from Hugging Face with progress and checksum,
a voice is made from a clip, a clip is converted, files in userData."""
import sys, os, json, time
import numpy as np, soundfile as sf, soxr
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'remake'))
from alab import AudioLab
from playwright.sync_api import sync_playwright
out = sys.argv[1] if len(sys.argv) > 1 else '.'; adir = sys.argv[2] if len(sys.argv) > 2 else '/tmp/claude-0/testaudio'
class AE(AudioLab):
    def start(self):
        self._pw = sync_playwright().start(); self.browser = self._pw.chromium.connect_over_cdp('http://127.0.0.1:9333')
        self.page = [p for c in self.browser.contexts for p in c.pages if p.url.startswith('audiolab://')][0]; self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)[:400]))
        self.page.reload(); self.page.wait_for_function("() => window.AudioLab && window.AudioLab.version", timeout=60000); self.page.wait_for_timeout(2500)
        self.version = self.js("() => AudioLab.version"); return self
    def stop(self): self._pw.stop()
al = AE('index.html'); al.start(); print('desktop app: version', al.version, 'page errors after reload', al.errors)
print('bridge:', al.run("!!(window.audiolabDesktop&&window.audiolabDesktop.voiceAI)"))
SR = 48000
ld = lambda n: soxr.resample(*(lambda x, s: (x.mean(1), s))(*sf.read(os.path.join(adir, n), dtype='float32', always_2d=True)), SR).astype(np.float32)
talk, refB = ld('talk.wav'), ld('refB.wav'); ids = [al.add_audio(a[None, :], SR) for a in (talk, refB)]
mk = lambda nm, i, a: {'name': nm, 'kind': 'audio', 'fx': [{'type': 'voice'}], 'clips': [{'start': 0, 'len': len(a) / SR / .5, 'buf': ids[i], 'dur': len(a) / SR, 'gain': 0, 'fi': 0, 'fo': 0, 'name': nm + ' clip'}]}
al.build({'bpm': 120, 'tracks': [mk('Talk', 0, talk), mk('Voice B', 1, refB)]}); al.run("selT=S.tracks[0].id;renderFx();1"); al.page.wait_for_timeout(500)
wait = lambda c, ms=600000: al.page.wait_for_function("()=>window.AudioLab.run(%s)" % json.dumps(c), timeout=ms)
al.run("window._d=0;(async()=>{const t=S.tracks[0];await NACT.voice(t.fx[0],'ai',t);window._d=1})();1"); wait('window._d===1')
print('window says:', al.run("document.querySelector('#vaiWin .vainfo').textContent")[:140])
al.page.screenshot(path=os.path.join(out, 'electron_ai_download.png'))
t0 = time.time(); al.page.click('#vaiWin [data-va="dl"]'); al.page.wait_for_timeout(700)
mid = al.run("VAI.msg"); wait("!!(VAI.st&&VAI.st.model.have)", 300000)
print('download: %.1f s; message during it: %s; after: %s' % (time.time() - t0, mid, al.run("VAI.msg")))
i = al.run("vaiClips().findIndex(o=>o.t.name==='Voice B')")
al.run("(()=>{const W=document.getElementById('vaiWin');W.querySelector('[data-va=src]').value='%d';W.querySelector('[data-va=name]').value='Singer B';W.querySelector('[data-va=make]').click();1})()" % i)
al.page.wait_for_timeout(300); wait('!VAI.busy'); print('make voice:', al.run("VAI.msg"))
al.run("(()=>{const f=S.tracks[0].fx[0];f.p.aiV=VAI.voices.find(v=>v.name==='Singer B').id;f.p.aiFit='own';1})()")
al.run("window._d=0;(async()=>{const t=S.tracks[0];await vaiConvert(t.fx[0],t);window._d=1})();1"); wait('window._d===1')
print('convert:', al.run("VAI.msg"), json.loads(al.run("JSON.stringify({cal:S.tracks[0].clips[0].vx.ai.cal,ms:S.tracks[0].clips[0].vx.ai.ms,plays:S.tracks[0].clips[0].buf!==S.tracks[0].clips[0].vx.buf})")))
al.run("vaiOpen(S.tracks[0].fx[0]);1"); al.page.wait_for_timeout(800); al.page.screenshot(path=os.path.join(out, 'electron_ai_ready.png'))
ud = os.path.expanduser('~/.config/AudioLab Studio/voice-ai')
for r, d, fs in os.walk(ud):
    for f in fs: print('  userData:', os.path.relpath(os.path.join(r, f), ud), os.path.getsize(os.path.join(r, f)))
print('page errors', al.errors); al.stop()
