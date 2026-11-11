# GraphQL testing when introspection is off

Modern Apollo deployments disable introspection and suppress field suggestions, which makes the endpoint look untestable. It is not — the validation errors are a full schema oracle. This is the procedure that enumerated an entire production schema one field at a time.

## 1. Confirm what is on

```
POST /api/graphql  {"query":"{__typename}"}      -> 200 {"data":{"__typename":"Query"}}
POST /api/graphql  {"query":"{__schema{queryType{fields{name}}}}"}
     -> 400 GRAPHQL_VALIDATION_FAILED "introspection is not allowed"
```

**Do not report "introspection enabled/disabled" either way.** Disabled introspection is a hardening control; enabled introspection is normally informational at best. Neither is a finding.

Check the method the edge allows: `GET /api/graphql` frequently returns a WAF page while `POST` returns 200. A blocked GET says nothing about POST.

## 2. Enumerate fields with aliases

One request can test many candidate field names by aliasing them onto the same root:

```graphql
{ consumer { _0:id _1:consumerId _2:userId _3:email _4:phoneNumber … _67:ssoId } }
```

- A **200 with a value or `null`** = the field exists.
- A **400 `Cannot query field "x" on type "Y"`** = it does not.

If an alias/complexity guard rejects the batch (a deliberate anti-amplification control), drop to 5-10 aliases per request. Two aliases on `__typename` succeeding while a wide alias set fails tells you the guard is per-object, not a global limit — that is a control working as designed, not a bug.

## 3. Ask whether the root field can be pointed at someone else

This is the IDOR question, and the error message answers it outright:

```
{ consumer(id:"1") { id email } }
  -> 400 Unknown argument "id" on field "Query.consumer".
```

If the root field takes **zero arguments** and resolves from session context, there is no parameter to tamper with and object-ID IDOR is structurally impossible on that field. Record that as a clean negative and stop hunting it — do not keep probing "just in case".

A session-scoped field returning `null`/`isGuest:true` for a guest session is **correct behaviour**, not a data leak. The leak test is whether an authenticated session returns *another* subject's data, which needs a real account.

## 4. Controls you will meet, and should not report

- Introspection disabled; no "Did you mean" suggestions.
- Query batching disabled (an array of operations is rejected) — no batch-based brute force.
- Alias / complexity guard.
- Automatic Persisted Queries bound to the hash: replaying a known hash with a modified `query` or `variables` fails.
- CORS refusing foreign and `null` origins.

All of these are the target being *good at this*. Note them as "over-hardened, no finding" in the output file so the next pass does not re-test them.

## 5. Where the money actually is

A thin guest schema usually means the interesting surface is elsewhere:

1. **Authenticated field-level authz** — the same schema resolves far more for a logged-in consumer. Needs a session, so it is the reason to spend the account-creation budget.
2. **Mutations** — map them, but do not execute state-changing ones without the user's approval; a mutation you fired is a change you made to production.
3. **Fields that DO take arguments** — object-ID IDOR lives there. Harvest real operation shapes from the JS bundles (persisted-query hashes, `operationName`, `extensions`) instead of guessing field names.
4. **Variables-level trust** — price, quantity, discount, fee fields accepted from the client in a quote/cart mutation. Business-logic payouts hide here.

## 6. Write it up as a null result properly

"Schema fully enumerated, one root field, zero arguments, no leak" is a valuable, honest deliverable: it stops the next pass from repeating the work. Put the enumerated field list, the exact probes, and the verdict in the findings file — a clean negative with evidence is worth more than a speculative Low.
