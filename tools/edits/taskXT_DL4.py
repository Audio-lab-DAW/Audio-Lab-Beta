"""Task XT-DL4: safe mode, what is changed, reset with a backup (lane H). Needs XT-DL3 in the file.
Inserts taskXT_DL4_early.js right after the line that reads the stored settings at start (with XT_UI0, a copy of the built-in defaults just
before it), taskXT_DL4_block.js before askChoice, taskXT_DL4_css.txt before .dacv, and "Restart in safe mode…" in the logo menu's Restart
submenu. Bumps VERSION.
  python3 tools/edits/taskXT_DL4.py [index.html]"""
import sys, os, re, json
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(P, encoding='utf-8').read()
early = open(os.path.join(H, 'taskXT_DL4_early.js'), encoding='utf-8').read()
blk = open(os.path.join(H, 'taskXT_DL4_block.js'), encoding='utf-8').read()
css = open(os.path.join(H, 'taskXT_DL4_css.txt'), encoding='utf-8').read()
assert 'task XT-DL4' not in s, 'already applied'
for d in ('task XT-DL1', 'task XT-DL2', 'task XT-DL3', 'task XT-DL12', 'task ST-S4'):
    assert d in s, d + ' first'
for n in ('XT_SAFE', 'XT_UI0', 'XT_SFM', 'xtSafe', 'xtChg', 'xtKeyShow', "'al-safe'", 'al-xt-start', 'help.safeMode', 'view.whatIsChanged'):
    assert n not in s, n + ' exists already'
def one(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80]); s = s.replace(a, b)
# what safe mode sets aside: every UI key of the settings table, the Workshop's own values, shortcuts, the four layout systems
i = s.index('const STT=['); j = s.index('\n];', i)
keys = []
for k in re.findall(r'"k":"UI\.([A-Za-z0-9_]+)', s[i:j]):
    if k not in keys: keys.append(k)
for k in re.findall(r"\{id:'[^']+',k:'([A-Za-z0-9_]+)'", s[s.index('const XT_SET_OWN=['):s.index('const XT_WS=')]):
    if k not in keys: keys.append(k)
for k in ('xtSet', 'keys', 'trOrder', 'trCompact', 'trHide', 'trX', 'hcz', 'mxOpt', 'fxHide'):
    if k not in keys: keys.append(k)
# Light mode stays as it is in safe mode: it protects a slow computer, and safe mode must never make AudioLab heavier
keys = [k for k in keys if k not in ('lite', 'liteMan', 'pm')]
assert len(keys) > 60 and 'buf' in keys and 'keys' in keys, len(keys)
m = re.findall(r"const VERSION='(\d+)\.(\d+)'", s); assert len(m) == 1
v = '%s.%03d' % (m[0][0], int(m[0][1]) + 1)
L = "\ntry{const u=JSON.parse(localStorage.getItem('audiolab-ui'));if(u&&Array.isArray(u.order)&&u.order.length===4)UI={...UI,...u}}catch(e){}\n"
one(L, "\nconst XT_UI0=JSON.parse(JSON.stringify(UI));/* lane H (task XT-DL4): the built-in defaults, for safe mode */" + L
    + early.replace('__STRIP__', json.dumps(keys, separators=(',', ':'))).rstrip('\n') + '\n')
A = 'function askChoice(title,text,btns,icon){'
C = '.dacv{display:flex;'
one(A, blk.replace('v0.000', 'v' + v) + A)
one(C, css + C)
R = "   {label:'Restart AudioLab',sub:'reload everything, back to the splash',ic:I('M16 10a6 6 0 1 1-2-4.5M16 3v3.5h-3.5M10 8v3','#ff9a3c'),act:()=>restartApp()}]},"
one(R, R[:-3] + ",\n   {label:XT_SAFE.on?'Leave safe mode…':'Restart in safe mode…',sub:XT_SAFE.on?'back to your settings, shortcuts and layout':'as it came: defaults, nothing deleted',ic:I('M10 3l6 2.5v4.5c0 3.5-2.6 6-6 7-3.4-1-6-3.5-6-7V5.5z','#ffbe50'),act:()=>xtSafeAsk()}]},")
s = re.sub(r"const VERSION='\d+\.\d+'", "const VERSION='%s'" % v, s)
open(P, 'w', encoding='utf-8').write(s); print('ok', v, len(keys), 'keys set aside in safe mode')
