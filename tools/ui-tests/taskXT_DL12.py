"""Task XT-DL12: the script sandbox spike (docs/extensions-plan.md 9.6 e, docs/script-sandbox.md).
The escape tests: user code run through xtSandboxRun tries every way out (network in seven forms, more code, eval, the page's globals,
storage, a channel to the page, forged messages) and each must fail; a local server counts requests and must see none from the sandbox
(and one from the page itself, the control). Then the time limit (an endless loop stopped at the limit while the page keeps drawing and the
sound keeps playing), "wait or stop", a memory bomb (its process dies, the page lives), the caps, error lines, and that with nothing asking
for it no frame, worker or listener exists. Run twice: as the browser version, and cross-origin isolated as the desktop app serves it.
Chromium is started with site isolation on, as Chrome and Electron have it (Playwright turns it off by default).
  python3 tools/ui-tests/taskXT_DL12.py [index.html] [out dir] [--quick]   (--quick leaves out the memory bomb)"""
import sys, os, json, threading, http.server, time
from playwright.sync_api import sync_playwright
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
QUICK = '--quick' in sys.argv
SRCB = open(ARGS[0] if ARGS else 'index.html', 'rb').read()
OUT = ARGS[1] if len(ARGS) > 1 else '.'; os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
HITS = []
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(s):
        if s.path in ('/app', '/appi'):
            s.send_response(200); s.send_header('Content-Type', 'text/html; charset=utf-8'); s.send_header('Cache-Control', 'no-store')
            if s.path == '/appi': s.send_header('Cross-Origin-Opener-Policy', 'same-origin'); s.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
            s.end_headers(); s.wfile.write(SRCB); return
        if s.path.startswith('/coi-serviceworker'): s.send_response(404); s.end_headers(); return   # the page's own request, not the sandbox's
        HITS.append(s.path); s.send_response(200); s.send_header('Access-Control-Allow-Origin', '*'); s.send_header('Cross-Origin-Resource-Policy', 'cross-origin')
        s.send_header('Content-Type', 'text/javascript'); s.end_headers(); s.wfile.write(b'self.leak=1;')
    def log_message(s, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H); U = 'http://127.0.0.1:%d' % srv.server_port
threading.Thread(target=srv.serve_forever, daemon=True).start()
INIT = "try{if(!sessionStorage.getItem('dl12')){sessionStorage.setItem('dl12','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}}catch(e){}"
B = "'blocked '+(e&&e.name||e)"
ESC = [
 ('fetch', "try{await fetch('%s/fetch');return 'LEAK'}catch(e){return %s}" % (U, B)),
 ('fetch, no-cors', "try{await fetch('%s/nocors',{mode:'no-cors'});return 'LEAK'}catch(e){return %s}" % (U, B)),
 ('XMLHttpRequest', "try{const x=new XMLHttpRequest();x.open('GET','%s/xhr',false);x.send();return 'LEAK'}catch(e){return %s}" % (U, B)),
 ('WebSocket', "return await new Promise(r=>{let s;try{s=new WebSocket('%s/ws')}catch(e){return r(%s)}s.onopen=()=>r('LEAK');s.onerror=()=>r('blocked error');setTimeout(()=>r('blocked timeout'),1500)})" % (U.replace('http', 'ws'), B)),
 ('EventSource', "return await new Promise(r=>{let s;try{s=new EventSource('%s/es')}catch(e){return r(%s)}s.onopen=()=>r('LEAK');s.onerror=()=>{s.close();r('blocked error')};setTimeout(()=>r('blocked timeout'),1500)})" % (U, B)),
 ('importScripts', "try{importScripts('%s/imp.js');return 'LEAK'}catch(e){return %s}" % (U, B)),
 ('import()', "try{await import('%s/dyn.js');return 'LEAK'}catch(e){return %s}" % (U, B)),
 ('a nested worker', "try{new Worker('%s/w.js');return 'LEAK'}catch(e){return %s}" % (U, B)),
 ('a nested worker from a blob (made, with the same walls)', "try{const w=new Worker(URL.createObjectURL(new Blob(['let r=\"blocked\";try{eval(\"1\");r=\"LEAK eval\"}catch(e){}fetch(\"%s/nb\").then(()=>postMessage(\"LEAK\"),()=>postMessage(r))'])));return await new Promise(r=>{w.onmessage=e=>r(e.data);setTimeout(()=>r('blocked timeout'),1500)})}catch(e){return %s}" % (U, B)),
 ('eval', "try{return 'LEAK '+eval('1+1')}catch(e){return %s}" % B),
 ('new Function', "try{return 'LEAK '+Function('return 2')()}catch(e){return %s}" % B),
 ('setTimeout with a string', "try{setTimeout('self.st=1');await new Promise(r=>setTimeout(r,200));return self.st?'LEAK':'blocked (not run)'}catch(e){return %s}" % B),
 ('indexedDB', "try{indexedDB.open('x');return 'LEAK'}catch(e){return %s}" % B),
 ('caches', "try{await caches.open('x');return 'LEAK'}catch(e){return %s}" % B),
]
GLOB = "return {origin:self.origin,names:['window','document','parent','top','opener','localStorage','sessionStorage','UI','AudioLab','audiolabDesktop','SharedArrayBuffer','require','process','navigator.sendBeacon'].filter(n=>{try{return n.split('.').reduce((o,k)=>o==null?undefined:o[k],self)!==undefined}catch(e){return false}})}"
def run_pass(p, coep, tag):
    HITS.clear()
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required', '--site-per-process'], ignore_default_args=['--disable-site-isolation-trials'])
    pg = b.new_page(viewport={'width': 1400, 'height': 900}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.add_init_script(INIT)
    pg.goto(U + ('/appi' if coep else '/app')); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(2500)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    SB = lambda code, o='{}': pg.evaluate('([c,o]) => xtSandboxRun(c, eval("("+o+")"))', [code, o])
    if coep: ok(J('crossOriginIsolated') is True, tag + 'the page is cross-origin isolated, as in the desktop app')
    else: ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 291), tag + 'version 0.291 or later', R('VERSION'))
    R("openDemoFractals()"); pg.wait_for_timeout(5000); R("play.on||toggle()"); pg.wait_for_timeout(1500)
    ok(J("XT_SBX.n") == 0 and J("document.querySelectorAll('iframe[data-xt-sbx]').length") == 0 and J("XT_SBX.runs.size") == 0,
       tag + 'with nothing asking for it: no sandbox frame, no worker, no run (start, a song, playing): it costs nothing')
    r = SB("console.log('hello',{a:1});console.warn('w');al.change({track:al.input.t,color:'#f00'});return al.input.t*2", "{input:{t:21}}")
    ok(r['ok'] and r['value'] == 42 and r['changes'] == [{'track': 21, 'color': '#f00'}] and [l['v'] for l in r['logs']] == ['hello {"a":1}', 'w'] and r['logs'][1]['k'] == 'warn',
       tag + 'a script runs: reads its input copy, logs, records a change, returns a value', (r['value'], r['changes'], r['logs'], r['ms']))
    ok(r['ms'] < 1500, tag + 'a run (fresh frame and worker) starts and ends quickly', '%d ms' % r['ms'])
    ok(J("document.querySelectorAll('iframe[data-xt-sbx]').length") == 0 and J("XT_SBX.runs.size") == 0, tag + 'a finished run leaves nothing behind (frame and worker gone)')
    r = SB("try{al.input.t=5}catch(e){return 'frozen'}return 'changed'", "{input:{t:1}}")
    ok(r['value'] == 'frozen', tag + 'the input is a frozen copy', r['value'])
    # escape attempts
    pg.evaluate("()=>{window.__bcGot=0;window.__bc=new BroadcastChannel('xt-probe');__bc.onmessage=()=>__bcGot++}")
    for name, code in ESC:
        r = SB(code, '{limit:4000}')
        v = str(r['value'])
        ok(r['ok'] and v.startswith('blocked'), tag + 'escape refused: ' + name, v[:90])
    r = SB("new BroadcastChannel('xt-probe').postMessage('hi');await new Promise(r=>setTimeout(r,300));return 'sent'")
    pg.wait_for_timeout(300)
    ok(J("window.__bcGot") == 0, tag + 'escape refused: a BroadcastChannel to the page (the sandbox has another origin)', J("window.__bcGot"))
    r = SB(GLOB)
    ok(r['ok'] and r['value']['names'] == [] and r['value']['origin'] == 'null', tag + 'no window, document, parent, storage, app globals, desktop bridge, SharedArrayBuffer or Node; origin null', r['value'])
    r = SB("self.postMessage({t:'done',v:'forged'});try{postMessage({t:'chg',v:'x'})}catch(e){};await new Promise(r=>setTimeout(r,200));return 'real'")
    ok(r['value'] == 'real' and r['changes'] == [], tag + 'a script cannot forge the messages the page reads', (r['value'], r['changes']))
    r = SB("}; self.__xtGo=async()=>'replaced'; (async function(){")
    ok(r['value'] in (None, 'replaced'), tag + 'breaking out of the wrapper only reaches the worker itself (no new power)', (r['ok'], r['value'], r['error']))
    pg.wait_for_timeout(600)
    ok(not HITS, tag + 'the local server saw no request from the sandbox', HITS)
    pg.evaluate("fetch('%s/control',{mode:'no-cors'}).catch(()=>0)" % U); pg.wait_for_timeout(500)
    ok(HITS == ['/control'], tag + 'control 1: the same server is reachable from the page itself', HITS)
    R("XT_SBX.__csp=XT_SBX.CSP;XT_SBX.CSP=\"script-src 'unsafe-inline' blob:; worker-src blob:\"")
    r = SB("try{await fetch('%s/control2',{mode:'no-cors'});return 'reached'}catch(e){return 'blocked '+e.name}" % U)
    R("XT_SBX.CSP=XT_SBX.__csp;delete XT_SBX.__csp"); pg.wait_for_timeout(300)
    ok(r['value'] == 'reached' and HITS == ['/control', '/control2'], tag + 'control 2: the same sandbox with its policy lifted reaches the server, so the walls above come from the policy', (r['value'], HITS))
    # errors with their line
    r = SB("const a=1;\nconst b=2;\nreturn (")
    ok(not r['ok'] and 'SyntaxError' in (r['error'] or '') and r['line'] == 3, tag + 'a syntax error is reported, at the last line of the user\'s code', (r['error'], r['line']))
    r = SB("const a=1;\nthrow new Error('boom');")
    ok(not r['ok'] and r['error'] == 'boom' and r['line'] == 2, tag + 'an error is reported with its line in the user\'s code', (r['error'], r['line']))
    # time limit: an endless loop while the page draws and plays
    pg.evaluate("window.__tk=0;(function f(){__tk++;if(window.__tkOn!==false)requestAnimationFrame(f)})()")
    t0 = J("[__tk, ctx.currentTime]")
    r = SB("while(true){}", "{limit:1000}")
    t1 = J("[__tk, ctx.currentTime]")
    ok(r['stopped'] == 'time' and 900 <= r['ms'] <= 1600, tag + 'an endless loop is stopped at the limit (1 s here, 2 s by default)', (r['stopped'], r['ms'], r['error']))
    ok(t1[0] - t0[0] >= 20 and t1[1] - t0[1] > 0.8, tag + 'meanwhile the page kept drawing and the sound kept playing', (t1[0] - t0[0], round(t1[1] - t0[1], 2)))
    ok(J("document.querySelectorAll('iframe[data-xt-sbx]').length") == 0, tag + 'the stopped script\'s frame is gone')
    r = pg.evaluate("""() => { let n=0; return xtSandboxRun('let i=0;for(;;){i++}', {limit:600, onSlow: ms => { n++; return n<2 }}).then(r => (r.asked=n, r)) }""")
    ok(r['stopped'] == 'user' and r['asked'] == 2 and 1100 <= r['ms'] <= 1800, tag + 'wait or stop (K9b): onSlow is asked at each limit; "wait" gives it one more, "stop" ends it', (r['stopped'], r['asked'], r['ms']))
    r = SB("await new Promise(r=>setTimeout(r,1700));return 'patient'", "{limit:2000}")
    ok(r['ok'] and r['value'] == 'patient', tag + 'a script that waits 1.7 s finishes (the heartbeat does not misfire)', (r['value'], r['error'], r['ms']))
    r = pg.evaluate("() => { const p = xtSandboxRun('for(;;){}', {limit:10000}); setTimeout(() => xtSandboxStop(), 300); return p }")
    ok(r['stopped'] == 'user' and r['ms'] < 1000, tag + 'xtSandboxStop() stops a running script at once', (r['stopped'], r['ms']))
    # caps
    r = SB("for(let i=0;i<300;i++)console.log(i);return 1")
    ok(len(r['logs']) == 200, tag + 'logs are capped at 200 lines', len(r['logs']))
    r = SB("const s='x'.repeat(5000);for(let i=0;i<400;i++)al.change({s});return 1")
    ok(r['stopped'] == 'size', tag + 'more than 1 MB sent back stops the script', (r['stopped'], len(r['changes'])))
    r = SB("//" + 'x' * 270000)
    ok(not r['ok'] and '256 kB' in r['error'], tag + 'a script over 256 kB is refused before it runs', r['error'])
    r = pg.evaluate("() => { const o = {a: 1}; o.self = o; return xtSandboxRun('return 1', {input: o}) }")
    ok(not r['ok'] and r['error'] == 'the input is not plain data', tag + 'input that is not plain data (a loop) is refused', r['error'])
    # memory bomb
    if not QUICK and not coep:
        pg.evaluate("window.__tk=0")
        r = SB("const a=[];for(;;){a.push({x:Math.random(),y:[1,2,3],s:'abc'+a.length})}", "{limit:90000}")
        ok(r['stopped'] == 'memory', tag + 'a script that eats all memory: its own process dies and the run is stopped', (r['stopped'], r['ms'], r['error']))
        ok(J("__tk") > 100 and J("1+1") == 2, tag + 'the page lived on and kept drawing meanwhile', J("__tk"))
        r = SB("return 'again'")
        ok(r['value'] == 'again', tag + 'and the next script runs normally', r['value'])
    R("play.on&&toggle()")
    ok(J("document.querySelectorAll('iframe[data-xt-sbx]').length") == 0 and J("XT_SBX.runs.size") == 0, tag + 'after all of it: no frame, no run left')
    pg.screenshot(path=os.path.join(OUT, 'xt_dl12_%s.png' % ('coep' if coep else 'browser')))
    errs = [e for e in errs if 'Content Security Policy' not in e and 'xt-probe' not in e]
    ok(not errs, tag + 'no console errors', errs[:5])
    b.close()
with sync_playwright() as p:
    run_pass(p, False, '')
    run_pass(p, True, 'isolated: ')
print('%d of %d checks passed' % (N[1], N[0]))
sys.exit(1 if FAIL else 0)
