#!/usr/bin/env python3
"""Fetch a logo for each tool card and store it in icons/.

Run by .github/workflows/fetch-icons.yml (weekly, or by hand from the Actions tab):
    python3 scripts/fetch_icons.py            # only cards that don't have an icon yet
    python3 scripts/fetch_icons.py --refresh  # re-fetch every card

For each card it visits the site's home page once and picks the best icon it offers:
  1. apple-touch-icon (usually a clean 180px square logo)
  2. the largest icon in the web app manifest
  3. the largest <link rel="icon"> on the page
  4. /apple-touch-icon.png, then /favicon.ico
Raster images are resized to 128x128 PNG (needs Pillow; without it they are saved as-is).
Cards with "iconLocked": true are never touched. Official XinFin/XDC entries, XDC Outpost's
own tools, and links to GitHub or app stores are skipped (they keep their built-in marks).
"""
import io, json, os, re, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "data/tools.json"
ICONS = ROOT / "icons"
UA = "Mozilla/5.0 (compatible; XDC-Atlas-icon-fetch; +https://xdcoutpost.xyz/XDC_Atlas/)"
OFFICIAL = re.compile(r"^(XinFin|XinFinOrg|XDC Network|XDC Foundation)$", re.I)
SKIP_HOSTS = {"github.com", "gitlab.com", "apps.apple.com", "play.google.com", "chrome.google.com",
              "chromewebstore.google.com", "medium.com", "www.npmjs.com", "t.me", "dappradar.com"}
MAX_BYTES = 1_000_000
IMAGE_TYPES = ("image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml",
               "image/x-icon", "image/vnd.microsoft.icon", "image/ico")

try:
    from PIL import Image
except ImportError:
    Image = None


def get(url, accept="*/*"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("too large")
        return r.geturl(), r.headers.get("Content-Type", "").split(";")[0].strip().lower(), data


class IconLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = []  # (rank, size, href)
        self.manifest = None

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        rel, href = a.get("rel", "").lower(), a.get("href", "")
        if not href:
            return
        size = max([int(n) for n in re.findall(r"(\d+)x\d+", a.get("sizes", ""))] or [0])
        if "apple-touch-icon" in rel:
            self.found.append((0, size or 180, href))
        elif "manifest" in rel:
            self.manifest = href
        elif "icon" in rel.split() or rel == "shortcut icon":
            self.found.append((2, size or (64 if href.endswith(".svg") else 16), href))


def candidates(site):
    """Return icon URLs for a site, best first."""
    final, ctype, html = get(site, "text/html")
    p = IconLinks()
    try:
        p.feed(html.decode("utf-8", "ignore"))
    except Exception:
        pass
    found = list(p.found)
    if p.manifest:
        try:
            murl = urljoin(final, p.manifest)
            _, _, m = get(murl, "application/json")
            for ic in json.loads(m).get("icons", []):
                size = max([int(n) for n in re.findall(r"(\d+)x\d+", ic.get("sizes", ""))] or [0])
                if ic.get("src"):
                    found.append((1, size, urljoin(murl, ic["src"])))
        except Exception:
            pass
    # Prefer rank (apple > manifest > icon), then sizes closest to 128-256
    found.sort(key=lambda x: (x[0], abs(min(x[1], 256) - 192)))
    urls = [urljoin(final, h) for _, _, h in found]
    origin = "{0.scheme}://{0.netloc}".format(urlparse(final))
    return urls + [origin + "/apple-touch-icon.png", origin + "/favicon.ico"]


def trim(img):
    """Crop transparent borders, then any solid border matching the corner colour (e.g. white padding)."""
    bb = img.getchannel("A").getbbox()
    if bb:
        img = img.crop(bb)
    px = img.load()
    w, h = img.size
    corner = px[0, 0]
    if corner[3] > 200 and all(px[x, y] == corner for x, y in ((w - 1, 0), (0, h - 1), (w - 1, h - 1))):
        bg = Image.new("RGBA", img.size, corner)
        from PIL import ImageChops
        diff = ImageChops.difference(img, bg).convert("L").point(lambda v: 255 if v > 24 else 0)
        bb = diff.getbbox()
        if bb and (bb[2] - bb[0]) * (bb[3] - bb[1]) > 0.15 * w * h:
            img = img.crop(bb)
    return img


def normalise(img, size=128, fill=0.86):
    """Trim padding and scale the logo to fill most of a square tile (small favicons are enlarged)."""
    img = trim(img.convert("RGBA"))
    target = int(size * fill)
    scale = target / max(img.size)
    new = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    img = img.resize(new, Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(img, ((size - img.width) // 2, (size - img.height) // 2), img)
    return canvas


def save(slug, ctype, data, url):
    ICONS.mkdir(exist_ok=True)
    is_svg = ctype == "image/svg+xml" or url.lower().split("?")[0].endswith(".svg")
    if is_svg:
        if b"<script" in data.lower():
            raise ValueError("svg contains script")
        path = ICONS / f"{slug}.svg"
        path.write_bytes(data)
        return path
    if Image:
        img = Image.open(io.BytesIO(data))
        if getattr(img, "n_frames", 1) > 1:
            img.seek(0)
        if img.format == "ICO" and hasattr(img, "ico"):
            sizes = sorted(img.ico.sizes(), key=lambda s: s[0])
            img = img.ico.getimage(sizes[-1])
        if min(img.size) < 16:
            raise ValueError("too small")
        path = ICONS / f"{slug}.png"
        normalise(img).save(path, "PNG", optimize=True)
        return path
    ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif"}.get(ctype, "ico")
    path = ICONS / f"{slug}.{ext}"
    path.write_bytes(data)
    return path


def fetch_for_site(site):
    slug = re.sub(r"[^a-z0-9]+", "-", urlparse(site).netloc.lower()).strip("-")
    try:
        urls = candidates(site)
    except Exception as e:
        return site, None, f"home page failed: {type(e).__name__}"
    best = None  # (score, ctype, data, final)
    seen = set()
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        try:
            final, ctype, data = get(u, "image/*")
            looks_svg = data.lstrip()[:5].lower() in (b"<svg ", b"<?xml") and b"<svg" in data[:500].lower()
            if ctype not in IMAGE_TYPES and not looks_svg and not ctype.startswith("image/"):
                continue
            if len(data) < 100:
                continue
            ctype = "image/svg+xml" if looks_svg else ctype
            score = 10_000 if ctype == "image/svg+xml" else pixel_size(data)
            if score and (best is None or score > best[0]):
                best = (score, ctype, data, final)
            if best and best[0] >= 180:
                break  # good enough; no need to keep downloading
        except Exception:
            continue
    if not best:
        return site, None, "no usable icon"
    try:
        path = save(slug, best[1], best[2], best[3])
    except Exception as e:
        return site, None, f"could not process icon: {type(e).__name__}"
    note = None if best[0] >= 64 else f"only a {best[0]}px icon was available"
    return site, path.relative_to(ROOT).as_posix(), note


def pixel_size(data):
    """Usable size of a raster icon: the smaller side after trimming transparent borders."""
    if not Image:
        return len(data) // 100
    try:
        img = Image.open(io.BytesIO(data))
        if img.format == "ICO" and hasattr(img, "ico"):
            img = img.ico.getimage(sorted(img.ico.sizes())[-1])
        img = img.convert("RGBA")
        bb = img.getchannel("A").getbbox() or (0, 0, *img.size)
        return min(bb[2] - bb[0], bb[3] - bb[1])
    except Exception:
        return 0


def site_for(t):
    L = t.get("links", {})
    url = L.get("app") or L.get("docs") or L.get("demo")
    if not url or not url.startswith("http"):
        return None
    host = urlparse(url).netloc.lower()
    if host in SKIP_HOSTS or host.endswith(".github.io"):
        return None
    return "{0.scheme}://{0.netloc}/".format(urlparse(url))


def main():
    refresh = "--refresh" in sys.argv
    data = json.loads(TOOLS.read_text())
    todo = {}
    for t in data["tools"]:
        if t.get("iconLocked") or t.get("by") == "s4njk4n" or OFFICIAL.match(t.get("by", "")):
            continue
        if t.get("icon") and not refresh and (ROOT / t["icon"]).exists():
            continue
        site = site_for(t)
        if site:
            todo.setdefault(site, []).append(t)

    with ThreadPoolExecutor(12) as pool:
        results = list(pool.map(fetch_for_site, sorted(todo)))

    got, failed, small = [], [], []
    for site, path, err in results:
        for t in todo[site]:
            if path:
                t["icon"] = path
                got.append(t["name"])
                if err:
                    small.append((t["name"], site, err))
            else:
                failed.append((t["name"], site, err))

    TOOLS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    lines = [f"## Icon fetch", f"Sites tried: {len(todo)}. Icons saved for {len(got)} cards. No icon for {len(failed)} cards (they keep initials).", ""]
    lines += [f"- ⚠️ {n} — {s} ({e})" for n, s, e in failed]
    if small:
        lines += ["", f"Low-resolution icons (enlarged, may look soft; consider a manual icon): {len(small)}"]
        lines += [f"- {n} — {s} ({e})" for n, s, e in small]
    out = "\n".join(lines)
    print(out)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        Path(os.environ["GITHUB_STEP_SUMMARY"]).write_text(out + "\n")


if __name__ == "__main__":
    main()
