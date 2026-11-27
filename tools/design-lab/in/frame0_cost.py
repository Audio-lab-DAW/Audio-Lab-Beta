"""IN-M: the app's own frame callback (frame0), ms per frame, Fractals playing with the mixer open at 2194x1139, two 4 s windows per page load;
give the files alternately (the cloud machine is noisy).  python3 tools/design-lab/in/frame0_cost.py a.html b.html a.html b.html ..."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'remake'))
from alab import AudioLab
for f in sys.argv[1:]:
    al = AudioLab(f, 2194, 1139); al.start(); R = al.run
    R("openDemoFractals()"); al.page.wait_for_timeout(6000)
    R("UI.mtr=Object.assign({},UI.mtr||{},{alg:'peak'});openMixer();if(play.on)stop();pos=128;start();0"); al.page.wait_for_timeout(2500)
    R("window.__f={t:0,n:0};const o=frame0;frame0=function(){const t=performance.now();try{return o.apply(this,arguments)}finally{__f.t+=performance.now()-t;__f.n++}};0")
    out = []
    for w in range(2):
        R("__f.t=0;__f.n=0;0"); al.page.wait_for_timeout(4000); r = R("[__f.t,__f.n]"); out.append(r[0] / max(1, r[1]))
    print(os.path.basename(f), ' '.join('%.2f' % x for x in out), 'ms per frame', 'errors', al.errors, flush=True); al.stop()
