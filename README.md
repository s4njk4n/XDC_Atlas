# XDC Atlas

A map of the XDC Network ecosystem: tools, apps and services, developer guides and live RPC status, curated by [XDC Outpost](https://xdcoutpost.xyz/).

Live at **https://xdcoutpost.xyz/XDC_Atlas/**

## What's in it

- **Ecosystem**: tools, apps and services for XDC (community-built, official and third-party), filterable by category and builder.
- **Reading**: developer docs, tutorials and references from across the XDC ecosystem, with older material marked as archived. To add one, open a pull request adding an entry to `data/articles.json` (`title`, `url`, `section`, `source`, `author`, `archived`).
- **Network status**: a live check of the public XDC RPC endpoints, run from the visitor's browser.

The page is plain HTML and JavaScript. All the content lives in three JSON files:

| File | What it holds |
|---|---|
| `data/tools.json` | Ecosystem cards and the category list |
| `data/articles.json` | Reading list, grouped into sections |
| `data/rpcs.json` | Public RPC endpoints to check |

Edit a JSON file, commit, and GitHub Pages republishes the page. No build step.

## Add your project

Open a pull request adding an entry to `data/tools.json`:

```json
{
  "id": "my-tool",
  "name": "My Tool",
  "by": "your-github-name",
  "byUrl": "https://github.com/your-github-name",
  "kind": "community",
  "category": "dev",
  "summary": "One or two sentences on what it does and who it's for.",
  "type": "web-app",
  "license": "MIT",
  "status": "active",
  "tags": ["rpc", "monitoring"],
  "links": { "app": "https://…", "repo": "https://github.com/…", "docs": "https://…", "demo": "https://…" },
  "tipAddress": "xdc…"
}
```

| Field | Values |
|---|---|
| `kind` | `community`, `official`, `third-party` |
| `category` | `node-ops`, `payments`, `everyday`, `dev`, `explorers`, `wallets` |
| `type` | `web-app`, `self-host`, `bot`, `library`, `service` |
| `status` | `active`, `in-development`, `archived` |
| `links` | Any of `app`, `repo`, `docs`, `demo`. The first one becomes the main button. |
| `tipAddress` | Optional. Shown on your card so people can tip you directly. XDC Atlas never holds funds. |

Listings are only accepted by pull request.

**Claiming a listing:** if your tool is already here, add an `xdc-tool.json` with the same fields to the root of your own repo and open a PR setting `"claimed": true` on your entry.

## Weekly link check

`.github/workflows/check-links.yml` runs `scripts/check_links.py` every Wednesday. It checks the main link of every tool and every article:

- A link that fails two weeks in a row gets `"linkStatus": "dead"` and is hidden on the page (visitors can still see it by ticking **Show archived and unreachable**). It clears itself if the link comes back.
- Links that answer 401, 403 or 429 are listed as *blocked* but stay visible, because many sites refuse automated checkers while working fine in a browser.
- Results go to `data/link-report.json` and the Actions run summary.

You can also run it any time from the **Actions** tab (**Check links → Run workflow**).

## Logos

`.github/workflows/fetch-icons.yml` runs `scripts/fetch_icons.py`. For each card it visits the project's website once, picks its best icon (the high-resolution home-screen icon most sites publish, then the web app manifest, then the ordinary favicon), resizes it to 128×128 and saves it in `icons/`. The card's `"icon"` field then points at that file, so visitors' browsers only ever load images from this site.

- **First run:** open **Actions → Fetch icons → Run workflow**. It fetches icons for every card and commits them.
- **After that:** it runs weekly and only fetches icons for new cards. Tick **refresh all** when running it by hand to re-fetch everything.
- **Skipped:** XDC Outpost's own tools (beacon mark), official XinFin and XDC entries (XDC mark), and links to GitHub or app stores, which would only give the store's logo. Cards with no usable icon keep their coloured initials.
- **Your own logo:** put an image in `icons/`, set `"icon": "icons/your-file.png"` and add `"iconLocked": true` so the script never replaces it.

Logos belong to their owners and are shown only to identify each project. Projects can ask for theirs to be changed or removed by opening an issue.

## Disclaimer

Listings, guides and RPC endpoints are third-party and shown for discovery only. Inclusion is not an endorsement by XDC Outpost. Users are responsible for their own security.

## Submit an RPC endpoint

The RPC list in `data/rpcs.json` comes from Chainlist (synced weekly by `.github/workflows/sync-rpcs.yml`), the official XinFin tools guide, and pull requests. To add your own endpoint, open a pull request adding it to the right network:

```json
{
  "url": "https://your-node.example.com",
  "provider": "Your name or project",
  "privacy": "none",
  "source": "manual"
}
```

Your endpoint must be public with no API key, use `https://` or `wss://`, return the right chain ID (50 mainnet, 51 Apothem), and allow browser (CORS) requests. Set `privacy` to `none`, `limited` or `yes` to match how you treat request data.

Entries marked `"source": "manual"` are never removed by the weekly sync. Endpoints that stop answering for a long stretch may be removed by hand.

## License

MIT. Linked tools and articles are subject to their own authors' terms.
