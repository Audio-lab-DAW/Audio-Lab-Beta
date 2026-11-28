"""Settings lab (task ST-S4): dump every control inside the Settings window from a fresh profile: id, kind, page, block, label, help, value.
The table in index.html (STT, task ST-S4) is built from this dump and the audit (docs/settings-audit.md); rerun to check it.
  python3 tools/settings-lab/dump_controls.py [index.html] [out.json]"""
import sys,os,json,mimetypes
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
F=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else 'index.html');ROOT=os.path.dirname(F);OUT=sys.argv[2] if len(sys.argv)>2 else 'controls.json'
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html';f=os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type=mimetypes.guess_type(f)[0] or 'application/octet-stream')
JS=r"""()=>{const out=[];const T=typeof TIPS!=='undefined'?TIPS:{};
 for(const sec of document.querySelectorAll('#setBody section[data-page]')){const pg=sec.dataset.page;
  const els=[...sec.querySelectorAll('input,select,textarea,button')];
  for(const el of els){if(!el.id)continue;let blk='';{let n=el;while(n&&n!==sec){let p=n.previousElementSibling;while(p){if(p.tagName==='H4'){blk=p.textContent.trim();break}const h=p.querySelector&&[...p.querySelectorAll('h4')].pop();if(h){blk=h.textContent.trim();break}p=p.previousElementSibling}if(blk)break;n=n.parentElement}}
   const lab=el.closest('label')||(el.id&&sec.querySelector('label[for="'+el.id+'"]'))||el.closest('.row,.cprow,.pnlrow,.phrow');
   let lt=lab?(lab.textContent||'').replace(/\s+/g,' ').trim():'';if(el.tagName==='SELECT'&&lab){lt=lt.replace([...el.options].map(o=>o.textContent).join(' ').replace(/\s+/g,' ').trim(),'').trim()}
   let tip='';for(const k in T){try{if(el.matches(k)||(lab&&lab.matches&&lab.matches(k))){tip=T[k];break}}catch(e){}}
   const ttl=el.title||el.dataset.tip||(lab&&(lab.title||lab.dataset.tip))||'';
   out.push({id:el.id,tag:el.tagName.toLowerCase(),type:el.type||'',pg,blk,label:lt.slice(0,160),aria:el.getAttribute('aria-label')||'',tip,title:ttl,
    val:el.type==='checkbox'?el.checked:(el.tagName==='BUTTON'?null:el.value),opts:el.tagName==='SELECT'?[...el.options].map(o=>[o.value,o.textContent.trim()]):null,hidden:!el.offsetParent&&!sec.hidden?1:0})}}
 return out}"""
with sync_playwright() as p:
    b=p.chromium.launch();c=b.new_context(viewport={'width':1600,'height':1000});pg=c.new_page();pg.route('https://app.test/**',alsong(serve))
    pg.add_init_script("if(!sessionStorage.getItem('d4')){sessionStorage.setItem('d4','1');localStorage.setItem('audiolab-ui',JSON.stringify({order:['arr','fx','tr','map'],splash:false,lat3:1}))}")
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(3000)
    pg.evaluate("()=>AudioLab.run(\"openSettings('general')\")");pg.wait_for_timeout(800)
    tabs=pg.evaluate("()=>[...document.querySelectorAll('#setNav [data-tab]')].map(b=>b.dataset.tab)")
    for t in tabs:
        pg.click('#setNav [data-tab=%s]'%t);pg.wait_for_timeout(250)
    d=pg.evaluate("()=>AudioLab.run('JSON.stringify(('+(%s)+')())')"%json.dumps(JS))
    json.dump(json.loads(d),open(OUT,'w'),indent=1);print(len(json.loads(d)),'controls')
    b.close()
