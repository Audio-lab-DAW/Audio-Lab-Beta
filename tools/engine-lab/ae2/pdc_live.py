"""How much delay compensation adds to a played note today (task AE2): the PDC target of the Fractals remake as built,
and the same project with one resonance suppressor (reson) on one track, the way a mix for clarity would add it."""
import json
from common import *
al=start();fractals(al)
print(al.run("""(async()=>{ensureCtx();await ctx.resume();const sr=ctx.sampleRate;const o={};const m=pdcMap(sr);o.fractals_ms=+(m.target/sr*1000).toFixed(2);
const lead=S.tracks.find(t=>t.name==='Lead');o.lead_delay_ms=+((m.get(lead.id)||0)/sr*1000).toFixed(2);
const b=S.tracks.find(t=>t.name==='Bass');const f=mkFx('reson');b.fx.push(f);changed(true);const m2=pdcMap(sr);o.with_reson_on_bass_ms=+(m2.target/sr*1000).toFixed(2);o.lead_delay_with_reson_ms=+((m2.get(lead.id)||0)/sr*1000).toFixed(2);
b.fx.pop();const L=mkFx('limit');L.p.look=10;b.fx.push(L);changed(true);const m3=pdcMap(sr);o.with_limit10_on_bass_ms=+(m3.target/sr*1000).toFixed(2);b.fx.pop();changed(true);
o.groups=S.tracks.filter(t=>t.kind==='group').map(g=>g.name+': '+g.fx.map(f=>f.type+' '+(fxLat(f,sr)/sr*1000).toFixed(1)+' ms').join(', '));return JSON.stringify(o)})()"""))
al.stop()
