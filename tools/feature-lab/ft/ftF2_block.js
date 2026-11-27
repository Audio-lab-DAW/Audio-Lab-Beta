/* v0.262 (task FT-F2): arranger moves. A section of the song can be moved, copied or deleted as a whole, and empty bars inserted, with
   everything that lives on the time line: the clips of every track (cut at the edges, as a split does), the parameter automation
   (S.pauto: the curve is kept, a point is added at each edge so the shape outside and inside stays), the tempo changes (S.tempo, S.bpm)
   and the time signature changes (S.sigs, S.sigN/D), the section markers and the loop. One undo step. Every edit is described as
   segments of the old time line put somewhere on the new one ([from, to, at], a copy keeps its source too), so move, copy, insert and
   delete are one code path. With a constant tempo and no automation the clips land exactly where the same cuts and moves made by hand
   put them (the render is the same, bit for bit). Drag a section in the section strip to move it (as before, now with the automation and
   tempo), Alt-drag to copy it; the section menu: Duplicate section, Insert empty bars before or after, Delete section and close the gap;
   the empty strip: Insert empty bars here; commands arr.secDup, arr.insertBars, arr.secDelete. Linked clips (FT-F1) stay linked when
   copied, as Duplicate does. Nothing runs while idle. */
const FTAM={E:1e-6};
/* the segments of an edit: [a, b, to, copy] (b may be Infinity) */
function ftAmSegs(op,s,L,dst){const I=Infinity;let g;
  if(op==='move'){if(dst>s-1e-6&&dst<s+L+1e-6)return null;g=dst<s?[[0,dst,0],[s,s+L,dst],[dst,s,dst+L],[s+L,I,s+L]]:[[0,s,0],[s+L,dst,s],[s,s+L,dst-L],[dst,I,dst]]}
  else if(op==='copy')g=[[0,dst,0],[dst,I,dst+L],[s,s+L,dst,1]];
  else if(op==='insert')g=[[0,s,0],[s,I,s+L]];
  else if(op==='delete')g=[[0,s,0],[s+L,I,s]];
  else return null;
  return g.filter(q=>q[1]-q[0]>FTAM.E)}
/* where a point of the old time line lands (null: deleted) */
function ftAmMap(G,b){for(const q of G)if(!q[3]&&b>=q[0]-FTAM.E&&b<q[1]-FTAM.E)return b-q[0]+q[2];return null}
const ftAmR6=v=>+(+v).toFixed(6);
/* parameter automation: points inside each segment move with it, an edge point holds the value at each cut */
function ftAmPts(pts,G,def){if(!pts||!pts.length)return pts;const P=pts.slice().sort((a,z)=>a.b-z.b),out=[];
  const at=b=>ftAmR6(envAt(P,b,def));
  for(const[a,b,to]of G){const ins=P.filter(q=>q.b>=a-FTAM.E&&q.b<b-FTAM.E);
    if(!(a<FTAM.E&&to<FTAM.E)&&!ins.some(q=>Math.abs(q.b-a)<FTAM.E))out.push({b:ftAmR6(to),v:at(a+1e-7),e:1,o:2});
    for(const q of ins){const n=Object.assign({},q);n.b=ftAmR6(q.b-a+to);n.o=1;out.push(n)}
    if(b!==Infinity)out.push({b:ftAmR6(to+b-a),v:at(b-1e-7),e:1,o:0})}
  out.sort((x,y)=>x.b-y.b||x.o-y.o);
  /* drop the edge points that change nothing (a flat stretch, or the same point twice) */
  for(let ch=1;ch;){ch=0;for(let i=0;i<out.length;i++){const e=out[i];if(!e.e)continue;const p=out[i-1],n=out[i+1];
    if((!p||(Math.abs(p.v-e.v)<1e-6&&!p.c))&&(!n||Math.abs(n.v-e.v)<1e-6)){out.splice(i,1);ch=1;break}}}
  return out.map(q=>{const n=Object.assign({},q);delete n.e;delete n.o;return n})}
/* the tempo map: the change in force at each cut starts each segment; a glide cut at the end of a segment ends there */
function ftAmTempo(G){if(!Array.isArray(S.tempo)||!S.tempo.length)return false;
  const P=[{b:0,bpm:S.bpm,ramp:!!S.tempoRamp0}].concat(S.tempo.filter(q=>q&&q.b>0).map(q=>({b:q.b,bpm:q.bpm,ramp:!!q.ramp}))).sort((a,z)=>a.b-z.b);
  const seg=b=>{let i=0;while(i+1<P.length&&P[i+1].b<=b+FTAM.E)i++;return i};
  const val=b=>{const i=seg(b),p=P[i],n=P[i+1];return!n||!p.ramp?p.bpm:p.bpm+(n.bpm-p.bpm)*(b-p.b)/(n.b-p.b)};
  const out=[];
  for(const[a,b,to]of G){const ins=P.filter(q=>q.b>=a-FTAM.E&&q.b<b-FTAM.E);
    if(!ins.some(q=>Math.abs(q.b-a)<FTAM.E)){const i=seg(a);out.push({b:ftAmR6(to),bpm:ftAmR6(val(a)),ramp:P[i].ramp,o:2})}
    for(const q of ins)out.push({b:ftAmR6(q.b-a+to),bpm:q.bpm,ramp:q.ramp,o:1});
    if(b!==Infinity){const i=seg(b-1e-7);if(P[i].ramp&&P[i+1])out.push({b:ftAmR6(to+b-a),bpm:ftAmR6(val(b-1e-7)),ramp:false,o:0})}}
  out.sort((x,y)=>x.b-y.b||x.o-y.o);
  const keep=[];for(const q of out){const p=keep[keep.length-1];if(p&&!p.ramp&&!q.ramp&&Math.abs(p.bpm-q.bpm)<1e-9)continue;keep.push(q)}
  const f=keep[0]||{bpm:S.bpm,ramp:false};S.bpm=f.bpm;S.tempoRamp0=!!f.ramp;
  S.tempo=keep.slice(1).map(q=>({b:q.b,bpm:q.bpm,ramp:!!q.ramp}));S.tempoV=(S.tempoV||0)+1;return true}
/* time signatures: the signature in force at each cut starts each segment */
function ftAmSigs(G){if(!Array.isArray(S.sigs)||!S.sigs.length)return false;const L=sigList().map(q=>({b:q.b,n:q.n,d:q.d})),out=[];
  for(const[a,b,to]of G){const ins=L.filter(q=>q.b>=a-FTAM.E&&q.b<b-FTAM.E);
    if(!ins.some(q=>Math.abs(q.b-a)<FTAM.E)){const g=sigAt(a);out.push({b:ftAmR6(to),n:g.n,d:g.d,o:2})}
    for(const q of ins)out.push({b:ftAmR6(q.b-a+to),n:q.n,d:q.d,o:1})}
  out.sort((x,y)=>x.b-y.b||x.o-y.o);
  const keep=[];for(const q of out){const p=keep[keep.length-1];if(p&&Math.abs(p.b-q.b)<FTAM.E){keep[keep.length-1]=q;continue}if(p&&p.n===q.n&&p.d===q.d)continue;keep.push(q)}
  const f=keep[0]||{n:S.sigN||4,d:S.sigD||4};S.sigN=f.n;S.sigD=f.d;S.sigs=keep.slice(1).map(q=>({b:q.b,n:q.n,d:q.d}));S.sigV=(S.sigV||0)+1;return true}
/* the sections */
function ftAmSecs(op,s,L,dst,G){const ss=S.sections||[];if(!ss.length)return;const e=s+L,E=FTAM.E;
  if(op==='move'){for(const sc of ss){const m=ftAmMap(G,sc.start);if(m!=null)sc.start=ftAmR6(m)}return}
  if(op==='insert'){for(const sc of ss){if(sc.start>=s-E)sc.start=ftAmR6(sc.start+L);else if(sc.start+sc.len>s+E)sc.len=ftAmR6(sc.len+L)}return}
  if(op==='delete'){S.sections=ss.filter(sc=>!(sc.start>=s-E&&sc.start+sc.len<=e+E));for(const sc of S.sections){const a=sc.start,b=a+sc.len;
      if(a>=e-E)sc.start=ftAmR6(a-L);else if(a<s-E&&b>e+E)sc.len=ftAmR6(sc.len-L);else if(a<s-E&&b>s+E)sc.len=ftAmR6(s-a);else if(a>=s-E&&b>e+E){sc.start=ftAmR6(s);sc.len=ftAmR6(b-e)}}return}
  if(op==='copy'){const cp=ss.filter(sc=>sc.start>=s-E&&sc.start<e-E).map(sc=>Object.assign(JSON.parse(JSON.stringify(sc)),{id:rid(),start:ftAmR6(dst+sc.start-s),len:ftAmR6(Math.min(sc.len,e-sc.start))}));
    for(const sc of ss){if(sc.start>=dst-E)sc.start=ftAmR6(sc.start+L);else if(sc.start+sc.len>dst+E)sc.len=ftAmR6(sc.len+L)}S.sections=ss.concat(cp)}}
/* the one edit: op move, copy, insert or delete; s and L the range in beats; dst where a move or copy goes (a point of the old time line) */
function ftAmEdit(op,s,L,dst,o){o=o||{};s=Math.max(0,+s||0);L=+L||0;if(!(L>FTAM.E))return false;if(dst!=null)dst=Math.max(0,+dst);
  const G=ftAmSegs(op,s,L,dst);if(!G)return false;if(!o.noUndo)pushUndo();
  const cuts=[...new Set(G.flatMap(q=>[q[0],q[1]]).filter(b=>b>FTAM.E&&b!==Infinity))];
  for(const t of S.tracks){for(const b of cuts)cutAt(t,b);const src=t.clips.map(c=>({c,s:c.start})),keep=[];
    for(const x of src){const m=ftAmMap(G,x.s);if(m!=null){x.c.start=ftAmR6(m);keep.push(x.c)}}
    for(const q of G)if(q[3])for(const x of src)if(x.s>=q[0]-FTAM.E&&x.s<q[1]-FTAM.E){const k=JSON.parse(JSON.stringify(x.c));k.id=rid();k.start=ftAmR6(x.s-q[0]+q[2]);keep.push(k)}
    t.clips=keep}
  const pa=S.pauto||{};for(const id in pa){const e=PAREG.get(id),def=e?e.spec.n(e.get()):.5;pa[id]=ftAmPts(pa[id],G,def)}
  ftAmTempo(G);ftAmSigs(G);
  const lr=S.loopRange;ftAmSecs(op,s,L,dst,G);
  if(lr){const sc=lr.id&&(S.sections||[]).find(q=>q.id===lr.id);if(sc)S.loopRange={id:sc.id,a:sc.start,b:sc.start+sc.len};
    else{const a=ftAmMap(G,lr.a),b=ftAmMap(G,lr.b-1e-7);S.loopRange=a!=null&&b!=null&&Math.abs((b+1e-7-a)-(lr.b-lr.a))<1e-4?{a:ftAmR6(a),b:ftAmR6(a+lr.b-lr.a)}:null}}
  try{SELCS.clear();SELR=null}catch(e){}if(selC&&!findClip(selC))selC=null;
  syncTransportUI();changed(false);dirty=true;return true}
const ftAmBars=(b,n)=>n*barPos(b).len;
const ftAmBarStr=b=>'bar '+(barPos(b).bar+1);
function ftAmMove(sc,dst){const ok=ftAmEdit('move',sc.start,sc.len,dst);return ok}
function ftAmDup(sc){if(!sc)return false;const ok=ftAmEdit('copy',sc.start,sc.len,sc.start+sc.len);if(ok)toast(`Copied “${sc.name}” right after it, with its clips, automation and tempo. Everything after it moved later.`);return ok}
function ftAmDel(sc){if(!sc)return false;const ok=ftAmEdit('delete',sc.start,sc.len);if(ok)toast(`Deleted “${sc.name}” and its music. The rest of the song moved up to close the gap. Undo brings it back.`);return ok}
async function ftAmInsertAsk(b){const p=barPos(Math.max(0,b)),at=p.inBar>1e-6?p.start+(p.inBar>p.len/2?p.len:0):p.start;
  const v=await askText('How many empty bars to insert at '+ftAmBarStr(at)+'?','4');if(v==null||v==='')return false;const n=Math.round(+String(v).replace(',','.'));
  if(!(n>=1&&n<=512)){toast('Type a number of bars from 1 to 512.');return false}
  const ok=ftAmEdit('insert',at,ftAmBars(at,n));if(ok)toast(`Inserted ${n} empty bar${n===1?'':'s'} at ${ftAmBarStr(at)}. Everything after it moved later.`);return ok}
const ftAmSecAt=b=>{const ss=(S.sections||[]).slice().sort((a,z)=>a.start-z.start);return ss.filter(sc=>b>=sc.start-FTAM.E&&b<sc.start+sc.len-FTAM.E).pop()||null};
function ftAmCmd(k){const b=play.on?curDisp():pos,sc=ftAmSecAt(b);if(!sc){toast('Put the playhead in a section first (sections are the coloured strip under the ruler).');return}
  if(k==='dup')ftAmDup(sc);else if(k==='del')ftAmDel(sc)}
/* the section menu's entries (beside Loop, Rename, colours) */
const FTAM_TIP={'Duplicate section':'Puts a copy of this section right after it: its clips, automation, tempo and signature changes. Everything after it moves later.',
  'Insert empty bars before…':'Adds empty bars before this section. Everything from here on moves later.',
  'Insert empty bars after…':'Adds empty bars after this section. Everything after it moves later.',
  'Delete section and close the gap':'Deletes this section with its clips, automation and tempo changes, and moves the rest of the song up. Undo brings it back.',
  'Remove the marker only':'Removes the coloured section marker. The music stays where it is.',
  'Insert empty bars here…':'Adds empty bars at this bar line. Everything after it moves later.'};
function ftAmSecItems(sc){return['-',{label:'Duplicate section',sub:'A copy right after it, the rest moves later',act:()=>ftAmDup(sc)},
  {label:'Insert empty bars before…',act:()=>ftAmInsertAsk(sc.start)},{label:'Insert empty bars after…',act:()=>ftAmInsertAsk(sc.start+sc.len)},
  {label:'Delete section and close the gap',danger:1,sub:'With its clips, automation and tempo',act:()=>ftAmDel(sc)}]}
/* tooltips on the new menu entries (the menu draws labels only) */
function ftAmTips(){const m=document.getElementById('ctxm');if(!m||m.hidden)return;for(const bt of m.querySelectorAll('button')){const l=bt.querySelector('.mlab'),t=l?l.childNodes[0]&&l.childNodes[0].textContent.trim():bt.textContent.trim();if(FTAM_TIP[t])bt.title=FTAM_TIP[t]}}
{const _sm=secMenu;secMenu=function(){const r=_sm.apply(this,arguments);try{ftAmTips()}catch(e){}return r}}
/* dragging a section: as before, with Alt a copy (the copy can also go right before or after the section itself) */
function ftAmDrag(ad,b,e){ad.cp=!!(e&&e.altKey);const want=ad.s0+(b-ad.b0);let bd=[...new Set((S.sections||[]).flatMap(q=>[q.start,q.start+q.len]).concat([0]))];
  if(!ad.cp)bd=bd.filter(q=>q<ad.s0-1e-6||q>ad.s0+ad.l0+1e-6);
  let best=null,bv=1e9;for(const q of bd){const tgt=ad.cp?q:(q>ad.s0?q-ad.l0:q),dd=Math.abs(tgt-want);if(dd<bv){bv=dd;best=q}}
  ad.dst=best;PREVT=null;PREVMAP=best==null?null:ad.cp?(q=>q>=best-1e-6?q+ad.l0:q):rippleMap(ad.s0,ad.l0,best);try{arr.style.cursor=ad.cp?'copy':'grabbing'}catch(er){}
  dirty=true}
function ftAmDrop(a){const nm=a.sc.name;
  if(a.cp){if(ftAmEdit('copy',a.s0,a.l0,a.dst,{noUndo:1}))toast(`Copied “${nm}” with its clips, automation and tempo. Everything after the copy moved later.`);else changed(false);return}
  if(ftAmEdit('move',a.s0,a.l0,a.dst,{noUndo:1}))toast(`Moved “${nm}” with its clips, automation and tempo. The rest of the song moved out of the way. Hold Alt while dragging to copy instead.`);else changed(false)}
/* the copy's place while Alt-dragging: a dashed box in the section strip */
function ftAmGhost(g,xd,sy,ad){const w=ad.l0*V.ppb;g.save();g.setLineDash([4,3]);g.strokeStyle='#fff';g.lineWidth=1.2;rr(g,xd+1,sy+3,Math.max(4,w-2),SECH-6,3);g.stroke();g.setLineDash([]);
  g.fillStyle=ad.sc.color||'#4cc9f0';g.globalAlpha=.22;g.fill();g.globalAlpha=1;g.font='500 10px Inter,system-ui,sans-serif';g.fillStyle='rgba(236,238,244,.95)';g.shadowColor='rgba(0,0,0,.8)';g.shadowBlur=3;
  g.beginPath();g.rect(xd,sy,w,SECH);g.clip();g.fillText('+ copy of '+ad.sc.name,xd+8,sy+13);g.restore()}
FT_HOOKS.arrangerMoves={edit:ftAmEdit,move:(id,dst)=>{const sc=(S.sections||[]).find(q=>q.id===id);return sc?ftAmMove(sc,dst):false},
  copy:(id,dst)=>{const sc=(S.sections||[]).find(q=>q.id===id);return sc?ftAmEdit('copy',sc.start,sc.len,dst==null?sc.start+sc.len:dst):false},
  insert:(b,beats)=>ftAmEdit('insert',b,beats),del:id=>{const sc=(S.sections||[]).find(q=>q.id===id);return sc?ftAmEdit('delete',sc.start,sc.len):false}};
