# Security research skills

Three skills I use for authorised bug bounty work with Hermes. Plain markdown with YAML
frontmatter, no dependencies, nothing tied to the machine that wrote them.

Most of this came out of getting reports closed. Two long nights of that taught me more than a
month of reading did. If a rule below looks oddly specific, it is because something got rejected
for exactly that reason.

## What's in the pack

### bug-bounty-hunting

The method: deciding whether a program is workable at all, reading its brief properly, and writing
something a triager can't wave away.

The main file walks through eligibility, pulling scopes, the four gates a target has to pass, the
hypothesis gate before any agent gets spent, and how to shape the report. The references go deeper
on the parts that kept biting me.

`platform-selection.md` covers the platforms and their gates, which is a longer list than it looks:
submission caps, Signal requirements, identity checks, and what still accepts a new account today.
`bugcrowd-platform.md` and `hackerone-platform.md` document the public JSON and GraphQL surfaces
along with the traps in reading the statistics. One of those traps is that HackerOne lays out a
number *above* its label, so it's easy to parse the wrong figure and rank programs on nonsense.

`vrt-1.19.1.md` is Bugcrowd's taxonomy read node by node, with the priority each node actually maps
to, and `scripts/vrt_lookup.py` does the lookup. I wrote this after picking a category that mapped
to "informational" twice in one night.

The per-artefact playbooks cover browser extensions, mobile APKs and smart contracts.
`local-build-and-run.md`, `hosted-instance-testing.md` and `waf-walled-targets.md` are about getting
the thing to run, or working out what is standing in front of it when it won't. `harness-honesty.md`
is the boring one that matters most: how to stop a test from proving something no real input could
cause.

### subagent-delegation

Running a swarm without ending up with eight agents reading the same file.

`prove-refute-swarm.md` is the structure that survived contact. A gate on the hypotheses first,
then five hunters each owning one vector, and five refuters each owning one permanent question.
Every claim clears all five before it becomes a report. It exists because a clean "no finding" is
cheaper than a rejected submission.

### humanizer

Rewriting text so it reads like a person wrote it. Every report in the source material went through
this before submission. Goes well with findings; less well with release notes.

## The things that actually mattered

A program's own severity model beats any taxonomy. If the brief or a published security model says
what it won't accept, that's the truth, and one target I worked had pre-answered nearly every class
its code contained.

Prove impact at the target's own call sites. "A caller might read this buffer" gets answered with
"every caller in the tree guards it", and then you have lost a week.

Ask who sends the input and whether they already hold the capability. An argument injection into a
shell is worth nothing when the only caller is the server that can already execute arbitrary code
through another field on the same message.

Check access before anything else. What does registration demand: an email, or a local phone
number, a tax identifier, a bank relationship? A program you cannot log into is a program you
cannot test, however good the code is. I burned four rounds on that in a single night.

Prefer surfaces where nothing sits between the attacker and the payoff. Browser extension, desktop
or IDE plugin, mobile app, something you compile and run yourself, a hosted instance, then
multi-tenant SaaS. That order is not aesthetic: each step up adds a layer that can absorb the bug.
An edge proxy, a redacted API response and a documented design trade accounted for three separate
dead ends in one evening.

A claim isn't real until someone compiled it. Static reading produces confident false positives,
including ones that survive a review pass. And parallelism is not the bottleneck, depth is:
sixteen agents skimming eight programs produced less than three agents reading one codebase.

## Installing

Drop the folders into your Hermes skills directory:

    ~/AppData/Local/hermes/skills/<category>/<skill-name>/

On Linux or macOS that's `~/.local/share/hermes/skills/`. The category folder is arbitrary; Hermes
only needs a `SKILL.md` at the root of each skill directory.

## Scope and conduct

Everything here assumes authorisation: a published scope, a VDP, or a signed engagement. The rules
that keep it that way are in `SKILL.md` under Non-negotiables. Only listed assets get traffic, no
scanners against live bounty targets, the minimum request needed to prove reachability, and never
someone else's credentials or data.

## Licence

MIT, except `humanizer`, which ships with its own LICENSE file.
