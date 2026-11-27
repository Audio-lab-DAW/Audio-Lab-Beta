"""Task SND-1 (lane L): Filter v2 (new device 'filter2') and the Auto Filter's Clean models. Re-runnable on a fresh file after a rebase.
  python3 tools/engine-lab/snd/snd1_edit.py [index.html] [version]
- the block (tools/engine-lab/snd/snd1_src.js, between /* ==SND1-js== and /* ==SND1-js-end== */) before askChoice;
- the Auto Filter's node gives its inner nodes to the Clean mode (X._v1); nothing else of its Classic code changes;
- VERSION set when given (also written into the block's first line)."""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', '..', 'index.html')
s = open(P, encoding='utf-8').read()
blk = open(os.path.join(HERE, 'snd1_src.js'), encoding='utf-8').read().rstrip('\n') + '\n'
ver = sys.argv[2] if len(sys.argv) > 2 else None
if ver: blk = blk.replace('/* ==SND1-js== v0.000', '/* ==SND1-js== v' + ver, 1)
if '/* ==SND1-js==' in s:
    a = s.index('/* ==SND1-js=='); e = '/* ==SND1-js-end== */\n'; b = s.index(e, a) + len(e)
    s = s[:a] + blk + s[b:]
else:
    A = 'function askChoice(title,text,btns,icon){'
    assert s.count(A) == 1, 'askChoice anchor'
    s = s.replace(A, blk + A)
X0 = 'const X={in:i,out,an,lan,ean,b1,b2,fm,fg,lfo,ph:0,t0:c.currentTime,cur:{},'
X1 = 'const X={in:i,out,an,lan,ean,b1,b2,fm,fg,lfo,ph:0,t0:c.currentTime,cur:{},_v1:{i,drv,dry,wet,post,lg,eg}/* SND-1: for the Clean mode */,'
if X1 not in s:
    assert s.count(X0) == 1, 'afilt anchor'
    s = s.replace(X0, X1)
assert s.count(X1) == 1
if ver:
    assert len(re.findall(r"const VERSION='[0-9.]+'", s)) == 1
    s = re.sub(r"const VERSION='[0-9.]+'", "const VERSION='%s'" % ver, s)
for name in ('sndFltCore', 'sndFltWL', 'sndFltNode', 'sndFltResp', 'sndAfClean', 'sndAfMap', 'sndDefFilter2', 'sndF2Map', 'sndTips'):
    assert len(re.findall(r'\bfunction %s\(' % name, s)) == 1, name
assert s.count('/* ==SND1-js==') == 1 and s.index('/* ==SND1-js==') < s.index('function askChoice(title,text,btns,icon){')
open(P, 'w', encoding='utf-8').write(s)
print('SND-1 edit done', P)
