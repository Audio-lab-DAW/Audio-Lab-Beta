"""Task ST-S10 (settings rebuild, step S10): the Audio page. One copy of output device, buffer, sample rate, processing block, headroom,
recording offset and keep awake, all on Audio (the Control Panel pop-up folded in); a Running now card; the copies on DAC and audio interface
replaced by read-outs that open Audio; "Keep?" (D1b) for a new sample rate, buffer or larger playback buffer and for a device used for the
first time, going back by itself, Keep, Go back, closing Settings keeps; a device used before switches with no question; search finds the moved
settings by their old names; an older profile loads; dark and Light level; no console errors.
  python3 tools/ui-tests/taskST_S10.py [repo dir] [out dir]"""
import sys,os,mimetypes,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else '.');OUT=sys.argv[2] if len(sys.argv)>2 else '.';os.makedirs(OUT,exist_ok=True)
N=[0,0];FAIL=[]
def ck(name,ok,info=''):
    N[0]+=1
    if ok:N[1]+=1
    else:FAIL.append(name);print('  FAIL',name,str(info)[:700])
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html';f=os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type='text/html' if f.endswith('.html') else (mimetypes.guess_type(f)[0] or 'application/octet-stream'))
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
J=lambda pg,c:json.loads(R(pg,"JSON.stringify("+c+")"))
VIS="""(sel=>{const e=document.querySelector(sel);if(!e)return false;const l=e.type==='checkbox'?e.closest('label')||e:e;return l.offsetParent!==null&&!!l.closest('#set')})"""
def vis(pg,sel):return pg.evaluate("s=>"+VIS+"(s)",sel)
def search(pg,q):
    r=pg.evaluate("q=>{const e=document.getElementById('setQ');e.focus();e.value=q;e.dispatchEvent(new Event('input'));return[...document.querySelectorAll('#setQR button')].map(b=>(b.querySelector('b')||b).textContent)}",q)
    pg.evaluate("()=>{const e=document.getElementById('setQ');e.value='';e.dispatchEvent(new Event('input'))}");return r
BAR=lambda pg:pg.evaluate("()=>{const k=document.getElementById('st10Keep');return k?{on:!k.hidden&&k.offsetParent!==null,t:k.textContent,mode:k.dataset.mode||''}:null}")
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        c=b.new_context(viewport={'width':1600,'height':1000});pg=c.new_page();errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and 'icons.json' not in m.text and errs.append('console '+m.text[:200]))
        pg.route('https://app.test/**',alsong(serve))
        u=dict(order=['arr','fx','tr','map'],splash=False,lat3=1,lite=lite,liteMan=lite,recOff=7,keepAwake=True,headroom=-3,hq=False,rq='auto')
        pg.add_init_script("if(!sessionStorage.getItem('t10')){sessionStorage.setItem('t10','1');localStorage.setItem('audiolab-ui',JSON.stringify(%s))}"%json.dumps(u))
        pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(2500)
        pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
        ck(f'{L}: version',float(R(pg,"VERSION"))>=0.289)
        R(pg,"openSettings('audio')");pg.wait_for_timeout(600)
        st=J(pg,"{o:UI.recOff,k:UI.keepAwake,h:UI.headroom,hq:!!UI.hq,ro:document.getElementById('recOff').value,ka:document.getElementById('kaChk').checked,hd:document.getElementById('hdSel').value}")
        ck(f'{L}: an older profile still loads (offset, keep awake, headroom shown on Audio)',st=={'o':7,'k':True,'h':-3,'hq':False,'ro':'7','ka':True,'hd':'-3'},st)
        R(pg,"ST5.show('audio')");pg.wait_for_timeout(300)
        need=['#outSel','#bufSel','#hqChk','#srSel','#rqSel','#hdSel','#recOff','#kaChk','#findDev']
        ck(f'{L}: Audio shows device, buffer, larger buffer, rate, blocks, headroom, offset, keep awake on the page',all(vis(pg,s) for s in need),[s for s in need if not vis(pg,s)])
        ck(f'{L}: the Control Panel pop-up and its button are gone from Settings',not vis(pg,'#cpBtn') and R(pg,"!document.querySelector('#set #cp')"))
        cards=J(pg,"[...document.querySelectorAll('#setBody>section[data-page=\"audio\"] .sbox>h4')].map(h=>h.childNodes[0].textContent.trim())")
        ck(f'{L}: the cards are Audio driver, Running now, Advanced, Test tone (after Devices from v0.315)',[x for x in cards if x!='Devices'][:4]==['Audio driver','Running now','Advanced','Test tone'],cards)
        pg.wait_for_timeout(700)
        rn=J(pg,"['st10Sr','st10Buf','st10Lat','st10Dev','st10Drop'].map(i=>document.getElementById(i).textContent)")
        ck(f'{L}: Running now shows rate, buffer, latency, device and dropouts',('kHz' in rn[0]) and ('samples' in rn[1] or 'not reported' in rn[1]) and rn[3] and rn[4]!='–',rn)
        ck(f'{L}: Running now names the helper for exclusive use and never assumes a Mac',R(pg,"/desktop helper/.test(document.querySelector('#st10Now .st10ex').textContent)&&/Mac and on Windows/.test(document.querySelector('#st10Now .st10ex').textContent)"))
        pg.locator('#set .setw').screenshot(path=f'{OUT}/s10_audio_{L}.png')
        # one copy each: no other visible control in Settings stores the same key
        dup=J(pg,"""(()=>{const out=[];for(const t of ST5P.map(p=>p[0])){ST5.show(t);for(const id of['lockSr','ifdBuf','ifdSr','ifdOff','ifdKa','ifdOut','cpBtn']){const e=document.getElementById(id);if(e&&e.offsetParent!==null)out.push(t+':'+id)}}ST5.show('audio');return out})()""")
        ck(f'{L}: no copy of rate, buffer, offset, keep awake or output is left on any page',dup==[],dup)
        ck(f'{L}: the settings table has no second-copy rows left',J(pg,"STT.filter(r=>r.same).map(r=>r.id)")==[])
        miss=J(pg,"STT.filter(r=>['audio','dac'].includes(r.pg)).filter(r=>{const e=SETT.ctl(r.id);return !e||!e.closest('#setBody>section[data-page=\"'+r.pg+'\"]')}).map(r=>r.id)")
        ck(f'{L}: every Audio and DAC row of the table points at a control on its own page',miss==[],miss)
        # DAC and audio interface read-outs and links
        R(pg,"ST5.show('dac')");pg.wait_for_timeout(300)
        ro=J(pg,"['st10DSr','st10DBuf','st10DOff','st10DOut'].map(i=>{const e=document.getElementById(i);return e?e.textContent:null})")
        ck(f'{L}: DAC page read-outs show rate, buffer, offset and output',ro[0] and 'kHz now' in ro[0] and ro[1] and ro[2]=='7 ms' and ro[3],ro)
        pg.evaluate("()=>document.getElementById('st10DSr').scrollIntoView()");pg.wait_for_timeout(100)
        pg.locator('#set .setw').screenshot(path=f'{OUT}/s10_dac_{L}.png')
        pg.click('[data-st10go="#srSel"]');pg.wait_for_timeout(400)
        ck(f'{L}: "Change on Audio" opens Audio at the sample rate',R(pg,"ST5.cur")=='audio' and vis(pg,'#srSel'))
        # strip
        R(pg,"ST5.show('general')");pg.wait_for_timeout(200);pg.click('#st5Strip [data-st5r="out"]');pg.wait_for_timeout(300)
        ck(f'{L}: the strip\'s output opens Audio',R(pg,"ST5.cur")=='audio')
        # Keep? for the sample rate: Go back
        R(pg,"ST10.SEC=15");pg.select_option('#srSel','48000');pg.wait_for_timeout(1200)
        k=BAR(pg);ck(f'{L}: a new sample rate asks Keep? with a countdown',k and k['on'] and 'Sample rate 48 kHz' in k['t'] and 'Going back in' in k['t'],k)
        ck(f'{L}: the new rate applies at once',J(pg,"[UI.sr,ctx.sampleRate]")==[48000,48000],J(pg,"[UI.sr,ctx.sampleRate]"))
        pg.locator('#set .setw').screenshot(path=f'{OUT}/s10_keep_{L}.png')
        pg.click('#st10Keep [data-st10k="back"]');pg.wait_for_timeout(1500)
        ck(f'{L}: Go back restores the rate before',J(pg,"[UI.sr,document.getElementById('srSel').value]")==[0,'0'],J(pg,"[UI.sr,document.getElementById('srSel').value]"))
        k=BAR(pg);ck(f'{L}: the bar says it went back',k and k['mode']=='done' and 'Went back' in k['t'],k)
        # buffer: no answer goes back by itself
        pg.wait_for_timeout(4200);R(pg,"ST10.SEC=2");pg.select_option('#bufSel','512');pg.wait_for_timeout(600)
        ck(f'{L}: a new buffer applies at once and asks',R(pg,"UI.buf")==512 and BAR(pg)['on'])
        pg.wait_for_timeout(3200)
        ck(f'{L}: with no answer the buffer goes back by itself',J(pg,"[UI.buf,document.getElementById('bufSel').value]")==[-1,'-1'],J(pg,"[UI.buf,document.getElementById('bufSel').value]"))
        ck(f'{L}: the bar says nobody answered',BAR(pg)['mode']=='done' and 'No answer' in BAR(pg)['t'],BAR(pg))
        # two changes at once, Keep keeps both
        pg.wait_for_timeout(4200);R(pg,"ST10.SEC=15");pg.select_option('#bufSel','1024');pg.wait_for_timeout(500);pg.click('#hqChk');pg.wait_for_timeout(800)
        k=BAR(pg);ck(f'{L}: two changes are listed in one question',k['on'] and 'buffer 1024' in k['t'].lower() and 'larger playback buffer on' in k['t'],k)
        pg.click('#st10Keep [data-st10k="keep"]');pg.wait_for_timeout(300)
        ck(f'{L}: Keep keeps both and closes the bar',J(pg,"[UI.buf,!!UI.hq]")==[1024,True] and not BAR(pg)['on'],[J(pg,"[UI.buf,!!UI.hq]"),BAR(pg)])
        # changing back by hand needs no question
        pg.select_option('#bufSel','-1');pg.wait_for_timeout(500);pg.click('#st10Keep [data-st10k="keep"]') if BAR(pg)['on'] else None;pg.click('#hqChk');pg.wait_for_timeout(500)
        if BAR(pg)['on']:pg.click('#st10Keep [data-st10k="keep"]')
        ck(f'{L}: buffer and larger buffer back as they were',J(pg,"[UI.buf,!!UI.hq]")==[-1,False],J(pg,"[UI.buf,!!UI.hq]"))
        # devices: first time asks, used before switches at once
        R(pg,"UI.st10Seen=[];UI.sink='';0")
        R(pg,"UI.sink='devNew';ST_HOOKS.outChanged('','devNew');0");pg.wait_for_timeout(200)
        k=BAR(pg);ck(f'{L}: a device used for the first time asks Keep?',k['on'] and 'Output' in k['t'],k)
        pg.click('#st10Keep [data-st10k="keep"]');pg.wait_for_timeout(200)
        ck(f'{L}: Keep remembers the device',J(pg,"UI.st10Seen.includes('devNew')"))
        R(pg,"UI.sink='';ST_HOOKS.outChanged('devNew','');0");pg.wait_for_timeout(200)
        ck(f'{L}: going to the system default asks nothing',not BAR(pg)['on'])
        R(pg,"UI.sink='devNew';ST_HOOKS.outChanged('','devNew');0");pg.wait_for_timeout(200)
        ck(f'{L}: a device used before switches at once with no question',not BAR(pg)['on'])
        R(pg,"UI.sink='devOther';ST_HOOKS.outChanged('','devOther');0");pg.wait_for_timeout(200)
        ck(f'{L}: another new device asks',BAR(pg)['on'])
        pg.click('#st10Keep [data-st10k="back"]');pg.wait_for_timeout(800)
        ck(f'{L}: Go back returns to the device before',R(pg,"UI.sink")=='' and not J(pg,"(UI.st10Seen||[]).includes('devOther')"),J(pg,"[UI.sink,UI.st10Seen]"))
        R(pg,"UI.sink='';UI.st10Seen=[];saveUI();0")
        # closing Settings keeps
        pg.wait_for_timeout(4200);R(pg,"ST10.SEC=15");pg.select_option('#srSel','48000');pg.wait_for_timeout(1200)
        R(pg,"closeSet();0");pg.wait_for_timeout(300)
        ck(f'{L}: closing Settings keeps the change and stops the countdown',R(pg,"UI.sr")==48000 and R(pg,"ST10.pend")is None and R(pg,"ST10.tmr")==0)
        R(pg,"openSettings('audio')");pg.wait_for_timeout(500);ck(f'{L}: no question waits when Settings opens again',not BAR(pg)['on'])
        R(pg,"ST10.quiet=true");pg.select_option('#srSel','0');R(pg,"ST10.quiet=false");pg.wait_for_timeout(1200)
        # help line, search
        pg.hover('#srSel');h=pg.evaluate("()=>document.getElementById('st9Help').textContent")
        ck(f'{L}: the help line says the rate asks Keep?',"Keep?" in h,h)
        for q,want in (('lock to dac rate','Sample rate'),('steadier playback','Larger playback buffer'),('control panel','Buffer size'),('play through','Output device'),('speed and delay recording latency','Recording latency offset')):
            r=search(pg,q);ck(f'{L}: search "{q}" finds {want}',any(want in x for x in r),r)
        ck(f'{L}: search shows no DAC-page copies any more',not any('(DAC page' in x for x in search(pg,'buffer')+search(pg,'sample rate')))
        R(pg,"closeSet();0");pg.wait_for_timeout(200)
        ck(f'{L}: no console errors',not errs,errs)
        c.close()
    b.close()
print(f'{N[1]}/{N[0]} passed');sys.exit(1 if FAIL else 0)
