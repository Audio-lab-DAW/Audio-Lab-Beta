"""Apply LT-3a's release bookkeeping to a fresh main (after lt_2 is released and lt_3a.py ran): python3 tools/engine-lab/lt/held/lt3a_release.py 0.296 v0.295"""
import sys,re,os
NUM=sys.argv[1].lstrip('v');V='v'+NUM;BASE=sys.argv[2];SP=os.path.dirname(os.path.abspath(__file__))
def rep(p,a,b):
    s=open(p).read();assert s.count(a)==1,(p,a[:60]);open(p,'w').write(s.replace(a,b))
s=open('index.html').read();s,n=re.subn(r"^const VERSION='[0-9.]+',BUILD='[^']*'","const VERSION='%s',BUILD='28 November 2026'"%NUM,s,flags=re.M);assert n==1;open('index.html','w').write(s)
p='desktop/update-notes.txt';s=open(p).read()
line="In the next desktop app, notes from a MIDI keyboard go straight to the instrument of the track you play: they no longer wait while the app is busy drawing or loading (185 ms to 40 ms during a long pause in our test).\n"
if line not in s:open(p,'w').write(s.rstrip('\n')+'\n'+line)
e=open(SP+'/LT-3a_log.md').read().replace('v0.LT3A',V)
s=open('docs/backlog-log.md').read()
if 'task LT-3a, fast MIDI notes' not in s:open('docs/backlog-log.md','w').write(s.rstrip('\n')+'\n\n'+e)
p='docs/latency-build.md';s=open(p).read()
a='| LT-3a | AE2-3 | L5 | desktop: notes read outside the page, posted into the worklet (the path, one instrument kind) | next |'
if a in s:rep(p,a,a[:-8]+'| **done**, %s (28 Nov): note to sound during a 200 ms long task 185 to 40 ms (Electron, the armed Lead); needs a new desktop app |'%V)
a='| LT-3b | AE2-3 | L5 | desktop: every worklet instrument, drums, recording and the read-out; the Electron proof | |'
if a in s:rep(p,a,a[:-3]+'| next |')
p='docs/device-backlog-2026-11-25.md';s=open(p).read()
m=re.search(r'\*\*step LT-3a (claimed|built and tested, held by the release freeze)\*\* \([^)]*\)\.',s);a=m.group(0) if m else '#none#'
if a in s:rep(p,a,"**step LT-3a done**, %s: fast MIDI notes in the desktop app (L5): notes read in a hidden window of the shell (desktop/lt-midi.js) and posted straight into the played track's worklet (the pooled voice engine: Plant, basic synths, Wavetable); note to sound during a 200 ms long task 185 to 40 ms; needs a new desktop app. Next: LT-3b."%V)
print('ok',V)
