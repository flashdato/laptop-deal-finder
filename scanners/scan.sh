#!/bin/bash
# One read-only scan batch of all website sources, then rebuild laptop-listings.csv and report new damaged rows.
cd "/home/flash/Laptop Research/.work" || exit 1
export TMPDIR="/home/flash/Laptop Research/.tmp"
python3 -c "import json;json.dump([r['url'] for r in json.load(open('ranked.json')) if r['category'] in ('sale','parts') and r['fault']!='working'],open('prev_damaged.json','w'))"
node mm.js 2>&1 | tail -1
python3 -c "import json;json.dump([str(x['product_id']) for x in json.load(open('mm_all.json'))],open('ids.json','w'))"
node mmdet.js ids.json 2>&1 | tail -1
python3 ul.py 2>&1 | tail -1
node ss.js 2>&1 | tail -1
node minda2.js 2>&1 | tail -1
python3 build.py 2>&1 | tail -2
python3 - <<'PY'
import json
prev=set(json.load(open('prev_damaged.json')))
r=json.load(open('ranked.json'))
new=[x for x in r if x['category'] in ('sale','parts') and x['fault']!='working' and x['url'] not in prev]
print('NEW_DAMAGED', len(new))
for x in new: print('  %s | %s GEL | %s | %s | %s | %s' % (x['title'][:60], x['price'] or 'agreement', x['fault'], x['model'], x['phone'] or '-', x['url']))
PY
TMPDIR="/home/flash/Laptop Research/.tmp" python3 photos.py 2>&1 | tail -1
