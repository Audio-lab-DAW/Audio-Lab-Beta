# task SP1 (v0.224): the splash pictures. python3 tools/edits/taskSP1.py index.html   (every replacement must match exactly once)
import sys
f=sys.argv[1];import os;d=os.path.dirname(os.path.abspath(__file__));s=open(f,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]);s=s.replace(a,b)
early=open(d+'/taskSP1_early.js').read().rstrip('\n');css=open(d+'/taskSP1_css.txt').read();js=open(d+'/taskSP1_block.js').read()
rep('<div id="splash" class="ld" data-st="1">','<div id="splash" class="ld sp1" data-st="1">')
rep("ms cubic-bezier(.25,.7,.4,1) forwards'}catch(e){}})();</script>","ms cubic-bezier(.25,.7,.4,1) forwards'}catch(e){}})();\n"+early+"</script>")
rep("const fr=now=>{if(!SPL)return;const sz=about?250:200;","const fr=now=>{if(!SPL||SPL.el!==el||el.classList.contains('sp1'))return;const sz=about?250:200;")
rep(".dacv{display:flex;",css+".dacv{display:flex;")
rep("function askChoice(title,text,btns,icon){",js+"function askChoice(title,text,btns,icon){")
rep("const VERSION='0.223'","const VERSION='0.224'")
open(f,'w',encoding='utf-8').write(s);print('ok',len(s))
