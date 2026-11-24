from eng import *
import song
al=start();R=song.recipe();build(al,R)
print(al.run("""(async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));ensureCtx();await ctx.resume();await w(3000);const o={ver:VERSION};
pos=%f;start();await w(8000);o.play={la:laSec(),late:CPU.late,maxGap:+LA.max.toFixed(3),drop:URS.total,aud:CPU.aud};
/* a pause of 0.1 s: inside the look-ahead */let t=performance.now();while(performance.now()-t<100){}await w(1500);o.stall100={la:laSec(),late:CPU.late};
/* a pause of 0.3 s: longer than the look-ahead */t=performance.now();while(performance.now()-t<300){}await w(1500);o.stall300={la:laSec(),late:CPU.late,abuf:UI.abuf};
t=performance.now();while(performance.now()-t<300){}await w(1500);o.stall300again={la:laSec(),late:CPU.late,abuf:UI.abuf};stop();
return JSON.stringify(o)})()"""%song.bar(81)))
al.stop()
