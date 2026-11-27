"""Shared set-up for the AE2 measurements (task AE2, performance and playing latency).
Opens index.html of this checkout headless through tools/remake/alab.py and builds the Fractals remake v6."""
import sys,os,json
HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.abspath(os.path.join(HERE,'../../..'))
sys.path.insert(0,os.path.join(ROOT,'tools/remake'));SONG=os.path.join(ROOT,'tools/remake/examples/fractals_v6');sys.path.insert(0,SONG)
from alab import AudioLab
def start():
    return AudioLab(os.path.join(ROOT,'index.html')).start()
def fractals(al,copies=1):
    cwd=os.getcwd();os.chdir(SONG)
    try:
        import song;R=song.recipe()
    finally:os.chdir(cwd)
    if copies>1:
        base=R['tracks'];out=[]
        for k in range(copies):
            for t in base:
                t2=json.loads(json.dumps(t))
                if k:t2['name']=t['name']+' x'+str(k+1)
                if k and t2.get('grp'):t2['grp']=t['grp']+' x'+str(k+1)
                if k and t2.get('sends'):t2['sends']={s+' x'+str(k+1):v for s,v in t2['sends'].items()}
                out.append(t2)
        R['tracks']=out
    al.build(R)
    m={t['name']:{k:t[k] for k in ('grp','sends') if k in t} for t in R['tracks']}
    al.run("(()=>{const M="+json.dumps(m)+",by={};for(const t of S.tracks)by[t.name]=t;for(const t of S.tracks){const o=M[t.name]||{};if(o.grp&&by[o.grp])t.grp=by[o.grp].id;if(o.sends){t.sends={};for(const k in o.sends)if(by[k])t.sends[by[k].id]=o.sends[k]}}changed(true);return 1})()")
    return R
