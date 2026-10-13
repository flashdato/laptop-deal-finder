#!/usr/bin/env python3
"""Laptop Deal Finder on your PC.

Run:  python3 serve.py      (then open the address it prints, normally http://localhost:8770)

The page reads every scan CSV in this folder (and ../laptop-listings.csv) each time it loads,
and saves your ratings to ratings.csv and your statuses and notes to meta.json, all in this folder.
"""
import csv, glob, io, json, os, re, sys, threading, webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PORT = int(os.environ.get("PORT", "8770"))  # 8765 is used by the Facebook scan's save server
RATINGS = os.path.join(HERE, "ratings.csv")
META = os.path.join(HERE, "meta.json")
SKIP = {"ratings.csv"}
PHOTO_DIRS = [os.path.join(HERE, "photos"), os.path.join(ROOT, ".work", "photos")]


def scan_files():
    files = sorted(f for f in glob.glob(os.path.join(HERE, "*.csv")) if os.path.basename(f) not in SKIP)
    extra = os.path.join(ROOT, "laptop-listings.csv")
    if os.path.exists(extra):
        files.append(extra)
    return files


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def _norm_url(u):
    u = (u or "").strip()
    m = re.search(r"facebook\.com/marketplace/item/(\d+)", u)
    if m:
        return "fb:" + m.group(1)
    m = re.search(r"mymarket\.ge/(?:\w\w/)?pr/(\d+)", u)
    if m:
        return "mm:" + m.group(1)
    return u.split("#")[0].rstrip("/")


def _seller(s):
    return re.sub(r"\s*\(https?://[^)]*\)\s*$", "", s or "").strip().lower()


def _words(s):
    return re.sub(r"\W+", " ", (s or "").lower()).strip()


def _filled(r):
    return sum(1 for v in r.values() if (v or "").strip())


def _photo_id(r):
    """Same id the page uses for a listing's photo and its ratings key (localPhoto/rkey in index.html)."""
    m = re.findall(r"\d{5,}", r.get("url") or "")
    if not m:
        return ""
    src = (r.get("source") or "").lower()
    pre = "fb" if "facebook" in src or "facebook.com" in (r.get("url") or "") else (re.findall(r"[a-z]+", src) or ["web"])[0]
    return f"{pre}-{m[-1]}"


def merge_rows(rows):
    """Drop duplicate laptops across all the scan files.

    Two rows are the same laptop when they point at the same post (unless both name different models,
    like a lot of several laptops in one post, or a group search link shared by different sellers),
    or when one seller reposts the same laptop: same price and the same specs, or the same title and text.
    Of each set of duplicates the most complete row is kept, in the place of the first one.
    """
    rows = [r for r in rows if (r.get("title") or "").strip()]
    parent = list(range(len(rows)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    by_key = {}
    for i, r in enumerate(rows):
        url, seller, price = _norm_url(r.get("url")), _seller(r.get("seller") or r.get("seller_id")), (r.get("price") or "").strip()
        model = _words(r.get("model"))
        specs = _words(r.get("specs"))
        keys = []
        if url:
            is_post = url.startswith(("fb:", "mm:")) or "/search" not in url
            keys.append(("url", url, model if is_post else seller + "|" + model + "|" + _words(r.get("title"))))
        if seller and price:
            if len(specs) > 8 and not re.search(r"photo|unknown", specs):
                keys.append(("specs", seller, price, specs))
            keys.append(("text", seller, price, _words(r.get("title")), _words((r.get("description") or "").split(" | ")[0])))
        for k in keys:
            j = by_key.setdefault(k, i)
            if j != i:
                parent[find(i)] = find(j)
    on_post = {}
    for i, r in enumerate(rows):
        on_post.setdefault(_norm_url(r.get("url")), []).append(i)
    for url, ids in on_post.items():  # a row with no model joins the post's only other laptop
        for i in ids:
            if url and "/search" not in url and not _words(rows[i].get("model")):
                others = {find(j) for j in ids if j != i}
                if len(others) == 1:
                    parent[find(i)] = others.pop()
    groups = {}
    for i in range(len(rows)):
        groups.setdefault(find(i), []).append(i)
    out, pid_seen = [], {}
    for i in sorted(min(g) for g in groups.values()):
        g = groups[find(i)]
        best = dict(rows[max(g, key=lambda j: (_filled(rows[j]), -j))])
        pid = _photo_id(best)
        if pid:  # different laptops sharing one post get their own key for ratings and statuses
            n = pid_seen.get(pid, 0)
            pid_seen[pid] = n + 1
            if n:
                best["key"] = f"{pid}-{n + 1}"
        out.append(best)
    return out


def load_all():
    rows, used = [], []
    for f in scan_files():
        try:
            rows += read_csv(f)
            used.append(os.path.relpath(f, HERE))
        except Exception as e:
            print("Could not read", f, e, file=sys.stderr)
    meta = {}
    if os.path.exists(META):
        try:
            meta = json.load(open(META, encoding="utf-8"))
        except Exception:
            pass
    ratings = read_csv(RATINGS) if os.path.exists(RATINGS) else []
    return {"rows": merge_rows(rows), "files": used, "meta": meta, "ratings": ratings}


def write_atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(data)
    os.replace(tmp, path)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/listings":
            return self.send_json(load_all())
        if path.startswith("/photos/"):
            name = os.path.basename(path)
            for d in PHOTO_DIRS:
                f = os.path.join(d, name)
                if os.path.isfile(f):
                    data = open(f, "rb").read()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
            return self.send_error(404)
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8")
        if self.path == "/api/ratings":
            list(csv.reader(io.StringIO(body)))  # refuse anything that isn't CSV
            write_atomic(RATINGS, body)
            return self.send_json({"ok": True})
        if self.path == "/api/meta":
            write_atomic(META, json.dumps(json.loads(body), ensure_ascii=False, indent=1))
            return self.send_json({"ok": True})
        self.send_error(404)


if __name__ == "__main__":
    for port in range(PORT, PORT + 20):  # skip ports another program is already using
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    else:
        sys.exit(f"No free port between {PORT} and {PORT + 19}.")
    url = f"http://localhost:{port}/"
    print(f"Laptop Deal Finder: {url}  (Ctrl+C to stop)")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
