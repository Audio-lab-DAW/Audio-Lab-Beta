"""Task ST-S8 (settings rebuild, step S8): scope marks, the Project page cards (this song, new projects), loudness target and tempo lane per project
(taskST_S8_block.js before askChoice, taskST_S8_css.txt before .dacv, the version line).
  python3 tools/edits/taskST_S8.py [index.html] [version]"""
import sys,os,re
H=os.path.dirname(os.path.abspath(__file__));P=sys.argv[1] if len(sys.argv)>1 else 'index.html';V=sys.argv[2] if len(sys.argv)>2 else '0.262'
B=open(os.path.join(H,'taskST_S8_block.js'),encoding='utf-8').read().replace("v0.262","v"+V).replace("{v:'0.262'}","{v:'"+V+"'}")
C=open(os.path.join(H,'taskST_S8_css.txt'),encoding='utf-8').read().replace("v0.262","v"+V)
s=open(P,encoding='utf-8').read()
assert 'const STS8=' not in s and 'const STS7=' in s
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]);s=s.replace(a,b)
rep('function askChoice(title,text,btns,icon){',B.rstrip('\n')+'\nfunction askChoice(title,text,btns,icon){')
rep('.dacv{display:flex;',C.rstrip('\n')+'\n.dacv{display:flex;')
m=re.findall(r"const VERSION='([0-9.]+)'",s);assert len(m)==1
rep("const VERSION='"+m[0]+"'","const VERSION='"+V+"'")
open(P,'w',encoding='utf-8').write(s);print('ok',m[0],'->',V)
