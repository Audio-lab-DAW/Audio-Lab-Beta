import os,sys;sys.path.insert(0,'/home/claude/audio-lab-beta/tools/remake')
import numpy as np, soundfile as sf, librosa, json
from measure import *
BPM=145.0;SPB=60/BPM;T0=0.0;SR=44100
ST='stems/htdemucs/ref/'
_cache={}
def stem(k):
    if k not in _cache:
        _cache[k]=load('ref.wav' if k=='mix' else ST+k+'.wav',SR)
    return _cache[k]
def cut(k,b0,b1):
    x=stem(k);a=int(round((T0+b0*SPB)*SR));b=int(round((T0+b1*SPB)*SR));return x[:,max(0,a):b]
def bar(n):return (n-1)*4   # bar number (1-based) -> beat
