"""Task ST-S10: the release's docs, for the run that releases S10 after the release freeze. Run after tools/edits/taskST_S10.py has put
S10 into index.html with the new version:
  python3 tools/edits/taskST_S10_release.py <version> [gate line]
Appends the log entry (tools/edits/taskST_S10_log.md with VER and GATE filled) to docs/backlog-log.md, puts one line on top of
desktop/update-notes.txt and rewrites task ST's line in 'Where it stands' of docs/device-backlog-2026-11-25.md. Every replacement is
asserted unique; running it twice fails instead of writing twice."""
import sys,os
R=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
V=sys.argv[1];G=sys.argv[2] if len(sys.argv)>2 else ("`--here --quick` on the build: a lint clean, c the start-up smoke test (all 14 scenarios clean), "
 "frame times as the reference (p50 16.7 ms, p95 50.0 ms), d windows (19 checks) passed; e: same checksums and 9 export lines bit-identical to v0.294 "
 "(on one run it flagged the Fractals lines as changed although they read the same, the render under load as in S9).")
rd=lambda p:open(os.path.join(R,p),encoding='utf-8').read()
def wr(p,s):open(os.path.join(R,p),'w',encoding='utf-8').write(s)
idx=rd('index.html');assert "const VERSION='%s'"%V in idx and 'const STS10=' in idx,'run taskST_S10.py with this version first'
log=rd('tools/edits/taskST_S10_log.md').split('-->',1)[1].lstrip('\n').replace('vVER','v'+V).replace('GATE',G)
bl=rd('docs/backlog-log.md');assert '(task ST-S10)' not in bl
wr('docs/backlog-log.md',bl.rstrip('\n')+'\n\n'+log.rstrip('\n')+'\n')
un=rd('desktop/update-notes.txt');line=("Settings, step 10 (v%s): the Audio page has every audio setting once, as cards: Audio driver (output, buffer, sample rate), "
 "Running now (what the engine really runs at, latency, the device it plays through, dropouts) and Advanced; the Control Panel pop-up is gone. "
 "A new sample rate or buffer, or a device you have not used before, asks Keep? and goes back by itself after 15 s; a device you used before "
 "switches at once.")%V
assert line not in un;wr('desktop/update-notes.txt',line+'\n'+un)
dv=rd('docs/device-backlog-2026-11-25.md');a='- Task ST (the settings rebuild, one step per run): **step S10 built and tested, not released yet**'
assert dv.count(a)==1;i=dv.index(a);j=dv.index('\n',i)
new=("- Task ST (the settings rebuild, one step per run): **steps S1 to S10 done**, v0.230, v0.231, v0.236, v0.240, v0.250, v0.251, v0.265, "
 "v0.275, v0.282 and v%s. S10: Settings › Audio holds every audio setting once, as cards (Audio driver: output, buffer, larger playback buffer, "
 "sample rate, the Audio devices window; Running now: engine rate, real buffer, output latency, the device, dropouts; Advanced: render blocks, "
 "headroom, recording offset, keep awake; Test tone); the Control Panel pop-up is gone and the DAC page's copies are read-outs with Change on "
 "Audio; a new rate or buffer and a first-time device ask Keep? and go back by themselves after 15 s, a known device switches at once (D1b, "
 "answer 4); the output messages name both Mac and Windows. Earlier steps: see the log entries 'task ST-S1' to 'task ST-S9'. Next: S11 (audio "
 "devices in the picked design B2: role cards, the Listening and Recording setups, the switch on arming).")%V
wr('docs/device-backlog-2026-11-25.md',dv[:i]+new+dv[j:])
print('docs for v%s written'%V)
