"""Emit (v0.174): screenshots and UI checks. python3 tools/ui-tests/emit.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
al.build({'tracks':[{'name':'E','preset':'emit','clips':[{'start':0,'len':16,'notes':[{'p':60,'s':0,'l':6,'v':.9},{'p':67,'s':6,'l':6,'v':.8}]}]}]})
al.run("selT=S.tracks[0].id;renderFx();1");al.page.wait_for_timeout(5000)
box=lambda:json.loads(al.run("(()=>{const r=fxin.querySelector('.dev.emd').getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:r.width,height:r.height})})()"))
shot=lambda n:(al.page.wait_for_timeout(700),al.page.screenshot(path=os.path.join(out,n),clip=box()))
print('device',box());shot('emit_stopped.png')
for tab in '2ms':
    al.page.click('.emd [data-emb="tab:%s"]'%tab);shot('emit_tab_%s.png'%tab)
al.page.click('.emd [data-emb="tab:1"]')
# every control inside the device, nothing cut off
print(al.run("(()=>{const d=fxin.querySelector('.dev.emd'),R=d.getBoundingClientRect();let bad=[];for(const el of d.querySelectorAll('.kn,button,select')){const r=el.getBoundingClientRect();if(r.width&&(r.right>R.right+.5||r.bottom>R.bottom+.5||r.left<R.left-.5))bad.push(el.className+' '+(el.dataset.c||el.dataset.emb||''))}return 'outside: '+JSON.stringify(bad)+' knobs '+d.querySelectorAll('.kn').length})()"))
# drag the emitter, its corner and its aim dot
b=box();g=json.loads(al.run("(()=>{const I=S.tracks[0].inst,cv=fxin.querySelector('canvas[data-k=em_main]'),r=cv.getBoundingClientRect(),G=emGeo(r.width/ZOOM,r.height/ZOOM,I),R=emRect(I,1,G);return JSON.stringify({l:r.left,t:r.top,z:ZOOM,R,am:emSA(I.ang1,G)})})()"))
z=g['z'];R=g['R'];cx=g['l']+(R['x']+R['w']/2)*z;cy=g['t']+(R['y']+R['h']/2)*z
st=lambda:al.run("(()=>{const I=S.tracks[0].inst;return [I.rx1,I.ry1,I.rw1,I.rh1,I.ang1].map(v=>+(+v).toFixed(3)).join(' ')})()")
print('before',st())
m=al.page.mouse;m.move(cx,cy);m.down();m.move(cx-120,cy-30,steps=5);m.up();print('moved ',st())
g=json.loads(al.run("(()=>{const I=S.tracks[0].inst,cv=fxin.querySelector('canvas[data-k=em_main]'),r=cv.getBoundingClientRect(),G=emGeo(r.width/ZOOM,r.height/ZOOM,I),R=emRect(I,1,G);return JSON.stringify({l:r.left,t:r.top,z:ZOOM,R,am:emSA(I.ang1,G)})})()"));R=g['R']
m.move(g['l']+(R['x']+R['w']-2)*z,g['t']+(R['y']+R['h']-2)*z);m.down();m.move(g['l']+(R['x']+R['w']+40)*z,g['t']+(R['y']+R['h']+20)*z,steps=5);m.up();print('sized ',st())
g=json.loads(al.run("(()=>{const I=S.tracks[0].inst,cv=fxin.querySelector('canvas[data-k=em_main]'),r=cv.getBoundingClientRect(),G=emGeo(r.width/ZOOM,r.height/ZOOM,I),R=emRect(I,1,G);return JSON.stringify({l:r.left,t:r.top,z:ZOOM,R,am:emSA(I.ang1,G)})})()"));R=g['R']
import math
cx=g['l']+(R['x']+R['w']/2)*z;cy=g['t']+(R['y']+R['h']/2)*z
m.move(cx+math.cos(g['am'])*36*z,cy+math.sin(g['am'])*36*z);m.down();m.move(cx,cy-60,steps=5);m.up();print('aimed ',st(),'knob shows',al.run("fxin.querySelector('[data-c=\"fx:em:ang1\"] output').textContent"))
al.run("undo();undo();undo();1");print('undone',st())
# live: play the song, the picture must show the engine's own particles

al.page.keyboard.press('Space');al.page.wait_for_timeout(1500)
print('live',al.run("(()=>{const v=EMV.get(S.tracks[0].inst);return v?('age ms '+Math.round(performance.now()-v.t)+' particles '+(v.pv.length>>2)+' angle '+Math.round(v.mo[0])):'no data from the engine'})()"),'playing',al.run("!!play.on"))
shot('emit_playing.png')
al.page.keyboard.press('Space');al.page.wait_for_timeout(300)
al.page.click('.emd [data-ikt]');shot('emit_hidden.png');print('hidden: knobs',al.run("fxin.querySelectorAll('.dev.emd .kn').length"));al.page.click('.emd [data-ikt]')
# a held key: particles while down, none a while after release
h=al.run("(()=>{window._h=voiceOn(S.tracks[0],60,.9);return !!window._h})()");al.page.wait_for_timeout(900);a=al.run("(()=>{const v=EMV.get(S.tracks[0].inst);return v?v.pv.length>>2:-1})()")
al.run("window._h.off();1");al.page.wait_for_timeout(2600);b2=al.run("(()=>{const v=EMV.get(S.tracks[0].inst);return v?(v.pv.length>>2)+' age '+Math.round(performance.now()-v.t):-1})()")
print('held key particles',a,'after release',b2)
print('errors',al.errors);al.stop()
