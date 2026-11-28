"""Processor use in front and in the background (task AO, v0.218), headless Chromium: python3 tools/ui-tests/taskAO_cpu.py [index.html] [seconds per measurement]
Reads the processor time of the browser's processes from Linux (/proc/<pid>/stat): the page's process (renderer) and everything else (browser, GPU
process, audio service), in % of one core. The page's visibility and focus are emulated, as in taskAO.py. Works on older versions too (they do not
react, which is the "before"). The numbers of the real desktop app come from taskAO_electron.js."""
import sys, os, time
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'; SECS = float(sys.argv[2]) if len(sys.argv) > 2 else 20
SRC = open(F, encoding='utf-8').read(); CLK = os.sysconf('SC_CLK_TCK')
INIT = r"""
(()=>{const T=window.__t={hidden:false,focus:true,raf:0,iv:0,to:0};
 Object.defineProperty(Document.prototype,'visibilityState',{configurable:true,get(){return T.hidden?'hidden':'visible'}});
 Object.defineProperty(Document.prototype,'hidden',{configurable:true,get(){return T.hidden}});
 Document.prototype.hasFocus=function(){return T.focus&&!T.hidden};
 const raf=window.requestAnimationFrame.bind(window);window.requestAnimationFrame=function(f){return raf(function(t){T.raf++;return f(t)})};
 const si=window.setInterval.bind(window);window.setInterval=function(f,ms,...a){return si(function(){T.iv++;return f.apply(this,arguments)},ms,...a)};
 const st=window.setTimeout.bind(window);window.setTimeout=function(f,ms,...a){return st(function(){T.to++;return typeof f==='function'?f.apply(this,arguments):0},ms,...a)};
 window.__go=function(kind){if(kind==='front'){T.hidden=false;T.focus=true;document.dispatchEvent(new Event('visibilitychange'));window.dispatchEvent(new Event('focus'))}
  else if(kind==='blur'){T.focus=false;window.dispatchEvent(new Event('blur'));document.documentElement.dispatchEvent(new MouseEvent('mouseleave'))}
  else{T.focus=false;T.hidden=true;window.dispatchEvent(new Event('blur'));document.dispatchEvent(new Event('visibilitychange'))}}})();
if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))
"""
def snap(mark):
    P = {}
    for d in os.listdir('/proc'):
        if not d.isdigit(): continue
        try:
            cmd = open('/proc/%s/cmdline' % d, 'rb').read().replace(b'\0', b' ').decode('utf8', 'ignore'); st = open('/proc/%s/stat' % d).read()
        except Exception: continue
        r = st[st.rindex(')') + 2:].split(); P[int(d)] = (int(r[1]), cmd, (int(r[11]) + int(r[12])) / CLK)
    root = [pid for pid, (pp, c, t) in P.items() if mark in c and '--type=' not in c][0]; keep = {root}; ch = True
    while ch:
        ch = False
        for pid, (pp, c, t) in P.items():
            if pp in keep and pid not in keep: keep.add(pid); ch = True
    return sum(P[i][2] for i in keep if '--type=renderer' in P[i][1]), sum(P[i][2] for i in keep if '--type=renderer' not in P[i][1]), time.time()
with sync_playwright() as p:
    mark = '--al-mark=%d' % os.getpid()
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required', mark]); pg = b.new_page(viewport={'width': 1600, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404, body=b'')))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_timeout(8000)
    R = lambda c: pg.evaluate("c=>window.AudioLab.run(c)", c)
    R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();pmSetOn(false);if(typeof AOG!=='undefined')AOG.boot=0;return 1})()")
    pg.mouse.click(800, 30); pg.wait_for_timeout(45000)   # the clip renders ahead that follow a start are not what is measured
    print('version', R('VERSION'), '| Full effects | page errors', errs)
    def measure(label):
        c0 = pg.evaluate("()=>({raf:__t.raf,iv:__t.iv,to:__t.to})"); a = snap(mark); pg.wait_for_timeout(int(SECS * 1000)); z = snap(mark); c1 = pg.evaluate("()=>({raf:__t.raf,iv:__t.iv,to:__t.to})"); dt = z[2] - a[2]
        print('%-44s page %5.2f %%, browser + GPU + audio %5.2f %% of one core | %5.1f frames, %5.1f timer ticks, %4.1f one-shot timers a second | audio %s' % (label, (z[0] - a[0]) / dt * 100, (z[1] - a[1]) / dt * 100, (c1['raf'] - c0['raf']) / SECS, (c1['iv'] - c0['iv']) / SECS, (c1['to'] - c0['to']) / SECS, R("ctx?ctx.state:'none'")), flush=True)
    measure('in front, nothing playing')
    pg.evaluate("()=>window.__go('blur')"); pg.wait_for_timeout(12000); measure('another app in front (window visible)')
    pg.evaluate("()=>window.__go('front')"); pg.wait_for_timeout(2000); pg.evaluate("()=>window.__go('hide')"); pg.wait_for_timeout(12000); measure('hidden or minimised')
    R("(()=>{pos=64;start();return 1})()"); pg.wait_for_timeout(3000); measure('hidden, playing from beat 64'); R("(()=>{stop();return 1})()")
    pg.evaluate("()=>window.__go('front')"); pg.wait_for_timeout(1500); R("(()=>{pos=64;start();return 1})()"); pg.wait_for_timeout(3000); measure('in front, playing from beat 64'); R("(()=>{stop();return 1})()")
    b.close()
