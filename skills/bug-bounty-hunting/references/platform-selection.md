# Where to file when the primary platform is capped

A good finding is worth nothing if no platform will accept the report. The caps are structural, not temporary, so they have to be planned around like any other gate in Phase 0.

## The caps

- **Bugcrowd**: a new account files six submissions per seven days. It is lifted by accuracy, not by time, so the way out is clean reports, not patience. Burned slots do not come back when the week rolls over if accuracy is still poor.
- **HackerOne**: trial reports are shared across every program whose Signal requirement the account does not meet. At zero balance the account cannot submit anywhere until one report is triaged or resolved, or roughly ninety days pass. Never spend the last trial on a maybe.
- Both caps hit the same way: the night produces findings and the account cannot file them. Check the balance before target selection, not after.

## Where the report can still go

**Audit contests are the best structural fit for a read-and-prove apparatus.** Code4rena, Sherlock, Cantina and CodeHawks run on a fixed scope, a fixed deadline, and a payout per valid finding, judged by other researchers against published rules. There is no submission cap, no triager who can call a real defect informational, and no attacker model to argue about — a finding either demonstrates the impact or it does not. When a swarm is already built for reading a repository and proving a bug with a test, this is the platform where that shape converts.

Selection criteria, in order: a contest live now or opening within about 48 hours; public source with a harness that runs on this machine; in-scope code under roughly 3,000 lines or a single module; then the payout split. Competition is measured by the participant count and finding count of the last comparable contest on the same platform, not by the prize pool.

**Immunefi** takes any number of reports and verifies identity only at payout. Its evidence standard is a working proof against the deployed code — a Foundry test on a fork, with the balances before and after. Scope small, forkable assets on Ethereum, Base, Arbitrum, Optimism or Polygon; recently listed projects and L2 deployments are far less contested than the blue chips, which have been audited and farmed for years. Tell the user KYC is required before money moves, since that is a decision only they can make.

**On Immunefi the known-issues gate is heavier than on any other platform.** A listed project can publish several audit reports plus a `Known_issues` repository, and the program page then excludes "issues listed in previous audits or known-issue documents, and any report sharing a root cause with them". That is an eligibility boundary, not a ranking signal: clone the known-issues repository and read the audit table before dispatching a single hunter, because everything in there is already spent. A project that has published five audits is not a target for a first pass; a project listed in the last six weeks whose assets were *added* just before that is.

## The signup is part of the scope

Every platform above can hand you a program that passes every selection criterion and is still untouchable, because the product's own registration stands in front of the authenticated surface. Consumer finance is the worst case: an app whose signup demands a local mobile number, a national tax or insurance identifier, and a domestic bank direct debit cannot be entered from outside that country, and no amount of recon fixes it. Check the signup form — not the marketing site — before ranking an authenticated program, and treat "registration requires local identity" as the program being code-only from then on.

What survives that gate is the work you can do without a session: the API's unauthenticated surface, its error shapes, and the source or mobile binary if those are in scope. Run it as a ten-minute gate with one agent and require a single `ACCESS-OK` or `ACCESS-BLOCKED - reason` line at the top of the report, so four other agents do not spend half an hour discovering the same wall.

**YesWeHack** is open registration with public programs paying from about $50. Pick a program whose brief allows self-registration of test accounts, whose scopes are web or API, and whose report volume is low for its age. A program with hundreds of reports a week is farmed.

The whole catalogue is readable without an account, which makes shortlisting cheap:

```
GET https://api.yeswehack.com/programs?page=1&count=100     -> 53 public programs
GET https://api.yeswehack.com/programs/<slug>              -> scopes, reward grids, exclusions, stats
GET https://api.yeswehack.com/programs/<slug>/versions     -> history, earliest accepted_at = launch date
GET https://yeswehack.com/programs/<slug>                  -> server-rendered page: hunting requirements, reward table
```

A plain browser `User-Agent` is enough; no auth. Read three fields per program before anything else: the **hunting requirement** block (a literal `Self-register` line is the difference between a program you can test and one you cannot), the **reward grid** (`reward_grid_critical` / `_high` / `_medium` are separate tables, so a Low can be $50 on one scope and $100 on another), and **`hacktivity`**. When hacktivity is closed the duplicate probability cannot be measured at all, only argued — say that out loud rather than pretending the usual crowdstream arithmetic applies.

**Vendor-run programs** (Google, Microsoft, Meta, Apple, Mozilla) have no cap and no intermediary, at a much higher bar and a slower payout cycle. They suit a bug that is already proven, not a night of exploration.

**huntr** is no longer the open-source bounty site it used to be; it runs AI/ML challenges now. Do not send open-source findings there.

## How to choose, once the cap is spent

Rank by, in this order:

1. **Evidence shape.** Does the platform want exactly what we can produce — a failing test, a fork repro, a request/response pair? A platform that wants a video of a live exploit on a customer tenant is a different job.
2. **Competition.** Few or no paid reports on the specific asset, recently listed, small participant count.
3. **Runnability.** The code builds or the product runs here, tonight.
4. **Scope size.** Readable in one pass.
5. **Payout.** Last, and never as a floor: a $100-500 listing nobody is working beats a $10,000 asset that everyone is.

**Do not filter candidates by a payout minimum.** A floor quietly removes exactly the small, new, uncontested listings where the first win is most likely, and the user's own position is usually that a small payment is worth more than a large maybe. Rank by money only after the four criteria above have already cut the field.
