---
name: general-mechanics-style
description: Draft or restructure scientific text using the General Mechanics writing style. Enforces the Setup-Derivation-Falsification structure, precise internal references, and localized Literature Notes.
---
# General Mechanics Writing Style

Applies the specific structural and stylistic conventions of the "General Mechanics" framework for scientific writing.

## When to Use

  - To author or restructure physics/math texts utilizing strict corollary blocks.
  - To format internal references and external literature notes precisely without disrupting mathematical flow.

## Core Conventions

### 1. Internal References

  - **No Vague Pointers:** Never use "see above" or "see the previous section."
  - **Equations:** Reference by precise number in parentheses: `(2.1)`, `(4.55)`.
  - **Sections:** Reference by section symbol or exact number: `§3`, `4.1.2`, `*2.3`.
  - **Appendices:** Reference explicitly: `App. A`, `App. B`.
  - **Cross-referencing:** Treat the document as a relational database; every claim must point to its exact logical predecessor.

### 2. Literature Notes

  - Do not use traditional inline citations that disrupt the mathematical flow.
  - Collect external references at the very end of a section or block under a `Literature note.` inline header.
  - **Format:** `Literature note. [Topic]: [Author] [[RefNumber]]; [Topic]: [Author] [[RefNumber]].`
  - *Example:* `Literature note. Geometric flux/Stokes: Frankel [1]. Poynting/export in EM: Jackson [2].`

### 3. The Corollary Block Template

When structuring derived consequences, use this strict hierarchy of bolded inline headers:

  - **Setup.** [Define the geometry, boundary, and explicit assumptions. E.g., "A narrow tube T connects..."]
  - **Derivation.** [Mathematical derivation proceeding only from setup and stated axioms. Cite internal equations heavily.]
  - **Specialization.** [Apply the derivation to a specific dimensional or operational case (e.g., 1D tube, 3D spherical).]
  - **Calibration.** [Map the abstract fields to measured sectors or operational units.]
  - **Falsification.** [Provide a concrete, quantifiable test that would contradict the derivation.]
  - **Provenance.** [List the internal reference numbers for the axioms/equations used. E.g., `(2.4), (2.3), (2.9)`.]
  - **Literature note.** [List external sources related to the concepts.]

## Tone and Style

  - Terse, declarative, and heavily reliant on mathematical notation.
  - Zero filler or rhetorical framing.
