# 11. Server Tool Paths

## Purpose

This note tells future agents where the browser and scraping tools live on the production server.

## Canonical production paths

- app runtime root: `/home/aicore/n8n-server`
- shared tool root: `/home/aicore/agent-tools`
- Firecrawl root: `/home/aicore/agent-tools/firecrawl`
- Firecrawl compat bridge: `/home/aicore/n8n-server/scripts/firecrawl_compat_bridge.py`
- Site Control Kit root: `/home/aicore/agent-tools/site-control-kit`
- Site Control Kit browser runtime: `/home/aicore/.local/share/site-control-kit-browser`
- Site Control Kit browser launcher: `/home/aicore/n8n-server/scripts/run_site_control_browser_client.sh`
- Site Control Kit hub env: `/etc/site-control-kit/hub.env`
- Site Control Kit browser timer: `/etc/systemd/system/site-control-kit-browser.timer`
- cosmetologist hunter env: `/home/aicore/n8n-server/.env.cosmetologist_hunter`

## Canonical localhost endpoints

- Firecrawl: `http://127.0.0.1:3002`
- Firecrawl Playwright service: `http://127.0.0.1:3003/scrape`
- Site Control Kit hub: `http://127.0.0.1:8765`
- Cosmetologist Hunter API: `http://127.0.0.1:8787`

## How the hunter should use them

Preferred fetch order:

1. Firecrawl
2. Site Control Kit browser bridge
3. direct `requests`

Reason:
- Firecrawl is the primary resilient HTML/render fetch layer.
- Site Control Kit is the browser fallback for pages that require a live browser session.
- direct `requests` stays as the cheapest fallback.

## Operational rule

Do not assume Site Control Kit is usable just because the hub service is running.
The hub still needs at least one connected browser client.
In production the browser client should start on demand for real parsing, with an optional low-frequency timer as a fallback.

Check tool status through:

`GET /tooling/status`

before assuming browser fallback is available.

## Recommended production client id

Use:

`client-cosmetologist-browser`


## Debug endpoint

Use:

`GET /debug/fetch-trace?limit=20`

It returns the last fetch attempts with the backend name and rejection reason.
