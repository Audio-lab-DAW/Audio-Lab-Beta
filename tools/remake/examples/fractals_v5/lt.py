from eng import *
import song
al=start();R=song.recipe();build(al,R)
print(al.run("""(async()=>{ensureCtx();await ctx.resume();await new Promise(r=>setTimeout(r,4000));const idle=[CPU.aud,CPU.pk,CPU.k];pos=%f;start();await new Promise(r=>setTimeout(r,9000));const pl=[CPU.aud,CPU.pk,CPU.pkMax];stop();UI.vcap=4;pos=%f;start();await new Promise(r=>setTimeout(r,4000));stop();UI.vcap=32;
return JSON.stringify({idle,playing:pl,over:CPU.over,stolenWithCap4:CPU.stolen,meter:!!LM.w,sab:!!LM.sab})})()"""%(song.bar(81),song.bar(81))))
al.stop()
