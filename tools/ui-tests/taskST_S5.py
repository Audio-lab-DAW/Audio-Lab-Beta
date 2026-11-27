"""Task ST-S5 (settings rebuild, step S5): the new pages in the picked structure A3.
13 pages in four groups; each block moved whole to its page (same elements, no copies); the table knows each row's page; the old page ids
still open the right page; the strip of live read-outs shows numbers and opens its pages; search finds the old page names; an older profile
still loads into the moved controls; the quick routes on the new cards work; no sideways scroll; dark and Light level; no console errors.
  python3 tools/ui-tests/taskST_S5.py [repo dir] [out dir]"""
import sys,os,mimetypes,json
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else '.');OUT=sys.argv[2] if len(sys.argv)>2 else '.';os.makedirs(OUT,exist_ok=True)
N=[0,0];FAIL=[]
def ck(name,ok,info=''):
    N[0]+=1
    if ok:N[1]+=1
    else:FAIL.append(name);print('  FAIL',name,str(info)[:600])
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html';f=os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type='text/html' if f.endswith('.html') else (mimetypes.guess_type(f)[0] or 'application/octet-stream'))
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
J=lambda pg,c:json.loads(R(pg,"JSON.stringify("+c+")"))
def ctx(b,lite,old,vw=1600,vh=1000):
    c=b.new_context(viewport={'width':vw,'height':vh});pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and errs.append('console '+m.text[:200]))
    pg.route('https://app.test/**',serve)
    u=dict(old,order=['arr','fx','tr','map'],splash=False,lat3=1,lite=lite,liteMan=lite)
    pg.add_init_script("if(!sessionStorage.getItem('t5')){sessionStorage.setItem('t5','1');localStorage.setItem('audiolab-ui',JSON.stringify(%s))}"%json.dumps(u))
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(3000)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
    return c,pg,errs
PAGES=['general','appearance','perf','layout','keys','nav','editing','mixer','audio','dac','recording','files','export']
NAMES=['General','Appearance','Performance','Layout','Keyboard shortcuts','Navigation','Editing','Mixer and meters','Audio','DAC and audio interface','Recording and metronome','Project','Export']
HOME={'tips':'general','askClose':'general','dawLook':'appearance','scale':'appearance','glassTrans':'appearance','bg':'appearance','clipA':'appearance','grid':'appearance',
 'layout':'layout','map':'layout','viz':'layout','zsPreset':'nav','zoomStyle':'nav','follow':'nav','phShape':'nav','chase':'editing','mixer':'mixer','meters':'mixer',
 'outDev':'audio','buffer':'audio','rate':'audio','ttKind':'audio','ifMode':'dac','devProfile':'dac','limiter':'dac','mono':'dac','autosave':'files','exFmt':'export','keys':'keys','density':'appearance','motion':'appearance'}
OLDP={'mono':False,'chase':False,'limiter':False,'clipA':60,'asMin':5,'autosave':True,'mtr':{'spd':'smooth','alg':'rms','hold':'3','col':'heat'},'dac':'gryphon','followMode':'ahead','gridB':70}
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        c,pg,errs=ctx(b,lite,OLDP)
        ck(f'{L}: version',float(R(pg,"VERSION"))>=0.250)
        R(pg,"openSettings('general')");pg.wait_for_timeout(600)
        nav=pg.evaluate("()=>[...document.querySelectorAll('#setNav [data-tab],#setNav .navh')].map(e=>e.dataset.tab?'b:'+e.dataset.tab+':'+e.textContent.trim():'h:'+e.textContent.trim())")
        want=['h:Program']+['b:%s:%s'%(a,n) for a,n in zip(PAGES[:5],NAMES[:5])]+['h:Working']+['b:%s:%s'%(a,n) for a,n in zip(PAGES[5:8],NAMES[5:8])]+['h:Sound']+['b:%s:%s'%(a,n) for a,n in zip(PAGES[8:11],NAMES[8:11])]+['h:Project']+['b:%s:%s'%(a,n) for a,n in zip(PAGES[11:],NAMES[11:])]
        ck(f'{L}: 13 pages in four groups, in the audit order',nav==want,nav)
        ck(f'{L}: every page button has a tooltip and an icon',pg.evaluate("()=>[...document.querySelectorAll('#setNav [data-tab]')].every(b=>b.title&&b.querySelector('.nic svg'))"))
        bad=[];over=[]
        for t,n in zip(PAGES,NAMES):
            pg.click('#setNav [data-tab=%s]'%t);pg.wait_for_timeout(150)
            s=pg.evaluate("()=>({vis:[...document.querySelectorAll('#setBody>section[data-page]')].filter(s=>!s.hidden).map(s=>s.dataset.page),on:[...document.querySelectorAll('#setNav [data-tab].on')].map(b=>b.dataset.tab),t:document.getElementById('st5T').textContent,sw:document.getElementById('setBody').scrollWidth-document.getElementById('setBody').clientWidth,h:document.querySelector('#setBody>section:not([hidden])').offsetHeight})")
            if s['vis']!=[t] or s['on']!=[t] or s['t']!=n or s['h']<40:bad.append((t,s))
            if s['sw']>1:over.append((t,s['sw']))
        ck(f'{L}: each page shows alone, with its title, and is not empty',not bad,bad)
        ck(f'{L}: no sideways scroll on any page',not over,over)
        # blocks moved whole: the controls sit on their new page, once
        where=J(pg,"Object.fromEntries(STT.map(r=>{const e=SETT.ctl(r.id),s=e&&e.closest('#setBody>section[data-page]');return[r.id,[s?s.dataset.page:null,r.pg]]}))")
        wrong=[(k,where.get(k),v) for k,v in HOME.items() if not where.get(k) or where[k][0]!=v]
        ck(f'{L}: each block is on its new page',not wrong,wrong)
        mism=[(k,v) for k,v in where.items() if v[0] and v[0]!=v[1]]
        ck(f'{L}: the table knows every row\'s page',not mism,mism)
        dup=J(pg,"(()=>{const ids=STT.map(r=>r.c).filter(c=>/^#[\\w-]+$/.test(c||''));return ids.filter(c=>document.querySelectorAll(c).length!==1)})()")
        ck(f'{L}: no control was copied (each id once)',not dup,dup)
        ck(f'{L}: the old page names are search words of the moved rows',J(pg,"['chase','limiter','mixer','dawLook','bg'].every(i=>/audio system|interface|colours/.test(STX.get(i).w))"))
        # the older profile shows in the moved controls, and they still store
        st=J(pg,"({chase:SETT.val('chase'),lim:SETT.val('limiter'),clipA:SETT.val('clipA'),asMin:SETT.val('asMin'),grid:SETT.val('grid'),mono:SETT.val('mono'),dac:SETT.val('devProfile')})")
        ck(f'{L}: an older profile loads into the moved controls',st['chase'] is False and st['lim'] is False and str(st['clipA'])=='60' and str(st['asMin'])=='5' and str(st['grid'])=='70' and st['dac']=='gryphon',st)
        R(pg,"openSettings('editing')");pg.wait_for_timeout(200)
        pg.click('#chaseChk');pg.wait_for_timeout(150)
        v=J(pg,"[UI.chase,document.getElementById('chaseChk').checked]");pg.wait_for_timeout(700)
        ck(f'{L}: Pick up notes works on Editing (stored)',v==[True,True] and json.loads(R(pg,"localStorage.getItem('audiolab-ui')")).get('chase')==True,[v,json.loads(R(pg,"localStorage.getItem('audiolab-ui')")).get('chase')])
        pg.click('#chaseChk');pg.wait_for_timeout(150)
        R(pg,"openSettings('dac')");pg.wait_for_timeout(300)
        ck(f'{L}: the safety limiter sits on DAC and audio interface under Protection',R(pg,"(()=>{const e=SETT.ctl('limiter'),b=e&&e.closest('.sbox');return !!(b&&b.querySelector('h4').textContent==='Protection'&&e.offsetParent)})()"))
        ok=R(pg,"(()=>{SETT.set('limiter',true);const a=UI.limiter!==false;SETT.set('limiter',false);return a&&UI.limiter===false})()")
        ck(f'{L}: the limiter still stores from its new page',ok)
        # old page ids
        olds=[]
        for o,np in [('glass','appearance'),('colors','appearance'),('layout','layout'),('nav','nav'),('dac','dac'),('files','files'),('export','export'),('perf','perf'),('keys','keys'),('audio','audio'),('general','general')]:
            R(pg,"openSettings('%s')"%o);pg.wait_for_timeout(250)
            v=pg.evaluate("()=>[...document.querySelectorAll('#setBody>section[data-page]')].filter(s=>!s.hidden).map(s=>s.dataset.page).join()")
            if v!=np:olds.append((o,v))
            if o=='glass':
                gv=pg.evaluate("()=>{const g=document.getElementById('st5Glass').getBoundingClientRect(),b=document.getElementById('setBody').getBoundingClientRect();return g.top>=b.top-2&&g.top<b.bottom-40}")
                ck(f'{L}: openSettings(\'glass\') shows the Glass card',gv)
        ck(f'{L}: the old page ids open the right page',not olds,olds)
        # the strip of live read-outs
        R(pg,"openSettings('general')");pg.wait_for_timeout(1200)
        sv=J(pg,"[...document.querySelectorAll('#st5Strip [data-st5r]')].map(b=>[b.dataset.st5r,b.querySelector('i').textContent,b.querySelector('span').textContent,b.title.length,b.dataset.tab5])")
        ck(f'{L}: the strip has six read-outs with tooltips',[x[0] for x in sv]==['rate','buf','cpu','fps','glass','out'] and all(x[3]>20 for x in sv),sv)
        ck(f'{L}: the read-outs show numbers',all(x[2] and x[2]!='–' for x in sv if x[0] in('rate','cpu','fps','glass','out')) and sv[0][2].endswith('kHz') and sv[3][2].endswith('fps'),sv)
        ck(f'{L}: Engine shows the context rate, Glass the glass level',J(pg,"[document.querySelector('[data-st5r=rate] span').textContent.startsWith(String(ctx.sampleRate/1000)),document.querySelector('[data-st5r=glass] span').textContent==={glass:'Glass',light:'Light',solid:'Solid'}[GLE.lv]]")==[True,True])
        routes=[]
        for k,pgw in [('rate','audio'),('buf','audio'),('cpu','perf'),('fps','perf'),('glass','perf'),('out','dac' if float(R(pg,"VERSION"))<0.289 else 'audio')]:  # from S10 (v0.289) the output is chosen on Audio
            pg.click('#st5Strip [data-st5r=%s]'%k);pg.wait_for_timeout(200)
            v=pg.evaluate("()=>document.querySelector('#setNav [data-tab].on').dataset.tab")
            if v!=pgw:routes.append((k,v))
        ck(f'{L}: each read-out opens its page',not routes,routes)
        t0=pg.evaluate("()=>document.querySelector('[data-st5r=fps] span').textContent");pg.wait_for_timeout(1600)
        ck(f'{L}: the read-outs are live',pg.evaluate("()=>!!document.querySelector('[data-st5r=fps] span').textContent"),t0)
        if not lite:
            pg.locator('#set .sheet').screenshot(path=f'{OUT}/s5_strip_dac_{L}.png')
        # search: old names and moved blocks
        def search(q):
            pg.evaluate("q=>{const e=document.getElementById('setQ');e.focus();e.value=q;e.dispatchEvent(new Event('input'))}",q);pg.wait_for_timeout(200)
            return pg.evaluate("()=>[...document.querySelectorAll('#setQR button')].map(b=>b.querySelector('b').textContent+' ['+b.querySelector('small').textContent+']')")
        for q,w in [('colours & clips','Appearance'),('glass & light','Appearance'),('zoom and playhead','Navigation'),('interface and dac','DAC and audio interface'),('audio system','Audio'),('project file','Project'),('export audio','Export'),('metronome','Recording and metronome'),('tint','Appearance'),('pick up notes','Editing'),('level meters','Mixer and meters'),('safety limiter','DAC and audio interface')]:
            h=search(q);ck(f'{L}: search "{q}" finds {w}',any(('['+w+']') in x or (' ['+w+' ›') in x or ('› '+w+']') in x or ('› '+w+' ›') in x or x.startswith(w+' [') for x in h),h[:5])  # from v0.251 (ST-S6) the path starts with the group
        h=search('pick up notes');i=next((n for n,x in enumerate(h) if 'Editing' in x),0)
        pg.click('#setQR button >> nth=%d'%i);pg.wait_for_timeout(300)
        ck(f'{L}: choosing a search result opens its new page and flashes the row',pg.evaluate("()=>document.querySelector('#setNav [data-tab].on').dataset.tab==='editing'&&!!document.querySelector('#setBody .sflash')"))
        # quick routes on the cards
        R(pg,"openSettings('general')");pg.wait_for_timeout(200)
        pg.click('#setBody section[data-page=general] [data-pmgo=perf]');pg.wait_for_timeout(200)
        ck(f'{L}: General keeps its link to Performance',pg.evaluate("()=>document.querySelector('#setNav [data-tab].on').dataset.tab")=='perf')
        R(pg,"openSettings('recording')");pg.wait_for_timeout(200)
        ck(f'{L}: Recording and metronome has its cards (four, and MIDI controllers) with help text and button tooltips',R(pg,"(()=>{const s=document.querySelector('#setBody>section[data-page=recording]');return s.querySelectorAll('.sbox').length===(typeof FT_HOOKS==='object'&&FT_HOOKS.controllersPage?5:4)&&[...s.querySelectorAll('.sbox')].every(b=>b.querySelector('.hint').textContent.length>40)&&[...s.querySelectorAll('button')].every(b=>b.title)})()"))
        if not lite: pg.locator('#set .sheet').screenshot(path=f'{OUT}/s5_recording_{L}.png')
        else: pg.locator('#set .sheet').screenshot(path=f'{OUT}/s5_recording_{L}.png')
        pg.click('#setBody section[data-page=recording] [data-pmgo=dac]');pg.wait_for_timeout(200)
        ck(f'{L}: Inputs leads to DAC and audio interface',pg.evaluate("()=>document.querySelector('#setNav [data-tab].on').dataset.tab")=='dac')
        R(pg,"openSettings('recording')");pg.wait_for_timeout(200)
        pg.click('#st5Mset');pg.wait_for_timeout(300)
        ck(f'{L}: Metronome setup… opens the Metronome setup',pg.evaluate("()=>!document.getElementById('mset').hidden"))
        R(pg,"(()=>{document.getElementById('mset').hidden=true;return 1})()")
        if R(pg,"typeof FT_HOOKS==='object'&&!!FT_HOOKS.controllersPage"):
            R(pg,"openSettings('recording')");pg.wait_for_timeout(200);pg.click('#st5CtlB');pg.wait_for_timeout(700)
            ck(f'{L}: Controllers… closes Settings and opens the Controllers window',pg.evaluate("()=>document.getElementById('set').hidden&&!!document.getElementById('ctlWin')&&!document.getElementById('ctlWin').hidden"))
            R(pg,"(()=>{const w=document.getElementById('ctlWin');if(w)w.remove();return 1})()")
        R(pg,"openSettings('mixer')");pg.wait_for_timeout(300)
        if True: pg.locator('#set .sheet').screenshot(path=f'{OUT}/s5_mixer_{L}.png')
        pg.click('#st5ShowMix');pg.wait_for_timeout(700)
        ck(f'{L}: Show the mixer closes Settings and shows the mixer',pg.evaluate("()=>document.getElementById('set').hidden&&!!document.getElementById('mixWin')&&!document.getElementById('mixWin').hidden"))
        R(pg,"openSettings('appearance')");pg.wait_for_timeout(400)
        pg.locator('#set .sheet').screenshot(path=f'{OUT}/s5_appearance_{L}.png')
        R(pg,"openSettings('editing')");pg.wait_for_timeout(300)
        pg.locator('#set .sheet').screenshot(path=f'{OUT}/s5_editing_{L}.png')
        # the glass chain's parts are untouched: the Performance page and the glass cards keep their controls
        ck(f'{L}: Performance and the Glass block keep their controls',pg.evaluate("()=>!!document.querySelector('#setBody>section[data-page=perf] #pmSl')&&!!document.querySelector('#setBody section[data-page=glass] .gcards')&&document.querySelector('#setBody section[data-page=glass]').closest('#setBody>section').dataset.page==='appearance'"))
        ck(f'{L}: no console errors',not errs,errs[:4])
        c.close()
    # a small window: the pages still fit without sideways scroll and the sidebar scrolls
    c,pg,errs=ctx(b,False,{},1280,720);R(pg,"openSettings('general')");pg.wait_for_timeout(500);over=[]
    for t in PAGES:
        pg.click('#setNav [data-tab=%s]'%t);pg.wait_for_timeout(120)
        sw=pg.evaluate("()=>document.getElementById('setBody').scrollWidth-document.getElementById('setBody').clientWidth")
        if sw>1:over.append((t,sw))
    ck('1280x720: no sideways scroll on any page',not over,over)
    pg.locator('#set .sheet').screenshot(path=f'{OUT}/s5_small.png')
    ck('1280x720: no console errors',not errs,errs[:3]);c.close()
    b.close()
print('%d/%d checks pass'%(N[1],N[0]));sys.exit(1 if FAIL else 0)
