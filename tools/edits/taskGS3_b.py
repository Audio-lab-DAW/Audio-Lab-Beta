# part B of taskGS3.py (run inside it: S, rep, cut, line_with are defined there): hooks into drawArr, the master meter and the Settings loop
rep("ch=hc.clientHeight||h,nT=S.tracks.length,bot=(AY-TY)-V.y+(()=>{const ab=hdrin.querySelector('.addrow button'),ar=ab&&ab.closest('.addrow');return ab&&ar?ar.offsetTop+ab.offsetTop+ab.offsetHeight/2:TOTH+34})()",
    "ch=ascHcH(hc,h),nT=S.tracks.length,bot=(AY-TY)-V.y+ascAddY()")
# the master meter: draw only when what it shows changed
rep("  g.fillStyle='#050608';g.fillRect(0,0,w,h);const sx=d=>clamp((d+60)/66,0,1)*w,bh=(h-5)/2;\n  if(!(w>2))return;\n",
    "  const sx=d=>clamp((d+60)/66,0,1)*w,bh=(h-5)/2;\n  if(!(w>2))return;const mk=mc.width+'|'+mc.height+'|'+Math.round(sx(MT2.l)*4)+'|'+Math.round(sx(MT2.r)*4)+'|'+Math.round(sx(MT2.hl)*4)+'|'+Math.round(sx(MT2.hr)*4),same=mk===meters.k;meters.k=mk;/* v0.228: nothing new to show, nothing drawn (it drew 120 times a second, also in silence) */\n  if(!same){g.fillStyle='#050608';g.fillRect(0,0,w,h);\n")
rep("g.fillStyle='rgba(255,77,77,.8)';g.fillRect(sx(0),0,1,h);\n  {const s1=", "g.fillStyle='rgba(255,77,77,.8)';g.fillRect(sx(0),0,1,h)}\n  {const s1=")
# the Settings logo: at most 60 pictures a second
rep("if(now-SLP2.l>=(UI.lite?31:6.2)){", "if(now-SLP2.l>=(UI.lite?31:16.2)){")
