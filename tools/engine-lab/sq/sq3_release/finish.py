"""Task SQ3 release, after release.sh: the status rows, the settings-ids 'Since', the release-run lines in the backlog entry.
  python3 tools/engine-lab/sq/sq3_release/finish.py"""
import re
v=re.search(r"const VERSION='([\d.]+)'",open('index.html').read()).group(1)
p='docs/quality-build.md';s=open(p).read()
s,n=re.subn(r"\| built and tested \(45 of 45 on v0\.296 \+ SQ1 \+ SQ3, 28 Nov\); \*\*done\*\*, (v0\.\d+) \|",r"| **done**, \1 |",s);assert n==1
s=s.replace("| SQ3b | The sinc (or cubic) read for pitched samples (Q12), under the device's quality | |","| SQ3b | The sinc (or cubic) read for pitched samples (Q12), under the device's quality | next |");open(p,'w').write(s)
p='docs/settings-ids.md';s=open(p).read();a="named in SQ3) | `songHiFi` | SQ3 |";assert s.count(a)==1;open(p,'w').write(s.replace(a,"named in SQ3) | `songHiFi` | %s |"%v))
p='docs/backlog-log.md';s=open(p).read()
a='### Left\n- SQ3b (next)';i=s.rindex(a)
s=s[:i]+("- Release run (28 Nov, after the gate's second freeze 12:35 to 15:4x UTC; six releases of other lanes landed while it was tested, so rebased up to v%s's base): `taskSQ3.py` 45/45 and `taskSQ1.py` 57/57 (on v0.304), `taskXT_DL2.py` 24/24, lint clean, `smoke_electron.js` real, none and push1-loop clean (frames p50 16.7, p95 50.0 ms); on the final rebase: lint and `taskSQ3.py` again. Built and fully checked on v0.296 at 12:30 UTC before that freeze.\n"
 "- Fixes for RG's fourth run (v0.297 not promoted, two regressions from v0.296, SQ1): `sq.cleanAll` and `sq.classicAll` listed in `docs/commands.md` (2821391, `taskXT_DL2.py` 24/24); the Settings row `songHiFi` gets its stable id `project.songHiFi` (set in `XT_SET_NS` after load from lane N's block, since the registry is defined later in the file) and its row in `docs/settings-ids.md`: both songHiFi checks of `taskXT_DL3.py` pass; its two remaining failures are `wsStart` (lane Q's start screen row, not lane N's).\n\n")%v+s[i:]
open(p,'w').write(s);print('finished',v)
