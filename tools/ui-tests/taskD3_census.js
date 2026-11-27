()=>{const out={text:[],hit:[],scr:[]},vis=e=>e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}),r1=v=>Math.round(v*10)/10;
const path=e=>{const p=[];for(let x=e;x&&x!==document.body&&p.length<4;x=x.parentElement)p.unshift(x.tagName.toLowerCase()+(x.id?'#'+x.id:'')+(typeof x.className==='string'&&x.className.trim()?'.'+x.className.trim().split(/\s+/).slice(0,3).join('.'):''));return p.join('>')};
const clipOf=e=>{const r=[-1e9,-1e9,1e9,1e9];for(let x=e.parentElement;x&&x!==document.documentElement;x=x.parentElement){const cs=getComputedStyle(x),b=x.getBoundingClientRect();if(/hidden|clip/.test(cs.overflowX)){r[0]=Math.max(r[0],b.left);r[2]=Math.min(r[2],b.right)}if(/hidden|clip/.test(cs.overflowY)){r[1]=Math.max(r[1],b.top);r[3]=Math.min(r[3],b.bottom)}if(cs.position==='fixed')break}return r};
const rec=(e,txt,rect,pseudo)=>{const cs=getComputedStyle(e,pseudo||null),o={p:path(e)+(pseudo||''),t:txt.slice(0,40),fs:parseFloat(cs.fontSize),fw:+cs.fontWeight,ff:cs.fontFamily.split(',')[0].replace(/["']/g,''),num:cs.fontVariantNumeric,z:e.currentCSSZoom||1,up:cs.textTransform==='uppercase'?1:0};
  if(rect){o.r=[r1(rect.left),r1(rect.top),r1(rect.right),r1(rect.bottom)];const c=clipOf(pseudo?e:e),b=e.getBoundingClientRect();const self=getComputedStyle(e);
    if(/hidden|clip/.test(self.overflowX)){c[0]=Math.max(c[0],b.left);c[2]=Math.min(c[2],b.right)}if(/hidden|clip/.test(self.overflowY)){c[1]=Math.max(c[1],b.top);c[3]=Math.min(c[3],b.bottom)}
    o.cx=r1(Math.max(0,c[0]-rect.left,rect.right-c[2]));o.cy=r1(Math.max(0,c[1]-rect.top-2,rect.bottom-c[3]-2));
    o.sx=r1(Math.max(0,rect.right-b.right,b.left-rect.left));o.el=(self.textOverflow==='ellipsis'&&e.scrollWidth>e.clientWidth+1)?1:0;
    o.on=(rect.right>0&&rect.left<innerWidth&&rect.bottom>0&&rect.top<innerHeight&&c[2]>c[0]&&c[3]>c[1])?1:0}
  if(rect&&o.on){const x=Math.min(innerWidth-1,Math.max(0,(rect.left+rect.right)/2)),y=Math.min(innerHeight-1,Math.max(0,(rect.top+rect.bottom)/2)),h=document.elementFromPoint(x,y);o.top=(h&&(h===e||e.contains(h)||h.contains(e)))?1:0}
  out.text.push(o)};
for(const e of document.body.querySelectorAll('*')){if(/^(SCRIPT|STYLE|svg|OPTION|OPTGROUP)$/i.test(e.tagName)||e.closest('svg'))continue;if(!vis(e))continue;
  let has=false;for(const n of e.childNodes){if(n.nodeType===3&&n.textContent.trim()){has=true;const g=document.createRange();g.selectNodeContents(n);const b=g.getBoundingClientRect();if(b.width>0&&b.height>0)rec(e,n.textContent.trim(),b)}}
  if(/^(INPUT|SELECT|TEXTAREA)$/.test(e.tagName)&&!/^(range|checkbox|radio|color|file|hidden)$/.test(e.type||'')){const b=e.getBoundingClientRect();if(b.width>0)rec(e,'['+(e.tagName==='SELECT'?(e.selectedOptions[0]||{}).text||'':e.value||e.placeholder||'')+']',null)}
  for(const ps of['::before','::after']){const c=getComputedStyle(e,ps).content;if(c&&c!=='none'&&c!=='normal'&&/[A-Za-z0-9]/.test(c.replace(/^(url|counter|attr)\(.*$/,'x'))&&c!=='""')rec(e,'pseudo '+c,null,ps)}
  if(e.matches('button,input,select,textarea,a[href],[role=button],[role=slider],[role=tab],[data-c],summary,label,[tabindex]')){const b=e.getBoundingClientRect();if(b.width>0)out.hit.push({p:path(e),r:[r1(b.left),r1(b.top),r1(b.width),r1(b.height)]})}
  const cs=getComputedStyle(e);if(/auto|scroll/.test(cs.overflowX+cs.overflowY)&&e.clientWidth>0)out.scr.push({p:path(e),x:e.scrollWidth-e.clientWidth,y:e.scrollHeight-e.clientHeight})}
/* pairs of texts from different elements that overlap on screen */
out.ov=[];const T=out.text.filter(t=>t.r&&t.on&&!t.cx&&!t.cy&&t.top),els=[];
for(let i=0;i<T.length;i++)for(let j=i+1;j<T.length;j++){const a=T[i].r,b=T[j].r,w=Math.min(a[2],b[2])-Math.max(a[0],b[0]),h=Math.min(a[3],b[3])-Math.max(a[1],b[1]);if(w>1.5&&h>3.4&&T[i].p!==T[j].p)out.ov.push([T[i].p,T[i].t.slice(0,20),T[j].p,T[j].t.slice(0,20),Math.round(w*10)/10])}
return out}
