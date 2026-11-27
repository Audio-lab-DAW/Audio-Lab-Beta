#!/usr/bin/env python3
"""Task IC4: the app icon picker block of index.html (prefix apic, the block 'App icon picker (v0.203, task V)').
J3 "Dipole Field" is the default; a choice of Ocean Yellow stored in the browser before IC4 meant the default, so it now gives J3.
Unique, asserted anchors; re-running on a fresh file is safe (skips when applied)."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(p, encoding='utf8').read()
if "APIC_OLD='ocean-yellow'" in s: print('already applied'); sys.exit(0)
def rep(old, new):
    global s
    n = s.count(old); assert n == 1, (n, old[:90]); s = s.replace(old, new)
rep("/* App icon picker (v0.203, task V): Ocean Yellow is the default.", "/* App icon picker (v0.203, task V): J3 Dipole Field is the default since task IC4 (Ocean Yellow before; a stored Ocean Yellow without the\n   version mark '-v' was the old default and now means the default).")
rep("const APIC_WEB='desktop/icon-assets/picker/',APIC_KEY='audiolab-app-icon',APIC_DEF='ocean-yellow';",
    "const APIC_WEB='desktop/icon-assets/picker/',APIC_KEY='audiolab-app-icon',APIC_DEF='dipole-field',APIC_OLD='ocean-yellow';\nfunction apicStored(){try{const id=localStorage.getItem(APIC_KEY);return id===APIC_OLD&&!localStorage.getItem(APIC_KEY+'-v')?null:id}catch(e){return null}}")
rep("const r=await fetch(APIC_WEB+'icons.json');if(!r.ok)throw new Error('HTTP '+r.status);const j=await r.json();let cur=null;try{cur=localStorage.getItem(APIC_KEY)}catch(e){}",
    "const r=await fetch(APIC_WEB+'icons.json');if(!r.ok)throw new Error('HTTP '+r.status);const j=await r.json();let cur=apicStored();")
rep("else{D.cur=id;try{localStorage.setItem(APIC_KEY,id)}catch(e){}apicFav(id,D.def)}",
    "else{D.cur=id;try{localStorage.setItem(APIC_KEY,id);localStorage.setItem(APIC_KEY+'-v','2')}catch(e){}apicFav(id,D.def)}")
rep(" if(!apicHost()){try{const id=localStorage.getItem(APIC_KEY);if(id&&id!==APIC_DEF)apicFav(id,APIC_DEF)}catch(e){}}",
    " if(!apicHost()){const id=apicStored();if(id&&id!==APIC_DEF)apicFav(id,APIC_DEF)}")
open(p, 'w', encoding='utf8').write(s); print('index.html: IC4 picker block applied')
