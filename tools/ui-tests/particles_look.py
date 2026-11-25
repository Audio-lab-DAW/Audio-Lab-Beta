"""All particle devices side by side in looks (v0.177), walls of Bouncy Notes drawn with the mouse, the small pictures in the instrument browser.
python3 tools/ui-tests/particles_look.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
nt=[{'p':60,'s':0,'l':6,'v':.9},{'p':67,'s':6,'l':6,'v':.8}]
al.build({'tracks':[{'name':'B','preset':'pluck','clips':[{'start':0,'len':16,'notes':nt}]},{'name':'E','preset':'emit','clips':[{'start':0,'len':16,'notes':nt}]},{'name':'G','preset':'vgrain','clips':[{'start':0,'len':16,'notes':nt}]},{'name':'F','preset':'vfm','clips':[{'start':0,'len':16,'notes':nt}]}]})
al.run("(()=>{const t=S.tracks[0];t.fx.unshift(mkFx('bnotes'));UI.modC=true;return 1})()")
def box(sel):return json.loads(al.run("(()=>{const r=document.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:Math.max(0,r.left),y:r.top,width:Math.min(r.width,1600-Math.max(0,r.left)),height:r.height})})()"%sel))
def shot(n,sel):al.page.wait_for_timeout(700);al.page.screenshot(path=os.path.join(out,n),clip=box(sel))
for i,(nm,sel) in enumerate([('bnotes','.dev.pbx-bnotes'),('emit','.dev.idev.pbx'),('vgrain','.dev.idev.pbx'),('vfm','.dev.idev.pbx')]):
    al.run("selT=S.tracks[%d].id;renderFx();1"%i);al.page.wait_for_timeout(900)
    print(nm,al.run("(()=>{const d=document.querySelector('%s'),cv=d.querySelector('canvas'),r=d.getBoundingClientRect(),c=cv.getBoundingClientRect();return 'pbx '+d.classList.contains('pbx')+' device '+Math.round(r.width)+'x'+Math.round(r.height)+' picture '+Math.round(c.width)+'x'+Math.round(c.height)+' bg '+getComputedStyle(d).backgroundColor})()"%sel))
    al.run("document.querySelector('%s').scrollIntoView({inline:'start'});1"%sel);shot('look_%s.png'%nm,sel)
# walls: draw two with the mouse, check, remove one with a click
al.run("selT=S.tracks[0].id;renderFx();1");al.page.wait_for_timeout(900);al.run("document.querySelector('.dev.pbx-bnotes').scrollIntoView({inline:'start'});1");al.page.wait_for_timeout(300)
g=json.loads(al.run("(()=>{const cv=fxin.querySelector('canvas.viz[data-t=bnotes]'),r=cv.getBoundingClientRect(),f=S.tracks[0].fx[0];return JSON.stringify({l:r.left,t:r.top,z:r.width/cv.clientWidth,G:f._bg})})()"));G=g['G'];z=g['z'];m=al.page.mouse
PX=lambda p:g['l']+(G['L']+(p-G['lo']+.5)/(G['hi']-G['lo']+1)*(G['RW']-G['L']))*z
PY=lambda h:g['t']+(G['KB']-4-h*(G['KB']-4-G['T']-6))*z
W=lambda:al.run("JSON.stringify(S.tracks[0].fx[0].p.walls||[])")
m.move(PX(57),PY(.6));m.down();m.move(PX(60),PY(.5),steps=4);m.move(PX(63),PY(.4),steps=4);al.page.wait_for_timeout(200);al.page.screenshot(path=os.path.join(out,'walls_drawing.png'),clip=box('.dev.pbx-bnotes'));m.up();print('one wall',W())
m.move(PX(64),PY(.2));m.down();m.move(PX(70),PY(.3),steps=6);m.up();print('two walls',W())
shot('walls_two.png','.dev.pbx-bnotes')
print('notes follow the walls',al.run("(()=>{const t=S.tracks[0];return mfxNotes(t,t.clips[0].notes).slice(0,8).map(n=>n.p).join(' ')})()"))
m.move(PX(60),PY(.5));m.down();m.up();print('after a click on the first wall',W())
al.run("undo();1");print('undo',W());al.run("undo();undo();1");print('two more undos',W())
m.move(PX(56),PY(.7));m.down();m.move(PX(66),PY(.45),steps=6);m.up()
al.run("pos=0;1");al.page.keyboard.press('Space');al.page.wait_for_timeout(1800);shot('walls_playing.png','.dev.pbx-bnotes');al.page.keyboard.press('Space')
al.page.click('.dev.pbx-bnotes [data-kt]');shot('walls_hidden.png','.dev.pbx-bnotes');al.page.click('.dev.pbx-bnotes [data-kt]')
# the small pictures in the instrument browser
al.run("openBrowser(S.tracks[2]);1");al.page.wait_for_timeout(2500);al.page.screenshot(path=os.path.join(out,'browser.png'))
for k in ('vgrain','vfm','emit'):
    r=al.run("(()=>{const el=document.querySelector('#ib .ibdv[data-k=%s]')||document.querySelector('#ib [data-k=%s]');if(!el)return '';chgSee(el.closest('.ibc'));const r=el.getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:r.width,height:r.height})})()"%(k,k))
    print('browser tile',k,r)
    if r:
        al.page.wait_for_timeout(900);r=json.loads(al.run("(()=>{const el=document.querySelector('#ib .ibdv[data-k=%s]')||document.querySelector('#ib [data-k=%s]');const r=el.getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:r.width,height:r.height})})()"%(k,k)));al.page.screenshot(path=os.path.join(out,'browser_%s.png'%k),clip=r)
print('errors',al.errors);al.stop()
