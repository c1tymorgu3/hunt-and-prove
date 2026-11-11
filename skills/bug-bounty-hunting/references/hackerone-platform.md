# HackerOne platform mechanics that decide whether a report is worth writing

Facts a hunter needs before spending a report slot or promising the user money.

## Signal requirement gates

Programs set a threshold from -1.0 to 7.0; the value is computed over a rolling 365-day window.
Common values: `0.0` (default, only excludes a recent net-negative record), `1.0` ("Strict"), `3.0`
(narrow set of proven researchers). Source-code-heavy crypto programs cluster at 3.0.

A gate does not lock you out. It routes you through trial reports.

### Checking a program's gate without reading the page

`signal_requirements_setting` is an object on `team`, not a scalar: selecting it bare fails with
"Field must have selections". Ask for `target_signal` inside it.

```graphql
{ team(handle: "PROGRAM") { name submission_state
    signal_requirements_setting { target_signal } } }
```

Paginating `teams(first:100, after:"...", where:{offers_bounties:{_eq:true}})` with those fields
returns the whole platform in three requests and answers "where could this account submit today"
before any target selection happens. Same shape with `offers_bounties:{_eq:false}` covers the VDPs.
`target_signal: null` means the program has no requirement, and in practice that only shows up on
paused or disabled programs — so treat null as "not accepting" until proven otherwise.

## Trial reports

- Every user has **3 trial reports, shared across all programs** whose signal requirement they do not meet.
- Every submission to such a program consumes one. A trial report is a **normal report**: it is triaged,
  it can be paid, it is not a draft or a sandbox.
- The allowance refills to 3 when **any** report of yours reaches `Triaged` or closes `Resolved` — it does
  not have to be the trial report itself, and a VDP report counts.
- A duplicate that duplicates an already-triaged/resolved undisclosed report returns 1, capped at 3.
- Burning all 3 without a resolution starts a **90-day pause**, which ends early if any report resolves.
- A program can lower its own per-program open-trial limit to 2 or 1.

Practical consequence: one good report on a gated program costs nothing in the long run. Ten speculative
ones cost the account.

## Payout methods and prerequisites

Three methods: bank transfer (Currencycloud), PayPal, and direct-to-wallet crypto (BTC or USDC).

| Method | Minimum | Timing |
|---|---|---|
| PayPal | none | Mon-Fri 12:30 UTC, 1-2 days |
| BTC / USDC wallet | $15 | daily 23:00 UTC, 1-2 days |
| Bank transfer | $50 regular / $100 priority | Mon-Fri 09:00 UTC, 1-10 days |

No payments are processed on the first or last day of the month.

Before any bounty is paid, three things must be complete under Settings > Rewards and Payments >
Payment Setup, in order: identity verification via Veriff (valid 12 months), at least one payment method
on file, and an approved tax form (W-8BEN for non-US). An awarded bounty with these missing just sits
there.

### Crypto payout gotchas

- **USDC goes out on Ethereum only (ERC-20).** Handing HackerOne a BEP-20 or TRC-20 deposit address
  loses the funds. If the user wants the money on an exchange, they must generate the **ERC-20** USDC
  address, not the default chain the exchange shows.
- BTC supports Legacy and BECH32 (`bc1...`); Taproot/Segwit are untested by HackerOne.
- Address validation is partial. A wrong-but-well-formed address is the researcher's loss.

### Country notes

- PayPal does not operate in Turkey, so the realistic routes there are bank transfer or crypto.
- Bank transfers are refused to sanctioned banks; HackerOne points at the OFAC search tool.
- Crypto received as a bounty is income. Say so and stop; do not give tax advice.

## Reading a program before committing

The program page carries the numbers that matter more than the reward table:

- `Reports received | 90 days` against `Reports resolved` — 4,000 against 3 is a wall no skill beats.
- `Response efficiency` under 80% means reports die in triage.
- `Total bounties paid` and `Top bounty` — if the total is roughly one top bounty, the program has paid
  once and may not again.
- Bounty table "last updated" date: a table from years ago is a signal the program is on autopilot.
- `Average time to triage` and `Average time from submission to bounty` are the **only** speed numbers on
  the page. `Response efficiency` measures whether the program replies at all, and `Last report resolved`
  is one report's date, not the queue's pace. A program showing ten months to triage and a year to
  resolution will not produce money this quarter however clean its scope looks.
- **Read those labels carefully: HackerOne renders the value *above* its label.** A regex like
  `Average time to triage\s*\n+([^\n]+)` captures the value belonging to the *next* metric and silently
  reports a healthy number for a dead program. Parse the pairs positionally, or print the whole
  highlights block and read it.

The opportunities feed (`hackerone.com/opportunities/all`) exposes awarded-report and awarded-reporter
counts per program. `awarded_reports / awarded_reporters` above ~3 means the program is already farmed;
under ~1.5 with high efficiency means few people are finding anything and the queue is short.

## Filtering the opportunities feed for fast, small, low-friction money

When the user needs a payout soon and a Low is acceptable, rank by friction and queue length, not by
max bounty. Flatten the feed into rows first (program name, bounty range, awarded reports, awarded
reporters, efficiency, asset-type badges, `Gold Standard` / `Fast Payment` badges), then apply:

- **Low band must actually pay**: minimum bounty ≤ $200. A program whose floor is $500 will not pay for
the finding a short session produces.
- **Efficiency ≥ 88%** — below that, valid reports die in triage.
- **Awarded reporters ≤ 70**, and prefer single digits. This is the competition number that matters.
- **At least one asset testable with no account**: `SourceCode`, `Android`, `iOS`, `Domain`, `Wildcard`.
  A program whose whole scope is an authenticated app is unusable when the signup is geo-fenced.
- Then sort by `awarded_reporters` ascending, efficiency descending.

Verify each survivor before recommending it: GraphQL for the real scope list, the program page for the
Signal requirement and reward table, and the policy text for killers ("full compromise only", "business
logic out of scope", "test account provided by us", physical-device requirements).

`Fast Payment` is the strongest tiebreaker when the user says the money is needed soon — it is a
commitment to pay within a month of the report, which is the difference between a promise and a payout.

Finally, state the trade-off out loud instead of hiding it: the empty program pays less per finding, and
the busy one may never answer. Running one of each in parallel is usually better than betting on either.

## What "information disclosure" costs you

A report whose impact sentence is "this endpoint answers without authentication and here is what is in
the response" is a Core Ineligible Finding, however interesting the contents. A node control API
returning the peer IP set, an internal build manifest, attestation certificates, an exposed admin
panel that renders but does nothing — all land in the same bin: no demonstrated exploitation, no
payout. The bar is *I obtained data or capability I should not have*, not *this thing answers strangers*.

Before writing, ask which of these the finding actually is:

| Shape | Pays? |
|---|---|
| Read another user's object by id (IDOR, real data returned) | yes |
| Reach an authenticated function without authenticating | yes |
| Working chain: XSS that steals a token, SSRF that hits internal metadata, RCE | yes |
| An endpoint exposing internal state, keys, topology, or config | no |
| A misconfiguration nobody has exercised | no |

## Disputing a close

The only argument that sometimes moves a triager on an information-disclosure close: the demonstration
they are asking for is itself excluded by the policy. If proving the impact means flooding validators,
that is DoS, and DoS is out of scope; if it means touching a third party, that is out of scope too.
Say that in two sentences and ask which in-scope, non-excluded demonstration they would accept. Either
they name one, or the silence is the answer.

Do not appeal a duplicate or an N/A on the merits. Both are final in practice, and a long rebuttal on
a weak finding spends credibility that a later good report needs.
