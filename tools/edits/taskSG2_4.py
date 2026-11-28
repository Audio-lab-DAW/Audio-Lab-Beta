"""Task SG2-4 (lane R, prefix sg): Audio to MIDI's split shows the lanes instead of a2dbar; done, the lanes become the listen rows.
Needs SG2-3. Inserts taskSG2_4_block.js after the SG2-3 block and taskSG2_4_css.txt before .a2dbar, and a small hook in the split(j)
callback of the Audio to MIDI pop-up: SG_HOOKS.a2m(...) gives the onCols for stemSplit / neuSeparate, the phases, the end.
The rows themselves are not rewritten. Bumps VERSION (highest on main + 0.001).
  python3 tools/edits/taskSG2_4.py [index.html]"""
import sys, os, re
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(P, encoding='utf-8').read()
blk = open(os.path.join(H, 'taskSG2_4_block.js'), encoding='utf-8').read()
css = open(os.path.join(H, 'taskSG2_4_css.txt'), encoding='utf-8').read()
assert 'task SG2-3' in s, 'SG2-3 first'
assert 'task SG2-4' not in s, 'already applied'
assert not re.search(r'(function|const|let|var)\s+sgA2M\b', s)
def one(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:90]); s = s.replace(a, b)
m = re.findall(r"const VERSION='(\d+)\.(\d+)'", s); assert len(m) == 1
v = '%s.%03d' % (m[0][0], int(m[0][1]) + 1)
A = "/* ===================== neural stem separation: HTDemucs v4 (Meta, MIT weights) running in the browser ====================="
one(A, blk.replace('v0.000', 'v' + v) + A)
one('.a2dbar{height:6px;', css + '.a2dbar{height:6px;')
# the hook in split(j)
one("    try{const src=sliceOf(j);let bufs,names,cols;\n",
    "    let sgo=null;/* lane R (SG2-4): the stem split lanes */try{const src=sliceOf(j);let bufs,names,cols;sgo=SG_HOOKS.a2m?SG_HOOKS.a2m(m,j,Q.eng,src):null;\n")
one("bufs=await stemSplit(src,p=>{s.p=p;s.msg=Math.round(p*100)+'%';upd()},{bass:140,vlo:140,vhi:9000,focus:1.5,smooth:8})}",
    "bufs=await stemSplit(src,p=>{s.p=p;s.msg=Math.round(p*100)+'%';upd()},{bass:140,vlo:140,vhi:9000,focus:1.5,smooth:8},sgo&&sgo.cols)}")
one("else if(ph==='run'){s.p=p;s.msg=Math.round(p*100)+'%'}upd()})}",
    "else if(ph==='run'){s.p=p;s.msg=Math.round(p*100)+'%'}upd();if(sgo)sgo.ph(ph,p,mb)},sgo&&sgo.cols)}")
one("if(Q.dead)return;s.status='done'}", "if(Q.dead){if(sgo)sgo.end();return}s.status='done';if(sgo)sgo.done(s)}")
one("    catch(e){if(Q.dead)return;s.status='err';", "    catch(e){if(sgo)sgo.end();if(Q.dead)return;s.status='err';")
s = re.sub(r"const VERSION='\d+\.\d+'", "const VERSION='%s'" % v, s, count=1)
open(P, 'w', encoding='utf-8').write(s)
print(v)
