---
name: paper-formatter-gm
description: Format physics and math papers using the strict General Mechanics style. Use when the user asks to format, restructure, or compile AFC/AOD research bundles or manuscripts.
---
# General Mechanics Paper Formatter

This skill enforces the rigid, dynamic "General Mechanics" writing style for scientific manuscripts, particularly when translating Axiomatic Fundamentalism Calculus (AFC) or Axiom of Distinction (AOD) research bundles into readable, narrative-driven LaTeX.

## When to Use

  - When structuring a LaTeX manuscript directory.
  - When ingesting AFC or AOD research bundles to rewrite them.
  - When the user asks to format a paper, apply General Mechanics style, or fix "boring" academic formatting.

## 1. LaTeX Project Architecture

Always structure the paper using a modular directory tree to prevent structural drift:

  * `main.tex`: Root file containing the document class, preamble, and `\input{}` directives.
  * `sections/`: Individual logic blocks (e.g., `01-axioms.tex`, `02-corollaries.tex`).
  * `figures/`: Standalone `.pdf` or `.tikz` assets.
  * `appendices/`: Reference tables, Glossaries, and Symbols.

## 2. Ingesting and Translating AFC/AOD

When given raw AFC or AOD texts (which often use a fragmented "Axiom -> Choice -> Consequence" legalistic format):

  * **Strip the legal bloat:** Do not output standalone "Choices" or fragmented definitions.
  * **Translate to Blocks:** Rewrite the raw logical concepts strictly into the General Mechanics "Corollary Block" format (see Section 3).
  * **Consolidate:** Sweep all definitions and assumptions smoothly into the `Setup` and `Derivation` blocks.

## 3. The Corollary Block Format

Every derived consequence or major logical result must rigidly follow this exact sequence of bolded inline headers:

  * **Setup.** Declare the geometry, boundary, and explicit assumptions.
  * **Derivation.** Execute the mathematical steps strictly from the setup and axioms.
  * **Specialization.** Apply the derivation to dimensional or operational cases (e.g., effective 1D flux-tube, isotropic topology).
  * **Calibration.** Map abstract fields to measured sectors using a constant-free, one-datum linear calibration or state the bounds (e.g., channel capacity).
  * **Falsification.** Define a concrete, quantifiable test that would contradict the specific derived statement. This must be a physical or mathematical breaking point.
  * **Provenance.** List the exact equation and axiom numbers used in the derivation.
  * **Literature note.** Collect external references at the very end of the block, formatted as `Topic: Author [RefNumber]`. Do not use inline citations.

## 4. Style and Rhythm Enforcement

  * **Internal References:** Treat the document like a relational database. Use precise, unique anchors (e.g., `§3.2`, `(4.55)`) instead of vague relational pointers ("see above").
  * **The Rule of One:** The title and abstract must communicate a single central contribution. All subsequent derivations tie directly back to this premise.
  * **Text-Figure-Equation Rhythm:** Break down complex derivations by cycling through a plain-text conceptual summary, the precise equation, and a placeholder for a labeled figure.
  * **Active Voice:** Eliminate passive constructions (e.g., "It was found that"). State findings directly and aggressively to maintain narrative momentum. Zero filler or rhetorical framing.