#!/usr/bin/env python3
"""Reads the output of `xcrun assetutil --info Assets.car` (a file name or stdin) and checks the Mac app icon in it (task IC1):
the layered AppIcon must be there for the default, the dark and the tintable appearance, and the tile of each must be the Ocean blue.
macOS 15 and older cannot read the layered entries (assetutil lists them as 'Unknown'); there the check only counts them, unless
--strict is given. The Mac icon proof job runs it with --strict on macOS 26."""
import json, sys, collections
args = [a for a in sys.argv[1:] if a != '--strict']; strict = '--strict' in sys.argv
rows = [r for r in json.load(open(args[0]) if args else sys.stdin) if isinstance(r, dict) and r.get('AssetType')]
print('--- Assets.car: %d entries: %s' % (len(rows), dict(collections.Counter(r['AssetType'] for r in rows))))
stacks = {r.get('Appearance') for r in rows if r.get('AssetType') == 'IconImageStack' and r.get('Name') == 'AppIcon'}
need = {'NSAppearanceNameAqua', 'NSAppearanceNameDarkAqua', 'ISAppearanceTintable'}
unknown = sum(1 for r in rows if r.get('AssetType') == 'Unknown')
if not stacks and unknown >= 6 and not strict:
    print('   this macOS cannot read the layered icon entries (%d listed as Unknown); they are checked on macOS 26 by the proof job' % unknown); sys.exit(0)
if not need <= stacks: sys.exit('Assets.car lacks the layered AppIcon for: ' + ', '.join(sorted(need - stacks)))
bad = []
for r in rows:
    if r.get('AssetType') == 'IconImageStack' and r.get('Name') == 'AppIcon':
        first = (r.get('Layers') or [{}])[0]; c = first.get('Color components') or []
        ok = first.get('AssetType') == 'Color' and len(c) == 4 and abs(c[0] - 0.078) < 0.01 and abs(c[1] - 0.314) < 0.01 and abs(c[2] - 0.659) < 0.01
        print('   tile of %-26s %s' % (r.get('Appearance'), ('blue ' + str([round(v, 3) for v in c])) if ok else 'NOT the blue: ' + str(first.get('Name'))))
        if not ok: bad.append(r.get('Appearance'))
if bad: sys.exit('the tile is not blue for: ' + ', '.join(map(str, bad)))
flat = sum(1 for r in rows if r.get('AssetType') in ('Icon Image', 'MultiSized Image'))
print('   flat pictures for macOS 15 and older inside Assets.car: %d (with any, those systems draw the icon from Assets.car too)' % flat)
