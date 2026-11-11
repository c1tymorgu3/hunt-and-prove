# Targets behind a WAF managed challenge

For Cloudflare / Tencent EdgeOne / Akamai interstitials ("Just a moment", "Bir dakika lütfen", "Verifying the safety of the connection").

The interstitial is **bot detection, not an IP ban**. Request libraries and automation browsers get challenged on TLS/JA3 fingerprint and CDP (`navigator.webdriver`) signals even from a clean residential IP. A human passes it once; the resulting `cf_clearance` cookie is what the rest of the work rides on.

## Procedure

1. **Launch a visible Chrome the user can see and you can drive.** A dedicated profile keeps the clearance separate from their browsing:

```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:/Users/<user>/bb/chrome-prof" \
  --no-first-run --no-default-browser-check \
  --window-size=1280,900 "https://<target>/" &
```

Confirm it came up: `curl -s http://127.0.0.1:9222/json/version`.

2. **Ask the user to solve the challenge in that window** and say so plainly — one link, one action. Do not try to script the challenge, and do not ask for a cookie value in chat.

3. **Pull the cookies out over CDP** (`Network.getAllCookies`) and write them to a JSON file, together with `navigator.userAgent`.

4. **Replay them with a Chrome TLS fingerprint.** `curl_cffi` with `impersonate="chrome"` plus the exact UA string. `cf_clearance` is bound to IP + UA, so a mismatched UA invalidates it silently (you get the challenge HTML back with status 403).

5. **Refresh when it expires.** A 403 that returns HTML instead of JSON means the clearance lapsed — re-dump cookies from the same Chrome and restart the script (a module that reads the cookie file at import time will not see a refresh).

## Volume burns the address, clearance or not

Passing the challenge once is not permission to sweep. Edge reputation escalates on request rate: on one host roughly fifteen requests at about one per second moved it from "GETs reach the application" to a challenge on every path, with no change to the cookie or the UA. The address was spent for the rest of the session.

Practical consequences:
- Probe an unknown host with a handful of requests and read the responses before writing the sweep script. Ten careful requests tell you more than a hundred blind ones and cost nothing.
- Put the per-host request budget in every agent's brief. A child that enumerates 400 ids at one per second will lose the host for everyone else in the fan-out.
- When the host starts challenging, stop requesting it. Rotating the cookie cannot fix an IP-level reputation; only time or a different egress can.

## A uniform block is not a challenge

Distinguish the two before spending anything on a target:

- **Challenge**: an interstitial on some paths, a 200 or a real application response on others. A human solves it once and the clearance replays.
- **Allowlist or country filter**: every path, including `/` and `/robots.txt`, returns the same small block page with `server: cloudflare`, and `/cdn-cgi/trace` is the only thing that answers (it is served by the edge itself). There is no cookie to win — corporate and internal-style hosts are commonly restricted to an office range or a home country, and `sycamore` / `admin`-style consoles sitting on an in-scope row are exactly where this happens.

Run `/cdn-cgi/trace` first: if it answers and nothing else does, the target is unreachable from here, and the honest write-up is "edge-blocked, no surface observable", not "no vulnerabilities found".

## CDP gotchas

- **Websocket handshake 403.** `websocket.create_connection(...)` sends an `Origin` header that modern Chrome rejects: `Rejected an incoming WebSocket connection from the http://127.0.0.1:9222 origin`. Pass `suppress_origin=True` (or start Chrome with `--remote-allow-origins=*`).
- **Match the method the WAF allows.** It is normal for `GET /api/graphql` to return a 403 WAF page while `POST /api/graphql` returns 200 — a "blocked" result from one method says nothing about the other.
- **`TypeError: Failed to fetch` from page-context `fetch()`** often means the tab's document is a WAF error page, not a CORS problem. Check `document.title` and `document.body.innerText` for the tab before debugging CORS.
- **Run the client with the interpreter that has the package.** On hosts where `pip` and `python` resolve to different installs, `pip install curl_cffi` lands in one interpreter and the default `python` cannot import it — invoke the pip-owning interpreter's absolute path.

## Use the same browser to kill leads

A real browser session is also the fastest falsifier. A redirect/`client_id`/`redirect_uri` hypothesis that looks plausible in server-side reasoning dies in seconds when the page answers `Provided Client ID is not valid` — far cheaper than writing the report first and discovering it in triage.
