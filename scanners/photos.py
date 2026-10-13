"""Download listing photos (plain GET, 1s gaps), resize to <=480px wide JPEG q80."""
import io, json, os, re, sys, time, urllib.request
from PIL import Image
W = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(W, 'photos'); os.makedirs(OUT, exist_ok=True)
rows = json.load(open(os.path.join(W, sys.argv[2] if len(sys.argv) > 2 else 'ranked.json')))
n = int(sys.argv[1]) if len(sys.argv) > 1 else len(rows)
ok = 0
for r in [x for x in rows if x.get('category') in ('sale', 'parts')][:n]:
    if not r.get('image'): continue
    src = re.split(r'[ .]', r['source'])[0].lower()
    m = re.findall(r'\d{5,}', r['url']); pid = m[-1] if m else re.findall(r'[\w-]+', r['url'].rstrip('/'))[-1]
    fn = os.path.join(OUT, f'{src}-{pid}.jpg')
    if os.path.exists(fn): ok += 1; continue
    try:
        data = urllib.request.urlopen(urllib.request.Request(r['image'], headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).read()
        im = Image.open(io.BytesIO(data)).convert('RGB')
        if im.width > 480: im = im.resize((480, round(im.height * 480 / im.width)))
        im.save(fn, 'JPEG', quality=80); ok += 1
    except Exception as e:
        print('skip', r['url'], e)
    time.sleep(1)
print('photos', ok)
