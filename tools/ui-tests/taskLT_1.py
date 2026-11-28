#!/usr/bin/env python3
"""Task LT-1 (lane J): the output check (L1) and the playing buffer (L2).
Fake outputs (Bose via eqMac at 16 kHz, Background Music, BlackHole, Cubase System Sound Link, a Bluetooth speaker, the iFi) through a stubbed
enumerateDevices: the warning shows for the bad ones and not for the iFi, its button names the iFi and sets the output; Keep this output silences it.
The playing buffer: arming a track while stopped runs the engine at 128 frames in 64-frame blocks; Play keeps it; dropouts at it switch to the mixing
buffer and the next Play starts on the mixing buffer; Off. Auto: a clean minute marks a step down applied at Stop; dropouts still take it up and
then a step down needs twice as long. The two Settings rows, the settings table, tooltips. No console errors. Screenshots dark and Light level.
   python3 tools/ui-tests/taskLT_1.py [index.html] [out dir]"""
import sys, os, json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
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
DEVS = [
 ('default', 'Default - Bose Mini II SoundLink (eqMac)'), ('bose-eq', 'Bose Mini II SoundLink (eqMac)'), ('ifi', 'iFi (by AMR) HD USB Audio '),
 ('bgm', 'Background Music'), ('bh', 'BlackHole 2ch'), ('cub', 'Cubase System Sound Link'), ('bose', 'Bose Mini II SoundLink'),
 ('spk', 'Mac mini Speakers'), ('g80', 'Odyssey G80SD')]
FAKE = "window.__LTDEV=" + json.dumps([{'deviceId': i, 'kind': 'audiooutput', 'label': l, 'groupId': 'g-' + i} for i, l in DEVS]) + \
 ";Object.defineProperty(navigator.mediaDevices,'enumerateDevices',{configurable:true,value:async()=>window.__LTDEV.map(d=>Object.assign({toJSON(){return this}},d))});"

with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    cx = b.new_context(viewport={'width': 1600, 'height': 1000}); pg = cx.new_page(); logs = []
    def con(m):
        if (m.type == 'error' and 'fetching the script' not in m.text) or (m.type == 'warning' and 'nominal range' not in m.text and 'GPU stall' not in m.text and 'willReadFrequently' not in m.text): logs.append(m.type + ': ' + m.text[:300])
    pg.on('console', con); pg.on('pageerror', lambda e: logs.append('pageerror: ' + str(e)[:300]))
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(status=200, content_type='text/html', body=SRC) if r.request.url.endswith('.html') else r.fulfill(status=404, body='')))
    pg.add_init_script(INIT + ';' + FAKE)
    pg.goto('https://app.test/index.html'); pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version", timeout=120000); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{for(const i of['splash','liteNote']){const s=document.getElementById(i);if(s)s.remove()}}")
    R = lambda c: pg.evaluate("c=>AudioLab.run(c)", c)
    W = pg.wait_for_timeout
    print('version', R("VERSION"))

    # --- the Settings rows
    r = R("""(()=>{const a=document.getElementById('ltPbSel'),c=document.getElementById('ltOcChk');return{a:!!a,c:!!c,av:a&&a.value,cc:c&&c.checked,
      at:a&&a.closest('.cprow').title,ct:c&&c.closest('label').title,after:a&&a.closest('.cprow').previousElementSibling.querySelector('#rqSel')!=null,
      stt:['playBuf','outCheck'].every(i=>STX.has(i)),hook:LT_HOOKS.audioRows===LT_ROWS,find:SETT.find('playing buffer').includes('playBuf')&&SETT.find('eqmac').includes('outCheck'),
      def:[SETT.isDefault('playBuf'),SETT.isDefault('outCheck')],auto:document.querySelector('#bufSel option[value="-1"]').textContent,
      em:[...document.querySelectorAll('#ltPbSel option')].map(o=>o.textContent).concat([c.closest('label').textContent,a.closest('.cprow').title]).some(t=>/—/.test(t))}})()""")
    ok(r['a'] and r['c'] and r['after'], 'the Playing buffer and Check the output device rows sit under Render blocks', r)
    ok(r['av'] == '128' and r['cc'], 'defaults: 128 samples, the check on', r)
    ok(bool(r['at']) and bool(r['ct']), 'both rows have tooltips')
    ok(r['stt'] and r['hook'] and r['find'] and r['def'] == [True, True], 'rows in the settings table (STT), LT_HOOKS.audioRows, found by search, at default', r)
    ok('back down' in r['auto'], 'the Auto option says it comes back down', r['auto'])
    ok(not r['em'], 'no em dashes in the new texts')

    # --- the playing buffer
    r = R("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));ensureCtx();await ctx.resume();await w(300);for(const t of S.tracks)t.arm=false;UI.kbPiano=false;CAPS=false;
      let t=S.tracks.find(t=>t.kind==='inst');
      /* the headless output has no real device and underruns at random: the browser's counter and the clock check are stubbed, the test adds its own dropouts */
      urNow=()=>-1;Object.defineProperty(CPU,'dropT',{configurable:true,get(){return -9},set(v){}});return{has:!!t,cur:LT.cur,rq:ctx.renderQuantumSize,lat4:UI.lat4,buf:UI.buf,abuf:UI.abuf}})()""")
    ok(r['has'], 'the start project has an instrument track', r)
    ok(r['cur'] == 'mix', 'nothing armed: the mixing buffer', r)
    r = R("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const c0=ctx;const t=S.tracks.find(t=>t.kind==='inst');t.arm=true;changed(true);ltSoon(30);await w(1300);let err='';try{latency()}catch(e){err=String(e)}
      return{cur:LT.cur,pb:LT.pbUsed,rq:ctx.renderQuantumSize,base:ctx.baseLatency*1000,newCtx:ctx!==c0,lat:document.getElementById('latO').textContent,err}})()""")
    ok(r['cur'] == 'play' and r['newCtx'], 'arming a track while stopped switches to the playing buffer', r)
    ok(r['rq'] == 64, 'render blocks of 64 frames where Chromium allows it', r)
    ok('playing buffer 128' in r['lat'], 'the latency read-out says so', r['lat'])
    r = R("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const c0=ctx;pos=0;start();await w(1500);const a={cur:LT.cur,same:ctx===c0,on:play.on};stop();await w(1200);a.after=LT.cur;a.same2=ctx===c0;return a})()""")
    ok(r['cur'] == 'play' and r['same'] and r['on'], 'Play keeps the playing buffer (no restart at Play)', r)
    ok(r['after'] == 'play' and r['same2'], 'Stop keeps it too', r)
    r = R("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const ab=UI.abuf;pos=0;start();await w(1300);URS.total+=3;await w(1500);const a={cur:LT.cur,on:play.on,heavy:LT.heavy,abuf:UI.abuf,ab0:ab,n:URS.n};
      stop();await w(1300);a.back=LT.cur;start();a.atPlay=LT.cur;await w(600);stop();await w(1300);a.end=LT.cur;LT.heavy=false;return a})()""")
    ok(r['cur'] == 'mix' and r['on'] and r['heavy'], 'dropouts at the playing buffer switch to the mixing buffer and keep playing', r)
    ok(r['abuf'] == r['ab0'], 'and do not raise the Auto buffer', r)
    ok(r['back'] == 'play' and r['atPlay'] == 'mix' and r['end'] == 'play', 'after that: the playing buffer while stopped, the mixing buffer from Play on', r)
    r = R("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const s=document.getElementById('ltPbSel');s.value='0';s.dispatchEvent(new Event('change'));await w(900);
      const a={off:LT.cur,ui:UI.ltPlayBuf};s.value='128';s.dispatchEvent(new Event('change'));await w(900);a.on=LT.cur;
      const t=S.tracks.find(t=>t.arm);t.arm=false;changed(true);ltSoon(30);await w(900);a.dis=LT.cur;a.rq=ctx.renderQuantumSize;return a})()""")
    ok(r['off'] == 'mix' and r['ui'] == 0, 'Playing buffer Off: the mixing buffer even when armed', r)
    ok(r['on'] == 'play', 'back on: the playing buffer again', r)
    ok(r['dis'] == 'mix' and r['rq'] >= 128, 'disarmed: the mixing buffer', r)
    r = R("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));selT=S.tracks.find(t=>t.kind==='inst').id;UI.kbPiano=true;ltSoon(30);await w(900);const a={kb:LT.cur};LT.keys.add('KeyZ');UI.kbPiano=false;ltSoon(30);await w(900);a.held=LT.cur;
      LT.keys.clear();ltSoon(30);await w(900);a.rel=LT.cur;return a})()""")
    ok(r['kb'] == 'play', 'the computer keyboard playing: the playing buffer', r)
    ok(r['held'] == 'play' and r['rel'] == 'mix', 'never switched while a key is held; switched once released', r)

    # --- Auto comes back down
    r = R("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));UI.buf=-1;UI.abuf=1024;restartAudio(true);await w(500);LT.abuf=1024;LT.stepT=-1e9;LT.need=60000;LT.clean=0;pos=0;start();
      await w(2300);const a={clean:LT.clean,down0:LT.down};LT.clean=59500;await w(1300);a.down=LT.down;stop();await w(1200);a.abuf=UI.abuf;a.rq=ctx.renderQuantumSize;a.lat=document.getElementById('latO').textContent;return a})()""")
    ok(r['clean'] >= 1000 and not r['down0'], 'clean playing is counted, no step before a minute', r)
    ok(r['down'] and r['abuf'] == 512, 'a clean minute marks a step down, applied at Stop (1,024 to 512)', r)
    r = R("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));pos=0;start();await w(1300);LT.clean=59500;LT.stepT=-1e9;/* the minute between two steps, skipped here; LT.downT stays recent */await w(1300);const a={down:LT.down};URS.n=3;stop();await w(1500);a.abuf=UI.abuf;
      pos=0;start();await w(1300);a.need=LT.need;a.down2=LT.down;stop();await w(800);return a})()""")
    ok(r['down'] and r['abuf'] == 1024, 'dropouts at Stop still take it up, and then there is no step down', r)
    ok(r['need'] == 120000 and not r['down2'], 'up again soon after a step down: the next step down needs two clean minutes', r)
    r = R("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));UI.abuf=256;LT.abuf=256;restartAudio(true);await w(400);pos=0;start();await w(1200);LT.clean=70000;LT.stepT=-1e9;await w(1200);const a={down:LT.down};stop();await w(900);a.abuf=UI.abuf;return a})()""")
    ok(not r['down'] and r['abuf'] == 256, 'never below 256 samples', r)

    # --- the output check
    r = R("""(async()=>{await adScan(true);const o={};for(const x of ADV.outs)o[x.id]=ltOutWhy(Object.assign({},x,{use:false})).length;
      o.call16=ltOutWhy({label:'Bose Mini II SoundLink (eqMac)',full:true,rate:16000,hw:{transport:'usb'},type:'builtin'}).join(' | ');
      o.cur=adCur()&&adCur().id;o.wired=(ltWired(ADV.outs,adCur())||{}).id;return o})()""")
    ok(r.get('bose-eq', 0) >= 2, 'Bose via eqMac: eqMac and Bluetooth', r)
    ok(r.get('bgm', 0) >= 1 and r.get('bh', 0) >= 1 and r.get('cub', 0) >= 1, 'Background Music, BlackHole, Cubase System Sound Link: virtual', r)
    ok(r.get('bose', 0) >= 1, 'the Bose by Bluetooth: Bluetooth', r)
    ok(r.get('ifi', 1) == 0 and r.get('spk', 1) == 0, 'the iFi and the speakers: no warning', r)
    ok('16 kHz' in r['call16'] and 'call mode' in r['call16'], 'a device at 16 kHz: call mode', r['call16'])
    ok(r['cur'] == 'bose-eq' and r['wired'] == 'ifi', 'the output in use is the Bose via eqMac, the wired one offered is the iFi', r)
    R("ctx.setSinkId=async id=>{ctx.__sink=id};UI.sink='';LT.shown.clear();LT.later.clear();UI.ltOkOut=[];window.__ltv=ltOutCheck('test');0")
    W(900)
    d = R("""(()=>{const m=document.getElementById('cdlg');return{open:!m.hidden,t:document.getElementById('cdT').textContent,p:document.getElementById('cdP').textContent,b:[...document.querySelectorAll('#cdB button')].map(b=>b.textContent)}})()""")
    ok(d['open'] and 'late' in d['t'], 'the notice shows for the Bose via eqMac', d)
    ok(d['b'] and d['b'][0] == 'Play through iFi (by AMR) HD USB Audio', 'its first button plays through the iFi', d['b'])
    ok('eqMac' in d['p'] and 'Bluetooth' in d['p'] and '—' not in d['p'], 'it says why in plain words', d['p'])
    pg.screenshot(path=os.path.join(OUT, 'lt1_notice_dark.png'))
    R("UI.lite=true;applyLite();0"); W(500); pg.screenshot(path=os.path.join(OUT, 'lt1_notice_light.png')); R("UI.lite=false;applyLite();0")
    pg.click('#cdB button[data-i="0"]'); W(1500)
    r = R("({sink:UI.sink,dev:ctx.__sink,wired:UI.ltWired,sel:document.getElementById('outSel').value})")
    ok(r['sink'] == 'ifi' and r['dev'] == 'ifi' and r['wired'] == 'ifi by amr hd usb audio', 'Play through the iFi sets the output and remembers it', r)
    r = R("(async()=>{LT.shown.clear();const v=await ltOutCheck('test');return{v,open:!document.getElementById('cdlg').hidden}})()")
    ok(r['v'] is None and not r['open'], 'playing through the iFi: no notice', r)
    R("UI.sink='';LT.shown.clear();window.__ltv=ltOutCheck('test');0"); W(900)
    pg.click('#cdB button:has-text("Keep this output")'); W(400)
    r = R("(async()=>{const k=UI.ltOkOut.slice();LT.shown.clear();const v=await ltOutCheck('test');return{k,v,open:!document.getElementById('cdlg').hidden}})()")
    ok('bose mini ii soundlink eqmac' in r['k'] and r['v'] is None and not r['open'], 'Keep this output: no more notices for that device', r)
    R("UI.ltOkOut=[];LT.shown.clear();UI.ltOutChk=false;window.__ltv=ltOutCheck('test');0"); W(700)
    ok(R("document.getElementById('cdlg').hidden"), 'Check the output device off: no notice')
    R("UI.ltOutChk=true;window.__LTDEV=window.__LTDEV.filter(d=>d.deviceId!=='default');window.__LTDEV.unshift({deviceId:'default',kind:'audiooutput',label:'Default - iFi (by AMR) HD USB Audio ',groupId:'g-ifi'});LT.shown.clear();0")
    r = R("(async()=>{const v=await ltOutCheck('test');return{v,open:!document.getElementById('cdlg').hidden}})()")
    ok(r['v'] is None and not r['open'], 'the iFi as the system output: no notice', r)
    R("(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));openSettings&&openSettings('audio');await w(300);const c=document.getElementById('cpBtn');if(c&&c.getAttribute('aria-expanded')!=='true')c.click()})()")
    W(800)
    try:
        el = pg.query_selector('#ltPbSel'); el.scroll_into_view_if_needed(); W(200)
        bx = el.bounding_box(); cl = {'x': max(0, bx['x'] - 260), 'y': max(0, bx['y'] - 160), 'width': 720, 'height': 360}
        pg.screenshot(path=os.path.join(OUT, 'lt1_rows_dark.png'), clip=cl)
        R("UI.lite=true;applyLite();0"); W(500); pg.screenshot(path=os.path.join(OUT, 'lt1_rows_light.png'), clip=cl); R("UI.lite=false;applyLite();0")
        ok(bx['width'] > 40, 'the rows are visible in Settings, Audio', bx)
    except Exception as e:
        ok(False, 'the rows are visible in Settings, Audio', e)
    ok(not logs, 'no console errors', logs[:5])
    b.close()
print('%d checks, %d failed' % (N[0], len(FAIL)))
sys.exit(1 if FAIL else 0)
