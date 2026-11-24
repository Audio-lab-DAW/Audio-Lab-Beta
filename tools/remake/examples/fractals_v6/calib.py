"""measure every track alone in its busiest clip and set its level to the target peak (dBFS before the master)"""
from eng import *
import song
TARGET={'Kick':-6,'Bass':-9.5,'Clap':-11,'Snare':-13,'Hat':-16,'Open hat':-15,'Percussion':-17,'Shaker':-22,'Toms':-12,'Crash':-13,'Snare roll':-11,
 'Lead':-11,'Lead low':-17,'Lead high':-19,'Hook left':-12,'Hook right':-12,'Arp':-14,'Acid':-13,'Pad':-17,'Riser':-14,'Reverse crash':-15,'Impact':-9,'Downlifter':-17,'Blip':-18,'Wind':-28}
al=start();R=song.recipe();build(al,R);g=dict(song.GAIN)
for t in R['tracks']:
    if not t.get('clips') or t['name'] not in TARGET:continue
    c=max(t['clips'],key=lambda c:len(c['notes'])*(1 if c['start']>=288 else .6));b0=c['start'];b1=b0+min(32,c['len'])
    x,_=al.render(b0=b0,b1=b1,only=t['name'],single=True,tail=1);p=20*np.log10(pk(x)+1e-9)
    g[t['name']]=round(g.get(t['name'],0)+TARGET[t['name']]-p,1);print('%-14s peak %6.1f -> gain %5.1f'%(t['name'],p,g[t['name']]),flush=True)
json.dump(g,open('gain.json','w'));al.stop()
