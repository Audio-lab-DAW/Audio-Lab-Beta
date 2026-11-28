/* ===================== stem split lanes, step 4 (v0.000, task SG2-4, lane R) =====================
   Audio to MIDI's "Split into stems first": the lanes replace the 4 px bar (a2dbar) while it splits, and when it is done each lane
   becomes its listen row (the row keeps ▶, Convert and the mode; the stem's spectrogram sits next to its name). A small hook in
   the split(j) callback calls SG_HOOKS.a2m(m, clipJob, engine, buffer) -> {cols, ph(phase,p,mb), done(state), end()}; the rows
   and the pop-up stay Audio to MIDI's. The pop-up redraws its body now and then, so the lanes are put back after each redraw. */
function sgA2M(m,a,eng,src){const q=eng==='quick',M=q?null:NEUM[eng],names=q?['Drums','Bass','Vocals','Other']:M.stems,cols=q?['#f5c84c','#4c8dff','#ff6bb5','#3ecf8e']:M.cols;
  const j=sgJob({kind:eng,name:a.c.name||'Audio',len:src.length,sr:src.sampleRate,stems:names.map((n,i)=>({name:n,col:cols[i],k:i}))});j.a2m=true;SG2.a2mLast=j;let el=null,mo=null;
  const place=()=>{if(!m.isConnected||j.phase==='stop'||j.phase==='err'){if(mo)mo.disconnect();sgDrop(j);SG2.jobs.delete(j);return}
    if(j.phase!=='done'){const bar=m.querySelector('.a2dbar');if(bar&&!(el&&el.isConnected)){m.querySelectorAll('.sgA2h').forEach(x=>x.remove());const h=document.createElement('div');h.className='sgA2h';bar.before(h);bar.hidden=true;sgDrop(j);el=sgLanes(h,j,{sub:' '})}}
    else m.querySelectorAll('.a2sr').forEach((r,i)=>{if(r.querySelector('.sgA2l')||!j.stems[i])return;r.classList.add('sgA2');const d=document.createElement('div');d.className='sgA2l';d.title=j.stems[i].name+': its spectrogram';d.innerHTML='<canvas></canvas>';const b=r.querySelector('b');if(b)b.after(d);else r.appendChild(d);sgView(j,d.firstChild,i)})};
  mo=new MutationObserver(place);mo.observe(m,{childList:true,subtree:true});place();if(q)sgPhase(j,'run');
  sgMixCols(src,j.cw).then(x=>{j.mix=x;sgDrop(j);for(const v of j.views)if(v.si<0)sgPaint(j,v,0,j.cw)}).catch(()=>{});
  const oc=d=>sgJobCols(j,d);oc.cw=j.cw;
  return{job:j,cols:oc,ph:(ph,p,mb)=>sgPhase(j,ph,{p,mb}),done:s=>{j.lv=(s.stems||[]).map(x=>x.db);sgEnd(j,'done');sgDrop(j);place();SG2.jobs.delete(j)},end:()=>{sgEnd(j,'err');if(mo)mo.disconnect();sgDrop(j)}}}
SG_HOOKS.a2m=sgA2M;
