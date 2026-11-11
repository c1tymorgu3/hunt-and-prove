# Testing a vendor-hosted instance

When the in-scope asset is a workspace the vendor provisions for you (`bugcrowd-<you>.<vendor>.cloud`, a trial tenant, a sandbox account), the whole class of testing changes shape. You get a real deployment and real runtime evidence, and you inherit two new failure modes that have nothing to do with the bug.

## 1. Provisioning is a human step

Signup flow, email verification and often a workspace name are interactive. A subagent cannot complete them: the verification mail has to be clicked by whoever owns the inbox. Budget the user's involvement explicitly and give them exact field values (workspace name must match the brief's in-scope pattern, for example `bugcrowd-<shortname>` so the host becomes `bugcrowd-*.cloud.<vendor>.com`).

Do not try to script past verification. On a cloud tenant the relevant setting is usually managed server-side: a `PUT /api/v4/config/patch` that sets `RequireEmailVerification: false` returns 200 with the full config and the value stays `true`, and `PUT /users/{id}/patch {"email_verified": true}` returns 200 while the field stays null. Both look like success and neither works.

**Create the second account by invite, to an inbox the user can open.** A user created through the admin API exists but cannot log in until verified. Send a team invite to a deliverable address (a plus-address on the user's own mailbox works), have them click it once, and then continue through the API. One invite costs the user thirty seconds; fighting the verifier costs an hour.

## 2. Drive an authenticated session without ever handling the password

Two accounts are needed for any cross-user claim, and both must come from a session the user established.

```
# Chrome refuses remote debugging on the default profile (136+). Use a fresh profile dir.
powershell -NoProfile -Command "Stop-Process -Name chrome -Force -ErrorAction SilentlyContinue"
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\Users\user\bb\chrome-<target>" <url>
```

- Killing Chrome first is required: a second `chrome.exe` invocation hands its arguments to the running instance and exits, leaving no debug port.
- The CDP HTTP endpoints need a `Host: localhost:9222` header. Plain `curl http://127.0.0.1:9222/json/list` returns an empty body; `urllib` with that header works.
- Read cookies with `Network.getAllCookies` over the page websocket: `HttpOnly` session cookies are invisible to `document.cookie`, and the session token is exactly the one you need.
- Turn that session into API calls with `Authorization: Bearer <token>`. Bearer auth skips CSRF; cookie auth needs the CSRF token on every POST.
- Hand the login to the user in the visible window, then drive everything after it. Never ask for or type the password.

## 3. Before claiming a bypass, tell the edge apart from the application

This is the failure that ends a night: the code has the defect, your request should reach it, and a proxy answers instead. Run a three-way matrix and classify every response before you write a word.

| identity | parameter | meaning |
|---|---|---|
| attacker, lacks the permission | the value that should be refused | the case under test |
| attacker, has the permission | the same value shape, legitimately scoped | proves the route works for this identity at all |
| privileged account, has the permission | the refused value from row 1 | proves the *value* is accepted by the app |

Classify by the response itself, not the status code alone:

- `server: cloudflare`, `content-type: text/html`, and a body that is a vendor redirect page → the edge answered. The application never saw the request.
- A JSON error with an `api.`-style id → the application answered, and the decision is the app's.
- A 500 only for the privileged row means the handler ran and the downstream call failed — the route is live and the parameter is accepted.

If the edge is what blocks the attacker, the defect is unreachable on the in-scope asset no matter how real it is in the source. That is the moment to stop, not to write it up: **a bug in a repository that is not itself an in-scope target does not pay when the deployed asset is the one that mitigates it.** Check the scope list for the repo before spending the night on a code-level bypass of a hosted product.

## 4. Small API facts that decide whether a probe is valid

- A 404 on a plausible path is usually a wrong path, not a missing feature (`/api/v4/teams/{id}/commands` 404s where `/api/v4/commands?team_id={id}` works).
- Enum-ish string fields are often single letters (`method: "P"` for POST, `"G"` for GET); a rejected write returns `is_valid.method.app_error`.
- A DM or group channel has no team, so any request that carries a `team_id` alongside a DM `channel_id` is a trust-boundary crossing by construction — that is where to aim, and also where the edge is most likely to police you.
- Keep a control request in every probe script whose only purpose is to prove the endpoint works at all for a legitimate caller. Without it, a 404 or 403 cannot be told apart from a malformed request.
