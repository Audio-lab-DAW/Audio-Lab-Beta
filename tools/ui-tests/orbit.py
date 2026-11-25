"""Orbit (v0.180): the device in the page. python3 tools/ui-tests/orbit.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
al.build({'tracks':[{'name':'O','preset':'orb','clips':[{'start':0,'len':16,'notes':[{'p':60,'s':0,'l':6,'v':.9},{'p':67,'s':6,'l':6,'v':.8}]}]}]})
al.run("selT=S.tracks[0].id;renderFx();1");al.page.wait_for_timeout(900)
D='.dev.idev.pbx'
def box():return json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:Math.max(0,r.left),y:r.top,width:Math.min(r.width,1600-Math.max(0,r.left)),height:r.height})})()"%D))
def shot(n):al.run("document.querySelector('%s').scrollIntoView({inline:'start'});1"%D);al.page.mouse.move(5,5);al.page.wait_for_timeout(700);al.page.screenshot(path=os.path.join(out,n),clip=box())
I=lambda k:al.run("JSON.stringify(S.tracks[0].inst.%s)"%k)
def inside(tag):
    print('%-10s %s'%(tag,al.run("(()=>{const d=document.querySelector('%s'),R=d.getBoundingClientRect(),bad=[];for(const el of d.querySelectorAll('[data-c],button,select')){const r=el.getBoundingClientRect();if(!r.width)continue;if(r.left<R.left-1||r.right>R.right+1||r.top<R.top-1||r.bottom>R.bottom+1)bad.push((el.textContent||el.dataset.c||'').trim().slice(0,16))}return 'device '+Math.round(R.width)+'x'+Math.round(R.height)+' controls '+d.querySelectorAll('[data-c]').length+' outside: '+(bad.join(' | ')||'none')})()"%D)))
inside('Operators');shot('orb_ops.png')
for v,nm in (('v','Vectors'),('p','Orbits'),('f','Output')):
    al.page.click(D+' [data-obb="tab:%s"]'%v);al.page.wait_for_timeout(300);inside(nm);shot('orb_%s.png'%nm.lower())
al.page.click(D+' [data-obb="tab:p"]');al.page.wait_for_timeout(300);al.run("document.querySelector('%s').scrollIntoView({inline:'start'});1"%D);al.page.wait_for_timeout(300)
g=json.loads(al.run("(()=>{const cv=fxin.querySelector('canvas.ivz[data-k=orb_main]'),r=cv.getBoundingClientRect(),w=r.width/ZOOM,h=r.height/ZOOM,G=orbGeo(w,h,S.tracks[0].inst);return JSON.stringify({l:r.left,t:r.top,z:ZOOM,G})})()"));G=g['G'];z=g['z'];m=al.page.mouse
X=lambda u:g['l']+(G['fx0']+(u+1)/2*(G['fx1']-G['fx0']))*z
Y=lambda u:g['t']+(G['fy1']-(u+1)/2*(G['fy1']-G['fy0']))*z
print('before: balls',I('num'),I('balls'))
m.move(X(.7),Y(0));m.down();m.up();al.page.wait_for_timeout(300);print('after a click at 0.7, 0: balls',I('num'),I('balls'))
m.move(X(-.4),Y(.5));m.down();m.up();al.page.wait_for_timeout(300);print('after a second click: balls',I('num'),I('balls'))
m.move(X(0),Y(0));m.down();m.move(X(0),Y(0)-30,steps=5);m.up();al.page.wait_for_timeout(300);print('centre dragged up 30 px: centre mass',I('cen'))
shot('orb_dropped.png')
al.run("undo();undo();undo();1");print('after three undos: balls',I('num'),I('balls'),'centre',I('cen'))
al.page.wait_for_timeout(300);print('clear button there',al.run("!!document.querySelector('[data-obb=clr]')"),'tab',I('otab'));al.run("(document.querySelector('[data-obb=clr]')||{click(){}}).click();1");print('clear dropped balls',I('balls'))
al.run("pos=0;1");al.page.keyboard.press('Space');al.page.wait_for_timeout(1800);shot('orb_playing.png')
print('playing: live balls',al.run("(()=>{const v=ORBV.get(S.tracks[0].inst);return v?v.n+' age '+Math.round(performance.now()-v.t)+' ms':'none'})()"))
al.page.keyboard.press('Space');al.page.wait_for_timeout(400)
print('in the instrument browser',al.run("JSON.stringify(IBG.filter(g=>g[2].includes('orb')).map(g=>g[0]))"),'name',al.run("PRESETS.orb.name"))
al.run("openBrowser(S.tracks[0]);1");al.page.wait_for_timeout(2500)
r=al.run("(()=>{const el=document.querySelector('#ib [data-k=orb]');if(!el)return '';el.scrollIntoView({block:'center'});return '1'})()")
if r:
    al.page.wait_for_timeout(1000);b=json.loads(al.run("(()=>{const r=document.querySelector('#ib [data-k=orb]').getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:r.width,height:r.height})})()"));al.page.screenshot(path=os.path.join(out,'orb_browser.png'),clip=b)
print('browser tile found',bool(r),'errors',al.errors);al.stop()
