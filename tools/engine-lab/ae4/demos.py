# Task AE4: the "today" half of every A/B demo on the pick page, rendered by the app itself (headless, its own engine).
#   python3 tools/engine-lab/ae4/demos.py [index.html]   -> tools/engine-lab/ae4/page/demos/*.wav (32 kHz, 16-bit)
# The improved half of each demo is computed in the page (pick.html) from the same notes.
import sys,os,json,numpy as np,wave
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(HERE,'..','..','remake'))
from alab import AudioLab
idx=sys.argv[1] if len(sys.argv)>1 else 'index.html';SR=32000;OUT=os.path.join(HERE,'page','demos');os.makedirs(OUT,exist_ok=True)
al=AudioLab(idx);al.start();print('version',al.version)
def wav(name,x,stereo=False):
    x=np.asarray(x,dtype=np.float64);x=x if stereo else x.mean(0);pk=np.abs(x).max();x=x/pk*.7 if pk>0 else x
    d=(np.clip(x,-1,1)*32767).astype('<i2');ch=2 if stereo else 1
    with wave.open(os.path.join(OUT,name+'.wav'),'wb') as w:w.setnchannels(ch);w.setsampwidth(2);w.setframerate(SR);w.writeframes((d.T.reshape(-1) if stereo else d).tobytes())
    print(name,'%.2f s'%(x.shape[-1]/SR),'peak before normalising %.1f dBFS'%(20*np.log10(max(pk,1e-9))))
def go(tr,b1,tail=0,bpm=145):al.build({'bpm':bpm,'tracks':tr});x,_=al.render(b0=0,b1=b1,sr=SR,tail=tail);return x
# the acid line of the app's own psy demo (AS pattern, F, 16ths), Acid preset 'psy' with cut 520 and dist 65 as in the demo
AS=[[0,.9],[0,.6],[12,.95],[0,.6],[-1,.7],[0,.6],[7,.95],[0,.6],[3,.7],[0,.6],[12,.95],[11,.65],[0,.7],[8,.95],[7,.7],[0,.6]]
acid=[{'p':41+iv,'s':k*.25,'l':.27 if (v>.9 and k%4<3) else .2,'v':v} for r in range(2) for k,(iv,v) in enumerate(AS) for _ in [0] ]
acid=[dict(n,s=n['s']+r*4) for r in range(2) for n in [{'p':41+iv,'s':k*.25,'l':.27 if (v>.9 and k%4<3) else .2,'v':v} for k,(iv,v) in enumerate(AS)]]
wav('acid_today',go([{'name':'A','preset':'acid','inst':{'cut':520,'dist':65},'clips':[{'start':0,'len':8,'notes':acid}]}],8,.3))
# rolling bass, K-B-B-B on F1, two bars, Psy Bass default
bass=[{'p':29,'s':b+o,'l':.2,'v':[.92,.74,.84][i]} for b in range(8) for i,o in enumerate((.25,.5,.75))]
wav('bass_today',go([{'name':'B','preset':'psyb','clips':[{'start':0,'len':8,'notes':bass}]}],8,.2))
# kick: Kick designer psyzap as in the demo song (tune 29, len .24, click 60, drive 45), four hits
wav('kick_today',go([{'name':'K','preset':'kick','inst':{'tune':29,'len':.24,'tail':14,'click':60,'drive':45,'start':2600},'clips':[{'start':0,'len':4,'notes':[{'p':36,'s':b,'l':.25,'v':.97} for b in range(4)]}]}],4,.3))
# supersaw chord: Venom init, oscillator A unison 7, detune .3; F minor chord, 2 beats at 120
ch=[{'p':p,'s':0,'l':3,'v':.8} for p in (53,56,60,65)]
wav('saw_today',go([{'name':'V','preset':'venom','inst':{'aun':7,'aud':.3},'clips':[{'start':0,'len':4,'notes':ch}]}],4,.5,bpm=120),stereo=True)
# reverb: a short synthetic pluck (same formula as the page) through Space reverb, decay 3.2 s, mix 35 %
t=np.arange(int(2.4*SR))/SR;pl=np.zeros_like(t)
for k,(f,at) in enumerate([(523.25,0),(659.25,.375),(783.99,.75),(1046.5,1.125)]):
    m=t>=at;tt=t[m]-at;pl[m]+=.5*np.exp(-tt*18)*(np.sin(2*np.pi*f*tt)+.35*np.sin(4*np.pi*f*tt)+.15*np.sin(6*np.pi*f*tt))
bid=al.add_audio(np.vstack([pl,pl]).astype(np.float32),SR)
al.build({'bpm':120,'tracks':[{'name':'R','kind':'audio','fx':[{'type':'reverb','p':{'decay':3.2,'mix':35,'predelay':15}}],'clips':[{'start':0,'len':9,'buf':bid,'dur':len(pl)/SR,'gain':0,'fi':0,'fo':0}]}]})
x,_=al.render(b0=0,b1=9,sr=SR);wav('verb_today',x,stereo=True)
al.stop()
