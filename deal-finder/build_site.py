#!/usr/bin/env python3
"""Build the read-only online copy of the deal finder (what GitHub Pages serves).

Run:  python3 build_site.py [output folder]      (default: ../_site)

It writes index.html, scan.js (every listing with duplicates removed, plus your statuses, notes and ratings)
and the photos those listings use. Visitors can look around; what they change stays in their own browser.
"""
import datetime, json, os, shutil, sys

import serve

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(serve.ROOT, "_site"))


def main():
    data = serve.load_all()
    os.makedirs(os.path.join(OUT, "photos"), exist_ok=True)
    shutil.copy(os.path.join(serve.HERE, "index.html"), OUT)
    date = datetime.date.today().isoformat()
    with open(os.path.join(OUT, "scan.js"), "w", encoding="utf-8") as f:
        for name, value in [("SCAN", data["rows"]), ("SCAN_META", data["meta"]),
                            ("SCAN_RATINGS", data["ratings"]), ("SCAN_DATE", date)]:
            f.write(f"window.{name}={json.dumps(value, ensure_ascii=False)};\n")
    copied = 0
    for r in data["rows"]:
        pid = serve._photo_id(r)
        for d in serve.PHOTO_DIRS:
            src = os.path.join(d, pid + ".jpg")
            if pid and os.path.isfile(src):
                shutil.copy(src, os.path.join(OUT, "photos"))
                copied += 1
                break
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print(f"Built {OUT}: {len(data['rows'])} listings, {copied} photos.")


if __name__ == "__main__":
    main()
