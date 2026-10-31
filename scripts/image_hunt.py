#!/usr/bin/env python3
"""image_hunt.py - find the BEST photo for a subject, look at candidates, then pick.

get_image.py takes the first few hits of one query. For video quality you want to see many
candidates from many queries side by side and pick by eye. This tool:
  1. runs several Wikimedia Commons searches (+ optional category listing),
  2. keeps photos (not logos/maps), records size, licence, author, source page,
  3. downloads small thumbnails and tiles them into one numbered contact sheet,
  4. `--pick N` downloads the full-size original (long side capped) + writes the credit line.

Usage:
  python image_hunt.py --out <proj>/assets --name bca --q "Menara BCA" --q "Wisma BCA Jakarta" --cat "Bank_Central_Asia"
  python image_hunt.py --out <proj>/assets --name bca --pick 7

Writes <out>/_hunt_<name>.json (candidates) and <out>/_hunt_<name>.jpg (numbered sheet).
Licence is listed for every candidate - this tool does not filter by licence, so read the
list and clear anything that is not free (the 'licence' column says which).
For images NOT on Commons (press photos, company media kits, news agencies) put the file in
assets yourself and add its source to credits.json - see the skill's sourcing table.
"""
import argparse, json, os, re, subprocess, sys, urllib.parse, urllib.request

UA = {"User-Agent": "kirocrew-video-automation/1.0 (image hunt)"}
API = "https://commons.wikimedia.org/w/api.php"
FF = r"C:\ffmpeg\bin\ffmpeg.exe"


def get(url, raw=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
        b = r.read()
    return b if raw else json.loads(b)


def strip(h):
    return re.sub(r"<[^>]+>", "", h or "").strip()


def info_for(pages):
    out = []
    for pg in pages:
        ii = (pg.get("imageinfo") or [{}])[0]
        if not ii.get("url"):
            continue
        mime = ii.get("mime", "")
        if not mime.startswith("image/") or mime in ("image/svg+xml", "image/gif"):
            continue
        w, h = ii.get("width", 0), ii.get("height", 0)
        if min(w, h) < 700:
            continue
        m = ii.get("extmetadata", {})
        out.append({"title": pg["title"], "url": ii["url"], "thumb": ii.get("thumburl"),
                    "w": w, "h": h, "licence": strip(m.get("LicenseShortName", {}).get("value")) or "?",
                    "author": strip(m.get("Artist", {}).get("value"))[:70] or "unknown",
                    "date": strip(m.get("DateTimeOriginal", {}).get("value"))[:10],
                    "page": ii.get("descriptionurl")})
    return out


def search(q, n=25):
    p = {"action": "query", "format": "json", "generator": "search", "gsrsearch": q + " filetype:bitmap",
         "gsrnamespace": 6, "gsrlimit": n, "prop": "imageinfo", "iiurlwidth": 360,
         "iiprop": "url|extmetadata|size|mime"}
    d = get(API + "?" + urllib.parse.urlencode(p))
    pages = sorted((d.get("query") or {}).get("pages", {}).values(), key=lambda x: x.get("index", 0))
    return info_for(pages)


def category(c, n=60):
    p = {"action": "query", "format": "json", "generator": "categorymembers", "gcmtitle": "Category:" + c,
         "gcmtype": "file", "gcmlimit": n, "prop": "imageinfo", "iiurlwidth": 360,
         "iiprop": "url|extmetadata|size|mime"}
    d = get(API + "?" + urllib.parse.urlencode(p))
    return info_for((d.get("query") or {}).get("pages", {}).values())


def sheet(cands, out, name):
    tdir = os.path.join(out, "_hunt_" + name)
    os.makedirs(tdir, exist_ok=True)
    files = []
    for i, c in enumerate(cands):
        p = os.path.join(tdir, "%02d.jpg" % i)
        try:
            open(p, "wb").write(get(c["thumb"], raw=True))
        except Exception:
            continue
        lab = os.path.join(tdir, "L%02d.jpg" % i)
        txt = ("%d  %dx%d  %s" % (i, c["w"], c["h"], c["licence"][:14])).replace(":", "\\:")
        subprocess.run([FF, "-y", "-i", p, "-vf", "scale=360:240:force_original_aspect_ratio=decrease,"
                        "pad=360:270:(ow-iw)/2:0:color=black,drawtext=text='%s':x=6:y=246:fontsize=17:fontcolor=white" % txt,
                        lab], capture_output=True)
        if os.path.exists(lab):
            files.append(lab)
    if not files:
        return None
    lst = os.path.join(tdir, "list.txt")
    open(lst, "w").write("".join("file '%s'\n" % f.replace("\\", "/") for f in files))
    cols = 6
    rows = (len(files) + cols - 1) // cols
    dst = os.path.join(out, "_hunt_%s.jpg" % name)
    subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-vf",
                    "tile=%dx%d:padding=4:color=black" % (cols, rows), "-frames:v", "1", dst], capture_output=True)
    return dst


def pick(out, name, n):
    cands = json.load(open(os.path.join(out, "_hunt_%s.json" % name), encoding="utf-8"))
    c = cands[n]
    w = min(2400, max(c["w"], c["h"]))
    p = {"action": "query", "format": "json", "titles": c["title"], "prop": "imageinfo",
         "iiprop": "url", "iiurlwidth": w if c["w"] >= c["h"] else int(w * c["w"] / c["h"])}
    d = get(API + "?" + urllib.parse.urlencode(p))
    ii = list(d["query"]["pages"].values())[0]["imageinfo"][0]
    url = ii.get("thumburl") or ii["url"]
    dst = os.path.join(out, name + ".jpg")
    open(dst, "wb").write(get(url, raw=True))
    credit = "Photo: %s / Wikimedia Commons, %s" % (c["author"], c["licence"])
    cp = os.path.join(out, "credits.json")
    cr = json.load(open(cp, encoding="utf-8")) if os.path.exists(cp) else []
    cr = [x for x in cr if x.get("name") != name] + [{"name": name, "file": "assets/%s.jpg" % name,
          "credit": credit, "licence": c["licence"], "source_url": c["page"]}]
    json.dump(cr, open(cp, "w", encoding="utf-8"), indent=1)
    # older entries (get_image.py / get_footage.py) store author + licence, not a ready credit line
    def line(x):
        return x.get("credit") or "Photo: %s / Wikimedia Commons, %s" % (x.get("author", "unknown"), x.get("licence", "?"))
    open(os.path.join(out, "credits.js"), "w", encoding="utf-8").write(
        "window.__CREDITS = " + json.dumps({x["name"]: line(x) for x in cr}) + ";\n")
    print("saved", dst, "|", credit, "|", c["page"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--q", action="append", default=[]); ap.add_argument("--cat", action="append", default=[])
    ap.add_argument("--pick", type=int)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.pick is not None:
        return pick(a.out, a.name, a.pick)
    seen, cands = set(), []
    for q in a.q:
        for c in search(q):
            if c["title"] not in seen: seen.add(c["title"]); cands.append(c)
    for c0 in a.cat:
        for c in category(c0):
            if c["title"] not in seen: seen.add(c["title"]); cands.append(c)
    cands = cands[:36]
    json.dump(cands, open(os.path.join(a.out, "_hunt_%s.json" % a.name), "w", encoding="utf-8"), indent=1)
    for i, c in enumerate(cands):
        print("%2d  %5dx%-5d %-16s %-10s %s" % (i, c["w"], c["h"], c["licence"][:16], c["date"], c["title"][5:70]))
    print("sheet:", sheet(cands, a.out, a.name))


if __name__ == "__main__":
    main()
