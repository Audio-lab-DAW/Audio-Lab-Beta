"""IN-O: drawMixer's time per call with every strip in the stereo field view (Fractals playing, mixer open, 2194x1139), for two files.
  python3 tools/design-lab/in/stereo_cost_o.py a.html [b.html] [--pol] [--lite]"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'remake'))
from alab import AudioLab
pol = '--pol' in sys.argv; lite = '--lite' in sys.argv
for F in [a for a in sys.argv[1:] if not a.startswith('--')]:
    al = AudioLab(os.path.abspath(F), 2194, 1139); al.start(); R = al.run
    R("UI.lite=%s;UI.mxView='stereo';try{mxSet('stereo','pol',%s)}catch(e){}openMixer();renderMixer();stop();pos=0;toggle();0" % ('true' if lite else 'false', 'true' if pol else 'false'))
    al.page.wait_for_timeout(2500)
    R("window.__T=[];window.__dm=drawMixer;drawMixer=function(){const t=performance.now();const r=__dm.apply(this,arguments);const d=performance.now()-t;if(d>0.05)__T.push(d);return r};0")
    al.page.wait_for_timeout(5000)
    T = json.loads(R("JSON.stringify(__T)")); T.sort()
    print(F[-30:], 'drawMixer calls %d, median %.2f ms, mean %.2f ms, p90 %.2f ms' % (len(T), T[len(T) // 2], sum(T) / len(T), T[int(len(T) * .9)]))
    R("stop();0")
