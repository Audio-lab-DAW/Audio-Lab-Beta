# mixer volume read-outs and fader sizing after every redraw: python3 tools/ui-tests/mixnums.py index.html [outdir]
import sys,json,os
from playwright.sync_api import sync_playwright
F=sys.argv[1] if len(sys.argv)>1 else 'index.html';OUT=sys.argv[2] if len(sys.argv)>2 else '.';os.makedirs(OUT,exist_ok=True)
def boot(p,f=F,scale=1,w=1600,h=1000,ui='{splash:false,lat3:1}'):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h},device_scale_factor=scale);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify(%s))"%ui)
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs
def run(pg,code): return pg.evaluate("c=>window.AudioLab.run(c)",code)
# what is on screen right now: how many read-outs are empty or wrong, fader height, lane height
B="const w=document.getElementById('mixWin'),ms=w.querySelector('.mxs'),os=[...w.querySelectorAll('.mxf output')],want=o=>o.dataset.o==='master'?SPEC_MASTER.f(S.master):SPEC_VOL.f((S.tracks.find(t=>t.id===o.dataset.o)||{}).vol);const p=ms.querySelector('.mx'),M=ms.querySelector('.mx.master');return [os.length,os.filter(o=>!o.textContent).length,os.filter(o=>o.textContent!==want(o)).length,os[0].textContent,os[os.length-1].textContent,'var '+ms.style.getPropertyValue('--fh'),'fader '+p.querySelector('.fwrap').offsetHeight+'/'+M.querySelector('.fwrap').offsetHeight,'num '+os[0].offsetHeight,'lane '+(w.classList.contains('mxcab')?w.style.getPropertyValue('--cabh'):'off'),'strip '+p.offsetHeight,M.classList.contains('mxtight')?'tight':'',w.classList.contains('mxcmp')?'compact':''].join(' | ')"
now=lambda pg:run(pg,"(()=>{"+B+"})()")
do=lambda pg,js:run(pg,"(()=>{"+js+";"+B+"})()")   # do it and read in the same instant, before any repaint
def rounds(pg,tag):
    for name,js in [('renderMixer','renderMixer()'),('fit again','mxFit()'),('select track','selT=S.tracks[2].id;renderMixer()'),('select master',"selT='__m';renderMixer()"),
        ('add track',"pushUndo();const c=JSON.parse(JSON.stringify(S.tracks[1]));c.id='zz'+Date.now();c.vol=.5;S.tracks.push(c);changed(true);renderMixer()"),
        ('remove track','pushUndo();S.tracks.pop();changed(true);renderMixer()'),('undo','undo()'),('undo','undo()'),
        ('compact on',"document.getElementById('mxCmp').click()"),('compact off',"document.getElementById('mxCmp').click()"),
        ('fader moved',"S.tracks[0].vol=.25;S.master=-3;renderMixer()"),('back',"S.tracks[0].vol=.8;S.master=0;renderMixer()")]:
        a=do(pg,js);pg.wait_for_timeout(900);c=now(pg);run(pg,'mxFit()');pg.wait_for_timeout(300);d=now(pg)
        print('%-14s at once: %s\n%-14s later  : %s%s'%(name,a,'',c,'' if c==d else '\n               refit  : '+d+'   <-- CHANGED BY A SECOND FIT'))
with sync_playwright() as p:
    for mode in ['default','full']:
        b,pg,errs=boot(p);pg.evaluate("()=>{const c=document.getElementById('liteNote');if(c)c.remove()}")
        if mode=='full': run(pg,"(()=>{UI.lite=false;UI.liteMan=false;applyLite();UI.fx=fxPre('full');applyTrans()})()");pg.wait_for_timeout(500)
        print('=====',mode,'effects; body:',pg.evaluate("()=>document.body.className"))
        print('open           at once:',do(pg,"document.getElementById('mBtn').click()"));pg.wait_for_timeout(1500);print('               later  :',now(pg))
        print('--- cables',run(pg,"cabOn()?'on':'off'"));rounds(pg,'a')
        pg.screenshot(path=OUT+'/nums-%s-a.png'%mode)
        run(pg,"mxsSet('cab',cabOn()?0:1)");pg.wait_for_timeout(900)
        print('--- cables',run(pg,"cabOn()?'on':'off'"));rounds(pg,'b')
        pg.screenshot(path=OUT+'/nums-%s-b.png'%mode)
        run(pg,"mxsSet('cab',cabOn()?0:1)");pg.wait_for_timeout(600)
        print('errors',errs);b.close()
