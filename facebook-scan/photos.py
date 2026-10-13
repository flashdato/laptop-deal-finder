"""Download each fetched listing's photo -> ../deal-finder/photos/fb-<id>.jpg (max 480px wide)."""
import glob, io, json, os, sys, urllib.request
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'deal-finder', 'photos')
os.makedirs(OUT, exist_ok=True)
ok = skip = fail = 0
for f in sorted(glob.glob(os.path.join(HERE, 'raw', 'items*'))):
    t = open(f, encoding='utf-8').read()
    if t.startswith('### Result'):
        t = json.JSONDecoder().raw_decode(t[t.index('"'):])[0]
    for it in json.loads(t):
        dst = os.path.join(OUT, f"fb-{it['id']}.jpg")
        if not it.get('img') or os.path.exists(dst):
            skip += 1; continue
        try:
            req = urllib.request.Request(it['img'], headers={'User-Agent': 'Mozilla/5.0'})
            im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=20).read())).convert('RGB')
            if im.width > 480:
                im = im.resize((480, round(im.height * 480 / im.width)))
            im.save(dst, 'JPEG', quality=82); ok += 1
        except Exception as e:
            fail += 1; print('fail', it['id'], e, file=sys.stderr)
print(f'downloaded {ok}, skipped {skip}, failed {fail}')
