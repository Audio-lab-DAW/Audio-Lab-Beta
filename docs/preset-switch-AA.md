# Preset switch on every instrument, before (v0.202) and after (v0.211), task AA

Made with tools/engine-tests/preset_switch2.py (method in its header and in the v0.211 entry of docs/backlog-log.md). Headless Chromium, 2 cores. 'silent ref' rows: the instrument's sound is over before the switch (drum hits, a pluck), nothing to compare.

## Before (v0.202; in the 'key held' case the extra level after the switch is mostly the test note of the preset change, removed in v0.211)
```
== one long note, playing ==
inst     | switch                     | new sound | glitch | over / dip (dB) | handler | ref level
saw      | def > bright               |     27 ms |  -1.5  |  +4.6 /  -5.9    |  13.9 ms |  -27.2 dB
square   | def > flute                |     37 ms |   1.9  |  +3.3 /  -0.1    |  19.2 ms |  -22.2 dB
sub      | def > long                 |     37 ms |  -1.1  |  +0.4 /  -0.4    |  13.4 ms |  -15.0 dB
bass     | def > dark                 |     87 ms |   1.7  |  +3.5 / -102.4    |  79.7 ms |  -18.7 dB
reese    | def > slow                 |    247 ms |  -2.1  |  +5.1 / -96.6    |  42.2 ms |  -24.1 dB
pad      | def > swell                |    182 ms |  -3.2  |  +5.4 / -89.7    |  53.9 ms |  -29.2 dB
strings  | def > slow                 |     42 ms |  -2.0  |  +1.7 /  -1.7    |  25.2 ms |  -28.7 dB
pluck    | def > soft                 |     32 ms |   0.0  |  +0.0 /  +0.0    |  20.3 ms | -140.0 dB  silent ref
keys     | def > bright               |     37 ms |   7.2  |  +3.6 /  -4.5    |  21.5 ms |  -31.7 dB
drums    | def > deephouse            |     12 ms |   0.0  |  +0.0 /  +0.0    |  20.2 ms | -180.0 dB  silent ref
acid     | psy > squirt               |     37 ms |   0.2  |  +0.1 /  -0.1    |  19.8 ms |  -22.8 dB
sfx      | riser > psyriser           |     17 ms |  -2.2  |  +4.2 /  -3.1    |  27.8 ms |  -55.9 dB
plant    | lush > sspad               |    207 ms |   3.5  | +13.1 /  -7.2    |  16.1 ms |  -24.0 dB
perc     | marimba > xylo             |     12 ms |   0.0  |  +0.0 /  +0.0    |  17.6 ms | -180.0 dB  silent ref
sampler  | choir > choirlead          |     22 ms |  -2.2  |  +0.2 /  -0.3    |  14.1 ms |  -13.5 dB
grid     | basic > init               |     32 ms |   4.1  |  +0.2 /  -0.2    |  45.3 ms |  -25.4 dB
kick     | psyzap > psyroll           |     12 ms |   0.0  |  +0.0 /  +0.0    |  16.5 ms | -180.0 dB  silent ref
wtab     | init > supersaw            |    307 ms |  -3.0  | +10.8 / -11.0    |  26.9 ms |  -26.5 dB
zsnare   | t909 > f808                |     12 ms |   0.0  |  +0.0 /  +0.0    |  19.7 ms | -180.0 dB  silent ref
zclap    | c909 > wide                |     12 ms |   0.0  |  +0.0 /  +0.0    |  13.7 ms | -180.0 dB  silent ref
zhat     | c909 > o909                |     12 ms |   0.0  |  +0.0 /  +0.0    |  13.8 ms | -180.0 dB  silent ref
ztom     | t808 > tmid                |     12 ms |   0.0  |  +0.0 /  +0.0    |  19.9 ms | -180.0 dB  silent ref
growl    | yoi > wub                  |     17 ms |  -1.1  |  +1.1 /  -1.4    |  18.5 ms |  -14.7 dB
emit     | spin > duo                 |    312 ms |  14.0  |  +5.7 /  -0.8    |  11.3 ms |  -18.9 dB
vgrain   | orbit > swarm              |    632 ms |  -3.2  |  -0.9 / -23.3    |  12.9 ms |  -12.4 dB
vfm      | glass > church             |     37 ms | -20.0  |  +5.7 /  -4.0    |  40.0 ms |  -19.0 dB
orb      | sun > ring                 |     32 ms |   8.1  | +11.2 /  -0.3    |  13.3 ms |  -19.5 dB
sbass    | pure > warm                |     never |  -2.0  |  +1.2 /  -1.4    |  20.9 ms |  -11.4 dB
bball    | marimba > pingp            |    892 ms |  -4.6  | +42.4 / -96.6    |  14.4 ms |  -32.5 dB
psyb     | fo145 > fo150              |     12 ms |   0.0  |  +0.0 /  +0.0    |  13.5 ms | -180.0 dB  silent ref
crk      | draw > drawab              |     never |  -0.1  |  +6.2 / -10.4    |  12.1 ms |  -24.4 dB
venom    | init > l_super             |    332 ms |   1.6  |  +1.0 /  -5.0    |  31.2 ms |  -20.4 dB
== sixteenth notes, playing ==
inst     | switch                     | new sound | glitch | over / dip (dB) | handler | ref level
saw      | def > bright               |    102 ms |  -4.2  |  +4.0 /  -1.9    |  25.5 ms |  -24.1 dB
square   | def > flute                |    207 ms |   2.4  |  +2.0 /  -2.7    |  18.6 ms |  -20.9 dB
sub      | def > long                 |    272 ms |  -5.2  |  +1.0 /  -7.4    |  13.8 ms |  -13.6 dB
bass     | def > dark                 |     72 ms |   0.2  |  +0.1 /  -0.4    |  12.6 ms |  -15.3 dB
reese    | def > slow                 |    142 ms |  -2.9  |  +0.1 /  -7.0    |  11.6 ms |  -21.6 dB
pad      | def > swell                |    672 ms |   4.3  | -15.5 / -47.2    |  12.0 ms |  -16.9 dB
strings  | def > slow                 |    362 ms |  -2.9  |  -9.0 / -40.6    |  12.9 ms |  -22.5 dB
pluck    | def > soft                 |     32 ms |  -5.2  |  +1.8 /  -0.1    |  15.9 ms |  -25.6 dB
keys     | def > bright               |    257 ms |   0.6  |  +4.4 /  -0.3    |  12.7 ms |  -19.7 dB
drums    | def > deephouse            |     27 ms |   1.2  |  +0.0 /  -0.0    |  29.3 ms |  -11.9 dB
acid     | psy > squirt               |     never |  -5.7  | +40.1 / -96.1    |  23.2 ms |  -24.1 dB
sfx      | riser > psyriser           |     92 ms | -17.0  |  +1.9 / -91.9    |  18.4 ms |  -29.8 dB
plant    | lush > sspad               |    212 ms |   1.5  |  +1.1 / -10.4    |  18.8 ms |  -27.7 dB
perc     | marimba > xylo             |     27 ms |  -7.5  |  +1.7 /  -0.3    |  14.0 ms |  -30.7 dB
sampler  | choir > choirlead          |    132 ms |  -4.1  |  +0.9 /  -5.2    |  16.8 ms |  -12.6 dB
grid     | basic > init               |     27 ms |   5.9  |  +4.6 /  +0.3    |  18.3 ms |  -24.8 dB
kick     | psyzap > psyroll           |     27 ms |   4.5  |  +0.0 /  -1.4    |  15.9 ms |   -9.2 dB
wtab     | init > supersaw            |     22 ms |  -3.4  |  +0.4 /  -1.6    |  22.8 ms |  -22.7 dB
zsnare   | t909 > f808                |     27 ms |   1.5  |  +2.7 /  -1.0    |  27.5 ms |  -15.2 dB
zclap    | c909 > wide                |    257 ms |  -5.1  |  +0.1 /  -5.8    |  17.6 ms |  -19.1 dB
zhat     | c909 > o909                |     82 ms |  -4.4  |  -0.3 /  -2.7    |  30.0 ms |  -22.7 dB
ztom     | t808 > tmid                |    117 ms |  -0.3  |  +4.0 /  -2.7    |  19.1 ms |  -11.9 dB
growl    | yoi > wub                  |     17 ms |   1.1  |  +0.1 /  -0.0    |  16.9 ms |  -15.5 dB
emit     | spin > duo                 |    667 ms |   6.4  |  +0.3 / -19.4    |  13.1 ms |  -13.2 dB
vgrain   | orbit > swarm              |    357 ms |  -2.9  |  -0.6 / -19.6    |  16.5 ms |  -11.4 dB
vfm      | glass > church             |     27 ms |   7.9  |  +6.0 /  +1.3    |  16.0 ms |  -13.7 dB
orb      | sun > ring                 |     32 ms |  12.3  |  +1.7 /  -8.6    |  13.3 ms |  -15.4 dB
sbass    | pure > warm                |    157 ms |  -3.1  |  +1.3 /  -2.3    |  21.3 ms |  -11.9 dB
bball    | marimba > pingp            |    787 ms |  12.0  |  +3.4 / -102.3    |  17.4 ms |  -23.3 dB
psyb     | fo145 > fo150              |     47 ms |   3.0  |  +0.0 / -51.8    |  19.8 ms |  -20.7 dB
crk      | draw > drawab              |    137 ms |  -0.5  |  +1.3 /  -2.3    |  11.5 ms |  -24.0 dB
venom    | init > l_super             |    622 ms |  -3.1  |  +4.2 /  -8.6    | 366.8 ms |  -19.1 dB
== a key held, stopped ==
inst     | switch                     | new sound | glitch | over / dip (dB) | handler | ref level
saw      | def > bright               |    297 ms |   5.0  | +12.5 /  -1.7    |  15.5 ms |  -27.3 dB
square   | def > flute                |    347 ms |   2.7  | +13.2 /  +7.0    |  12.6 ms |  -24.1 dB
sub      | def > long                 |    717 ms | -10.4  |  +4.3 /  -0.2    |  18.2 ms |  -15.0 dB
bass     | def > dark                 |    457 ms |   2.1  |  +6.9 /  +2.2    |  21.4 ms |  -18.2 dB
reese    | def > slow                 |    502 ms |  -2.1  |  +6.8 /  +0.4    |  12.6 ms |  -23.6 dB
pad      | def > swell                |    227 ms |  -2.7  |  -0.6 / -19.6    |  17.4 ms |  -29.4 dB
strings  | def > slow                 |    577 ms |  -8.6  |  +3.2 / -17.8    |  15.6 ms |  -28.9 dB
pluck    | def > soft                 |    772 ms |   0.0  | +94.6 / +83.9    |  11.2 ms | -118.4 dB  silent ref
keys     | def > bright               |    572 ms |  12.9  | +47.1 / +14.0    |  16.0 ms |  -36.5 dB
drums    | def > deephouse            |    472 ms |   0.0  | +109.5 / +73.0    |  23.4 ms | -180.0 dB  silent ref
acid     | psy > squirt               |    317 ms |   5.9  |  +5.2 /  +0.9    |  14.1 ms |  -22.8 dB
sfx      | riser > psyriser           |    322 ms | -21.6  | +21.4 /  +1.7    |  15.8 ms |  -41.7 dB
plant    | lush > sspad               |    142 ms |  -8.2  |  +2.3 /  -4.3    |  25.0 ms |  -25.9 dB
perc     | marimba > xylo             |    637 ms |   0.0  | +98.8 / +63.6    |  16.2 ms | -180.0 dB  silent ref
sampler  | choir > choirlead          |     17 ms |  -2.7  |  +3.6 /  -0.2    | 211.2 ms |  -13.4 dB
grid     | basic > init               |    177 ms |   3.7  |  +3.3 /  +1.5    |  17.8 ms |  -22.4 dB
kick     | psyzap > psyroll           |    262 ms |   0.0  | +115.0 / +50.3    |  28.8 ms | -180.0 dB  silent ref
wtab     | init > supersaw            |     72 ms |  -8.6  |  +9.1 /  -7.0    |  38.9 ms |  -26.4 dB
zsnare   | t909 > f808                |    497 ms |   0.0  | +111.7 / +94.5    |  16.4 ms | -180.0 dB  silent ref
zclap    | c909 > wide                |    652 ms |   0.0  | +106.7 / +95.1    |  19.5 ms | -180.0 dB  silent ref
zhat     | c909 > o909                |    797 ms |   0.0  | +101.7 / +91.6    |  17.6 ms | -180.0 dB  silent ref
ztom     | t808 > tmid                |    582 ms |   0.0  | +111.8 / +99.9    |  20.0 ms | -180.0 dB  silent ref
growl    | yoi > wub                  |    322 ms |   6.2  |  +5.4 /  -0.5    |  19.9 ms |  -14.7 dB
emit     | spin > duo                 |     37 ms |  10.8  |  +7.9 /  -5.6    |  16.0 ms |  -17.0 dB
vgrain   | orbit > swarm              |     12 ms |   9.1  |  +7.1 / -19.4    |  14.3 ms |  -13.9 dB
vfm      | glass > church             |    512 ms |  -9.2  | +12.1 / -99.3    |  15.0 ms |  -20.3 dB
orb      | sun > ring                 |     52 ms |   5.2  | +13.2 / -104.3    |  43.8 ms |  -17.3 dB
sbass    | pure > warm                |     12 ms |  11.6  |  +1.3 /  -1.2    |  17.5 ms |  -11.4 dB
bball    | marimba > pingp            |   1102 ms |  -3.0  | +16.9 / -98.9    |  19.5 ms |  -30.7 dB
psyb     | fo145 > fo150              |     87 ms |   0.0  | +98.4 / +46.3    |  28.7 ms | -180.0 dB  silent ref
crk      | draw > drawab              |     47 ms |  15.2  |  +7.3 / -101.5    |  16.4 ms |  -24.4 dB
venom    | init > l_super             |    302 ms |  -7.7  |  +7.4 / -102.0    |  37.1 ms |  -19.9 dB
```

## After (v0.211)
```
== one long note, playing ==
inst     | switch                     | new sound | glitch | over / dip (dB) | handler | ref level
saw      | def > bright               |     32 ms |  -4.2  |  +0.9 /  -0.9    |  22.3 ms |  -26.9 dB
square   | def > flute                |     37 ms |   0.7  |  +0.3 /  -0.5    |  20.6 ms |  -21.8 dB
sub      | def > long                 |     37 ms |  -1.1  |  +0.5 /  -0.5    |  19.4 ms |  -15.0 dB
bass     | def > dark                 |     22 ms |   1.6  |  +0.0 /  -0.0    |  17.9 ms |  -18.8 dB
reese    | def > slow                 |     17 ms |   0.4  |  +0.0 /  -0.0    |  11.7 ms |  -24.2 dB
pad      | def > swell                |     27 ms |   0.7  |  +0.0 /  -0.0    |  13.6 ms |  -28.8 dB
strings  | def > slow                 |     27 ms |   0.2  |  +0.0 /  -0.0    |  12.8 ms |  -28.6 dB
pluck    | def > soft                 |     32 ms |   0.0  |  +0.0 /  +0.0    |  15.5 ms | -137.9 dB  silent ref
keys     | def > bright               |     32 ms |   1.9  |  +0.1 /  -0.4    |  18.0 ms |  -31.9 dB
drums    | def > deephouse            |     12 ms |   0.0  |  +0.0 /  +0.0    |  33.5 ms | -180.0 dB  silent ref
acid     | psy > squirt               |     32 ms |   0.4  |  +0.1 /  -0.1    |  13.5 ms |  -22.8 dB
sfx      | riser > psyriser           |     17 ms |  -2.2  |  +3.2 /  -3.0    |  15.4 ms |  -55.8 dB
plant    | lush > sspad               |     37 ms |  -3.8  |  +1.0 /  -0.8    |  15.9 ms |  -25.4 dB
perc     | marimba > xylo             |     12 ms |   0.0  |  +0.0 /  +0.0    |  12.7 ms | -180.0 dB  silent ref
sampler  | choir > choirlead          |     22 ms |  -1.9  |  +0.4 /  -0.8    |  18.8 ms |  -15.3 dB
grid     | basic > init               |     27 ms |   2.8  |  +0.1 /  -0.1    |  10.8 ms |  -25.4 dB
kick     | psyzap > psyroll           |     12 ms |   0.0  |  +0.0 /  +0.0    |  25.3 ms | -180.0 dB  silent ref
wtab     | init > supersaw            |     37 ms |  -4.5  |  +1.1 /  -1.4    |  19.2 ms |  -25.9 dB
zsnare   | t909 > f808                |     12 ms |   0.0  |  +0.0 /  +0.0    |  18.8 ms | -180.0 dB  silent ref
zclap    | c909 > wide                |     12 ms |   0.0  |  +0.0 /  +0.0    |  18.7 ms | -180.0 dB  silent ref
zhat     | c909 > o909                |     12 ms |   0.0  |  +0.0 /  +0.0    |  16.7 ms | -180.0 dB  silent ref
ztom     | t808 > tmid                |     12 ms |   0.0  |  +0.0 /  +0.0    |  19.8 ms | -180.0 dB  silent ref
growl    | yoi > wub                  |     17 ms |   1.5  |  +0.4 /  -0.5    |  16.4 ms |  -14.7 dB
emit     | spin > duo                 |     17 ms |  15.2  |  +0.7 / -11.3    |  19.0 ms |  -28.0 dB
vgrain   | orbit > swarm              |    397 ms |  -4.5  |  +6.6 / -20.4    |  18.6 ms |  -15.8 dB
vfm      | glass > church             |    697 ms |  -5.9  |  +8.6 /  +4.0    |  13.4 ms |  -20.0 dB
orb      | sun > ring                 |     27 ms |  10.9  |  +9.6 /  -6.0    |  16.8 ms |  -20.0 dB
sbass    | pure > warm                |     never |  -1.7  |  +1.4 /  -1.4    |  12.5 ms |  -11.4 dB
bball    | marimba > pingp            |    882 ms |   1.0  | +31.7 / -95.5    |  13.2 ms |  -33.6 dB
psyb     | fo145 > fo150              |     12 ms |   0.0  |  +0.0 /  +0.0    |  13.2 ms | -180.0 dB  silent ref
crk      | draw > drawab              |     never |  -2.0  |  +1.6 /  -8.6    |  30.8 ms |  -24.4 dB
venom    | init > l_super             |    277 ms |   1.5  |  +2.2 /  -6.6    |  38.2 ms |  -20.0 dB
== sixteenth notes, playing ==
inst     | switch                     | new sound | glitch | over / dip (dB) | handler | ref level
saw      | def > bright               |     37 ms |  -1.0  |  +0.7 /  -0.5    |  18.4 ms |  -24.1 dB
square   | def > flute                |     32 ms |  -1.0  |  +3.4 /  -3.2    |  15.0 ms |  -20.8 dB
sub      | def > long                 |    152 ms |  -3.7  |  +0.8 /  -3.3    |  14.1 ms |  -13.6 dB
bass     | def > dark                 |     32 ms |  -8.0  |  +1.2 /  -1.2    |  19.5 ms |  -15.3 dB
reese    | def > slow                 |    127 ms |  -1.8  |  -0.5 / -11.3    |  12.1 ms |  -21.6 dB
pad      | def > swell                |    577 ms |   1.6  | -18.7 / -47.2    |  18.8 ms |  -17.3 dB
strings  | def > slow                 |    447 ms |  -1.3  | -11.0 / -38.1    |  22.5 ms |  -22.2 dB
pluck    | def > soft                 |    227 ms |   1.3  |  +2.8 /  -0.5    |  19.8 ms |  -25.7 dB
keys     | def > bright               |     27 ms |   0.5  |  +1.7 /  -0.7    |  14.7 ms |  -19.7 dB
drums    | def > deephouse            |     12 ms |   0.0  |  +0.0 /  +0.0    |  23.4 ms |  -11.9 dB
acid     | psy > squirt               |     27 ms |   1.3  |  +0.0 /  -0.1    |  15.5 ms |  -24.1 dB
sfx      | riser > psyriser           |     17 ms |  -2.1  |  +2.4 /  -2.3    |  17.5 ms |  -29.7 dB
plant    | lush > sspad               |    207 ms |  -0.1  |  +0.3 / -15.8    |  18.9 ms |  -27.8 dB
perc     | marimba > xylo             |     27 ms |  -4.9  |  +1.9 /  -0.3    |  14.9 ms |  -30.7 dB
sampler  | choir > choirlead          |    182 ms |  -7.6  |  +1.0 /  -5.9    |  11.5 ms |  -17.4 dB
grid     | basic > init               |     27 ms |   5.4  |  +5.1 /  +0.9    |  13.3 ms |  -24.8 dB
kick     | psyzap > psyroll           |     27 ms |   4.4  |  +0.0 /  -1.8    |  23.4 ms |   -9.2 dB
wtab     | init > supersaw            |    107 ms |  -8.3  |  +6.1 /  -3.5    |  36.9 ms |  -22.7 dB
zsnare   | t909 > f808                |     27 ms |  -0.4  |  +3.0 /  -0.6    |  21.3 ms |  -15.2 dB
zclap    | c909 > wide                |    227 ms |  -6.7  |  +0.1 /  -4.7    |  14.7 ms |  -19.1 dB
zhat     | c909 > o909                |    142 ms |  -2.1  |  -0.3 /  -2.4    |  14.6 ms |  -22.7 dB
ztom     | t808 > tmid                |    117 ms |  -0.3  |  +4.0 /  -2.7    |  15.3 ms |  -11.9 dB
growl    | yoi > wub                  |     17 ms |   0.0  |  +0.1 /  -0.0    |  14.9 ms |  -15.5 dB
emit     | spin > duo                 |    557 ms |  14.7  |  -3.6 / -94.9    |  16.5 ms |  -26.7 dB
vgrain   | orbit > swarm              |    292 ms |  -7.7  |  +2.3 / -33.4    |  13.4 ms |  -14.1 dB
vfm      | glass > church             |    412 ms |   4.6  |  +6.0 /  +0.4    |  17.3 ms |  -14.6 dB
orb      | sun > ring                 |     27 ms |  14.4  |  +5.4 /  -7.2    |  13.2 ms |  -16.5 dB
sbass    | pure > warm                |     37 ms |  -1.9  |  +0.0 /  -0.6    |  11.9 ms |  -11.9 dB
bball    | marimba > pingp            |    462 ms |  11.9  |  +3.4 / -102.3    |  12.2 ms |  -23.3 dB
psyb     | fo145 > fo150              |     82 ms | -13.2  |  +0.0 / -96.2    |  23.2 ms |  -20.7 dB
crk      | draw > drawab              |    137 ms |  -1.2  |  +1.3 /  -2.2    |  20.3 ms |  -24.0 dB
venom    | init > l_super             |    152 ms |   0.1  |  +3.3 /  -6.9    |  19.9 ms |  -18.8 dB
== a key held, stopped ==
inst     | switch                     | new sound | glitch | over / dip (dB) | handler | ref level
saw      | def > bright               |     22 ms |   0.1  |  +0.0 /  +0.0    |  15.7 ms |  -27.2 dB
square   | def > flute                |     27 ms |   2.1  |  +0.0 /  +0.0    |  13.0 ms |  -23.6 dB
sub      | def > long                 |     27 ms |   3.3  |  +0.0 /  +0.0    |  17.8 ms |  -15.0 dB
bass     | def > dark                 |     27 ms |   2.7  |  +0.0 /  +0.0    |  14.8 ms |  -18.4 dB
reese    | def > slow                 |     12 ms |   2.0  |  +0.0 /  +0.0    |  12.6 ms |  -23.6 dB
pad      | def > swell                |     27 ms |   1.1  |  +0.0 /  +0.0    |  16.6 ms |  -28.7 dB
strings  | def > slow                 |     27 ms |   1.0  |  +0.0 /  +0.0    |  12.0 ms |  -28.8 dB
pluck    | def > soft                 |     17 ms |   0.0  |  +0.0 /  +0.0    |  21.6 ms | -120.0 dB  silent ref
keys     | def > bright               |     27 ms |   6.6  |  +0.0 /  +0.0    |  15.3 ms |  -35.5 dB
drums    | def > deephouse            |     12 ms |   0.0  |  +0.0 /  +0.0    |  20.4 ms | -180.0 dB  silent ref
acid     | psy > squirt               |     22 ms |   2.6  |  +0.0 /  -0.0    |  12.7 ms |  -22.8 dB
sfx      | riser > psyriser           |     12 ms |  -0.5  |  +3.2 /  -2.8    |  14.6 ms |  -42.4 dB
plant    | lush > sspad               |     22 ms |  -0.9  |  +1.3 /  -1.4    |  18.0 ms |  -25.3 dB
perc     | marimba > xylo             |     27 ms |   0.0  |  +0.0 /  +0.0    |  21.7 ms | -180.0 dB  silent ref
sampler  | choir > choirlead          |     42 ms |  -3.5  |  +1.6 /  -0.2    |  17.9 ms |  -15.4 dB
grid     | basic > init               |     27 ms |   2.4  |  +0.3 /  -0.3    |  16.4 ms |  -22.4 dB
kick     | psyzap > psyroll           |     12 ms |   0.0  |  +0.0 /  +0.0    |  26.4 ms | -180.0 dB  silent ref
wtab     | init > supersaw            |     27 ms |  -0.1  |  +0.0 /  +0.0    |  17.4 ms |  -25.5 dB
zsnare   | t909 > f808                |     12 ms |   0.0  |  +0.0 /  +0.0    |  14.5 ms | -180.0 dB  silent ref
zclap    | c909 > wide                |     12 ms |   0.0  |  +0.0 /  +0.0    |  12.3 ms | -180.0 dB  silent ref
zhat     | c909 > o909                |     12 ms |   0.0  |  +0.0 /  +0.0    |  12.9 ms | -180.0 dB  silent ref
ztom     | t808 > tmid                |     12 ms |   0.0  |  +0.0 /  +0.0    |  16.0 ms | -180.0 dB  silent ref
growl    | yoi > wub                  |     17 ms |   4.3  |  +1.0 /  -1.5    |  21.4 ms |  -14.7 dB
emit     | spin > duo                 |     32 ms |  19.6  |  -0.4 / -13.0    |  18.3 ms |  -28.1 dB
vgrain   | orbit > swarm              |    377 ms |  -0.5  |  +1.1 / -21.5    |  12.2 ms |  -15.0 dB
vfm      | glass > church             |    812 ms |   0.8  | +10.5 /  +6.0    |  15.0 ms |  -20.8 dB
orb      | sun > ring                 |    147 ms |  10.7  | +13.6 /  -2.1    |  15.1 ms |  -20.4 dB
sbass    | pure > warm                |     never |   1.6  |  +1.2 /  -1.3    |  11.4 ms |  -11.4 dB
bball    | marimba > pingp            |    237 ms |  35.2  | +47.0 / -97.4    |  10.9 ms |  -31.8 dB
psyb     | fo145 > fo150              |     77 ms |   0.0  | +95.6 / +55.7    |  16.8 ms | -180.0 dB  silent ref
crk      | draw > drawab              |     never |   3.0  | +25.8 / -26.9    |  17.2 ms |  -24.4 dB
venom    | init > l_super             |    152 ms |   0.2  |  +4.2 /  -5.2    |  19.4 ms |  -19.9 dB
```
