"""Task IN-C and IN-D: what the Soft Clipper's display and the CPU graph cost per call, in the app's own loops, with a 1 kHz sine playing
through a Soft Clipper (its panel shown). Alternates the files given.
  python3 tools/design-lab/in/dev_cost_cd.py old.html new.html [rounds]"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'remake'))
from alab import AudioLab
F = sys.argv[1:3]; RN = int(sys.argv[3]) if len(sys.argv) > 3 else 3
SET = r"""(()=>{const o=VIZX.clip,oc=cpuFrame;window.__cc=[0,0,0,0,o,oc];VIZX.clip=function(){const t=performance.now();try{return o.apply(this,arguments)}finally{__cc[0]+=performance.now()-t;__cc[1]++}};
  cpuFrame=function(){const t=performance.now();try{return oc.apply(this,arguments)}finally{__cc[2]+=performance.now()-t;__cc[3]++}};return 0})()"""
GET = "(()=>{VIZX.clip=__cc[4];cpuFrame=__cc[5];const c=__cc;return JSON.stringify([c[0]/Math.max(1,c[1]),c[1],c[2]/Math.max(1,c[3]),c[3]])})()"
res = {f: [] for f in F}
for r in range(RN):
    for f in F:
        al = AudioLab(f, 2194, 1139); al.start(); R = al.run
        SR = int(R('ctx.sampleRate')); t = np.arange(20 * SR) / SR; x = (0.5 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
        b = al.add_audio(np.vstack([x, x]), SR)
        al.build({'bpm': 120, 'master': 0, 'tracks': [{'kind': 'audio', 'name': 'S', 'vol': 1.0, 'clips': [{'start': 0, 'len': 40, 'name': 'S', 'buf': b}], 'fx': [{'type': 'clip', 'p': {'thr': -12}}]}]})
        R("stop();pos=0;toggle();selectTrack(S.tracks[0].id);renderFx();0"); al.page.wait_for_timeout(1500)
        R(SET); al.page.wait_for_timeout(4000); v = json.loads(R(GET)); res[f].append(v); al.stop()
        print(r, os.path.basename(f), 'Soft Clipper display %.3f ms a call (%d calls), cpuFrame %.3f ms a call (%d calls)' % tuple(v), flush=True)
