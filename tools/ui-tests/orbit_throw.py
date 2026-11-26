"""Orbit (v0.189): throw a ball by dragging, remove one with a right-click, change its mass by scrolling, the orbit paths.
python3 tools/ui-tests/orbit_throw.py [index.html] [out dir]"""
import sys,os,json,math
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('errors after load',al.errors)
al.build({'bpm':120,'tracks':[{'name':'Orbit','preset':'orb','clips':[{'start':0,'len':8,'notes':[{'p':60,'s':0,'l':8,'v':.9}]}]}]})
al.run("selT=S.tracks[0].id;S.tracks[0].inst.otab='p';renderFx();1");al.page.wait_for_timeout(900)
D='.dev.idev.pbx';CV=D+' canvas.ivz[data-k=orb_main]'
al.run("document.querySelector('%s').scrollIntoView({inline:'start'});1"%D);al.page.wait_for_timeout(400)
def box(sel=D):return json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:Math.max(0,r.left),y:r.top,width:Math.min(r.width,1600-Math.max(0,r.left)),height:r.height})})()"%sel))
def shot(n):al.page.screenshot(path=os.path.join(out,n),clip=box())
I=lambda k:json.loads(al.run("JSON.stringify(S.tracks[0].inst.%s??null)"%k))
cb=box(CV);Z=al.run("ZOOM")
def geo():return json.loads(al.run("(()=>{const cv=document.querySelector('%s'),r=cv.getBoundingClientRect(),G=orbGeo(r.width/ZOOM,r.height/ZOOM,S.tracks[0].inst);return JSON.stringify(G)})()"%CV))
G=geo();cx=(G['fx0']+G['fx1'])/2;cy=(G['fy0']+G['fy1'])/2;R=(G['fx1']-G['fx0'])/2
pg=lambda x,y:(cb['x']+x*Z,cb['y']+y*Z)
# 1. a click drops a ball at rest on a circle (as before)
n0=I('num');x,y=pg(cx+R*.5,cy);al.page.mouse.click(x,y);al.page.wait_for_timeout(400)
print('click: balls %d -> %d, entry %s'%(n0,I('num'),I('balls')[n0]))
# 2. press, drag 70 px up, release: a throw
x,y=pg(cx-R*.55,cy);al.page.mouse.move(x,y);al.page.mouse.down();al.page.mouse.move(x+10,y-20,steps=3);al.page.mouse.move(x+20,y-70,steps=6);al.page.wait_for_timeout(250)
print('while dragging: a throw line is drawn',al.run("!!ORBTH&&ORBTH.I===S.tracks[0].inst"));shot('orbit_throwing.png')
al.page.mouse.up();al.page.wait_for_timeout(400);e=I('balls')[n0+1]
print('throw: balls %d, entry %s (x, y, mass, speed right, speed up)'%(I('num'),e),'line gone',al.run("ORBTH===null"))
sp=math.hypot(e[3],e[4]);print('throw speed %.3f, direction %.0f degrees (dragged 20 right, 70 up: %.0f)'%(sp,math.degrees(math.atan2(e[4],e[3])),math.degrees(math.atan2(70,20))))
# the engine's start of that ball: velocity = stored speed x sqrt(pull)
r=al.run("""(()=>{const I=S.tracks[0].inst,P=orbPar(I,1),C=orbPhys(),F=C.field(123);C.step(F,P,0);const s=%d,k=Math.sqrt(Math.max(4*P.cen*P.grav,.25)),b=I.balls[s];
  return JSON.stringify({x:F.x[s],y:F.y[s],vx:F.vx[s],vy:F.vy[s],want:[b[0],b[1],b[3]*k,b[4]*k]})})()"""%(n0+1))
print('engine start of the thrown ball',r)
# 3. stand still, then right-click a ball to remove it
al.run("S.tracks[0].inst.spd=0;orbPush(S.tracks[0].inst);1");al.page.wait_for_timeout(500)
H=json.loads(al.run("JSON.stringify(orbDraw.H.get(S.tracks[0].inst))"));h=H[2]
before=json.loads(al.run("""(()=>{const I=S.tracks[0].inst,P=orbPar(I,1),C=orbPhys(),F=C.field(99);C.step(F,P,0);return JSON.stringify([...Array(16).keys()].map(s=>F.on[s]?[+F.x[s].toFixed(6),+F.y[s].toFixed(6)]:null))})()"""))
n1=I('num');x,y=pg(h['x'],h['y']);al.page.mouse.click(x,y,button='right');al.page.wait_for_timeout(400)
after=json.loads(al.run("""(()=>{const I=S.tracks[0].inst,P=orbPar(I,1),C=orbPhys(),F=C.field(99);C.step(F,P,0);return JSON.stringify([...Array(16).keys()].map(s=>F.on[s]?[+F.x[s].toFixed(6),+F.y[s].toFixed(6)]:null))})()"""))
print('right-click on ball %d: balls %d -> %d, slot now %s'%(h['k'],n1,I('num'),I('balls')[h['k']] if len(I('balls'))>h['k'] else None))
print('the other balls keep their places:',all(before[s]==after[s] for s in range(16) if s!=h['k']),'removed one gone:',after[h['k']] is None)
al.run("undo();1");al.page.wait_for_timeout(300);print('undo: balls',I('num'),'slot',(I('balls')+[None]*16)[h['k']])
# 4. scroll over a ball: its mass
H=json.loads(al.run("JSON.stringify(orbDraw.H.get(S.tracks[0].inst))"));h=H[1];x,y=pg(h['x'],h['y']);al.page.mouse.move(x,y);al.page.wait_for_timeout(100)
for i in range(4):al.page.mouse.wheel(0,-100);al.page.wait_for_timeout(60)
bm=I('bm');print('scroll up 4 notches over ball %d: mass x%s'%(h['k'],bm[h['k']] if bm else None));al.page.wait_for_timeout(200);shot('orbit_mass.png')
r=al.run("""(()=>{const I=S.tracks[0].inst,P=orbPar(I,1),C=orbPhys(),F=C.field(5);C.step(F,P,0);const a=[0,0,0,0,0];C.attr(F,P,%d,a);const m=F.m[%d];const b=[0,0,0,0,0];C.attr(F,P,%d,b);return JSON.stringify({mass:F.m[%d],other:F.m[%d],massValue:a[4],otherValue:b[4]})})()"""%(h['k'],h['k'],H[0]['k'],h['k'],H[0]['k']))
print('engine: ',r)
for i in range(2):al.page.mouse.wheel(0,100);al.page.wait_for_timeout(60)
print('scroll down 2: mass x%s'%I('bm')[h['k']]);al.page.mouse.move(x+300,y);al.page.wait_for_timeout(800)
al.run("undo();1");al.page.wait_for_timeout(300);bm=I('bm');print('undo (one step for the whole scroll): mass',bm[h['k']] if bm else None)
# scrolling where there is no ball scrolls the page as before (not taken)
print('wheel over empty space is not taken:',al.run("(()=>{const cv=document.querySelector('%s');const e=new WheelEvent('wheel',{deltaY:100,clientX:cv.getBoundingClientRect().left+3,clientY:cv.getBoundingClientRect().top+3,bubbles:true,cancelable:true});cv.dispatchEvent(e);return !e.defaultPrevented})()"%CV))
# 5. the orbit paths: drawn faintly; with the default the balls go round in circles
al.run("S.tracks[0].inst.spd=100;orbPush(S.tracks[0].inst);1");al.page.wait_for_timeout(900);shot('orbit_paths.png')
# 6. clear forgets throws, removals and masses
al.page.click(D+' [data-obb="clr"]');al.page.wait_for_timeout(300);print('clear: balls',I('balls'),'masses',I('bm'))
# 7. one per key: right-click does nothing but say why
al.run("S.tracks[0].inst.pn=true;renderFx();1");al.page.wait_for_timeout(400);n2=I('num');H=json.loads(al.run("JSON.stringify(orbDraw.H.get(S.tracks[0].inst))"))
if H:x,y=pg(H[0]['x'],H[0]['y']);al.page.mouse.click(x,y,button='right');al.page.wait_for_timeout(300)
print('one per key, right-click: balls',n2,'->',I('num'))
# 8. while the song plays the paths come from the engine
al.run("S.tracks[0].inst.pn=false;renderFx();pos=0;1");al.page.keyboard.press('Space');al.page.wait_for_timeout(1500);print('engine reports speeds',al.run("(()=>{const v=ORBV.get(S.tracks[0].inst);return !!(v&&v.ov&&v.ov.some(x=>x!==0))})()"));shot('orbit_playing.png');al.page.keyboard.press('Space');al.page.wait_for_timeout(300)
print('errors',al.errors);al.stop()
