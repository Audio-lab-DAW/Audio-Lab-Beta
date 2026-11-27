# task AB1 (v0.225): the About window with the Earth pictures and the fine atom. python3 tools/edits/taskAB1.py index.html   (every replacement must match exactly once)
import sys,os
f=sys.argv[1];d=os.path.dirname(os.path.abspath(__file__));s=open(f,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]);s=s.replace(a,b)
css=open(d+'/taskAB1_css.txt',encoding='utf-8').read();js=open(d+'/taskAB1_block.js',encoding='utf-8').read()
rep(".dacv{display:flex;",css+".dacv{display:flex;")
rep("function askChoice(title,text,btns,icon){",js+"function askChoice(title,text,btns,icon){")
rep("const VERSION='0.224'","const VERSION='0.225'")
open(f,'w',encoding='utf-8').write(s);print('ok',len(s))
