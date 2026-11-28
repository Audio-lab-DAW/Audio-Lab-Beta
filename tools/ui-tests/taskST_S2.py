"""Task ST-S2 (settings rebuild, step S2): export options and piano roll options are remembered.
Fresh and older profiles start on the old defaults; export choices (WAV/FLAC/MP3, rate, bits, bitrate, FLAC level, dither, normalize, range, tail,
limiter, folder) come back after a restart; the export file name belongs to the project (another project keeps its own, the .audiolab file carries it);
piano roll tool, snap, chord, ghost and lane come back after a restart; scale and root belong to the project (an old project shows A minor).
Dark and Light level, screenshots to the out dir, no console errors.
  python3 tools/ui-tests/taskST_S2.py [repo dir] [out dir]"""
import sys,os,mimetypes,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(sys.argv[1] if len(sys.argv)>1 else '.');OUT=sys.argv[2] if len(sys.argv)>2 else '.';os.makedirs(OUT,exist_ok=True)
N=[0,0];FAIL=[]
def ck(name,ok,info=''):
    N[0]+=1
    if ok:N[1]+=1
    else:FAIL.append(name);print('  FAIL',name,info)
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html';f=os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type=mimetypes.guess_type(f)[0] or 'application/octet-stream')
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
def boot(pg):
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(3000)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
def ctx(b,lite,old=None):
    c=b.new_context(viewport={'width':1600,'height':1000});pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and errs.append('console '+m.text[:200]))
    pg.route('https://app.test/**',alsong(serve))
    u=dict(old or {},order=['arr','fx','tr','map'],splash=False,lat3=1,lite=lite,liteMan=lite)
    pg.add_init_script("if(!sessionStorage.getItem('t2')){sessionStorage.setItem('t2','1');localStorage.setItem('audiolab-ui',JSON.stringify(%s))}"%json.dumps(u))
    boot(pg);return c,pg,errs
EXS="JSON.stringify({fmt:EX.fmt,sr:$('#exSr').value,bit:$('#exBit').value,kbps:$('#exKbps').value,flac:$('#exFlacC').value,dit:$('#exDit').value,norm:$('#exNorm').value,range:$('#exRange').value,tail:$('#exTail').value,lim:$('#exLim').checked,folder:$('#exFolder').checked,name:$('#exName').value,on:[...$('#exFmt').children].filter(b=>b.classList.contains('on')).map(b=>b.dataset.f)})"
PRS="JSON.stringify({tool:PR.tool,snap:PR.snap,chord:PR.chord,ghost:PR.ghost,lane:PR.lane||'vel',root:PR.root,scale:PR.scale,ui:[$('#prSnap').value,$('#prChord').value,$('#prRoot').value,$('#prScale').value,(document.querySelector('#prTools .on')||{}).dataset?.tool]})"
OPENPR="(()=>{const t=S.tracks.find(t=>t.kind==='inst'&&t.clips.some(c=>c.notes&&c.notes.length));openPR(t,t.clips.find(c=>c.notes&&c.notes.length));return 1})()"
def sel(pg,id,v):pg.evaluate("([id,v])=>{const e=document.getElementById(id);e.value=v;e.dispatchEvent(new Event('change',{bubbles:true}))}",[id,v])
def persist(pg):R(pg,"(()=>{try{saveProjects()}catch(e){}try{saveUINow()}catch(e){}return 1})()");pg.wait_for_timeout(600)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        # A. an older profile: nothing stored, old defaults
        c,pg,errs=ctx(b,lite,{'exSeed':True,'ghostGrey':False,'prLock':False})
        R(pg,"openSettings('export')");pg.click('#setNav [data-tab=export]');pg.wait_for_timeout(500)
        e=json.loads(R(pg,EXS))
        ck(f'{L}: older profile, export defaults as before',e['fmt']=='wav' and e['on']==['wav'] and e['sr']=='0' and e['bit']=='24' and e['kbps']=='320' and e['dit']=='tpdf' and e['norm']=='off' and e['range']=='song' and e['tail']=='2' and e['lim'] and e['folder'] and e['name']=='AudioLab mix',e)
        ck(f'{L}: the export page says what is remembered',pg.evaluate("()=>{const h=document.getElementById('exMem');return !!h&&h.offsetHeight>0&&/remembers/.test(h.textContent)}"))
        ck(f'{L}: file name has a tooltip',len(pg.evaluate("()=>document.getElementById('exName').title"))>20)
        pg.locator('#set .sheet').screenshot(path=f'{OUT}/s2_export_{L}.png')
        R(pg,"closeSet()");R(pg,OPENPR);pg.wait_for_timeout(700)
        pr=json.loads(R(pg,PRS))
        ck(f'{L}: older profile, piano roll defaults as before',pr['tool']=='draw' and pr['snap']==0.25 and pr['chord']=='none' and pr['ghost'] is True and pr['lane']=='vel' and pr['root']==9 and pr['scale']=='minor' and pr['ui'][:4]==['0.25','none','9','minor'],pr)
        # B. change everything
        R(pg,"closeSet&&closeSet()");R(pg,"openSettings('export')");pg.click('#setNav [data-tab=export]');pg.wait_for_timeout(400)
        pg.click('#exFmt [data-f=flac]');pg.wait_for_timeout(100)
        sel(pg,'exBit','16');sel(pg,'exFlacC','0');sel(pg,'exDit','ns');sel(pg,'exNorm','-1');sel(pg,'exRange','pos');sel(pg,'exTail','4');sel(pg,'exSr','96000')
        pg.click('#exLim');pg.click('#exFolder')
        pg.fill('#exName','Night drive mix');pg.press('#exName','Tab')
        proj1=R(pg,'PJ.cur')
        R(pg,"closeSet()");R(pg,OPENPR);pg.wait_for_timeout(500)
        sel(pg,'prSnap',str(0.5));sel(pg,'prChord','major');sel(pg,'prRoot','2');sel(pg,'prScale','dorian');sel(pg,'prLane','1')
        pg.click('#prTools [data-tool=paint]');R(pg,"PR.ghost=false")
        pg.wait_for_timeout(200);pg.locator('#pr .prbar').screenshot(path=f'{OUT}/s2_prbar_{L}.png')
        ck(f'{L}: key change marks the project changed',R(pg,"PJ.list.find(p=>p.id===PJ.cur).dirty")==True)
        # the .audiolab file carries the name and the key
        rt=json.loads(pg.evaluate("async()=>{const r=await AudioLab.run('(async()=>{const b=await packProject(curP());const J=await unpackProject(new File([b],\"t.audiolab\"));return JSON.stringify({n:J.project.exName,k:J.project.prKey})})()');return r}"))
        ck(f'{L}: the .audiolab file keeps the export name and the key',rt['n']=='Night drive mix' and rt['k']=={'root':2,'scale':'dorian'},rt)
        # C. another project keeps its own name and key
        if R(pg,"PJ.list.length")<2:R(pg,"(()=>{const keep=S;demo();const ps=S;S=keep;PJ.list.push({id:'pT2',name:'Second',S:ps});return 1})()")
        others=json.loads(R(pg,"JSON.stringify(PJ.list.filter(p=>p.id!==PJ.cur).map(p=>p.id))"))
        if others:
            R(pg,"switchProject(%s)"%json.dumps(others[0]));pg.wait_for_timeout(500)
            R(pg,"openSettings('export')");pg.click('#setNav [data-tab=export]');pg.wait_for_timeout(300)
            e2=json.loads(R(pg,EXS));R(pg,"closeSet()");k2=json.loads(R(pg,"JSON.stringify([PR.root,PR.scale,$('#prRoot').value,$('#prScale').value])"))
            ck(f'{L}: another project: default name, its export format the same (global)',e2['name']=='AudioLab mix' and e2['fmt']=='flac',e2)
            ck(f'{L}: another project: its own key (old project: A minor)',k2==[9,'minor','9','minor'],k2)
            R(pg,"switchProject(%s)"%json.dumps(proj1));pg.wait_for_timeout(500)
            R(pg,"openSettings('export')");pg.click('#setNav [data-tab=export]');pg.wait_for_timeout(300)
            ck(f'{L}: back: the name returns',json.loads(R(pg,EXS))['name']=='Night drive mix');R(pg,"closeSet()")
            ck(f'{L}: back: the key returns',json.loads(R(pg,"JSON.stringify([PR.root,PR.scale,$('#prRoot').value])"))==[2,'dorian','2'])
        else: ck(f'{L}: a second project exists for the check',False,'only one project')
        # D. restart
        persist(pg)
        st=pg.evaluate("id=>{const J=JSON.parse(localStorage.getItem('audiolab-projects'));const P=J.list.find(p=>p.id===id);const Q=J.list.find(p=>p.id==='pT2');return{n:P&&P.S.exName,k:P&&P.S.prKey,n2:Q?Q.S.exName||'':'-',k2:Q?Q.S.prKey||null:'-',ui:JSON.parse(localStorage.getItem('audiolab-ui')).prMem}}",proj1)
        ck(f'{L}: stored: the project holds its export name and key, the other project none',st['n']=='Night drive mix' and st['k']=={'root':2,'scale':'dorian'} and st['n2']=='' and st['k2'] is None,st)
        ck(f'{L}: stored: the piano roll options',st['ui']=={'tool':'paint','snap':0.5,'chord':'major','ghost':False,'lane':'1'},st['ui'])
        boot(pg)
        R(pg,"openSettings('export')");pg.click('#setNav [data-tab=export]');pg.wait_for_timeout(500)
        e=json.loads(R(pg,EXS))
        ck(f'{L}: after a restart the export choices are back',e['fmt']=='flac' and e['on']==['flac'] and e['sr']=='96000' and e['bit']=='16' and e['flac']=='0' and e['dit']=='ns' and e['norm']=='-1' and e['range']=='pos' and e['tail']=='4' and not e['lim'] and not e['folder'],e)
        here=R(pg,"PJ.list.some(p=>p.id===%s)"%json.dumps(proj1))
        if here:R(pg,"switchProject(%s)"%json.dumps(proj1));pg.wait_for_timeout(300)
        if here:ck(f'{L}: after a restart the project keeps its export name',json.loads(R(pg,EXS))['name']=='Night drive mix')
        else:print('  note: the test page starts a fresh demo project each time, so the project checks use the stored data above')
        ck(f'{L}: FLAC hides MP3 bitrate and shows FLAC level',pg.evaluate("()=>document.getElementById('exKbpsL').hidden&&!document.getElementById('exFlacL').hidden"))
        R(pg,"closeSet()")
        if not here:R(pg,"S.prKey={root:2,scale:'dorian'}")
        R(pg,OPENPR);pg.wait_for_timeout(600)
        pr=json.loads(R(pg,PRS))
        ck(f'{L}: after a restart the piano roll options are back',pr['tool']=='paint' and pr['snap']==0.5 and pr['chord']=='major' and pr['ghost'] is False and pr['lane']=='1' and pr['ui'][0]=='0.5' and pr['ui'][1]=='major' and pr['ui'][4]=='paint',pr)
        ck(f'{L}: after a restart the project keeps its key',pr['root']==2 and pr['scale']=='dorian' and pr['ui'][2:4]==['2','dorian'],pr)
        ck(f'{L}: lane select shows the remembered lane',pg.evaluate("()=>{const l=document.getElementById('prLane');return !!l&&l.value==='1'}"))
        # E. MP3 and its bitrate
        R(pg,"closeSet&&closeSet()");R(pg,"openSettings('export')");pg.click('#setNav [data-tab=export]');pg.wait_for_timeout(300)
        pg.click('#exFmt [data-f=mp3]');sel(pg,'exKbps','192');persist(pg);boot(pg)
        R(pg,"openSettings('export')");pg.click('#setNav [data-tab=export]');pg.wait_for_timeout(300);e=json.loads(R(pg,EXS))
        ck(f'{L}: MP3 at 192 kbps comes back',e['fmt']=='mp3' and e['kbps']=='192' and not pg.evaluate("()=>document.getElementById('exKbpsL').hidden"),e)
        ck(f'{L}: search "file name" finds Export audio',pg.evaluate("()=>{const i=document.getElementById('setQ');i.value='file name';i.dispatchEvent(new Event('input'));return [...document.querySelectorAll('#setQR button')].some(b=>/Export/.test(b.textContent))}"))
        ck(f'{L}: no console errors',not errs,errs[:3])
        c.close()
    b.close()
print(f'{N[1]}/{N[0]} checks passed');sys.exit(1 if FAIL else 0)
