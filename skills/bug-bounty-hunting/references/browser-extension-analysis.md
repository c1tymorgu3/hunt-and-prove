# Browser extensions as a bounty surface

The top rung of the surface ladder: the code runs on the victim's machine, the attacker is a web page the victim already visits, and nothing — no edge proxy, no API redaction, no tenant scoping — sits between the two. A page cannot read `chrome.storage` by itself, so any path that lets it do so is a real boundary crossing, and the payoff is a session token the vendor cannot mask.

## Get the artifact (no account)

Chromium stores accept a direct CRX download by extension id:

    https://clients2.google.com/service/update2/crx?response=redirect&prodversion=131.0&acceptformat=crx2,crx3&x=id%3D<EXTENSION_ID>%26uc

Firefox XPI is a plain zip. Edge uses the same Chromium format with its own store id.

The CRX carries a `Cr24` header, so `unzip` refuses it. Verify the magic, then slice at the first local-file header and unzip the remainder:

```python
import urllib.request
data = urllib.request.urlopen(url, timeout=60).read()
assert data[:4] == b"Cr24"
open("ext.zip", "wb").write(data[data.index(b"PK\x03\x04"):])
```

Record the byte size and the manifest version: they are what tells a triager you tested the shipped build.

## Read the manifest before the code

- `permissions` — `cookies`, `storage`, `declarativeNetRequest`, `webRequest` decide what the extension can touch.
- `content_scripts[].matches` — `*://*/*` means the script runs on every page, including the attacker's. That is a precondition, not a finding.
- `web_accessible_resources` — with `use_dynamic_url: true` a page cannot address the resource; without it, any page can load and frame it.
- `externally_connectable` — if present, web pages can message the extension directly. Its absence is why most extension findings die.
- `content_security_policy` — an `unsafe-eval` or remote-script allowance is worth chasing only if attacker data reaches the evaluated code.

## Hunt the boundary, not the file list

Two worlds: the content script runs beside the page, the service worker holds the privileges (`chrome.cookies`, cross-origin fetches, storage). The only finding is a path from page input into a privileged action. Enumerate the bridges, then test each:

1. A `window.postMessage` listener in an injected iframe — reachable if the frame is web-accessible and the listener skips `event.origin`.
2. A `CustomEvent` or DOM event the content script listens for on an injected element.
3. `externally_connectable` messaging from a page.
4. A message relay: content script receives from the page and forwards with `chrome.runtime.sendMessage`.

Then rule the others out explicitly, because each is a dead end that looks like a live one: page JavaScript has no `chrome.runtime`, the content script's isolated world is not the page's, and `use_dynamic_url: true` makes the frame unaddressable.

A worker handler that performs privileged work with **no** `sender.id` / `sender.url` check is not yet a finding — it is the missing half. State it as a primitive and keep hunting for the bridge; a report built on the handler alone gets "the page cannot send this message".

## Prove it with two parties

Load the unpacked extension into a Chrome profile with CDP (`--load-extension`, separate `--user-data-dir`), serve the attack page, and capture the artefact: the `fetch` the extension made with the victim's cookies, the value that appeared in the page, the tab that opened. Redact tokens but keep the length and prefix.

If the capture is missing, the claim is a HYPOTHESIS regardless of how clean the code path reads. And the chain must be shown end to end: three separately true links that do not connect are worth zero, which is exactly how a promising extension lead ends — a worker with no sender check, a raw session cookie in `storage.local`, and a page-drivable frame, with no edge between them.

## Rebuttals to beat before writing

- **"The page already has the session."** True for cookies the page can read; false for `HttpOnly` session cookies the extension holds and the page cannot. Say which cookie, and prove the page could not read it directly.
- **"Broad permissions are consented at install."** A permission alone is P5; the finding is the use, not the grant.
- **"The user has to visit the page."** That is the attacker's normal precondition, not a weakness, as long as no click is needed.
- **"The value is not sensitive."** Name what the token unlocks and show the request it authorises.
