"""Apply LT-2's release bookkeeping to a fresh main (after lt_2.py): python3 tools/engine-lab/lt/held/lt2_release.py 0.299 v0.298"""
import sys,re
NUM=sys.argv[1].lstrip('v');V='v'+NUM;BASE=sys.argv[2];import os;SP=os.path.dirname(os.path.abspath(__file__))
def rep(p,a,b):
    s=open(p).read();assert s.count(a)==1,(p,a[:60]);open(p,'w').write(s.replace(a,b))
s=open('index.html').read();s,n=re.subn(r"^const VERSION='[0-9.]+',BUILD='[^']*'","const VERSION='%s',BUILD='27 November 2026'"%NUM,s,flags=re.M);assert n==1;open('index.html','w').write(s)
p='desktop/update-notes.txt';s=open(p).read()
line="The track you play now skips delay compensation while you play it: with a track armed or the computer keyboard on, its notes are no longer held back to line up with slow effects elsewhere in the song (6 ms in Fractals, 50 ms or more with a resonance suppressor), and the notes you record land where you heard them, within a millisecond.\n"
if line not in s:open(p,'w').write(s.rstrip('\n')+'\n'+line)  # appended: one line per release, newest last (the gate keeps the last ten)
e=open(SP+'/LT-2_log.md').read().replace('v0.292',V).replace('On the step rebased onto v0.291 (as %s)'%V,'On the step rebased onto %s (as %s)'%(BASE,V))
s=open('docs/backlog-log.md').read()
if 'task LT-2, the played track' not in s:open('docs/backlog-log.md','w').write(s.rstrip('\n')+'\n\n'+e)
p='docs/latency-build.md';s=open(p).read()
a='| LT-2 | AE2-2 | L4 | the played track skips delay compensation; recorded notes on the compensated clock | next |'
if a in s:rep(p,a,'| LT-2 | AE2-2 | L4 | the played track skips delay compensation; recorded notes on the compensated clock | **done**, %s (27 Nov): the armed Lead\'s compensation 6 ms (52 ms with a resonance suppressor) to 0; recorded notes within 0.1 ms of what was heard (before +18 ms) |'%V)
a='| LT-3a | AE2-3 | L5 | desktop: notes read outside the page, posted into the worklet (the path, one instrument kind) | |'
if a in s:rep(p,a,a[:-3]+'| next |')
p='docs/device-backlog-2026-11-25.md';s=open(p).read()
import re as _re;m=_re.search(r'\*\*step LT-2 (claimed|built and tested, held by the release freeze)\*\* \([^)]*\)\.',s);a=m.group(0) if m else '#none#'
if a in s:rep(p,a,"**step LT-2 done**, %s: the played track (armed or keyboard-played) skips delay compensation while you play (the Lead 6 ms, 52 ms with a resonance suppressor, to 0; ramped, exports unchanged), recorded notes placed by the compensated clock (within 0.1 ms of what was heard, before +18 ms). Next: LT-3a."%V)
print('ok',V)
