# A harness that proves nothing

Every claim in a code or contract report rests on a test, and a test is itself a claim. These are the shapes that read exactly like proof and are not. Run the matching check before you believe an output, and before you let an agent's "REPRODUCED" into a report.

## The eight shapes

**1. The test creates the balance it then steals.** A sweep or withdraw function is called on a contract that only holds funds because `deal()` or a `transfer` in the setup put them there. No deployment funds that address, so the "theft" is the test robbing itself.
Check: before the exploit step, print the asset's balance on the real deployment or state why it would be non-zero. A router holding dust is not a router holding user funds.

**2. The harness grants a role no deployment grants.** The attacker is seeded as admin because the test was easier to write that way, or the permission layer is skipped entirely.
Check: the attacker's identity and role must come through the same path a real request takes. If the test calls the DAO or the handler directly, it proves a defect in the handler and nothing about reachability.

**3. The mock stands in for the target.** A locally deployed copy with different constructor arguments, a stub contract, a fake API — and the finding is really about the stand-in.
Check: attach to the live address where one exists, and if you cannot, say "local deploy" in the same sentence as the impact.

**4. The same party is on both sides.** The "victim" is the attacker's own second session, or the second account was never created.
Check: the victim's data must differ — different object ids, different names, different balances. Quote both.

**5. The shim supplies an input no real caller can send.** A struct built by hand instead of parsed from the wire, an invented request context, an argument the public entry point never forwards.
Check: does the malicious input pass through the target's own parser on the way in? If the test skips the parser, the wire format may forbid the input entirely.

**6. The claim is a negative dressed as a positive.** The test shows that something does *not* happen, or a panic in a path no caller reaches. Real, and worth nothing.
Check: state what the attacker gains, in funds or data, and whether the test printed it.

**7. Absence of evidence from a search whose output was truncated.** "Nothing calls this function" derived from a search that stopped early, while the caller sat in `scripts/`, a systemd unit or a molecule test.
Check: re-run the symbol search unfiltered, then look in the places a call hides — init units, entrypoints, CI files, cron, the second language in the tree.

**8. The control was never run.** If the honest path also fails, the harness is broken and both results are meaningless.
Check: every test needs a passing control beside it — a valid token rejected by nothing, a legitimate caller succeeding, the same request with the correct value going through.

## The one question that kills most of them

Ask what the test would print if the bug did **not** exist. If the answer is the same output, the test is not testing the bug. If the answer is "it would revert", the test is testing a revert and not an exploit.

## Where this ends up

The evidence a report needs is a test that fails because of the defect and a control that passes beside it, with the victim's asset measured before and after. When a hunter cannot get there, the honest label is HYPOTHESIS, and a hunter that says so has finished its job — several did, and the claims they refuted themselves were the cheapest saves of the night.
