# Smart-contract triage

Use when a bounty scope is a list of contract addresses rather than a repo or a host. The work is
reading verified source and confirming one claim against chain state, not fuzzing.

## What pays and what does not

**Pays:** an unauthenticated caller reaching a write or a privileged read. The strongest shape is a
trust inversion in an access check — a modifier that asks a question the caller controls:

```solidity
modifier onlyExternalAdmin(address token) {
    if (!ILatamStableToken(token).hasRole(ILatamStableToken(token).DEFAULT_ADMIN_ROLE(), msg.sender))
        revert NotExternalAdmin();
    _;
}
function registerToken(address token, address destination, uint256 cap)
    external onlyExternalAdmin(token) { ... }
```

`token` is an argument, so the caller supplies the contract that answers the question. Deploy anything that
returns `true` from `hasRole` and the check passes. Look for this shape wherever a modifier takes an
address argument it then interrogates.

**Does not pay, however good it looks in a report:** one EOA holding mint, freeze, upgrade, pause and
compliance rights across several deployments; a bridge that accepts a caller-supplied source-chain tuple
from a trusted operator role; a cap that is larger than supply; a missing global supply invariant. Each of
these needs a privileged key to exercise, so the answer is "compromise of a key is out of scope" and the
triager is right. Write those to the user as a hardening note, not to the program.

A related trap: a missing cross-chain proof (no merkle root, no attestation, no signature, caller picks the
nonce) reads as Critical and prices as nothing, because the only caller who benefits already holds the
role. Grade it by who can call it, never by what they could do.

## Confirm it yourself before writing it up

Two `eth_call` requests settle a state claim. No node, no toolchain, no fork.

```python
import json, urllib.request
RPC = 'https://ethereum.publicnode.com'          # llamarpc 403s scripted clients; publicnode does not
def call(to, data):
    body = json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_call',
                       'params':[{'to':to,'data':data},'latest']}).encode()
    req = urllib.request.Request(RPC, data=body,
        headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(req, timeout=30))['result']
```

Selectors you can hardcode: `name()` `0x06fdde03`, `symbol()` `0x95d89b41`, `decimals()` `0x313ce567`,
`totalSupply()` `0x18160ddd`. For anything else compute it — `pycryptodome` has keccak, `hashlib.sha3_256`
does **not** (NIST variant, wrong hash):

```python
from Crypto.Hash import keccak
k = keccak.new(digest_bits=256); k.update(b'tokenConfigs(address)')
selector = k.hexdigest()[:8]        # -> 1b69dc5f
```

A cross-check worth doing: compute the selector of the function named in a child's report and compare it to
the selector in the transaction it cites. A match means the child actually read the source; a mismatch means
the report is built on an assumption.

Decode the return as consecutive 32-byte words: an `address` is the last 20 bytes of a word, a `bool` is the
final byte, a `uint256` is the whole word. A three-word return of
`address, 1e18-scaled cap, 1` is `destination, dailyMaxMint, exists`.

State that is already polluted is the strongest evidence you can hand a triager: a fake token registered in
the live allowlist, readable today, needs no exploit and no permission to demonstrate.

## Multi-chain deployments

The same contract address usually exists on every chain the product supports, behind an ERC-1967 proxy
pointing at one shared implementation. Diff the deployments rather than auditing the same code twice:
`owner()`, paused state, initializer state, and every hardcoded address (bridge, oracle, treasury). A new
chain is where an initializer is left un-run or an owner is still the deployer. Cross-chain message
validation — is the source chain and nonce bound, can a message be replayed — is the highest-value target
on any bridge, and the first thing to check when a pair of deployments claims to talk to each other.

## Proving it with a fork test

When the scope includes a repo *and* a deployed address, a Foundry fork test is the strongest evidence
there is: it runs the real bytecode against real state, and a triager can re-run one command. Three
rules keep it honest.

- **Attach to the deployed address, not a local deployment.** `forge test --fork-url <RPC>` plus an
  interface bound to the in-scope address tests the contract the program actually ships. A `new Contract()`
  in `setUp()` with your own constructor arguments is a different contract, and a bug in it says nothing
  about the deployment. Pin the block number once the test is stable so the evidence stays reproducible.
- **Assert on assets, not on the absence of a revert.** `balanceOf` and `ownerOf` before and after, printed
  in the assertion message. "It did not revert" is not impact and gets closed as such.
- **Do not manufacture the attacker's permissions.** `vm.prank` / `vm.deal` can hand an address approvals or
  tokens no real user would grant, and a mock token can answer whatever the test wants. If the exploit needs
  an approval, show who signed it and why they would.

Pick the RPC before writing the test: scripted clients are refused by some public endpoints, so probe one
with a trivial `eth_call` first and fall back until one answers. See the selector recipe above for that probe.

## When the platform is Immunefi

The bounty page, not the code, decides what a finding is worth there. Read four things before opening a repo.

- **The scope is often a list of repositories, not addresses.** Check first. With no address, the repo *is* the asset, and the evidence shape flips: a test that deploys the in-scope contracts with the project's own script is the right proof, and the fork rule above does not apply because there is no deployment to attach to. Say in the report which of the two you did and why.
- **The proof has to run.** A finding with no executable test is rejected by the platform before a human reads it, so a read-only claim is a note to yourself, not a submission. Budget the harness into the night.
- **Primacy of impact.** Many bounties pay the impact listed in scope even where the deployed bytecode and the repository diverge. Quote the impact line verbatim in the report and make the test demonstrate that impact rather than a related one — a test that proves something adjacent gets argued down.
- **Trusted-role exclusions are wide and they are the first thing that kills an access-control finding.** "Issues requiring a malicious, compromised or careless trusted role" removes whole classes: the factory owner, the oracle admin, the pool admin acting inside their own bounds. Read the excluded actors and ask whether your attacker is one of them before writing the test; if they are, the finding is a hardening note however clean the harness.
- **Intended behaviour is often listed in the impact table, not in a policy page**: a pool halting on a stale feed, a price provider serving a bad price, an admin changing something inside its configured cap. Those are out of scope by name, and they are exactly what a fresh reader mistakes for a denial of service.

Competition on this platform is measured by **paid bounties and the listing date**, not by report count. Zero paid reports on a listing days old means nobody has had time to look; zero on an asset a year old means it is hardened. Report both dates and the paid count when you recommend one.

## Reporting

Quote the verified source line, the address, and the exact call that returns the state. Then state the
limit in one sentence: "minting still requires MINTER_ROLE, so this is registry integrity, not fund loss."
A Low that names its own ceiling gets accepted; a Low dressed up as Critical gets dropped to Informational.
