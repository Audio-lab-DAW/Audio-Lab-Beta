# task D2 (v0.221): the sidechain outline on the mixer strips shows only when the sender or the receiver is selected.
#   python3 tools/edits/taskD2.py index.html
import sys
f=sys.argv[1] if len(sys.argv)>1 else 'index.html';s=open(f,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:80]);s=s.replace(a,b)
# 1. abxLights: a link lights its two strips only when one of its ends is selected (selT or the shared multi-selection TSEL)
rep("""function abxLights(w){const now=performance.now(),L=new Map(),put=""","""function abxLights(w){const now=performance.now(),L=new Map(),sel=id=>id===selT||TSEL.has(id),put=""")
rep("""if(f.type!=='duck'||!f.on)continue;const s=abxSrc(f);if(!s)continue;const X=abxX(t,f),live=""","""if(f.type!=='duck'||!f.on)continue;const s=abxSrc(f);if(!s||!(sel(t.id)||sel(s.id)))continue;const X=abxX(t,f),live=""")
rep("""const s=trkById(m.p.src);if(!s||s===t)continue;const st=MOD.st.get(m.id),v=st?""","""const s=trkById(m.p.src);if(!s||s===t||!(sel(t.id)||sel(s.id)))continue;const st=MOD.st.get(m.id),v=st?""")
# 2. selection changes update the outline in the same step (no wait for the next frame, no extra work per frame)
rep("""function askChoice(title,text,btns,icon){""","""/* ---------- v0.221 (task D2): the sidechain outline follows the selection ----------
   abxLights lights the sender and receiver strips only when one of them is selected (selT, or part of the shared selection TSEL of mixer and arrangement).
   It already runs once per mixer frame; here it also runs right when the selection changes, so the outline appears or goes in the same step. Cables are not touched. */
function abxSelNow(){try{const w=document.getElementById('mixWin');if(w&&!w.hidden)abxLights(w)}catch(e){}}
{const _s=selectTrack;selectTrack=function(){const r=_s.apply(this,arguments);abxSelNow();return r}}
{const _h=hdrMark;hdrMark=function(){const r=_h.apply(this,arguments);abxSelNow();return r}}
{const _m=selMaster;selMaster=function(){const r=_m.apply(this,arguments);abxSelNow();return r}}
function askChoice(title,text,btns,icon){""")
rep("const VERSION='0.220',BUILD='26 November 2026'","const VERSION='0.221',BUILD='27 November 2026'")
open(f,'w',encoding='utf-8').write(s);print('ok')
