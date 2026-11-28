"""Task TH1: fit, tune and measure every proposed theme, then write themes.json (read by build_page.py) and report.md.

  python3 check.py            fit + tune + measure, write themes.json and report.md
  python3 check.py --gate     measure only (no fitting), exit 1 when a rule fails: the proposed release-gate step

The rules (RULES below) are the readability rules of docs/research-themes.md. Theme A (today) is locked: its known misses are
reported as the baseline, never fitted."""
import json, random, sys, os, copy
from colour import *
from themes_src import THEMES

HERE = os.path.dirname(os.path.abspath(__file__))
VISIONS = ['normal', 'protan', 'deutan', 'tritan']

# ---------- the rules: (id, label, token, surfaces, kind, thresholds) ----------
# kind 'text': APCA |Lc| and WCAG ratio both; 'ui': WCAG >= 3 (WCAG 2.2 SC 1.4.11 non-text contrast); 'spot': APCA only
SURF_ALL = ['bg', 'chrome', 'ruler', 'lane0', 'lane1', 'laneSel', 'panel', 'panel2', 'strip', '@glass']
RULES = [
 ('T1', 'Main text', 'ink', SURF_ALL, 'text', dict(lc=75, wc=7)),
 ('T2', 'Labels', 'lab', ['chrome', 'lane0', 'panel', 'panel2', 'strip', '@glass'], 'text', dict(lc=60, wc=4.5)),
 ('T3', 'Quiet text (11 px, weight 500)', 'mut', ['bg', 'chrome', 'lane0', 'panel', 'panel2', 'strip', '@glass'], 'text', dict(lc=45, wc=4.5)),
 ('T4', 'Disabled text', 'dis', ['panel', 'strip'], 'spot', dict(lc=30)),
 ('T5', 'Ruler numbers', 'rulerTxt', ['ruler'], 'text', dict(lc=60, wc=4.5)),
 ('T6', 'Units (amber, L2) on panels', 'unit', ['chrome', 'panel', 'strip'], 'text', dict(lc=55, wc=4.5)),
 ('T6d', 'Units in displays', 'unitD', ['display'], 'text', dict(lc=55, wc=4.5)),
 ('T7', 'Text on accent buttons', 'onAccent', ['accent'], 'text', dict(lc=60, wc=4.5)),
 ('T8', 'Over read-out in displays', 'overD', ['display'], 'text', dict(lc=45, wc=4.5)),
 ('T10', 'Text in displays', 'inkD', ['display'], 'text', dict(lc=75, wc=7)),
 ('T9', 'Over / error text on panels', 'over', ['panel', 'strip'], 'text', dict(lc=45, wc=4.5)),
 ('U1', 'Accent (buttons on, links, toggles)', 'accent', ['bg', 'chrome', 'panel', 'strip'], 'ui', {}),
 ('U2', 'Selection outline (A1)', 'sel', ['lane0', 'laneSel', 'panel', 'strip'], 'ui', {}),
 ('U3', 'Record button', 'rec', ['chrome', 'panel'], 'ui', {}),
 ('U4', 'Playhead', 'ph', ['ruler', 'lane0', 'lane1'], 'ui', {}),
 ('U5', 'Meter segments in their well', ['m0', 'm1', 'm2', 'm3'], ['display'], 'ui', {}),
 ('U6', 'Limit colours in displays', ['warn', 'ok', 'overD'], ['display'], 'ui', {}),
 ('U9', 'Curves and handles in displays', ['accentD', 'selD'], ['display'], 'ui', {}),
 ('U7', 'Focus ring (two colours, best band)', '@focus', SURF_ALL[:-1], 'ui', {}),
 ('U8', 'Track colours against the lanes (clip edges)', '@pal', ['lane0', 'lane1'], 'ui', {}),
]
# meaning colours that must never be confused with each other (CIEDE2000)
DISTINCT = [('accent', 'sel', 15), ('sel', 'over', 15), ('sel', 'rec', 15), ('accent', 'rec', 15), ('accent', 'ok', 10), ('ph', 'sel', 10), ('ph', 'rec', 15)]
CVD_TARGET, CVD_FLOOR = 10, 6

def is_dark(c): return rel_lum(c) < 0.18

def clip_bodies(th):
    t = th['t']
    return [mix(c, t['lane0'], t['clipA']) for c in th['pal']]

def glass_backdrops(th):
    t = th['t']; b = clip_bodies(th)
    lum = sorted(b, key=rel_lum)
    return [t['lane0'], t['laneSel'], t['bg'], lum[0], lum[-1]]

def glass_over(th, a=None):
    t = th['t']; a = t['glassA'] if a is None else a
    return [mix(t['glass'], bd, a) for bd in glass_backdrops(th)]

def surfaces(th, s):
    return glass_over(th) if s == '@glass' else [th['t'][s]]

def measure_rule(th, rule):
    rid, label, tok, surfs, kind, thr = rule
    t = th['t']; rows = []
    toks = tok if isinstance(tok, list) else [tok]
    if tok == '@pal': toks = ['pal%d' % i for i in range(len(th['pal']))]
    for k in toks:
        for s in surfs:
            for bg in surfaces(th, s):
                if k == '@focus':
                    w = max(wcag(t['focusIn'], bg), wcag(t['focusOut'], bg)); lc = None; fg = t['focusIn']
                else:
                    fg = th['pal'][int(k[3:])] if k.startswith('pal') else t[k]
                    w = wcag(fg, bg); lc = apca(fg, bg)
                if kind == 'text': ok = abs(lc) >= thr['lc'] and w >= thr['wc']
                elif kind == 'spot': ok = abs(lc) >= thr['lc']
                else: ok = w >= 3
                rows.append(dict(tok=k, fg=fg, surf=s, bg=bg, wc=round(w, 2), lc=None if lc is None else round(lc, 1), ok=ok))
    worst = min(rows, key=lambda r: (r['ok'], abs(r['lc']) if (kind != 'ui' and r['lc'] is not None) else r['wc']))
    return dict(id=rid, label=label, kind=kind, thr=thr, n=len(rows), fails=sum(not r['ok'] for r in rows), worst=worst)

def measure(th):
    t = th['t']
    t.setdefault('unitD', t['unit'])
    t.setdefault('accentD', t['accent']); t.setdefault('selD', t['sel'])
    t.setdefault('inkD', t['ink'] if is_dark(t['lane0']) else t['lane0'])
    res = [measure_rule(th, r) for r in RULES]
    dist = [dict(a=a, b=b, need=n, de=round(de2000(t[a], t[b]), 1), ok=de2000(t[a], t[b]) >= n) for a, b, n in DISTINCT]
    cvd = {}
    for v in VISIONS:
        d, pair = min_de(th['pal'], v); cvd[v] = dict(de=round(d, 1), pair=pair)
    cvd_min = min(x['de'] for x in cvd.values())
    # clip titles: the better of the theme's ink and a near-black ink on each clip body
    titles = []
    for c, body in zip(th['pal'], clip_bodies(th)):
        cands = [t['ink'], '#101114', '#FFFFFF']
        best = max(cands, key=lambda x: wcag(x, body))
        titles.append(dict(clip=c, body=body, ink=best, wc=round(wcag(best, body), 2), lc=round(apca(best, body), 1)))
    # glass floor: lowest panel opacity at which T1 to T3 still pass over every backdrop
    floor = None
    chk = lambda k, lc, wc, a: all(abs(apca(t[k], g)) >= lc and wcag(t[k], g) >= wc for g in glass_over(th, a))
    req = [x for x in [('ink', 75, 7), ('lab', 60, 4.5), ('mut', 45, 4.5)] if chk(*x, 1.0)]
    for a100 in range(0, 101):
        a = a100 / 100
        if all(chk(*x, a) for x in req): floor = a; break
    return dict(rules=res, distinct=dist, cvd=cvd, cvd_min=cvd_min, titles=titles, glass_floor=floor,
                fails=sum(r['fails'] > 0 for r in res) + sum(not d['ok'] for d in dist) + (cvd_min < CVD_FLOOR))

# ---------- fitting: move lightness only, until the rule passes ----------
FIT = {'ink': ['T1'], 'lab': ['T2'], 'mut': ['T3'], 'dis': ['T4'], 'rulerTxt': ['T5'], 'unit': ['T6'], 'unitD': ['T6d'], 'inkD': ['T10'], 'accentD': ['U9'], 'selD': ['U9'], 'overD': ['T8'], 'over': ['T9'],
       'sel': ['U2'], 'rec': ['U3'], 'ph': ['U4'], 'm0': ['U5'], 'm1': ['U5'], 'm2': ['U5'], 'm3': ['U5'], 'warn': ['U6'], 'ok': ['U6']}

def tok_passes(th, tok, rid):
    rule = [r for r in RULES if r[0] == rid][0]
    r = list(rule); r[2] = tok
    return measure_rule(th, tuple(r))['fails'] == 0

def fit_token(th, tok, rids, log):
    t = th['t']; orig = t[tok]
    for rid in rids:
        if tok_passes(th, tok, rid): continue
        rule = [r for r in RULES if r[0] == rid][0]
        bgs = [b for s in rule[3] for b in surfaces(th, s)]
        up = sum(is_dark(b) for b in bgs) >= len(bgs) / 2
        L0 = oklch(t[tok])[0]
        for i in range(1, 80):
            L = min(0.995, L0 + 0.005 * i) if up else max(0.02, L0 - 0.005 * i)
            t[tok] = set_L(orig, L)
            if tok_passes(th, tok, rid): break
    if t[tok].upper() != orig.upper(): log.append(dict(tok=tok, was=orig, now=t[tok]))

def fit_accent(th, log):
    """the accent must stand out from the panels (U1) and carry its button text (T7): darken or lighten it, else flip the text colour"""
    t = th['t']; orig = (t['accent'], t['onAccent'])
    def good(): return tok_passes(th, 'accent', 'U1') and tok_passes(th, 'onAccent', 'T7')
    if not good():
        best = None
        for on in [t['onAccent'], '#FFFFFF', t['bg']]:
            for i in range(0, 120):
                for sgn in (1, -1):
                    L = oklch(orig[0])[0] + sgn * 0.004 * i
                    if not 0.05 < L < 0.98: continue
                    t['accent'], t['onAccent'] = set_L(orig[0], L), on
                    if good():
                        cand = (i, t['accent'], on)
                        if best is None or cand[0] < best[0]: best = cand
                if best and best[0] <= i: break
        if best: t['accent'], t['onAccent'] = best[1], best[2]
        else: t['accent'], t['onAccent'] = orig
    if (t['accent'], t['onAccent']) != orig: log.append(dict(tok='accent / onAccent', was='%s / %s' % orig, now='%s / %s' % (t['accent'], t['onAccent'])))

def tune_palette(th, log, iters=2500):
    """hill climb in OKLCH: each track colour may move a little (L 0.10, C 0.05, hue 18 degrees) from the hand-picked one, to raise
    the smallest CIEDE2000 under normal, protan, deutan and tritan vision while every clip edge keeps 3:1 against both lanes"""
    t = th['t']; base = [oklch(c) for c in th['pal']]; rnd = random.Random(7 + ord(th['id'][0]))
    def score(p):
        pen = sum(max(0, 3 - wcag(c, t[l])) for c in p for l in ('lane0', 'lane1')) * 40
        return min(min_de(p, v)[0] for v in VISIONS) - pen
    cur = list(th['pal']); cs = score(cur); state = [list(b) for b in base]
    for _ in range(iters):
        i = rnd.randrange(len(cur)); L, C, h = state[i]; bL, bC, bh = base[i]
        nL = min(bL + .10, max(bL - .10, L + rnd.uniform(-.03, .03)))
        nC = min(bC + .05, max(max(0, bC - .05), C + rnd.uniform(-.015, .015)))
        nh = bh + max(-18, min(18, (h - bh) + rnd.uniform(-5, 5)))
        cand = list(cur); cand[i] = from_oklch(nL, nC, nh % 360); s = score(cand)
        if s >= cs: cur, cs, state[i] = cand, s, [nL, nC, nh]
    before = min(min_de(th['pal'], v)[0] for v in VISIONS)
    if cur != th['pal']:
        log.append(dict(tok='track colours', was=' '.join(th['pal']), now=' '.join(cur), note='smallest CIEDE2000 over four visions %.1f -> %.1f' % (before, min(min_de(cur, v)[0] for v in VISIONS))))
        th['pal'] = cur

def main():
    gate = '--gate' in sys.argv
    themes = copy.deepcopy(THEMES)
    if gate:
        themes = json.load(open(os.path.join(HERE, 'themes.json')))['themes']
    out = []
    for th in themes:
        th = copy.deepcopy(th); log = []
        th['t'].setdefault('unitD', th['t']['unit'])
        th['t'].setdefault('accentD', th['t']['accent']); th['t'].setdefault('selD', th['t']['sel'])
        th['t'].setdefault('inkD', th['t']['ink'] if is_dark(th['t']['lane0']) else th['t']['lane0'])
        if not gate and not th.get('lock'):
            th['src'] = dict(t=dict(th['t']), pal=list(th['pal']))
            tune_palette(th, log)
            # glass first: thicker glass instead of whiter text (pure white on near-black halates, research section 3)
            a100 = round(th['t']['glassA'] * 100)
            for a100 in range(a100, 86):
                g = glass_over(th, a100 / 100)
                if all(abs(apca(th['t'][k], x)) >= lc and wcag(th['t'][k], x) >= wc for k, lc, wc in [('ink', 75, 7), ('lab', 60, 4.5), ('mut', 45, 4.5)] for x in g): break
            if a100 / 100 > th['t']['glassA']:
                log.append(dict(tok='glassA', was=th['t']['glassA'], now=a100 / 100, note='raised so the hand-picked text passes over the brightest clip')); th['t']['glassA'] = a100 / 100
            for tok, rids in FIT.items(): fit_token(th, tok, rids, log)
            fit_accent(th, log)
            if th['t']['accentD'] == th['src']['t']['accent']: th['t']['accentD'] = th['t']['accent']
            for tok, rids in FIT.items(): fit_token(th, tok, rids, log)   # second pass: the accent or palette may have moved
            fl = measure(th)['glass_floor']
            if fl is not None and fl > th['t']['glassA']:
                log.append(dict(tok='glassA', was=th['t']['glassA'], now=fl, note='raised to the glass floor')); th['t']['glassA'] = fl
        if not gate: th['fit'] = log
        th['m'] = measure(th)
        out.append(th)
    if gate:
        bad = [(th['id'], r['id']) for th in out for r in th['m']['rules'] if r['fails'] and not th.get('lock')]
        print('theme contrast gate:', 'PASS' if not bad else 'FAIL ' + str(bad)); sys.exit(1 if bad else 0)
    json.dump(dict(rules=[dict(id=r[0], label=r[1], kind=r[4], thr=r[5], surfaces=r[3]) for r in RULES], distinct=DISTINCT,
                   cvd_target=CVD_TARGET, cvd_floor=CVD_FLOOR, themes=out), open(os.path.join(HERE, 'themes.json'), 'w'), indent=1)
    # report
    L = ['| Theme | Mode | Rule fails | Worst main text | Worst quiet text | Worst units | Smallest track ΔE (N/P/D/T) | Glass floor |', '|---|---|---|---|---|---|---|---|']
    for th in out:
        m = th['m']; R = {r['id']: r for r in m['rules']}
        w = lambda k: '%s Lc %s, %.1f:1' % (R[k]['worst']['surf'], R[k]['worst']['lc'], R[k]['worst']['wc'])
        c = m['cvd']
        L.append('| %s %s | %s | %d | %s | %s | %s | %s / %s / %s / %s | %s |' % (th['id'], th['name'], th['mode'], m['fails'], w('T1'), w('T3'), w('T6'),
                 c['normal']['de'], c['protan']['de'], c['deutan']['de'], c['tritan']['de'], m['glass_floor']))
    open(os.path.join(HERE, 'report.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    for th in out:
        bad = [(r['id'], r['fails'], r['worst']['tok'], r['worst']['surf'], r['worst']['wc'], r['worst']['lc']) for r in th['m']['rules'] if r['fails']]
        dbad = [(d['a'], d['b'], d['de']) for d in th['m']['distinct'] if not d['ok']]
        if bad or dbad: print(th['id'], 'FAILS', bad, dbad)

if __name__ == '__main__':
    main()
