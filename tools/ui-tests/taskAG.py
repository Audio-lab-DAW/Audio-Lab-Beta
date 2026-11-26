# task AG (v0.210): mixer flicker and the sidechain window layout.
#   python3 tools/ui-tests/taskAG.py index.html [outdir]
# 1. while playing (and stopped), turn a device (a neutral Imager added for the test, so the sound itself does not change) on and off in a mixer channel; every frame record the channel's picture (same canvas element,
#    sum of its pixels), its level meter (clip of the fader meter) and the master loudness read-out: no blank frame, no full meter, no jump
#    bigger than the music's own movement. Also a mute click (a full mixer rebuild) keeps the pictures.
# 2. the sidechain window: screenshots stopped (preview of one duck) and playing; Remove, then Undo brings it back with its window.
import sys,os,json
from playwright.sync_api import sync_playwright
f=sys.argv[1] if len(sys.argv)>1 else 'index.html';out=sys.argv[2] if len(sys.argv)>2 else '.'
def boot(p,w=1600,h=1000,dsf=1):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h},device_scale_factor=dsf);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text and 'fetching the script' not in m.text else None)
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b''))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs,(lambda c:pg.evaluate("c=>window.AudioLab.run(c)",c))
REC="""(()=>{const t=window.__T;window.__rec=[];const gen=window.__gen=(window.__gen|0)+1;let n=0;
 const step=()=>{n++;const st=document.querySelector('#mixWin .mx[data-id="'+t.id+'"]'),cv=st&&st.querySelector('canvas.mxv'),fm=st&&st.querySelectorAll('.fm u');let sum=-1;
  if(cv&&cv.width>1){const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;sum=0;for(let i=0;i<d.length;i+=4)sum+=d[i]+d[i+1]+d[i+2]}
  const H=MXH.get(t.id),pk=H?Math.max(H.l[H.i],H.r[H.i]):-1,lu=document.getElementById('mxLu');
  window.__rec.push({n,id:cv?(cv.__id||(cv.__id=Math.random().toString(36).slice(2,7))):'-',sum,clip:fm&&fm[0]?fm[0].style.clipPath:'none',pk,lu:lu?lu.textContent:'',ms:(()=>{const m=document.querySelector('#mixWin .mxs');return m?(m.__id||(m.__id=Math.random().toString(36).slice(2,7))):'-'})(),tg:window.__tg|0});
  if(n<%d&&window.__gen===gen)requestAnimationFrame(step)};requestAnimationFrame(step);
 const tog=()=>{window.__tg=(window.__tg|0)+1;const b=document.querySelector('#mixWin .mx[data-id="'+t.id+'"] .slot[data-fid="'+window.__F+'"] .pw');b.click()};
 %s})()"""
def run(R,pg,frames,acts,wait):
    R(REC%(frames,acts));pg.wait_for_timeout(wait);return json.loads(R("JSON.stringify(window.__rec)"))
def judge(rec,label,view):  # the meter view draws its own meter, the fader meter is not used there
    ids={r['id'] for r in rec};blank=[r['n'] for r in rec if r['sum']==0];full=[r['n'] for r in rec if r['clip'] in ('','none')] if view!='meter' else [];dash=[r['n'] for r in rec if r['lu']=='–']
    d=[abs(rec[i]['sum']-rec[i-1]['sum']) for i in range(1,len(rec))];tg=[i for i in range(1,len(rec)) if rec[i]['tg']!=rec[i-1]['tg']]
    near=set(j for i in tg for j in range(i-2,i+4) if 0<j<len(rec));dn=[d[j-1] for j in near];df=sorted(d[j-1] for j in range(1,len(rec)) if j not in near)
    ref=df[-1] if df else 0;pz=[r['n'] for r in rec if r['pk']==0 and any(q['pk']>0 for q in rec)]
    print('  %s: %d frames, toggles %d, canvas elements %d, blank frames %s, full or empty meter frames %s, loudness dashes %s'%(label,len(rec),len(tg),len(ids),blank,full,dash))
    print('    biggest picture change next to a toggle %d, the biggest change from the music alone %d: %s'%(max(dn) if dn else 0,ref,'OK' if (not dn or max(dn)<=ref*1.05) and len(ids)==1 and not blank and not full else 'CHECK'))
    print('    peak per frame around the first toggle:',[round(r['pk'],3) for r in rec[max(0,tg[0]-4):tg[0]+6]] if tg else '-')
with sync_playwright() as p:
    b,pg,errs,R=boot(p);print('load errors',errs,'version',R("VERSION"))
    for view in ('stereo','meter'):
        R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();UI.mxView='%s';for(const t of S.tracks)delete t.mxv;openMixer();renderMixer()})()"%view);pg.wait_for_timeout(800)
        R("(()=>{stop();pos=72;start()})()");pg.wait_for_timeout(1500)
        nm=R("(()=>{let b=null,v=-1;for(const t of S.tracks){const N=NODES.get(t.id);if(!N||!t.fx.length||t.kind==='group'||t.kind==='return')continue;const v2=peakOf(N.aL);if(v2>v){v=v2;b=t}}window.__T=b;const q=mkFx('imager');b.fx.push(q);window.__F=q.id;changed(true);renderMixer();return b.name+' ('+b.fx.map(f=>f.type).join(', ')+')'})()")
        print(view,'view, playing, channel',nm,'+ a neutral Imager that is turned off and on')
        rec=run(R,pg,90,"setTimeout(tog,1500);setTimeout(tog,3000);",6500);judge(rec,'device off and on, playing',view)
        print('    full mixer rebuilds during the two toggles:',len({r['ms'] for r in rec})-1,'| the Imager slot is on again:',R("__T.fx.find(f=>f.id===__F).on"),R("!document.querySelector('#mixWin .slot[data-fid=\"'+__F+'\"]').classList.contains('off')"))
        R("stop()");pg.wait_for_timeout(600)
        rec=run(R,pg,70,"setTimeout(tog,800);setTimeout(tog,1800);",4500);judge(rec,'device off and on, stopped',view)
        R("(()=>{pos=72;start()})()");pg.wait_for_timeout(1200)
        rec=run(R,pg,70,"setTimeout(()=>{window.__tg=1;document.querySelector('#mixWin .mx[data-id=\"'+window.__T.id+'\"] [data-a=mute]').click()},1500);setTimeout(()=>{window.__tg=2;document.querySelector('#mixWin .mx[data-id=\"'+window.__T.id+'\"] [data-a=mute]').click()},2800);",5500)
        ids={r['id'] for r in rec};print('  mute on and off (a full mixer rebuild): canvas elements',len(ids),'blank frames',[r['n'] for r in rec if r['sum']==0],'full meter frames',[r['n'] for r in rec if r['clip'] in ('','none')] if view!='meter' else '(meter view)')
        R("stop()")
    print('errors so far',errs)
    b.close()
    b,pg,errs,R=boot(p,dsf=2)
    R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove();openMixer()})()");pg.wait_for_timeout(800)
    R("(()=>{const k=S.tracks.find(t=>t.name==='Kick'),q=S.tracks.find(t=>/Pad/.test(t.name))||S.tracks.find(t=>t.name==='Bass');window.__P=q;window.__D=abxMake(k,q)})()");pg.wait_for_timeout(500)
    box=lambda:json.loads(R("JSON.stringify(document.querySelector('.abxw').getBoundingClientRect())"))
    shot=lambda n:(lambda r:pg.screenshot(path=os.path.join(out,n),clip={'x':r['x']-8,'y':r['y']-8,'width':r['width']+16,'height':r['height']+16}))(box())
    shot('ag_window_stopped.png');R("(()=>{pos=72;start()})()");pg.wait_for_timeout(2500);shot('ag_window_playing.png')
    print('window sections:',R("JSON.stringify([...document.querySelectorAll('.abxw .agsh b')].map(e=>e.textContent))"),'| footer:',R("JSON.stringify([...document.querySelectorAll('.abxw .agft button')].map(e=>e.textContent.trim()))"))
    print('controls without a tooltip:',R("[...document.querySelectorAll('.abxw button,.abxw [data-c]')].filter(e=>!e.title).length"))
    u0=R("UNDO.length");pg.locator('.abxw .agrm').click();pg.wait_for_timeout(300)
    print('Remove: Ducker on',R("__P.name"),'still there:',R("__P.fx.includes(__D)||__P.fx.some(f=>f.id===__D.id)"),'| window open:',R("!!document.querySelector('.abxw')"),'| undo bar:',repr(R("(document.querySelector('#agUndo span')||{}).textContent")),'| undo steps',R("UNDO.length")-u0)
    r=json.loads(R("JSON.stringify(document.getElementById('agUndo').getBoundingClientRect())"));pg.screenshot(path=os.path.join(out,'ag_undo.png'),clip={'x':r['x']-8,'y':r['y']-8,'width':r['width']+16,'height':r['height']+16})
    pg.locator('#agUndo button').first.click();pg.wait_for_timeout(400)
    print('Undo: Ducker back:',R("trkById(__P.id).fx.some(f=>f.id===__D.id)"),'| window open again:',R("!!document.querySelector('.abxw')"),'| undo bar gone:',R("!document.getElementById('agUndo')"))
    pg.locator('.abxw [data-w="on"]').click();pg.wait_for_timeout(300);print('Pause: Ducker on =',R("trkById(__P.id).fx.find(f=>f.id===__D.id).on"),'| text:',repr(R("document.querySelector('.abxw .abxwt').textContent")));shot('ag_window_paused.png')
    pg.locator('.abxw [data-w="on"]').click();pg.wait_for_timeout(200)
    pg.locator('.abxw [data-fo="band"]').click();pg.wait_for_timeout(200);print('Listen to Band: focus slider shown',R("!!document.querySelector('.abxw .agff .hb')"))
    print('errors',errs);b.close()
