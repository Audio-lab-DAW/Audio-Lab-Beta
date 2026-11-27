"""IN-M: the cost of the level meters and the mixer drawing while Fractals plays with the mixer open, per meter frame, for one or more index.html files
(alternate them; the cloud machine is noisy).  python3 tools/design-lab/in/meter_cost_m.py a.html [b.html ...]"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'remake'))
from alab import AudioLab
for f in sys.argv[1:]:
    al = AudioLab(f, 2194, 1139); al.start(); R = al.run
    R("openDemoFractals()"); al.page.wait_for_timeout(6000)
    R("UI.mtr=Object.assign({},UI.mtr||{},{alg:'peak'});openMixer();if(play.on)stop();pos=128;start();0"); al.page.wait_for_timeout(2000)
    K = ['meters', 'trackMeters', 'miniMeter', 'drawMixer']
    R("window.__mc={t:{},n:0};for(const k of%s){const o=eval(k);window['__o'+k]=o;__mc.t[k]=0;eval(k+'=function(){const t=performance.now();try{return o.apply(this,arguments)}finally{__mc.t[k]+=performance.now()-t;if(k===\"meters\")__mc.n++}}')};0" % K)
    al.page.wait_for_timeout(6000)
    r = R("JSON.parse(JSON.stringify(__mc))"); n = max(1, r['n'])
    R("for(const k of%s)eval(k+'=window.__o'+k);stop();0" % K)
    print(os.path.basename(f), al.version, ' '.join('%s %.3f' % (k, r['t'][k] / n) for k in K), 'total %.3f ms per meter frame (%d), %.0f ms per second' % (sum(r['t'].values()) / n, n, sum(r['t'].values()) / 6), 'errors', al.errors); al.stop()
