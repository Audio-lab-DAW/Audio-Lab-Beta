/* ===== v0.2xx (task SC-B, lane G): the About background as a random set, the user's pick Y1 (docs/science-look-round-2.md, section Y) =====
   Each time About opens: the Earth with its belts 3 times in 5 (task AB1's two pictures, E2 "corner" and E7 "sheet", an even split of those 3),
   the orbit corner (B2) 1 in 5, the field arcs (B3) 1 in 5. The two new pictures are drawn with the science module (SCI.D.corner, SCI.D.field)
   on the same dark ground as the Earth, under the same veil that keeps the text column readable; AB1 keeps its window, its timing (at most
   30 pictures a second, only while open, still at the Light level, with reduce motion and when Motion is not Ambient) and its atom.
   No new science drawings in Light mode (the user's W14 off) and none with Settings > Science drawings off: then About shows the Earth only,
   as before. Test hook as AB1's: AB1.force('orbit' | 'arcs' | 'corner' | 'sheet'), or localStorage 'audiolab-about-test'. */
const SCI_ABOUT={earth:.6,orbit:.2,arcs:.2};
/* which About picture: Y1, or the Earth only when the science drawings are off or in Light mode */
function sciAboutPick(){const r=Math.random(),sci=typeof SCI==='object'&&SCI.on()&&!document.body.classList.contains('lite');
  if(sci&&r>=SCI_ABOUT.earth)return r<SCI_ABOUT.earth+SCI_ABOUT.orbit?'orbit':'arcs';
  return(sci?r/SCI_ABOUT.earth:r)<.5?'corner':'sheet'}
/* the two science pictures, drawn where AB1 draws the Earth: the same ground, the drawing, then AB1's veil over the text */
function sciAboutDraw(c,w,h,t,kind,M){const gr=c.createRadialGradient(w/2,h*.417,0,w/2,h*.417,560*Math.max(w/780,h/720));gr.addColorStop(0,'#0b1322');gr.addColorStop(.6,'#060910');gr.addColorStop(1,'#04060a');c.fillStyle=gr;c.fillRect(0,0,w,h);
  /* strength above 1: the lines as bright as the Earth's (line alpha is capped at 1; these drawings carry no labels) */
  const D=SCI.D,s=Math.min(w/780,h/720);
  /* B2: tick rings from just outside the lower right corner, reaching across the window */
  if(kind==='orbit')D.corner(c,w+8*s,h+12*s,Math.max(w,h)*.9,2.2,t);
  /* B3: dipole field arcs rising from below the window's lower edge */
  else D.field(c,w/2,h*1.09,w*.62,0,t,1.9,{a:.2});
  if(M&&M.veil){c.imageSmoothingEnabled=true;c.drawImage(M.veil,0,0,w,h)}}
