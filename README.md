# XDC Atlas

A map of the XDC Network ecosystem: tools, apps and services, developer guides and live RPC status, curated by [XDC Outpost](https://xdcoutpost.xyz/).

Live at **https://xdcoutpost.xyz/XDC_Atlas/**

## What's in it

- **Ecosystem**: tools, apps and services for XDC (community-built, official and third-party), filterable by category and builder.
- **Reading**: developer docs, tutorials and references from across the XDC ecosystem, with older material marked as archived. To add one, open a pull request adding an entry to `data/articles.json` (`title`, `url`, `section`, `source`, `author`, `archived`).
- **Network status**: a live check of the public XDC RPC endpoints, run from the visitor's browser.

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

## Logos

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
