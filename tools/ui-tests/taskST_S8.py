"""Task ST-S8 (settings rebuild, step S8): scope. An older profile's global loudness target and tempo lane become the defaults for new
projects and the open songs keep them; the loudness target and tempo lane are kept per song (switching songs switches them, a reload keeps
them); the Project page has "This song" (loudness target, key, tempo lane) and "New projects start with" (tempo, loudness target, tempo lane),
linked both ways with the master strip, the Loudness window and the piano roll; new projects start with the defaults; rows carry the
project / computer / new marks without changing their text; search finds the new rows; dark and Light level; no console errors.
  python3 tools/ui-tests/taskST_S8.py [repo dir] [out dir]"""

import sys,os,mimetypes,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
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
OLDP={'lufsP':'club','tempoLane':True,'chase':False}
def ctx(b,lite):
    c=b.new_context(viewport={'width':1600,'height':1000},accept_downloads=True);pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and 'icons.json' not in m.text and errs.append('console '+m.text[:200]))
    pg.route('https://app.test/**',alsong(serve))
    u=dict(OLDP,order=['arr','fx','tr','map'],splash=False,lat3=1,lite=lite,liteMan=lite)
    pg.add_init_script("if(!sessionStorage.getItem('t8')){sessionStorage.setItem('t8','1');localStorage.setItem('audiolab-ui',JSON.stringify(%s))}"%json.dumps(u))
    pg.goto('https://app.test/index.html');ready(pg)
    return c,pg,errs
def ready(pg):
    pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(2500)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
def openS(pg,t):
    R(pg,"openSettings('%s')"%t);pg.wait_for_timeout(400)
MK="""id=>{const r=SETT.get(id),h=ST7.host(r),b=document.querySelector('.st7rs[data-st7="'+id+'"]');return{chg:!!h&&h.classList.contains('st7chg'),rs:!!b&&!b.hidden&&b.offsetWidth>0,tip:b?b.title:''}}"""
mk=lambda pg,i:J(pg,"("+MK+")("+json.dumps(i)+")")
cnt=lambda pg,t:pg.evaluate("t=>{const i=document.querySelector('#setNav [data-tab=\"'+t+'\"] .st7n');return i&&!i.hidden?+i.dataset.n:0}",t)

TAG="id=>{const e=SETT.row(id),t=e&&e.querySelector('.st8t');return t?t.dataset.t:''}"
tag=lambda pg,i:J(pg,"("+TAG+")("+json.dumps(i)+")")
def setv(pg,id,v):
    pg.evaluate("([id,v])=>{const e=document.getElementById(id);if(e.type==='checkbox')e.checked=v;else e.value=String(v);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}",[id,v]);pg.wait_for_timeout(200)
def newproj(pg):
    R(pg,"(npOpen(),1)");pg.wait_for_timeout(300);b=R(pg,"document.getElementById('npBpm').value");pg.click('#npGo');pg.wait_for_timeout(1500);return b
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        c,pg,errs=ctx(b,lite)
        ck(f'{L}: version',float(R(pg,"VERSION"))>=0.267)
        st=J(pg,"{n:UI.stNew,l:UI.lufsP,s:S.lufsP,tl:UI.tempoLane,st:S.tempoLane,h:TMPH(),t:lmTarget()[0],chase:UI.chase}")
        ck(f'{L}: the old global target and lane become the defaults and the open song keeps them',st['n'].get('lufs')=='club' and st['n'].get('tempoLane')==True and st['l']=='club' and st['s']=='club' and st['tl']==True and st['st']==True and st['h']==44 and st['t']=='club' and st['chase']==False,st)
        ck(f'{L}: every open project is stamped',J(pg,"PJ.list.every(p=>p.S.lufsP==='club'&&p.S.tempoLane===true)"))
        openS(pg,'files')
        ck(f'{L}: the Project page has This song and New projects start with',J(pg,"[...document.querySelectorAll('#setBody section[data-page=files] .sbox>h4')].map(h=>h.textContent).slice(0,2)")==['This song','New projects start with'])
        v=J(pg,"{l:$('#st8Lufs').value,r:$('#st8Root').value,sc:$('#st8Scale').value,ln:$('#st8Lane').checked,nb:$('#st8NBpm').value,nl:$('#st8NLufs').value,nn:$('#st8NLane').checked,pr:[PR.root,PR.scale]}")
        ck(f'{L}: the cards show the song and the defaults',v['l']=='club' and v['ln'] and v['nb']=='' and v['nl']=='club' and v['nn'] and v['r']==str(v['pr'][0]) and v['sc']==v['pr'][1],v)
        if not lite or True: pg.locator('#set .sheet').screenshot(path=f'{OUT}/s8_project_{L}.png')
        # this song: loudness target, linked with the Loudness window and the master strip
        setv(pg,'st8Lufs','pod')
        st=J(pg,"{s:S.lufsP,n:UI.stNew.lufs,lm:(document.getElementById('lmSel')||{}).value,t:lmTarget()[0],d:curP().dirty}")
        ck(f'{L}: the song\'s loudness target is kept in the song, the default stays',st['s']=='pod' and st['n']=='club' and st['t']=='pod' and st.get('lm') in (None,'pod') and st['d']==True,st)
        R(pg,"(UI.lufsP='ebu',1)");pg.wait_for_timeout(1200)
        ck(f'{L}: a target set on the master strip shows on the Project page',R(pg,"$('#st8Lufs').value")=='ebu' and R(pg,"S.lufsP")=='ebu')
        setv(pg,'st8Lufs','pod')
        # key, linked with the piano roll
        setv(pg,'st8Root','2');setv(pg,'st8Scale','major')
        ck(f'{L}: the key is the piano roll\'s key, kept in the song',J(pg,"[PR.root,PR.scale,S.prKey.root,S.prKey.scale,$('#prRoot').value,$('#prScale').value]")==[2,'major',2,'major','2','major'])
        # tempo lane per song
        setv(pg,'st8Lane',False)
        ck(f'{L}: the tempo lane is hidden for this song only',J(pg,"[UI.tempoLane,S.tempoLane,TMPH(),UI.stNew.tempoLane]")==[False,False,0,True])
        # defaults for new projects
        setv(pg,'st8NBpm',98);setv(pg,'st8NLufs','apple');setv(pg,'st8NLane',False)
        ck(f'{L}: the defaults are stored on this computer',J(pg,"UI.stNew")=={'lufs':'apple','tempoLane':False,'bpm':98})
        first=R(pg,"PJ.cur")
        bpm=newproj(pg)
        st=J(pg,"{id:PJ.cur,bpm:S.bpm,l:S.lufsP,tl:S.tempoLane,t:lmTarget()[0]}")
        ck(f'{L}: a new project starts with the defaults (tempo 98, Apple Music, no lane)',bpm=='98' and st['id']!=first and st['bpm']==98 and st['l']=='apple' and st['tl']==False and st['t']=='apple',[bpm,st])
        R(pg,"switchProject(%s)"%json.dumps(first));pg.wait_for_timeout(600)
        ck(f'{L}: switching back brings the first song\'s target, key and lane',J(pg,"[UI.lufsP,lmTarget()[0],PR.root,UI.tempoLane]")==['pod','pod',2,False])
        setv(pg,'st8NBpm','');R(pg,"(npOpen(),1)");pg.wait_for_timeout(300)
        ck(f'{L}: with no default tempo, New project takes the open song\'s tempo as before',R(pg,"document.getElementById('npBpm').value")==str(R(pg,"S.bpm")));R(pg,"(document.getElementById('np').hidden=true,1)")
        # marks
        openS(pg,'files')
        ck(f'{L}: project, new and computer marks',[tag(pg,'songLufs'),tag(pg,'songLane'),tag(pg,'newLufs'),tag(pg,'asMin')]==['project','project','new',''],[tag(pg,i) for i in ('songLufs','songLane','newLufs','asMin')])
        openS(pg,'audio');ck(f'{L}: the audio driver card is marked computer on its title',R(pg,"(SETT.row('outDev').closest('.sbox').querySelector('h4 .st8t')||{dataset:{}}).dataset.t")=='computer')
        if not lite: pg.locator('#set .sheet').screenshot(path=f'{OUT}/s8_audio_{L}.png')
        openS(pg,'export');ck(f'{L}: the export file name is marked project',tag(pg,'exName')=='project')
        openS(pg,'general');ck(f'{L}: own-taste rows have no mark',tag(pg,'tips')=='' and tag(pg,'askClose')=='')
        ck(f'{L}: the marks do not change the row text',R(pg,"SETT.row('songLane').textContent.trim()")=='Show the tempo and time signature lane')
        openS(pg,'files');ck(f'{L}: the changed mark sees the new-project defaults',J(pg,"(()=>{const h=ST7.host(SETT.get('newLufs'));return h.classList.contains('st7chg')})()"))
        # search
        h=pg.evaluate("q=>{const e=document.getElementById('setQ');e.focus();e.value=q;e.dispatchEvent(new Event('input'));return [...document.querySelectorAll('#setQR button')].map(b=>b.querySelector('b').textContent+' | '+b.querySelector('small').textContent)}",'loudness target')
        ck(f'{L}: search "loudness target" finds the song\'s and the new-project rows on Project',any('this song' in x.lower() and 'Project' in x for x in h) and any('new projects' in x.lower() for x in h),h)
        h=pg.evaluate("q=>{const e=document.getElementById('setQ');e.value=q;e.dispatchEvent(new Event('input'));return [...document.querySelectorAll('#setQR button b')].map(b=>b.textContent)}",'tempo lane')
        ck(f'{L}: search "tempo lane" finds the lane rows',any('tempo' in x.lower() and 'lane' in x.lower() for x in h),h)
        pg.evaluate("()=>{const e=document.getElementById('setQ');e.value='';e.dispatchEvent(new Event('input'));e.blur()}")
        # what is stored: each song keeps its own (the projects store), the defaults on this computer; a reload keeps the defaults
        R(pg,"(saveProjects(),saveUINow(),1)");pg.wait_for_timeout(300)
        st=J(pg,"JSON.parse(localStorage.getItem('audiolab-projects')).list.map(p=>[p.S.lufsP,p.S.tempoLane])")
        ck(f'{L}: the projects store keeps each song\'s target and lane',['pod',False] in st and ['apple',False] in st,st)
        pg.reload();ready(pg)
        st=J(pg,"{n:UI.stNew,s:S.lufsP,l:UI.lufsP}")
        ck(f'{L}: a reload keeps the defaults, and a song opened fresh starts with them',st['n']=={'lufs':'apple','tempoLane':False} and st['s']==st['l'],st)
        ck(f'{L}: no console errors',not errs,errs[:5])
        c.close()
    b.close()
print(f'taskST_S8: {N[1]}/{N[0]} checks pass'+('' if not FAIL else ' FAILED: '+', '.join(FAIL)))
sys.exit(1 if FAIL else 0)
