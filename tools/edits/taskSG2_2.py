"""Task SG2-2 (lane R, prefix sg): G1 lanes under the mix in the Split sheet, P1 draft stretch, F1 scan (the user's SG1 picks).
Needs SG2-1. Inserts taskSG2_2_block.js after the SG2-1 block, taskSG2_2_css.txt before .a2dbar, keeps the Split sheet open after
Split (stemAsk resolves with the sheet in P.m) and rewrites stemsFor (lane R owns it): the sheet becomes the lanes, the split fills
them chunk by chunk, Keep working / Stop / Add N tracks, Stop changes nothing, the neural fallback to the quick split keeps the sheet.
Bumps VERSION (highest on main + 0.001).
  python3 tools/edits/taskSG2_2.py [index.html]"""
import sys, os, re
P = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
H = os.path.dirname(os.path.abspath(__file__))
s = open(P, encoding='utf-8').read()
blk = open(os.path.join(H, 'taskSG2_2_block.js'), encoding='utf-8').read()
css = open(os.path.join(H, 'taskSG2_2_css.txt'), encoding='utf-8').read()
assert 'task SG2-1' in s, 'SG2-1 first'
assert 'task SG2-2' not in s, 'already applied'
for n in ('sgReduce', 'sgFmt', 'sgFmt0', 'sgJob', 'sgSetCw', 'sgLut', 'sgAlpha', 'sgPaint', 'sgView', 'sgDrop', 'sgJobCols', 'sgPhase', 'sgUpd', 'sgEnd', 'sgEta', 'sgU', 'sgRoHtml', 'sgLanes', 'sgSheet', 'sgStop', 'sgKeep', 'sgPill', 'sgLevels'):
    assert not re.search(r'(function|const|let|var)\s+' + n + r'\b', s), n + ' exists already'
def one(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:90]); s = s.replace(a, b)
m = re.findall(r"const VERSION='(\d+)\.(\d+)'", s); assert len(m) == 1
v = '%s.%03d' % (m[0][0], int(m[0][1]) + 1)
A = "/* ===================== neural stem separation: HTDemucs v4 (Meta, MIT weights) running in the browser ====================="
one(A, blk.replace('v0.000', 'v' + v) + A)
one('.a2dbar{height:6px;', css + '.a2dbar{height:6px;')
# the Split sheet stays open after Split
one("const done=v=>{m.remove();res(v)};$('#stNo',m).onclick=()=>done(null);", "const done=v=>{if(m.dataset.sg)return;m.remove();res(v)};$('#stNo',m).onclick=()=>done(null);")
one("if(!P.keep.some(Boolean))return toast('Pick at least one stem.');done(P)}})}", "if(!P.keep.some(Boolean))return toast('Pick at least one stem.');m.dataset.sg='1';P.m=m;res(P)}})}/* task SG2-2: the sheet stays, stemsFor turns it into the lanes */")
# stemsFor
i0 = s.index('async function stemsFor(t,c){'); i1 = s.index('\n/* tempo guess from onset autocorrelation */', i0)
assert 'SG_HOOKS.onChunk(sgj,d)' in s[i0:i1]
NEW = r"""/* task SG2-2: the split fills the lanes of the Split sheet (sgSheet); Keep working sends it on in the background; Add N tracks adds the ticked stems */
async function stemsFor(t,c){if(!BUFS.has(c.buf)){toast('The audio for this clip is not loaded.');return}
  if([...SG2.jobs].some(j=>j.phase!=='done')){toast('A stem split is already running. Wait for it, or stop it first.');return}
  ensureCtx();const src=BUFS.get(c.buf).buf,names0=['Drums','Bass','Vocals','Other'],cols0=['#f5c84c','#4c8dff','#ff6bb5','#3ecf8e'],of=SG2.batch&&IMPCH&&IMPCH.all?{i:++SG2.batch.k,n:SG2.batch.n}:null;
  const PS=await stemAsk(c.name||t.name);if(!PS)return;let m=PS.m,j,bufs;delete PS.m;
  for(;;){const q=PS.engine==='quick',M=q?null:NEUM[PS.engine],names=q?names0:M.stems,cols=q?cols0:M.cols;
    j=sgJob({kind:PS.engine,name:c.name||t.name,of,len:src.length,sr:src.sampleRate,stems:names.map((n,i)=>({name:n,col:cols[i],k:i})).filter((x,i)=>PS.keep[i])});
    if(m&&m.isConnected)sgSheet(m,j);else{sgSetCw(j,880);sgKeep(j)}
    sgMixCols(src,j.cw).then(x=>{j.mix=x;sgDrop(j);for(const v of j.views)if(v.si<0)sgPaint(j,v,0,j.cw)}).catch(()=>{});
    const onCols=d=>sgJobCols(j,d);onCols.cw=j.cw;onCols.ks=j.stems.map(x=>x.k);
    try{if(q){sgPhase(j,'run');const all=await stemSplit(src,null,PS,onCols);bufs=all.map((b,i)=>PS.keep[i]?b:null)}
      else bufs=await neuSeparate(src,PS.engine,PS.keep,(ph,p,mb)=>sgPhase(j,ph,{p,mb}),onCols);break}
    catch(e){const sh=j.sheet;if(e&&e.stopped){sgEnd(j,'stop');if(sh)sh.remove();toast('Stopped. Nothing was changed.');return}sgEnd(j,'err');
      if(!q){const ok=await askChoice('The neural split could not run',`${e&&e.message||e}. This needs an internet connection the first time (the model and the engine come from Hugging Face and jsDelivr). Use the quick split instead?`,[{label:'Cancel',v:null},{label:'Quick split',v:1,cls:'pri'}]);
        if(ok){PS.engine='quick';PS.keep=[true,true,true,true];Object.assign(PS,{bass:140,vlo:140,vhi:9000,focus:1.5,smooth:8});m=j.sheet;if(m)sgDrop(j,m);continue}if(j.sheet)j.sheet.remove();return}
      if(sh)sh.remove();toast('Could not split this audio: '+(e&&e.message||e));return}}
  const got=j.stems.map(x=>bufs[x.k]);j.bufs=got;j.lv=sgLevels(got);j.on=j.lv.map(d=>d>-60);const pr=new Promise(r=>j.pick=r);sgEnd(j,'done');
  const pick=j.bg?j.on.map((v,i)=>v?i:-1).filter(i=>i>=0):await pr;j.pick=null;SG2.jobs.delete(j);
  if(j.sheet){sgDrop(j,j.sheet);j.sheet.remove();j.sheet=null}
  if(!pick||!pick.length){j.added=0;if(SG_HOOKS.added)SG_HOOKS.added(j);else toast(pick?'No stem had sound, so nothing was added.':'Nothing was changed.');return}
  pushUndo();j.undo=UNDO[UNDO.length-1];const at=S.tracks.indexOf(t)+1;
  pick.forEach((li,n)=>{const x=j.stems[li],b=got[li],id=addBuf(b),nt=mkTrack('audio',null,t.name+' · '+x.name,x.col);S.tracks.splice(at+n,0,nt);nt.clips.push(mkClip({start:c.start,len:c.len,off:c.off,name:c.name+' ('+x.name.toLowerCase()+')',buf:id,dur:b.duration,gain:c.gain||0,fi:c.fi||0,fo:c.fo||0}))});
  c.mute=true;changed(true);j.added=pick.length;j.under=t.name;
  if(SG_HOOKS.added)SG_HOOKS.added(j);else toast(j.kind==='quick'?'Done. '+pick.length+' stem track'+(pick.length===1?'':'s')+' added below. The original clip is muted. Quick split is approximate: use it for sketching and remixing.':`Done: ${pick.length} neural stem track${pick.length===1?'':'s'} added below. The original clip is muted.`)}"""
s = s[:i0] + NEW + s[i1:]
s = re.sub(r"const VERSION='\d+\.\d+'", "const VERSION='%s'" % v, s, count=1)
open(P, 'w', encoding='utf-8').write(s)
print(v)
