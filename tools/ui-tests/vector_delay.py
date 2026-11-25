"""Vector Delay (v0.179): the device in the page. python3 tools/ui-tests/vector_delay.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
nt=[{'p':60,'s':i,'l':.25,'v':.9} for i in range(0,16,2)]
al.build({'tracks':[{'name':'B','preset':'pluck','clips':[{'start':0,'len':16,'notes':nt}]}]})
al.run("(()=>{const t=S.tracks[0];t.fx.push(mkFx('vdelay'));selT=t.id;changed(true);renderFx();return 1})()");al.page.wait_for_timeout(900)
D='.dev.pbx-vdelay'
def box(sel=D):return json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:Math.max(0,r.left),y:r.top,width:Math.min(r.width,1600-Math.max(0,r.left)),height:r.height})})()"%sel))
def shot(n):al.run("document.querySelector('%s').scrollIntoView({inline:'start'});1"%D);al.page.mouse.move(5,5);al.page.wait_for_timeout(600);al.page.screenshot(path=os.path.join(out,n),clip=box())
P=lambda k:al.run("JSON.stringify(S.tracks[0].fx[0].p.%s)"%k)
# nothing may stick out of the device, on any page
def inside(tag):
    r=al.run("(()=>{const d=document.querySelector('%s'),R=d.getBoundingClientRect(),bad=[];for(const el of d.querySelectorAll('.kn,.ndtb label,.ndtb button,.devh>*')){const r=el.getBoundingClientRect();if(!r.width)continue;if(r.left<R.left-1||r.right>R.right+1||r.top<R.top-1||r.bottom>R.bottom+1)bad.push((el.textContent||el.className).trim().slice(0,18)+' '+Math.round(r.right-R.right)+','+Math.round(r.bottom-R.bottom))}return 'device '+Math.round(R.width)+'x'+Math.round(R.height)+' knobs '+d.querySelectorAll('.kn').length+' choices '+d.querySelectorAll('.ndtb label').length+' outside: '+(bad.join(' | ')||'none')})()"%D)
    print('%-10s %s'%(tag,r))
print(al.run("(()=>{const d=document.querySelector('%s'),cv=d.querySelector('canvas'),r=d.getBoundingClientRect(),c=cv.getBoundingClientRect();return 'pbx '+d.classList.contains('pbx')+' picture '+Math.round(c.width)+'x'+Math.round(c.height)+' bg '+getComputedStyle(d).backgroundColor})()"%D))
inside('Delay');shot('vd_delay.png')
for a,nm in (('tv','Vectors'),('tf','Forces'),('te','Particles'),('tq','Emitter')):
    al.page.click(D+' [data-nact=%s]'%a);al.page.wait_for_timeout(300);inside(nm);shot('vd_%s.png'%nm.lower())
# Forces page: Flow shows other knobs
al.page.click(D+' [data-nact=tf]');al.page.select_option(D+' select[data-x=mot]','w');al.page.wait_for_timeout(400);print('flow knobs',al.run("[...document.querySelectorAll('%s .kn span')].map(s=>s.textContent).join(',')"%D));shot('vd_flow.png')
al.page.select_option(D+' select[data-x=mot]','f');al.page.wait_for_timeout(300)
# handles: range bars
al.run("document.querySelector('%s').scrollIntoView({inline:'start'});1"%D);al.page.wait_for_timeout(300)
g=json.loads(al.run("(()=>{const cv=fxin.querySelector('canvas.viz[data-t=vdelay]'),r=cv.getBoundingClientRect(),G=VDLG.get(S.tracks[0].fx[0].p);return JSON.stringify({l:r.left,t:r.top,z:r.width/cv.clientWidth,G})})()"));G=g['G'];z=g['z'];m=al.page.mouse
X=lambda u:g['l']+(G['fx0']+u*(G['fx1']-G['fx0']))*z
Y=lambda u:g['t']+(G['fy1']-u*(G['fy1']-G['fy0']))*z
by=g['t']+G['by']*z;bx=g['l']+G['bx']*z
m.move(X(0),by);m.down();m.move(X(.3),by,steps=5);m.up();print('left edge dragged to 30%:',P('x0'))
m.move(X(1),by);m.down();m.move(X(.8),by,steps=5);m.up();print('right edge to 80%:',P('x1'))
m.move(bx,Y(1));m.down();m.move(bx,Y(.7),steps=5);m.up();print('top edge to 70%:',P('y1'))
al.run("undo();undo();undo();1");print('after three undos',P('x0'),P('x1'),P('y1'))
# emitter: switch on, move it, aim it
al.page.click(D+' [data-nact=tq]');al.page.wait_for_timeout(300);al.page.check(D+' input[data-x=em]');al.page.wait_for_timeout(500);print('emitter on',P('em'))
m.move(X(.5),Y(.5));m.down();m.move(X(.3),Y(.7),steps=6);m.up();print('emitter moved to',P('ex'),P('ey'))
ex=X(.3);ey=Y(.7);m.move(ex,ey-34*z);m.down();m.move(ex+40*z,ey,steps=6);m.up();print('aim dragged to the right: angle',P('ea'))
shot('vd_emitter.png')
# a knob, a preset
al.run("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,JSON.parse(JSON.stringify(FXPRE.vdelay.cloud[1])));f.p.pre='cloud';for(const k of['td','tv','tf','te','tq'])f.p['_'+k]=k==='td';changed(false);renderFx()})()");al.page.wait_for_timeout(400)
print('tooltip of Time:',al.run("(document.querySelector('%s [data-c$=\":time\"]')||{}).title"%D))
print('tooltip of Recycle:',al.run("(document.querySelector('%s input[data-x=rec]').closest('label')||{}).title"%D))
al.page.select_option(D+' select[data-x=pre]','rise');al.page.wait_for_timeout(300);print('preset Rising shimmer: pitch',P('pitch'),'recycle',P('rec'),'page stays',P('_td'))
# playing: the picture shows the engine's own particles
al.run("pos=0;1");al.page.keyboard.press('Space');al.page.wait_for_timeout(1800)
print('playing: live particles',al.run("(()=>{const N=[...NODES.values()][0],x=[...N.fxm.values()].find(x=>x.m&&x.m.pv);if(!x)return 'no messages';let n=0;for(let s=0;s<16;s++)if(x.m.pv[s*7])n++;return n+' at step '+x.m.k+', age of last message '+Math.round(performance.now()-x.pt)+' ms'})()"))
shot('vd_playing.png');al.page.wait_for_timeout(1500)
k1=al.run("(()=>{const N=[...NODES.values()][0],x=[...N.fxm.values()].find(x=>x.m&&x.m.pv);return x.m.k+'|'+Math.round((ctx.currentTime-originT(ctx))*100)})()");print('engine step | song time in steps',k1)
al.page.keyboard.press('Space');al.page.wait_for_timeout(500)
al.page.click(D+' [data-kt]');shot('vd_hidden.png');al.page.click(D+' [data-kt]')
# it is in the effect browser group, and in the saved project
print('group',al.run("JSON.stringify(FBG.find(g=>g[2].includes('vdelay')).slice(0,1))"),'in project data',al.run("JSON.stringify(S).includes('\"vdelay\"')"))
al.page.screenshot(path=os.path.join(out,'vd_whole.png'))
print('errors',al.errors);al.stop()
