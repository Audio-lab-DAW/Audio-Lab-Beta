# log-frequency spectrograms (uint8, dB -84..0 relative to the mix's peak) of the mix and each stem, for the pick page
import numpy as np, json, base64, sys
SR=44100; N=4096; H=2048; ROWS=72; F0,F1=32.,16000.
def bands():
    f=np.fft.rfftfreq(N,1/SR); e=np.geomspace(F0,F1,ROWS+1); W=np.zeros((ROWS,len(f)))
    for r in range(ROWS):
        lo,hi=e[r],e[r+1]; c=np.sqrt(lo*hi)
        m=(f>=lo)&(f<hi)
        if m.sum()==0: W[r,np.argmin(abs(f-c))]=1
        else: W[r,m]=1/m.sum()
    return W
W=bands(); win=np.hanning(N)
def spec(x):
    m=x.mean(0); n=1+(len(m)-N)//H
    fr=np.lib.stride_tricks.sliding_window_view(m,N)[::H][:n]*win
    P=np.abs(np.fft.rfft(fr,axis=1))**2
    return W@P.T  # rows x cols (power)
def enc(P,ref):
    d=10*np.log10(P/ref+1e-12); d=np.clip((d+84)/84,0,1)
    return base64.b64encode((d[::-1]*255).astype(np.uint8).tobytes()).decode()  # row 0 = top = high freq
out={}
mix=np.load('/home/claude/sg1w/out/mix.npy'); Pm=spec(mix); ref=np.percentile(Pm,99.9)
out['mix']=enc(Pm,ref); out['cols']=Pm.shape[1]; out['rows']=ROWS; out['hop']=H/SR
for k in sys.argv[1:]:
    import os
    p=f'/home/claude/sg1w/out/stems_{k}.npy'
    if os.path.exists(p): st=np.load(p)
    else:
        f=np.fromfile(f'/home/claude/sg1w/out/stems_{k}.f32',np.float32); n=mix.shape[1]; st=f.reshape(-1,2,n)
    out[k]=[enc(spec(s),ref) for s in st]
    out[k+'_db']=[round(float(10*np.log10(np.mean(s.astype(np.float64)**2)+1e-20)),2) for s in st]
json.dump(out,open('/home/claude/sg1w/build/spec.json','w'))
print(out['cols'],{k:len(out[k]) for k in sys.argv[1:]}, len(json.dumps(out)))
