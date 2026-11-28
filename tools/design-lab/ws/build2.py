# task WS-0b: build the round 2 pick page. Inlines the round 1 page's CSS (same family), SPLBG (unchanged copy from index.html) and r2draw.js
import os
h=os.path.dirname(os.path.abspath(__file__))
r=lambda n:open(os.path.join(h,n)).read()
src=r('start2.src.html');one=r('start.src.html');sp=r('splbg.js');r2=r('r2draw.js')
css=one[one.index('<style>')+7:one.index('</style>')]
for m in ('/*CSS1*/','/*SPLBG*/','/*R2DRAW*/'):assert src.count(m)==1,m
assert sp.startswith('var SPLBG=(function(){') and r2.startswith('/* Task WS-0b')
out=src.replace('/*CSS1*/',css).replace('/*SPLBG*/',sp).replace('/*R2DRAW*/',r2)
open(os.path.join(h,'start2.html'),'w').write(out);print('start2.html',len(out))
