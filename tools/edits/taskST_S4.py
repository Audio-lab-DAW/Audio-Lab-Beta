"""Task ST-S4 (settings rebuild, step S4): one settings table in the code (STT, from taskST_S4_table.js, made by tools/settings-lab/make_table.py)
and its helpers (SETT, from taskST_S4_block.js), before askChoice. No visible change.
  python3 tools/edits/taskST_S4.py [index.html]"""
import sys,os
H=os.path.dirname(os.path.abspath(__file__));P=sys.argv[1] if len(sys.argv)>1 else 'index.html'
T=open(os.path.join(H,'taskST_S4_table.js'),encoding='utf-8').read();B=open(os.path.join(H,'taskST_S4_block.js'),encoding='utf-8').read()
s=open(P,encoding='utf-8').read()
A='function askChoice(title,text,btns,icon){'
assert s.count(A)==1 and 'const STS4=' not in s and 'const STT=' not in s
s=s.replace(A,T.rstrip('\n')+'\n'+B.rstrip('\n')+'\n'+A)
open(P,'w',encoding='utf-8').write(s);print('ok')
