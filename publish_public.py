#!/usr/bin/env python3
"""Make the public copy of this folder in public/ (its own git repo, pushed to GitHub as laptop-deal-finder).

Run:  python3 publish_public.py            (then: cd public && git add -A && git commit -m update && git push)

The public copy has the deal finder, the scanner code, your ratings, statuses and notes, and the photos.
Seller names, phone numbers and seller profile links are left out; listing links stay.
Raw scan dumps (json, html, logs), browser profiles and caches are never copied.
"""
import csv, glob, os, re, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "public")

PHONE = re.compile(r"(?:\+?995[\s-]?)?(?<!\d)5\d{2}(?:[\s-]?\d{2,3}){2,3}(?!\d)|\+?995[\s-]?5\d{2}(?:[\s-]?\d{2,3}){2,3}(?!\d)")
HIDDEN_PHONE = re.compile(r"phone partly hidden on site:[^|]*\|?\s*", re.I)


def no_phones(text):
    text = HIDDEN_PHONE.sub("", text or "")
    return PHONE.sub(lambda m: "[phone removed]" if len(re.sub(r"\D", "", m.group())) in (9, 12) else m.group(), text)


def clean_csv(src, dst):
    with open(src, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys()) if rows else []
    for r in rows:
        for c in cols:
            if c in ("seller", "phone"):
                r[c] = ""
            elif isinstance(r[c], str):
                r[c] = no_phones(r[c])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(OUT):  # start fresh, keep the public repo's git history
        if name != ".git":
            p = os.path.join(OUT, name)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)

    df = os.path.join(ROOT, "deal-finder")
    for f in ["index.html", "serve.py", "start.sh", "build_site.py", "ratings.csv", "meta.json"]:
        copy(os.path.join(df, f), os.path.join(OUT, "deal-finder", f))
    n = 0
    for f in glob.glob(os.path.join(df, "*.csv")):
        if os.path.basename(f) != "ratings.csv":
            n += clean_csv(f, os.path.join(OUT, "deal-finder", os.path.basename(f)))
    n += clean_csv(os.path.join(ROOT, "laptop-listings.csv"), os.path.join(OUT, "laptop-listings.csv"))
    # All photos in one place, so the online build finds them without the scan's work folder
    for d in [os.path.join(df, "photos"), os.path.join(ROOT, ".work", "photos")]:
        for f in glob.glob(os.path.join(d, "*.jpg")):
            copy(f, os.path.join(OUT, "deal-finder", "photos", os.path.basename(f)))
    # Scanner code only, no scraped data
    for pat in ["facebook-scan/*.py", "facebook-scan/*.js", "facebook-scan/analysis/*.md",
                ".work/*.py", ".work/*.js", ".work/*.sh", ".work/package.json", "publish_public.py"]:
        for f in glob.glob(os.path.join(ROOT, pat)):
            rel = os.path.relpath(f, ROOT).replace(".work/", "scanners/")
            copy(f, os.path.join(OUT, rel))
    for name in ["README.md", ".gitignore"]:
        src = os.path.join(ROOT, "public-template", name)
        if os.path.exists(src):
            copy(src, os.path.join(OUT, name))
    os.makedirs(os.path.join(OUT, ".github", "workflows"), exist_ok=True)
    copy(os.path.join(ROOT, "public-template", "pages.yml"), os.path.join(OUT, ".github", "workflows", "pages.yml"))
    print(f"Public copy in {OUT}: {n} listings with seller names and phones removed.")


if __name__ == "__main__":
    main()
