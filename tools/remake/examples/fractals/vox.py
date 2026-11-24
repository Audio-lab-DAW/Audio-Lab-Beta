"""load the original's vocal samples (Demucs vocals stem) into the app, only where the voice is clearly present"""
from common import *
import build
from scipy.signal import resample_poly
REG=[(1,16),(25,26),(70,70),(144,144),(148,150),(190,190),(208,208),(254,255),(270,272),(286,288)]
VSR=22050
def load(al):
    v=mono(stem('vocals'));out=[]
    for a,c in REG:
        x=v[int(bar(a)*SPB*SR):int(bar(c+1)*SPB*SR)]
        y=resample_poly(x,1,2).astype(np.float32)
        bid=al.add_audio(y[None,:],VSR);out.append((bar(a),bar(c+1)-bar(a),bid,len(y)/VSR))
    build.VOX=out;return out
