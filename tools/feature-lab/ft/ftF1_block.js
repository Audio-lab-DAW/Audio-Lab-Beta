/* v0.255 (task FT-F1): linked clips. A clip can be a linked copy (clip.link, an id shared by its copies; optional, older projects have none):
   editing the notes, controller lanes, bend range or envelopes of one changes every copy (MIDI clips); for audio clips the gain, the warp
   markers and the envelopes. Where a copy sits, its length, start offset, fades, name and mute stay its own. Envelopes are shared in the
   clip's content time (a copy that starts later in the content keeps its envelope in step); a move, a resize or a split never counts as an
   edit to share. How: each linked clip keeps a baseline of what it holds; after an edit (changed()), a linked clip whose content differs from
   its baseline is the edited one and its content is copied into the others, in the same undo step. The selected clips and the piano roll's
   clip are checked at once, every linked clip a quarter second later (only after an edit, never while idle). Every copy keeps its full
   content in the file, so older AudioLab versions open the song as plain clips (the file is gzipped, so copies cost little). Made by
   Alt+Shift-drag (Shift-drag stays a plain copy), "Duplicate as linked copy" (clip menu, command clip.linkedDup); "Make unique" breaks the
   link (clip.unique); "Select linked copies". A small chain mark sits on every linked clip. The Fractals song's repeated Kick and Bass
   clips are linked. */
const LK={base:new Map(),S:null,sweepT:0,alt:false,n:{prop:0,check:0,sweep:0},MIDI:['notes','cc','pbr'],AUD:['gain','warp']};
window.LK=LK;
const lkId=()=>'L'+rid();
const lkKind=c=>c.notes?'m':'a';
const lkJ=v=>JSON.stringify(v===undefined?null:v,(k,x)=>k==='sel'?undefined:x);
/* the shared content of a clip: its own fields, and its envelopes in content time (clip time + offset) */
function lkContent(c){const ks=c.notes?LK.MIDI:LK.AUD,o={};for(const k of ks)o[k]=c[k]===undefined?null:c[k];return lkJ(o)}
function lkEnv(c){const o=+c.off||0,e={};for(const k in c.env||{}){const p=c.env[k];if(Array.isArray(p)&&p.length)e[k]=p.map(q=>Object.assign({},q,{b:Math.round((q.b+o)*1e6)/1e6}))}return lkJ(e)}
const lkPlace=c=>(+c.off||0)+'|'+c.len;
const lkSnap=c=>({n:lkContent(c),e:lkEnv(c),p:lkPlace(c)});
function lkGroup(id){const g=[];for(const t of S.tracks)for(const c of t.clips)if(c.link===id)g.push({t,c});return g}
function lkAllLinked(){const a=[];for(const t of S.tracks)for(const c of t.clips)if(c.link)a.push(c);return a}
/* a new song or an undo: every linked clip's baseline is what it holds now */
function lkBaseAll(){LK.S=S;LK.base.clear();for(const c of lkAllLinked())LK.base.set(c.id,lkSnap(c))}
function lkCopyTo(src,dst,what){
  if(what.n){const ks=src.notes?LK.MIDI:LK.AUD;for(const k of ks){if(src[k]===undefined){delete dst[k];continue}
    const v=JSON.parse(lkJ(src[k]));if(k==='notes'&&Array.isArray(dst.notes)){dst.notes.splice(0,dst.notes.length,...v)}else dst[k]=v}}
  if(what.e){const sh=(+src.off||0)-(+dst.off||0),E={};for(const k in src.env||{}){const p=src.env[k];if(Array.isArray(p))E[k]=p.map(q=>Object.assign({},q,{b:Math.round((q.b+sh)*1e6)/1e6}))}
    const keep=dst.env&&typeof dst.env==='object'?dst.env:{};for(const k of Object.keys(keep))if(!(k in E))keep[k]=[];for(const k in E)keep[k]=E[k];dst.env=keep}}
/* check some linked clips against their baselines; an edited one is copied into its group */
function lkCheck(list){if(LK.S!==S){lkBaseAll();return 0}let n=0;
  for(const c of list){if(!c||!c.link)continue;LK.n.check++;const b=LK.base.get(c.id),now=lkSnap(c);if(!b){LK.base.set(c.id,now);continue}
    const dn=now.n!==b.n,de=now.e!==b.e&&now.p===b.p;if(!dn&&!de){if(now.e!==b.e||now.p!==b.p)LK.base.set(c.id,now);continue}
    const kind=lkKind(c);for(const{c:d}of lkGroup(c.link)){if(d===c||lkKind(d)!==kind)continue;lkCopyTo(c,d,{n:dn,e:de});LK.base.set(d.id,lkSnap(d));n++}
    LK.base.set(c.id,now)}
  if(n){LK.n.prop+=n;dirty=true}return n}
const lkCands=()=>{const a=[],add=id=>{const f=id&&findClip(id);if(f&&f.c.link&&!a.includes(f.c))a.push(f.c)};add(selC);for(const id of SELCS)add(id);try{if(PR.open){const p=prClip();if(p&&p.link&&!a.includes(p))a.push(p)}}catch(e){}return a};
/* a quarter second after an edit: every linked clip, and links left with one clip are dropped */
function lkSweep(){LK.sweepT=0;LK.n.sweep++;const all=lkAllLinked();if(!all.length){LK.base.clear();return}lkCheck(all);
  const cnt=new Map();for(const c of all)cnt.set(c.link,(cnt.get(c.link)||0)+1);for(const c of all)if(cnt.get(c.link)<2){delete c.link;LK.base.delete(c.id);dirty=true}}
{const _c=changed;changed=function(){const r=_c.apply(this,arguments);try{if(LK.S!==S){lkBaseAll()}else{const cs=lkCands();if(cs.length&&lkCheck(cs)){dirty=true}}
  if(!LK.sweepT&&(LK.base.size||lkAllLinked().length))LK.sweepT=setTimeout(lkSweep,250)}catch(e){console.error('AudioLab linked clips',e)}return r}}
/* making and breaking links */
function lkSel(){const ids=SELCS.size?[...SELCS]:selC?[selC]:[],out=[];for(const id of ids){const f=findClip(id);if(f)out.push(f)}return out}
function lkDup(t,c){if(LK.S!==S)lkBaseAll();pushUndo();if(!c.link){c.link=lkId();LK.base.set(c.id,lkSnap(c))}dupClip(t,c);const k=findClip(selC);if(k&&k.c!==c){k.c.link=c.link;LK.base.set(k.c.id,lkSnap(k.c))}changed(false);
  toast('Linked copy: editing the notes'+(c.notes?'':' (gain, warp)')+' or envelopes of one changes all '+lkGroup(c.link).length+'.')}
function lkDupSel(){const f=lkSel()[0];if(!f){toast('Select a clip first.');return}if(f.t.frz){toast(f.t.name+' is frozen.');return}lkDup(f.t,f.c)}
function lkUnique(list){list=list.filter(f=>f.c.link);if(!list.length){toast('No linked clip selected.');return 0}pushUndo();
  for(const f of list){delete f.c.link;LK.base.delete(f.c.id)}changed(false);toast(list.length===1?f1Name(list[0].c)+' is unique now: its edits stay its own.':list.length+' clips are unique now.');return list.length}
const f1Name=c=>c.name||'The clip';
function lkSelectGroup(c){if(!c.link)return;const g=lkGroup(c.link);SELR=null;SELCS=new Set(g.map(x=>x.c.id));selC=c.id;dirty=true;toast(g.length+' linked copies selected.')}
/* Alt+Shift-drag: a linked copy; Shift-drag: a plain copy (a linked clip's plain copy is unique) */
arr.addEventListener('pointerdown',e=>{LK.alt=!!(e.altKey&&e.shiftKey)},true);
{const _a=ajShStart;ajShStart=function(x,y){const a=ad,lk=LK.alt;let src=[];if(a&&a.k==='ajsh'){const ids=SELCS.has(a.c.id)&&SELCS.size>1?new Set(SELCS):new Set([a.c.id]);S.tracks.forEach(t=>{if(t.frz)return;for(const q of t.clips)if(ids.has(q.id))src.push(q)})}
  const r=_a.apply(this,arguments);if(!r||!ad||!ad.items)return r;
  try{if(LK.S!==S)lkBaseAll();ad.items.forEach((it,i)=>{const q=src[i];if(lk&&q&&lkKind(q)===lkKind(it.c)){if(!q.link){q.link=lkId();LK.base.set(q.id,lkSnap(q))}it.c.link=q.link;LK.base.set(it.c.id,lkSnap(it.c))}else delete it.c.link});
    if(lk)ad.link=true}catch(e){console.error('AudioLab linked clips',e)}return r}}
/* the chain mark (drawn into the clip's cached picture, so the cache key knows about it) */
{const _s=clipSig;clipSig=function(t,c){return _s.apply(this,arguments)+'|'+(c.link?'L':'')}}
function lkMark(g,c,G){if(!c.link||G.w<26||G.h<12)return;const lx=Math.max(G.x,X0)+5,w=13,h=10;let x=lx,y=G.y+Math.max(1,(G.h-h)/2);
  if(G.top){g.save();g.font=(dsAC3()?'600':'500')+' 11px Inter,system-ui,sans-serif';x=lx+g.measureText((c.mute?'muted · ':'')+(c.name||'')).width+5;g.restore();y=G.y+3}
  if(x+w>G.x+G.w-3)return;
  g.save();g.globalAlpha=1;g.fillStyle='rgba(8,9,12,.62)';rr(g,x,y,w,h,3);g.fill();g.translate(x+w/2,y+h/2);g.rotate(-Math.PI/4);g.strokeStyle='rgba(255,255,255,.92)';g.lineWidth=1.2;
  rr(g,-4.6,-1.6,5,3.2,1.6);g.stroke();rr(g,-.4,-1.6,5,3.2,1.6);g.stroke();g.restore()}
{const _d=drawClip;drawClip=function(g,t,c,G){const r=_d.apply(this,arguments);try{lkMark(g,c,G)}catch(e){}return r}}
/* the clip menu: Duplicate as linked copy, and for a linked clip Make unique and Select linked copies */
{const _cm=clipMenu;clipMenu=function(x,y,t,c){LK.menu={t,c};try{return _cm.apply(this,arguments)}finally{LK.menu=null}}}
{const _om=openMenu;openMenu=function(cx,cy,items){const M=LK.menu;if(M&&Array.isArray(items)){LK.menu=null;try{const i=items.findIndex(o=>o&&o.label==='Duplicate');if(i>=0){const n=M.c.link?lkGroup(M.c.link).length:0,add=[
    {label:'Duplicate as linked copy',key:'⌥⇧-drag',sub:'edit one, every copy changes',dis:!!M.t.frz,act:()=>lkDup(M.t,M.c)}];
    if(n)add.push({label:'Make unique',sub:'stop following its '+(n-1)+' linked cop'+(n-1===1?'y':'ies'),act:()=>lkUnique([{t:M.t,c:M.c}])},{label:'Select linked copies',sub:n+' clips share these '+(M.c.notes?'notes':'settings'),act:()=>lkSelectGroup(M.c)});
    items=items.slice(0,i+1).concat(add,items.slice(i+1))}}catch(e){console.error('AudioLab linked clips',e)}}return _om.call(this,cx,cy,items)}}
/* a split keeps both halves linked (their notes are the same); the halves' envelopes are their own placement */
/* the Fractals song: its repeated Kick and Bass clips are linked (same notes and envelopes) */
function lkAuto(P,names){let n=0;for(const t of P.tracks||[]){if(names&&!names.includes(t.name))continue;const m=new Map();
    for(const c of t.clips||[]){if(c.link)continue;const k=lkKind(c)+lkContent(c)+lkEnv(c);if(!m.has(k))m.set(k,[]);m.get(k).push(c)}
    for(const g of m.values())if(g.length>1){const id=lkId();for(const c of g)c.link=id;n++}}return n}
{const _fp=frxProject;frxProject=async function(){const J=await _fp.apply(this,arguments);try{if(J&&J.project)lkAuto(J.project,['Kick','Bass'])}catch(e){console.error('AudioLab linked clips',e)}return J}}
/* a Fractals tab stored before linked clips is still the same song */
{const _f=frxSame;frxSame=function(q,J){if(_f.apply(this,arguments))return true;try{const st=P=>JSON.parse(JSON.stringify(P,(k,v)=>k==='link'?undefined:v));return _f.call(this,Object.assign({},q,{S:st(q.S)}),J&&Object.assign({},J,{project:st(J.project)}))}catch(e){return false}}}
FT_HOOKS.clipLinks={group:id=>lkGroup(id).map(x=>x.c.id),linkedCopy:id=>{const f=findClip(id);if(f)lkDup(f.t,f.c)},unique:id=>{const f=findClip(id);return f?lkUnique([f]):0},sync:()=>lkSweep()};
