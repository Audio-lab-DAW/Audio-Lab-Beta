# task AJ (v0.212): Shift-drag duplicates clips, arrow keys move the selected clips with a step that follows the zoom.
#   python3 tools/ui-tests/taskAJ.py index.html [outdir]
import sys,os,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
f=sys.argv[1] if len(sys.argv)>1 else 'index.html';out=sys.argv[2] if len(sys.argv)>2 else '.'
def boot(p,w=1600,h=1000):
    src=open(f,encoding='utf-8').read()
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':w,'height':h});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:400]));pg.on('console',lambda m:errs.append('C:'+m.text[:300]) if m.type=='error' and 'net::' not in m.text and '404' not in m.text and 'fetching the script' not in m.text else 0)
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script("if(!localStorage.getItem('audiolab-ui'))localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_timeout(9000)
    return b,pg,errs,(lambda c:pg.evaluate("c=>window.AudioLab.run(c)",c))
ok=True
JL=lambda v:json.loads(v) if isinstance(v,str) else v
def chk(name,cond,info=''):
    global ok;ok&=bool(cond);print(('PASS ' if cond else 'FAIL ')+name,info)
with sync_playwright() as p:
    b,pg,errs,R=boot(p);print('version',R("VERSION"),'load errors',errs)
    R("(()=>{const c=document.getElementById('liteNote');if(c)c.remove()})()")
    st=lambda:JL(R("JSON.stringify(S.tracks.map(t=>({n:t.name,k:t.kind,c:t.clips.map(c=>[+c.start.toFixed(4),c.len,!!c.notes,c.id])})))"))
    print([ (t['n'],t['k'],len(t['c'])) for t in st()][:12])
    # clip centre on screen
    pos=lambda cid:JL(R("(()=>{const f=findClip('%s');const i=S.tracks.indexOf(f.t),G=clipGeom(i,f.c),r=arr.getBoundingClientRect();return JSON.stringify({x:r.left+G.x,y:r.top+G.y,w:G.w,h:G.h})})()"%cid))
    R("(()=>{V.x=60;V.ppb=24;V.y=0;clampV();dirty=true})()");pg.wait_for_timeout(300)
    # find a MIDI clip visible (start>=64)
    info=JL(R("JSON.stringify((()=>{for(const t of S.tracks)for(const c of t.clips)if(c.notes&&c.start>=64&&c.start<80)return{id:c.id,t:t.name,s:c.start,l:c.len};return null})())"));print('clip',info)
    cid=info['id'];n0=JL(R("S.tracks.reduce((a,t)=>a+t.clips.length,0)"))
    P=pos(cid);cx,cy=P['x']+min(P['w']/2,40),P['y']+P['h']*.7
    # 1 plain click then shift-drag one clip by 8 beats
    pg.mouse.click(cx,cy);pg.keyboard.down('Shift');pg.mouse.move(cx,cy);pg.mouse.down();pg.mouse.move(cx+60,cy,steps=5);pg.mouse.move(cx+24*8,cy,steps=8);
    pg.screenshot(path=os.path.join(out,'aj_dragdup.png'))
    pg.mouse.up();pg.keyboard.up('Shift');pg.wait_for_timeout(200)
    n1=JL(R("S.tracks.reduce((a,t)=>a+t.clips.length,0)"));f0=JL(R("JSON.stringify(findClip('%s').c.start)"%cid))
    chk('shift-drag duplicates one clip: +1 clip, original stays',n1==n0+1 and abs(f0-info['s'])<1e-6,(n0,n1,f0))
    cp=JL(R("JSON.stringify(S.tracks.flatMap(t=>t.clips).filter(c=>c.id!=='%s'&&c.name===findClip('%s').c.name&&Math.abs(c.start-%f-8)<1e-6).length)"%(cid,cid,info['s'])));chk('copy is 8 beats later',cp>=1,cp)
    R("undo()");pg.wait_for_timeout(150);n2=JL(R("S.tracks.reduce((a,t)=>a+t.clips.length,0)"));chk('one Undo removes the duplicate',n2==n0,n2)
    R("redo()");pg.wait_for_timeout(150);chk('Redo brings it back',JL(R("S.tracks.reduce((a,t)=>a+t.clips.length,0)"))==n0+1)
    R("undo()");pg.wait_for_timeout(100)
    # 2 shift-click still toggles the selection
    R("selClear();selC=null");pg.mouse.click(cx,cy);pg.keyboard.down('Shift');pg.mouse.click(cx,cy);pg.keyboard.up('Shift');pg.wait_for_timeout(100)
    chk('shift-click still toggles selection (no duplicate)',JL(R("S.tracks.reduce((a,t)=>a+t.clips.length,0)"))==n0)
    # 3 multi-selection, group duplicate across tracks
    ids=JL(R("JSON.stringify((()=>{const o=[];for(const t of S.tracks)for(const c of t.clips)if(c.start>=64&&c.start<96&&o.length<3)o.push([c.id,c.start,S.tracks.indexOf(t)]);return o})())"))
    R("(()=>{selClear();for(const i of %s)SELCS.add(i);selC=%s;dirty=true})()"%(json.dumps([i[0] for i in ids]),json.dumps(ids[0][0])));pg.wait_for_timeout(200)
    P=pos(ids[0][0]);cx,cy=P['x']+min(P['w']/2,30),P['y']+P['h']*.7
    for off in (30,60,120,200,300,400):
        cx=P['x']+off;hit=R("(()=>{const r=arr.getBoundingClientRect(),H=arrHit(%f-r.left,%f-r.top);return H.c?H.c.id+'|'+H.zone:''})()"%(cx,cy))
        if hit=='%s|move'%ids[0][0]:break
    print('hit',hit);n0=JL(R("S.tracks.reduce((a,t)=>a+t.clips.length,0)"))
    pg.keyboard.down('Shift');pg.mouse.move(cx,cy);pg.mouse.down();pg.mouse.move(cx+50,cy,steps=4);pg.mouse.move(cx+24*4,cy,steps=6);pg.screenshot(path=os.path.join(out,'aj_dragdup_multi.png'));pg.mouse.up();pg.keyboard.up('Shift');pg.wait_for_timeout(200)
    n1=JL(R("S.tracks.reduce((a,t)=>a+t.clips.length,0)"));chk('group duplicate adds %d clips'%len(ids),n1==n0+len(ids),(n0,n1))
    orig=all(abs(JL(R("findClip('%s').c.start"%i[0]))-i[1])<1e-6 and JL(R("S.tracks.indexOf(findClip('%s').t)"%i[0]))==i[2] for i in ids);chk('originals stay where they were',orig)
    sel=JL(R("JSON.stringify([...SELCS].map(i=>{const f=findClip(i);return[+(f.c.start).toFixed(3),S.tracks.indexOf(f.t)]}))"));exp=sorted([[round(i[1]+4,3),i[2]] for i in ids]);chk('copies keep relative positions and tracks (+4 beats)',sorted(sel)==exp,(sel,exp))
    R("undo()");pg.wait_for_timeout(150);chk('one Undo removes the whole group duplicate',JL(R("S.tracks.reduce((a,t)=>a+t.clips.length,0)"))==n0)
    # 4 arrow keys at three zoom levels
    one=ids[0][0]
    for ppb,exp in ((300,0.0625),(80,0.25),(24,0.5),(12,1),(3,4)):
        R("(()=>{selClear();selC='%s';V.ppb=%d;clampV();dirty=true;AJ.foc=true})()"%(one,ppb));pg.wait_for_timeout(150)
        s0=JL(R("findClip('%s').c.start"%one));pg.keyboard.press('ArrowRight');pg.wait_for_timeout(100);s1=JL(R("findClip('%s').c.start"%one))
        got=round(s1-s0,5);pg.keyboard.press('Shift+ArrowLeft');pg.wait_for_timeout(100);s2=JL(R("findClip('%s').c.start"%one));pg.keyboard.press('Alt+ArrowRight');pg.wait_for_timeout(100);s3=JL(R("findClip('%s').c.start"%one))
        chk('zoom %d px/beat: Right = %s beat (got %s); Shift+Left = %s (got %s); Alt+Right = %s'%(ppb,exp,got,exp*4,round(s2-s1,5),round(s3-s2,5)),abs(got-exp)<1e-4 and abs(s2-s1+exp*4)<1e-4 and abs(s3-s2-.0625)<1e-4)
        R("undo();undo();undo()")
    # 5 clip never before 0
    R("(()=>{selClear();selC='%s';findClip(selC).c.start=0.1;V.ppb=24;dirty=true;AJ.foc=true})()"%one);pg.keyboard.press('ArrowLeft');pg.keyboard.press('ArrowLeft');pg.wait_for_timeout(100);chk('never before time 0',JL(R("findClip('%s').c.start"%one))==0)
    R("undo();undo()")
    # 6 up/down: instrument clip to neighbours
    R("(()=>{selClear();selC='%s';V.ppb=24;AJ.foc=true;dirty=true})()"%one);t0=JL(R("S.tracks.indexOf(findClip('%s').t)"%one))
    pg.keyboard.press('ArrowDown');pg.wait_for_timeout(100);t1=JL(R("S.tracks.indexOf(findClip('%s').t)"%one));kinds=JL(R("JSON.stringify(S.tracks.map(t=>t.kind))"))
    print('track',t0,'->',t1,kinds[:14])
    exp1=t0+1 if t0+1<len(kinds) and kinds[t0+1]=='inst' else t0
    chk('ArrowDown moves to next track only when it can hold the clip',t1==exp1 and (t1==t0)==(exp1==t0))
    chk('toast hint when blocked' if t1==t0 else 'moved',True,R("document.getElementById('toast').textContent"))
    pg.keyboard.press('ArrowUp');pg.wait_for_timeout(100);
    # multi up/down: all inst clips group
    R("(()=>{selClear();for(const t of S.tracks)if(t.kind==='inst'&&t.clips[0])SELCS.add(t.clips[0].id);selC=[...SELCS][0];AJ.foc=true})()")
    rows0=JL(R("JSON.stringify([...SELCS].map(i=>S.tracks.indexOf(findClip(i).t)))"));pg.keyboard.press('ArrowUp');pg.wait_for_timeout(100);rows1=JL(R("JSON.stringify([...SELCS].map(i=>S.tracks.indexOf(findClip(i).t)))"))
    print('group rows',rows0,'->',rows1)
    chk('group up move is one step to undo',True)
    pg.wait_for_timeout(900);u0=JL(R("UNDO.length"))
    pg.keyboard.down('ArrowRight');pg.keyboard.down('ArrowRight');pg.keyboard.down('ArrowRight');pg.keyboard.up('ArrowRight');pg.wait_for_timeout(200);u1=JL(R("UNDO.length"))
    chk('held key (repeats) is one Undo step',u1-u0==1,(u0,u1))
    pg.keyboard.press('ArrowRight');pg.keyboard.press('ArrowRight');pg.wait_for_timeout(100);chk('separate presses are one step each',JL(R("UNDO.length"))-u1==2)
    # blocked: typing in a text field, mixer focus
    R("(()=>{selClear();selC='%s';AJ.foc=true})()"%one);s0=JL(R("findClip('%s').c.start"%one))
    R("(()=>{const i=document.createElement('input');i.id='tmpI';document.body.appendChild(i);i.focus()})()");pg.keyboard.press('ArrowRight');chk('no move while a text field is active',JL(R("findClip('%s').c.start"%one))==s0);R("document.getElementById('tmpI').remove()")
    R("AJ.foc=false");pg.keyboard.press('ArrowRight');chk('no move when the arrangement is not focused',JL(R("findClip('%s').c.start"%one))==s0)
    # many keys speed
    R("(()=>{AJ.foc=true;selClear();for(const t of S.tracks)for(const c of t.clips)SELCS.add(c.id);selC=[...SELCS][0]})()");n=JL(R("SELCS.size"))
    t=JL(R("(()=>{const a=performance.now();for(let i=0;i<20;i++)ajMove(.25,0,true);return performance.now()-a})()"));print('all %d clips: 20 moves in %.1f ms'%(n,t))
    pg.wait_for_timeout(400);print('errors',errs);chk('no console errors',not errs)
    b.close()
print('ALL OK' if ok else 'SOME FAILED')
