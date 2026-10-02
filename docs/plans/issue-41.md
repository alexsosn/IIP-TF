# Issue #41 plan — evaluate text-fabric-factory

Research: `docs/research/text-fabric-factory-evaluation.md`

## Gate result

The research gate rejects TFF as a production parser/converter dependency before
an implementation/performance spike. The incompatibilities are semantic, not
micro-performance issues: vanilla TFF creates TEI-element node types, offers
word/token/char slot populations rather than IIP's sign/event contract, strips
XML namespaces during its walk, treats teiHeader as corpus text, and can continue
after malformed XML is skipped.

A full TFF benchmark would first require reimplementing IIP-TF's frozen semantic
pipeline as custom TFF hooks. That would be migration work before the candidate
has passed the architecture gate.

## Planned change

1. Record the decision as ADR-0002.
2. Keep `text-fabric-factory` out of runtime and development dependencies.
3. Preserve the canonical parser -> IR -> writer boundary.
4. In #5, evaluate direct use of the already-installed
   `tf.convert.walker.CV` only if it simplifies deterministic IR serialization.
5. In #8, use TFF's generated app/documentation conventions as reference material
   where useful.

## TDD/test gate

No production code changes are planned, so there is no behavioral RED/GREEN
cycle to manufacture for this research-only decision.

Verification is instead:

- exact diff review confirms no package dependency or runtime import is added;
- existing CI remains green;
- the ADR is checked against the accepted schema 0.1 and the pinned full-source
  evidence cited in the research document;
- independent adversarial review challenges the conclusion against TFF source
  and representative IIP files before merge.

If review identifies a TFF extension point that can satisfy the frozen schema
without reproducing the current parser, reopen the implementation-spike path
rather than merging the rejection prematurely.
