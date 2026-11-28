"""Builds the self-contained pick page (pick-page.html) from page.src.html: round 4's page styles, every PNG of
renders/manifest.json as a data URI (run node render5s.js first), and the names and notes of small5s.js."""
import base64, json, os, subprocess
d = os.path.dirname(os.path.abspath(__file__))
def rd(*p): return open(os.path.join(d, *p)).read()
man = json.load(open(os.path.join(d, 'renders', 'manifest.json')))
img = {}
for kind, m in man.items():
    for k, rel in m.items():
        img[kind + ':' + k] = 'data:image/png;base64,' + base64.b64encode(open(os.path.join(d, 'renders', rel), 'rb').read()).decode()
des = json.loads(subprocess.check_output(['node', '-e', "const S=require('./small5s.js');const o={};for(const k of S.IDS)o[k]={name:S.D[k].name,note:S.D[k].note};process.stdout.write(JSON.stringify(o))"], cwd=d))
s = rd('page.src.html')
r4 = rd('..', 'round4', 'page.src.html')
s = s.replace('<!--CSS4-->', r4[r4.index('<style>'):r4.index('</style>') + 8], 1)
s = s.replace('/*IMG*/', json.dumps(img), 1).replace('/*DES*/', json.dumps(des), 1)
open(os.path.join(d, 'pick-page.html'), 'w').write(s)
print(len(s))
