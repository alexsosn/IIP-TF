# Issue #49 — research → plan → RED → GREEN → independent review

1. Execute the exact pinned Brown full-source responsibility inventory, including
   unexpanded XInclude and observed `name` vs `persName` variants.
2. Derive a native node/feature schema from measured source shapes and update
   schema 0.1/reference documentation only through an explicit rationale.
3. RED tests for repeatable contributions, role text (including typos),
   optional source IDs, non-lossy names, unsupported markup fail-closed, and
   duplicate local IDs across files.
4. GREEN metadata parser enrichment and TF serialization without sidecars.
5. Verify the full 5,535-record native TF gate, updating frozen counts only
   for newly justified contributor/authority nodes.
6. Independently review exact final head against Brown XML, IR and loaded TF
   query results; repair blockers before merge.
7. Unblock #6 only after researcher queries can retrieve this provenance.
