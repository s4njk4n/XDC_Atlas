#!/usr/bin/env python3
"""Refresh data/rpcs.json from Chainlist and ethereum-lists.

Run by .github/workflows/sync-rpcs.yml once a week, or by hand:
    python3 scripts/sync_rpcs.py

Endpoints already in data/rpcs.json keep their provider name and notes.
New endpoints found upstream are added with a provider name guessed from the host.
Endpoints that disappear upstream are kept but marked "source": "manual",
so nothing you added by hand is ever deleted.
"""
import json, re, urllib.request
from pathlib import Path
from urllib.parse import urlparse

DATA = Path(__file__).resolve().parent.parent / "data" / "rpcs.json"
CHAINLIST = "https://raw.githubusercontent.com/DefiLlama/chainlist/main/constants/extraRpcs.js"
ETH_LISTS = "https://raw.githubusercontent.com/ethereum-lists/chains/master/_data/chains/eip155-{}.json"

PROVIDERS = {
    "xinfin.network": "XinFin", "apothem.network": "XinFin", "xdc.org": "XDC Foundation",
    "xdc.network": "XDC Network", "xdcrpc.com": "xdcrpc.com", "plugin.global": "Plugin",
    "ankr.com": "Ankr", "tatum.io": "Tatum", "dwellir.com": "Dwellir", "drpc.org": "dRPC",
    "routeme.sh": "RouteMesh", "public-rpc.com": "public-rpc.com",
}

def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode()

def provider(url):
    host = urlparse(url).hostname or ""
    for dom, name in PROVIDERS.items():
        if host == dom or host.endswith("." + dom):
            return name
    return host

def norm(url):
    return url.rstrip("/")

def chainlist_entries(src, chain_id):
    m = re.search(r"\n\s*%d:\s*\{\s*rpcs:\s*\[(.*?)\]\s*,?\s*\}" % chain_id, src, re.S)
    if not m:
        return []
    out = []
    for obj in re.finditer(r'\{\s*url:\s*"([^"]+)"\s*,\s*tracking:\s*"([^"]+)"', m.group(1)):
        out.append((obj.group(1), obj.group(2)))
    body = re.sub(r"\{[^{}]*\}", "", m.group(1))
    out += [(u, "unspecified") for u in re.findall(r'"([^"]+)"', body)]
    return [(norm(u), t) for u, t in out if "${" not in u]

def main():
    data = json.loads(DATA.read_text())
    src = get(CHAINLIST)
    for net in data["networks"]:
        found = dict(chainlist_entries(src, net["chainId"]))
        try:
            for u in json.loads(get(ETH_LISTS.format(net["chainId"]))).get("rpc", []):
                if "${" not in u:
                    found.setdefault(norm(u), "unspecified")
        except Exception as e:
            print("ethereum-lists skipped:", e)
        existing = {norm(e["url"]): e for e in net["endpoints"]}
        for url, e in existing.items():
            if url in found:
                e["source"] = "chainlist"
                if found[url] != "unspecified":
                    e["privacy"] = found[url]
            elif e.get("source") == "chainlist":
                e["source"] = "manual"
        for url, tracking in found.items():
            if url not in existing:
                net["endpoints"].append({"url": url, "provider": provider(url),
                                         "privacy": tracking, "source": "chainlist"})
                print("added", url)
    DATA.write_text(json.dumps(data, indent=2) + "\n")

if __name__ == "__main__":
    main()
