"""DR6: screenshots of today's arrangement lines (Fractals demo) at the user's size, 2194x1139 CSS px at 1.75x,
at three zooms: whole song, 16 bars, 1 bar.  python3 tools/design-lab/dr6/shots_today.py [index.html] [outdir]"""
import sys, os
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
idx = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'index.html')
out = sys.argv[2] if len(sys.argv) > 2 else 'shots'
os.makedirs(out, exist_ok=True)
src = open(idx, encoding='utf-8').read()
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 2194, 'height': 1139}, device_scale_factor=1.75)
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(body=src, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body='')))
    pg.goto('https://app.test/')
    pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=60000)
    pg.wait_for_timeout(2000)
    run = lambda c: pg.evaluate('c => AudioLab.run(c)', c)
    run('openDemoFractals()'); pg.wait_for_timeout(4000)
    print('version', run('AudioLab.version'), 'tracks', run('S.tracks.length'), 'end', run('songEnd()'), 'arrW', run('arrW'))
    for name, bars, x0 in [('whole', None, 0), ('16bars', 16, 64), ('1bar', 1, 128.0)]:
        if bars is None:
            run('V.x=0;V.ppb=arrW/(Math.max(songEnd(),loopEnd())+4);dirty=true')
        else:
            run('V.x=%s;V.ppb=arrW/(%d*4);dirty=true' % (x0, bars))
        pg.wait_for_timeout(700)
        pg.screenshot(path=os.path.join(out, 'today-%s.png' % name))
        # a close crop of the ruler and the first lanes, at device pixels
        pg.screenshot(path=os.path.join(out, 'today-%s-crop.png' % name), clip={'x': 200, 'y': 40, 'width': 700, 'height': 260})
        print(name, 'ppb', run('V.ppb'))
    b.close()
