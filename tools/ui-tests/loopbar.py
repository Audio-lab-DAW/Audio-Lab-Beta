# Loop bar while playing (task AC).  python3 tools/ui-tests/loopbar.py [index.html]
# Plays the Fractals demo and, recording the transport every frame:
#  1. draws a new loop on the ruler slowly, starting just behind the playhead (slower than the playhead moves)
#  2. moves that loop by its middle   3. resizes it by its right edge
# Checks for each: during the drag no loop shorter than one beat is ever active, the loop the transport uses does not change,
# the transport is not restarted and does not go round a loop; after release the playback goes round the new region exactly.
# Also: no page errors on load.
import sys,json
import sys as _ws_sys, os as _ws_os; _ws_sys.path.insert(0, _ws_os.path.join(_ws_os.path.dirname(_ws_os.path.abspath(__file__)), '../test-songs')); from alsong import alsong  # task WS-F: the test songs
from playwright.sync_api import sync_playwright
idx=sys.argv[1] if len(sys.argv)>1 else 'index.html'
src=open(idx,encoding='utf-8').read()
REC="""(()=>{window.__L=[];window.__S=[];window.__st=0;if(!window.__hk){window.__hk=1;const s0=start;start=function(){window.__st++;return s0.apply(this,arguments)};const c0=schedule;schedule=function(f,t){if(window.__rec&&!play.only)window.__S.push([f,t,play.pass]);return c0.apply(this,arguments)}}
 const f=()=>{if(!window.__rec)return;window.__L.push({t:performance.now(),d:curDisp(),a:loopA(),b:loopB(),on:!!S.loop,past:!!play.past,pass:play.pass,st:window.__st,pl:play.on});requestAnimationFrame(f)};window.__rec=1;requestAnimationFrame(f)})()"""
fails=[]
def ok(c,msg):
    print(('  ok   ' if c else '  FAIL ')+msg)
    if not c:fails.append(msg)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':1600,'height':1000})
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:300]))
    pg.route('https://app.test/**',alsong(lambda r:r.fulfill(status=200,content_type='text/html',body=src.encode()) if r.request.url.endswith('.html') else r.fulfill(status=404,body=b'')))
    pg.add_init_script("localStorage.setItem('audiolab-ui',JSON.stringify({splash:false,lat3:1}))")
    pg.goto('https://app.test/index.html');pg.wait_for_function("()=>window.AudioLab&&window.AudioLab.version",timeout=60000);pg.wait_for_timeout(5000)
    R=lambda c:pg.evaluate("c=>AudioLab.run(c)",c)
    ok(not errs,'no page errors on load %s'%errs)
    R("(()=>{pmSetOn(false);devHide(true);setFollow(false)})()");pg.wait_for_timeout(600)
    BPM=R("S.bpm");print('version',R("VERSION"),'| demo',R("S.name||''"),'| bpm',R("S.bpm"))
    def xy(beat):  # client point on the ruler for a beat
        return R("(b=>{const r=arr.getBoundingClientRect();return [r.left+(X0+(b-V.x)*V.ppb)*ZOOM,r.top+(TY+RUL/2)*ZOOM]})(%s)"%beat)
    def stoprec():R("window.__rec=0");return R("window.__L")
    def stoprec2(what):L=stoprec();nodouble(what);return L
    def drag(fr,to,steps,ms):
        x0,y0=fr;x1,y1=to;pg.mouse.move(x0,y0);pg.mouse.down()
        for i in range(1,steps+1):pg.mouse.move(x0+(x1-x0)*i/steps,y0);pg.wait_for_timeout(ms)
    def nodouble(what):
        S_=R("window.__S");bad=0
        for i in range(1,len(S_)):
            if S_[i][2]==S_[i-1][2] and S_[i][0]<S_[i-1][1]-1e-6:bad+=1
        ok(bad==0,'%s: nothing scheduled twice (%d scheduler calls, %d overlapping)'%(what,len(S_),bad))
    def during(L,a0,b0,what):
        bad=[f for f in L if f['on'] and f['pl'] and f['b']-f['a']<1-1e-6]
        ok(not bad,'%s: no active loop shorter than one beat during the drag (%d frames, shortest %s)'%(what,len(L),min([round(f['b']-f['a'],3) for f in L if f['on']] or [None])))
        st=L[-1]['st']-L[0]['st'];ok(st==0,'%s: transport restarts during the drag: %d'%(what,st))
        ch=[f for f in L if (f['a'],f['b'])!=(a0,b0)];ok(not ch,'%s: the loop the transport uses stays %s..%s during the drag (changed in %d frames)'%(what,a0,b0,len(ch)))
        tw=[L[i]['t'] for i in range(1,len(L)) if L[i]['pass']>L[i-1]['pass']];sec=(b0-a0)*60/BPM;dur=(L[-1]['t']-L[0]['t'])/1000
        gaps=[(tw[i]-tw[i-1])/1000 for i in range(1,len(tw))];ok(len(tw)<=dur/sec+1 and all(g>.9*sec for g in gaps),'%s: the old loop comes round at its own pace during the drag: %d rounds in %.1f s, loop %.2f s, gaps %s'%(what,len(tw),dur,sec,[round(g,2) for g in gaps]))
    def after(L,a,b,what):
        ok(abs(L[-1]['a']-a)<1e-6 and abs(L[-1]['b']-b)<1e-6,'%s: loop after release %.3f..%.3f (want %.3f..%.3f)'%(what,L[-1]['a'],L[-1]['b'],a,b))
        d=[f['d'] for f in L];wr=[i for i in range(1,len(d)) if d[i]<d[i-1]-.01]
        ok(len(wr)>=1,'%s: playback went round the new loop %d times'%(what,len(wr)))
        if wr:
            tail=d[wr[0]:];out=[v for v in tail if v<a-.02 or v>b+.06];ok(not out,'%s: after the first round every frame is inside %.2f..%.2f (outside: %d, range %.3f..%.3f)'%(what,a,b,len(out),min(tail),max(tail)))
            bps=BPM/60;jumps=[(round(d[i-1],3),round(d[i],3)) for i in wr];err=[abs((d[i]-a)+(b-d[i-1])-(L[i]['t']-L[i-1]['t'])/1000*bps) for i in wr[1:]];good=all(x<.06 for x in err) and a-.02<=jumps[0][1]<b;print('    jump error per round, beats (frame time taken out)',[round(x,3) for x in err])
            ok(good,'%s: the first jump lands inside the loop, every later one goes from the loop end to the loop start %s'%(what,jumps[:4]))
        st=L[-1]['st']-L[0]['st'];ok(st<=1,'%s: restarts after release: %d'%(what,st))
    # ---- 1. draw a new loop slowly from just behind the playhead
    R("(()=>{S.loop=false;S.loopRange=null;pos=64;V.ppb=40;V.x=60;clampV();syncTransportUI();dirty=true})()")
    pg.click('#bPlay');pg.wait_for_timeout(1500)
    R(REC);pg.wait_for_timeout(100)
    d0=R("curDisp()");start_b=round(d0)-1  # a beat line just behind the playhead
    fr=xy(start_b);pg.wait_for_timeout(20)
    # 24 px per step every 120 ms at 40 px per beat = 5 beats per second for the pointer... first slower than the playhead (145 BPM = 2.4 beats/s)
    x0,y0=fr;pg.mouse.move(x0,y0);pg.mouse.down()
    for i in range(1,41):pg.mouse.move(x0+i*2,y0);pg.wait_for_timeout(40)      # 80 px in 1.6 s: 2 beats, the playhead runs away
    for i in range(1,21):pg.mouse.move(x0+80+i*12,y0);pg.wait_for_timeout(40)  # then catch up: 240 px more
    L=stoprec();during(L,0,R("loopEnd()"),'draw')
    R(REC);pg.mouse.up();ta=R("S.loopRange&&S.loopRange.a");tb=R("S.loopRange&&S.loopRange.b");print('  new loop',ta,tb,'| playhead',round(R("curDisp()"),2))
    pg.wait_for_timeout(int((tb-ta)*60/R("S.bpm")*1000*2.6));L=stoprec2('draw');after(L,ta,tb,'draw')
    # ---- 2. move the loop by its middle, one bar to the right, slowly
    R(REC);m=xy((ta+tb)/2);a0,b0=ta,tb;drag((m[0],m[1]),(m[0]+4*40,m[1]),40,40);L=stoprec();during(L,a0,b0,'move')
    R(REC);pg.mouse.up();na=R("S.loopRange.a");nb=R("S.loopRange.b");print('  moved to',na,nb);pg.wait_for_timeout(int((nb-na)*60/R("S.bpm")*1000*2.6));L=stoprec2('move');after(L,na,nb,'move')
    ok(abs(na-(a0+4))<1e-6,'move: loop moved by one bar')
    # ---- 3. resize by the right edge: first shrink towards a tiny loop (below one beat is never used), then grow
    R(REC);e=xy(nb);drag((e[0]-2,e[1]),(e[0]-2-(nb-na-.4)*40,e[1]),30,40);
    sh=R("(()=>{const L=loopShow();return L.b-L.a})()");ok(sh>=1-1e-6,'resize: the loop drawn while shrinking is never shorter than one beat (%.2f)'%sh)
    e2=R("(()=>{const r=arr.getBoundingClientRect();return r.left+(X0+(loopShow().b-V.x)*V.ppb)*ZOOM})()")
    for i in range(1,21):pg.mouse.move(e2+i*8,e[1]);pg.wait_for_timeout(40)
    L=stoprec();during(L,na,nb,'resize')
    R(REC);pg.mouse.up();ra=R("S.loopRange.a");rb=R("S.loopRange.b");print('  resized to',ra,rb);pg.wait_for_timeout(int((rb-ra)*60/R("S.bpm")*1000*2.6));L=stoprec2('resize');after(L,ra,rb,'resize')
    # ---- 4. stopped: the loop still follows the mouse while drawing (nothing to schedule)
    pg.click('#bPlay');pg.wait_for_timeout(300);R("(()=>{pos=8;S.loop=false;S.loopRange=null;V.x=60;dirty=true})()");pg.wait_for_timeout(100)
    s=xy(70);pg.mouse.move(s[0],s[1]);pg.mouse.down()
    for i in range(1,11):pg.mouse.move(s[0]+i*16,s[1]);pg.wait_for_timeout(30)
    live=R("S.loopRange&&[S.loopRange.a,S.loopRange.b]");pg.mouse.up();ok(live==[70,74],'stopped: the loop follows the mouse while drawing %s'%live)
    print('page errors',errs);ok(not errs,'no page errors')
    b.close()
print('FAILED: %d'%len(fails) if fails else 'ALL PASSED');sys.exit(1 if fails else 0)
