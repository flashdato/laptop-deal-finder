"""Join analysed listings (+ prices when available) into deal-finder/facebook-listings.csv.

Usage: python3 -I final_csv.py [out.csv]
"""
import csv, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, 'analysis')
DF = os.path.join(HERE, '..', 'deal-finder')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DF, 'facebook-listings.csv')
COLS = ['title', 'price', 'location', 'seller', 'phone', 'url', 'source', 'description', 'fault', 'model',
        'resale', 'image', 'category', 'specs', 'condition', 'price_source']
SERIOUS = re.compile(r'motherboard|liquid|water|not turn|won.t turn|no power|dead|no display|no image|gpu|for parts', re.I)


def load_json_list(pattern):
    rows = []
    for f in sorted(glob.glob(pattern)):
        t = open(f, encoding='utf-8').read()
        if t.startswith('### Result'):
            t = json.JSONDecoder().raw_decode(t[t.index('"'):])[0]
        rows += json.loads(t)
    return rows


def clean_desc(text, title):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    drop = {'Message', 'Details', 'See more', 'See less', 'Send seller a message', 'Send', title}
    lines = [l for l in lines if l not in drop and not re.match(r'^(GEL|\$|€)[\d,]+', l)]
    return ' '.join(lines)


cards = {c['id']: c for c in json.load(open(os.path.join(HERE, 'cards.json'), encoding='utf-8'))}
items = {i['id']: i for i in load_json_list(os.path.join(HERE, 'raw', 'items*'))}
cf = os.path.join(A, 'comps.json')
prices = json.load(open(cf, encoding='utf-8')) if os.path.exists(cf) else {}
rows = []
for r in load_json_list(os.path.join(A, 'out_*.json')):
    if r['category'] == 'skip':
        continue
    c, it = cards.get(r['id'], {}), items.get(r['id'], {})
    is_mac = re.search(r'mac\s?book|apple', (r.get('model') or '') + c.get('title', ''), re.I)
    if is_mac and r['category'] != 'buyer' and SERIOUS.search((r.get('fault') or '') + ' ' + r['category']):
        continue  # Dato: no MacBooks with serious faults
    desc = clean_desc(it.get('text', ''), c.get('title', ''))
    phones = re.findall(r'(?<!\d)(?:\+?995[\s-]?)?5\d{2}[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}(?!\d)', desc)
    seller = it.get('seller', '')
    if it.get('profile'):
        seller = f"{seller} ({it['profile']})" if seller else it['profile']
    price = r.get('price_gel')
    if r['category'] == 'buyer' or price is None or price < 20:
        price = ''
    p = prices.get(r['id'], {})
    photo = f"photos/fb-{r['id']}.jpg"
    rows.append({
        'title': c.get('title', ''),
        'price': round(price) if price != '' else '',
        'location': c.get('loc') or c.get('city', '').title(),
        'seller': seller,
        'phone': ', '.join(dict.fromkeys(re.sub(r'[\s-]', '', x) for x in phones)),
        'url': f"https://www.facebook.com/marketplace/item/{r['id']}/",
        'source': 'Facebook Marketplace',
        'description': ((r.get('summary_ka') or '') + ' | ' + desc[:1500]).strip(' |'),
        'fault': r.get('fault') or '',
        'model': r.get('model') or '',
        'resale': p.get('resale') if p.get('resale') is not None else '',
        'image': photo if os.path.exists(os.path.join(DF, photo)) else it.get('img', ''),
        'category': r['category'],
        'specs': r.get('specs') or '',
        'condition': r.get('condition') or '',
        'price_source': p.get('price_source') or '',
    })
order = {'sale': 0, 'parts': 1, 'buyer': 2}
rows.sort(key=lambda x: (order[x['category']], x['price'] == '', x['price'] if x['price'] != '' else 0))
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
cnt = {k: sum(x['category'] == k for x in rows) for k in order}
print(f"{len(rows)} rows -> {OUT}: {cnt}; priced {sum(x['resale'] != '' for x in rows)}; "
      f"with fault {sum(bool(x['fault']) for x in rows)}; with phone {sum(bool(x['phone']) for x in rows)}; "
      f"no price {sum(x['price'] == '' for x in rows)}")
