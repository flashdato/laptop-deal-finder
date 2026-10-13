"""Resale price from real Georgian comparables.

Comparables = working laptops for sale in ../laptop-listings.csv (mymarket.ge, ss.ge, unlim.ge, minda.city)
plus the analysed Facebook listings. For each Facebook listing: median price of the same model
(brand + series + number), else of the same CPU tier, else the earlier estimate (price_out_*.json).
Writes analysis/comps.json {id: {resale, price_source}}.
"""
import csv, glob, json, os, re, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, 'analysis')
STOP = {'laptop', 'notebook', 'model', 'unknown', 'not', 'stated', 'gen', 'generation', 'the', 'series', 'inch',
        'touch', 'touchscreen', '2-in-1', '2in1', 'x360', 'gaming', 'school', 'business', 'new', 'used'}
BAD_COND = re.compile(r'not working|for parts|broken|dead|damag|crack|არ ირთვ|ნაწილ', re.I)


def model_key(m):
    m = re.sub(r'\(.*?\)', ' ', (m or '').lower())
    toks = [t for t in re.findall(r'[a-z0-9]+(?:-[a-z0-9]+)?', m) if t not in STOP]
    if len(toks) < 2:
        return None, None
    k3 = ' '.join(toks[:3]) if len(toks) >= 3 and re.search(r'\d', ' '.join(toks[1:3])) else None
    return k3, ' '.join(toks[:2])


def cpu_tier(s):
    s = (s or '').lower()
    m = re.search(r'\bi([3579])[- ]?(\d{4,5})', s)
    if m:
        num = m.group(2)
        gen = num[:2] if num.startswith('1') and len(num) >= 4 else num[0]
        return f'i{m.group(1)} gen{gen}'
    m = re.search(r'\bi([3579])\b.{0,6}?(\d{1,2})(?:th|st|nd|rd|-?ე|\s*gen)', s) or re.search(r'(\d{1,2})(?:th|-?ე)\s*(?:gen|თაობ)?.{0,10}?\bi([3579])\b', s)
    if m:
        a, b = m.groups()
        return f'i{a} gen{b}' if len(a) == 1 and a in '3579' and not s[m.start():m.end()].startswith(a + 'th') else f'i{b} gen{a}'
    m = re.search(r'ryzen\s*([3579])\s*(?:pro\s*)?(\d)\d{3}', s)
    if m:
        return f'ryzen{m.group(1)} {m.group(2)}000'
    m = re.search(r'apple m([1-4])', s) or re.search(r'\bm([1-4])\b', s)
    if m and ('mac' in s or 'apple' in s):
        return f'apple m{m.group(1)}'
    if re.search(r'celeron|pentium|atom|athlon', s):
        return 'low-end'
    return None


comps = []  # (model_key3, model_key2, tier, price, source)
for r in csv.DictReader(open(os.path.join(HERE, '..', 'laptop-listings.csv'), encoding='utf-8')):
    try:
        p = float(r['price'])
    except ValueError:
        continue
    if r.get('category', 'sale') != 'sale' or p < 80 or p > 15000 or BAD_COND.search(r.get('condition', '') + ' ' + (r.get('fault') or '').replace('unknown', '')):
        continue
    k3, k2 = model_key(r.get('model'))
    comps.append((k3, k2, cpu_tier(r.get('specs', '') + ' ' + r.get('title', '')), p, r['source']))
fb = []
for f in sorted(glob.glob(os.path.join(A, 'out_*.json'))):
    fb += json.load(open(f, encoding='utf-8'))
for r in fb:
    p = r.get('price_gel')
    if r['category'] == 'sale' and p and 80 <= p <= 15000 and not r.get('fault'):
        k3, k2 = model_key(r.get('model'))
        comps.append((k3, k2, cpu_tier((r.get('specs') or '') + ' ' + (r.get('model') or '')), p, 'facebook'))

est = {}
for f in glob.glob(os.path.join(A, 'price_out_*.json')):
    for p in json.load(open(f, encoding='utf-8')):
        est[p['id']] = p


def summarize(ps, what):
    ps = sorted(x[3] for x in ps)
    srcs = sorted({x[4] for x in ps_list}) if False else None
    return round(statistics.median(ps) / 10) * 10, f'{len(ps)} listings {round(ps[0])}-{round(ps[-1])} GEL'


out = {}
stats = {'model': 0, 'series': 0, 'cpu': 0, 'estimate': 0, 'none': 0}
for r in fb:
    if r['category'] not in ('sale', 'parts'):
        continue
    k3, k2 = model_key(r.get('model'))
    tier = cpu_tier((r.get('specs') or '') + ' ' + (r.get('model') or ''))
    res = None
    for label, sel, need in (('model', lambda c: k3 and c[0] == k3, 2),
                             ('series', lambda c: k2 and tier and c[1] == k2 and c[2] == tier, 3),
                             ('cpu', lambda c: tier and c[2] == tier, 5)):
        if label == 'series' and not k2:
            continue
        m = [c for c in comps if sel(c)]
        # don't compare a listing only with itself
        if len(m) >= need:
            ps = sorted(c[3] for c in m)
            srcs = ', '.join(sorted({c[4] for c in m}))
            name = {'model': k3, 'series': f'{k2}' + (f' {tier}' if tier else ''), 'cpu': f'{tier} laptops'}[label]
            res = {'resale': int(round(statistics.median(ps) / 10) * 10),
                   'price_source': f'used: median of {len(ps)} Georgian listings for "{name}" ({srcs}), range {round(ps[0])}-{round(ps[-1])} GEL'}
            stats[label] += 1
            break
    if not res:
        e = est.get(r['id'])
        if e and e.get('resale'):
            res = {'resale': e['resale'], 'price_source': 'used: rough estimate, no Georgian comparables found; ' + (e.get('price_source') or '')}
            stats['estimate'] += 1
        else:
            res = {'resale': None, 'price_source': 'no estimate: model and specs not stated'}
            stats['none'] += 1
    e = est.get(r['id'], {})
    newp = re.search(r'new:[^;]*', e.get('price_source') or '')
    if newp and 'new:' not in res['price_source']:
        res['price_source'] += '; new: ' + re.sub(r'^(new:\s*)+', '', newp.group(0)).strip()
    out[r['id']] = res
json.dump(out, open(os.path.join(A, 'comps.json'), 'w'), ensure_ascii=False, indent=1)
print(len(comps), 'comparables;', stats)
