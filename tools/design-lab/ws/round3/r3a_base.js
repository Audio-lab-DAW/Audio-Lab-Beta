/* Task WS-0c (lane Q): round 3 drawings for the start screen and the splash. Nothing here changes SPLBG or R2 (WSR2).
   Same shape as SPLBG.FN: fn(c,w,h,t,P,d), drawn in a frame of w x h (the splash's 577 x 427) with the picture centred at (w/2, h*.345).
   P is a palette like SPLBG.PAL (L lines, T trails, O dots and labels, as "r,g,b"; the dipole also reads an optional A, the aurora's colour).
   d is a per-picture scratch object. Two optional hints in d, both set by the host:
     d.ext  half of the visible width in frame units (the start screen's band is much wider than the splash card); default w/2.
   Every picture is a pure function of t on its first call (a still frame at any t is complete), then advances by the time between calls.
   Global options: R3.cnt (0 fewer, 1 today, 2 more: the dipole's particle count), R3.dir (1 Jupiter, -1 Earth). */
var R3=(function(){var PI=Math.PI,TAU=PI*2,RG={};
 function K(w){return Math.max(1,Math.min(1.8,w/640))}
 function dot(c,x,y,r,col){c.fillStyle=col;c.beginPath();c.arc(x,y,r,0,TAU);c.fill()}
 function lab(c,w,tx,x,y,al,col){c.font='500 '+Math.max(8,Math.min(13,w/72)).toFixed(1)+'px ui-monospace,"SF Mono",Menlo,Consolas,monospace';if('letterSpacing'in c)c.letterSpacing='0.12em';c.textAlign=al;c.textBaseline='middle';c.fillStyle=col;c.fillText(tx,x,y);if('letterSpacing'in c)c.letterSpacing='0px'}
 function rgba(s,a){return 'rgba('+s+','+(+a).toFixed(3)+')'}
 function rgb(s){return RG[s]||(RG[s]=s.split(',').map(Number))}
 function mix(a,b,q){var A=rgb(a),B=rgb(b);q=q<0?0:q>1?1:q;return Math.round(A[0]+(B[0]-A[0])*q)+','+Math.round(A[1]+(B[1]-A[1])*q)+','+Math.round(A[2]+(B[2]-A[2])*q)}
 /* the lines fade out behind the name and the bar, as in the splash's dipole */
 function fadeName(c,w,h){c.save();c.globalCompositeOperation='destination-out';c.translate(w/2,h*.86);c.scale(w*.5,h*.35);var g=c.createRadialGradient(0,0,.78,0,0,1);g.addColorStop(0,'rgba(0,0,0,1)');g.addColorStop(1,'rgba(0,0,0,0)');c.fillStyle=g;c.fillRect(-1,-1,2,2);c.restore()}
 function hash(i){var x=Math.sin(i*127.1+311.7)*43758.5453;return x-Math.floor(x)}
 /* seconds since the last call; 0 on the first call and after a jump (so a picture rebuilds its state from t) */
 function step(d,t){var dt=d.lt==null?-1:t-d.lt;d.lt=t;return dt>=0&&dt<.25?dt:-1}
 function ease(x){x=x<0?0:x>1?1:x;return x*x*(3-2*x)}
 return{PAL:{},FN:{},BAND:{},NAME:{},cnt:1,dir:1,np:0,U:{K:K,dot:dot,lab:lab,rgba:rgba,rgb:rgb,mix:mix,fadeName:fadeName,hash:hash,step:step,ease:ease}}})();
