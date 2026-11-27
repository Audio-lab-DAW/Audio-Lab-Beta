"""Task ST-S9 (settings rebuild, step S9): the help line at the foot of the Settings window (D4c) with default and scope, and a help line for
every setting and control in the window that had none (taskST_S9_help.js and taskST_S9_block.js before askChoice, taskST_S9_css.txt before
.dacv, the version line).
  python3 tools/edits/taskST_S9.py [index.html] [version]"""
import sys,os,re
H=os.path.dirname(os.path.abspath(__file__));P=sys.argv[1] if len(sys.argv)>1 else 'index.html';V=sys.argv[2] if len(sys.argv)>2 else '0.278'
HELP=open(os.path.join(H,'taskST_S9_help.js'),encoding='utf-8').read().rstrip('\n')
B=open(os.path.join(H,'taskST_S9_block.js'),encoding='utf-8').read().replace('/*HELP*/',HELP).replace("v0.278","v"+V).replace("{v:'0.278'}","{v:'"+V+"'}")
C=open(os.path.join(H,'taskST_S9_css.txt'),encoding='utf-8').read().replace("v0.278","v"+V)
s=open(P,encoding='utf-8').read()
assert 'const STS9=' not in s and 'const STS8=' in s and 'const ST_HOOKS' not in s and 'const ST9H' not in s
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]);s=s.replace(a,b)
rep('function askChoice(title,text,btns,icon){',B.rstrip('\n')+'\nfunction askChoice(title,text,btns,icon){')
rep('.dacv{display:flex;',C.rstrip('\n')+'\n.dacv{display:flex;')
m=re.findall(r"const VERSION='([0-9.]+)'",s);assert len(m)==1
rep("const VERSION='"+m[0]+"'","const VERSION='"+V+"'")
open(P,'w',encoding='utf-8').write(s);print('ok',m[0],'->',V)
