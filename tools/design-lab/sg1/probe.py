import sys, os, json
sys.path.insert(0,'/home/claude/alp/tools/remake')
from alab import AudioLab
from playwright.sync_api import sync_playwright
class AL(AudioLab):
    def start(self, iso=True):
        self._pw=sync_playwright().start()
        self.browser=self._pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        self.ctx=self.browser.new_context(viewport={"width":1600,"height":1000})
        self.page=self.ctx.new_page(); self.errors=[]; self.logs=[]
        self.page.on("pageerror",lambda e:self.errors.append(str(e)[:400]))
        self.page.on("console",lambda m:self.logs.append(m.text[:300]))
        src=open(self.index,encoding="utf-8").read()
        H={"Cross-Origin-Opener-Policy":"same-origin","Cross-Origin-Embedder-Policy":"require-corp","Cross-Origin-Resource-Policy":"cross-origin"} if iso else {}
        D='/home/claude/sg1w/ort/package/dist/'; M='/home/claude/sg1w/model/'
        def handle(route):
            u=route.request.url
            if 'cdn.jsdelivr.net/npm/onnxruntime-web' in u:
                f=D+u.split('/dist/')[1].split('?')[0]
                ct='application/wasm' if f.endswith('.wasm') else 'application/javascript'
                if os.path.exists(f): route.fulfill(path=f,content_type=ct,headers=H|{"Access-Control-Allow-Origin":"*"}); return
                route.fulfill(status=404,body='',headers=H); return
            if 'huggingface.co' in u:
                f=M+('htdemucs_6s.onnx' if '6s' in u else 'htdemucs_fp16weights.onnx')
                route.fulfill(path=f,content_type='application/octet-stream',headers=H|{"Access-Control-Allow-Origin":"*"}); return
            if u.startswith('https://app.test/') and (u.endswith('/') or u.endswith('index.html')):
                route.fulfill(body=src,content_type='text/html',headers=H); return
            route.fulfill(status=404,body='',headers=H)
        self.ctx.route("**/*",handle)
        self.page.goto("https://app.test/")
        self.page.wait_for_function("() => window.AudioLab && window.AudioLab.version",timeout=60000)
        self.page.wait_for_timeout(2500)
        self.version=self.js("() => AudioLab.version"); return self
if __name__=='__main__':
    al=AL('/home/claude/alp/index.html'); al.start()
    print(al.version, al.run("({iso:self.crossOriginIsolated,cores:navigator.hardwareConcurrency,tracks:S.tracks.map(t=>t.name),bpm:S.bpm,end:typeof songEnd==='function'?songEnd():null})"))
    print(al.errors[:3]); al.stop()
