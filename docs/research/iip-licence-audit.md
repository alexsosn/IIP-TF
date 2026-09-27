# IIP licence and redistribution audit

**Scope:** issue #2 research for the pinned Brown IIP source revision `0b7dc8358ccdfd0c9391f049da4839fbd91c26e5`.

## Project-level terms

The official IIP copyright and citation page states that the project makes its data available for use and reuse under the **Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)**.

Project citation guidance identifies:

> Michael L. Satlow, ed. *Inscriptions of Israel/Palestine*, Brown University. DOI: 10.26300/pz1d-st89.

The current IIP search site likewise displays the project DOI and CC BY-NC 4.0 in its site-level publication metadata.

Authoritative sources checked:

- https://www.inscriptionsisraelpalestine.org/copyright/
- https://www.inscriptionsisraelpalestine.org/about/
- https://search.inscriptionsisraelpalestine.org/
- DOI: https://doi.org/10.26300/pz1d-st89

Checked: 2026-09-27.

## Important rights boundary

The same official copyright page says that IIP largely republishes scholarly editions of epigraphic material with attribution and that the copyright of scholarly contributions remains with their contributors. It also says that images are either public domain or used with permission and that IIP generally does not itself hold image copyright.

Therefore IIP-TF must not describe the source situation as though CC BY-NC 4.0 extinguished or replaced all rights and attribution obligations in the underlying editions, contributed scholarship, or images.

For the initial TF release:

- generated corpus data derived from IIP must carry the IIP project attribution, DOI, and CC BY-NC 4.0 terms;
- source bibliography and inscription-level provenance must remain queryable so researchers can identify and cite the underlying editions;
- the release documentation must tell researchers to consult/cite the original source edition where IIP supplies it;
- image binaries are out of scope for the corpus release unless their individual reuse status is separately established;
- facsimile/image references and source credits may be preserved as metadata without copying the image itself;
- the MIT licence in this repository applies only to IIP-TF-authored software and software documentation.

## Per-record licence markup

The pinned EpiDoc snapshot is not internally uniform: the corpus-wide audit finds explicit `<licence>` / CC BY-NC / DOI markup in only a small subset of files. This is not evidence that the remainder has different project terms; older/current files frequently rely on shared publication metadata or XInclude-era project conventions rather than embedding a complete licence block.

Consequently, release licensing should be derived from the authoritative project-level publication terms, while retaining per-record licence markup where present as source provenance. The converter must not infer a different licence merely because an individual XML record omits an inline `<licence>` element.

## Release requirement

Before publishing generated TF data, release validation must verify that:

1. the generated corpus metadata names IIP/Brown as upstream source;
2. the exact source revision is recorded;
3. CC BY-NC 4.0 and the DOI are present in corpus/release documentation;
4. underlying bibliographic/source attribution remains available;
5. no image binary is redistributed without a separately justified licence path.
