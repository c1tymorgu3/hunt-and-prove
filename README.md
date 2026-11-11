# hunt-and-prove

**Bug bounty methodology for [Hermes](https://hermes-agent.nousresearch.com/docs).**
Pick a target you can actually reach, gate the hypotheses, then prove or refute before writing a
word.

`MIT` · `markdown only` · `no dependencies`

---

## The shape of a run

```
   ┌───────────┐    ┌──────────────┐    ┌────────────┐    ┌────────────┐
   │ 4 gates   │───▶│    gate      │───▶│ 5 hunters  │───▶│ 5 refuters │───┐
   │ can I     │    │ attacker +   │    │ one vector │    │ one        │   │
   │ reach it? │    │ gain + the   │    │ each,      │    │ question   │   │
   │           │    │ killer line  │    │ executed   │    │ each       │   │
   └───────────┘    └──────────────┘    └────────────┘    └────────────┘   │
                                                                          ▼
                                                        ┌──────────────────────┐
                                                        │ report, or a clean no │
                                                        └──────────────────────┘
```

Nothing reaches a triager until it has survived all five refuters. That rule is the whole point of
the pack: a clean "no finding" costs a night, a rejected submission costs credibility.

---

## What's inside

| Skill | What it's for | Open this first |
|---|---|---|
| **bug-bounty-hunting** | Choosing a program, reading its brief, writing a report that holds | `SKILL.md` |
| **subagent-delegation** | Running ten agents without them reading the same file | `references/prove-refute-swarm.md` |
| **humanizer** | Making the prose read like a person wrote it | `SKILL.md` |

<details>
<summary><b>bug-bounty-hunting</b> — references</summary>

| File | What it covers |
|---|---|
| `platform-selection.md` | Platforms and their gates: submission caps, Signal, identity checks |
| `bugcrowd-platform.md` | Public JSON endpoints, brief structure, the new-account cap |
| `hackerone-platform.md` | GraphQL scopes, Signal, and how to read the statistics without misreading the labels |
| `vrt-1.19.1.md` | The taxonomy node by node, with the priority each node actually maps to |
| `browser-extension-analysis.md` | CRX/XPI extraction, message boundaries, storage |
| `mobile-apk-analysis.md` | Getting the APK, decompiling, what to look for |
| `smart-contract-triage.md` | Reading deployed code, deciding what is real |
| `local-build-and-run.md` | Getting the artefact to execute |
| `hosted-instance-testing.md` | Working against a vendor-provisioned instance |
| `waf-walled-targets.md` | What to do when everything returns 403 |
| `harness-honesty.md` | Stopping a test from proving something no real input could cause |
| `recon-by-asset.md` | Recon shaped by asset type |
| `graphql-testing.md` | Introspection, batching, auth boundaries |
| `scripts/vrt_lookup.py` | Flatten the live taxonomy, look up any class with its priority |

</details>

<details>
<summary><b>subagent-delegation</b> — references and scripts</summary>

| File | What it covers |
|---|---|
| `prove-refute-swarm.md` | The gate, the 5/5 split, the survival test, the stop rule |
| `scripts/audit_agents.py` | Reads delegation logs and flags a stalled child |

</details>

<details>
<summary><b>humanizer</b></summary>

| File | What it covers |
|---|---|
| `references/fidelity-constrained-editing.md` | Editing when the facts are fixed and only the prose may move |
| `LICENSE` | Ships with the skill |

</details>

---

## The four gates

Before any agent is dispatched, the target has to answer these. Each one is a ten-minute check and
each one has killed a whole night when skipped.

| Gate | Question | What it kills |
|---|---|---|
| **Reach** | Can we create an account or run the artefact? | A consumer finance app that wants a national insurance number |
| **Coverage** | Does the brief pre-answer the classes we would find? | A published security model that lists every class in the code |
| **Outcomes** | Is there a closed list of acceptable findings? | A five-item list that excludes parsing and memory safety |
| **Access** | Is the surface behind an edge that refuses us? | A host that returns a challenge to every request from our address |

---

## Installing

```bash
git clone git@github.com:c1tymorgu3/hunt-and-prove.git
cp -r hunt-and-prove/skills/* ~/AppData/Local/hermes/skills/
```

On Linux or macOS the destination is `~/.local/share/hermes/skills/`. Hermes only needs a
`SKILL.md` at the root of each skill directory; the category folder is arbitrary.

---

## Why it's shaped like this

Most of these rules came out of getting reports closed. Two long nights of that taught me more
than a month of reading did. If a line in here looks oddly specific, it is because something got
rejected for exactly that reason.

A few that keep paying for themselves:

**A program's own severity model beats any taxonomy.** If the brief or a published security model
says what it won't accept, that's the truth. One target had pre-answered nearly every class its
code contained, and we found them anyway.

**Prove impact at the target's own call sites.** "A caller might read this buffer" gets answered
with "every caller in the tree guards it", and then you have lost a week.

**Ask who sends the input and whether they already hold the capability.** An argument injection
into a shell is worth nothing when the only caller is the server that can already execute arbitrary
code through another field on the same message.

**Prefer surfaces where nothing sits between the attacker and the payoff.** Browser extension,
desktop or IDE plugin, mobile app, something you compile yourself, a hosted instance, then SaaS.
Each step up adds a layer that can absorb the bug. An edge proxy, a redacted API response and a
documented design trade accounted for three dead ends in a single evening.

**A claim isn't real until someone compiled it.** Static reading produces confident false positives,
including ones that survive a review pass. And parallelism is not the bottleneck, depth is:
sixteen agents skimming eight programs produced less than three agents reading one codebase.

---

## Scope and conduct

Everything here assumes authorisation: a published scope, a VDP, or a signed engagement. The rules
that keep it that way live in `SKILL.md` under **Non-negotiables** — only listed assets get traffic,
no scanners against live bounty targets, the minimum request needed to prove reachability, and
never someone else's credentials or data.

## Licence

MIT, except `humanizer`, which ships with its own LICENSE file.
