"""measure every track alone in its busiest 8 bars; print peak and RMS"""
from eng import *
import song,sys
al=start();R=song.recipe();build(al,R)
print(al.run("JSON.stringify(S.tracks.filter(t=>t.kind!=='inst').map(t=>[t.name,t.kind]))"))
out={}
for t in R['tracks']:
    if not t.get('clips'):continue
    c=max(t['clips'],key=lambda c:len(c['notes'])*(1 if c['start']>=128 else .5))
    b0=c['start'];b1=b0+min(32,c['len'])
    x,_=al.render(b0=b0,b1=b1,only=t['name'],single=True,tail=1)
    out[t['name']]=dict(peak=pk(x),rms=float(db(x)),bar=int(b0//4+1))
    print('%-16s bar %3d  peak %6.1f dB  rms %6.1f dB'%(t['name'],b0//4+1,20*np.log10(pk(x)+1e-9),db(x)),flush=True)
json.dump(out,open('calib.json','w'),indent=1)
al.stop()
