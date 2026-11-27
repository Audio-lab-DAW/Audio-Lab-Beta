# task AB2 (v0.229): the About card in the Settings menu gets the fine atom (FATOM) and a small splash drawing (SPLBG) in the drawing's colours. python3 tools/edits/taskAB2.py index.html   (every replacement must match exactly once)
import sys,os
f=sys.argv[1];d=os.path.dirname(os.path.abspath(__file__));s=open(f,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]);s=s.replace(a,b)
css=open(d+'/taskAB2_css.txt',encoding='utf-8').read();js=open(d+'/taskAB2_block.js',encoding='utf-8').read()
# the card: the canvas of the blurred balls becomes the drawing's canvas
rep('<div class="navAtom" title="AudioLab Pro"><canvas class="bubc" aria-hidden="true"></canvas>','<div class="navAtom" title="AudioLab Pro"><canvas class="nab" aria-hidden="true"></canvas>')
# SPLBG: the pick takes its own memory and test keys (the splash keeps its own), and the drawing code and the spectrogram width are shared
rep("function pick(){var f=null,last=null,w=[],tot=0,i,r;try{f=localStorage.getItem('audiolab-splash-test');last=localStorage.getItem('audiolab-splash-last')}catch(e){}",
    "function pick(lk,tk){lk=lk||'audiolab-splash-last';var f=null,last=null,w=[],tot=0,i,r;try{f=localStorage.getItem(tk||'audiolab-splash-test');last=localStorage.getItem(lk)}catch(e){}")
rep("try{localStorage.setItem('audiolab-splash-last',KINDS[i])}catch(e){}return KINDS[i]}","try{localStorage.setItem(lk,KINDS[i])}catch(e){}return KINDS[i]}")
rep("return{attach:attach,stop:stop,pick:pick,KINDS:KINDS,PAL:PAL,","return{attach:attach,stop:stop,pick:pick,KINDS:KINDS,PAL:PAL,FN:FN,BW:BW,")
rep(".dacv{display:flex;",css+".dacv{display:flex;")
rep("function askChoice(title,text,btns,icon){",js+"function askChoice(title,text,btns,icon){")
rep("const VERSION='0.228'","const VERSION='0.229'")
open(f,'w',encoding='utf-8').write(s);print('ok',len(s))
