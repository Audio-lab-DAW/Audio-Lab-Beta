"""Task D3 (v0.226): the type scale. One run looks at every screen of the app at one window size and one light level and writes,
for every piece of text on it, the size, weight, family, digit style and where it sits (census.json), plus a screenshot of each screen.
Screens: the main window (transport, arrangement, track headers), the devices of eight tracks and of the master, every instrument and
effect one by one (alldev), the mixer, every Settings page scrolled through, About (both pictures and the full list), and 24 popups
(menus, dialogs, browsers, piano roll, time machine, loudness, CPU, update, tooltips, toast).
  python3 tools/ui-tests/taskD3.py ROOT OUT W H LIGHT(0/1) [only these screens, comma separated]
Fonts: requests to Google Fonts are blocked so that every run uses the same Inter (the one installed on the test machine).
Then: python3 tools/ui-tests/taskD3_compare.py BEFORE_OUT AFTER_OUT   (BEFORE = the same run on the version before)
With CENSUS=taskD3_probe.js and a --probe copy of the app (tools/edits/taskD3.py) the run measures line heights for taskD3_pins.py."""
import sys,os,mimetypes,json
from playwright.sync_api import sync_playwright
ROOT=sys.argv[1];OUT=sys.argv[2];W=int(sys.argv[3]);H=int(sys.argv[4]);LITE=sys.argv[5]=='1';FILT=sys.argv[6] if len(sys.argv)>6 else ''
os.makedirs(OUT,exist_ok=True)
def serve(route):
    p=route.request.url.split('https://app.test/',1)[1].split('?')[0] or 'index.html';f=os.path.join(ROOT,p)
    if p.endswith('coi-serviceworker.js') or not os.path.isfile(f): return route.fulfill(status=404,body=b'')
    route.fulfill(status=200,body=open(f,'rb').read(),content_type=mimetypes.guess_type(f)[0] or 'application/octet-stream')
CENSUS=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),os.environ.get('CENSUS','taskD3_census.js'))).read();SHOTS=not os.environ.get('NOSHOT')
ERRS=[]
def page(b):
    c=b.new_context(viewport={'width':W,'height':H});pg=c.new_page()
    pg.on('pageerror',lambda e:ERRS.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'ERR_FAILED' not in m.text and ERRS.append('console '+m.text[:200]));pg.route('https://app.test/**',serve);pg.route('https://fonts.googleapis.com/**',lambda r:r.abort());pg.route('https://fonts.gstatic.com/**',lambda r:r.abort())
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%json.dumps({'splash':False,'lat3':1,'lite':LITE,'liteMan':LITE}))
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(2500)
    pg.evaluate("c=>window.AudioLab.run(c)",'UI.lite=%s;UI.liteMan=%s;applyLite()'%(('true','true') if LITE else ('false','false')));pg.wait_for_timeout(300)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove();const t=document.getElementById('toast');t&&t.classList.remove('show')}")
    pg.evaluate("()=>document.fonts.ready");pg.mouse.move(640,5)
    return c,pg
RES={}
def snap(pg,name,wait=500):
    pg.wait_for_timeout(wait);pg.evaluate("()=>{const t=document.getElementById('toast');t&&t.classList.remove('show')}")
    RES[name]=pg.evaluate(CENSUS);SHOTS and pg.screenshot(path=os.path.join(OUT,name+'.png'));print(name,flush=True)
def G(name):return (not FILT) or any(f in name for f in FILT.split(','))
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    def fresh():
        c,pg=page(b);return c,pg,(lambda code:pg.evaluate("c=>window.AudioLab.run(c)",code))
    if G('main') or G('dev'):
        c,pg,R=fresh()
        if G('main'):snap(pg,'main')
        if G('dev'):
            for n in ['Kick','Bass','Lead','Acid','Plate reverb','Drums','Crash','Vocals (original)']:
                R("(()=>{const t=S.tracks.find(t=>t.name===%s);selectTrack(t.id);renderFx();devHide(false)})()"%json.dumps(n));pg.mouse.move(640,5);snap(pg,'dev_'+n.split()[0].lower(),900)
                for i in range(1,4):
                    mv=R("(()=>{const f=document.getElementById('fxin');const b=f.scrollLeft;f.scrollLeft+=f.clientWidth-80;return f.scrollLeft-b})()")
                    if not mv or mv<40:break
                    snap(pg,'dev_'+n.split()[0].lower()+'_s%d'%i,600)
            R("selMaster()");snap(pg,'dev_master',900)
        c.close()
    if G('mixer'):
        c,pg,R=fresh();R("openMixer()");pg.mouse.move(640,5);snap(pg,'mixer',1200)
        R("(()=>{const s=document.querySelector('#mixWin .mxs');s.scrollLeft=s.scrollWidth})()");snap(pg,'mixer_end',600);c.close()
    if G('set'):
        c,pg,R=fresh();R("openSettings()")
        for t in pg.evaluate("()=>[...document.querySelectorAll('#setNav [data-tab]')].map(b=>b.dataset.tab)"):
            pg.click('#setNav [data-tab=%s]'%t);pg.mouse.move(5,5);snap(pg,'set_'+t,600)
            for i in range(1,8):
                mv=pg.evaluate("()=>{const s=[...document.querySelectorAll('#set *')].filter(e=>e.checkVisibility()&&/auto|scroll/.test(getComputedStyle(e).overflowY)&&e.scrollHeight>e.clientHeight+20).sort((a,b)=>b.clientHeight-a.clientHeight)[0];if(!s)return 0;const b=s.scrollTop;s.scrollTop+=s.clientHeight-60;return s.scrollTop-b}")
                if not mv or mv<30:break
                snap(pg,'set_%s_s%d'%(t,i),350)
        c.close()
    if G('about'):
        c,pg,R=fresh();R('AB1.force("corner");showAbout()');snap(pg,'about_corner',1500)
        pg.evaluate("()=>{const b=[...document.querySelectorAll('#splash button')].find(b=>/feature|all/i.test(b.textContent));b&&b.click()}");snap(pg,'about_all',900);c.close()
        c,pg,R=fresh();R('AB1.force("sheet");showAbout()');snap(pg,'about_sheet',1500);c.close()
    if G('alldev') and not os.environ.get('NOALL'):
        c,pg,R=fresh();R("devHide(false);1")
        insts=json.loads(R("JSON.stringify(IBG.flatMap(g=>g[2]))"));fxs=json.loads(R("JSON.stringify(FBG.flatMap(g=>g[2]))"))
        R("(()=>{const t=S.tracks[1];selectTrack(t.id);return 1})()")
        for k in insts:
            R("(()=>{const t=S.tracks[1];t.fx=[];for(const key of Object.keys(t.inst))delete t.inst[key];Object.assign(t.inst,JSON.parse(JSON.stringify(PRESETS['%s'])),{preset:'%s'});selT=t.id;changed(true);renderFx();return 1})()"%(k,k));pg.wait_for_timeout(500)
            R("(()=>{const d=[...fxin.querySelectorAll('.dev[data-d=inst]')].filter(d=>!d.parentElement.closest('.dev'))[0];if(d)d.scrollIntoView({inline:'start'});return 1})()");pg.mouse.move(640,5);snap(pg,'ad_i_'+k,350)
        R("(()=>{const t=S.tracks[1];for(const key of Object.keys(t.inst))delete t.inst[key];Object.assign(t.inst,JSON.parse(JSON.stringify(PRESETS.pluck)),{preset:'pluck'});changed(true);renderFx();return 1})()")
        for k in fxs:
            R("(()=>{const t=S.tracks[1];t.fx=[mkFx('%s')];selT=t.id;changed(true);renderFx();return 1})()"%k);pg.wait_for_timeout(500)
            R("(()=>{const d=[...fxin.querySelectorAll('.dev[data-d=fx]')].filter(d=>!d.parentElement.closest('.dev'))[0];if(d)d.scrollIntoView({inline:'start'});return 1})()");pg.mouse.move(640,5);snap(pg,'ad_f_'+k,350)
        c.close()
    POPS=[('pop_ai',lambda pg,R:pg.click('#bAI')),('pop_tut',lambda pg,R:pg.click('#bTut')),('pop_tm',lambda pg,R:pg.click('#bTM')),('pop_controls',lambda pg,R:pg.click('#bHcz')),
      ('pop_kbd',lambda pg,R:pg.click('#bKbd')),('pop_lufs',lambda pg,R:pg.click('#lufsB')),('pop_cpu',lambda pg,R:pg.click('#cpu')),('pop_newproj',lambda pg,R:pg.click('#pAdd')),
      ('pop_ctx_track',lambda pg,R:pg.click('#hdrin .hdr .nm',button='right')),('pop_ctx_clip',lambda pg,R:pg.mouse.click(700,200,button='right')),('pop_ctx_empty',lambda pg,R:pg.mouse.click(700,130,button='right')),
      ('pop_choice',lambda pg,R:R("askChoice('Delete the track?','The track Kick and its 29 clips are removed. You can undo this.',[{label:'Cancel'},{label:'Delete',primary:true}]);1")),
      ('pop_text',lambda pg,R:R("askText('Rename the track','Kick');1")),
      ('pop_fxbrowser',lambda pg,R:R("openFxBrowser(S.tracks[1]);1")),('pop_instbrowser',lambda pg,R:R("openBrowser();1")),
      ('pop_pianoroll',lambda pg,R:R("(()=>{const t=S.tracks[1];openPR(t,t.clips[0])})();1")),
      ('pop_update',lambda pg,R:R("updOpen();1")),('pop_metro',lambda pg,R:R("document.getElementById('mset').hidden=false;1")),
      ('pop_env',lambda pg,R:R("(()=>{const t=S.tracks[1];openEnvEditor(t,t.clips[0])})();1")),
      ('pop_shortcuts',lambda pg,R:R("document.getElementById('kbov').hidden=false;1")),
      ('pop_toast',lambda pg,R:None),
      ('pop_mixpop',lambda pg,R:pg.click('#mBtn',button='right')),('pop_addfx',lambda pg,R:(R("devHide(false)"),pg.click('#fxin .addfx, #fxin [data-a=addfx], #fxin button:has-text("Add effect")'))),
      ('pop_tip',lambda pg,R:(pg.hover('#bLoop'),pg.wait_for_timeout(1500)))]
    for name,act in POPS:
        if not G(name):continue
        c,pg,R=fresh()
        try:
            act(pg,R)
            if name=='pop_toast':
                pg.wait_for_timeout(300);R("toast('Demo song loaded. Press space to play. 12 clips, 3 tracks.')");pg.wait_for_timeout(300);RES[name]=pg.evaluate(CENSUS);SHOTS and pg.screenshot(path=os.path.join(OUT,name+'.png'))
            else:
                if name not in('pop_tip',):pg.mouse.move(640,5)
                snap(pg,name,900)
        except Exception as e:print(name,'ERR',str(e)[:200])
        c.close()
json.dump({'res':RES,'errs':ERRS},open(os.path.join(OUT,'census.json'),'w'));print('errors',ERRS)
