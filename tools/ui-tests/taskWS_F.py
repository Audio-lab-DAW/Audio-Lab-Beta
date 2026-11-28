"""Task WS-F (lane Q): the song data is out of index.html (the user's 28 Nov decision: the Fractals song is only for testing; D6).
Checks:
  - index.html holds no song data: no DEMO_FRACTALS / DEMO_VOX / DEMO_VOX_FLAC, no FLAC in base64, no vocal sample path, no string
    literal over 100 kB; tools/test-songs/ has the project, fractals.json and the ten FLACs
  - under automation with tools/test-songs served (alsong): the Fractals song opens at start as before, 31 tracks with the
    'Vocals (original)' track of 10 clips, master -10 dB; openDemoFractals() says it is already open
  - the same with the files given as window.AL_TEST_SONGS (what the Electron tests do), nothing served
  - without the files (a plain route): an empty project, no page error, no console error, no toast; openDemoFractals() shows
    a plain message and opens nothing
  - the real start (audiolab-ws-test 1), fresh profile: the start screen, no song loaded, no Fractals request at all
  python3 tools/ui-tests/taskWS_F.py [index.html]"""
import sys, os, json, re
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong, songs  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); TS = os.path.join(HERE, '..', 'test-songs')
IDX = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', 'index.html'))
SRC = open(IDX, encoding='utf-8').read()
N = [0, 0]; FAIL = []
def ck(name, ok, info=''):
    N[0] += 1
    if ok: N[1] += 1; print('  ok  ', name, '' if info == '' else info)
    else: FAIL.append(name); print('  FAIL', name, info)

print('index.html')
ck('no DEMO_FRACTALS, DEMO_VOX or DEMO_VOX_FLAC', not re.search(r'DEMO_(FRACTALS|VOX)', SRC))
ck('no FLAC data (fLaC in base64) and no vocal sample path', 'ZkxhQw' not in SRC and 'vox/fractals_vox_' not in SRC)
big = [len(x) for x in re.findall(r"'([A-Za-z0-9+/=]{100000,})'", SRC)]
ck('no base64 string over 100 kB', not big, big)
ck('the file is under 5 MB (was 7.09 MB)', len(SRC.encode('utf-8')) < 5e6, '%.2f MB' % (len(SRC.encode('utf-8')) / 1e6))
M = json.load(open(os.path.join(TS, 'fractals.json')))
ck('tools/test-songs has the project, fractals.json and 10 FLACs', os.path.isfile(os.path.join(TS, M['file'])) and len(M['vox']) == 10 and all(os.path.isfile(os.path.join(TS, p)) and open(os.path.join(TS, p), 'rb').read(4) == b'fLaC' for _, p in M['vox']))

PLAIN = lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body='')
TOASTS = "window.__toasts=[];new MutationObserver(()=>{const t=document.getElementById('toast');if(t&&t.textContent&&__toasts[__toasts.length-1]!==t.textContent)__toasts.push(t.textContent)}).observe(document,{subtree:true,childList:true,characterData:true});"

def run(p, label, handler, init='', wait_song=True):
    ctx = p.new_context(viewport={'width': 1254, 'height': 651}, device_scale_factor=1.75)
    ctx.route('https://app.test/**', handler)
    ctx.add_init_script(TOASTS + init)
    pg = ctx.new_page(); errs, cons, reqs = [], [], []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: cons.append(m.text[:200]) if m.type == 'error' and 'Failed to load resource' not in m.text and 'fetching the script' not in m.text else None)
    pg.on('request', lambda q: reqs.append(q.url) if 'test-songs' in q.url else None)
    pg.goto('https://app.test/'); pg.wait_for_function('()=>window.AudioLab&&window.AudioLab.version', timeout=120000)
    R = lambda c: pg.evaluate('c=>AudioLab.run(c)', c)
    J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    if wait_song:
        try: pg.wait_for_function("()=>AudioLab.run('!!(FRX.ready&&PJ.list.length&&!PJ.list.some(p=>p.frxHold))')", timeout=60000)
        except Exception: pass
    pg.wait_for_timeout(1500)
    return ctx, pg, R, J, errs, cons, reqs

SONG = "(()=>{const v=S.tracks.find(t=>t.name==='Vocals (original)');return{name:curP().name,n:S.tracks.length,master:S.master,vox:v?v.clips.length:0,voxBuf:v?v.clips.every(c=>BUFS.has(c.buf)):false}})()"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])

    print('automation, tools/test-songs served')
    ctx, pg, R, J, errs, cons, reqs = run(b, 'served', alsong(PLAIN))
    s = J(SONG)
    ck('the Fractals song opens at start: 31 tracks, master -10 dB', s['name'] == 'Fractals_remake' and s['n'] == 31 and s['master'] == -10, s)
    ck('its Vocals (original) track has 10 clips with their audio', s['vox'] == 10 and s['voxBuf'], s)
    ck('the files came from tools/test-songs (fractals.json, the project, 10 FLACs)', len(set(reqs)) == 12, len(set(reqs)))
    R("openDemoFractals();0"); pg.wait_for_timeout(800)
    ck('openDemoFractals() says it is already open', any('already open' in t for t in J('__toasts')), J('__toasts'))
    ck('no page or console errors', not errs and not cons, errs + cons); ctx.close()

    print('automation, files as window.AL_TEST_SONGS, nothing served')
    ctx, pg, R, J, errs, cons, reqs = run(b, 'given', PLAIN, init='window.AL_TEST_SONGS=' + json.dumps(songs()) + ';')
    s = J(SONG)
    ck('the Fractals song opens from AL_TEST_SONGS, with its vocals', s['name'] == 'Fractals_remake' and s['n'] == 31 and s['vox'] == 10 and s['voxBuf'], s)
    ck('nothing was fetched', not reqs, reqs)
    ck('no page or console errors', not errs and not cons, errs + cons); ctx.close()

    print('automation, no test song files')
    ctx, pg, R, J, errs, cons, reqs = run(b, 'none', PLAIN)
    st = J("({tabs:PJ.list.map(p=>p.name),n:S.tracks.length,hold:PJ.list.some(p=>p.frxHold)})")
    ck('an empty project instead (one tab, no tracks, no placeholder left)', st['tabs'] == ['Untitled'] and st['n'] == 0 and not st['hold'], st)
    OLD = 'Demo song loaded. Press space to play. Right-click a clip, a track or empty space for options.'   # the automation start's own toast (firstRun, unchanged)
    T0 = [t for t in J('__toasts') if t != OLD]
    ck('no toast at start about the song (only the automation start\'s usual one)', not T0, J('__toasts'))
    R("openDemoFractals();0"); pg.wait_for_timeout(1500)
    ck('openDemoFractals() shows a plain message and opens nothing', [t for t in J('__toasts') if t != OLD] == ['The Fractals song is a test song and is not part of the app.'] and J('PJ.list.length') == 1, (J('__toasts'), J('PJ.list.length')))
    ck('no page or console errors', not errs and not cons, errs + cons); ctx.close()

    print('the real start (fresh profile)')
    ctx, pg, R, J, errs, cons, reqs = run(b, 'real', alsong(PLAIN), init="localStorage.setItem('audiolab-ws-test','1');", wait_song=False)
    pg.wait_for_timeout(2500)
    st = J("({on:WS.on,tabs:PJ.list.map(p=>p.name),fr:PJ.list.some(p=>p.file===FRX_FILE)})")
    ck('the start screen, no Fractals song, one Untitled project', st['on'] and not st['fr'] and st['tabs'] == ['Untitled'], st)
    ck('the app asked for no test song file', not reqs, reqs)
    ck('no page or console errors', not errs and not cons, errs + cons); ctx.close()
    b.close()

print('\ntaskWS_F: %d/%d' % (N[1], N[0]) + ('' if not FAIL else '  FAILED: ' + '; '.join(FAIL)))
sys.exit(1 if FAIL else 0)
