"""Build tools/edits/taskST_S4_table.js (the settings table STT) from st_table_src.py and a control dump of a fresh profile.
  python3 tools/settings-lab/dump_controls.py index.html controls.json
  python3 tools/settings-lab/make_table.py controls.json"""
import sys,os,json
H=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,H)
from st_table_src import R
D={x['id']:x for x in json.load(open(sys.argv[1] if len(sys.argv)>1 else 'controls.json'))}
out=[];miss=[]
for (i,l,pg,b,sc,k,c,t,w,x) in R:
    e={'id':i,'l':l,'pg':pg,'b':b,'sc':sc,'k':k,'c':c,'t':t}
    cid=c[1:] if c.startswith('#') and ' ' not in c else None
    dd=D.get(cid) if cid else None
    if dd:
        if dd['pg']!=pg:miss.append((i,'page',dd['pg']))
        if not b:e['b']=dd['blk']
        if t in('check','select','range','number','text','color'):e['d']=dd['val']
        tip=dd['tip'].split('|',1)[-1] if dd['tip'] else (dd['title'] or '')
        if tip:e['h']=tip
    elif t in('check','select','range','number','text','color'):miss.append((i,'no control',c))
    if 'd' in x:e['d']=x['d']
    if not e['b']:e['b']={'general':'General','dac':'Interface and DAC','perf':'Performance','glass':'Glass','keys':'Keyboard shortcuts','layout':'Interface'}.get(pg,'')
    e['w']=w
    for kk in('own','same'):
        if kk in x:e[kk]=x[kk]
    if e.get('d',0) is None:del e['d']
    out.append(e)
if miss:print('CHECK',miss)
js='/* the settings table (task ST-S4): one row per setting in the Settings window. Built by tools/settings-lab/make_table.py; see st_table_src.py for the fields. */\nconst STT=[\n'+',\n'.join(json.dumps(e,ensure_ascii=False,separators=(',',':')) for e in out)+'];\n'
open(os.path.join(H,'..','edits','taskST_S4_table.js'),'w',encoding='utf-8').write(js);print(len(out),'rows')
