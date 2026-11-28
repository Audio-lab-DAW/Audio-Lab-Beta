"""Task XT-DL2: the commands registry (docs/extensions-plan.md 9.6 c, docs/commands.md).
Fails when a command id listed in docs/commands.md disappears (a retired id must stay in COMMAND_ALIAS and point at a living one),
when the registry has a command not listed there (a new SCA row needs a namespaced id and a row in docs/commands.md), or when
runCommand, the aliases or the keyboard shortcuts stop working. Nothing visible changes: the Settings shortcut list is the same.
  python3 tools/ui-tests/taskXT_DL2.py [index.html] [out dir]"""
import sys, os, json, re
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', encoding='utf-8').read()
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'; os.makedirs(OUT, exist_ok=True)
N = [0, 0]; FAIL = []
def ok(c, m, info=''):
    N[0] += 1
    if c: N[1] += 1; print('ok   ', m, info if info != '' else '')
    else: FAIL.append(m); print('FAIL ', m, info)
REL = []
for l in open(os.path.join(HERE, '..', '..', 'docs', 'commands.md'), encoding='utf-8'):
    m = re.match(r'^\|\s*`([a-z]+(?:\.[A-Za-z0-9]+)+)`\s*\|', l)
    if m: REL.append(m.group(1))
INIT = "if(!sessionStorage.getItem('dl2')){sessionStorage.setItem('dl2','1');localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))}"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); pg = b.new_page(viewport={'width': 1600, 'height': 1000}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console: ' + m.text[:300]) if m.type == 'error' and 'fetching the script' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.add_init_script(INIT)
    pg.route('https://app.test/**', alsong(lambda r: r.fulfill(body=SRC, content_type='text/html') if r.request.url.endswith('/') else r.fulfill(status=404, body='')))
    pg.goto('https://app.test/'); pg.wait_for_function('() => window.AudioLab && window.AudioLab.version', timeout=90000); pg.wait_for_timeout(2500)
    R = lambda c: pg.evaluate('c => AudioLab.run(c)', c); J = lambda c: json.loads(R('JSON.stringify(' + c + ')'))
    ok(tuple(map(int, R('VERSION').split('.'))) >= (0, 273), 'version 0.273 or later', R('VERSION'))
    R("openDemoFractals()"); pg.wait_for_timeout(6000); R("toggle()"); pg.wait_for_timeout(2000); R("play.on&&toggle()")
    ok(J("XT_CMD.n") == -1 and J("XT_CMD_LOG.length") == 0, 'with nothing asking for it, the registry is never built (start, a song, playing): it costs nothing')
    C = J("[...xtCommands().values()].map(c=>({id:c.id,name:c.name,g:c.group,legacy:c.legacy,gesture:c.gesture,key:c.key,dk:c.defaultKey}))")
    ids = [c['id'] for c in C]
    ok(len(ids) >= 60 and len(ids) == len(set(ids)), 'one registry entry per command, ids used once', len(ids))
    nsa = J("SCA.length")
    ok(len([c for c in C if c['legacy']]) == nsa, 'every row of the shortcut list (SCA) is in the registry', (len([c for c in C if c['legacy']]), nsa))
    bad = [i for i in ids if not re.match(r'^[a-z]+(\.[a-z][A-Za-z0-9]*)+$', i)]
    ok(not bad, 'every command id is namespaced (section.name)', bad)
    ok(J("SCA.filter(a=>a.id.includes('.')).every(a=>xtCommandId(a.id)===a.id)"), 'ids that already had a namespace (ctl.*, ni.*, clip.*) are kept as they are')
    ok(len(REL) >= 60, 'docs/commands.md lists the released commands', len(REL))
    alias = J("COMMAND_ALIAS")
    gone = [i for i in REL if i not in ids and not (i in alias and alias[i] in ids)]
    ok(not gone, 'every released command id is in the registry (or an alias of one)', gone)
    new = [i for i in ids if i not in REL]
    ok(not new, 'every command in the registry is listed in docs/commands.md', new)
    res = J("SCA.map(a=>[a.id,xtCommandId(a.id)]).filter(([o,n])=>!n||xtCommands().get(n).legacy!==o)")
    ok(not res, 'every old id resolves to its own command', res[:5])
    ok(J("xtCommandId('learn')") == 'ctl.learn' and J("xtCommandId('play')") == 'transport.play' and J("xtCommandId('nope.x')") is None, 'aliases: learn, play; an unknown id is null')
    ok(all(c['name'] and '—' not in c['name'] for c in C), 'every command has a plain name (no em dash)')
    # runCommand
    a0 = J("$('#bClick').getAttribute('aria-pressed')")
    r1 = J("runCommand('transport.metronome','test')"); a1 = J("$('#bClick').getAttribute('aria-pressed')")
    r2 = J("runCommand('click','test')"); a2 = J("$('#bClick').getAttribute('aria-pressed')")
    ok(r1 and r2 and a1 != a0 and a2 == a0, 'runCommand runs by the namespaced id and by the old id (metronome on, then off)', (a0, a1, a2))
    c0 = J("$('#bCount').getAttribute('aria-pressed')"); J("runCommand('transport.countIn')"); c1 = J("$('#bCount').getAttribute('aria-pressed')"); J("runCommand('transport.countIn')")
    ok(c1 != c0, 'a command with a button but no shortcut row (count-in) runs', (c0, c1))
    ok(J("runCommand('edit.copy')") is False and J("runCommand('no.such')") is False, 'a gesture and an unknown id are refused, without an error')
    lg = J("XT_CMD_LOG.slice(-2).map(e=>[e.id,e.ok,e.why])")
    ok(lg == [['edit.copy', False, 'gesture'], ['no.such', False, 'unknown']], 'the run log says what ran and why something did not', lg)
    ok(J("(()=>{for(let i=0;i<80;i++)runCommand('no.such');return XT_CMD_LOG.length})()") == 50, 'the run log keeps the last 50')
    n0 = J("xtCommands().size"); R("SCA.push({id:'xtprobe.cmd',g:'view',l:'Probe',d:'',ic:'',run:()=>{window.__xtp=(window.__xtp||0)+1}})")
    ok(J("xtCommands().size") == n0 + 1 and J("runCommand('xtprobe.cmd')") and J("window.__xtp") == 1, 'a row added to SCA later joins the registry')
    R("SCA.pop()")
    ok(J("xtCommands().size") == n0, 'and leaves it again')
    # keys and the shortcut page are unchanged
    k0 = J("$('#bClick').getAttribute('aria-pressed')")
    pg.mouse.click(800, 500); pg.keyboard.press('c'); pg.wait_for_timeout(200)
    k1 = J("$('#bClick').getAttribute('aria-pressed')"); pg.keyboard.press('c'); pg.wait_for_timeout(200)
    ok(k1 != k0, 'the C key still toggles the metronome', (k0, k1))
    ok(J("xtCommands().get('transport.play').key") == 'Space', 'the current key is read from the user keys (Space for Play)')
    R("UI.keys=Object.assign({},UI.keys,{click:'Shift+K'})")
    ok(J("xtCommands().get('transport.metronome').key") == 'Shift+K', 'a changed key shows in the registry')
    R("delete UI.keys.click")
    R("openSettings('keys')"); pg.wait_for_timeout(800)
    rows = J("document.querySelectorAll('#scBody .scr').length")
    ok(rows == nsa, 'the Settings shortcut list shows the same rows as before (count-in, tap and capture are not added)', (rows, nsa))
    pg.screenshot(path=os.path.join(OUT, 'xt_dl2_keys.png'))
    ok(not errs, 'no console errors', errs[:5])
    b.close()
print('%d of %d checks passed' % (N[1], N[0]))
if FAIL: print('FAILED:', FAIL); sys.exit(1)
