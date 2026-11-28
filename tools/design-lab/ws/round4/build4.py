# task WS-0d: build the final pick page. Inlines the round 1 page's CSS (same family), SPLBG (unchanged copy from index.html, for S2 moons),
# r2draw.js (R4 interference, R6 Lissajous, R7 TRAPPIST-1: in the set, unchanged) and the round 4 drawings (r4a to r4e, in order)
import os
h=os.path.dirname(os.path.abspath(__file__));up=os.path.dirname(h)
r=lambda p:open(p,encoding='utf-8').read()
src=r(os.path.join(h,'start4.src.html'));one=r(os.path.join(up,'start.src.html'));r2=r(os.path.join(up,'r2draw.js'));sp=r(os.path.join(up,'splbg.js'))
r4='\n'.join(r(os.path.join(h,n)) for n in ('r4a_base.js','r4b_dipole.js','r4c_phase.js','r4d_fourier.js','r4e_new.js'))
css=one[one.index('<style>')+7:one.index('</style>')]
for m in ('/*CSS1*/','/*SPLBG*/','/*R2DRAW*/','/*R4DRAW*/'):assert src.count(m)==1,m
assert r2.startswith('/* Task WS-0b') and r4.startswith('/* Task WS-0d') and sp.startswith('var SPLBG=(function(){')
assert '—' not in r4 and '—' not in src,'no em dashes'
out=src.replace('/*CSS1*/',css).replace('/*SPLBG*/',sp).replace('/*R2DRAW*/',r2).replace('/*R4DRAW*/',r4)
open(os.path.join(h,'start4.html'),'w',encoding='utf-8').write(out);print('start4.html',len(out))
