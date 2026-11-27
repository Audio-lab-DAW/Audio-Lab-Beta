"""Builds the self-contained pick page (pick-page.html) from page.src.html, geom.json and icons.js."""
import os
d = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(d, 'page.src.html')).read()
s = s.replace('/*GEOM*/', 'window.AL2_GEOM=' + open(os.path.join(d, 'geom.json')).read() + ';', 1)
s = s.replace('/*ICONS*/', open(os.path.join(d, 'icons.js')).read().replace('</script', '<\\/script'), 1)
open(os.path.join(d, 'pick-page.html'), 'w').write(s)
print(len(s))
