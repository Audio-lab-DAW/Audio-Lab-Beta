from common import *
FMIN=librosa.note_to_hz('A1');BPS=3;NOCT=7
NAMES='C C# D D# E F F# G G# A A# B'.split()
def nn(m):return NAMES[m%12]+str(m//12-1)
def cqt_steps(k,b0,b1,sub=1):
    """per-16th (or finer) CQT magnitude: returns (steps, semitones) from A1 up, in dB-ish linear magnitude"""
    x=mono(cut(k,b0-1,b1+1));hop=256
    C=np.abs(librosa.cqt(x,sr=SR,hop_length=hop,fmin=FMIN,n_bins=12*BPS*NOCT,bins_per_octave=12*BPS,filter_scale=0.8))
    # collapse 3 bins per semitone -> take max around centre
    S=np.maximum.reduce([C[0::3],C[1::3],C[2::3]]) if BPS==3 else C
    nst=int((b1-b0)*4*sub);out=np.zeros((nst,S.shape[0]))
    for s in range(nst):
        ta=(1+s/(4*sub))*SPB;tb=(1+(s+1)/(4*sub))*SPB;a=int(ta*SR/hop);b=int(tb*SR/hop)
        a2=a+int((b-a)*.15);b2=a+max(a2-a+1,int((b-a)*.85));out[s]=np.median(S[:,a2:b2],1)
    return out   # midi of bin j = 33+j (A1=33)
def salience(M,nh=5):
    """harmonic summation: f0 salience per semitone"""
    n=M.shape[1];sal=np.zeros_like(M);offs=[0,12,19,24,28];w=[1,.6,.45,.35,.25]
    for h,(o,ww) in enumerate(zip(offs[:nh],w)):
        if o<n:sal[:,:n-o]+=ww*M[:,o:]
    return sal
