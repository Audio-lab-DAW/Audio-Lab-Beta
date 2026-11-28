"""Task TH2: fit, tune and measure the reworked themes with the rules of tools/design-lab/th1/check.py plus the round 2 rules.

  python3 check.py            fit + tune + measure, write themes.json and report.md
  python3 check.py --gate     measure only, exit 1 when a rule fails (A0 is the locked baseline and never fails the gate)

Round 1's twenty rules are imported unchanged from ../th1/check.py, with two widenings:
  T7  text on filled buttons is measured on the new token accentFill (it equals accent when a theme does not split them)
  U8  clip edges must keep 3 : 1 on the selected lane too, not only on the two plain lanes
New in round 2:
  U1b filled buttons (accentFill) 3 : 1 against the panels they sit on
  U6s play and "on" green on panels (okS) 3 : 1   (round 1 measured ok only inside displays; it failed on paper)
  T11 clip titles: the ink picked per clip on the clip's title band (body plus the band's tint) on all three lanes, 4.5 : 1 and Lc 60
  T12 tooltip text on the tooltip, 7 : 1 and Lc 75
  U10 tooltip outline (tipEdge; the plate itself when it is an inverse plate) against what is under it, 3 : 1
  H1  halation: main text in a dark theme is never pure white (OKLCH L at most 0.985)
  G1  glass tint at or above the measured floor
"""
import json, random, sys, os, copy, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
TH1 = os.path.join(HERE, '..', 'th1')
sys.path.insert(0, TH1)
from colour import *
_spec = importlib.util.spec_from_file_location('th1check', os.path.join(TH1, 'check.py'))
B = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(B)
_s2 = importlib.util.spec_from_file_location('th2themes', os.path.join(HERE, 'themes_src.py'))
_m2 = importlib.util.module_from_spec(_s2); _s2.loader.exec_module(_m2)
THEMES = _m2.THEMES

VISIONS = B.VISIONS
LANES = ['lane0', 'lane1', 'laneSel']
PANELS = ['chrome', 'panel', 'panel2', 'strip']

def rules2():
    out = []
    for r in B.RULES:
        r = list(r)
        if r[0] == 'T7': r[1] = 'Text on filled buttons'; r[3] = ['accentFill']
        if r[0] == 'U8': r[1] = 'Track colours against the lanes (clip edges), selected lane too'; r[3] = LANES
        out.append(tuple(r))
        if r[0] == 'U1': out.append(('U1b', 'Filled buttons against their panel', 'accentFill', PANELS, 'ui', {}))
        if r[0] == 'U6': out.append(('U6s', 'Play and "on" green on panels', 'okS', PANELS, 'ui', {}))
    out.append(('T12', 'Tooltip text', 'tipInk', ['tip'], 'text', dict(lc=75, wc=7)))
    out.append(('U10', 'Tooltip outline against what is under it', 'tipEdge', ['bg', 'chrome', 'ruler', 'lane0', 'laneSel', 'panel', 'strip'], 'ui', {}))
    return out
B.RULES = rules2()
B.FIT = dict(B.FIT, okS=['U6s'], tipInk=['T12'], tipEdge=['U10'])

def defaults(th):
    t = th['t']
    t.setdefault('unitD', t['unit']); t.setdefault('accentD', t['accent']); t.setdefault('selD', t['sel'])
    t.setdefault('inkD', t['ink'] if B.is_dark(t['lane0']) else t['lane0'])
    t.setdefault('accentFill', t['accent']); t.setdefault('okS', t['ok']); t.setdefault('selFill', t['sel']); t.setdefault('tipEdge', t['tip'])

def title_ink(t, body):
    """the ink a clip title takes on its clip body: the theme's ink, near black or white, whichever clears both measures best"""
    return max([t['ink'], '#101114', '#FFFFFF'], key=lambda x: min(wcag(x, body) / 4.5, abs(apca(x, body)) / 60))

def title_bg(th, c, lane):
    t = th['t']; body = mix(c, t[lane], t['clipA'])
    return mix(c, body, th.get('style', {}).get('clipHead', 0))

def clip_titles(th):
    t = th['t']; rows = []
    for i, c in enumerate(th['pal']):
        for l in LANES:
            body = title_bg(th, c, l); ink = title_ink(t, body)
            w, lc = wcag(ink, body), apca(ink, body)
            rows.append(dict(tok='title on clip %d' % (i + 1), fg=ink, surf=l, bg=body, wc=round(w, 2), lc=round(lc, 1), ok=w >= 4.5 and abs(lc) >= 60))
    return rows

def extra_rules(th, m):
    t = th['t']; ex = []
    rows = clip_titles(th); worst = min(rows, key=lambda r: (r['ok'], abs(r['lc'])))
    ex.append(dict(id='T11', label='Clip titles on their clips (ink picked per clip)', kind='text', thr=dict(lc=60, wc=4.5), n=len(rows), fails=sum(not r['ok'] for r in rows), worst=worst))
    if th['mode'] == 'dark':
        L = oklch(t['ink'])[0]; ok = L <= .985
        ex.append(dict(id='H1', label='Main text is not pure white (halation)', kind='val', thr=dict(max=.985), n=1, fails=0 if ok else 1,
                       worst=dict(tok='ink', fg=t['ink'], surf='lane0', bg=t['lane0'], wc=round(wcag(t['ink'], t['lane0']), 2), lc=round(apca(t['ink'], t['lane0']), 1), ok=ok, val='L %.3f' % L)))
    fl = m['glass_floor']; ok = fl is not None and t['glassA'] + 1e-9 >= fl
    worstg = min(B.glass_over(th), key=lambda g: abs(apca(t['mut'], g)))
    ex.append(dict(id='G1', label='Glass tint at or above the floor', kind='val', thr=dict(min=fl), n=1, fails=0 if ok else 1,
                   worst=dict(tok='mut', fg=t['mut'], surf='@glass', bg=worstg, wc=round(wcag(t['mut'], worstg), 2), lc=round(apca(t['mut'], worstg), 1), ok=ok,
                              val='%d %% (floor %s)' % (round(t['glassA'] * 100), 'none' if fl is None else '%d %%' % round(fl * 100)))))
    return ex

def measure(th):
    defaults(th)
    m = B.measure(th)
    ex = extra_rules(th, m)
    m['rules'] += ex
    m['fails'] += sum(r['fails'] > 0 for r in ex)
    m['pairs'] = sum(r['n'] for r in m['rules'])
    m['titles'] = [dict(i=int(r['tok'].split()[-1]) - 1, lane=r['surf'], ink=r['fg'], bg=r['bg'], wc=r['wc'], lc=r['lc']) for r in clip_titles(th)]
    return m

def fit_fill(th, log):
    """accentFill carries the button text (T7) and must stand off its panel (U1b): move its lightness the shortest way"""
    t = th['t']; orig = t['accentFill']
    good = lambda: B.tok_passes(th, 'onAccent', 'T7') and B.tok_passes(th, 'accentFill', 'U1b')
    if good(): return
    L0 = oklch(orig)[0]
    for i in range(1, 150):
        for sgn in (1, -1):
            L = L0 + sgn * .004 * i
            if not .05 < L < .98: continue
            t['accentFill'] = set_L(orig, L)
            if good():
                log.append(dict(tok='accentFill', was=orig, now=t['accentFill'])); return
    t['accentFill'] = orig

def tune_palette(th, log, iters=8000):
    """hill climb in OKLCH inside the theme's limits: raise the smallest CIEDE2000 under four visions while every clip edge keeps
    3 : 1 on all three lanes and every clip title keeps 4.5 : 1 and Lc 60"""
    t = th['t']; lim = th.get('tune', dict(L=.10, C=.05, h=18))
    base = [oklch(c) for c in th['pal']]; rnd = random.Random(7 + sum(map(ord, th['id'])))
    def score(p):
        pen = sum(max(0, 3.02 - wcag(c, t[l])) for c in p for l in LANES) * 40
        for c in p:
            for l in LANES:
                body = title_bg(th, c, l); ink = title_ink(t, body)
                pen += max(0, 4.55 - wcag(ink, body)) * 20 + max(0, 61 - abs(apca(ink, body))) * 2
        return min(min_de(p, v)[0] for v in VISIONS) - pen
    cur = list(th['pal']); cs = score(cur); state = [list(b) for b in base]
    for _ in range(iters):
        i = rnd.randrange(len(cur)); L, C, h = state[i]; bL, bC, bh = base[i]
        nL = min(bL + lim['L'], max(bL - lim['L'], L + rnd.uniform(-.03, .03)))
        nC = min(bC + lim['C'], max(max(0, bC - lim['C']), C + rnd.uniform(-.015, .015)))
        nh = bh + max(-lim['h'], min(lim['h'], (h - bh) + rnd.uniform(-5, 5)))
        cand = list(cur); cand[i] = from_oklch(nL, nC, nh % 360); s = score(cand)
        if s >= cs: cur, cs, state[i] = cand, s, [nL, nC, nh]
    before = min(min_de(th['pal'], v)[0] for v in VISIONS)
    if cur != th['pal']:
        log.append(dict(tok='track colours', was=' '.join(th['pal']), now=' '.join(cur),
                        note='smallest CIEDE2000 over four visions %.1f -> %.1f (limits: lightness %.2f, chroma %.3f, hue %d degrees)' % (before, min(min_de(cur, v)[0] for v in VISIONS), lim['L'], lim['C'], lim['h'])))
        th['pal'] = cur

GLASS_REQ = [('ink', 75, 7), ('lab', 60, 4.5), ('mut', 45, 4.5)]

def fit(th):
    log = []; t = th['t']
    th['src'] = dict(t=dict(t), pal=list(th['pal']))
    tune_palette(th, log)
    # glass: keep the hand-picked tint if the text can be lifted to pass on it (lightness only, inside caps that keep the four text
    # levels apart and main text off pure white); otherwise thicken the glass one step and try again
    dark = th['mode'] == 'dark'
    def lift(a):
        tt = dict(t); cap = dict(ink=.972 if dark else .0, lab=None, mut=None)
        for k, lc, wc in GLASS_REQ:
            L0 = oklch(tt[k])[0]
            for i in range(0, 60):
                L = L0 + (.004 * i if dark else -.004 * i)
                if i and k == 'ink' and dark and L > .972: return None
                if i and k == 'lab' and abs(L - oklch(tt['ink'])[0]) < .07: return None
                if i and k == 'mut' and abs(L - oklch(tt['lab'])[0]) < .085: return None
                if not 0.03 < L < .99: return None
                c = set_L(t[k], L)
                th2 = dict(th, t=dict(tt, **{k: c}))
                if all(abs(apca(c, x)) >= lc and wcag(c, x) >= wc for x in B.glass_over(th2, a)): tt[k] = c; break
            else: return None
        return tt
    a0 = round(t['glassA'] * 100)
    for a100 in range(a0, 96):
        tt = lift(a100 / 100)
        if tt: break
    else: tt = dict(t); a100 = a0
    for k in ('ink', 'lab', 'mut'):
        if tt[k].upper() != t[k].upper(): log.append(dict(tok=k, was=t[k], now=tt[k], note='lifted to read on the glass')); t[k] = tt[k]
    if a100 / 100 > t['glassA']:
        log.append(dict(tok='glassA', was=t['glassA'], now=a100 / 100, note='thickened: the text could not be lifted further')); t['glassA'] = a100 / 100
    for _ in range(2):
        for tok, rids in B.FIT.items(): B.fit_token(th, tok, rids, log)
        if t['accentFill'] == th['src']['t'].get('accentFill', th['src']['t']['accent']) and 'accentFill' not in th['src']['t']:
            B.fit_accent(th, log); t['accentFill'] = t['accent']
        else:
            # split accent: the line colour only has to stand out (U1); the fill carries the text
            if not B.tok_passes(th, 'accent', 'U1'): B.fit_token(th, 'accent', ['U1'], log)
            fit_fill(th, log)
        if t['accentD'] == th['src']['t']['accent']: t['accentD'] = t['accent']
    fl = B.measure(th)['glass_floor']
    if fl is not None and fl > t['glassA']:
        log.append(dict(tok='glassA', was=t['glassA'], now=fl, note='raised to the glass floor')); t['glassA'] = fl
    # merge repeated moves of one token into one line
    seen = {}
    for e in log:
        if e['tok'] in seen and e['tok'] != 'track colours': seen[e['tok']]['now'] = e['now']
        else: seen[e['tok']] = e
    return [e for e in seen.values() if str(e['was']).upper() != str(e['now']).upper()]

def main():
    gate = '--gate' in sys.argv
    themes = json.load(open(os.path.join(HERE, 'themes.json')))['themes'] if gate else copy.deepcopy(THEMES)
    out = []
    for th in themes:
        th = copy.deepcopy(th); defaults(th)
        if not gate:
            th['fit'] = [] if th.get('lock') else fit(th)
        th['m'] = measure(th)
        out.append(th)
    bad = [(th['id'], r['id'], r['fails']) for th in out for r in th['m']['rules'] if r['fails'] and not th.get('lock')]
    bad += [(th['id'], 'D %s/%s' % (d['a'], d['b']), d['de']) for th in out for d in th['m']['distinct'] if not d['ok'] and not th.get('lock')]
    bad += [(th['id'], 'C', th['m']['cvd_min']) for th in out if th['m']['cvd_min'] < B.CVD_FLOOR and not th.get('lock')]
    if gate:
        print('theme contrast gate (round 2):', 'PASS, %d themes' % len(out) if not bad else 'FAIL ' + str(bad)); sys.exit(1 if bad else 0)
    rules = [dict(id=r[0], label=r[1], kind=r[4], thr=r[5], surfaces=r[3]) for r in B.RULES]
    json.dump(dict(rules=rules, distinct=B.DISTINCT, cvd_target=B.CVD_TARGET, cvd_floor=B.CVD_FLOOR, themes=out), open(os.path.join(HERE, 'themes.json'), 'w'), indent=1)
    L = ['| Version | Mode | Rules passed | Pairs | Main text (worst) | Quiet text (worst) | Clip titles (worst) | Clip edge (worst) | Track ΔE N / P / D / T | Glass floor | Glass |',
         '|---|---|---|---|---|---|---|---|---|---|---|']
    for th in out:
        m = th['m']; R = {r['id']: r for r in m['rules']}; c = m['cvd']
        w = lambda k: '%.1f : 1, Lc %s' % (R[k]['worst']['wc'], R[k]['worst']['lc'])
        n = len(m['rules']); f = sum(r['fails'] > 0 for r in m['rules'])
        L.append('| %s %s | %s | %d of %d%s | %d | %s | %s | %s | %.2f : 1 | %s / %s / %s / %s | %d %% | %d %% |' % (
            th['id'], th['name'], th['mode'], n - f, n, ' (today\'s misses, kept)' if th.get('lock') and f else '', m['pairs'], w('T1'), w('T3'), w('T11'), R['U8']['worst']['wc'],
            c['normal']['de'], c['protan']['de'], c['deutan']['de'], c['tritan']['de'], round((m['glass_floor'] or 0) * 100), round(th['t']['glassA'] * 100)))
    open(os.path.join(HERE, 'report.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    print('FAILS:', bad or 'none')
    for th in out:
        if th.get('fit'): print(th['id'], '; '.join('%s %s -> %s' % (e['tok'], str(e['was'])[:17], str(e['now'])[:17]) if e['tok'] != 'track colours' else 'pal: ' + e['note'][:60] for e in th['fit']))

if __name__ == '__main__':
    main()
