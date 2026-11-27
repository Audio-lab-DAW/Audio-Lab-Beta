()=>{const info=new Map(),depthC=new Map();
const get=e=>{let v=info.get(e);if(!v){const cs=getComputedStyle(e);v={i:cs.getPropertyValue('--d3').trim(),k:cs.getPropertyValue('--d3l').trim(),lh:cs.lineHeight,fs:parseFloat(cs.fontSize),ff:cs.fontFamily,fw:cs.fontWeight,disp:cs.display};info.set(e,v)}return v};
const depth=e=>{let d=0;for(let x=e;x.parentElement;x=x.parentElement)d++;return d};
const owner=(e,key)=>{const v=get(e)[key];if(v==='')return 0;let x=e;while(x.parentElement&&x.parentElement!==document.documentElement&&get(x.parentElement)[key]===v)x=x.parentElement;return depth(x)};
const normC=new Map(),box=document.createElement('div');box.style.cssText='position:absolute;left:-9999px;top:0;visibility:hidden;white-space:nowrap;line-height:normal;padding:0;border:0';box.textContent='Xg';document.body.appendChild(box);
const normal=v=>{const k=v.ff+'|'+v.fs+'|'+v.fw;if(!normC.has(k)){box.style.fontFamily=v.ff;box.style.fontSize=v.fs+'px';box.style.fontWeight=v.fw;normC.set(k,box.getBoundingClientRect().height)}return normC.get(k)};
const sites={};
for(const e of document.body.querySelectorAll('*')){if(e===box||/^(SCRIPT|STYLE|OPTION|OPTGROUP|BR|CANVAS|IMG)$/.test(e.tagName)||e.closest('svg'))continue;if(!e.checkVisibility())continue;
  let txt=false,inl=false;for(const n of e.childNodes){if(n.nodeType===3&&n.textContent.trim())txt=true;else if(n.nodeType===1&&!inl){const d=n instanceof SVGElement?'inline':get(n).disp;if(/^inline/.test(d))inl=true}}
  if(!txt&&!inl&&!/^(INPUT|SELECT|TEXTAREA|BUTTON)$/.test(e.tagName))continue;
  const v=get(e);if(v.i===''&&v.k==='')continue;
  const prev=e.style.getPropertyValue('font-size'),prio=e.style.getPropertyPriority('font-size');e.style.setProperty('font-size',(v.fs+3)+'px','important');const lh1=getComputedStyle(e).lineHeight;
  if(prev)e.style.setProperty('font-size',prev,prio);else e.style.removeProperty('font-size');
  if(!(v.lh==='normal'||lh1!==v.lh))continue;
  const lh0=v.lh==='normal'?normal(v):parseFloat(v.lh),di=owner(e,'i'),dk=owner(e,'k'),site=(v.k!==''&&dk>di)?v.k:(v.i!==''?v.i:v.k);
  let multi=0;if(txt){const g=document.createRange();g.selectNodeContents(e);const rs=g.getClientRects();let top=1e9,bot=-1e9;for(const r of rs){top=Math.min(top,r.top);bot=Math.max(bot,r.bottom)}if(bot-top>lh0*1.7)multi=1}
  const anc=new Set();for(let x=e.parentElement;x&&x!==document.documentElement;x=x.parentElement){const a=get(x);if(a.i!=='')anc.add(a.i);if(a.k!=='')anc.add(a.k)}
  const s=sites[site]||(sites[site]={v:{},is:{},multi:0,anc:{},ex:''});const key=(Math.round(lh0*100)/100)+'';s.v[key]=(s.v[key]||0)+1;s.is[v.i]=1;s.multi+=multi;for(const a of anc)s.anc[a]=1;
  if(!s.ex)s.ex=e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+'.'+String(e.className).slice(0,30)+' "'+(e.textContent||'').trim().slice(0,16)+'"'}
box.remove();return {text:[],sites}}
