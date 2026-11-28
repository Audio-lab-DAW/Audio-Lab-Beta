# task SG1: gathers the measured spectrograms (spec.py) and chunk timings (run.py in Chromium for the quick split, chunks_node.mjs for
# HTDemucs with onnxruntime-web 1.20.1 WASM) into sg1-data.json, which the pick page fetches.
import json, sys, os
W=sys.argv[1] if len(sys.argv)>1 else '/home/claude/sg1w'
sp=json.load(open(W+'/build/spec.json')); ti=json.load(open(W+'/out/timing_iso.json'))
def node(k,th):
    j=json.load(open(f'{W}/out/full_{k}_{th}.json')); return {'init':round(j['init']),'runs':[round(e['run']) for e in j['ev']],'add':[round(e['add'],1) for e in j['ev']],'ST':j['ST'],'N':j['N'],'OV':j['OV'],'nc':j['nc'],'rssMB':round(j['rss']/1e6)}
q=ti['quick']; ends=[round(e[0]) for e in q['tl']]
D={'clip':{'song':'Fractals','b0':ti['B0'],'b1':ti['B1'],'bpm':ti['bpm'],'len':ti['len'],'sr':ti['sr']},
   'spec':sp,'stft':ti['stft'],
   'T':{'quick':{'ends':ends,'seg':262144,'tot':round(q['tot'])},'n4':node('n4',2),'n6':node('n6',2),'n4_1':node('n4',1)},
   'machine':'cloud container, 2 cores (x86-64), headless Chromium 1.x / Node 22; not the user\'s Mac'}
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),'sg1-data.json')
json.dump(D,open(out,'w'),separators=(',',':'));print(out,os.path.getsize(out))
print(json.dumps(D['T'])[:900])
