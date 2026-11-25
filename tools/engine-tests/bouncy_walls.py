"""Bouncy Notes walls (v0.177). python3 tools/engine-tests/bouncy_walls.py [index.html]"""
import sys,numpy as np,json
import os;sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('ver',al.version)
al.build({'tempo':120,'tracks':[{'name':'T','preset':'pluck','clips':[{'start':0,'len':16,'notes':[{'p':60,'s':0,'l':1,'v':.9},{'p':67,'s':4,'l':1,'v':.6}]}]}]})
rms=lambda x:float(np.sqrt((x**2).mean()))
al.run("(()=>{const t=S.tracks[0];t.fx.unshift(mkFx('bnotes'));changed(true);return 1})()")
N=lambda:json.loads(al.run("(()=>{const t=S.tracks[0];return JSON.stringify(mfxNotes(t,t.clips[0].notes).map(n=>[n.p,+n.s.toFixed(4),+n.v.toFixed(3)]))})()"))
a=N();x0,sr=al.render(b0=0,b1=16)
# a wall that slopes down to the right, over key 60, half way up; and a flat one over key 67
al.run("S.tracks[0].fx[0].p.walls=[[57,.55,63,.35],[66,.3,68,.3]];1");b=N();x1,_=al.render(b0=0,b1=16);x2,_=al.render(b0=0,b1=16)
print('notes without / with walls',len(a),len(b),'| same times',[n[1] for n in a]==[n[1] for n in b],'| same loudness',[n[2] for n in a]==[n[2] for n in b])
print('keys without',[n[0] for n in a][:14]);print('keys with   ',[n[0] for n in b][:14])
print('ball 1 is pushed up the keyboard (wall leans right):',b[1][0]>60 and b[2][0]>b[1][0])
print('render: rms',round(rms(x1),4),'peak',round(float(np.abs(x1).max()),3),'nan',bool(np.isnan(x1).any()),'equal twice',bool(np.array_equal(x1,x2)),'differs from no walls',not np.array_equal(x0,x1))
al.run("S.tracks[0].fx[0].p.walls=[[57,.35,63,.55]];1");c=N();print('wall leaning left: keys',[n[0] for n in c if n[1]<4][:10])
al.run("S.tracks[0].fx[0].p.walls=[[57,.95,63,.99]];1");d=N();print('wall above the drop height changes nothing',d==a or [n[0] for n in d]==[n[0] for n in a])
al.run("(()=>{const p=S.tracks[0].fx[0].p;Object.assign(p,FXPRE.bnotes.scatter[1]);p.walls=[[50,.5,70,.2],[40,.3,55,.6],[60,.7,80,.75]];return 1})()");e=N();e2=N()
print('scatter preset with 3 walls: notes',len(e),'same twice',e==e2,'keys in range',min(n[0] for n in e),max(n[0] for n in e),'all in minor pentatonic',all((n[0]%12) in (0,3,5,7,10) for n in e))
al.run("S.tracks[0].fx[0].p.walls=[];1");print('walls removed: as the preset alone',N()==json.loads(al.run("(()=>{const t=S.tracks[0];delete t.fx[0].p.walls;return JSON.stringify(mfxNotes(t,t.clips[0].notes).map(n=>[n.p,+n.s.toFixed(4),+n.v.toFixed(3)]))})()")))
print('errors',al.errors);al.stop()
