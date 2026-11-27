"""Builds the self-contained pick page (pick-page.html) from page.src.html, round 2's geom.json, round 3's icons3.js
(the J3, J4, J6, J8, J9 and J10 references) and this round's icons4.js and small4.js."""
import os
d = os.path.dirname(os.path.abspath(__file__))
def js(p): return open(p).read().replace('</script', '<\\/script')
s = open(os.path.join(d, 'page.src.html')).read()
s = s.replace('/*GEOM*/', 'window.AL2_GEOM=' + open(os.path.join(d, '..', 'round2', 'geom.json')).read() + ';', 1)
s = s.replace('/*ICONS3*/', js(os.path.join(d, '..', 'round3', 'icons3.js')), 1)
s = s.replace('/*ICONS4*/', js(os.path.join(d, 'icons4.js')), 1)
s = s.replace('/*SMALL4*/', js(os.path.join(d, 'small4.js')), 1)
open(os.path.join(d, 'pick-page.html'), 'w').write(s)
print(len(s))
