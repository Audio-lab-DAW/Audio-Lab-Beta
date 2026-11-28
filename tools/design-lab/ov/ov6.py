#!/usr/bin/env python3
"""Task OV6a (lane F, overlays; docs/design-round-5-overlays.md section 5, step OV6, built as the user's pick T3): tooltips become
callouts with a leader (amber hairline and dot), name and key, value with unit, sentence, DEFAULT and SCOPE; 500 ms, then warm 300 ms;
hoverable; Esc hides; keyboard focus shows them.
   python3 tools/design-lab/ov/ov6.py index.html
Anchors, asserted unique: the JS block (ov6_block.js) before askChoice, the CSS (ov6_css.txt) before .dacv, and six small asserted
changes in the tooltip code itself (lane F's own: tipShow, tipHide, its three document listeners and the clip-name follower's stop). Re-run on a fresh file after a rebase."""
import sys, os
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(F, encoding='utf-8').read()
assert 'task OV6a' not in s, 'already applied'
assert 'task OV1' in s and 'function ovMs(' in s and 'const ovKeyTx=' in s, 'needs OV1 and OV8'
for nm in ['ovT3Show', 'ovT3Off', 'ovT3Parse', 'ovT3Val', 'ovT3Cmd', 'ovT3Move', 'ovT3Over', 'ovT3Out', 'ovT3Start', 'ovT3In', 'ovT3Br', 'ovT3Delay', 'OV_T3']:
    assert 'function ' + nm + '(' not in s and nm + '=' not in s, 'name taken: ' + nm

def rep(old, new):
    global s
    c = s.count(old)
    assert c == 1, (c, old[:80])
    s = s.replace(old, new)

def ins(anchor, text):
    rep(anchor, text + anchor)

# tipShow: the old body (a rich card under the control) becomes the callout
a = s.index('function tipShow(el){const raw=tipText(el);')
b = s.index("TIPEL.style.top=Math.max(6,y)+'px'}", a) + len("TIPEL.style.top=Math.max(6,y)+'px'}")
assert s.count('function tipShow(el){') == 1 and b - a < 1200, (b - a)
s = s[:a] + 'function tipShow(el){ovT3Show(el)}/* task OV6a: the T3 callout (ovT3Show) */' + s[b:]
rep("const tipHide=()=>{clearTimeout(tipT);tipFor=null;if(TIPEL)TIPEL.className=''};",
    "const tipHide=()=>{clearTimeout(tipT);tipFor=null;if(TIPEL)TIPEL.className='';ovT3Off()};")
rep("document.addEventListener('pointerover',e=>{if(e.pointerType==='touch')return;const el=tipTarget(e.target);if(el===tipFor)return;tipHide();if(!el)return;tipText(el);tipFor=el;tipT=setTimeout(()=>tipShow(el),420)},true);",
    "document.addEventListener('pointerover',e=>{if(e.pointerType==='touch')return;ovT3Over(e)},true);")
rep("document.addEventListener('pointerout',e=>{if(tipFor&&!tipFor.contains(e.relatedTarget))tipHide()},true);",
    "document.addEventListener('pointerout',e=>{ovT3Out(e)},true);")
rep("document.addEventListener('pointerdown',tipHide,true);document.addEventListener('wheel',tipHide,{capture:true,passive:true});",
    "document.addEventListener('pointerdown',e=>{if(!ovT3In(e.target))tipHide()},true);document.addEventListener('wheel',tipHide,{capture:true,passive:true});")
# the clip-name follower on the arrangement canvas: crossing clips on the way to a callout no longer closes it
rep(" const stop=()=>{clearTimeout(tT);if(cur){cur=null;tipHide()}};",
    " const stop=()=>{clearTimeout(tT);if(cur){cur=null;if(!(typeof OV_T3==='object'&&OV_T3&&OV_T3.ptr))tipHide()}};")
ins('function askChoice(title,text,btns,icon){', open(os.path.join(H, 'ov6_block.js'), encoding='utf-8').read())
ins('.dacv{display:flex;', open(os.path.join(H, 'ov6_css.txt'), encoding='utf-8').read())
open(F, 'w', encoding='utf-8').write(s)
print('task OV6a applied')
