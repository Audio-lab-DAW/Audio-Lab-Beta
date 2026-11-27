#!/usr/bin/env python3
"""Task DS-T2 (design round 2, TM1, TC1, TS1): the transport meter with a dB scale and hold, the CPU as the last
10 seconds as a line, the top bar's status line (audio format and save state).
   python3 tools/ui-tests/taskDS_T2.py [index.html] [--shots OUTDIR]
At the user's size (2194 x 1139 CSS px at 1.75x) with Fractals, Dark (glass) and Light. SwiftShader: correctness only."""
import sys, json, os
from playwright.sync_api import sync_playwright
F = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'index.html'
SHOTS = sys.argv[sys.argv.index('--shots') + 1] if '--shots' in sys.argv else None
SRC = open(F, encoding='utf-8').read()
ARGS = ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
INIT = "if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))"
FAIL = []; N = [0]
def ok(c, m, d=''):
    N[0] += 1; print(('ok   ' if c else 'FAIL ') + m + (('   ' + str(d)) if d != '' else ''), flush=True)
    if not c: FAIL.append(m)

# pixels of the meter: the tick row, the bar rows, the label row (CSS px from the canvas's top left)
MTR = r"""(()=>{const c=$('#mtr'),g=c.getContext('2d'),r=fitRect(c),k=c.width/(r.width/ZOOM),w=r.width/ZOOM,h=r.height/ZOOM,sx=d=>clamp((d+60)/66,0,1)*w;
  const P=(x,y)=>Array.from(g.getImageData(Math.min(c.width-1,Math.round(x*k)),Math.min(c.height-1,Math.round(y*k)),1,1).data).slice(0,3);
  let lab=0;for(let x=sx(-24)-5;x<sx(-24)+5;x+=.5)for(let y=h-7;y<h;y+=.5){const p=P(x,y);if(p[0]+p[1]+p[2]>200)lab++}
  return{h,w,tick12:P(sx(-12)+.3,1),tick0:P(sx(0)+.3,1),gap:P(sx(-30),1),lab,pk:$('#pkNow').textContent}})()"""
CPUPX = r"""(()=>{const c=$('#cpuC'),g=c.getContext('2d'),d=g.getImageData(0,0,c.width,c.height).data;let gr=0,n=0;for(let i=0;i<d.length;i+=4){n++;if(d[i+1]>50&&d[i+1]>d[i]+25)gr++}return{gr,n,frac:gr/n}})()"""

def load(p, logs):
    ctx = p.chromium.launch(args=ARGS).new_context(viewport={'width': 2194, 'height': 1139}, device_scale_factor=1.75); pg = ctx.new_page()
    pg.on('console', lambda m: logs.append(m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text else None)
    pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body=''))
    pg.add_init_script(INIT); pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=90000); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    R("pmSetOn(false)"); R("openDemoFractals()"); pg.wait_for_timeout(6000)
    return pg, R

with sync_playwright() as p:
    logs = []
    pg, R = load(p, logs)
    J = lambda c: json.loads(R("JSON.stringify(" + c + ")"))
    print('version', R("VERSION"))
    f = J("['dsT2Mtr','dsT2Cpu','dsT2CpuPush','dsT2Stat','dsT2Ago'].map(n=>typeof window[n]).concat([typeof DS_HOOKS])")
    ok(all(x in ('function', 'object') for x in f), 'the DS-T2 helpers and DS_HOOKS exist', f)
    R("play.on||toggle()"); pg.wait_for_timeout(3500)
    for mode in ['dark', 'light']:
        R("pmSetOn(%s)" % ('true' if mode == 'light' else 'false')); pg.wait_for_timeout(2500)
        m = J(MTR)
        ok(sum(m['tick12']) > 250 and sum(m['gap']) < 60, mode + ': scale ticks above the bars', [m['tick12'], m['gap']])
        ok(m['tick0'][0] > 150 and m['tick0'][0] > m['tick0'][1] + 60, mode + ': the 0 dB tick in red', m['tick0'])
        ok(m['lab'] > 4, mode + ': dB labels under the bars', m['lab'])
        ok(m['pk'].endswith('dBFS'), mode + ': the peak read-out in dBFS', m['pk'])
        c = J(CPUPX)
        ok(0.02 < c['frac'] < 0.35, mode + ': the CPU as a line (not a filled area)', c)
        st = J("(()=>{const e=$('#dsStat');return{h:e.hidden,t:e.textContent,tip:e.title}})()")
        ok(not st['h'] and 'kHz' in st['t'] and '32-bit float' in st['t'], mode + ': the status line shows the audio format', st['t'])
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True)
            r = J("(()=>{const a=document.querySelector('.mgrp').getBoundingClientRect(),b=$('#cpu').getBoundingClientRect();return{x:a.left-10,y:a.top-8,w:b.right-a.left+20,h:a.height+16}})()")
            pg.screenshot(path=f'{SHOTS}/{mode}-t2-transport.png', clip={'x': r['x'], 'y': r['y'], 'width': r['w'], 'height': r['h']})
            pg.screenshot(path=f'{SHOTS}/{mode}-t2-top.png', clip={'x': 0, 'y': 0, 'width': 2194, 'height': 34})
            pg.screenshot(path=f'{SHOTS}/{mode}-t2-win.png')
    R("pmSetOn(false)"); pg.wait_for_timeout(800)
    n0 = J("DST2.n"); pg.wait_for_timeout(2000); n1 = J("DST2.n")
    ok(5 <= n1 - n0 <= 10, 'one CPU point per 250 ms while playing', n1 - n0)
    ok(J("tmRects().some(([a,b])=>{const r=$('#dsStat').getBoundingClientRect(),q=$('#ptabs').getBoundingClientRect();return Math.abs(a-(r.left-q.left)/ZOOM)<2})"), 'the playhead time hides behind the status line like behind a tab')
    # save states
    s1 = J("(()=>{const p=PJ.list.find(q=>q.id===PJ.cur);p.dirty=true;dsT2Stat();const e=$('#dsStat');return[e.textContent,e.dataset.s]})()")
    ok(s1[0].endswith('unsaved changes') and s1[1] == 'chg', 'unsaved changes with an amber dot', s1)
    s2 = J("(()=>{const p=PJ.list.find(q=>q.id===PJ.cur);p.dirty=false;p.file='Fractals.audiolab';p.savedAt=Date.now()-125000;dsT2Stat();const e=$('#dsStat');return[e.textContent,e.dataset.s,getComputedStyle(e.firstChild).backgroundColor]})()")
    ok(s2[0].endswith('saved 2 min ago') and s2[1] == 'ok' and '62, 207, 142' in s2[2], 'saved 2 min ago with a green dot', s2)
    s3 = J("(()=>{const p=PJ.list.find(q=>q.id===PJ.cur);delete p.file;delete p.savedAt;DS_HOOKS.status=()=>'Kick to Master';dsT2Stat();const t=$('#dsStat').textContent;DS_HOOKS.status=null;dsT2Stat();return[t,$('#dsStat').textContent]})()")
    ok('Kick to Master' in s3[0] and s3[1].endswith('not saved to a file yet'), 'DS_HOOKS.status adds its text (X10 later); never saved', s3)
    ok(J("!!$('#dsStat').title&&!!$('#mtr').title&&!!$('#cpuC').title"), 'tooltips on the status line, the meter and the CPU line')
    # idle: nothing redrawn
    R("play.on&&toggle()"); pg.wait_for_timeout(3000)
    R("(()=>{window.__dsS=0;const g=$('#cpuC').getContext('2d'),s=g.stroke;g.stroke=function(){window.__dsS++;return s.apply(this,arguments)};window.__dsM=meters.k})()")
    pg.wait_for_timeout(3000)
    ok(J("window.__dsS") <= 4, 'idle: the CPU line redrawn once a second at most (as the old graph)', J("window.__dsS"))
    # another look keeps today's meter, CPU graph and top bar
    R("UI.dawLook='fl';applyTheme();dsT2Stat()"); R("play.on||toggle()"); pg.wait_for_timeout(2500)
    m = J(MTR); c = J(CPUPX)
    ok(not J("dsAC3()") and J("$('#dsStat').hidden") and m['pk'].endswith(' dB') and c['frac'] > 0.2, 'FL style: today\'s meter, CPU area and no status line', [m['pk'], c['frac']])
    R("play.on&&toggle()"); R("delete UI.dawLook;applyTheme();dsT2Stat()"); pg.wait_for_timeout(600)
    ok(not J("$('#dsStat').hidden"), 'back to the AudioLab look: the status line returns')
    ok(not logs, 'no console errors', logs[:5])
    print(f'{N[0] - len(FAIL)} of {N[0]} checks passed'); sys.exit(1 if FAIL else 0)
