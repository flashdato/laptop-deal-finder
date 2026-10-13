"""Write analysis/price_in_<n>.json for analysed sale/parts listings not yet priced."""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, 'analysis')
size = int(sys.argv[1]) if len(sys.argv) > 1 else 55
done = set()
for f in glob.glob(os.path.join(A, 'price_in_*.json')):
    done.update(x['id'] for x in json.load(open(f, encoding='utf-8')))
todo = []
for f in sorted(glob.glob(os.path.join(A, 'out_*.json'))):
    for r in json.load(open(f, encoding='utf-8')):
        if r['category'] in ('sale', 'parts') and r['id'] not in done:
            todo.append({k: r.get(k) for k in ('id', 'model', 'specs', 'condition', 'fault', 'price_gel')})
todo.sort(key=lambda r: (r['model'] or '').lower())
n0 = len(glob.glob(os.path.join(A, 'price_in_*.json')))
for i in range(0, len(todo), size):
    json.dump(todo[i:i + size], open(os.path.join(A, f'price_in_{n0 + i // size}.json'), 'w'), ensure_ascii=False, indent=1)
print(len(todo), 'listings ->', (len(todo) + size - 1) // size, 'chunks from', n0)
