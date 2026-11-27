# AudioLab Pro About page, science backgrounds (task SR6, 27 November 2026)

Pick page: **AudioLab About page, science backgrounds**, https://claude.ai/artifact/41E2nKqQnc88HucvBH43Do

A pick page only: **nothing in index.html or desktop/ was changed, no version bump.** The user's words: "Maybe we can improve the About page with a scientific background with Mars and some magnetic lines or something, and make it look really cool and scientific and detailed in the background." It follows the taste notes of `docs/glass-engine-plan.md` 2.8 (field lines around a planet, orbit rings on a dark grid, small capital mono labels in amber, thin lines, a date stamp) and round 1 in `docs/science-look.md` (section B; no B pick is recorded there yet, so B2 "Orbit corner" stays open next to these).

How to answer: one number, with "quiet" if wanted, for example "AB1" or "AB3 quiet". The picks bar on the page gives the line to paste. ★ marks the recommendation.

## The options

Every option is shown behind the real About content of v0.221 (atom logo, AudioLab PRO, version, "Designed by Ilja V. Jakovliev", the info grid, the "Under the hood" highlights, the buttons, the copyright line). Each has a **Full** and a **Quiet** version (Quiet: lines at half strength, only the main labels) and a **Light** still picture.

| # | Option | What it draws | Cost (see below) |
|---|---|---|---|
| AB0 | Today | The plain dark blue glow. | none |
| **AB1 ★** | **Mars, the real field** | Mars turning (axis tilted 25.19°) in the solar wind. Field lines arrive straight, hang up on the planet, drape around it and stretch into a tail; charges slide along them. Small crustal loops rise from the southern highlands and turn with the planet. Bow shock and pile-up boundary dashed at their measured places. Labels: bow shock 1.64 R, pile-up boundary 1.29 R, crustal field up to 1 500 nT at 100 km, solar wind about 400 km/s, IMF about 2 to 3 nT, draped field 20 to 30 nT, UTC stamp, Mars sol date, scale bar. | about 1.0 ms a picture |
| AB2 | Mars and its two moons | View from above the north pole on a polar grid in Mars radii with a tick ring. Phobos and Deimos orbit to scale, with their real period ratio (1 s on screen = 10 min); Mars turns once per sol; the stationary orbit is dashed. Read-outs for both moons and Mars, a 10 000 km scale bar, a mission clock, UTC stamp, a tick frame. | about 0.3 ms |
| AB3 | Instrument read-out sheet | A framed sheet with tick marks and corner brackets on a fine grid: the globe with graticule, surface marks and the east-west crustal field stripes, a degree ring and the axis; a small Sun, Earth, Mars chart with today's real positions, the Earth to Mars distance and light time; the orbit numbers; UTC stamp and Mars sol date. | about 0.6 ms |
| AB4 | Jupiter, true dipole | A real planetary magnet: dipole field lines (r = L cos²λ) tilted 10.31°, wobbling as the planet turns, with the direction marked; the inner radiation belt, the Io torus at 5.90 radii, charges bouncing between mirror points; banded planet with the Red Spot. | about 0.3 ms |
| AB5 | Earth, Van Allen belts | Earth's dipole (tilt 9.2°), inner belt 1.2 to 3 radii and outer belt 4 to 7 radii, the geostationary shell L 6.6, the magnetopause dashed on the sunward side. | about 0.35 ms |
| AB6 | Saturn, aligned dipole | Saturn with rings D to A to scale (to 2.27 radii). Its magnetic axis lies on its spin axis to under 0.01°, so this field does not wobble. | about 0.3 ms |

### Recommendation: AB1, second choice AB3

AB1 is what was asked for (Mars with magnetic lines) and it is true: the lines are the solar wind's field draped around Mars, plus the crustal patches, which is exactly what Mars Global Surveyor and MAVEN measured. It also has the most motion and depth. AB3 is the most "detailed read-out" and the calmest behind the text; it is the choice if AB1 feels too busy. If a real magnet with closed loops is wanted, AB4 (Jupiter) is the strongest of the three dipoles. Start with Full; Quiet is there if the labels distract.

## Science notes (so the picture is honest)

- **Mars has no global dipole field today.** Mars Global Surveyor found only magnetised crust. The strongest sources are in the southern highlands, in Terra Cimmeria and Terra Sirenum (120° to 210° W, 30° to 85° S, straddling 180°, a prominent feature near 53° S), in east-west bands about 200 km wide and up to 2000 km long. Total field up to about 1600 nT at about 100 km (more than 1500 nT measured), about 220 nT at the 400 km mapping altitude. Upper limit for any global dipole moment: about 2 × 10^18 A m². AB1 and AB3 place the loops and stripes at 150° to 240° E, 30° to 80° S, strongest near 190° E, 52° S; a few weak loops elsewhere stand for the weaker patches.
- **The big structure is induced.** The solar wind's magnetic field piles up against the upper atmosphere, drapes around the planet and is pulled into a two-lobed tail. Shapes used in AB1: the conic fits of Vignes et al. 2000 to Mars Global Surveyor crossings. Bow shock: focus 0.64 R, eccentricity 1.03, semi-latus rectum 2.04 R (1.64 R at the nose, 2.62 R at the terminator). Pile-up boundary: 0.78, 0.90, 0.96 (1.29 R at the nose, 1.47 R at the terminator). Draped field in the dayside barrier: about 20 to 30 nT (MAVEN). Upstream: solar wind about 400 km/s (369 km/s average in one study), field about 2 to 3 nT (1.87 nT average in that study; other samples 2.2 to 6.1 nT). MAVEN also found the tail twisted by about 45° (NASA, October 2017) and mapped the electric currents (May 2020); the twist is not drawn.
- **What is simplified in AB1:** the draping is a drawn model (straight lines carried along, held back on a paraboloid that tightens with age), not a simulation; the picture is a flat cut through the plane of the field; the bend of the lines at the shock is left out.
- **Jupiter, Earth and Saturn have real dipoles.** AB4 to AB6 draw the dipole formula with each planet's tilt; the page labels them "dipole approximation", since real magnetospheres are squeezed on the sunward side and stretched behind. Jupiter's and Saturn's fields point the opposite way to Earth's; the small direction marks follow that. The wobble in AB4 and AB5 is the tilted axis turning with the planet, seen from the side.
- **Live numbers:** UTC from the clock; Mars sol date from the Mars24 formula; Earth and Mars positions from JPL's approximate elements. Check: the page gave 1.212 AU for 27 November 2026, JPL Horizons gives 1.2124 AU.

### Numbers on the labels

| Body | Value | Source |
|---|---|---|
| Mars | mean radius 3389.5 km; sidereal day 24.6229 h (24 h 37 m 23 s); sol 24.6597 h (24 h 39 m 35 s); a 1.5237 AU; e 0.0934; i 1.85°; year 686.98 d; axial tilt 25.19° | NSSDCA Mars fact sheet |
| Phobos | a 9378 km; period 0.31891 d (7 h 39 m); e 0.0151 | NSSDCA Mars fact sheet |
| Deimos | a 23 459 km; period 1.26244 d (30 h 18 m); e 0.0005 | NSSDCA Mars fact sheet |
| Stationary orbit of Mars | 20 428 km from the centre | Wikipedia "Areostationary orbit"; agrees with a calculation from GM and the day length |
| Jupiter | equatorial radius 71 492 km; day 9 h 55 m 30 s; dipole 4.170 gauss (417 000 nT at the equator), tilt 10.31° (Juno model JRM09; the older NSSDCA figure is 4.30 gauss, 9.4°); Io at 421 800 km = 5.90 radii | NSSDCA Jupiter fact sheet; Connerney et al. 2018; JPL SSD |
| Earth | mean radius 6371.0 km; sidereal day 23.9345 h; dipole 0.306 gauss (30 600 nT at the equator); tilt 9.21° (2025; 9.35° in 2020); belts about 1.25 to 3.0 and 4.0 to 7.3 radii from the centre (converted from NASA's miles); magnetopause about 10.5 radii | NSSDCA Earth fact sheet; NOAA NCEI; NASA |
| Saturn | equatorial radius 60 268 km; day 10.656 h; dipole 0.215 gauss (21 500 nT); tilt under 0.0095° (Cassini); rings D 1.110 to 1.236, C 1.239 to 1.526, B 1.526 to 1.950, A 2.030 to 2.270 radii (outer edge 136 780 km) | NSSDCA Saturn and Saturn rings fact sheets; NASA Cassini release |

How the sources were read: a research helper opened each page on 27 November 2026 through a fetch tool that summarises pages, so digits are as that reader reported them. Not opened: Acuña et al. 1998, DiBraccio et al. 2018, the full text of Dougherty et al. 2018, IGRF-13 tables. The polarity of Saturn is stated by NASA for the giant planets as a group. Symbols on the page (R♂, R♃, R⊕, R♄) are the usual planet signs.

### Sources

- NSSDCA fact sheets: https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html , jupiterfact.html , earthfact.html , saturnfact.html , satringfact.html (same folder)
- JPL Solar System Dynamics: satellite elements https://ssd.jpl.nasa.gov/sats/elem/ ; approximate planet positions (elements 1800 to 2050) https://ssd.jpl.nasa.gov/planets/approx_pos.html ; Horizons https://ssd.jpl.nasa.gov/horizons/
- Acuña et al. 1999, Science 284, 790: https://people.ucsc.edu/~igarrick/290_2018/acuna_et_al_1999.pdf
- Connerney et al. 1999, Science 284, 794: https://mgs-mager.gsfc.nasa.gov/publications/science_284_5415_connerney/science_284_5415_connerney.pdf
- Connerney et al. 2001, GRL 28: https://mgs-mager.gsfc.nasa.gov/publications/grl_28_connerney/grl_28_connerney_paper.html
- Vignes et al. 2000, GRL 27, 49: https://ui.adsabs.harvard.edu/abs/2000GeoRL..27...49V/abstract (full text read at https://scispace.com/pdf/the-solar-wind-interaction-with-mars-locations-and-shapes-of-1faawaqnu8.pdf)
- Draped field at Mars (MAVEN): https://arxiv.org/pdf/1801.08878 ; upstream solar wind and field: https://arxiv.org/pdf/2604.08710 (citing Liu et al. 2021)
- NASA MAVEN: twisted tail https://www.nasa.gov/news-release/nasas-maven-mission-finds-mars-has-a-twisted-tail ; electric currents https://www.nasa.gov/news-release/maven-maps-electric-currents-around-mars-that-are-fundamental-to-atmospheric-loss
- Mars sol date, NASA GISS Mars24: https://www.giss.nasa.gov/tools/mars24/help/algorithm.html (MSD = (JD_TT − 2451549.5) / 1.0274912517 + 44796.0 − 0.0009626; TT − UTC = 69.184 s)
- Jupiter field, Connerney et al. 2018 (JRM09): https://ntrs.nasa.gov/citations/20180004823
- Planet polarity: https://pwg.gsfc.nasa.gov/earthmag/planetmg.htm ; Earth's magnetopause: https://pwg.gsfc.nasa.gov/Education/wmpause.html
- Earth's dipole tilt: https://www.ncei.noaa.gov/products/wandering-geomagnetic-poles ; Van Allen belts: https://www.nasa.gov/image-article/radiation-belts-with-satellites/
- Saturn's tilt: https://science.nasa.gov/missions/cassini/groundbreaking-science-emerges-from-ultra-close-orbits-of-saturn

**No NASA pictures and no logos are used.** Every planet, line and label is drawn in code, so there is nothing to credit or license.

## Readability

Three things keep the text easy to read, and they are part of each option: the info grid and the feature tiles get a darker backing (about 77 % opaque instead of today's 3 to 6 %); the canvas is dimmed behind the name, version and credits and behind the "Under the hood" heading; and the lower two thirds are dimmed slightly overall. The planet and the labels live in the top band beside the logo and at the edges.

Checked in a headless browser: for every text style, the text colour against the **brightest single point** of the canvas behind it (a hard test, since most of the text sits on the dark ground).

| Text | Today (AB0) | Worst of AB1 to AB6, Full | Worst, Quiet |
|---|---|---|---|
| Feature names, credits name, values, grid labels, "Under the hood" | 4.8 to 15.8 : 1 | 4.6 : 1 or better | 4.8 : 1 or better |
| Copyright line | 4.27 : 1 | 4.27 : 1 | 4.27 : 1 |
| "Version 0.221" under the name | 2.97 : 1 | 3.16 : 1 | 3.23 : 1 |

So no option reads worse than today. The one weak line, the small grey "Version 0.221", is weak today as well (the backgrounds dim the glow behind it a little, hence the slightly better figure); a step brighter grey would fix it whichever option is picked. In the **Light** level the tiles are solid (as today) and the background is a still picture, so the same figures hold or improve.

## Cost

Rules built into the page and meant for the app: one canvas for the whole background; at most 30 pictures a second; pixel ratio capped at 2; no blur, no shadows; drawing stops when the About window is closed or hidden and when the app is in the background; the Light level and "reduce motion" draw one still picture once.

Measured drawing time per picture, 780 × 828, on the cloud machine (no graphics card, so real computers should do better): AB1 0.9 to 1.1 ms, AB2 0.2 to 0.3, AB3 0.6 to 0.8, AB4 0.3, AB5 0.35, AB6 0.3; Quiet is a little cheaper. At 30 a second that is about 3 % of one core for AB1 and about 1 to 2 % for the others, only while About is open. The page shows the live figure on the user's own computer above the preview.

## Next (after the pick; nothing started)

Implement the chosen option in index.html as a serial task with the usual release routine: one canvas behind `#splash.ab` (sticky while the content scrolls), the darker backing for `.abg` and `.ahfT`, the freeze-in-background and Light rules above, and a headless test. The drawing code on the pick page is written to be lifted as it is (about 250 lines for one option with its helpers).
