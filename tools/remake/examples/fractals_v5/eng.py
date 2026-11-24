import sys,json,os;sys.path.insert(0,'/home/claude/audio-lab-beta/tools/remake')
import numpy as np,soundfile as sf
from alab import AudioLab
BPM=148.0;SPB=60/BPM;SR=44100
APP='/home/claude/audiolab/index.html'
def start():return AudioLab(APP).start()
def route(al,R):
    """after build: groups, sends, icons (by track name)"""
    m={t['name']:{k:t[k] for k in ('grp','sends','icon','iconCol') if k in t} for t in R['tracks']}
    al.run("(()=>{const M="+json.dumps(m)+",by={};for(const t of S.tracks)by[t.name]=t;for(const t of S.tracks){const o=M[t.name]||{};if(o.grp&&by[o.grp])t.grp=by[o.grp].id;if(o.sends){t.sends={};for(const k in o.sends)if(by[k])t.sends[by[k].id]=o.sends[k]}if(o.icon)t.icon='i:'+o.icon;if(o.iconCol)t.iconCol=o.iconCol}changed(true);return 1})()")
def build(al,R):
    al.build(R);route(al,R)
def db(x):return 20*np.log10(np.sqrt(np.mean(np.square(x)))+1e-12)
def pk(x):return float(np.abs(x).max())
