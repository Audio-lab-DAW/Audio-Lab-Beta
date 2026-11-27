"""Task SQ1 (sound quality, lane N): the Quality switch (shown as one on/off switch "Hi-Fi", the user's naming), per device and per
song, and the DC blocker after biased shapers (Q10) as the first Hi-Fi feature. Internally off = 'classic', on = 'clean'.
Checks: the open song (Fractals) is Classic and no device is stamped when a song opens; the mirror p._sq is never saved (not in JSON,
not in Object.keys); a new device is Clean; in a song set to Classic by hand a new device is Classic; the Soft Clipper's Classic output is
bit-identical to the device without the switch, at Asymmetry 0, 25 and 50 %; the DC measured at its output (110 Hz sine at -4.4 dBFS,
+12 dB, research doc section 3) falls from about -24 / -18 dBFS to under -90 dBFS in Clean and the sine's level stays within 0.05 dB;
the live node follows the switch; the Hi-Fi switch with its short line at the bottom of the device's controls (text, line, tooltip,
click, undo, right-click menu, inside the device); "Hi-Fi everywhere" and back in one undo step each; Settings > Project > Hi-Fi (the
switch, its line, the one-time note for an older song, counts, buttons, search); a song from the New project window starts with Hi-Fi
on; dark and Light level; no console errors.
  python3 tools/ui-tests/taskSQ1.py [repo dir] [out dir]"""

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
def ctx(b,lite):
    c=b.new_context(viewport={'width':1600,'height':1000});pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:300]));pg.on('console',lambda m:m.type=='error' and 'fetching the script' not in m.text and 'net::' not in m.text and 'icons.json' not in m.text and errs.append('console '+m.text[:200]))
    pg.route('https://app.test/**',serve)
    u=dict(order=['arr','fx','tr','map'],splash=False,lat3=1,lite=lite,liteMan=lite)
    pg.add_init_script("if(!sessionStorage.getItem('q1')){sessionStorage.setItem('q1','1');localStorage.setItem('audiolab-ui',JSON.stringify(%s))}"%json.dumps(u))
    pg.goto('https://app.test/index.html')
    pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=90000);pg.wait_for_timeout(2500)
    pg.evaluate("()=>{const n=document.getElementById('liteNote');n&&n.remove()}")
    return c,pg,errs
# the Soft Clipper offline: 110 Hz sine at -4.4 dBFS, 3 s; DC and level of the last second; Classic against the device without the switch
DCJS="""async([bias,q,raw])=>{const sr=48000,n=sr*3,c=new OfflineAudioContext(2,n,sr),b=c.createBuffer(1,n,sr),d=b.getChannelData(0),A=Math.pow(10,-4.4/20);
 for(let i=0;i<n;i++)d[i]=A*Math.sin(2*Math.PI*110*i/sr);const s=c.createBufferSource();s.buffer=b;
 const x=raw?AudioLab.run('SQ.raw')(c,'clip'):mkFxNode(c,'clip'),p=Object.assign(mkFx('clip').p,{gain:12,bias});if(q)p._sq=q;x.set(p);s.connect(x.in);x.out.connect(c.destination);s.start();
 const r=await c.startRendering(),o=r.getChannelData(0),a=sr*2;let m=0,e=0;for(let i=a;i<n;i++){m+=o[i];e+=o[i]*o[i]}m/=(n-a);e/=(n-a);
 let h=0;for(let i=0;i<n;i++){const u=new Uint32Array(new Float32Array([o[i]]).buffer)[0];h=(Math.imul(h,31)+u)|0}
 return{dc:20*Math.log10(Math.max(Math.abs(m),1e-12)),ac:10*Math.log10(Math.max(e-m*m,1e-24)),h}}"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    for lite in (False,True):
        L='light' if lite else 'dark'
        c,pg,errs=ctx(b,lite)
        ck(f'{L}: version',float(R(pg,"VERSION"))>=0.278)
        st=J(pg,"{p:sqProj(),sq:S.sq===undefined,q:sqDevs(S).filter(([d])=>sqOwnQ(d)||d[sqF(d)]!==undefined&&sqF(d)==='quality').length,n:sqDevs(S).length,clap:sqDevs(S).filter(([d])=>typeof d.q==='number').length}")
        ck(f'{L}: the open song is Classic and nothing is stamped when it opens',st['p']=='classic' and st['sq'] and st['q']==0 and st['n']>5 and st['clap']>0,st)
        m=J(pg,"(()=>{const f=sqDevs(S).find(([d,,k])=>k==='fx')[0];return{sq:f.p._sq,keys:Object.keys(f.p).includes('_sq'),json:JSON.stringify(f.p).includes('_sq'),undo:undoSnap().includes('_sq')}})()")
        ck(f'{L}: the mirror p._sq is there and never saved',m['sq']=='classic' and not m['keys'] and not m['json'] and not m['undo'],m)
        if not lite:
            res={}
            for bias in (0,25,50):
                k=pg.evaluate(DCJS,[bias,'classic',False]);r0=pg.evaluate(DCJS,[bias,None,True]);cl=pg.evaluate(DCJS,[bias,'clean',False])
                res[bias]=(k,cl);print(f'  Soft Clipper asymmetry {bias} %: DC Classic {k["dc"]:.1f} dBFS, Clean {cl["dc"]:.1f} dBFS; level {k["ac"]:.3f} / {cl["ac"]:.3f} dB')
                ck(f'Classic is bit-identical to the device without the switch (asymmetry {bias} %)',k['h']==r0['h'],(k,r0))
                if bias: ck(f'Clean: DC under -90 dBFS (asymmetry {bias} %; Classic {k["dc"]:.1f})',cl['dc']<-90 and k['dc']>-30,(k,cl))
                else: ck('Clean at asymmetry 0 is the same as Classic (no blocker)',cl['h']==k['h'],(k,cl))
                ck(f'Clean keeps the level (asymmetry {bias} %)',abs(cl['ac']-k['ac'])<.05,(k,cl))
        # a new device is Clean; the open song's devices stay as they were
        t=J(pg,"(()=>{const t=S.tracks.find(t=>t.kind!=='return'&&t.kind!=='group'&&t.inst);selT=t.id;pushUndo();const f=mkFx('clip');f.p.bias=25;t.fx.push(f);changed(true);return{id:t.id,f:f.id,q:f.q,old:sqDevs(S).filter(([d])=>d!==f&&sqOwnQ(d)).length}})()")
        ck(f'{L}: a new device is Clean and no other device changed',t['q']=='clean' and t['old']==0,t)
        R(pg,"ensureCtx();syncGraph();1");pg.wait_for_timeout(300)
        lv=lambda:J(pg,"(()=>{const N=NODES.get(%s),x=N&&N.fxm.get(%s);return x&&x.sqDc?x.sqDc():null})()"%(json.dumps(t['id']),json.dumps(t['f'])))
        ck(f'{L}: the live node has the DC blocker in Clean',lv()==True,lv())
        R(pg,"renderFx();1");pg.wait_for_timeout(400)
        sel="#fxin .dev[data-id='%s'] .sqrow .sqchip"%t['f']
        ch=pg.locator(sel)
        LN=lambda:J(pg,"(()=>{const D=document.querySelector(\"#fxin .dev[data-id='%s']\"),r=D.querySelector('.sqrow'),l=r&&r.querySelector('.sqln'),a=r&&r.getBoundingClientRect(),d=D.getBoundingClientRect();return r&&{line:l.textContent,vis:l.offsetWidth>0&&l.offsetHeight>0,inside:a.bottom<=d.bottom+1&&a.right<=d.right+1,rail:r.parentNode.classList.contains('dfs'),ar:r.querySelector('.sqchip').getAttribute('aria-checked'),title:!D.querySelector('.devh>.sqchip')}})()"%t['f'])
        ln=LN()
        ck(f'{L}: the Hi-Fi switch and its line sit at the bottom of the device controls',ch.count()==1 and ch.inner_text().strip()=='Hi-Fi' and ln and ln['line']=='Hi-Fi on: higher quality sound.' and ln['vis'] and ln['inside'] and ln['rail'] and ln['ar']=='true' and ln['title'] and 'DC blocker' in (ch.get_attribute('title') or '') and 'Hi-Fi off: lighter and faster' in (ch.get_attribute('title') or ''),(ch.count(),ln))
        others=J(pg,"[...document.querySelectorAll('#fxin .dev')].filter(D=>!D.querySelector('.sqchip')).length")
        ck(f'{L}: devices without a Hi-Fi sound have no switch',others>0,others)
        ui=J(pg,"[...document.querySelectorAll('#fxin .sqrow,#fxin .sqchip')].map(e=>e.textContent+' '+(e.title||'')).join(' ')")
        ck(f'{L}: no Classic or Clean in the interface, no em dash',not any(w in ui for w in ('Classic','Clean','\u2014')),ui)
        if ch.count():
            ch.scroll_into_view_if_needed();pg.locator('#fxin').screenshot(path=f'{OUT}/sq1_chip_{L}.png')
            ch.click();pg.wait_for_timeout(300)
            q=J(pg,"S.tracks.flatMap(t=>t.fx).find(f=>f.id===%s).q"%json.dumps(t['f']))
            ln=LN()
            ck(f'{L}: a click turns Hi-Fi off on the device',q=='classic' and ln['ar']=='false' and ln['line'].startswith('Hi-Fi off: lighter and faster') and lv()==False,(q,ln,lv()))
            R(pg,"undo();1");pg.wait_for_timeout(300)
            q=J(pg,"S.tracks.flatMap(t=>t.fx).find(f=>f.id===%s).q"%json.dumps(t['f']));R(pg,"syncGraph();1")
            ck(f'{L}: undo turns Hi-Fi on again',q=='clean' and lv()==True,(q,lv()))
            R(pg,"renderFx();1");pg.wait_for_timeout(300);pg.locator(sel).click(button='right');pg.wait_for_timeout(300)
            mn=J(pg,"[...document.querySelectorAll('#ctxm .mlab')].map(e=>e.firstChild.textContent)")
            ck(f'{L}: the right-click menu',all(x in mn for x in ['Hi-Fi on','Hi-Fi off','Hi-Fi everywhere','Hi-Fi off everywhere']),mn)
            pg.keyboard.press('Escape');pg.wait_for_timeout(200)
        # the whole song, one undo step each
        n0=R(pg,"UNDO.length")
        a=J(pg,"(sqUseAll('clean'),{p:S.sq,all:sqDevs(S).every(([d])=>sqOwnQ(d)==='clean'),u:UNDO.length})")
        ck(f'{L}: Hi-Fi everywhere sets the song and every device in one undo step',a['p']=='clean' and a['all'] and a['u']==n0+1,a)
        R(pg,"undo();1");pg.wait_for_timeout(200)
        a=J(pg,"{p:S.sq===undefined,n:sqDevs(S).filter(([d])=>sqOwnQ(d)).length,c:sqProj()}")
        ck(f'{L}: one undo brings the song back as it was',a['p'] and a['n']==1 and a['c']=='classic',a)
        # a song set to Classic by hand: new devices are Classic
        R(pg,"(sqUseAll('classic'),1)")
        q=J(pg,"(()=>{const t=curT();pushUndo();const f=mkFx('drive');t.fx.push(f);changed(true);return f.q})()")
        ck(f'{L}: in a song set to Hi-Fi off by hand a new device has Hi-Fi off',q=='classic',q)
        R(pg,"undo();undo();1");pg.wait_for_timeout(200)
        # Settings > Project
        R(pg,"openSettings('files')");pg.wait_for_timeout(600)
        s=J(pg,"(()=>{const c=document.getElementById('sqCard');return c&&{h:c.querySelector('h4').textContent,v:$('#sqProj').checked,ln:$('#sqLine').textContent,old:$('#sqOld').hidden?'':$('#sqOld').textContent,st:$('#sqStat').textContent,b:[...c.querySelectorAll('button')].map(b=>[b.textContent,!!b.title]),vis:c.offsetWidth>0,find:SETT.find('hi-fi').includes('songHiFi')&&SETT.find('sound quality').includes('songHiFi'),tip:!!c.querySelector('label.chk').title}})()")
        ck(f'{L}: Settings > Project has the Hi-Fi card with its line',s and s['h']=='Hi-Fi' and s['v']==False and s['ln']=='Hi-Fi off: lighter and faster, good for slower computers or big projects.' and s['vis'] and s['find'] and s['tip'] and all(x[1] for x in s['b']) and [x[0] for x in s['b']]==['Hi-Fi everywhere','Hi-Fi off everywhere'] and '1 on' in s['st'],s)
        ck(f'{L}: an older song shows the note once',s and s['old']=='This song was made before Hi-Fi mode was implemented, so it plays as you made it. Turn Hi-Fi on for higher quality.',s and s['old'])
        pg.locator('#sqCard').screenshot(path=f'{OUT}/sq1_settings_{L}.png')
        pg.check('#sqProj');pg.wait_for_timeout(300)
        a=J(pg,"{p:S.sq,o:sqDevs(S).filter(([d])=>!sqOwnQ(d)).every(([d])=>sqOf(d)==='clean')}")
        ck(f'{L}: the switch sets the song; devices without their own choice follow',a['p']=='clean' and a['o'] and J(pg,"$('#sqLine').textContent")=='Hi-Fi on: higher quality sound.',a)
        R(pg,"undo();1");pg.wait_for_timeout(300)
        ck(f'{L}: undo of the switch',J(pg,"[S.sq===undefined,$('#sqProj').checked]")==[True,False])
        pg.click('#sqAllC');pg.wait_for_timeout(300)
        ck(f'{L}: Hi-Fi everywhere in Settings',J(pg,"S.sq==='clean'&&sqDevs(S).every(([d])=>sqOwnQ(d)==='clean')&&/ on, 0 off/.test($('#sqStat').textContent)"))
        R(pg,"undo();1");pg.keyboard.press('Escape');pg.wait_for_timeout(300);R(pg,"$('#set').hidden=true;1")
        # the command list
        ck(f'{L}: commands',J(pg,"SCM.has('sq.cleanAll')&&SCM.has('sq.classicAll')"))
        # New project window: Clean
        R(pg,"(npOpen(),1)");pg.wait_for_timeout(300);pg.click('#npGo');pg.wait_for_timeout(2500)
        ck(f'{L}: a song from the New project window starts with Hi-Fi on',J(pg,"[S.sq,sqProj()]")==['clean','clean'])
        R(pg,"openSettings('files')");pg.wait_for_timeout(600)
        ck(f'{L}: a new song shows no older-song note, the switch is on',J(pg,"[$('#sqOld').hidden,$('#sqProj').checked]")==[True,True])
        R(pg,"switchProject(PJ.list[0].id);1");pg.wait_for_timeout(1500);R(pg,"openSettings('files')");pg.wait_for_timeout(600)
        ck(f'{L}: the older song note does not come back',J(pg,"[S.sq===undefined,$('#sqOld').hidden]")==[True,True],J(pg,"[S.sq,S.sqSeen,$('#sqOld').hidden]"))
        R(pg,"$('#set').hidden=true;1")
        ck(f'{L}: no console errors',not errs,errs)
        c.close()
    b.close()
print(f'taskSQ1: {N[1]} of {N[0]} checks passed'+('' if not FAIL else '; FAILED: '+', '.join(FAIL)))
sys.exit(1 if FAIL else 0)
