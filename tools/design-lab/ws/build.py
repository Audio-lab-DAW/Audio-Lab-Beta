# task WS-0: inline the splash drawing code (SPLBG, unchanged from index.html) into the pick page
import re,sys,os
h=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(h,'start.src.html')).read();sp=open(os.path.join(h,'splbg.js')).read()
assert src.count('/*SPLBG*/')==1 and sp.startswith('var SPLBG=(function(){')
open(os.path.join(h,'start.html'),'w').write(src.replace('/*SPLBG*/',sp))
print('start.html',len(src)+len(sp))
