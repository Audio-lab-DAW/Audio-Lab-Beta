"""Task D3: compare two runs of tools/ui-tests/taskD3.py.  python3 tools/ui-tests/taskD3_compare.py BEFORE_OUT AFTER_OUT [v]
Prints: text that is off the scale (sizes 11, 12, 13, 15; weights 400, 500, 600; Inter, or mono), numbers without equal-width digits,
every element shown in mono, text that is newly cut off or spills out of its box, hit targets whose size changed or that moved,
text that newly overlaps other text, labels whose capitalisation should be looked at, and scroll areas that newly scroll.
Not counted as off the scale: glyphs used as icons (no letter or digit), the wordmark, the Aa sample card, the enlarged preview in Controls."""
import sys,json,re,collections
B=json.load(open(sys.argv[1]+'/census.json'));A=json.load(open(sys.argv[2]+'/census.json'));V=len(sys.argv)>3
print('errors after:',A['errs'])
EX=re.compile(r'\.wm[ALPS]?\b|\.abW\b|\.navAtom|\.tic\b|\.qk\b|\.qwerty|\.scic\b|#hczEd')
glyph=lambda t:not re.search(r'[A-Za-z0-9]',t.replace('pseudo ',''))
bad=collections.Counter();badex={};nt=collections.Counter();mono={};tot=0
clipN=collections.OrderedDict();hitS=collections.OrderedDict();hitM=collections.Counter();scrN=collections.OrderedDict();ovN=collections.OrderedDict();case=collections.OrderedDict();missing=[]
for sc,a in A['res'].items():
    b=B['res'].get(sc)
    for t in a['text']:
        tot+=1
        if glyph(t['t']) or EX.search(t['p']):continue
        if t['fs'] not in(11,12,13,15) or t['fw'] not in(400,500,600) or t['ff'] not in('Inter','ui-monospace') or t['z']!=1:
            k=(t['p'].split('>',1)[-1][-70:],t['fs'],t['fw'],t['ff'],round(t['z'],2));bad[k]+=1;badex.setdefault(k,(sc,t['t']))
        if re.search(r'\d',t['t']) and 'tabular' not in t['num']:nt[t['p'][-50:]]+=1
        if t['ff']!='Inter':mono.setdefault(t['p'].split('>',1)[-1][-60:],(sc,t['t']))
    if not b:missing.append(sc);continue
    bup=set(t['p'] for t in b['text'] if t.get('up'))
    for t in a['text']:
        if t['p'] in bup and not t.get('up') and re.search(r'[A-Za-z]',t['t']):
            x=t['t']
            if x[0].islower() or (len(re.sub(r'[^A-Za-z]','',x))>3 and x.upper()==x):case.setdefault((t['p'].split('>',1)[-1][-60:],x[:30]),sc)
    bk=collections.defaultdict(list)
    for t in b['text']:
        if 'r' in t:bk[(t['p'],t['t'])].append(t)
    for t in a['text']:
        if 'r' not in t or not t['on']:continue
        cand=bk.get((t['p'],t['t']),[]);o=cand.pop(0) if cand else None
        for f in('cx','cy','sx','el'):
            lim=0.6 if f!='el' else 0
            if t[f]>lim and (o is None or o[f]<=lim):
                clipN.setdefault((f,t['p'].split('>',1)[-1][-80:],t['t'][:24]),[sc,t[f],o[f] if o else None,t['fs'],o['fs'] if o else None])
    if len(a['hit'])==len(b['hit']) and all(x['p']==y['p'] for x,y in zip(a['hit'],b['hit'])):
        for x,y in zip(a['hit'],b['hit']):
            dw,dh=x['r'][2]-y['r'][2],x['r'][3]-y['r'][3];dx,dy=x['r'][0]-y['r'][0],x['r'][1]-y['r'][1]
            if abs(dw)>0.5 or abs(dh)>0.5:hitS.setdefault((x['p'].split('>',1)[-1][-80:],round(dw,1),round(dh,1)),[sc,y['r']])
            elif abs(dx)>0.5 or abs(dy)>0.5:hitM[(x['p'].split('>',1)[-1][-70:],round(dx),round(dy))]+=1
    else:
        hitS.setdefault(('LIST DIFFERS',len(a['hit']),len(b['hit'])),[sc])
    bo=set((x[0],x[1],x[2],x[3]) for x in b.get('ov',[]))
    for x in a.get('ov',[]):
        if (x[0],x[1],x[2],x[3]) not in bo:ovN.setdefault((x[0].split('>',1)[-1][-60:],x[1],x[2].split('>',1)[-1][-60:],x[3]),[sc,x[4]])
    bs={x['p']:x for x in b['scr']}
    for x in a['scr']:
        o=bs.get(x['p'])
        if o and ((x['x']>1 and o['x']<=1) or (x['y']>1 and o['y']<=1)):scrN.setdefault(x['p'][-90:],[sc,o['x'],o['y'],x['x'],x['y']])
print('texts',tot,'scenes',len(A['res']),'missing before',missing)
print('OFF SCALE kinds',len(bad),'instances',sum(bad.values()))
for k,v in sorted(bad.items(),key=lambda x:-x[1])[:400 if V else 60]:print('  ',v,k,badex[k])
print('NOT TABULAR',len(nt),list(nt.items())[:20])
print('MONO');[print('  ',k,v) for k,v in mono.items()]
print('NEW CLIP/SPILL',len(clipN));[print('  ',k,v) for k,v in list(clipN.items())[:400 if V else 80]]
hs=collections.Counter();[hs.__setitem__((re.sub(r'^.*>','',k[0]) if k[0]!='LIST DIFFERS' else k[0],k[1]!=0,k[2]),hs[(re.sub(r'^.*>','',k[0]) if k[0]!='LIST DIFFERS' else k[0],k[1]!=0,k[2])]+1) for k in hitS]
print('HIT SIZE CHANGED',len(hitS),'(element, width changed, height change): count');[print('  ',k,v) for k,v in sorted(hs.items(),key=lambda x:-abs(x[0][2]))[:400 if V else 70]]
print('HIT MOVED kinds',len(hitM),'n',sum(hitM.values()));[print('  ',v,k) for k,v in sorted(hitM.items(),key=lambda x:-x[1])[:400 if V else 50]]
print('NEW TEXT OVERLAPS',len(ovN));[print('  ',k,v) for k,v in list(ovN.items())[:400 if V else 60]]
print('CASE TO CHECK',len(case));[print('  ',k,v) for k,v in case.items()]
print('NEW SCROLL',len(scrN));[print('  ',k,v) for k,v in scrN.items()]
