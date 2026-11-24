"""Fractals v2: real note transcription of the melodic stems (other+vocals) -> melody.json"""
from common import *
NB=288;NS=NB*16;step=SPB/4;HOP=512;FMIN=librosa.note_to_hz('A1');NO=7;BPS=3
x=mono(stem('other'))+mono(stem('vocals'))
C=np.abs(librosa.cqt(x,sr=SR,hop_length=HOP,fmin=FMIN,n_bins=12*BPS*NO,bins_per_octave=12*BPS,filter_scale=0.8))
S=np.maximum.reduce([C[0::3],C[1::3],C[2::3]])**.7        # semitones from A1 (midi 33)
nsem=S.shape[0];sal=np.zeros_like(S)
for o,w in zip([0,12,19,24,28],[1,.6,.45,.35,.25]):
    sal[:nsem-o]+=w*S[o:]
fr=SR/HOP
M=np.zeros((NS,nsem))
for i in range(NS):
    a=int((T0+i*step)*fr);b=int((T0+(i+1)*step)*fr);a2=a+int((b-a)*.15);b2=max(a2+1,a+int((b-a)*.85))
    if a2<sal.shape[1]:M[i]=np.median(sal[:,a2:min(b2,sal.shape[1])],1)
floor=np.percentile(M.max(1),30);ref=np.percentile(M.max(1),95)
notes_at=[[] for _ in range(NS)]
for i in range(NS):
    m=M[i]
    if m.max()<floor*.8:continue
    pk=[j for j in range(1,nsem-1) if m[j]>=m[j-1] and m[j]>m[j+1] and m[j]>.30*m.max()]
    pk=sorted(pk,key=lambda j:-m[j])[:3]
    for j in pk:
        if 33+j<=88:notes_at[i].append((33+j,float(m[j]/ref)))
# link into notes
out=[];active={}
for i in range(NS+1):
    cur={p:v for p,v in notes_at[i]} if i<NS else {}
    for p in list(active):
        if p not in cur:
            st,vs=active.pop(p);
            out.append((p,st,i-st,float(np.mean(vs))))
    for p,v in cur.items():
        if p in active:active[p][1].append(v)
        else:active[p]=[i,[v]]
# merge notes of the same pitch separated by a 1-step gap
out.sort(key=lambda n:(n[0],n[1]));mg=[]
for n in out:
    if mg and mg[-1][0]==n[0] and n[1]-(mg[-1][1]+mg[-1][2])<=1:
        p,s,l,v=mg[-1];mg[-1]=(p,s,n[1]+n[2]-s,max(v,n[3]))
    else:mg.append(n)
mg=[n for n in mg if n[3]>.06]
print('notes',len(mg),'steps with notes',sum(1 for a in notes_at if a))
json.dump([[int(p),int(s),int(l),round(min(1,v),3)] for p,s,l,v in sorted(mg,key=lambda n:n[1])],open('melody.json','w'))
import collections;print(collections.Counter((p-33)%12 for p,_,_,_ in mg).most_common())
print('by register',sum(1 for n in mg if n[0]<=52),sum(1 for n in mg if 53<=n[0]<=67),sum(1 for n in mg if n[0]>=68))
