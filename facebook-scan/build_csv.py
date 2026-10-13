"""Build facebook-listings.csv from Marketplace search cards + item page dumps.

Usage: python3 -I build_csv.py <out.csv> [limit]
"""
import csv, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
COLS = ['title', 'price', 'location', 'seller', 'phone', 'url', 'source',
        'description', 'fault', 'model', 'resale', 'image', 'category']

BUYER_RE = re.compile(r'ჩაბარებ|ვიბარებ|ჩავიბარებ|ვყიდულობ|შევიძენ|ვიყიდი|ჩაგვაბარ|куплю|скупка|выкуп|покупаю|we buy|buying|i buy|ყიდვა ', re.I)
PARTS_RE = re.compile(r'იშლება|ნაწილებად|ნაწილები|for parts|parts only|на запчаст|запчасти|разбор', re.I)

FAULT_PATTERNS = [
    (r'არ ირთვ|не включ|won.?t turn on|not turn(ing)? on|dead', 'does not turn on'),
    (r'ეკრან\S* (გატეხ|დაზიან|გაფუჭ)|გატეხილი ეკრან|cracked screen|broken screen|screen (is )?broken|разбит\S* экран|матриц', 'screen damaged'),
    (r'დედაპლატ|motherboard|материнск', 'motherboard issue'),
    (r'წყალ|water|залит|liquid', 'liquid damage'),
    (r'ბატარე\S* (სუსტ|მკვდ|გაფუჭ)|ელემენტი სუსტი|battery (is )?(weak|dead|bad)|аккумулятор', 'weak/dead battery'),
    (r'კლავიატურ\S* (არ|გაფუჭ|დაზიან)|keyboard (not|broken|issue)', 'keyboard issue'),
    (r'ტეცავ|hinge|петл', 'hinge issue'),
    (r'ვიდეობარათ\S* (გაფუჭ|არ)|gpu (dead|issue|problem)|no display|არ აჩვენებს', 'no display / GPU'),
    (r'ნაწილებად|for parts|на запчаст|parts only', 'for parts'),
    (r'ვინდოუს\S* გადასაყენ|windows (needs|reinstall)', 'needs Windows reinstall'),
    (r'დაზიან|გატეხ|გაფუჭ|broken|damaged|неисправ|сломан|дефект|დეფექტ|პრობლემ', 'damaged (see description)'),
]
MODEL_RE = re.compile(
    r'((?:thinkpad|ideapad|legion|yoga|elitebook|probook|pavilion|envy|omen|victus|spectre|zbook|'
    r'latitude|inspiron|vostro|xps|precision|alienware|zenbook|vivobook|rog\s*\w+|tuf\s*\w*|'
    r'aspire|nitro|predator|swift|travelmate|galaxy book|surface laptop|surface book|matebook|magicbook|'
    r'macbook\s*(?:air|pro)?|msi\s*\w+|razer blade|lg gram)[\w\s\-./]{0,18})', re.I)
SPEC_RE = re.compile(r'(?<![\w.])(i[3579][- ]?\d{3,5}\w*|i[3579][- ]\d+(?:th|ე)?|ryzen\s*\d\s*\w*|rtx\s*\d{4}\w*|gtx\s*\d{3,4}|m[1-4]\s*(?:pro|max)?|\d{1,2}\s*gb(?: ram)?|\d{3,4}\s*gb\s*ssd|\d\s*tb)', re.I)


def gel(price):
    m = re.sub(r'[^\d.]', '', price or '')
    if not m:
        return 0 if (price or '').lower().startswith('free') else None
    v = float(m)
    if price.startswith('$'):
        v *= 2.7
    elif price.startswith('€'):
        v *= 3.1
    return round(v)


def load_items():
    items = {}
    for f in sorted(glob.glob(os.path.join(HERE, 'raw', 'items*'))):
        t = open(f, encoding='utf-8').read()
        if t.startswith('### Result'):
            t = json.JSONDecoder().raw_decode(t[t.index('"'):])[0]
        for it in json.loads(t):
            items[it['id']] = it
    return items


def clean_desc(text, title):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    drop = {'Message', 'Details', 'See more', 'See less', 'Send seller a message', 'Send', title}
    lines = [l for l in lines if l not in drop and not re.match(r'^(GEL|\$|€)[\d,]+', l)]
    return ' '.join(lines)


def main():
    out = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    cards = {c['id']: c for c in json.load(open(os.path.join(HERE, 'cards.json'), encoding='utf-8'))}
    kinds = {c['id']: c['kind'] for c in json.load(open(os.path.join(HERE, 'laptops.json'), encoding='utf-8'))}
    items = load_items()
    rows = []
    for id_, it in items.items():
        c = cards.get(id_)
        if not c or it.get('err') or it.get('gone'):
            continue
        desc = clean_desc(it.get('text', ''), c['title'])
        blob = c['title'] + ' ' + desc
        if id_ not in kinds:
            continue
        if kinds[id_] == 'buyer' or BUYER_RE.search(c['title']):
            category = 'buyer'
        elif re.search(r'\b(?:tablet|monitor|iphone|ipad)\b|ტაბლეტ|მონიტორ', c['title'], re.I):
            continue
        elif PARTS_RE.search(blob):
            category = 'parts'
        else:
            category = 'sale'
        faults = []
        for pat, label in FAULT_PATTERNS:
            if re.search(pat, blob, re.I) and label not in faults:
                if label == 'damaged (see description)' and faults:
                    continue
                faults.append(label)
        if re.search(r'mac\s?book', blob, re.I) and any(f in faults for f in
                ('motherboard issue', 'liquid damage', 'does not turn on', 'no display / GPU', 'for parts')):
            continue  # Dato: skip Macs with serious faults
        m = MODEL_RE.search(c['title']) or MODEL_RE.search(desc)
        model = m.group(1).strip(' -/') if m else ''
        specs = []
        for s in SPEC_RE.findall(blob):
            s = s.strip()
            if s.lower() not in [x.lower() for x in specs]:
                specs.append(s)
        if specs:
            model = (model + ' | ' if model else '') + ', '.join(specs[:5])
        phones = re.findall(r'(?<!\d)(?:\+?995[\s-]?)?5\d{2}[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}(?!\d)', desc)
        seller = it.get('seller', '')
        if it.get('profile'):
            seller = f"{seller} ({it['profile']})" if seller else it['profile']
        p = gel(c['price'])
        rows.append({
            'title': c['title'],
            'price': '' if p is None else p,
            'location': c['loc'] or c['city'].title(),
            'seller': seller,
            'phone': ', '.join(dict.fromkeys(re.sub(r'[\s-]', '', x) for x in phones)),
            'url': f'https://www.facebook.com/marketplace/item/{id_}/',
            'source': 'Facebook Marketplace',
            'description': desc[:1200],
            'fault': '; '.join(faults),
            'model': model,
            'resale': '',
            'image': it.get('img', ''),
            'category': category,
        })
    # damaged first, then cheapest
    rows.sort(key=lambda r: (['sale', 'parts', 'buyer'].index(r['category']), not r['fault'], bool(re.search(r'mac\s?book', r['title'], re.I)), r['price'] if r['price'] != '' else 1e9))
    if limit:
        rows = rows[:limit]
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f'{len(rows)} rows -> {out}; with fault: {sum(1 for r in rows if r["fault"])}; with phone: {sum(1 for r in rows if r["phone"])}; categories: {dict((k, sum(r['category'] == k for r in rows)) for k in ('sale', 'parts', 'buyer'))}')


if __name__ == '__main__':
    main()
