<!-- Connective punctuation, the catalogue's exemptions, and the misfires
found by running the detector over real prose. -->

The build failed — the token had expired. <!-- expect: PG001 -->

The build failed -- the token had expired. <!-- expect: PG001 -->

The cache — which is per host — is cleared on boot. <!-- expect: PG001 PG001 (misfire: true parenthetical; density-only) -->

Apply by default; don't ask. <!-- expect: PG002 -->

Tiers are full; click; read.

- Edge cases; boundary values.

Keep it lean: every line is loaded context. <!-- expect: PG003 -->

Enumerate scenarios in three buckets:

- Edge cases.
- Error states.

The reply was short: "no".

Per scenario, state: trigger, observed behaviour, expected behaviour.

Keep it lean: every line counts, and none is free. <!-- expect: PG003 (one comma is a clause, not a list) -->

Say where it is (file:line) and the class.

Run it at 10:30 on Tuesday.

- **MD022** — headings surrounded by blank lines. <!-- expect: PG001 (misfire: bullet label dash; the skill's own catalogue uses it) -->
