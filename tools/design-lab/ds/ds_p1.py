#!/usr/bin/env python3
"""Task DS-P1 (lane A, design round 2, details PS3 and PK3 of look P4): piano roll rows, keys and chord names.
   python3 tools/design-lab/ds/ds_p1.py index.html
PS3: with a scale chosen, rows in the scale lift (#17181e) and the others sink (#0d0d11), a fine amber line on every root
row, a note outside the scale gets a dotted amber ring, and says so ("G#3 outside A minor") when it is the only one or
two in view, or when it is selected or under the pointer; chord names (Am, F, C, G7 ...) in the ruler, found from every
instrument track's notes under the clip (half-bar steps, once per edit, cached). PK3: narrow keys (24 px) and a name on
every row (root amber, in the scale light, outside grey), the key column drawn once per view change into a cached
picture. Only the AudioLab look (dsAC3), not on drum clips (their pad names stay). No audio nodes.
Every anchor is asserted. Re-run on a fresh file after a rebase."""
import sys
F = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(F, encoding='utf-8').read()
assert 'task DS-P1' not in s, 'already applied'
assert 'function dsAC3()' in s, 'needs task DS-A3'

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:120])
    s = s.replace(old, new)

BLOCK = r"""/* task DS-P1 (lane A, design round 2, PS3 and PK3): piano roll scale rows, root line, out-of-scale ring, chord names in
   the ruler, narrow keys with every row named. dsP1Begin gives the drawing state for one picture; the chord list is worked
   out once per edit (changed() counts edits) and the key column is a cached picture redrawn only when the view changes. */
const DSP1={rev:0,S:null,ck:'',chords:[],kc:null,kk:'',hov:null,amb:'245,185,76'};
{const f=changed;changed=function(){DSP1.rev++;return f.apply(this,arguments)}}
function dsNN(p){return nname(p).replace('#','♯')}
function dsP1Begin(t,c){const on=dsAC3(),sc=SCALES[PR.scale],d=(window.devicePixelRatio||1)*(typeof ZOOM==='number'?ZOOM:1);
  return{on,sc:on?sc:null,drum:!!(t.inst&&t.inst.preset==='drums'),d,hp:lkT().hair(d),t,c,out:[]}}
function dsP1In(sc,p){return sc.includes(((p-PR.root)%12+12)%12)}
/* the row colour (only the AudioLab look with a scale) */
function dsP1Row(DQ,deg,col){return DQ.on&&DQ.sc?(DQ.sc.includes(deg)?'#17181e':'#0d0d11'):col}
function dsP1Root(g,DQ,y,w){if(!DQ.on||!DQ.sc)return;g.fillStyle='rgba('+DSP1.amb+',.42)';g.fillRect(KEYW,Math.round((y+PR.rh)*DQ.d)/DQ.d-DQ.hp,w-KEYW,DQ.hp)}
/* a note outside the scale: dotted amber ring; remembered for its label */
function dsP1Out(g,DQ,n,x,y,nw){if(!DQ.sc||DQ.drum||dsP1In(DQ.sc,n.p))return;g.save();g.setLineDash([2,2]);g.strokeStyle='rgba('+DSP1.amb+',.9)';g.lineWidth=1;rr(g,x-1.5,y-.5,nw+3,PR.rh+1,3);g.stroke();g.restore();DQ.out.push({n,x,y,nw})}
function dsP1Labels(g,DQ,w){if(!DQ.on||!DQ.out.length)return;const all=DQ.out.length<=2,sn=NN[PR.root].replace('#','♯')+' '+PR.scale;
  g.save();g.font='10px Inter,system-ui,sans-serif';g.textBaseline='middle';g.fillStyle='rgba('+DSP1.amb+',.95)';
  for(const o of DQ.out){if(!(all||o.n.sel||o.n===DSP1.hov))continue;const s=dsNN(o.n.p)+' outside '+sn,tw=g.measureText(s).width,yc=o.y+PR.rh/2+.5;
    if(o.x-6-tw>KEYW+2){g.textAlign='right';g.fillText(s,o.x-6,yc)}else if(o.x+o.nw+6+tw<w){g.textAlign='left';g.fillText(s,o.x+o.nw+6,yc)}}
  g.restore()}
/* chords: every instrument track's notes under the clip (not drums, not muted), in half-bar steps */
const DSP1_CH=[['',[0,4,7]],['m',[0,3,7]],['dim',[0,3,6]],['aug',[0,4,8]],['sus2',[0,2,7]],['sus4',[0,5,7]],['7',[0,4,7,10]],['maj7',[0,4,7,11]],['m7',[0,3,7,10]]];
function dsP1ChordOf(wt,bass){let tot=0,mx=0;for(const x of wt){tot+=x;mx=Math.max(mx,x)}if(!tot)return null;const th=mx*.3;let npc=0;for(const x of wt)if(x>th)npc++;if(npc<3)return null;
  let best=null,bs=-1e9;for(let r=0;r<12;r++)for(const[nm,T]of DSP1_CH){let inW=0,ok=true;for(const i of T){const v=wt[(r+i)%12];if(v<=th){ok=false;break}inW+=v}if(!ok)continue;
    const sc=inW-.7*(tot-inW)+(bass===r?.15*tot:0)-(T.length>3?.04*tot:0);if(sc>bs){bs=sc;best=NN[r].replace('#','♯')+nm}}
  return best}
function dsP1Chords(c){const key=DSP1.rev+'|'+c.id+'|'+c.start+'|'+c.len+'|'+c.off;if(DSP1.S===S&&DSP1.ck===key)return DSP1.chords;
  const s0=c.start,s1=c.start+c.len,g0=Math.floor(c.off/2)*2,NS=Math.max(0,Math.ceil((c.off+c.len-g0)/2)),W=[],B=[];for(let i=0;i<NS;i++){W.push(new Float32Array(12));B.push(999)}
  for(const t2 of S.tracks){if(t2.kind!=='inst'||t2.mute||(t2.inst&&t2.inst.preset==='drums'))continue;
    for(const c2 of t2.clips){if(!c2.notes||c2.mute||c2.start>=s1||c2.start+c2.len<=s0)continue;
      for(const n of c2.notes){if(n.m||n.s<c2.off||n.s>=c2.off+c2.len)continue;const a=c2.start+n.s-c2.off,e=Math.min(a+n.l,c2.start+c2.len);
        const la=Math.max(a,s0)-c.start+c.off,le=Math.min(e,s1)-c.start+c.off;if(le<=la)continue;
        for(let k=Math.max(0,Math.floor((la-g0)/2));k<NS&&g0+k*2<le;k++){const ov=Math.min(le,g0+k*2+2)-Math.max(la,g0+k*2);if(ov<=0)continue;W[k][n.p%12]+=ov;if(ov>=.5&&n.p<B[k])B[k]=n.p}}}}
  const out=[];let last=null;for(let k=0;k<NS;k++){const nm=dsP1ChordOf(W[k],B[k]<999?B[k]%12:-1);if(nm&&nm!==last)out.push({s:Math.max(c.off,g0+k*2),name:nm});last=nm}
  DSP1.S=S;DSP1.ck=key;DSP1.chords=out;return out}
function dsP1Ruler(g,DQ,c,w,lb){if(!DQ.on||DQ.drum)return;const L=dsP1Chords(c);if(!L.length)return;
  g.save();g.beginPath();g.rect(KEYW,0,w-KEYW,PRUL);g.clip();g.font='11px Inter,system-ui,sans-serif';
  const px=s=>KEYW+(s-PR.x)*PR.ppb;let end=-1e9;
  for(let i=0;i<L.length;i++){const e=L[i];let x=px(e.s);const nx=i+1<L.length?px(L[i+1].s):1e9;if(nx<KEYW)continue;if(x>w)break;
    let off=5;const bar=e.s/4;if(Math.abs(bar-Math.round(bar))<1e-6&&Math.round(bar)%lb===0){g.font='11px Inter,system-ui,sans-serif';off=g.measureText(String(Math.round(bar)+1)).width+10}
    g.font='600 10.5px Inter,system-ui,sans-serif';const tw=g.measureText(e.name).width;
    if(x<KEYW){x=KEYW;off=4;if(x+off+tw+8>nx)continue}else{g.fillStyle='rgba('+DSP1.amb+',.7)';g.fillRect(Math.round(x*DQ.d)/DQ.d,1,DQ.hp,5)}
    if(x+off<end+6)continue;g.fillStyle='rgba('+DSP1.amb+',.95)';g.fillText(e.name,x+off,14);end=x+off+tw}
  g.restore()}
/* PK3: narrow keys (24 px) and a name on every row, a cached picture of the whole key column */
function dsP1Keys(g,DQ,pTop,pBot,gh){const H=gh-PRUL;if(H<=0)return;const D=DQ.d,key=[PR.y,PR.rh,PR.scale,PR.root,H,D,pTop,pBot].join('|');
  let cv=DSP1.kc;if(!cv){cv=DSP1.kc=document.createElement('canvas')}
  if(DSP1.kk!==key){DSP1.kk=key;const pw=Math.max(1,Math.round(KEYW*D)),ph=Math.max(1,Math.round(H*D));if(cv.width!==pw||cv.height!==ph){cv.width=pw;cv.height=ph}
    const k=cv.getContext('2d');k.setTransform(D,0,0,D,0,0);k.clearRect(0,0,KEYW,H);const KN=24,sc=DQ.sc;
    k.fillStyle='#101014';k.fillRect(KN,0,KEYW-KN,H);k.font='9.5px Inter,system-ui,sans-serif';k.textAlign='right';k.textBaseline='middle';
    for(let p=pTop;p>=pBot;p--){const y=py(p)-PRUL,m=p%12,blk=[1,3,6,8,10].includes(m);
      k.fillStyle=blk?'#1e1e22':'#d8d8de';k.fillRect(0,y,blk?KN*.62:KN,PR.rh-.5);if(blk){k.fillStyle='#d8d8de';k.fillRect(KN*.62,y,KN*.38,PR.rh-.5)}
      k.fillStyle='rgba(255,255,255,.04)';k.fillRect(KN,Math.round((y+PR.rh)*D)/D-DQ.hp,KEYW-KN,DQ.hp);
      if(m===0){k.fillStyle='rgba(255,255,255,.15)';k.fillRect(KN,Math.round((y+PR.rh)*D)/D-DQ.hp,KEYW-KN,DQ.hp)}
      if(PR.rh>=9||(m===0&&PR.rh>=7)){const deg=((p-PR.root)%12+12)%12;k.fillStyle=sc?(deg===0?'rgb('+DSP1.amb+')':sc.includes(deg)?'#ececf1':'#8b8b97'):(blk?'#8b8b97':'#ececf1');
        if(m===0&&!sc)k.font='600 9.5px Inter,system-ui,sans-serif';k.fillText(dsNN(p),KEYW-4,y+PR.rh/2+.5);if(m===0&&!sc)k.font='9.5px Inter,system-ui,sans-serif'}}
    k.fillStyle='rgba(0,0,0,.6)';k.fillRect(KEYW-1,0,1,H)}
  g.drawImage(cv,0,PRUL,KEYW,H)}
/* the note under the pointer, for its "outside the scale" label (a redraw only when it changes to or from such a note) */
prc.addEventListener('pointermove',e=>{if(!PR.open||pd)return;const o=prClip();if(!o||!dsAC3())return;const sc=SCALES[PR.scale];if(!sc){DSP1.hov=null;return}
  const{x,y,h}=prPt(e);const n=(x>KEYW&&y>PRUL&&y<h-VELH)?hitN(o.c,bAt(x),pAt(y)):null;if(n===DSP1.hov)return;const was=DSP1.hov;DSP1.hov=n;
  if((n&&!dsP1In(sc,n.p))||(was&&!dsP1In(sc,was.p)))dirty=true},{passive:true});
prc.addEventListener('pointerleave',()=>{if(DSP1.hov){const sc=SCALES[PR.scale],was=DSP1.hov;DSP1.hov=null;if(sc&&!dsP1In(sc,was.p))dirty=true}});
"""
rep("function askChoice(title,text,btns,icon){", BLOCK + "function askChoice(title,text,btns,icon){")

# drawing state for this picture
rep("const{g,w,h}=fit(prc);const gh=h-VELH,sc=SCALES[PR.scale];", "const{g,w,h}=fit(prc);const gh=h-VELH,sc=SCALES[PR.scale],DQ=dsP1Begin(t,c);")
# rows: scale rows lift, others sink; amber root line
rep("if(sc)col=sc.includes(deg)?(deg===0?'#262c3f':blk?'#1a1d27':'#1f2230'):(blk?'#0d0d10':'#111114');\n    g.fillStyle=col;g.fillRect(KEYW,y,w-KEYW,PR.rh);",
    "if(sc)col=sc.includes(deg)?(deg===0?'#262c3f':blk?'#1a1d27':'#1f2230'):(blk?'#0d0d10':'#111114');col=dsP1Row(DQ,deg,col);\n    g.fillStyle=col;g.fillRect(KEYW,y,w-KEYW,PR.rh);if(deg===0)dsP1Root(g,DQ,y,w);")
# notes: out-of-scale ring, then the labels after all notes
rep("g.fillText(nname(n.p),x+4,y+PR.rh/2+3.5)}}\n  if(pd&&pd.k==='rect')",
    "g.fillText(nname(n.p),x+4,y+PR.rh/2+3.5)}if(DQ.on)dsP1Out(g,DQ,n,x,y,nw)}\n  dsP1Labels(g,DQ,w);if(pd&&pd.k==='rect')")
# ruler: chord names after the bar numbers
rep("g.fillText(bar+1,x+4,14)}\n  g.save();g.beginPath();g.rect(0,PRUL,KEYW,gh-PRUL);g.clip();",
    "g.fillText(bar+1,x+4,14)}\n  dsP1Ruler(g,DQ,c,w,lb);g.save();g.beginPath();g.rect(0,PRUL,KEYW,gh-PRUL);g.clip();")
# keys: the cached narrow-key column with every row named (drum clips keep today's keys and pad names)
rep("  for(let p=pTop;p>=pBot;p--){const y=py(p),k=p%12,blk=[1,3,6,8,10].includes(k);g.fillStyle=blk?'#1e1e22':'#d8d8de';",
    "  if(DQ.on&&!DQ.drum)dsP1Keys(g,DQ,pTop,pBot,gh);else for(let p=pTop;p>=pBot;p--){const y=py(p),k=p%12,blk=[1,3,6,8,10].includes(k);g.fillStyle=blk?'#1e1e22':'#d8d8de';")
open(F, 'w', encoding='utf-8').write(s)
print('task DS-P1 applied')
