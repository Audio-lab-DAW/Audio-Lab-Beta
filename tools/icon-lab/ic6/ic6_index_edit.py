#!/usr/bin/env python3
"""Task IC6: the app icon picker block of index.html (prefix apic; new names ic*). In the browser the tab icon of a picked icon is
its own small picture drawn for 32 px (icons.json 'small', S1 way since IC6) instead of its 128 px thumbnail shrunk; the
apple-touch-icon keeps the thumbnail. Icons without small pictures (the older ones) keep the thumbnail.
Unique, asserted anchors; re-running on a fresh file is safe (skips when applied)."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
s = open(p, encoding='utf8').read()
if 'function icFavSrc(' in s: print('already applied'); sys.exit(0)
assert 'icFavSrc' not in s and 'icFavList' not in s
def rep(old, new):
    global s
    n = s.count(old); assert n == 1, (n, old[:90]); s = s.replace(old, new)
rep("l.setAttribute('href',!id||id===(def||APIC_DEF)?l.dataset.apic0:APIC_WEB+'thumb/'+id+'.png')}}catch(e){}}",
    "l.setAttribute('href',!id||id===(def||APIC_DEF)?l.dataset.apic0:icFavSrc(id,l))}}catch(e){}}\n"
    "/* task IC6: the tab icon of a picked icon is its own 32 px small picture (icons.json 'small'); the list is read once when the\n"
    "   picker has not loaded it yet; apple-touch-icon and icons without small pictures keep the 128 px thumbnail */\n"
    "let icFavList=null;\n"
    "function icFavSrc(id,l){const big=APIC_WEB+'thumb/'+id+'.png';if(l&&l.rel==='apple-touch-icon')return big;\n"
    "  const gs=(apicData&&apicData.groups)||icFavList;\n"
    "  if(!gs){if(icFavList===null&&!apicHost()){icFavList=0;fetch(APIC_WEB+'icons.json').then(r=>r.ok?r.json():null).then(j=>{if(j&&j.groups){icFavList=j.groups;if(apicStored()===id)apicFav(id,j.default)}}).catch(()=>{})}return big}\n"
    "  const ic=gs.flatMap(g=>g.icons||[]).find(i=>i.id===id),sm=ic&&ic.small&&ic.small['32'];return sm?APIC_WEB+sm:big}")
open(p, 'w', encoding='utf8').write(s); print('index.html: IC6 picker favicon applied')
