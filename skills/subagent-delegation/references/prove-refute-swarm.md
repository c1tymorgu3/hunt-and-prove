# The prove/refute swarm, v2

The pattern for covering a target's attack surface in one night with no second chance at the
submission slot. v1 was 8 hunters plus 7 refuters; it verified well and produced nothing, because
most of the eight vectors could never have paid. v2 spends fewer agents and puts a gate in front.

## Shape

**Gate first.** Every vector arrives as four lines: attacker, evidence (`file:line`), gain,
and the most likely killer sentence. A vector whose gain is an error message, a revert, self-harm,
or something an admin could already do is dropped before it gets an agent. See the `Phase 0`
section of `bug-bounty-hunting`. The `İMKANSIZLIK` line becomes the refuters' first target.

**5 hunters, one vector each**, chosen from the gate's survivors by how cheaply they can be
executed. Each writes one file and one record in `claims.json`. A claim without an executed
command is not a claim.

**5 refuters, one permanent question each**, down from seven:

| role | question |
|---|---|
| R1 reproduction | does it happen again from a clean copy, and does the harness fabricate its input? |
| R2 attacker and gain | who is the attacker, what do they obtain, does that party already hold the capability? |
| R3 novelty | in the test suite, fixed in history, in an advisory, already in the crowdstream? |
| R4 second control | does something upstream already mask, scope, redact or block the payoff? |
| R5 adversary | write the triager's rejection while the claim is being born, not at the end |

R4 is the one v1 did not have, and it is the one that killed our best lead: a real confused-deputy
primitive whose payoff was a secret the vendor's own API already returns as `<redacted>`. Ask it
about every claim, early, with a live call where one is possible.

## claims.json — records instead of prose

    {"id":"E3-1","title":"page reads the extension session token","file_line":"background.js:412",
     "attacker":"any web page the victim visits","payoff":"the victim's session cookie",
     "command":"node harness/e3.js","output_file":"out/e3-run.log",
     "status":"EXECUTED|STATIC|REFUTED","second_control":"none|redacted|edge|documented"}

Markdown is written only for a claim that passes. Everything else lives in the JSON, which is what
lets the parent dedupe, gate and rank mechanically instead of re-reading eight essays per refuter.

## Staged pipeline, not parallel-and-poll

    stage 0  gate the hypotheses (parent, 3 min)       8 candidates -> 3-5
    stage 1  hunters (5 agents, 25 min)                claims.json + raw logs
    stage 2  first cut: R1 + R2 (10 min)               does it exist, does it pay
    stage 3  survivors only: R3 + R4 + impact work     novelty, second control, real data
    stage 4  adversary (1 agent)                       report, or a clean no

**Stop rule:** if nothing passes stage 2, the round ends there. Stages 3 and 4 are not paid for.

## Converge on the first passer

v1 ran all eight vectors to completion while one of them was already the answer. The moment a claim
clears stage 2, stop the remaining hunters and put everyone on weaponising it: minimal repro, real
data, two accounts, a clean machine, captured output. One finished finding beats eight half-audits.

## The survival test

A claim survives only if all five hold: it lives in the target's own code (not a vendored dependency,
not test-only code), it was executed, the attacker position is real and does not already hold the
capability, no exclusion covers it, and its taxonomy node pays. Apply them in that order — the first
is the cheapest to check and the most often wrong.

## Pitfalls

- **Hunters manufacture their own input.** A test that calls an internal method with an argument no
  real message can carry proves nothing. R1 exists for this; ask it explicitly whether the input
  went through the real parser.
- **A vendored dependency is neither automatically in nor out.** Check whether the package is the
  target's own fork before deciding.
- **Refuters outrun the hunters and review an empty directory.** Have them write the board first
  and fill it as files appear.
- **Do not let a refuter soften its verdict.** R2's usual failure is calling a malicious-server bug
  "remote"; make it name the attacker in one of four fixed words.
- **A clean no is a result.** Eight targets in one night produced twelve real defects and zero
  payments, because every payoff sat behind a second control. Recording why each claim died is what
  makes the next gate sharper.
