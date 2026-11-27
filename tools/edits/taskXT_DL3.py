"""Task XT-DL3: the advanced settings list in the Workshop window. Inserts tools/edits/taskXT_DL3_block.js before askChoice and
taskXT_DL3_css.txt before .dacv, opens the first constants (Undo's depth, the run log's length), adds "Workshop…" to the logo menu,
bumps VERSION.
  python3 tools/edits/taskXT_DL3.py [index.html]"""
import sys, os, re, json
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(__file__)
s = open(P, encoding='utf-8').read()
blk = open(os.path.join(H, 'taskXT_DL3_block.js'), encoding='utf-8').read()
css = open(os.path.join(H, 'taskXT_DL3_css.txt'), encoding='utf-8').read()
ns = json.load(open(os.path.join(H, 'taskXT_DL3_ns.json'), encoding='utf-8'))
assert 'task XT-DL3' not in s, 'already applied'
for d in ('task XT-DL1', 'task XT-DL2', 'task XT-DL12', 'task ST-S4'):
    assert d in s, d + ' first'
for n in ('XT_SET_NS', 'XT_SET_OWN', 'XT_WS', 'xtV(', 'xtSetRows', 'xtWsOpen', 'XT_HOOKS', 'xtSet', 'xtWsSeen', "'xtWs'"):
    assert n not in s, n + ' exists already'
def one(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80]); s = s.replace(a, b)
A = 'function askChoice(title,text,btns,icon){'
C = '.dacv{display:flex;'
assert s.count(A) == 1 and s.count(C) == 1
m = re.findall(r"const VERSION='(\d+)\.(\d+)'", s); assert len(m) == 1
v = '%s.%03d' % (m[0][0], int(m[0][1]) + 1)
blk = blk.replace('v0.000', 'v' + v).replace('__NS__', json.dumps(ns, separators=(',', ':')))
one(A, blk + A)
one(C, css + C)
# the first opened constants: Undo's depth (core), the run log's length (lane H)
U = 'if(UNDO.length>80)UNDO.shift()'
assert s.count(U) == 2, s.count(U)
s = s.replace(U, "while(UNDO.length>xtV('edit.undoSteps',80))UNDO.shift()")
one('XT_CMD_LOG.push(e);if(XT_CMD_LOG.length>50)XT_CMD_LOG.shift();', "XT_CMD_LOG.push(e);while(XT_CMD_LOG.length>xtV('workshop.consoleLines',50))XT_CMD_LOG.shift();")
# the door: the logo menu, before Settings… (K4a: always in the menu)
S = "   {label:'Settings…',crow:'set',crowL:'Settings',"
one(S, "   {label:'Workshop…',sub:'advanced: every setting by its id',ic:I('M4 16l6-6M9 5a3 3 0 0 0 4 4l3 3-2 2-3-3a3 3 0 0 0-4-4l2-2z','#b583ff'),act:()=>xtWsOpen()},\n" + S)
# the ids registry keeps up with other lanes: three mixer controls added since DL1 (lane K MX-1: the send's pre or post ring, the
# channel's Output button; lane D: the master's Loss button), so tools/ui-tests/taskXT_DL1.py passes again (docs/ids.md has their rows)
one("['mixer.cables.style','.cablg [data-cl=sty]','cable legend Style switch'],['mixer.cables.clashes','.cablg [data-ni=clash]','cable legend Clashes switch']];",
    "['mixer.cables.style','.cablg [data-cl=sty]','cable legend Style switch'],['mixer.cables.clashes','.cablg [data-ni=clash]','cable legend Clashes switch'],\n"
    " ['mixer.strip.sendPrePost','.mxsr .mxpp','send before or after the fader ring'],['mixer.strip.output','.mx:not(.master) .mxout','channel Output button'],\n"
    " ['mixer.master.monoLoss','.mx.master [data-niml]','Mono loss button']];")
s = re.sub(r"const VERSION='\d+\.\d+'", "const VERSION='%s'" % v, s)
open(P, 'w', encoding='utf-8').write(s); print('ok', v)
