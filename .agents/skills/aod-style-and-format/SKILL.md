---
name: aod-style-and-format
description: Enforce the canonical Alpha-Omega Dynamics (AOD) ontologies, Art of the Leprechaun (D.E.C. ledger execution), manuscript format, dataset pipeline, and project structure from https://github.com/rpoyau/aod across AOD Main, AOD Manual, and downstream Usage releases (Matter I - Elementary elements, Matter II - Molecular, Matter III - Biomolecular chaining, and Intelligence).
---
# AOD Ontologies, Art of the Leprechaun (D.E.C.), Format & Project Structure

Codifies the canonical Alpha$\leftrightarrow$Omega Dynamics ($\mathrm{A}\Omega\mathrm{D}$) ontologies, **Art of the Leprechaun** (**D.E.C.** — Declared Edge Computation ledger execution), manuscript format, dataset/fixture pipeline, and repository project structure from **`https://github.com/rpoyau/aod`** (`v41.02`).

## Bundled Canonical References
* [references/aod-main-v41-02.pdf](references/aod-main-v41-02.pdf) — **AOD Main** (*Alpha$\leftrightarrow$Omega Dynamics ($\mathrm{A}\Omega\mathrm{D}$) — The Hidden Temporal Dynamics of Stokes — The Art Of The Leprechaun: Fractal Calculus – $\mathfrak{S}$*, 69 pages, §§1–6, App. A–J, Defs. 1–26, Eqs. (1)–(172) & (RG1)–(RG12)).
* [references/aod-manual-v41-02.pdf](references/aod-manual-v41-02.pdf) — **AOD Manual** (*Alpha$\leftrightarrow$Omega Dynamics ($\mathrm{A}\Omega\mathrm{D}$) — Manual*, 76 pages, §§1–12 including §4 *Pen-and-Paper AFC Raw Execution and D.E.C. Ledger*, App. A–C, Tables 1–41, Figs. 1–32).
* [references/ontology-and-dec-reference.md](references/ontology-and-dec-reference.md) — Complete indexed map of Main §§1–6 equations, Definitions 1–26, Curling-Curl grammar (`App. B`), and D.E.C. Ledger rules (`Manual §4`).
* [references/usage-paper-template.md](references/usage-paper-template.md) — Ready-to-use LaTeX (`main.tex`, `00_scope.tex`, `09_prediction_test_fixture_registry.tex`) and Python (`--check-data`) templates for downstream Usage papers.

---

## 1. Core AOD Ontologies & Topological Spine (`Main §§1–6`)

> *"Axioms $\to$ Distinctions $\to$ Relations $\to$ Motifs $\to$ Calculus. This is the way."* (Main, p. 2)

Every AOD derivation and application must preserve the strict topological Directed Acyclic Graph (DAG) across the six foundational sections of Main (see [references/ontology-and-dec-reference.md](references/ontology-and-dec-reference.md) for all equation numbers):

1. **§1 Specific Distinction & Retained Support (`Eqs. (1)–(11)`):**
   * **Null Sameness:** $x=\mathcal{N},\;x=x,\;\mathcal{N}\equiv\infty_{\mathcal{D}}$ `(1)` and $\mathcal{N}\equiv\infty,\;\mathcal{N}\to\mathcal{N}\to\mathcal{N}\equiv\mathcal{N}$ `(2)`. Schematic repetition of $\mathcal{N}$ creates no new object; once finite events are committed, their distinct identities remain in the trace.
   * **First Finite Anchor:** $a_0=\mathtt{00}_8,\;\mathbf{a}\in\mathcal{A}_8^{\mathrm{ret}}\subseteq\{0,1,\dots,7\}^{<\omega}$ `(3)`. Keep five types strictly distinct: Null $\mathcal{N}$, fibre zero $0$, vertex $0000$, anchor $\mathtt{00}_8$, and scope $B_0$. The glyph $a\mid -$ binds address, with local origin $0\mid -$.
   * **Branch, Hinge, Counterbranch & Awareness:** $x\mapsto x\succ x=x$ `(4)` and $1\,0^*\,-1\rightsquigarrow M_{\varepsilon,m}=\varepsilon\,0_H(0_D)^m(-\varepsilon)$ `(5)`. The hinge $0_H$ is mandatory; $(0_D)^m$ ($m\in\mathbb{Z}_{\ge 0}$) is optional dwell. **Awareness** names this `branch / boundary / not-branch` dynamical motif with role labels `self |` $\mu$ `| not-self` (`SELF`, `BETWEEN`, `NOT-SELF`).
   * **Faithful $Q_4$ Encoding:** $V(Q_4)=\{0,1\}^4,\;E(Q_4)=\{(u,v):d_H(u,v)=1\}$ `(8)`. Each vertex has degree $4$ ($1$ incoming ancestor slot $+ 3$ continuation slots). Conditional atomic support $\Pr[d_H=1\mid\text{admitted atomic event}]=1$ `(9)`; unconstrained ternary capacity $C_3(k)=\log_3(3^k)=k$ `(10)`; scoped boundary $\partial_T R\subseteq E(Q_4)\times\{-1,0,+1\},\;B=(\partial_T R,\omega)$ `(11)`.

2. **§2 Closure-Phase Cycle & Recurring Wave (`Eqs. (12)–(29)`):**
   * **Certified Return & Monon:** Trace $\Gamma_C$ `(12)` and certificate $\operatorname{Cert}(C)$ with $\operatorname{end}(C)\sim_{B,i,\mathcal{W}_C}\operatorname{start}(C)$ `(13)`. Primitive closure $\operatorname{Monon}(x)=\operatorname{cycle}_{\mathrm{H}_3}(x\succ x=x)$ `(14)` requires $m(C)\ge 2$ committed phase-bearing traversals `(15)` and contributes $\Delta\Phi(C)=1_C$ `(16)`.
   * **Return Identity, Beat, Cadence & Wave:** Immutable $\mathrm{id}_{\mathrm{return}}(C)$ `(20)`, reclosure count $\operatorname{bip}_i(\omega)$ `(21)`–`(23)` ($N\ge 1$ closures yield $N$ cycles and $N-1$ beats), and recurring wave $W_{B,i}^{\mathrm{id}},\;W_{B,i}|_k$ `(24)` (requiring $\ge 2$ compatible distinct completions).
   * **Reflected-Leg Bound:** Via formal comparison embedding $\iota_{\mathrm{ref}}(n1_C)=2nh$ `(26)`, $\delta\phi^\to+\delta\phi^\leftarrow\ge 2\Delta\phi_{\mathrm{step}}=\iota_{\mathrm{ref}}(1_C)$ `(27)`–`(28)` is a necessary phase-support conjunct of closure, never sufficient closure admission; equal-leg factorization $2\delta\phi\ge\iota_{\mathrm{ref}}(1_C)$ `(29)` requires declared leg equality.

3. **§3 Curl Closure, Duon Current & Field Compression (`Defs. 1–14`, `Eqs. (30)–(51)`):**
   * **Strict Motif Typing:** Curl, Nested curl, Pin-curl, Curling curls (`Defs. 1–4`); $\mathrm{Dion}$ $D_\alpha=(+1,-1),\;D_\Omega=(-1,+1)$ (`Def. 5`); $\mathrm{Duon}$ $D_i\mu_M D_j$ (`Def. 6`, `(30)`, $2\times 3\times 2=12$ variants); $\mathrm{Duad}$ seated state (`Def. 7`); $\mathrm{Dimonon}=2\,\mathrm{Monon}\ne\mathrm{Dion}$ `(34)`.
   * **Reflection Duration & Curling-Curl Support:** $RD_\gamma(B)=\Pi_\gamma^-(B)+H_{\mu,\gamma}(B)+\Pi_\gamma^+(B)$ `(31)`, symmetric $2\Pi+H_{\mu,\gamma}(B)$ `(32)`, single-hinge $2\Pi+1$ `(50)`. Support model $\Pi(p{:}q)=q^p+q$ `(35)` gives $(\Pi,RD_B^{(1)})=(4,9),(10,21),(30,61),(68,137)$ for $1{:}2$ (`Dimonon`), $3{:}2$ (`Ditrion`), $3{:}3$ (`Tritrion`), $3{:}4$ (`Tetratrion`). Admission requires trace $K_{\mathrm{prop}}\xrightarrow{HT(K;B)}K_{\mathrm{adm}}(B)$ `(37)`.
   * **Field Organization & Compression:** Scoped field $F_{B,\lambda}|_k$ `(38)` resolves wave identities (`Defs. 10–12`: Region, Boundary, Polychiral shell dressing). Certified cycle-valued field compression $C_f[\Sigma]_{\mathrm{A}\leftrightarrow\Omega}$ `(40)` (`Def. 13`), $\operatorname{Fold}^\uparrow$ `(41)`, $\operatorname{Expose}^\downarrow$ `(42)`, and hinge kernel $\mathrm{AO}_\mu(C)=\langle\Pi_\alpha(C),H_\mu(C),\Pi_\Omega(C)\rangle$ `(44)`–`(51)` (`Def. 14`).

4. **§4 Wave State, RCD & Relational Time (`Eqs. (52)–(70)`):**
   * Complete wave state $S_{B,i,k}^W$ `(52)`, coupling state $S_{I,B,k}^\times$ `(53)`, update law $\mathcal{U}_B$ `(54)`, pair contact record $e_s^\times$ `(55)`.
   * Directional $\mathrm{RCD}_{ij}(B)=RD_B(C_{ij})\bowtie_B R_{ij}^{\mathrm{asym}}(B)$ `(56)`, scalar duration $\rho_{ij}^D(B)$ `(57)`, window clip $\rho_{\omega,ij}^D=\min_{\mathcal{D}}(\rho_{ij}^D,|\omega|_{ij}^{\mathcal{D}})$ `(60)`.
   * **Relational Time:** $\operatorname{biz}_{i\mid j}^{TF}(\omega)=\Delta\operatorname{bip}_i(\omega)/\Delta\operatorname{bip}_j(\omega)$ `(61)` and $\operatorname{RT}_{I,B}(\omega)$ `(64)` require $\ge 2$ recurrent coupled lineages with repeated bound contacts on common integer window $\omega=(u,v]$ (no background clock $t$).
   * **Hinge Saturation (`§4.4.1`):** When additional same-resolution dwell is empty `(67)`–`(69)`, continuation is restricted to $\sigma'\in\{-1,+1\}$ `(70)` with conditional binary role entropy $\le\log_3 2$ (distinct from $C_3(k)=k$ `(10)`).

5. **§5 Field, Finite Stokes, SADAR, Shedding, Shells, Fusion, FRG & Harmonics (`Defs. 15–26`, `Eqs. (71)–(154)`, `(RG1)–(RG12)`):**
   * **Typed Finite Flux & Stokes:** Keep normalized $\phi_{ij}^{\mathrm{AFC}}$ (`|\phi_{ij}^{\mathrm{AFC}}|\le 1`) distinct from pressure-bearing $\phi_{ij}^{\mathrm{AOD}}(B)=p_{ij}^D(B)A_{ij}(B)=C_{3,ij}\rho_{\omega,ij}^D(B)\Delta\chi_{ij}^{\mathrm{lag}}(B)i_{ij}(B)$ `(71)`–`(82)`. Internal pairs cancel in $\sum_{i\in R}\operatorname{div}(i;B)=\sum_{i\in R,j\notin R}\phi_{ij}(B)$ `(73)` while contributing lineage records remain retained. Slice flux $\Phi_{\partial R}^D(t;B|_t)$ `(83)`, window current $J_{\partial R}^D(\omega;B)$ `(84)`, moving boundary $\Phi_{\partial R,\mathrm{mov}}^D=\Phi_{\mathrm{cross}}^D-\Phi_{\mathrm{sweep}}^D+\Phi_{\mathrm{shedding}}^D$ `(88)`.
   * **Field Count, Pressure & SADAR:** $n_F(\mathcal{B})=|\mathcal{F}_{\mathcal{B}}|$ `(89)`, $\mathcal{O}_{\partial F}(\mathcal{B})=n_F(\mathcal{B})\log n_F(\mathcal{B})$ for $n_F(\mathcal{B})\ge 1$ `(90)`; Duonic pressure $P_F^D(B)$ `(91)`; SADAR operator $\mathfrak{S}_B(C)$ `(92)`–`(95)`; ADAR `(96)`; SADAR balance `(97)`; attention vector $\mathbf{A}_F(B)$ `(98)`–`(99)`; realized motion at $k+1$ `(100)`–`(101)`; pending overhang $Q_{ij}^D(B)=C_{3,ij}\max(0,\rho_{ij}^D(B)-|\omega|_{ij})$ `(104)`–`(105)`.
   * **Shedding, Enclosures, Fusion & FRG:** Shedding $X_{\mathrm{shedding}}=\max(0,P_W^{\mathfrak{S}}-C_W^{\mathrm{close}})$ `(107)`–`(110)`; $\operatorname{Yro}_L(K;B)$ odd-window route status between even support enclosures $\mathsf{C}_6$ (`hexon`), $\mathsf{C}_8$ (`octon`), $\mathsf{C}_{10}$ (`decon`), $\mathsf{C}_{2n}$; $\operatorname{TTL}_{\mathcal{C}}(\partial F,\omega)$ `(113)`; fusion $\operatorname{Fuse}_B(F,G)=\operatorname{Close}_B(\widehat{F}\,\mu\,\widehat{G})$ `(114)`, exoshedding lift `(119)`–`(121)`, link-closure ladder `(122)`–`(123)`; Fractal Field Ring Gate $T_k^\times-T_k^0=\sum C_{ij,k}^\times(B)$ `(RG1)`–`(RG12)`; trace discipline spine `(135)`.
   * **Finite Harmonics (`§5.16`):** Downstream representation `(139)`–`(150)` on finite abelian group $G$ of *already admitted* recurrence; never admits waves or certifies closure.

6. **§6 Operative Self, Learning & Retained Carriage (`Eqs. (155)–(160)`):**
   * Complete-state factorization $S_k^+=(X_k,M_k^C,R_k)$ `(155)`, retained rebalancing $r_e=\Phi_e^{\mathrm{recurrent}}-\Phi_e^{\mathrm{independent}}$ `(156)`, structural removal $S_k^{-e}=(X_k,M_k^C,R_k\setminus\{R_e\})$ (without inserting numeric zero), strictly later outcome $t>k$ in $\operatorname{Op}_e^{O,H}(S_k)=1$ `(157)`, operative self subgraph $(I_k^{\mathrm{op}},V_k^{\mathrm{op}},E_k^{\mathrm{op}})$ `(159)`, persistent learning, and upward carriage $R^\uparrow$ `(160)`.

---

## 2. The Art of the Leprechaun aka D.E.C. Ledger (`Manual §4`)

> *"AFC runs raw. The trace records the run. $\mathrm{A}\Omega\mathrm{D}$ names detected motifs."*
> *"D.E.C. means Declared Edge Computation ledger. ... Use the dotted form D.E.C.; the ledger is a manual value container for declared edge data."* (Manual §4, pp. 14–15)

### 2.1 The D.E.C. Execution Spine
$$\text{AFC raw node}\to\text{D.E.C. ledger}\to\text{exact kernel}\to\text{blocked hinge}\to\text{hinge slide}\to\text{oriented ADAR component}\to\text{SADAR value}\to\text{boundary audit}.$$

### 2.2 D.E.C. Row Schema & Invariants (`Manual §§4.1–4.10`)
1. **9-Column D.E.C. Row Format:**
   $$\bigl(B,\; v,\; e,\; v_e,\; \sigma(e),\; \operatorname{adm}(e;B),\; w(e;B),\; P(e;B),\; \operatorname{route}(e;B)\bigr)$$
   * Records the $H1$ base traversal $(v,e,v_e)$ separately from the local ternary fibre state $\sigma(e)\in\{-1,0,+1\}$.
   * $\operatorname{adm}(e;B)=0\implies P(e;B)=0$; normalized kernel satisfies $\sum_e P(e;B)=1$ over admissible slots using exact rational fractions.
   * $\operatorname{route}(e;B)\in\{\text{returned},\;\text{outgoing},\;\text{blocked},\;\text{slide},\;\text{hinge},\;\text{pending}\}$.
2. **Blocking Rule & Hinge Slide (`§§4.4–4.5`):**
   * When same-resolution hinge dwell is blocked ($\operatorname{adm}(e_3,0;B)=0$), remove the **additional-dwell row $(e_3,0_D)$**—not the edge slot $e_3$ itself—setting $m=0$ in $\varepsilon\,0_H(0_D)^m(-\varepsilon)$ while retaining the structural hinge $0_H$.
   * Slot $e_3$ may re-enter only as an admitted branch state $\sigma'\in\{-1,+1\}$.
   * Declare the post-block slide pool $\operatorname{Slide}_\mu(B|_t)=\{s_1,\dots,s_n\}$ and renormalize **only after** the slide pool is declared: $P_{\mathrm{slide}}(s_i;B|_t)=w(s_i;B|_t)/Z_{\mathrm{slide}}(B|_t)$.
3. **Field Tunnelling: Hinge-Slide Window Clip (`§4.6`):**
   * For a blocked direct hinge $\operatorname{adm}(e_0;B|_t)=0$, evaluate each slide-compatible successor $s_i\in\operatorname{Slide}_\mu(B|_t)$:
     $$\rho_{\omega,s_i}^D(B)=\min(RD_{s_i}(B),|\omega|_{s_i}),\quad p_{s_i}^D(B)=C_{3,s_i}\rho_{\omega,s_i}^D(B),\quad T_{\mathrm{tunnel}}^D(B|_t)=\sum_{s_i}P_{\mathrm{slide}}(s_i;B|_t)p_{s_i}^D(B).$$
4. **ADAR/SADAR Promotion & Route Audit (`§§4.7–4.10`):**
   * Promote a routed D.E.C. row-pair to ADAR/SADAR: $p^D=C_3\rho_\omega^D,\;\mathfrak{S}_B=p^D A_{12},\;\mathfrak{S}_B(C_{\bar{e}})=-\mathfrak{S}_B(C_e)$.
   * Boundary closure & sheddic route audit: $\Delta_{\mathrm{close}}=P^D-C_{\mathrm{close}},\;X_{\mathrm{shedding}}=\max(0,\Delta_{\mathrm{close}})$.
   * Missing-burden diagnostic: record exact rational $\operatorname{miss}_\tau(K)=M_{\mathrm{miss}}(K)/M_{\mathrm{ref}}(K)$ (`missing_num`, `missing_den`, `missing_frac_exact`), with any decimal (`missing_fraction_display`) strictly quarantined to presentation.

---

## 3. Repository & Downstream Usage Project Structure (`https://github.com/rpoyau/aod`)

### 3.1 Canonical `rpoyau/aod` Repository Layout
```text
aod/
├── main.tex                          # Main container (\input{preamble.tex}, sections/00..08, appendices/A..J)
├── preamble.tex                      # Main macros (\AO, \SADARop, \secref, \eqnref, \appref, \aodprovenance, etc.)
├── refs.bib                          # Main foundational bibliography (10 entries: AF, AFC, Markov/combinatorics)
├── sections/                         # Main §§1–6 (00_title, 01_abstract, 03_afc_basis .. 08_awareness_learning_mindfulness)
├── appendices/                       # Main Appendices A–J (A_fractal_address_bip_biz .. J_ao_field_fractal_properties)
├── figures/ & figures_jpg/           # Main figures (Figs. 1–15)
├── manual/                           # Paired Manual / Usage package (built after Main using ../main.aux & ../main.fls)
│   ├── main.tex                      # Manual container (titlepage, TOC, sections/00..09, appendices/A..C)
│   ├── preamble.tex                  # xr-hyper verification of ../main.aux & ../main.fls + \mainequation/\mainsection/\mainappendix/\maintable
│   ├── refs.bib                      # Manual dataset & measured-target bibliography (38 entries)
│   ├── sections/                     # Manual §§1–12 (00_scope, 00_native_..., 00_awareness_fixtures, 00_dec_ledger, 01..07, 09_registry)
│   ├── appendices/                   # Manual Appendices A (Simulation fixtures), B (Quarantined external comparison), C (3D phase-cycle delta_3)
│   ├── data/                         # Input & derived datasets (m1/, m2/, dec/, higgs/, sparc/, lensing/, tau/, brownian/, run_tumble/, derived/)
│   ├── scripts/                      # Deterministic Python engines (aod_native_closure_wave.py, aod_awareness.py, score_sparc_field_dynamics.py, etc.)
│   └── figures/                      # Manual figures (Figs. 1–32)
├── evidence/                         # Frozen SHA-256 & DAG audit bindings (ONTOLOGY_COMPACTION_BINDINGS.json, etc.)
├── scripts/                          # Repository-wide verifiers (audit_scientific_sources.py, audit_ontology_compaction.py, sync_zenodo_references.py)
├── tests/                            # Pytest suite enforcing ontology, Main/Manual ownership, table grammar, and fixture execution
├── CANONICAL_VERSION.txt             # Active canonical release tag (e.g., v41.02)
├── RELEASE_READINESS.txt             # Release status locks
└── .zenodo.json & README.md          # Publication metadata
```

### 3.2 Downstream Usage Paper Architecture (`Matter I–III`, `Intelligence`)
Downstream releases (**Matter I — Elementary elements**, **Matter II — Molecular**, **Matter III — Biomolecular chaining**, **Intelligence**) are **pure specific usages of AOD Main** structured identically to `manual/` (see [references/usage-paper-template.md](references/usage-paper-template.md)):
1. **No Re-Axiomatization:** Never duplicate or mutate Main ontology; import Main equations, sections, appendices, and tables via `\mainequation{main:...}`, `\mainsection{main:...}`, `\mainappendix{main:...}`, `\maintable{main:...}`.
2. **Active Calculation Spine (`Manual §1.3`):**
   $$\mathbf{a}\vdash(F,R,\partial_T R,\omega),\quad B=(\partial_T F,\omega)\implies C_f[\Sigma]_{\mathrm{A}\Omega},\quad \mathrm{AO}_\mu(C)=\langle\Pi_\alpha,H_\mu,\Pi_\Omega\rangle,\quad \mathfrak{S}_B(C)=p_{C,\mathrm{A}\Omega}^D A_{C,\mathrm{A}\Omega},\quad \Phi_{\partial_T R}^D=\sum_{e\in\partial_T R}\mathfrak{S}_B(C_e).$$
   *Tables store evaluated values. Tables are not the calculus.*
3. **Input-Data & Benchmark Dataset Pipeline (`Manual §§1.4–1.10, §10, §12`):**
   * **Exact $\mathbb{Z}/\mathbb{Q}$ Native Side vs. Quarantined External Side:** $\mathrm{A}\Omega$-internal calculations use exact integers and `fractions.Fraction`. External constants ($c,h_{\mathrm{ext}},e,\eta_{\mathrm{ext}}=\alpha_{\mathrm{fs}}^{-1},K_{\mathrm{ext}}$) and decimals live strictly inside $\mathsf{Q}_{\mathrm{ext}}(\nu_{x,\mathrm{A}\leftrightarrow\Omega};\mathcal{T}_x)$ (`Manual App. B`) with 6-tuple decimal precision records $(x_{\mathrm{disp}},u_x,\mathrm{unit}(x),\mathrm{src}(x),\mathrm{round}(x),\mathrm{scope}(x))$.
   * **Pre-Freeze Candidate Selection vs. Post-Freeze Target Join:** Internal candidates (`data/candidates/*_internal_candidates_selection.csv`) and score formulas (`*_score_formula.md`) must freeze using purely native accessors ($RD, P^D, Q^D$, saddle residuals) **before** external targets join (`*_external_map_after_candidate_freeze.csv`).
   * **Data-Support Classes (`Table 25`):** Declare $D0$ (exact internal $\delta_3$ fixture), $O0$ (observable-map fixture), $G0$ (radial shell projection), $G1$ (radial + proxy medium), $G2$ (3D shell field-dynamics retention), $G3$ (time-resolved 3D/4D tracer-current simulation, `App. C`), or $L0\text{--}L3$ (staged field-ring / target-acquisition / 3D+time-flow input-gate lanes) along the error chain $D\to R(D)\to\mathcal{M}(D,R)\to\Pi_{\mathrm{report}}\to\epsilon_{\mathrm{report}}$ with simulation data card $(D,C_{\mathrm{support}},M_{\mathrm{A}\leftrightarrow\Omega},\Pi_{\mathrm{report}},\sigma_{\mathrm{input}},\epsilon_{\mathrm{report}},\mathrm{src})$.
   * **Honest Incomplete Gates:** If an upstream calculation recipe, adapter, or $L3/K4$ dataset is not supplied, state explicitly that it is not supplied and hold the row as an input manifest or `HOLD_MISSING_AUTHENTIC_SOURCES` gate.

---

## 4. Revision & Pull Request Governance

* **All Changes Require an Open PR for the Next Revision:** Never push directly to `main`. Every manuscript, dataset, fixture, or metadata change must be committed on a dedicated branch and opened as a Pull Request targeting the next canonical revision.
* **Mandatory Verification Gate:**
  1. `python3 scripts/audit_scientific_sources.py` (verifies `audit_ontology_compaction.py`, 436 Main / 201 Manual labels, 99 literal provenance records, 72 DAG dependencies, and 167 frozen SHA-256 files).
  2. `python3 manual/scripts/aod_native_closure_wave.py --check-data` and `python3 manual/scripts/aod_awareness.py --check-data`.
  3. Full `pytest` suite (`python3 -m pytest -q`).
  4. Paired `latexmk` builds (`Main` first, then `Manual` / Usage papers) with zero unresolved references or stale AUX files.
