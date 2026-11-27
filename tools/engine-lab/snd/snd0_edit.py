"""Task SND-0 (lane L): puts the shared DSP kit into index.html. Re-runnable on a fresh file after a rebase.
  python3 tools/engine-lab/snd/snd0_edit.py [index.html] [version]
- the kit (tools/engine-lab/snd/kit_src.js: sndKitCore, sndWL, SND_HOOKS) before askChoice (the lanes' rule for new JS);
- wlLoad appends sndWL() to the worklet module (SNDK there, and the test probe al-snd-kit);
- VERSION set when given."""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', '..', 'index.html')
s = open(P, encoding='utf-8').read()
kit = open(os.path.join(HERE, 'kit_src.js'), encoding='utf-8').read().rstrip('\n') + '\n'
if 'function sndKitCore(){' in s:
    a = s.index('/* ===== AudioLab shared DSP kit (task SND-0, lane L'); b = s.index('const SND_HOOKS={kit:1};\n', a) + len('const SND_HOOKS={kit:1};\n')
    s = s[:a] + kit + s[b:]
else:
    A = 'function askChoice(title,text,btns,icon){'
    assert s.count(A) == 1, 'askChoice anchor'
    s = s.replace(A, kit + A)
W0 = "(typeof ABXWL==='string'?ABXWL:'')],{type:'application/javascript'}));"
W1 = "(typeof ABXWL==='string'?ABXWL:'')+'\\n;'+(typeof sndWL==='function'?sndWL():'')],{type:'application/javascript'}));"
if W1 not in s:
    assert s.count(W0) == 1, 'wlLoad anchor'
    s = s.replace(W0, W1)
assert s.count(W1) == 1
if len(sys.argv) > 2:
    v = sys.argv[2]; n = len(re.findall(r"const VERSION='[0-9.]+'", s)); assert n == 1
    s = re.sub(r"const VERSION='[0-9.]+'", "const VERSION='%s'" % v, s)
for name in ('sndKitCore', 'sndWL'):
    assert len(re.findall(r'\bfunction %s\(' % name, s)) == 1, name
assert s.count('const SND_HOOKS=') == 1
open(P, 'w', encoding='utf-8').write(s)
print('SND-0 edit done', P)
