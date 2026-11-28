/* ===================== UI RULES: HIDE AND RENAME A CONTROL (v0.000, task XT-DL5) =====================
   docs/extensions-plan.md 9.6 b and 9.7 DL5; the user's pick K12a with their note: the right-click entries name the control
   ("Hide the Loop button", "Customise the Loop button…", never a bare "Hide this"), sit in the amber Advanced group of the menu,
   and the first use explains what happens and how to undo it.
   The rules (UI.xtRules, the format of ui-rules.json): {audiolab:'ui-rules',version:1,layouts:{all:[{id,hide,rename}]}}, by the
   stable control ids of DL1 (data-al, CONTROLS). A rule on a repeated control (track.mute) covers every track. Later rules win.
   - hide: one small stylesheet ([data-al="id"]{display:none}); hidden is not gone: its key and command still work.
   - rename: 24 characters at most, plain text; the label where the control shows plain text, and its tooltip and spoken name.
   - Protected controls (XT_RULE_PROTECT: the menu, Record, the master meter and level boxes, the clip warning, the performance
     meter, the mixer's Close, the master faders) can never be hidden: the entry says why.
   - A rule with an unknown id (a newer AudioLab, a typo) or a bad value is kept and changes nothing; What is changed lists it.
   - Undo: every rule is a row of the Workshop's What is changed (✕), reset and safe mode cover them (key xtRules).
   For lane F (OV3): XT_HOOKS.rules.items(control) gives the Advanced group's entries for a control (xtControlOf(el));
   set OV_HOOKS.xtAdvanced=true when your menus add them, and this block stops adding them.
   Cost: no rules: no stylesheet, nothing per frame, one capture listener for right-clicks. With rules: one stylesheet, and a
   rename pass inside the id pass of an area that was rebuilt. */
const XT_RULE_PROTECT=new Set(['transport.logo','transport.record','transport.masterMeter','transport.clipWarning','transport.peak','transport.loudness','transport.performance',
  'mixer.close','mixer.master.volume','mixer.master.display','track.master.volume']);
const XT_RL={hid:new Set(),ren:new Map(),bad:[],css:null,cm:null,cmT:0,MAX:24,IC:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/></svg>'};
function xtRulesAll(){const r=UI.xtRules;return r&&r.layouts&&Array.isArray(r.layouts.all)?r.layouts.all:[]}
function xtRuleId(id){let i=String(id||'');for(let n=0;n<8&&CONTROL_ALIAS[i];n++)i=CONTROL_ALIAS[i];return i}
/* one rule checked: {ok, why}; the same check for the menu, the dialog and (DL9) the file */
function xtRuleCheck(o){if(!o||typeof o!=='object')return{ok:false,why:'not a rule'};const id=xtRuleId(o.id);if(!XTCI.has(id))return{ok:false,why:'no control has the id '+String(o.id).slice(0,60)};
  if(o.hide!==undefined&&typeof o.hide!=='boolean')return{ok:false,why:'hide is true or false'};
  if(o.hide&&XT_RULE_PROTECT.has(id))return{ok:false,why:'the '+XTCI.get(id)[2]+' is protected: AudioLab always shows it'};
  if(o.rename!==undefined){if(typeof o.rename!=='string'||!o.rename.trim())return{ok:false,why:'a name is some plain text'};if(o.rename.trim().length>XT_RL.MAX)return{ok:false,why:'a name is '+XT_RL.MAX+' characters at most'}}
  return{ok:true,why:''}}
function xtRuleClean(s){return String(s||'').replace(/[\u0000-\u001f\u007f<>]/g,'').replace(/\s+/g,' ').trim().slice(0,XT_RL.MAX)}
/* apply every rule: the hide stylesheet, the renames; nothing at all when there are none */
function xtRulesApply(){const H=new Set(),R=new Map(),bad=[];
  for(const o of xtRulesAll()){const c=xtRuleCheck(o);if(!c.ok){bad.push({o,why:c.why});continue}const id=xtRuleId(o.id);
    if(o.hide===true)H.add(id);else if(o.hide===false)H.delete(id);if(o.rename!==undefined)R.set(id,xtRuleClean(o.rename))}
  const old=XT_RL.ren;XT_RL.hid=H;XT_RL.ren=R;XT_RL.bad=bad;
  if(H.size){if(!XT_RL.css){XT_RL.css=document.createElement('style');XT_RL.css.id='xtRulesCss';document.head.appendChild(XT_RL.css)}
    XT_RL.css.textContent=[...H].map(id=>`[data-al="${id}"]`).join(',')+'{display:none!important}'}
  else if(XT_RL.css){XT_RL.css.remove();XT_RL.css=null}
  if(R.size||old.size)for(const a in CONTROL_AREAS)xtRenArea(a);return{hidden:H.size,renamed:R.size,bad:bad.length}}
/* the renames in one area (after its id pass); a control whose rename was removed gets its own words back */
function xtRenArea(area){const r=document.querySelector(CONTROL_AREAS[area]);if(!r)return;
  for(const e of r.querySelectorAll('[data-xtren]')){const id=e.dataset.al;if(XT_RL.ren.has(id)&&e.dataset.xtren===XT_RL.ren.get(id))continue;xtRenOff(e)}
  if(!XT_RL.ren.size)return;for(const[id,nm]of XT_RL.ren){if(!id.startsWith(area+'.'))continue;for(const e of r.querySelectorAll(`[data-al="${id}"]`))if(e.dataset.xtren!==nm)xtRenOn(e,nm)}}
function xtRenOn(e,nm){if(e.dataset.xtren===undefined){e.dataset.xtrT=e.title||'';e.dataset.xtrA=e.getAttribute('aria-label')||'';
    const plain=!e.children.length&&e.textContent.trim()!==''&&!/^(INPUT|SELECT|TEXTAREA|CANVAS)$/.test(e.tagName);e.dataset.xtrX=plain?e.textContent:'\u0000'}
  if(e.dataset.xtrX!=='\u0000')e.textContent=nm;const t=e.dataset.xtrT;e.title=nm+(t?': '+t:'');e.setAttribute('aria-label',nm);e.dataset.xtren=nm}
function xtRenOff(e){if(e.dataset.xtrX!==undefined&&e.dataset.xtrX!=='\u0000')e.textContent=e.dataset.xtrX;e.title=e.dataset.xtrT||'';
  if(e.dataset.xtrA)e.setAttribute('aria-label',e.dataset.xtrA);else e.removeAttribute('aria-label');for(const k of['xtren','xtrT','xtrA','xtrX'])delete e.dataset[k]}
{const _xt=xtTag;xtTag=function(area){const n=_xt.apply(this,arguments);if(XT_RL.ren.size||(document.querySelector(CONTROL_AREAS[area]+' [data-xtren]')))try{xtRenArea(area)}catch(e){console.error('AudioLab rules',e)}return n}}
/* change the rules: one rule per control (hide and rename merged), stored, applied */
function xtRuleSet(id,ch){id=xtRuleId(id);const L=xtRulesAll().filter(o=>xtRuleId(o.id)!==id),cur=xtRulesAll().filter(o=>xtRuleId(o.id)===id).reduce((a,o)=>Object.assign(a,o),{});
  if(typeof ch.rename==='string'&&ch.rename.trim().length>XT_RL.MAX)return{ok:false,why:'a name is '+XT_RL.MAX+' characters at most'};const n=Object.assign({},cur,ch,{id});for(const k of Object.keys(n))if(n[k]===null||n[k]===false&&k==='hide')delete n[k];if(n.rename!==undefined)n.rename=xtRuleClean(n.rename);if(n.rename==='')delete n.rename;
  const c=xtRuleCheck(n);if(!c.ok&&Object.keys(n).length>1)return c;if(Object.keys(n).length>1)L.push(n);
  if(L.length)UI.xtRules={audiolab:'ui-rules',version:1,layouts:{all:L}};else delete UI.xtRules;saveUI();xtRulesApply();try{xtChgDraw()}catch(e){}return{ok:true,why:''}}
function xtRuleOf(id){id=xtRuleId(id);return xtRulesAll().filter(o=>xtRuleId(o.id)===id).reduce((a,o)=>Object.assign(a,o),{})}
function xtRuleWhere(c){const id=c[0];return id.startsWith('mixer.strip.')?' on every channel':id.startsWith('track.lane.')?' on every automation lane':/^track\.(?!add\.|master\.|recordAutomation|showAutomation)/.test(id)?' on every track':''}
function xtRuleArea(c){const a=c[0].split('.')[0];return a==='transport'?'the transport bar':a==='mixer'?'the mixer':'the track headers'}
/* the Advanced group for a right-clicked control (K12a): names the control, marked, explained on first use */
function xtAdvItems(c){if(!c)return[];const nm=c[2],pro=XT_RULE_PROTECT.has(c[0]),r=xtRuleOf(c[0]),shown=nm,now=r.rename?' (named “'+r.rename+'” now)':'';
  return[{g:'Advanced',adv:1},
    pro?{label:'Hide the '+shown,sub:'Protected: AudioLab always shows the '+nm+', so it cannot be hidden',dis:true}
       :{label:'Hide the '+shown,sub:'Advanced: takes it out of '+xtRuleArea(c)+xtRuleWhere(c)+'. Its key and command still work. Workshop › What is changed brings it back',act:()=>xtRuleHideAsk(c)},
    {label:'Customise the '+shown+'…',sub:'Advanced: give the '+nm+now+' another name'+(pro?'':', hide it')+', or put it back as it came. Every change is listed in Workshop › What is changed',act:()=>xtRuleCustom(c)}]}
function xtRuleHowBack(c){return'To bring it back: the AudioLab menu (right-click the logo) › Workshop… › What is changed, then ✕ on its row. Holding Shift while AudioLab starts gives safe mode, which shows everything as it came.'}
async function xtRuleHideAsk(c){if(XT_RULE_PROTECT.has(c[0]))return false;const nm=c[2];
  if(!UI.xtRuleSeen){const r=await askChoice('Advanced: hide the '+nm+'?','This is an advanced customisation. The '+nm+' disappears from '+xtRuleArea(c)+xtRuleWhere(c)+'. Nothing else changes: its keyboard shortcut and its command keep working. '+xtRuleHowBack(c),
      [{label:'Cancel',v:null},{label:'Hide the '+nm,v:1,cls:'pri'}],XT_RL.IC);if(r!==1)return false;UI.xtRuleSeen=1}
  const k=xtRuleSet(c[0],{hide:true});if(k.ok)toast('The '+nm+' is hidden. Workshop › What is changed brings it back.');return k.ok}
async function xtRuleCustom(c){const nm=c[2],pro=XT_RULE_PROTECT.has(c[0]),r=xtRuleOf(c[0]),first=!UI.xtRuleSeen;
  const now=[r.rename?'named “'+r.rename+'”':'',r.hide?'hidden':''].filter(Boolean).join(' and ');
  const B=[{label:'Cancel',v:null},{label:'Rename…',v:'ren',cls:'pri'}];if(!pro&&!r.hide)B.push({label:'Hide it',v:'hide'});if(r.hide)B.push({label:'Show it again',v:'show'});if(now)B.push({label:'Put it back as it came',v:'reset'});
  const v=await askChoice('Advanced: customise the '+nm,(first?'This is an advanced customisation: it changes how AudioLab looks for you, never your projects. ':'')+'The '+nm+(now?' is '+now+' now. ':' is as it came. ')+'You can give it another name'+(pro?' (it is protected, so it cannot be hidden)':' or hide it')+xtRuleWhere(c)+'. '+xtRuleHowBack(c),B,XT_RL.IC);
  if(!v)return false;UI.xtRuleSeen=1;
  if(v==='hide')return xtRuleSet(c[0],{hide:true}).ok;if(v==='show')return xtRuleSet(c[0],{hide:null}).ok;if(v==='reset')return xtRuleSet(c[0],{hide:null,rename:null}).ok;
  const t=await askText('New name for the '+nm+' ('+XT_RL.MAX+' characters at most; empty puts back its own)',r.rename||'');if(t===null||t===undefined)return false;
  const k=xtRuleSet(c[0],{rename:t.trim()?t:null});if(!k.ok)toast('Not renamed: '+k.why+'.');return k.ok}
/* the right-click: remember the control under it; menus opened for it get the Advanced group; a control with no menu of its own gets one */
if(!CHILD){addEventListener('contextmenu',e=>{const c=xtControlOf(e.target);XT_RL.cm=c&&c[0]!=='transport.extra.gap'&&c[0]!=='transport.extra.space'?c:null;XT_RL.cmT=performance.now()},true);
  addEventListener('contextmenu',e=>{const c=XT_RL.cm;if(!c||e.defaultPrevented||performance.now()-XT_RL.cmT>100||window.OV_HOOKS&&OV_HOOKS.xtAdvanced)return;e.preventDefault();
    openMenu(e.clientX,e.clientY,[{head:c[2].charAt(0).toUpperCase()+c[2].slice(1)}])})}
{const _om=openMenu;openMenu=function(cx,cy,items){const c=XT_RL.cm;
  if(c&&Array.isArray(items)&&performance.now()-XT_RL.cmT<400&&!(window.OV_HOOKS&&OV_HOOKS.xtAdvanced)){XT_RL.cm=null;try{items=items.concat(xtAdvItems(c))}catch(e){}}
  return _om.call(this,cx,cy,items)}}
/* What is changed (DL4): one row per rule, ✕ removes it; reset and safe mode cover the key xtRules */
XT_SAFE.K.push('xtRules');if(XT_SAFE.on)delete UI.xtRules;
{const _l=xtChgList;xtChgList=function(stored){const out=_l.apply(this,arguments);if(stored){try{if(Array.isArray(JSON.parse(sessionStorage.getItem('al-safe-list')||'null')))return out}catch(e){}}
  const U=stored?(XT_SAFE.stored||{}):UI,A=U.xtRules&&U.xtRules.layouts&&Array.isArray(U.xtRules.layouts.all)?U.xtRules.layouts.all:[],seen=new Set();
  for(let i=A.length-1;i>=0;i--){const o=A[i];if(!o||seen.has(xtRuleId(o.id)))continue;seen.add(xtRuleId(o.id));const ck=xtRuleCheck(o),c=XTCI.get(xtRuleId(o.id));
    const v=ck.ok?[o.hide?'hidden':'',o.rename?'named “'+xtRuleClean(o.rename)+'”':''].filter(Boolean).join(', '):'not used: '+ck.why;
    out.push({kind:'lay',id:'xtr:'+String(o.id),l:c?c[2].charAt(0).toUpperCase()+c[2].slice(1):String(o.id).slice(0,60),v,d:'as it came',x:!stored,why:'a control rule'+(c?xtRuleWhere(c):'')})}
  return out}}
{const _u=xtChgUndo;xtChgUndo=function(kind,id){if(kind==='lay'&&String(id).startsWith('xtr:')){const rid=String(id).slice(4),L=xtRulesAll().filter(o=>o&&String(o.id)!==rid&&xtRuleId(o.id)!==xtRuleId(rid));
    if(L.length)UI.xtRules={audiolab:'ui-rules',version:1,layouts:{all:L}};else delete UI.xtRules;saveUI();xtRulesApply();return true}return _u.apply(this,arguments)}}
XT_HOOKS.rules={items:xtAdvItems,set:xtRuleSet,of:xtRuleOf,check:xtRuleCheck,apply:xtRulesApply,hidden:id=>XT_RL.hid.has(xtRuleId(id)),protected:id=>XT_RULE_PROTECT.has(xtRuleId(id))};
if(xtRulesAll().length)xtRulesApply();
