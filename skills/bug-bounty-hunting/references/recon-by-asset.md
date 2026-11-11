# Recon by asset type

Load this when the scope contains more than one asset type, or when an agent is about to be assigned to
a mobile or source-code target and the prerequisite check has not been run.

## Web / API (URL, Domain, Wildcard)

- Fingerprint from headers, cookies, JS bundles, error pages. Identify the CDN/WAF first — a managed
  challenge is bot detection, not a verdict on the target: switch to the clearance-cookie route in
  `waf-walled-targets.md` rather than giving up on the asset or hammering it.
- Map endpoints from `robots.txt`, `sitemap.xml`, `/.well-known/*`, JS bundle strings, SSR JSON in the HTML,
  and `apple-app-site-association` (leaks app routes and OAuth clients).
- Find the real API base. GraphQL is usually `/api/graphql` or `/graphql`; probe introspection once and
  record the exact response. When introspection is off, the validation errors are the schema oracle —
  enumeration recipe and what *not* to report: `graphql-testing.md`.
- Measure CORS with an actual `Origin:` header and record the real `Access-Control-Allow-Origin` — never
  assume.

## Mobile (Play Store / App Store)

**Run the availability check before assigning an agent.** Confirm the APK is obtainable for that exact
package; an app that is not listed in any mirror turns a two-agent mobile plan into two agents re-trying
mirrors until their budget ends. If it is unavailable, say so and move the program to an asset that needs
no binary.

Then: get the APK, read `AndroidManifest.xml` (exported components, deep links, permissions),
`res/values/strings.xml`, network-security-config, hardcoded keys, WebView settings, Firebase config,
certificate pinning. Working download and decompile procedure on Windows: `mobile-apk-analysis.md`.

**iOS without an IPA:** fetch the AASA file, enumerate universal-link paths and custom schemes, pull OAuth
clients and deeplink parameters out of the web SSR payload. That alone yields testable hypotheses.

## Browser extension (Chrome, Edge, Firefox)

No account, no provisioning, and no proxy between the attacker and the defect: the attacker is a page
the victim visits. Get the bundle from the store's update endpoint rather than a mirror:

    https://clients2.google.com/service/update2/crx?response=redirect&prodversion=131.0&acceptformat=crx2,crx3&x=id%3D<extension-id>%26uc

The download begins with a `Cr24` header, so a plain `unzip` fails — slice at the first `PK\x03\x04`
and unzip the remainder, then record the file count and the version from the manifest.

Read the manifest before the code: `permissions`, `host_permissions`, `content_scripts.matches`,
`web_accessible_resources` (and whether it sets `use_dynamic_url`), `externally_connectable`, and
`content_security_policy`. A broad `matches` or a large permission list is a fact, not a finding — it
is consented at install time and pays nothing on its own.

**The reachability model decides everything.** Page script lives in the page's world and has no
`chrome.*` at all; a content script runs in an isolated world the page cannot read. So the only hops
that matter are the bridges: DOM data the page controls entering the extension's UI, a
`window.postMessage` listener that omits `event.origin`, an injected `web_accessible_resources` frame
whose parent-trust anchor is a query parameter the embedder supplies, and `externally_connectable`
accepting a foreign origin. Enumerate those four, then ask what the privileged side does with the
message — a service-worker `onMessage` handler that checks no `sender.id` is worth nothing until one
of the four gives the page a way to reach it.

Running it: load the unpacked directory into a Chrome started with its own `--user-data-dir` and
`--remote-debugging-port`, serve the malicious page locally (note: extension `matches` patterns often
exclude `localhost`, so use a hosts entry if the script does not inject), and read the effect back
over CDP — the network request the worker made, the storage write, the DOM in the extension's origin.
A finding here is a page-driven action with a captured artefact; a page that could already do the same
thing without the extension is the first defence a triager reaches for, so answer it before writing.

## Source code

Shallow clone, read the security-relevant crates/modules, prove reachability. Rank by "can a remote peer
trigger this": reachable panic > theoretical overflow > style issue.
