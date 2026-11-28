/* lane H (task XT-DL4): safe mode, the early half. It runs once, right where the settings are read at start, before anything uses them.
   In safe mode (sessionStorage al-safe, set by "Restart in safe mode") the customisations (XT_SAFE.K: every setting of the settings table,
   the Workshop's values, the keyboard shortcuts, the layout of the transport bar, track headers, mixer and devices) start at AudioLab's
   defaults. Nothing is deleted: UI.toJSON writes the stored customisations back on every save, so they all return when safe mode ends.
   al-xt-start marks a start that has not reached its first frame yet; if it is still there at the next start, safe mode is offered. */
const XT_SAFE=(function(){const K=__STRIP__,S={on:false,K,stored:null,offer:false,drop:false,shift:false};if(CHILD)return S;
 try{S.on=sessionStorage.getItem('al-safe')==='1'}catch(e){}
 try{S.offer=!S.on&&!!localStorage.getItem('al-xt-start');localStorage.setItem('al-xt-start',String(Date.now()))}catch(e){}
 if(!S.on)return S;
 try{S.stored=JSON.parse(localStorage.getItem('audiolab-ui')||'null')}catch(e){}if(!S.stored||typeof S.stored!=='object')S.stored={};
 for(const k of K){if(k in XT_UI0)UI[k]=JSON.parse(JSON.stringify(XT_UI0[k]));else delete UI[k]}
 Object.defineProperty(UI,'toJSON',{configurable:true,enumerable:false,value(){const o={};for(const k of Object.keys(this))if(S.drop||!K.includes(k))o[k]=this[k];/* drop: a reset or a restore writes its own values */
  if(!S.drop)for(const k of K)if(k in S.stored)o[k]=S.stored[k];return o}});
 return S})();
