# task SP1 (v0.224): the splash pictures and the last stretch.   python3 tools/ui-tests/taskSP1.py index.html [outdir]
# Each of the five pictures is forced through localStorage 'audiolab-splash-test' (moons, harm, dipole, chart, spec) and looked at in three window sizes;
# then the timing (never closes before loading is done, closes by itself about 1.5 s after, click and key only in that last stretch), the random pick,
# the frame rate, the freeze gate, reduce motion, the Show now preview and the splash switched off.
import sys,os,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
f=sys.argv[1] if len(sys.argv)>1 else 'index.html';out=sys.argv[2] if len(sys.argv)>2 else '.';os.makedirs(out,exist_ok=True)
src=open(f,encoding='utf-8').read().encode();fails=[];n=[0]
def ck(name,ok,extra=''):
    n[0]+=1;print(('PASS ' if ok else 'FAIL ')+name,extra)
    if not ok:fails.append(name)
KINDS=['moons','harm','dipole','chart','spec']
INIT="""if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify(%s));%s
window.__T={ev:[]};new MutationObserver(()=>{const s=document.getElementById('splash'),n=performance.now();if(s&&!__T.show)__T.show=n;if(s&&s.classList.contains('rdy')&&!__T.rdy)__T.rdy=n;if(s&&s.classList.contains('out')&&!__T.out)__T.out=n;if(__T.show&&!s&&!__T.gone)__T.gone=n}).observe(document,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});"""
def page(b,w=1280,h=720,kind=None,ui='{lat3:1}',thr=1,**kw):
    cx=b.new_context(viewport={'width':w,'height':h},**kw);pg=cx.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text and 'fetching the script' not in m.text else None)
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script(INIT%(ui,("localStorage.setItem('audiolab-splash-test','%s');"%kind) if kind else "localStorage.removeItem('audiolab-splash-test');"))
    if thr>1:pg.context.new_cdp_session(pg).send('Emulation.setCPUThrottlingRate',{'rate':thr})
    return cx,pg,errs
R=lambda pg,c:pg.evaluate("c=>window.AudioLab.run(c)",c)
RDY="()=>{const s=document.getElementById('splash');return !!(s&&s.classList.contains('rdy'))}"
GEO="""()=>{const s=document.getElementById('splash'),cv=s.querySelector('canvas'),R=e=>{const r=e.getBoundingClientRect();return[r.left,r.top,r.right,r.bottom]},card=R(s),o={card,kind:s.dataset.sp,cv:[cv.width,cv.height],cvr:R(cv),hint:s.querySelector(':scope>p').textContent,
  items:{name:R(s.querySelector('.spw>b')),daw:R(s.querySelector('.sdaw')),ver:R(s.querySelector('.sver')),bar:R(s.querySelector('i')),hint:R(s.querySelector(':scope>p'))},
  vars:['ink','a','b','d','m'].map(k=>s.style.getPropertyValue('--sp'+k)),lab:getComputedStyle(s.querySelector('.wmL')).backgroundImage,em:getComputedStyle(s.querySelector('em')).backgroundImage,audio:getComputedStyle(s.querySelector('.wmA')).color,
  texts:[...s.querySelectorAll('*')].filter(e=>e.children.length===0&&e.textContent.trim()&&getComputedStyle(e).clipPath==='none').map(e=>e.textContent.trim()),ncanvas:s.querySelectorAll('canvas').length,vertxt:s.querySelector('.sver').textContent};
  /* how much of the picture lies under the text: the strongest drawn pixel inside each text box */
  const g=cv.getContext('2d'),kx=cv.width/(card[2]-card[0]),ky=cv.height/(o.cvr[3]-o.cvr[1]);o.under={};let drawn=0;
  for(const k in o.items){const r=o.items[k],x=Math.max(0,Math.floor((r[0]-card[0])*kx)),y=Math.floor((r[1]-o.cvr[1])*ky),w=Math.ceil((r[2]-r[0])*kx),h=Math.ceil((r[3]-r[1])*ky);let mx=0;if(y<cv.height&&w>0&&h>0){const d=g.getImageData(x,Math.max(0,y),w,Math.min(h,cv.height-y)).data;for(let i=3;i<d.length;i+=4)if(d[i]>mx)mx=d[i]}o.under[k]=mx}
  {const d=g.getImageData(0,0,cv.width,cv.height).data;for(let i=0;i<d.length;i+=4)if(d[i+3]>40&&(d[i]+d[i+1]+d[i+2])>60)drawn++}o.drawn=drawn;return o}"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    # ---- 1. each picture, three sizes ----
    for (w,h) in [(1280,720),(1920,1080),(3840,2160)]:
        for k in KINDS:
            cx,pg,errs=page(b,w,h,k);pg.goto('https://app.test/index.html');pg.wait_for_function(RDY,timeout=90000);R(pg,"clearTimeout(SP1.tm)");pg.wait_for_timeout(500)
            g=pg.evaluate(GEO);pg.screenshot(path=os.path.join(out,f'sp1_{k}_{w}x{h}.png'))
            if w==1280:pg.locator('#splash').screenshot(path=os.path.join(out,f'sp1_{k}_card.png'))
            it=g['items'];c=g['card'];order=['name','daw','ver','bar','hint']
            ck(f'{w}x{h} {k}: forced picture shown, one canvas, drawn',g['kind']==k and g['ncanvas']==1 and g['drawn']>300,[g['kind'],g['cv'],g['drawn']])
            ck(f'{w}x{h} {k}: card inside the window',c[0]>=0 and c[1]>=0 and c[2]<=w and c[3]<=h,[round(x) for x in c])
            ck(f'{w}x{h} {k}: name, two lines, bar and hint in order, apart, inside the card',all(it[order[i]][3]<=it[order[i+1]][1]+.5 for i in range(4)) and all(c[0]<=it[q][0] and it[q][2]<=c[2] and c[1]<=it[q][1] and it[q][3]<=c[3] for q in order),{q:[round(x) for x in it[q]] for q in order})
            ck(f'{w}x{h} {k}: text block in the lower third (top at {round((it["name"][1]-c[1])/(c[3]-c[1])*100)} % of the card)',(it['name'][1]-c[1])/(c[3]-c[1])>.62)
            ck(f'{w}x{h} {k}: the figure does not run under the text (strongest pixel under each box, of 255)',max(g['under'].values())<=40,g['under'])
            if w==1280:
                ck(f'{k}: only the name, the two lines and the hint as text',g['texts']==['Audio','Lab','PRO','Digital audio workstation',g['vertxt'],'Click to continue'] and g['vertxt'].startswith('Version '),g['texts'])
                pal=json.loads(pg.evaluate("JSON.stringify(SPLBG.PAL)"))[k];hx=lambda s:'rgb(%d, %d, %d)'%tuple(int(s[i:i+2],16) for i in (1,3,5))
                ck(f'{k}: name and bar take the picture\'s colours',g['vars']==[pal[q] for q in ('ink','a','b','d','m')] and hx(pal['a']) in g['lab'] and hx(pal['b']) in g['lab'] and hx(pal['a']) in g['em'] and hx(pal['d']) in g['em'] and g['audio']==hx(pal['ink']),g['vars'])
            ck(f'{w}x{h} {k}: no console errors',errs==[],errs);cx.close()
    # ---- 2. timing, normal start (three starts in one profile) and a slow computer ----
    for thr in (1,4):
        cx,pg,errs=page(b,1600,1000,None,thr=thr)
        for run in range(3 if thr==1 else 1):
            pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.__T&&window.__T.gone",timeout=180000)
            T=pg.evaluate("window.__T");at=json.loads(R(pg,"JSON.stringify(BOOTU)"))['at'];last=max(at.values());st=json.loads(R(pg,"JSON.stringify({run:SPLBG.running(),kind:SPLBG.kind(),sp:!!document.getElementById('splash'),boot:document.body.classList.contains('booting'),bk:document.querySelectorAll('[data-bk]').length,hold:SP1.hold})"))
            print(f'  cpu x{thr} run {run}: splash at {T["show"]:.0f} ms, last loading step {last} ms, ready {T["rdy"]:.0f}, fade starts {T["out"]:.0f}, gone {T["gone"]:.0f}; steps {at}')
            ck(f'cpu x{thr} run {run}: not closed before loading was done',T['rdy']>=last and T['out']>T['rdy'])
            ck(f'cpu x{thr} run {run}: closes by itself {T["out"]-T["rdy"]:.0f} ms after loading (constant {st["hold"]})',1000<=st['hold']<=2000 and st['hold']-30<=T['out']-T['rdy']<=st['hold']+(350 if thr==1 else 900))
            ck(f'cpu x{thr} run {run}: short fade, then animation stopped, splash and canvas removed, app unlocked',T['gone']-T['out']<700 and not st['run'] and st['kind'] is None and not st['sp'] and not st['boot'] and st['bk']==0,st)
        ck(f'cpu x{thr}: no console errors',errs==[],errs);cx.close()
    # ---- 3. keys and clicks while loading do nothing; in the last stretch they close at once ----
    cx,pg,errs=page(b,1600,1000,'chart',thr=2)
    # the moment the app's code is ready (the splash is still loading then), from inside the page: Esc, Enter, a letter, a press and a click on the card
    pg.add_init_script("""(function f(){try{if(!(window.AudioLab&&window.AudioLab.version&&document.getElementById('splash')&&document.querySelector('#splash.sp1 .sver').textContent.trim().length>3)){requestAnimationFrame(f);return}
      const s=document.getElementById('splash'),o={pre:s.classList.contains('rdy'),ms:window.AudioLab.run('BOOTU.ms')};for(const k of['Escape','Enter','a',' '])document.dispatchEvent(new KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true}));
      for(const ty of['pointerdown','mousedown','pointerup','mouseup','click'])s.dispatchEvent(new MouseEvent(ty,{bubbles:true,cancelable:true,clientX:800,clientY:430}));
      const z=document.getElementById('splash');Object.assign(o,{there:!!z,out:!!(z&&z.classList.contains('out')),rdy:!!(z&&z.classList.contains('rdy')),hint:z?z.querySelector(':scope>p').textContent:null,op:z?getComputedStyle(z.querySelector(':scope>p')).opacity:null,playing:window.AudioLab.run('String(!!play.on)')});window.__early=o}catch(e){window.__early={err:String(e.stack||e)}}})()""")
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.__early",timeout=120000);st=pg.evaluate("window.__early")
    print('  probe:',st)
    ck('while loading: Esc, Enter, a letter, Space and a click leave the splash up','pre' in st and (not st['pre']) and st['ms']<0 and st['there'] and not st['out'] and not st['rdy'],st)
    ck('while loading: no "Click to continue" line',st.get('hint')=='' and st.get('op')=='0',st)
    pg.wait_for_function(RDY,timeout=120000);ck('after loading the line appears',pg.evaluate("document.querySelector('#splash>p').textContent")=='Click to continue')
    t=pg.evaluate("performance.now()");pg.mouse.click(800,430);pg.wait_for_timeout(80);T=pg.evaluate("window.__T")
    ck(f'last stretch: a click closes at once ({T.get("out",0)-T["rdy"]:.0f} ms after ready, well before the 1.5 s)',T.get('out') is not None and T['out']-T['rdy']<1200 and T['out']-t<150)
    ck('click test: no console errors',errs==[],errs);cx.close()
    for key in ('Space','Escape','k'):
        cx,pg,errs=page(b,1600,1000,'moons');pg.goto('https://app.test/index.html');pg.wait_for_function(RDY,timeout=120000)
        t=pg.evaluate("performance.now()");pg.keyboard.press(key);pg.wait_for_timeout(120);T=pg.evaluate("window.__T");pl=R(pg,"String(!!play.on)")
        ck(f'last stretch: the {key} key closes at once and is not passed on (not playing)',T.get('out') is not None and T['out']-t<170 and pl=='false',[T.get('out'),t,pl])
        pg.wait_for_function("()=>!document.getElementById('splash')",timeout=5000)
        if key=='Space':
            pg.keyboard.press('Space');pg.wait_for_timeout(400);pl2=R(pg,"String(!!play.on)");ck('after the splash the app takes keys at once (Space plays)',pl2=='true',pl2);pg.keyboard.press('Space')
        ck(f'{key} test: no console errors',errs==[],errs);cx.close()
    # ---- 4. the random pick ----
    cx,pg,errs=page(b,1280,720,None);pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.__T&&window.__T.gone",timeout=120000)
    N=60000;r=pg.evaluate("N=>{const c={},tr={};let last=localStorage.getItem('audiolab-splash-last'),rep=0;for(let i=0;i<N;i++){const k=SPLBG.pick();if(k===last)rep++;c[k]=(c[k]||0)+1;if(last==='spec')tr[k]=(tr[k]||0)+1;last=k}return{c,rep,tr,w:SPLBG.SPEC_CHANCE}}",N)
    # expected long-run shares with "never twice in a row": the stationary shares of the chain (weights 1,1,1,1,w; the last one left out)
    w=[1,1,1,1,r['w']];P=[[0 if i==j else w[j]/(sum(w)-w[i]) for j in range(5)] for i in range(5)];v=[.2]*5
    for _ in range(500):v=[sum(v[i]*P[i][j] for i in range(5)) for j in range(5)]
    got=[r['c'].get(k,0)/N for k in KINDS];print('  shares over',N,'picks:',{k:round(x,4) for k,x in zip(KINDS,got)},'expected',[round(x,4) for x in v],'spectrogram to each other:',round(got[4]/(sum(got[:4])/4),3))
    ck('pick: never the same twice in a row',r['rep']==0,r['rep'])
    ck('pick: the four share equally, the spectrogram about a third as often',all(abs(got[i]-v[i])<.012 for i in range(5)) and abs(r['w']-1/3)<1e-9 and .3<got[4]/(sum(got[:4])/4)<.48,got)
    seq=[]
    for i in range(14):
        pg.goto('https://app.test/index.html');pg.wait_for_function("()=>document.getElementById('splash')&&document.getElementById('splash').dataset.sp",timeout=120000);seq.append(pg.evaluate("document.getElementById('splash').dataset.sp"))
    print('  14 real starts:',seq);ck('real starts: never the same picture twice in a row, more than two different ones',all(seq[i]!=seq[i+1] for i in range(13)) and len(set(seq))>2,seq)
    ck('pick test: no console errors',errs==[],errs);cx.close()
    # ---- 5. frame rate, the freeze gate, Show now ----
    cx,pg,errs=page(b,1600,1000,'dipole',ui='{lat3:1,splash:false}');pg.goto('https://app.test/index.html');pg.wait_for_timeout(6000)
    ck('splash switched off in Settings: none at the start, no picture running',pg.evaluate("!document.getElementById('splash')&&!SPLBG.running()"))
    R(pg,"(()=>{const c=document.getElementById('liteNote');if(c)c.remove()})()")
    for kind in KINDS:
        pg.evaluate("k=>localStorage.setItem('audiolab-splash-test',k)",kind);R(pg,"showSplash('pv')");pg.wait_for_timeout(300)
        res={}
        for lite in (False,True):
            pg.evaluate("l=>{document.body.classList.toggle('lite',l);document.body.classList.toggle('fxstill',l)}",lite);pg.wait_for_timeout(200)
            a=pg.evaluate("()=>new Promise(r=>{const f0=SPLBG.frames(),t0=performance.now();let n=0;const f=()=>{n++;if(performance.now()-t0<2000)requestAnimationFrame(f);else r({fr:SPLBG.frames()-f0,scr:n,ms:performance.now()-t0})};requestAnimationFrame(f)})");res[lite]=a
        cost=pg.evaluate("()=>{const s=document.getElementById('splash'),t=performance.now();for(let i=0;i<200;i++)SPLBG.attach(s);return(performance.now()-t)/200}")
        r0,r1=res[False],res[True];print(f'  {kind}: {r0["fr"]/r0["ms"]*1000:.1f} pictures a second ({r0["scr"]/r0["ms"]*1000:.1f} screen frames), lighter looks {r1["fr"]/r1["ms"]*1000:.1f}; one picture {cost:.3f} ms at 1600x1000')
        ck(f'{kind}: at most 60 pictures a second, at most 30 in the lighter looks',r0['fr']/r0['ms']*1000<=61 and r0['fr']>20 and r1['fr']/r1['ms']*1000<=31.5,[r0,r1])
        ck(f'{kind}: Light mode: the picture stands still (task LK, M3: no ambient motion in Light mode)',r1['fr']<=1,r1)
        pg.evaluate("()=>{document.body.classList.remove('lite');document.body.classList.remove('fxstill')}");pg.wait_for_timeout(100)
        if kind=='dipole':
            g=pg.evaluate("()=>{const s=document.getElementById('splash');return{hint:s.querySelector(':scope>p').textContent,bar:getComputedStyle(s.querySelector('em')).transform,sp1:s.classList.contains('sp1')}}");ck('Show now: the same card, bar full, "Click to close"',g['sp1'] and g['hint']=='Click to close' and g['bar'] in('none','matrix(1, 0, 0, 1, 0, 0)'),g)
            a=pg.evaluate("()=>new Promise(r=>{const A=window.AudioLab.run('AO');A.gate=true;const f0=SPLBG.frames();setTimeout(()=>{const f1=SPLBG.frames();A.open();setTimeout(()=>r([f1-f0,SPLBG.frames()-f1]),600)},700)})") if R(pg,"typeof AO")=='object' else None
            ck('background freeze (the app\'s frame gate shut): the picture stops, and runs again when it opens',a is not None and a[0]<=1 and a[1]>5,a)
        pg.mouse.click(800,500);pg.wait_for_timeout(500);ck(f'{kind}: Show now closes on a click, picture stopped',pg.evaluate("!document.getElementById('splash')&&!SPLBG.running()"))
    ck('preview tests: no console errors',errs==[],errs);cx.close()
    # ---- 6. reduce motion: one still picture ----
    cx,pg,errs=page(b,1280,720,'harm',reduced_motion='reduce');pg.goto('https://app.test/index.html');pg.wait_for_function(RDY,timeout=90000);R(pg,"clearTimeout(SP1.tm)");f0=pg.evaluate("SPLBG.frames()");pg.wait_for_timeout(800);f1=pg.evaluate("SPLBG.frames()");g=pg.evaluate(GEO)
    ck('reduce motion: a finished still picture, no frames after it',f1==f0 and g['drawn']>300 and not pg.evaluate("SPLBG.running()"),[f0,f1,g['drawn']]);pg.locator('#splash').screenshot(path=os.path.join(out,'sp1_harm_still.png'));ck('reduce motion: no console errors',errs==[],errs);cx.close()
    # ---- 7. About is untouched; the splash while a project is opened inside the app leaves right after loading ----
    cx,pg,errs=page(b,1600,1000,'moons');pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.__T&&window.__T.gone",timeout=120000);pg.wait_for_timeout(500)
    R(pg,"showSplash(true)");pg.wait_for_timeout(600);g=pg.evaluate("()=>{const s=document.getElementById('splash');return{ab:s.classList.contains('ab'),sp1:s.classList.contains('sp1'),run:SPLBG.running(),cv:s.querySelector('canvas').width}}")
    ck('About: still its own window with the atom, no splash picture',g['ab'] and not g['sp1'] and not g['run'] and g['cv']>100,g);pg.keyboard.press('Escape');pg.wait_for_timeout(900)
    pg.evaluate("()=>{window.__T={};}");R(pg,"withSplash(()=>{})");pg.wait_for_function("()=>window.__T&&window.__T.gone",timeout=60000);T=pg.evaluate("window.__T");h=R(pg,"SP1.holdOpen")
    print(f'  splash inside the running app: up for {T["out"]-T["show"]:.0f} ms, no hold (constant {h})');ck('splash inside the running app: no extra hold, no "Click to continue", closes by itself',h==0 and 'rdy' not in T and T['out']-T['show']<1400 and not pg.evaluate("SPLBG.running()"),T)
    ck('About and in-app splash: no console errors',errs==[],errs);cx.close()
    b.close()
print(f'{n[0]-len(fails)} of {n[0]} checks pass');print('FAILED:',fails) if fails else None
