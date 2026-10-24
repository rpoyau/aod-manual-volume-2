# AOD Downstream Usage Paper & Dataset Templates

Use these canonical templates when scaffolding or authoring any downstream AOD Usage release (**Matter I — Elementary elements**, **Matter II — Molecular**, **Matter III — Biomolecular chaining**, or **Intelligence**).

---

## 1. `main.tex` Template (Usage Paper Root Container)

```latex
\documentclass[11pt]{article}
\input{preamble.tex}
\begin{document}
\begin{titlepage}
\begin{center}
{\LARGE Alpha$\leftrightarrow$Omega Dynamics (A$\Omega$D)}

\vspace{0.35em}

{\Large The Hidden Temporal Dynamics of Stokes}

\vspace{0.45em}

{\large\itshape The Art Of The Leprechaun: Fractal Calculus -- $\SADARop$}

\vspace{0.65em}

{\large 43 $^\circ\mathrm{c}$}

\vspace{0.35em}

{\Large <Domain Subtitle: e.g., Matter I -- Elementary Elements>}

\vspace{0.45em}

{\large \AODDocumentAuthor}

\vspace{0.25em}

{\small \AODDocumentDate}

\vspace{0.55em}

\[A\leftrightarrow_{\mu}\Omega\;\longleftrightarrow\;\Omega\leftrightarrow_{\mu}A\]

\vspace{1.35em}

{\small\itshape Epitaph}

\vspace{0.2em}

\[
\mathcal{N}\equiv\infty
\qquad
\mathcal{N}\to\mathcal{N}\to\mathcal{N}\equiv\mathcal{N}
\]

{\small\itshape Comprehension, cooperation, and presence are not prerequisites of AFC.}

\vspace{0.2em}

{\small\itshape Nuff said.}
\end{center}
\end{titlepage}
\tableofcontents
\input{sections/00_scope.tex}
\input{sections/00_native_fixtures.tex}
\input{sections/00_dec_ledger.tex}
% --- Domain Application & Dataset Sections ---
\input{sections/01_domain_applications.tex}
\input{sections/09_prediction_test_fixture_registry.tex}
\appendix
\input{appendices/A_simulation_fixtures_and_context.tex}
\input{appendices/B_quarantined_external_comparison.tex}
\input{appendices/C_coordinate_phase_delta3_fixture.tex}
\nocite{*}
\bibliographystyle{plain}
\bibliography{refs}
\end{document}
```

---

## 2. `sections/00_scope.tex` Template (Scope, Spine & Dataset Quarantine)

```latex
\section{Scope}\label{usage:scope}
This manuscript carries domain application, dataset evaluation, and prediction-test material downstream from the main A\(\Omega\)D note. The main note carries the AF/AFC/A\(\Omega\)D ontology and calculus. This manuscript carries domain calculation records, setup diagrams, input-data and benchmark-dataset evaluations, external-comparison records, error audits, and registry tables.

\subsection{Calculation spine}\label{usage:calculation-spine}
A calculation declares
\[
\mathbf a\vdash(F,R,\partial_T R,\omega),\qquad B=(\partial_TF,\omega).
\]
It forms retained cycle provenance, evaluates branch/hinge/branch, and computes a SADAR value:
\[
C_f[\Sigma]_{\AO},
\qquad
\mathsf{AO}_{\mu}(C)=\langle\Pi_\alpha,H_\mu,\Pi_\Omega\rangle,
\qquad
\SADARop_B(C)=p^D_{C,\AO}A_{C,\AO}.
\]
The boundary value is accumulated by
\[
\Phi^D_{\partial_T R}=\sum_{e\in\partial_T R}\SADARop_B(C_e).
\]
Tables store evaluated values. Tables are not the calculus.

\subsection{Worked-calculation and dataset release}\label{usage:worked-calculation-release}
For an exact A\(\Omega\)-internal fixture ($D0$), form
\[
\text{setup}\to A\leftrightarrow_{\mu}\Omega\text{ calculation}\to \text{fixture comparator}\to \Delta^{\mathbb Z},\delta_3\to \text{audit}.
\]
For an external comparison calculation ($O0/G0\text{--}G3$), form
\[
\text{setup}\to A\leftrightarrow_{\mu}\Omega\text{ calculation}\to \text{observable / target record}\to \Delta,\epsilon,z,\sigma\to \text{error audit}.
\]
For a benchmark-dataset calculation, record
\[
\mathbf a\vdash(F,R,\partial_T R,\omega),\quad \mathcal D_{\mathrm{bench}},\quad \mathcal Q_{\mathrm{required}},\quad \mathcal S=\text{benchmark manifest}.
\]
```

---

## 3. `sections/09_prediction_test_fixture_registry.tex` Template

```latex
\section{Prediction-Test Fixture Registry}\label{usage:prediction-test-registry}
\aodnoteblock{Scope}{This registry records completion fields for domain fixtures, input datasets, and external comparisons. Rows carry their data-support class, active fields, required A\(\Omega\) calculation, and audit artifact.}

\scriptsize
\begin{longtable}{@{}p{0.16\textwidth}p{0.08\textwidth}p{0.16\textwidth}p{0.25\textwidth}p{0.18\textwidth}@{}}
\caption{Prediction-test fixture registry.}\label{tab:usage-prediction-test-registry}\\
\toprule
Record & Class & Active fields & Required A\(\Omega\) calculation & Artifact\\
\midrule
\endfirsthead
\toprule
Record & Class & Active fields & Required A\(\Omega\) calculation & Artifact\\
\midrule
\endhead
% Populate rows with D0, O0, G0-G3, or L0-L3 records
\bottomrule
\end{longtable}
\normalsize

\aodnoteblock{Completion rule}{External-comparison rows record numeric map value, target, residual, percent error, and audit hook. Benchmark-dataset rows record benchmark data table, A\(\Omega\) calculation row, report coordinate, residual, and audit hook.}
```

---

## 4. Python Native Fixture & Dataset Evaluator Pattern (`scripts/`)

Every domain script under `scripts/` must separate exact native $\mathbb{Z}/\mathbb{Q}$ computation from quarantined external dataset comparison:

```python
#!/usr/bin/env python3
"""Deterministic AOD Usage domain fixture & dataset evaluator."""
from __future__ import annotations

import argparse
import csv
import json
from fractions import Fraction
from pathlib import Path


def delta_three(t_cross: int, observed: int) -> tuple[int, int, int]:
    """Return exact integer residual (delta_z, s_k^(3), m_k)."""
    delta_z = int(t_cross) - int(observed)
    sign_3 = 0 if delta_z == 0 else (1 if delta_z > 0 else -1)
    mag = abs(delta_z)
    return delta_z, sign_3, mag


def check_data(data_dir: Path) -> dict[str, int]:
    """Validate all native CSV/JSONL fixtures using exact integer/Fraction arithmetic."""
    # Verify pre-freeze candidate rows and exact D0 fixtures here
    return {"verified_rows": 0}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-data", action="store_true", help="Verify all native and dataset fixtures")
    args = parser.parse_args()
    if args.check_data:
        summary = check_data(Path(__file__).resolve().parents[1] / "data")
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
```
