"""Task ST-S11: the release's docs. Run after tools/edits/taskST_S11.py has put S11 into index.html with the new version:
  python3 tools/edits/taskST_S11_release.py <version> [gate line]
Appends the log entry, puts one line on top of desktop/update-notes.txt and rewrites task ST's line in 'Where it stands' of
docs/device-backlog-2026-11-25.md. Every replacement is asserted unique; running it twice fails instead of writing twice."""
import sys,os
R=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
V=sys.argv[1];G=sys.argv[2] if len(sys.argv)>2 else ("`--here --quick --ref 0.314` on v0.314 + S11: a lint clean, c the start-up smoke test (all 14 scenarios clean), "
 "frame times p50 16.7 ms, p95 33.3 ms (reference 16.7 and 50.0), d windows (19 checks), e Fractals levels and exports (same checksums, 9 export "
 "lines bit-identical to v0.314) all passed.")
rd=lambda p:open(os.path.join(R,p),encoding='utf-8').read()
def wr(p,s):open(os.path.join(R,p),'w',encoding='utf-8').write(s)
idx=rd('index.html');assert "const VERSION='%s'"%V in idx and 'const STS11=' in idx,'run taskST_S11.py with this version first'
log=rd('tools/edits/taskST_S11_log.md').split('-->',1)[1].lstrip('\n').replace('vVER','v'+V).replace('GATE',G)
bl=rd('docs/backlog-log.md');assert '(task ST-S11)' not in bl
wr('docs/backlog-log.md',bl.rstrip('\n')+'\n\n'+log.rstrip('\n')+'\n')
un=rd('desktop/update-notes.txt');line=("Settings, Audio (v%s): a Devices card with Listen through and Record from, and two setups, Listening and Recording. "
 "Recording fills itself with your audio interface for input and output; arming an audio track switches to it at once with a short notice and "
 "Back to Listening, and disarming switches back. Switching is instant and click-free.")%V
assert line not in un;wr('desktop/update-notes.txt',line+'\n'+un)
dv=rd('docs/device-backlog-2026-11-25.md');a='- Task ST (the settings rebuild, one step per run): **steps S1 to S10 done; S11 built and tested, not released yet**'
assert dv.count(a)==1;i=dv.index(a);j=dv.index('\n',i)
new=("- Task ST (the settings rebuild, one step per run): **steps S1 to S11 done**, v0.230, v0.231, v0.236, v0.240, v0.250, v0.251, v0.265, "
 "v0.275, v0.282, v0.298 and v%s. S11: Settings › Audio opens with Devices: role cards Listen through and Record from (the one output and input "
 "selects), the Listening and Recording setups, Recording filled automatically with the interface for both (groupId or name, Mac and Windows "
 "names), changeable by hand; arming an audio track switches by itself with a quiet notice and Back to Listening, disarming goes back (answer 1); "
 "switching is instant with a 25 ms and 30 ms ramp (answer 4); a setting for audio tracks, any track or never. Earlier steps: see the log entries "
 "'task ST-S1' to 'task ST-S10'. Next: S12 (the signal path read-out), then S13 (safe volume synced with the device's own volume).")%V
wr('docs/device-backlog-2026-11-25.md',dv[:i]+new+dv[j:])
ids=rd('docs/settings-ids.md');a2='| `audio.outCheck` | Check the output device | `outCheck` | 0.295 |\n';assert ids.count(a2)==1 and '`audio.setupNow`' not in ids
wr('docs/settings-ids.md',ids.replace(a2,a2+'| `audio.setupNow` | Setup in use (Listening or Recording; task ST-S11) | `setupNow` | %s |\n| `audio.armSwitch` | Switch to Recording when I arm (task ST-S11) | `armSwitch` | %s |\n'%(V,V)))
print('docs for v%s written'%V)
