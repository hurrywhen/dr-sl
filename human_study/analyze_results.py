#!/usr/bin/env python3
"""Human study analysis: utility scoring (T23 anchor) + coupling annotation (T24 anchor).

Inputs (returned by raters):
  utility_scoring_sheet1.csv / utility_scoring_sheet2.xlsx   (160 rows each)
  annotation_sheet1.csv / annotation_sheet2.xlsx             (50 rows each)
Joined against:
  utility_variant_key.json                 (blinded variant decoding)
  ../results/stage5_20260907/stage5_p37_utility_detail.jsonl (auto U_sem)
  ../results/stage5_20260907/stage5_p38_mixed_detail.jsonl   (auto coupling verdict)

Registered decision criteria (README_人工研究说明.md):
  utility:   paired human-vs-auto Spearman rho >= 0.8 (subjects >= 50)
  annotation: human-vs-auto Cohen's kappa >= 0.8
Outputs: analysis_results.json + printed summary.
"""
import csv, json, math, os, re, zipfile
import xml.etree.ElementTree as ET
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(BASE, '..', 'results', 'stage5_20260907')

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

def read_xlsx(path):
    z = zipfile.ZipFile(path)
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall(f'{NS}si'):
            shared.append(''.join(t.text or '' for t in si.iter(f'{NS}t')))
    sheet = [n for n in z.namelist() if re.match(r'xl/worksheets/sheet\d+\.xml', n)][0]
    root = ET.fromstring(z.read(sheet))
    out = []
    for row in root.iter(f'{NS}row'):
        cells, maxc = {}, 0
        for c in row.findall(f'{NS}c'):
            col = ''.join(ch for ch in c.get('r') if ch.isalpha())
            idx = 0
            for ch in col:
                idx = idx * 26 + ord(ch) - 64
            idx -= 1
            maxc = max(maxc, idx)
            v = c.find(f'{NS}v')
            if v is None:
                isv = c.find(f'{NS}is')
                val = ''.join(t.text or '' for t in isv.iter(f'{NS}t')) if isv is not None else ''
            elif c.get('t') == 's':
                val = shared[int(v.text)]
            else:
                val = v.text
            cells[idx] = val
        out.append([cells.get(i, '') for i in range(maxc + 1)])
    return out

def read_csv_rows(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.reader(f))

def rows_to_dicts(rows):
    hdr = rows[0]
    return [dict(zip(hdr, r + [''] * (len(hdr) - len(r)))) for r in rows[1:] if any(str(c).strip() for c in r)]

# ---------- stats helpers (stdlib) ----------
def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r

def spearman(xs, ys):
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx)
    vy = sum((b - my) ** 2 for b in ry)
    return cov / math.sqrt(vx * vy) if vx > 0 and vy > 0 else float('nan')

def cohen_kappa(a, b):
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    labels = set(ca) | set(cb)
    pe = sum((ca.get(l, 0) / n) * (cb.get(l, 0) / n) for l in labels)
    return (po - pe) / (1 - pe) if pe < 1 else float('nan'), po

def krippendorff_alpha_ordinal(r1, r2):
    # two raters, ordinal metric
    vals = sorted(set(r1) | set(r2))
    n = len(r1)
    pairs = list(zip(r1, r2))
    Do = sum((a - b) ** 2 for a, b in pairs) / n
    allv = r1 + r2
    N = len(allv)
    cnt = Counter(allv)
    De = sum(cnt[v1] * cnt[v2] * (v1 - v2) ** 2 for v1 in vals for v2 in vals) / (N * (N - 1))
    return 1 - Do / De if De > 0 else float('nan')

# ---------- load key + auto data ----------
key = {k: v for k, v in json.load(open(os.path.join(BASE, 'utility_variant_key.json'))).items()}
POINT_MAP = {'ldp': 'selective_ldp', 'placeholder': 'placeholder',
             'generalized': 'generalized', 'direct': 'direct'}
agg = {}
with open(os.path.join(RES, 'p37_semantic_u.jsonl')) as f:
    for line in f:
        d = json.loads(line)
        agg.setdefault((d['id'], d['point']), []).append(float(d['score']))
auto_u = {f"{iid}_{lbl}": sum(agg[(iid, POINT_MAP[v])]) / len(agg[(iid, POINT_MAP[v])])
          for (iid, lbl), v in
          ((rid.rsplit('_', 1), v) for rid, v in key.items())
          if (iid, POINT_MAP[v]) in agg}
# utility field per row: mean judge score for that (instance, point)
auto_u = {rid: u for rid, u in auto_u.items()}
auto_c = {}
auto_c_broad = {}
auto_items = {}
for line in open(os.path.join(BASE, '..', 'dataset', 'output', 'dr_sl_dataset_v2.jsonl')):
    d = json.loads(line)
    if d['split'] != 'test':
        continue
    ann = d['annotations']
    auto_c[d['id']] = 'y' if ann.get('combos') else 'n'
    auto_c_broad[d['id']] = 'y' if (ann.get('combos') or ann.get('explicit_identifiers')) else 'n'
    items = set()
    for e in ann.get('explicit_identifiers', []) + ann.get('quasi_identifiers', []):
        items.add((e['type'], e['value']))
    auto_items[d['id']] = items

# ---------- part 1: utility ----------
u1 = rows_to_dicts(read_csv_rows(os.path.join(BASE, 'utility_scoring_sheet1.csv')))
u2 = rows_to_dicts(read_xlsx(os.path.join(BASE, 'utility_scoring_sheet2.xlsx')))
s1 = {r['row_id']: float(r['score_0_or_0.5_or_1']) for r in u1 if r.get('score_0_or_0.5_or_1', '') != ''}
s2 = {r['row_id']: float(r['score_0_or_0.5_or_1']) for r in u2 if r.get('score_0_or_0.5_or_1', '') != ''}
common = sorted(set(s1) & set(s2) & set(auto_u))
print(f'utility rows: rater1={len(s1)} rater2={len(s2)} joined_with_auto={len(common)}')

human = {rid: (s1[rid] + s2[rid]) / 2 for rid in common}
auto = {rid: auto_u[rid] for rid in common}
variant_of = {rid: key[rid] for rid in common}

alpha_inter = krippendorff_alpha_ordinal([s1[r] for r in common], [s2[r] for r in common])
rho_all = spearman([human[r] for r in common], [auto[r] for r in common])

VARIANTS = ['direct', 'generalized', 'placeholder', 'ldp']
by_variant = {}
for v in VARIANTS:
    ids = [r for r in common if variant_of[r] == v]
    hm = sum(human[r] for r in ids) / len(ids)
    am = sum(auto[r] for r in ids) / len(ids)
    rho_v = spearman([human[r] for r in ids], [auto[r] for r in ids])
    by_variant[v] = dict(n=len(ids), human_mean=round(hm, 3), auto_mean=round(am, 3),
                         rho_within=round(rho_v, 3))
# operating-point level correlation (4 points)
pts_h = [by_variant[v]['human_mean'] for v in VARIANTS]
pts_a = [by_variant[v]['auto_mean'] for v in VARIANTS]
rho_points = spearman(pts_h, pts_a)

print('\n=== utility: human vs auto ===')
print(f'inter-rater Krippendorff alpha (ordinal): {alpha_inter:.3f}')
print(f'row-level Spearman rho (n={len(common)}): {rho_all:.3f}  [registered >= 0.8]')
print(f'operating-point rho (4 points): {rho_points:.3f}')
for v in VARIANTS:
    d = by_variant[v]
    print(f"  variant {v}: n={d['n']} human={d['human_mean']} auto={d['auto_mean']} rho_within={d['rho_within']}")

# ---------- part 2: annotation ----------
a1 = rows_to_dicts(read_csv_rows(os.path.join(BASE, 'annotation_sheet1.csv')))
a2 = rows_to_dicts(read_xlsx(os.path.join(BASE, 'annotation_sheet2.xlsx')))
def norm_y(x):
    return str(x).strip().lower()[:1]
c1 = {r['instance_id']: norm_y(r.get('combo_risk(y/n)', '')) for r in a1}
c2 = {r['instance_id']: norm_y(r.get('combo_risk(y/n)', '')) for r in a2}
common_c = sorted(set(c1) & set(c2) & set(auto_c))
common_c = [r for r in common_c if c1[r] in 'yn' and c2[r] in 'yn']
print(f'\nannotation rows: rater1={len(c1)} rater2={len(c2)} joined_with_auto={len(common_c)}')

auto_verdict = {r: auto_c[r] for r in common_c}
kappa_12, po_12 = cohen_kappa([c1[r] for r in common_c], [c2[r] for r in common_c])
kappa_1a, po_1a = cohen_kappa([c1[r] for r in common_c], [auto_verdict[r] for r in common_c])
kappa_2a, po_2a = cohen_kappa([c2[r] for r in common_c], [auto_verdict[r] for r in common_c])
agree = [r for r in common_c if c1[r] == c2[r]]
kappa_ca, po_ca = cohen_kappa([c1[r] for r in agree], [auto_verdict[r] for r in agree]) if agree else (float('nan'), float('nan'))
disagree = [r for r in common_c if c1[r] != c2[r]]
# human positive rate vs auto hold rate
hp = sum(1 for r in common_c if c1[r] == 'y' or c2[r] == 'y') / len(common_c)
ah = sum(1 for r in common_c if auto_verdict[r] == 'y') / len(common_c)
print('\n=== annotation: human vs auto coupling judgement ===')
print(f'inter-rater kappa={kappa_12:.3f} (agree {po_12*100:.1f}%)')
print(f'rater1 vs auto kappa={kappa_1a:.3f} (agree {po_1a*100:.1f}%)')
print(f'rater2 vs auto kappa={kappa_2a:.3f} (agree {po_2a*100:.1f}%)')
print(f'consensus(n={len(agree)}) vs auto kappa={kappa_ca:.3f} (agree {po_ca*100:.1f}%)  [registered >= 0.8]')
print(f'human coupled-rate(any rater y)={hp*100:.1f}%  auto hold-rate={ah*100:.1f}%')
print('rater-disagreement rows:', disagree)

# ---------- part 2b: construct-matched gold + item-level recall/precision ----------
auto_b = {r: auto_c_broad[r] for r in common_c}
kappa_1b, po_1b = cohen_kappa([c1[r] for r in common_c], [auto_b[r] for r in common_c])
kappa_2b, po_2b = cohen_kappa([c2[r] for r in common_c], [auto_b[r] for r in common_c])
print('\n=== construct-matched gold (combos OR any explicit identifier) ===')
print(f'auto broad-gold y-rate={sum(1 for r in common_c if auto_b[r]=="y")/len(common_c)*100:.1f}%')
print(f'rater1 vs broad kappa={kappa_1b:.3f} (agree {po_1b*100:.1f}%)')
print(f'rater2 vs broad kappa={kappa_2b:.3f} (agree {po_2b*100:.1f}%)')

def parse_items(s):
    out = set()
    for part in re.split(r'[;；]', str(s)):
        part = part.strip()
        m = re.match(r'([A-Za-z_]+)\s*[=＝]\s*(.+)', part)
        if m:
            out.add((m.group(1).strip(), m.group(2).strip()))
    return out

items1 = {r['instance_id']: parse_items(r.get('sensitive_items(type=value;...)', '')) for r in a1}
items2 = {r['instance_id']: parse_items(r.get('sensitive_items(type=value；...)',
                                        r.get('sensitive_items(type=value;...)', ''))) for r in a2}

def rp(human_sets):
    tp = fp = fn = 0
    for r in common_c:
        gold_t = {t for t, v in auto_items[r]}
        gold_tv = auto_items[r]
        h_t = {t for t, v in human_sets[r]}
        h_tv = human_sets[r]
        tp += len(h_t & gold_t); fp += len(h_t - gold_t); fn += len(gold_t - h_t)
    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    return prec, rec

p1, r1_ = rp(items1); p2, r2_ = rp(items2)
print('\n=== item-level (type) vs auto gold ===')
print(f'rater1: precision={p1:.3f} recall={r1_:.3f}')
print(f'rater2: precision={p2:.3f} recall={r2_:.3f}')

out = dict(
    utility=dict(n=len(common), alpha_inter_rater=round(alpha_inter, 3),
                 rho_row_level=round(rho_all, 3), rho_operating_points=round(rho_points, 3),
                 by_variant=by_variant,
                 criterion='rho>=0.8', passed=bool(rho_all >= 0.8)),
    annotation=dict(n=len(common_c), kappa_inter_rater=round(kappa_12, 3),
                    kappa_rater1_auto=round(kappa_1a, 3), kappa_rater2_auto=round(kappa_2a, 3),
                    kappa_consensus_auto=round(kappa_ca, 3), n_consensus=len(agree),
                    human_coupled_rate=round(hp, 3), auto_hold_rate=round(ah, 3),
                    disagreement_rows=disagree,
                    criterion='kappa>=0.8', passed=bool(kappa_ca >= 0.8),
                    broad_gold=dict(kappa_rater1=round(kappa_1b, 3), kappa_rater2=round(kappa_2b, 3),
                                    y_rate=round(sum(1 for r in common_c if auto_b[r] == 'y') / len(common_c), 3)),
                    item_level=dict(rater1=dict(precision=round(p1, 3), recall=round(r1_, 3)),
                                    rater2=dict(precision=round(p2, 3), recall=round(r2_, 3)))),
)
with open(os.path.join(BASE, 'analysis_results.json'), 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print('\nwrote analysis_results.json')
