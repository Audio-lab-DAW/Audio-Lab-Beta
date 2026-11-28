"""Task SND-R (lane L): one random stream per device. Re-runnable on a fresh file after a rebase.
  python3 tools/engine-lab/snd/sndr_edit.py [index.html] [version]
- the block (sndr_src.js, /* ==SNDR-js== ... /* ==SNDR-js-end== */) before askChoice;
- wlLoad puts SNDR_WL at the top of the worklet module (after the shared generator, before every processor), in both paths."""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', '..', 'index.html')
s = open(P, encoding='utf-8').read()
blk = open(os.path.join(HERE, 'sndr_src.js'), encoding='utf-8').read().rstrip('\n') + '\n'
ver = sys.argv[2] if len(sys.argv) > 2 else None
if ver: blk = blk.replace('/* ==SNDR-js== v0.000', '/* ==SNDR-js== v' + ver, 1)
if '/* ==SNDR-js==' in s:
    a = s.index('/* ==SNDR-js=='); e = '/* ==SNDR-js-end== */\n'; b = s.index(e, a) + len(e)
    s = s[:a] + blk + s[b:]
else:
    A = 'function askChoice(title,text,btns,icon){'
    assert s.count(A) == 1, 'askChoice anchor'
    s = s.replace(A, blk + A)
W = "SNDR=typeof SNDR_WL==='string'?SNDR_WL:''"
A0 = "return(t>>>0)/4294967296}})();\\n'+(window.LT_WL||'')"
A1 = "return(t>>>0)/4294967296}})();\\n'+(typeof SNDR_WL==='string'?SNDR_WL:'')+(window.LT_WL||'')"
if A1 not in s:
    assert s.count(A0) == 1, 'wlLoad prelude anchor'
    s = s.replace(A0, A1)
B0 = "btoa(unescape(encodeURIComponent(WLSRC+"
B1 = "btoa(unescape(encodeURIComponent((typeof SNDR_WL==='string'?SNDR_WL:'')+WLSRC+"
if B1 not in s:
    assert s.count(B0) == 1, 'wlLoad fallback anchor'
    s = s.replace(B0, B1)
assert s.count(A1) == 1 and s.count(B1) == 1
if ver:
    assert len(re.findall(r"const VERSION='[0-9.]+'", s)) == 1
    s = re.sub(r"const VERSION='[0-9.]+'", "const VERSION='%s'" % ver, s)
for name in ('sndRHash', 'sndRSeed', 'sndRWL', 'sndRInstall'):
    assert len(re.findall(r'\bfunction %s\(' % name, s)) == 1, name
assert s.count('const SNDR_WL=') == 1
assert s.index('/* ==SNDR-js==') < s.index('function askChoice(title,text,btns,icon){')
assert s.index('const SND_HOOKS=') < s.index('/* ==SNDR-js==')
open(P, 'w', encoding='utf-8').write(s)
print('SND-R edit done', P)
