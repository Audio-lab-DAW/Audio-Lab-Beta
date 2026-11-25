"""Vector FM (v0.176): screenshots and UI checks. python3 tools/ui-tests/vector_fm.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
al.build({'tracks':[{'name':'V','preset':'vfm','clips':[{'start':0,'len':16,'notes':[{'p':60,'s':0,'l':6,'v':.9},{'p':67,'s':6,'l':6,'v':.8}]}]}]})
al.run("selT=S.tracks[0].id;renderFx();1");al.page.wait_for_timeout(4000)
box=lambda:json.loads(al.run("(()=>{const r=fxin.querySelector('.dev.vfd').getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:r.width,height:r.height})})()"))
shot=lambda n:(al.page.wait_for_timeout(700),al.page.screenshot(path=os.path.join(out,n),clip=box()))
inside=lambda:al.run("(()=>{const d=fxin.querySelector('.dev.vfd'),R=d.getBoundingClientRect();let bad=[];for(const el of d.querySelectorAll('.kn,button,select,p')){const r=el.getBoundingClientRect();if(r.width&&(r.right>R.right+.5||r.bottom>R.bottom+.5||r.left<R.left-.5))bad.push(el.className+' '+(el.dataset.c||el.dataset.vfb||el.dataset.vfs||''))}return 'outside: '+JSON.stringify(bad)+' knobs '+d.querySelectorAll('.kn').length})()")
print('device',box());shot('vfm_stopped.png');print('tab g',inside())
for tab in 'vpf':
    al.page.click('.vfd [data-vfb="tab:%s"]'%tab);shot('vfm_tab_%s.png'%tab);print('tab',tab,inside())
al.page.click('.vfd [data-vfb="tab:p"]');al.page.click('.vfd [data-vfb="mot:w"]');shot('vfm_flow.png');print('flow',inside(),al.run("S.tracks[0].inst.mot"));al.run("undo();1")
al.page.click('.vfd [data-vfb="tab:o"]');al.page.click('.vfd [data-vfb="ops:3"]');print('3 operators',inside(),'algorithm choice shown',al.run("!!fxin.querySelector('.vfd select[data-vfs=alg]')"),al.run("S.tracks[0].inst.ops"));shot('vfm_chains.png')
al.page.select_option('.vfd select[data-vfs=alg]','o');print('fan out',al.run("S.tracks[0].inst.alg"));shot('vfm_fanout.png');al.run("undo();undo();renderFx();1");print('undone: operators',al.run("S.tracks[0].inst.ops"))
al.page.click('.vfd [data-vfb="pn"]');print('one per key',inside(),al.run("S.tracks[0].inst.pn"));al.run("undo();renderFx();1")
# drag the right end of the X bar and the top end of the Y bar, then the middle of the X bar
geo=lambda:json.loads(al.run("(()=>{const I=S.tracks[0].inst,cv=fxin.querySelector('canvas[data-k=vfm_main]'),r=cv.getBoundingClientRect(),G=vfmGeo(r.width/ZOOM,r.height/ZOOM,I);return JSON.stringify({l:r.left,t:r.top,z:ZOOM,G})})()"))
st=lambda:al.run("(()=>{const I=S.tracks[0].inst;return [I.x0,I.x1,I.y0,I.y1].join(' ')})()")
g=geo();G=g['G'];z=g['z'];m=al.page.mouse;print('before',st())
m.move(g['l']+G['fx1']*z,g['t']+G['by']*z);m.down();m.move(g['l']+(G['fx0']+(G['fx1']-G['fx0'])*.6)*z,g['t']+G['by']*z,steps=5);m.up();print('x end ',st())
m.move(g['l']+G['bx']*z,g['t']+G['fy0']*z);m.down();m.move(g['l']+G['bx']*z,g['t']+(G['fy0']+(G['fy1']-G['fy0'])*.3)*z,steps=5);m.up();print('y end ',st())
m.move(g['l']+(G['fx0']+(G['fx1']-G['fx0'])*.3)*z,g['t']+G['by']*z);m.down();m.move(g['l']+(G['fx0']+(G['fx1']-G['fx0'])*.5)*z,g['t']+G['by']*z,steps=5);m.up();print('x move',st())
shot('vfm_range.png')
al.run("undo();undo();undo();1");print('undone',st())
print('tooltip',al.run("fxin.querySelector('[data-c=\"fx:vf:idx\"]').title"))
# live: play the song, the picture must show the engine's own particles
al.page.keyboard.press('Space');al.page.wait_for_timeout(1500)
print('live',al.run("(()=>{const v=VFMV.get(S.tracks[0].inst);return v?('age ms '+Math.round(performance.now()-v.t)+' particles '+v.n):'no data from the engine'})()"),'playing',al.run("!!play.on"))
shot('vfm_playing.png')
al.page.keyboard.press('Space');al.page.wait_for_timeout(300)
al.page.click('.vfd [data-ikt]');shot('vfm_hidden.png');print('hidden: knobs',al.run("fxin.querySelectorAll('.dev.vfd .kn').length"));al.page.click('.vfd [data-ikt]')
# a held key: particles while down, none a while after release; Lock stops held keys while the song is stopped
h=al.run("(()=>{window._h=voiceOn(S.tracks[0],60,.9);return !!window._h})()");al.page.wait_for_timeout(900);a=al.run("(()=>{const v=VFMV.get(S.tracks[0].inst);return v?v.n:-1})()")
al.run("window._h.off();1");al.page.wait_for_timeout(5000);b2=al.run("(()=>{const v=VFMV.get(S.tracks[0].inst);return v?v.n+' age '+Math.round(performance.now()-v.t):-1})()")
print('held key',h,'particles',a,'after release',b2)
print('lock on, song stopped: key sounds',al.run("(()=>{S.tracks[0].inst.lock=true;const h=voiceOn(S.tracks[0],60,.9);S.tracks[0].inst.lock=false;if(h)h.off();return !!h})()"))
# one per key: three held keys give three particles
al.run("(()=>{S.tracks[0].inst.pn=true;window._k=[60,64,67].map(p=>voiceOn(S.tracks[0],p,.8));return 1})()");al.page.wait_for_timeout(800)
print('one per key, 3 keys held: particles',al.run("VFMV.get(S.tracks[0].inst).n"));al.run("window._k.forEach(h=>h.off());S.tracks[0].inst.pn=false;1")
# the instrument browser shows it
print('in browser list',al.run("IBG.some(g=>g[2].includes('vfm'))"),'presets',al.run("Object.keys(VFMPRE).length"))
print('errors',al.errors);al.stop()
