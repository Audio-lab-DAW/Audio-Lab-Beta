window.SY={sr:44100,
 buf(sec){return ctx.createBuffer(2,Math.ceil(sec*44100),44100)},
 add(b,ch,t0,dur,fn){const d=b.getChannelData(ch),sr=44100,i0=Math.floor(t0*sr),n=Math.floor(dur*sr);for(let i=0;i<n&&i0+i<d.length;i++)d[i0+i]+=fn(i/sr,i/n)},
 hz:p=>440*Math.pow(2,(p-69)/12),
 saw(f,t){let v=0;for(let h=1;h<=8;h++)v+=Math.sin(2*Math.PI*f*h*t)/h;return v*.5},
 env(u,a=.01,r=.08){const t=u;return Math.min(1,t/a)*Math.min(1,(1-t)/r)},
 note(b,p,t0,dur,amp,fn){const f=SY.hz(p),sr=44100;for(const ch of[0,1])SY.add(b,ch,t0,dur,(t,u)=>amp*(fn?fn(f,t):SY.saw(f,t))*Math.min(1,t/.01)*Math.min(1,(dur-t)/.05))},
 melody(){const b=SY.buf(4),P=[60,62,64,65,67,69,71,72];P.forEach((p,i)=>SY.note(b,p,i*.5,.45,.4));return{b,notes:P.map((p,i)=>({p,s:i,l:.9}))}},
 chords(){const b=SY.buf(8),C=[[57,60,64],[53,57,60],[60,64,67],[55,59,62]];C.forEach((c,i)=>c.forEach(p=>SY.note(b,p,i*2,1.95,.22)));return{b,C}},
 noise(){let s=12345;return()=>{s=(s*1664525+1013904223)>>>0;return s/2147483648-1}},
 drums(b,amp=1){const nz=SY.noise();for(let beat=0;beat<8;beat++){const t=beat*.5;
   if(beat%2===0)for(const ch of[0,1])SY.add(b,ch,t,.18,(tt,u)=>amp*.9*Math.sin(2*Math.PI*(45*tt+75*(1-Math.exp(-30*tt))/30))*Math.exp(-tt*14));
   else for(const ch of[0,1]){let y=0;SY.add(b,ch,t,.15,(tt,u)=>{y+=.3*(nz()-y);return amp*(1.6*y+.3*Math.sin(2*Math.PI*190*tt))*Math.exp(-tt*28)})}
   for(const k of[0,1]){const th=t+k*.25;for(const ch of[0,1]){let a=0,b1=0;SY.add(b,ch,th,.05,(tt,u)=>{const n=nz();const v=n-2*a+b1;b1=a;a=n;return amp*.12*v*Math.exp(-tt*90)})}}}},
 drumloop(){const b=SY.buf(4);SY.drums(b);return{b}},
 mix(){const b=SY.buf(4);SY.drums(b,.8);[33,33,36,38,33,33,36,31].forEach((p,i)=>SY.note(b,p,i*.5,.45,.35,(f,t)=>Math.sin(2*Math.PI*f*t)+.3*Math.sin(4*Math.PI*f*t)));
   const C=[[57,60,64],[53,57,60]];C.forEach((c,i)=>c.forEach(p=>SY.note(b,p,i*2,1.9,.12,(f,t)=>Math.exp(-t*1.2)*(Math.sin(2*Math.PI*f*t)+.5*Math.sin(4*Math.PI*f*t)+.25*Math.sin(6*Math.PI*f*t)))));return{b}},
 put(tname,b,start,name){const t=S.tracks.find(x=>x.name===tname);const id=addBuf(b);const c=mkClip({start,len:b.duration*S.bpm/60,name,buf:id,dur:b.duration,gain:0,fi:0,fo:0});t.clips.push(c);return c.id}};
