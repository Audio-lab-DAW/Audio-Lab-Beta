from eng import *
import song,vox,time
al=start()
R=song.recipe();build(al,R);al.run("V.x=0;0");al.save('out/v5_novox.audiolab');print('novox',os.path.getsize('out/v5_novox.audiolab'),flush=True)
R=song.recipe();vox.load(al,R);build(al,R);al.run("V.x=0;0");al.save('out/Fractals_remake_v5.audiolab');print('project',os.path.getsize('out/Fractals_remake_v5.audiolab'),'tracks',len(R['tracks']),flush=True)
t=time.time();x,_=al.render(b0=0,b1=1152,tail=3);print('full render',x.shape,'in',round(time.time()-t),'s peak',pk(x),flush=True)
np.save('out/v5_raw.npy',x.astype(np.float32))
p=pk(x);y=x/p*.985 if p>.985 else x
sf.write('out/Fractals_remake_v5.flac',y.T,SR,subtype='PCM_16');print('DONE',flush=True)
al.stop()
