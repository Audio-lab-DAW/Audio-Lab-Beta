import sys, json, base64, time, numpy as np
from probe import AL
B0,B1=0,96
iso = sys.argv[1]!='noiso' if len(sys.argv)>1 else True
kinds = sys.argv[2].split(',') if len(sys.argv)>2 else ['quick','n4','n6']
al=AL('/home/claude/alp/index.html'); al.start(iso=iso)
P=al.page; P.set_default_timeout(3600_000)
print('iso',al.run("self.crossOriginIsolated"),flush=True)
al.run(f"""(async()=>{{ensureCtx();const b=await renderMix(44100,{B0},{B1},0,false,null,false);window.SGmix=b;
 window.SGget=(b,ch,off,n)=>{{const d=b.getChannelData(ch).subarray(off,off+n);let s='';const u=new Uint8Array(d.buffer,d.byteOffset,d.byteLength);for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));return btoa(s)}};
 return [b.length,b.sampleRate,b.numberOfChannels]}})()""")
info=al.run("[SGmix.length,SGmix.sampleRate,SGmix.numberOfChannels]");print('mix',info,flush=True)
def pull(expr,ch):
    n=al.run(f"({expr}).length");out=np.zeros(n,np.float32);C=1<<20
    for off in range(0,n,C):
        k=min(C,n-off);b=P.evaluate("a=>AudioLab.run(a)",f"SGget({expr},{ch},{off},{k})");out[off:off+k]=np.frombuffer(base64.b64decode(b),np.float32)
    return out
res={'B0':B0,'B1':B1,'bpm':al.run('S.bpm'),'len':info[0],'sr':info[1],'iso':iso}
mix=np.stack([pull('SGmix',0),pull('SGmix',1)]);np.save('out/mix.npy',mix)
# STFT cost in JS for one 7.8 s chunk, 4 stems (full 2048/512) and 'display only' (24 columns)
res['stft']=al.run("""(()=>{STF.init();const N=2048,H=512,re=new Float32Array(N),im=new Float32Array(N),L=SGmix.getChannelData(0);let t0=performance.now();
 for(let st=0;st<4;st++)for(let p=0;p+N<343980;p+=H){for(let i=0;i<N;i++){re[i]=L[p+i]*STF.win[i];im[i]=0}STF.fft(re,im,false)}const full=performance.now()-t0;
 t0=performance.now();for(let st=0;st<6;st++)for(let c=0;c<64;c++){const p=c*4000;for(let i=0;i<N;i++){re[i]=L[p+i]*STF.win[i];im[i]=0}STF.fft(re,im,false)}const disp=performance.now()-t0;return{full4:full,cols64x6:disp}})()""")
print('stft',res['stft'],flush=True)
for k in kinds:
    t0=time.time()
    if k=='quick':
        al.run("""(async()=>{window.SGt=[];const t0=performance.now();const o=await stemSplit(SGmix,p=>SGt.push([performance.now()-t0,p]),{});window.SGo=o;window.SGtot=performance.now()-t0;return 1})()""")
        names=['Drums','Bass','Vocals','Other']
    else:
        al.run(f"""(async()=>{{window.SGt=[];const t0=performance.now();const o=await neuSeparate(SGmix,'{k}',NEUM['{k}'].stems.map(()=>true),(ph,p)=>SGt.push([performance.now()-t0,ph,p]));window.SGo=o;window.SGtot=performance.now()-t0;return 1}})()""")
        names=al.run(f"NEUM['{k}'].stems")
    tl=al.run("SGt");tot=al.run("SGtot")
    print(k,'total ms',round(tot),'events',len(tl),tl[:3],tl[-3:],flush=True)
    res[k]={'names':names,'tl':tl,'tot':tot}
    st=np.stack([np.stack([pull(f'SGo[{i}]',0),pull(f'SGo[{i}]',1)]) for i in range(len(names))]);np.save(f'out/stems_{k}.npy',st)
    json.dump(res,open(f'out/timing_{"iso" if iso else "noiso"}.json','w'),indent=1)
print('errors',al.errors[:3],al.logs[-5:]);al.stop()
