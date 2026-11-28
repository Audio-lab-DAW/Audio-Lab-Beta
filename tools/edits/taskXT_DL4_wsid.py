"""Task XT-DL4 (lane H): the start screen's Settings row wsStart (lane Q, task WS-1) gets its stable id general.wsStart in lane H's registry
XT_SET_NS and a row in docs/settings-ids.md (taskXT_DL3.py asks for both). Run after taskXT_DL4.py, before taskXT_DL4_release.py.
  python3 tools/edits/taskXT_DL4_wsid.py <version>"""
import sys
V = sys.argv[1]
s = open('index.html', encoding='utf-8').read()
a = 'const XT_SET_NS={"tips":"general.tips",'
assert s.count(a) == 1
if '"wsStart":' in s[s.index(a):s.index('}', s.index(a))]: print('already named'); sys.exit(0)
s = s.replace(a, 'const XT_SET_NS={"tips":"general.tips","wsStart":"general.wsStart",')
open('index.html', 'w', encoding='utf-8').write(s)
d = open('docs/settings-ids.md', encoding='utf-8').read()
b = "| `general.askClose` | Ask before closing with unsaved changes | `askClose` | 0.295 |\n"
assert d.count(b) == 1 and 'general.wsStart' not in d
d = d.replace(b, b + "| `general.wsStart` | Show the start screen at start-up (lane Q, task WS-1, named in XT-DL4) | `wsStart` | %s |\n" % V)
open('docs/settings-ids.md', 'w', encoding='utf-8').write(d); print('ok')
