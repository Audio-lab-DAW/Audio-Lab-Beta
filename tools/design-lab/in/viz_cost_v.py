"""IN-V: the Visualizer's own frame (vizFrame, its own rAF loop), ms per drawn frame, Fractals playing, the Visualizer in All docked at the
bottom at 2194x1139 (UI.vizH 190, the default), two 4 s windows per page load; give the files alternately (the cloud machine is noisy).
  python3 tools/design-lab/in/viz_cost_v.py a.html b.html a.html b.html ...      INVMODE=spec|fft|wave|lev for one tab"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'remake'))
from alab import AudioLab
mode = os.environ.get('INVMODE', 'all')
for f in sys.argv[1:]:
    al = AudioLab(f, 2194, 1139); al.start(); R = al.run
    R("openDemoFractals()"); al.page.wait_for_timeout(6000)
    R("UI.lite=false;UI.viz=true;UI.vizMode='%s';UI.vizDock='bottom';UI.vizH=190;vizApply();if(play.on)stop();pos=128;start();0" % mode); al.page.wait_for_timeout(2500)
    R("window.__v={t:0,n:0};const o=vizFrame;vizFrame=function(now){const l=VZ.last,t=performance.now();try{return o.apply(this,arguments)}finally{if(VZ.last!==l){__v.t+=performance.now()-t;__v.n++}}};0")
    out = []
    for w in range(2):
        R("__v.t=0;__v.n=0;0"); al.page.wait_for_timeout(4000); r = R("[__v.t,__v.n]"); out.append((r[0] / max(1, r[1]), r[1]))
    print(os.path.basename(f), ' '.join('%.2f ms (%d frames)' % x for x in out), 'errors', al.errors, flush=True); al.stop()
