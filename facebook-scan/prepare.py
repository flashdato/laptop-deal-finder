"""Merge raw search dumps -> cards.json, laptops.json; write next item batch script(s).

Usage: python3 -I prepare.py [batch_size]
"""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')

LAP = re.compile(r'laptop|leptop|notebook|ლეპტ|ლეფტ|ლევტ|ნოუთბუქ|ნოუტბუქ|ბუქი|ბუკი|ноутбук|thinkpad|thinkbook|elitebook|probook|latitude|inspiron|vostro|xps|pavilion|envy|spectre|omen|victus|ideapad|legion|yoga|zenbook|vivobook|rog|tuf|aspire|nitro|predator|swift|msi|katana|alienware|mac ?book|surface laptop|surface book|dell|lenovo|asus|acer|hp |toshiba|galaxy book|chromebook|matebook|magicbook|lg gram|razer blade|ირთვება', re.I)
BAD = re.compile(r'monitor|მონიტორ|charger|დამტენ|bag|ჩანთ|stand|სადგამ|mouse|მაუს|tablet|ტაბლეტ|პლანშეტ|ipad|iphone|printer|პრინტერ|cooler|ქულერ|cooling pad|desktop|სისტემური|playstation|xbox|ტელევიზ|კორპუს|surface pro|gaming pc|mini pc|ვიდეო ბარათ|video card|sleeve|ოპერატიულ|оперативн|ეკრანებ|ეკრანი\. იდეალ|wifi მოდული|მაკომპლექტ|all in one|კომპიუტერი$|კომპლექტი|screen extender|parts ans service', re.I)
BUYER = re.compile(r'ჩაბარებ|ვიბარებ|ჩავიბარებ|ვყიდულობ|შევიძენ|შეძენა|ამოყიდვა|ჩაგვაბარ|куплю|скупка|выкуп|покупаю|we buy|buying|buy a laptop', re.I)
FAULT = re.compile(r'broken|parts|not work|dead|crack|damag|დაზიან|ნაწილ|იშლება|გატეხ|გაფუჭ|არ ირთვ|არ მუშ|ირთვება მგონი|დეფექტ|პრობლემ|სუსტი|შესაკეთ|неисправ|запчаст|разбит|сломан|ремонт|no charger', re.I)


def gel(p):
    m = re.sub(r'[^\d.]', '', p or '')
    if not m:
        return 0 if (p or '').lower().startswith('free') else None
    v = float(m)
    return round(v * 2.7 if p.startswith('$') else v * 3.1 if p.startswith('€') else v)


def read_search(path):
    t = open(path, encoding='utf-8').read()
    if t.startswith('### Result'):
        t = json.JSONDecoder().raw_decode(t[t.index('"'):])[0]
    for line in t.split('\n'):
        p = line.split(' ;; ', 2)
        if len(p) < 3 or not p[2].strip():
            continue
        parts = [x.strip() for x in p[2].split('|')]
        prices = [x for x in parts if re.match(r'^(GEL|\$|€|Free)', x)]
        rest = [x for x in parts if x not in prices and x != 'Just listed']
        yield dict(id=p[0], city=p[1], price=prices[0] if prices else '', old=prices[1] if len(prices) > 1 else '',
                   title=rest[0] if rest else '', loc=rest[1] if len(rest) > 1 else '')


def fetched_ids():
    ids = set()
    for f in glob.glob(os.path.join(RAW, 'items*')):
        t = open(f, encoding='utf-8').read()
        ids.update(re.findall(r'\\?"id\\?":\s*\\?"(\d+)', t))
    return ids


def main():
    bs = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    cards = {}
    for f in sorted(glob.glob(os.path.join(RAW, 'search*.txt'))):
        for c in read_search(f):
            cards.setdefault(c['id'], c)
    rows = list(cards.values())
    laptops, buyers = [], []
    for r in rows:
        r['gel'] = gel(r['price'])
        t = r['title']
        if BUYER.search(t) and (LAP.search(t) or re.search(r'კომპიუტერ|техник|ტექნიკ', t, re.I)):
            r['kind'] = 'buyer'; buyers.append(r)
        elif LAP.search(t) and not BAD.search(t):
            r['kind'] = 'laptop'; r['faulty'] = bool(FAULT.search(t)); laptops.append(r)
    json.dump(rows, open(os.path.join(HERE, 'cards.json'), 'w'), ensure_ascii=False, indent=0)
    json.dump(laptops + buyers, open(os.path.join(HERE, 'laptops.json'), 'w'), ensure_ascii=False, indent=0)
    want = [r['id'] for r in buyers] + [r['id'] for r in laptops if r['faulty'] or (r['gel'] is not None and 20 <= r['gel'] <= 1500)]
    done = fetched_ids()
    todo = [i for i in want if i not in done]
    tpl = open(os.path.join(HERE, 'item_batch.tpl.js'), encoding='utf-8').read()
    for f in glob.glob(os.path.join(RAW, 'next*.js')):
        os.remove(f)
    n = 0
    for i in range(0, len(todo), bs):
        name = f'items_{len(done) + i}.json'
        open(os.path.join(RAW, f'next{n}.js'), 'w').write(tpl.replace('__IDS__', json.dumps(todo[i:i + bs])).replace('__NAME__', name))
        n += 1
    print(f'cards {len(rows)}, laptops {len(laptops)}, buyers {len(buyers)}, want {len(want)}, fetched {len(done & set(want))}, todo {len(todo)} in {n} batches')


main()
