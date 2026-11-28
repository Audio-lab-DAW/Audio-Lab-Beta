# task WS-0c: build the round 3 pick page. Inlines the round 1 page's CSS (same family), r2draw.js (today's R5 and R8, to compare) and the round 3 drawings (r3a to r3e, in order)
import os
h=os.path.dirname(os.path.abspath(__file__));up=os.path.dirname(h)
r=lambda p:open(p,encoding='utf-8').read()
src=r(os.path.join(h,'start3.src.html'));one=r(os.path.join(up,'start.src.html'));r2=r(os.path.join(up,'r2draw.js'))
r3='\n'.join(r(os.path.join(h,n)) for n in ('r3a_base.js','r3b_dipole.js','r3c_phase.js','r3d_fourier.js','r3e_new.js'))
css=one[one.index('<style>')+7:one.index('</style>')]
for m in ('/*CSS1*/','/*R2DRAW*/','/*R3DRAW*/'):assert src.count(m)==1,m
assert r2.startswith('/* Task WS-0b') and r3.startswith('/* Task WS-0c')
out=src.replace('/*CSS1*/',css).replace('/*R2DRAW*/',r2).replace('/*R3DRAW*/',r3)
assert '—' not in r3,'no em dashes in the drawings'
open(os.path.join(h,'start3.html'),'w',encoding='utf-8').write(out);print('start3.html',len(out))
