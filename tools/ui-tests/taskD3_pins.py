"""Task D3: the line heights to keep.  python3 tools/ui-tests/taskD3_pins.py decl.json out.json census.json [more census files]
A new font size changes the height of a line wherever the line height is a multiple of the size. To keep rows where they were, the
probe run (taskD3.py with CENSUS=taskD3_probe.js on the --probe copy) notes, for every numbered font declaration, the line height its
text had before. This script turns that into pins (declaration number > px), used by tools/edits/taskD3.py --pins=...
Not pinned: declarations whose text had several line heights, and text on several lines that would become cramped (it may grow)."""
import sys,json,collections
decl={d[0]:d for d in json.load(open(sys.argv[1]))};S={}
for f in sys.argv[3:]:
    for sc,v in json.load(open(f))['res'].items():
        for site,x in v['sites'].items():
            s=S.setdefault(int(site),{'v':collections.Counter(),'is':set(),'multi':0,'anc':set(),'ex':x['ex'],'sc':sc})
            s['v'].update(x['v']);s['is'].update(int(i) for i in x['is'] if i!='');s['multi']+=x['multi'];s['anc'].update(int(a) for a in x['anc'])
def changed(i):
    d=decl.get(i);return bool(d) and d[1] in('size','font') and (d[2]!=d[3] or (len(d)>4 and d[4]))
def newsize(s):
    z=[decl[i][3] for i in s['is'] if i in decl and isinstance(decl[i][3],(int,float))];return max(z) if z else 0
P={};rep=collections.Counter();why={}
def val(s):
    tot=sum(s['v'].values());k,c=s['v'].most_common(1)[0]
    return float(k) if c>=tot*0.95 else None
for n,s in S.items():
    if not any(changed(i) for i in s['is']):continue
    v=val(s)
    if v is None:rep['changed, several line heights']+=1;why[n]=('several',dict(s['v']),s['ex'],s['sc']);continue
    if s['multi'] and v<1.2*newsize(s):rep['changed, text on several lines would be cramped: left to grow']+=1;why[n]=('cramped',v,newsize(s),s['ex'],s['sc']);continue
    P[n]=v
n0=len(P)
while True:
    add={}
    for n,s in S.items():
        if n in P or n in why:continue
        if s['anc']&set(P):
            v=val(s)
            if v is None:why[n]=('protect: several',dict(s['v']),s['ex'],s['sc']);continue
            add[n]=v
    if not add:break
    P.update(add)
json.dump(P,open(sys.argv[2],'w'),sort_keys=True)
print('sites seen',len(S),'pins for changed sizes',n0,'pins to protect what sits inside them',len(P)-n0,dict(rep))
for n,w in why.items():print('  not pinned',n,decl.get(n),w)
