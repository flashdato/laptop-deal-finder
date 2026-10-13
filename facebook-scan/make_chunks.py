"""Write analysis/in_<n>.json chunks of fetched listings not yet chunked (for the model-reading pass)."""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
size = int(sys.argv[1]) if len(sys.argv) > 1 else 45
cards = {c['id']: c for c in json.load(open(os.path.join(HERE, 'laptops.json'), encoding='utf-8'))}
done = set()
for f in glob.glob(os.path.join(HERE, 'analysis', 'in_*.json')):
    done.update(x['id'] for x in json.load(open(f, encoding='utf-8')))
todo = []
for f in sorted(glob.glob(os.path.join(HERE, 'raw', 'items*'))):
    t = open(f, encoding='utf-8').read()
    if t.startswith('### Result'):
        t = json.JSONDecoder().raw_decode(t[t.index('"'):])[0]
    for it in json.loads(t):
        c = cards.get(it['id'])
        if not c or it['id'] in done or it.get('err') or it.get('gone'):
            continue
        txt = re.sub(r'\n(Message|Details|See more|See less)\n', '\n', it.get('text', ''))
        todo.append({'id': it['id'], 'title': c['title'], 'card_price': c['price'], 'location': c['loc'], 'page_text': txt})
        done.add(it['id'])
n0 = len(glob.glob(os.path.join(HERE, 'analysis', 'in_*.json')))
for i in range(0, len(todo), size):
    json.dump(todo[i:i + size], open(os.path.join(HERE, 'analysis', f'in_{n0 + i // size}.json'), 'w'), ensure_ascii=False, indent=1)
print(len(todo), 'listings in', (len(todo) + size - 1) // size, 'new chunks')
