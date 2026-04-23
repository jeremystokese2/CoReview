# Tone & Hedging Guidelines

These rules govern how the organisation's documents express claims, recommendations,
and advice. The goal is a careful, trustworthy voice: confident where evidence is
strong, hedged where it is not.

Each rule below has an explicit `rule_id`. Use that exact id in the `rule_id` and
`citations[].rule_id` fields of issues.

---

## Definitive Language

### rule: tone.definitive_language
**Title:** Avoid unhedged guarantees
**Severity:** high

Documents must not make absolute guarantees about outcomes, capability, or
performance. Absolute terms such as "will", "guarantees", "ensures", "always",
"every time", "never fails", "100%", "completely eliminates" create legal and
reputational risk when an edge case exposes them.

Hedge absolute claims with words that acknowledge conditions, probability, or
typicality: "may", "can", "typically", "in most cases", "under the conditions
described", "is designed to".

Applies to: marketing copy, product descriptions, policy statements, executive
summaries, recommendations. Does NOT apply to direct quotations, statutory
language being cited, or unambiguous factual statements (e.g. "the report was
published in 2024").

### rule: tone.unsupported_claims
**Title:** Unsupported superlatives or comparatives
**Severity:** medium

Claims that use superlatives ("the best", "the most", "industry-leading",
"world-class", "unparalleled") or comparatives ("faster than", "more secure
than") without a cited, verifiable source should be flagged. Either cite the
source, reframe as aspiration ("aims to be"), or remove.

---

## Voice and Register

### rule: tone.passive_voice_overuse
**Title:** Passive voice where active is clearer
**Severity:** low

Passive constructions are acceptable and often correct — particularly when
the actor is unknown, unimportant, or deliberately obscured for policy reasons.
Flag only when:

- The sentence is in passive voice ("A decision was made to ...", "It has been
  determined that ...")
- The actor would be informative to the reader
- Converting to active voice would shorten the sentence or clarify responsibility

Do NOT flag passive voice in procedural / instructional text where the actor is
implicitly the reader ("the form is submitted", "once approval is received").

### rule: tone.nominalisation
**Title:** Unnecessary nominalisation
**Severity:** low

Nominalisation turns verbs into nouns and dilutes prose ("conduct an
investigation" vs "investigate"; "make a decision" vs "decide"; "provide
assistance" vs "assist"). Flag nominalised phrases that could be replaced
with a direct verb without losing meaning. This is a stylistic rule — keep
severity low and do not flag when the nominal form is the accepted term of art.

---

## Clarity

### rule: tone.jargon_undefined
**Title:** Specialised jargon without definition
**Severity:** medium

Specialised or organisation-internal jargon — acronyms, product code names,
process names — should be defined on first use, or replaced with plainer
language. Flag terms that appear without context and that a reader outside
the immediate team would not understand. Do NOT flag well-established
industry-standard terms that the stated audience can be expected to know.

### rule: tone.vague_quantifiers
**Title:** Vague quantifiers
**Severity:** low

Phrases like "many users", "often", "significant improvement", "a number of",
"several" without a concrete number hide the evidence. Either cite the figure
or reframe qualitatively and honestly ("in our pilot, X of Y users...").
