from eng import *
import song
from scipy.signal import butter,sosfiltfilt
al=start();R=song.recipe();build(al,R)
ids=[al.tid(n) for n in ['Kick & Bass','Kick','Bass sub','Bass top']]
x,_=al.render(b0=song.bar(81),b1=song.bar(81)+4,tracks=ids,single=True);m=x.mean(0);sf.write('out/kb.wav',x.T,SR)
lo=sosfiltfilt(butter(4,120,'low',fs=SR,output='sos'),m);hi=m-lo
n=int(SPB*SR);st=int(.005*SR)
for nm,sig in [('full',m),('<120Hz',lo),('>120Hz',hi)]:
    e=[np.abs(sig[n+i:n+i+st]).max() for i in range(0,n,st)]   # second beat (sidechain running)
    print(nm.ljust(7),' '.join('%.2f'%v for v in e))
print('16th =',round(SPB/4*1000),'ms; each value = 5 ms')
al.stop()
