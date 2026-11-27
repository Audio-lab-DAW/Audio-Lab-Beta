"""Task ST-S7 (settings rebuild, step S7): the changed mark, reset per setting and per page, Reset all that lists what it resets and saves
a backup first. An older profile loads and its changed settings carry the blue bar and a ↺; the sidebar counts them per page; ↺ puts one
setting back (stored), "Reset this page" puts a page back and Undo restores it; the glass chain's rows are never marked; Reset all lists the
changed settings and the options outside Settings, saves a backup, resets and reloads (shortcuts kept); the backup restores; search finds
the new card; dark and Light level; no console errors.
  python3 tools/ui-tests/taskST_S7.py [repo dir] [out dir]"""
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
OLDP={'chase':False,'limiter':False,'clipA':60,'asMin':5,'autosave':True,'followMode':'lead','gridB':70,'clickLvl':70}
def ctx(b,lite):
    c=b.new_context(viewport={'width':1600,'height':1000},accept_downloads=True);pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and 'icons.json' not in m.text and errs.append('console '+m.text[:200]))
    pg.route('https://app.test/**',serve)
    u=dict(OLDP,order=['arr','fx','tr','map'],splash=False,lat3=1,lite=lite,liteMan=lite)
    pg.add_init_script("if(!sessionStorage.getItem('t7')){sessionStorage.setItem('t7','1');localStorage.setItem('audiolab-ui',JSON.stringify(%s))}"%json.dumps(u))
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
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        c,pg,errs=ctx(b,lite)
        ck(f'{L}: version',float(R(pg,"VERSION"))>=0.262)
        # the older profile still loads
        openS(pg,'editing')
        st=J(pg,"{chase:SETT.val('chase'),clipA:SETT.val('clipA'),grid:SETT.val('grid'),asMin:SETT.val('asMin'),follow:SETT.val('follow'),lim:SETT.val('limiter')}")
        ck(f'{L}: an older profile loads into the controls',st=={'chase':False,'clipA':'60','grid':'70','asMin':'5','follow':'lead','lim':False},st)
        # marks
        for i in ['chase','clipA','grid','asMin','follow','limiter']:
            openS(pg,J(pg,"SETT.get(%s).pg"%json.dumps(i)));pg.wait_for_timeout(150)
            m=mk(pg,i);ck(f'{L}: {i} is marked changed with a ↺ that names the default',m['chg'] and m['rs'] and 'Back to the default' in m['tip'],m)
        openS(pg,'general');m=mk(pg,'tips');ck(f'{L}: an unchanged row has no mark',not m['chg'] and not m['rs'],m)
        ck(f'{L}: the sidebar counts per page',cnt(pg,'editing')==1 and cnt(pg,'appearance')>=2 and cnt(pg,'files')==1 and cnt(pg,'general')==1 and cnt(pg,'nav')==1,
           [cnt(pg,t) for t in ('editing','appearance','files','general')])
        # glass rows are never marked, Performance has no page reset
        openS(pg,'appearance')
        R(pg,"(()=>{const e=SETT.ctl('glassTrans');e.value=String(+e.value+10);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return 1})()");pg.wait_for_timeout(300)
        m=mk(pg,'glassTrans');ck(f'{L}: the glass chain\'s rows are never marked',not m['chg'] and not m['rs'],m)
        R(pg,"(()=>{const e=SETT.ctl('glassTrans');e.value='50';e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return 1})()")
        openS(pg,'perf');ck(f'{L}: Performance shows no Reset this page',R(pg,"document.getElementById('st7Pg').hidden")==True)
        # a change made in the window is marked at once
        openS(pg,'general');pg.click('label:has(#setTips)');pg.wait_for_timeout(300)
        m=mk(pg,'tips');ck(f'{L}: a change in the window is marked at once',m['chg'] and m['rs'] and cnt(pg,'general')==2,m)
        pg.click('.st7rs[data-st7="tips"]');pg.wait_for_timeout(300)
        ck(f'{L}: ↺ on Show tooltips puts it back and stores it',R(pg,"SETT.val('tips')")==True and R(pg,"UI.tips!==false")==True and not mk(pg,'tips')['chg'],R(pg,"UI.tips"))
        # ↺ per setting on a range
        openS(pg,'appearance')
        if not lite: pg.locator('#set .sheet').screenshot(path=f'{OUT}/s7_marks_appearance_{L}.png')
        pg.locator('.st7rs[data-st7="clipA"]').click();pg.wait_for_timeout(300)
        t=R(pg,"document.getElementById('toast').textContent")
        ck(f'{L}: ↺ on Clip transparency sets 36, stores it, drops the mark and says so',R(pg,"SETT.val('clipA')")=='36' and R(pg,"UI.clipA")==36 and not mk(pg,'clipA')['chg'] and 'Clip transparency' in t,[R(pg,"UI.clipA"),t])
        # reset this page, then undo
        openS(pg,'nav');pg.wait_for_timeout(200)
        pb=J(pg,"{t:document.getElementById('st7Pg').textContent,d:document.getElementById('st7Pg').disabled,h:document.getElementById('st7Pg').hidden}")
        ck(f'{L}: Navigation shows Reset this page with its count',pb['t']=='Reset this page (1)' and not pb['d'] and not pb['h'],pb)
        if lite: pg.locator('#set .sheet').screenshot(path=f'{OUT}/s7_marks_nav_{L}.png')
        pg.click('#st7Pg');pg.wait_for_timeout(300)
        ck(f'{L}: Reset this page puts Follow back to Keep centred and stores it',R(pg,"UI.followMode")=='center' and cnt(pg,'nav')==0 and R(pg,"document.getElementById('st7Pg').textContent")=='Undo the reset',R(pg,"UI.followMode"))
        ck(f'{L}: other pages are untouched',R(pg,"UI.chase")==False and R(pg,"UI.gridB")==70)
        pg.click('#st7Pg');pg.wait_for_timeout(300)
        ck(f'{L}: Undo the reset restores the page',R(pg,"UI.followMode")=='lead' and cnt(pg,'nav')==1)
        # search finds the backup card and Reset all
        openS(pg,'general')
        h=pg.evaluate("q=>{const e=document.getElementById('setQ');e.focus();e.value=q;e.dispatchEvent(new Event('input'));return [...document.querySelectorAll('#setQR button b')].map(b=>b.textContent)}",'backup')
        ck(f'{L}: search "backup" finds Settings backup and restore',any('Settings backup' in x for x in h),h)
        h=pg.evaluate("q=>{const e=document.getElementById('setQ');e.value=q;e.dispatchEvent(new Event('input'));return [...document.querySelectorAll('#setQR button b')].map(b=>b.textContent)}",'reset all')
        ck(f'{L}: search "reset all" finds Reset all settings',any('Reset all settings' in x for x in h),h)
        pg.evaluate("()=>{const e=document.getElementById('setQ');e.value='';e.dispatchEvent(new Event('input'));e.blur()}")
        # back up now, save as a file
        ck(f'{L}: no backup yet',R(pg,"ST7.backups().length")==0 and R(pg,"document.getElementById('st7BkSel').hidden")==True)
        pg.click('#st7BkNow');pg.wait_for_timeout(200)
        ck(f'{L}: Back up now keeps one backup with every setting',R(pg,"ST7.backups().length")==1 and R(pg,"ST7.backups()[0].UI.chase")==False and R(pg,"document.getElementById('st7BkSel').options.length")==1)
        with pg.expect_download() as dl:pg.click('#st7BkFile')
        d=dl.value;path=d.path();data=json.load(open(path))
        ck(f'{L}: Save as a file gives the backup as JSON',d.suggested_filename.startswith('AudioLab settings backup') and data.get('kind')=='audiolab-settings-backup' and data['UI'].get('clipA')==36,d.suggested_filename)
        if not lite: pg.evaluate("()=>document.getElementById('st7Bk').scrollIntoView()");pg.locator('#st7Bk').screenshot(path=f'{OUT}/s7_backup_card_{L}.png')
        # Reset all: the list, cancel
        keys0=R(pg,"JSON.stringify(UI.keys||{})")
        pg.click('#genReset');pg.wait_for_timeout(300)
        li=pg.evaluate("()=>[...document.querySelectorAll('#cdP .st7list b, #cdP .st7ul span')].map(e=>e.textContent)")
        ck(f'{L}: Reset all lists the changed settings with their defaults',any('Editing › Pick up notes' in x and 'back to on' in x for x in li) and any('Navigation › Follow the playhead' in x for x in li),li[:12])
        ck(f'{L}: Reset all lists what goes back outside Settings and what is kept',any(x.startswith('Also back to how they came') for x in li) and 'Metronome and count-in' in li and 'Your keyboard shortcuts' in li,li)
        ck(f'{L}: the dialog says a backup is made first',R(pg,"document.getElementById('cdB').textContent").find('Back up and reset')>=0 and 'backup' in R(pg,"document.getElementById('cdP').textContent"))
        pg.locator('#set .sheet').page.screenshot(path=f'{OUT}/s7_reset_all_{L}.png')
        pg.click('#cdB button[data-i="0"]');pg.wait_for_timeout(200)
        ck(f'{L}: Cancel changes nothing',R(pg,"UI.chase")==False and R(pg,"ST7.backups().length")==1)
        # Reset all: confirm (reloads)
        pg.click('#genReset');pg.wait_for_timeout(300)
        with pg.expect_navigation():pg.click('#cdB button[data-i="1"]')
        ready(pg)
        st=J(pg,"{chase:UI.chase!==false,clipA:(UI.clipA??36),f:UI.followMode,keys:JSON.stringify(UI.keys||{}),bk:ST7.backups().map(b=>[b.why,b.UI.chase,b.UI.followMode])}")
        ck(f'{L}: Reset all reset every setting and kept the shortcuts',st['chase']==True and st['clipA']==36 and st['f']=='center' and st['keys']==keys0,st)
        ck(f'{L}: the backup from before Reset all holds the old settings',st['bk'][:1]==[['before Reset all',False,'lead']] and len(st['bk'])==2,st['bk'])
        openS(pg,'editing');ck(f'{L}: after the reset nothing is marked',cnt(pg,'editing')==0 and cnt(pg,'nav')==0 and not mk(pg,'chase')['chg'])
        # restore it
        openS(pg,'general');pg.click('#st7BkRes');pg.wait_for_timeout(300)
        with pg.expect_navigation():pg.click('#cdB button[data-i="1"]')
        ready(pg)
        st=J(pg,"{chase:UI.chase,f:UI.followMode,lim:UI.limiter,bk:ST7.backups().map(b=>b.why)}")
        ck(f'{L}: Restore brings the old settings back and backs up the current ones first',st['chase']==False and st['f']=='lead' and st['lim']==False and st['bk'][0]=='before a restore' and len(st['bk'])==3,st)
        openS(pg,'editing');ck(f'{L}: the restored settings are marked again',cnt(pg,'editing')==1 and mk(pg,'chase')['chg'])
        ck(f'{L}: no console errors',not errs,errs[:5])
        c.close()
    b.close()
print(f'taskST_S7: {N[1]}/{N[0]} checks pass'+('' if not FAIL else ' FAILED: '+', '.join(FAIL)))
sys.exit(1 if FAIL else 0)
