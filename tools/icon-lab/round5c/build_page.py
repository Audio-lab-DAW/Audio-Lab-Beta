"""Builds the self-contained pick page (pick-page.html) from page.src.html: round 4's page styles, round 5's icons5.js
(M5d as picked; palettes, Dock and macOS mock-ups), this round's icons5c.js and small5c.js."""
import os
d = os.path.dirname(os.path.abspath(__file__))
def rd(*p): return open(os.path.join(d, *p)).read()
def js(*p): return rd(*p).replace('</script', '<\\/script')
s = rd('page.src.html')
r4 = rd('..', 'round4', 'page.src.html')
s = s.replace('<!--CSS4-->', r4[r4.index('<style>'):r4.index('</style>') + 8], 1)
s = s.replace('/*ICONS5*/', js('..', 'round5', 'icons5.js'), 1)
s = s.replace('/*ICONS5C*/', js('icons5c.js'), 1)
s = s.replace('/*SMALL5C*/', js('small5c.js'), 1)
open(os.path.join(d, 'pick-page.html'), 'w').write(s)
print(len(s))
