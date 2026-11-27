"""IN-G: the draw time of each dynamics display (median of 200 draws at 2x, pink noise playing through the device), for two files.
  python3 tools/design-lab/in/draw_cost_g.py a.html [b.html]"""
import sys, os, math, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'remake'))
from alab import AudioLab
DEV = [('comp', {'threshold': -30, 'ratio': 4}, 300, 235), ('limit', {'gain': 6, 'ceil': -1}, 520, 200), ('gate', {'thr': -30}, 540, 200),
       ('ott', {}, 520, 200), ('mband', {'t1': -40, 't2': -40, 't3': -40}, 580, 200), ('deess', {'thr': -50}, 560, 200)]
for F in sys.argv[1:]:
    al = AudioLab(os.path.abspath(F), 2194, 1139); al.start(); R = al.run
    R("UI.lite=false;UI.headroom=-6;0"); SR = int(R('ctx.sampleRate')); n = 20 * SR
    rng = np.random.default_rng(1); x = (rng.standard_normal(n) * .1).astype(np.float32)
    bid = al.add_audio(np.vstack([x, x]), SR); out = []
    for ty, p, w, h in DEV:
        R("stop();0")
        al.build({'bpm': 120, 'tracks': [{'kind': 'audio', 'name': 'N', 'vol': 1.0, 'clips': [{'start': 0, 'len': 40, 'name': 'N', 'buf': bid}], 'fx': [{'type': ty, 'p': p}]}]})
        R("stop();pos=0;toggle();selectTrack(S.tracks[0].id);renderFx();0"); al.page.wait_for_timeout(1500)
        t = R(r"""(()=>{const c=document.createElement('canvas');c.width=%d*2;c.height=%d*2;const g=c.getContext('2d');g.setTransform(2,0,0,2,0,0);const f=S.tracks[0].fx[0],X=vizInst(f),T=[];
          for(let i=0;i<200;i++){const t0=performance.now();g.clearRect(0,0,%d,%d);if(f.type==='comp')vizComp(g,%d,%d,f,X);else if(f.type==='ott')vizOTT(g,%d,%d,f,X);else VIZX[f.type](g,%d,%d,f,X);g.getImageData(0,0,1,1);T.push(performance.now()-t0)}T.sort((a,b)=>a-b);return T[100]})()""" % (w, h, w, h, w, h, w, h, w, h))
        out.append('%s %.3f' % (ty, t))
    R("stop();0"); print(F[-28:], ' | '.join(out)); al.stop() if hasattr(al, 'stop') else None
