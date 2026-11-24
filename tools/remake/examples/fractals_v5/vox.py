"""the original's vocal samples (Demucs vocals stem), only where the voice is clearly present"""
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
import song
REG=[(1,16),(25,26),(70,70),(144,144),(148,150),(190,190),(208,208),(254,255),(270,272),(286,288)]
def load(al,R):
    v,sr=sf.read('/home/claude/remake/fractals/stems/htdemucs/ref/vocals.wav');v=v.mean(1);spb=60/145;cl=[]
    for a,c in REG:
        x=v[int((a-1)*4*spb*sr):int(c*4*spb*sr)];y=resample_poly(x,1,2).astype(np.float32)
        bid=al.add_audio(y[None,:],sr//2);d=len(y)/(sr//2)
        cl.append({'start':song.bar(a),'len':round(d*song.BPM/60,3),'name':f'Vocal {a}','buf':bid,'dur':d,'gain':0,'fi':.05,'fo':.25})
    R['tracks'].append({'name':'Vocals (original)','kind':'audio','color':'#ffd166','icon':'mic-vocal','vol':.8,'sends':{'Reverb (shared)':.15},
                        'fx':[{'type':'eq','p':{'an':'off','out':4}}],'clips':cl})
