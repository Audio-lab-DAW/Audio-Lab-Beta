"""Task ST-S6 (settings rebuild, step S6): search with synonyms and help text (from the settings table STT), the whole path in each result,
in-place options with "Show me" (taskST_S6_block.js before askChoice, taskST_S6_css.txt before .dacv; four edits in the Settings search).
  python3 tools/edits/taskST_S6.py [index.html]"""
import sys,os
H=os.path.dirname(os.path.abspath(__file__));P=sys.argv[1] if len(sys.argv)>1 else 'index.html'
B=open(os.path.join(H,'taskST_S6_block.js'),encoding='utf-8').read();C=open(os.path.join(H,'taskST_S6_css.txt'),encoding='utf-8').read()
s=open(P,encoding='utf-8').read()
assert 'const STS6=' not in s and 'const STS5=' in s
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]);s=s.replace(a,b)
rep('function askChoice(title,text,btns,icon){',B.rstrip('\n')+'\nfunction askChoice(title,text,btns,icon){')
rep('.dacv{display:flex;',C.rstrip('\n')+'\n.dacv{display:flex;')
# the index takes the table's labels, help lines and synonyms, and the in-place options
rep("page:1})}};","page:1})}try{if(typeof ST6==='object')ST6.extend(IDX)}catch(e){console.warn('settings search (ST-S6)',e)}};")
# an in-place option closes Settings and shows the control
rep("const go=it=>{const nb=it.tab?","const go=it=>{if(it.ip){R.hidden=true;q.value='';ST6.show(it);return}const nb=it.tab?")
rep(".sort((a,b)=>b.sc-a.sc).slice(0,9);",".sort((a,b)=>b.sc-a.sc).slice(0,12);")
rep("R.innerHTML=hits.length?hits.map((h,i)=>`<button role=\"option\" data-qi=\"${i}\" class=\"${i===0?'on':''}\"><b>${esc(h.it.t)}</b><small>${esc(h.it.tn)}${h.it.head&&h.it.head!==h.it.t?' › '+esc(h.it.head):''}</small></button>`).join('')",
    "R.innerHTML=hits.length?hits.map((h,i)=>typeof ST6==='object'?ST6.item(h.it,i,v):`<button role=\"option\" data-qi=\"${i}\" class=\"${i===0?'on':''}\"><b>${esc(h.it.t)}</b><small>${esc(h.it.tn)}${h.it.head&&h.it.head!==h.it.t?' › '+esc(h.it.head):''}</small></button>`).join('')")
open(P,'w',encoding='utf-8').write(s);print('ok')
