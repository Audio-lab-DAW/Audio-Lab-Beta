"""Task AB2 (v0.229): the About card in the Settings menu (under Output and Export audio): the fine atom (FATOM) and a small splash drawing (SPLBG.FN) behind it.
Each of the five drawings forced (AB2.force) at device pixel ratio 1 and 2, moving and at the Light level: the forced drawing is shown, two canvases (drawing and atom)
and no blurred balls, both at the device pixel ratio, the name and the version in the drawing's colours, nothing of the drawing under the name and the version,
the old nucleus never painted; the tooltip and the click to About. Frames counted: at most 30 a second while open, nothing while closed (also after 30 openings),
at the Light level the drawing still and the atom at most 15 a second, one still picture with reduce motion, the frame gate of task AO holds them. The random choice: 60,000 picks and 40 real openings.
Screenshots of the card go to the out dir.
  python3 tools/ui-tests/taskAB2.py [repo dir] [out dir]"""
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
def page(b,w,h,dpr=1,lite=False,**kw):
    c=b.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr,**kw);pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and errs.append('console '+m.text[:200]));pg.route('https://app.test/**',alsong(serve))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%json.dumps({'splash':False,'lat3':1,'lite':lite,'liteMan':lite}))
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(2500)
    R(pg,'UI.lite=%s;UI.liteMan=%s;applyLite()'%(('true','true') if lite else ('false','false')));pg.wait_for_timeout(300)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
    R(pg,"window.__old=0;{const o=paintAtom;paintAtom=function(c){if(c&&c.id==='navAtomC')__old++;return o.apply(this,arguments)}}")
    return c,pg,errs
GEO="""()=>{const el=document.querySelector('#setNav .navAtom'),r=e=>{const b=e.getBoundingClientRect();return[b.left,b.top,b.right,b.bottom]},bg=el.querySelector('canvas.nab'),at=document.getElementById('navAtomC'),cs=s=>getComputedStyle(el.querySelector(s));
  /* the strongest pixel of the drawing under a piece of text (0 to 255, the largest of r, g, b weighted by alpha) */
  const g=bg.getContext('2d'),sx=bg.width/bg.clientWidth,sy=bg.height/bg.clientHeight,br=r(bg),under=e=>{const b=r(e),x0=Math.max(0,Math.floor((b[0]-br[0])*sx)),y0=Math.max(0,Math.floor((b[1]-br[1])*sy)),x1=Math.min(bg.width,Math.ceil((b[2]-br[0])*sx)),y1=Math.min(bg.height,Math.ceil((b[3]-br[1])*sy));if(x1<=x0||y1<=y0)return 0;const d=g.getImageData(x0,y0,x1-x0,y1-y0).data;let m=0;for(let i=0;i<d.length;i+=4){const v=Math.max(d[i],d[i+1],d[i+2])*d[i+3]/255;if(v>m)m=v}return Math.round(m)};
  return{kind:el.dataset.sp,cls:el.className,title:el.title,canv:el.querySelectorAll('canvas').length,bub:el.querySelectorAll('.bubc').length,bg:[bg.width,bg.height,bg.clientWidth,bg.clientHeight],atom:[at.width,at.height,at.clientWidth,at.clientHeight],
    ink:cs('.wmA').color,p:cs('.wmP').color,pb:cs('.wmP').borderTopColor,lab:cs('.wmL').backgroundImage,ver:cs('small').color,verText:el.querySelector('small').textContent,
    underName:under(el.querySelector('b')),underVer:under(el.querySelector('small')),card:r(el),atomR:r(at),nameR:r(el.querySelector('b')),verR:r(el.querySelector('small'))}}"""
def hex2rgb(h):h=h.lstrip('#');return 'rgb(%d, %d, %d)'%(int(h[0:2],16),int(h[2:4],16),int(h[4:6],16))
def cnt(pg):return json.loads(R(pg,'JSON.stringify(AB2.n)'))
KS=['moons','harm','dipole','chart','spec']
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    PAL=None
    # 1. the five drawings, pixel ratio 1 and 2, moving and Light
    for dpr in (1,2):
        for lite in (False,True):
            cx,pg,errs=page(b,1440,900,dpr,lite);tag0=f'@{dpr}'+('_light' if lite else '')
            if PAL is None:PAL=json.loads(R(pg,'JSON.stringify(SPLBG.PAL)'))
            ver=pg.evaluate("()=>AudioLab.version")
            for k in KS:
                tag=f'{k}{tag0}';R(pg,f'AB2.force("{k}");openSettings("general")');pg.wait_for_timeout(1200);g=pg.evaluate(GEO);P=PAL[k]
                ck(f'{tag}: the forced drawing is shown',g['kind']==k and 'ab2c' in g['cls'],g['kind'])
                ck(f'{tag}: two canvases (drawing, atom), no blurred balls',g['canv']==2 and g['bub']==0,[g['canv'],g['bub']])
                ck(f'{tag}: drawing canvas at the device pixel ratio',abs(g['bg'][0]-g['bg'][2]*dpr)<=1 and abs(g['bg'][1]-g['bg'][3]*dpr)<=1,g['bg'])
                ck(f'{tag}: atom canvas at the device pixel ratio',g['atom'][2]>=60 and abs(g['atom'][0]-g['atom'][2]*dpr)<=1 and g['atom'][0]==g['atom'][1],g['atom'])
                ck(f'{tag}: "Audio", PRO, its ring and the version in the drawing\'s colours',g['ink']==hex2rgb(P['ink']) and g['p']==hex2rgb(P['p']) and g['pb']==hex2rgb(P['a']) and g['ver']==hex2rgb(P['n']),[g['ink'],g['p'],g['pb'],g['ver']])
                ck(f'{tag}: "Lab" in the drawing\'s gradient',hex2rgb(P['a']) in g['lab'] and hex2rgb(P['b']) in g['lab'],g['lab'])
                ck(f'{tag}: nothing of the drawing under the name and the version (at most 12 of 255)',g['underName']<=12 and g['underVer']<=12,[g['underName'],g['underVer']])
                ck(f'{tag}: atom, name and version in order inside the card',g['card'][1]<=g['atomR'][1] and g['atomR'][3]<=g['nameR'][1]+6 and g['nameR'][3]<=g['verR'][1]+2 and g['verR'][3]<=g['card'][3],[g['atomR'],g['nameR'],g['verR'],g['card']])
                ck(f'{tag}: version shown, tooltip kept',g['verText']=='v'+ver and g['title']=='AudioLab Pro',[g['verText'],g['title']])
                pg.locator('.navAtom').screenshot(path=f'{OUT}/card_{k}_dpr{dpr}{"_light" if lite else ""}.png')
                if dpr==2 and not lite:
                    pg.locator('#navAtomC').screenshot(path=f'{OUT}/atom_{k}.png')
                R(pg,'closeSet()');pg.wait_for_timeout(150)
            ck(f'{tag0}: the old nucleus is never painted on the card',R(pg,'__old')==0,R(pg,'__old'))
            if lite:
                R(pg,'AB2.force("chart");openSettings("general")');pg.wait_for_timeout(500);n0=cnt(pg);pg.wait_for_timeout(1200);n1=cnt(pg)
                fa=(n1['atom']-n0['atom'])/1.2;ck(f'{tag0}: Light level: the drawing one still picture, the atom moving at most 15 a second',n0['bg']==n1['bg'] and n0['bg']>=1 and 8<=fa<=16,[n0,n1,fa]);R(pg,'closeSet()')
            # the card still opens About
            if dpr==1 and not lite:
                R(pg,'openSettings("general")');pg.wait_for_timeout(300);pg.click('.navAtom');pg.wait_for_timeout(700)
                ck('a click on the card opens About',pg.evaluate("()=>!!document.querySelector('#splash.ab2')"));pg.keyboard.press('Escape');pg.wait_for_timeout(400);R(pg,'closeSet()')
            ck(f'{tag0}: no console errors',not errs,errs);cx.close()
    # 2. frames
    cx,pg,errs=page(b,1440,900,1);R(pg,'AB2.force(null)')
    R(pg,'openSettings("general")');pg.wait_for_timeout(600);n0=cnt(pg);pg.wait_for_timeout(3000);n1=cnt(pg);fps=(n1['bg']-n0['bg'])/3
    ck('open and moving: 20 to 31 pictures a second, the atom with each',20<=fps<=31 and n1['bg']-n0['bg']==n1['atom']-n0['atom'],fps);print('  open: %.1f pictures a second'%fps)
    R(pg,'closeSet()');pg.wait_for_timeout(200);n0=cnt(pg);pg.wait_for_timeout(2000);n1=cnt(pg)
    ck('closed: nothing drawn',n0['bg']==n1['bg'] and n0['atom']==n1['atom'],[n0,n1]);ck('closed: no drawing kept',R(pg,'AB2.kind()') is None)
    seq=[]
    for i in range(30):
        R(pg,'openSettings("general")');pg.wait_for_timeout(120);seq.append(R(pg,'AB2.kind()'));R(pg,'closeSet()');pg.wait_for_timeout(60)
    pg.wait_for_timeout(200);n0=cnt(pg);pg.wait_for_timeout(1500);n1=cnt(pg)
    ck('after 30 openings: nothing drawn while closed',n0['bg']==n1['bg'],[n0,n1])
    R(pg,'openSettings("general")');pg.wait_for_timeout(600);R(pg,'AO.gate=true');pg.wait_for_timeout(150);n0=cnt(pg);pg.wait_for_timeout(900);n1=cnt(pg)
    ck('frame gate shut (app in the background): nothing drawn',n0==n1,[n0,n1]);R(pg,'AO.open()');pg.wait_for_timeout(700);n2=cnt(pg);ck('frame gate open: it runs again',n2['bg']>n1['bg'],[n1,n2])
    # the card scrolled out of view (a spacer pushes it below the menu's fold): nothing drawn
    out=pg.evaluate("()=>{const n=document.getElementById('setNav'),c=n.querySelector('.navAtom'),sp=document.createElement('div');sp.id='ab2sp';sp.style.cssText='height:1200px;flex:none';n.insertBefore(sp,c);n.scrollTop=0;const a=n.getBoundingClientRect(),b=c.getBoundingClientRect();return b.top>=a.bottom||b.bottom<=a.top||c.clientHeight<2}")
    if out:
        pg.wait_for_timeout(300);n0=cnt(pg);pg.wait_for_timeout(1000);n1=cnt(pg);ck('card out of view: nothing drawn',n0==n1,[n0,n1])
        pg.evaluate("()=>{const n=document.getElementById('setNav');n.scrollTop=n.scrollHeight}");pg.wait_for_timeout(400);n2=cnt(pg);ck('card scrolled into view again: it runs',n2['bg']>n1['bg'],[n1,n2])
    else:ck('the card can be pushed out of view for the check',False)
    pg.evaluate("()=>{const s=document.getElementById('ab2sp');s&&s.remove()}")
    R(pg,'closeSet()')
    for i in range(40):
        R(pg,'openSettings("general")');pg.wait_for_timeout(60);seq.append(R(pg,'AB2.kind()'));R(pg,'closeSet()');pg.wait_for_timeout(40)
    ck('70 real openings: never the same twice in a row',all(seq[i]!=seq[i+1] for i in range(len(seq)-1)),seq)
    ck('70 real openings: all five seen',set(seq)==set(KS),sorted(set(seq)))
    # the splash's own memory is not touched by the card
    sp=pg.evaluate("()=>localStorage.getItem('audiolab-splash-last')");R(pg,'openSettings("general")');R(pg,'closeSet()')
    ck('the splash keeps its own memory',pg.evaluate("()=>localStorage.getItem('audiolab-splash-last')")==sp)
    # 3. the random weights
    sh=json.loads(pg.evaluate("""()=>{const c={},K=SPLBG.KINDS;let last=null,rep=0;for(const k of K)c[k]=0;for(let i=0;i<60000;i++){const k=SPLBG.pick('ab2-weights-test','ab2-no-test');c[k]++;if(k===last)rep++;last=k}return JSON.stringify({c,rep})}"""))
    s={k:sh['c'][k]/600 for k in KS};print('  shares %',{k:round(v,1) for k,v in s.items()})
    ck('60,000 picks: never the same twice in a row',sh['rep']==0,sh['rep'])
    ck('60,000 picks: 22.7 % each for the four line drawings, 9.1 % for the spectrogram (within 0.8)',all(abs(s[k]-22.73)<.8 for k in KS[:4]) and abs(s['spec']-9.09)<.8,s)
    ck('frames and picks: no console errors',not errs,errs);cx.close()
    # 4. reduce motion
    cx,pg,errs=page(b,1440,900,1,reduced_motion='reduce');R(pg,'AB2.force("moons");openSettings("general")');pg.wait_for_timeout(700);n0=cnt(pg);pg.wait_for_timeout(1000);n1=cnt(pg)
    ck('reduce motion: one still picture, no frames',n0==n1 and n0['bg']>=1,[n0,n1]);ck('reduce motion: no errors',not errs,errs);cx.close()
    b.close()
print(f'{N[1]} of {N[0]} checks pass');sys.exit(1 if FAIL else 0)
