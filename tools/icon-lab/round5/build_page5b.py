"""Builds the self-contained round 5b pick page (pick-page-5b.html) from page5b.src.html: round 4's page styles,
round 2's geom.json and round 3's icons3.js (J3 as shipped), round 5b's icons5b.js and small5b.js, IC6's small6.js
(S1 and the small M5 as shipped) and picker-review.json (run picker_data.py first)."""
import os
d = os.path.dirname(os.path.abspath(__file__))
def rd(*p): return open(os.path.join(d, *p)).read()
def js(*p): return rd(*p).replace('</script', '<\\/script')
s = rd('page5b.src.html')
r4 = rd('..', 'round4', 'page.src.html')
s = s.replace('<!--CSS4-->', r4[r4.index('<style>'):r4.index('</style>') + 8], 1)
s = s.replace('/*GEOM*/', 'window.AL2_GEOM=' + rd('..', 'round2', 'geom.json') + ';', 1)
s = s.replace('/*ICONS3*/', js('..', 'round3', 'icons3.js'), 1)
s = s.replace('/*ICONS5B*/', js('icons5b.js'), 1)
s = s.replace('/*SMALL5B*/', js('small5b.js'), 1)
s = s.replace('/*SMALL6*/', '(function(){var module={exports:{}};var require=function(){return {PAL:window.AL5B.PAL};};\n' + js('..', 'ic6', 'small6.js') + '\nwindow.AL6S=module.exports;})();', 1)
s = s.replace('/*PICKER*/', rd('picker-review.json'), 1)
s = s.replace('/*WEAK*/', rd('weak5b.txt').strip().replace("'", "\\'"), 1)
open(os.path.join(d, 'pick-page-5b.html'), 'w').write(s)
print(len(s))
