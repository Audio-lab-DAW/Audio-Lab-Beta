"""Vector Map (v0.177): screenshots and UI checks. python3 tools/ui-tests/vector_map.py [index.html] [out dir]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
out=sys.argv[2] if len(sys.argv)>2 else '.'
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('ver',al.version)
al.build({'tracks':[{'name':'V','preset':'pluck','clips':[{'start':0,'len':16,'notes':[{'p':60,'s':i,'l':.5,'v':.9} for i in range(16)]}]}]})
al.run("(()=>{const t=S.tracks[0];t.fx.push(mkFx('filter'));t.fx.push(mkFx('delay'));selT=t.id;UI.modC=false;t.mods=[modNew('vmap')];renderFx();return 1})()");al.page.wait_for_timeout(1500)
box=lambda sel='.vmcard',pad=0:json.loads(al.run("(()=>{const r=fxin.querySelector('%s').getBoundingClientRect();return JSON.stringify({x:r.left-%d,y:r.top-%d,width:r.width+%d,height:r.height+%d})})()"%(sel,pad,pad,2*pad,2*pad)))
shot=lambda n,sel='.vmcard',pad=4:(al.page.wait_for_timeout(600),al.page.screenshot(path=os.path.join(out,n),clip=box(sel,pad)))
inside=lambda:al.run("(()=>{const d=fxin.querySelector('.vmcard'),R=d.getBoundingClientRect();let bad=[];for(const el of d.querySelectorAll('.kn,button,select,small,.mr')){const r=el.getBoundingClientRect();if(r.width&&(r.right>R.right+.5||r.bottom>R.bottom+.5||r.left<R.left-.5))bad.push(el.className+' '+(el.dataset.c||''))}return 'outside: '+JSON.stringify(bad)+' knobs '+d.querySelectorAll('.kn').length+' card '+Math.round(R.width)+'x'+Math.round(R.height)})()")
print('menu has it',al.run("Object.keys(MODT).join(',')"))
shot('vm_empty.png');print('empty',inside())
# map three outputs with the target picker: click the add button, then a knob
def addout(sel):
    al.page.click('.vmcard [data-mo="map"]');al.page.wait_for_timeout(200);al.page.click(sel);al.page.wait_for_timeout(300)
knobs=json.loads(al.run("JSON.stringify([...fxin.querySelectorAll('.dev.fxd [data-c]')].slice(0,10).map(e=>e.dataset.c))"));print('knobs',knobs)
for k in knobs[:3]: addout('.dev.fxd [data-c="%s"]'%k)
al.page.click('#fxin .modcol .devh .mch');al.page.wait_for_timeout(200)
print('routes',al.run("JSON.stringify(S.tracks[0].mods[0].routes.map(r=>[r.pid.split(':').slice(2).join(':'),r.pt,r.at,r.d]))"))
shot('vm_outputs.png');print('outputs',inside())
v0=al.run("JSON.stringify(S.tracks[0].fx.map(f=>f.p))");al.page.wait_for_timeout(700);v1=al.run("JSON.stringify(S.tracks[0].fx.map(f=>f.p))");print('stopped: controls move',v0!=v1)
# selects of an output
al.page.select_option('.vmcard [data-vmr="1:at"]','d');al.page.select_option('.vmcard [data-vmr="2:pt"]',index=3);al.page.wait_for_timeout(200)
print('after selects',al.run("JSON.stringify(S.tracks[0].mods[0].routes.map(r=>[r.pt,r.at]))"))
# tabs, motion, preset
al.page.click('.vmcard [data-vmb="tab:p"]');shot('vm_particles.png');print('particles tab',inside())
al.page.click('.vmcard [data-vmb="mot:w"]');shot('vm_flow.png');print('flow',inside(),al.run("S.tracks[0].mods[0].p.mot"))
al.page.select_option('.vmcard [data-vms="pre"]','swarm');al.page.wait_for_timeout(300);print('preset',al.run("(()=>{const p=S.tracks[0].mods[0].p;return [p.pre,p.num,p.mot,S.tracks[0].mods[0].routes.length].join(' ')})()"))
# a knob of the card: drag it
kb=json.loads(al.run("(()=>{const r=fxin.querySelector('.vmcard .kn').getBoundingClientRect();return JSON.stringify([r.left+r.width/2,r.top+r.height/2,fxin.querySelector('.vmcard .kn').dataset.c,fxin.querySelector('.vmcard .kn').title])})()"))
m=al.page.mouse;b=al.run("S.tracks[0].mods[0].p.num");m.move(kb[0],kb[1]);m.down();m.move(kb[0],kb[1]-40,steps=6);m.up();print('knob',kb[2],'num',b,'->',al.run("S.tracks[0].mods[0].p.num"),'| tip:',kb[3][:70])
al.page.click('.vmcard [data-vmb="tab:o"]')
# range bars
geo=lambda:json.loads(al.run("(()=>{const cv=fxin.querySelector('canvas.vmcv'),r=cv.getBoundingClientRect(),G=vmGeo(cv.clientWidth);return JSON.stringify({l:r.left,t:r.top,z:r.width/cv.clientWidth,G})})()"))
st=lambda:al.run("(()=>{const p=S.tracks[0].mods[0].p;return [p.x0,p.x1,p.y0,p.y1].map(v=>+(+v).toFixed(3)).join(' ')})()")
g=geo();G=g['G'];z=g['z'];print('range before',st())
m.move(g['l']+G['fx1']*z,g['t']+G['by']*z);m.down();m.move(g['l']+(G['fx0']+(G['fx1']-G['fx0'])*.6)*z,g['t']+G['by']*z,steps=5);m.up();print('x end ',st())
m.move(g['l']+G['bx']*z,g['t']+G['fy0']*z);m.down();m.move(g['l']+G['bx']*z,g['t']+(G['fy0']+(G['fy1']-G['fy0'])*.3)*z,steps=5);m.up();print('y end ',st())
shot('vm_range.png');al.run("undo();undo();1");print('undone',st())
# depth chip: drag sideways, double-click flips, x removes
r=json.loads(al.run("(()=>{const r=fxin.querySelector('.vmcard .mr b').getBoundingClientRect();return JSON.stringify([r.left+4,r.top+4])})()"))
m.move(r[0],r[1]);m.down();m.move(r[0]+60,r[1],steps=5);m.up();print('depth after drag',al.run("S.tracks[0].mods[0].routes[0].d"))
# play: the field follows the song time; same place after a restart
al.run("pos=0;1");al.page.keyboard.press('Space');al.page.wait_for_timeout(1500);print('playing',al.run("!!play.on"))
shot('vm_playing.png')
a=al.run("(()=>{const m=S.tracks[0].mods[0],P=vmPar(m),F=vmAt(m,2.5,P);return [F.x[0],F.y[0],F.x[1]].join(',')})()")
al.page.keyboard.press('Space');al.page.wait_for_timeout(300)
b=al.run("(()=>{const m=S.tracks[0].mods[0],P=vmPar(m);vmAt(m,9,P);vmAt(m,.4,P);const F=vmAt(m,2.5,P);return [F.x[0],F.y[0],F.x[1]].join(',')})()");print('same field at the same song time after jumping about',a==b,a)
# live: while the song plays, and loops, the control is where the export would put it at that song time
al.run("(()=>{const t=S.tracks[0],m=t.mods[0];m.routes.push({pid:'t:'+t.id+':pan',d:1,pt:0,at:'x'});S.loop=true;S.loopRange={id:'vmtest',a:0,b:4};pos=0;renderFx();return 1})()")
al.page.keyboard.press('Space');al.page.wait_for_timeout(400)
al.run("window._vm=[];window._vmi=setInterval(()=>{if(!play.on)return;const t=S.tracks[0];vmSt(t.mods[0]).fn=-1;modTick(performance.now());const b=curDisp(),a=vmOffSums().get('t:'+t.id+':pan');_vm.push([b,t.pan,vmOffVal(a,secOf(b),[0,0,0,0,0])])},40);1")
al.page.wait_for_timeout(5200);al.run("clearInterval(_vmi);1")
L=json.loads(al.run("JSON.stringify(_vm)"));beats=[q[0] for q in L];wraps=sum(1 for i in range(1,len(beats)) if beats[i]<beats[i-1])
print('live vs export value: samples',len(L),'loop wraps',wraps,'biggest difference in pan',round(max(abs(q[1]-q[2]) for q in L),5),'pan range',round(min(q[1] for q in L),2),round(max(q[1] for q in L),2))
al.page.keyboard.press('Space');al.run("(()=>{const t=S.tracks[0];t.mods[0].routes.pop();S.loop=false;S.loopRange=null;renderFx();return 1})()");al.page.wait_for_timeout(300)
# eight outputs is the limit
for k in knobs[3:10]: 
    if al.run("!!fxin.querySelector('.vmcard [data-mo=\"map\"]')"): addout('.dev.fxd [data-c="%s"]'%k)
print('routes now',al.run("S.tracks[0].mods[0].routes.length"),'add button there',al.run("!!fxin.querySelector('.vmcard [data-mo=\"map\"]')"))
al.run("fxin.scrollLeft=0;1");shot('vm_many.png');print('many',inside())
al.page.screenshot(path=os.path.join(out,'vm_panel.png'),clip=json.loads(al.run("(()=>{const r=document.querySelector('#fx').getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,width:Math.min(1500,r.width),height:r.height})})()")))
al.page.click('.vmcard [data-mo="pow"]');al.page.wait_for_timeout(200);print('off',al.run("S.tracks[0].mods[0].off"))
al.page.click('.vmcard [data-mo="del"]');al.page.wait_for_timeout(200);print('removed',al.run("S.tracks[0].mods.length"))
print('errors',al.errors);al.stop()
