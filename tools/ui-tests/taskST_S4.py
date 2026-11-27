"""Task ST-S4 (settings rebuild, step S4): the settings table STT and its helpers SETT.
Every row finds its control on its own page; every stored control in the window is in the table; a fresh profile shows each row's default;
the stored key of each row is the one its control writes (checked by changing it and putting it back); rows are marked (data-stid, data-stsc);
an older profile reads back through SETT; find() knows synonyms; draw() makes a working row that stays in step with the window;
no visible change: the Settings window's structure and text are the same as the previous version, page by page. Dark and Light level, no console errors.
  python3 tools/ui-tests/taskST_S4.py [repo dir] [out dir] [previous index.html]"""
import sys,os,mimetypes,json,re
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else '.');OUT=sys.argv[2] if len(sys.argv)>2 else '.';OLD=sys.argv[3] if len(sys.argv)>3 else None;os.makedirs(OUT,exist_ok=True)
N=[0,0];FAIL=[]
def ck(name,ok,info=''):
    N[0]+=1
    if ok:N[1]+=1
    else:FAIL.append(name);print('  FAIL',name,str(info)[:600])
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html'
    f=OLD if (p=='old.html' and OLD) else os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type='text/html' if f.endswith('.html') else (mimetypes.guess_type(f)[0] or 'application/octet-stream'))
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
J=lambda pg,c:json.loads(R(pg,"JSON.stringify("+c+")"))
def ctx(b,lite,old,page='index.html'):
    c=b.new_context(viewport={'width':1600,'height':1000});pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and errs.append('console '+m.text[:200]))
    pg.route('https://app.test/**',serve)
    u=dict(old,order=['arr','fx','tr','map'],splash=False,lat3=1,lite=lite,liteMan=lite)
    pg.add_init_script("if(!sessionStorage.getItem('t4')){sessionStorage.setItem('t4','1');localStorage.setItem('audiolab-ui',JSON.stringify(%s))}"%json.dumps(u))
    pg.goto('https://app.test/'+page);pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(3000)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
    return c,pg,errs
def alltabs(pg):
    R(pg,"openSettings('general')");pg.wait_for_timeout(500)
    for t in pg.evaluate("()=>[...document.querySelectorAll('#setNav [data-tab]')].map(b=>b.dataset.tab)"):
        pg.click('#setNav [data-tab=%s]'%t);pg.wait_for_timeout(200)
# structure and text of each page, live numbers and the marks left out
STRUCT=r"""()=>{const o={};for(const sec of document.querySelectorAll('#setBody section[data-page]')){const a=[];
 const walk=n=>{if(n.nodeType===3){const t=n.textContent.replace(/[\d.,:−-]+/g,'#').replace(/\s+/g,' ').trim();if(t)a.push('"'+t);return}if(n.nodeType!==1||n.tagName==='CANVAS'||n.tagName==='svg')return;
  const at=[...n.attributes].filter(x=>!/^(data-stid|data-stsc|style|value|data-tip|title)$/.test(x.name)&&!/^aria-valuenow/.test(x.name)).map(x=>x.name+'='+(x.name==='class'?x.value.split(' ').filter(c=>!/^(on|sflash|hot|act)$/.test(c)).sort().join('.'):x.value.replace(/[\d.]+/g,'#'))).sort().join(' ');a.push('<'+n.tagName+' '+at);for(const ch of n.childNodes)walk(ch)};
 walk(sec);o[sec.dataset.page]=a}return o}"""
EXCL={'ttFn','scQ','phCC','pmEdge','pmAnim','setRefr','fxRefr'}
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        c,pg,errs=ctx(b,lite,{})
        ck(f'{L}: version',float(R(pg,"VERSION"))>=0.240)
        alltabs(pg)
        rows=J(pg,"STT.map(r=>({id:r.id,pg:r.pg,t:r.t,c:r.c,k:r.k,d:r.d,own:r.own||'',same:r.same||'',sc:r.sc,has:'d' in r}))")
        ck(f'{L}: the table has the Settings window rows',len(rows)>=90,len(rows))
        ck(f'{L}: ids unique',len({r['id'] for r in rows})==len(rows))
        bad=[r['id'] for r in rows if not R(pg,"(()=>{const e=SETT.ctl(%s);return !!e&&!!e.closest('#setBody section[data-page=%s]')})()"%(json.dumps(r['id']),r['pg']))]
        ck(f'{L}: every row finds its control on its own page',not bad,bad)
        m=J(pg,"STT.filter(r=>!r.l||!r.b||!/^(app|project|session)$/.test(r.sc)||!r.w).map(r=>[r.id,r.b,r.sc])");ck(f'{L}: every row has a label, block, scope and search words',m==[],m)
        inwin=J(pg,"[...document.querySelectorAll('#setBody section[data-page] input[id],#setBody section[data-page] select[id],#setBody section[data-page] textarea[id]')].map(e=>e.id)")
        cov=set(r['c'][1:] for r in rows if r['c'].startswith('#'))
        un=[i for i in inwin if i not in cov and i not in EXCL]
        ck(f'{L}: every stored control in the window is in the table',not un,un)
        if not lite:
            nd=[r['id'] for r in rows if r['has'] and R(pg,"SETT.isDefault(%s)"%json.dumps(r['id'])) is False and r['id'] not in ('splash',)]
            ck(f'{L}: a fresh profile shows every default',not nd,[(i,R(pg,"JSON.stringify([SETT.val(%s),SETT.get(%s).d])"%(json.dumps(i),json.dumps(i)))) for i in nd])
        n=R(pg,"document.querySelectorAll('#setBody [data-stid]').length")
        ck(f'{L}: rows are marked with their id and scope',n>=len(rows)-3 and R(pg,"document.querySelector('[data-stid=mono]').dataset.stsc")=='app' and R(pg,"document.querySelector('[data-stid=exName]').dataset.stsc")=='project',n)
        # keys: change through the table, read the stored key, put back
        wrong=[]
        for r in rows:
            if r['own'] or r['same'] or r['t'] not in ('check','select') or not r['k'].startswith('UI.') or r['id'] in ('outDev','inDev','rate','buffer','renderBlocks','scSet','devProfile','bitPerfect'):continue
            i=json.dumps(r['id'])
            res=J(pg,"""(()=>{const id=%s,r=SETT.get(id),el=SETT.ctl(id);const k0=JSON.stringify(SETT.key(id)??null),v0=SETT.val(id);let nv;
              if(r.t==='check')nv=!v0;else{const o=[...el.options].map(o=>o.value).filter(v=>v!==v0);if(!o.length)return {skip:1};nv=o[0]}
              SETT.set(id,nv);const k1=JSON.stringify(SETT.key(id)??null),v1=SETT.val(id);SETT.set(id,v0);const k2=JSON.stringify(SETT.key(id)??null);
              return {k0,k1,k2,v1,nv}})()"""%i)
            if res.get('skip'):continue
            if res['k1']==res['k0'] or res['v1']!=res['nv']:wrong.append((r['id'],res))
        ck(f'{L}: each row stores into its key (changed and put back)',not wrong,wrong)
        # find and draw
        ck(f'{L}: find knows synonyms',set(['buffer'])<=set(J(pg,"SETT.find('latency')")) and 'outDev' in J(pg,"SETT.find('sound card')") and 'mono' in J(pg,"SETT.find('mono')"))
        d=J(pg,"""(()=>{const e=SETT.draw('mono');document.body.appendChild(e);const c=e.querySelector('input');c.click();const a=[UI.monoChk,$('#monoChk').checked,e.tagName,e.title.length>20,e.dataset.stid];
          $('#monoChk').click();a.push(c.checked);e.remove();
          const s=SETT.draw('ceiling');document.body.appendChild(s);const sel=s.querySelector('select');a.push([...sel.options].map(o=>o.value).join()===[...$('#ceilSel').options].map(o=>o.value).join());
          sel.value='-6';sel.dispatchEvent(new Event('input'));a.push(UI.ceil,$('#ceilSel').value);SETT.set('ceiling','-1');a.push(sel.value);s.remove();return a})()""")
        ck(f'{L}: draw() makes a working row in step with the window',d==[True,True,'LABEL',True,'mono',False,True,-6,'-6','-1'],d)
        ck(f'{L}: reset() puts a row back to its default',R(pg,"(()=>{SETT.set('grid','80');const a=SETT.isDefault('grid');SETT.reset('grid');return [a,SETT.isDefault('grid'),UI.gridB].join()})()")=='false,true,50')
        ck(f'{L}: glass rows are not reset here',R(pg,"SETT.reset('glassTrans')")==False)
        ck(f'{L}: no console errors',not errs,errs)
        pg.click('#setNav [data-tab=dac]');pg.wait_for_timeout(300);pg.locator('#set .sheet').screenshot(path=f'{OUT}/s4_dac_{L}.png')
        c.close()
        # older profile reads back through SETT
        c,pg,errs=ctx(b,lite,{'monoChk':True,'ceil':-3,'followMode':'lead','follow':True,'mapZoom':'ableton','gridB':70,'asMin':5,'exOpt':{'fmt':'flac','exBit':'16'}})
        alltabs(pg)
        v=J(pg,"['mono','ceiling','follow','zoomStyle','grid','asMin','exFmt','exBit'].map(i=>SETT.val(i))")
        ck(f'{L}: an older profile reads back through the table',v==[True,'-3','lead','ableton','70','5','flac','16'],v)
        ck(f'{L}: older profile: not default where changed',J(pg,"['mono','grid','tips'].map(i=>SETT.isDefault(i))")==[False,False,True])
        ck(f'{L}: older profile: no console errors',not errs,errs)
        c.close()
        # no visible change against the previous version
        if OLD:
            c,pg,e1=ctx(b,lite,{});alltabs(pg);new=pg.evaluate(STRUCT);c.close()
            c,pg,e2=ctx(b,lite,{},'old.html');alltabs(pg);old=pg.evaluate(STRUCT);c.close()
            diff=[k for k in old if old[k]!=new.get(k)]
            info={k:[(i,a,b2) for i,(a,b2) in enumerate(zip(old[k],new[k])) if a!=b2][:3] for k in diff}
            ck(f'{L}: no visible change: every Settings page has the same structure and text as before',not diff and set(old)==set(new),info)
    b.close()
print(f'{N[1]}/{N[0]} checks pass');sys.exit(1 if FAIL else 0)
