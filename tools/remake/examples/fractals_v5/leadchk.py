from eng import *
import song,librosa
al=start();R=song.recipe()
for t in R['tracks']:
    if t['name'] in('Lead question','Lead answer'):t['fx']=[]     # dry, to read the notes
build(al,R)
for n in ['Lead question','Lead answer']:
    x,_=al.render(b0=song.bar(73),b1=song.bar(81),only=n,single=True);m=x.mean(0)
    f0,vf,vp=librosa.pyin(m,fmin=200,fmax=1200,sr=SR,frame_length=2048,hop_length=256)
    st=SPB/4*SR/256;seq=[]
    for i in range(128):
        seg=f0[int(i*st+st*.25):int(i*st+st*.9)];seg=seg[~np.isnan(seg)]
        seq.append(librosa.hz_to_note(np.median(seg)) if len(seg)>2 else '.')
    print(n);[print('  bar',73+b,' '.join(s.ljust(3) for s in seq[b*16:(b+1)*16])) for b in range(8)]
al.stop()
