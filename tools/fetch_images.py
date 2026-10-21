"""Скачивает свободные иллюстрации из Википедии/Wikimedia Commons для МЭфира.
Для каждой статьи берётся её главное свободное изображение (pageimages, pilicense=free),
уменьшенная копия 400px и сведения об авторе и лицензии."""
import json, os, re, time, urllib.parse, urllib.request

UA = {"User-Agent": "MEfir-image-fetch/1.0 (https://github.com/Mirmontash/efir)"}
API = "https://en.wikipedia.org/w/api.php"

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def api(**p):
    p.update(format="json", formatversion="2")
    return json.loads(get(API + "?" + urllib.parse.urlencode(p)))

def clean(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()

items = json.load(open("tools/images.json"))
os.makedirs("img", exist_ok=True)
credits = {}
for slug, title in items.items():
    try:
        q = api(action="query", titles=title, prop="pageimages", piprop="thumbnail|name",
                pithumbsize=400, pilicense="free", redirects=1)
        page = q["query"]["pages"][0]
        thumb, name = page.get("thumbnail", {}).get("source"), page.get("pageimage")
        if not thumb or not name:
            print("no image:", slug, title); continue
        meta = api(action="query", titles="File:" + name, prop="imageinfo",
                   iiprop="extmetadata|url", redirects=1)["query"]["pages"][0]
        info = (meta.get("imageinfo") or [{}])[0]
        em = info.get("extmetadata", {})
        ext = os.path.splitext(urllib.parse.urlparse(thumb).path)[1].lower() or ".jpg"
        if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
            ext = ".jpg"
        fn = f"img/{slug}{ext}"
        open(fn, "wb").write(get(thumb))
        credits[slug] = {"file": fn, "title": page.get("title"), "name": name,
                         "page": info.get("descriptionurl", "https://commons.wikimedia.org/wiki/File:" + name),
                         "artist": clean(em.get("Artist", {}).get("value"))[:160],
                         "license": clean(em.get("LicenseShortName", {}).get("value")),
                         "desc": clean(em.get("ImageDescription", {}).get("value"))[:200]}
        print("ok:", slug, name)
        time.sleep(0.4)
    except Exception as e:
        print("fail:", slug, title, e)
json.dump(credits, open("img/credits.json", "w"), ensure_ascii=False, indent=1)
