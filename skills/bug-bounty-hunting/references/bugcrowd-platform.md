# Bugcrowd — reading programs logged out

Use when HackerOne gates the account (Signal requirement, no trial reports) and the hunt has to move to a
platform that lets a brand-new researcher submit. Bugcrowd has no Signal gate and no invite gate: every
engagement on the public list is submittable by a fresh account.

Measured across the full listing: 296 engagements, all `participation: open`, all `pay_for_success`, all
`isPrivate: false`, 273 in progress and 23 paused. There is no reputation ladder to climb first.

## The endpoints

All of these answer logged out. Use `curl_cffi` with `impersonate="chrome"`; plain urllib gets Cloudflare'd
on some paths.

```
GET https://bugcrowd.com/engagements.json                 Accept: application/json
    -> {"engagements":[{name, briefUrl, rewardSummary{minReward,maxReward}, accessStatus,
        productEngagementType, isPrivate, serviceLevel}], paginationMeta{totalCount}}
    paginated 24/page; 296 records total
```

`https://bugcrowd.com/programs.json` is a 404 and `api.bugcrowd.com/engagements` is a 404. The `.json` on
the engagements route is the one that works.

**The gotcha that silently breaks a scraper:** the `Accept` header has to match the route. `Accept:
application/json` on a `.json` path, `Accept: text/html` on an HTML path. Mismatch returns `406 Not
acceptable`, not an auth error, so it reads like the endpoint died.

## Getting a program's real scope and rewards

The brief page is a JS app whose rendered text is empty, but its HTML carries `data-api-endpoints` with a
`getBriefVersionDocument` changelog UUID:

```python
# 1. GET https://bugcrowd.com/engagements/<code>     (Accept: text/html)
#    -> data-api-endpoints -> engagementBriefApi.getBriefVersionDocument
#       = "/engagements/<code>/changelog/<uuid>"
# 2. GET https://bugcrowd.com/engagements/<code>/changelog/<uuid>.json   (Accept: application/json)
```

Step 2 returns the whole brief: `scope[]` with `inScope`, `targets[{name,uri,category}]`, and
`rewardRangeData` keyed by priority — `{"1":{min,max},"2":{...},"3":{...},"4":{...}}` in dollars, so P4 is
the low-priority floor. Also `engagementConfiguration.participation` and `engagement.state`.

Three more public JSON routes per engagement:

```
/engagements/<code>/statistics          -> rewardedVulnerabilities, averagePayout, validationWithin
/engagements/<code>/crowdstream.json    -> accepted-submission feed
/engagements/<code>/hall_of_fames.json  -> credited researchers
```

`statistics` is the closest analogue to HackerOne's hacktivity and it is better: it gives the count of
rewarded findings, the average payout and the validation window in one call. Use `validationWithin` as the
triage-speed filter and `rewardedVulnerabilities` as the competition filter.

## Asset categories

There is **no `source_code` category**. A repository target is `category: "other"` with a `github.com/...`
URI, so filtering for source code means scanning `other` targets for a GitHub URI. Categories seen:
`website` 270, `other` 96, `ios` 87, `android` 85, `api` 84, `hardware` 10, `iot` 5, `network` 5.

## Filter chain that actually narrows to a few

1. `participation == open` and state not paused → 273.
2. Has an asset that needs no account: `android`, `ios`, `hardware`, `iot`, or a GitHub URI → 81 mobile-only
   candidates, 18 with GitHub URIs.
3. P3 min > 0, so a low-priority finding still pays → 93 of the intersection.
4. Low competition by `rewardedVulnerabilities`, `crowdstream` entries and hall-of-fame size → a handful.

### Keep the corpus on disk, then query it

Download every brief once into `briefs/<code>.json` (296 files, a few minutes), and from then on answer
"which program fits these constraints" with a script instead of a fresh recon round. Re-scouting from the
web each time costs a fan-out; filtering a local corpus costs seconds, and it lets you re-rank after the
criteria change, which they always do.

```python
import json, glob, os, re
rows = []
for f in sorted(glob.glob('briefs/*.json')):
    d = json.load(open(f, encoding='utf-8'))
    if d.get('participation') != 'open' or d.get('rewardAllocation') != 'pay_for_success':
        continue
    p3 = None
    targets = []
    for g in d.get('data', {}).get('scope', []):
        if not g.get('inScope'):          # out-of-scope groups carry full target lists too
            continue
        e = (g.get('rewardRangeData') or {}).get('3') or {}
        lo, hi = e.get('min'), e.get('max')
        if isinstance(lo, int) and isinstance(hi, int):
            p3 = (lo, hi)                 # P5 rows arrive as null/null
        for t in (g.get('targets') or []):
            targets.append((t.get('uri') or '', t.get('name') or ''))
    if not p3 or not (300 <= p3[0] <= 1500):
        continue
    if not any(re.search(r'github|gitlab|bitbucket|crates\.io|npmjs|pypi|source code',
                         u + ' ' + n, re.I) for u, n in targets):
        continue
    rows.append((os.path.basename(f)[:-5], p3[0], p3[1], targets[:2]))
rows.sort(key=lambda r: (-r[2], r[1]))
```

Two parsing facts that cost time: only groups with `inScope: true` count (the out-of-scope group in the
same array lists real targets, and filing against one is filing against an out-of-scope asset), and
`rewardRangeData` mixes `null` with integers, so a naive `min`/`max` comparison raises `TypeError` halfway
through the corpus.

## What to pick

**Check that the artefact runs before anything else.** Among the 18 repo targets in the $300–1,500 band,
the ones that died were the ones whose product could not be executed on the available host, whose brief
named a closed eligible-outcome list, or whose only caller was a trusted party. Reward size did not predict
which produced a finding; runnability did. Prefer a program that hands you the running thing — its own
test harness, a native binary, or a hosted instance with email-only signup — over one that pays ten times
more for software you can only read.

**Rank source-code programs by the P4 floor, because P4 is what most findings turn out to be.** A P3-only filter hides the programs that actually pay for a Low: read both rungs of `rewardRangeData` and prefer the program whose *worst* paid outcome still clears the user's bar — `$300` flat is worth more than a `$25,000` P3 on a codebase you cannot execute or contradict.

**`rewardRangeData` is per scope group, and the groups differ by an order of magnitude.** A program can carry a headline table of $660–990 for one tier while the org-wide open-source repository row — the one your target actually sits in — pays $50–250. Reading the wrong group produces a confident number that is off by 4x; quote the table from the group that contains your target row, and quote it in the reply so the user is not promised money the row does not carry. Two groups with the same shape appear on many programs: a product or tier group and an OSS/licence group.

**Only a repository listed as an in-scope target row counts as source code.** Measured over all 296 briefs, 15 name a `github.com`/`gitlab.com` URI as a target; the rest mention GitHub in prose, in docs or inside an out-of-scope group, and a report filed against one of those is filed against nothing. That number is the whole reason source-code programs feel scarce: the filter is the target row, not the word.

**When several of those repos are candidates, choose by what landed recently.** Shallow-clone each (`--depth 50`) and read `git log --since=90.days --oneline` before reading any code: a merge that adds a fallback, a retry, a new endpoint or a new permission branch is the least-exercised and most promising code in the tree, and a repo with nothing but dependency bumps has nothing new to break. This is the cheapest way to pick between programs that all look equal on the brief.

**Skip a codebase with published audit reports and an empty crowdstream.** Multiple firms' audit PDFs in `audits/` or on the vendor's site, plus zero accepted reports on that specific asset in six months, is not an untouched target — it is one where everyone with more context than you already tried. A genuine primitive can come out of such a pass and still be documented behaviour, which is a whole night for nothing.

A **mobile-only scope** is the best shape for a team with no accounts anywhere: two store listings, nothing
else in scope, a P4 floor around $250, and a lifetime rewarded count in single digits means the binary has
never been opened. The engagement brief for those programs typically names the OWASP Mobile Top 10 as the
expected deliverable, which means code and binary findings are paid without a live web exploit.

A **pure source-code engagement** is the second shape: three or four GitHub repos, no account, and the
brief invites standing up your own instance. Watch the clause that says issues reproducing only in
non-production virtualised environments are not rewarded — that moves the bar to a committed test in the
repo's own harness.

Skip a program whose hall of fame and crowdstream are full even when the money is better; a repo with
hundreds of lifetime rewarded findings has had its easy classes taken.

## Submitting

The human URL is `https://bugcrowd.com/engagements/<code>`. `https://bugcrowd.com/<code>` 404s, so every
program link in a deliverable has to carry the `/engagements/` segment.

New accounts are capped at **6 submissions per 7-day period** until accuracy earns the cap off, so a batch of
nine ready reports does not all go out in one sitting. Order the batch by payout and evidence strength and
say which six go first, rather than letting the user discover the cap mid-form.

The form asks for: submission title, target (a dropdown of the brief's target `name` strings, quoted
exactly — `github.com/fireblocks/mpc-lib`, `https://github.com/freedomofpress/securedrop`, `LaunchDarkly
Open Source SDKs`), VRT category, URL/location, description (25,000 character cap), optional attachments and
a brief-terms checkbox.

The VRT suggestion is advisory in theory — Bugcrowd states the suggested rating is not the applied rating —
but in practice the triager adopts the node's own priority, so a category that maps to P5 is a $0 report
however sound the bug is. Pick the node, read *its* priority in `references/vrt-1.19.1.md`, and if the best
fit is P5 either find the sibling at P3/P4 or say what extra impact the finding would need to land there.
Getting a plausible-sounding path wrong is the worst case: a path that does not resolve to a node sends no
suggested priority at all, and the triager then rates from scratch.

The picker lists full variant paths, and **selecting only the parent subcategory gives you a node with no
priority** — the field then shows `Broken Access Control (BAC) > Insecure Direct Object References (IDOR)`
with no `P4 —` prefix, which is the failure mode above. Always drill to the variant. When several variants
differ only by identifier type, the identifier in the target decides which one is honest: an object id minted
from a UUID (a base64-UUID, a `deploy-<uuid>`) belongs to the `Complex Object Identifiers GUID/UUID` variant at
P4, while the `Iterable Object Identifiers` siblings pay P1–P3 and require a guessable, sequential id. Taking
the P1 variant for a UUID id reads as inflation the moment the triager sees the id shape, so grep the
generator before choosing.

### Where the replies land

The submit form is `https://bugcrowd.com/engagements/<code>/submissions/new`. There is **no notification
page**: `/notifications` returns 404, so do not send the user looking for an inbox. Replies, status changes
and the customer's rating all appear as a comment thread on the individual submission, reached from the list
at `https://bugcrowd.com/submissions` (filter one program with `?engagement[]=<code>`). Email is the practical
notification channel, since Bugcrowd mails on every status change and comment, so point the user at their
inbox rather than the panel.

A submission moves `New` → `Still being assessed` with no priority shown, then gains its `P1`–`P5` badge when
the customer rates it. The badge shows on the list row, which makes the list the fastest way to see what got
downrated. A P5 pays nothing and earns no points however sound the bug is, and disputing one whose only
argument is a severity opinion is not worth the accuracy cost.

Two counters on that page are unrelated and easy to misread. `Requests for response: 0 of 2` counts open
requests for the customer to respond, not submissions. `Total payments` and `Total points` read `$0` on a
filtered view until something is actually rewarded, so a `$0` there says nothing about reports still being
assessed.

## Asking for CrowdStream disclosure

Each submission page carries a "Disclose report to CrowdStream" panel with two text fields and a visibility
choice, and it stays available on a report that was closed as a duplicate.

Check `coordinatedDisclosure` in the brief JSON (`true` on programs that allow it) before spending the
request, then fill:

- **Message to customer** — why publishing helps, in two or three sentences. On a duplicate the honest reason
  is the shape of the mistake rather than the vulnerability: the endpoint's own comment names the fields it
  may change, the code binds one more, and anyone self-hosting the project can check their build against that
  in a minute. Offer to withdraw and re-request later if they would rather wait until the original report is
  resolved — Bugcrowd recommends asking only after resolution, so a refusal is expected and not worth arguing.
- **Summary to be published** — component, the defect, the two or three `file:line` facts, the impact, the
  fix. No reproduction steps, no payload, no internal comments.
- **Disclosure level** — pick **Limited visibility** whenever the report is a duplicate or its thread quotes
  another researcher's work. Full visibility publishes the entire timeline, comments and attachments, which
  are not yours to release; limited publishes the summary and a simplified timeline, which still documents
  the technique.
