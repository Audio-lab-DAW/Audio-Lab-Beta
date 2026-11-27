#!/usr/bin/env python3
"""Inline today's screenshots into learn.html so the pick page is one file: python3 tools/design-lab/ux3/build.py [out.html]"""
import sys, os, base64, re
D = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(D, 'learn-built.html')
s = open(os.path.join(D, 'learn.html'), encoding='utf-8').read()
def inl(m):
    f = os.path.join(D, m.group(1))
    return 'src="data:image/jpeg;base64,' + base64.b64encode(open(f, 'rb').read()).decode() + '"'
s = re.sub(r'src="(today/[^"]+\.jpg)"', inl, s)
open(OUT, 'w', encoding='utf-8').write(s); print(OUT, len(s))
