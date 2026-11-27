"""Task ST-S5 (settings rebuild, step S5): the new pages in the picked structure A3. 13 pages in four groups, card grids, a strip of live
read-outs, each block moved whole (taskST_S5_block.js before askChoice, taskST_S5_css.txt before .dacv); the Settings search indexes the
new top-level pages and keeps the old page names as search words.
  python3 tools/edits/taskST_S5.py [index.html]"""
import sys,os
H=os.path.dirname(os.path.abspath(__file__));P=sys.argv[1] if len(sys.argv)>1 else 'index.html'
B=open(os.path.join(H,'taskST_S5_block.js'),encoding='utf-8').read();C=open(os.path.join(H,'taskST_S5_css.txt'),encoding='utf-8').read()
s=open(P,encoding='utf-8').read()
assert 'const STS5=' not in s
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]);s=s.replace(a,b)
A='function askChoice(title,text,btns,icon){'
rep(A,B.rstrip('\n')+'\n'+A)
rep('.dacv{display:flex;',C.rstrip('\n')+'\n.dacv{display:flex;')
# search: one entry per top-level page (Glass & light and Colours & clips now sit inside Appearance), old names as words
rep("for(const sec of document.querySelectorAll('#setBody section[data-page]')){const tab=sec.dataset.page,nb=navs.find(b=>b.dataset.tab===tab),tn=nb?nb.textContent.trim():tab;let head='';",
    "for(const sec of document.querySelectorAll('#setBody>section[data-page]')){const tab=sec.dataset.page,nb=navs.find(b=>b.dataset.tab===tab),tn=nb?nb.textContent.trim():tab;let head='';")
rep("for(const sec of document.querySelectorAll('#setBody section[data-page]')){const tab=sec.dataset.page,nb=navs.find(b=>b.dataset.tab===tab);if(nb)IDX.push({tab,tn:nb.textContent.trim(),el:null,t:nb.textContent.trim(),head:'',ex:extra[tab]||'',page:1})}",
    "for(const sec of document.querySelectorAll('#setBody>section[data-page]')){const tab=sec.dataset.page,nb=navs.find(b=>b.dataset.tab===tab);if(nb)IDX.push({tab,tn:nb.textContent.trim(),el:null,t:nb.textContent.trim(),head:'',ex:(extra[tab]||'')+' '+(typeof ST5W==='object'&&ST5W[tab]||'')+(tab==='appearance'?' '+(extra.glass||'')+' '+(extra.colors||''):''),page:1})}")
open(P,'w',encoding='utf-8').write(s);print('ok')
