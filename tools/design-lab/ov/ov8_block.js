/* task OV8 (lane F, overlays, pick K1): the command palette on ⌘K, with the Assistant inside, and the key sheet on ?.
   ⌘K (Ctrl+K) opens the palette at the top of the window over every command of the registry (xtCommands(): the shortcut list SCA with
   the commands of lanes C and D, ctl.*, ni.*, clip.*, and the extra commands), gestures left out since they cannot be run. Type a few
   letters: fuzzy search, the matched letters in blue, keys on the right in mono; with nothing typed, Recent (the last five run here)
   comes first, then the groups of Settings › Keyboard shortcuts. While something is typed, the last row asks the Assistant with it.
   ⌘K again opens the Assistant (with what was typed), so ⌘K keeps its old meaning one press away; the Assistant's own row lost its
   default key for this (a key the user gave it is kept). ? (empty search, or anywhere outside a text field) opens the key sheet:
   every shortcut in two columns by area, a search that also finds keys, the number of conflicts, and a button to change keys in Settings.
   Keyboard: combobox with aria-activedescendant; arrows, Page Up/Down, Enter runs, Esc closes and gives focus back to where it was,
   Tab stays inside. Nothing runs at start: the two rows join SCA after the script, the registry is built on the first open. */
const OV_K1={el:null,ks:null,rows:[],fi:0,ret:null,n:0};
function ovFz(q,s){q=q.toLowerCase();const t=s.toLowerCase();let i=0,sc=0,last=-2,out='';
  for(let j=0;j<s.length;j++){if(i<q.length&&t[j]===q[i]){sc+=j===last+1?3:1;if(j===0)sc+=4;else if(t[j-1]===' '||t[j-1]==='(')sc+=2;if(last>=0&&j>last+1)sc-=(j-last-1)*.06;last=j;i++;out+='<mark>'+esc(s[j])+'</mark>'}else out+=esc(s[j])}
  return i===q.length?{sc:sc-s.length*.01,h:out}:null}
const ovKeyTx=k=>{if(!k)return'';const P=scShow(k);let o='';P.forEach((x,i)=>{o+=(i&&x.length>1&&P[i-1].length>1?' + ':'')+x});return o};
function ovRecent(){const R=Array.isArray(UI.ovRecent)?UI.ovRecent:[];return R}
function ovPalCmds(){return[...xtCommands().values()].filter(c=>!c.gesture&&c.id!=='help.palette')}
const OV_GORD=['transport','edit','view','project','help'];
function ovGName(g){return(typeof SCG!=='undefined'&&SCG[g])?SCG[g][0]:'More'}
function ovPalDraw(){const P=OV_K1,el=P.el,q=el.querySelector('input').value.trim(),C=ovPalCmds(),rs=el.querySelector('.ovrs');let h='';P.rows=[];
  const row=(c,lab)=>{const i=P.rows.length;P.rows.push(c);return`<div class="ovr${c.ask!=null?' ovai':''}" role="option" id="ovpo${i}" data-r="${i}" aria-selected="false"><span class="ovl">${lab}</span><kbd>${c.ask!=null?'↵':esc(ovKeyTx(c.key))}</kbd></div>`};
  if(!q){const M=new Map(C.map(c=>[c.id,c])),rec=ovRecent().map(id=>M.get(id)).filter(Boolean);
    if(rec.length){h+='<div class="ovpg" role="presentation">Recent</div>';for(const c of rec)h+=row(c,esc(c.name))}
    const used=new Set(rec.map(c=>c.id)),gs=OV_GORD.concat([...new Set(C.map(c=>c.group))].filter(g=>!OV_GORD.includes(g)));
    for(const g of gs){const L=C.filter(c=>c.group===g&&!used.has(c.id));if(!L.length)continue;h+=`<div class="ovpg" role="presentation">${esc(ovGName(g))}</div>`;for(const c of L)h+=row(c,esc(c.name))}}
  else{const res=[];for(const c of C){const m=ovFz(q,c.name);if(m)res.push([m.sc,c,m.h]);else{const w=ovFz(q,c.id);if(w)res.push([w.sc-50,c,esc(c.name)])}}
    res.sort((a,b)=>b[0]-a[0]);for(const r of res.slice(0,40))h+=row(r[1],r[2]);
    h+='<div class="ovpg" role="presentation">Assistant</div>'+row({ask:q},'Ask the Assistant: “'+esc(q)+'”')}
  rs.innerHTML=h;P.fi=0;ovPalHl(false)}
function ovPalHl(sc){const P=OV_K1,rs=P.el.querySelector('.ovrs'),inp=P.el.querySelector('input');const o=rs.querySelector('.ovr.on');if(o){o.classList.remove('on');o.setAttribute('aria-selected','false')}
  const f=rs.querySelector('#ovpo'+P.fi);if(f){f.classList.add('on');f.setAttribute('aria-selected','true');inp.setAttribute('aria-activedescendant',f.id);if(!sc)return;if(!P.fi){rs.scrollTop=0;return}
    const a=f.offsetTop,b=a+f.offsetHeight;if(a<rs.scrollTop+4)rs.scrollTop=Math.max(0,a-(f.previousElementSibling&&f.previousElementSibling.classList.contains('ovpg')?24:4));else if(b>rs.scrollTop+rs.clientHeight)rs.scrollTop=b-rs.clientHeight+4}
  else inp.removeAttribute('aria-activedescendant')}
function ovK1Ret(){const r=OV_K1.ret;OV_K1.ret=null;if(r&&r.isConnected&&r!==document.body)try{r.focus({preventScroll:true})}catch(e){}}
function ovPalClose(back){const P=OV_K1;if(!P.el||P.el.hidden)return;P.el.hidden=true;document.removeEventListener('pointerdown',ovK1Out,true);if(back!==false)ovK1Ret()}
function ovK1Out(e){const P=OV_K1;if(P.el&&!P.el.hidden&&!P.el.contains(e.target)){P.ret=null;ovPalClose(false)}if(P.ks&&!P.ks.hidden&&!P.ks.contains(e.target)){P.ret=null;ovKeysClose(false)}}
function ovPalRun(i){const P=OV_K1,c=P.rows[i];if(!c)return;ovPalClose();
  if(c.ask!=null){aiOpen(true);aiSend(c.ask);return}
  const R=ovRecent().filter(x=>x!==c.id);R.unshift(c.id);UI.ovRecent=R.slice(0,5);saveUI();P.n++;runCommand(c.id,'palette')}
function ovPalAi(){const q=OV_K1.el.querySelector('input').value.trim();ovPalClose(false);OV_K1.ret=null;aiOpen(true);
  if(q)setTimeout(()=>{const ta=document.querySelector('#aip textarea');if(ta){ta.value=q;ta.dispatchEvent(new Event('input'))}},70)}
function ovPalOpen(){const P=OV_K1;if(P.ks&&!P.ks.hidden)ovKeysClose(false);
  if(P.el&&!P.el.hidden){P.el.querySelector('input').focus();return}
  if(!P.ret){const a=document.activeElement;P.ret=a&&a!==document.body?a:null}
  let el=P.el;if(!el){el=P.el=document.createElement('div');el.id='ovPal';el.className='pop';el.setAttribute('role','dialog');el.setAttribute('aria-label','Command palette');
    el.innerHTML=`<div class="ovq"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5"/><path d="M12.3 12.3 17 17"/></svg><input type="text" spellcheck="false" autocomplete="off" placeholder="Type a command, or ask the Assistant" aria-label="Command" role="combobox" aria-expanded="true" aria-autocomplete="list" aria-controls="ovPalL"></div><div class="ovrs" role="listbox" id="ovPalL" aria-label="Commands"></div><div class="ovft"><span>↑↓ move</span><span>↵ run</span><span>Esc close</span><span>? keys</span><span class="ovfr">${esc(ovKeyTx('Mod+K'))} again: the Assistant</span></div>`;
    document.body.appendChild(el);const inp=el.querySelector('input'),rs=el.querySelector('.ovrs');
    inp.addEventListener('input',()=>{rs.scrollTop=0;ovPalDraw()});
    inp.addEventListener('keydown',e=>{const k=e.key,n=P.rows.length;e.stopPropagation();
      if(k==='ArrowDown'){e.preventDefault();P.fi=n?(P.fi+1)%n:0;ovPalHl(true)}else if(k==='ArrowUp'){e.preventDefault();P.fi=n?(P.fi-1+n)%n:0;ovPalHl(true)}
      else if(k==='PageDown'){e.preventDefault();P.fi=Math.min(n-1,P.fi+8);ovPalHl(true)}else if(k==='PageUp'){e.preventDefault();P.fi=Math.max(0,P.fi-8);ovPalHl(true)}
      else if(k==='Enter'){e.preventDefault();if(!e.repeat)ovPalRun(P.fi)}else if(k==='Escape'){e.preventDefault();ovPalClose()}else if(k==='Tab'){e.preventDefault()}
      else if(k==='?'&&!inp.value){e.preventDefault();ovPalClose(false);ovKeysOpen()}
      else if((e.metaKey||e.ctrlKey)&&!e.altKey&&k.toLowerCase()==='k'){e.preventDefault();ovPalAi()}});
    inp.addEventListener('keyup',e=>e.stopPropagation());
    rs.addEventListener('pointermove',e=>{const r=e.target.closest('.ovr');if(r&&+r.dataset.r!==P.fi){P.fi=+r.dataset.r;ovPalHl(true)}});
    el.addEventListener('pointerdown',e=>{if(e.target!==inp)e.preventDefault()});
    rs.addEventListener('click',e=>{const r=e.target.closest('.ovr');if(r)ovPalRun(+r.dataset.r)});
    inp.addEventListener('blur',()=>setTimeout(()=>{if(!el.hidden&&!el.contains(document.activeElement)){P.ret=null;ovPalClose(false)}},150))}
  const inp=el.querySelector('input'),rs=el.querySelector('.ovrs');inp.value='';rs.textContent='';el.hidden=false;inp.focus({preventScroll:true});ovPalDraw();
  document.addEventListener('pointerdown',ovK1Out,true)}
/* the key sheet (?): every shortcut by area, a search over names and keys, conflicts counted (a key that two commands share) */
function ovKeysDraw(){const el=OV_K1.ks,q=el.querySelector('input').value.trim().toLowerCase(),words=q.split(/\s+/).filter(Boolean);
  const all=SCA.map(a=>[a,scBind(a)]).filter(x=>x[1]),cnt=new Map();for(const[a,b] of all)if(!a.lock)cnt.set(b,(cnt.get(b)||0)+1);
  const cf=new Set([...cnt].filter(x=>x[1]>1).map(x=>x[0]));let h='',n=0;
  const gs=OV_GORD.concat([...new Set(SCA.map(a=>a.g))].filter(g=>!OV_GORD.includes(g)));
  for(const g of gs){const L=all.filter(([a,b])=>{if(a.g!==g)return false;const t=(a.l+' '+ovGName(g)+' '+ovKeyTx(b)+' '+b.replace(/Mod/,'cmd command ctrl').replace(/Alt/,'option alt')).toLowerCase();return words.every(w=>t.includes(w))});
    if(!L.length)continue;n+=L.length;h+=`<div class="ovpg">${esc(ovGName(g))}</div>`+L.map(([a,b])=>`<div class="ovkr${!a.lock&&cf.has(b)?' ovcf':''}"><span>${esc(a.l)}</span><kbd>${esc(ovKeyTx(b))}</kbd></div>`).join('')}
  el.querySelector('.ovcols').innerHTML=h||'<div class="ovkr"><span>No shortcut matches “'+esc(q)+'”.</span></div>';
  el.querySelector('.ovcnt').textContent=`${all.length} KEYS · ${[...cnt].filter(x=>x[1]>1).reduce((s,x)=>s+x[1],0)} IN CONFLICT`}
function ovKeysClose(back){const P=OV_K1;if(!P.ks||P.ks.hidden)return;P.ks.hidden=true;document.removeEventListener('pointerdown',ovK1Out,true);if(back!==false)ovK1Ret()}
function ovKeysOpen(){const P=OV_K1;if(P.el&&!P.el.hidden)ovPalClose(false);
  if(!P.ret){const a=document.activeElement;P.ret=a&&a!==document.body?a:null}
  let el=P.ks;if(!el){el=P.ks=document.createElement('div');el.id='ovKeys';el.className='pop';el.setAttribute('role','dialog');el.setAttribute('aria-label','Keyboard shortcuts');
    el.innerHTML=`<div class="ovq"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5"/><path d="M12.3 12.3 17 17"/></svg><input type="text" spellcheck="false" autocomplete="off" placeholder="Find a shortcut or a key" aria-label="Find a shortcut"><span class="ovcnt"></span></div><div class="ovcols"></div><div class="ovft"><span>Esc close</span><span>${esc(ovKeyTx('Mod+K'))} commands</span><button type="button" class="ovfr ovkset">Change keys in Settings</button></div>`;
    document.body.appendChild(el);const inp=el.querySelector('input');inp.addEventListener('input',ovKeysDraw);
    inp.addEventListener('keydown',e=>{e.stopPropagation();if(e.key==='Escape'){e.preventDefault();ovKeysClose()}else if(e.key==='Tab'){e.preventDefault();el.querySelector('.ovkset').focus()}
      else if((e.metaKey||e.ctrlKey)&&!e.altKey&&e.key.toLowerCase()==='k'){e.preventDefault();ovKeysClose(false);ovPalOpen()}});
    inp.addEventListener('keyup',e=>e.stopPropagation());
    const sb=el.querySelector('.ovkset');sb.addEventListener('click',()=>{P.ret=null;ovKeysClose(false);openSettings('keys')});
    sb.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();ovKeysClose()}else if(e.key==='Tab'){e.preventDefault();e.stopPropagation();inp.focus()}})}
  const inp=el.querySelector('input');inp.value='';el.hidden=false;ovKeysDraw();inp.focus({preventScroll:true});
  document.addEventListener('pointerdown',ovK1Out,true)}
/* the two commands join the shortcut list once the script has run (SCA is defined further down) */
function ovK1Init(){try{SCA.length;SCM.size}catch(e){setTimeout(ovK1Init,30);return}if(SCM.has('help.palette'))return;
  const ai=SCM.get('ai');if(ai&&ai.d==='Mod+K')ai.d='';
  SCA.push({id:'help.palette',g:'help',l:'Command palette (every command, and the Assistant)',d:'Mod+K',ic:'M3 5h14v10H3zM6 9l2 1.5L6 12M10 12h4',run:()=>ovPalOpen()});SCM.set('help.palette',SCA[SCA.length-1]);
  SCA.push({id:'help.keySheet',g:'help',l:'Key sheet (every shortcut at a glance)',d:'?',ic:'M2 6h16v9H2zM5 9h1M8 9h1M11 9h1M14 9h1M6 12h8',run:()=>ovKeysOpen()});SCM.set('help.keySheet',SCA[SCA.length-1])}
setTimeout(ovK1Init,0);
window.OV_HOOKS=window.OV_HOOKS||{};OV_HOOKS.palette={open:()=>ovPalOpen(),close:()=>ovPalClose(),keys:()=>ovKeysOpen()};
