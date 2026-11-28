"""Task WS-1 (lane Q): puts the start screen into index.html. Re-run on a fresh index.html after every rebase.
   python3 tools/design-lab/ws/ws1_edit.py [index.html]
Inserts tools/design-lab/ws/ws1.css before `.dacv{display:flex;` and tools/design-lab/ws/ws1.js (with r2draw.js as WSR2:
the drawings R4 to R8 and the dipole flow F1, its particles a little smaller and fewer) before `function askChoice(title,text,btns,icon){`.
Checks the anchors are unique, that nothing is inserted twice and that no new top-level name clashes with the app's."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', '..', 'index.html'))
s = open(P, encoding='utf-8').read()
assert 'task WS-1 (lane Q): the start screen' not in s, 'already inserted'
A_CSS, A_JS = '.dacv{display:flex;', 'function askChoice(title,text,btns,icon){'
assert s.count(A_CSS) == 1 and s.count(A_JS) == 1, 'anchors'
css = open(os.path.join(HERE, 'ws1.css'), encoding='utf-8').read().strip() + '\n'
js = open(os.path.join(HERE, 'ws1.js'), encoding='utf-8').read().strip() + '\n'
r2 = open(os.path.join(HERE, 'r2draw.js'), encoding='utf-8').read().strip()
# r2draw.js as one const of this block (it is one IIFE); only the names it declares at its top
assert r2.count('var R2=(function(){') == 1
r2 = r2.replace('var R2=(function(){', 'const WSR2=(function(){', 1)
# the user: "let's have the particles a little smaller and a little less particles" (F1 only)
for a, b in [("gap=mode===1?1.1:", "gap=mode===1?1.55:"),
             ("if(p[2])dot(c,sg*p[0],p[1],.95*k,'rgba('+P.O+',.3)');else dot(c,sg*p[0],p[1],1.3*k,'rgba('+P.O+',.88)')",
              "if(p[2])dot(c,sg*p[0],p[1],(mode===1?.72:.95)*k,'rgba('+P.O+',.3)');else dot(c,sg*p[0],p[1],(mode===1?1:1.3)*k,'rgba('+P.O+',.88)')")]:
    assert r2.count(a) == 1, a
    r2 = r2.replace(a, b)
assert js.count('/*@WSR2@*/') == 1
js = js.replace('/*@WSR2@*/', r2)
assert '—' not in js + css, 'no em dashes'
# new top-level names must not exist in the app yet
new = set(re.findall(r'^(?:function|async function)\s+([A-Za-z_$][\w$]*)', js, re.M)) | set(re.findall(r'^(?:const|let|var)\s+([A-Za-z_$][\w$]*)', js, re.M))
for n in sorted(new):
    assert not n.startswith(('R2',)), n
    if re.search(r'(?:^|[\s;{}])(?:function\s+|const\s+|let\s+|var\s+)' + re.escape(n) + r'\b', s):
        raise SystemExit('top-level name already in index.html: ' + n)
    assert n.startswith(('ws', 'WS')), 'prefix: ' + n
s = s.replace(A_CSS, css + A_CSS, 1).replace(A_JS, js + A_JS, 1)
open(P, 'w', encoding='utf-8').write(s)
print('WS-1 inserted:', len(css), 'bytes of CSS,', len(js), 'bytes of JS;', len(new), 'top-level names:', ', '.join(sorted(new)))
