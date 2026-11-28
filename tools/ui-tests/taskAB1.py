"""Task AB1 (v0.225): the About window with the Earth pictures and the fine atom.
Both pictures forced (AB1.force) at 1280 x 720, 1920 x 1080 and 1920 x 1080 at device pixel ratio 2, moving and at the Light level; the random
choice; canvas sizes; text contrast against the brightest point of the picture under each piece of text; frame counts (nothing while closed,
at most 30 and 60 a second while open, one still picture at the Light level and with reduce motion, the frame gate of task AO holds them);
the list, the buttons, Esc, Settings > General. Screenshots go to the out dir.
  python3 tools/ui-tests/taskAB1.py [repo dir] [out dir]"""
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
    return c,pg,errs
# everything the checks need to know about the open window, measured in the page
GEO="""()=>{const el=document.getElementById('splash');if(!el)return null;const q=s=>el.querySelector(s),r=e=>{const b=e.getBoundingClientRect();return[b.left,b.top,b.right,b.bottom]},bg=q('.abBg'),at=q('.abAtom'),er=r(el);
  const lum=c=>{const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c[0])+.7152*f(c[1])+.0722*f(c[2])},rgb=s=>s.match(/[\\d.]+/g).slice(0,3).map(Number);
  const g=bg.getContext('2d'),sx=bg.width/bg.clientWidth,sy=bg.height/bg.clientHeight,br=r(bg);
  /* brightest point of the picture under an element */
  const under=e=>{const b=r(e),x0=Math.max(0,Math.floor((b[0]-br[0])*sx)),y0=Math.max(0,Math.floor((b[1]-br[1])*sy)),x1=Math.min(bg.width,Math.ceil((b[2]-br[0])*sx)),y1=Math.min(bg.height,Math.ceil((b[3]-br[1])*sy));if(x1<=x0||y1<=y0)return 0;const d=g.getImageData(x0,y0,x1-x0,y1-y0).data;let m=0;for(let i=0;i<d.length;i+=4){const l=lum([d[i],d[i+1],d[i+2]]);if(l>m)m=l}return m};
  const con={},T={'Audio':['.wmA'],'Lab':['.wmL','#7aaaff'],'small line':['.abS'],'Designed by':['.abBy'],'the name':['.abBy span'],'info label':['.abI span:not(.v)'],'info value':['.abI .v'],'Under the hood':['.abH'],'feature name':['.abT .n'],'feature value':['.abT .v'],'copyright':['.abCr'],'button':['.abB button']};
  for(const k in T){let worst=99;for(const e of el.querySelectorAll(T[k][0])){const b=r(e);if(b[3]<=er[1]||b[1]>=er[3])continue;const col=T[k][1]?[122,170,255]:rgb(getComputedStyle(e).color),a=lum(col),u=under(e);worst=Math.min(worst,(Math.max(a,u)+.05)/(Math.min(a,u)+.05))}con[k]=+worst.toFixed(2)}
  return{kind:el.dataset.abp,cls:el.className,win:er,vw:innerWidth,vh:innerHeight,canv:el.querySelectorAll('canvas').length,bg:[bg.width,bg.height,bg.clientWidth,bg.clientHeight],atom:[at.width,at.height,at.clientWidth,at.clientHeight],atomR:r(at),
    sh:[el.clientHeight,el.scrollHeight,el.clientWidth,el.scrollWidth],text:q('.abC').innerText,old:el.querySelectorAll('.ahf,.ahfT,.abg,.spw,p').length,rows:[r(at),r(q('.abW')),r(q('.abS')),r(q('.abBy')),r(q('.abI')),r(q('.abH')),r(q('.abF')),r(q('.abB')),r(q('.abCr'))],con,
    dpr:devicePixelRatio,tiles:el.querySelectorAll('.abT').length,info:el.querySelectorAll('.abI>div').length}}"""
def counts(pg):return json.loads(R(pg,'JSON.stringify(AB1.n)'))
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    worst={}
    # 1. both pictures, three sizes, moving and Light
    for (w,h,dpr) in [(1280,720,1),(1920,1080,1),(1920,1080,2)]:
        for lite in (False,True):
            cx,pg,errs=page(b,w,h,dpr,lite);tag0=f'{w}x{h}@{dpr}'+('_light' if lite else '')
            ck(f'{tag0}: Light level as asked',pg.evaluate("()=>document.body.classList.contains('lite')")==lite)
            for k in ('corner','sheet'):
                tag=f'{k}_{tag0}';R(pg,f'AB1.force("{k}");showAbout()');pg.wait_for_timeout(1300);g=pg.evaluate(GEO)
                ck(f'{tag}: the forced picture is shown',g and g['kind']==k and 'ab2' in g['cls'],g and g['kind'])
                ck(f'{tag}: two canvases, picture and atom',g['canv']==2,g['canv'])
                ck(f'{tag}: window inside the screen',g['win'][0]>=0 and g['win'][1]>=0 and g['win'][2]<=g['vw'] and g['win'][3]<=g['vh'],g['win'])
                ck(f'{tag}: no scrolling needed, no sideways scroll',g['sh'][1]<=g['sh'][0]+1 and g['sh'][3]<=g['sh'][2],g['sh'])
                ck(f'{tag}: picture drawn at the device pixel ratio (at most 2)',abs(g['bg'][0]-g['bg'][2]*min(dpr,2))<=1 and abs(g['bg'][1]-g['bg'][3]*min(dpr,2))<=1,g['bg'])
                ck(f'{tag}: atom drawn at the device pixel ratio, 116 points across',g['atom'][2]==116 and g['atom'][0]==round(116*dpr) and g['atom'][1]==round(116*dpr),g['atom'])
                rows=g['rows'];ck(f'{tag}: logo, name, lines, list, buttons, copyright in order and apart',all(rows[i][3]<=rows[i+1][1]+.5 for i in range(len(rows)-1)),rows)
                ck(f'{tag}: 8 info values, 6 features, none of the old About markup',g['info']==8 and g['tiles']==6 and g['old']==0,[g['info'],g['tiles'],g['old']])
                ck(f'{tag}: no em dash, version shown',('—' not in g['text']) and ('VERSION '+pg.evaluate("()=>AudioLab.version")) in g['text'].upper())
                # contrast: Light = the one still picture; moving = six moments
                cons=[g['con']]
                if not lite:
                    for i in range(5):pg.wait_for_timeout(450);cons.append(pg.evaluate(GEO)['con'])
                for c in cons:
                    for key,v in c.items():
                        wk=(key,'Light' if lite else 'moving');worst[wk]=min(worst.get(wk,99),v)
                lo=min(min(c.values()) for c in cons);ck(f'{tag}: every text at least 4.5 : 1 against the brightest point behind it',lo>=4.5,lo)
                n0=counts(pg);pg.wait_for_timeout(1000);n1=counts(pg);run=R(pg,'AB1.running()')
                if lite:ck(f'{tag}: Light level, a still picture (no frames)',n1['bg']==n0['bg'] and n1['atom']==n0['atom'] and not run,[n0,n1,run])
                else:ck(f'{tag}: moving, picture at most 30 a second, atom at most 60',0<n1['bg']-n0['bg']<=32 and n1['bg']-n0['bg']<=n1['atom']-n0['atom']<=63 and run,[n1['bg']-n0['bg'],n1['atom']-n0['atom']])
                pg.screenshot(path=f'{OUT}/ab1_{tag}.png')
                pg.screenshot(path=f'{OUT}/ab1_{tag}_atom.png',clip={'x':g['atomR'][0]-12,'y':g['atomR'][1]-12,'width':140,'height':140})
                pg.keyboard.press('Escape');pg.wait_for_timeout(120);n2=counts(pg);ck(f'{tag}: Esc closes and the drawing stops at once',R(pg,'!SPL&&!AB1.state()') and not R(pg,'AB1.running()'))
                pg.wait_for_timeout(900);n3=counts(pg);ck(f'{tag}: nothing drawn while About is closed',n3['bg']==n2['bg'] and n3['atom']==n2['atom'] and pg.evaluate("()=>!document.getElementById('splash')"),[n2,n3])
            ck(f'{tag0}: no errors',not errs,errs);cx.close()
    print('worst contrast per text (moving / Light):')
    for key in dict.fromkeys(k for k,_ in worst):print('  %-16s %5.1f : 1   %5.1f : 1'%(key,worst.get((key,'moving'),0),worst.get((key,'Light'),0)))
    # 2. the rest on one page
    cx,pg,errs=page(b,1500,950)
    R(pg,'AB1.force(null)')
    st=json.loads(R(pg,"(()=>{const c={corner:0,sheet:0};let run=0,mx=0,last='';for(let i=0;i<20000;i++){const k=AB1.pick();c[k]++;if(k===last){run++;mx=Math.max(mx,run)}else run=0;last=k}return JSON.stringify([c,mx])})()"))
    print('20000 picks',st);ck('pick: both pictures, about half each',abs(st[0]['corner']-10000)<400 and st[0]['corner']+st[0]['sheet']==20000,st);ck('pick: the same one can come twice in a row (plain chance)',st[1]>=3,st[1])
    seq=[]
    for i in range(40):
        R(pg,'showAbout()');pg.wait_for_timeout(60);seq.append(pg.evaluate("()=>document.getElementById('splash').dataset.abp"));R(pg,'hideSplash()');pg.wait_for_timeout(700 if i%10==0 else 30)
    print('40 openings',''.join(k[0] for k in seq));ck('40 real openings: both seen, no restart needed',6<=seq.count('corner')<=34 and seq.count('corner')+seq.count('sheet')==40,seq.count('corner'))
    pg.wait_for_timeout(900);ck('after 40 openings: one splash at most, nothing running',pg.evaluate("()=>document.querySelectorAll('#splash').length")==0 and not R(pg,'AB1.running()'))
    ck('localStorage hook forces a picture',R(pg,"localStorage.setItem('audiolab-about-test','sheet');const a=[1,2,3,4,5,6,7,8].every(()=>AB1.pick()==='sheet');localStorage.removeItem('audiolab-about-test');a"))
    # the frame gate of task AO holds both drawings
    R(pg,'AB1.force("corner");showAbout()');pg.wait_for_timeout(800);R(pg,'AO.gate=true');pg.wait_for_timeout(150);n0=counts(pg);pg.wait_for_timeout(900);n1=counts(pg)
    ck('frame gate shut (app in the background): nothing drawn',n0==n1,[n0,n1]);R(pg,'AO.open()');pg.wait_for_timeout(700);n2=counts(pg);ck('frame gate open: it runs again',n2['bg']>n1['bg'] and n2['atom']>n1['atom'],[n1,n2])
    # Light level switched while open
    R(pg,'UI.lite=true;UI.liteMan=true;applyLite()');pg.wait_for_timeout(400);n0=counts(pg);pg.wait_for_timeout(800);n1=counts(pg);ck('Light switched on while open: still picture',n0==n1 and not R(pg,'AB1.running()'),[n0,n1])
    R(pg,'UI.lite=false;UI.liteMan=false;applyLite()');pg.wait_for_timeout(600);n2=counts(pg);ck('Light switched off while open: moves again',n2['bg']>n1['bg'] and R(pg,'AB1.running()'),[n1,n2])
    # the list
    more=pg.evaluate("()=>document.getElementById('abMore').textContent");ck('button names all 35 features',more=='All 35 features',more)
    pg.click('#abMore');pg.wait_for_timeout(1200);g=pg.evaluate("()=>{const s=document.getElementById('splash');return{rows:s.querySelectorAll('.abR').length,groups:s.querySelectorAll('.abG').length,btn:document.getElementById('abMore').textContent,ex:document.getElementById('abMore').getAttribute('aria-expanded'),sh:[s.clientHeight,s.scrollHeight,s.clientWidth,s.scrollWidth],top:s.scrollTop,em:s.innerText.includes('\\u2014'),cv:s.querySelector('.abBg').getBoundingClientRect().top-s.getBoundingClientRect().top}}")
    ck('full list: 35 features in 6 groups, scrolls, no sideways scroll, no em dash',g['rows']==35 and g['groups']==6 and g['btn']=='Show less' and g['ex']=='true' and g['sh'][1]>g['sh'][0] and g['sh'][3]<=g['sh'][2] and not g['em'],g)
    ck('full list: the picture stays in place while the list scrolls',g['top']>50 and abs(g['cv'])<2,[g['top'],g['cv']]);pg.screenshot(path=f'{OUT}/ab1_list_top.png')
    pg.evaluate("()=>document.getElementById('splash').scrollTo(0,99999)");pg.wait_for_timeout(400);pg.screenshot(path=f'{OUT}/ab1_list_end.png')
    pg.evaluate("()=>document.getElementById('splash').scrollTo(0,0)");pg.click('#abMore');pg.wait_for_timeout(500);ck('full list closes again',pg.evaluate("()=>{const s=document.getElementById('splash');return document.getElementById('abAll').hidden&&s.scrollHeight<=s.clientHeight+1}"))
    pg.click('#abUpd');pg.wait_for_timeout(800);ck('Check for updates opens the update window',pg.evaluate("()=>!!document.getElementById('updDlg')"));R(pg,'updClose();hideSplash()');pg.wait_for_timeout(800)
    R(pg,'showAbout()');pg.wait_for_timeout(400);pg.click('#splash .abx');pg.wait_for_timeout(800);ck('the close button closes',pg.evaluate("()=>!document.getElementById('splash')"))
    R(pg,"openSettings('general')");pg.wait_for_timeout(600);pg.evaluate("()=>document.getElementById('genHood').scrollIntoView()");pg.wait_for_timeout(300);pg.click('#genHood');pg.wait_for_timeout(900)
    ck('Settings, General, About opens the new window',pg.evaluate("()=>!!document.querySelector('#splash.ab.ab2 .abF')"));R(pg,'hideSplash()');pg.wait_for_timeout(800)
    # outside About nothing changed: the nav logo is still the app's atom, the loading splash preview has no About parts
    ck('nav logo untouched',pg.evaluate("()=>!!document.getElementById('atomC')&&document.getElementById('atomC').width>0"))
    R(pg,"showSplash('pv')");pg.wait_for_timeout(500);ck('the splash preview is not the About window',pg.evaluate("()=>{const s=document.getElementById('splash');return !!s&&s.classList.contains('ld')&&!s.classList.contains('ab2')&&!s.querySelector('.abBg')}") and not R(pg,'AB1.state()'));R(pg,'hideSplash()');pg.wait_for_timeout(700)
    # cost of one picture, off screen, 780 x 720 at 2 canvas pixels per point
    cost=json.loads(R(pg,"JSON.stringify({corner:AB1.bench('corner',780,720,120),sheet:AB1.bench('sheet',780,720,120),corner1080:AB1.bench('corner',780,860,120),sheet1080:AB1.bench('sheet',780,860,120),atom:AB1.benchAtom(300),particles:FATOM.count()})"))
    print('cost, ms a picture',{k:round(v,3) for k,v in cost.items()});ck('cost: a picture under 3 ms, the atom under 1 ms here',max(cost['corner'],cost['sheet'],cost['corner1080'],cost['sheet1080'])<3 and cost['atom']<1,cost)
    ck('no errors',not errs,errs);cx.close()
    # reduce motion: one still picture
    cx,pg,errs=page(b,1280,720,reduced_motion='reduce');R(pg,'AB1.force("sheet");showAbout()');pg.wait_for_timeout(900);n0=counts(pg);pg.wait_for_timeout(800);n1=counts(pg)
    ck('reduce motion: one still picture, no frames',n0==n1 and n0['bg']>=1 and not R(pg,'AB1.running()'),[n0,n1]);ck('reduce motion: no errors',not errs,errs);cx.close()
    # a small window
    cx,pg,errs=page(b,700,560);R(pg,'AB1.force("corner");showAbout()');pg.wait_for_timeout(900);g=pg.evaluate(GEO);pg.screenshot(path=f'{OUT}/ab1_small_700x560.png')
    ck('small window: inside the screen, no sideways scroll',g['win'][2]<=g['vw'] and g['win'][3]<=g['vh'] and g['sh'][3]<=g['sh'][2],[g['win'],g['sh']]);ck('small window: no errors',not errs,errs);cx.close()
    b.close()
print(f'{N[1]} of {N[0]} checks pass');sys.exit(0 if N[1]==N[0] else 1)
