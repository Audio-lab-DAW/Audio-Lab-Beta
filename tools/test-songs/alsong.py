"""Task WS-F (lane Q): the test songs for the browser tests. index.html ships no song; frxProject() / openDemoFractals() read
tools/test-songs/<file> next to the page. A test that serves the app from https://app.test/ wraps its route handler:
    from alsong import alsong            (sys.path gets tools/test-songs)
    page.route('https://app.test/**', alsong(handler))
Requests for .../tools/test-songs/<file> get the file from this folder; every other request goes to the test's own handler.
songs() gives {path: base64} for window.AL_TEST_SONGS (pages that cannot fetch next to themselves, such as the Electron app)."""
import os, base64, json
DIR = os.path.dirname(os.path.abspath(__file__))
MARK = '/tools/test-songs/'
TYPES = {'.json': 'application/json', '.flac': 'audio/flac', '.audiolab': 'application/octet-stream', '.wav': 'audio/wav'}

def path_of(url):
    u = url.split('?', 1)[0].split('#', 1)[0]
    if MARK not in u: return None
    rel = u.split(MARK, 1)[1]
    f = os.path.normpath(os.path.join(DIR, rel))
    return f if f.startswith(DIR + os.sep) and os.path.isfile(f) else None

def alsong(handler):
    import inspect
    try: two = len(inspect.signature(handler).parameters) >= 2
    except (TypeError, ValueError): two = False
    def h(route):
        f = path_of(route.request.url)
        if f: return route.fulfill(body=open(f, 'rb').read(), content_type=TYPES.get(os.path.splitext(f)[1], 'application/octet-stream'))
        return handler(route, route.request) if two else handler(route)
    return h

def songs():
    M = json.load(open(os.path.join(DIR, 'fractals.json')))
    files = ['fractals.json', M['file']] + [p for _, p in M['vox']]
    return {p: base64.b64encode(open(os.path.join(DIR, p), 'rb').read()).decode() for p in files}

def init_script():
    """JS to run before the page's own scripts (add_init_script): sets window.AL_TEST_SONGS."""
    return 'window.AL_TEST_SONGS=' + json.dumps(songs()) + ';'
