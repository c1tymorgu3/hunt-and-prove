# VRT 1.19.1 — classify before you submit

Bugcrowd's Vulnerability Rating Taxonomy. The category you pick in the submission form decides the
priority the triager sees first, and a node whose priority is 5 pays nothing however good the bug is.

## Getting it

    curl -s https://bugcrowd.com/vrt.json -o vrt.json              # current version, ~204 KB
    curl -s https://bugcrowd.com/vulnerability-rating-taxonomy/1.19.1.json -o vrt-1.19.1.json

Structure: a list of 37 categories, each with `children` (subcategory) and `children` again
(variant). **Only variants carry a `priority`.** Some subcategories carry one directly, with no
variants of their own.

## Looking it up

Use `scripts/vrt_lookup.py <keyword>` (flattens the tree and prints every matching path with its
priority). Read the priority on the node you are about to select, not on its parent.

## The traps that cost us submissions

- **`Application-Level Denial-of-Service (DoS) > App Crash`** has only two variants, both mobile
  and both **P5**: `Malformed Android Intents`, `Malformed iOS URL Schemes`. A native or service
  crash has no P4 node under `App Crash`. Pick `Application-Level Denial-of-Service (DoS) > High
  Impact and/or Medium Difficulty` (P3) or `> Critical Impact and/or Easy Difficulty` (P2), or the
  `Denial-of-Service (DoS)` subcategory `Tenant-Scoped` (P4) / `Application-Wide` (P2).
- **`Cryptographic Weakness > Insufficient Entropy > Pseudo-Random Number Generator (PRNG) Seed
  Reuse`** is **P5**. `Limited Random Number Generator (RNG) Entropy Source`, `Predictable PRNG
  Seed` and `Small Seed Space in PRNG` are P4. Same family, two priority levels apart.
- **`Sensitive Data Exposure > Sensitive Data Hardcoded > File Paths`** is **P5**. Hardcoded
  credentials are not: `Disclosure of Secrets > For Internal Asset` P3, `For Publicly Accessible
  Asset` P1.
- **`Sensitive Data Exposure > Disclosure of Secrets > Intentionally Public, Sample or Invalid`**
  is P5 — the exact node a triager reaches for when the "secret" is a public identifier.
- **Side-channel**: `Cryptographic Weakness > Side-Channel Attack > Timing Attack` is P4 in the
  taxonomy, but most crypto programs exclude timing in their own brief. The taxonomy priority does
  not override the program's exclusion list.
- **Prototype pollution is not a VRT 1.19.1 category.** There is no node for it. For a JS prototype
  bug, the nearest nodes with a real priority are under `Client-Side Injection` or
  `Server-Side Injection`; pick one whose own priority is not 5 and argue the class in the text.
- **Some classes have no node at all, and the picker will still accept a wrong path.** A submission
  was filed under `Active Directory (AD) > Sensitive Data Exposure`; the AD category contains only
  `Kerberos Abuse` and `Configuration Weaknesses`, so the path does not exist, no priority was sent
  to the triager, and the finding had no suggested severity at all. Before submitting, confirm the
  path resolves to a node in the flattened taxonomy — a plausible-sounding path that does not exist
  is worse than an honest near-miss, because it silently discards the classification.
- **Data-retention and "deleted but not deleted" findings have no node.** Nothing describes stored
  data outliving its deletion. The defensible near-miss is `Sensitive Data Exposure > Disclosure of
  Secrets > For Internal Asset` (P3) when the residue is a secret or private content reachable by
  someone who should not have it; `Insecure Data Storage > Server-Side Credentials Storage >
  Plaintext` (P4) only when the residue really is a credential. Say in the text which node you
  picked and why, rather than filing under a category that maps to nothing.

## Categories (37)

AI Application Security, Algorithmic Biases, Application-Level Denial-of-Service (DoS), Automotive
Security Misconfiguration, Blockchain Infrastructure Misconfiguration, Broken Access Control (BAC),
Broken Authentication and Session Management, Client-Side Injection, Cloud Security, Cross-Site
Request Forgery (CSRF), Cross-Site Scripting (XSS), Cryptographic Weakness, Data Biases,
Decentralized Application Misconfiguration, Developer Biases, External Behavior, Indicators of
Compromise, Insecure Data Storage, Insecure Data Transport, Insecure OS/Firmware, Insufficient
Security Configurability, Lack of Binary Hardening, Misinterpretation Biases, Mobile Security
Misconfiguration, Network Security Misconfiguration, Physical Security Issues, Privacy Concerns,
Protocol Specific Misconfiguration, Sensitive Data Exposure, Server Security Misconfiguration,
Server-Side Injection, Smart Contract Misconfiguration, Societal Biases, Unvalidated Redirects and
Forwards, Using Components with Known Vulnerabilities, Zero Knowledge Security Misconfiguration,
Active Directory (AD).

## Before submitting

1. Look up the class. Find the exact node. Read its priority.
2. If it is 5, either find the sibling node at 4 or change what you claim the impact is. Do not
   submit and hope.
3. **Verify the node exists** in the flattened tree, not just that the words sound right. A path
   that resolves to nothing sends no suggested priority, and the triager then picks a level for you.
4. Cross-check the program's own severity model. A program that publishes its own P-levels
   (Fireblocks does, in `SECURITY-MODEL.md`) overrides the taxonomy for triage, and its exclusion
   list overrides everything.
