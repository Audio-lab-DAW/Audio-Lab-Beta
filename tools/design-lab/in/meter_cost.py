"""IN-A: the cost of the level meters themselves (meters, trackMeters, miniMeter) while Fractals plays, per frame, for one or more index.html files.
  python3 tools/design-lab/in/meter_cost.py a.html [b.html ...]"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'remake'))
from alab import AudioLab
for f in sys.argv[1:]:
    al = AudioLab(f, 2194, 1139); al.start(); R = al.run
    R("openDemoFractals()"); al.page.wait_for_timeout(6000)
    out = []
    for alg in ('peak', 'lufs'):
        R("UI.mtr=Object.assign({},UI.mtr||{},{alg:'%s'});if(play.on)stop();pos=128;start();0" % alg); al.page.wait_for_timeout(1500)
        R("""window.__mc={t:0,n:0};for(const k of['meters','trackMeters','miniMeter']){const o=eval(k);window['__o'+k]=o;eval(k+'=function(){const t=performance.now();try{return o.apply(this,arguments)}finally{__mc.t+=performance.now()-t;if(k==="meters")__mc.n++}}')};0""")
        al.page.wait_for_timeout(5000)
        r = R("JSON.parse(JSON.stringify(__mc))")
        R("for(const k of['meters','trackMeters','miniMeter'])eval(k+'=window.__o'+k);stop();0")
        out.append('%s %.3f ms per frame (%d frames)' % (alg, r['t'] / max(1, r['n']), r['n']))
    print(os.path.basename(f), al.version, ' | '.join(out), 'errors', al.errors); al.stop()
