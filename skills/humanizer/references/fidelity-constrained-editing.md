# Humanizing text that is bound to a source

Use when the document must not gain claims: audits, postmortems, incident
reviews, evidence write-ups, or anything the user framed as "only use what is in
the document". The usual humanizer pass assumes the writer owns the claims. Here
the writer owns the phrasing only.

## The split

| Layer | Status on this class of text |
|---|---|
| Content patterns (significance inflation, promotional tone, weasel attributions, `-ing` analysis) | Remove. They are invented claims |
| Style, rhythm, vocabulary (em dash, bold, list shape, openers, sentence length) | Apply freely |
| Personality and soul (opinions, reactions, mixed feelings, asides) | Forbidden unless the source already has them |

Voice has to come from rhythm, sentence variety, and plain verbs. Not from
added judgment. A neutral report with varied sentences reads human; an
opinionated summary of someone else's findings reads fabricated.

## Hedges that surrender the claim

The defect in this class of text is rarely an added opinion; it is an added
concession. "If the team considers this intentional, I would rather hear that"
is not modesty, it is an invitation to reject the document, and it gets written
because the author is nervous about being wrong.

- Cut every clause that hands the reader an exit from the claim. State the
  finding, state its limit once, stop.
- Keep the limit that is evidence ("reachability depends on a config outside the
  repository"). Drop the limit that is deference ("if this is intentional I
  respect it").
- A report about someone else's work still asserts something. Voice comes from
  how plainly that is said, not from how much room is left to disagree with it.
- The same rule kills the commercial aside: what the work pays, or what the
  author hopes to earn from it, never belongs in the document.

## Pronouns

- Match the source's stance. A first-person review stays first person. Neutral
  third person on a personal document reads as a press release and discards the
  accountability the document exists to demonstrate.
- Keep the source's passive where it does not name an actor. "Kayıtlar silindi"
  becoming "kayıtları sildim" adds an admission the source never made;
  "trafik ölçüldü" becoming "trafiği ölçtüm" adds an actor for nothing.
- Do not invent an author either. A sudden "we" is as false as stripped "I".

## Do not touch

- Label legends (verified / no evidence / corrected) and every sentence that
  uses them. Rewording changes what they assert.
- Quoted source passages, code blocks, tables of technical constants, numbers,
  offsets, keys, header names.
- Section order and headings the user prescribed, even when they feel formulaic.
  The container is not the tell.

## Tells that survive translation

The 34 patterns are shaped by English. These read as machine-written in any
language and are the ones to hunt first:

- every paragraph the same length, every bullet the same grammatical shape
- bold lead-in plus colon where the item is a full sentence (inline-header list)
- scaffolding in front of a sentence that already says it: "Sonuç:", "Önemli:",
  "Ayrıca:", "Not:"
- a table followed by one sentence restating the table
- nominalizations where a verb exists ("doğrulama yapıldı" → "doğruladım" or
  "doğrulandı")
- em dash in a heading; use a colon
- bold on every second noun phrase; keep bold for two or three verdicts total
- three-item lists that could be one sentence

## Working order

1. Read the source and the deliverable. Mark the sentences that carry evidence:
   numbers, labels, quotes, paths.
2. Rewrite prose around them. Those sentences stay byte-identical unless the
   scaffolding itself is the problem.
3. Convert bold-lead bullet lists to prose when the items are sentences. Keep
   bullets when the list is a checklist of distinct facts.
4. Vary paragraph length deliberately: one short paragraph next to a long one
   does more than any vocabulary swap.
5. Audit out loud before reporting: name two or three things that still read as
   machine text, including the ones left on purpose (prescribed structure,
   source sentences you refused to edit).
6. Report the remaining tells. Do not claim a clean pass.
