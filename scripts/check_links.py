#!/usr/bin/env python3
"""Check every link in data/tools.json and data/articles.json.

Run weekly by .github/workflows/check-links.yml, or by hand:
    python3 scripts/check_links.py

For each tool (its main link) and each article:
  - A link that fails on two runs in a row is marked "linkStatus": "dead".
    The page hides dead entries unless the visitor ticks "Show archived and unreachable".
  - A link that works again is cleared automatically.
  - 401, 403 and 429 answers are recorded as "blocked" but NOT hidden: many sites refuse
    automated checkers while working fine in a browser. Review these by hand.
A summary is written to data/link-report.json and to the GitHub Actions job summary.
"""
import json, os, ssl, socket, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS, ARTICLES, REPORT = ROOT / "data/tools.json", ROOT / "data/articles.json", ROOT / "data/link-report.json"
UA = "Mozilla/5.0 (compatible; XDC-Atlas-link-check; +https://xdcoutpost.xyz/XDC_Atlas/)"
BLOCKED = {401, 403, 429}


def check(url):
    if not url.startswith("http"):
        return url, "ok", None
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=25, context=ssl.create_default_context()) as r:
                return url, "ok", r.status
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (400, 403, 404, 405, 429, 500, 501):
                continue  # some servers reject HEAD; retry with GET
            return url, ("blocked" if e.code in BLOCKED else "dead"), e.code
        except (urllib.error.URLError, socket.timeout, ssl.SSLError, ConnectionError, OSError) as e:
            if method == "HEAD":
                continue
            return url, "dead", type(getattr(e, "reason", e)).__name__
    return url, "dead", None


def primary(t):
    L = t.get("links", {})
    return L.get("app") or L.get("repo") or L.get("demo") or L.get("docs")


def main():
    tools, arts = json.loads(TOOLS.read_text()), json.loads(ARTICLES.read_text())
    entries = [("tool", t, primary(t)) for t in tools["tools"]] + [("article", a, a["url"]) for a in arts["articles"]]
    urls = sorted({u for _, _, u in entries if u})
    with ThreadPoolExecutor(16) as pool:
        results = {u: (s, c) for u, s, c in pool.map(check, urls)}

    report = {"checked": datetime.now(timezone.utc).isoformat(timespec="seconds"), "dead": [], "blocked": []}
    for kind, item, url in entries:
        if not url:
            continue
        state, code = results[url]
        name = item.get("name") or item.get("title")
        if state == "dead":
            item["linkFails"] = item.get("linkFails", 0) + 1
            if item["linkFails"] >= 2:
                item["linkStatus"] = "dead"
            report["dead"].append({"type": kind, "name": name, "url": url, "error": code, "consecutiveFails": item["linkFails"]})
        else:
            item.pop("linkFails", None)
            item.pop("linkStatus", None)
            if state == "blocked":
                report["blocked"].append({"type": kind, "name": name, "url": url, "status": code})

    TOOLS.write_text(json.dumps(tools, indent=2, ensure_ascii=False) + "\n")
    ARTICLES.write_text(json.dumps(arts, indent=2, ensure_ascii=False) + "\n")
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    lines = [f"## Link check {report['checked']}", f"Checked {len(urls)} links.",
             f"**Failing:** {len(report['dead'])} (hidden after 2 failed runs)", f"**Blocked to bots:** {len(report['blocked'])} (still shown; check by hand)", ""]
    for r in report["dead"]:
        lines.append(f"- ❌ {r['name']} — {r['url']} ({r['error']}, fail #{r['consecutiveFails']})")
    for r in report["blocked"]:
        lines.append(f"- ⚠️ {r['name']} — {r['url']} ({r['status']})")
    out = "\n".join(lines)
    print(out)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        Path(os.environ["GITHUB_STEP_SUMMARY"]).write_text(out + "\n")


if __name__ == "__main__":
    main()
