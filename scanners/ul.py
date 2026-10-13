"""Re-scan unlim.ge computer pages and fetch contacts for new laptop posts."""
import json, re, subprocess, time, os
W = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(W, 'ul')
def get(u): return subprocess.run(['curl', '-s', '-m', '25', '-A', 'Mozilla/5.0', u], capture_output=True, text=True).stdout
posts = {}
for i in range(1, 30):
    h = get('https://unlim.ge/en/search/computer?page=%d' % i)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    if not m: break
    ip = json.loads(m.group(1))['props']['pageProps']['initialPosts']
    for k in ('posts', 'vipPosts'):
        for p in ip['data'][k] or []: posts[p['id']] = p
    if not ip['meta'].get('hasNextPage'): break
    time.sleep(0.5)
old = {p['id']: p for p in json.load(open(os.path.join(D, 'ul_laptops.json')))} if os.path.exists(os.path.join(D, 'ul_laptops.json')) else {}
out = []
for p in posts.values():
    if 'laptops' not in p['categories']: continue
    if p['id'] in old and old[p['id']].get('contacts'):
        p['contacts'] = old[p['id']]['contacts']; p['url'] = old[p['id']]['url']
    else:
        p['url'] = 'https://unlim.ge/en/' + (p['slug'] if p.get('slug') else 'post/' + p['id'])
        mm = re.search(r'"contacts":(\{[^{}]*\})', get(p['url'])); p['contacts'] = json.loads(mm.group(1)) if mm else {}
        time.sleep(0.5)
    out.append(p)
json.dump(out, open(os.path.join(D, 'ul_laptops.json'), 'w'), ensure_ascii=False)
print('unlim laptops', len(out), 'new', len([p for p in out if p['id'] not in old]))
