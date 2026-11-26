# Bouncy Notes (v0.189): chord steps for Harmony and a rhythm per ball (Auto).  python3 tools/engine-tests/bounce_chords.py [index.html]
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','remake'))
from alab import AudioLab
al=AudioLab(sys.argv[1] if len(sys.argv)>1 else 'index.html');al.start()
print('ver',al.version,'errors after load',al.errors)
NM=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];nm=lambda p:NM[p%12]+str(p//12-1)
def run(p,notes):
    return json.loads(al.run("JSON.stringify(bnRun({p:Object.assign({},BN0,%s)},%s).map(n=>[+n.s.toFixed(4),n.p]))"%(json.dumps(p),json.dumps(notes))))
def chords(out):
    d={}
    for s,p in out:d.setdefault(s,[]).append(p)
    return [(s,' '.join(nm(p) for p in sorted(ps))) for s,ps in sorted(d.items())]
print('--- chord steps I V VI IV, one per bar, triads in C major, a ball on every beat for 16 beats (key C3 held)')
o=run({'sync':'1/4','bmode':'steady','life':30,'harm':'triad','scale':'major','vfade':0,'pg0':'1','pg1':'5','pg2':'6','pg3':'4'},[{'p':60,'s':0,'l':16,'v':.9}])
for s,c in chords(o)[:16]:print('beat %5.2f: %s'%(s,c))
print('--- the same, chords move every 1/2 bar (2 beats), steps I _ VI _ IV V (empty steps left out)')
o=run({'sync':'1/4','bmode':'steady','life':30,'harm':'triad','scale':'major','vfade':0,'pg0':'1','pg2':'6','pg4':'4','pg5':'5','prate':'1/2'},[{'p':60,'s':0,'l':16,'v':.9}])
print(' | '.join('%g: %s'%(s,c) for s,c in chords(o)[:10]))
print('--- minor scale, four-note chords, steps I VI III VII every bar on A2')
o=run({'sync':'1/2','bmode':'steady','life':30,'harm':'7th','scale':'minor','tonic':9,'vfade':0,'pg0':'1','pg1':'6','pg2':'3','pg3':'7'},[{'p':57,'s':0,'l':16,'v':.9}])
print(' | '.join('%g: %s'%(s,c) for s,c in chords(o)[::2][:8]))
print('--- no chord steps: exactly as before (Chords on every beat preset)')
a=run({'sync':'1/2','bmode':'steady','life':8,'harm':'triad','scale':'major','vfade':0,'len':400},[{'p':60,'s':0,'l':8,'v':.9}]);print(chords(a)[:3])
print('--- a rhythm per ball: Auto drops a ball every 1/2 (2 beats) while the key is held; Rhythm 1/4 halving, 2nd ball 1/8 triplet, 3rd 1/8')
B=json.loads(al.run("JSON.stringify(bnBalls(Object.assign({},BN0,{auto:true,ivl:'1/2',sync:'1/4',bmode:'half',r2:'1/8 triplet',r3:'1/8',life:30}),[{p:60,s:0,l:8,v:.9}],.5).map(b=>[b.s,b.tk.slice(0,4).map(t=>+(t/b.sp/.5).toFixed(4))]))"))
for s,t in B:print('ball dropped at beat %g: landings after %s beats'%(s,t))
B=json.loads(al.run("JSON.stringify(bnBalls(Object.assign({},BN0,{auto:true,ivl:'1/2',sync:'1/4',bmode:'half',life:30}),[{p:60,s:0,l:8,v:.9}],.5).map(b=>[b.s,b.tk.slice(0,3).map(t=>+(t/b.sp/.5).toFixed(4))]))"))
print('all Same (as before):',B)
print('--- in a render: Bouncy Notes in front of Pluck, chord steps on; two renders identical')
al.build({'bpm':120,'tracks':[{'name':'P','preset':'pluck','fx':[{'type':'bnotes'}],'clips':[{'start':0,'len':16,'notes':[{'p':60,'s':0,'l':16,'v':.9}]}]}]})
al.run("(()=>{const f=S.tracks[0].fx[0];Object.assign(f.p,FXPRE.bnotes.popc[1]);changed(true)})()")
import numpy as np
x,_=al.render(b0=0,b1=16);y,_=al.render(b0=0,b1=16);print('peak %.3f, identical %s, NaN %s'%(np.abs(x).max(),np.array_equal(x,y),np.isnan(x).any()))
print('presets of the new group',al.run("JSON.stringify(Object.entries(FXPRE.bnotes).filter(([k,v])=>v[0].startsWith('Chord steps')).map(([k,v])=>v[0]))"))
print('errors',al.errors);al.stop()
