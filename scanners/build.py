"""Merge mymarket / ss.ge / unlim.ge scrapes into laptop-listings.csv with fault/model/resale guesses."""
import csv, html, json, re, sys, os

W = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(W)
HEADER = ['title','price','location','seller','phone','url','source','description','fault','model','resale','image','category','specs','condition','price_source']
USD = 2.7

def clean(s):
    s = html.unescape(s or '')
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

# ---------- fault detection ----------
NEG = re.compile(r'(არ\s*აქვს|არანაირ|გარეშე|без\s|нет\s|no\s|without|zero|0\s)$', re.I)
FAULTS = [  # (label, serious, regex)
    ('for parts', True, r'ნაწილებ(ად|ში)|ნაწილად|на\s*запчаст|for\s*parts|parts\s*only|დასაშლელ'),
    ("won't turn on", True, r'(?<!კამერა, ვიდეოთვალი )(?<!ვიდეოთვალი )(?<!კამერა )არ\s*ირთვ|არ\s*ჩაირთ|не\s*включ|won.?t\s*turn|doesn.?t\s*turn\s*on|not\s*turn(ing)?\s*on|no\s*power|არ\s*იტვირთ'),
    ('no display', True, r'გამოსახულება\s*არ|ეკრანი\s*(არ\s*ანათებს|ჩამქრალ|შავი)|нет\s*изображ|no\s*(display|image|picture)|black\s*screen'),
    ('broken screen', True, r'(გატეხილი|გაბზარული|დაზიანებული|ჩამსხვრეული)\s*(ეკრან|დისპლე|მატრიც)|(ეკრან|დისპლე|მატრიც)\S*\s*(\S+\s*)?(გატეხ|გაბზარ|დაზიანებ|ზოლ|გაფუჭ)|ეკრანის\s*დაზიანებ|შლეიფ\S*\s*(გატეხ|დაზიან)|(dead|მკვდარი)\s*(pixel|პიქსელ)|разбит\S*\s*(экран|матриц)|(экран|матриц)\S*\s*(разбит|трещ|полос)|(broken|cracked|damaged)\s*(screen|display|lcd)|(screen|display)\s*(is\s*)?(broken|cracked|damaged)'),
    ('motherboard', True, r'ჩამრთველი\s*(\S+\s*)?გაფუჭ|დედაპლატ|материнск|motherboard\s*(issue|problem|dead|broken|fault)|mainboard'),
    ('liquid damage', True, r'წყლის\s*დაქცევ|წყალი\s*დაექცა|წყალ(ი|ში)\s*(ჩაესხა|ჩავარდ|დაესხა|მოხვდ)|დაისხა|ჩაესხა|залит|залил|water\s*damage|liquid(?!\s*metal)|spilled'),
    ('icloud/locked', True, r'icloud|activation\s*lock|ბლოკირებ|დაბლოკილ|bios\s*(password|lock)|заблокир'),
    ('gpu/chip', True, r'code\s*43|ვიდეოკარტ\S*.{0,60}არ\s*მუშაობს|ვიდეო\s*ბარათი\s*(არ|დაზიან|გაფუჭ)|видеокарт\S*\s*(не|сгор)|gpu\s*(dead|issue|problem|fault)'),
    ('battery', False, r'(ბატარეა|ბატარია|ელემენტი|ელემენტის|აკუმულატორ)\S*\s*(არ\s*(მუშაობს|იჭერს|ინახავს|უძლებს)|მკვდარ|გაბერილ|დაზიანებ|სუსტ)|გარდა\s*ბატარი|батаре\S*\s*(не|умер|слаб|вздут)|battery\s*(dead|not|bad|weak|swollen|needs)|(dead|bad|weak|swollen)\s*battery'),
    ('keyboard', False, r'კლავიატურ\S*\s*(აქვს\s*)?(არ\s|არ$|არმუშ|დაზიან|ზოგი|დეფექტ|გაფუჭ)|გაფუჭებული\s*აქვს\s*კლავ|კლავიატურაზე\S*\s*(აქვს\s*)?დეფექტ|клавиатур\S*\s*(не\s|частично)|keyboard\s*(not\s|issue|broken|some\s*keys)|(broken|faulty)\s*keyboard|ღილაკ\S*\s*არ\s*მუშაობს|key\S*\s*(doesn.t|does\s*not|don.t)\s*work|(თაჩპად|თაჩფად)\S*.{0,25}არ\s*მუშაობს|არ\s*მუშაობს\s*(თაჩპად|თაჩფად)|touchpad\s*(is\s*)?not\s*working'),
    ('hinge/case', False, r'ანჯამ\S*\s*(\S+\s*)?(გატეხ|დაზიან|შეკეთ|მოტეხ|პრობლემ|ხარვეზ)|(შეკეთებულია|გატეხილია|დაზიანებულია)\s*ანჯამ|петл\S*\s*(сломан|трещ|люфт|отремонт)|(broken|cracked|loose|damaged|repaired)\s*hinge|hinge\s*(is\s*|was\s*)?(broken|cracked|loose|damaged|repaired)|issue\s*with\s*(the\s*)?(right|left)?\s*hinge|корпус\S*\s*(трещ|сломан|поврежд)|კორპუს\S*\s*(გატეხ|დაზიან|გაბზარ)|კორპუსის\s*დაზიანება'),
    ('charging port', False, r'(დამუხტვ|დატენვ|ზარიადკ)\S*\s*(არ|პრობლემ)|не\s*заряж|charg\w*\s*(port\s*)?(issue|problem|not|broken)|not\s*charging'),
    ('storage/ssd', False, r'(ssd|hdd|ვინჩესტერ|მყარი\s*დისკი)\S*\s*(გარეშე|არ\s*აქვს|დაზიან|გაფუჭ)|без\s*(ssd|hdd|диска|жесткого)|(no|without)\s*(ssd|hdd|storage|hard\s*drive)'),
    ('overheating', False, r'ხურდება|გადახურ|перегрев|греется|overheat'),
    ('damaged/defect', True, r'დაზიანებ|გატეხილ|დეფექტ|გაფუჭებ|არ\s*მუშაობს|უწესივრო|сломан|не\s*работа|неисправ|дефект|поврежд|broken|damaged|not\s*working|faulty|defect'),
]
FAULTS = [(l, s, re.compile(r, re.I)) for l, s, r in FAULTS]
GOOD = re.compile(r'(დაზიანებ|დეფექტ)\S*\s*(გარეშე|არ\s*აქვს)|არანაირი\s*(დაზიანება|დეფექტი|პრობლემა)|без\s*(дефект|поврежд|царап|проблем)|no\s*(damage|defects|issues|problems)|without\s*(damage|defects|issues)|no\s+(\w+\s+){0,3}defects|უნაკლო|no\s*(defects|scratches)|χωρίς|არ\s*აქვს\s*(დაზიანება|დეფექტი)', re.I)

PRENEG = re.compile(r'(\bnot|n.t|\bno|არ|არა|не|нет|без|არანაირი|never|zero)\s*$', re.I)
POSTNEG = re.compile(r'^\S*\s*(არ\s*(აქვს|ჰქონდა|არის|ემჩნევა)|გარეშე|არა|არ\b)', re.I)
SELF_NEG = {"won't turn on", 'no display', 'storage/ssd', 'battery', 'keyboard', 'charging port', 'gpu/chip'}

def faults(text):
    found = []
    for label, serious, rx in FAULTS:
        for m in rx.finditer(text):
            if label not in SELF_NEG:
                pre = text[max(0, m.start()-14):m.start()]
                if PRENEG.search(pre): continue
                if POSTNEG.search(text[m.end():m.end()+25]): continue
                if label == 'damaged/defect' and m.start() > 0 and text[m.start()-1] == 'უ': continue
                if GOOD.search(text[max(0, m.start()-25):m.end()+25]): continue
                if label == 'damaged/defect' and re.search(r'ვიზუალურ|კოსმეტიკ|cosmetic|косметич|ნაკაწრ|царап|scratch|signs\s*of\s*use|ხმარების\s*კვალ|მცირე|ფოტოზე\s*ჩანს|გარე', text[max(0, m.start()-40):m.end()+40], re.I): continue
            found.append((label, serious)); break
    labels = [l for l, _ in found]
    if 'damaged/defect' in labels and len(labels) > 1:
        found = [f for f in found if f[0] != 'damaged/defect']
    return found

# ---------- model / resale ----------
BRANDS = ['ThinkPad','IdeaPad','Legion','Yoga','LOQ','ThinkBook','Lenovo','MacBook Pro','MacBook Air','MacBook','HP Omen','Omen','Victus','Pavilion','EliteBook','ProBook','Envy','Spectre','ZBook','HP','Dell XPS','XPS','Latitude','Inspiron','Vostro','Precision','Alienware','G15','Dell','ROG','TUF','Zenbook','Vivobook','VivoBook','ExpertBook','Asus','Predator','Nitro','Aspire','Swift','Acer','Surface','MSI','Razer','Toshiba','Samsung','Huawei','MateBook','Xiaomi','Fujitsu','Gigabyte','Aorus','Sony','Vaio','Chromebook','Microsoft']
BRX = re.compile(r'\b(' + '|'.join(re.escape(b) for b in sorted(BRANDS, key=len, reverse=True)) + r')\b[\s\-]*([A-Za-z0-9\-]{0,12}(?:\s[0-9A-Za-z\-]{1,8})?)', re.I)

def model_of(title, brand):
    m = BRX.search(title)
    if m:
        s = (m.group(1) + ' ' + m.group(2)).strip()
        s = re.sub(r'\s+(laptop|notebook|gaming|for|with|in|and|ლეპტოპი|ნოუთბუქი)\b.*$', '', s, flags=re.I)
        if brand and brand.lower() not in s.lower() and brand.lower() not in ('apple', 'microsoft'):
            s = brand + ' ' + s
        return s.strip()[:40]
    return brand or ''

GPU_VAL = [(r'rtx\s*5090|rtx\s*4090', 5500), (r'rtx\s*5080|rtx\s*4080', 4200), (r'rtx\s*5070|rtx\s*4070', 3000), (r'rtx\s*5060|rtx\s*4060', 2400),
           (r'rtx\s*5050|rtx\s*4050', 1900), (r'rtx\s*3080', 2400), (r'rtx\s*3070', 2100), (r'rtx\s*3060', 1700), (r'rtx\s*3050', 1300),
           (r'rtx\s*2080', 1700), (r'rtx\s*2070', 1500), (r'rtx\s*2060', 1250), (r'gtx\s*1660', 1050), (r'gtx\s*1650', 900),
           (r'gtx\s*1070|gtx\s*1080', 950), (r'gtx\s*1060', 750), (r'gtx\s*1050', 600), (r'gtx\s*9[5-8]0|gtx\s*8\d0', 400)]
APPLE_VAL = [(r'\bm4\b', 3300), (r'\bm3\b', 2600), (r'\bm2\b', 2000), (r'\bm1\b', 1350), (r'201[0-5]', 400), (r'201[6-9]|2020', 700)]

def resale(text, brand):
    t = text.lower()
    if 'macbook' in t or (brand or '').lower() == 'apple':
        for rx, v in APPLE_VAL:
            if re.search(rx, t):
                if 'pro' in t and v > 700: v = int(v * 1.25)
                return v
        return None
    for rx, v in GPU_VAL:
        if re.search(rx, t): return v
    m = re.search(r'(?:i[3579]|core\s*i[3579])[\s\-]*(\d{4,5})[a-z]{0,2}\b', t)
    tier = re.search(r'i([3579])', t)
    if m and tier:
        num = m.group(1); gen = int(num[:2]) if (len(num) == 5 or (num[0] == '1' and num[1] in '01234')) else int(num[0])
        base = {2: 150, 3: 180, 4: 230, 5: 260, 6: 330, 7: 400, 8: 550, 10: 700, 11: 850, 12: 1050, 13: 1250, 14: 1450}.get(gen)
        if base:
            return int(base * {'3': .8, '5': 1, '7': 1.25, '9': 1.5}[tier.group(1)])
    m = re.search(r'ryzen\s*([3579])\s*(?:pro\s*)?(\d)(\d{3})', t)
    if m:
        base = {2: 450, 3: 550, 4: 750, 5: 900, 6: 1100, 7: 1200, 8: 1400}.get(int(m.group(2)))
        if base: return int(base * {'3': .8, '5': 1, '7': 1.2, '9': 1.45}[m.group(1)])
    m = re.search(r'\bi([3579])\s*(\d{1,2})\s*(?:th|st|nd|rd)?\s*gen', t)
    if m:
        base = {2: 150, 3: 180, 4: 230, 5: 260, 6: 330, 7: 400, 8: 550, 9: 600, 10: 700, 11: 850, 12: 1050, 13: 1250, 14: 1450}.get(int(m.group(2)))
        if base: return int(base * {'3': .8, '5': 1, '7': 1.25, '9': 1.5}[m.group(1)])
    if re.search(r'core\s*ultra\s*[579]', t): return 1800
    if re.search(r'celeron|pentium|atom|amd\s*a[46]|e1-', t): return 180
    return None

ACCESSORY = re.compile(r'^(ლეპტოპის|ნოუთბუქის|laptop|notebook)?\s*(ჩანთა|დამტენი|მაგიდა|სადგამი|ქულერი|bag|charger|adapter|stand|cooling|კლავიატურა|keyboard|ეკრანი|matrix|ბატარეა|battery|ram|ოპერატიული)\b', re.I)

rows = []

# ---------- mymarket ----------
locs = {l['loc_id']: l['title'].strip() for l in json.load(open(os.path.join(W, 'mm_locs.json')))['data']} if isinstance(json.load(open(os.path.join(W, 'mm_locs.json'))), dict) else {l['loc_id']: l['title'].strip() for l in json.load(open(os.path.join(W, 'mm_locs.json')))}
det = json.load(open(os.path.join(W, 'mm_details.json'))) if os.path.exists(os.path.join(W, 'mm_details.json')) else {}
for x in json.load(open(os.path.join(W, 'mm_all.json'))):
    pid = str(x['product_id']); d = det.get(pid, {})
    title = clean(x['title']); _a1, _a2 = clean(d.get('descr')), clean(x.get('descr')); descr = _a2 if len(_a2) >= len(_a1) else _a1
    price = float(x['price'] or 0) * (USD if x['currency_id'] == 1 else 1)
    phones = re.findall(r'(?<!\d)(?:\+?995\s?)?(5\d{2}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2})(?!\d)', title + ' ' + descr)
    phone = phones[0] if phones else (d.get('phone') or '')
    shop = (x.get('shop') or {}).get('title') if isinstance(x.get('shop'), dict) else None
    rows.append(dict(title=title, price=round(price), location=locs.get(x['loc_id'], ''), seller=(shop + ' (shop)') if shop else (x.get('username') or x.get('user') or ''),
                     phone=phone, url='https://www.mymarket.ge/en/pr/%s/' % pid, source='mymarket.ge', description=descr[:600],
                     brand=x.get('brand_title') or '', image=(x.get('photos') or [{}])[0].get('large', ''), shop=bool(x.get('shop_id')), date=x.get('order_date', ''),
                     usd=float(x['price'] or 0) if x['currency_id'] == 1 else None, attrs=d.get('attrs') or [], mm_model=d.get('model') or ''))

# ---------- ss.ge ----------
for x in json.load(open(os.path.join(W, 'ss_all.json'))):
    t = x.get('detail') or ''
    if not re.search(r'კომპიუტერული ტექნიკა\s*\n\s*(ლეპტოპები|ნოუთბუქები|Apple)', t):
        continue
    m = re.search(r'პროდუქტის აღწერა\n(.*?)\n(სპეციფიკაციები|similar)', t, re.S)
    descr = clean(m.group(1) if m else x.get('descr'))
    pr = re.sub(r'[^\d.]', '', x.get('price') or '')
    tel = next((h[4:] for h in x.get('tels') or []), '')
    seller = (x.get('user') or '').split('\n')[0]
    rows.append(dict(title=clean(x['title']), price=round(float(pr)) if pr else 0, location=x.get('loc') or '', seller=seller, phone=tel,
                     url=x['href'], source='ss.ge', description=descr[:600], brand='', image=x.get('image', ''), shop=False, date=x.get('date', '')))

# ---------- unlim.ge ----------
for x in json.load(open(os.path.join(W, 'ul', 'ul_laptops.json'))):
    c = x.get('contacts') or {}
    rows.append(dict(title=clean(x.get('nameEn') or x.get('nameGe')), price=round(x.get('gelPrice') or 0), location=(x.get('city') or '').title(),
                     seller=(x.get('user') or {}).get('name') or c.get('name') or '', phone=c.get('phone') or c.get('additionalPhone') or '',
                     url=x['url'], source='unlim.ge', description=clean((x.get('textEn') or '') + ' | ' + (x.get('textGe') or ''))[:600],
                     brand=((x.get('computersFilters') or {}).get('brand') or ''), image=(x.get('images') or [''])[0], shop=bool((x.get('user') or {}).get('isBusiness')), date=x.get('createdAt', '')[:10], cf=x.get('computersFilters') or {}))


# ---------- minda.city ----------
if os.path.exists(os.path.join(W, 'minda_all.json')):
    for x in json.load(open(os.path.join(W, 'minda_all.json'))):
        t = x.get('text') or ''
        if not re.search(r'Computers(Laptops and accessories|Apple Mac)', t) or 'Description' not in t: continue
        title = x.get('title') or ''
        if not title or 'Laptops and accessories' == title: continue
        m = re.search(r'\n([₾$])\s*([\d ]+)\nDescription', t)
        cur, amt = (m.group(1), float(m.group(2).replace(' ', ''))) if m else ('₾', 0)
        d = re.search(r'Description\n(.*?)\n(GENERAL|LOCATION)', t, re.S)
        seller = t.split(title, 2)[-1].strip().split('\n')[0] if t.count(title) >= 2 else ''
        cityname = re.search(r'\nCity\n([^\n]+)', t)
        ph = re.search(r'Phone\n(\+995[^\n]*)', t)
        state = re.search(r'\nState\n([^\n]+)', t)
        if state and state.group(1).strip().lower() == 'new': continue
        rows.append(dict(title=clean(title), price=round(amt * (USD if cur == '$' else 1)), location=cityname.group(1) if cityname else '', seller=seller,
                         phone=(ph.group(1).strip() + ' **') if ph else '', url=x['url'], source='minda.city', description=clean(d.group(1) if d else ''),
                         brand='', image=x.get('img') or '', shop=False, date='', usd=amt if cur == '$' else None))

# ---------- categorise + clean ----------
BUYER = re.compile(r'ჩაბარებ|ვიბარებ|ჩავიბარებ|ვყიდულობ|ვიყიდი|ვიყიდით|ვყიდულობთ|ნებისმიერ\s*მდგომარეობაში|куплю|скупк|покупаем|выкуп|we\s*buy|buying\s*(laptops|notebooks)|i\s*buy\s*laptops', re.I)
PARTS = re.compile(r'იშლება|ნაწილებ|ნაწილად|ნაწილები|დასაშლელ|for\s*parts|parts\s*only|на\s*запчаст|разбор|donor', re.I)
SERVICE = re.compile(r'შეკეთება\s*(ადგილზე|სწრაფად)|სერვის\s*ცენტრ|ნოუთბუქების\s*შეკეთება|ლეპტოპების\s*შეკეთება|ремонт\s*ноутбук|laptop\s*repair\s*service', re.I)
NONLAPTOP = re.compile(r'^\s*(ჩანთა|bag|დამტენი|charger|adapter|კომპიუტერი\s|desktop|სისტემური\s*ბლოკი|მონიტორი|monitor|iphone|ტელეფონი|პლანშეტი|ipad|tablet|мышь|mouse|black\s*ikea|desk|dexp\s*h-|наушник|headset)\b', re.I)
SINGLEPART = re.compile(r'^\s*(ლეპტოპის|ნოუთბუქის|laptop|notebook)?\s*(ეკრანი|მატრიცა|დედაპლატა|კლავიატურა|ბატარეა|ელემენტი|კორპუსი|ქულერი|screen|display|motherboard|keyboard|battery|matrix|lcd|hinge|fan)\b', re.I)
CITIES = ['Tbilisi','Batumi','Kutaisi','Rustavi','Zugdidi','Gori','Poti','Telavi','Kobuleti','Zestaponi','Samtredia','Marneuli','Khashuri','Ozurgeti','Senaki','Akhaltsikhe','Mtskheta','Borjomi','Sagarejo','Gardabani','Kaspi','Chiatura','Tkibuli','Gurjaani','Lagodekhi']
CITY_KA = {'თბილისი':'Tbilisi','ბათუმი':'Batumi','ქუთაისი':'Kutaisi','რუსთავი':'Rustavi','ზუგდიდი':'Zugdidi','გორი':'Gori','ფოთი':'Poti','თელავი':'Telavi','ქობულეთი':'Kobuleti'}
FAULT_MAP = {'for parts':'unknown',"won't turn on":'nopower','no display':'nodisplay','broken screen':'screen','motherboard':'nopower','liquid damage':'liquid',
             'icloud/locked':'icloud','gpu/chip':'nodisplay','battery':'battery','keyboard':'keyboard','hinge/case':'hinge','charging port':'nopower',
             'storage/ssd':'storage','overheating':'overheat','damaged/defect':'unknown'}
FAULT_PRI = ['liquid','nopower','nodisplay','screen','icloud','bios','keyboard','hinge','storage','battery','overheat','unknown']
NORM = [  # (regex on lower text, canonical prefix)
    (r'x1\s*yoga', 'Lenovo ThinkPad X1 Yoga'), (r'x1\s*carbon', 'Lenovo ThinkPad X1 Carbon'), (r'pro\s*art', 'Asus ProArt'), (r'thinkpad', 'Lenovo ThinkPad'), (r'ideapad', 'Lenovo IdeaPad'), (r'legion', 'Lenovo Legion'), (r'\bloq\b', 'Lenovo LOQ'), (r'thinkbook', 'Lenovo ThinkBook'), (r'\byoga\b', 'Lenovo Yoga'),
    (r'elitebook', 'HP EliteBook'), (r'probook', 'HP ProBook'), (r'\bomen\b', 'HP Omen'), (r'victus', 'HP Victus'), (r'pavilion', 'HP Pavilion'), (r'\benvy\b', 'HP Envy'), (r'spectre', 'HP Spectre'), (r'zbook', 'HP ZBook'),
    (r'latitude', 'Dell Latitude'), (r'inspiron', 'Dell Inspiron'), (r'vostro', 'Dell Vostro'), (r'\bxps\b', 'Dell XPS'), (r'precision', 'Dell Precision'), (r'alienware', 'Alienware'),
    (r'\btuf\b', 'Asus TUF'), (r'zephyrus', 'Asus ROG Zephyrus'), (r'\bstrix\b', 'Asus ROG Strix'), (r'\brog\b', 'Asus ROG'), (r'zenbook', 'Asus Zenbook'), (r'vivobook', 'Asus VivoBook'), (r'expertbook', 'Asus ExpertBook'),
    (r'predator|helios', 'Acer Predator'), (r'\bnitro\b', 'Acer Nitro'), (r'aspire', 'Acer Aspire'), (r'\bswift\b', 'Acer Swift'),
    (r'macbook\s*pro', 'MacBook Pro'), (r'macbook\s*air', 'MacBook Air'), (r'macbook', 'MacBook'), (r'surface', 'Microsoft Surface'), (r'matebook', 'Huawei MateBook'),
    (r'katana', 'MSI Katana'), (r'\bmsi\b', 'MSI'), (r'razer|rezer', 'Razer Blade'), (r'aorus', 'Gigabyte Aorus'), (r'\bnuc\b', 'Intel NUC'),
]
BRAND_ONLY = {'lenovo':'Lenovo','hp':'HP','dell':'Dell','asus':'Asus','acer':'Acer','apple':'MacBook','msi':'MSI','toshiba':'Toshiba','samsung':'Samsung','huawei':'Huawei','xiaomi':'Xiaomi','fujitsu':'Fujitsu','microsoft':'Microsoft Surface','sony':'Sony Vaio','razer':'Razer Blade','gigabyte':'Gigabyte','honor':'Honor','alienware':'Alienware'}
KA_BRAND = {'ლენოვო':'lenovo','ასუს':'asus','ეისერ':'acer','დელ':'dell','მაკბუქ':'macbook'}

def norm_model(title, desc, brand):
    t = (title + ' ').lower()
    for ka, en in KA_BRAND.items(): t = t.replace(ka, en)
    full = t + ' ' + desc.lower()
    base = None
    for rx, name in NORM:
        m = re.search(rx, t) or re.search(rx, full[:200])
        if m:
            base = name
            rest = t[m.end():] if re.search(rx, t) else full[m.end():m.end()+30]
            if name.startswith('MacBook'):
                chip = re.search(r'\b(m[1-5])\s*(pro|max)?\b', full)
                yr = re.search(r'\b(20[01]\d|202[0-6])\b', full)
                return base + (' ' + chip.group(1).upper() + (' ' + chip.group(2).title() if chip.group(2) else '') if chip else (' ' + yr.group(1) if yr else ''))
            tok = re.match(r'[\s\-]*((?:[a-z]{0,3}\d[a-z0-9]*)(?:\s*(?:gen\s*\d+|g\d+))?)(?!-?\d{3,})', rest)
            if tok and not re.match(r'^(i[3579]|\d+gb|\d+\s*gb|ram|ssd)', tok.group(1)):
                base += ' ' + tok.group(1).upper().replace('GEN', 'Gen').strip()
            break
    if not base:
        b = (brand or '').lower()
        for k, v in BRAND_ONLY.items():
            if b == k or re.search(r'\b' + k + r'\b', t):
                base = v; break
    if not base: return ''
    gpu = re.search(r'(rtx|gtx)\s*-?\s*(\d{3,4})', full)
    if gpu and gpu.group(0).upper().replace(' ', '') not in base.replace(' ', ''):
        base += ' ' + gpu.group(1).upper() + ' ' + gpu.group(2)
    return re.sub(r'\s+', ' ', base).strip()

def city(loc, text):
    l = (loc or '').strip()
    for c in CITIES:
        if c.lower() in l.lower(): return c
    for ka, en in CITY_KA.items():
        if ka in l: return en
    return l.split(',')[0].strip().title() if l else ''

def phone9(p):
    d = re.sub(r'\D', '', p or '')
    if d.startswith('995'): d = d[3:]
    return d if re.fullmatch(r'5\d{8}', d) else ''


# ---------- specs / condition ----------
def _a(r, *names):
    for t, v, dim in r.get('attrs') or []:
        if t in names and v and v not in ('Not Included', 'No', 'None'):
            return (str(v) + (' ' + dim if dim and dim not in ('Inch',) else '')).strip()
    return ''

def get_specs(r, text):
    t = text
    cpu = ''
    m = re.search(r'\b(i[3579])[\s\-]*(\d{4,5}[a-z]{0,2})\b', t, re.I)
    if m: cpu = m.group(1).lower() + '-' + m.group(2).upper()
    if not cpu:
        m = re.search(r'ryzen\s*([3579])\s*(?:pro\s*)?(\d{4}[a-z]{0,2})', t, re.I)
        if m: cpu = 'Ryzen %s %s' % (m.group(1), m.group(2).upper())
    if not cpu:
        m = re.search(r'core\s*ultra\s*([579])\s*-?\s*(\d{3}[a-z]{0,2})?', t, re.I)
        if m: cpu = 'Core Ultra %s %s' % (m.group(1), (m.group(2) or '').upper())
    if not cpu:
        m = re.search(r'\b(m[1-5])\s*(pro|max)?\b', t, re.I)
        if m and 'mac' in t.lower(): cpu = 'Apple ' + m.group(1).upper() + (' ' + m.group(2).title() if m.group(2) else '')
    if not cpu:
        m = re.search(r'\b(celeron|pentium|atom)\s*([a-z]?\d{3,4}[a-z]?)?', t, re.I)
        if m: cpu = (m.group(1).title() + ' ' + (m.group(2) or '').upper()).strip()
    if not cpu:
        m = re.search(r'\b(i[3579])\b[^.\n]{0,25}?(\d{1,2})\s*(?:th|-?th)?\s*(?:gen|თაობ|покол)', t, re.I) or re.search(r'(\d{1,2})\s*(?:th\s*)?(?:gen|თაობის|поколени)[^.\n]{0,15}\b(i[3579])\b', t, re.I)
        if m:
            g = [x for x in m.groups()]; tier = [x for x in g if x.lower().startswith('i')][0]; gen = [x for x in g if x.isdigit()][0]
            cpu = '%s %sth gen' % (tier.lower(), gen)
    if not cpu and r.get('attrs'):
        pt, gen, fr = _a(r, 'Processor type'), _a(r, 'Processor Generation'), _a(r, 'Processor frequency')
        cpu = ' '.join(x for x in [pt, gen.replace(' Gen', 'th gen') if gen else '', fr] if x)
    if not cpu and r.get('cf'):
        cpu = r['cf'].get('cpu') or ''
    ram = ''
    m = re.search(r'(?:ram|ოპერატიული|оперативн\w*|memory)\s*(?:მეხსიერება)?\s*[:\-–]?\s*(\d{1,2})\s*gb', t, re.I) or re.search(r'\b(\d{1,2})\s*gb\s*(?:ram|ddr\d?|ოპერატიული|оператив)', t, re.I) or re.search(r'\b(4|8|12|16|20|24|32|64)\s*/\s*(?:128|256|512|1000|1\s*tb)', t, re.I)
    if m: ram = m.group(1) + 'GB'
    elif r.get('attrs') and _a(r, 'Memory (RAM)'): ram = _a(r, 'Memory (RAM)').replace(' ', '')
    elif r.get('cf', {}).get('ram'): ram = str(r['cf']['ram']).upper().replace(' ', '')
    sto = []
    for m in re.finditer(r'\b(\d{3,4}|[12])\s*(gb|tb|გბ|гб)\s*(nvme\s*)?(ssd|m\.?2|hdd|nvme|emmc)', t, re.I):
        sto.append('%s%s %s' % (m.group(1), m.group(2).upper().replace('ГБ', 'GB').replace('გბ', 'GB'), 'HDD' if m.group(4).lower() == 'hdd' else ('eMMC' if m.group(4).lower() == 'emmc' else 'SSD')))
    if not sto:
        m = re.search(r'(ssd|hdd|nvme)\s*[:\-–]?\s*(\d{3,4}|[12])\s*(gb|tb)', t, re.I)
        if m: sto.append('%s%s %s' % (m.group(2), m.group(3).upper(), 'HDD' if m.group(1).lower() == 'hdd' else 'SSD'))
    if not sto and r.get('attrs'):
        for name, kind in (('M2 SSD', 'SSD'), ('SSD Capacity', 'SSD'), ('HDD Capacity', 'HDD')):
            v = _a(r, name)
            if v and re.search(r'\d', v): sto.append(v.replace(' ', '') + ' ' + kind); break
    if not sto and r.get('cf', {}).get('diskSize'): sto.append('%s %s' % (r['cf']['diskSize'], (r['cf'].get('diskType') or '').upper()))
    gpu = ''
    m = re.search(r'\b(rtx|gtx|mx)\s*-?\s*(\d{3,4})\s*(ti|super)?', t, re.I)
    if m: gpu = ('%s %s %s' % (m.group(1).upper(), m.group(2), (m.group(3) or '').title())).strip()
    else:
        m = re.search(r'radeon\s*(rx\s*\d{3,4}m?|pro\s*\d{3,4}|vega\s*\d*)?', t, re.I)
        if m: gpu = ('Radeon ' + (m.group(1) or '')).strip().upper().replace('RADEON', 'Radeon')
        elif r.get('attrs') and _a(r, 'Videocard'): gpu = _a(r, 'Videocard') + (' graphics' if _a(r, 'Videocard') == 'Integrated' else '')
        elif r.get('cf', {}).get('gpu'): gpu = str(r['cf']['gpu'])
    scr = ''
    m = re.search(r'(1[0-8](?:[.,]\d)?)\s*(?:"|”|″|\'\'|´´|ინჩ|inch|in\b|дюйм|-inch)', t, re.I)
    if m: scr = m.group(1).replace(',', '.') + '"'
    elif r.get('attrs') and _a(r, 'Screen size'): scr = _a(r, 'Screen size') + '"'
    elif r.get('cf', {}).get('screenSize'): scr = str(r['cf']['screenSize']) + '"'
    res = re.search(r'\b(4k|uhd|qhd\+?|wqxga|2\.?5k|2k|fhd\+?|full\s*hd|hd\+?|retina|oled)\b|(\d{4})\s*[x×х*]\s*(\d{3,4})', t, re.I)
    if res:
        rs = res.group(1) or ('%sx%s' % (res.group(2), res.group(3)))
        rs = {'full hd': 'FHD', 'fullhd': 'FHD'}.get(rs.lower().replace('  ', ' '), rs.upper() if len(rs) < 6 else rs)
        scr = (scr + ' ' + rs).strip()
    elif r.get('attrs') and _a(r, 'Resolution'): scr = (scr + ' ' + re.sub(r'\s*\(.*', '', _a(r, 'Resolution'))).strip()
    hz = re.search(r'\b(\d{2,3})\s*(?:hz|ჰც|гц)', t, re.I)
    if hz and int(hz.group(1)) >= 90: scr += ' %sHz' % hz.group(1)
    parts = [cpu, ram, ' + '.join(dict.fromkeys(sto)), gpu, scr.strip()]
    return '; '.join(p if p else '?' for p in parts) if any(parts) else ''

FAULT_NOTE = {'screen': 'screen damage', 'nopower': "won't power on", 'nodisplay': 'no picture / GPU fault', 'liquid': 'liquid damage', 'keyboard': 'keyboard fault',
              'battery': 'battery worn/swollen', 'hinge': 'hinge or case damage', 'overheat': 'overheating', 'bios': 'BIOS lock/password', 'icloud': 'iCloud/activation lock',
              'storage': 'no or faulty storage', 'unknown': 'defect mentioned'}

def snippet(text, f):
    for label, _, rx in FAULTS:
        if label in [l for l, _ in f]:
            m = rx.search(text)
            if m:
                a = max(0, m.start() - 60); b = min(len(text), m.end() + 70)
                return ('…' if a else '') + text[a:b].strip() + ('…' if b < len(text) else '')
    return ''

def condition_of(cat, f, fault, text, agree):
    base = 'parts' if cat == 'parts' else ('damaged' if f else 'working') if cat == 'sale' else 'buyer ad'
    note = ''
    if f:
        labels = sorted({FAULT_MAP[l] for l, _ in f}, key=FAULT_PRI.index)
        note = ', '.join(FAULT_NOTE[l] for l in labels)
        sn = snippet(text, f)
        if sn: note += ' — "' + sn + '"'
    elif cat == 'sale':
        good = re.search(r'იდეალურ|კარგ\s*მდგომარეობ|ახალივით|отличн|хорош\w*\s*состоян|perfect|excellent|very\s*good|like\s*new', text, re.I)
        g0 = good.group(0) if good else ''
        note = ('seller says ' + ('ideal condition' if g0.startswith('იდეალ') else 'good condition' if g0.startswith('კარგ') else 'like new' if g0.startswith('ახალ') else g0.lower())) if good else 'no fault mentioned'
        if re.search(r'ნაკაწრ|царап|scratch', text, re.I): note += ', scratches'
    out = base + (': ' + note if note else '')
    if agree: out = 'price by agreement; ' + out
    return out

MODEL_CODE = re.compile(r'\b((?:[A-Z]{1,3}\d{2,4}[A-Z]{0,3}(?:-[A-Z0-9]{2,6})?)|(?:\d{2}-[a-z]{1,2}\d{3,4}[a-z]{0,3}))\b')
def model_code(t):
    for m in MODEL_CODE.finditer(t):
        c = m.group(1)
        if re.match(r'^(i[3579]|DDR\d|RTX|GTX|MX\d|SSD|HDD|USB|HDMI|RAM|FHD|UHD|IPS|LED|N\d{3,4}$|\d+GB|\d+TB)', c, re.I): continue
        if re.match(r'^[A-Z]{1,3}\d{2,4}', c) and not re.match(r'^(GB|TB|HZ)', c, re.I):
            return c
    return ''

OVERRIDES = {  # checked by hand from listing photos
    '36205259': {'model': 'Medion 2-in-1 convertible (exact model not shown; 15" touchscreen, Core i5 10th gen per spec table)'},
    '36314777': {'model': 'Lenovo IdeaPad 15" (Slim 3/5 class, Core i7 + Iris Xe stickers in photos, so 11th gen or newer; spec table says 7th gen)', 'fault': 'nopower'},
}
out, seen_url, seen_st = [], set(), set()
for r in rows:
    text = r['title'] + ' ' + r['description']
    if NONLAPTOP.search(r['title']) or SERVICE.search(text):
        continue
    if (BUYER.search(r['title']) or (BUYER.search(text) and not r['price'])) and not re.search(r'^(იყიდება|ვყიდი)', r['title'].strip()):
        cat = 'buyer'
    elif PARTS.search(text) or (SINGLEPART.search(r['title']) and not re.search(r'ლეპტოპი|ნოუთბუქი|laptop|notebook', r['title'][8:], re.I)):
        cat = 'parts'
    elif ACCESSORY.search(r['title']):
        continue
    else:
        cat = 'sale'
    f = faults(text)
    serious = any(s for _, s in f)
    is_mac = 'macbook' in text.lower() or r['brand'].lower() == 'apple'
    if is_mac and serious and cat == 'sale':
        continue  # Dato: drop MacBooks with serious faults
    if [l for l, _ in f] == ['damaged/defect'] and re.search(r'ვიზუალურ|კოსმეტიკ|cosmetic|косметич|ნაკაწრ|царап|scratch|signs\s*of\s*use|ხმარების\s*კვალ', text, re.I) and re.search(r'does\s*not\s*affect|გამართულ|მუშაობს\s*(გამართულად|იდეალურად|კარგად|ნორმალურად)|работает\s*(отлично|идеально|хорошо)|works\s*(perfectly|fine|well)|fully\s*functional|სრულად\s*ფუნქციონ', text, re.I):
        f = []; cosmetic = True
    else:
        cosmetic = False
    fk = sorted({FAULT_MAP[l] for l, _ in f}, key=FAULT_PRI.index)
    fault = fk[0] if fk else 'working'
    if fault == 'unknown' and 'bios' in text.lower() and 'password' in text.lower(): fault = 'bios'
    desc = r['description']
    notes = []
    if r.get('usd'): notes.append('(converted from $%g)' % r['usd'])
    raw_phone = r['phone']; ph = phone9(raw_phone)
    if not ph:
        mm = re.search(r'(?<!\d)(?:\+?995[\s\-]?)?(5\d{2}[\s\-]?\d{2,3}[\s\-]?\d{2,3}[\s\-]?\d{0,2})(?!\d)', text)
        if mm and len(re.sub(r'\D', '', mm.group(1))) == 9: ph = re.sub(r'\D', '', mm.group(1))
    if not ph and re.search(r'[*X]', raw_phone or ''):
        notes.append('phone partly hidden on site: %s (%s)' % (raw_phone.replace(' **', ''), 'full number needs login' if r['source'] == 'minda.city' else 'full number needs a captcha on the listing page'))
    if re.search(r'შეთანხმებით|negotiable|договорн', text, re.I): notes.append('price negotiable')
    if r['source'] == 'ss.ge' and not r['price']: notes.append('price on agreement')
    if cat == 'sale' and re.search(r'ნაწილ', text) and not PARTS.search(text): notes.append('(may be partly for parts)')
    if r['shop']: notes.append('(seller is a shop)')
    desc = re.sub(r'\s+', ' ', ' '.join(notes) + (' | ' if notes else '') + desc).strip()[:600]
    model = norm_model(r['title'], r['description'], r['brand'])
    code = model_code(r['title'] + ' ' + r['description'][:200])
    if model and code and code.lower() not in model.lower().replace(' ', '') and len(model.split()) <= 3 and not re.search(r'\d', model.split()[-1]):
        model = model + ' ' + code
    if not model or model.lower() == (r['brand'] or '').lower():
        b = model or BRAND_ONLY.get((r['brand'] or '').lower(), r['brand'] or '')
        if code and b: model = b + ' ' + code
        elif b and not model: model = b
    specs = get_specs(r, text)
    agree = (not r['price'] or int(r['price']) <= 5) or bool(re.search(r'შეთანხმებით|договорн', r['title']))
    rv = resale(text + ' ' + specs.replace('Intel Core ', ''), r['brand'])
    p = 0 if agree else int(r['price'] or 0)
    cond = condition_of(cat, f, fault, text, agree)
    if not f and re.search(r'ვიზუალურ\S*\s*(დეფექტ|დაზიან)|(დეფექტ|დაზიან)\S*\s*(\S+\s*)?ვიზუალურ|მცირე\s*(დეფექტ|დაზიან)|cosmetic|signs\s*of\s*use|ხმარების\s*კვალ', text, re.I): cosmetic = True
    if cosmetic: cond = cond.replace('no fault mentioned', 'cosmetic marks only, seller says it works fine')
    idm = re.search(r'/pr/(\d+)/', r['url'])
    if idm and int(idm.group(1)) < 30000000: cond += ' (old listing, first posted years ago; may be stale)'
    ov = OVERRIDES.get(r['url'].rstrip('/').split('/')[-1])
    if ov:
        model = ov.get('model', model); cond = ov.get('condition', cond); fault = ov.get('fault', fault)
    key = (r['seller'].strip().lower(), r['title'].strip().lower())
    if r['url'] in seen_url or (r['seller'] and key in seen_st): continue
    seen_url.add(r['url']); seen_st.add(key)
    score = 0
    if f: score += 50 + (20 if serious else 10)
    if rv and p > 0: score += min(60, 40 * rv / p)
    if p and p < 300: score += 10
    if p == 0: score -= 15
    if r['shop']: score -= 20
    if is_mac: score -= 15
    out.append(dict(title=r['title'], price=p if p > 0 else '', location=city(r['location'], text), seller=r['seller'], phone=ph, url=r['url'],
                    source=r['source'], description=desc, fault=fault, model=model, resale=rv or '', image=r['image'], category=cat,
                    score=round(score, 1), damaged=bool(f), specs=specs, condition=cond, est=rv, mac=is_mac))


# ---------- pricing ----------
import statistics
def mkey(m):
    m = (m or '').lower()
    m = re.sub(r'\s+(rtx|gtx)\s*\d+.*$', '', m)
    return m if len(m.split()) >= 2 and re.search(r'\d', m) else ''

# ---------- cross-site / repeat duplicates ----------
def pfx(r):
    if r['phone']: return r['phone']
    m = re.search(r'phone partly hidden on site: \+?(?:995\s*)?\(?(\d{3})\)?\s*(\d{2})', r['description'])
    return (m.group(1) + m.group(2)) if m else ''
def near(a, b):
    if not a['price'] or not b['price']: return a['price'] == b['price']
    return abs(a['price'] - b['price']) <= 0.15 * max(a['price'], b['price'])
drop = set()
for i, a in enumerate(out):
    if i in drop: continue
    for j in range(i + 1, len(out)):
        if j in drop: continue
        b = out[j]
        pa, pb = pfx(a), pfx(b)
        phone_ok = pa and pb and (pa.startswith(pb) or pb.startswith(pa))
        same_title = a['title'].strip().lower() == b['title'].strip().lower() and a['fault'] == b['fault']
        same_seller = a['seller'] and a['seller'].strip().lower() == b['seller'].strip().lower()
        gpu = lambda r: ((re.search(r'(rtx|gtx)\s*\d{4}', (r['model'] + ' ' + r['specs']).lower()) or [''])[0]).replace(' ', '') or None
        ta, tb = set(re.findall(r'[a-z0-9]{2,}', (a['title'] + ' ' + a['model']).lower())), set(re.findall(r'[a-z0-9]{2,}', (b['title'] + ' ' + b['model']).lower()))
        simt = len(ta & tb) / max(1, min(len(ta), len(tb)))
        same_kit = (mkey(a['model']) and mkey(a['model']) == mkey(b['model'])) or (gpu(a) and gpu(a) == gpu(b))
        mk = mkey(a['model']) and mkey(a['model']) == mkey(b['model'])
        shopish = '(seller is a shop)' in a['description'] or '(seller is a shop)' in b['description']
        cross = a['source'] != b['source']
        hit = (phone_ok and near(a, b) and (same_title or (mk and not shopish)))
        hit = hit or (same_title and a['fault'] == b['fault'] != 'working' and (same_seller or a['source'] == b['source'] == 'unlim.ge'))
        hit = hit or (cross and not shopish and near(a, b) and (same_seller or phone_ok) and (mk or simt >= 0.75 or (gpu(a) and gpu(a) == gpu(b))))
        if hit:
            keep, lose = (a, b) if (len(a['phone']) >= len(b['phone'])) else (b, a)
            keep['description'] = ('also listed at %s (%s GEL) | ' % (lose['url'], lose['price'] or 'by agreement') + keep['description'])[:600]
            if not keep['image']: keep['image'] = lose['image']
            drop.add(j if keep is a else i)
            if keep is b: break
out = [r for k, r in enumerate(out) if k not in drop]
print('merged duplicates', len(drop))

import statistics
def mkey(m):
    m = (m or '').lower()
    m = re.sub(r'\s+(rtx|gtx)\s*\d+.*$', '', m)
    return m if len(m.split()) >= 2 and re.search(r'\d', m) else ''
def skey(m):
    m = (m or '').lower(); m = re.sub(r'\s+(rtx|gtx)\s*\d+.*$', '', m)
    return m if len(m.split()) >= 2 else ''
sgroups = {}
for r in out:
    k = skey(r['model'])
    if k and r['category'] == 'sale' and r['fault'] == 'working' and r['price'] and r['price'] >= 80: sgroups.setdefault(k, []).append(r['price'])
groups = {}
for r in out:
    k = mkey(r['model'])
    if k and r['category'] == 'sale' and r['fault'] == 'working' and r['price'] and r['price'] >= 80 and '(seller is a shop)' not in r['description']:
        groups.setdefault(k, []).append((r['price'], r['source']))
stores = json.load(open(os.path.join(W, 'stores.json'))) if os.path.exists(os.path.join(W, 'stores.json')) else []
STOP = {'laptop', 'notebook', 'gaming', 'intel', 'core', 'amd', 'ryzen', 'gb', 'ssd', 'ram', 'free', 'dos', 'windows', 'apple', 'chip', 'cpu', 'gpu', 'gray', 'grey', 'silver', 'black', 'inch'}
def toks(s): return [t for t in re.findall(r'[a-z0-9]+', re.sub(r'\b[am]\d+\s*(pro|max)\b', ' ', (s or '').lower())) if t not in STOP]
def store_match(model, specs):
    mt = toks(model)
    if len(mt) < 2: return None
    best = None
    for it in stores:
        nt = set(toks(it['name']))
        if mt[0] not in nt and not (mt[0] == 'macbook' and 'macbook' in nt): continue
        hit = sum(1 for t in mt[1:] if t in nt)
        if hit == 0: continue
        same = hit == len(mt) - 1 and len(mt) >= 3
        sc = (2 if same else 1, hit, -float(it['price'] or 1e9))
        if not best or sc > best[0]: best = (sc, it, same)
    if not best or not best[1]['price']: return None
    return best[1], best[2]
cache = {}
WEB_PRICES = [  # looked up 13 Oct 2026, USD at 2.7 GEL
    (r'envy.*16-?h1059|envy laptop 16-h1059', 3000, 'about 3,000 GEL working: refurbished i9-13900H/RTX 4060 HP Envy 16 sold on eBay UK for GBP 1,589 (https://www.ebay.de/itm/156945382099); private used about $1,100'),
    (r'proart\s*p16|pro\s*art\s*p16|h7606', 3600, 'about 3,600 GEL working: certified pre-owned H7606WV $1,349.95 at Computer Overhauls (https://shop.computeroverhauls.com/products/16-asus-proart-p16-h7606wv-amd-ryzen-ai-9-hx-370-32gb-1tb-rtx-4060-touch)'),
    (r'fx505d', 1400, 'about 1,400 GEL working: used FX505DV (R7 3750H, RTX 2060) sold for $524.99 at PayMore (https://northraleighnc.paymore.com/products/asus-tuf-gaming-fx505d-15-6-ryzen-7-3750h-2-38ghz-16gb-1tb-ssd-geforce-rtx-2060-1788380541502-kvjqrc9kw)'),
    (r'a2179', 850, 'about 850 GEL working: eBay sold A2179 i5 8/256 at $288-350 (https://www.ebay.com/itm/296973735496)'),
    (r'k50ij|x53u|a52j|b50-30|np355v5c|c870|gnb1450|x200m|e145|g50-45|ideapad\s*100|80ku|სკოლის|hp\s*250|pavilion\s*x360|15-n030', 200, 'estimate: 2010-2016 entry laptop; working ones sell for 150-250 GEL on mymarket, parts value is lower'),
]
for r in out:
    k = mkey(r['model'])
    src = []
    resale_v = None
    g = groups.get(k, [])
    own = [p for p, _ in g]
    if r['category'] == 'sale' and r['fault'] == 'working' and r['price'] in own and len(own) > 1:
        own = own.copy(); own.remove(r['price'])
    if len(own) >= 2:
        med0 = statistics.median(own); own = [p for p in own if 0.5 * med0 <= p <= 2 * med0]
    if len(own) >= 2 and max(own) <= 2.2 * min(own):
        resale_v = int(statistics.median(own))
        src.append('resale: median of %d working %s listings of %s (%s)' % (len(own), '/'.join(sorted({s for _, s in g})), r['model'], ', '.join(str(p) for p in sorted(own)[:8])))
    elif r['est']:
        resale_v = r['est']
        src.append('resale: estimate from CPU/GPU tier (%s), no comparable working listings of this exact model found' % (r['specs'].split(';')[0] if r['specs'] else 'specs'))
    elif len(sgroups.get(skey(r['model']), [])) >= 3:
        sg = sgroups[skey(r['model'])]; resale_v = int(statistics.median(sg))
        src.append('resale: rough, median of %d working listings in the %s line (exact model not stated)' % (len(sg), r['model']))
    if not resale_v:
        tl = (r['model'] + ' ' + r['title'] + ' ' + r['description'][:200]).lower()
        for rx, v, why in WEB_PRICES:
            if re.search(rx, tl):
                resale_v = v; src.append('resale: ' + why); break
    if k not in cache: cache[k] = store_match(r['model'], r['specs']) if k else None
    sm = cache[k]
    if sm:
        it, same = sm
        src.append('new: %s %s GEL %s (%s%s)' % (it['store'], format(round(float(it['price'])), ','), it['url'], 'same model line: ' if same else 'closest current model: ', it['name'][:70]))
    r['resale'] = resale_v or ''
    r['price_source'] = '; '.join(src)
    pr = r['price'] or 0
    if resale_v and pr: r['score'] = round(r['score'] - (min(60, 40 * (r['est'] or 0) / pr) if r['est'] else 0) + min(60, 40 * resale_v / pr), 1)

# ---------- ratings from Dato (read only) ----------
ratings_path = os.path.join(P, 'deal-finder', 'ratings.csv')
liked, disliked = {}, {}
fault_scores, bad_urls = {}, set()
if os.path.exists(ratings_path):
    try:
        for rr in csv.DictReader(open(ratings_path, encoding='utf-8')):
            try: v = int(float(rr.get('rating') or 0))
            except ValueError: continue
            if v == 0: continue  # 0 = not rated
            mk = mkey(rr.get('model')) or (rr.get('model') or '').strip().lower()
            faults_r = [x.strip() for x in (rr.get('fault') or '').split(';') if x.strip()]
            for fk_ in faults_r: fault_scores.setdefault(fk_, []).append(v)
            if v >= 4:
                if mk: liked[('m', mk)] = liked.get(('m', mk), 0) + 1
                for fk_ in faults_r: liked[('f', fk_)] = liked.get(('f', fk_), 0) + 1
            elif v <= 2:
                bad_urls.add(rr.get('url'))
                if mk: disliked[('m', mk)] = disliked.get(('m', mk), 0) + 1
    except Exception as e:
        print('ratings read failed', e)
for fk_, vs in fault_scores.items():  # a whole fault class only drops after 3+ ratings averaging <= 2
    if len(vs) >= 3 and sum(vs) / len(vs) <= 2: disliked[('f', fk_)] = len(vs)
for r in out:
    mk = mkey(r['model']) or r['model'].strip().lower()
    adj = 40 * (('m', mk) in liked) + 25 * (('f', r['fault']) in liked)
    adj -= 40 * (('m', mk) in disliked) + 40 * (('f', r['fault']) in disliked) + 60 * (r['url'] in bad_urls)
    if r['fault'] == 'nopower' and re.search(r'thinkpad|elitebook|latitude|probook|vostro|expertbook|rtx|gtx|tuf|legion|nitro|rog|omen|victus|katana|loq', (r['model'] + ' ' + r['specs']).lower()):
        adj += 20  # Dato's best targets
    r['rating_adj'] = adj; r['score'] += adj
print('ratings: liked', liked, 'disliked', disliked)

def bucket(r):
    if r['category'] == 'sale' and r['fault'] != 'working': return 0
    if r['category'] == 'parts': return 1
    if r['category'] == 'sale': return 2
    return 3
out.sort(key=lambda r: (bucket(r), -r['score']))
with open(os.path.join(P, 'laptop-listings.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, HEADER, extrasaction='ignore'); w.writeheader(); w.writerows(out)
json.dump(out, open(os.path.join(W, 'ranked.json'), 'w'), ensure_ascii=False)
from collections import Counter
print('rows', len(out), Counter(r['source'] for r in out), Counter(r['category'] for r in out), Counter(r['fault'] for r in out))
