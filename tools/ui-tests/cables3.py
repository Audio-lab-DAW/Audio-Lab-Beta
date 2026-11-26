# mixer cables v0.195 (task S2): split drag keeps the window size, bottom edge changes only the cable area, corner and edges resize the window,
# 2 / 8 / 20 cables at small and large heights, animation, frame time.   python3 tools/ui-tests/cables3.py index.html [outdir]
import sys,json,os
from playwright.sync_api import sync_playwright
f=sys.argv[1] if len(sys.argv)>1 else 'index.html';out=sys.argv[2] if len(sys.argv)>2 else '.'
def boot(p,w=1600,h=1000):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs
SETUP="""(n=>{for(const t of S.tracks){delete t.grp;t.sends={};t.fx=t.fx.filter(f=>f.type!=='side');t.mods=[]}
 const T=S.tracks.filter(t=>t.kind!=='return'&&t.kind!=='group'),Rt=S.tracks.filter(t=>t.kind==='return'),Gp=S.tracks.filter(t=>t.kind==='group');let k=0,i=0;
 while(k<n&&i<200){const a=T[i%T.length],m=i%5;i++;
  if(m===0&&Rt.length){const r=Rt[i%Rt.length];if(!a.sends[r.id]){a.sends[r.id]=.3+.1*(i%6);k++}}
  else if(m===1&&Gp.length){const g=Gp[i%Gp.length];if(!a.grp&&a!==g){a.grp=g.id;k++}}
  else if(m===2){const b=T[(i*7+3)%T.length];if(b!==a&&!(b.mods||[]).some(x=>x.p.src===a.id)){const q=modNew('side');q.p.src=a.id;q.routes.push({pid:'t:'+b.id+':vol',d:.5});b.mods.push(q);k++}}
  else if(m===3){const b=T[(i*5+1)%T.length];if(b!==a){const q=modNew('lfo');q.routes.push({pid:'t:'+b.id+':pan',d:.4});a.mods.push(q);k++}}
  else{const b=T[(i*3+2)%T.length];if(b!==a&&!b.fx.some(f=>f.type==='side')){const x=mkFx('side');x.p.src=a.id;b.fx.push(x);k++}}}
 renderMixer();changed(true);return cabList().length})"""
def info(R): return json.loads(R("JSON.stringify((()=>{const w=document.getElementById('mixWin'),ms=w.querySelector('.mxs'),mx=ms.querySelector('.mx');return{win:[w.offsetLeft,w.offsetTop,w.offsetWidth,w.offsetHeight],lay:cabH(),tot:cs2T(),strip:mx.offsetHeight,cables:cabList().length,labels:w.querySelectorAll('svg.cabs .clab').length,rows:new Set([...w.querySelectorAll('svg.cabs .ctr')].map(p=>/ ([\\d.]+)(?:H|Q)/.exec(p.getAttribute('d'))?.[1])).size}})())"))
with sync_playwright() as p:
    b,pg,errs=boot(p);R=lambda c:pg.evaluate("c=>window.AudioLab.run(c)",c)
    print('load errors',errs)
    R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();openMixer()})()");pg.wait_for_timeout(1500)
    shot=lambda n:pg.screenshot(path=os.path.join(out,n+'.png'),clip=json.loads(R("JSON.stringify((()=>{const r=document.getElementById('mixWin').getBoundingClientRect();return{x:Math.max(0,r.left-4),y:Math.max(0,r.top-40),width:Math.min(1600,r.width+8),height:Math.min(1000-Math.max(0,r.top-40),r.height+50)}})())")))
    i0=info(R);print('start',i0)
    # 1. drag the top grip up: window unchanged
    g=pg.locator('#mixWin .cabrz').bounding_box()
    for dy in (60,200):
        pg.mouse.move(g['x']+600,g['y']+3);pg.mouse.down();pg.mouse.move(g['x']+600,g['y']+3-dy,steps=10);pg.mouse.up();pg.wait_for_timeout(600)
        i1=info(R);print('grip up',dy,i1,'window same:',i1['win']==i0['win']);g=pg.locator('#mixWin .cabrz').bounding_box()
    shot('s2_grip_up')
    # 2. bottom edge: only the cable area, channels keep their size
    s0=info(R);bb=pg.locator('#mixWin>.rz-s').bounding_box()
    pg.mouse.move(bb['x']+400,bb['y']+3);pg.mouse.down();pg.mouse.move(bb['x']+400,bb['y']+3+120,steps=10);pg.mouse.up();pg.wait_for_timeout(600)
    s1=info(R);print('bottom down',s1,'strip same:',s1['strip']==s0['strip'],'cable +',s1['tot']-s0['tot'],'window +',s1['win'][3]-s0['win'][3])
    bb=pg.locator('#mixWin>.rz-s').bounding_box();pg.mouse.move(bb['x']+400,bb['y']+3);pg.mouse.down();pg.mouse.move(bb['x']+400,bb['y']+3-80,steps=10);pg.mouse.up();pg.wait_for_timeout(600)
    s2=info(R);print('bottom up',s2,'strip same:',s2['strip']==s0['strip'])
    # 3. corner and other edges resize the whole window
    for k,dx,dy in (('se',-60,40),('n',0,-30),('w',-40,0),('e',30,0),('sw',20,20)):
        a=info(R);bx=pg.locator('#mixWin>.rz-'+k).bounding_box();x,y=bx['x']+bx['width']/2,bx['y']+bx['height']/2
        pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x+dx,y+dy,steps=8);pg.mouse.up();pg.wait_for_timeout(700);c=info(R)
        print('edge',k,'win',a['win'],'->',c['win'],'cable',a['tot'],'->',c['tot'])
    R("mxsSet('cabH',0)");pg.wait_for_timeout(500)
    # 4. 2, 8, 20 cables, small and large, while playing
    R("(()=>{pmSetOn(false);pos=64;start()})()");pg.wait_for_timeout(1500)
    for n in (2,8,20):
        print('cables',n,R(SETUP+"(%d)"%n));pg.wait_for_timeout(700)
        for h,nm in ((0,'auto'),(46,'small'),(260,'large')):
            R("mxsSet('cabH',%d)"%h);pg.wait_for_timeout(900);print(' ',nm,info(R));shot('s2_%d_%s'%(n,nm))
    # animation is moving
    st=R("JSON.stringify(CS2.an.map(a=>a.k+':'+a.s).slice(0,12))");pg.wait_for_timeout(300);st2=R("JSON.stringify(CS2.an.map(a=>a.k+':'+a.s).slice(0,12))");print('anim',st,'\n     ',st2,'idle',R("CS2.idle"))
    # frame time: playing with the mixer open (cables animating) and closed
    FT="new Promise(r=>{let n=0,t0=performance.now();const f=()=>{if(++n<120)requestAnimationFrame(f);else r(((performance.now()-t0)/120).toFixed(2))};requestAnimationFrame(f)})"
    TK="(()=>{let s=0,n=0;const o=cs2Tick;cs2Tick=function(){const t=performance.now();const r=o.apply(this,arguments);s+=performance.now()-t;n++;return r};return new Promise(r=>setTimeout(()=>{cs2Tick=o;r((s/Math.max(1,n)).toFixed(3)+' ms x'+n)},2000))})()"
    print('frame open',pg.evaluate(FT),'cs2Tick',R(TK))
    R("document.querySelector('#mixWin .fwc').click()");pg.wait_for_timeout(500)
    print('frame closed',pg.evaluate(FT),'cs2Tick closed',R(TK))
    R("stop()")
    print('errors',errs);b.close()
