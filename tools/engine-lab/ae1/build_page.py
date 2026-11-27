# Task AE1: build the pick page from page_template.html, dsp.js and the measured results.
#   python3 tools/engine-lab/ae1/build_page.py   -> tools/engine-lab/ae1/sound-quality-picks.html
import os, json
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, 'results')
t = open(os.path.join(H, 'page_template.html')).read()
t = t.replace('/*DSP*/', open(os.path.join(H, 'dsp.js')).read())
t = t.replace('/*PLOTS*/', open(os.path.join(R, 'plots.json')).read())
t = t.replace('/*LAB*/', json.dumps(json.load(open(os.path.join(R, 'lab.json'))), separators=(',', ':')))
t = t.replace('/*APP*/', json.dumps(json.load(open(os.path.join(R, 'app.json'))), separators=(',', ':')))
open(os.path.join(H, 'sound-quality-picks.html'), 'w').write(t)
print('page %.0f kB' % (len(t) / 1024))
